# lionel-openclaw-1 setup export

This branch is a sanitized export of the current OpenClaw workspace setup.

Included:
- workspace behavior/persona scaffolding
- orchestration draft (`HERMES-ORCHESTRATION-V2.md`)
- Hermes gateway API draft (`HERMES-GATEWAY-API-V1.md`)
- full hybrid deployment runbook (`HERMES-HYBRID-SETUP-RUNBOOK.md`)
- machine-readable interface specs under `specs/`
- worker-gateway deployment artifacts under `deploy/hermes-worker-gateway/`
- Command-side Hermes dispatch skill under `skills/hermes-dispatch/`
- ACP config helpers
- local setup notes

Intentionally omitted:
- `MEMORY.md`
- `USER.md`
- `memory/`
- `.env*` except sanitized examples
- runtime caches/logs/state
- unrelated app project secrets/runtime files

Reason: the live workspace contains personal memory and credentials. Those should not be pushed blindly, even to a repo owned by Lionel.
