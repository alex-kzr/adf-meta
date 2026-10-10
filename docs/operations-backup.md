# Private runtime snapshots and isolated restore rehearsal

This workflow backs up the current local ADF PostgreSQL database, registered API artifact bytes and committed target Git repositories. It runs from the Windows umbrella checkout and reads target repositories as the ordinary user of the `Ubuntu` WSL distribution on ext4. The implementation is [snapshot-runtime.py](../scripts/snapshot-runtime.py); [security](security.md), [reliability](reliability.md), [data model](data-model.md) and [local development](local-development.md) describe the surrounding runtime.

## Before taking a snapshot

The operator must hold the factory quiescent throughout the snapshot. Every nonterminal run must already be `paused` with `control.pause_requested=true`. Every execution must be `succeeded`, `failed` or `cancelled`. This includes old runs: `created`, leased, running, cancelling and `uncertain` executions all block backup. Reconcile uncertain executions through the normal recovery workflow; never relabel them merely to pass the gate. Do not start runs, resume runs, change definitions/settings, upgrade services or write target repositories while the snapshot is being taken.

The script performs authenticated read-only API requests, compares the complete visible execution inventory with global metrics, binds API project/run/execution/artifact metadata to a direct read-only PostgreSQL inventory, and checks API/database/Git inventory again after copying. It does not pause runs, cancel executions or stop containers. These checks detect observed changes; they are not an atomic server-side maintenance fence across the database, artifacts and Git. A change that starts and finishes between checks can escape the check. Operator-controlled quiescence remains a prerequisite.

Run the commands in PowerShell from the umbrella checkout, with the supported local Python environment:

```powershell
python scripts/snapshot-runtime.py --preflight
python scripts/snapshot-runtime.py --snapshot
```

`--preflight` checks the API drain gate only and creates no snapshot directory. `--snapshot` additionally verifies the local Docker context, the locked running `adf-postgres-1` service, and every registered Git repository/worktree. It rejects dirty or untracked worktree bytes, shallow repositories, target submodules, symlinks, paths outside the configured roots, non-ext4 targets and root-user WSL execution. Ignored worktree files are excluded. Preserve required ignored local data separately before proceeding.

Authentication comes from the generated `.bootstrap/secrets/admin-token` file. The `--admin-token-file` option accepts that same canonical file only; alternate credential paths are refused. The default API URL is `http://127.0.0.1:8080`; an explicit `--api-url` must remain a plain loopback HTTP origin. HTTP proxies and redirects are disabled. No token, API response body, provider credential or subprocess stderr is printed. The admin token is never included in a subprocess argument or snapshot.

The existing generated admin token has administrative scope; this workflow uses it solely for the listed read-only API routes. A separately issued least-privilege backup capability is future work. The script does not mint another token or change authentication.

## Snapshot contents and privacy

A successful invocation prints the generated `snapshot_id` and manifest path under the ignored `.bootstrap/runtime-snapshots/<snapshot_id>/` directory. It writes one complete manifest only after all consistency gates pass. A failed invocation preserves partial private files without marking them complete; it never deletes data automatically. Each invocation uses a fresh identifier.

| File | Contents |
| --- | --- |
| `database.dump` | Custom-format logical dump of the complete `adf` database, including all application schemas and data; ownership and ACL restoration are excluded. |
| `inventory.json` | Project paths, run states/revisions/event sequences/control flags, execution states/epochs and artifact identity/storage-key/size/SHA-256 metadata. |
| `artifacts/<artifact_id>.bin` | Every registered artifact downloaded through the API, verified against its ledger size and SHA-256. |
| `git/<project_id>.bundle` | Self-contained Git objects for all refs and `HEAD`, checked against the source ref inventory. |
| `manifest.json`, `manifest.sha256` | Versioned completeness record, pinned PostgreSQL image, correlation inventory, exact filenames, byte counts and SHA-256 checksums. |

PostgreSQL documents that `pg_dump` obtains a consistent logical backup of one database; the custom archive supports controlled restoration. That guarantee does not synchronize external artifact/Git files. The script uses the already running PostgreSQL 18 container's `pg_dump`, Unix-socket authentication and `--no-password`, with a ten-second lock wait and a bounded timeout. It copies no database-role password or host environment file. [PostgreSQL 18 pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html).

Git bundles preserve referenced Git history, not the working tree, repository configuration or hooks. No global Git security setting is changed, hooks/fsmonitor are disabled for these administration commands and only the local file protocol is enabled. Each bundle includes all common refs plus the registered repository's `HEAD`, using `--single-worktree` to avoid exporting linked-worktree pseudo refs. Every linked worktree must be clean and its HEAD reachable from those saved refs; a detached-only commit blocks snapshot until the operator preserves it with a named ref. Prerequisite/incremental bundles are refused. [Git revision worktree options](https://git-scm.com/docs/git-rev-list). [Git bundle documentation](https://git-scm.com/docs/git-bundle).

Excluded from this snapshot: provider/OAuth credentials, `.env` files, database roles/passwords, Redis transport state, Langfuse data, worker journals, untracked/ignored worktree bytes and repository hooks/configuration. Database records, artifact bytes and Git history can still contain sensitive project material. This is a private local backup, not a sanitization or upload feature. Never commit or upload its directory. Langfuse requires a separate coordinated backup plan for its own PostgreSQL/ClickHouse/object storage; see [observability](observability.md).

Private destinations refuse symlinks, Windows junctions, hardlinks and path traversal. New POSIX directories/files use `0700`/`0600`. On Windows they inherit the umbrella user's NTFS ACL; the script does not alter ACLs or global settings. Keep `.bootstrap` in a user-private local directory and inspect its inherited access before using it as backup storage. The script refuses shared paths outside `.bootstrap` but does not certify Windows ACL privacy. SHA-256 detects corruption against a trusted manifest; it does not authenticate a manifest that an attacker can rewrite together with its checksum.

Limits are deliberate: at most 10,000 paginated projects/runs, 16 MiB per JSON response, 20 MiB per artifact, 1 GiB per dump/bundle, and 5 GiB total recorded payload. HTTP requests time out after 15 seconds; administration subprocesses after at most 300 seconds, with individual WSL Git commands limited to 90 seconds. Provider/OAuth/database secret environment variables are removed from helper environments. No arbitrary shell command, restore path, remote Docker endpoint or external upload is accepted.

## Verify and rehearse in isolation

Use the identifier printed by `--snapshot`; the CLI accepts a generated identifier, never an arbitrary filesystem path:

```powershell
$SnapshotId = 'REPLACE_WITH_REPORTED_SNAPSHOT_ID'
python scripts/snapshot-runtime.py --verify $SnapshotId
python scripts/snapshot-runtime.py --rehearse $SnapshotId --allow-isolated-restore
```

`--verify` is local and read-only. It checks completeness, checksums, size bounds, archive/bundle headers, exact file coverage, source refs and referential artifact/run/execution/project metadata. It does not prove that a database archive or Git pack can actually be restored. Unit fixture archives deliberately do not claim that proof.

The explicit rehearsal flag creates only new named QA resources:

- Docker container `adf-snapshot-qa-<snapshot_id in lowercase>` with the manifest's exact PostgreSQL 18 digest, 512 MiB memory and one CPU. It has `--network none`, no published ports, no source volume mount and a fresh image-managed volume. Its fixed user/database are `adf_restore`; trust authentication applies solely inside this disconnected QA container. No credential/OAuth environment is forwarded.
- Registered Git bundles cloned as new bare mirrors beneath the regular WSL user's `~/ai-factory/snapshot-rehearsals/<snapshot_id>/<project_id>.git` on ext4. Source refs/worktrees remain untouched. All ref hashes and the recorded `HEAD` commit object are checked.
- Artifact bytes copied only to the new private `rehearsal-artifacts/<storage_key>` directory, verified against the restored database's size/SHA-256 metadata.

PostgreSQL readiness is checked over its internal loopback TCP listener to avoid accepting the initialization-only socket server. `pg_restore` then reads the private archive via stdin with `--no-password --no-owner --no-privileges --exit-on-error --single-transaction`. It uses no `--clean`, no database drop and no source database connection. PostgreSQL warns that restoring an untrusted dump can execute SQL selected by its source; use only a trusted local snapshot and preserve this disconnected QA boundary. [PostgreSQL 18 pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html).

A successful `rehearsal-report.json` is written only after real database restoration, referential inventory equality, artifact-byte checks and Git restoration all pass. The report states `isolated_restore_verified=true` and `runtime_recovery_verified=false`. Rehearsal is a restore proof for these backup components; it does not launch the restored ADF control plane or prove worker-journal/Redis replay and resumed execution. Keep the report as private acceptance evidence.

QA resources and failed partial restores are preserved. The script never stops containers or deletes volumes/files. Existing rehearsal names/directories cause failure rather than reuse. Repeating a successful rehearsal for the same snapshot requires a separately reviewed cleanup or a new snapshot identifier; this script provides no cleanup command.

## Acceptance and eventual recovery

The operator runs the commands above after obtaining a quiet runtime and records the real report before claiming restore acceptance. Automated coverage in [test_snapshot_runtime.py](../tests/test_snapshot_runtime.py) verifies drain/state gates, actual subprocess output bounds and secret-free failure handling, redirect refusal, provider-secret environment stripping, path/link refusal, artifact corruption and concurrent-inventory failures. These checks are distinct from a live restore rehearsal.

For disaster recovery, provision a fresh installation and generate new local authentication/database roles. Restore the database, artifact layout and Git refs into that fresh installation under a separate reviewed recovery procedure. Validate schema compatibility and migrations against the recorded image/revision before enabling schedulers or workers. Reconstruct Redis delivery from the durable outbox, reconcile every worker journal/execution ownership record, verify artifact paths and target roots, and run provider doctor without exposing OAuth material. Resume paused work only after those runtime recovery gates pass. An overwrite-in-place command for the live `adf` database is intentionally not provided by this workflow.

Recovery point is the completed quiescent snapshot. No numerical RPO/RTO or unattended retention schedule has been established. This workflow does not delete old snapshots, encrypt/export backups, back up Langfuse or prove complete runtime disaster recovery; those require explicit policy and additional acceptance.
