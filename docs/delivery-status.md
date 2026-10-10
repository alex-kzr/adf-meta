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
- Four child repos have root commits, main branches, real local bare origins and absorbed Git directories; .gitmodules has local URLs and umbrella index has exactly four 160000 gitlinks.

Final static verification passed for 78 source files: all relative Markdown links, Python AST/TOML/JSON, schema fixtures, OpenAPI local references, gitlinks and heuristic tracked-secret checks. Git diff whitespace checks passed. Mock-produced envelopes also validated against the event schema and contained no prompt/environment payload.

## Remaining implementation and environment limitations

No Docker daemon was available; images, container builds/startup, authenticated DB/Redis connectivity, network-isolation smoke tests and actual Collector config execution are not validated. No subscriptions/auth stores were accessed; CLI terms, concrete permission/auth capabilities and live compatibility remain gates. No real LangGraph scheduling/checkpointing, supervisor, worktree execution, CRUD, migration, SSE or paid provider is implemented. The static secret check is heuristic, supplemented by tracked-file inspection, not an exhaustive security audit.

No GitHub repository was created and no push was performed. Local runtime/build/QA/bundle artifacts and IDE state stay ignored. Before publication, a remote recursive clone cannot locate ignored local bare origins; use the documented bundle bootstrap, then publish modules before the umbrella.

## Repository and offline evidence

| Repository | Initial commit |
| --- | --- |
| adf (umbrella) | `11d827a97645c064546ec4e121bd8445db4833f0` |
| adf-web | `71ae0bb8f3134ef63ddaa130e0e8913e2c6cd18f` |
| adf-api | `d40aab3ff49b5137ad8314eda767c0857a4f6509` |
| adf-orchestrator | `d9863e371877a272a27c42a6bc64a1decc1a1da7` |
| adf-runtime-worker | `86491fae34f9165ff2ad6322810f79ef1ad7a6b3` |

After the umbrella initial commit, clean-state export produced five self-contained Git bundles with SHA-256 manifest. Exact pins restored successfully in a fresh OS temporary directory; static verification passed in the restored checkout. A separate recursive clone from the original local umbrella also restored the same four module pins and passed static verification. A modified checksum failed before any destination was created. This report is a follow-up documentation commit; final export is regenerated after it so the delivered manifest points to the final umbrella HEAD rather than the initial report snapshot.

Original verification directory: `C:\Users\admin\AppData\Local\Temp\adf-foundation-i54zpwph`. Ignored `.bootstrap/verification.json` stores machine-readable checks. Bundles/manifest are in `.bootstrap/export/`; they are generated delivery artifacts and deliberately absent from Git. Local-only origins remain real bare repos; umbrella has no origin. All source/documentation changes are committed locally; generated files and existing IDE state remain ignored. No push, remote repository creation, global Git security change or credential modification occurred.

Windows-only read-only version probes observed Codex CLI 0.162.1 and Claude Code 2.1.296. These observations do not validate WSL installations, authentication, subscription permission or live adapter behavior.
