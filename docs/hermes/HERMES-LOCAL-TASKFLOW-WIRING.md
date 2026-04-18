# Hermes Local TaskFlow Wiring

## Purpose

This document explains how the **same-VPS local worker stack** was wired into **OpenClaw TaskFlow** on the Command box.

This is the local version of the Hermes orchestration layer.

Important honesty note:
- the local workers are not the separate remote Hermes CLI runtime
- they are **isolated OpenClaw agents** on the same VPS
- TaskFlow is being used as the durable flow ledger above those workers

## What this wiring is for

Without TaskFlow, local worker dispatch is just an ad hoc call like:

```bash
openclaw agent --agent development --message "..." --json
```

That works, but it does **not** give durable orchestration state.

TaskFlow adds:
- flow identity
- owner session binding
- persistent state
- waiting / blocked / finished lifecycle
- a clean place to map worker outcomes back into Command

## Current live state

As of this wiring pass, the following is live on this VPS:

- local workers:
  - `marketing`
  - `development`
  - `operations`
- bundled `webhooks` plugin enabled in OpenClaw
- local TaskFlow webhook route registered
- local `create_flow` smoke test succeeded
- flow appears in `openclaw tasks flow list --json`

## Key files and paths

### Main config

- `/home/openclaw/.openclaw/openclaw.json`

### Local worker dispatch

- `skills/hermes-local-dispatch/SKILL.md`
- `skills/hermes-local-dispatch/scripts/hermes_local_client.py`

### Local TaskFlow route helper env file

- `/home/openclaw/.openclaw/workspace/.env.hermes-local-taskflow`

This file is intended to stay **untracked**.

### Current local TaskFlow webhook route

- route id: `hermes-local-taskflow`
- path: `/plugins/webhooks/hermes-local-taskflow`
- local URL: `http://127.0.0.1:19000/plugins/webhooks/hermes-local-taskflow`
- controller id: `hermes-local/taskflow`

## Architecture

```text
Lionel chat
   |
   v
Command / main OpenClaw agent
   |
   +--> TaskFlow-managed local route
   |      |
   |      +--> create / resume / finish / fail flow
   |
   +--> local worker dispatch
          |
          +--> marketing
          +--> development
          +--> operations
```

## Why the webhooks plugin was used

OpenClaw's bundled `webhooks` plugin exposes a trusted way to drive TaskFlow through authenticated local HTTP.

That gives us a clean bridge for:
- `create_flow`
- `set_waiting`
- `resume_flow`
- `finish_flow`
- `fail_flow`
- `cancel_flow`
- `run_task`

This is a good fit because the local worker bridge is not itself a plugin yet.

## Wiring process

### 1. Keep the local worker trio separate from TaskFlow

First, the same-VPS worker trio was created as isolated agents:

- `marketing`
- `development`
- `operations`

They already work directly through:

```bash
openclaw agent --agent <worker> --message "..." --json
```

This is the execution layer.

TaskFlow is the orchestration layer above it.

### 2. Enable the bundled `webhooks` plugin in `openclaw.json`

The local TaskFlow bridge was enabled under `plugins.entries.webhooks`.

Conceptually, the config looks like this:

```json
{
  "plugins": {
    "entries": {
      "webhooks": {
        "enabled": true,
        "config": {
          "routes": {
            "hermes-local-taskflow": {
              "path": "/plugins/webhooks/hermes-local-taskflow",
              "sessionKey": "agent:main:telegram:direct:8155333249",
              "secret": "REDACTED",
              "controllerId": "hermes-local/taskflow",
              "description": "Local same-VPS TaskFlow bridge for Hermes-equivalent workers"
            }
          }
        }
      }
    }
  }
}
```

### 3. Bind the route to an owner session

The route must be bound to a trusted OpenClaw session key.

The current live binding is:

- `agent:main:telegram:direct:8155333249`

This means flows created through this route are owned by this direct Telegram session.

### 4. Store the route URL and secret in an untracked local env file

A local helper env file was written to:

- `/home/openclaw/.openclaw/workspace/.env.hermes-local-taskflow`

This is the local convenience layer for testing the route.

It contains:

```bash
HERMES_LOCAL_TASKFLOW_URL=http://127.0.0.1:19000/plugins/webhooks/hermes-local-taskflow
HERMES_LOCAL_TASKFLOW_SECRET=...secret...
```

Important note:
- this file should remain untracked
- do not publish the secret

### 5. Restart or reload the gateway so the route actually registers

Critical nuance discovered during setup:

**adding the route to config is not enough by itself**.

The webhook route only becomes reachable after the gateway loads the plugin with the updated config.

Practical takeaway:
- after enabling or changing this route, restart or reload the local gateway
- then verify route registration before assuming it works

### 6. Verify the plugin is loaded and the route is registered

Verification command:

```bash
openclaw plugins inspect webhooks
```

Expected signal:
- plugin status is `loaded`
- diagnostics show the route was registered on `/plugins/webhooks/hermes-local-taskflow`

### 7. Smoke test `create_flow`

A local authenticated POST was sent to the route with:

```json
{
  "action": "create_flow",
  "goal": "smoke test local TaskFlow bridge",
  "status": "queued",
  "notifyPolicy": "done_only"
}
```

This succeeded and returned a managed flow.

### 8. Verify the created flow in TaskFlow CLI

Verification command:

```bash
openclaw tasks flow list --json
```

Observed result:
- managed flow exists
- controller id is `hermes-local/taskflow`
- owner is the Telegram direct session
- goal is `smoke test local TaskFlow bridge`

## Current proof that wiring works

The local TaskFlow bridge has already passed this minimum proof:

1. route loaded
2. route authenticated successfully
3. `create_flow` returned `ok: true`
4. flow became visible in `openclaw tasks flow list --json`

So the TaskFlow bridge is not hypothetical. It is live.

## What is wired now vs not wired yet

### Wired now

- local worker trio exists
- local TaskFlow route exists
- authenticated `create_flow` works
- flow inspection works

### Not wired yet

The full automatic worker lifecycle has **not** been connected yet.

Still missing:
- create a flow automatically when Command decides to delegate
- dispatch the local worker run under that flow
- map worker result back into TaskFlow mutation calls
- optionally emit waiting state for review/approval cases
- finish or fail the flow based on worker result

## Recommended result mapping

When the local worker returns a normalized status, map it like this:

### `completed`
- call `finish_flow`
- store result summary in `stateJson`

### `needs_review`
- usually call `set_waiting`
- include structured review reason in `waitJson` or `stateJson`

### `blocked`
- either call `set_waiting` if human input can unblock it
- or call `fail_flow` if it is a real failure condition

### `failed`
- call `fail_flow`
- include `blockedSummary` and any useful result detail

### `cancelled`
- call `cancel_flow` or mark cancellation intent appropriately

## Recommended next implementation shape

The clean next step is a small local bridge wrapper that does this sequence:

1. receive structured delegation request
2. call TaskFlow `create_flow`
3. call local worker dispatch
4. inspect normalized worker result
5. call one of:
   - `finish_flow`
   - `set_waiting`
   - `fail_flow`
6. return both:
   - worker result
   - flow id

That will give Command a durable flow id for every delegated local worker job.

## Current footguns / caveats

### Session binding is currently specific

Right now the route is bound to this exact owner session:

- `agent:main:telegram:direct:8155333249`

That is fine for the current direct-chat workflow, but it is a little brittle.

Long-term cleaner option:
- bind to a more stable owner session if this system needs to outlive one chat thread or be shared across entry points

### Secret handling should be hardened later

The fast bootstrap path used a working route secret so the bridge could be proven quickly.

Long-term improvement:
- move the route secret out of inline config and into a secret reference or file-backed path

### Webhook route is local infrastructure, not user-facing behavior

This route is an internal bridge for TaskFlow orchestration.
It is not the final user routing layer by itself.

## Example verification commands

Inspect plugin:

```bash
openclaw plugins inspect webhooks
```

List flows:

```bash
openclaw tasks flow list --json
```

Show one flow:

```bash
openclaw tasks flow show <flow-id>
```

## Example local route smoke test

```bash
python3 - <<'PY'
import json, urllib.request
url = 'http://127.0.0.1:19000/plugins/webhooks/hermes-local-taskflow'
secret = 'REDACTED'
payload = {
    'action': 'create_flow',
    'goal': 'smoke test local TaskFlow bridge',
    'status': 'queued',
    'notifyPolicy': 'done_only',
}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {secret}',
    },
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as r:
    print(r.read().decode())
PY
```

## Bottom line

The local same-VPS worker stack now has a real TaskFlow entry point.

What exists now is:
- durable flow creation
- session-bound ownership
- flow inspection through CLI
- a clear path to wrap local worker dispatch with TaskFlow lifecycle updates

What remains is the final automation layer that makes Command use that lifecycle by default.
