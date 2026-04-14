# Claude Code Setup Status

Current machine: `/home/openclaw/.openclaw/workspace`

## Summary

Claude Code is **installed and authenticated**, but execution is only **partially working** right now.

The short version:
- **Installed:** yes
- **Authenticated:** yes
- **Raw `claude -p ...` execution:** **not working reliably** on this host right now
- **Direct `acpx -> claude` execution with local override config:** **working in specific contexts**
- **OpenClaw `sessions_spawn(runtime: "acp")` with `agentId: "claude"`:** **not working**

## Confirmed working

### 1. Claude binary exists

Path:

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude
```

Version check works:

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude --version
```

Observed result:

```text
2.1.104 (Claude Code)
```

### 2. Claude auth is valid

Command:

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude auth status
```

Observed result:
- logged in: `true`
- auth method: `claude.ai`
- email: `lionel@musicalbasics.com`
- subscription: `max`

### 3. `acpx` can talk to Claude when launched from the workspace root with a local override

This currently works from:

```bash
/home/openclaw/.openclaw/workspace
```

using the workspace-level config file:

```bash
/home/openclaw/.openclaw/workspace/.acpxrc.json
```

Current override:

```json
{
  "agents": {
    "claude": {
      "command": "env PATH=/home/openclaw/.openclaw/workspace/.npm-global/bin:/usr/bin:/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/snap/bin npm_config_cache=/home/openclaw/.openclaw/workspace/.npm-cache TMPDIR=/home/openclaw/.openclaw/workspace/.npm-tmp /usr/bin/npx -y @zed-industries/claude-agent-acp@0.21.0"
    }
  }
}
```

Smoke test that worked:

```bash
node /usr/lib/node_modules/openclaw/node_modules/acpx/dist/cli.js \
  --approve-all --timeout 120 --format quiet claude exec 'Reply with exactly ACPX_OK'
```

Observed result:

```text
ACPX_OK
```

## Confirmed not working

### 1. Raw Claude print-mode execution currently fails

This failed:

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude -p --model sonnet --effort high --no-session-persistence "Reply with exactly DIRECT_OK"
```

Observed error:

```text
API Error: EROFS: read-only file system, open '/home/openclaw/.claude.json'
```

This means:
- Claude is authenticated
- but a normal non-interactive execution still tries to write under `/home/openclaw/`
- that write path is read-only in this environment

So right now, **direct raw Claude execution is not a reliable default on this host**.

### 2. OpenClaw ACP session spawn still fails

This is still failing:

- `sessions_spawn({ runtime: "acp", agentId: "claude", ... })`

Observed error:

```text
spawn_failed: ACP connection closed
```

So even though Claude itself is installed and authenticated, the **OpenClaw ACP bridge path is still broken**.

### 3. `acpx` fails when run from repo directories that do not have the local override config

Example failure mode from repo cwd:
- `npx` tries to use `/home/openclaw/.npm/...`
- that path is read-only
- adapter bootstrap fails before Claude starts

So `acpx` is **not globally fixed** right now. It only works where the needed cache/path override config is actually loaded.

## Known causes

### 1. Wrong agent id was part of the problem earlier

Correct ACP/acpx harness id is:

```text
claude
```

Not:

```text
claude-code
```

### 2. Non-interactive PATH does not naturally expose the Claude binary

Required binary directory:

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin
```

Interactive shells may see it, but service-like or tool-launched processes may not.

### 3. Read-only home paths break both Claude and `npx`

Observed breakpoints:
- `/home/openclaw/.claude.json`
- `/home/openclaw/.npm/...`

That is why extra cache/path overrides were needed for `acpx`.

## What is currently the safest working execution path

If Claude Code must be used right now on this machine, the most reliable currently-tested path is:

- launch through local `acpx`
- from a cwd that loads a working `.acpxrc.json`
- with explicit cache/path overrides

## Preferred model defaults

Per Lionel's preference, Claude runs should default to:

```text
--model sonnet --effort high
```

## What still needs fixing

### To make raw `claude -p` usable
Need a supported way for Claude to avoid writing to the read-only `/home/openclaw/.claude.json` path, or a writable home/config path for the process.

### To make `acpx` usable everywhere
Need one of these:
- a writable global `~/.acpx/config.json`, or
- a reusable wrapper script, or
- per-project `.acpxrc.json` files that are intentionally managed

### To make OpenClaw ACP spawns usable
Need to fix the OpenClaw ACP bridge path that is still closing immediately even after adapter/path/cache fixes.

## Practical recommendation right now

### Use this mental model
- **Setup/auth status:** good
- **Raw direct execution:** blocked by read-only Claude config write path
- **Local `acpx` execution:** works if launched from a cwd with the right override config
- **OpenClaw ACP spawn:** still broken

### Best next hardening step
Create one reusable local wrapper for Claude execution so future Claude runs do not depend on ad hoc cwd-specific config.
