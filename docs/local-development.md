# Local development and operations

## Two distinct locations

Foundation source is the requested Windows `C:\Users\admin\Documents\workspace\projects\adf` umbrella. Real factory target repos/worktrees and worker runtime must live on Ubuntu WSL2 ext4 (`/home/<worker>/ai-factory`), not `/mnt/c`. Export/bundle-bootstrap or published clone into ext4; do not concurrently run Windows CLI sessions. Keep user credentials in that dedicated regular WSL account.

Prerequisites: Windows 11, Ubuntu WSL2 (`wsl --status`, `wsl -l -v`), Docker Desktop WSL integration, Git, Python 3.12+/uv and Node 24 LTS/npm. Source pins observed: FastAPI 0.143.0/Uvicorn 0.54.0, React 19.3.0/Vite 8.3.4/TypeScript 7.0.2. PyPI candidate orchestration versions: LangGraph 1.2.14, checkpoint-postgres 3.1.2, LangChain 1.4.4; no compatibility is claimed or dependencies installed for them yet. CLI versions/account terms need separate verification.

## Foundation commands (implemented)

From umbrella, use a virtual environment for Python tools:

```sh
python3 -m venv .bootstrap/dev-env
source .bootstrap/dev-env/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -r services/api/requirements.lock
python -m pip install --no-deps -e services/api -e services/orchestrator -e services/runtime-worker
python scripts/verify.py
npm --prefix frontend ci
npm --prefix frontend run build
adf-orchestrator validate packages/contracts/examples/workflow.json
adf-worker mock --request packages/contracts/examples/execution-request.json
```

On Windows use `.bootstrap\dev-env\Scripts\Activate.ps1`. Worker doctor can report versions portably, but `ready_for_real_execution` remains false; auth is unknown. `scripts/doctor.sh`/`bootstrap-wsl.sh` are read-only preparation diagnostics, not installers or full W1 tests.

## Diagnostic Compose startup

```sh
python scripts/init-local-env.py
docker compose --env-file .env -f infra/compose.yaml config --quiet
docker compose --env-file .env -f infra/compose.yaml up -d --build
curl --fail http://127.0.0.1:8080/healthz
curl -i http://127.0.0.1:8080/readyz
```

Expected: UI `http://localhost:8088` shows design screen; API readyz is **503**. This is not a working factory. Image candidates require build/runtime validation and digest locking. `init-local-env.py` creates only ignored DB/Redis secret files, never CLI credentials; it preserves existing files and prints no secret. Verify Windows ACLs/Linux file ownership. Passwords stay outside env defaults; Docker configuration output should use --quiet to avoid future secret exposure.

Loopback ports: UI 8088, API 8080, ADF PostgreSQL 55432, ADF Redis 6380. Orchestrator 8081 is internal only. With `--profile observability`, Collector OTLP 4317/4318 and health 13133 are loopback-only. Scaffold apps do not yet connect to DB/Redis; acceptance requires authenticated SQL/Redis/API probes, not pg_isready alone. API artifact volume permissions for uid 10001 need E1 validation before uploads exist.

For a real E1 startup add locked migrations/scoped accounts and one migrator gated by healthy DB, then gate API/orchestrator on service_completed_successfully. Current Compose cannot claim that behavior because migrations are not implemented. `depends_on` aids startup but clients still need bounded reconnect backoff.

## Optional official Langfuse

Use official source URL from [sources](sources.md). Obtain an audited exact upstream Git revision in ignored `infra/vendor/langfuse`; do not add it as an ADF service repo/submodule. Record revision and all image digests in local deployment lock. Configure every upstream CHANGEME credential, disable upstream telemetry and unnecessary AI/MCP features, set six required LANGFUSE_*_IMAGE variables in ignored Langfuse env file. Never start with upstream default secrets.

```sh
# After a verified upstream checkout and private environment have been prepared:
docker compose -p adf-langfuse --env-file infra/vendor/langfuse/.env -f infra/vendor/langfuse/docker-compose.yml -f infra/compose.langfuse.yaml --profile observability config --quiet
docker compose -p adf-langfuse --env-file infra/vendor/langfuse/.env -f infra/vendor/langfuse/docker-compose.yml -f infra/compose.langfuse.yaml --profile observability up -d
```

Run separately from ADF to avoid service-name/volume collisions. Overlay preserves official web/worker/PostgreSQL/Redis/ClickHouse/MinIO, removes internal host ports and restricts UI 3000/object media 39090 to loopback. Official setup's RAM/storage demand is substantial; measure headroom with three CLI processes. Overlay compatibility must be checked for the pinned source, including every remaining credential default. Collector export is intentionally absent. E5 must configure a dedicated shared ingestion network or tested restricted host route, private auth and HTTP OTLP filter before enabling trace links; `localhost` inside a container is not Langfuse.

## Future real host worker sequence

Install CLIs using official instructions; authenticate interactively under WSL worker account; probe actual auth with approved read-only calls without token dumps. Configure registered ext4 roots/provider versions/scoped worker token; start implemented supervisor/consumer via uv or user systemd with process-group cleanup. No such daemon is provided in this foundation. Run mock end-to-end and acceptance tests before real subscription work.

Verify listeners from Windows and WSL, and denial from another host. If loopback fails, diagnose Docker Desktop/WSL networking; do not expose 0.0.0.0 as a shortcut. Pause/drain before planned upgrades/backups. Keep DB/artifact volumes on recreation; `docker compose down` retains them, `down -v` deletes them and is not a normal recovery step. Back up DB, Git refs and artifacts with one snapshot manifest, excluding ordinary credential stores. Restore isolated and verify before enabling workers. Recovery follows [reliability](reliability.md); never prune active worktrees or repeat uncertain CLI/Git effects.
