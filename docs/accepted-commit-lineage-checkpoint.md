# Accepted historical commit import and blocked review checkpoint

October 13, 2026. Published worker `e93f421973e9dda3b9d40a0926d735f8d6ba4c28`
is installed. API `0724e985db016df5e2ebe259f8efe86817b6f44a` and orchestrator
`630b37e44a38f30508fab672630dacf991058beb` retain their previously installed pins.
Only the worker package changed in this checkpoint. Whole-MVP readiness is false.

## Result and boundary

The historical import defect is fixed: a fresh provider generation imports three
previously accepted commits through validation-only authority. It obtains its own
current native receipt rather than forwarding retired grants. Source writer,
immutable approved request, passing exact-tree checks, independent review, separate
successful durable Git publication, parent/tree/trailers and path delta must agree.
Ambiguous, unconfirmed, foreign or tampered sources fail closed. More than one
distinct successful publication journal is refused; retransmission into the same
journal remains supported. Live execution, repair, lease, generation, native-read
and repository-root fences remain mandatory.

Worker `043efe0` implements this validated data import. Worker `e93f421` adds bounded
staged diff and executed check metadata to native review. Neither change establishes
that the full dependent-task review/integration pipeline passes. Historical source
file projection was developed separately but failed independent confidentiality
review and is not committed, published or installed.

See [ADR 010](adr/010-accepted-historical-commits.md) and the worker's
[lineage contract](../services/runtime-worker/docs/accepted-commit-lineage.md).

## Closed runtime windows

| Window | Native turns | Observed result |
| --- | --- | --- |
| Earlier repair/provenance | 13 Codex + 2 Claude | Parallel developers, bounded repairs, capability isolation, cancellation, consumer/provider recovery and Codex/Claude integration observed. Original historical-import refusal retained. |
| `ad9e2321-b060-48a5-ab50-20242b5937d0` | 2 Codex | Historical import, native Developer and registered test pass. Native Reviewer refuses missing baseline/diff/check evidence. No task commit or integration. |
| `8a5ffb22-1f88-4d7d-a19c-f6beb0ee3701` | 1 Codex | Historical import, mock Developer and test pass. Native Reviewer confirms staged diff but refuses missing predecessor contents and sufficient check coverage. No task commit or integration. |

Each new window is closed with zero automatic retries. The last Developer is mock;
its result is not another native coding success. No third acceptance window ran.
Old failed executions were not replayed. The earlier 13-Codex/two-Claude budget,
report, capability and trace evidence retains its original digest. Subscription
CLIs were used without paid API fallback, login, setup-token, authorization copying
or forced refresh. Actual upstream inference count, model identifier and financial
cost remain unknown.

## Unreleased review projection and concrete blocker

The unreviewed change selects only exact changed files from approved historical
commits, verifies the dependency chain reaches the target base, preserves UTF-8
blob bytes, rejects private paths, and applies byte/type/hash bounds. These fences
do not solve arbitrary source-text credential confidentiality. At the end of the first two cycles, independent synthetic
probes exposed sensitive values through three forms: comment-separated implicit
key literals, named Unicode escapes in keys, and escaped serialized JSON within
source strings. No real secret was used in these probes.

Two fresh fix/review cycles failed. The last static checks pass, but final pytest
did not complete; an earlier combined run timed out after 600 seconds and is not
PASS. RED regressions recorded 24 failures/two passes, then 14 failures/two passes.
There is no final independent approval for this projection. Exactly four files,
their hashes and a binary patch are preserved in ignored local
`.bootstrap/accepted-history-blocked-20261013`; a private local stash retains the
same work. The module worktree is clean at the installed/published `e93f421`.
No stash or private ref is included in publication.

The local review workflow requires escalation after two cycles: its Step 7 says
"Maximum 2 fix-and-reverify cycles." The exact operator-local instruction is
`C:/Users/admin/Syncthing/agents/skills/software-development/requesting-code-review/SKILL.md`.
The user authorized exactly one additional focused cycle. That cycle replaced
regex literal matching with bounded token/literal parsing, scanned comments and
decoded serialized strings, and withheld unsupported syntax/partial hunks. The
original six miss probes then passed; the pure sweep passed 50 negative and two
legitimate positive probes, and eight unsupported-boundary pytest cases passed.
Ruff/Bandit passed. Windows mypy reported 73 platform/missing-dependency errors;
no baseline comparison was run and no authoritative Linux GREEN is claimed.

The sole fresh independent review FAILED: signed numeric credential values are
not withheld. Both unary signs, parentheses, signed floats and signed hexadecimal
values bypass the token-immediate-value check. Exact review-context probes export
the synthetic literal with completeness true and all redaction flags false;
unsigned numeric controls are correctly withheld. This can authorize review with
disclosed credential data. The extra cycle ends here; no further fix, Linux QA,
installation or model window ran. Its exact four-file snapshot, patch, safe verdict
and second private stash are retained under ignored
`.bootstrap/accepted-history-extra-cycle-20261013`. The original two-cycle snapshot
is also retained. Neither stash or unsafe source is published.

The narrow implementation follow-up would recognize sensitive-field numeric
expressions structurally, or withhold unsupported sensitive-field expressions, and
add historical/removed regression checks for absence and completeness false. This
is a proposal for a new separately authorized cycle, not an applied correction.

The narrowest proposed confidentiality boundary is to withhold arbitrary source
text entirely, emit only a closed structured projection of validated metadata and
registered check evidence, and continue refusing approval when that evidence is
insufficient. Supporting arbitrary historical-code review would require an explicit
reviewed design for adequate evidence. This proposal is not implemented or verified,
does not complete the pipeline and does not waive any guard. More regex cases alone
do not establish a complete source-text privacy boundary. Keep native review stopped
until the outstanding confidentiality/context decision is resolved.

## Installation, rollback and preserved local state

The final local read-only verifier proves 30 worker modules, 40 RECORD files, 27
unchanged distributions, unchanged configuration/operator seals and original
ownership/modes. Offline candidate/rollback/candidate rehearsal verified rollback
to `043efe0fb2507930128b9864623fd8b3328c7dcc`. Earlier `a342879` recovery artifacts
and all three inode-preserved bytecode caches remain available. No auth was copied.

All six executions in the two new windows are terminal, result/terminal persisted
and Redis ACKed in their durable journals. All 46 worker locks were reacquired.
Owned native sessions, provider server and consumer are stopped. Original main
remains clean at `ff3b0d4703e4b71e42c90b4ac5d22b7c8d5dbb63`; temporary project checks
were restored. No users, listeners, firewall or global Git security settings changed.

The last successful closed-window checks recorded PEL/active/queue zero, 122 Redis
entries, 13 production components (12 running, 11 healthchecked healthy, migrator
exited zero), and exact preservation of 24 other containers against the original
baseline. These are dated results, not a claim about current live services.

During final read-only checks Docker Desktop returned `unable to start`; Redis
returned a connection error. Current API health, queue/PEL counts and other-container
comparison are therefore unavailable. This worker task attempted no Docker/WSL/service restart;
runtime operations stopped. A separate executor owns the separately approved platform
recovery. Its completion and fresh state checks are not confirmed here and remain
necessary before another runtime operation. Do not rewrite the baseline
or infer current queue state from earlier ACKs.

The last closed review trace has 16 real Langfuse v4 observations, unique and
correlated to run/session/trace, with empty input/output/status text. Earlier actual
skills/MCP evidence is preserved; neither new review adds skills or MCP grants.

## Inspection and remaining gates

After platform availability is restored, open the [last failed review run](http://localhost:8088/#/runs/8a5ffb22-1f88-4d7d-a19c-f6beb0ee3701)
and its [Langfuse trace](http://localhost:3000/project/adf-local/traces/8dcc2c2d3fbb270c179538a234d878d6).
The earlier [completed parallel pipeline](http://localhost:8088/#/runs/f3975994-3496-42ec-8ea6-1ad65dace0be)
remains separate evidence. Links contain no tokens; an existing local ADF login is
sufficient when services are available. No repeat provider login or account setup
is needed for this checkpoint.

Review confidentiality/sufficient context and current platform availability remain
open. Whole-MVP gates also include actual external-origin denial on current host
bindings, current UI event-to-screen latency and a supported isolated Node/build
route. Hostile-code isolation and atomic full-host cross-store recovery are additional
unimplemented hardening. Readiness stays false.

[Sanitized evidence](evidence/accepted-commit-lineage-runtime-2026-10-13.json) separates
published source verification, actual failed windows, local durability checks and
unavailable current service checks. Detailed operator reports, wheels, rollback
archives, stash and unreviewed patch remain private ignored artifacts.
