# Worker Briefs

Use this reference when building a richer brief for the local same-VPS worker trio.

## Goal

A good worker brief should answer:

- what exactly needs to be done
- why it matters to the business or project
- what constraints must be preserved
- what a successful result looks like
- what kind of output Command expects back

## Minimal request shape

This is enough for a basic dispatch:

```json
{
  "agent": "development",
  "objective": "Fix the checkout bug.",
  "context": {
    "summary": "Checkout is dropping users before payment on mobile Safari."
  },
  "constraints": ["Smallest safe fix first."],
  "successCriteria": ["Bug reproduced and fixed.", "Return evidence."]
}
```

## Preferred request shape

This is the richer shape the automatic dispatch layer should aim to fill:

```json
{
  "agent": "development",
  "objective": "Fix the checkout bug on mobile Safari.",
  "deliverable": "Verified patch with root-cause summary and file list.",
  "priority": "high",
  "businessContext": "Checkout breakage directly hurts revenue, so conversion protection matters more than polish.",
  "executionMode": "claude_assisted",
  "context": {
    "summary": "Users can add to cart, but the final payment action silently fails on iPhone Safari.",
    "project": "dreamplay-shop-2",
    "background": "Lionel prefers the smallest safe direct fix first.",
    "decisionContext": "Do not redesign checkout unless the root cause truly requires it.",
    "notes": [
      "DreamPlay One and DreamPlay Pro must stay clearly distinct.",
      "Gold is Pro-only."
    ]
  },
  "files": [
    "dreamplay-shop-2/app/checkout/page.tsx",
    "dreamplay-shop-2/components/checkout-form.tsx"
  ],
  "assets": [],
  "constraints": [
    "Smallest safe fix first.",
    "Do not change product positioning logic."
  ],
  "successCriteria": [
    "Root cause identified.",
    "Patch applied.",
    "Relevant check or test run.",
    "Evidence returned."
  ],
  "nonGoals": [
    "No visual redesign.",
    "No unrelated refactor."
  ],
  "requiredOutput": [
    "State root cause clearly.",
    "List files touched.",
    "Include verification evidence."
  ],
  "questionsToAnswer": [
    "What exactly caused the break?",
    "What is the smallest safe fix?"
  ]
}
```

## Field guide

### `agent`
Worker id:
- `marketing`
- `development`
- `operations`

### `objective`
One-sentence task statement.

Good:
- `Write 3 hero hooks for the masterclass waitlist page.`
- `Fix the failing checkout submit action on mobile Safari.`

Bad:
- `Help with website`
- `Figure something out`

### `deliverable`
Concrete thing Command expects back.

Examples:
- `Three hooks plus one recommended CTA.`
- `Verified patch plus root-cause summary.`
- `Prioritized checklist with owners and dependencies.`

### `priority`
Use one of:
- `low`
- `normal`
- `high`
- `urgent`

### `businessContext`
Why this matters commercially or operationally.

Examples:
- conversion protection
- launch readiness
- customer trust
- revenue timing
- keeping product positioning clean

### `executionMode`
Optional dispatcher override.

Allowed values:
- `standard`
- `claude_assisted`

Use this mainly for `development` when Command wants to force or preserve the Claude-assisted path.
If omitted, the local dispatcher now infers it conservatively.

### `context`
Project-specific details.

Useful subfields:
- `summary`
- `project`
- `background`
- `decisionContext`
- `notes`

### `files`
Relevant code or document paths to inspect first.

### `assets`
Non-file-path inputs, URLs, references, or named artifacts.

### `constraints`
Hard guardrails.

Examples:
- `Do not invent pricing.`
- `Smallest safe fix first.`
- `Do not publish anything.`
- `Do not change product tier logic.`

### `successCriteria`
How Command will judge whether the worker succeeded.

### `nonGoals`
Things the worker should explicitly avoid.

### `requiredOutput`
How the answer should be shaped, beyond the standard section headers.

### `questionsToAnswer`
Useful when Command wants the worker to resolve specific uncertainties.

## Role templates

### Marketing
Use when the main need is messaging, offer clarity, or conversion framing.

Bias toward:
- angle clarity
- concrete copy
- premium concise language
- conversion logic

Usually include:
- `businessContext`
- audience or offer context
- tone constraints
- explicit ban on invented proof/pricing if relevant

Good deliverables:
- hooks
- CTA options
- offer framing
- section structure
- content angles

### Development
Use when the main need is implementation or diagnosis.

Bias toward:
- root cause clarity
- smallest safe fix
- evidence
- explicit file impact

Usually include:
- relevant files
- product/business rules that must remain true
- verification expectations
- non-goals to prevent refactor drift
- `executionMode: claude_assisted` when the task is clearly heavy enough to benefit from Claude Code

Good deliverables:
- patch
- root-cause summary
- file list
- verification notes
- recommended next technical step

### Operations
Use when the main need is sequencing, clarity, ownership, or execution hygiene.

Bias toward:
- prioritized checklist
- dependency awareness
- blockers surfaced early
- concrete next action

Usually include:
- timeline or urgency context
- owner assumptions
- what decisions are pending
- what should wait versus what should happen now

Good deliverables:
- checklist
- timeline
- owner map
- follow-up plan
- blocker summary

## Default prompting rule

The future automatic dispatch layer should prefer:
- fewer but clearer facts
- explicit business reason
- explicit guardrails
- explicit success criteria

Not just raw transcript dumping.

## DreamPlay-oriented examples

### Marketing example

```json
{
  "agent": "marketing",
  "objective": "Write 3 hero options for the masterclass waitlist page.",
  "deliverable": "Three hero options plus one recommended CTA.",
  "priority": "high",
  "businessContext": "Masterclass revenue matters more than extra DreamPlay polish right now.",
  "context": {
    "summary": "Keep it premium, direct, and non-fluffy.",
    "project": "ultimate-pianist-masterclass",
    "notes": ["Do not invent pricing.", "A $1 VIP waitlist exists."]
  },
  "constraints": ["Draft only.", "No fake proof or invented scarcity."],
  "successCriteria": ["3 distinct options.", "Each option is short enough for a hero section."],
  "requiredOutput": ["Lead with the recommended option."]
}
```

### Development example

```json
{
  "agent": "development",
  "objective": "Audit the product detail page logic for finish-tier regressions.",
  "deliverable": "Bug findings plus the smallest safe fix if needed.",
  "priority": "high",
  "businessContext": "Incorrect finish logic could blur DreamPlay One vs Pro and hurt product clarity.",
  "context": {
    "summary": "Protect tier separation.",
    "project": "dreamplay-shop-2",
    "notes": [
      "DreamPlay One and DreamPlay Pro must stay clearly distinct.",
      "Gold is Pro-only."
    ]
  },
  "files": ["dreamplay-shop-2"],
  "constraints": ["Smallest safe fix first."],
  "successCriteria": ["Issue confirmed or ruled out.", "Evidence returned."],
  "nonGoals": ["No broad refactor."]
}
```

### Operations example

```json
{
  "agent": "operations",
  "objective": "Turn the masterclass launch into a prioritized execution checklist.",
  "deliverable": "Ordered checklist with blockers and next action.",
  "priority": "high",
  "businessContext": "Execution clarity matters because money is tight and the launch needs to move.",
  "context": {
    "summary": "One concrete next step at a time.",
    "project": "ultimate-pianist-masterclass"
  },
  "constraints": ["Keep it concise.", "Prioritize execution over brainstorming."],
  "successCriteria": ["Checklist is prioritized.", "Dependencies are clear."],
  "requiredOutput": ["Put the next immediate action first."]
}
```
