#!/usr/bin/env bash
set -euo pipefail

CLAUDE_BIN="/home/openclaw/.openclaw/workspace/.npm-global/bin/claude"
REAL_HOME="/home/openclaw"
CUSTOM_HOME="/home/openclaw/.openclaw/workspace/.openclaw/claude-development-home"

mkdir -p \
  "$CUSTOM_HOME/.claude" \
  "$CUSTOM_HOME/.config" \
  "$CUSTOM_HOME/.cache" \
  "$CUSTOM_HOME/.local/state"

python3 - <<'PY'
import json
from pathlib import Path

real_home = Path('/home/openclaw')
custom_home = Path('/home/openclaw/.openclaw/workspace/.openclaw/claude-development-home')
(custom_home / '.claude').mkdir(parents=True, exist_ok=True)

cred_src = real_home / '.claude' / '.credentials.json'
cred_dst = custom_home / '.claude' / '.credentials.json'
if cred_src.exists() and not cred_dst.exists():
    cred_dst.write_text(cred_src.read_text())

state_src = real_home / '.claude.json'
state_dst = custom_home / '.claude.json'
state = {}
if state_dst.exists():
    try:
        state = json.loads(state_dst.read_text())
    except Exception:
        state = {}
elif state_src.exists():
    state = json.loads(state_src.read_text())

state['theme'] = state.get('theme') or 'dark'
state['hasCompletedOnboarding'] = True
state_dst.write_text(json.dumps(state, indent=2) + '\n')
PY

export HOME="$CUSTOM_HOME"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_STATE_HOME="$HOME/.local/state"

exec "$CLAUDE_BIN" "$@"
