# Hermes Orchestration V2

Status: proposed v1
Owner: Lionel
Updated: 2026-04-15

## Blunt assessment

The high-level architecture is right:
- one orchestrator with full context
- three specialist workers
- Claude Code reserved for harder coding
- clear approval gates for publishing, spending, and sensitive systems

The missing piece is a control plane.

Telegram is a transport layer, not the system of record.
If we rely on chat threads alone, task state will drift.

## Core model

- **Command (OpenClaw)** owns context, priority, approvals, and final judgment.
- **Hermes agents** are stateless specialist workers.
- **TaskFlow** is the durable task ledger.
- **Telegram now / Tailscale later** are just dispatch channels.
- **Claude Code** is a tool Command drives for non-routine coding, not a peer manager.

## Role boundaries

### Command

Owns:
- intake
- prioritization
- delegation decisions
- cross-project context
- approval routing
- final summaries to Lionel
- task state in TaskFlow

Does not offload:
- final publishing approval
- pricing decisions
- spending approval
- Stripe/payment changes
- ambiguous high-judgment decisions without review

### Hermes 1: Marketing

Owns:
- email drafts
- newsletter drafts
- social copy
- ad copy / creative briefs
- customer comms drafts

Never does:
- send/publish without approval
- invent pricing or timelines
- touch code repos directly

### Hermes 2: Development

Owns:
- routine Shopify maintenance
- routine API work
- known-pattern bug fixes
- dependency updates
- tests for routine changes

Escalates to Command + Claude Code:
- Stripe
- auth
- user data
- architecture
- unclear debugging

### Hermes 3: Operations

Owns:
- masterclass migration tracking
- lesson organization
- asset organization
- scheduling support
- funnel/config coordination that does not alter pricing or payment logic

Never does:
- publish lessons without sign-off
- change pricing or product structure
- change funnel logic without review

## The actual missing layer: TaskFlow

Every delegated job should have a durable flow.

TaskFlow should hold:
- `flowId`
- `title`
- `domain` (`marketing`, `development`, `operations`, `command`, `claude-code`)
- `objective`
- `status` (`running`, `waiting`, `blocked`, `done`, `failed`, `cancelled`)
- `currentStep`
- `priority`
- `deadline`
- `stateJson`
- `waitJson`
- linked child task refs
- requester context
- artifact links
- blockers
- approval state

TaskFlow should be the source of truth for:
- who owns the next move
- what is blocked
- what is awaiting Lionel
- what completed
- what artifact came back from which worker

## Lifecycle

### 1. Intake

Command receives a request from Lionel.

Command decides one of three paths:
- do it inline now
- delegate to one Hermes agent
- drive Claude Code directly

### 2. Create managed flow

If the task is delegated or will outlive one reply, Command creates a managed TaskFlow.

Suggested first fields:
- `goal`: short plain-English deliverable
- `currentStep`: `triage`
- `stateJson`: objective, context, assets, constraints, success criteria, deadline, approval gates, chosen worker

### 3. Dispatch child task

Command creates a linked child task under the flow and dispatches it to the selected Hermes agent.

For now:
- dispatch via Telegram DM

Later:
- same payload over Tailscale HTTP

The transport can change without changing the TaskFlow state model.

### 4. Wait / monitor

If Hermes is working, TaskFlow stays `running`.
If Hermes needs input, set flow to `waiting` with structured `waitJson`:
- `kind`: `lionel_reply`, `approval`, `external_dependency`, `worker_blocked`
- `who`: `lionel`, `marketing`, `development`, `operations`, `external`
- `reason`

### 5. Review

Command reviews Hermes output before anything sensitive happens.

Sensitive outputs always stop here:
- emails
- social posts
- ads
- pricing changes
- deployments with meaningful risk
- anything touching money, auth, or user data

### 6. Finish / fail / cancel

When the result is accepted, Command finishes the flow with final artifact links and summary.
If the work is impossible or obsolete, Command fails or cancels the flow explicitly.

## Decision rule: when NOT to delegate

Do it yourself when:
- the task takes under ~5 minutes
- the task is mostly context recall or judgment
- delegation overhead is larger than execution overhead
- the task spans multiple domains and needs one brain

Delegate when:
- the task is repeatable
- the output format is known
- the domain is clear
- success criteria can be written in one pass

Use Claude Code when:
- the work is non-routine coding
- the fix is architecturally meaningful
- the work touches payments, auth, or user data
- debugging requires deeper reasoning than a routine patch

## Required Hermes brief format

Every delegated task should use the same shape.

### Brief template

```text
TASK: <flowId>/<taskId>
DOMAIN: <marketing|development|operations>
OBJECTIVE: <one-sentence deliverable>
DEADLINE: <date/time or none>
PRIORITY: <high|medium|low>

CONTEXT:
<only the context required to do the job>

ASSETS:
- <file path or URL>
- <file path or URL>

CONSTRAINTS:
- <what not to do>
- <approval boundaries>

SUCCESS CRITERIA:
- <what Command will accept as done>

ESCALATE IF:
- <conditions that should come back immediately>

RETURN FORMAT:
STATUS:
WHAT I DID:
ARTIFACTS:
BLOCKERS:
RECOMMENDED NEXT STEP:
```

## Required Hermes completion format

```text
TASK: <flowId>/<taskId>
STATUS: <done|blocked|needs-review|failed>

WHAT I DID:
- <concise summary>

ARTIFACTS:
- <file path / commit / URL / draft text>

EVIDENCE:
- <proof, test result, screenshot, metric>

BLOCKERS:
- <none or explicit blocker>

NEEDS FROM COMMAND:
- <approval / missing asset / question>

RECOMMENDED NEXT STEP:
- <single next action>
```

## Approval gates

Command must stop and get Lionel review before:
- anything customer-facing is sent or published
- any money is spent
- pricing changes
- Stripe/payment changes
- auth or user-data changes
- risky production deployments
- commitments made on Lionel's behalf

## Daily operating rhythm

### Morning brief

The daily brief should be generated from TaskFlow, not memory vibes.

It should include:
- top priority
- tasks waiting on Lionel
- tasks blocked
- tasks completed since last brief
- one recommended next move

### Weekly review

Also generated from TaskFlow + project metrics where available:
- completed flows by domain
- blocked flows
- overdue flows
- masterclass migration progress
- marketing outputs awaiting approval
- development changes shipped

## Data model for a minimum viable ledger

Even before a full custom UI, the ledger should be able to answer:
- What is active right now?
- What is waiting on Lionel?
- What is each Hermes agent doing?
- What finished this week?
- What is overdue?

Minimum per-task fields:
- `flowId`
- `taskId`
- `title`
- `domain`
- `owner`
- `status`
- `priority`
- `deadline`
- `requestedAt`
- `updatedAt`
- `currentStep`
- `blockedSummary`
- `objective`
- `assets[]`
- `artifactRefs[]`
- `approvalRequired`
- `approvedByLionel`

## Rollout recommendation

Do not launch all three Hermes agents in full complexity on day one.

Recommended rollout:

### Phase 1
- Command + TaskFlow discipline
- one Hermes agent as pilot
- Telegram DM dispatch
- standard brief/completion templates

### Phase 2
- all three Hermes agents
- shared task taxonomy
- scheduled morning brief pulled from TaskFlow state

### Phase 3
- Tailscale HTTP dispatch
- structured payloads instead of chat-only briefs
- optional dashboard / queue view

## My recommendation

Use this architecture, but with one rule:

**Hermes does work. Command owns the truth.**

That means:
- memory stays centralized here
- task state stays in TaskFlow
- Hermes gets tight briefs, not full life context
- Lionel only sees distilled updates and approval requests

## Immediate next step

Before scaling to all three Hermes agents, define these four things:
1. Hermes agent identifiers and contact paths
2. the canonical brief template
3. the canonical completion template
4. the TaskFlow fields we will treat as mandatory from day one
