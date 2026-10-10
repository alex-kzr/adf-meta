# Repository lifecycle and publication

## Current local structure

| Path | GitHub name to create | Branch |
| --- | --- | --- |
| umbrella root | adf | main |
| frontend | adf-web | main |
| services/api | adf-api | main |
| services/orchestrator | adf-orchestrator | main |
| services/runtime-worker | adf-runtime-worker | main |

Child repos have real initial commits and gitlinks (`160000`) in the umbrella. `.gitmodules` uses real local bare repo URLs `./.bootstrap/remotes/<name>.git`. Those ignored bare repositories are available only in this local checkout. Relative URLs resolve against the parent origin; they are not portable published URLs. Do not claim that an ordinary copied/remote recursive clone works before publication. Git file protocol is enabled only per trusted command, never globally. Local config URLs may override .gitmodules during offline restore.

## Offline export and restore

Commit all modules and gitlink updates first. Export refuses dirty repositories or pin mismatches. Only committed history/refs are bundled; IDE/env/credential/runtime files remain outside. Trust the source export: SHA-256 detects corruption, not an adversary replacing both bundles and manifest.

```powershell
python scripts/export-bundles.py .bootstrap/export
# Destination must not exist. It may be an operator-chosen WSL ext4 directory.
python scripts/bootstrap-local.py .bootstrap/export C:\Users\admin\AppData\Local\Temp\adf-restore-example
```

Copy the whole export directory (five bundles + manifest.json) together for offline transfer. Bootstrap verifies checksums and exact Git pins, clones umbrella from bundle, builds real local bare child origins in destination .bootstrap, overrides only that checkout's submodule URL config and initializes children with command-local file permission. It never deletes/overwrites an existing destination or contacts GitHub. Restored umbrella is on main; child submodules are detached at pinned commits. Before developing a child, `git -C <module> switch main` if main matches pin, or `switch -c <new-branch>` from the pin. Origins in restored repos remain real local bundle/mirror paths until explicitly replaced.

When cloning directly from this existing local root, `git -c protocol.file.allow=always clone --recurse-submodules <local-adf-path> <new-path>` may use its real .bootstrap origins. It depends on that source root still being present; offline bundles are the portable prepublication delivery. They have been checked in a separate temporary directory as recorded in [delivery status](delivery-status.md).

## Exact user publication sequence

Create **five empty GitHub repositories**, with no generated README/license/gitignore: `adf`, `adf-web`, `adf-api`, `adf-orchestrator`, `adf-runtime-worker`. Choose owner/visibility/license yourself. No license grant is inferred by the foundation. Copy actual GitHub clone URLs; angle-bracket labels below are substitution instructions, not configured remotes.

1. From umbrella, replace each existing local child origin and push children first:

```powershell
git -C frontend remote set-url origin <ACTUAL-ADF-WEB-URL>
git -C frontend push -u origin main
git -C services/api remote set-url origin <ACTUAL-ADF-API-URL>
git -C services/api push -u origin main
git -C services/orchestrator remote set-url origin <ACTUAL-ADF-ORCHESTRATOR-URL>
git -C services/orchestrator push -u origin main
git -C services/runtime-worker remote set-url origin <ACTUAL-ADF-RUNTIME-WORKER-URL>
git -C services/runtime-worker push -u origin main
```

For a restored detached child, explicitly attach/create main at the desired pin before push; never force an unrelated remote history. Initial local root modules are already on main.

2. Put the same actual URLs in the authoritative submodule configuration:

```powershell
git submodule set-url frontend <ACTUAL-ADF-WEB-URL>
git submodule set-url services/api <ACTUAL-ADF-API-URL>
git submodule set-url services/orchestrator <ACTUAL-ADF-ORCHESTRATOR-URL>
git submodule set-url services/runtime-worker <ACTUAL-ADF-RUNTIME-WORKER-URL>
git submodule sync --recursive
python scripts/verify.py
git add .gitmodules
git commit -m "chore(repos): point submodules to published origins"
```

Inspect `git remote -v` in every module; sync updates initialized origins. Never use `submodule update --remote` to replace explicit release pins. If module commits changed, stage their four paths and commit those gitlink changes too.

3. Original umbrella has no origin: add the actual URL and publish. A restored bundle clone already has a local origin, so use set-url instead of add.

```powershell
git remote add origin <ACTUAL-ADF-UMBRELLA-URL>
git push -u origin main
# In a new directory, using the real published URL:
git clone --recurse-submodules <ACTUAL-ADF-UMBRELLA-URL> <NEW-DIRECTORY>
```

Recheck pins/status/links in that clean clone. No `--force`, global protocol.file.allow or global safe.directory changes are needed. Keep local bundles until the published recursive clone is verified. Existing local-only historical umbrella commit still refers to bootstrap URLs; document that older commit's offline restore requirement rather than rewriting history.

This sequence is documentation for the user. No push, GitHub repository creation or guessed remote was performed by the agent.
