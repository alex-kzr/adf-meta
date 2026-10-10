# Testing and quality gates

## Foundation checks delivered now

`python scripts/verify.py` checks relative Markdown links across initialized submodules, JSON/OpenAPI internal refs/schema fixtures, Python AST and TOML parsing, Git gitlinks/config consistency, unchanged SPEC hash and suspicious tracked secrets/files. This is a static heuristic scan, not proof against every secret. Module tests verify only implemented scaffold behavior. Bundle export/restore validates exact commit pins in a fresh temporary checkout and no accidental network origin. Delivery evidence distinguishes successful checks from unavailable Docker/live CLI tests.

## MVP test pyramid

| Layer | Tests |
| --- | --- |
| Unit | Transition guards, graph type/cycle/fork validation, canonical hashes, path/argv policy, error/usage mapping, redaction |
| Contract | Pydantic/TS from JSON schema, schema compatibility, provider CLI fixture streams/denials/malformed/unknown events, capability version pins |
| Integration | Real PostgreSQL/Redis/outbox/checkpointer, DB grants, idempotency key reuse/conflict, stale epoch, SSE replay, artifact authorization |
| Worker | Mock subprocess descendants/timeouts/output flood, cwd/path symlink escape, auth required, supervisor journal restart, worktree locks and secret staging |
| Git | Three parallel worktrees, overlapping reservations, dependent-base content, serial integration/conflict, crash after commit before result, original branch unchanged |
| E2E | Fresh WSL startup, plan/edit/approve/versioned run, live monitoring/control/recovery, disabled Langfuse |
| Security | Sentinel credential in every channel, prompt-injected tool expansion, malicious hooks/tests, token/Origin/CSRF assumptions, external-host port denial |

Use MockAdapter before subscriptions and no paid calls in ordinary CI. Live Codex/Claude smoke tests are opt-in on trusted scratch repos with pinned version and accepted permission policy. Store sanitized captured fixture shape, never account credentials or raw sensitive source. Real adapters cannot be called compliant merely because mock passes.

Fault injection targets every row in [reliability](reliability.md), including uncertain live CLI with expired lease. Assert no second writer, one authoritative commit/result and preserved diagnostics. Kill worker/orchestrator/Redis separately; restore DB and artifacts in an isolated install. Calibration measures event p95 and three actual overlapping executions, not concurrent queued states.

Before release: all A1–A12/W1–W8 evidence, dependency/secret review, fresh recursive published clone or bundle restore, migration/backup restore, network trust verification and actual subscription capability gate. Scaffolds fail readiness intentionally. No coverage percentage replaces these invariants.
