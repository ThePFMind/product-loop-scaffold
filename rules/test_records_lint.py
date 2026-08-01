"""Executable rules for the research loops (R2/R11-R13).

Market truth is not machine-checkable; record STRUCTURE is. Every record in
records/{evidence,questions,hypotheses,decisions,feedback}/ must carry the
fields that make it auditable. Templates in records/templates/ are linted
too, so the scaffold ships green and stays green.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "records"

REQUIRED = {
    "evidence": {"id", "question", "claim", "source_url", "retrieved",
                 "quote", "provenance", "trust", "confidence"},
    "question": {"id", "text", "status", "spawned_by"},
    "hypothesis": {"id", "statement", "evidence", "kill_condition", "status"},
    "decision": {"id", "hypothesis", "decision", "by", "date", "slice",
                 "falsifier"},
    "feedback": {"id", "source", "received", "channel"},
}
DIR_KIND = {"evidence": "evidence", "questions": "question",
            "hypotheses": "hypothesis", "decisions": "decision",
            "feedback": "feedback"}


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    assert m, f"{path}: missing frontmatter"
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields, m.group(2)


def record_files():
    out = []
    for d, kind in DIR_KIND.items():
        for p in sorted((ROOT / d).glob("*.md")):
            out.append((p, kind))
    for p in sorted((ROOT / "templates").glob("*.md")):
        out.append((p, p.stem))
    return out


@pytest.mark.parametrize("path,kind", record_files(),
                         ids=lambda x: str(x) if isinstance(x, str) else x.name)
def test_record_structure(path, kind):
    fields, body = parse_frontmatter(path)
    missing = REQUIRED[kind] - fields.keys()
    assert not missing, f"{path.name}: missing {sorted(missing)}"

    if kind == "evidence":
        q = fields["quote"].strip('"')
        assert 0 < len(q.split()) <= 25, f"{path.name}: quote over 25 words"
        assert fields["provenance"] in {"external", "inference", "memory",
                                        "contract"}
        assert fields["trust"] in {"verified", "unverified"}
        assert 0.0 <= float(fields["confidence"]) <= 1.0
        assert fields["source_url"].startswith("http")
    if kind == "hypothesis":
        assert fields["kill_condition"], f"{path.name}: empty kill_condition"
        assert fields["evidence"].strip("[] "), \
            f"{path.name}: hypothesis with no linked evidence (R7)"
    if kind == "decision":
        assert fields["by"] == "human", \
            f"{path.name}: decisions are made by humans only (R14)"
        assert fields["decision"] in {"build", "park", "kill"}
    if kind == "feedback":
        assert body.strip(), f"{path.name}: feedback with no verbatim body (R12)"


def test_no_orphan_dirs():
    for d in DIR_KIND:
        assert (ROOT / d).is_dir(), f"records/{d}/ missing"
