# Minimal operator acceptance actions

This document distinguishes completed explicitly authorized provisioning from remaining proposals. It grants no permission to change accounts, permissions, credentials or network configuration. See [acceptance status](acceptance-status.md) for source SPEC gates and additional hardening.

## Separate WSL worker identity (required)

Completed on October 11 after the user's direct exact-scope authorization: Ubuntu account `adf-worker` (UID 1001/GID 1002), only primary group `adf-worker`, and `/home/adf-worker`, `/home/adf-worker/ai-factory`, `/home/adf-worker/ai-factory/config` owned by that account with mode 0700. Exactly `/home/alex/ai-factory/config/worker-token` and `redis-worker-password` were copied to its config with the same filenames, new ownership and mode 0600. No secret values/hashes were printed or recorded. Existing users/groups and source files remain unchanged; no Codex/Claude/Windows/admin authentication was copied. See [evidence](evidence/publication-account-2026-10-11.json).

The account password remains locked. Actual-UID verification reports only group `adf-worker`, denied noninteractive sudo listing and denied Docker socket access. Do not repeat account creation or credential copying. No pinned tools, provider profiles or runtime processes have yet been installed in the new account.

The remaining deployment proposal prepares the locked worker `8af54fd` directly in `/home/adf-worker/ai-factory/tools/worker-venv`, pinned CLIs and private persistent profiles outside projects/worktrees, for example `/home/adf-worker/ai-factory/provider-profiles/codex` and `provider-profiles/claude`. Shared Codex refuses config/rules/skill layers in its explicit profile; do not delete existing profile configuration to bypass that check. Personal subscription credentials will be created only through the user's own interactive login. Prepare the new contour alongside the current runtime, retain rollback, stop dispatch and drain work before switching only ADF's provider owner/consumer. API deployment targets `a0e0205`; add the exact new project root to `ADF_ALLOWED_ROOTS` while preserving previous roots. Do not deploy an intermediate worker into the old `alex` environment, recursively change its ownership, or modify global Git/Docker security settings.

Deployment/tooling/launcher changes and native model acceptance still require their exact user scope. Existing accounts/groups, Windows settings, firewall/listeners and global Git security are excluded. The two approved ADF service-file transfers are complete; no further credential transfer is proposed.

Rollback: drain/stop exactly the new ADF worker, restore saved ADF launcher/allowed-root settings and the previous worker. Leave the new account unused/locked and preserve its private home; account/home deletion and auth revocation are separate user actions.

Risk: an incorrect ownership/group/credential transfer could expose another user's files or grant Docker/root access. Acceptance must prove no sudo/docker membership, no Docker socket access, private credential/config permissions, permitted project writes and denied credential/outside-root writes under the actual identity. A second Linux user in the same WSL distro is not by itself a Windows DrvFs/interoperability security boundary. Verify foreign credential-path access without reading contents; do not change automount/interoperability settings without a separate approved proposal. This setup reduces trusted-host privilege; it is not a hostile-code sandbox.

## Interactive subscription authentication (required)

The user has explicitly chosen personal login under the prepared new identity. Read [provider identity findings](provider-identity.md) and [shared-provider migration](../services/runtime-worker/docs/shared-provider.md) first. Worktrees do not require per-job login. A shared Codex authority and persistent supported profiles are implemented; no Windows/WSL credential broker or auth migration is implemented. Tool/profile preparation must precede the user's login, so the instructions below are not a request to authenticate before that preparation is approved and completed.

Enter the correct identity with `wsl -d Ubuntu -u adf-worker` from Windows, then `umask 077`. After pinned tools and exact private profile selectors are installed, the user signs in to the WSL CLIs from that identity's own terminal. Use the installed Codex `login` and Claude `auth login` flows with the same `CODEX_HOME`/`CLAUDE_CONFIG_DIR` paths configured for ADF; complete browser/account steps personally. Never paste credentials into chat or copy Windows authentication stores. The worker never initiates login, creates setup tokens or substitutes paid API access. Authentication under `alex` would prove adapter availability only, not this new identity's gate.

Risk: CLI login persists subscription credentials in the selected Linux home. Confirm the intended account/subscription and verify provider health without printing token files. Then run one bounded native Claude fixture and scoped allowlist/denial tests. No paid API fallback or new subscription is assumed.

## External-origin denial evidence (required)

Provide an authorized external machine or suitable VM capable of reaching this host, and approve a bounded TCP probe against the configured ADF host ports. Verify the path reaches this host rather than a disconnected virtual network. Do not widen listeners, add inbound firewall exceptions or expose services to make the probe pass. Expected outcome is denied connections; retain observed source/network context and results.

Risk: a broad scan would contact unrelated services. Restrict probes to the ADF loopback-published API/UI/data/OTLP/Langfuse ports and the exact host address. Existing Windows/WSL local probes do not prove this external-origin result.

## Work that needs no account/security approval

Continue isolated mock restoration, native positive skills and a self-contained trusted MCP server with no external credentials, automated fault/security tests, documentation, and ordinary authorized publication. Full host-loss rehearsal uses separate recovered storage/processes and must not stop, overwrite or remove real-host services. Optional Library screenshot delivery already has permission, but its local upload capability is currently unavailable; no repeat permission request or credential workaround is needed.
