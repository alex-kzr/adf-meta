# Proposed authenticated metadata-only comparison

Subsequent runtime update: the separately approved [Redis repair](redis-repair-runtime-checkpoint.md) completed with exact PEL=3 and unchanged AOF/data. The historical PEL=0 observations below remain dated evidence. The metadata/package diagnostic and Langfuse migration were not executed by that repair; host consumer/provider remain stopped.

October 12, 2026. **Concrete next scope; not executed by source publication.** The operator subsequently authorized this scope at 06:44 UTC; the [execution checkpoint](shared-auth-metadata-runtime-checkpoint.md) stopped at prerequisite inspection before installation/native startup; a separately authorized Docker restoration later exposed Redis PEL=0 instead of required3. Use only the exact published worker pin and successful exact-commit CI in the [source checkpoint](shared-rpc-source-checkpoint.md#exact-source-release). The public Node/npm launcher, production factory environment/arguments and empty-profile persistent-owner check already pass; do not deploy an intermediate pin to investigate that public difference again. Existing local-profile behavior is the next comparison; cloud/network behavior and the discarded historical RPC cause remain separate questions.

## Paths and preserved state

All runtime paths below are under `/home/adf-worker/ai-factory`, owned by the existing unprivileged `adf-worker` account. Current installed worker is `f5a713a3df44ffdad58aaa80fc3a36157e6c2736`. API `a0e0205`, orchestrator `9932a87`, provider CLI pins and dependencies stay unchanged. The installed runtime is stopped. The three `uncertain` executions in run `67727194-095a-4e9e-afde-6af74ca84247` and its three Redis pending deliveries remain fenced; a stale API `running` status is not permission to resume them.

| Item | Exact path / boundary |
| --- | --- |
| Package to update | `tools/worker-venv`, worker package only |
| Existing profile, never copied | `provider-profiles/codex` |
| Public launcher | `tools/provider-cli/bin/codex` |
| Public Node | `tools/node-24.21.0/node-v24.21.0-linux-x64/bin/node` |
| Owner startup cwd | `providers/codex` |
| Operator policy, unchanged | `tools/shared-profile-policy.json` |
| Native read policy, unchanged | `tools/shared-native-read-policy.json` |
| Synthetic data | A new private diagnostic directory beneath the already authorized synthetic project root; fresh local IDs and marker data, preserving its existing main/worktrees |

## Package preparation and rollback

1. Recheck stopped PID/start-ticks/session identities and reacquirable locks. Require no newly active execution beyond the three preserved uncertain receipts; stop on changed manifests/profile seals, active native processes, unresolved writes or unrelated user changes. Consumer and supervisors stay stopped throughout. No API POST, queue consumption, lease renewal, cancellation, terminal rewrite, ACK or replay.
2. Verify the retained immutable f5 source/inventory and all 29 installed Python source files plus the existing 27 dependency pins. Rebuild/restore that rollback into a fresh private test venv and compare complete package/dependency inventories before touching the installed package. Save exact old package restore commands and pre-install receipts. Do not copy authentication or secrets into this rollback.
3. Stage the exact final published worker under a new immutable `tools/worker-source-<full-sha>` directory; install only its package into `tools/worker-venv` without dependency upgrades. Compare the complete new inventory with source. No provider-server/consumer auto-start, service/container rebuild, CLI upgrade, policy change or listener change follows from package installation.
4. Rollback on failed package verification or diagnostic safety gates: prove the diagnostic owner and all its children stopped; retain uncertain evidence, restore f5 from verified immutable source with the old dependency set, verify its complete inventory, and remain stopped. No old job is relaunched.

## One bounded metadata test

Prepare and review an operator-only diagnostic harness before execution. The committed empty-profile test is a regression fixture, not an authenticated operator command: do not point pytest or its copying helpers at real profile files. The harness must retain the exact source factory flags/configuration and the nine-name production allowlisted environment, replacing only synthetic worktree/capability data. Its existing-profile startup auth gate must neither login nor refresh; use no login/setup-token commands, auth RPCs, secret environment inspection or copied credentials. Document any inert probe replacement as a diagnostic boundary, never authenticated readiness.

Start exactly one fresh app-server through the pinned Node/npm launcher, keep the consumer stopped, and use the existing profile in place. Protect the profile at its canonical path by a read-only bind in a private mount namespace, and fully unshare network access before native startup, without copying its bytes or modifying host mount/global security settings. Both protections are required: a read-only profile alone cannot prevent remote token rotation before a failed local write. The reviewed harness must prove the private namespace has no host network path or mounted host IPC endpoint before native startup and before its first request; otherwise remain stopped. This read-only protection may itself expose a CLI write requirement: if startup or metadata needs an auth/profile write or refresh, record the bounded safe failure and stop. Do not relax the mount or claim production profile-write parity. Validate namespace feasibility with public/synthetic data first; if unavailable, leave runtime stopped. Preserve existing manifests, auth and operator settings; all diagnostic artifacts stay private and outside the profile.

Allow only `initialize`, the `initialized` notification, `model/list`, one `thread/start`, `skills/list`, `mcpServerStatus/list`, and `thread/unsubscribe`. No `turn/start`, model generation/tool execution, account/auth methods, paid API fallback, public server endpoint or queue access. The private namespace has no network route, including auth/refresh/model endpoints. No real authenticated cloud route is exercised and no host network configuration or listeners are changed. Cached/local account-specific metadata may be observed; a metadata network requirement ends the test without enabling network. A future authenticated cloud comparison would require another concrete scope and a proven pre-request refresh prohibition. Limit the entire window to 120 seconds, individual RPCs to 12 seconds and shutdown proof to 10 seconds. An RPC failure ends the comparison; no automatic retry or second thread.

Use one fresh allocated synthetic worktree with a selected instruction skill and a scoped read-only marker MCP fixture. Check returned model/catalog metadata, cwd, literal roots, named active permissions and selected-only skill/MCP catalogs. This verifies metadata selection, not model invocation of skills or MCP. Persist only the fixed safe RPC receipts and bounded boolean/pin/closure evidence; discard raw provider errors/data/stderr, account/catalog bodies, prompts and environment values. Verify correlated `thread/closed` and full owner/child-session death before releasing locks/materialized skills; retain resources if either proof fails. Finish with unchanged manifest/auth protection, stopped consumer and unchanged old API/Redis receipts.

## What follows only from a later decision

Success narrows only the existing local-profile metadata comparison; it cannot reconstruct the three discarded original replies or prove model/subscription/tool execution. Failure produces new safe outcome metadata without changing old terminal states. The three old uncertain executions require a separate explicit reconciliation scope, using their retained stopped/lock evidence, with no native replay. A full cancellation/recovery/queue acceptance window remains another separately bounded operation.
