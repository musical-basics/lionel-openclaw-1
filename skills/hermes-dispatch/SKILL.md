---
name: hermes-dispatch
description: Delegate specialist or longer-running work to the private Hermes worker gateway. Use when the user explicitly asks for Hermes, or asks marketing, development, or operations to take a task, or when a task is cleanly handoffable to one of those three workers.
metadata: {"openclaw":{"os":["linux"],"requires":{"bins":["python3"]}}}
---

# Hermes Dispatch

Use this skill when the user wants work handed to the private Hermes worker box instead of doing it directly in Command.

## Route selection

- `marketing` for copy, messaging, offer framing, hooks, campaign ideas, launch positioning, outreach drafts.
- `development` for coding, debugging, implementation plans, technical audits, refactors, and engineering problem solving.
- `operations` for logistics, admin flows, project tracking, task cleanup, process docs, execution checklists, and coordination.

Do **not** delegate tiny tasks that are faster to do directly unless the user specifically asked for Hermes.

## Required local config

The client script expects a local untracked env file at:

- `/home/openclaw/.openclaw/workspace/.env.hermes-gateway`

Format:

```bash
HERMES_GATEWAY_URL=http://100.95.180.106:8788
HERMES_GATEWAY_TOKEN=...long secret...
```

If the script says config is missing, fix that first.

## Normal workflow

1. Pick the worker.
2. Build a **small, focused JSON task**. Include only the context Hermes actually needs.
3. Call the client script.
4. Summarize the result back to the user.
5. If Hermes returns `blocked`, `needs_review`, or `failed`, surface that honestly with blockers and the recommended next step.

## Request shape

The script auto-fills `schemaVersion`, `command.flowId`, `command.taskId`, `command.requestedAt`, and a default `command.requester.agent = "command"`.

So you can usually send just this shape:

```json
{
  "agent": "marketing",
  "objective": "Write 3 high-converting hooks for the masterclass waitlist page.",
  "priority": "high",
  "context": {
    "summary": "Masterclass launch matters more than polish. Keep it direct and premium.",
    "project": "ultimate-pianist-masterclass",
    "notes": [
      "Do not invent pricing.",
      "Keep the tone concise, not fluffy."
    ]
  },
  "assets": [],
  "constraints": [
    "Do not publish anything.",
    "Return drafts only."
  ],
  "successCriteria": [
    "Return 3 distinct hooks.",
    "Keep each hook short enough for a landing page hero section."
  ],
  "approval": {
    "required": false,
    "kind": null
  }
}
```

## Command examples

For quick jobs that should finish now, use `run --wait`:

```bash
python3 {baseDir}/scripts/hermes_gateway_client.py run --wait <<'EOF'
{
  "agent": "marketing",
  "objective": "Write 3 high-converting hooks for the masterclass waitlist page.",
  "priority": "high",
  "context": {
    "summary": "Masterclass launch matters more than polish. Keep it direct and premium.",
    "project": "ultimate-pianist-masterclass",
    "notes": ["Do not invent pricing.", "Keep the tone concise, not fluffy."]
  },
  "constraints": ["Do not publish anything.", "Return drafts only."],
  "successCriteria": ["Return 3 distinct hooks.", "Keep each hook short enough for a landing page hero section."]
}
EOF
```

For longer jobs, do not block the turn unnecessarily. Submit first, then poll with `process`:

```bash
python3 {baseDir}/scripts/hermes_gateway_client.py submit <<'EOF'
{ ...request json... }
EOF
```

Then use:

```bash
python3 {baseDir}/scripts/hermes_gateway_client.py status <remoteTaskId>
python3 {baseDir}/scripts/hermes_gateway_client.py wait <remoteTaskId> --timeout-seconds 1800
python3 {baseDir}/scripts/hermes_gateway_client.py cancel <remoteTaskId>
```

## Output handling

Important terminal states:

- `completed`
- `needs_review`
- `blocked`
- `failed`
- `cancelled`

When Hermes returns structured result fields like `summary`, `whatIDid`, `blockers`, `needsFromCommand`, or `recommendedNextStep`, use them in your reply instead of paraphrasing away important details.

## Safety

- Do not send secrets or unrelated private memory just because you can.
- Keep task context minimal and relevant.
- Hermes is a worker, not the final authority. Command still owns judgment.
- Do not claim a task is done if Hermes returned `needs_review` or `blocked`.
