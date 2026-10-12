# One ADF Compose project: source plan and migration gates

Subsequent runtime update: the separately approved [Redis repair](redis-repair-runtime-checkpoint.md) completed with exact PEL=3 and unchanged AOF/data. The historical PEL=0 observations below remain dated evidence. The metadata/package diagnostic and Langfuse migration were not executed by that repair; host consumer/provider remain stopped.

October 12, 2026. **Canonical source entrypoint prepared; live regrouping not applied.** The requested Docker Desktop group is the Compose project `adf`. Existing production containers are still split between `adf` and `adf-langfuse`; their current names, images, environments, bindings and data have not been changed by this task. Redis preservation passed in the separately approved repair; no Langfuse migration backup or container recreation has been performed.

## Managed scope

| Project before migration | Services in canonical project `adf` | Existing containers |
| --- | --- | --- |
| `adf` | postgres, redis, migrator, api, orchestrator, frontend, otel-collector | `adf-<service>-1` (seven; migrator remains exited successfully) |
| `adf-langfuse` | langfuse-web, langfuse-worker | `adf-langfuse-langfuse-web-1`, `adf-langfuse-langfuse-worker-1` |
| `adf-langfuse` | langfuse-postgres, langfuse-redis, langfuse-clickhouse, langfuse-minio | `adf-langfuse-postgres-1`, `adf-langfuse-redis-1`, `adf-langfuse-clickhouse-1`, `adf-langfuse-minio-1` |

These are 13 own production containers, including all Langfuse dependencies and OTel. The WSL worker remains a host process, outside Compose. Other containers are not adopted. No extra application/service repository is introduced, and SPEC is preserved.

[Docker project-name precedence](https://docs.docker.com/compose/how-tos/project-name/) makes explicit `--project-name adf` authoritative. Compose assigns its own [project/service labels](https://docs.docker.com/reference/compose-file/services/#labels); reserved Compose labels must not be fabricated in YAML. Changing only container names does not change project membership. Existing six Langfuse containers require controlled recreation through Compose for new labels. No core container needs recreation for project membership: all seven already belong to `adf`.

## Persistent source entrypoint

Run from the umbrella root, with the existing checksum-verified official Langfuse source prepared. Local rendering was checked with Docker Compose **5.5.1**; other versions must pass the same config/contract checks before use.

```powershell
python scripts/compose-adf.py status
python scripts/compose-adf.py prepare
python scripts/compose-adf.py plan
```

All status/prepare/plan/start operations must use the previously verified **local Docker Desktop** endpoint/context. A new or remote Docker context is outside this approved scope; verify the endpoint and exact target inventory again before any separately approved application. The entrypoint does not change contexts or global Docker settings.

`prepare` verifies [Langfuse source lock](../infra/langfuse-source.lock.json) and renders its official Compose plus [local overlay](../infra/compose.langfuse.yaml) with a new empty env file and `--no-interpolate --no-env-resolution`. It remaps the six service IDs and dependencies, retains symbolic env/command references, and writes ignored `.bootstrap/compose.adf-observability.json`. It does not load/copy private environment values or start containers. `plan` adds a read-only inventory. The generated model is reproducible from committed code and the locked public source; it is not a private resolved-config archive.

The canonical model joins [core Compose](../infra/compose.yaml) and the generated overlay, always with `--project-name adf`. It keeps existing six Langfuse container names and gives internal dependencies unique service IDs. Existing `postgres`, `redis`, `minio` and `clickhouse` DNS aliases remain on the separate Langfuse network, so public upstream URLs do not need secret-bearing replacement. Core PostgreSQL/Redis remain on `adf_default`; the databases/caches are separate.

The five existing Langfuse volumes are external by exact name:

```text
adf-langfuse_langfuse_postgres_data
adf-langfuse_langfuse_redis_data
adf-langfuse_langfuse_clickhouse_data
adf-langfuse_langfuse_clickhouse_logs
adf-langfuse_langfuse_minio_data
```

The network `adf-langfuse_default` is reused as external `langfuse-existing`; `adf-telemetry` remains external and retains web alias `adf-langfuse`. Docker's [external-volume semantics](https://docs.docker.com/reference/compose-file/volumes/#external) preserve existing stores instead of creating project-renamed empty volumes, and [named external networks](https://docs.docker.com/reference/compose-file/networks/#name) preserve cross-stack routing. Read-only membership checks found only the six Langfuse containers on their network/volumes and only Langfuse web plus ADF Collector on telemetry.

`start` is a guarded **post-migration resume command**, not the migration executor:

```powershell
python scripts/compose-adf.py start
```

It refuses missing targets, wrong project/service labels, additional `adf` members, a stopped Redis or failed Redis AOF-load durability checks. When all gates pass, it uses existing images, no build/pull/recreation, no dependencies and an explicit service list that excludes the already completed migrator. It must not rerun database migrations. A failed Compose apply reports possible partial changes; it does not claim an attempted operation made no changes. Current `start` is deliberately blocked.

## Current blockers and concrete migration scope

The [Redis diagnosis](redis-aof-preservation-diagnosis.md) proves an AOF/ACL transaction replay problem; grouping does not require touching core Redis and must not become a Redis recovery workaround. The separately approved Redis repair has passed its preservation gate. No production Langfuse backup destination or backup procedure has been agreed for this migration.

A read-only inventory also found **33 old recovery QA container members** carrying Compose project `adf`, outside the 13 production targets. A retained QA API image itself contains baked `adf` project/API service labels, explaining at least that fixture's inherited membership. Do not assume all history is disposable, sweep these containers, edit their labels or run `--remove-orphans`. Keep them untouched until an operator decides whether to retain/archive/recreate their test history under distinct QA projects. Their mistaken labels currently prevent an exclusive production group and block the guarded start. Future QA images must not inherit production Compose labels; address that separately with fixture contract tests.

Before any live regrouping, present the operator with:

1. The exact 13 target inventory, including image IDs, environment hashes, ports, mounts, network aliases and migrator exit status. Compare a privately rendered canonical config to existing settings without printing secrets; stop on any difference outside project/service labels. Image aliases for built core services need explicit current-image binding before any fresh creation; `--no-build` alone is not an image-identity guarantee.
2. An agreed consistent backup/restore plan for all affected Langfuse stores (PostgreSQL, Redis, ClickHouse data/logs and MinIO), plus current Compose/private config. Preserve ongoing data by coordinated quiescence; test restoration in isolation. Select a private location and access/retention before capture; do not commit backups or secret-bearing config.
3. A bounded maintenance plan recreating **only the six named Langfuse containers**, through canonical Compose under `adf`, with the exact retained immutable images, env values, loopback publications, external stores and network aliases. Keep all seven core containers, host worker and unrelated containers untouched; use explicit targets and no orphan/volume cleanup.
4. Post-checks for project/service labels, image/env hashes, bindings, external volume identities and health, plus a separately authorized trace-ingestion validation. Recheck API's three uncertain executions, stopped host workers and Redis preservation throughout. New labels alone do not prove data preservation or MVP acceptance.
5. A tested rollback retaining original Langfuse Compose/private settings and backups. Return only those six containers to the former project/settings if the approved migration fails; never reset stores or delete volumes. A data-writing period after migration requires a new consistent backup before restoring older data.

No automated migration command bypasses these gates. Once source review and tests pass, the source can be published independently of live application. [Sanitized inventory](evidence/compose-grouping-source-2026-10-12.json) includes only settings hashes and infrastructure metadata; no private values. Current production grouping and readiness are unchanged.
