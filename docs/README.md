# Development documentation

Start with [current implementation status](implementation-status.md), [live acceptance status](acceptance-status.md), [release checkpoint](release-checkpoint.md) and [implementation board](kanban.md).

1. [Product and acceptance](product.md)
2. [Decisions, assumptions and unresolved gates](decisions.md)
3. [Architecture and ownership](architecture.md)
4. [Agent workflow and approval](agent-workflow.md)
5. [Reliability and recovery](reliability.md)
6. [Data model](data-model.md)
7. [API/events/contracts](contracts.md)
8. [Security](security.md)
9. [Observability](observability.md)
10. [Frontend](frontend.md)
11. [Local development and operations](local-development.md) and [backup/restore](operations-backup.md) and [isolated runtime recovery](operations-recovery.md)
12. [Testing](testing.md) and [backlog](backlog.md)
13. [Repository lifecycle](repositories.md)
14. [Technical sources](sources.md) and [delivery evidence](delivery-status.md)

## Architecture decision records

- [001: Four deployment units](adr/001-deployment-units.md)
- [002: Durable scheduling and host execution](adr/002-durable-execution.md)
- [003: Declarative workflows and approval](adr/003-workflows-and-approval.md)
- [004: Local submodules](adr/004-local-submodules.md)
- [005: Observability routing](adr/005-observability.md)

Machine-readable contracts in [packages/contracts](../packages/contracts/README.md) are generated from the implemented API and checked against actual HTTP claims/events/results. Redacted live evidence: [three Codex agents](evidence/codex-three-agent-2026-10-10.json), [recovery and telemetry outage](evidence/codex-recovery-2026-10-10.json), [live CLI cancellation](evidence/codex-cancellation-2026-10-10.json), [Langfuse trace](evidence/langfuse-three-agent-2026-10-10.json), and [isolated backup restoration](evidence/isolated-backup-2026-10-10.json).

Additional native acceptance: [dependency contents](evidence/codex-dependencies-2026-10-10.json) and [three-process resource/API-orchestrator restart](evidence/codex-load-restart-2026-10-10.json).

[Browser acceptance](evidence/frontend-ui-2026-10-10.json), [manual conflict resolution](evidence/codex-conflict-resolution-2026-10-10.json), and [operator actions requiring approval](operator-acceptance.md).

[Native Architect plan, approval and edit evidence](evidence/codex-architect-plan-2026-10-10.json).

[Recovered checkpoint/outbox and mock runtime evidence](evidence/runtime-recovery-2026-10-10.json).

[Native approved skill/scoped MCP, independent review and owned-session evidence](evidence/codex-scoped-capabilities-2026-10-10.json).
