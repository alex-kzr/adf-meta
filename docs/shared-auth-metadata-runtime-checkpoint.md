# Approved local-profile metadata diagnostic: queue preservation mismatch

October 12, 2026. **Metadata scope authorized at 06:44 UTC; existing-service restoration separately authorized at 06:56 UTC. Installation and native test remain unstarted.** The [approved diagnostic scope](shared-auth-metadata-scope.md) required preserving three uncertain deliveries with Redis PEL=3. After the authorized Docker Desktop restart, existing services are available but PEL is **0**, so preflight stops. [Sanitized evidence](evidence/shared-auth-metadata-runtime-2026-10-12.json) retains the initial unavailable-service checkpoint and this later observation.

## Service restoration

The installed Docker Desktop 4.94.0.241994 executable was started once, hidden, at 06:59:21 UTC. Existing ADF PostgreSQL, Redis, API, orchestrator and frontend containers auto-started and are healthy; OTel is running. Six existing Langfuse containers also auto-started under their existing restart policy and are healthy. No container was recreated, image rebuilt, configuration changed, new permission/security prompt accepted or new terms accepted by operator actions. Dedicated WSL consumer/provider/native/supervisors remain stopped; none auto-started.

The Redis container retains its existing `adf_redis-data` volume and image `sha256:f218e591b571a4129aa29a8566b597d849fba21af7be853d31b03122b20db5e9`. Orchestrator image remains `sha256:e661b27513d510ae5c956598eb49df2fbe76c1f22fbbe8f20154218328df2753`. This proves retained image/volume identities, not successful preservation of Redis runtime state.

## Queue discrepancy and diagnostic boundary

GET-only API checks still report run `67727194-095a-4e9e-afde-6af74ca84247` as `running` with exactly three `uncertain` executions. Two read-only XPENDING observations after restart report **0 pending deliveries and no pending consumers**, compared with the prior verified **3**. Old local journals still have no ACK flag, results persisted and no terminal persistence. These facts do not prove that the old deliveries were safely ACKed or reconciled.

Redis's 06:59:33 startup log repeatedly reports `NOPERM` for its AOF-loading client when processing `EXEC`, then reports ready. The pinned [Redis 7.4.5 transaction implementation](https://github.com/redis/redis/blob/7.4.5/src/multi.c) checks ACL permissions before executing queued commands, including the AOF-client execution path. The initial checkpoint treated this as an inference. A subsequently authorized [read-only diagnosis and synthetic exact-binary regression](redis-aof-preservation-diagnosis.md) now proves denied transactional AOF replay as the PEL-loss mechanism. The later audit streams raw RESP only through a bounded parser that discards bodies/credential/consumer values; no raw payload is emitted or copied into evidence and no privileged workaround is attempted. The original native RPC cause remains unknown. The existing worker ACL denied optional XLEN/XINFO metadata reads; those denials were respected without another identity or permission change.

Safe local category is `queue_preservation_mismatch`. RPC outcome and numeric provider error code are **null**: no app-server or metadata thread was started. This is separate from the discarded historical Codex RPC failure.

## Preserved worker and unused native allowance

Installed worker remains **`f5a713a3df44ffdad58aaa80fc3a36157e6c2736`**; all 29 Python source files match its retained immutable inventory. Approved source `0dd5ac7b8be6f792921f29bc376e520f3c0754c6` was not installed. The new rollback rehearsal and operator harness were not started. The single 120-second native metadata allowance is unused: zero owners, thread/start, turn/start or model calls.

Read-only local checks prove stopped dedicated provider/consumer/native and all old supervisor/child sessions, reacquirable allocation locks, unchanged clean synthetic main, unchanged trust/config hashes and profile ownership/mode. Three old uncertain journals/worktrees and their selected skills are retained. No auth/manifest/package mutation, API write, ACK, replay, terminal rewrite, cancellation, lease renewal, ACL change, data repair or AOF manipulation was issued by this task. Existing orchestrator settings/image were retained; its already authorized container restart is distinct from a source/config update.

## Required next decision

Stop at this preservation gate. Investigating/restoring Redis transaction replay and the missing pending deliveries requires a separate concrete scope, including data protection and a review of any ACL/service changes. Do not manufacture PEL entries, broaden permissions, change AOF files or relaunch old native jobs to make the count pass. The operator may separately decide the queue discrepancy is sufficiently explained/fenced to proceed with the metadata scope, but that decision has not been made here. Consumer stays stopped; readiness remains false.

The initial blocked checkpoint was committed as `29caa6ea0e3b44bfebfefc35b9e74bf8ec1b5b17`; its [exact-commit CI](https://github.com/alex-kzr/adf-meta/actions/runs/38214820098) passed contract/static tests and offline bootstrap. This current checkpoint records the subsequently authorized restoration and new blocker.
