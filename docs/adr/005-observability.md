# ADR 005: Observability without duplicate traces

Status: Accepted design detail; runtime exporter deferred.

## Context

Langfuse is an agent trace backend; current releases and headers differ. Credentials/prompts/source must not leak through traces.

## Decision

Use one OTel instrumentation owner per agent invocation. Route filtered agent traces to official Langfuse HTTP OTLP; metrics/logs stay local or use separate standard backends. Core works without telemetry.

## Consequences

Pin official stack separately and test privacy/correlation. Scaffold Collector drops traces until safe exporter/filter configuration is implemented.

See [architecture](../architecture.md), [decisions](../decisions.md) and [sources](../sources.md).
