# Reliability and lifecycle

| Entity | States and guards |
| --- | --- |
| Task | draft -> ready; ready -> blocked/running/cancelled; blocked -> ready/cancelled; running -> review/failed/cancelled; review -> running (bounded repair)/done/failed/cancelled. done requires final integration. |
| Run | queued -> running/cancelled; running -> paused/completed/failed/cancelled; paused -> running/failed/cancelled; terminal immutable |
| Node | pending/ready/dispatched/running/waiting_approval/retry_wait/succeeded/failed/cancelled/skipped; each attempt immutable; skips only for unselected branches |
| Execution | created/leased/starting/running/validating/committing/succeeded; active -> cancelling -> cancelled/failed/uncertain; uncertain resolved only by evidence |
| Integration | pending/running/passed/needs_resolution/failed; needs_resolution pauses run |

Requested controls are separate monotonic fields. Pause stops dispatch transactionally, lets active work finish and becomes paused when drained. Cancel cannot be cleared by resume; cancelled requires stopped/reconciled descendants. Completion requires all selected nodes/tests/reviews/integration successful and executions terminal.

## Delivery and fencing

1. DB transaction creates execution, stable dispatch/outbox ID and config/policy/base hashes. XADD relay may duplicate.
2. Consumer requests internal API lease; transaction locks execution/checks eligibility/control state and returns owner, monotonic epoch and expiry. DB clock authoritative.
3. Supervisor holds OS worktree lock and journals execution/epoch/process identity before process-group spawn. Heartbeat 10 s, expiry 45 s (calibrate).
4. Events/results carry epoch/idempotency key. API rejects stale owners; unique `(execution_id,epoch,sequence)` deduplicates. Persist the terminal execution result and its event atomically; acknowledge Redis only after the durable terminal response. The outbox reconstructs dispatch delivery, not a separate completion queue.
5. Graph replay consumes existing ledger result. Application DB and checkpointer writes are not assumed atomic; deterministic command IDs deduplicate.

XAUTOCLAIM transfers pending Redis delivery, not execution authority. Retain until durable terminal/no-op. Invalid poison messages get bounded parse/delivery handling and sanitized dead-letter DB record, separate from execution retries. AOF helps; DB outstanding intents reconstruct Redis loss.

**Lease expiry cannot fence a live CLI's filesystem writes.** Mark uncertain; block reassignment; local supervisor must prove old process termination using PID + start time + session/group identity. Retain OS lock across worker restart through supervisor. Unrecoverable journal needs manual recovery. Only then increment epoch/create fresh attempt worktree. Worker losing heartbeat must stop CLI within lease safety margin; stale owner cannot commit or report success. Future systemd supervisor uses `KillMode=control-group`; scaffold does not implement it.

## Retry, control and side effects

| Failure | Policy |
| --- | --- |
| Transient DB/Redis/API | Backoff+jitter capped 30 s, deadline bounded, reuse event keys |
| Rate limit | No implicit switch. Provider-specific normalization and retry-after-aware delay remain unimplemented; current retries use bounded generic backoff. |
| Auth/policy/validation/capability failure | Actionable block/failure, no automatic retry |
| Test/review failure | At most 2 repairs (3 attempts total), fresh attempt worktree, renewed tree-bound review |
| Unknown spawn/commit or lease loss | Reconcile; never blind repeat |
| Integration conflict | Pause; optional one approved isolated repair |

Execution deadline covers retry/test/output drain. Run deadline includes waits unless explicit approval budget says otherwise. Poll cancellation at least every 2 s; Redis wakeups are hints. TERM group, 10 s grace, KILL if required, reap children, persist evidence; output remains bounded. Cancel during commit reconciles any created commit as artifact, but run still cancels.

Journal Git intent: branch/expected base/tree/trailers. After crash inspect HEAD/tree/trailers/sequencer. Matching commit is recorded once; conflicting/multiple candidates pause for resolution. Serialize mutations by project/ref locks.

## Crash checks

| Boundary | Recovery |
| --- | --- |
| Before/after publish | Republish stable ID; lease dedup |
| After claim before spawn | Journal proves no process; safe resume/new attempt |
| After spawn before result | Prove old process dead before replacement |
| Commit before DB result | Discover matching commit, no second commit |
| DB result before XACK | Terminal duplicate is acknowledged |
| DB result before checkpoint | Graph replay reads persisted result |
| Mid cherry-pick | Inspect sequencer/conflicts, preserve branch and pause |

Pause/drain before coordinated DB/Git/artifact backup. Restore disconnected, validate hashes, reconstruct Redis, then enable workers. Credential backup is separate protected storage.

## Manual integration conflict resolution

Keep the conflicted integration workspace, original task branches and supervisor journal. The operator inspects the recorded conflict and fixes only approved files in that held workspace. Verify every staged path is within the approved set and perform the registered secret checks. Commit the resolution locally on the held integration branch using an explicitly configured local identity, then require a clean HEAD/index/worktree. A staged-only tree is not accepted by the current worker.

Submit the exact integration execution and clean HEAD tree through the resolution API, approve the resulting immutable snapshot, then resume. This is an operator continuation of that conflict, not an extra provider repair retry; ordinary retries remain bounded by the original policy. Do not change main, rewrite task refs, edit journals, force-reset, or publish while resolving. The worker verifies the bound tree and runs integration checks without replaying the original conflicting cherry-picks. An approval for another execution or tree must fail closed.
