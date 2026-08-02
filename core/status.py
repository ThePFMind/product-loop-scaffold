"""Project status, derived — never written (a lens, not a ledger).

Recomputes everything from existing truth on every call: the journal,
gates/*.md, records/ frontmatter, contracts/ hashes. If this module and
reality ever disagree, reality wins and this module has the bug.

CLI:  uv run python -m core.status
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from core import journal
from core.hashing import file_hash

ROOT = Path(__file__).resolve().parent.parent
GATE_ROW = re.compile(r"^\|\s*([A-Z]\d+)\s*\|\s*(.+?)\s*\|\s*(PASS|FAIL)\s*\|")
GATE_LIKE = re.compile(r"^\|\s*[A-Z]\d+\s*\|")

# The lens's vocabulary. An event kind outside this set is LENS DRIFT: truth
# the monitor does not yet understand. Drift spawns a monitor-update task
# (normal governed path); it is never silently ignored.
KNOWN_KINDS = {
    "session.start", "session.blocked", "session.zero", "iteration", "exit",
    "phase.green", "budget.exhausted", "merge.proposed", "merge.approved",
    "revert", "gate.verdict", "feedback.received", "research.evidence",
    "hypothesis.killed", "ledger.post",
}
FRONT = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def gates() -> tuple[list[dict], int]:
    """Every gate file is shown, even rowless (truth may not vanish);
    gate-like lines that fail to parse are counted as drift."""
    out, unparsed = [], 0
    for path in sorted((ROOT / "gates").glob("*.md")):
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            m = GATE_ROW.match(line)
            if m:
                rows.append({"id": m.group(1),
                             "criterion": m.group(2)[:90],
                             "state": m.group(3)})
            elif GATE_LIKE.match(line):
                unparsed += 1
        out.append({"gate": path.stem, "rows": rows,
                    "passed": sum(r["state"] == "PASS" for r in rows),
                    "total": len(rows)})
    return out, unparsed


def journal_stats() -> dict:
    entries = list(journal.entries())
    sessions: dict[str, int] = {}
    proposed: dict[str, dict] = {}
    phase = None
    for e in entries:
        if e["kind"] == "session.start":
            sessions[e["actor"]] = sessions.get(e["actor"], 0) + 1
        if e["kind"] == "merge.proposed" and "sha" in e["payload"]:
            proposed[e["payload"]["sha"]] = e
        if e["kind"] == "merge.approved" and "sha" in e["payload"]:
            proposed.pop(e["payload"]["sha"], None)
        if e["kind"] == "iteration":
            phase = e["payload"].get("phase", phase)
    unknown = sorted({e["kind"] for e in entries} - KNOWN_KINDS)
    return {"events": len(entries), "sessions": sessions,
            "unapproved": list(proposed.values()),
            "phase": phase, "chain_ok": journal.verify_chain(),
            "unknown_kinds": unknown, "last": entries[-5:]}


def frontmatter(path: Path) -> dict:
    m = FRONT.match(path.read_text(encoding="utf-8"))
    fields: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
    return fields


def records_stats() -> dict:
    out: dict = {"blocking": [], "records": {}}
    rec = ROOT / "records"
    if not rec.is_dir():
        return out
    for path in rec.rglob("*.md"):
        if path.parent.name == "templates":
            continue
        f = frontmatter(path)
        if "blocking" in f:
            out["blocking"].append(
                {"record": path.stem, "on": f["blocking"].strip("[]")})
        bucket = path.parent.name if path.parent != rec else "root"
        status = f.get("status") or f.get("decision") or "-"
        out["records"].setdefault(bucket, {}).setdefault(status, 0)
        out["records"][bucket][status] += 1
    return out


def contract_hashes() -> list[dict]:
    return [{"file": p.name, "sha256": file_hash(p)[:12]}
            for p in sorted((ROOT / "contracts").glob("*.py"))
            if p.name != "__init__.py"]


def git_line() -> str:
    try:
        r = subprocess.run(["git", "log", "--oneline", "-1"],
                           capture_output=True, text=True, cwd=ROOT, timeout=5)
        return r.stdout.strip() or "no commits"
    except Exception:
        return "not a git repo"


def compute() -> dict:
    j = journal_stats()
    r = records_stats()
    g, unparsed = gates()
    needs_you = []
    for e in j["unapproved"]:
        needs_you.append(f"merge proposed, unapproved: {e['payload'].get('sha', '?')[:8]}")
    for bucket, counts in r["records"].items():
        if bucket == "hypotheses" and counts.get("proposed"):
            needs_you.append(f"{counts['proposed']} hypothesis(es) awaiting decision")
        if bucket == "questions" and counts.get("open"):
            needs_you.append(f"{counts['open']} question(s) open")
    drift = {"unknown_kinds": j["unknown_kinds"],
             "unparsed_gate_rows": unparsed}
    return {"needs_you": needs_you,
            "drift": drift,
            "gates": g,
            "sessions": j["sessions"],
            "phase": j["phase"],
            "blocked": r["blocking"],
            "integrity": {"chain_ok": j["chain_ok"],
                          "journal_events": j["events"],
                          "contracts": contract_hashes(),
                          "git": git_line()},
            "records": r["records"],
            "recent": [{"ts": e["ts"], "actor": e["actor"], "kind": e["kind"]}
                       for e in j["last"]]}


def _fmt(s: dict) -> str:
    lines = []
    lines.append("NEEDS YOU  " + ("; ".join(s["needs_you"]) or "nothing — loops may run"))
    for g in s["gates"]:
        lines.append(f"GATE       {g['gate']}: {g['passed']}/{g['total']} PASS")
    sess = " · ".join(f"{k}:{v}" for k, v in s["sessions"].items()) or "none yet"
    lines.append(f"SESSIONS   {sess}" + (f" · phase: {s['phase']}" if s["phase"] else ""))
    if s["blocked"]:
        lines.append("BLOCKED    " + "; ".join(f"{b['record']} on {b['on']}" for b in s["blocked"]))
    d = s["drift"]
    if d["unknown_kinds"] or d["unparsed_gate_rows"]:
        bits = []
        if d["unknown_kinds"]:
            bits.append("kinds not understood: " + ", ".join(d["unknown_kinds"]))
        if d["unparsed_gate_rows"]:
            bits.append(f"{d['unparsed_gate_rows']} gate row(s) unparsed")
        lines.append("DRIFT      " + " · ".join(bits) + "  -> monitor-update task")
    i = s["integrity"]
    ch = "OK" if i["chain_ok"] else "BROKEN"
    lines.append(f"INTEGRITY  chain {ch} · {i['journal_events']} events · {i['git']}")
    for c in i["contracts"]:
        lines.append(f"CONTRACT   {c['file']} {c['sha256']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_fmt(compute()))
