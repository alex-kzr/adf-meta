# Bounded WSL live acceptance after the approved mask installation

October 13, 2026. This is an execution plan, not an acceptance result. Whole-MVP
readiness remains false. The operator separately approved the exact live mask
repair at 08:22 UTC: worker `a3428799713e94e65153b87c8df0771fd9077f2a`, replacing
the parent `/run` deny with `/run/WSL` and `/run/current-system/sw` denies while
retaining default root deny. See the [source and rollback checkpoint](shared-wsl-mask-source-checkpoint.md).

## Entry conditions and permitted changes

Complete the preserved-environment comparison before installation. Retain the
original snapshots and report startup timestamps separately from settings or
health differences. Do not replace a baseline to obtain a passing result. Stop
installation if a material unrelated-resource difference or unresolved risk is
found. Recheck all 13 production ADF components without changing them.

Require zero active API/Redis work, an empty consumer-group pending list, free
allocation/provider locks, stopped recorded sessions and unchanged sealed inputs.
Historical cancelled deliveries, journals, worktrees and Redis entries remain
intact; none is reused. The previously installed worker is `0dd5ac7`.

Install only the [39 recorded worker files](evidence/shared-wsl-worker-file-inventory-2026-10-13.json)
and private installation receipts. Use the verified candidate and rollback wheels
offline, with no dependency or CLI upgrade. The old source installation additionally
contains the verified empty uv build metadata; preserve it and the private worker
bytecode cache for rollback as documented in the source checkpoint. Check 29 canonical source hashes, 27
distribution versions, file ownership/modes and unchanged manifest hashes. Record
the installed commit, Codex 0.157.0 and Node 24.21.0 explicitly. Retain the existing
backend selection, sealed policies, user/groups, endpoints, listener bindings,
firewall, Git security settings and all other services.

Existing subscription authorization may be used normally through the SDK within
the approved MVP task. `account/read` uses `refreshToken=false`; do not request a
forced refresh. Do not run login/setup-token, create or copy credentials, change
account configuration, or enable a paid API/provider fallback. If the provider
requires a concrete new authorization or persistent-access action, stop and report
that action and phase. Possible ordinary SDK state updates alone are not a blanket
pre-execution authorization blocker.

## Fixed budget and stop conditions

Use one new acceptance namespace inside the already sealed synthetic project
`/home/adf-worker/ai-factory/projects/shared-acceptance-resumed-20261011`.
No production repository, new manifest grant or old execution ID is used.

- Total live acceptance wall time: **40 minutes**, including cleanup; installation
  and its rollback have a separate **180-second** bounded window.
- Codex: at most **10 accepted or attempted native turns** across the two cohorts
  below, at most **three concurrent developer executions**, one fresh repair,
  at most **120 seconds per turn** and **180 seconds per execution**. A failed
  turn consumes its allowance. Do not replace a failed/uncertain turn to fill a cohort.
- Claude: at most **two native attempts** and **five minutes**, only after the
  Codex success cohort passes and only if the current adapter/policy supports the
  required operations. An unsupported capability is a failed gate, not permission
  to bypass a guard or change credentials.
- Per execution: at most 100 observed tool steps, 256 KiB original output and
  16 MiB private worktree/check data; retain stricter existing limits. Count
  worker/SDK turn attempts durably. Underlying provider HTTP/inference requests
  are unknown unless directly measured; a turn is not an exact billing count.
- Stop on guard drift, an unexpected native read/write, an out-of-scope edit,
  output/time/disk/attempt exhaustion, provider fallback, a new auth requirement,
  an unowned process or an unresolved execution/mutation intent. Never replay an
  uncertain delivery or launch another turn after the budget is exhausted.

Each stage is attempted once. Preflight refusal or an earlier failed gate prevents
dependent stages. Do not silently enlarge the budget. Reserve at least five minutes
for owned-session shutdown, durable reconciliation and evidence collection.

## Stages and hypotheses

1. **Startup and capability preflight, no model turn.** Start only the dedicated
   provider owner with the existing command and sealed manifests, then validate
   subscription/account type, model availability and configured backend. Record
   the actual selected model before dispatch. Start only its dedicated consumer
   after the queue and owner checks pass. Hypothesis: the repaired pinned native
   sandbox can initialize and create a thread under production-equivalent inputs.
   `thread/start` alone does not prove useful generation or MVP acceptance.
2. **Useful Codex cohort, at most seven turns and 20 minutes.** Submit three
   synthetic Python tasks through API/orchestrator/Redis with immutable agent
   configurations, distinct branches/worktrees, disjoint marker skills and scoped
   approved MCP inputs. Observe all three generating concurrently; prove each
   receives only its own assigned configuration/capabilities. Require actual skill
   consumption and successful narrow MCP results, not configuration metadata alone.
   One deterministic registered assertion fails the first generated tree; permit
   one fresh repair. Passing fixed trees receive three independent reviews, task
   commits and serial integration with passing checks. The original main SHA stays
   unchanged. Hypothesis: native generation reaches a useful tested and reviewed
   integrated result through the real queue, within the existing Python checker scope.
3. **Fault cohort, exactly three additional turn allowances and 10 minutes.** Start
   three fresh synthetic developers. Cancel one while siblings are active and
   before host patch application, proving only its thread/helper stops and it writes
   nothing. Inject one recorded-owner failure while the other two remain active;
   preserve and reconcile their failed/uncertain journals with no model replay.
   During already-budgeted initial work, one dedicated-consumer restart may test
   reattachment to the same owned execution; it must not create a second turn.
   If timing cannot establish the intended overlap within the existing allowances,
   report the gate as unverified. Hypothesis: cancellation is local, process/lease
   recovery is durable, and ambiguous work cannot be committed or acknowledged twice.
4. **Claude contract, at most two attempts and five minutes.** After the successful
   Codex cohort, exercise a minimal synthetic developer/check/reviewer contract with
   the already pinned Claude and its existing profile. Record actual model/session
   metadata, useful output, exit/cancellation behavior and capability support. Do
   not count installation/auth status as successful native Claude execution.
5. **Assessment and shutdown.** Read API events/artifacts, Redis pending/ACK state,
   owned process identities, journal fences, locks and Git evidence. Correlate
   run/execution IDs with the existing UI/SSE and OTel/Langfuse path; test redaction
   using synthetic sentinels. Preserve cancelled/failed/uncertain evidence. Stop only
   recorded acceptance sessions, prove child groups dead and locks reacquired, and
   leave readiness false unless the full matrix below has evidence.

The ten-turn Codex allocation is three initial developers, one repair, three
independent reviewers and three fault-case developers. It is a maximum, not a
requirement to spend the whole allowance after a failure. Integration/check stages
must use their existing deterministic contracts; they receive no extra model turn.

## Whole-MVP evidence matrix

The source [SPEC](../SPEC.md) and [product acceptance matrix](product.md#acceptance-matrix)
remain authoritative. This bounded Python cohort cannot by itself satisfy unsupported
Node/build routes or all provider/UI/deployment gates.

| SPEC gate | Required evidence before readiness |
| --- | --- |
| A1, W1 | Reproducible local startup; exact pins; dedicated UID/ext4 paths; both CLI health and authorization results |
| A2 | Actual project/task creation, or validated structured decomposition and approval |
| A3 | UI edit/validation/publication; a run keeps its immutable workflow version |
| A4, W4 | Three overlapping native executions, distinct cwd/branches, dependencies respected, main unchanged |
| A5 | Both Codex and Claude selected through the common contract and actual supported native execution |
| A6, A7, W7 | Passing exact-tree tests and independent review, task commits, separate integration branch; conflicts preserve main and task branches |
| A8, W2, W3 | Pause/resume/cancel, bounded retry/timeout and restart reconciliation; whole child group stopped; no duplicate turn/commit |
| A9 | Immutable assignments plus actual allowlisted skills/tools/MCP use and audit evidence |
| A10, W8 | UI/SSE replay and trace links correlate the submitted run through execution and Git completion; measured event latency |
| A11 | Enforced concurrency/time/step/attempt/output/disk limits; unavailable usage/cost remains unknown |
| A12, W5 | Synthetic-secret redaction in API/logs/traces; private auth paths unreadable; no credential/Docker socket mounts |
| W6 | An actual external-origin denial test for the current host bindings, without changing listeners or firewall |

Previously completed source/mock/browser checks may support their specific gates;
they must not be relabelled as new native queued acceptance. Record unresolved gates
individually. An auth, schema, transport, tool, check, review, commit or integration
failure is reported at that exact phase, with durable cleanup and remaining budget.

## Regression rollback

If installation parity fails, restore only the verified `0dd5ac7` worker wheel in
the stopped venv and verify its hashes/dependencies. If a live regression occurs,
first stop only owned candidate sessions and retain new SDK/journal state, then
apply the same package rollback. Do not restore profiles, secrets, database or Redis
data over current state. Leave provider/consumer stopped and report the actual
installed pin, reconciliation state and readiness. A failure to prove quiescence
stops rollback mutations rather than guessing process ownership.
