# Shared-patch source release checkpoint

> Historical October 11 source/proposal record. The separately authorized October 12 installation and blocked queue trial are recorded in the [current runtime checkpoint](shared-patch-runtime-checkpoint.md); its installed-state evidence supersedes this document's historical statements. Readiness remains false.

Current shared source also requires [operator-owned native read permissions](shared-native-read-policy.md). The legacy native preflight FAILED; source canaries and future installation/acceptance are separate. The exact scope below must include both mandatory operator flags; old source hashes remain historical.


October 11, 2026. Source delivery only; no installation or native/model acceptance. The [source contract and phases](shared-patch-source.md), [ADR 008](adr/008-shared-patch-and-isolated-checks.md) and [separate exact installation/acceptance scope](shared-patch-deployment.md) are the current documents. Older release checkpoints retain their historical pins/results.

## Exact source publication

Worker `a0b2abad379802242091d16398b2e7c34c756026` contains the bounded shared-patch backend, writer and isolated checker. Orchestrator `9932a87e676b651c7ff2eb89246b900c6d0f843e` explicitly makes patch safety/conflict failures non-retryable; its [exact-commit CI](https://github.com/alex-kzr/adf-orchestrator/actions/runs/38164378320) succeeded. Its request builder/envelope did not change: the source-bound fixture records the original capture commit and current verification fingerprint separately. No new native request was captured.

Worker [exact-commit CI](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38165325565) succeeded, including the exact-hash standalone namespace fixture, static checks and the complete Linux suite. Both child commits are published to their existing user-provided origins; no runtime installation follows that publication.

API stays `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca`; frontend stays `92bfa64f38202872dbf2999d9343884a12036959`. Dependency pins, `.gitmodules`, provider policy source and SPEC are unchanged. The umbrella pins committed children first; its exact CI receipt is provided with the final delivery, avoiding a self-referential commit hash in this document.

## Verification boundaries

Release worker QA runs in a fresh private `/var/tmp` environment under the existing regular WSL worker identity. Existing pinned QA libraries are copied read-only into that environment; no installed package, authorization or source manifest is changed. Only synthetic fake-provider processes, real temporary Git allocations and the separately pinned standalone namespace launcher execute. The adapter contract, hostile patch paths/content, durable crash/cancellation/ACK fencing and complete three-developer failed-check/repair/review/commit/serial integration pipeline are offline evidence.

The final source passes 291 Linux tests with zero skips, Ruff, strict mypy across 28 worker files and Bandit with zero medium/high findings. Orchestrator passes 33 tests, Ruff, strict mypy across 11 files and Bandit with no findings. Umbrella passes 94 tests with four documented platform skips, six unchanged API/model snapshots and docs/contracts/SPEC/gitlink/heuristic-secret verification. [Sanitized evidence](evidence/shared-patch-source-2026-10-11.json) records these checks; CI/native acceptance are distinct from local offline evidence.

Independent read-only source review found no remaining blocking P1/P2 defects after task/kernel-resource syscall denial, backup cleanup guards, registry preflight and mutation-proof fixes. The fake-owner restart fixture now waits for its old owner thread to finish socket cleanup rather than treating a stale socket as replacement readiness. This is a test synchronization correction, not a production provider/auth repair.

## Installed runtime preserved

Read-only verification confirmed all 23 installed and retained-source Python files match worker `13c4624a8791fa4c9035c284a4689e412f0b7b42`. Reads used no-follow/no-atime and verified observed file metadata remained unchanged. Recorded provider, consumer and native server identities are stopped; the existing Codex/Claude profile directories retain UID 1001 and 0700, and their contents were not read. The default `.codex` layer remains absent. Existing auth, sealed manifest, API settings, other services, users/groups, Windows, listeners, firewall and global Git security settings were not changed. No model/thread/turn, login, setup-token or paid API fallback occurred.

## Open deployment gates

Native read-only generation does not establish secret-read isolation: the pinned native sandbox can expose full host reads. Checker v1 accepts single-process pinned Python only; Node/React/build/thread/subprocess checks require another reviewed release. No broad MVP readiness is claimed. A future approved installation uses the exact source pins above, retains verified `13c4624a` rollback, leaves the existing provider manifest unchanged and introduces only the separately scoped private checker manifest/consumer selection. The proposed subscription acceptance is at most three concurrent developers, ten native turns and twenty minutes, including the full loop plus cancellation/consumer/provider-owner failure cases. See the separate scope before authorizing any runtime work.
