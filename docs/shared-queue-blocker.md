# Shared queue acceptance: environment contract blocker

Historical first queue attempt. The user subsequently authorized the narrow worker repair; it is published and installed. See [the current fixed-worker checkpoint](fixed-worker-checkpoint.md) for the next pre-thread blocker and safely stopped runtime. The evidence below remains unchanged.

Observed on October 11, 2026 after the user's personal subscription login. This supersedes the login-pending part of [runtime preparation](dedicated-runtime.md). [Sanitized evidence](evidence/shared-queue-blocker-2026-10-11.json) records the single actual API/Redis probe. Whole runtime/MVP readiness remains false.

## What ran

Both explicit profiles under Ubuntu `adf-worker` report authenticated/ready with the pinned Codex 0.157.0 and Claude Code 2.1.296. Native CLI status was used; no auth file content, token, login or setup-token was requested by the assistant. The fresh drain and retained API rollback dry run pass.

Only the dedicated ADF provider owner and consumer were started, with the exact profile selectors, shared backend and maximum parallelism three. Shared health reports ready/authenticated. The owner generation was `17f5d936-f7a3-4499-94c3-27bbcd718573`. This health result alone does not validate queued execution.

One disposable ext4 project `/home/adf-worker/ai-factory/projects/shared-acceptance-20261011` was initialized without a remote. The actual API registered one bounded native skill, one `adf.scoped-files.v1` MCP server, its exact `read_marker` tool mapping, separate developer/reviewer versions and a complete approval/development/check/review/commit workflow. A policy permits only `evidence.json`, maximum three jobs, zero retries and a three-minute execution deadline. The same run creation idempotency key returns the same run; no duplicate run is created.

Run `67398f61-5346-43c5-ba61-4be1ee0ba004` received an exact snapshot/revision approval under the user's authorized synthetic-test scope. The real orchestrator dispatched execution `3df02fe5-e222-56f8-9862-958451774983` through API/outbox/Redis to the dedicated consumer. Its immutable claim includes the assigned skill/tool/MCP snapshots and explicit shared worker configuration.

## Reproduced failure

The deployed orchestrator request builder at commit `6fe7c1402864210fd8b6c2aed44695436c147f3f` always includes:

```json
{"env_allowlist": ["PATH", "HOME", "LANG", "TERM"]}
```

The pinned worker `8af54fd1590139fa0730e7705d276188c9be3ca3` rejects every nonempty `Request.env_allowlist` in `SharedCodexAdapter.argv`, with `CAPABILITY_UNSUPPORTED`. API claim preserves the field. The actual consumer journal confirms the exact list above and the shared backend/profile selectors. The running orchestrator source hash matches the pinned request builder. This is a real queue interoperability failure, not an authentication failure or provider model failure.

The only execution and run are terminal `failed`, with `process_stopped=true`. The result is durable in API, and Redis message `1791723516958-0` is acknowledged. There are **zero accepted shared provider jobs and zero native thread/model calls**. No paid API fallback or repeated model attempt occurred. The exact environment refusal happens before bridge/thread dispatch; the provider's startup/status handshakes are not model calls.

Stopping after this first blocker avoids spending subscription calls on the remaining scenarios. Native three-job overlap, per-thread settings/skill/MCP behavior, separate cancellation and active crash recovery remain **unperformed**, not passed. Immutable capability snapshots transferred through the queue and skill materialization cleanup are verified; that does not prove a provider read the skill or invoked MCP.

## Restored safe state

The probe supervisor and all its owned sessions are proved stopped, and the worktree lock is reacquired. Temporary native skill materialization is removed. Fixture main remains `0f941376a1439819f0d70cb1ca03873e3466c626`, its default checkout is clean and it has no remote. The failed worktree/journal and synthetic API definitions remain for diagnosis; no destructive cleanup was attempted.

Only recorded new consumer/provider sessions were stopped, including verified native server session shutdown. No new ADF execution remains active. The prepared tools/profiles and authorized API update remain intact; the old worker installation/API image and exact settings rollback remain available. Existing API/UI/Langfuse probes return HTTP 200 and `runtime_ready=false`. No other service, account permission, Windows/firewall/listener or global Git security setting was modified.

## Historical repair proposal (subsequently applied)

Current runtime authorization pins worker `8af54fd` and excludes updating other services. Changing orchestrator deployment or installing a different worker commit therefore needs a separate scope decision. No pinned implementation was silently edited.

The narrow worker-only proposal is to recognize **exactly** the legacy orchestrator baseline selector list at trusted request adaptation for shared Codex and normalize it to an empty per-job list. The provider owner already uses one fixed sanitized operator environment. Do not accept arbitrary per-job environment overrides, selectors or values, and do not forward environment data from an agent or queue frame. Keep the shared adapter's direct override refusal and auth/profile controls.

Before adopting a new worker commit, review that normalization against the actual orchestrator-generated request and add contract tests for the accepted exact baseline, rejection of other lists, fixed HOME/PATH/profile selection and exclusion of secret environment variables. Then run the worker suite/lint/type/security checks, update the umbrella gitlink, verify installed bytes and rollback, and repeat the bounded native queue acceptance with explicit new run/execution identities. Native results must determine readiness; offline contract tests cannot replace the requested acceptance. Alternative repair in orchestrator would require changing another service and is outside the current deployment scope.
