# Gate: discovery (per cycle)

Steward-owned. Default FAIL (R8); only falsifier-verified evidence flips a
row. This gate stands between research and any build decision.

| # | Criterion | State | Evidence |
|---|-----------|-------|----------|
| D1 | Every open SEED/records question has ≥2 independent-source evidence records, or an explicit dead-end note | FAIL | |
| D2 | Existing alternatives mapped: who solves this today, what their users complain about, what people pay (evidence-backed) | FAIL | |
| D3 | Every proposed hypothesis links evidence AND states a kill condition | FAIL | |
| D4 | Contradiction sought: each hypothesis has at least one contra-evidence record, or a journaled note that a genuine search found none | FAIL | |
| D5 | All records pass lint (`pytest -q rules/test_records_lint.py`) | FAIL | |
| D6 | Human decision recorded (build/park/kill) for every hypothesis leaving `proposed`; no decision defaulted or agent-made | FAIL | |
| D7 | Research budget respected: ≤ 5 researcher sessions this cycle (journal count); breach escalates, does not extend | FAIL | |

A hypothesis whose kill condition later fires is journaled `hypothesis.killed`
and its decision superseded — killing is a normal outcome, not a failure.
