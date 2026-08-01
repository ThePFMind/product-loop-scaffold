# Gate: build (per decided slice)

Steward-owned. Default FAIL. Copy this file to gates/build-<DEC-id>.md when
a decision authorizes a slice; the loop-engineering skeleton gate is the
worked example of this pattern.

| # | Criterion | State | Evidence |
|---|-----------|-------|----------|
| B1 | The slice traces to a decision record (DEC-…) and its hypothesis | FAIL | |
| B2 | A contract for the slice exists in contracts/ with an executable rule suite (property-form where the domain allows) | FAIL | |
| B3 | Rules execute and pass: `pytest -q` green | FAIL | |
| B4 | Every runtime write in the journal; `python -m core.journal verify` OK; replay reconstructs state | FAIL | |
| B5 | Falsifier (fresh session, read-only, different model tier than the builder) refuses one seeded defect and names it | FAIL | |
| B6 | Every merge human-approved (journal shows `human` approval per merge) | FAIL | |
| B7 | The shipped slice's success signal (from SEED + the decision's falsifier) is measurable and its intake path works: `python -m core.intake` round-trips | FAIL | |
| B8 | Build budget respected: ≤ 10 sessions (owner may amend); breach reopens the decision | FAIL | |

B7 is what closes the outer loop: a slice that ships without a feedback
path is a hypothesis you chose not to test.
