# ADF shared contract sources

This directory is owned by the umbrella, not a fifth deployable repository.

- [Workflow JSON schema](workflow.schema.json): shape/vocabulary, semantic validation required.
- [Execution request](execution-request.schema.json): private versioned worker job; path allocated by key.
- [Normalized worker event](execution-event.schema.json): bounded event envelope, not the full domain event registry.
- [OpenAPI draft](openapi.json): public/internal route baseline and core request types. Detail response schemas, per-node config schemas, internal bodies and multipart uploads are deliberately incomplete pending E1/E2.
- [Fixtures](examples/workflow.json) and [mock job](examples/execution-request.json): offline examples; zero SHA is a fixture, never a real execution base.

Draft contracts do not claim a working API. API app OpenAPI currently describes diagnostics only. Generate clients/models in implementation from pinned umbrella sources, record the contract hash, and test compatibility. Python validation tooling: `python -m pip install -r requirements-dev.txt` at umbrella, then `python scripts/verify.py`. Future schema changes must include semantic/compiler and client tests.
