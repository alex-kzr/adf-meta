# adf-meta - AI Development Factory umbrella

This repository is [adf-meta](https://github.com/alex-kzr/adf-meta), the ADF umbrella. ADF is a local, single-user development factory for planning tasks, running coding agents in parallel Git worktrees, testing, reviewing and integrating their commits into a separate branch. Windows 11 + Ubuntu WSL2 + Docker Desktop is the target runtime. React/TypeScript provides the UI, FastAPI the control API, LangGraph the orchestration, and a host Python worker runs Codex and Claude Code CLI adapters.

**Status: MVP implementation and integration verification in progress.** Current source implements the control API, durable workflow scheduler, supervised WSL worker and connected UI. Core containers and official Langfuse/Collector have started successfully. Full provider/concurrency/recovery/security acceptance is still pending; runtime readiness remains false. See [current implementation status](docs/implementation-status.md) and [historical delivery evidence](docs/delivery-status.md).

Start with [documentation](docs/README.md), [product/acceptance](docs/product.md), [architecture](docs/architecture.md), [local development](docs/local-development.md) and [backlog](docs/backlog.md). The original [SPEC.md](SPEC.md) remains unchanged; [decisions](docs/decisions.md) distinguish requirements from adopted assumptions.

| Submodule | GitHub repository | Responsibility |
| --- | --- | --- |
| [frontend](frontend/README.md) | [adf-web](https://github.com/alex-kzr/adf-web) | React UI and monitoring |
| [services/api](services/api/README.md) | [adf-api](https://github.com/alex-kzr/adf-api) | Validated control API, persistence facade, SSE |
| [services/orchestrator](services/orchestrator/README.md) | [adf-orchestrator](https://github.com/alex-kzr/adf-orchestrator) | Durable DAG scheduling and recovery |
| [services/runtime-worker](services/runtime-worker/README.md) | [adf-runtime-worker](https://github.com/alex-kzr/adf-runtime-worker) | WSL CLI execution and Git worktrees |

PostgreSQL, Redis, OpenTelemetry Collector and Langfuse remain external products. Contracts and deployment configuration live here. Submodule commit pins define an integrated release.

## Repositories and offline restoration

All four directories are real Git submodules. Their origins and `.gitmodules` now use the exact GitHub URLs supplied by the user; the umbrella origin is `https://github.com/alex-kzr/adf-meta`. Initial read-only `ls-remote` checks succeeded for all five repositories and advertised no refs. The authorized publication pushed modules before the umbrella and verified a fresh GitHub recursive clone with exact pins; see the delivery report for results. Pinned CI workflows are added in the implementation branch; remote run results require publication and verification. Export committed repositories with `python scripts/export-bundles.py .bootstrap/export`, then restore with `python scripts/bootstrap-local.py <export-directory> <new-empty-destination>`. Read [repository lifecycle](docs/repositories.md) for the exact user push sequence and offline restoration. Bundles are delivery artifacts, not committed source.

```powershell
python scripts/verify.py
python scripts/export-bundles.py .bootstrap/export
```

Each module README explains its implemented commands and remaining acceptance gates. Successful diagnostics do not satisfy MVP acceptance. Publication requires explicit user authorization; it does not grant a standing automatic push policy.
