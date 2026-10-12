# Existing-profile metadata diagnostic: completed bounded window

[Public initialize diagnosis](public-initialize-diagnosis.md) proves the full-RO-profile helper is incompatible with pinned SQLite/installation-ID writes; an empty writable control initializes and closes correctly. Three focused source regressions pass; installed0dd, real auth, queue and services remain unchanged. This does not attribute discarded production errors or grant another native window.

October 12, 2026; postchecks completed by 12:06 UTC. **Worker `0dd5ac7b8be6f792921f29bc376e520f3c0754c6` is installed. The single approved metadata window completed with `bounded_rpc_failure`: `initialize` received `transport_closed` after 88 ms.** No native thread or model turn started; skills/MCP/model metadata acceptance was not reached. Provider and consumer remain stopped, the allowance is used, and readiness remains false. [Sanitized evidence](evidence/shared-auth-metadata-completed-2026-10-12.json) contains the fixed outcome and preservation witnesses.

This continues the [scope approved at 06:44 UTC](shared-auth-metadata-scope.md) after the separately completed [Redis preservation repair](redis-repair-runtime-checkpoint.md). The earlier [PEL mismatch checkpoint](shared-auth-metadata-runtime-checkpoint.md) remains historical evidence. No new generation, network/auth operation or queue trial followed from this continuation.

## Exact package and rollback

The published worker pin's [exact-commit CI](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38208061137) passed 386 tests with zero skips. Public source was exported from that exact Git commit; archive SHA-256 is `ce4c2a825562fd8960791a3b725d3a577dd554f1f215cf5f814e4f5afb98c17b`. It was staged as owner-only immutable public source under `/home/adf-worker/ai-factory/tools/worker-source-0dd5ac7b8be6f792921f29bc376e520f3c0754c6`.

A fresh private test venv rehearsed **f5 → 0dd → f5** before installation. All 29 worker Python files and all 27 dependency pins matched each step. Installation changed only the worker package in `tools/worker-venv`; complete source inventory and dependencies were reverified afterward. Existing API `a0e0205` and orchestrator `9932a87`, tool pins, manifests, configuration and personal profiles were retained. No provider or consumer auto-start occurred.

Verified rollback pin is `f5a713a3df44ffdad58aaa80fc3a36157e6c2736`. The reviewed public rollback helper is retained at `tools/metadata-package-0dd-reviewed-v2.py` (0400), SHA-256 `7fff6b34d3939f597556e34e000543351c8fd75be302a6e298a42e17c625eabc`. Its private exact-command receipt is `tools/metadata-rollback-command-v2-20261012.json` (0600). The original helper and receipt remain separate and unchanged. No authentication files or credentials were copied into rollback artifacts. The documented bounded pre-thread RPC failure passed all safety/preservation gates, so rollback was not needed and 0dd remains installed and stopped.

For an authorized package-only rollback, after fresh correlated owner/child death and unchanged preservation gates, the saved command is:

```powershell
wsl -d Ubuntu -u adf-worker -- /home/adf-worker/ai-factory/tools/worker-venv/bin/python -I -B /home/adf-worker/ai-factory/tools/metadata-package-0dd-reviewed-v2.py rollback
```

The helper refuses unproved native death or drift; this command does not reconcile or relaunch any job. No automatic rollback, retry or cleanup schedule was created.

## Reviewed public preflight

The first synthetic-profile namespace check produced negative closure receipts. Those originals were not overwritten or relabeled. A separate read-only follow-up positively established the original PID/session had ended and correlated all four original receipt hashes. An independently reviewed public-only probe then proved namespace feasibility and parent-side isolation and stopped its own session in **7,405 ms**, with zero native owners and no real profile mount. Separate owner-only durable follow-up/probe-pass records retain that evidence.

The operator helper's process scan was corrected to skip only positively known zombies or explicit process disappearance; live/unknown permission errors remain blockers. A zombie enumeration race is a hypothesis for the first failure, not a confirmed causal result. The [Linux namespaces manual](https://man7.org/linux/man-pages/man7/namespaces.7.html) documents access checks on namespace handles; no ptrace/sysctl/dumpability/global security workaround was applied. The final package/owner helpers received independent source review; 24 public fake/AST checks passed. The negative-native-death fence stayed unchanged: the public follow-up exception cannot authorize recovery from an unproved native session.

## One existing-profile attempt

The approved factory arguments and nine-name production environment were preserved, with a fresh synthetic allocation and selected skill/read-only marker MCP fixture. The startup authentication probe was explicitly inert for this diagnostic; no authenticated readiness claim follows from it. The canonical Codex profile was mounted read-only in place, with no auth copying. Private user/mount/PID/network/IPC namespaces excluded host routes and host IPC endpoints; the parent proved those protections before native startup and before the first RPC. No host listeners, firewall or network configuration changed.

Exactly one owner startup attempt was charged for execution `0c5676ef-96ac-40fe-888f-415be6596ace`. `initialize` returned only the safe receipt `transport_closed`, elapsed 88 ms, provider numeric error code null. The full measured owner window was **454 ms**, below 120 seconds; RPC and shutdown bounds were met. No raw upstream response, stderr, account/catalog body, environment value or secret was persisted. The cause of this new failure remains unknown; profile-write, offline network, launcher or provider hypotheses are not established by this receipt. It also cannot explain the three discarded historical failures.

Because initialization failed, `initialized`, `model/list`, `thread/start`, `skills/list`, `mcpServerStatus/list` and `thread/unsubscribe` were not sent. Zero thread attempts means no `thread/closed` event was expected. No `turn/start`, model generation, tool invocation, auth/account RPC, login/refresh/setup-token or paid fallback occurred. The comparison stopped without a retry or second owner.

Correlated launch/death/result receipts prove all owned child/session processes ended. A fresh independent read-only check confirmed the recorded PID absent and SID dead. The fresh allocation lock/materialized skill context was released after those proofs; original three job resources were retained. Profile metadata and configuration seals remained unchanged. The one-use native allowance has **zero remaining attempts**.

## Preserved control plane and final state

Run `67727194-095a-4e9e-afde-6af74ca84247` still has exactly three `uncertain` executions, with unchanged persisted results, no ACK/terminal-persistence flags, no native thread/turn IDs and retained journals/worktrees/selected skills. Their supervisors/native children are stopped, locks reacquirable and synthetic main remains clean at its prior SHA. A stale API `running` run does not authorize a resume.

Final global metrics equal the pre-install snapshot: **active executions 0; queue depth 0; uncertain 3**. Redis PEL contains the same three IDs `1791774765065-0`, `1791774765075-0`, `1791774765082-0`. All 70 entries retain content SHA-256 `aa68cf51d7e76b30837b1d9ed5cff5eee18117bd6d90a2e6861b3334b26e0f89`; default AUTH is rejected. No Redis ACL/config/data/AOF operation, API write, queue consumption, ACK, claim, replay, lease renewal, cancellation or old-result rewrite was performed.

All 69 containers outside Redis/orchestrator retain their precheck IDs, images, status and StartedAt. This continuation performed no service lifecycle operation at all. Langfuse, QA, other users, Windows, firewall, listeners and global Git security settings remain unchanged. Their broader grouping/migration is still unapplied.

## Remaining gates and bounded next work

The approved scope is complete with a safe failure, not successful metadata acceptance. Production settings/skills/MCP selection, subscription/cloud model execution, three-job isolation, single-job cancellation with sibling continuation, crash recovery through API/Redis and complete MVP acceptance remain unverified for this installed release.

Next technical work can inspect public pinned launcher/app-server source and reproduce early initialization using synthetic profiles in a separate source-only fixture. The real profile must not be retried or given write/network access under the used allowance. Another existing-profile/native operation requires its own concrete bounded scope; existing protections are not relaxed to obtain a passing result. The three uncertain old jobs need a separate explicit reconciliation decision without native replay. No new approval question or automatic operation is queued by this checkpoint.
