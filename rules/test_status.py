"""The lens must not rot: status derives, parses gates, and renders."""
from core import status
from core.monitor import render


def test_compute_shape_and_gates_default_fail():
    s = status.compute()
    assert {"needs_you", "gates", "integrity", "recent"} <= s.keys()
    assert {g["gate"] for g in s["gates"]} >= {"discovery", "build"}
    assert all(g["passed"] == 0 for g in s["gates"])  # default-FAIL


def test_render_is_html_and_escapes():
    page = render(status.compute(), "<t>")
    assert page.startswith("<!doctype html>") and "&lt;t&gt;" in page
