# Local development and operations

## Source and execution locations

The umbrella source is `C:\Users\admin\Documents\workspace\projects\adf`. Factory target repositories, worktrees, journals and the host-worker environment belong on Ubuntu WSL2 ext4, for example `/home/alex/ai-factory`. Windows `/mnt/c` source can be read to install the host package; it must never become an execution worktree. Do not run Windows provider sessions against the same target worktree.

Verified local tools: Python 3.12.9, WSL Node 24.21.0, uv 0.12.18, Codex CLI 0.157.0 and Claude Code 2.1.296. Adapter pins are separate from the Windows CLI versions. Python packages and frontend dependencies are pinned in each module's lock; core image digests are in [images.lock.env](../infra/images.lock.env). Passing the image lock as the **second** env file overrides an older preserved local image selection. Install provider CLIs only from official sources and authenticate interactively in the worker account; do not copy OAuth stores or substitute API payment credentials.

The current `alex` account has `sudo`/`docker` group access and can access the Docker socket. It is suitable for a bounded trusted-workstation test, but a dedicated least-privilege runtime account is **not verified**. This task does not change account groups, Docker integration, firewall or security settings. Complete that operator gate before treating real execution as accepted.

## Core startup

```powershell
python scripts/init-local-env.py
docker compose --env-file .env --env-file infra/images.lock.env -f infra/compose.yaml config --quiet
docker compose --env-file .env --env-file infra/images.lock.env -f infra/compose.yaml up -d --build --wait --wait-timeout 120
curl.exe --noproxy "*" --fail --max-time 5 http://127.0.0.1:8080/readyz
```

`init-local-env.py` creates private ignored random infrastructure secrets, three distinct bearer tokens and hashed Redis ACL credentials. It preserves existing values and the operator's `.env`; it appends only missing configuration keys. It never creates provider credentials. Generated text is LF-terminated, including on Windows. Do not rewrite a mounted secret while its container is running: Docker Desktop file sharing can retain stale file handles. Explicit rotation requires coordinated recreation; rerunning initialization does not rotate secrets.

Fresh PostgreSQL initialization creates a bootstrap owner, migrator, API role and checkpoint role. Alembic runs as the migrator before API startup. API has CRUD rights in `control`, `runtime` and `audit`; orchestrator owns only checkpoint table creation in `checkpoints`. API does not have schema DDL rights; PUBLIC database/schema access is revoked. `pg_isready` establishes server liveness, while API/orchestrator `/readyz` establishes authenticated dependency health. Runtime acceptance remains a separate false flag.

The worker runs outside Compose. PostgreSQL 55432, Redis 6380, API 8080 and frontend 8088 are published to loopback; orchestrator 8081 has no host port. Redis identities differ: scheduler publishes, worker consumes/acknowledges, monitor reads health. New ACL command requirements must be reviewed and tested; broad `+@all` is forbidden. Redis is transport; the API's database ledger is the ownership/result authority.

Open `http://127.0.0.1:8088` and enter the **ADF admin token**, read privately from `.bootstrap/secrets/admin-token`. UI keeps it only in memory. Codex/Claude credentials are never entered into ADF. A project registration identifies an ext4 repository beneath an API-configured root, its default branch and trusted check argv. API prefix validation is followed by worker canonical-path, symlink, clean-repo and branch validation.

## WSL worker preparation and diagnostics

Prerequisites must already be installed in the regular WSL account. Preparation installs only the locked worker Python package and copies the generated ADF worker/Redis credentials to private files; provider authentication remains interactive. Existing credentials are preserved and mismatches fail closed.

```bash
cd /mnt/c/Users/admin/Documents/workspace/projects/adf
bash scripts/bootstrap-wsl.sh \
  --root /home/alex/ai-factory \
  --token-file .bootstrap/secrets/worker-token \
  --redis-password-file .bootstrap/secrets/redis-worker-password \
  --node /absolute/path/to/pinned/node \
  --codex /home/alex/.local/bin/codex \
  --claude /home/alex/ai-factory/tools/node_modules/.bin/claude \
  --codex-home /home/alex/ai-factory/provider-profiles/codex \
  --claude-config-dir /home/alex/ai-factory/provider-profiles/claude

bash scripts/doctor.sh \
  --root /home/alex/ai-factory \
  --node /absolute/path/to/pinned/node \
  --codex /home/alex/.local/bin/codex \
  --claude /home/alex/ai-factory/tools/node_modules/.bin/claude \
  --codex-home /home/alex/ai-factory/provider-profiles/codex \
  --claude-config-dir /home/alex/ai-factory/provider-profiles/claude \
  --redis-password-file /home/alex/ai-factory/config/redis-worker-password
```

Doctor reports actual CLI versions/auth status for explicitly selected existing private profiles, ext4 filesystem, current groups/socket access, authenticated Redis health, API readiness and Docker host bindings. Provision/authenticate those profiles personally before diagnosing them. The source repair forwards `--codex-home`, `--claude-config-dir` and `--node` through both wrappers. Omitted profiles report `PROFILE_REQUIRED` without invoking their CLIs; shell selectors are not implicitly adopted. It neither installs nor authenticates software nor starts jobs. See [diagnostic profile behavior](../services/runtime-worker/docs/doctor-profiles.md). The dedicated installed worker remains `a8bb1cc`; use its current shared preflight until an updated installation is separately authorized. `runtime_healthy` is operational health; `mvp_ready` remains false until the umbrella gates pass. A missing provider does not become a mock-provider success. External-host denial and dedicated-account privilege remain explicit unknown gates.

After reviewing doctor and registering project/configuration/policy versions, start the implemented consumer:

```bash
/home/alex/ai-factory/tools/worker-venv/bin/adf-worker serve \
  --root /home/alex/ai-factory \
  --api-url http://127.0.0.1:8080 \
  --token-file /home/alex/ai-factory/config/worker-token \
  --redis-url redis://adf_worker@127.0.0.1:6380/0 \
  --redis-password-file /home/alex/ai-factory/config/redis-worker-password \
  --max-parallel 3 \
  --codex /home/alex/.local/bin/codex \
  --claude /home/alex/ai-factory/tools/node_modules/.bin/claude
```

The project root defaults to `root/projects`; repeatable `--project-root` selects registered roots without exposing journals/tools as project scope. Worker supervision owns process groups and worktree locks independently of Redis consumer lifetime. Restart does not prove old-process death or authorize repeating uncertain effects. Follow [recovery](reliability.md) and inspect persistent execution/journal/Git evidence.

Codex enforces its coarse read-only/workspace-write sandbox for built-in tools. The reviewed worker source additionally supports exact assigned `mcp__<server>__<tool>` mappings through the owned `adf.scoped-files.v1` server, with exact read paths, byte/time limits and independent server denials. Generic MCP argv/scope contracts and unsupported built-in mappings fail with `CAPABILITY_UNSUPPORTED`; they are never silently expanded. Source contract tests, native trials and the currently installed runtime are distinguished in [acceptance status](acceptance-status.md). Claude uses safe/restricted modes, explicit builtin tools and strict MCP configuration. Subscription cost is unknown unless actual billing evidence exists; CLI token counters are source-tagged.

## Official Langfuse and Collector

```powershell
python scripts/prepare-langfuse.py --validate --check-resources --pull
docker network create --label com.adf.purpose=telemetry adf-telemetry
docker compose -p adf-langfuse --env-file .bootstrap/langfuse/.env -f infra/vendor/langfuse/docker-compose.yml -f infra/compose.langfuse.yaml --profile observability up -d --wait --wait-timeout 240
docker compose --env-file .env --env-file infra/images.lock.env -f infra/compose.yaml --profile observability up -d --no-deps otel-collector
python scripts/check-telemetry.py
```

Create `adf-telemetry` only if it does not exist; use `docker network inspect adf-telemetry` to check. Preparation downloads checksum-verified official Compose, resolves only locked images and generates private ignored deployment/project/operator credentials. It does not start services. Preserve all volumes. Read [observability](observability.md) for effective Community retention, exporter privacy and exact trace validation. Upstream web/worker `HOSTNAME=0.0.0.0` is an internal listener setting; published host ports remain loopback.

Langfuse UI is `http://localhost:3000`; the private generated operator login is in `.bootstrap/langfuse/operator-login.txt`. Collector OTLP 4317/4318 and health 13133 are loopback. Instrumentation is opt-in with `ADF_TELEMETRY_ENABLED=true`; use a temporary Compose override for an acceptance run if the preserved `.env` disables it. The host worker additionally uses `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces`. Backend failure must not prevent execution; validate an actual active run with `check-telemetry.py --outage-run`, not only service health.

## Development and release checks

Use independent virtual environments for the API/orchestrator/worker, installing each exact requirements lock. Worker tests execute on Linux ext4; see each module README. Umbrella checks:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/verify.py
python -m unittest discover -s tests -v
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
```

Inspect every nested status, commit children before updating gitlinks, and run fresh bundle/recursive-clone restoration after committing. Keep secrets, runtime state, bundles and IDE files ignored. The user's current MVP task explicitly authorizes ordinary incremental pushes to the five existing exact origins; this is scoped to that task and grants no force-push or global security permissions.

Pause/drain before backups or upgrades. Do not use `docker compose down -v` as recovery. A useful backup must bind PostgreSQL, artifacts and Git refs in one manifest and restore into an isolated environment; the [isolated rehearsal](evidence/isolated-backup-2026-10-10.json) passed for PostgreSQL, 13 artifact hashes and two Git repositories. See [backup operations](operations-backup.md) for the exact commands, quiescence requirement and exclusions. Windows/WSL local connectivity and actual Docker bindings are recorded; denial from another physical host is still unverified.
