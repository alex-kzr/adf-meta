# Sealed shared policy: deployment and bounded runtime result

Later source-only follow-up: [sandbox/recovery diagnosis](shared-sandbox-recovery-repair.md) resolves the previously unknown mechanism using pinned source, a no-model reproduction, retained synthetic-target registry evidence and an inert replay of the startup helper. [The proposed compatible writing route](shared-write-path.md) remains future source work. Historical runtime evidence below is preserved; installed `13c4624a` and stopped sessions were not changed by that investigation.

October 11, 2026. The operator approved the exact [ADR 007 deployment scope](shared-policy-deployment.md) at 16:09 UTC. Worker **`13c4624a8791fa4c9035c284a4689e412f0b7b42`** is installed in `/home/adf-worker/ai-factory/tools/worker-venv`. The single three-job API/Redis trial reached three concurrent native Codex turns and completed one assigned scoped MCP call per job, then **failed closed**. Full cancellation/recovery/output isolation acceptance did not pass. Runtime and MVP readiness remain **false**. [Sanitized evidence](evidence/shared-profile-policy-runtime-2026-10-11.json) records exact IDs and limitations.

## Deployment and final state

Before installation, API reported no nonterminal executions. Recorded dedicated sessions and historical writers were stopped, results reconciled and locks reacquired. Retained `a8bb1cc97015e9d46c25acdc9c88228cd65a4876` source matched the old installed package's 22 Python files. Separate immutable candidate source and private rollback inventory were retained.

The candidate archive SHA-256 is `7517b81022ab95fc976ae538cafaa2ba997e5eb558a7c5e482a9db64539017d8`. Installation was offline, without dependency resolution. All 23 installed candidate Python files match its exact snapshot; all 27 installed distribution versions remain unchanged, and `uv pip check` passed. Python 3.12.9, uv 0.12.18, Node 24.21.0, Codex 0.157.0 and Claude Code 2.1.296 remain the approved pins. No other application or infrastructure service was deployed. API stays at `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca`.

The new `/home/adf-worker/ai-factory/tools/shared-profile-policy.json` is owned by `adf-worker`, mode 0600, and declares only `/home/adf-worker/ai-factory/projects/shared-acceptance-resumed-20261011`. The validator classified existing Codex `config.toml` as valid internally before installation, after installation and after the trial. Its seal/metadata stayed unchanged; values were not emitted and the file was not modified. No authentication contents were inspected or copied by the assistant; no login or setup-token was performed.

Only the dedicated provider-server and consumer were started under `adf-worker`, with the approved manifest, shared backend, prior credentials/settings and maximum concurrency three. Startup reported healthy subscription authentication, matching Codex pin and a new owner generation. After the failed trial, terminal-only recovery acknowledged the remaining durable Redis record without starting another native thread/turn. Both dedicated services and the native app-server session are now **stopped**. Worker 13c4624 remains installed; package rollback was not performed.

## What the one trial proves

Fresh executions reused synthetic project `7223cbc6-55cb-4ba1-9875-34979eda39c0`. Main remains clean at `ff3b0d4703e4b71e42c90b4ac5d22b7c8d5dbb63`, with no remote. Three idempotent run creates and exact snapshot approvals passed. Each job had its own worktree, immutable agent configuration, approved native skill snapshot and scoped `read_marker` MCP server. The workflow had one developer execution per run, no native reviews, commits, retries or paid API fallback.

| Gate | Observed result | Limit |
| --- | --- | --- |
| Parallel native startup | Three simultaneously running jobs, distinct native thread/turn IDs, same owner generation | Exactly three accepted turn starts; backend HTTP/model-call count is unknown |
| Assigned configuration | Distinct cwd/configuration/skill paths and MCP names; no job environment overrides; network disabled in recorded thread baseline | All used default model (`model: null`); different-model isolation is unverified |
| Native skills | One `skill_loaded` event with assigned immutable hash per job | Hidden skill-stamp use was not verified in completed output |
| Scoped MCP | `filesalpha`, `filesbeta`, `filesgamma` each completed one assigned `read_marker` call through actual queue/native chain | Expected final JSON and registered checks did not complete; full output isolation is unverified |
| Consumer fault | Recorded consumer alone killed once using matched identity/pidfd; owner alive at injection | Immediate recovery failed; original generation continuity was not proved |
| Single-job cancellation | Intended gamma cancellation step was not reached | No claim that one active job was cancelled while siblings continued |
| Fail-closed shutdown | Original generation blocked; all jobs failed `PERMISSION_DENIED` with `thread_closed` proof | Failure fencing does not complete cancellation/recovery acceptance |
| Terminal reconciliation | Later terminal-only recovery persisted/ACKed all results without new native IDs | Does not establish active supervisor continuation across fault |

Accepted native turns are real model work; they must not be reported as zero model calls. Exact backend request count and normalized token/cost usage were unavailable. Usage remains null, not zero. Subscription authentication was used; no paid fallback was configured or invoked.

| Scope | Run ID | Execution ID |
| --- | --- | --- |
| alpha | `fe0da41c-bb93-451f-a151-42ff75e7d398` | `5e5dbb7e-93b2-5ddf-ba03-2b85a4cfe600` |
| beta | `35fa0a96-471d-41e9-9469-3dd515d6cdff` | `855b0e09-6018-5aa6-bb43-2ebc25758ab9` |
| gamma | `7db6ab7c-785d-42a5-b059-b0cc38765991` | `b6b76ed2-4cf3-5836-a87a-d08dc95963c5` |

## Failure evidence and unresolved cause

Original generation `13d6cd2a-01c9-4f94-bb0a-bba6bc5fbac5` was recorded `policy_blocked: true`. Post-trial profile/manifest classification passes with identical seal. All three `.git` pointer hashes and inode/owner/mode/size/time seals match allocation receipts. Alpha/beta have no rejected workspace/ancestor layers. Gamma has an unexpected worktree-local `.codex` directory, UID 1001, mode 0755. It is empty at final metadata inspection, with no `config.toml`. It was preserved without reading file contents or changing permissions.

That directory violates ADR 007's absence rule and explains why the retained gamma workspace fails the same guard. Evidence does **not** establish which process created it, whether it was the first triggering mutation, or why the immediate recovery command exited with status 1. It does not prove that a replacement consumer reached startup. No raw config/auth/log values or speculative upstream attribution are published. Bounded diagnostic extraction found no retained consumer/provider traceback. Creation attribution and recovery failure remain unresolved pending separate source/protocol investigation.

All jobs have durable failed results, terminal API confirmation, Redis ACK, stopped supervisors/owned sessions and reacquired worktree locks. Approved temporary native skill materialization is removed. Unexpected gamma layer, allocation worktrees and private journals are retained. API final inventory has no nonterminal executions (eight failed, six completed, six cancelled runs including history). Default-profile backup retains inode, owner, mode and mtime; `HOME/.codex` stays absent. Explicit profile roots remain owned 0700 and the two existing service files owned 0600. Existing users, Windows, firewall, listeners, global Git settings and other services were not changed.

## Rollback and next decision

Private `tools/worker-rollback-13c4624.json`, immutable `tools/worker-source-a8bb1cc` and candidate snapshot remain available; old/new source hashes and unchanged dependencies were reverified after stopping. Current state is installed 13c4624 with provider/consumer stopped. An approved rollback can stop/drain only recorded sessions, reinstall retained a8bb1cc offline with no dependency changes, verify source hashes and leave services stopped. It must not repair config/profile files or restart rejected prior-generation outputs.

Before another acceptance attempt, investigate the directory's origin and failed immediate recovery. Any policy exception, workspace cleanup, new source deployment or additional native/model trial requires a concrete separate scope; this three-job authorization was consumed. Do not silently allow/remove the empty directory, weaken fencing, replay accepted IDs or claim complete MVP acceptance. Historical [source-only release evidence](evidence/shared-profile-policy-source-2026-10-11.json) and [earlier resumed trial](shared-resumed-checkpoint.md) remain intact.
