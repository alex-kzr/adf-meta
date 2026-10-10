# ADF — AI Development Factory

ADF is a local, single-user development factory for planning tasks, running coding agents in parallel Git worktrees, testing, reviewing and integrating their commits into a separate branch. Windows 11 + Ubuntu WSL2 + Docker Desktop is the target runtime. React/TypeScript provides the UI, FastAPI the control API, LangGraph the orchestration, and a host Python worker runs Codex and Claude Code CLI adapters.

**Status: design and repository foundation.** The documents describe the intended MVP. The scaffold provides diagnostics, a workflow validator, a mock event producer and a frontend starting screen. It does not execute a real factory workflow, access subscriptions or implement project/task CRUD. See [delivery status](docs/delivery-status.md).

Start with [documentation](docs/README.md), [product/acceptance](docs/product.md), [architecture](docs/architecture.md), [local development](docs/local-development.md) and [backlog](docs/backlog.md). The original [SPEC.md](SPEC.md) remains unchanged; [decisions](docs/decisions.md) distinguish requirements from adopted assumptions.

| Submodule | Proposed GitHub name | Responsibility |
| --- | --- | --- |
| [frontend](frontend/README.md) | adf-web | React UI and monitoring |
| [services/api](services/api/README.md) | adf-api | Validated control API, persistence facade, SSE |
| [services/orchestrator](services/orchestrator/README.md) | adf-orchestrator | Durable DAG scheduling and recovery |
| [services/runtime-worker](services/runtime-worker/README.md) | adf-runtime-worker | WSL CLI execution and Git worktrees |

PostgreSQL, Redis, OpenTelemetry Collector and Langfuse remain external products. Contracts and deployment configuration live here. Submodule commit pins define an integrated release.

## Before publication

All four directories are real Git submodules. Current origins are real local bare repositories under ignored `.bootstrap/remotes/`; no GitHub URLs have been invented. **A clean recursive clone is not portable until modules are published.** Export committed repositories with `python scripts/export-bundles.py .bootstrap/export`, then restore with `python scripts/bootstrap-local.py <export-directory> <new-empty-destination>`. Read [repository lifecycle](docs/repositories.md) before assigning remotes. Bundles are delivery artifacts, not committed source.

```powershell
python scripts/verify.py
python scripts/export-bundles.py .bootstrap/export
```

Each module README explains its scaffold commands. Successful diagnostics do not satisfy MVP acceptance. Nothing is pushed or created on GitHub by this foundation.
