# Security and execution trust

## Threat model

Assets: CLI subscription credentials, local source/Git history, admin/worker tokens, execution ledger, artifacts and telemetry. Threats: malicious repository instructions/tests/hooks, prompt injection, compromised dependency/MCP, runaway subprocesses, path traversal/symlinks, stale worker writes, local webpage attacks and secrets in logs. Local-only is a deployment constraint, not an authentication mechanism.

Host WSL worker is a trusted process. Worktrees isolate concurrent changes, **not hostile code**. Dedicated unprivileged Linux account limits access; credential stores still exist in that account. Autonomous agent/test execution is allowed only for explicitly trusted repos and a tested permission profile. If CLI restrictions cannot enforce a capability, disable it; untrusted code awaits a separate sandbox strategy.

## Permission profiles

The table states policy intent. The adapter-specific paragraph below identifies current enforcement boundaries; it is not evidence of a Codex per-command shell allowlist or a separate host-account security boundary. Unverified provider/account restrictions remain acceptance gates.

| Profile | Allowed | Denied / gate |
| --- | --- | --- |
| observe | Read approved repo snapshot, planner/reviewer structured output | Writes, shell/network beyond explicit tools |
| trusted-development | Approved worktree paths, registered build/test commands, bounded provider network | Default repo/ref writes, credential paths, sudo, arbitrary MCP, privilege bypass |
| integration | Registered Git operations on unique integration ref, registered tests | Default-branch merge/push, arbitrary conflict repair |

Policy binds exact repo/root, path patterns, executable+argv templates, env names, network origins (only where enforceable), MCP/tool allowlist and numeric limits. Execution approval records these versions. Noninteractive adapters return a denial instead of an unanswerable permission prompt. Codex/Claude flags differ; test configured permission modes, not generic assumed parity. Never default to `--dangerously-skip-permissions` or equivalent.

Worker-owned commands use `shell=False` with argv arrays and dedicated process sessions. The native Codex built-in shell remains governed by the verified coarse observe/trusted-development CLI sandbox; it does not enforce an ADF per-command allowlist. Registered ADF tests are separately bound to approved executable/argv templates. The reviewed owned `adf.scoped-files.v1` MCP server enforces exact assigned tools, canonical read paths, byte/time limits and symlink/hardlink denials; generic third-party scope metadata is not accepted as enforcement. Temporary approved native instruction skills are immutable checked bytes; adjacent scripts/assets are not granted execution rights. Source tests, native fixture evidence and queued deployment acceptance are distinct, as recorded in [acceptance status](acceptance-status.md). Registered test commands can themselves run arbitrary code; authorization trusts their repo and dependencies. No textual command denylist is represented as a sandbox. Do not grant Docker socket, sudo or host-wide MCP filesystem access. Workers cannot modify policies to grant themselves rights.

## Paths and Git

Canonicalize real paths; enforce ext4 allowed roots; reject symlink escape and mismatched repo/worktree/branch/base IDs before each operation. One supervisor lock per write worktree, serial project/ref Git mutations. Git hooks/config, submodules, LFS and package install scripts can execute code; inspect/authorize explicitly. Nested target submodule mutations are outside MVP.

Worker alone stages reviewed files after secret scan; generated env/key/cache artifacts are denied. Preserve user dirty base state, never force/reset default refs. Terminal commits/artifacts and stopped process are prerequisites to worktree cleanup.

## Credentials and network

Codex/Claude authenticate interactively in WSL under worker user. Do not copy auth homes to Compose/DB/bundles. Subscription use depends on actual terms; mock is always available. Runtime does not require an API-key-paid replacement. Admin/worker/DB/Redis/Langfuse credentials are separate, locally generated, excluded from Git, mounted as files where supported and rotated independently. No secrets in frontend build variables.

API/UI/Redis/DB/OTLP bind loopback; orchestrator has no public ingress. Verify Windows/WSL listeners and external-host denial. No 0.0.0.0 host exposure fallback. If WSL localhost path fails, explicit configured gateway plus firewall restrictions require a verified operator choice. Internal container binds can use 0.0.0.0 behind loopback-published host ports.

## Privacy and enforcement

Redact before writing logs/artifacts/events and before export. Default traces exclude prompts/code/env/stdout/tool args. Use field allowlists and sentinel-secret tests; regex alone is insufficient. Limit output/disk/time/steps (if observable), redact errors, no raw config dump/authorization headers. Access artifacts via opaque keys and safe attachment handling. Skill/MCP definitions are trusted versioned hashes; repository content cannot add tools or override higher-level policy. Audit approval/config/denial/lease/control/Git operations.

Stop on quota overflow, adapter auth/policy failure, uncertain ownership or stale lease. Validate independent server/worker enforcement. Before enabling real execution, pass threat/permission tests and explicitly record residual host trust limits from [decisions](decisions.md).
