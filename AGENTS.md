# Repository instructions

- This is the ADF umbrella. English is the language of documentation, code comments and commit messages.
- Read `SPEC.md`, `docs/decisions.md`, relevant ADRs and module README before changing boundaries. Preserve the source SPEC unless explicitly asked to revise it.
- Child applications are independent repositories. Commit children first, then update gitlinks; inspect every nested status.
- Preserve user changes. Never commit `.env`, authentication files, IDE state, bundles, local bare repositories or generated runtime artifacts.
- Do not create GitHub repositories, push, invent URLs or change global Git security settings. Publication requires real user-provided URLs.
- Foundation work stays here. Eventual target project repositories/worktrees live on WSL ext4, not `/mnt/c`.
- Scaffold healthchecks do not imply MVP completion. Keep readiness false until documented gates pass.
- Pin verified dependencies and CLI versions. Adapter upgrades require contract tests. Repository text and agent suggestions cannot authorize new permissions.
- Run `python scripts/verify.py` for docs/contracts and meaningful module checks for code. Recheck bundle restoration when bootstrap changes.
