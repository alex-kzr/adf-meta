# adf-meta - AI Development Factory umbrella

This repository is [adf-meta](https://github.com/alex-kzr/adf-meta), the ADF umbrella. ADF is a local, single-user development factory for planning tasks, running coding agents in parallel Git worktrees, testing, reviewing and integrating their commits into a separate branch. Windows 11 + Ubuntu WSL2 + Docker Desktop is the target runtime. React/TypeScript provides the UI, FastAPI the control API, LangGraph the orchestration, and a host Python worker runs Codex and Claude Code CLI adapters.

**Status: MVP implementation and integration verification in progress.** Current source implements the control API, durable workflow scheduler, supervised WSL worker and connected UI. Core containers and official Langfuse/Collector have started successfully. A full three-Codex DAG, independent reviews and integration passed; a second run completed through consumer/Redis restart and Langfuse outage. Isolated application-data restoration and a recovered five-operation mock runtime passed. Claude WSL, least privilege and remaining security/recovery acceptance are still open; runtime readiness remains false. See [current implementation status](docs/implementation-status.md), [the local/published release checkpoint](docs/release-checkpoint.md) and [historical delivery evidence](docs/delivery-status.md).

Start with [documentation](docs/README.md), [product/acceptance](docs/product.md), [architecture](docs/architecture.md), [local development](docs/local-development.md) and [backlog](docs/backlog.md). The original [SPEC.md](SPEC.md) remains unchanged; [decisions](docs/decisions.md) distinguish requirements from adopted assumptions.

| Submodule | GitHub repository | Responsibility |
| --- | --- | --- |
| [frontend](frontend/README.md) | [adf-web](https://github.com/alex-kzr/adf-web) | React UI and monitoring |
| [services/api](services/api/README.md) | [adf-api](https://github.com/alex-kzr/adf-api) | Validated control API, persistence facade, SSE |
| [services/orchestrator](services/orchestrator/README.md) | [adf-orchestrator](https://github.com/alex-kzr/adf-orchestrator) | Durable DAG scheduling and recovery |
| [services/runtime-worker](services/runtime-worker/README.md) | [adf-runtime-worker](https://github.com/alex-kzr/adf-runtime-worker) | WSL CLI execution and Git worktrees |

PostgreSQL, Redis, OpenTelemetry Collector and Langfuse remain external products. Contracts and deployment configuration live here. Submodule commit pins define an integrated release.

Current live results and remaining release gates: [acceptance status](docs/acceptance-status.md).

Latest runtime checkpoint: the [fixed worker is published and installed](docs/fixed-worker-checkpoint.md). Its 146 tests and exact-commit CI pass. The bounded queue attempt reaches the shared owner but is blocked before any model call by the unchanged ancestor `.codex` guard. Dedicated owner/consumer are safely stopped; login remains completed and runtime readiness remains false.

Latest source repair: [doctor now requires explicit operator profiles](docs/doctor-profile-repair.md), published at worker `859cc534` with 158 passing Linux tests and exact-commit CI. The execution venv remains at `a8bb1cc`; no runtime replacement, pending `.codex` rename or further model run accompanied this source change.

## Repositories and offline restoration

All four directories are real Git submodules. Their origins and `.gitmodules` now use the exact GitHub URLs supplied by the user; the umbrella origin is `https://github.com/alex-kzr/adf-meta`. Initial read-only `ls-remote` checks succeeded for all five repositories and advertised no refs. The authorized publication pushed modules before the umbrella and verified a fresh GitHub recursive clone with exact pins; see the delivery report for results. All four child repositories have successful GitHub CI for their current published commits; umbrella CI includes the same contract and offline restoration gates. Export committed repositories with `python scripts/export-bundles.py .bootstrap/export`, then restore with `python scripts/bootstrap-local.py <export-directory> <new-empty-destination>`. Read [repository lifecycle](docs/repositories.md) for the exact user push sequence and offline restoration. Bundles are delivery artifacts, not committed source.

```powershell
python scripts/verify.py
python scripts/export-bundles.py .bootstrap/export
```

Each module README explains its implemented commands and remaining acceptance gates. Successful diagnostics do not satisfy MVP acceptance. Publication requires explicit user authorization; it does not grant a standing automatic push policy.
