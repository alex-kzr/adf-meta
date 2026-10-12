# Shared-patch installed runtime and bounded queue checkpoint

October 12, 2026. **Installation and no-model isolation gates passed; the real API/Redis trial is BLOCKED. Readiness remains false.** The dedicated provider, consumer, native owner and three job supervisors are stopped. Three executions remain uncertain and unACKed; physical quiescence is proven, but logical cancellation is not complete. This dated checkpoint supersedes installed-state statements in the October 11 source/deployment proposals. [Sanitized evidence](evidence/shared-patch-deployment-2026-10-12.json) records the result.

## Exact installed release and preserved configuration

The operator separately authorized worker `f5a713a3df44ffdad58aaa80fc3a36157e6c2736`, orchestrator `9932a87e676b651c7ff2eb89246b900c6d0f843e`, exactly two private manifests, dedicated provider/consumer startup, an orchestrator-only rebuild and one bounded subscription trial. Source publication alone did not authorize these operations. Repository origins, existing user/group memberships, network listeners, firewall and global Git security settings were unchanged. Native grants were limited to the separately approved manifests.

| Component | Installed result |
| --- | --- |
| Worker | All 29 Python files match the exact Git archive in `/home/adf-worker/ai-factory/tools/worker-venv` |
| Orchestrator | All 11 Python modules match the exact source pin; image `sha256:e661b27513d510ae5c956598eb49df2fbe76c1f22fbbe8f20154218328df2753`, container healthy |
| API | Retained `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca`; no update in this deployment |
| Frontend | Retained `92bfa64f38202872dbf2999d9343884a12036959`; no update in this deployment |
| Runtime tools | Python 3.12.9, uv 0.12.18, Node 24.21.0, Codex 0.157.0 and Claude Code 2.1.296 retained; all 27 runtime dependency versions unchanged |

Runtime root is `/home/adf-worker/ai-factory`. The Codex and Claude profile directories remain owned by `adf-worker`, mode 0700. Existing `tools/shared-profile-policy.json` and Codex configuration bytes are unchanged. No authorization was copied, and no login/setup-token command or paid API fallback was used. Existing subscription authorization was used only by the dedicated native owner.

Exactly two new canonical, single-link operator files are owned by `adf-worker`, mode 0600:

- `tools/shared-native-read-policy.json`: version 1, `read_tool_roots` contains only the verified public Codex vendor directory `tools/provider-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl` under the runtime root.
- `tools/shared-patch-check-sandbox.json`: version 1, standalone `codex-resources/bwrap` beneath that vendor root, SHA-256 `77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c`; exact read-only toolchain roots `tools/worker-venv`, `tools/python/cpython-3.12.9-linux-x86_64-gnu`, `/usr/lib`, `/usr/lib64`. The two `tools/...` entries resolve under the runtime root.

The dedicated owner retained `--shared-profile-policy` and added `--shared-native-read-policy`. The consumer selected `--codex-backend shared-patch --check-sandbox-manifest ...`. All other roots, API/Redis credential file paths, worker identity and provider profile settings were retained. These processes are currently stopped; this record is not a restart instruction.

### Orchestrator configuration preservation

The initial orchestrator recreation failed the saved settings fingerprint because Compose's current input had `ADF_TELEMETRY_ENABLED=false`, while the previous container had `true`; ENV ordering also differed. Only that container was stopped during diagnosis, before the trial. Read-only reconstruction recovered the exact previous full settings hash. The original telemetry flag was then supplied only to the Compose subprocess, without editing `.env`, Compose files or global environment settings.

After recreation, all original semantic settings matched: every ENV key/value, command, user, working directory, healthcheck, ports, mounts, limits and security settings. Environment ordering was normalized for this comparison. Image/build labels were separate from the settings fingerprint. All other container IDs and configuration file hashes remained unchanged. The mismatch is resolved; it does not explain the later native startup failure.

## Drain and verified rollback

Before switching, the API reported zero active executions and no blocking runs; Redis PEL was empty. Dedicated sessions were stopped, and all nine historical broker jobs had stopped-session and reacquired-lock proof.

The previous immutable worker source and inventory remain at `tools/worker-source-13c4624`; the new archive is retained at `tools/worker-source-f5a713a`. The private `tools/worker-rollback-f5a713a.json` contains complete source inventories, dependency versions and preserved configuration hashes. In the fresh `tools/worker-rollback-check-f5a713a` environment, installing the 29-file new package and restoring the 23-file old package was verified. Restoration removed all six new-only modules and their bytecode: `check_bootstrap.py`, `check_payload.py`, `check_sandbox.py`, `native_read_policy.py`, `patches.py`, `shared_patch_adapter.py`. No dependency upgrade was required.

The previous orchestrator image `sha256:23625c97fd2182bf0ffbac7a8f017bd20b4f4d5edd22bebdb2d6f6f1a92394fa` is retained as `adf-orchestrator:rollback-23625c97fd21`; all 11 source modules matched `6fe7c1402864210fd8b6c2aed44695436c147f3f`. Exact previous settings are retained privately with the rollback evidence. No active rollback was performed after the trial; the new source remains installed in a stopped worker runtime.

Rollback must preserve uncertain deliveries, journals, worktrees and artifacts. Re-prove stopped process identities/groups and reacquired allocation locks before any package/container restore; verify restored source hashes and unchanged dependencies/settings afterward. Do not ACK, replay or mark unknown executions terminal to obtain a clean queue. The legacy worker's full-host native read mode failed isolation and must remain stopped even after a verified package rollback.

## No-model gates and their limits

Fresh private QA copied all actual installed worker modules, using exact public Codex/bwrap hashes and fake provider profiles. Ruff, strict mypy across 29 files and Bandit passed. The selected real-native IPC canary passed: **1 passed, 107 deselected, 8.60 seconds**. It checked synthetic filesystem denial and actual native thread/skills/MCP metadata, with protocol-double lifecycle turns; it made no actual native model turn.

The active installed checker passed an empty snapshot and a trusted isolation probe. Checker processes stopped; sockets/fork were denied, and actual private configuration/authentication paths were stat-hidden without reading their contents. Operator trust/native manifests and modes validated before the model window opened.

These gates do not prove model skill/MCP invocation or the actual persistent-owner transition from baseline startup to per-thread assigned settings. Independent read-only review subsequently confirmed that the canary starts a separate app-server with each job's configuration and worktree cwd. Production starts one shared owner from `providers/codex` with baseline configuration, then supplies job overrides. A production-parity no-model harness is still required. Earlier [source verification](shared-native-read-source-checkpoint.md) and its successful [worker CI](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38173696418) remain separate evidence.

## One actual API/Redis trial

Only synthetic project `7223cbc6-55cb-4ba1-9875-34979eda39c0`, already trusted at `/home/adf-worker/ai-factory/projects/shared-acceptance-resumed-20261011`, was used. Its registered deterministic Python check was temporarily updated and restored with a revision guard after stopping. Historical runs retained their snapshots. Three scopes received distinct approved instruction documents and scoped `read_marker` MCP assignments. The immutable workflow/run was validated and idempotent creation verified.

Run `67727194-095a-4e9e-afde-6af74ca84247` reserved a worst-case initial nine turns behind approval. Subsequent independent review approvals would have opened only if the remaining budget permitted their worst-case retries. No review approval or fault stage was reached.

| Bound/result | Observed value |
| --- | --- |
| Concurrent execution limit | 3; three broker jobs accepted, actual parallel model turns unverified |
| Total native turn allowance | 10, including failed/uncertain attempts |
| Charged attempts | 3; zero confirmed native turns, seven unused, budget closed |
| Wall limit | 1,200 seconds |
| Actual process window | 03:12:43–03:18:23 UTC, 339.76 seconds |
| Provider selection | Subscription Codex only; no paid API fallback |

All three jobs became `EXECUTION_UNCERTAIN` after native thread-spawn intent with no recorded thread or turn ID. No patch generation completed, no patch application intent was recorded and no task commit/integration occurred. Null IDs do not prove that upstream never created a thread: the retained RPC diagnostics cannot distinguish a provider error, invalid response or transport closure.

The whole-run cancel request was submitted and only the dedicated provider/consumer/native/supervisor processes were stopped. Every job has `server_session_dead`, stopped child-group/owned-session proof and a reacquired worktree lock. The synthetic main checkout remains unchanged and clean; one assigned materialized instruction file per worktree is retained.

**Logical state is unresolved:** the API run remains `running`, three executions remain `uncertain`, results are saved but terminal persistence is false, and Redis PEL contains three unACKed deliveries. No forced ACK, terminal-status rewrite, replay or additional model turn occurred. Physical quiescence is not successful cancellation/recovery acceptance.

Live generation, selected skill/MCP use, deterministic test failure/fresh repair, independent review, task commits/integration, individual cancellation, consumer fault recovery and provider fault recovery remain unverified. Planned fault injections were not executed after the early blocker. Readiness remains false.

## Diagnosis and next scope

Read-only review of [shared RPC](../services/runtime-worker/src/adf_runtime_worker/shared_rpc.py), [shared server](../services/runtime-worker/src/adf_runtime_worker/shared_server.py) and [native canary](../services/runtime-worker/tests/fixtures/native_read_canary.py) found two evidence gaps:

1. Explicit RPC errors, malformed results and synthetic transport errors fold into `PROVIDER_FAILED`; after spawn intent with no thread ID, the owner records `EXECUTION_UNCERTAIN`. This keeps conservative locks/no-replay fencing but loses the original diagnostic outcome.
2. The canary does not exercise several per-thread configurations on the same baseline-started native owner. Pinned upstream configuration source appends request overrides after CLI overrides; the claim that CLI baseline always wins is not established.

The upstream failure cause remains unknown. The next useful work is source-only: add bounded sanitized receipts for method, phase, outcome category, recognized numeric code and elapsed time, excluding raw message/data/stderr; then test production startup and multiple metadata threads on one owner without models. Preserve existing uncertain/quiescence fences. No permissions expansion, disabled guard, queue replay or new subscription run is justified by the available evidence. A new installed-source switch or model window needs its own concrete scope.

Full settings, journals, runtime definitions, profiles, secrets and generated artifacts remain local and ignored. Only this written checkpoint and selected sanitized evidence are published.
