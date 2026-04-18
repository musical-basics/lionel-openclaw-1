# Claude Code Setup Status

Current machine: `/home/openclaw/.openclaw/workspace`

## Summary

Claude Code is **installed and authenticated**, and there is now **one working execution path** for local worker use on this VPS.

Current state:
- **Installed:** yes
- **Auth state exists:** yes
- **Raw default `claude auth status`:** works
- **Raw default `claude -p ...` inside the OpenClaw sandbox:** still fails with `401`
- **Wrapped development path:** working
- **Development worker using wrapped path:** working
- **OpenClaw ACP runtime spawn to Claude:** still not the primary working path here

## Confirmed working

### 1. Claude binary exists

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude --version
```

Observed result:

```text
2.1.104 (Claude Code)
```

### 2. Claude auth state exists

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude auth status
```

Observed result included:
- `loggedIn: true`
- `authMethod: "claude.ai"`
- `email: "lionel@musicalbasics.com"`
- `subscriptionType: "max"`

### 3. Wrapped Claude path works

Working wrapper:

```bash
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh
```

This wrapper uses a writable custom HOME at:

```bash
/home/openclaw/.openclaw/workspace/.openclaw/claude-development-home
```

Successful smoke test:

```bash
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh -p "Reply with exactly: OK"
```

Observed result:

```text
OK
```

### 4. The local `development` worker can use the wrapper

A real worker handoff was run through the local same-VPS `development` agent, and it successfully executed the wrapper and returned `OK`.

## Confirmed not working

### 1. Raw default Claude print-mode execution in this sandbox

This still fails from the OpenClaw tool environment:

```bash
/home/openclaw/.openclaw/workspace/.npm-global/bin/claude -p "Reply with exactly: OK"
```

Observed result:

```text
Failed to authenticate. API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"Invalid authentication credentials"}...}
```

Important nuance:
- `auth status` can still report `loggedIn: true`
- but real inference can fail in this sandboxed execution context

### 2. Raw default path is not the safe automation path

So on this VPS, the default binary path should **not** be treated as the safe automation entrypoint for worker execution.

## Why the wrapper is needed

The OpenClaw sandboxed tool path on this host does not reliably behave like a normal human SSH shell for Claude's writable state under `/home/openclaw/.claude`.

The wrapper works around that by launching Claude with a writable custom HOME inside the workspace.

## Current safest working path

For Claude-backed local worker automation on this VPS, use:

```bash
/home/openclaw/.openclaw/workspace/scripts/claude-development.sh
```

## Current policy split

Preserve this split unless Lionel changes it:
- `development` uses the Claude wrapper when heavier coding help is needed
- `marketing` stays a normal OpenClaw worker
- `operations` stays a normal OpenClaw worker

## Bottom line

Use this mental model:
- **Setup/auth:** present
- **Raw default Claude in sandbox:** unreliable
- **Development wrapper path:** working
- **Best current execution path:** `scripts/claude-development.sh`
