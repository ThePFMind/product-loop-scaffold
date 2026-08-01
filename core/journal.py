"""Append-only, hash-chained journal — the single source of runtime truth (R6).

One SQLite table. No UPDATE, no DELETE: blocked by triggers, and any tampering
that bypasses the triggers breaks the hash chain (verify_chain -> False).

Law 0 justification: agents faking or rewriting logs is a *recorded* failure
class (Darwin Godel Machine incidents). The chain makes tampering evident;
the triggers make append-only mechanical rather than conventional.

v0 is single-writer (BEGIN IMMEDIATE serializes). Concurrent writers are a
deferred trigger (see records/REQ-001.md -> Postgres).

CLI:
  python -m core.journal append <actor> <kind> '<json-payload>'
  python -m core.journal verify
  python -m core.journal tail [n]
  python -m core.journal replay          # prints every entry in order
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Callable, Iterator, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "state" / "journal.db"
GENESIS = "0" * 64

_SCHEMA = """
CREATE TABLE IF NOT EXISTS journal (
  seq       INTEGER PRIMARY KEY AUTOINCREMENT,
  ts        TEXT NOT NULL,
  actor     TEXT NOT NULL CHECK (length(actor) > 0),
  kind      TEXT NOT NULL,
  payload   TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  hash      TEXT NOT NULL UNIQUE
);
CREATE TRIGGER IF NOT EXISTS journal_no_update
BEFORE UPDATE ON journal
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER IF NOT EXISTS journal_no_delete
BEFORE DELETE ON journal
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
"""


def _row_hash(ts: str, actor: str, kind: str, payload: str, prev_hash: str) -> str:
    material = "\x1f".join((ts, actor, kind, payload, prev_hash))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def connect(db: Path = DB_PATH) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db, isolation_level=None)  # explicit transactions
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def append(actor: str, kind: str, payload: dict,
           conn: Optional[sqlite3.Connection] = None) -> dict:
    """Append one entry. Provenance (actor) is mandatory — empty actor aborts."""
    own = conn is None
    conn = conn or connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT hash FROM journal ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else GENESIS
        ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        h = _row_hash(ts, actor, kind, body, prev)
        conn.execute(
            "INSERT INTO journal (ts, actor, kind, payload, prev_hash, hash) "
            "VALUES (?,?,?,?,?,?)", (ts, actor, kind, body, prev, h))
        conn.execute("COMMIT")
        return {"ts": ts, "actor": actor, "kind": kind, "payload": payload, "hash": h}
    except BaseException:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        if own:
            conn.close()


def verify_chain(conn: Optional[sqlite3.Connection] = None) -> bool:
    """Recompute every hash in order. True iff the whole chain is intact."""
    own = conn is None
    conn = conn or connect()
    try:
        prev = GENESIS
        cur = conn.execute(
            "SELECT ts, actor, kind, payload, prev_hash, hash "
            "FROM journal ORDER BY seq")
        for ts, actor, kind, payload, prev_hash, h in cur:
            if prev_hash != prev:
                return False
            if _row_hash(ts, actor, kind, payload, prev_hash) != h:
                return False
            prev = h
        return True
    finally:
        if own:
            conn.close()


def entries(conn: Optional[sqlite3.Connection] = None) -> Iterator[dict]:
    own = conn is None
    conn = conn or connect()
    try:
        cur = conn.execute(
            "SELECT seq, ts, actor, kind, payload, hash FROM journal ORDER BY seq")
        for seq, ts, actor, kind, payload, h in cur:
            yield {"seq": seq, "ts": ts, "actor": actor, "kind": kind,
                   "payload": json.loads(payload), "hash": h}
    finally:
        if own:
            conn.close()


def replay(handler: Callable[[str, dict], None],
           conn: Optional[sqlite3.Connection] = None) -> int:
    """Feed every entry, in order, to handler(kind, payload).
    Verification-by-reconstruction (R6): rebuild state from history, compare."""
    n = 0
    for e in entries(conn):
        handler(e["kind"], e["payload"])
        n += 1
    return n


def _main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "append" and len(argv) >= 4:
        payload = json.loads(argv[4]) if len(argv) > 4 else {}
        e = append(argv[2], argv[3], payload)
        print(json.dumps(e))
        return 0
    if cmd == "verify":
        ok = verify_chain()
        print("chain: OK" if ok else "chain: BROKEN")
        return 0 if ok else 1
    if cmd == "tail":
        n = int(argv[2]) if len(argv) > 2 else 10
        rows = list(entries())[-n:]
        for e in rows:
            print(json.dumps(e))
        return 0
    if cmd == "replay":
        count = replay(lambda kind, payload: print(kind, json.dumps(payload)))
        print(f"replayed {count} entries")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
