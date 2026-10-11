# Shared sandbox capability and recovery source repair

October 11, 2026. This source-only repair follows the [bounded failed native trial](shared-policy-runtime-checkpoint.md). The installed worker remains `13c4624a8791fa4c9035c284a4689e412f0b7b42`, with the dedicated provider and consumer stopped. No installed package, policy, profile, authentication, service setting or existing runtime file was changed during this investigation. No new API/Redis job, native thread or model turn was created. MVP readiness remains false.

## Why gamma acquired an empty `.codex`

The official Codex `rust-v0.157.0` tag tree is `00c972ed5d6ff6499317fd41b7f23605b8e6850d`. Six public source files were fetched and their Git blob IDs verified against that pinned tree. [Missing protected subpath construction](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/linux-sandbox/src/bwrap.rs#L1219) creates empty read-only mount targets for absent `.git`, `.agents` and `.codex` paths. On a writable host workspace, bubblewrap materializes the mount point as an empty host directory. [Supervisor registration and cleanup](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/linux-sandbox/src/linux_run_main.rs#L954) records newly synthetic targets and normally removes them after the sandbox child exits. Abrupt supervisor shutdown can leave the host placeholder behind.

A native **no-model** reproduction used a fresh empty HOME, CODEX_HOME, XDG directories and TMPDIR, a synthetic Git main repository/linked worktree, and only `/bin/sleep 3`:

```sh
codex sandbox \
  -c 'sandbox_mode="workspace-write"' \
  -c 'sandbox_workspace_write.network_access=false' \
  -c 'features.daemon_auto_start=false' \
  -c 'allow_login_shell=false' \
  -c 'projects."<fresh-synthetic-main>".trust_level="trusted"' \
  -- /bin/sleep 3
```

This is recorded evidence, not an instruction to run against the operator profile. There was no login, auth copy/read, app-server request, `thread/start`, `turn/start` or model call. During execution the host worktree acquired an empty owned `.codex` directory, mode 0755. The command exited 0; normal cleanup removed the directory. Synthetic profile config remained absent.

Retained live provenance independently corroborates the mechanism. The registry path was derived from **gamma's actual allocation journal** using the pinned FNV-1a path hash, without scanning unrelated registry entries. That exact target has an owned mode-0600 marker containing the fixed classification `synthetic`, registered by sandbox PID `937995`, now absent. Its mtime is `1791735544907687598` ns. The preserved empty gamma directory's mtime is `1791735544922449009` ns, approximately 14.762 ms later. Gamma's command-start event follows at `16:19:05.054444Z`; the earliest sibling failure is `16:19:04.989600Z`.

The matching native registry establishes that the actual target was registered as newly synthetic. Combined with pinned source and an isolated reproduction, this proves the sandbox conflict; it is not evidence of a configuration payload or a model intentionally writing configuration. There is no kernel mkdir audit trace proving the exact creating syscall/PID, and cleanup interruption details were not retained. These precision limits do not change the capability incompatibility.

## Why the immediate recovery command returned 1

The saved dedicated startup helper, SHA-256 `67f3325286b0e7d56f85a745847aed08220c33c50877eeb7a7de401bf68e86b0`, bundles provider startup and consumer startup. It first reuses/launches the owner, requires `health == ready` for 40 checks separated by 250 ms, then stops the recorded owner and raises a runtime error if readiness does not return. Consumer launch happens only after that loop succeeds.

Policy drift makes the original generation's health irreversibly blocked. The owner remains alive until explicitly stopped; the monitor itself does not terminate the owner process. An offline replay of the helper's **exact start-branch AST**, with inert facades and no filesystem/process/provider operations, reproduced 40 blocked probes, 10 seconds of simulated wait, one owner stop and **zero consumer launches**, followed by the uncaught-error exit-1 branch. Retained fault/result timestamps span approximately 12 seconds, consistent with that gate and bounded stop. Both dedicated diagnostic logs are empty, so no consumer traceback was captured. The historical helper stderr was not retained; its exact historical exception string cannot be asserted.

The deterministic control-flow failure is the startup helper's owner-readiness gate, not a proven exit of a newly restarted consumer. `WorkerService` does not require provider-ready health before terminal reconciliation. Source recovery now has an explicit mode that avoids this combined lifecycle control.

## Minimal source changes

- **Truthful sealed capability:** `SharedServer` authoritatively rejects `workspace-write` with `CAPABILITY_UNSUPPORTED` before policy binding, `thread/start` or `turn/start`. It produces a quiesced `no_thread` tombstone without blocking the generation. The adapter preflights before session/skill materialization. Read-only siblings remain usable.
- **Explicit health boundary:** authentication, policy status, permission profiles and unsupported writes are separate metadata. Transport/auth readiness does not imply autonomous write support or MVP acceptance.
- **Consumer-only recovery:** `serve --recovery-only` skips provider probes, API lease claims, supervisor starts and all Redis delivery reads/reassignment. It uses existing locally owned worker-ID/epoch journals, replays durable intent or reconciles through unchanged stopped-session/worktree-lock proof, and ACKs only API-confirmed terminal results using saved message IDs. Unknown/foreign work remains pending. Live writers, unproved shared references, held locks or nonterminal API confirmation prevent ACK. It never starts/stops the provider or replaces its generation.

The strict `.codex` absence checks, closed manifest/config validation, independent monitor and immutable receipt/commit fencing remain unchanged. No empty-directory exception, legacy sandbox substitution, CLI upgrade or paid API fallback was introduced. Existing unsealed/subprocess behavior is preserved, without claiming new isolation acceptance.

## Verification and publication

The matching umbrella gitlink selects the source release. [Sanitized machine-readable evidence](evidence/shared-sandbox-recovery-source-2026-10-11.json) records public source hashes, no-model reproduction, exact-target marker provenance and helper replay. Offline Linux tests use freshly copied source/dependencies and synthetic repositories/profiles under short private `/var/tmp` paths. Existing runtime/QA installations are not modified; no dependency upgrade or download is required. Independent review, Ruff, strict mypy, Bandit, complete Linux pytest and exact-commit CI are publication gates.

Published worker source is `8ab95f4cda40ab750f2d6dcd31c84960f32620aa`. All 247 Linux pytest cases pass; Ruff and strict mypy (23 source files) pass, Bandit reports zero medium/high findings, and independent source/proposal review has no blocking P1/P2 findings. The umbrella verifier passes for 260 files and its 94 tests pass with four documented skips. Final read-only verification proves all 23 installed and retained source files still match old `13c4624a`; the owner, consumer and native server remain stopped, and both profiles remain private without reading their contents. Source publication does not install this release.

[Worker CI run 38159529141](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38159529141) succeeds for that exact source SHA, including all Linux source checks and pytest. The current umbrella publication's CI result is reported separately after its commit; this document does not claim a future run succeeded.

Regressions verify adapter refusal before materialization, direct forged IPC refusal with no-thread proof, repeated health/read-only sibling survival, unchanged drift fencing, no recovery claim/spawn/provider probe/stream read/reassignment, foreign/unknown messages, stopped intent/result replay, live supervisors/processes/shared references, held locks, nonterminal API responses and fixed transport dead-letter behavior. Historical evidence files retain the facts known at their own checkpoints; this report resolves their previously unknown sandbox/recovery mechanism.

## Remaining product and deployment gate

This repair fixes false write capability and unsafe recovery control. It **does not implement sealed shared workspace-write**, hidden-skill use, completed output isolation, targeted cancellation or full active recovery acceptance. Three-job coding/MVP acceptance remains blocked. Subscription usage/call counts from the historical run remain unknown where not emitted; they are not zero.

[The concrete path to parallel writing agents](shared-write-path.md) proposes shared read-only code generation plus worker-applied validated structured patches under the original approved write scope, with a separately versioned MCP write broker as a later alternative. Three isolated no-model read-only sandboxes denied native writes while trusted host writes succeeded in distinct worktrees without `.codex`. The design lists exact implementation/recovery work and source-only versus deployment/model approval boundaries; the patch backend is not implemented or installed by this repair.

No new installation, policy change or model trial is included in the current source authorization. A possible **separate minimal installation scope**, after exact source CI passes, is:

1. Install only the published worker source commit selected by this umbrella into `/home/adf-worker/ai-factory/tools/worker-venv`. Keep all 27 runtime dependency versions and five tool pins unchanged. Retain immutable installed `13c4624a` plus existing `a8bb1cc` rollback and hash/dependency inventories. Prove no active writers and source-byte restoration before switching.
2. Leave API/containers/allowed roots, service secrets, policy manifest, provider config/auth, backup, user groups, Windows/firewall/listeners and global Git settings unchanged. No login/setup-token/auth copying. Provider/consumer remain stopped by default.
3. If terminal reconciliation is specifically requested, start only the dedicated consumer with the existing settings plus `--recovery-only`, use the existing worker identity, then stop only that recorded consumer after durable terminal/ACK proofs. This scope has **zero new queue/native/model jobs**, no provider startup/restart and no profile reads by the assistant. Actual service clients may consume their existing credential files internally without printing values.

Because the historical three results are already durable and ACKed, another recovery operation is currently unnecessary. Restoring autonomous writes needs a separately reviewed execution/policy design; allowing transient empty `.codex`, changing the sandbox/CLI or weakening checks is outside this repair. Any further native model acceptance needs fresh explicit limits/IDs and approval; the earlier three-job budget is exhausted. No new model trial is proposed as a prerequisite for safely publishing this source fix.
