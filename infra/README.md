# Local deployment foundation

[compose.yaml](compose.yaml) is a diagnostic scaffold: ADF PostgreSQL/Redis plus API/orchestrator/frontend. Worker deliberately runs outside Compose. The optional Collector [configuration](otel-collector.yaml) drops all traces and has no Langfuse exporter.

[compose.langfuse.yaml](compose.langfuse.yaml) is an **overlay**, not a replacement for official Langfuse dependencies. Use a separate pinned upstream checkout/project and replace all upstream credential placeholders before starting. No upstream repository or secret is committed here. It requires recent Compose !override support. Read [startup/operations](../docs/local-development.md) and [observability](../docs/observability.md).

Current gaps: no Alembic migrator/scoped DB roles, runtime clients, authenticated execution endpoints, OTel instrumentation/exporter or tested Collector container healthcheck. Readiness is intentionally 503. Dockerfiles/image tags/Compose parsing are foundation inputs; they are not evidence that containers started. In E1, build/pull candidates, lock digests, run migrations before API/orchestrator through service_completed_successfully and verify reconnect/health/ports. No credentials or Docker socket are mounted from the host.
