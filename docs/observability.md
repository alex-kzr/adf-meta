# Observability and local Langfuse operations

ADF uses one OpenTelemetry instrumentation owner per CLI invocation. API, orchestrator and host worker emit bounded metadata spans; the Collector forwards only eligible agent workflow traces to the separate official Langfuse stack. Metrics and logs are not sent to Langfuse's OTLP trace endpoint. Core execution does not depend on the exporter being available.

## Reproducible official stack

[langfuse-source.lock.json](../infra/langfuse-source.lock.json) fixes upstream revision `35d16971a3f83256d33f846b85dbff8c2d5c4d77`, the exact Compose SHA-256 and immutable registry image digests. The bootstrap downloads only that official Compose file into ignored `infra/vendor/langfuse/` and verifies its checksum before use. A changed upstream file is rejected, not silently replaced. [compose.langfuse.yaml](../infra/compose.langfuse.yaml) only overlays local exposure, resource caps, healthchecks, log rotation and the telemetry network. PostgreSQL, Redis, ClickHouse, MinIO, Langfuse web and worker remain the upstream components. Their stores are separate from ADF's stores.

Run from the umbrella root using Python 3.12 or newer:

```powershell
python scripts/prepare-langfuse.py --validate --check-resources
python scripts/prepare-langfuse.py --pull
docker network create adf-telemetry
docker compose --project-name adf-langfuse --env-file .bootstrap/langfuse/.env -f infra/vendor/langfuse/docker-compose.yml -f infra/compose.langfuse.yaml --profile observability up -d --wait --wait-timeout 240
docker compose --project-name adf --env-file .env --env-file infra/images.lock.env -f infra/compose.yaml --profile observability up -d --no-deps otel-collector
```

Create the network only if `docker network inspect adf-telemetry` reports it absent. The same commands work in WSL with its Python command. Preparation never starts containers or changes Docker settings. Check actual available resources and running containers before `up`. The official VM guide recommends at least four cores and 16 GiB of RAM; that is a recommendation for Langfuse, not a combined ADF capacity guarantee. On the inspected workstation Docker reports 16 CPUs and 15.18 GiB. This is below 16 GiB, so full-stack capacity must be measured during acceptance. The local six-container memory caps total 8.75 GiB (web 2, worker 2, ClickHouse 3, PostgreSQL 1, MinIO 0.5, Redis 0.25); caps prevent accidental memory expansion but do not prove throughput or startup success. Do not change Docker's memory settings automatically.

The bootstrap generates distinct local database/cache/object-store/application secrets plus a project API key and initial operator password. It writes them only into ignored `.bootstrap/langfuse/`, uses mode 0600 files and 0700 directories on Linux, preserves existing values and refuses divergent derived files. On Windows, protect that directory with the user's filesystem ACL; the Python mode flag is not an ACL management mechanism. No provider authentication home is read or mounted. Upstream Langfuse consumes environment variables, so a local Docker administrator can inspect container configuration; Compose is a trusted local administration boundary.

Headless initialization creates organization/project `adf-local` and user `operator@adf.local`. The live public project API confirmed project `adf-local`; its effective `retentionDays` is `null` on this Community deployment. Open `http://localhost:3000`; inspect the generated `operator-login.txt` privately for the password. Never paste its contents into agent prompts or diagnostics. The configuration requests 30-day retention. The pinned initialization code applies it only when the `data-retention` entitlement is available; Community deployments can retain data indefinitely. Verify the effective project setting before relying on retention. No license is purchased or enabled by this bootstrap. Changing the generated initialization variables does not rotate existing database users/API keys; perform rotation through the supported Langfuse interface and then update the local generated configuration deliberately.

Published ports are only `127.0.0.1:3000` (web) and `127.0.0.1:39090` (browser media endpoint). Databases, cache, worker and MinIO console have no host ports. Only Langfuse web and ADF Collector share the external `adf-telemetry` network, using the `adf-langfuse` alias. Langfuse's other services stay on its project network. ADF application containers need only their core network and the Collector address. No host CLI credential directories or Docker socket are mounted. The overlay explicitly sets Node `HOSTNAME=0.0.0.0` inside web/worker so their loopback healthchecks work; Docker host publications remain restricted to 127.0.0.1. Web probes `/api/public/health?failIfDatabaseUnavailable=true`; worker probes `/api/health`, which checks PostgreSQL and Redis. Neither response alone proves trace ingestion.

## Collector and instrumentation contract

[otel-collector.yaml](../infra/otel-collector.yaml) is an active filtered HTTP exporter, validated against Collector Contrib 0.162.0. Its image digest is recorded in the lock. Merge the ignored private authorization fragment without printing resolved configuration:

```text
--config=/etc/otelcol/config.yaml
--config=/run/secrets/langfuse-collector-auth.yaml
```

Mount `.bootstrap/langfuse/collector-auth.yaml` read-only at the second path. This contains only the Langfuse exporter Basic authorization headers; application services and the WSL worker receive no Langfuse secret. The exporter uses `http://adf-langfuse:3000/api/public/otel`, which appends `/v1/traces`, with `x-langfuse-ingestion-version: 4`. Langfuse supports HTTP JSON/protobuf OTLP; its ingestion endpoint does not support gRPC. The Collector can accept local gRPC and HTTP and export HTTP.

| Producer field | Contract |
| --- | --- |
| Resource `service.name` | `adf-api`, `adf-orchestrator`, `adf-runtime-worker` only |
| `adf.telemetry.eligible` | Boolean `true` only for an approved agent workflow trace, including its root |
| Span name | Fixed `api.request`, `workflow.run`, `workflow.node`, `agent.execution`, `cli.session`, `tool.call`, `git.operation`, `test.run` |
| Correlation attributes | `project_id`, `task_id`, `run_id`, `node_run_id`, `execution_id`, `agent_id`; UUID or 32 lowercase hex IDs, required `run_id` |
| Provider/role/outcome | Fixed enums; no free-form names or descriptions |
| Numeric metadata | Bounded integers for `adf.attempt`, `adf.exit_code`, `adf.usage.input_tokens`, `adf.usage.output_tokens`; missing usage stays unknown |
| W3C context | `traceparent` persisted in run/job metadata and propagated to node, CLI, Git and test spans |

The Collector drops untrusted producer names, ineligible spans, unsupported span names, invalid/missing run IDs and spans containing links. It discards all span events, clears status descriptions and tracestate, normalizes instrumentation scope name/version and removes non-allowlisted span/resource/scope attributes. It maps validated IDs to `langfuse.trace.metadata.*` on every span and `langfuse.session.id=run_id`, sets a fixed trace name, and assigns chain/agent/tool/evaluator/span observation types. CLI sessions remain agent observations; they are not invented direct model API calls. No callback integration is layered over these same spans.

SDK producers must also construct telemetry from an allowlist before enqueueing it: credentials, request headers, source, prompts, stdout/stderr, tool arguments, raw exception text, filesystem paths and arbitrary baggage/schema URLs never enter telemetry. A Collector filter is defense in depth, not authorization to emit raw payloads. SDK schema URLs are fixed library metadata, never user data. Resource and span IDs are not metric labels. Use bounded provider/role/outcome labels for metrics; keep per-run IDs in the execution ledger and traces.

`ADF_TELEMETRY_ENABLED=false` disables application exporters by default. Enable it deliberately for acceptance and set `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318` in containers or `http://127.0.0.1:4318` in WSL. Receiver ports remain loopback-published. To run a Collector with tracing explicitly disabled and without Langfuse credentials, select [otel-collector.disabled.yaml](../infra/otel-collector.disabled.yaml); it acknowledges then discards traces through a `nop` exporter. Disabled mode cannot satisfy trace acceptance.

## Real ingestion and privacy validation

After both stacks and Collector are healthy:

```powershell
python scripts/check-telemetry.py --timeout 90
python scripts/check-telemetry.py --existing-trace <32-lowercase-hex-trace-id> --report .bootstrap/run-trace-validation.json
```

The first check posts an actual OTLP smoke trace through the Collector, then queries Langfuse's real-time `/api/public/v2/observations` endpoint. It requires the exact root/child span IDs, parent relationship, session/run metadata and no duplicates; it verifies that ineligible/untrusted spans and sensitive sentinel fields are absent. The smoke fixture also exercises raw prompts, code, stdout, tool arguments, credentials, scope/resource fields, span events, status descriptions, tracestate and span-link rejection. It writes only safe IDs/counts/deep links into ignored `.bootstrap/telemetry-validation.json`. A synthetic OTLP check tests the pipeline; A10/W8 additionally require an actual ADF run's trace, from dispatch through CLI execution and Git commit. A UI trace link is unavailable until that run has a valid trace ID and configured local Langfuse project; do not invent it from a run UUID.

The trace URL format `/project/<project-id>/traces/<trace-id>` exists in the pinned upstream route. Verification uses the v4 observations API because other public read endpoints may lag by approximately ten minutes. Browser session login is still required for the private trace UI; traces are never made public automatically.

Collector batches are limited to 256 spans, its in-memory export queue to 32 batches, exporter requests to 3 seconds, retries to 30 seconds and memory-limiter to 192 MiB. SDK batch queues/timeouts must also be bounded and run in background; errors never become failed workflow transitions. Trace delivery is best effort: queue overflow, disabled tracing, container restart or a prolonged outage can lose telemetry, while the execution ledger and redacted artifacts remain authoritative. Inspect exporter dropped/failure counters through Collector self-metrics and safe service diagnostics. No detailed/debug exporter is enabled.

Acceptance must stop Langfuse/Collector temporarily while a controlled workflow continues, confirm core completion, restore observability and confirm a subsequent trace arrives. For a real controlled run still queued/running while Langfuse is stopped, run:

```powershell
python scripts/check-telemetry.py --outage-run <run-uuid> --admin-token-file .bootstrap/secrets/admin-token --timeout 180 --report .bootstrap/telemetry-outage-validation.json
```

Use the actual generated ADF admin token filename when it differs. This mode makes no container or workflow mutations and reads no provider credential store. It rejects a previously completed run, requires Langfuse to remain unavailable at every polling step and records only safe completion evidence. Stop/restore the stack separately as part of the controlled fault scenario. Record measured resource usage, process health, cross-stack connectivity, Windows/WSL loopback access and external-host denial. Configuration parsing and `/health` alone do not prove these properties. Use `docker compose stop`, not `down -v`, for fault tests; never delete persistent volumes as part of a smoke test.

## Verified sources and status

Official behavior was checked against [Docker Compose deployment](https://langfuse.com/self-hosting/deployment/docker-compose), [headless initialization](https://langfuse.com/self-hosting/administration/headless-initialization), [OTLP ingestion and mapping](https://langfuse.com/integrations/native/opentelemetry), [health endpoints](https://langfuse.com/self-hosting/configuration/health-readiness-endpoints), the pinned [official Compose source](https://github.com/langfuse/langfuse/blob/35d16971a3f83256d33f846b85dbff8c2d5c4d77/docker-compose.yml) and [v4 API specification](https://github.com/langfuse/langfuse/blob/35d16971a3f83256d33f846b85dbff8c2d5c4d77/web/public/generated/api/openapi.yml). OTTL behavior was checked against [Collector 0.162 filter](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/v0.162.0/processor/filterprocessor/README.md) and [span context](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/v0.162.0/pkg/ottl/contexts/ottlspan/README.md).

Verified so far: source checksum, immutable registry manifests and pulled images, private generation/preservation, all six resolved official services, removal of default credentials, loopback-only port declarations, resource caps and Collector configuration validation. Seventeen bootstrap/privacy/correlation/outage-validator unit tests pass. The opt-in Docker test also captured a real Collector HTTP export: exactly two eligible root/child spans, correct mapped IDs and no sentinel in exported fields or Collector logs. Run `ADF_TEST_OTEL_DOCKER=1 python -m unittest discover -s tests -p test_observability.py` in WSL/Linux, or set `$env:ADF_TEST_OTEL_DOCKER='1'` first in PowerShell. This test uses a dedicated temporary network and pinned ephemeral capture/Collector containers, then removes only those test containers and network. The official six-container stack is now healthy and runs the locked image digests; live web reports Langfuse 4.56.0 (image revision `1d072771971e3d30620b7d4d63a3080ebe72d4a2`). A real Collector-to-Langfuse smoke trace was retrieved through the v4 observations API with exactly two root/child records, correct parent/session/run/execution correlation, no duplicate spans and no sensitive sentinel. Bounded web/worker/Collector log scans found no generated secret. Windows and Ubuntu WSL loopback health probes returned 200; local non-loopback interface probes for port 3000 were denied/unbound and Docker inspected publications were loopback-only. This is local-interface evidence, not a separate external-host test. An idle snapshot measured approximately 2.13 GiB for Langfuse and 2.52 GiB for all running ADF/Langfuse/Collector containers, with no OOM flags; it is not a throughput/load capacity result. Ignored evidence lives in `.bootstrap/telemetry-validation.json` and `.bootstrap/langfuse-runtime-validation.json`. Actual ADF-run CLI/Git correlation, authenticated browser trace rendering, controlled core completion during outage and an external-host exposure test remain acceptance gates. See [delivery status](delivery-status.md) for the overall MVP gate.
