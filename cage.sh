#!/usr/bin/env bash
# ⚠ UNATTENDED MODE. Runs the loop with permission prompts OFF — legal ONLY
# inside this container (repo = only writable host path; no host creds).
# Never pass --dangerously-skip-permissions outside the cage.
# Egress narrowing (per-phase network profiles) is a registered later
# hardening; today the cage isolates filesystem + credentials.
set -euo pipefail
cd "$(dirname "$0")"
PHASE="${1:-}"
IMAGE=product-loop-cage:latest
docker build -q -t "$IMAGE" . >/dev/null
exec docker run --rm \
  -v "$PWD":/work \
  -v product-loop-claude:/home/agent/.claude \
  -e GIT_AUTHOR_NAME -e GIT_AUTHOR_EMAIL -e GIT_COMMITTER_NAME -e GIT_COMMITTER_EMAIL \
  "$IMAGE" bash -lc "uv sync --frozen && CLAUDE_FLAGS=--dangerously-skip-permissions MAX_ITER=\"${MAX_ITER:-10}\" ./loop.sh ${PHASE:-research}"
