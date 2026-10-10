# MVP implementation tasks and executable gates

Status: In progress. Source: unchanged [SPEC](../../../SPEC.md), [decisions](../../decisions.md), [backlog](../../backlog.md). English source/documentation; Russian progress reports.

## E1 - durable control and local startup

Start PostgreSQL/Redis with generated scoped secrets, apply Alembic under a migrator role, verify application roles cannot perform DDL or access unrelated schemas. Build/start services with loopback ports. Run API migration, auth/Origin/revision/idempotency/CRUD tests and UI create project/task. Export implemented OpenAPI and validate umbrella contracts. Service readiness reports dependency health separately from MVP acceptance.

## E2 - contained execution and Git

Run worker tests on Linux ext4: process descendants killed on timeout/cancel/lease loss; output flood bounded; credential sentinel redacted; canonical symlink/path escape denied. Worker claims authoritative API jobs through Redis; duplicate messages never create duplicate worktrees/commits. Git intent journal recovers crash after commit. Live CLI tests use a dedicated disposable test repo and existing subscription authentication, no API payment fallback.

## E3 - durable workflows

Validate all supported graph node types/ports/fork/join/condition/cycles and immutable versions. Real LangGraph checkpointer resumes same thread after approval/restart. Three independent CLI executions overlap in distinct worktrees; dependent execution base contains approved predecessor changes. Verify pause drain, cancel, retries, reservations, limits, lost Redis, expired live lease uncertainty, orchestrator/worker restart. Run independent review/test and serial integration; default branch remains unchanged; conflicts pause with preserved evidence.

## E4 - complete UI

Browser tests create/edit/validate/publish/launch workflow, configure agents/skills/tools/MCP, approve bound snapshots, view authenticated SSE events/replay, controls, execution usage and Git evidence. Check keyboard labels/errors/loading and responsive layout. Save redacted screenshots in Library and report verified file IDs.

## E5 - telemetry and release

Start audited official Langfuse stack using exact source/image pins and private credentials. Verify eligible OTel trace correlation and Langfuse lookup, privacy sentinels, no duplicate spans and execution during telemetry outage. Measure resources, event latency and limits with three processes. Verify migration/backup restore and listeners from Windows/WSL; external-host denial remains a separately evidenced gate. Publish verified child increments, then umbrella pins; verify remote SHAs, configured CI and fresh recursive clone. Keep final readiness false if any A1-A12/W1-W8 evidence is absent.

## Actual skills

Python owners use local python-project-structure, python-type-safety, python-testing-patterns and py-security; API additionally FastAPI/configuration/error-handling, worker/orchestrator background-jobs/resource-management/resilience/async patterns. Frontend uses react-dev, Vite, TanStack Query and beforemerge React review. Observability uses Python configuration/observability. These skills are read from C:/Users/admin/Syncthing/agents/skills/software-development; they guide cohesive modules, strict typed boundaries, meaningful isolated fault tests and safe credentials/process control. Root applies delegation-patterns with disjoint ownership and integration gates, and Git commit guidance. Exact per-owner usage is recorded after review.
