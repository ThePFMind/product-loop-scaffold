"""Harness self-test: the journal (v0 machinery) must arrive green at
scaffold time — only the ledger rule suite is default-FAIL.
"""
from __future__ import annotations

import sqlite3

import pytest

from core import journal


@pytest.fixture
def conn(tmp_path):
    c = journal.connect(tmp_path / "journal.db")
    yield c
    c.close()


def test_append_and_verify_chain(conn):
    journal.append("test", "alpha", {"n": 1}, conn=conn)
    journal.append("test", "beta", {"n": 2}, conn=conn)
    journal.append("test", "gamma", {"n": 3}, conn=conn)
    assert journal.verify_chain(conn=conn)
    kinds = [e["kind"] for e in journal.entries(conn=conn)]
    assert kinds == ["alpha", "beta", "gamma"]


def test_update_and_delete_are_blocked(conn):
    journal.append("test", "alpha", {}, conn=conn)
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE journal SET kind='tampered' WHERE seq=1")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM journal WHERE seq=1")


def test_chain_detects_tampering_even_without_triggers(conn):
    journal.append("test", "alpha", {"n": 1}, conn=conn)
    journal.append("test", "beta", {"n": 2}, conn=conn)
    conn.execute("DROP TRIGGER journal_no_update")  # simulate a bypass
    conn.execute("UPDATE journal SET payload='{\"n\":99}' WHERE seq=1")
    assert not journal.verify_chain(conn=conn)


def test_empty_actor_is_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError):
        journal.append("", "alpha", {}, conn=conn)


def test_replay_reconstructs_in_order(conn):
    for i in range(5):
        journal.append("test", "tick", {"i": i}, conn=conn)
    seen: list[int] = []
    n = journal.replay(lambda kind, p: seen.append(p["i"]), conn=conn)
    assert n == 5 and seen == [0, 1, 2, 3, 4]
