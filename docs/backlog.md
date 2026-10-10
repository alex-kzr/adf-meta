# Phased implementation backlog

The table below defines exit gates. Implementation is **in progress**, with core code and module tests present; individual gates require the evidence in [current implementation status](implementation-status.md) and [kanban](kanban.md). Foundation documentation/scaffolding is the completed preparatory step. Priorities retain SPEC's end-to-end flow, extensibility, UI/monitoring and parallelism together.

| Stage / item | Deliverable | Exit evidence / dependency |
| --- | --- | --- |
| E1.1 configuration | Pinned runtime/image lock, scoped secrets, health/ready distinction, Docker/WSL doctor | Fresh local bootstrap; network smoke; version audit |
| E1.2 data/control | Alembic schemas/roles, project/task/config CRUD, auth/errors/revisions | Migration+CRUD+grants tests; depends E1.1 |
| E1.3 contract generation | Pydantic/TS clients, draft OpenAPI reconciled to implementation | Schema compatibility tests |
| E1.4 UI foundation | Navigation, forms, API server cache, error display | Project/task creation E2E |
| E2.1 supervisor | Process groups, durable journals/locks, limits/redaction/cancel | Descendant termination/output-flood/fault tests |
| E2.2 mock + transport | Redis consumer/internal API lease/results, fenced mock execution/outbox | Duplicate/reconnect/lost Redis tests; depends E1.2/E2.1 |
| E2.3 Git | Worktree allocation, reviewed index/commit intent, artifact upload | Three distinct cwd/branches, commit-crash dedup |
| E2.4 CLI adapters | Pin Codex/Claude, capability/permission/auth fixtures and opt-in live checks | Terms/auth/scoping gate, unknown usage; depends supervisor |
| E3.1 compiler | Full typed DAG/fork/join validation and LangGraph checkpointer | Immutable versions, replay without duplicate effects |
| E3.2 planner/approval | Structured plan, versioned policies/config, hash-bound interrupts | Changed/expired/rejected approval tests |
| E3.3 scheduler | Global/provider/project quotas, path reservations, predecessor base assembly | Three actual independent overlaps, dependencies respected |
| E3.4 review/integration | Independent review/tree evidence, sequential deltas/tests/conflicts | Default branch unchanged, manual resolution; no automatic repair initially |
| E3.5 recovery | State reconciler, uncertain leases, cancel/pause deadlines | All reliability crash boundaries |
| E4.1 editor | React Flow forms/ports/validation/version publishing | A3 and accessibility E2E |
| E4.2 monitor | Fetch SSE replay, run/execution/Git evidence/approval UX | <2 s target, disconnect/reconnect/control tests |
| E4.3 agent settings | Registry/policy/capability screens | Unsupported capability explicit, no secret editor |
| E5.1 observability | OTel propagation/filtering, official pinned Langfuse stack/links/evals | No duplicate/private spans, outage-safe execution |
| E5.2 hardening | Allowlists/MCP/skills, trusted-host gates, quota/retention | A9/A11/A12/W5/W6 tests |
| E5.3 operations/release | Backup restore, upgrade matrix, WSL doctor, full acceptance | A1–A12/W1–W8 evidence and docs updated |

Security/telemetry privacy and concurrency invariants apply from E1/E2, not deferred until E5. E5 completes integration/hardening. Stop enabling real CLI execution if permission/terms gates fail; continue mock development. No extra deployable service should be introduced without ADR and independent operational need.
