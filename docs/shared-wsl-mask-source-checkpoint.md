# WSL native mask repair: source verification and proposed installation

October 13, 2026. Source and separately approved installed worker:
`a3428799713e94e65153b87c8df0771fd9077f2a`. The exact installation and bounded
native queue trial are recorded below. Readiness remains false; protected operator
reports retain detailed journals and current runtime state. Source QA remains
distinct from the later authenticated acceptance.

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
metadata files. The [candidate installed file and mode inventory](evidence/shared-wsl-worker-file-inventory-2026-10-13.json) lists all 39 proposed replacement files: 29 modules, nine distribution/installer metadata files and one console entry. Rehearsal modes match existing modes: 0600 for source/metadata and 0711 for `bin/adf-worker`. Console scripts and installer metadata are generated by uv. The already pinned build
tool was [setuptools 80.9.0](https://pypi.org/project/setuptools/80.9.0/), checked
against its official wheel hash; this is not a signature-verification claim.
The helper requires a fixed artifact-manifest hash, regular single-link/no-follow
inputs, exclusive private staging copies, rejects startup hooks in dependency
wheels and enforces a 180-second total alarm. Independent review passed before
its sole actual execution.

Live source-install preflight found 40 literal RECORD entries, rather than the
39 in the candidate wheel-install inventory. The sole extra entry is uv's generated
`adf_runtime_worker-0.1.0.dist-info/uv_build.json`: exactly two bytes, `{}`, a regular
single-link file owned by `adf-worker` with mode 0600. The first live installer
refused this shape before invoking uv. Pinned
[uv 0.12.18 source](https://github.com/astral-sh/uv/blob/0.12.18/crates/uv-install-wheel/src/wheel.rs#L839)
accounts for optional source-build metadata and its RECORD entry. Candidate wheel
installation still replaces exactly the published 39 files; rollback restores the
verified old wheel and this empty metadata entry, then verifies all 40 old entries.

The preexisting package-only `__pycache__` has 26 private regular files; one did
not match compilation of current public old source. That observation does not
establish its cause. Preserve the entire validated cache directory by a
same-filesystem rename into private installation staging, retaining its original
inodes and payload. Cache validation and relocation neither read nor copy nor
execute bytecode payload. Rollback renames the retained directory back after old
source/metadata/dependency verification. No profile, auth or dependency payload
is copied. This preservation was applied during the separately approved installation.

The [complete preserved-environment comparison](shared-wsl-preservation-checkpoint.md)
matches all ten retained containers' image/Config/Env/HostConfig/mounts/configured
network/health data. Six StartedAt values and computed network endpoint fields differ;
their cause is unproven. Original baselines remain unchanged. The separate fresh
13-component/API/Redis preflight passed with no active work, PEL zero and all 73
entries retained. No ADF health failure or settings change is inferred from timestamps.

## Separately approved reversible installation: applied

This source repair changes the effective runtime security policy even though it
adds no host read grant. The operator separately approved this exact policy/worker
installation on October 13 at 08:22 UTC. The candidate, verified inventory and
completed rollback proof remain the scope; no other grant or credential change is
authorized. Follow the [finite live acceptance plan](shared-wsl-live-acceptance-plan.md).

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
   acceptance is a separate bounded action. Normal use of existing subscription
   authorization is already within the approved MVP task; it is not a generic
   blocker. Do not run login/setup-token, copy/create credentials, request forced
   refresh or change account configuration. Stop and report a concrete new auth or
   persistent-access action if required. No paid API fallback.
6. On failed checks, stop only owned candidate sessions, preserve any new journals
   and SDK state, reinstall the verified old wheel in the same stopped venv and
   confirm canonical module/dependency parity. Leave provider/consumer stopped;
   do not revert database/Redis data or overwrite profiles/secrets from backups.

## Observed bounded API/Redis result

The reviewed installer `0d3827dbdda6634fab181b4844c9cfc52254505b231c3e9215652f6f45b793a6`
installed exact `a342879` offline. All 29 source hashes, 39 candidate RECORD paths,
27 unchanged distributions, ownership/modes and sealed inputs passed. The old
empty uv metadata, original 26 cache inodes and verified old wheel remain private
and available for rollback. Installation itself made zero native model calls.

One fresh run, `523c5ba8-f9fa-4adc-b41c-58273cdbcf17`, used the existing subscription
and pinned Codex 0.157.0/Node 24.21.0. Three native developers overlapped in distinct
worktrees with distinct assigned native skills and successful scoped MCP calls.
A consumer crash/restart preserved the same provider generation and execution
identities, with no duplicate turn. The beta assertion failed once, then one fresh
repair passed. Seven native turns completed: four developer/repair and three review.
Two independent reviews and task commits passed (`f8effd8e7609b3c1199518c78041f4a9836c98e1`,
`797799e52eef5b06048d48b0512b562b7c5704e5`).

The gamma reviewer rejected unavailable independent skill/MCP provenance evidence,
although code, marker and registered test passed. Its automatic repair was refused
before a new native turn: serial earlier commits changed the repair allocation's
dependency tree relative to the original gamma worktree (`VERSION_CONFLICT`).
The worker's [snapshot guard](../services/runtime-worker/src/adf_runtime_worker/executor.py)
correctly retained that boundary. The run failed; integration did not execute.
Fix the synthetic task/reviewer evidence contract with explicit expected values
and bound audit evidence. Preserve the source task's immutable repair dependencies
in [orchestration](../services/orchestrator/src/adf_orchestrator/engine.py); alternatively,
place all independent reviews before serial commits in this acceptance graph.
Do not weaken the worker snapshot guard or grant reviewers extra profile/MCP access.

The dependent fault and Claude stages were not attempted after this failed gate.
Seven native turns consumed seven of the ten allowances; three remain unused.
The actual default model identifier is not exported by this adapter; no model name
is inferred. Upstream HTTP/inference request counts and billing remain unknown.
No login/setup-token, forced refresh, credential copy or paid API fallback occurred.

Final checks: all 14 new execution journals durable/ACKed and owned sessions stopped;
31 locks reacquired; Redis PEL zero, queue depth zero, 87 entries (73 prior + 14 new).
The synthetic main is clean at `ff3b0d4703e4b71e42c90b4ac5d22b7c8d5dbb63`.
Its temporary check registry was restored with revision fencing. All 13 production
components retain expected health; unrelated retained-container settings and frozen
baselines remain unchanged. Installed source stays `a342879`, provider/consumer are
stopped, rollback retained, and whole-MVP readiness remains false.
