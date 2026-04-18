# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Hermes worker gateway

- Remote Command-side bridge skill: `skills/hermes-dispatch`
- Remote client script: `skills/hermes-dispatch/scripts/hermes_gateway_client.py`
- Local untracked env file path: `/home/openclaw/.openclaw/workspace/.env.hermes-gateway`
- Gateway URL: `http://100.95.180.106:8788`
- `GET /v1/health` does not require bearer auth, so it is the fastest smoke test from Command.
- Task submission still requires the bearer token from Bot 2's `/home/hermes/worker-gateway/.env`.

## Same-VPS local worker stack

- Local worker agent ids: `marketing`, `development`, `operations`
- Local worker workspaces:
  - `/home/openclaw/.openclaw/workspace-marketing`
  - `/home/openclaw/.openclaw/workspace-development`
  - `/home/openclaw/.openclaw/workspace-operations`
- Local dispatch skill: `skills/hermes-local-dispatch`
- Local dispatch client: `skills/hermes-local-dispatch/scripts/hermes_local_client.py`
- Worker brief reference: `skills/hermes-local-dispatch/references/worker-briefs.md`
- Worker brief schema: `skills/hermes-local-dispatch/references/worker-brief.schema.json`
- Auto-dispatch playbook: `skills/hermes-local-dispatch/references/auto-dispatch-playbook.md`
- Deterministic prepare step: `python3 skills/hermes-local-dispatch/scripts/hermes_local_client.py prepare`
- Direct invoke pattern: `openclaw agent --agent <worker> --message "..." --json`
- Development-only Claude launcher: `scripts/claude-development.sh`
- Development Claude writable home: `/home/openclaw/.openclaw/workspace/.openclaw/claude-development-home`
- `scripts/claude-development.sh auth status` and `scripts/claude-development.sh -p "Reply with exactly: OK"` are the fastest smoke tests.
- Shared project workspace remains: `/home/openclaw/.openclaw/workspace`

## Same-VPS local TaskFlow bridge

- Local TaskFlow route id: `hermes-local-taskflow`
- Local TaskFlow route path: `/plugins/webhooks/hermes-local-taskflow`
- Local TaskFlow URL: `http://127.0.0.1:19000/plugins/webhooks/hermes-local-taskflow`
- Local untracked env file: `/home/openclaw/.openclaw/workspace/.env.hermes-local-taskflow`
- Current bound owner session: `agent:main:telegram:direct:8155333249`
- Controller id: `hermes-local/taskflow`
- Canonical wiring doc: `docs/hermes/HERMES-LOCAL-TASKFLOW-WIRING.md`

## Discord mention troubleshooting

- For reliable bot-to-bot pings in Discord, use raw mention syntax with ids, not plain `@Openclaw X` text.
- Reliable mentions in this server:
  - Openclaw 1: `<@1494663087373160580>`
  - Openclaw 2: `<@1494531954618536007>`
  - Openclaw 3: `<@1494656974732656681>`
- In the `#general` troubleshooting exchange on 2026-04-17, once raw mentions were used in the same message, cross-bot visibility worked as expected.

Add whatever helps you do your job. This is your cheat sheet.
