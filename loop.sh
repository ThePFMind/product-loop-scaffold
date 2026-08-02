#!/usr/bin/env bash
# Product-loop runner. Attended by default (permission prompts ON).
# Unattended = the Docker-cage trigger. Do not skip permissions on a bare host.
#
#   ./loop.sh research    # researcher sessions until lint green or budget out
#   ./loop.sh analyze     # one analyst session
#   ./loop.sh build       # builder sessions (needs a DEC record)
#   ./loop.sh falsify     # one falsifier session (different model tier)
set -euo pipefail
cd "$(dirname "$0")"
PHASE="${1:-research}"
case "$PHASE" in
  research) PROMPT=prompts/researcher.md; MAX_ITER="${MAX_ITER:-5}" ;;
  analyze)  PROMPT=prompts/analyst.md;    MAX_ITER=1 ;;
  build)    PROMPT=prompts/builder.md;    MAX_ITER="${MAX_ITER:-10}" ;;
  falsify)  PROMPT=prompts/falsifier.md;  MAX_ITER=1 ;;
  *) echo "usage: ./loop.sh research|analyze|build|falsify"; exit 2 ;;
esac
LOG="state/loop.log"; mkdir -p state
i=0
while (( i < MAX_ITER )); do
  i=$((i+1))
  echo "── ${PHASE} ${i}/${MAX_ITER} ── $(date -Is)" | tee -a "$LOG"
  uv run python -m core.journal append loop iteration "{\"phase\":\"${PHASE}\",\"n\":${i}}" >> "$LOG" || true
  claude ${CLAUDE_FLAGS:-} -p "$(cat "$PROMPT")" 2>&1 | tee -a "$LOG" || true
  if uv run python -m core.journal verify && uv run pytest -q; then
    uv run python -m core.journal append loop phase.green "{\"phase\":\"${PHASE}\"}" >> "$LOG"
    echo "chain OK, rules green — gate review is human work (gates/*.md)."
    exit 0
  fi
done
uv run python -m core.journal append loop budget.exhausted "{\"phase\":\"${PHASE}\",\"n\":${MAX_ITER}}" >> "$LOG" || true
echo "budget exhausted — escalate, do not extend."
exit 1
