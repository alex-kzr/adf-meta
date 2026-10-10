# Foundation delivery status

Date: October 10, 2026. This is a design/documentation/repository foundation, not an MVP implementation.

## Delivered

English documentation covers product/acceptance, four deployment boundaries, agent workflow and hash-bound approval, lifecycle/retries/leases/cancel/recovery, data/API/event contracts, trusted-host security, Langfuse/OTel, frontend, local operations and phased backlog. Five ADRs document significant choices. SPEC.md is preserved with recorded SHA-256 and provenance.

Four independently committed app/service scaffolds are true Git submodules. Frontend builds; API and orchestrator diagnostics remain unready. Orchestrator has basic structural DAG validation only; worker has offline mock/probe only. Draft OpenAPI/schema fixtures are explicitly incomplete for production implementation. Compose is a diagnostic foundation with optional no-export Collector and separate official Langfuse overlay.

## Verified so far

- Frontend TypeScript + Vite production build succeeds; npm audit reports 0 vulnerabilities for the installed lock.
- Six meaningful scaffold tests pass: one API diagnostic HTTP test, three graph invariant tests and two mock adapter contract tests.
- Example DAG validator succeeds; offline mock emits started/completed envelopes without prompt/environment content.
- Core Compose with observability profile parses successfully using .env.example without starting containers.
- Langfuse overlay parses successfully against freshly retrieved official Compose source in ignored QA storage; no stack was started. Current upstream source uses v4 major images; QA candidates are not a deployment pin.
- At the foundation checkpoint, four child repos had root commits, main branches, real local bare origins and absorbed Git directories; .gitmodules had local URLs and the umbrella had exactly four 160000 gitlinks. See the publication update below for current origins.

Final static verification passed for 78 source files: all relative Markdown links, Python AST/TOML/JSON, schema fixtures, OpenAPI local references, gitlinks and heuristic tracked-secret checks. Git diff whitespace checks passed. Mock-produced envelopes also validated against the event schema and contained no prompt/environment payload.

## Remaining implementation and environment limitations

No Docker daemon was available; images, container builds/startup, authenticated DB/Redis connectivity, network-isolation smoke tests and actual Collector config execution are not validated. No subscriptions/auth stores were accessed; CLI terms, concrete permission/auth capabilities and live compatibility remain gates. No real LangGraph scheduling/checkpointing, supervisor, worktree execution, CRUD, migration, SSE or paid provider is implemented. The static secret check is heuristic, supplemented by tracked-file inspection, not an exhaustive security audit.

At the original foundation checkpoint, no GitHub repository was created and no push was performed. Local runtime/build/QA/bundle artifacts and IDE state stay ignored. Before publication, remote recursive clone cannot restore the locally pinned commits; use offline bundle bootstrap, then publish modules before the umbrella.

## Repository and offline evidence

| Repository | Initial commit |
| --- | --- |
| adf-meta (umbrella, originally named adf) | `11d827a97645c064546ec4e121bd8445db4833f0` |
| adf-web | `71ae0bb8f3134ef63ddaa130e0e8913e2c6cd18f` |
| adf-api | `d40aab3ff49b5137ad8314eda767c0857a4f6509` |
| adf-orchestrator | `d9863e371877a272a27c42a6bc64a1decc1a1da7` |
| adf-runtime-worker | `86491fae34f9165ff2ad6322810f79ef1ad7a6b3` |

After the umbrella initial commit, clean-state export produced five self-contained Git bundles with SHA-256 manifest. Exact pins restored successfully in a fresh OS temporary directory; static verification passed in the restored checkout. A separate recursive clone from the original local umbrella also restored the same four module pins and passed static verification. A modified checksum failed before any destination was created. This report is a follow-up documentation commit; final export is regenerated after it so the delivered manifest points to the final umbrella HEAD rather than the initial report snapshot.

Original verification directory: `C:\Users\admin\AppData\Local\Temp\adf-foundation-i54zpwph`. Ignored `.bootstrap/verification.json` stores machine-readable checks. Bundles/manifest are in `.bootstrap/export/`; they are generated delivery artifacts and deliberately absent from Git. At that original checkpoint local-only origins were real bare repos and umbrella had no origin. The publication update below supersedes that configuration. All source/documentation changes are committed locally; generated files and existing IDE state remain ignored. No push, remote repository creation, global Git security change or credential modification occurred.

Windows-only read-only version probes observed Codex CLI 0.162.1 and Claude Code 2.1.296. These observations do not validate WSL installations, authentication, subscription permission or live adapter behavior.

## Publication preparation update - October 10, 2026

The user supplied five exact origins under `https://github.com/alex-kzr/`: umbrella `adf-meta`, modules `adf-web`, `adf-api`, `adf-orchestrator`, `adf-runtime-worker`. All are configured locally; `.gitmodules` uses the four GitHub URLs and submodule sync was run. Read-only anonymous `ls-remote` succeeded for every repository and advertised no refs. No push, remote file/branch creation, credential change or permission change was performed.

Module README publication links are locally committed and umbrella gitlinks updated. Current export names the umbrella `adf-meta.bundle`; bootstrap also accepts old `adf.bundle` manifests. Offline restoration is distinct from remote recursive clone. The latter is a post-publication check and is recorded in the subsequent publication result. See [repository lifecycle](repositories.md) for exact URLs and fail-fast PowerShell push commands. Static checks and current/legacy export restoration results are rechecked during this preparation; generated reports remain ignored.

## One-time publication authorization

The user explicitly authorized publishing this ADF snapshot to the five exact GitHub URLs after local preparation. The prior no-push restriction is overridden for this publication only. No force push, credential creation, permission change or default authorization for future pushes is permitted. Before pushing: verify tracked secrets/artifacts, exact origins/pins, current and legacy offline bootstrap, and remote branch state. Publish children first, then umbrella; check advertised SHA, fresh remote recursive clone and existing CI afterward.

## Published snapshot and verified remote clone - October 10, 2026

Under the user's explicit one-time authorization, ordinary pushes published four modules first and then the umbrella. No force push, remote repository creation, credential setup, permission change or unrelated application implementation occurred. All branches are main; advertised remote SHA matched local SHA after each push.

| Repository | Published snapshot SHA |
| --- | --- |
| [adf-web](https://github.com/alex-kzr/adf-web) | `57df5e8e1fa8ec8719354fa834d92cb8309d5312` |
| [adf-api](https://github.com/alex-kzr/adf-api) | `67f6b665136487a75fe6106fc623dc418c8c9d0e` |
| [adf-orchestrator](https://github.com/alex-kzr/adf-orchestrator) | `3554522f956dc4173bfae8933de9f61bc0464413` |
| [adf-runtime-worker](https://github.com/alex-kzr/adf-runtime-worker) | `f88564cde4ada2542a9cceab3f89909c959f1be8` |
| [adf-meta](https://github.com/alex-kzr/adf-meta) | `8df53ff613321e2e409dd1e255f59fdcfb11f371` |

A fresh **GitHub** recursive clone restored the exact four pinned module commits and a clean umbrella; static verification passed for 78 source files, relative Markdown links, Python/TOML/JSON, schema fixtures, OpenAPI refs, Git pins and heuristic secrets checks. This is separate from the earlier local recursive clone and offline bootstrap. Both current adf-meta and legacy adf exports restored successfully with file-only Git protocols before publication. All reachable published history was checked for suspicious secret patterns and generated/sensitive file paths (116 unique blobs across five repos); no matches were found. Such pattern scans are not an exhaustive security audit.

GitHub REST API reported zero workflows, workflow runs, check runs and status contexts for every SHA in the table. **CI is not configured**; no green CI result is claimed. Foundation build/six scaffold tests passed earlier; no Docker daemon/live CLI/MVP acceptance claim is added by publication.

This report is an additive documentation commit after the verified first-publication snapshot shown above. It is published to umbrella main without changing module pins; the final branch HEAD and clone/CI recheck are recorded in ignored `.bootstrap/publication-validation.json` and can be reproduced through the documented commands. Original working trees remain clean, and local bundles are regenerated for final HEAD. Publication authorization does not extend to future automatic pushes.
