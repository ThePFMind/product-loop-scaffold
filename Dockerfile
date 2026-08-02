# One image, two modes: dev.sh (attended shell, prompts ON) and cage.sh
# (unattended, skip-permissions INSIDE this boundary only).
# Cage properties: repo bind-mount is the only writable host path; non-root;
# no host credentials or SSH agent; uv pinned (R5).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      git nodejs npm ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "uv==0.11.7" \
 && npm install -g @anthropic-ai/claude-code
RUN useradd -m agent
USER agent
WORKDIR /work
# Deps come from the bind-mounted repo's uv.lock at start (uv sync --frozen),
# so the repo stays the single source of truth and the image stays generic.
CMD ["bash"]
