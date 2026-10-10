# Live acceptance status

October 10, 2026. This report separates implemented behavior, observed acceptance and remaining work. `mvp_ready` remains **false**. Health checks and successful CI do not complete missing SPEC evidence. The source SPEC remains unchanged.

## Acceptance evidence

| Gate | Observed result | Remaining criterion |
| --- | --- | --- |
| A1/W1: native runtime | Core Compose and audited Langfuse are healthy; WSL ext4 worktrees, pinned Codex 0.157.0 and existing subscription authentication passed. | WSL Claude 2.1.296 is installed but unauthenticated. Dedicated least-privilege worker identity is not configured. |
| A2: tasks/planning | Persistent manual task, plan/edit/approval API and validation tests pass; actual bound execution approvals pass. | A2 allows the manual project/task journey, which passed. A full native Architect-generated plan/edit journey is additional coverage in progress. |
| A3: workflows | [Browser evidence](evidence/frontend-ui-2026-10-10.json) creates, edits, rejects unreachable/cyclic graphs, publishes immutable versions and shows immutable version UUIDs/hashes; separate API tests enforce run snapshot binding. Measured editor/read-only graph bounds are retained across updates. | See the dated frontend evidence for exact browser coverage; no blanket accessibility audit is claimed. |
| A4/W4: concurrency/dependencies | [Three developers and independent reviewers](evidence/codex-three-agent-2026-10-10.json) completed. [Dependent tasks](evidence/codex-dependencies-2026-10-10.json) received predecessor contents in their approved base SHA and request hash. [Load/restart run](evidence/codex-load-restart-2026-10-10.json) preserved all three active CLI identities across one API/orchestrator restart. | General workload capacity is not inferred from these small fixtures. |
| A5: adapters | Codex native development/review, structured review, cancellation and restart pass; mock and Claude adapter contract tests exist. | Native WSL Claude execution and scoped capability acceptance require authentication first. Windows Claude authentication does not satisfy this gate. |
| A6/A7/W7: Git | Tests and independent tree-bound reviews precede three task commits and isolated integration; original main stays clean/unchanged. | [Actual conflict/resolution](evidence/codex-conflict-resolution-2026-10-10.json) passes with zero automatic retries: one stopped conflict, one exact operator-approved clean-tree continuation and unchanged main/task refs. Historical attempt one retains its waiting-approval projection; latest attempt two succeeds. |
| A8/W2/W3: recovery/control | [Recovery/outage](evidence/codex-recovery-2026-10-10.json), active API/orchestrator restart, Linux fault tests and [live cancellation](evidence/codex-cancellation-2026-10-10.json) pass. Latest cancellation retains matched execution proof and closes all persisted nonterminal node attempts. | Automated uncertain ownership/recovery tests and actual component/consumer restarts cover A8/W2/W3. Full host-loss/live expired-supervisor drills are additional hardening. Latest cancellation elapsed timing was not retained; its 45-second observation bound and prior separately measured 2.219-second cancellation are distinguished in evidence. |
| A9: skills/tools/MCP | Registry validation, immutable manifests, skill SHA-256/root/size checks, role restrictions and negative permission tests are implemented. Codex configured narrow tools/MCP reject with `CAPABILITY_UNSUPPORTED`. | Positive native skill/tool/MCP integration is being implemented and exercised. Existing generic MCP scope/timeout metadata is not enforced by the old worker path; this implementation gap is distinct from unverified Claude argv behavior. See the capability distinctions below. |
| A10/W8: events/telemetry | 222 unique ordered SSE events and 13 artifact hashes were checked. [Actual Langfuse trace](evidence/langfuse-three-agent-2026-10-10.json) has 80 correlated observations; execution completed during a 147.921-second telemetry outage. | SPEC targets event-to-UI latency below two seconds; no p95 definition was specified, and live latency calibration is unmeasured. Community Langfuse retention remains unrestricted (`retentionDays: null`), not an enforced 30-day policy. |
| A11: limits/usage | Meaningful attempt/time/concurrency/output/disk tests pass; actual zero-retry runs and three parallel Codex developers pass. Measured developer peak RSS is 666 MiB; same-time CLI plus 12 container working sets peak at 3.21 GiB. | Measurements exclude WSL/kernel/VM overhead and cache; a 4 GiB host capacity guarantee is not established. Full 30-minute/5-GiB stress calibration is not performed. Subscription financial caps are unavailable; absent cost remains null. |
| A12/W5: secrets/trust | Redaction/denial/sentinel tests pass, traces exclude sensitive payloads; application containers have no provider credential or Docker socket mounts. Scoped PostgreSQL/Redis roles are tested. | Host worker currently runs as `alex`, which can access sudo/docker/socket. Least-privilege account setup and its native denial checks are not performed. Strong hostile-code isolation is not implemented and remains outside the trusted-repository MVP. |
| W6: networking | Docker host ports bind loopback; Windows/WSL authenticated reachability and local non-loopback denials are checked. | Negative connection from an external host or suitable isolated VM remains unverified; SPEC does not specifically require a second physical workstation. |
| E5: backup/release | [Isolated restoration](evidence/isolated-backup-2026-10-10.json) verifies PostgreSQL inventory, 13 artifacts and two Git repositories without touching source services. Published child/umbrella CI and bundle/recursive-clone restoration pass. | Backup excludes Redis, Langfuse and worker journals; full runtime crash restoration and an atomic cross-store maintenance fence are not implemented by this snapshot workflow. |

## Capability distinctions

Skill loading is implemented: the worker reads only approved-root content, verifies the immutable digest and 32 KiB cap, then inserts the text in the provider request. Registry and enforcement tests are evidence of this code path, not a positive native provider/skill trial.

Codex has a verified coarse observe/trusted-development profile for the recorded trusted fixtures. Its adapter deliberately has **no supported narrow configured tool or MCP profile**; those requests fail before launch. This is an unsupported capability, not a silently permissive fallback.

Claude constructs explicit built-in tools, read-only role restrictions and `--strict-mcp-config` with a generated registered stdio configuration. The code exists and negative/argv contracts are tested. Diagnostic `mcp_scope_verified` remains false; native installed-provider enforcement and positive MCP/skill trials are **unverified**. Do not enable or widen capabilities based on registry presence alone.

Git worktrees and process groups manage concurrent trusted work and lifecycle. They do not isolate malicious code from the host account. The old generic MCP path ignores declarative `scope` and per-server `timeout_sec`: metadata alone is not an enforced filesystem or timeout boundary. A supported server needs a validated, enforced scope and denial fixture; authentication alone cannot prove this.

A separate hostile-code sandbox is **not implemented** and is a deferred architectural feature, rather than a test that merely needs rerunning.

## Mandatory MVP blockers and operator actions

The outstanding mandatory gates are the separate minimally privileged worker account (SPEC security/W1), authenticated selectable Claude (A5/W1), and usable assigned/audited skills/tools/MCP with enforced restrictions (A9). External-origin denial evidence (W6) is also outstanding. Current work closes available positive capabilities; see [minimal operator actions](operator-acceptance.md) for the permission-dependent steps. Full native planning is extra coverage because A2 accepts the already-tested manual journey.

## Operator decisions and actions

- WSL Claude login needs the user's interactive authentication authorization. No credentials are copied from Windows or exposed to containers.
- A dedicated account, group membership, Docker socket access and credential-home policy require an explicit approved operator setup. Existing `alex` membership has not been changed.
- External-host denial needs an available authorized external host or suitable VM and a bounded connection probe. Local loopback checks cannot substitute for it.
- Full host-loss and additional live uncertain-supervisor drills are hardening after MVP; existing automated and actual restart proofs cover the exact required recovery behavior. The separately requested nondestructive restored-environment rehearsal is in progress.
- Once native Claude authentication and the permission profile are accepted, run positive/negative skill, tool and MCP fixtures and the full planning journey. Do not grant unsupported Codex scopes as a shortcut.

## Hardening after MVP

Strong hostile-code sandboxing is deferred by SPEC. Full host-loss/expired-supervisor fault drills, full-size disk/duration stress, a four-GiB capacity guarantee, an atomic cross-store maintenance fence and extended Redis/Langfuse/journal backups are additional hardening, not newly invented release gates. Provider rate-limit normalization and delay-aware retry remain unimplemented; no provider switching is performed. Native automatic planning is additional journey coverage. Thirty-day Langfuse retention is not a source SPEC requirement.

## Screenshot delivery

Six original redacted screenshots were explicitly approved for the user's ChatGPT Library. The one authorized upload retry failed because the local Library helper could not access its required hosted tool. No Library file IDs were returned or claimed. Permission is resolved; delivery capability remains unavailable. This optional attachment failure does not block other acceptance work. The six files are preserved in `C:/Users/admin/Documents/Codex/2026-10-10/task/adf-screenshots/`: `01-project-registration.jpg`, `02-run-approval.jpg`, `04-completed-desktop.jpg`, `06-mobile-dag.jpg`, `07-git-evidence.jpg`, `08-artifact-preview.jpg`. Other QA screenshots are local and are not part of that upload authorization.
