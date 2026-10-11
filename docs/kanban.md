# MVP implementation board

The foundation is complete; MVP implementation is in progress. Readiness remains false until all applicable SPEC acceptance evidence exists. User authorization for this task includes implementation, agent delegation, verified incremental local commits and ordinary pushes to the five existing exact origins. It does not authorize force pushes, credentials/security/network changes or new repositories.

| Owner | Scope | State | Acceptance |
| --- | --- | --- | --- |
| Root | Core Compose, contracts, integration, release evidence | In progress | Fresh startup, database grants, recursive clone, acceptance report |
| API | services/api only | Latest scoped capability commit tested locally; published baseline CI passed | Real migration/auth/CRUD/runtime ledger/SSE/artifacts; PostgreSQL and fault tests |
| Worker | services/runtime-worker only | Latest scoped capability/lifecycle commits tested locally; published baseline CI passed | Linux process containment, real adapters, unique worktrees, commit/integration recovery |
| Orchestrator | services/orchestrator only | Implemented, tests and CI passed | LangGraph checkpoints, full graph validation, limits/dependencies/approval/recovery |
| Frontend | frontend only | Implemented, tests/CI and browser DAG passed | Editable workflows/configuration, live run controls/evidence, browser acceptance |
| Observability | Langfuse/Collector configuration and preparation/check scripts | Trace, privacy, outage, isolated backup and recovered mock runtime passed | Official pinned stack, privacy/correlation/outage checks |

No owner edits another owner's files without explicit coordination. Root reviews specification compliance and code quality before integrated commits. Child commits precede umbrella pins. See [implementation tasks](plans/tasks/mvp.md) and [backlog](backlog.md).
