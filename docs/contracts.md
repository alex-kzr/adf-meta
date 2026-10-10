# API and event contracts вЂ” draft v0.1

The machine-readable [OpenAPI](../packages/contracts/openapi.json) is a design baseline. The scaffold exposes only health/readiness; these routes are not implemented. UUIDs, RFC3339 UTC, snake_case fields, JSON request/response and versioned envelopes are canonical. Pagination uses opaque cursor + `limit` (default 50/max 200), response `{items,next_cursor}`. Mutations use optimistic `If-Match` revision, conflicts 409/412, validation 422, denied 403, missing 404, unavailable 503.

Errors: `{code,message,details,request_id}`; details are bounded/redacted. Relevant codes: INVALID_WORKFLOW, VERSION_CONFLICT, AUTH_REQUIRED, PERMISSION_DENIED, CAPABILITY_UNSUPPORTED, IDEMPOTENCY_CONFLICT, LEASE_STALE, EXECUTION_UNCERTAIN, INTEGRATION_CONFLICT, QUOTA_EXCEEDED, CURSOR_EXPIRED.

## Public routes

| Area | Routes / semantics |
| --- | --- |
| Projects | GET/POST `/api/projects`; GET/PATCH `/api/projects/{id}`; validate canonical path and configured root/check IDs |
| Tasks | GET/POST `/api/tasks`; GET/PATCH `/api/tasks/{id}`; POST `/api/tasks/{id}/decompose` creates asynchronous planning command, never implicit approval |
| Agents | GET/POST `/api/agents`; GET/PATCH `/api/agents/{id}`; editing produces new config version |
| Workflows | GET/POST `/api/workflows`; GET/PATCH `/api/workflows/{id}`; POST `/api/workflows/{id}/validate`; POST `/api/workflows/{id}/versions` publishes immutable validated version |
| Runs | POST `/api/runs` with task/workflow version/plan hash/policy ref; GET `/api/runs`, `/api/runs/{id}`; POST pause/resume/cancel commands return 202 + command_id |
| Evidence | GET `/api/runs/{id}/nodes`, `/artifacts`, `/git-changes`; GET `/api/artifacts/{id}/content` with authorization/checksum metadata |
| Approval | GET `/api/runs/{id}/approvals`; POST `/api/approvals/{id}/decision` with approve/reject, snapshot hash and request revision |
| Registries | GET/POST `/api/skills`, `/api/mcp-servers`; validated immutable manifests/scopes; never accept a credential blob |
| Health | GET `/api/providers/health`, `/api/metrics/overview`, `/healthz`, `/readyz` |
| Stream | GET `/api/runs/{id}/events`, text/event-stream |

All non-health routes require a local admin bearer token. Same-origin proxy avoids permissive CORS. UI keeps token in memory (user enters it after reload), never query params/localStorage. Fetch-based SSE carries Authorization; native EventSource cannot set that header. Cookie sessions are deferred until explicit CSRF/Origin/SameSite design.

POST run/decompose/control/approval requires `Idempotency-Key` scoped to principal+route. Store key, canonical request hash and result in the same DB transaction; exact duplicate returns same result, changed body 409. Retain at least run lifetime plus 7 days. Status mutation is validated server-side; no generic user-set terminal status. Pause/resume/cancel are durable commands, not claims of immediate control completion.

## Worker internal routes

POST `/internal/workers/register`; POST `/internal/workers/{id}/heartbeat`; POST `/internal/executions/{id}/claim`; POST `/heartbeat`, `/events`, `/artifacts`, `/result`; GET `/internal/executions/{id}/control`. Worker token scope binds worker/projects/allowed roots. All execution mutations validate monotonic lease epoch and owner. Result accepts idempotent terminal outcome plus exit/test/review/tree/commit/artifact hashes. Redis acknowledgement follows persisted result. Orchestrator consumes completion ledger/outbox; worker cannot approve its own policy expansion.

## Jobs, normalized events and SSE

[Job schema](../packages/contracts/execution-request.schema.json) covers execution/run/node/task IDs, operation, root+execution base, immutable agent/policy versions, project-relative worktree allocation, timeout/steps/output/disk and env **names** allowlist. Prompt is private job data, never trace default. Worker resolves allowed paths/check IDs from trusted registration, not arbitrary transport-supplied cwd or shell strings.

Canonical normalized CLI events: started, output, tool_started, tool_finished, usage_reported, heartbeat, completed, failed, cancelled. Domain events additionally include run.status_changed, approval.requested/decided, node.status_changed, integration.conflict, artifact.created. Envelope has schema_version/event_id/run_id/execution_id/epoch/sequence/type/time/trace_id/payload. Schema limits shape; runtime also caps 64 KiB/event and 20 MiB execution output before storage.

Adapter mapping: Codex thread/turn/item events and Claude init/assistant/tool/result events map to canonical types through pinned fixtures. Preserve unknown provider event as a bounded warning with redacted summary; do not mistake malformed/unknown terminal data for success. Usage is provider-reported or null, never estimated subscription spend. Final result aggregates stream outcome plus process exit and independent validation.

SSE `id` is persistent per-run sequence, `event` is domain type, `data` is the redacted JSON envelope. `Last-Event-ID`/cursor replays ordered persisted events with at-least-once delivery; UI deduplicates event_id. Send heartbeat comment every 15 s; it is not a persisted event. Expired cursor -> 409 CURSOR_EXPIRED then snapshot/refetch. Keep bounded buffering/backpressure, disable proxy buffering and limit concurrent streams.

## Compatibility

Version `1` schemas reject unknown execution/job semantics. Additive response fields are backward-compatible only if clients ignore them; new enum/node/operation meanings require explicit capability negotiation or schema version. Umbrella owns JSON schema/OpenAPI; generate Pydantic/TS code later from pinned sources, not divergent hand-written copies. A contract hash is included in service/worker registration; bootstrap diagnoses mismatched release pins.

## Node configuration registry to implement

| Type | Required typed configuration / gate |
| --- | --- |
| start / end | Empty config; only valid input/output ports |
| planner | Immutable planner agent version, task budget, structured plan schema hash; read-only capability |
| agent_task | Task binding, immutable agent version, write-path reservation, dependency base and approved policy |
| condition | Allowlisted state field, enum operator (eq/in), typed literal; true/false ports; no script/expression |
| parallel_fork | Paired join ID and unique selected branch IDs; properly nested scope |
| parallel_join | Paired fork ID, all-success policy; unselected branches skipped, required failures propagate |
| test | Registered check IDs, timeout and required result schema; no arbitrary command text |
| review | Independent reviewer version, exact tree/diff SHA and test evidence; no developer self-review |
| approval | Action type, hash-bound snapshot/policy, expiry; no permission granted by node text |
| git_commit | Accepted tree SHA, reviewed path set, approved scope and execution metadata; worker performs operation |

These per-node JSON Schemas and fork nesting checks are E3 implementation work. The checked-in workflow schema currently validates the outer shape only.

Domain events use a separate server envelope with optional task/node/execution context, a monotonic run_sequence and immutable event_id. Normalized worker sequence is per execution+epoch; ingestion allocates run_sequence transactionally. SSE id uses run_sequence, not the worker sequence. Public payloads exclude raw prompts/logs and expose artifact references instead.
