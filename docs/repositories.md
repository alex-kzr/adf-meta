# Repository lifecycle and publication

## Current repositories

The user supplied these exact GitHub URLs. They are configured locally as origins; module URLs also appear in `.gitmodules`. The local umbrella directory stays `C:\Users\admin\Documents\workspace\projects\adf`; its GitHub repository name is **adf-meta**.

| Local path | Configured origin | Branch |
| --- | --- | --- |
| umbrella root | https://github.com/alex-kzr/adf-meta | main |
| frontend | https://github.com/alex-kzr/adf-web | main |
| services/api | https://github.com/alex-kzr/adf-api | main |
| services/orchestrator | https://github.com/alex-kzr/adf-orchestrator | main |
| services/runtime-worker | https://github.com/alex-kzr/adf-runtime-worker | main |

Read-only `git ls-remote` on October 10, 2026 succeeded for all five URLs and advertised no refs. Checks used no credential helper or interactive authorization. This confirms read access at that time, not write permission or successful publication. These were prepublication checks. The user later explicitly authorized this one-time publication; see [delivery status](delivery-status.md) for observed results. This is not standing authorization for future pushes.

Four child repos remain real Git submodules with pinned `160000` gitlinks and absorbed Git directories. Module README updates are committed before updating umbrella gitlinks. Never use `submodule update --remote` to replace explicit pins.

## Publication order and manual commands

Origins, `.gitmodules`, sync and local documentation commits have already been prepared. From the original checkout, push **four modules first**, then umbrella:

```powershell
Set-Location 'C:\Users\admin\Documents\workspace\projects\adf'
git -C frontend push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'adf-web push failed' }
git -C services/api push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'adf-api push failed' }
git -C services/orchestrator push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'adf-orchestrator push failed' }
git -C services/runtime-worker push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'adf-runtime-worker push failed' }
git push -u origin main
```

Stop if any child push fails; the umbrella must not advertise unavailable child commits. No force push, global file-protocol changes or new GitHub repository creation is needed. Existing authentication/write access is the user's responsibility; read-only availability checks do not establish it.

After all pushes, use a **new** directory to verify the published recursive clone:

```powershell
git clone --recurse-submodules https://github.com/alex-kzr/adf-meta C:\Users\admin\AppData\Local\Temp\adf-meta-published-check
```

Then inspect exact pins/status and run `python scripts/verify.py` with the documented development dependencies installed. A remote recursive clone is a post-publication check; its observed status is recorded in the delivery report. A local recursive clone from the updated umbrella would also resolve its child URLs through GitHub; it is no longer an offline validation command.

## Offline export and restore

Commit all children and umbrella gitlink updates first. Export refuses dirty repos/pin mismatches. Only committed history/refs are bundled; IDE/env/credential/runtime files remain outside. Trust the export source: SHA-256 detects corruption, not replacement of both bundles and manifest.

```powershell
python scripts/export-bundles.py .bootstrap/export
# Choose a destination that does not exist.
python scripts/bootstrap-local.py .bootstrap/export C:\Users\admin\AppData\Local\Temp\adf-meta-restore-example
```

Current exports contain `adf-meta.bundle`, four child bundles and `manifest.json`. Copy exactly the manifest-listed files together; unrelated older exports may remain in ignored storage. Bootstrap also accepts previous v1 exports whose umbrella name/file is `adf`/`adf.bundle` for backwards compatibility.

Bootstrap verifies checksums and exact gitlinks, clones umbrella from bundle, creates real local bare child mirrors under destination `.bootstrap`, overrides only that checkout's submodule URL config and initializes with command-local file permission. It does not contact GitHub or delete/overwrite an existing destination. **Committed `.gitmodules` keeps the real GitHub URLs, while the restored local config/origins use offline mirrors.** This distinction makes offline restoration work before pushes. Original ignored mirrors are retained for historical foundation snapshots; they are no longer the current original checkout's origins.

Restored umbrella is on main; children are detached at pinned commits. Before publishing a restored checkout, attach main to the desired pin (inspect any existing branch before changing it), replace local bundle/mirror origins with the five exact URLs above, then run `git submodule sync --recursive` and verify every origin. For example:

```powershell
git remote set-url origin https://github.com/alex-kzr/adf-meta
git -C frontend remote set-url origin https://github.com/alex-kzr/adf-web
git -C services/api remote set-url origin https://github.com/alex-kzr/adf-api
git -C services/orchestrator remote set-url origin https://github.com/alex-kzr/adf-orchestrator
git -C services/runtime-worker remote set-url origin https://github.com/alex-kzr/adf-runtime-worker
git submodule sync --recursive
```

The old foundation umbrella commits still refer to local bootstrap URLs. Preserve their offline restore path rather than rewriting history. Keep bundles until a published recursive clone is verified. No license or new permission grant is inferred by configuration changes.
