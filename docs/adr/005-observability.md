# ADR 005: Filtered agent telemetry through the official Langfuse stack

Status: Accepted and implemented; real filtered Collector-to-Langfuse ingestion verified. Actual ADF-run and outage acceptance remain separate gates.

## Context

The local CLI adapters are subprocess integrations rather than direct LangChain model calls. Langfuse v4 ingests OpenTelemetry over HTTP with a realtime ingestion header. ADF must not export credentials, prompts, source or tool arguments, duplicate spans or make workflow success depend on an observability backend.

## Decision

Use one OTel instrumentation owner per invocation and persist W3C trace context in durable run/job metadata. SDK producers construct only fixed-name, bounded, allowlisted metadata spans. The Collector accepts trusted ADF service names and explicit eligible workflow spans, strips unsafe fields/events, rejects links and invalid identifiers, then maps validated IDs to Langfuse metadata on every span. Auth is merged from an ignored read-only local file and never supplied to the host worker or frontend.

Bootstrap the official six-component Langfuse Compose at a committed upstream revision and SHA-256; pin every image by immutable registry digest. Keep its databases/object storage/cache and persistent volumes separate from ADF. Overlay only loopback exposure, local resource caps, healthchecks, log rotation and a dedicated Collector-to-web network. Generate all upstream placeholder credentials locally, preserve them and disable upstream product telemetry and its in-app agent. No external product is reimplemented.

Metrics/logs do not go to Langfuse's trace endpoint. Export queues, requests and retries are bounded; an outage can lose telemetry but cannot change execution ledger states. Operators can disable instrumentation independently or select an explicitly no-export Collector configuration. Disabled traces do not satisfy A10/W8.

## Consequences and verification

The initial API/worker/orchestrator version must agree on eligible names, typed IDs and trace context. A representative root/child OTLP trace must be retrieved via the v4 observations API, including sentinel privacy and duplicate checks, before declaring the pipeline verified. An actual ADF run must additionally demonstrate CLI/Git correlation and a real UI deep link; an outage fault test proves core independence. Memory limits are bounds, not capacity evidence; inspect actual resources and use an observability profile on this workstation. Local Docker administrators can inspect upstream environment secrets, so Docker remains a trusted local administration boundary.

See [operations and contract](../observability.md), [architecture](../architecture.md), [security](../security.md) and [sources](../sources.md).
