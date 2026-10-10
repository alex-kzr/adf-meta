# ADF shared contract snapshots

The umbrella owns these compatibility artifacts; this directory is not another deployable application.

- [OpenAPI](openapi.json): current create_app export covering public, orchestrator and worker routes.
- [Workflow schema](workflow.schema.json): exported model shape; actual node/DAG semantics require orchestrator validation.
- [Claimed job](execution-request.schema.json): private nonterminal API claim request with trusted snapshots, limits and lease deadline.
- [Worker event](execution-event.schema.json) and [batch](worker-event-batch.schema.json): actual ingestion inputs.
- [Persisted run event](run-event.schema.json): server event-history/SSE data envelope.
- [Offline job](examples/execution-request.json), [worker event](examples/execution-event.json), [run event](examples/run-event.json) and [workflow](examples/workflow.json): synthetic fixtures. Zero Git SHAs never identify an executable repository.

Read [contracts and guarantees](../../docs/contracts.md) before integrating. Some OpenAPI responses remain generic objects; the frontend and worker model implementations are not automatically generated from these files.

Regenerate using the API Python dependency environment:

~~~powershell
services/api/.venv/Scripts/python.exe scripts/export-api-contract.py
services/api/.venv/Scripts/python.exe scripts/export-api-contract.py --check
services/api/.venv/Scripts/python.exe -m unittest discover -s tests -p test_contract_snapshot.py -v
python scripts/verify.py
~~~

The exporter obtains OpenAPI directly from the factory, workflow/event/batch shape directly from model JSON Schemas and the claimed job by composing API model schemas with the authoritative dictionary overlay. The maintained run-event schema describes event_view output. Tests compare generated snapshots and validate actual API-created jobs for all seven operations, replay behavior and worker adapter conversion in isolation.

Schema validation does not authorize execution or establish MVP readiness. Source upgrades require regenerated snapshots and compatibility tests; PostgreSQL/WSL/provider/browser gates remain separate.
