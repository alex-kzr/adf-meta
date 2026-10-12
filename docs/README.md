# Development documentation

[Approved local-profile metadata diagnostic](shared-auth-metadata-runtime-checkpoint.md): preflight is blocked by unavailable existing Docker/API/Redis services. Installed f5 worker and stopped old jobs are preserved; no installation, native test or queue operation occurred.

[Latest source-only RPC diagnostics and persistent-owner checkpoint](shared-rpc-source-checkpoint.md), with [sanitized evidence](evidence/shared-rpc-source-2026-10-12.json): safe error categories and two owners with six metadata threads each pass through native and pinned Node/npm startup, with confirmed closure and separate skills/MCP/model/policy witnesses. Installed runtime and pending deliveries are unchanged; no native model turn or authenticated-route acceptance. [Proposed next local-profile metadata scope](shared-auth-metadata-scope.md) retains a stopped consumer, readonly auth and unshared networking.

[Current installed runtime and bounded API/Redis checkpoint](shared-patch-runtime-checkpoint.md), with [sanitized evidence](evidence/shared-patch-deployment-2026-10-12.json): worker `f5a713a` and orchestrator `9932a87` installed; rollback and no-model gates verified. Actual native startup remains uncertain, provider/consumer are stopped, and three deliveries remain unACKed. Readiness is false; live generation, settings/skills/MCP, cancellation, recovery and the full workflow remain unverified.

Source/design records: [operator-owned native read permissions](shared-native-read-policy.md), [ADR 009](adr/009-operator-owned-native-read-policy.md), [exact source checkpoint](shared-native-read-source-checkpoint.md), [shared-patch implementation](shared-patch-source.md), [ADR 008](adr/008-shared-patch-and-isolated-checks.md), and [historical separately approved deployment proposal](shared-patch-deployment.md). These are separate from actual runtime acceptance.

Historical October 11 [sealed-policy deployment and trial](shared-policy-runtime-checkpoint.md) and [evidence](evidence/shared-profile-policy-runtime-2026-10-11.json) describe installed `13c4624a`, scoped MCP turns and their ACKs; the October 12 checkpoint supersedes their installed-state result.

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

[Doctor explicit-profile source repair](doctor-profile-repair.md): selected profiles reach native diagnostics; 158 worker tests and pinned empty-profile smoke pass. Source `859cc534` is separate from installed runtime `a8bb1cc`; the operator rename and native queue acceptance remain pending.

## Architecture decision records

- [001: Four deployment units](adr/001-deployment-units.md)
- [002: Durable scheduling and host execution](adr/002-durable-execution.md)
- [003: Declarative workflows and approval](adr/003-workflows-and-approval.md)
- [004: Local submodules](adr/004-local-submodules.md)
- [005: Observability routing](adr/005-observability.md)
- [006: Persistent provider authority and independent Codex jobs](adr/006-provider-profile-ownership.md)
- [007: Opt-in sealed shared-profile trust policy](adr/007-sealed-shared-profile-policy.md), with [18 no-model native thread probes and pinned source evidence](evidence/shared-profile-config-research-2026-10-11.json), [exact deployment scope](shared-policy-deployment.md) and [actual bounded runtime result](shared-policy-runtime-checkpoint.md)
- [008: Guarded shared patches and isolated single-process Python checks](adr/008-shared-patch-and-isolated-checks.md), with [current source release](shared-patch-source-checkpoint.md), [offline evidence](evidence/shared-patch-source-2026-10-11.json) and [separate installation/acceptance scope](shared-patch-deployment.md)

Machine-readable contracts in [packages/contracts](../packages/contracts/README.md) are generated from the implemented API and checked against actual HTTP claims/events/results. Redacted live evidence: [three Codex agents](evidence/codex-three-agent-2026-10-10.json), [recovery and telemetry outage](evidence/codex-recovery-2026-10-10.json), [live CLI cancellation](evidence/codex-cancellation-2026-10-10.json), [Langfuse trace](evidence/langfuse-three-agent-2026-10-10.json), and [isolated backup restoration](evidence/isolated-backup-2026-10-10.json).

Additional native acceptance: [dependency contents](evidence/codex-dependencies-2026-10-10.json) and [three-process resource/API-orchestrator restart](evidence/codex-load-restart-2026-10-10.json).

[Browser acceptance](evidence/frontend-ui-2026-10-10.json), [manual conflict resolution](evidence/codex-conflict-resolution-2026-10-10.json), and [operator actions requiring approval](operator-acceptance.md).

[Native Architect plan, approval and edit evidence](evidence/codex-architect-plan-2026-10-10.json).

[Recovered checkpoint/outbox and mock runtime evidence](evidence/runtime-recovery-2026-10-10.json).

[Native approved skill/scoped MCP, independent review and owned-session evidence](evidence/codex-scoped-capabilities-2026-10-10.json).

[Provider identity reuse across Windows, WSL and parallel worktrees](provider-identity.md): initial read-only findings, followed by an opt-in shared Codex implementation and persistent Claude profiles; no credential changes. [Migration, protocol and remaining native gates](../services/runtime-worker/docs/shared-provider.md).

[Shared-provider implementation evidence](evidence/provider-shared-2026-10-11.json): 134 Linux tests, pinned schemas and native unauthenticated handshake; zero model calls/deployment.

[Publication and dedicated-account evidence](evidence/publication-account-2026-10-11.json): all five implementation heads published with successful CI and a fresh recursive clone; `adf-worker` created with private directories and exactly two approved service files.

[Dedicated runtime preparation, exact personal-login commands and API rollback](dedicated-runtime.md), with [sanitized deployment evidence](evidence/dedicated-runtime-2026-10-11.json): pinned tools/worker and private profiles installed, only API updated. The post-login queue update below records the current blocker.

[Post-login shared queue blocker and proposed repair](shared-queue-blocker.md), with [actual API/Redis evidence](evidence/shared-queue-blocker-2026-10-11.json): both logins and owner/consumer startup pass; one bounded probe fails on the orchestrator/shared-worker environment contract before any model calls. The new processes are stopped safely and native acceptance remains blocked.

[Current fixed-worker installation and remaining ancestor-profile blocker](fixed-worker-checkpoint.md), with [sanitized actual queue evidence](evidence/worker-fixed-queue-2026-10-11.json): worker `a8bb1cc` is published, passes 146 tests/CI and is byte-verified in the dedicated venv. Three claims reach the shared owner, then stop before native threads on `/home/adf-worker/.codex` discovery. No model calls occurred; native acceptance remains blocked and processes are stopped.
