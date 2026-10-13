# WSL native mask repair: source verification and proposed installation

October 13, 2026. Worker source commit `a3428799713e94e65153b87c8df0771fd9077f2a`. Source-only delivery; readiness remains false. No live policy,
provider, consumer, authentication, API, Redis, CLI pin or other service was changed
by this repair. Installed worker remains `0dd5ac7b8be6f792921f29bc376e520f3c0754c6`.
Protected operator reports remain authoritative for current runtime/queue state.

## Concrete failure and production diff

A bounded non-authenticated FS-helper control on the current WSL host failed
before its sole metadata request: bwrap mkdir at `/run/WSL`, `EROFS`, exit 1 in
64 ms. Fixed public categories were emitted; raw stderr and credential values
were not retained. This identifies the current pre-exec failure, not the cause
of discarded historical `thread/start -32603` responses.

The only production file changed is
[`native_read_policy.py`](../services/runtime-worker/src/adf_runtime_worker/native_read_policy.py):

```diff
- "/nix": "deny", "/run": "deny", "/mnt": "deny",
+ "/nix": "deny", "/run/current-system/sw": "deny", "/run/WSL": "deny",
+ "/mnt": "deny",
```

Codex 0.157.0 appends its empty WSL-interop tmpfs after policy filesystem mounts.
A denied, read-only `/run` ancestor prevents that child mount. Its sole minimal
read root under `/run` is `/run/current-system/sw`.
[Pinned primary source](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/linux-sandbox/src/bwrap.rs).
The root deny, minimal/platform selection, public vendor grants, private masks,
canonical guards, network denial, durable receipts and no-replay fences are retained.

## Boundary proof and verification

Independent source review found no blocking defect in the complete production/test
diff. Canonical guards prohibit runtime/profile/home under `/run`; canonical tool
roots and allocator-bound worktrees remain below that private runtime. There is
therefore no explicit read/write grant below `/run`. Its sole pinned minimal root
is denied. Other host descendants cannot appear in the empty guest tree, including
paths created after sandbox entry and symlinks resolving there. The SDK interop
mask exposes an empty guest view rather than the host sockets.

This is an invariant of the tested native host-data read boundary. It does not
prove every tool route or prohibit every guest temporary write. Trusted same-UID
host mutation remains outside the threat model; dependency upgrades require new
contracts.

The complete Linux suite passed **390 tests in 147.95 seconds**, with Ruff, mypy
(29 production modules) and Bandit at the existing medium/high threshold passing.
The focused two-case regression also passed before the full suite. All tests use
synthetic profiles and public checksum-pinned binaries; native model turns, login,
real authentication RPCs and real API/Redis acceptance runs remain zero for this source QA.

The updated fixture mounts only generated WSL/Nix trees, never host `/run` or real
profiles. Both direct and Nix-symlink minimal roots are tested. Existing `/run`
siblings, WSL/Nix contents, worktree/proc aliases, private and sibling worktrees
remain unreadable; assigned reads pass and persistent worktree writes/network fail.
A Python readiness handshake after actual sandbox entry precedes creation of five
late descendants/aliases, which all remain unreadable. Restoring the old parent
mask fails entry under the same synthetic WSL view; its exit code alone is not
used to identify an errno. Persistent native and Node/npm owners retain their
settings/skills/MCP metadata regressions. Fake turns are not model acceptance.

The interrupted first QA run is not counted. An intermediate full run had 388
passes and two fixture-admission failures before sandbox entry; the corrected
fixture uses normal trust/native bind calls and the actual test-owner generation.
It adds no bypass or fabricated seal. See [sanitized evidence](evidence/shared-wsl-mask-source-2026-10-13.json).

## Verified isolated rollback artifacts

The reviewed offline helper built exact candidate/old wheels from Git archives and
completed candidate -> `0dd5ac7` -> candidate in a new private synthetic venv in
**2.08 seconds**. All three stages matched 29 canonical module hashes and the same
27 distribution versions; `uv pip check` passed each time. The live venv's modules
and versions remained unchanged. The 26 dependency wheels came directly from
official PyPI and were verified against published SHA-256 values; their locked
versions are unchanged. No live dependency payload or personal authorization was
copied. All install commands were offline, with no SDK, auth, model or queue call.

| Artifact | SHA-256 |
| --- | --- |
| Candidate wheel, source `a342879` | `c207a703115585235a46cd7772eb0107d0176d8df3d453c3cf9f42e1ec39ca1f` |
| Rollback wheel, source `0dd5ac7` | `aacab91bb62858f284e2f455b3e4a7ef77db6cc225b148d0f90f1b6d7eaac3b0` |

Each ADF wheel contains exactly the 29 source modules and five distribution
metadata files. The [exact installed file and mode inventory](evidence/shared-wsl-worker-file-inventory-2026-10-13.json) lists all 39 proposed replacement files: 29 modules, nine distribution/installer metadata files and one console entry. Rehearsal modes match existing modes: 0600 for source/metadata and 0711 for `bin/adf-worker`. Console scripts and installer metadata are generated by uv. The already pinned build
tool was [setuptools 80.9.0](https://pypi.org/project/setuptools/80.9.0/), checked
against its official wheel hash; this is not a signature-verification claim.
The helper requires a fixed artifact-manifest hash, regular single-link/no-follow
inputs, exclusive private staging copies, rejects startup hooks in dependency
wheels and enforces a 180-second total alarm. Independent review passed before
its sole actual execution.

Read-only installed0dd/locks/quiescence/policy preflight passed with zero native
starts. A separate preservation health guard did **not** pass: its closed error
frame identified `unrelated_preserved`, not an ADF health check. Its predicate
compares unrelated containers' running/status/start timestamps as well as other
metadata. A direct names/state/status check found all 13 ADF components in their
expected states: 12 running, migrator exited 0; all reported healthchecks were
healthy. A subsequent bounded read-only observation identified only
`started_at` in the first failed unrelated-container comparison: name, image,
running and status matched that saved entry. Actual names/timestamps/values were
discarded. The next environment/HostConfig comparison was not reached, and the
remaining unrelated entries are not certified by this first-failure observation.
The cause of the startup-time change is not established. No services, guard baseline,
credential values or security settings were changed to make it pass. Resolve
that preservation gate before any live installation.

## Proposed reversible installation: approval still required

This source repair changes the effective runtime security policy even though it
adds no host read grant. General MVP authorization is insufficient for activation.
Obtain action-time approval for the exact published worker commit and this scope
before modifying the installed venv or starting its owner/consumer.

1. Recheck no active API/Redis work, free allocation/provider locks, stopped owned
   sessions, all existing service health guards, and the sealed operator inputs.
   Stop on drift, an active job, uncertainty or failed preservation proof. Never
   replay any old delivery.
2. Prepare offline wheels from the exact reviewed candidate and retained `0dd5ac7`
   source, validate the wheel file inventory and unchanged locked dependencies.
   Rehearse candidate-to-old restoration only in a fresh private synthetic venv
   with an empty profile. Retain existing stopped `f5a713a` rollback artifacts;
   their earlier verified rehearsal does not authorize running a legacy policy.
3. After approval, replace only the worker distribution in
   `/home/adf-worker/ai-factory/tools/worker-venv`: the 29
   `lib/python3.12/site-packages/adf_runtime_worker/*.py` modules, its
   `adf_runtime_worker-0.1.0.dist-info` installation metadata and the
   `bin/adf-worker` console entry. Reinstallation may regenerate bytecode inside
   that package only. Source/dependency pins must match the candidate manifest.
   Write a private installation receipt under `tools`, with no secret values.
   Do not replace the interpreter, other distributions or native/Node/Claude pins.
4. Ownership remains `adf-worker`; retain existing venv modes. New staging roots/receipt parent
   directories are 0700 and regular private receipts 0600. No account groups,
   HOME/profile permissions, secret files, manifests, API allowed roots, service
   endpoints, listeners, firewall, Git security settings or other users change.
5. Start only the existing ADF provider/consumer commands with their current
   sealed manifests and backend selection. Their private process journals and
   ordinary SDK runtime state may change. Installation itself performs no login,
   setup-token, auth-file copy, account probe or native turn. Authenticated
   acceptance is a separate bounded action: SDK operations may refresh existing
   credentials even without an explicit refresh RPC, so the credential boundary
   must be separately resolved before that action. No paid API fallback.
6. On failed checks, stop only owned candidate sessions, preserve any new journals
   and SDK state, reinstall the verified old wheel in the same stopped venv and
   confirm canonical module/dependency parity. Leave provider/consumer stopped;
   do not revert database/Redis data or overwrite profiles/secrets from backups.

No step above has been applied to the live runtime by this source delivery.
The exact candidate commit, verified wheel inventory and completed offline rollback
rehearsal must be attached to the approval record before activation. The unrelated-container
preservation gate and action-time live-security consent remain unresolved. Native queued generation,
three-job settings isolation, cancellation/recovery, skills/MCP, review and integration
still require authenticated acceptance. See [ADR 009](adr/009-operator-owned-native-read-policy.md),
[worker contract](../services/runtime-worker/docs/native-read-policy.md) and
[release gates](decisions.md).
