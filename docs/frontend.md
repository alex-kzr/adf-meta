# Frontend implementation design

React + strict TypeScript + Vite; React Flow is the visual editor, TanStack Query owns server state. Graph drafts and selection are local UI state; API snapshots/versions/events are authoritative. No state library/service is needed initially. React Flow custom nodes map to a typed registry; use stable memoized node types and selective subscriptions to avoid rerendering all nodes for every event.

| Screen | MVP behavior |
| --- | --- |
| Dashboard | Projects/runs/queue/agent health/limits/errors; unknown usage distinct |
| Projects | Canonical WSL repo/path validation, branches and registered checks |
| Tasks | List/kanban, criteria, dependency DAG, proposed plan edit/approval |
| Workflow | Node palette/settings/typed handles, validation errors, draft vs published versions, launch |
| Agents | Role/prompt/provider/capabilities, versioned skills/tools/MCP and numeric limits |
| Run | Parallel branches, node states, SSE replay, pause/drain/resume/cancel and approval cards |
| Execution | Bounded redacted stream/test/review artifacts, provider health, unknown usage and trace link |
| Git changes | Accepted diff/tree/commit/base IDs, final branch, conflict files/resolution state |
| Settings | Roots/policy/telemetry; credential references only, no credential editor |

Mutations carry idempotency key and revision; on conflict fetch latest and let user reconcile edits. Never optimistically mark run done/approval accepted. Explicit stale-data and disconnection indicators; reconnect replay then invalidate relevant queries. Query retries are limited for transient reads; do not blindly retry paid/mutating commands. Abort requests on navigation; deduplicate stream events and cap in-memory log rows.

Server graph validation is mandatory regardless of client validation. Render approval's exact scope/hash/base, expiry and changed-snapshot error. Pause button explains draining. Cancellation remains pending until server terminal evidence. Permission/auth/capability failures are actionable; UI cannot suggest bypass by default.

Accessibility: keyboard node selection/settings, focus management, semantic form labels, error summaries, reduced motion and text/icon states independent of color. Stream updates should not continually steal focus or announce every token. Diff/log content is escaped; no raw agent HTML. Token stays in memory; fetch-based SSE sends header. No secrets embedded in Vite env vars. E4 tests cover editor invalid graph, immutable version launch, approval conflict, SSE reconnect and cancellation status.

The current UI only shows a read-only design DAG and foundation status. It has no task/control backend integration and no claim of runnable execution.
