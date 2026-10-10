# MVP implementation checkpoint

October 10, 2026. Implementation and integration verification are in progress. `SPEC.md` is unchanged. Current source is not declared an accepted MVP; no runtime healthcheck overrides the [acceptance matrix](product.md#acceptance-matrix).

## Implemented and checked

- API: FastAPI/SQLAlchemy/Alembic persistence, immutable configurations/workflow versions, public CRUD/plan/approval/control, fenced execution ledger/outbox, SSE replay, bounded artifacts and Git evidence. Dedicated PostgreSQL migration/concurrent/grant tests and HTTP/security regressions exist.
- Orchestrator: actual LangGraph compiler and PostgreSQL checkpointer, typed DAG validation, durable dispatch/interrupts/approvals/plans, limits and recovery. Unit/fault and actual API/HttpLedger regressions exist; actual CLI/PG restart acceptance is separate.
- Worker: Linux host Redis consumer plus durable supervisors, bounded process groups/deadlines, canonical paths/redaction, pinned CLI adapters, unique worktrees, reviewed commits, sequential integration and recovery journals. Linux fault/security/Git tests exist; the actual Codex subscription adapter passed full DAG and cancellation/recovery checks; Claude remains a separate gate.
- Frontend: projects/tasks/plan editor, React Flow graph editing/publishing/launch, agents/registries/policies, approvals/control/SSE/artifact/Git views. Production build, lint, contract tests and audit pass. Browser authorization, project registration and manual task creation are exercised against real API data; desktop/mobile DAG fitting and reconciled control notices were verified in the browser; broader resolution acceptance continues.
- Infrastructure: locked images, scoped generated secrets/Redis ACL, one-shot migrator and service readiness. Core containers are healthy. Windows and WSL authenticated probes confirm local API/Redis reachability and Docker loopback host bindings.
- Observability: locked official Langfuse v4 stack and Collector are healthy. Actual OTLP-to-observation checks preserve root/child/run correlation and reject sensitive/untrusted spans. No duplicate fixture spans or credential sentinel appeared. Idle memory is approximately 2.52 GiB for the combined running contour; three-CLI peak load capacity remains unmeasured. The actual DAG produced 80 correlated observations; a second run completed during a 148-second Langfuse outage.

## Open gates

1. Full API/scheduler/worker Codex DAG passed: three developers overlapped for 23.246 seconds, three distinct reviewers approved the checked trees, all 14 operations succeeded, 13 artifact hashes and 222 SSE replay events were verified, and integration checks passed without changing main. Live dependent-task and manual-resolution acceptance remain separate gates.
2. Live Codex cancellation stopped the observed PID in 2.219 seconds without integration. Short Redis outage, exact consumer restart, full completion during Langfuse outage, and isolated PostgreSQL/artifact/Git restoration passed. Full host loss and uncertain supervisor reconciliation remain separate gates.
3. Finish browser evidence for graph, approval, monitoring and resolution, upload redacted screenshots and verify Library file IDs.
4. WSL Claude login is required; Windows Claude login is not a WSL authentication proof. Codex 0.157.0, Node 24.21.0 and existing subscription authentication pass native diagnostics; three real developers and three independent reviewers completed in separate worktrees, with successful tests and integration. WSL Claude is still unauthenticated.
5. The current `alex` account has sudo/docker access and Docker socket access. A dedicated least-privilege account is unverified; no account/security changes are authorized or performed. External-host negative connectivity is also unverified.
6. Scoped skills/tool/MCP enforcement must pass the live capability matrix. Codex narrow tool/MCP scopes currently fail closed rather than widening permissions.
7. All four child implementation commits are published to the user-provided origins with successful GitHub CI. Finish acceptance increments and fresh bundle/recursive-clone verification under the current task's publication authorization.

Historical foundation/publication evidence is retained in [delivery status](delivery-status.md). Current work and skill/executor allocation are tracked in [kanban](kanban.md), [tasks](plans/tasks/mvp.md) and [skills](plans/skills-and-executors.md). Secret/raw runtime/build reports remain ignored; only redacted acceptance evidence may be committed or uploaded.
