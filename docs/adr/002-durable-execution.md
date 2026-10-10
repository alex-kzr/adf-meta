# ADR 002: Durable scheduling and host execution

Status: Accepted design detail.

## Context

CLI/filesystem operations are non-atomic and cannot be fenced by DB epochs alone. Subscription auth stays in WSL.

## Decision

PostgreSQL ledger/outbox + LangGraph checkpoints are authority; Redis is at-least-once transport. WSL worker uses scoped API and local supervisor/OS locks. Lease expiry requires proving prior process death before reassignment.

## Consequences

Supervisor/reconciliation complexity is mandatory. Worktrees are not a sandbox; untrusted code is deferred.

See [architecture](../architecture.md), [decisions](../decisions.md) and [sources](../sources.md).
