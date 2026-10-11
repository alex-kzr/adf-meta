# Shared native read source release checkpoint

October 11, 2026. Source publication only. [Current policy, evidence and exact future deployment scope](shared-native-read-policy.md), [ADR 009](adr/009-operator-owned-native-read-policy.md) and [worker manifest contract](../services/runtime-worker/docs/native-read-policy.md) define this release. Earlier checkpoints retain historical source and runtime results.

## Repository pins

| Repository | Exact source commit | Change |
| --- | --- | --- |
| adf-runtime-worker | `f5a713a3df44ffdad58aaa80fc3a36157e6c2736` | Mandatory operator named native-read policy, durable skills/MCP reconstruction, generation/Git fences and synthetic native regressions |
| adf-api | `a0e0205e85bd5e8f9c0d69d9316b7303f6add8ca` | Unchanged |
| adf-orchestrator | `9932a87e676b651c7ff2eb89246b900c6d0f843e` | Unchanged |
| adf-web | `92bfa64f38202872dbf2999d9343884a12036959` | Unchanged |

The umbrella commits English documentation/evidence and the child gitlink after the worker. The final delivery gives its exact commit and CI receipt, avoiding a self-referential commit hash. Worker [exact-commit workflow](https://github.com/alex-kzr/adf-runtime-worker/actions/runs/38173696418) contains the static, complete Linux and pinned public native-canary gates; publication alone does not establish workflow success or native runtime acceptance.

## Local checks and independent review

The complete worker suite passes **356 Linux tests, zero skips** in a fresh private temporary environment with copied public pinned QA dependencies. Ruff and strict mypy across 29 source files pass; Bandit reports zero medium/high findings (17 low severity findings remain). Umbrella runs 94 tests with four documented Windows/POSIX skips, checks six unchanged API snapshots and validates docs/contracts/gitlinks/SPEC plus heuristic secret patterns. SPEC hash remains `3494049865774af023fa49427feb3f71b8865dc82adcac3d7e5bc6a81cdde5a2`; dependency locks and submodule URLs are unchanged.

An independent read-only source/security reviewer found no remaining blockers after capability reconstruction, permission/account gates, exact sibling masks, private/public-root overlap refusal and native receipt inheritance fixes. Review inspected pinned protocol/tool implementation and synthetic fixtures; it did not execute runtime/model acceptance. [Sanitized verification evidence](evidence/shared-native-read-source-2026-10-11.json) records the source canary and limits.

Actual native ThreadStartParams/Response validate against the pinned generated experimental schema. Real ADF Unix IPC and SCM_RIGHTS carry three temporary allocations; one cancellation leaves two successful siblings. Actual Codex metadata and standalone command probes confirm assigned reads, selected instruction availability, denied private/external/alias/hardlink/sibling paths, denied writes/network, selected-only skill metadata and narrowed `read_marker` MCP inventory. Lifecycle turns/refresh/crash/recovery are synthetic protocol-double tests. Actual native model turn count is zero; no real authorizations or secret contents were used.

The first candidate CI exposed a synthetic namespace placement bug: mounting `/tmp` after binding a `/tmp` test root hid that root. The final test-only correction mounts private tmpfs first and uses a regular CI package installation so owned MCP code is inside the public Python mount. An actual canary in an additional private namespace with `/tmp` roots passes (one targeted test); no existing ancestor layer was removed or bypassed. The complete suite remains required in the final exact-commit workflow.

## Runtime preserved and open gates

Read-only no-follow/no-atime verification matched all 23 installed and retained worker source files to `13c4624a8791fa4c9035c284a4689e412f0b7b42`, with observed file metadata unchanged. Recorded dedicated provider, consumer and native server identities are stopped. Existing Codex/Claude profile directories remain UID 1001, mode 0700; their contents were not read. No runtime source/manifest/config/authentication, existing user/group, Windows, firewall, listener, global Git security setting or other service was changed.

The **legacy secret-read preflight FAILED**. The new **source metadata/command canary PASSED**. Installed subscription/API/Redis acceptance has not been performed. Full native tool-route execution, actual refresh, live failure/recovery and Node/build checks remain gates. Public platform/approved tool content and trusted same-UID mutation limits are explicit. Readiness remains false. A future deployment needs the exact separate scope and public tool inventory; a stopped verified old worker is the safe rollback state.
