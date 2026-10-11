# Fixed worker installation and remaining shared queue blocker

Subsequent authorized action: [the exact preserving rename and resumed test](shared-resumed-checkpoint.md) completed. The proposal below is now historical: the backup exists, `HOME/.codex` remains absent, one native turn was cancelled with closure proof, and two pre-thread failures reveal a different explicit-profile `config.toml` guard blocker. Installed `a8bb1cc` and the guard are unchanged; services are stopped and native acceptance remains incomplete.

Source-only follow-up: worker `859cc5341643d2031a622e662dbaf23be2c5badb` repairs [explicit diagnostic profiles](doctor-profile-repair.md) with 158 passing tests and successful CI. The execution venv described here remains `a8bb1cc`; it was not replaced. Use the installed shared preflight for the current acceptance, not its old unprofiled doctor. The operator rename remains pending and no new model call occurred.

October 11, 2026. This is the current runtime checkpoint and supersedes the deployment/repair proposal in [the first queue failure](shared-queue-blocker.md). [Sanitized evidence](evidence/worker-fixed-queue-2026-10-11.json) records installed bytes and the actual second queue attempt. Native acceptance and whole MVP readiness remain false.

## Published and installed repair

The user explicitly authorized replacing worker `8af54fd` with the narrow repair and continuing the same bounded test. Worker **`a8bb1cc97015e9d46c25acdc9c88228cd65a4876`** is committed, published to the existing [adf-runtime-worker repository](https://github.com/alex-kzr/adf-runtime-worker), and installed at `/home/adf-worker/ai-factory/tools/worker-venv` from an immutable Git archive. All 22 installed Python files match that archive; all 27 package versions are unchanged and `uv pip check` passes. [Exact-commit hosted CI](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38142701138) succeeds. Linux pytest passes 146 tests; Ruff, strict mypy (22 files), and Bandit medium/high checks pass. The umbrella contract test binds the fixture to the actual pinned orchestrator request builder.

Only the exact ordered legacy selector list `PATH, HOME, LANG, TERM` is normalized to an empty per-job selector list for shared Codex. Values are never forwarded. The single owner continues using its fixed sanitized HOME/PATH and explicit persistent profile. Other nonempty lists, additions, duplicates, reordered lists, secret/profile selectors and value-like entries are rejected before dispatch. No arbitrary environment override or permission expansion was introduced. The API remains `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca`; the orchestrator remains `6fe7c1402864210fd8b6c2aed44695436c147f3f`.

The fresh drain and retained API rollback dry run passed before installation. The verified original source remains at `tools/worker-source-8af54fd`, with package hashes and unchanged dependency versions in private `tools/worker-rollback-a8bb1cc.json`. The new source snapshot is `tools/worker-source-a8bb1cc`. No authentication data was included in either source/rollback snapshot.

## Actual bounded queue attempt

Only the dedicated provider-server and consumer were started with the exact Codex/Claude profile selectors, `--codex-backend shared` and `--max-parallel 3`. Shared health/authentication was ready. The user does not need to log in again.

A new local ext4 fixture `/home/adf-worker/ai-factory/projects/shared-acceptance-parallel-20261011` has no remote and contains only synthetic marker files and a registered JSON check. Its initial main SHA is `b7ab0053ffb5391425d36a18c193ff43ae3c820b`. Three separately approved runs each receive a distinct native skill hash, exact scoped MCP server/read path, immutable developer configuration and expected output path. Every run creation was repeated with its original idempotency key and retained one ID. Policies permit at most three jobs, zero retries, a three-minute execution deadline, and no push/sudo or paid API fallback.

| Scope | Run | Actual final state |
| --- | --- | --- |
| alpha | `57de55ae-007f-431a-b2cc-33f96b4b78fd` | failed |
| beta | `2c6b4b17-c90d-4d22-921f-aefd64b648ce` | failed |
| gamma | `847e2651-17f1-46fd-b942-8eaaa1d83117` | cancelled after the stop-on-blocker request; its execution failed before thread creation |

All three real queue claims reached the shared owner. The environment normalization therefore resolved the first blocker. Each accepted execution then failed the unchanged permission guard with `PERMISSION_DENIED`, before `thread/start`. Native thread, turn, model and MCP call counts are **zero**. Skill snapshot transfer and materialization events are observed; native skill consumption is not established. Three consumer slots were assigned, but this does not prove three native jobs overlapped. Active native cancellation, per-thread skills/MCP/settings isolation and active crash recovery were not exercised and are not passed.

## Exact remaining blocker

`clean_config(profile, workspace)` in the worker rejects any ancestor `.codex` directory outside the explicit profile, including directories containing no known policy layer. The conflicting path is **`/home/adf-worker/.codex`**, owned by UID 1001 with mode 0700. Existence checks found none of `config.toml`, `rules`, `skills`, `AGENTS.md` or `environments.toml`. A metadata-only immediate inventory shows one `tmp` entry and no root-level `auth.json` or `credentials.json`; this is not a recursive content/auth audit. File contents were not read. Its presence alone triggers `Shared job cannot inherit project or ancestor Codex configuration`.

The dedicated profiles are separate paths under `ai-factory/provider-profiles`; their personal logins remain intact. The assistant did not read, copy, rename or delete the default `.codex` directory, and did not weaken the guard. Authentication does not authorize changing another authentication/configuration store.

A possible operator remedy is to preserve the whole conflicting directory outside Codex discovery, after explicitly authorizing that exact move or performing it personally. This preserves the worker guard. Its success must be verified after restart; it has not been rehearsed. These commands are a reviewable proposal, **not performed**:

```powershell
wsl -d Ubuntu -u adf-worker
```

```bash
# First ensure ADF dispatch is drained and the dedicated owner/consumer are stopped.
# These exact paths belong to adf-worker; never substitute another user's directory.
if [ -d /home/adf-worker/.codex ] && [ ! -L /home/adf-worker/.codex ] && \
   [ ! -e /home/adf-worker/.codex.adf-backup-20261011 ] && \
   [ ! -L /home/adf-worker/.codex.adf-backup-20261011 ]; then
  mv -T --no-clobber -- /home/adf-worker/.codex /home/adf-worker/.codex.adf-backup-20261011
else
  echo 'Source/destination preconditions failed; nothing moved.'
fi
```

The move preserves bytes and private ownership/mode; it neither copies credentials into the dedicated profiles nor changes another account. Undo only while ADF is drained/stopped and the original destination remains absent, by moving the held directory back. Do not delete it, print its contents or run another login. Check whether native startup recreates the conflicting directory before resuming queued work; if it does, stop and preserve that evidence rather than repeatedly moving it. An isolated pinned `codex --version` probe with a fresh diagnostic HOME and the same explicit CODEX_HOME did not create `.codex` or `tmp`; this does not establish behavior of login status, interactive sessions or app-server startup. Alternatively, a separately reviewed source change could distinguish harmless default state from policy layers, but that needs verified pinned discovery behavior and security contract tests; this checkpoint does not claim such a fix.

After the conflict is resolved, recheck drain, exact installed source/pins and rollback; start only the recorded ADF owner/consumer with the same profiles/shared backend. Continue the bounded acceptance using **new run/execution IDs**. Accepted IDs must never be replayed. Preserve the failed fixture/journals as evidence. Record actual outcomes before changing any readiness gate.

## Safe current state and rollback

All three execution results are durable in API and Redis messages are ACKed. Every accepted job has a `no_thread` quiescence proof; supervisors and their owned sessions are stopped and every worktree lock was reacquired. Fixture main remains unchanged, its default checkout is clean, and temporary native skill materialization is removed. Cancellation was requested for nonterminal synthetic runs when the overlap gate failed. Only the recorded dedicated consumer/provider were then stopped, with native server session shutdown verified. There are no nonterminal executions. API/database, UI and Langfuse public probes return HTTP 200; `runtime_ready=false`. The umbrella verifier passes for 240 source files and its 91-test unittest run finishes OK (four documented platform/opt-in skips).

The fixed worker remains installed and both private subscription profiles remain prepared/authenticated. Other services, users, Windows, firewall, listeners and global Git security were unchanged. The API-only rollback remains available as documented in [dedicated runtime preparation](dedicated-runtime.md#local-api-update-and-rollback). Umbrella checkpoint `09a7daa0dd1bedaedf1870f10f52d74c2ee4d593` has [successful hosted CI](https://github.com/alex-kzr/adf-meta/actions/runs/38144214433); a fresh recursive GitHub clone resolves all four exact gitlinks, passes the verifier for 239 committed source files and the actual orchestrator compatibility test. The local verifier's 240-file count includes locally present ignored source text; it is not the committed-file count. Bootstrap code was unchanged.

To revert the worker during an explicitly requested, drained/stopped rollback, use the retained source rather than a mutable checkout:

```bash
source /home/adf-worker/ai-factory/tools/runtime-env.sh
uv pip install --python /home/adf-worker/ai-factory/tools/worker-venv/bin/python \
  --no-deps --reinstall-package adf-runtime-worker \
  /home/adf-worker/ai-factory/tools/worker-source-8af54fd
uv pip check --python /home/adf-worker/ai-factory/tools/worker-venv/bin/python
```

Verify all installed Python hashes against the retained rollback manifest before restarting. A live rollback rehearsal was not performed. The old version reintroduces the documented environment incompatibility, so reverting it is not a successful shared acceptance.
