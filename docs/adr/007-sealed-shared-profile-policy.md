# ADR 007: Explicit sealed trust policy for the shared Codex profile

Status: Proposed, source/design validation only. No worker guard or installed runtime change is implemented by this ADR. October 11, 2026.

## Reproduced cause

Codex `rust-v0.157.0`, tag tree `00c972ed5d6ff6499317fd41b7f23605b8e6850d`, automatically persists project trust in `thread/start`. The branch requires an explicit cwd, absent project trust, a non-projectless configuration and effective permissions that can write the cwd. It resolves the main Git project root for linked worktrees and writes `projects.<root>.trust_level = "trusted"` through `set_project_trust_level` / `ConfigEditsBuilder::new(CODEX_HOME)`. Ephemeral threads still take this path. See the verified [thread processor](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server/src/request_processors/thread_processor.rs#L1347), [trust writer](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/core/src/config/mod.rs#L2388) and [config editor](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/core/src/config/edit.rs#L790).

This is security-relevant trust state, not an arbitrary harmless cache. Main-project configuration can launch host processes. A generated origin alone cannot justify allowing its contents. The real profile's file contents remain unclassified and unread; the empty-profile reproduction establishes a matching mechanism without claiming a file-write trace of the earlier live run.

## Pinned no-model verification

Eighteen unauthenticated `thread/start` requests used six fresh private test profiles and synthetic repositories/worktrees; there were no `turn/start`, login, setup-token, auth copies or model calls. All native sessions were stopped by recorded process identity/SID proof. Real profile/config/backup metadata and installed worker remained unchanged. [Sanitized evidence and public-source hashes](../evidence/shared-profile-config-research-2026-10-11.json) record:

| Case | Observed user config behavior |
| --- | --- |
| Empty profile, read-only, three worktrees | No `config.toml` |
| Empty profile, workspace-write, three worktrees | First thread writes only main-root project trust; later starts retain the same bytes |
| Exact preseeded main-root trust, workspace-write | Three starts leave config bytes unchanged |
| Owner CLI project-trust override, empty profile | Three starts do not create config |
| Exact preseeded trust, three concurrent starts | Three distinct threads; config bytes unchanged |
| Owner CLI trust, three concurrent starts | Three distinct threads; no config created |

These direct metadata-only probes bypass the current ADF clean-profile guard and are not API/Redis/native model acceptance. No model turn was run. TUI preference/notice persistence and explicit app-server config-write RPCs are separate upstream paths; ADF does not use the TUI or expose those RPCs through its bridge. This investigation does not assert that all future model-turn state mutations are absent. Any unreviewed configuration mutation must stop execution, rather than extend the allowlist automatically.

## Proposed minimum change

Introduce an **opt-in operator-owned sealed project-trust policy**, while keeping today's absence-only mode as the default. Do not permit `config.toml` solely because it exists or its hash was approved. The content must satisfy an exact closed schema and an explicitly selected project set:

```toml
[projects."/home/adf-worker/ai-factory/projects/shared-acceptance-resumed-20261011"]
trust_level = "trusted"
```

The example is an expected synthetic configuration, not a read of the real file or an instruction performed against it. Only `projects` is allowed at top level; every entry must contain exactly `trust_level = "trusted"`, and its canonical Git root must equal an operator-declared project. Reject unlisted roots, directory-wide/wildcard trust, additional fields, malformed/duplicate TOML, symlink/hardlink/oversize files, wrong owner/mode and permission/config layers. Model/provider/API routing, notices, hooks, rules, features, MCP, environment, profile/include selectors and arbitrary settings are not accepted from this file.

A private canonical operator manifest should declare the exact allowed Git roots under the existing approved project root; it must be regular, same-UID, mode 0600, without symlinks/hardlinks. Adding another project requires deliberate operator policy review/restart, not a job-defined field or dynamic learning from the generated config. The JSON manifest is policy input, not an authentication file. The actual profile config must be regular, same-UID, canonical and 0600, read with `O_NOFOLLOW`, bounded to 64 KiB and checked for concurrent replacement. Errors/logs contain fixed codes and key classifications, never values or raw config.

After schema validation, seal the exact config bytes for that owner generation. Preserve the current absence checks for rules/skills/AGENTS/environment layers. Check `.codex` layers on both the allocated worktree's ancestors **and the declared main repository's ancestors**, because upstream trust resolves a linked worktree to its main Git root. Verify the execution's durable allocator record binds that worktree and main root to the approved manifest; a client-supplied cwd alone is insufficient.

The server's existing fixed feature/network/approval/skills/MCP baseline remains authoritative. Derive the identical `projects` override only from the validated operator manifest. Inject it inside the owner after validating the client frame; clients and jobs may not supply a `projects` field or OAuth/env selectors. This avoids the automatic trust-write branch. An existing file is reusable only if it already equals the explicit closed policy; the source change must not provision, merge, repair, delete or replace it implicitly.

## Exact implementation points

1. Add `profile_policy.py` with a closed-schema validator and per-generation byte seal. Add an operator-only `provider-server --shared-profile-policy <private-manifest>` option. Omission retains the current guard; API/Redis/job schemas and `restricted_env` do not change.
2. In `server_command`, validate/seal before any CLI version/auth probe or app-server launch. Pass the trusted immutable policy to `SharedServer`; never serialize config contents into broker journals.
3. In `_handle`, verify allocator/main-root binding and both ancestry sets before native dispatch. Reject client trust/config overrides with the existing fixed baseline validation, then add only the owner's derived project trust to native parameters.
4. Serialize the config validation plus `thread/start` segment. Recheck the seal after startup **before `turn/start`**. During active turns and before success/commit eligibility, verify drift again. On mismatch, block the generation/health, interrupt and close its active threads; if closure cannot be proven, retain locks/materialization and mark uncertain. Keep accepted-ID tombstones and existing fencing/ACK rules.
5. Keep configuration writing out of ordinary startup. If an existing real file fails validation, stop with a fixed classification and preserve it. A separately reviewed exact baseline installation/backup operation is needed only if the operator later chooses that remedy.

## Required source and integration checks

- Offline contract tests: absence-only default remains unchanged; exactly declared trust accepted; unknown root/key/value, provider/env/MCP/hooks/model/notice/inclusion settings, malformed TOML, links, broad permissions, large files and concurrent replacement rejected without printing sentinels.
- Real subprocess/Unix-socket tests: jobs cannot change the owner's policy; distinct approved allocations work; wrong allocator/main-root or main-root `.codex` layers fail before native requests. Three concurrent starts preserve the seal.
- Drift tests: mutation before start blocks launch; mutation between thread/start and turn/start yields no turn; mutation during one active turn blocks the generation and cancels siblings with closure/lock proofs. Missing closure remains uncertain and prevents cleanup/ACK/commit. Restart never replays an accepted ID.
- Native empty-profile test: exact policy/owner baseline plus three worktrees and concurrent starts, no turns/auth/model calls, stable bytes and stopped SID proof. The current upstream experiments pass; the proposed **ADF integration** tests have not yet been implemented.
- After source checks/CI and separate exact-pin deployment authorization, retain immutable `a8bb1cc` rollback, recheck drain and validate the existing profile against the reviewed manifest without outputting its contents. Only provider/consumer may be updated. Then run the existing bounded synthetic API/Redis skills/MCP/cancel/recovery acceptance using fresh IDs, subscription auth and no paid fallback.

## Current decision boundary

This is a concrete tested design proposal, not a ready-to-deploy worker patch. The installed `a8bb1cc`, published doctor source `859cc534`, real profile config/auth, backup and current guard remain unchanged. Actual profile content need not be read to approve the design. During a later explicitly authorized deployment, the closed validator would need to read **only `CODEX_HOME/config.toml`** to classify it against the exact reviewed policy, without printing values; no `auth.json`, token or other credential read by the assistant is required. It must not assume the real file matches the synthetic reproduction. Native model acceptance and readiness remain false.
