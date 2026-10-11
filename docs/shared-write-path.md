# Path to parallel writing agents with pinned Codex

October 11, 2026. **Proposed implementation, not an enabled capability or completed MVP.** The [source repair](shared-sandbox-recovery-repair.md) deliberately rejects sealed native workspace-write. The requirement for three parallel coding agents remains open. Installed runtime, current security policy, permissions, profiles and service settings were not changed to research this path.

## Recommended minimum: shared read-only generation, worker-applied patches

Keep one pinned Codex 0.157.0 app-server/auth owner and three independent native threads, each bound to its own ext4 worktree, approved skills and existing read-only scoped MCP. Use native `sandbox: read-only` for code generation. Require a bounded structured **patch result** rather than native shell/apply-patch writes. After the native thread is proven closed, the trusted worker validates and applies those edits in that same worktree under the existing original `trusted-development` job policy, allowed-write paths, lease and execution lock. Review/test/commit/integration remain separate registered operations.

The developer's original role and write authorization stay `trusted-development`; only its provider generation stage is read-only. An `observe` planner/reviewer must never receive host write authority. This is not permission escalation from a read-only role, and no model-generated instruction can grant new paths. It implements agent-authored code changes through an ADF-controlled writer. It requires product acknowledgement of that execution mechanism, rather than pretending the CLI directly edits files.

```mermaid
flowchart LR
  Q[Approved API execution and lease] --> W[Worker and unique worktree lock]
  W --> C[One shared Codex owner]
  C --> T[Three read-only threads in distinct worktrees]
  T --> P[Bounded structured patch results]
  P --> V[Closed schema and original write-scope validation]
  V --> A[Worker applies edits after thread closure]
  A --> R[Registered tests and independent review]
  R --> G[Reviewed commit and serial integration]
```

The conflicting synthetic metadata mount comes from **writable workspace roots** in [pinned bubblewrap construction](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/linux-sandbox/src/bwrap.rs#L621). A fresh no-model test launched three simultaneous native read-only sandboxes in synthetic linked worktrees. All three denied native shell writes, exited 0, and produced no host `.codex`. During those commands an external trusted host writer created distinct files in the three worktrees. No auth, API/Redis job, native thread/turn or model was involved; no installed runtime file was modified. This establishes the filesystem mechanism, **not native patch-generation/MVP acceptance**. [Evidence](evidence/shared-sandbox-recovery-source-2026-10-11.json) distinguishes the prototype from production implementation.

Existing pinned app-server structured output and independent read-only jobs are already covered by schema/offline tests and previous runtime MCP results. A complete patch-generation adapter is **not implemented in this release**. Whether the authenticated model reliably follows the patch schema remains a later bounded native acceptance gate.

## Exact source work required

| Area | Required change and boundary |
| --- | --- |
| Worker backend selector | Add an opt-in proposed `shared-patch` mode; keep present `shared` write refusal. Snapshot this selection in durable worker tickets. Owner remains the same pinned process and accepts only the existing fixed read-only native frame. Health distinguishes agent-authored patch capability from native workspace-write. |
| Request/structured result | Define a closed, versioned patch schema: ordered exact relative files, create/replace/delete action, expected preimage SHA-256 (explicit absent for create), UTF-8 content for create/replace, per-file/aggregate bytes and file-count bounds. No executable command, permission, symlink, hook, remote, environment or arbitrary patch instruction fields. Start with bounded text files; binary edits and renames fail explicitly. |
| Baseline snapshot | Worker supplies trusted preimage hashes or opaque baseline IDs in the generation context; do not depend on the model calculating a hash. Every selected baseline is checked again before mutation. Define v1 behavior for delete, absent files/new parent directories and file modes explicitly; reject unsupported metadata changes rather than guessing. |
| Durable phase/size | Native generation success is an intermediate `generated` phase, never terminal execution success or ACK-safe. Persist `generated -> validated -> applying -> applied -> checks/review` evidence; API terminal result/ACK only follows resolved mutation intents and host writer stopped proof. Fit schema/aggregate UTF-8 bytes within the current 65,536-character event/final-output constraints and bounded shared frame, or separately version/test a bounded adapter/parser limit increase. Do not imply arbitrary `max_output_bytes` support. |
| Validation | Recheck original approved developer role/policy, immutable expected paths and lease epoch. Reject traversal, aliases, symlinks, hardlinks, credential/configuration paths, `.git`/`.agents`/`.codex`/`.claude`, broad unapproved targets, oversized content, secret payloads and preimage conflicts. Never infer approval from output text. Preserve the existing profile/marker receipts and generation fence. |
| Transaction/recovery | Under the held allocation lock, prove native writer quiescence, live lease and valid policy receipt before applying. Record patch hash and durable per-file intent/preimage/postimage before mutations. Use no-follow directory FDs, same-directory temporary regular files, fsync and atomic replace/create/delete semantics; prevent target replacement races. Resume only proven matching intents; ambiguous partial state becomes uncertain/manual resolution, never another native job or a fresh blind patch application. |
| Cancellation | Before application, cancellation means no edits. During a recorded application, stop new edits, classify/restore only proven owned partial mutations and persist the result; no success or ACK without resolved intent and stopped proof. Cancellation/restart must not replay a model turn. |
| Existing pipeline | Worker runs the registered checks on the applied tree; independent reviewer sees that tree. Existing reviewed commit, allowed-path diff, marker/config seal and serial integration gates remain mandatory. No auto-merge into main. Read-only planner/reviewer output cannot enter the patch writer. |
| API/orchestrator/UI | MVP can keep current `trusted-development`, immutable policy and read-only skills/MCP registries. If backend/result capability becomes selectable in an API snapshot, add an explicit typed/versioned field and refresh umbrella contracts; never let arbitrary request config choose host permissions. UI must show agent-authored patch versus native write, unsupported binary/interactive operations and readiness gates. |
| Regression coverage | Three concurrent fake structured results and distinct worktrees; wrong role/path/epoch/seal; malicious payloads; create/replace/delete; duplicate exact patch delivery; preimage conflict; crash at each write/fsync/receipt window; cancellation before/during apply; held locks/live provider; independent review/commit/integration. No model calls needed for source verification. |

All of the implementation and offline tests above can be done **source-only now**, without changing installed runtime, account privileges, CLI version, manifest/config, filesystem/security policy, authentication or listeners. The existing read-only `adf.scoped-files.v1` must remain unchanged. This report proposes the exact next source work; it does not claim that work is already delivered or that current `shared` executes writing jobs.

## Alternative for iterative in-turn editing

A later explicitly approved `adf.scoped-files.v2` write broker could expose bounded exact-path create/replace/delete tools while native shell stays read-only. The pinned [local stdio MCP launch path](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/codex-mcp/src/rmcp_client.rs#L1190) supports ADF-owned host processes; this must not be mistaken for a sandbox of a generic MCP server. Existing ADF v1 supports only `read_file` / `read_marker`, and `Executor`/API explicitly refuse Codex write tools. Therefore a write broker needs a new closed contract, API mappings, lease/cancel-aware authoritative writer, safe mutations/idempotency and independent contract tests. Do not add write tools to v1 or silently reinterpret `observe`.

This route gives iterative feedback within a turn but has more lifecycle and per-call authorization work than post-turn patches. Source implementation/prototype tests can be built without activation; enabling a write-tool catalog/allowlist in deployed policy is a separate explicit permission decision. Live pinned MCP write behavior has not been verified by this no-model investigation.

## Why other shortcuts are unsuitable

| Option | Assessment under current constraints |
| --- | --- |
| Empty `.codex` exception | Changes the accepted strict guard and introduces a new transient race/allowlist. Not authorized or selected. |
| Switch to legacy/less restrictive sandbox | Changes the isolation mechanism and requires separate evidence/approval. Not needed by the patch route. |
| Three subprocess CLIs against one profile | Loses the single refresh owner design and does not prove compatible configuration isolation. No auth copying or multi-client profile workaround is authorized. |
| Per-job container/namespace with private metadata overlays | Possible future architecture, but current worker has no Docker group/socket privilege. A new container runner or OS sandbox, filesystem mappings, lifecycle proofs and authorization would be required. No new privileges or mounts were installed. |
| Paid API fallback or CLI upgrade | Outside current subscription-only and exact-pin constraints. |

## What requires new agreement

1. **Execution choice:** acknowledge agent-authored patches applied by the worker as the selected MVP coding mechanism, its bounded text-file limitations and the exact existing original-job write scope. This report is a proposal, not a user requirement. Source implementation can precede deployment approval.
2. **Exact installation/deployment:** after source review/QA/CI, approve the new immutable worker release, retained old package/dependency/source inventories, drain/rollback and only the dedicated provider/consumer switch to the new backend. Existing source publication permission does not authorize this installation. API/UI deployment is needed only if their selectable capability/contracts change.
3. **A fresh bounded model acceptance:** authorize fresh synthetic IDs and explicit turn/concurrency/time/output limits because the previous three-job budget is exhausted. Test three agent-authored patches in isolated worktrees, skills/MCP reads, one targeted cancellation, consumer/owner failure recovery, result/ACK proofs, review/checks and integration. Use the existing subscription profile, no new login/auth copy and no paid fallback. These are not scheduled or executed by this report.
4. **Only if selecting the alternative:** separately authorize a v2 MCP write capability/policy or a new OS/container isolation design. The preferred post-turn patch route does not require an empty-directory exception, Docker/sudo membership or a change to strict `.codex` guard.

Until implementation and actual authorized acceptance pass, parallel coding and full MVP readiness remain incomplete. Publishing fail-fast/recovery-only is useful safe progress, not a substitute for this requirement.
