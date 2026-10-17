#!/bin/bash
# Production launcher: policy remains disabled; reviews use inline packets only.
set -euo pipefail
umask 077
cd /home/hei/.local/share/rel301m-aris-setup/sandbox
export CLAUDE_BIN=/home/hei/.local/share/rel301m-aris-setup/claude-review-guard.py
export CLAUDE_REVIEW_TOOLS=
export CLAUDE_REVIEW_MODEL=sonnet
export CLAUDE_REVIEW_STATE_DIR=/home/hei/.local/share/rel301m-aris-setup/state
export CLAUDE_REVIEW_DEBUG_LOG=/dev/null
exec /home/hei/.cache/rel301m-conda311/bin/python /home/hei/.local/share/rel301m-aris-runtime/mcp-servers/claude-review/server.py
