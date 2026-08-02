# Product loop — generic self-building scaffold

Input one SEED. The system researches the market, you decide what the
evidence authorizes, the build atom delivers it, feedback flows back in,
and the cycle repeats. A governed graph of three loops around one journal:

    SEED ──> [research loop] ──> evidence + questions
                   ^                    │
                   │                    v
             feedback intake     [analyst] hypotheses (+ kill conditions)
                   ^                    │
                   │                    v
             shipped slice <── [build loop] <── HUMAN DECISION (only gate
                                                that never automates)

## What is autonomous, and what never is
Autonomous between gates: gathering evidence, drafting hypotheses,
building decided slices, disproving everything. Never autonomous:
**deciding what to build** (R14 — decisions are human, journaled, never
defaulted), merging, shipping irreversibles. This is by design, not
timidity: "what the market wants" has no executable rule suite, so an
agent optimizing it would optimize a proxy. Structure is what the machine
enforces — every claim sourced, quoted under 25 words, dated, confidence-
scored, lint-checked; every hypothesis evidence-linked with a kill
condition; every piece of feedback verbatim and immutable.

## Quickstart
    uv sync                        # env from the pinned uv.lock
    git init && git add -A && git commit -m "[state] session 0: product-loop scaffold"
    uv run pytest -q               # all green: machinery + record lint
    # 1. Fill SEED.md (the only required input)
    ./loop.sh research             # evidence accumulates in records/evidence/
    ./loop.sh analyze              # hypotheses drafted for your decision
    # 2. You write records/decisions/DEC-001.md (template in records/templates/)
    ./loop.sh build                # builds ONLY what DEC records authorize
    ./loop.sh falsify              # fresh session, different model tier
    uv run python -m core.intake "raw feedback text" --source "call with Dana"

Unlike the domain skeleton, this scaffold ships all-green: there is no
domain code yet to default-FAIL. The gates (gates/*.md) are where FAIL
lives, and they are checklists the falsifier grades, not tests.

## Layout
    SEED.md                 the input (steward-owned)
    CLAUDE.md               constitution: Law 0, rules 1-14
    records/                evidence, questions, hypotheses, decisions,
                            feedback (verbatim), templates — one writer
                            class per directory
    rules/                  record lint + journal self-tests
    gates/discovery.md      default-FAIL research gate
    gates/build.md          generic build gate (copy per decision)
    prompts/                researcher, analyst, builder, falsifier
    core/                   journal (hash-chained), hashing, intake
    contracts/, modules/    empty by design — the first decision fills them

## Cadence
Research is a rhythm, not a sprint: e.g. weekly `./loop.sh research` plus
one on every new feedback record; analyze when evidence accumulates;
decide at your pace — decisions never default. Unattended runs use the cage: `./cage.sh research` — same image as
`./dev.sh`, skip-permissions legal only inside it.

## Lineage
The build atom's worked example is the loop-engineering ledger skeleton
(REQ-001); the board machinery library (loop-system, Pass 1) wakes on the
triggers annotated there; research rules 11-13 descend from Pass 1's
invariants. Same journal, same Law 0, same physics — this scaffold is the
outer loop the others were always going to get.

## Status & monitor
Status is a query, never a document — derived from journal + gates +
records + git on every call. CLI: `uv run python -m core.status`.
Page: `uv run python -m core.monitor` -> http://127.0.0.1:8322 (separate
port, read-only, recomputed per request, auto-refresh 5s; `/api` = JSON).
Runs fine inside `./dev.sh` with `-p 8322:8322` added to the docker run.

The lens is a governed engine target: agents may improve core/status.py and
core/monitor.py through the normal path (contract-preserving diff, tests,
human approval). The trigger is evidence, not a timer — when the lens meets
truth it doesn't understand (new journal kinds, unparseable gate rows) it
renders a LENS DRIFT band naming its own blind spots; that band IS the
monitor-update task. What no improvement may touch:
rules/test_monitor_contract.py, the steward-owned conformance suite
(derived-only, every gate shown, integrity and drift unsuppressible) — the
unmodifiable part that evaluates the rest.
