# Product and MVP scope

The MVP serves one developer on one trusted workstation. They register a WSL Git repository, submit a manual task or goal, approve a plan/permission profile, select immutable workflow/agent versions and receive verified changes on an integration branch. Model assertions are never completion evidence.

## Journeys

1. Prepare: doctor checks paths, infrastructure, versions and explicit auth state. Register clean ext4 repo/default branch/test-command registry. Invalid path, dirty base or missing auth is actionable.
2. Plan: structured tasks include criteria, dependencies, expected paths and unknowns. User edits and approves immutable plan hash. Manual tasks still receive execution authorization.
3. Execute: independent tasks get distinct worktrees/branches. Dependency tasks start from a SHA containing predecessor changes. Overlapping path reservations serialize work.
4. Inspect: persisted event stream, bounded logs, test/review artifacts, unknown usage and redacted trace links. SSE reconnect replays by cursor.
5. Control: pause drains; resume is explicit; cancel stops descendants and preserves diagnostic state. Approval binds a concrete snapshot.
6. Integrate: independent review and tests evaluate fixed tree hashes. Sequential cherry-picks and integration tests precede completion. Conflicts pause; user controls later merge/publication.
7. Recover: reconcile checkpoints, dispatches, supervisor journals and Git operations before repeating uncertain side effects.

## Boundaries

Included: CRUD, structured planning, visual DAG validation/versioning, 3 parallel executions, Codex/Claude/mock adapters, Git worktrees/commits/integration, tests/review/approval, SSE, limits, recovery, skills/tools/MCP allowlists and privacy-preserving traces.

Deferred: multi-user/remote access, container sandbox, arbitrary code/plugin nodes, Kubernetes, remote workers, PR/CI automation, default-branch merge, multi-repo atomic integration, guaranteed subscription financial caps and Windows-native/macOS execution. A target project is one Git repo; nested gitlinks are read-only until a separate policy exists.

## Acceptance matrix

| SPEC IDs | Required evidence |
| --- | --- |
| A1/W1 | Fresh WSL ext4 startup; doctor verifies versions/auth without credential output |
| A2 | Manual task + structured plan CRUD, validation/edit/approval snapshots |
| A3 | Editor rejects invalid ports/cycles/forks; run version remains immutable |
| A4/W4 | Three overlapping jobs have distinct cwd/branches; dependents read predecessor changes |
| A5 | Pinned Codex/Claude fixture + live adapter contracts pass |
| A6/A7/W7 | Accepted task commits, integration tests, conflict preserves branches and default SHA |
| A8/W2/W3 | Fault injection around dispatch/spawn/commit/report; no duplicate writer/commit; cancel kills process tree |
| A9 | Skill/MCP/tool allowlists enforced/audited; injected permission changes denied |
| A10/W8 | SSE replay and end-to-end run/execution/trace correlation |
| A11 | Time/attempt/concurrency/output/disk limits enforced; absent usage is null |
| A12/W5 | Sentinel secrets absent from API/logs/artifacts/traces; no credential/Docker socket mount |
| W6 | Windows/WSL plus external-host negative connection tests prove loopback exposure |

SPEC defaults: 3 agents, 12 planned tasks, 2 retries (3 total attempts), 30 minutes/execution, 180 minutes/run, 20 MiB output/execution and 5 GiB/run. Proposed calibration targets: persisted event-to-UI p95 <2 s, heartbeat 10 s/lease 45 s, TERM grace 10 s. These are defaults to test, not measured results.
