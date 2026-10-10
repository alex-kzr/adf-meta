# Observability design

OpenTelemetry instruments API/orchestrator/worker. Correlation attributes: project_id, task_id, run_id, node_run_id, execution_id, agent_id and provider, with W3C traceparent propagated in durable job metadata. Do not put IDs with unlimited cardinality in metric labels. Spans: api.request, workflow.run/node, agent.execution, cli.session, tool.call, git.operation, test.run.

Langfuse is the agent/LLM trace and evaluation backend. It is not a generic OTel metrics/log storage backend. Send only eligible redacted agent trace spans to its HTTP OTLP endpoint; system metrics/logs stay local or go to future standard backends. The current Collector file is **disabled/no-export** and drops all received traces; it is not the production exporter setup. Before enabling an exporter, implement producer allowlists, collector filtering and sentinel tests. Do not enable verbose debug exporters on raw spans.

Choose one instrumentation owner per agent invocation: either LangChain/Langfuse integration producing OTel observations or explicit adapter spans. Do not add duplicate callback and manual roots. CLI agents are subprocess adapters, not LangChain model calls; record actual exposed CLI events and unknown usage. Raw source/prompts/stdout/tool arguments/credential headers never export by default. Generic OTel span IDs may need explicit mapped Langfuse attributes verified against the pinned release.

Official docs currently describe Langfuse v4 headers for realtime ingestion; older versions differ. HTTP OTLP is supported, gRPC ingestion is not documented as supported by Langfuse. Collector may accept gRPC locally, then export HTTP. Configure auth only in ignored secret files, never an example literal key. See [verified sources](sources.md).

Metrics: execution/run duration, outcomes/retries, queue depth, active workers/jobs, lease loss, conflicts, test pass rate, event latency, disk and known provider usage. Limit labels to provider/role/outcome; run/execution IDs stay in spans/logs. UI shows a compact overview and links to trusted Langfuse URLs; missing backend/usage is clearly unavailable, never zero.

Telemetry outage must not stop core work. Use bounded batch/export buffers, timeout/retry, sampling and dropped-span counters; disable tracing independently. Proposed retention: 7-day logs, 30-day redacted events/traces. Langfuse upgrade/resource/backup lifecycle stays with its official stack. Validate one representative trace, parent/child IDs, no duplicates, no sensitive fields and core operation with exporter offline before A10/W8 acceptance.
