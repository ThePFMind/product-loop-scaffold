#!/usr/bin/env bash
# Attended dev shell inside the cage image. Permission prompts stay ON.
set -euo pipefail
cd "$(dirname "$0")"
IMAGE=product-loop-cage:latest
docker build -q -t "$IMAGE" . >/dev/null
exec docker run -it --rm \
  -v "$PWD":/work \
  -v product-loop-claude:/home/agent/.claude \
  -e GIT_AUTHOR_NAME -e GIT_AUTHOR_EMAIL -e GIT_COMMITTER_NAME -e GIT_COMMITTER_EMAIL \
  "$IMAGE" bash -lc "uv sync --frozen && exec bash"
