# adf-meta - AI Development Factory umbrella

This repository is [adf-meta](https://github.com/alex-kzr/adf-meta), the ADF umbrella. ADF is a local, single-user development factory for planning tasks, running coding agents in parallel Git worktrees, testing, reviewing and integrating their commits into a separate branch. Windows 11 + Ubuntu WSL2 + Docker Desktop is the target runtime. React/TypeScript provides the UI, FastAPI the control API, LangGraph the orchestration, and a host Python worker runs Codex and Claude Code CLI adapters.

**Status: MVP acceptance remains incomplete; readiness is false.**
[Approved WSL runtime result](docs/shared-wsl-mask-source-checkpoint.md#observed-bounded-api-redis-result):
worker `a342879` installed; seven native Codex turns confirmed three-way parallelism,
assigned skills/MCP and consumer recovery. Two task commits passed; a third review
and repair dependency guard stopped the run before integration. Provider/consumer
are stopped, all new deliveries are ACKed, PEL is zero and the original main is clean.
API `a0e0205`, orchestrator `9932a87` and other services/settings remain unchanged.
[Preservation evidence](docs/shared-wsl-preservation-checkpoint.md) and the
[bounded acceptance plan](docs/shared-wsl-live-acceptance-plan.md) retain the exact
scope, rollback and remaining gates. No paid API fallback or credential copy.

Operational status belongs in protected local reports. Earlier [metadata](docs/shared-auth-metadata-completed-checkpoint.md),
[Redis preservation](docs/redis-repair-runtime-checkpoint.md) and [runtime deployment](docs/shared-patch-runtime-checkpoint.md)
records are dated history. Source fixtures do not establish current queue/service state or authenticated
MVP acceptance. [Implementation status](docs/implementation-status.md), [acceptance status](docs/acceptance-status.md)
and [release history](docs/release-checkpoint.md) retain the remaining gates.

Start with [documentation](docs/README.md), [product/acceptance](docs/product.md), [architecture](docs/architecture.md), [local development](docs/local-development.md) and [backlog](docs/backlog.md). The original [SPEC.md](SPEC.md) remains unchanged; [decisions](docs/decisions.md) distinguish requirements from adopted assumptions.

| Submodule | GitHub repository | Responsibility |
| --- | --- | --- |
| [frontend](frontend/README.md) | [adf-web](https://github.com/alex-kzr/adf-web) | React UI and monitoring |
| [services/api](services/api/README.md) | [adf-api](https://github.com/alex-kzr/adf-api) | Validated control API, persistence facade, SSE |
| [services/orchestrator](services/orchestrator/README.md) | [adf-orchestrator](https://github.com/alex-kzr/adf-orchestrator) | Durable DAG scheduling and recovery |
| [services/runtime-worker](services/runtime-worker/README.md) | [adf-runtime-worker](https://github.com/alex-kzr/adf-runtime-worker) | WSL CLI execution and Git worktrees |

PostgreSQL, Redis, OpenTelemetry Collector and Langfuse remain external products. Contracts and deployment configuration live here. Submodule commit pins define an integrated release.

Current live results and remaining release gates: [acceptance status](docs/acceptance-status.md).

Current source and installed scope: [operator-owned named native permissions](docs/shared-native-read-policy.md), [ADR 009](docs/adr/009-operator-owned-native-read-policy.md), [shared-patch generation and isolated Python checks](docs/shared-patch-source.md), [ADR 008](docs/adr/008-shared-patch-and-isolated-checks.md). The [October 12 runtime checkpoint](docs/shared-patch-runtime-checkpoint.md) distinguishes installation, no-model evidence and blocked live acceptance. Production-parity settings/skills/MCP, generation, individual cancellation, recovery, review/commit/integration and Node/build checks remain open gates.

Historical October 11 result: [the sealed-policy deployment and bounded queue trial](docs/shared-policy-runtime-checkpoint.md) installed worker `13c4624a`. Three simultaneous native turns each completed scoped MCP, then generation failed closed; results were durable/ACKed and writers stopped. Those historical ACKs do not apply to the current three uncertain deliveries.

[ADR 007](docs/adr/007-sealed-shared-profile-policy.md) and [its exact deployment scope](docs/shared-policy-deployment.md) describe the opt-in guard. Historical [doctor repair](docs/doctor-profile-repair.md), [fixed-worker checkpoint](docs/fixed-worker-checkpoint.md) and [preserving rename/resumed trial](docs/shared-resumed-checkpoint.md) retain their dated evidence.

## Repositories and offline restoration

All four directories are real Git submodules. Their origins and `.gitmodules` now use the exact GitHub URLs supplied by the user; the umbrella origin is `https://github.com/alex-kzr/adf-meta`. Initial read-only `ls-remote` checks succeeded for all five repositories and advertised no refs. The authorized publication pushed modules before the umbrella and verified a fresh GitHub recursive clone with exact pins; see the delivery report for results. All four child repositories have successful GitHub CI for their current published commits; umbrella CI includes the same contract and offline restoration gates. Export committed repositories with `python scripts/export-bundles.py .bootstrap/export`, then restore with `python scripts/bootstrap-local.py <export-directory> <new-empty-destination>`. Read [repository lifecycle](docs/repositories.md) for the exact user push sequence and offline restoration. Bundles are delivery artifacts, not committed source.

```powershell
python scripts/verify.py
python scripts/export-bundles.py .bootstrap/export
```

Each module README explains its implemented commands and remaining acceptance gates. Successful diagnostics do not satisfy MVP acceptance. Publication requires explicit user authorization; it does not grant a standing automatic push policy.
