# Local release and publication checkpoint

Latest October 12 runtime result: [completed existing-profile metadata window](shared-auth-metadata-completed-checkpoint.md) installed worker `0dd5ac7` with verified f5 rollback. `initialize` ended with `transport_closed` in 88 ms; zero threads/turns, used one-owner allowance, all owned processes stopped. Old three uncertain/unACKed deliveries and all 70 Redis entries remain unchanged; provider/consumer stay stopped and readiness is false. Earlier installed-state statements below are dated history.

Latest source-only release: [shared-patch implementation](shared-patch-source.md) completes the bounded source loop with a durable writer, closed Python checker and explicit reconciliation fences. [ADR 008](adr/008-shared-patch-and-isolated-checks.md) and [separate installation/acceptance scope](shared-patch-deployment.md) record limitations and approval boundaries. Installed `13c4624a`, unchanged policy/auth and stopped runtime are preserved; source publication is separate from deployment or a native trial. Older pins below are historical.

Latest runtime checkpoint: [authorized preserving rename and resumed shared queue](shared-resumed-checkpoint.md). Installed worker remains `a8bb1cc`; published source remains `859cc534`. The exact default directory is backed up, one native turn is cancelled safely, and two pre-thread failures reveal an explicit-profile `config.toml` guard blocker. Dedicated services are stopped and readiness is false. No further runtime pin replacement or profile/guard remedy was performed.

Latest source-only repair: [explicit operator profiles in doctor](doctor-profile-repair.md) is published at worker `859cc5341643d2031a622e662dbaf23be2c5badb` with 158 passing Linux tests and [successful exact-commit CI](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38146428340). The dedicated installed execution worker remains `a8bb1cc`; the other three module pins are unchanged. No installed runtime replacement, pending `.codex` move or new model execution accompanied this publication. The current runtime checkpoint below and its failed queue evidence retain their historical installed pin; they do not assert that the new source is deployed.

Current October 11 repair checkpoint: worker `a8bb1cc97015e9d46c25acdc9c88228cd65a4876` is published and byte-verified in the dedicated venv; 146 Linux tests and exact-commit CI pass. The existing orchestrator environment baseline now reaches the shared owner. Three real queue claims then fail the unchanged ancestor `.codex` guard before any native thread/model call. All results are durable/ACKed and dedicated sessions are stopped. Both personal logins remain completed. [Current installation, exact remaining blocker and operator proposal](fixed-worker-checkpoint.md) and [sanitized evidence](evidence/worker-fixed-queue-2026-10-11.json) supersede the historical login/repair-pending statements below. Native skills/MCP/isolation/cancel/crash acceptance and readiness remain false.

October 11, 2026, local completion after host reconnection. The umbrella remains `adf-meta` at `C:\Users\admin\Documents\workspace\projects\adf`. All four child directories are independent repositories and real `160000` submodule gitlinks. `SPEC.md` is unchanged. Readiness remains false; see [acceptance status](acceptance-status.md) and [operator actions](operator-acceptance.md).

## Latest publication and account update

On October 11, the user's direct five-URL instruction authorized ordinary publication. Children were pushed before umbrella implementation snapshot `d941d535c3ca0cf3da1ce53291addf730d55af76`. Remote heads match frontend `92bfa64`, API `a0e0205`, orchestrator `6fe7c14` and worker `8af54fd`; all five exact-head CI runs pass. A fresh recursive GitHub clone resolves every pin and passes the verifier (230 files). The source verifier passes for 231 files. See [sanitized evidence](evidence/publication-account-2026-10-11.json); this subsequent documentation update records the completed operations.

The user separately and directly authorized `adf-worker` in Ubuntu, only primary group `adf-worker`, private home/runtime/config directories (0700), and copying exactly the existing ADF worker/Redis service files into its config (0600, new owner). Provisioning completed as UID 1001/GID 1002. Checks from that actual UID prove the listed ownership/modes, no noninteractive sudo listing permission and no Docker socket access. Existing user/group metadata and source service files were preserved. No provider/Windows/admin credentials were copied, no personal login occurred, and no tools or services were installed for the new account.

A subsequent direct human instruction authorized runtime preparation and API deployment. Worker `8af54fd` is installed at `/home/adf-worker/ai-factory/tools/worker-venv`; Python 3.12.9, uv 0.12.18, Node 24.21.0, Codex 0.157.0 and Claude Code 2.1.296 are installed from verified public distributions. Both persistent private profiles are prepared outside projects/worktrees. Only API was recreated at exact `a0e0205`; the new allowed root was appended and all other settings, mounts/ports/security options and 70 other containers were preserved. Drain, installed-source, dependency and rollback dry-run checks pass. Read [exact login commands and rollback](dedicated-runtime.md) and [evidence](evidence/dedicated-runtime-2026-10-11.json). Personal login is the prerequisite for the already authorized shared provider/consumer switch and bounded queued acceptance. Neither was started; readiness stays false.

The sections below preserve the earlier prepublication/preprovisioning checkpoint and approval history. Their unpublished/account-pending statements are historical and are superseded by this update; their older running-service claims are superseded by the runtime preparation above; native acceptance remains pending.

## Exact child refs

These published heads were observed through read-only `ls-remote`. Hosted CI links apply to the listed published heads; a green earlier build does not validate an unpublished child commit.

| Path | Repository | Current local commit | Observed published commit | Published CI |
| --- | --- | --- | --- | --- |
| `frontend` | [adf-web](https://github.com/alex-kzr/adf-web) | `92bfa64f38202872dbf2999d9343884a12036959` | `92bfa64f38202872dbf2999d9343884a12036959` | [passed](https://github.com/alex-kzr/adf-web/actions/runs/38081761107) |
| `services/api` | [adf-api](https://github.com/alex-kzr/adf-api) | `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca` | `9a55fac1e7eff6d7b68cc1f5b38e58aa97789220` | [passed](https://github.com/alex-kzr/adf-api/actions/runs/38080853784) |
| `services/orchestrator` | [adf-orchestrator](https://github.com/alex-kzr/adf-orchestrator) | `6fe7c1402864210fd8b6c2aed44695436c147f3f` | `6fe7c1402864210fd8b6c2aed44695436c147f3f` | [passed](https://github.com/alex-kzr/adf-orchestrator/actions/runs/38082038475) |
| `services/runtime-worker` | [adf-runtime-worker](https://github.com/alex-kzr/adf-runtime-worker) | `8af54fd1590139fa0730e7705d276188c9be3ca3` | `dcea28d25da7fde70cbfa6920677836ce68d4c20` | [passed for published DCEA only](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38114321085) |

The last published umbrella is `5a4e600046f130678111b533987de9aea1e4220a`, with [passed CI](https://github.com/alex-kzr/adf-meta/actions/runs/38081219696). Its pins are frontend `e5ff745`, API `9a55fac`, orchestrator `431153c` and worker `e39b1e5`. A fresh recursive clone and an offline five-bundle restoration of that exact published snapshot were verified. The commit containing this checkpoint pins the current local child commits above; it is not claimed published.

## Running snapshot

Latest local provider implementation: profiles `faa9164`, shared backend `8af54fd`. All 134 Linux tests, Ruff, strict mypy (22 files) and Bandit medium/high checks pass. The pinned native binary passed an isolated empty-profile handshake with zero model/thread calls. See [ADR 006](adr/006-provider-profile-ownership.md), [migration](../services/runtime-worker/docs/shared-provider.md) and [evidence](evidence/provider-shared-2026-10-11.json). These new commits have not been pushed or installed. Running versions and credential/account state remain unchanged; exact publication/account/deploy questions are pending. Native shared acceptance and MVP readiness remain false.

The October 11 read-only reconnect check received HTTP 200 from frontend `http://127.0.0.1:8088`, API health/readiness `http://127.0.0.1:8080` and Langfuse `http://127.0.0.1:3000`. API readiness reports `database_ready: true` and `runtime_ready: false`; healthy services do not imply accepted MVP readiness. Existing core containers remain healthy and their published ports are loopback. No services, identities, authentication stores or network settings were changed during reconnect completion.

The existing healthy API still runs `9a55fac`; its image ID is `sha256:b7e91591b729bb1437309510eb7e412e0ed2c6b03ef7457cb91ce444b8a7a538`. The production worker venv still contains `e39b1e5`; reconnect byte checks of installed adapters/process/supervisor match that commit. Its previous consumer was restored after the October 10 rejected installation, but the October 11 check finds its old PID absent and no own-user ADF `serve` process. Starting/replacing the consumer remains pending deployment authorization; reconnection alone did not authorize it. Frontend `92bfa64` and orchestrator `6fe7c14` were rebuilt in the existing local contour. A candidate API image was built but was not installed. New native scoped-capability trials use only a disposable ext4 fixture and the existing editable test venv; they do not prove queued API/Redis deployment.

## Verified evidence and limitations

- [Native Architect](evidence/codex-architect-plan-2026-10-10.json): structured plan, exact approval, bounded human edit and regenerated proposal; coding was not launched.
- [Native approved skill/scoped MCP](evidence/codex-scoped-capabilities-2026-10-10.json): the complete five-operation worker chain passes with actual assigned MCP audits, hidden skill/marker hash matches, independent native review, unchanged main and verified closure of all owned sessions. Two observed bundled hosts use separate PGIDs within their CLI SIDs. The fsynced local ledger is a test double; API/Redis queued deployment is not claimed. Earlier failed/rejected fixtures remain evidence.
- [Isolated runtime recovery](evidence/runtime-recovery-2026-10-10.json): two fresh internal Docker contours, restored checkpoint/outbox identities, initially empty Redis, five successful mock operations, 13 original artifact hashes, duplicate terminal acknowledgements and unchanged main. This is real Executor/Supervisor/API execution through the bounded QA bridge; it is not unfinished native CLI host-loss recovery.
- API: 151 tests, including real PostgreSQL checks; the parent independently reran 77 scoped-registry HTTP cases. Worker: 116 Linux tests, with 60 process/session/scoped cases independently rerun by the parent, plus strict typing, lint and security checks. Frontend: 27 tests plus lint/typecheck/build. Orchestrator: 32 unit and seven actual HTTP/SQL wire cases. Recovery helpers: 19 Windows and 19 Linux cases, strict typing, lint and Bandit with zero findings. Umbrella: 90 tests with four expected platform/opt-in skips; all six API snapshots match.
- New unpublished source cannot claim hosted CI. The umbrella adds a separately pinned worker-dependency CI job for recovery helpers, avoiding incompatible API/worker telemetry toolchain combinations.
- Existing live native concurrency, dependencies, component restart, cancellation, conflict/resolution, Langfuse trace/outage and browser evidence remain indexed in [documentation](README.md). No hostile-code sandbox, authenticated WSL Claude, separate worker identity or external-origin denial proof is claimed.

## Publication and installation approval

Automatic approval review initially rejected the ordinary worker push and one identical retry because it could not validate the later human publication authorization forwarded from the parent. It separately rejected installation into the existing worker venv and replacement of the local API container because of service-disruption/rollback risk without trusted deployment authorization. No force push, credential workaround or alternative outbound publication was attempted. At that earlier checkpoint both increments were local and the runtime was returned to the previous consumer/API snapshot. The direct-confirmation update below supersedes worker publication; API and the current umbrella checkpoint remain local.

The pending publication request is restricted to ordinary `main` pushes to the five exact existing user-provided origins. The pending runtime request is restricted to installing the reviewed worker snapshot, replacing only the local API container, and restarting only the ADF consumer after checking that no jobs are active, followed by one bounded capability fixture. Account creation, provider login and network changes are excluded and remain distinct operator proposals.

## Exact next operator steps

### October 11 direct-confirmation update

The human directly confirmed push in this execution task. The ordinary worker push completed and anonymous `ls-remote` verifies `dcea28d`; GitHub Actions run `38114321085` completed successfully for that exact head. Frontend `92bfa64` and orchestrator `6fe7c14` also have successful CI for their exact current published heads. API `a0e0205` still has no hosted run because its push was rejected before execution: automatic approval review required the direct confirmation to identify the repository and destination explicitly. A single exact five-origin publication question is pending. No rejected publication was retried through another transport.

The human also directly confirmed deployment and the account. Automatic approval review nevertheless rejected the inspected account helper before execution because the brief confirmation did not itself enumerate the account, paths, memberships and two service-token files. `adf-worker` is not created. One combined question now enumerates both account provisioning and the exact worker/API/consumer deployment, excluding provider/admin authentication, other accounts/services, Windows and firewall changes. Elapsed time and a delivered question do not constitute approval. The new deployment operation has not been executed while this exact confirmation is pending.

Read-only API preflight found six completed and four cancelled runs, with no nonterminal executions. A private rollback snapshot at `/home/alex/ai-factory/tools/deployment-20261011-retry-snapshot-complete` verifies thirteen installed worker Python files against old commit `e39b1e5`, archives only package/essential metadata/entrypoint, and records the old immutable API image with an override. It copies no provider authentication or service-token files. The first incomplete snapshot is preserved separately. Readiness remains false; neither a backup nor source/hosted tests prove the pending installed queued capability run.

1. Verify `git status --short`, each child status, `git submodule status`, `git ls-files --stage` and all five origins. Do not publish an umbrella ref before its child refs are available.
2. After publication authorization is accepted, use the existing origins and the [child-first ordinary push commands](repositories.md#publication-order-and-manual-commands). No new GitHub repository, invented URL or force push is needed.
3. Verify a new recursive GitHub clone with exact current pins and run `python scripts/verify.py`. Until publication, use the committed five-bundle offline scheme below; a recursive clone resolves the real GitHub child URLs and cannot recover unpublished child refs.
4. Approve/review the exact new `adf-worker` identity proposal, provision its own private runtime without sudo/docker memberships, and complete personal Codex/Claude logins. Then perform native provider and privilege denial checks under that identity. Do not copy provider authentication stores.
5. Supply an authorized external host or suitable VM for the bounded ADF-port denial probe. Do not widen listeners or add inbound firewall exceptions.

```powershell
python scripts/export-bundles.py .bootstrap/export-release-20261011-final
python scripts/bootstrap-local.py .bootstrap/export-release-20261011-final C:\Users\admin\AppData\Local\Temp\adf-restored-release-20261011-final
python C:\Users\admin\AppData\Local\Temp\adf-restored-release-20261011-final\scripts\verify.py
```

Export only clean committed state. The destination must not exist. Bundles/private reports/credentials/runtime files remain ignored; bootstrap uses command-local file permission and fresh local mirror URLs without changing committed `.gitmodules` or global Git settings.

## Frozen execution bytes and committed source

The immutable native evidence SHA-256 remains `3108ca79246d84d61b35983f592e7e26864e1cfefab60baf5ff095db1b12451e`. Its `source_freeze.files_sha256` records the actual CRLF worktree bytes used during execution. Git's existing text policy stores LF blobs. The reconnect check compared every one of the fourteen recorded worktree hashes and proved that each committed blob differs only by CRLF-to-LF normalization; no measured execution hash or native trial was rewritten. The final worker commit is `dcea28d25da7fde70cbfa6920677836ce68d4c20`. Its committed LF blob digests below support fresh-checkout verification independently of checkout newline policy.

| Worker-relative path | Committed LF blob SHA-256 |
| --- | --- |
| `docs/development.md` | `3a542dd5e65fdd7f16293df09af2068389b34471a616b44c83b5759b8b30c4ef` |
| `src/adf_runtime_worker/adapters.py` | `e5868eec6151d55d997eabf5a4bcdef40a1e3fb1f5df903f56e342e556e04a43` |
| `src/adf_runtime_worker/executor.py` | `bf72dfd6a0d634154dcd08209236649794647df43a270b8baec9450d79c0d378` |
| `src/adf_runtime_worker/git_workspace.py` | `d2fa419654c4383c3372ab1197924dda463ee98bf8a16683930244a50e74c421` |
| `src/adf_runtime_worker/journal.py` | `ea6a188834b39d9628cdbbb75e70d58e5cc623572918fc51cb5b740337e2dbc4` |
| `src/adf_runtime_worker/process.py` | `bc3050c78ef3b6283af5345c57cf9da32c7356bbe9eea6b3351383b055d5ad4b` |
| `src/adf_runtime_worker/supervisor.py` | `c96d80641792f504a9adb09a73d7f2ff72579934a6ea1ad5c2db47a46e751414` |
| `src/adf_runtime_worker/pidfd.py` | `8f5bd1813e53e6c4d1f3a269cd0d340db4c5d0c3f045ae9b4469eef3cd5c0687` |
| `tests/fixtures/codex-0.157.0-scoped-schema.json` | `0fc465b7a8076da6c3b4e1ffd4d5adc1e6e87dd64bced21bfff69d26faf4082e` |
| `tests/test_client_supervisor.py` | `0c023dd2f9135e198351c23a8f66e2123420c3d93f2ecb2fb731bdad99872659` |
| `tests/test_process.py` | `06368815d447ecaf61f0f3a6517def9664f454e9b6cc8003877bdddd78537c30` |
| `tests/test_scoped_capabilities.py` | `59ac4d84c57e4af2769eee6559bd29e52a264c31cf16fce638237f8f2e7a9f0f` |
| `tests/test_session_lifecycle.py` | `2123dcce8812d15a565aa33b71e6099fcc19041439264f38044040efcb5fa9b9` |
| `tests/test_service_recovery.py` | `96a1490999a121e8ce3ad642fee4a43ae0022efa1f4ea7ce01d0f7e3fa3ecc9a` |
