# Shared profile policy release and proposed deployment scope

This source-only release implements [ADR 007](adr/007-sealed-shared-profile-policy.md) and its [worker operator contract](../services/runtime-worker/docs/shared-profile-policy.md). The exact candidate worker is **`13c4624a8791fa4c9035c284a4689e412f0b7b42`**, matching this release's `services/runtime-worker` gitlink. The installed execution worker remains `a8bb1cc97015e9d46c25acdc9c88228cd65a4876`. Real profile/config/auth contents were not read or modified, and no new native/model/queue run occurred during this implementation.

## One concrete deployment approval scope

Authorize installation of **`13c4624a8791fa4c9035c284a4689e412f0b7b42`** into `/home/adf-worker/ai-factory/tools/worker-venv`, followed by restarting **only** ADF provider-server and consumer under `adf-worker`, using `--codex-backend shared`. Keep Python 3.12.9, uv 0.12.18, Node 24.21.0, Codex 0.157.0 and Claude Code 2.1.296, all existing consumer/service credentials and settings. No dependency/tool upgrade, API/web/orchestrator/other-service change, new network listener, account/group, Windows/firewall, Git security or auth provisioning operation is included.

Create only the operator manifest `/home/adf-worker/ai-factory/tools/shared-profile-policy.json`, owned by `adf-worker`, mode 0600, with exactly:

```json
{
  "version": 1,
  "project_roots": [
    "/home/adf-worker/ai-factory/projects/shared-acceptance-resumed-20261011"
  ]
}
```

The provider uses the existing 0700 `/home/adf-worker/ai-factory/provider-profiles/codex`. Its validator may read **only that directory's `config.toml`** internally to classify it against this exact policy, without emitting values. It accepts absence or exactly that trust table; an invalid file stops deployment and is preserved. No config rename/edit/replacement, auth-file inspection/copy, login/setup-token or permission broadening is authorized by this proposed scope. Claude's profile and the preserved `/home/adf-worker/.codex.adf-backup-20261011` remain untouched.

## Drain, rollback and acceptance bounds

1. Recheck API/Redis nonterminal executions and recorded supervisor/provider/consumer ownership before switching. Proceed only with no active jobs/writers. Do not infer safety from an empty process list alone.
2. Retain/verify immutable `tools/worker-source-a8bb1cc`, its installed 22-file source hashes and current dependency inventory/rollback evidence. Save a separate immutable candidate source snapshot; install only that package with no dependency resolution. Verify the candidate's 23 Python source hashes and unchanged dependency inventory. Preserve service files and profile metadata without displaying secrets.
3. Validate the exact private manifest and existing config with the candidate. Start only the dedicated provider owner with `--shared-profile-policy` and the dedicated consumer with its prior settings plus shared backend. Require healthy/authenticated owner, new generation and unchanged config seal before queue dispatch.
4. Reuse the existing synthetic project/clean main fixture, with **fresh run/execution IDs** and no replay of historical attempts. Enqueue at most three concurrent native Codex jobs through existing API approval/Redis paths. Use distinct worktrees/models/approved skills and the owned scoped MCP marker checks; verify cross-job settings/output isolation. No paid API/provider fallback, unrelated repository or new trusted root is included.
5. Cancel exactly one active job and prove its thread/owned writers stop without cancelling its siblings. Inject at most one failure of the recorded dedicated **consumer** while the remaining supervisors run, restart that consumer and verify durable result/Redis reconciliation without repeating native execution IDs. Do not crash unrelated services or mutate the real profile to test drift; source-only doubles cover those drift faults.
6. Verify all bounded jobs reach durable terminal results/ACK or correctly fenced uncertainty, reacquire eligible worktree locks, preserve fixture main and config seal, remove only approved temporary skill/config materialization after quiescence, and record sanitized evidence. A failed gate stops the trial without broadening policy or inventing success. Native MCP/skills/cancel/recovery and MVP readiness remain false until their evidence passes. Accepted native turn counts are observable; exact backend HTTP/model-call counts remain unknown unless independently measured.

Rollback stops/drains only the recorded dedicated sessions and reinstalls the retained exact `a8bb1cc` package with unchanged dependencies, then verifies hashes and quiescence. Do not start jobs against the rejected configuration with the old guard. Leave provider/consumer stopped if that is the safe previous state. Preserve the new manifest, journals, fixture, config and backup for review; rollback does not silently repair or reauthorize prior-generation outputs.

## Source validation and limitations

234 Linux pytest cases pass under the pinned Python 3.12.9 in a separate QA venv, together with Ruff, strict mypy (23 source files) and Bandit (zero medium/high findings). Independent static re-review found every reported P1/P2 addressed and no new finding in the reviewed patch; it did not independently run the suite or native acceptance. Umbrella local contract tests run 94 cases with four documented platform/opt-in skips. [Sanitized source release evidence](evidence/shared-profile-policy-source-2026-10-11.json) distinguishes these checks from historical native runs.

The worker pin is published to the authorized [adf-runtime-worker origin](https://github.com/alex-kzr/adf-runtime-worker); [its exact-commit CI run](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38153462401) completed successfully. Remote main equals `13c4624a8791fa4c9035c284a4689e412f0b7b42`. The umbrella gitlink advances only after that child publication; source publication does not install or start the runtime.

The implementation uses the owner CLI trust override proven by the pinned upstream no-model research, plus strict validation/sealing if an existing config is present. No new app, schema, broker, secret source or policy-writing daemon is added. Tests use synthetic temporary profiles and fake-provider IPC; installed `a8bb1cc` and actual profile contents are outside this source work. Same-UID hostile mutation is outside the trusted-host boundary; pre/post checks and polling do not create an atomic OS sandbox. Invalid local evidence and retired-generation outputs fail closed, which may require fresh operator-approved attempts.
