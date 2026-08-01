"""Feedback intake (R12): preserve verbatim, journal the receipt.

  python -m core.intake "the raw feedback text" --source "call with Dana" --channel call
"""
from __future__ import annotations
import argparse, datetime, re
from pathlib import Path
from core import journal

FEEDBACK = Path(__file__).resolve().parent.parent / "records" / "feedback"

def next_id() -> str:
    nums = [int(m.group(1)) for p in FEEDBACK.glob("FB-*.md")
            if (m := re.match(r"FB-(\d+)", p.stem))]
    return f"FB-{(max(nums) + 1 if nums else 1):03d}"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--source", default="unattributed")
    ap.add_argument("--channel", default="chat")
    a = ap.parse_args()
    fid = next_id()
    today = datetime.date.today().isoformat()
    body = (f"---\nid: {fid}\nsource: {a.source}\nreceived: {today}\n"
            f"channel: {a.channel}\n---\n{a.text}\n")
    path = FEEDBACK / f"{fid}.md"
    path.write_text(body, encoding="utf-8")
    journal.append("human", "feedback.received",
                   {"id": fid, "source": a.source, "channel": a.channel})
    print(path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
