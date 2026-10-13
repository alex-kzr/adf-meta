# adf-meta - AI Development Factory umbrella

This repository is [adf-meta](https://github.com/alex-kzr/adf-meta), the ADF umbrella. ADF is a local, single-user development factory for planning tasks, running coding agents in parallel Git worktrees, testing, reviewing and integrating their commits into a separate branch. Windows 11 + Ubuntu WSL2 + Docker Desktop is the target runtime. React/TypeScript provides the UI, FastAPI the control API, LangGraph the orchestration, and a host Python worker runs Codex and Claude Code CLI adapters.

**Status: historical import is fixed; dependent native review and MVP acceptance remain incomplete.**
The [current checkpoint](docs/accepted-commit-lineage-checkpoint.md) records installed
worker `e93f421`, verified rollback and successful import of three accepted commits
across provider generations. Both bounded dependent pipelines stop at native review.
The final authorized structural review-context cycle failed verification; its source
is preserved privately and remains uninstalled. Fresh checks after separately owned
Docker recovery confirm healthy ADF services, empty active/queue/PEL state and preserved
worker settings. Earlier 13 Codex + two Claude evidence and both failed windows remain
unchanged. Provider owner and consumer are stopped. No new model window ran; readiness
is false. API `0724e98` and orchestrator `630b37e` retain their installed pins. Worker
source pin `1dc7ee6` changes only contract-fixture provenance, with runtime code identical
to installed `e93f421`. No paid API fallback, login or credential copy occurred.

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

Current source and installed scope: [operator-owned named native permissions](docs/shared-native-read-policy.md), [ADR 009](docs/adr/009-operator-owned-native-read-policy.md), [shared-patch generation and isolated Python checks](docs/shared-patch-source.md), [ADR 008](docs/adr/008-shared-patch-and-isolated-checks.md). The [October 12 runtime checkpoint](docs/shared-patch-runtime-checkpoint.md) distinguishes installation, no-model evidence and blocked live acceptance. Current results and remaining gates are in the checkpoint; earlier deployment records retain their dated scope.

Historical October 11 result: [the sealed-policy deployment and bounded queue trial](docs/shared-policy-runtime-checkpoint.md) installed worker `13c4624a`. Three simultaneous native turns each completed scoped MCP, then generation failed closed; results were durable/ACKed and writers stopped. Later reconciliation and dated delivery results are recorded in the current checkpoint; live availability is separately unverified.

[ADR 007](docs/adr/007-sealed-shared-profile-policy.md) and [its exact deployment scope](docs/shared-policy-deployment.md) describe the opt-in guard. Historical [doctor repair](docs/doctor-profile-repair.md), [fixed-worker checkpoint](docs/fixed-worker-checkpoint.md) and [preserving rename/resumed trial](docs/shared-resumed-checkpoint.md) retain their dated evidence.

## Repositories and offline restoration

All four directories are real Git submodules. Their origins and `.gitmodules` now use the exact GitHub URLs supplied by the user; the umbrella origin is `https://github.com/alex-kzr/adf-meta`. Initial read-only `ls-remote` checks succeeded for all five repositories and advertised no refs. The authorized publication pushed modules before the umbrella and verified a fresh GitHub recursive clone with exact pins; see the delivery report for results. Exact published snapshots and CI evidence are recorded in the checkpoints; umbrella CI includes contract and offline restoration gates. Export committed repositories with `python scripts/export-bundles.py .bootstrap/export`, then restore with `python scripts/bootstrap-local.py <export-directory> <new-empty-destination>`. Read [repository lifecycle](docs/repositories.md) for the exact user push sequence and offline restoration. Bundles are delivery artifacts, not committed source.

```powershell
python scripts/verify.py
python scripts/export-bundles.py .bootstrap/export
```

Each module README explains its implemented commands and remaining acceptance gates. Successful diagnostics do not satisfy MVP acceptance. Publication requires explicit user authorization; it does not grant a standing automatic push policy.
