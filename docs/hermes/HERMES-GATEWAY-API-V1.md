# Hermes Gateway API V1

Status: proposed v1
Owner: Lionel
Updated: 2026-04-15

## Purpose

This is the recommended API contract for the **hybrid architecture**:

- **VPS A**: Command / OpenClaw / TaskFlow / memory / Telegram
- **VPS B**: Hermes gateway hosting 3 logical workers
  - `marketing`
  - `development`
  - `operations`

TaskFlow remains the source of truth on Command.
Hermes gateway is an execution service, not the source of truth.

## Design principles

1. **One gateway, three logical agents**
   - one Hermes HTTP service
   - select worker via `agent`
   - do not start with 3 separate public APIs

2. **Command owns state**
   - Hermes should not invent task lifecycle semantics
   - Hermes echoes Command ids back

3. **Async-first**
   - `POST /v1/tasks` accepts work quickly
   - Hermes completes later via callback or status fetch

4. **Idempotent dispatch**
   - same `commandTaskId` should not create duplicate remote work

5. **Tailscale only**
   - private tailnet access only
   - no public internet exposure

## Recommended endpoints

### 1. Create task

`POST /v1/tasks`

Creates or reuses a remote Hermes task.

### 2. Get task status

`GET /v1/tasks/{remoteTaskId}`

Returns the latest task state and outputs.

### 3. Cancel task

`POST /v1/tasks/{remoteTaskId}/cancel`

Requests cancellation.

### 4. Health check

`GET /v1/health`

Returns gateway liveness and registered worker availability.

## Request headers

```http
Authorization: Bearer <TAILNET_SHARED_SECRET>
Content-Type: application/json
Idempotency-Key: <commandFlowId>:<commandTaskId>
X-Command-Flow-Id: <commandFlowId>
X-Command-Task-Id: <commandTaskId>
```

## Canonical enums

### Agent

```json
["marketing", "development", "operations"]
```

### Priority

```json
["low", "medium", "high", "critical"]
```

### Remote task status

```json
["accepted", "running", "waiting", "blocked", "needs_review", "completed", "failed", "cancelled"]
```

### Wait kind

```json
["command_reply", "lionel_approval", "missing_asset", "external_dependency", "worker_clarification"]
```

## POST /v1/tasks request schema

```json
{
  "schemaVersion": "hermes.task.v1",
  "command": {
    "flowId": "flow_01JRM7K8KQZ3W7QJ5P3S1E2ABC",
    "taskId": "task_01JRM7KAW3N3JQX9A1CDEF2345",
    "requestedAt": "2026-04-15T08:30:00Z",
    "requester": {
      "agent": "command",
      "sessionKey": "agent:main:telegram:direct:8155333249",
      "user": "Lionel"
    }
  },
  "agent": "operations",
  "objective": "Update masterclass migration tracker for 12 lessons and return a clean status summary.",
  "priority": "high",
  "deadline": "2026-04-16T02:00:00Z",
  "context": {
    "summary": "Masterclass launch is top priority. Hermes should only do migration tracking, not pricing or publishing.",
    "project": "ultimate-pianist-masterclass",
    "notes": [
      "Use existing naming conventions.",
      "Escalate immediately if lesson assets are missing or product structure looks inconsistent."
    ]
  },
  "assets": [
    {
      "type": "url",
      "label": "migration-sheet",
      "value": "https://example.com/masterclass-tracker"
    },
    {
      "type": "path",
      "label": "lesson-folder",
      "value": "/srv/hermes/shared/masterclass/lessons"
    }
  ],
  "constraints": [
    "Do not publish anything.",
    "Do not change pricing or product structure.",
    "Do not touch Stripe or auth-related systems."
  ],
  "successCriteria": [
    "Tracker updated for all assigned lessons.",
    "Return a concise per-lesson status summary.",
    "List blockers explicitly."
  ],
  "approval": {
    "required": false,
    "kind": null
  },
  "callback": {
    "mode": "webhook",
    "url": "http://100.88.10.4:19001/hermes/callback",
    "secret": "command_callback_secret",
    "events": ["waiting", "blocked", "completed", "failed", "cancelled"]
  }
}
```

## POST /v1/tasks accepted response

```json
{
  "schemaVersion": "hermes.task.accepted.v1",
  "remoteTaskId": "hermes_01JRM7KD4C8N7A4D1234567890",
  "status": "accepted",
  "agent": "operations",
  "deduped": false,
  "acceptedAt": "2026-04-15T08:30:02Z",
  "echo": {
    "flowId": "flow_01JRM7K8KQZ3W7QJ5P3S1E2ABC",
    "taskId": "task_01JRM7KAW3N3JQX9A1CDEF2345"
  }
}
```

## GET /v1/tasks/{remoteTaskId} response schema

```json
{
  "schemaVersion": "hermes.task.status.v1",
  "remoteTaskId": "hermes_01JRM7KD4C8N7A4D1234567890",
  "status": "running",
  "agent": "operations",
  "currentStep": "scan_assigned_lessons",
  "progress": {
    "percent": 40,
    "summary": "Checked 5 of 12 lessons"
  },
  "waiting": null,
  "blockers": [],
  "artifacts": [],
  "result": null,
  "error": null,
  "updatedAt": "2026-04-15T08:41:00Z",
  "echo": {
    "flowId": "flow_01JRM7K8KQZ3W7QJ5P3S1E2ABC",
    "taskId": "task_01JRM7KAW3N3JQX9A1CDEF2345"
  }
}
```

## Callback payload schema

Hermes should callback to Command on meaningful transitions.

`POST <callback.url>`

```json
{
  "schemaVersion": "hermes.task.event.v1",
  "event": "completed",
  "remoteTaskId": "hermes_01JRM7KD4C8N7A4D1234567890",
  "status": "completed",
  "agent": "operations",
  "currentStep": "done",
  "updatedAt": "2026-04-15T08:55:00Z",
  "echo": {
    "flowId": "flow_01JRM7K8KQZ3W7QJ5P3S1E2ABC",
    "taskId": "task_01JRM7KAW3N3JQX9A1CDEF2345"
  },
  "result": {
    "summary": "Updated tracker for 12 lessons. 9 clean, 3 missing one asset each.",
    "whatIDid": [
      "Reviewed assigned lesson directories.",
      "Updated migration tracker.",
      "Flagged three lessons missing PDFs."
    ],
    "artifacts": [
      {
        "type": "url",
        "label": "updated-tracker",
        "value": "https://example.com/masterclass-tracker"
      }
    ],
    "evidence": [
      "Tracker row count matches assignment count.",
      "Three missing-PDF blockers listed explicitly."
    ],
    "blockers": [
      "Lesson 17 missing Full-version PDF",
      "Lesson 22 missing thumbnail",
      "Lesson 31 missing source video"
    ],
    "needsFromCommand": [],
    "recommendedNextStep": "Assign asset recovery for the three blocked lessons."
  },
  "waiting": null,
  "error": null
}
```

## Waiting / blocked callback example

```json
{
  "schemaVersion": "hermes.task.event.v1",
  "event": "waiting",
  "remoteTaskId": "hermes_01JRM7KD4C8N7A4D1234567890",
  "status": "waiting",
  "agent": "marketing",
  "currentStep": "await_subject_line_approval",
  "updatedAt": "2026-04-15T09:10:00Z",
  "echo": {
    "flowId": "flow_01JRM7K8KQZ3W7QJ5P3S1E2ABC",
    "taskId": "task_01JRM7KAW3N3JQX9A1CDEF2345"
  },
  "waiting": {
    "kind": "lionel_approval",
    "summary": "Need Lionel to choose between two subject line options before finalizing the email draft.",
    "options": [
      "Moonlight Sonata Nightmare is live",
      "The hardest Moonlight Sonata arrangement I’ve ever taught"
    ]
  },
  "result": null,
  "error": null
}
```

## Cancel response

```json
{
  "schemaVersion": "hermes.task.cancel.v1",
  "remoteTaskId": "hermes_01JRM7KD4C8N7A4D1234567890",
  "status": "cancelled",
  "cancelledAt": "2026-04-15T09:12:00Z",
  "echo": {
    "flowId": "flow_01JRM7K8KQZ3W7QJ5P3S1E2ABC",
    "taskId": "task_01JRM7KAW3N3JQX9A1CDEF2345"
  }
}
```

## Health response

```json
{
  "schemaVersion": "hermes.health.v1",
  "status": "ok",
  "workers": {
    "marketing": "ready",
    "development": "ready",
    "operations": "ready"
  },
  "time": "2026-04-15T08:30:00Z"
}
```

## Error shape

Use one consistent error envelope.

```json
{
  "schemaVersion": "hermes.error.v1",
  "error": {
    "code": "INVALID_AGENT",
    "message": "agent must be one of marketing, development, operations",
    "retryable": false
  }
}
```

Suggested error codes:
- `INVALID_AGENT`
- `INVALID_SCHEMA`
- `UNAUTHORIZED`
- `DUPLICATE_TASK`
- `TASK_NOT_FOUND`
- `TASK_ALREADY_FINISHED`
- `WORKER_UNAVAILABLE`
- `INTERNAL_ERROR`

## TaskFlow mapping

This is the key point.

TaskFlow remains canonical on Command.

### Command-side TaskFlow state

Store at minimum:
- `flowId`
- `commandTaskId`
- `remoteTaskId`
- `targetAgent`
- `status`
- `currentStep`
- `deadline`
- `approvalRequired`
- `latestArtifactRefs`
- `latestBlockers`
- `latestSummary`

### Mapping rules

- On `POST /v1/tasks` accepted:
  - TaskFlow child task becomes `running`
  - store `remoteTaskId`

- On callback `waiting`:
  - TaskFlow `setWaiting(...)`
  - mirror `waiting.kind` into `waitJson`

- On callback `blocked`:
  - TaskFlow becomes `blocked` or `waiting`, depending on whether Command can resolve it

- On callback `completed`:
  - TaskFlow `resume(...)`
  - Command reviews output
  - then `finish(...)`

- On callback `failed`:
  - TaskFlow `fail(...)`

- On user stop:
  - Command sends cancel request
  - then `requestCancel(...)` or `cancel(...)`

## Recommendation on sync vs async

Use **async by default**.

Even if a task might finish quickly, do not tie Command’s turn lifecycle to the remote worker.

Preferred pattern:
- Command dispatches
- Hermes accepts immediately
- Hermes later callbacks
- Command resumes TaskFlow and reports back

## Recommendation on one endpoint vs three endpoints

Start with **one gateway service** and **one task creation endpoint**.

Use `agent` routing inside the payload.

Only split into three separate service endpoints later if one of these becomes true:
- different auth per worker
- different deploy schedules
- different reliability/SLO needs
- hard isolation requirement
- one worker becomes materially heavier than the others

## My recommendation

If we build this now, I would ship exactly this first:

- `POST /v1/tasks`
- `GET /v1/tasks/{remoteTaskId}`
- `POST /v1/tasks/{remoteTaskId}/cancel`
- `GET /v1/health`
- webhook callbacks back to Command
- one Hermes gateway process
- `agent` enum for worker routing
- TaskFlow state kept only on Command
