# ADR 006: Persistent provider authority with independent Codex jobs

Status: Accepted local implementation, opt-in backend; native production acceptance pending.

## Context

The user accepted implementing persistent ADF provider profiles and a shared Codex app-server on October 11, 2026. Independent worktrees do not require per-job login. Multiple CLI processes sharing a rotating cache do not establish a single refresh authority. Windows/WSL credential transfer, a new OS account and deployment remain separate permission scopes.

## Decision

Keep stable operator-owned Linux profiles outside repositories/worktrees. Trusted worker configuration selects `CODEX_HOME` / `CLAUDE_CONFIG_DIR`; agent snapshots cannot set auth variables. Claude prefers its supported persistent CLI profile. No automatic login, OAuth generation or Windows credential copy is implemented; `setup-token` remains an optional operator alternative.

Add an opt-in shared Codex backend inside runtime-worker. One independently supervised provider owner launches the pinned 0.157.0 app-server, whose ThreadManager shares one AuthManager and its refresh semaphore. Existing detached job supervisors, API leases, epochs, Redis delivery and Git checks remain authoritative. Each job owns a distinct native thread/turn/worktree/model/skill/MCP configuration. The local same-UID Unix socket is not a new remote service or hostile-code security boundary.

Before dispatch, fsync the generation reference and transfer the exact execution-lock FD. Routine cancellation interrupts only that thread/turn. A job is quiescent only after the pinned `thread/closed` notification, or independently verified death of the recorded whole-server SID. The `thread/unsubscribe` response alone is insufficient. Set unload delay to zero; do not invent a `thread/unload` RPC or infer death from a timeout. Missing proof retains locks and launch material and produces `uncertain`.

Provider crash/restart never replays accepted execution IDs. Recovery proves old-owner death and stops its recorded server SID with checked pidfds before starting a new generation. Incomplete/recycled identities fail closed. Explicit ledger retries receive new execution IDs after the usual stopped-proof fence.

Subprocess mode remains the compatible default, including old tickets. Shared mode requires an explicit private clean profile and refuses user/project Codex configuration/policy layers that the pinned app-server cannot ignore. Per-job environment overrides are unsupported. No workflow/API schema migration or fifth repository is introduced.

## Consequences and verification

The implementation adds bounded local IPC, durable provider/job metadata and a second quiescence condition to existing supervisor recovery. Shared AuthManager serialization is established by pinned source inspection, not a cross-process/cross-machine auth-cache lock. Operators must keep one authority per profile. Same-UID code retains host-account access; strong secret isolation remains deferred.

Offline concurrency/cancellation/crash/auth/cleanup tests and vendored pinned public-schema contracts pass. The actual binary passed unauthenticated initialize/account-read under an empty temporary profile with zero model/thread calls. Native three-session skill/MCP/descendant cleanup, intended UID/profile provisioning and queued control-plane acceptance remain pending; readiness is false. No service or credential migration was executed.

See [module migration and protocol details](../../services/runtime-worker/docs/shared-provider.md), [identity findings](../provider-identity.md), [ADR 002](002-durable-execution.md) and [security](../security.md).

## Primary sources checked October 11, 2026

- [AuthManager refresh semaphore](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/login/src/auth/manager.rs).
- [Shared message processor/ThreadManager](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server/src/message_processor.rs).
- [Thread shutdown and closed notification](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server/src/thread_lifecycle.rs).
- [Unsubscribe processing](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server/src/thread_processor.rs).
- [Public 0.157.0 protocol schemas](https://github.com/openai/codex/tree/rust-v0.157.0/codex-rs/app-server-protocol/schema/json/v2) and [configuration schema](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/core/config.schema.json).
- [Claude authentication/profile documentation](https://code.claude.com/docs/en/authentication).
