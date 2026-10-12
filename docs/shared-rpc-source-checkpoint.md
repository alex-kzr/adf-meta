# Shared RPC source repair and persistent-owner checkpoint

October 12, 2026. **Source repair and no-model verification passed. The original live failure cause remains unknown; readiness is false.** Installed worker `f5a713a` and orchestrator `9932a87`, operator manifests/authentication and the three uncertain deliveries are unchanged. No new source was installed, consumer resumed, delivery ACKed/replayed or native model turn started. [Sanitized evidence](evidence/shared-rpc-source-2026-10-12.json), [worker diagnostic contract](../services/runtime-worker/docs/shared-rpc-diagnostics.md) and the [installed runtime checkpoint](shared-patch-runtime-checkpoint.md) separate these results.

## Exact source release

Worker source `3ce3c2ab5cd1d6af4e51a2ca076515f18df26431` preserves safe RPC outcome metadata and adds an actual persistent-owner metadata fixture. Its [exact-commit CI](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38205561482) runs static checks, the complete Linux suite and pinned public native fixtures. API `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca`, orchestrator `9932a87e676b651c7ff2eb89246b900c6d0f843e` and frontend `92bfa64f38202872dbf2999d9343884a12036959` source pins remain unchanged. The umbrella records the worker gitlink after the child commit. SPEC, dependency locks and repository origins are unchanged.

The local full suite at the implementation commit passed **385 tests, zero skips, 116.64 seconds**. Initial worker CI passed 384 tests but exposed a test-only Unix socket pathname overflow in the new generation-reset fixture. The final source changes only that fixture basename from `recovered-initialize` to `r`; the affected regression passed under a deliberately long CI-style base path (**1 passed, 136 deselected, 0.54 seconds**). Production Python sources are unchanged by that portability fix; final exact-commit CI runs the complete suite again. Ruff and strict mypy across 29 source files passed; Bandit found no medium/high issues (17 low findings remain). Independent read-only review passed after fixing owner/skills/lock cleanup order, stale generation error attribution and concurrent model verification. Fake regressions cover closure failure, initialization stages, unproved shutdown, malformed error/identity frames, bounded transport wakeups, deterministic uncertain writes, private-payload exclusion and lock/no-replay fencing.

## Proven defect and repair

The old RPC transport collapsed explicit provider errors and invalid responses into `PROVIDER_FAILED`; EOF used a synthetic JSON-RPC error, losing the distinction from an upstream error. The owner then conservatively replaced a post-spawn failure without a thread ID with `EXECUTION_UNCERTAIN`, discarding its original diagnostic category.

The repair keeps `provider_error`, `malformed_response`, `transport_closed`, `response_timeout` and `write_uncertain` distinct in closed receipts: fixed method/phase/outcome, bounded elapsed milliseconds and a recognized numeric error code or null. Raw messages/data/stderr and full provider payloads never become journal diagnostics. Local transport failure uses a typed sentinel; malformed native identity values are rejected instead of coerced into strings. The original job failure survives separate cleanup errors; owner initialization diagnostics reset on each new generation.

The safety conclusion is unchanged: an error after thread-spawn intent cannot prove that no thread exists. Unknown outcomes retain locks and remain uncertain until owned thread/session death is proved. No success conversion or automatic retry/replay was introduced.

## Actual native metadata result and parity boundary

One actual Codex 0.157.0 app-server handled **three sequential and three concurrent thread/start requests**, producing six unique native IDs. It started from `providers/codex` with production-factory baseline flags/configuration, empty skills/MCP and an empty synthetic profile. Requests used allocator-bound worktrees, the actual adapter configuration and durable capability reconstruction. The real default model and explicit native-catalog model selections were verified in both stages.

The three scopes had no capabilities, selected `scoped` plus `files.read_marker`, or selected `alternate` plus `alternatefiles.read_file`. Each returned its own skill/MCP inventory and exact active named permission/workspace/cwd/network/provider witnesses. Both request and response matched the pinned generated schemas. Every unsubscribe was followed by correlated `thread/closed`; the owner stopped before skills or locks were cleaned up. Failed proof retains synthetic resources rather than treating an unsubscribe response as quiescence.

No native turn/auth method was called. Model tool invocation, subscription execution and the live workflow remain unverified. The older per-job metadata/standalone command canary remains a separate filesystem regression, not proof of singleton startup parity.

The fixture invokes the exact verified Rust binary directly. The installed npm/Node wrapper, pinned Node PATH/interpreter, actual account/refresh/catalog/cloud policy and authenticated network route are **not reproduced**. These are remaining comparison dimensions, not established causes. Public QA runtimes and synthetic files are mounted in an outer namespace with unshared networking; actual home/auth/service configuration is absent.

The pinned [upstream configuration manager](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server/src/config_manager.rs) appends request overrides after CLI overrides, and the [model metadata protocol](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server-protocol/src/protocol/v2/model.rs) permits catalog/default witnesses without turns. Source and actual metadata evidence reject the general claim that startup baseline always wins. They do not recover the three discarded original upstream replies.

## Three existing uncertain jobs are a separate matter

Read-only post-QA checks confirmed installed worker f5 source hashes, stopped provider/consumer/native/supervisors, unchanged trust/configuration, reacquired locks and an unchanged clean synthetic main checkout. Run `67727194-095a-4e9e-afde-6af74ca84247` still reports `running`; its three executions remain `uncertain`, and Redis PEL remains three. Journals, materialized skills and worktrees are retained. No cancellation request, terminal rewrite, ACK, replay or deployment was sent by this source repair.

## Minimal next separately approved scope

The old raw RPC replies were intentionally discarded and cannot be reconstructed from null IDs or later `server_session_dead`. Further empty-profile successes cannot identify that historical upstream cause.

A useful next diagnostic scope would install exactly this published worker into the stopped dedicated venv with verified f5 rollback, retain orchestrator/API/manifests/profile settings and keep the consumer stopped. Prepare one fresh synthetic **metadata-only** comparison with the exact installed Node launcher/PATH and existing account profile, production flags and assigned policy/skills/MCP. Enforce a method allowlist with no turn/start, no paid API fallback, a short fixed wall bound and durable safe RPC receipts; prove owner/thread shutdown before releasing resources. Profile authentication must remain operator-owned; no login/setup-token or credential copies. That experiment requires a concrete separately approved runtime scope and is not performed by source publication.

Old uncertain jobs must remain fenced and unACKed during that comparison. Any later terminal reconciliation of those three jobs is a separate explicit operation with their preserved stopped/lock evidence; it must never relaunch their native work. Full bounded workflow acceptance remains a later gate.
