# Hermes Hybrid Setup Runbook

Status: live partial setup
Owner: Lionel
Updated: 2026-04-16

## Goal

Stand up a hybrid orchestration system where:

- **Command / OpenClaw** runs on one VPS and owns context, memory, routing, approvals, and eventually TaskFlow state.
- **Hermes workers** run on a separate VPS behind one internal HTTP gateway.
- Communication between them happens over **Tailscale-only HTTP**.

## Current architecture

### VPS A: Command

Responsibilities:
- Telegram interface with Lionel
- long-term memory via `memory-core`
- semantic memory search via OpenAI embeddings
- orchestration logic
- future TaskFlow control plane

Current state:
- live and working
- semantic memory is enabled and verified
- command-side bridge code now exists as a workspace skill + local client script
- live health checks to the Hermes worker gateway from Command are verified
- full task submission from Command is still pending local bearer-token wiring

### VPS B: Hermes worker box

Public IP:
- `5.161.102.170`

Tailscale:
- hostname: `ubuntu-4gb-ash-2`
- Tailscale IP: `100.95.180.106`

Current roles on the box:
- existing live Discord Hermes bot, left untouched
- new parallel worker gateway for `marketing`, `development`, and `operations`

## What was already on Bot 2 before changes

The server already had a live Hermes install:

- systemd service: `hermes-gateway.service`
- runs as user: `hermes`
- working directory: `/home/hermes`
- launch command: `/home/hermes/.local/bin/hermes gateway run`
- Hermes code/config root: `/home/hermes/.hermes`

Important note:
The original service is a **Discord bot gateway**, not the new worker gateway design.
That is why the new worker gateway was added **alongside** it instead of replacing it immediately.

## What I changed

## 1. Verified SSH access

Working server credentials were verified for Bot 2.

Result:
- SSH access works to `root@5.161.102.170`

## 2. Installed and connected Tailscale

Installed Tailscale and enabled `tailscaled`.
Then authenticated the node into Lionel's tailnet.

Result:
- Bot 2 can now be reached internally at `100.95.180.106`
- current OpenClaw host can ping it over Tailscale

Why this matters:
- this removes the need for public worker APIs
- it lets the Hermes gateway bind privately on the tailnet

## 3. Created 3 isolated Hermes worker profiles

Created Hermes profiles cloned from the existing Hermes install:

- `marketing`
- `development`
- `operations`

Command used conceptually:

```bash
hermes profile create --clone marketing
hermes profile create --clone development
hermes profile create --clone operations
```

Profile directories:

```text
/home/hermes/.hermes/profiles/marketing
/home/hermes/.hermes/profiles/development
/home/hermes/.hermes/profiles/operations
```

Each profile got:
- its own workspace
- its own logs/sessions/memories/plans dirs
- its own config.yaml and SOUL.md

## 4. Copied existing Hermes auth into the worker profiles

Problem found:
- new cloned profiles did **not** automatically inherit working Codex auth
- test call returned: `No Codex credentials stored`

Fix applied:
- copied the existing authenticated `auth.json` into each worker profile

Source auth store:

```text
/home/hermes/.hermes/auth.json
```

Result:
- the worker profiles can actually execute `hermes chat -Q -q ...`

## 5. Replaced cloned personality files with worker-specific roles

The cloned profiles inherited the original display/personality defaults, including a kawaii-style display personality.
That is wrong for worker execution.

I replaced each worker profile's `SOUL.md` with a stricter domain-specific version:

- `marketing.SOUL.md`
- `development.SOUL.md`
- `operations.SOUL.md`

Behavior enforced:
- no chit-chat before `STATUS:`
- stay in domain
- do not publish/send
- do not touch prohibited systems
- return structured worker output only

I also changed the cloned config display personality from `kawaii` to `concise` in each worker profile config.

## 6. Deployed a parallel Hermes worker gateway service

New deployment path on Bot 2:

```text
/home/hermes/worker-gateway
```

Main files:

```text
/home/hermes/worker-gateway/worker_gateway.py
/home/hermes/worker-gateway/.env
/etc/systemd/system/hermes-worker-gateway.service
```

Systemd service:
- `hermes-worker-gateway.service`

Runs as:
- user `hermes`

Launches:

```text
/usr/bin/python3 /home/hermes/worker-gateway/worker_gateway.py
```

This service was added **without stopping or modifying** the live Discord bot service.

## Worker gateway behavior

The new worker gateway:
- binds to the box's Tailscale IPv4 automatically
- uses bearer auth from its `.env`
- routes tasks to one of the 3 Hermes worker profiles
- persists task state in a local JSON file
- supports async polling now
- has callback scaffolding for later Command integration

Task state path:

```text
/home/hermes/worker-gateway/state/tasks.json
```

## Live gateway API

Bound address:

```text
http://100.95.180.106:8788
```

Live endpoints:

- `GET /v1/health`
- `POST /v1/tasks`
- `GET /v1/tasks/{id}`
- `POST /v1/tasks/{id}/cancel`

Contract docs:
- `docs/hermes/HERMES-GATEWAY-API-V1.md`
- `plans/hermes/hermes-gateway-v1.openapi.yaml`
- `plans/hermes/hermes-task.v1.schema.json`

## End-to-end verification performed

The new gateway was tested from the OpenClaw host over Tailscale.

Verified:
- health endpoint returns all 3 workers ready
- task creation works with bearer auth
- polling works
- sample marketing task ran through the `marketing` profile successfully
- structured output was returned with `needs_review`

So this is not just design work.
The worker gateway is **actually live and responding**.

## Command-side bridge status

A first Command-side bridge now exists in the OpenClaw workspace:

- skill: `skills/hermes-dispatch/SKILL.md`
- client: `skills/hermes-dispatch/scripts/hermes_gateway_client.py`

What it does now:
- teaches Command when to hand work to `marketing`, `development`, or `operations`
- provides a reusable local client for `health`, `submit`, `run`, `status`, `wait`, and `cancel`
- auto-fills `schemaVersion`, `flowId`, `taskId`, and request metadata for normal dispatches
- supports local untracked config via `/home/openclaw/.openclaw/workspace/.env.hermes-gateway`

What was verified:
- the skill loads in OpenClaw as `hermes-dispatch`
- the client script passes Python compile checks
- `health` works live from Command to `http://100.95.180.106:8788` and reports all 3 workers ready

What is still blocked:
- full submit/run testing from Command still needs the bearer token copied locally into the untracked env file
- automatic TaskFlow-backed flow ownership is not added yet

## Files added locally in this repo

Reference docs:
- `docs/hermes/HERMES-ORCHESTRATION-V2.md`
- `docs/hermes/HERMES-GATEWAY-API-V1.md`
- `docs/hermes/HERMES-HYBRID-SETUP-RUNBOOK.md`

Machine-readable specs:
- `plans/hermes/hermes-gateway-v1.openapi.yaml`
- `plans/hermes/hermes-task.v1.schema.json`

Deployment artifacts:
- `deploy/hermes-worker-gateway/worker_gateway.py`
- `deploy/hermes-worker-gateway/hermes-worker-gateway.service`
- `deploy/hermes-worker-gateway/marketing.SOUL.md`
- `deploy/hermes-worker-gateway/development.SOUL.md`
- `deploy/hermes-worker-gateway/operations.SOUL.md`
- `deploy/hermes-worker-gateway/.env.example`

Command-side bridge artifacts:
- `skills/hermes-dispatch/SKILL.md`
- `skills/hermes-dispatch/scripts/hermes_gateway_client.py`

## Operational commands

### On Bot 2

Check worker gateway:

```bash
systemctl status hermes-worker-gateway.service
journalctl -u hermes-worker-gateway.service -n 100 --no-pager
```

Check original Discord bot:

```bash
systemctl status hermes-gateway.service
journalctl -u hermes-gateway.service -n 100 --no-pager
```

Check Tailscale:

```bash
tailscale status
tailscale ip -4
```

### From Command/OpenClaw host

Health check example:

```bash
curl -H "Authorization: Bearer <TOKEN>" http://100.95.180.106:8788/v1/health
```

Create task example:

```bash
curl -X POST http://100.95.180.106:8788/v1/tasks \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d @task.json
```

## What is still missing

The worker side is ready, but the full system is **not complete yet**.

Missing piece:
- **Command/OpenClaw is not yet automatically wired to dispatch normal user tasks into Hermes**

What still needs to be built on the Command side:
1. Command-side Hermes client wrapper
2. TaskFlow-managed dispatch lifecycle
3. callback receiver or polling bridge
4. routing rules from Command to `marketing` / `development` / `operations`
5. approval-state handling on Command side

## Recommended next step

Build the **Command → Hermes bridge** now.

That means:
- create one local integration point on the OpenClaw side
- send structured task payloads to `http://100.95.180.106:8788`
- persist mapping between `flowId/taskId` and `remoteTaskId`
- then return Hermes results back into TaskFlow / user-facing updates

## Safety notes

- The live Discord Hermes bot was intentionally left alone.
- The new worker gateway was added in parallel for low-risk rollout.
- Secrets are not included in this repo export.
- Raw local workspace history is still not safe to publish directly because local git history contains private memory and runtime state.

## Git publishing note

This setup should be pushed via the **sanitized export branch**, not raw local `master`, unless Lionel explicitly wants the full private workspace history published.
