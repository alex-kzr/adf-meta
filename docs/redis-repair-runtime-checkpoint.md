# Authorized Redis preservation repair: runtime checkpoint

October 12, 2026. **Human approval at 09:07 UTC; Redis repair completed.** The user explicitly limited this step to Redis. Langfuse grouping and all QA resources remain unchanged. [Sanitized evidence](evidence/redis-repair-runtime-2026-10-12.json) records backup, isolation, cold load and post-resume checks. The [prior diagnosis](redis-aof-preservation-diagnosis.md) remains the explanation of the earlier PEL loss.

## Private backup and tested rollback

Before stopping Redis or editing ACL, global API metrics showed zero active executions, zero newly queued executions and exactly three uncertain executions in one running run. Dedicated provider/consumer/native and old supervisors were stopped; locks, journals/results, selected skills, clean main and all 29 installed f5 source files were preserved. The exact existing orchestrator writer was stopped for the maintenance window.

A root-owned WSL ext4 backup was created at `/root/adf-redis-repair-backups/20261012T094116Z-69814180`, with 0700 directories and 0600 single-link files. It contains original incremental AOF, base RDB, manifest, the current dump RDB, original ACL and Redis container configuration. Files, manifests and directory entries were fsynced; hashes and private modes were reverified before production modification. Manifest SHA-256 is `0771e539fb45ada280503bde33f3ad5a7856e3a660e50d3930ea22d1895026ca`. No provider authorizations or plaintext service/admin passwords are included. No backup/data was committed or uploaded, and no automatic retention/deletion was scheduled.

Exact pinned public Redis 7.4.5 binaries restored the real backup in private user/mount/PID/network/IPC namespaces with no host network/IPC or provider-profile mounts. Only existing worker/monitor read permissions were used. All three cases retained the same 70 stream entries and exact AOF/base/manifest bytes: original ACL reproduced PEL=0 with 153 denied EXEC commands; the narrow repair restored the exact PEL=3 with zero denials; rollback to the original ACL reproduced its original PEL=0/153-denial behavior. Default AUTH was rejected in every case. The rollback is a proved configuration/backup restoration path; returning to the historical broken ACL would reintroduce its PEL problem. It was not needed in production.

## Exact production change

Only the first ACL row changed:

```text
user default off resetpass ~adf:executions +select +xclaim +xgroup|setid
```

The user remains disabled and has no password. Scheduler, worker and monitor rows remained byte-for-byte identical. ACL write intent and same-file identity were recorded before the in-place update; partial-write rollback checks reject unrelated external drift. No active-role expansion, broad wildcard grant or new listener was introduced.

The existing `adf-redis-1` was stopped, its persisted AOF bytes rechecked, and the same container cold-started. Container ID remains `b8bbc58f0cb4dfe0fc1066e757ece69c73562c3234cace19ffa86ff75d9612a9`; image remains `sha256:f218e591b571a4129aa29a8566b597d849fba21af7be853d31b03122b20db5e9`; volume remains `adf_redis-data`; host publication remains `127.0.0.1:6380`. Config, mounts and network identities were unchanged. No recreation, image build/pull, AOF rewrite/truncation or manually injected transport entries were used.

Cold-load logs positively confirm AOF loading and readiness with no ACL/load/truncation failure. Mounted ACL matched the candidate exactly, role rows matched their original bytes, and default AUTH failed. Incremental AOF SHA-256 remained `d5b9927a259e6d9d218bd852696505fa070e2daa4fc794a731b98fd63dfe6961`; base and manifest hashes also matched backup. All 70 entries retained content SHA-256 `aa68cf51d7e76b30837b1d9ed5cff5eee18117bd6d90a2e6861b3334b26e0f89`.

The exact old pending IDs are restored: `1791774765065-0`, `1791774765075-0`, `1791774765082-0`. This is **Redis persistence loading**, not agent-job replay or ownership/result reconciliation. No operator ACK/claim, API state mutation, lease renewal, native thread/turn/model call or paid API fallback occurred.

## Post-resume state and source prevention

Full gates were rerun immediately before resuming the same orchestrator image/identity/settings. After resume, Redis again had PEL=3 with those exact IDs, identical stream/AOF data and rejected default AUTH. API run `67727194-095a-4e9e-afde-6af74ca84247` remains running with three uncertain executions. The installed worker remains `f5a713a3df44ffdad58aaa80fc3a36157e6c2736`; provider/consumer/native remain stopped; the separate authenticated metadata allowance is unused. The earlier native RPC cause remains unknown, and readiness remains false.

PostgreSQL, Redis, API, orchestrator, frontend and all six Langfuse containers are healthy; OTel is running and the existing migrator remains exited=0. All 69 containers outside Redis/orchestrator retained ID, image, status and StartedAt. No QA container, Windows/account/group/firewall/global Git setting or Langfuse grouping was changed.

The [fresh bootstrap template](../scripts/init-local-env.py) now generates this same disabled, narrowly granted default row; existing private ACL files remain preserved by initialization. Its security contract test is updated, with scheduler/worker/monitor generation unchanged. The initializer was not rerun against the deployed runtime. Actual-binary cold-load/default-auth regression remains in CI. This prevents fresh environments from regenerating the diagnosed permissionless row without introducing another runtime operation.

The [one-project Compose plan](compose-grouping.md) still requires its own consistent Langfuse backup and maintenance gates; 33 historical QA labels remain untouched. This completed Redis step does not apply that migration or start the separately approved metadata/package diagnostic.
