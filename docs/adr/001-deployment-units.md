# ADR 001: Four deployment units

Status: Accepted from SPEC v0.2.

## Context

Four processes have distinct UI/HTTP/scheduling/host-execution boundaries. Avoid needless microservices and copies of external products.

## Decision

Keep React frontend, FastAPI API, LangGraph orchestrator and WSL runtime-worker independently deployable in four repos. Keep infra/contracts/docs in umbrella. Integrator, planner and registries are roles/components, not services.

## Consequences

Shared DB requires explicit ownership/grants; release pins coordinate contracts. A future service split needs measured need and ADR.

See [architecture](../architecture.md), [decisions](../decisions.md) and [sources](../sources.md).
