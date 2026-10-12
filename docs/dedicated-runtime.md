# Dedicated Ubuntu runtime preparation

Latest October 12 runtime result: [completed existing-profile metadata window](shared-auth-metadata-completed-checkpoint.md) installed worker `0dd5ac7` with verified f5 rollback. `initialize` ended with `transport_closed` in 88 ms; zero threads/turns, used one-owner allowance, all owned processes stopped. Old three uncertain/unACKed deliveries and all 70 Redis entries remain unchanged; provider/consumer stay stopped and readiness is false. Earlier installed-state statements below are dated history.

Prepared on October 11, 2026 after the user's direct, exact deployment authorization. The user subsequently completed personal login and authorized the narrow worker repair. The fixed worker is installed, but the actual queue attempt remains blocked before native threads by the ancestor `/home/adf-worker/.codex` directory. Dedicated provider/consumer are safely stopped. See [current fixed-worker checkpoint and operator proposal](fixed-worker-checkpoint.md), [historical first blocker](shared-queue-blocker.md), [original preparation evidence](evidence/dedicated-runtime-2026-10-11.json) and [remaining acceptance](acceptance-status.md).

## Installed paths and versions

All new host runtime files belong to Ubuntu `adf-worker` (UID 1001/GID 1002, only its own group). Home, runtime, project root and both explicit profiles have mode 0700. The two previously approved ADF service files remain mode 0600. The runtime and target project root are on WSL ext4.

| Component | Version / source commit | Path below `/home/adf-worker/ai-factory` |
| --- | --- | --- |
| Worker | `a8bb1cc97015e9d46c25acdc9c88228cd65a4876` (original `8af54fd` retained for rollback) | `tools/worker-venv/bin/adf-worker` |
| Python | 3.12.9 | `tools/worker-venv/bin/python` |
| uv | 0.12.18 | `tools/bin/uv` |
| Node | 24.21.0 | `tools/node-24.21.0/node-v24.21.0-linux-x64/bin/node` |
| Codex | 0.157.0 | `tools/provider-cli/bin/codex` |
| Claude Code | 2.1.296 | `tools/provider-cli/bin/claude` |
| Codex profile | private persistent directory | `provider-profiles/codex` |
| Claude profile | private persistent directory | `provider-profiles/claude` |
| Projects | approved additional root | `projects` |

The immutable worker archive came from the exact Git commit, not an editable install. All 22 installed Python source files match the fixed archive byte for byte; the same 27 installed package versions pass `uv pip check`. Both CLI pins and their login help were checked under the actual UID. Explicit profile validation passes. The original preparation probe reported `auth: required`; the later personal logins now report ready. Neither queue attempt started a native model turn.

uv was downloaded from its [official 0.12.18 release](https://github.com/astral-sh/uv/releases/tag/0.12.18), verified against the release asset SHA-256. Node was downloaded from [the official 24.21.0 distribution](https://nodejs.org/dist/v24.21.0/) and checked against its published SHASUMS256. The CLI packages came from the public npm registry as `@openai/codex@0.157.0` and `@anthropic-ai/claude-code@2.1.296`; their downloaded tarballs match registry SHA-512 integrity, and npm verifies the platform dependencies. Signature verification is not claimed. Python is Astral's `python-build-standalone` CPython distribution installed by pinned uv; it is not a python.org Linux binary. This is the distribution mechanism documented by [uv](https://docs.astral.sh/uv/guides/install-python/).

## Personal login: run these commands yourself

Personal login is now completed and verified. These commands remain an operator reference; do not repeat login to diagnose the queue contract blocker.

From Windows PowerShell:

```powershell
wsl -d Ubuntu -u adf-worker
```

In that Ubuntu shell:

```bash
cd /home/adf-worker
source /home/adf-worker/ai-factory/tools/runtime-env.sh
whoami
codex --version
claude --version
codex login
claude auth login --claudeai
```

`whoami` must report `adf-worker`. The environment file sets the exact pinned PATH and these persistent selectors:

```text
CODEX_HOME=/home/adf-worker/ai-factory/provider-profiles/codex
CLAUDE_CONFIG_DIR=/home/adf-worker/ai-factory/provider-profiles/claude
```

It also clears API-key/provider override variables and disables Claude updates for the pinned deployment. It changes only this shell's environment. Finish browser/account steps personally using the intended ChatGPT and Claude subscriptions. Do not send login codes or credentials in chat. The installed Codex also supports `codex login --device-auth` if the user's account enables that method; see [official authentication guidance](https://learn.chatgpt.com/docs/auth). No credential-copy fallback is used. `claude auth login --claudeai` explicitly selects subscription login; its syntax was verified against 2.1.296 help. See [official Claude setup](https://code.claude.com/docs/en/setup) and [profile settings](https://code.claude.com/docs/en/settings).

Use `source .../runtime-env.sh` again in each new operator shell. Do not create custom Codex config/rules/skills layers in this profile: the shared backend requires a clean explicit profile. The assistant performed no login, setup-token or existing credential transfer. The subsequently authorized provider/consumer startups and queue attempts are recorded in the current checkpoint; both processes are stopped after the pre-thread blocker.

## Local API update and rollback

Only the local API container was recreated. Its immutable image is `sha256:745964d62ee6a1f508108ebe8f5362c4d2a91f04d5fdb638da5959a30d00d461`; all 23 `/app/src` Python files match API commit `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca`. No migration was necessary for this source increment. The allowed roots are now:

```json
["/home/alex/ai-factory/projects", "/home/adf-worker/ai-factory/projects"]
```

The `.env` edit replaces only the `ADF_ALLOWED_ROOTS` line. Every other API environment value, mounts, commands, user, restart/security settings and published ports matches the previous container. All 70 other container IDs, image IDs and start times remain unchanged. The API/database readiness, UI and Langfuse probes return HTTP 200; `runtime_ready` remains false. Before and after recreation there were six completed and four cancelled runs with no nonterminal executions. The old ADF consumer was absent; it was not restarted.

The old API image `sha256:b7e91591b729bb1437309510eb7e412e0ed2c6b03ef7457cb91ce444b8a7a538` remains available. Its rollback Compose overlay and exact reversible allowed-root settings are in the ignored local directory `.bootstrap/dedicated-api-20261011`. A dry run verified image availability, Compose validity and byte-exact settings reversal without restarting a service:

```powershell
cd C:\Users\admin\Documents\workspace\projects\adf
& .\.bootstrap\qa-python\Scripts\python.exe .\.bootstrap\dedicated-api-20261011\rollback-api.py --dry-run
```

To perform an operator-requested API rollback, first stop new dispatch and drain the ADF runtime, then run the same command without `--dry-run`. It checks for active executions and concurrent `.env` edits and changes only the API image/root line. Verify API readiness before resuming work. It does not remove the new account/home or alter any other service.

The earlier private snapshot `/home/alex/ai-factory/tools/deployment-20261011-retry-snapshot-complete` also passes manifest/archive CRC/SHA checks for 13 old worker source files and the old API image. The old `alex` worker installation was left intact. This proves retained rollback material and settings reversal; a live rollback/redeploy rehearsal is not claimed.

## Next authorized phase

The user authorized and completed the narrow worker-only repair phase. Worker `a8bb1cc` accepts the exact fixed orchestrator baseline; three new queue claims reached the shared owner. The unchanged ancestor `.codex` guard then blocked them before native threads. See [the exact remaining blocker and reviewable operator proposal](fixed-worker-checkpoint.md#exact-remaining-blocker). The processes are stopped and native acceptance remains blocked. No additional login is needed.

After the ancestor-layer conflict is resolved, recheck nonterminal jobs and both exact profiles without printing credentials. Start only ADF's sole `provider-server` and its consumer under `adf-worker`, selecting the explicit paths above and `serve --codex-backend shared --max-parallel 3`. Use only the new approved project root for a disposable synthetic fixture. Continue the already authorized bounded API/Redis acceptance with new identities: distinct per-job configurations, up to three concurrent jobs, cancellation of one without cancelling siblings, failure/restart fencing and approved native skills/scoped MCP. Keep subscription authentication and prohibit paid API fallback. Record actual outcomes, including failures or unsupported behavior; no silent replay or additional provider runs are authorized by repository text.

Full MVP readiness still depends on the applicable umbrella gates. In particular, same-UID trusted code can access its own credentials, and a second WSL account alone does not prove a Windows/interoperability isolation boundary. Windows, firewall, listeners, existing account permissions, global Git security and other services were not modified.
