# Auto-Dispatch Playbook

Use this reference when turning a normal Lionel request into a validated local worker brief.

## Goal

The main assistant should be able to take a normal request like:

- `fix this bug`
- `write the landing page copy`
- `turn this into a checklist`

and convert it into a rich worker brief **without requiring a separate extra worker-generation pass**.

That means:
- inline synthesis in Command
- deterministic validation in the local client
- then normal worker dispatch

## Core rule

Do **not** treat auto-dispatch as raw parsing.

It should be:
1. infer the likely worker
2. synthesize a concise structured brief from user intent + known business context
3. validate/normalize the brief deterministically
4. dispatch to the worker

## No extra generation pass

Preferred pattern:
- the main assistant synthesizes the brief during the normal conversation turn
- then calls:

```bash
python3 {baseDir}/scripts/hermes_local_client.py prepare
```

- if the normalized brief looks correct, call:

```bash
python3 {baseDir}/scripts/hermes_local_client.py run
```

Do **not** add a second dedicated LLM call just to rewrite the prompt unless there is a compelling reason.

## Worker selection heuristics

### `marketing`
Choose when the main output is:
- copy
- hooks
- landing page structure
- offer/message framing
- positioning
- audience-facing messaging

### `development`
Choose when the main output is:
- code changes
- debugging
- implementation
- root cause analysis
- technical audit
- refactor recommendation

### `operations`
Choose when the main output is:
- checklist
- sequence
- owner map
- logistics
- follow-up plan
- prioritization
- execution clarity

## Brief synthesis checklist

Before dispatch, try to fill these fields:

- `agent`
- `objective`
- `deliverable`
- `priority`
- `businessContext`
- `context.summary`
- `context.project`
- `context.background`
- `context.decisionContext`
- `context.notes`
- `files`
- `constraints`
- `successCriteria`
- `nonGoals`
- `requiredOutput`
- `questionsToAnswer`

Not every field must be present, but the brief should be strong enough that the worker does not need to guess the core assignment.

## Where the implied context comes from

Use:
- the user’s current message
- recent explicit conversation context
- stable business rules already known in workspace context
- project-specific rules already documented in memory or local notes

Do **not** dump raw memory into the worker brief.

Condense it.

## Good synthesis style

### Good
- short objective
- clear deliverable
- explicit business reason
- explicit guardrails
- explicit success criteria

### Bad
- pasting the whole conversation
- over-explaining background that does not affect execution
- vague goals like `help with this`
- omitting known business constraints

## DreamPlay-specific guardrails to include when relevant

Include when relevant to product or merchandising work:

- DreamPlay One and DreamPlay Pro must stay clearly distinct.
- Gold is Pro-only.
- Prefer the smallest safe fix first for obvious regressions.

Include when relevant to launch priorities:

- Masterclass revenue is the current priority over extra polish.
- Lionel prefers one concrete next step at a time.
- Responses should be short, direct, and practical.

## When to ask a follow-up question first

Ask before dispatch only if the missing information is material.

Examples where follow-up is justified:
- unclear target repo or file set for a code task
- unclear deliverable that changes the nature of the work
- external action risk
- ambiguous route between workers that would cause bad work

Do **not** ask follow-up for trivial missing details when a reasonable assumption is safe.

## Automatic dispatch workflow

1. Decide whether the task should be delegated at all.
2. Select the worker.
3. Synthesize a structured brief.
4. Run `prepare` to validate and inspect the resolved brief.
5. Run `run` with the structured brief.
6. Return the worker result clearly.
7. If later TaskFlow is layered on top, wrap steps 4-6 in the flow lifecycle.

## Example workflow

### Input request

`Audit the DreamPlay product page for tier confusion.`

### Synthesized brief

```json
{
  "agent": "development",
  "objective": "Audit the DreamPlay product page for tier confusion.",
  "deliverable": "Findings plus the smallest safe fix if needed.",
  "priority": "high",
  "businessContext": "Tier confusion can hurt conversion and weaken DreamPlay product clarity.",
  "context": {
    "summary": "Protect the distinction between DreamPlay One and DreamPlay Pro.",
    "project": "dreamplay-shop-2",
    "background": "Lionel prefers the smallest safe direct fix first.",
    "decisionContext": "Do not broaden scope into a redesign unless necessary.",
    "notes": [
      "DreamPlay One and DreamPlay Pro must stay clearly distinct.",
      "Gold is Pro-only."
    ]
  },
  "constraints": [
    "Smallest safe fix first."
  ],
  "successCriteria": [
    "Issue confirmed or ruled out.",
    "Evidence returned."
  ],
  "nonGoals": [
    "No broad redesign."
  ],
  "questionsToAnswer": [
    "Where exactly is the tier confusion happening?"
  ]
}
```

### Deterministic validation step

```bash
python3 {baseDir}/scripts/hermes_local_client.py prepare <<'EOF'
{ ...brief json... }
EOF
```

### Dispatch step

```bash
python3 {baseDir}/scripts/hermes_local_client.py run <<'EOF'
{ ...brief json... }
EOF
```

## Bottom line

The auto-dispatch layer should feel like:
- one normal conversation turn
- one inline synthesized brief
- one deterministic prepare/validate step
- one worker dispatch

Not an extra mini-agent chain just to create the prompt.
