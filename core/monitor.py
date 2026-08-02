"""Status monitor page — separate port, read-only, stateless.

Every request recomputes core.status.compute(); the page holds no state and
accepts only GET. Bind is 127.0.0.1 — this is a dev lens, not a service.

  uv run python -m core.monitor            # http://127.0.0.1:8321
  uv run python -m core.monitor --port 9000
"""
from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core import status

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>{title} — status</title><style>
body{{font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;background:#111;
color:#ddd;max-width:860px;margin:2rem auto;padding:0 1rem}}
h1{{font-size:16px;color:#fff}} section{{margin:1.2rem 0}}
.band{{color:#888;letter-spacing:.08em;font-size:11px}}
.pill{{display:inline-block;padding:1px 8px;border-radius:9px;font-size:12px;
margin-right:6px}} .ok{{background:#123c1e;color:#7fd98f}}
.bad{{background:#3c1212;color:#e08a8a}} .warn{{background:#3a2f10;color:#e0c76a}}
table{{border-collapse:collapse;width:100%}} td,th{{padding:2px 8px;text-align:left;
border-bottom:1px solid #222;font-size:13px}} .dim{{color:#777}}
</style></head><body>
<h1>{title} <span class="dim">· derived per request · read-only</span></h1>
<section><div class="band">NEEDS YOU</div>{needs}</section>
<section><div class="band">GATES</div>{gates}</section>
<section><div class="band">SESSIONS</div><p>{sessions}</p></section>
{drift}
{blocked}
<section><div class="band">INTEGRITY</div><p>{integrity}</p>{contracts}</section>
<section><div class="band">RECENT</div>{recent}</section>
</body></html>"""


def render(s: dict, title: str) -> str:
    needs = ("".join(f"<p class='pill warn'>{html.escape(n)}</p>"
                     for n in s["needs_you"])
             or "<p class='pill ok'>nothing — loops may run</p>")
    gates_html = ""
    for g in s["gates"]:
        rows = "".join(
            f"<tr><td>{r['id']}</td><td>{html.escape(r['criterion'])}</td>"
            f"<td><span class='pill {'ok' if r['state'] == 'PASS' else 'bad'}'>"
            f"{r['state']}</span></td></tr>" for r in g["rows"])
        gates_html += (f"<p>{html.escape(g['gate'])} — {g['passed']}/{g['total']} PASS</p>"
                       f"<table>{rows}</table>")
    sessions = " · ".join(f"{html.escape(k)}: {v}"
                          for k, v in s["sessions"].items()) or "none yet"
    if s["phase"]:
        sessions += f" · phase: {html.escape(str(s['phase']))}"
    d = s["drift"]
    drift = ""
    if d["unknown_kinds"] or d["unparsed_gate_rows"]:
        bits = "".join(f"<p class='pill warn'>kind not understood: {html.escape(k)}</p>"
                       for k in d["unknown_kinds"])
        if d["unparsed_gate_rows"]:
            bits += f"<p class='pill warn'>{d['unparsed_gate_rows']} gate row(s) unparsed</p>"
        drift = ("<section><div class='band'>LENS DRIFT — monitor-update task"
                 "</div>" + bits + "</section>")
    blocked = ""
    if s["blocked"]:
        items = "".join(f"<p class='pill bad'>{html.escape(b['record'])} on "
                        f"{html.escape(b['on'])}</p>" for b in s["blocked"])
        blocked = f"<section><div class='band'>BLOCKED</div>{items}</section>"
    i = s["integrity"]
    chain = ("<span class='pill ok'>chain OK</span>" if i["chain_ok"]
             else "<span class='pill bad'>chain BROKEN</span>")
    integrity = (f"{chain} {i['journal_events']} events · "
                 f"{html.escape(i['git'])}")
    contracts = "".join(f"<p class='dim'>{html.escape(c['file'])} "
                        f"{c['sha256']}</p>" for c in i["contracts"])
    recent = "<table>" + "".join(
        f"<tr><td class='dim'>{html.escape(e['ts'])}</td>"
        f"<td>{html.escape(e['actor'])}</td>"
        f"<td>{html.escape(e['kind'])}</td></tr>"
        for e in reversed(s["recent"])) + "</table>"
    return PAGE.format(title=html.escape(title), needs=needs, gates=gates_html,
                       sessions=sessions, drift=drift, blocked=blocked,
                       integrity=integrity, contracts=contracts, recent=recent)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8322)
    ap.add_argument("--title", default=status.ROOT.name)
    a = ap.parse_args()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            s = status.compute()
            if self.path.startswith("/api"):
                body = json.dumps(s, default=str).encode()
                ctype = "application/json"
            else:
                body = render(s, a.title).encode()
                ctype = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # quiet
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"monitor: http://127.0.0.1:{a.port}  (read-only, derived per request)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
