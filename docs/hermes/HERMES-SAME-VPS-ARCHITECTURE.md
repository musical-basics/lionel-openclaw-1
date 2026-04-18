# HERMES Same-VPS Architecture

## What is live now

Lionel asked for the same 3 Hermes worker roles on the **same VPS as Command/OpenClaw**, while leaving the remote Bot 2 setup untouched.

That is now live here as a **same-role local implementation**:

- `marketing`
- `development`
- `operations`

Important honesty note: on this VPS, these workers are implemented as **isolated OpenClaw agents**, not the separate remote Hermes CLI runtime. Functionally, this gives the same 3-worker split with less infrastructure overhead on the local box.

## Why this is better on the same VPS

Compared with the hybrid remote worker gateway, the local version is simpler because it removes:

- Tailscale hop
- remote bearer token dependency
- remote systemd service dependency
- cross-VPS debugging friction
- remote auth drift

So for fast iteration, the same-VPS model is better.

## Live topology

```text
Lionel chat
   |
   v
Command / main OpenClaw agent
   |
   +--> local worker agent: marketing
   |
   +--> local worker agent: development
   |
   +--> local worker agent: operations

Shared project files:
/home/openclaw/.openclaw/workspace
```

## Worker boundaries

Each worker has its own isolated OpenClaw agent identity, workspace, and state.

### Agent ids

- `marketing`
- `development`
- `operations`

### Workspaces

- `/home/openclaw/.openclaw/workspace-marketing`
- `/home/openclaw/.openclaw/workspace-development`
- `/home/openclaw/.openclaw/workspace-operations`

### Agent state dirs

- `/home/openclaw/.openclaw/agents/marketing/agent`
- `/home/openclaw/.openclaw/agents/development/agent`
- `/home/openclaw/.openclaw/agents/operations/agent`

## Shared-workspace model

The worker-specific workspaces mainly hold persona and worker-local instructions.

Real project work should usually happen in the shared main workspace:

- `/home/openclaw/.openclaw/workspace`

This keeps the mental model simple:

- worker workspace = who the worker is
- main workspace = where the project files usually live

## Worker roles

### marketing
Use for:
- offer framing
- hooks and copy
- landing page structure
- launch messaging
- content angles

### development
Use for:
- coding
- debugging
- implementation
- architecture
- verification

### operations
Use for:
- task sequencing
- logistics
- checklists
- follow-up planning
- process docs
- execution tracking

## Dispatch path

Local dispatch now goes through OpenClaw itself:

```bash
openclaw agent --agent marketing --message "..." --json
openclaw agent --agent development --message "..." --json
openclaw agent --agent operations --message "..." --json
```

A local wrapper skill/client was added in the main workspace:

- `skills/hermes-local-dispatch/SKILL.md`
- `skills/hermes-local-dispatch/scripts/hermes_local_client.py`

## Verification completed

All 3 local workers were invoked successfully through the real OpenClaw agent path on this VPS:

- `marketing` returned `STATUS: completed`
- `development` returned `STATUS: completed`
- `operations` returned `STATUS: completed`

## What stays untouched

The remote Bot 2 Hermes worker gateway remains intact and separate.

That means there are now effectively **two worker stacks**:

1. **Local same-VPS worker stack** on this Command box, now preferred for fast local delegation
2. **Remote Bot 2 Hermes worker stack** on the other VPS, left unchanged for separate management

## Recommended usage rule

For now:

- use **local workers first** when the work can stay on this VPS
- use the **remote Bot 2 stack only when there is a specific reason** to involve that box

## Limitations of same-VPS mode

This model is simpler, but it does reduce isolation compared with separate-VPS workers:

- same host resources
- same OpenClaw installation
- less fault isolation
- less clean separation if you want truly independent worker runtime environments

For Lionel's current speed and simplicity goal, that tradeoff is worth it.

## Best next layer

The next clean improvement is:

1. keep these 3 local workers as the default specialist layer
2. add TaskFlow-owned dispatch/resume on top
3. keep the remote Bot 2 gateway as optional overflow or separate-environment workers

For the TaskFlow bridge wiring details, see:

- `docs/hermes/HERMES-LOCAL-TASKFLOW-WIRING.md`
