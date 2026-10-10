# Implemented API and execution contracts v1

[OpenAPI](../packages/contracts/openapi.json) is an export of the current API factory, including public, orchestrator and worker routes. It replaces the foundation route sketch. The source authority is [create_app](../services/api/src/adf_api/main.py), [API input models](../services/api/src/adf_api/schemas.py), [execution overlay](../services/api/src/adf_api/ledger.py) and [worker conversion](../services/runtime-worker/src/adf_runtime_worker/executor.py). A schema snapshot is compatibility evidence; it does not establish whole-MVP readiness.

## Reproduce and check

Use Python 3.12 with the API's pinned dependencies plus the umbrella development dependencies. The local API environment already provides them:

~~~powershell
services/api/.venv/Scripts/python.exe scripts/export-api-contract.py
services/api/.venv/Scripts/python.exe scripts/export-api-contract.py --check
services/api/.venv/Scripts/python.exe -m unittest discover -s tests -p test_contract_snapshot.py -v
python scripts/verify.py
~~~

On Linux, use the equivalent Python environment path. The exporter adds the checked-out API, orchestrator and worker source directories to its import path. It clears configuration/secret-file environment variables while importing the API's default app, disables telemetry and constructs an in-memory database engine. Export does not connect to operational databases, start services, authenticate providers or read configured credentials.

The tests use synthetic bearer values, an isolated SQLite database, actual FastAPI routes and actual graph validation. They replay execution creation, claims, events and terminal results; validate all seven operation snapshots; test nullable pre-inspection fields and immutable context after definition edits; and convert supported claimed jobs to the worker's internal adapter Request without executing code. PostgreSQL locking, Git/process recovery and live provider acceptance are separate module/umbrella checks.

API-dependent tests explicitly skip when their dependency environment is absent. CI must install both API and umbrella pinned dependencies and run the exporter with --check to enforce drift; a static-fixture-only run is insufficient.

## Contract files and ownership

| File | Meaning and source |
| --- | --- |
| [openapi.json](../packages/contracts/openapi.json) | Exact current create_app().openapi() export; includes /api, /internal and health routes |
| [workflow.schema.json](../packages/contracts/workflow.schema.json) | Exported orchestrator Workflow model; node config and DAG semantics additionally require validate_graph |
| [execution-request.schema.json](../packages/contracts/execution-request.schema.json) | Private nonterminal claim request, including authoritative project/agent/policy snapshots; maintained overlay description composed with API model schemas |
| [execution-event.schema.json](../packages/contracts/execution-event.schema.json) | Actual WorkerEvent accepted within an event batch; ownership/epoch are outside this event |
| [worker-event-batch.schema.json](../packages/contracts/worker-event-batch.schema.json) | Exported EventBatch input: worker_id, epoch, optional process_identity and events |
| [run-event.schema.json](../packages/contracts/run-event.schema.json) | Persisted event_view output carried by SSE and event-history; includes run_sequence and nullable execution context |
| [Examples](../packages/contracts/examples/execution-request.json) | Synthetic offline fixtures; zero Git SHAs are never executable repository bases |

The API's output dictionaries and some nested request dictionaries are intentionally open shapes. OpenAPI reflects the implemented route declarations; several response bodies remain generic objects. Custom {code,message,details,request_id} errors, binary attachment behavior and SSE framing are described here and tested at runtime rather than fully expressed by the generated response schemas. Do not infer a strict generated client or comprehensive response validation from this export.

Frontend TypeScript and the worker adapter dataclass remain separately maintained implementations. No automatic client/model generation or contract-hash handshake is implemented. Source changes require snapshot regeneration and compatibility tests.

## Authentication, identifiers and mutations

Admin routes use a local bearer token. Orchestrator ledger routes and worker lease routes use distinct tokens. Non-health requests with an Origin must match configured allowed origins. The UI keeps its token in memory and uses same-origin proxy requests, including fetch-based SSE; tokens do not belong in URLs or persistent browser storage. /healthz is process liveness; /readyz checks API configuration/migration state and keeps runtime_ready false.

Persisted entity IDs are UUID strings. Workflow node IDs are bounded slugs; worker IDs are bounded strings. Graph-node identity is distinct from the UUID node_run_id in an execution request. Stable agent.id/agent_id identifies the definition; agent.config_version_id and top-level agent_config_version identify its immutable version. Built-in Observer operations may have null agent/version references.

Definition PATCH requires If-Match revision. Run creation, decomposition, controls, approval decisions, plan revisions and conflict-resolution requests require Idempotency-Key where declared in OpenAPI. The API persists request hash/result transactionally; exact replay returns the existing result and changed input rejects. Current idempotency rows have no automatic expiry policy. Controls return durable commands, not proof of immediate process termination; cancel remains monotonic.

Paginated definition/run lists return {items,next_cursor} using UUID cursors and limit up to 200. Event history uses integer after/run_sequence. Some bounded per-run evidence lists currently return next_cursor:null without pagination. Clients must use each route's actual declared parameters.

## Public routes

| Area | Current behavior |
| --- | --- |
| Projects/tasks | CRUD, trusted repository/check configuration, revisions, same-project acyclic task dependencies |
| Agents/workflows | Immutable agent configuration versions; semantic workflow validation and published workflow versions |
| Skills/tools/MCP/policies | Typed manifests and immutable versions; credential blobs rejected; tool provider_mappings and trusted stdio MCP declarations |
| Runs | Create/list/detail, executions/nodes/evidence, durable pause/resume/cancel |
| Planning | Asynchronous task decomposition; revision-bound plan editing; separate validated graph proposal and proposal plan hash |
| Approval/resolution | Hash-bound approve/reject; integration conflict resolution requires its exact tree approval plus explicit resume |
| Artifacts | Authenticated opaque-ID attachments, checksum verification and nosniff; no host path download parameter |
| Events/diagnostics | Persisted event history, fetch SSE, provider health, usage metrics and public settings |

See OpenAPI for every exact path and method, including /api/runs/{run_id}/executions, /api/executions/{execution_id}, /api/runs/{run_id}/plan and /api/runs/{run_id}/resolution.

Public execution responses omit the private request dictionary. Authorized definition/run views can include user-authored configuration and task text. Output events and supported artifact content are redacted before API persistence; this is not a guarantee that every authorized public response contains no user text.

## Orchestrator ledger and worker transport

The orchestrator uses the internal run/command/outbox facade, node and execution ledgers, immutable base/trace compare-and-set, plan persistence, graph proposals and approval requests. It publishes Redis stream entries containing only execution_id and dispatch_id. The worker fetches the authoritative job from the API; Redis never supplies cwd, shell commands, policies or credentials.

A nonterminal claim returns {execution_id,epoch,lease_expires_at,request,status,terminal:false}. The [claimed request schema](../packages/contracts/execution-request.schema.json) applies to request after successful claim. It is neither the orchestrator's ExecutionInput nor the worker's internal adapter Request. Cancel-before-claim and terminal replay may return an older request without claim-only fields; do not validate those as nonterminal jobs.

| Job fields | Implemented meaning |
| --- | --- |
| IDs/version | execution/run/task/project/node UUIDs, lease_epoch; nullable config/policy versions for built-in/default configurations |
| Operation | repo_inspect, planner, agent_task, test, review, git_commit, integrate |
| Base/allocation | Nullable base before read-only inspection; exact Git bases for writing/validation; worktree_key is execution UUID, git_branch is worker allocation intent |
| Snapshots | API-owned project paths/check_registry/check_timeouts; stable agent identity plus pinned config/registries; approved policy |
| Scope/dependencies | Pinned expected_files/allowed_write_paths; accepted predecessor commits; complete selected integration commits |
| Limits | Authoritative deadline_at; smaller agent/policy timeout, steps, output and disk budgets; registered per-check timeout |
| Private context | task_prompt, pinned agent prompt/skills, trace context and optional repair/resolution evidence; no credential values or caller-allocated workspace_path |

ExecutionRequest currently permits additional extension fields. The job schema preserves that fact; unknown fields do not authorize capabilities. Unknown operation meanings are rejected. API guards reject overrides of trusted project/agent/policy/cwd/argv and enlargement of pinned write scope. Worker canonical-path, permission and Git checks remain necessary after schema validation.

Write approval binds graph, plan, base, dependency, policy and all agent/registry hashes plus write paths/tools. Internal task dependencies require successful accepted git_commit evidence; external task dependencies require completed integration. Review identity differs from the stable developer identity. Test/review/commit results bind the requested tree. Final integration requires the complete selected accepted commit set and all registered checks on its exact tree.

Heartbeat renewal uses a stable supervisor identity with journal binding. Expired ownership becomes uncertain; another database epoch cannot fence a live process. Reconciliation requires the same recorded identity, stopped child group and reacquired worktree lock. Consumer recovery replays durable events/results or proves death; it does not relaunch a consumed execution. Redis ACK follows terminal persisted evidence.

Codex rejects a configured narrow tool registry it cannot enforce. Claude mappings use explicit reviewed CLI tool names; trusted stdio MCP capabilities still require verified provider/security fixtures. Schema validity or repository text never grants a permission or proves hostile-code isolation.

## Worker events, persisted events and SSE

Worker ingestion is {worker_id,epoch,events:[{event_id,sequence,type,time?,payload}]}. A worker event has no required schema_version, run_id, execution_id, lease_epoch or trace_id: the route/batch supplies ownership. Supported normalization includes started, output, tool_started, tool_finished, usage_reported, completed, failed, cancelled and bounded warning. The API accepts a bounded type string rather than a closed enum.

Ingestion assigns immutable event_id and monotonic run_sequence transactionally. Persisted envelopes use schema_version:"1", event_id, run_id, run_sequence, execution_id, epoch, sequence, type, time and payload. Domain events may have null execution_id/epoch/sequence; producer time is not the authoritative persistence timestamp. Exact duplicate event identity/sequence is a no-op; changed content conflicts.

SSE uses id: run_sequence, event: type and data: persisted envelope. Last-Event-ID or after replays persisted events; clients deduplicate and never move their cursor backwards. Invalid/out-of-range cursors return CURSOR_EXPIRED. Heartbeat comments appear about every 15 seconds; terminal EOF follows the final persisted event. JSON event-history exposes the same envelopes.

Event payloads are capped at 60,000 UTF-8 bytes so the SSE envelope stays below 64 KiB. Execution output uses the pinned quota. Ordinary bodies are capped at 1 MiB, artifact base64 envelopes at 30 MiB and decoded UTF-8 text/diff/JSON content at 20 MiB. The API redacts content before checksummed opaque-key storage.

Usage counters are provider-reported numbers or unknown, with partial/known-count metadata. Reported API-equivalent provider_estimated_cost_usd is distinct from actual billed cost; subscription spend remains null without evidence. These metrics do not establish a financial spending cap.

## Remaining acceptance gates

Contract tests prove the current local wire shapes and replay checks. They do not prove real provider authorization, three parallel CLI sessions, WSL process/Git restart recovery, dedicated least privilege, external-host connection denial, scoped MCP behavior or the complete user/browser acceptance matrix. Those gates belong to the [implementation status](implementation-status.md) and [delivery status](delivery-status.md). Keep whole-MVP readiness false until their required evidence is recorded.
