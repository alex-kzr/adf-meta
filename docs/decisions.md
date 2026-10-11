# Decisions, assumptions and release gates

## Source precedence

The only initial product file was `SPEC.md` v0.2, SHA-256 `3494049865774af023fa49427feb3f71b8865dc82adcac3d7e5bc6a81cdde5a2`. It labels itself October 11, 2026; foundation work is October 10. This discrepancy is retained. No checkout `.agents/skills`, AGENTS.md, Git history or code was present. `.idea/` remains user-owned ignored IDE state. Relevant Git, Python, React, Vite and architecture diagram skills were read. No memories were found at the inspected default Codex memories location; none were edited.

Current user instructions precede SPEC, then documented design choices. The user's additional answers confirm local single user, React workflow editor, autonomy with limits, shared workspace, Codex/Claude subscriptions, agents/skills/tools/MCP, branches/commits, FastAPI and Compose. The original questions behind вЂњboth optionsвЂќ and вЂњall itemsвЂќ are unavailable; SPEC's manual task/goal decomposition and four priorities are the source for those details. Shared workspace means a common root with isolated write worktrees, as SPEC explicitly requires. This is the evolution from the earlier broad workspace answer to the explicit v0.2 design. It does not authorize concurrent writes to one checkout. Subscription CLI use does not require replacement with paid API access.

## Adopted design choices (not additional user requirements)

| Choice | Reason |
| --- | --- |
| Exactly four module repos | SPEC names frontend/API/orchestrator/worker; integrator and roles stay inside them |
| Worker uses scoped internal API, no direct PostgreSQL | Centralizes fencing and limits database privilege |
| Single orchestrator leader via DB lock | Adequate for one workstation |
| REST + SSE, same-origin bearer admin token | Minimal realtime/control surface; cookie sessions would require CSRF design |
| Default conflict repair manual | Bounded automatic repair requires explicit policy, at most one attempt |
| Pause drains active work and stops dispatch | Avoids unsafe OS process suspension |
| `done` task requires successful final integration | Task branch completion is recorded separately |
| Diagnostic scaffolds remain unready | Distinguishes design from functioning MVP |
| Contracts remain in umbrella | No fifth service or duplicate schema authority |
| Persistent operator profiles; opt-in single Codex app-server | Keeps one refresh authority while jobs have independent threads/worktrees; see [ADR 006](adr/006-provider-profile-ownership.md) |

The deployment appendix's branch format and adapter interface win over earlier generic examples: `factory/task/<task-id>/<execution-id>`, `factory/integration/<run-id>`; `probe/execute/cancel/collect_usage`. Approval is an explicit node; integration is a registered post-task operation. UI DAGs remain acyclic while retries are internal runtime transitions. `needs_resolution` is an integration substatus of a paused run, not a new run-status enum.

## Gates before real execution

- Check current subscription terms, authorization, CLI flags and reported usage for the actual account. Generic documentation does not establish contractual permission.
- Prove selected adapter permission controls can enforce required scopes. If not, disable autonomous writes; prompt prohibitions and shell filtering do not sandbox a host.
- Accept execution of trusted local repositories under a dedicated regular WSL account; untrusted code requires future sandbox work.
- Pin and test LangGraph/checkpointer/CLIs/Langfuse together. Current documentation describes newer APIs and Langfuse v4; do not assume v3 compatibility.
- Verify running Docker Desktop/WSL loopback, resources and subscriptions. Docker daemon was unavailable during foundation checks.

These gates block enabling real agents, not documentation/mock scaffolding/repo creation. Later choices: optional conflict repair, retention defaults, depth of metrics versus trace links, cookie sessions.
