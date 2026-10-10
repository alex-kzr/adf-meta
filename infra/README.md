# Local deployment

[compose.yaml](compose.yaml) runs authenticated PostgreSQL/Redis, a scoped Alembic migrator and the API/orchestrator/frontend. The worker executes on the WSL host. Apply [images.lock.env](images.lock.env) after the preserved local env file to select verified immutable digests.

[compose.langfuse.yaml](compose.langfuse.yaml) overlays checksum-verified official Langfuse Compose. [langfuse-source.lock.json](langfuse-source.lock.json) records source/image pins; generated secrets and downloaded source remain ignored. Run it as a separate project using `.bootstrap/langfuse/.env` and the dedicated `adf-telemetry` network.

[otel-collector.yaml](otel-collector.yaml) exports only eligible bounded ADF spans, strips sensitive fields and maps validated correlation to Langfuse v4. A private generated auth overlay supplies Basic ingestion credentials. [otel-collector.disabled.yaml](otel-collector.disabled.yaml) provides a no-export diagnostic option. Logs/metrics are not exported to Langfuse.

Core containers, scoped migrations and dependency readiness have run successfully locally. Official Langfuse/Collector privacy/correlation ingestion has passed. These checks do not establish full MVP acceptance: actual provider/concurrency/recovery, dedicated-account privilege, external-host denial and backup/restore gates require separate evidence. Read [operations](../docs/local-development.md), [observability](../docs/observability.md) and [current implementation status](../docs/implementation-status.md).
