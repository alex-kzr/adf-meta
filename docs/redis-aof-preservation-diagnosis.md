# Redis AOF preservation diagnosis and proposed recovery scope

October 12, 2026. **Read-only production diagnosis; synthetic regression only. No production repair or restart is authorized by this document.** The installed worker remains `f5a713a3df44ffdad58aaa80fc3a36157e6c2736`, provider/consumer remain stopped, and the approved authenticated metadata window is unused. Readiness is false.

## Proven mechanism

Before the separately authorized Docker Desktop restoration, Redis PEL contained three deliveries for run `67727194-095a-4e9e-afde-6af74ca84247`. After the existing container started at 06:59:32 UTC, XPENDING returned zero. GET-only API checks still report the run as running and all three executions as uncertain. These are independent transport and database observations; zero PEL is not evidence of completion.

The retained incremental AOF is 50,953 bytes, inode 62123, last modified at Unix time 1791775084 (03:18:04 UTC). A bounded streaming [audit](../scripts/redis-aof-audit.py) reads only RESP framing and allowlisted command/header metadata; message bodies, unknown commands, credentials and consumer values are discarded. Raw AOF is neither printed nor copied to evidence. All 67 MULTI transactions have matching EXEC. There are 92 XCLAIM, 60 XGROUP SETID and one SELECT inside those transactions: **153 commands**. Redis's actual startup has exactly **153 AOF-loading-client NOPERM errors**. The default ACL row has only the disabled `off` flag, with no command/key grants; credential rows were not emitted.

| Previous execution | Persisted delivery ID | XADD | Transactional claims | XACK | XDEL |
| --- | --- | --- | --- | --- | --- |
| `f0d9cf44-eaae-5dba-bbb7-5fefccc44410` | `1791774765075-0` | 1 | 8 | 0 | 0 |
| `b17996ac-323a-5485-8cfc-25704aa98653` | `1791774765065-0` | 1 | 8 | 0 | 0 |
| `09f04ce2-9b40-5469-9f54-8ccfd050d63e` | `1791774765082-0` | 1 | 8 | 0 | 0 |

The [exact Redis 7.4.5 AOF loader](https://github.com/redis/redis/blob/7.4.5/src/aof.c) constructs an AOF client and loads persisted commands. Its [EXEC implementation](https://github.com/redis/redis/blob/7.4.5/src/multi.c) checks ACL permissions for queued commands before executing each one; the AOF execution branch does not bypass that check. The combination of actual retained claims, no target ACK/deletion, the exact denial count and the independent reproduction establishes **denied transaction replay under the disabled, permissionless default user** as the PEL-loss mechanism. This does not explain the earlier Codex native RPC startup failure; that upstream cause remains unknown.

## Independent synthetic reproduction

The [regression script](../scripts/redis-aof-regression.py) runs the exact verified public Redis executable and its three public musl/OpenSSL libraries from the installed official Redis image `redis@sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08`. All four SHA-256 hashes and the standalone Codex 0.157.0 namespace launcher hash are checked before execution. No actual AOF, database, ACL credential, provider profile or configuration is mounted in the fixture.

The process runs as the regular worker UID in new user/PID/mount/network/IPC namespaces, with an empty environment, dropped capabilities and private tmpfs. Redis listens only on a fixture Unix socket inside that namespace; no host listener is added. No Codex or Claude session/thread/turn/model call is made.

Three synthetic XADD messages and a consumer group are followed by one transaction containing SELECT, XCLAIM and XGROUP SETID. With `user default off`, stream length remains three but PEL is zero and EXEC logs three NOPERM errors. With the proposed narrow disabled default row below, PEL is three, the expected last-delivered ID and one consumer are restored, and no AOF NOPERM occurs. Default-user authentication remains denied in both cases. Explicit safety checks remain active under Python `-O`.

Actual optional XINFO/XLEN requests were denied by the existing worker ACL. They were not retried through broader privileges. The fixture cursor/entries-read/consumer observations are **synthetic evidence**; the real group cursor was not directly observed. A damaged or stale cursor is therefore an inference, not an additional live measurement. No runtime claim, ACK, replay, cleanup or reconciliation is permitted by this diagnosis.

## Concrete proposed repair: new approval required

Candidate first ACL row, verified only against fake data:

```text
user default off resetpass ~adf:executions +select +xclaim +xgroup|setid
```

This grants only the persistence-loader command/key surface demonstrated by the retained AOF. The user remains disabled and has no password; interactive AUTH must still fail. Scheduler, worker and monitor credential rows and their permissions must remain byte-for-byte unchanged. No `+@all`, active worker permission expansion, new listener, global Git setting or account/group change is proposed. This is a security configuration change and is **not installed**.

A separately approved recovery would:

1. Confirm stopped host provider/consumer/native and unchanged three uncertain API executions. Quiesce only specifically approved Redis writers for a bounded maintenance window; preserve all journals/results/worktrees.
2. Agree a private backup destination and retention/access policy, then capture a consistent `adf_redis-data` backup with the original incremental AOF, base RDB and manifest, file hashes and same-image restore instructions. Rehearse restoration into an isolated namespace before changing production. Do not overwrite the original archive with the post-failure `dump.rdb`: its later timestamp does not establish the previous PEL state. Backup payloads and ACL credentials must never enter Git or agent output.
3. Change only the first disabled default ACL row, preserving all role rows. Coordinate Docker Desktop secret bind handling; do not assume editing a mounted file updates an existing container handle. Approve a Redis-only reload/recreation with its exact current image, existing volume, bindings and settings; stop if a broader change is required.
4. Allow **Redis persistence loading only** as part of that cold start. This is distinct from replaying an agent job, and must be explicitly included in approval. Require no AOF load/ACL/truncation error and verify the three exact old delivery IDs in PEL, stream/group consistency, and unchanged API uncertainty before considering the preservation gate satisfied.
5. Keep consumer/provider stopped. If validation fails, stop the maintenance flow and preserve both baseline and failed-start evidence. Execute only the specifically rehearsed/approved rollback; do not manufacture pending entries or use XCLAIM/XACK, rewrite AOF or relaunch native jobs to force success.

No backup was taken or data changed by this source-only task. Restoring PEL alone cannot reconcile external effects or authorize old native execution. The separately approved metadata diagnostic can resume only after its own preservation gates and any further operator decision are satisfied.

## Evidence and checks

[Sanitized Redis diagnosis](evidence/redis-aof-diagnosis-2026-10-12.json) records the framing counts, original file metadata and exact synthetic outcomes. [Prior runtime checkpoint](shared-auth-metadata-runtime-checkpoint.md) records the authorized Desktop restoration and retained installed runtime. [Compose grouping plan](compose-grouping.md) is also blocked until preservation and backup gates are resolved. Source unit tests use fake RESP and fake Docker results; production operations remain read-only.
