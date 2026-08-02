"""MONITOR CONFORMANCE — steward-owned (deny-listed). The unmodifiable part
that evaluates the lens (the DGM lesson: the agent improving the monitor
must never be able to edit the checks that keep the monitor honest).

Agents MAY improve core/status.py and core/monitor.py through the normal
governed path — these invariants are what every improvement must preserve.
"""
from __future__ import annotations

from pathlib import Path

from core import status
from core.monitor import render

SRC = (Path(status.__file__).read_text(encoding="utf-8")
       + (Path(status.__file__).parent / "monitor.py").read_text(encoding="utf-8"))


def test_lens_is_derived_only():
    """The lens never writes: no journal appends, no non-GET handlers."""
    assert "journal.append" not in SRC
    assert "do_POST" not in SRC and "do_PUT" not in SRC and "do_DELETE" not in SRC


def test_every_gate_file_is_shown():
    """Truth may not vanish: every gates/*.md appears, rowless included."""
    s = status.compute()
    shown = {g["gate"] for g in s["gates"]}
    files = {p.stem for p in (status.ROOT / "gates").glob("*.md")}
    assert files == shown


def test_integrity_and_drift_are_unsuppressible():
    """Chain status and the drift channel must always be present and rendered."""
    s = status.compute()
    assert "chain_ok" in s["integrity"]
    assert {"unknown_kinds", "unparsed_gate_rows"} <= s["drift"].keys()
    page = render(s, "t")
    assert "chain" in page  # integrity band always rendered


def test_unknown_journal_kind_surfaces_as_drift(tmp_path, monkeypatch):
    """A new event kind the lens doesn't know must appear as drift, not silence."""
    from core import journal as jl
    conn = jl.connect(tmp_path / "j.db")
    jl.append("test", "totally.new.kind", {}, conn=conn)
    monkeypatch.setattr(jl, "connect", lambda db=None: jl.sqlite3.connect(
        tmp_path / "j.db"))
    # re-derive via journal_stats which uses journal.entries -> connect
    stats = status.journal_stats()
    assert "totally.new.kind" in stats["unknown_kinds"]
