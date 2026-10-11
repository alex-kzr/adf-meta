# Preserved default directory and resumed shared queue checkpoint

Subsequent read-only research: [proposed sealed profile policy](adr/007-sealed-shared-profile-policy.md) identifies and reproduces the pinned upstream automatic project-trust write using empty profiles, including three concurrent metadata threads. This does not implement a new guard or change the real profile/runtime; model turns in that research are zero.

October 11, 2026. The human explicitly approved preserving `/home/adf-worker/.codex` as `/home/adf-worker/.codex.adf-backup-20261011` and continuing the bounded synthetic queue test. That exact rename is complete. The test reached one native thread/turn, then a different profile guard blocked its siblings. It is safely stopped and **not accepted**. [Sanitized evidence](evidence/shared-resumed-queue-2026-10-11.json) supersedes the rename-pending and zero-thread statements in [the earlier installed checkpoint](fixed-worker-checkpoint.md); historical evidence is preserved.

## Exact runtime boundary and preserving rename

The execution venv remains **`a8bb1cc97015e9d46c25acdc9c88228cd65a4876`**. All 22 installed Python files still match the immutable source snapshot. Original `8af54fd` rollback hashes still match. Published doctor repair `859cc534` was not installed and the old doctor was not invoked. API remains `a0e0205`; no other service, user, Windows, firewall, listener or global Git security setting was changed.

Before renaming, the API had no nonterminal executions, dedicated provider/consumer and native sessions were stopped, and worktree locks were reacquired. Metadata checks proved the source and parent were canonical directories owned by UID 1001/GID 1002, mode 0700, on the same filesystem; the target did not exist. Linux `renameat2(RENAME_NOREPLACE)` moved only the exact approved directory and its parent was fsynced. The same device/inode, owner/group, 0700 mode and directory mtime were verified afterward. No directory content or credential was read, deleted or copied. Provider-profile root metadata was unchanged by this move.

The backup remains preserved with those metadata. Reverse transfer remains possible using the same no-replace operation only while ADF is drained/stopped and `/home/adf-worker/.codex` is absent. A reverse transfer would restore the earlier ancestor guard blocker; it is not a remedy for the new acceptance failure. No rollback move was performed.

Only the recorded dedicated provider-server and consumer were started with explicit persistent profiles, `--codex-backend shared` and three slots. Shared auth/health were ready in generation `e9646331-f296-41a8-9590-26d97dbf3d6c`. Before any dispatch, `HOME/.codex` remained absent and the unchanged ancestry guard passed. It is still absent after the test.

## Actual bounded queue outcome

A new ext4 fixture `/home/adf-worker/ai-factory/projects/shared-acceptance-resumed-20261011` contains only synthetic markers, native skills and a JSON check, without a remote. Initial main is `ff3b0d4703e4b71e42c90b4ac5d22b7c8d5dbb63`. Three independent immutable scopes were registered through the existing API; each run creation was repeated with its original idempotency key and retained one ID, and exact approval snapshots were approved within the authorized acceptance test. Limits stayed at three parallel slots, zero retries and 180 seconds per execution. All run/execution IDs are new; older accepted IDs were not replayed.

| Scope | Run ID | Execution ID | Final state and proof |
| --- | --- | --- | --- |
| alpha | `742ace26-e548-4e18-9751-fe3a35d6c252` | `8d5988d1-a7d9-5866-971c-de4fad597f62` | cancelled; native `thread_closed` |
| beta | `6e06c27b-aa81-44de-86a4-612bd1066f48` | `778408bc-d8ba-5ba1-ae77-3e768fe352e7` | failed, `PERMISSION_DENIED`; `no_thread` |
| gamma | `0b13367d-611c-4185-bd6e-f82f5531cde6` | `747af473-ae17-5eb9-a91a-61ce89332286` | failed, `PERMISSION_DENIED`; `no_thread` |

Alpha received native thread `01a12b6a-36ee-79e3-9636-940859c944da` and accepted turn `01a12b6a-3759-76c2-aadc-d376145071f2`. The failed parallel gate cancelled that active synthetic run. Its native closure, stopped supervisor/owned sessions, durable API result and Redis ACK are verified. The two siblings already failed before native threads, so this proves active cancellation but not cancellation isolation among three executing native siblings.

Observable counters: **one accepted `turn/start`, zero completed model outputs, zero MCP call events, no usage recorded**. An accepted turn is not an exact count of backend HTTP/model inference requests. That transport count was not instrumented and is **unknown**, including whether cancellation preceded the first request. No claim of zero backend model calls is made. Subscription auth was used; no paid API/provider fallback, login, setup-token or auth transfer occurred.

Three native jobs did not overlap. Distinct approved skill hashes, immutable configurations and scoped MCP assignments reached the real queue and were materialized, but native skill consumption/MCP results/settings isolation did not complete. The captured alpha launch config has only its own MCP server and skill path, a unique canonical worktree, `workspace-write`, `ephemeral=true`, approval `never`, network disabled and no environment override fields. This one snapshot does not establish three-thread isolation. Consumer crash injection/recovery was gated on successful parallel/MCP observation and therefore was not attempted. No review, test or commit stage was reached.

## New profile blocker and required scope decision

Before dispatch, `clean_config` passed for the exact Codex profile. During the first native thread startup, `/home/adf-worker/ai-factory/provider-profiles/codex/config.toml` appeared, owned by UID 1001, mode 0600, mtime `2026-10-11T14:42:23.574548+00:00`. Subsequent read-only validation rejects the profile with `Shared Codex requires an operator profile without configuration or policy layers`. The other two jobs have pre-thread `PERMISSION_DENIED` and `no_thread` proofs. No known rules/skills/AGENTS/environment policy path was found in that profile. The creator was not proven by a file-write trace; appearance during native startup is the observed timing, not a claim about the file's contents or safety.

Neither this file nor any authentication/config content was read, moved, edited or removed by the assistant. The backup and persistent profiles are preserved. No guard was weakened, new source pin installed or further model attempt run. Continuing requires a separately reviewed remedy for upstream profile configuration persistence and ADF's clean-profile contract. That remedy must preserve rejection of job-controlled OAuth/env, unauthorized policy/permission/MCP overrides and configuration outside approved ownership. The current rename/test authorization does not authorize deleting or moving this different profile file or silently broadening configuration acceptance.

## Verified safe state

All three results are durable and their Redis messages ACKed. Every supervisor/owned session is stopped and each execution lock was reacquired. The native server's recorded SID is dead; dedicated provider/consumer are stopped. Temporary native skill materialization is removed. Synthetic default checkout is clean, main unchanged and no remote added. API reports zero nonterminal executions; global run counts are six completed, five failed and six cancelled. Public API/database, UI and Langfuse probes return HTTP 200. Profile roots remain owned/private 0700; saved directory contents and profile auth remain unread. Runtime/MVP readiness remain **false**.
