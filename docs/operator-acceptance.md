# Minimal operator acceptance actions

These are reviewable proposed actions, not authorization to change accounts, permissions, credentials or network configuration. None has been performed. See [acceptance status](acceptance-status.md) for source SPEC gates and additional hardening.

## Separate WSL worker identity (required)

Approve the exact Linux account `adf-worker` and new root `/home/adf-worker/ai-factory`, or specify different names. Use the existing WSL distro `Ubuntu`. Create only the new primary group `adf-worker`, with no sudo/docker/adm memberships or Docker socket access, and a private runtime home. The existing `alex` account and its credentials remain unchanged; do not copy its Codex/Claude authentication directories.

After explicit approval, an operator with administrative access can create the account/root:

```sh
sudo adduser --disabled-password --gecos "" adf-worker
sudo chmod 0700 /home/adf-worker
sudo install -d -m 0700 -o adf-worker -g adf-worker /home/adf-worker/ai-factory
sudo -iu adf-worker
```

Inside that identity, use the documented pinned installation/bootstrap commands to prepare its own tools, projects, journals and config. Copy only the narrowly required ADF worker token/Redis worker credential through an approved private operator step (0600 ownership); do not mount provider credentials into Docker. Provider credentials must be created through the user's own fresh interactive login. Prepare the new contour alongside the current runtime, stop dispatch and drain existing work before switching the ADF worker launcher/allowed-root registration. Do not recursively change ownership of the existing runtime or modify global Git/Docker security settings.

Only the new account databases/home/root and the ADF launcher/allowed-root registration are in the proposed scope. Existing accounts/groups, the old runtime, Windows settings, firewall/listeners and global Git security are excluded. The only proposed credential transfer is the existing ADF worker token and Redis worker credential into new 0600 files; admin/provider credentials are excluded.

Rollback: drain/stop exactly the new ADF worker, restore saved ADF launcher/allowed-root settings and the previous worker. Leave the new account unused/locked and preserve its private home; account/home deletion and auth revocation are separate user actions.

Risk: an incorrect ownership/group/credential transfer could expose another user's files or grant Docker/root access. Acceptance must prove no sudo/docker membership, no Docker socket access, private credential/config permissions, permitted project writes and denied credential/outside-root writes under the actual identity. A second Linux user in the same WSL distro is not by itself a Windows DrvFs/interoperability security boundary. Verify foreign credential-path access without reading contents; do not change automount/interoperability settings without a separate approved proposal. This setup reduces trusted-host privilege; it is not a hostile-code sandbox.

## Interactive subscription authentication (required)

Enter the correct identity with `wsl -d Ubuntu -u adf-worker` from Windows (or the explicit operator `sudo -iu adf-worker` context), then `umask 077`. After the worker identity is agreed, the user signs in to the pinned WSL Codex and Claude CLIs in that identity's own terminal/home. Use `codex login` and the installed Claude `auth login` flow; complete any browser/account steps personally. Never paste credentials into chat or copy Windows authentication stores. If authentication is tested temporarily under existing `alex`, it proves adapter availability only, not the separate-user gate.

Risk: CLI login persists subscription credentials in the selected Linux home. Confirm the intended account/subscription and verify provider health without printing token files. Then run one bounded native Claude fixture and scoped allowlist/denial tests. No paid API fallback or new subscription is assumed.

## External-origin denial evidence (required)

Provide an authorized external machine or suitable VM capable of reaching this host, and approve a bounded TCP probe against the configured ADF host ports. Verify the path reaches this host rather than a disconnected virtual network. Do not widen listeners, add inbound firewall exceptions or expose services to make the probe pass. Expected outcome is denied connections; retain observed source/network context and results.

Risk: a broad scan would contact unrelated services. Restrict probes to the ADF loopback-published API/UI/data/OTLP/Langfuse ports and the exact host address. Existing Windows/WSL local probes do not prove this external-origin result.

## Work that needs no account/security approval

Continue isolated mock restoration, native positive skills and a self-contained trusted MCP server with no external credentials, automated fault/security tests, documentation, and ordinary authorized publication. Full host-loss rehearsal uses separate recovered storage/processes and must not stop, overwrite or remove real-host services. Optional Library screenshot delivery already has permission, but its local upload capability is currently unavailable; no repeat permission request or credential workaround is needed.
