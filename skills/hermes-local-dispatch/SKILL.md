---
name: hermes-local-dispatch
description: Delegate specialist work to the 3 local same-VPS Hermes-equivalent workers implemented as isolated OpenClaw agents: marketing, development, and operations. Use when local worker delegation is better than doing the task inline and you want to keep work on this VPS.
metadata: {"openclaw":{"os":["linux"],"requires":{"bins":["python3","openclaw"]}}}
---

# Hermes Local Dispatch

Use this skill when the task should go to the local same-VPS worker trio instead of the remote Bot 2 Hermes gateway.

## Important reality

These are the same 3 worker roles Lionel asked for, but on this VPS they are implemented as **isolated OpenClaw agents**, not the separate remote Hermes CLI.

Worker ids:

- `marketing`
- `development`
- `operations`

## When to use

- The task is handoffable and specialized.
- Keeping work on this VPS is simpler or safer than using the remote worker box.
- You want lower latency and easier debugging.

Do **not** delegate tiny tasks that are faster to do directly unless Lionel explicitly wants the worker path.

## Route selection

- `marketing` for copy, hooks, offers, positioning, launch messaging, landing page structure, and content ideas.
- `development` for coding, debugging, implementation, audits, refactors, technical plans, and verification.
- `operations` for logistics, admin flows, checklists, sequencing, process docs, coordination, and follow-up planning.

## Command examples

List local workers:

```bash
python3 {baseDir}/scripts/hermes_local_client.py list
```

Run a worker task:

```bash
python3 {baseDir}/scripts/hermes_local_client.py run <<'EOF'
{
  "agent": "marketing",
  "objective": "Write 3 concise hero hooks for the masterclass waitlist page.",
  "priority": "high",
  "context": {
    "summary": "Keep it premium, direct, and non-fluffy.",
    "project": "ultimate-pianist-masterclass",
    "notes": ["Do not invent pricing.", "Do not publish anything."]
  },
  "constraints": ["Draft only."],
  "successCriteria": ["Return 3 distinct hooks.", "Keep each hook short."]
}
EOF
```

## Request shape

Expected JSON shape:

```json
{
  "agent": "marketing",
  "objective": "...",
  "priority": "high",
  "context": {
    "summary": "...",
    "project": "...",
    "notes": ["..."]
  },
  "assets": ["..."],
  "constraints": ["..."],
  "successCriteria": ["..."]
}
```

## Output handling

The client returns normalized JSON with:

- `transport`
- `workerAgentId`
- `status`
- `summary`
- `parsed`
- `rawText`
- `runId`
- `sessionId`

Important terminal states:

- `completed`
- `needs_review`
- `blocked`
- `failed`
- `cancelled`

## Safety

- Keep task context minimal and relevant.
- Do not send secrets or unrelated private memory.
- Command still owns judgment.
- Do not claim completion if the worker returned `needs_review`, `blocked`, or `failed`.
