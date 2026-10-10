"""Contract snapshots and actual API claim/event replay; never starts coding CLIs."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar, cast
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker, ValidationError  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "packages" / "contracts"
spec = importlib.util.spec_from_file_location(
    "adf_contract_export", ROOT / "scripts" / "export-api-contract.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Contract exporter module could not be loaded")
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def read(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any], json.loads((CONTRACTS / name).read_text(encoding="utf-8"))
    )


def validate(name: str, document: dict[str, Any]) -> None:
    Draft202012Validator(read(name), format_checker=FormatChecker()).validate(document)


class StaticContractTests(unittest.TestCase):
    def test_examples_and_local_schemas(self) -> None:
        for stem in ("workflow", "execution-request", "execution-event", "run-event"):
            schema = read(stem + ".schema.json")
            Draft202012Validator.check_schema(schema)
            validate(stem + ".schema.json", read("examples/" + stem + ".json"))

    def test_claim_rejects_unknown_operation_missing_snapshot_and_unapproved_write(
        self,
    ) -> None:
        sample = read("examples/execution-request.json")
        for change in (
            {"operation": "run_arbitrary_shell"},
            {"root_base_sha": None},
            {"policy": {**sample["policy"], "approved": False}},
        ):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                validate("execution-request.schema.json", {**sample, **change})
        del sample["project"]
        with self.assertRaises(ValidationError):
            validate("execution-request.schema.json", sample)

    def test_server_and_worker_envelopes_are_distinct(self) -> None:
        with self.assertRaises(ValidationError):
            validate("execution-event.schema.json", read("examples/run-event.json"))
        with self.assertRaises(ValidationError):
            validate("run-event.schema.json", read("examples/execution-event.json"))


class ActualApiContractTests(unittest.TestCase):
    # Runtime imports deliberately span independent repositories with no typing stubs.
    source: ClassVar[dict[str, Any]]
    TestClient: ClassVar[Any]
    Base: ClassVar[Any]
    Run: ClassVar[Any]
    approval_bindings: ClassVar[Any]
    validate_graph: ClassVar[Any]
    Executor: ClassVar[Any]

    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.source = exporter.load_sources()
            ledger = importlib.import_module("adf_api.ledger")
            models = importlib.import_module("adf_api.models")
            validation = importlib.import_module("adf_orchestrator.validation")
            worker = importlib.import_module("adf_runtime_worker.executor")
            fastapi = importlib.import_module("fastapi.testclient")
        except ImportError as exc:
            raise unittest.SkipTest(
                "API/worker dependencies required; use the documented API Python environment."
            ) from exc
        cls.TestClient = fastapi.TestClient
        cls.Base, cls.Run = models.Base, models.Run
        cls.approval_bindings = staticmethod(ledger.approval_bindings)
        cls.validate_graph = staticmethod(validation.validate_graph)
        cls.Executor = worker.Executor

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="adf-contract-")
        self.addCleanup(self.directory.cleanup)
        self.settings = self.source["Settings"](
            admin_token="contract-fixture-admin-" + "a" * 32,
            orchestrator_token="contract-fixture-orchestrator-" + "b" * 32,
            worker_token="contract-fixture-worker-" + "c" * 32,
            allowed_roots=("/home/adf/ai-factory",),
            artifact_root=Path(self.directory.name) / "artifacts",
        )
        self.database = self.source["Database"](self.settings.database_url)
        self.Base.metadata.create_all(self.database.engine)
        self.addCleanup(self.database.engine.dispose)
        check_graph = self.validate_graph

        class LocalValidator:
            def validate(self, graph: dict[str, Any]) -> dict[str, Any]:
                errors = check_graph(graph)
                return {"valid": not errors, "errors": errors}

        app = self.source["create_app"](self.settings, self.database, LocalValidator())
        self.client = self.TestClient(app)
        self.addCleanup(self.client.close)
        self.headers = {
            "admin": {"Authorization": "Bearer " + self.settings.admin_token},
            "orch": {"Authorization": "Bearer " + self.settings.orchestrator_token},
            "worker": {"Authorization": "Bearer " + self.settings.worker_token},
        }
        self.worker_id = "contract-worker"
        self.post(
            "worker",
            "/internal/workers/register",
            {
                "worker_id": self.worker_id,
                "capabilities": {"contract_version": "1", "provider": "mock"},
                "allowed_roots": ["/home/adf/ai-factory"],
            },
            200,
        )

    def post(
        self,
        principal: str,
        path: str,
        body: dict[str, Any],
        status: int = 201,
        idempotency: str | None = None,
    ) -> dict[str, Any]:
        headers = dict(self.headers[principal])
        if idempotency:
            headers["Idempotency-Key"] = idempotency
        response = self.client.post(path, headers=headers, json=body)
        self.assertEqual(response.status_code, status, response.text)
        return cast(dict[str, Any], response.json())

    def seed(self, configured: bool = True) -> dict[str, Any]:
        project = self.post(
            "admin",
            "/api/projects",
            {
                "name": "Contract fixture",
                "repo_path": "/home/adf/ai-factory/projects/contract/repo",
                "allowed_root": "/home/adf/ai-factory",
                "trusted": True,
                "checks": [
                    {
                        "id": "unit",
                        "argv": ["python", "-m", "unittest"],
                        "timeout_sec": 7,
                    }
                ],
            },
        )
        task = self.post(
            "admin",
            "/api/tasks",
            {
                "project_id": project["id"],
                "title": "Contract fixture only",
                "status": "ready",
                "description": "No real repository or provider is invoked.",
                "expected_files": ["src/example.py"],
            },
        )
        body: dict[str, Any] = {"task_id": task["id"]}
        agents = {}
        if configured:
            for role in ("Planner", "Developer", "Reviewer", "Tester", "Integrator"):
                agents[role] = self.post(
                    "admin",
                    "/api/agents",
                    {
                        "name": role,
                        "role": role,
                        "provider": "mock",
                        "permission_profile": "observe"
                        if role in ("Planner", "Reviewer")
                        else "trusted-development",
                        "limits": {"max_execution_minutes": 1, "max_steps": 9},
                    },
                )
            policy = self.post(
                "admin",
                "/api/policies",
                {
                    "name": "Contract fixture approval",
                    "manifest": {
                        "allowed_write_paths": ["src/**"],
                        "allow_commit": True,
                        "trusted_repository": True,
                    },
                },
            )
            graph = read("examples/workflow.json")
            workflow = self.post(
                "admin",
                "/api/workflows",
                {"name": "Contract fixture DAG", "graph_json": graph},
            )
            version = self.post(
                "admin", "/api/workflows/" + workflow["id"] + "/versions", {}
            )
            body.update(
                workflow_version_id=version["id"],
                agent_config_version_id=agents["Developer"]["config_version_id"],
                policy_id=policy["id"],
                root_base_sha="a" * 40,
            )
        if not configured:
            graph = {
                "schema_version": "1",
                "nodes": [
                    {"id": "start", "type": "start"},
                    {"id": "end", "type": "end"},
                ],
                "edges": [{"source": "start", "target": "end"}],
            }
            workflow = self.post(
                "admin",
                "/api/workflows",
                {"name": "Inspection fixture", "graph_json": graph},
            )
            version = self.post(
                "admin", "/api/workflows/" + workflow["id"] + "/versions", {}
            )
            body["workflow_version_id"] = version["id"]
        run = self.post("admin", "/api/runs", body, idempotency="contract-run")
        return {"run": run, "task": task, "project": project, "agents": agents}

    def approve(self, run: dict[str, Any]) -> None:
        with self.database.transaction() as session:
            snapshot = {
                **self.approval_bindings(session.get(self.Run, run["id"])),
                "action": "execute_plan",
            }
        approval = self.post(
            "orch",
            "/internal/runs/" + run["id"] + "/approvals",
            {
                "action": "execute_plan",
                "snapshot": snapshot,
            },
        )
        self.post(
            "admin",
            "/api/approvals/" + approval["id"] + "/decision",
            {
                "decision": "approve",
                "snapshot_hash": approval["snapshot_hash"],
                "revision": approval["revision"],
            },
            200,
            "contract-approval",
        )

    def claim(
        self, run: dict[str, Any], operation: str, request: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        execution_id = str(uuid4())
        intent = {
            "execution_id": execution_id,
            "node_id": "__contract_" + operation,
            "attempt": 1,
            "operation": operation,
            "request": request or {},
        }
        path = "/internal/runs/" + run["id"] + "/executions"
        original = self.post("orch", path, intent)
        self.assertEqual(
            self.post("orch", path, intent)["request"], original["request"]
        )
        route = "/internal/executions/" + execution_id + "/claim"
        claim = self.post("worker", route, {"worker_id": self.worker_id}, 200)
        self.assertEqual(
            self.post("worker", route, {"worker_id": self.worker_id}, 200)["request"],
            claim["request"],
        )
        validate("execution-request.schema.json", claim["request"])
        self.assertEqual(claim["request"]["lease_epoch"], claim["epoch"])
        return claim

    def finish(self, claim: dict[str, Any], result: dict[str, Any]) -> None:
        body = {
            "worker_id": self.worker_id,
            "epoch": claim["epoch"],
            "status": "succeeded",
            "result": {"process_stopped": True, **result},
        }
        path = "/internal/executions/" + claim["execution_id"] + "/result"
        first = self.post("worker", path, body, 200)
        self.assertEqual(self.post("worker", path, body, 200), first)

    def test_exact_export_matches_live_factory(self) -> None:
        for name, document in exporter.snapshots().items():
            with self.subTest(name=name):
                self.assertEqual(read(name), document)
        paths = read("openapi.json")["paths"]
        self.assertIn("/api/runs/{run_id}/plan", paths)
        self.assertIn("/internal/executions/{execution_id}/reconcile", paths)
        self.assertIn("/internal/runs/{run_id}/trace", paths)
        self.assertNotIn("/api/runs/{run_id}/status", paths)

    def test_export_does_not_read_configured_secret_files(self) -> None:
        names = (
            "ADF_ADMIN_TOKEN_FILE",
            "ADF_DB_PASSWORD_FILE",
            "ADF_WORKER_TOKEN_FILE",
        )
        saved = {name: os.environ.get(name) for name in names}
        try:
            for name in names:
                os.environ[name] = str(Path(self.directory.name) / "missing-secret")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/export-api-contract.py"),
                    "--check",
                ],
                cwd=ROOT,
                env=dict(os.environ),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            for name in names:
                self.assertTrue(os.environ[name].endswith("missing-secret"))
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def test_preinspection_claim_allows_null_base_and_versions(self) -> None:
        state = self.seed(configured=False)
        request = self.claim(state["run"], "repo_inspect", {"task_prompt": None})[
            "request"
        ]
        self.assertIsNone(request["task_prompt"])
        self.assertIsNone(request["root_base_sha"])
        self.assertIsNone(request["agent_config_version"])
        self.assertIsNone(request["policy_version"])
        self.assertEqual(request["agent"]["provider"], "none")

    def test_claim_keeps_pinned_context_after_definition_edits(self) -> None:
        state = self.seed()
        self.approve(state["run"])
        changed = [
            (
                "tasks",
                state["task"],
                {
                    "description": "Changed after approval",
                    "expected_files": ["src/later.py"],
                },
            ),
            (
                "projects",
                state["project"],
                {
                    "checks": [
                        {"id": "later", "argv": ["python", "-V"], "timeout_sec": 99}
                    ]
                },
            ),
            (
                "agents",
                state["agents"]["Developer"],
                {"prompt": "Changed after approval", "limits": {"max_steps": 99}},
            ),
        ]
        for kind, original, update in changed:
            response = self.client.patch(
                "/api/" + kind + "/" + original["id"],
                headers={
                    **self.headers["admin"],
                    "If-Match": str(original["revision"]),
                },
                json=update,
            )
            self.assertEqual(response.status_code, 200, response.text)
        job = self.claim(state["run"], "agent_task")["request"]
        self.assertEqual(job["task_prompt"], state["task"]["description"])
        self.assertEqual(job["expected_files"], ["src/example.py"])
        self.assertEqual(job["allowed_write_paths"], ["src/example.py"])
        self.assertEqual(job["project"]["check_timeouts"], {"unit": 7})
        self.assertEqual(job["agent"]["prompt"], "")
        self.assertEqual(job["max_steps"], 9)
        self.assertEqual(
            job["agent_config_version"],
            state["agents"]["Developer"]["config_version_id"],
        )

    def test_all_seven_operations_replay_and_worker_projection(self) -> None:
        state = self.seed()
        run, agents = state["run"], state["agents"]
        self.approve(run)
        captured = {}
        for operation in ("repo_inspect", "planner"):
            claim = self.claim(run, operation)
            captured[operation] = claim["request"]
            self.finish(
                claim,
                {"root_base_sha": "a" * 40}
                if operation == "repo_inspect"
                else {"plan": {"tasks": []}},
            )
        developer = self.claim(run, "agent_task")
        captured["agent_task"] = developer["request"]
        self.assertEqual(developer["request"]["project"]["check_timeouts"], {"unit": 7})
        self.assertEqual(developer["request"]["timeout_sec"], 60)
        self.assertEqual(developer["request"]["max_steps"], 9)
        self.assertEqual(developer["request"]["agent"]["id"], agents["Developer"]["id"])
        self.assertEqual(
            developer["request"]["agent_config_version"],
            agents["Developer"]["config_version_id"],
        )
        event = {
            "event_id": str(uuid4()),
            "sequence": 1,
            "type": "warning",
            "time": "2026-10-10T00:00:00Z",
            "payload": {"message": "Synthetic contract fixture."},
        }
        batch = {
            "worker_id": self.worker_id,
            "epoch": developer["epoch"],
            "events": [event],
        }
        validate("execution-event.schema.json", event)
        validate("worker-event-batch.schema.json", batch)
        path = "/internal/executions/" + developer["execution_id"] + "/events"
        persisted = self.post("worker", path, batch, 200)
        self.assertEqual(self.post("worker", path, batch, 200), persisted)
        validate("run-event.schema.json", persisted["items"][0])
        self.finish(developer, {"tree_sha": "b" * 40, "base_sha": "a" * 40})
        target = {
            "target_execution_id": developer["execution_id"],
            "tree_sha": "b" * 40,
        }
        checks = [
            {
                "check_id": "unit",
                "status": "passed",
                "exit_code": 0,
                "tree_sha": "b" * 40,
            }
        ]
        tested = self.claim(run, "test", {**target, "check_ids": ["unit"]})
        captured["test"] = tested["request"]
        self.finish(tested, {"tree_sha": "b" * 40, "test_results": checks})
        reviewed = self.claim(run, "review", target)
        captured["review"] = reviewed["request"]
        review = {
            "approved": True,
            "tree_sha": "b" * 40,
            "developer_id": agents["Developer"]["id"],
            "reviewer_id": agents["Reviewer"]["id"],
            "findings": [],
        }
        self.finish(reviewed, {"tree_sha": "b" * 40, "review": review})
        committed = self.claim(
            run, "git_commit", {**target, "review": review, "test_results": checks}
        )
        captured["git_commit"] = committed["request"]
        self.finish(committed, {"tree_sha": "b" * 40, "commit_sha": "c" * 40})
        integrated = self.claim(
            run, "integrate", {"integration_commits": ["c" * 40], "check_ids": ["unit"]}
        )
        captured["integrate"] = integrated["request"]
        self.assertEqual(integrated["request"]["predecessor_commits"], [])
        self.finish(
            integrated,
            {
                "tree_sha": "d" * 40,
                "commit_sha": "e" * 40,
                "branch": "factory/integration/" + run["id"],
                "integration_status": "passed",
                "test_results": [{**checks[0], "tree_sha": "d" * 40}],
            },
        )
        root = Path(self.directory.name) / "worker-root"
        root.mkdir()
        workspace = root / "allocated"
        workspace.mkdir()
        executor = self.Executor(root, require_ext4=False)
        for operation, job in captured.items():
            if operation == "repo_inspect":
                continue
            executor.execution_deadline = time.monotonic() + job["timeout_sec"]
            request = executor._request(
                copy.deepcopy(job), SimpleNamespace(path=workspace), None, None
            )
            self.assertEqual(request.execution_id, job["execution_id"])
            self.assertEqual(request.allowed_tools, ())
            self.assertEqual(request.max_steps, job["max_steps"])


if __name__ == "__main__":
    unittest.main()
