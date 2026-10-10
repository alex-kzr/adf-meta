# Official technical sources and verification scope

Reviewed October 10, 2026. These sources establish provider capabilities. Exact release locks and bounded runtime checks are recorded in [implementation status](implementation-status.md); passing those checks does not establish all acceptance gates. No quoted provider terms or assumption of subscription automation entitlement is made.

| Official source | Verified fact / implication |
| --- | --- |
| [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | Checkpoints are organized by thread; durable state enables resume. External filesystem effects still require ADF journals/dedup. |
| [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | Resume uses same thread with Command; interrupted node restarts. Typed interrupt schemas are version-dependent; API validates independently. |
| [Codex noninteractive](https://developers.openai.com/codex/noninteractive) (redirects to official ChatGPT Learn) | `codex exec --json` emits JSONL; output schema and saved CLI auth are supported. Pin flags/event shapes; do not expose auth files. |
| [Claude Code programmatic execution](https://code.claude.com/docs/en/headless) | `-p`, JSON/stream-json and structured output exist; streaming verbose/partial flags and cancellation behavior vary by version. |
| [Langfuse Compose guide](https://langfuse.com/self-hosting/deployment/docker-compose) | Use official Compose, configured secrets, persistent stores; it is not an HA/backup solution. |
| [Official Langfuse Compose source](https://github.com/langfuse/langfuse/blob/main/docker-compose.yml) | Inspected source uses web/worker, PostgreSQL, Redis, ClickHouse and MinIO; current source uses v4 major tags. Pin full revision/images before deployment. |
| [Langfuse OpenTelemetry](https://langfuse.com/integrations/native/opentelemetry) | HTTP OTLP trace endpoint/auth exists; current v4 realtime header differs from older releases; do not export generic logs/metrics there. |
| [OTel Collector configuration](https://opentelemetry.io/docs/collector/configuration/) | Receivers/processors/exporters need explicit pipeline wiring; no-export scaffold is not a trace backend. |
| [Redis XAUTOCLAIM](https://redis.io/docs/latest/commands/xautoclaim/) | Claims pending deliveries by idle time; it cannot prove old CLI process death. |
| [Git submodule](https://git-scm.com/docs/git-submodule) and [Git bundle](https://git-scm.com/docs/git-bundle) | Gitlinks pin commits; relative URLs depend on parent remote; bundles transport committed refs, not dirty state. |
| [Docker WSL2](https://docs.docker.com/desktop/features/wsl/) | WSL integration and Linux filesystem placement matter; actual networking still needs environment smoke tests. |
| [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) | Healthy/completed dependency conditions aid startup, not ongoing reconnect reliability. |
| [pg_isready](https://www.postgresql.org/docs/current/app-pg-isready.html) | Server accepting connections is not proof of authenticated application access. |
| [Vite guide](https://vite.dev/guide/) | Node requirements/tooling checked; this scaffold uses exact publisher registry versions plus npm lock. |
| [React Flow custom nodes](https://reactflow.dev/learn/customization/custom-nodes) | Custom typed nodes/handles support a declarative editor, not an execution engine. |
| [TanStack Query defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults) | Defaults include refetch/retry behavior; control mutation semantics must be configured explicitly. |

Package metadata was checked against npm/PyPI publisher registries. [Core image digests](../infra/images.lock.env), the [official Langfuse source and image lock](../infra/langfuse-source.lock.json), and each child lockfile pin the tested inputs. Docker core services, WSL worker diagnostics, PostgreSQL contract tests, real Codex worktree execution and the Langfuse OTLP privacy route have been exercised locally. Remote CI is also checked for each published child commit. Full recovery, hostile-code isolation, dedicated-account privileges, external-host denial, live scoped MCP and Claude WSL execution remain separate gates. Subscription usage has real token counters when reported, with financial cost unknown; no paid API fallback is configured.
