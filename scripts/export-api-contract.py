"""Export the current API/model contracts without services, secrets or network access."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "packages" / "contracts"


@contextmanager
def isolated_import_environment() -> Iterator[None]:
    """The API module constructs a default app at import; prevent local secret reads."""
    names = [name for name in os.environ if name.startswith("ADF_")]
    names += ["DATABASE_URL", "ORCHESTRATOR_URL"]
    saved = {name: os.environ[name] for name in names if name in os.environ}
    try:
        for name in names:
            os.environ.pop(name, None)
        os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
        os.environ["ADF_TELEMETRY_ENABLED"] = "false"
        yield
    finally:
        for name in names:
            os.environ.pop(name, None)
        os.environ.pop("ADF_TELEMETRY_ENABLED", None)
        os.environ.update(saved)


def load_sources() -> dict[str, Any]:
    for module in ("api", "orchestrator", "runtime-worker"):
        source = str(ROOT / "services" / module / "src")
        if source not in sys.path:
            sys.path.insert(0, source)
    with isolated_import_environment():
        config = importlib.import_module("adf_api.config")
        db = importlib.import_module("adf_api.db")
        main = importlib.import_module("adf_api.main")
        schemas = importlib.import_module("adf_api.schemas")
        workflow = importlib.import_module("adf_orchestrator.models")
    # Explicit references survive import cleanup; no locals()/globals() registry.
    return {
        "Settings": config.Settings,
        "Database": db.Database,
        "create_app": main.create_app,
        "AgentInput": schemas.AgentInput,
        "EventBatch": schemas.EventBatch,
        "ExecutionRequest": schemas.ExecutionRequest,
        "PolicyManifest": schemas.PolicyManifest,
        "ProjectInput": schemas.ProjectInput,
        "WorkerEvent": schemas.WorkerEvent,
        "Workflow": workflow.Workflow,
    }


def model_schema(model: Any, title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **model.model_json_schema(),
        "title": title,
    }


def claimed_job_schema(source: dict[str, Any]) -> dict[str, Any]:
    """API overlays dictionaries, not an output Pydantic model; maintain this boundary."""
    uuid = {"type": "string", "format": "uuid"}
    sha = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
    optional_uuid = {"anyOf": [uuid, {"type": "null"}]}
    optional_sha = {"anyOf": [sha, {"type": "null"}]}
    paths = {
        "type": "array",
        "maxItems": 100,
        "items": {"type": "string", "minLength": 1, "maxLength": 1024},
    }
    project = source["ProjectInput"].model_json_schema(ref_template="#/$defs/{model}")
    agent = source["AgentInput"].model_json_schema(ref_template="#/$defs/{model}")
    policy = source["PolicyManifest"].model_json_schema(ref_template="#/$defs/{model}")
    definitions: dict[str, Any] = {}
    for nested in (project, agent, policy):
        definitions.update(nested.pop("$defs", {}))
        nested["additionalProperties"] = True
    project["properties"].update(
        {
            "check_registry": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                },
            },
            "check_timeouts": {
                "type": "object",
                "additionalProperties": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1800,
                },
            },
        }
    )
    project["required"] = [
        "name",
        "repo_path",
        "allowed_root",
        "default_branch",
        "trusted",
        "checks",
        "check_registry",
        "check_timeouts",
    ]
    agent["properties"].update(
        {
            "id": optional_uuid,
            "agent_id": optional_uuid,
            "config_version_id": optional_uuid,
            "allowed_tools": {"type": "array", "items": {"type": "string"}},
            "tools": {"type": "array", "items": {"type": "object"}},
            "skills": {"type": "array", "items": {"type": "object"}},
            "mcp_servers": {"type": "array", "items": {"type": "object"}},
        }
    )
    agent["properties"]["role"] = {
        "enum": [
            "Planner",
            "Architect",
            "Developer",
            "Tester",
            "Reviewer",
            "Integrator",
            "Observer",
        ]
    }
    agent["properties"]["provider"] = {"enum": ["codex", "claude", "mock", "none"]}
    agent["required"] = [
        "id",
        "role",
        "provider",
        "permission_profile",
        "allowed_tools",
        "tools",
        "skills",
        "mcp_servers",
    ]
    policy["properties"]["approved"] = {"type": "boolean"}
    policy["required"] = [
        "max_parallel_agents",
        "max_tasks_per_plan",
        "max_retries",
        "max_execution_minutes",
        "max_run_minutes",
        "max_steps",
        "max_output_bytes",
        "max_disk_bytes",
        "allowed_write_paths",
        "allow_commit",
        "trusted_repository",
        "approved",
    ]
    definitions.update(
        ProjectSnapshot=project, AgentSnapshot=agent, PolicySnapshot=policy
    )
    request_fields = source["ExecutionRequest"].model_json_schema()["properties"]
    properties: dict[str, Any] = {
        "schema_version": {"const": "1"},
        **{
            name: uuid
            for name in (
                "execution_id",
                "run_id",
                "task_id",
                "node_run_id",
                "project_id",
            )
        },
        "lease_epoch": {"type": "integer", "minimum": 1},
        "operation": {
            "enum": [
                "agent_task",
                "planner",
                "repo_inspect",
                "test",
                "review",
                "git_commit",
                "integrate",
            ]
        },
        "agent_config_version": optional_uuid,
        "policy_version": optional_uuid,
        "root_base_sha": optional_sha,
        "execution_base_sha": optional_sha,
        "worktree_key": uuid,
        "git_branch": {"type": "string", "pattern": "^factory/(task|integration)/"},
        "task_prompt": request_fields["task_prompt"],
        "expected_files": paths,
        "allowed_write_paths": paths,
        "allowed_tool_ids": {
            "type": "array",
            "maxItems": 100,
            "items": {"type": "string"},
        },
        "check_ids": {"type": "array", "maxItems": 20, "items": {"type": "string"}},
        "env_allowlist": {"type": "array", "maxItems": 20, "items": {"type": "string"}},
        "timeout_sec": {"type": "integer", "minimum": 1, "maximum": 1800},
        "max_steps": {"type": "integer", "minimum": 1, "maximum": 1000},
        "max_output_bytes": {"type": "integer", "minimum": 1, "maximum": 20971520},
        "max_disk_bytes": {"type": "integer", "minimum": 1, "maximum": 5368709120},
        "trace_id": {"type": ["string", "null"], "pattern": "^[0-9a-f]{32}$"},
        "traceparent": {
            "type": ["string", "null"],
            "pattern": "^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        },
        "deadline_at": {"type": "string", "format": "date-time"},
        "project": {"$ref": "#/$defs/ProjectSnapshot"},
        "agent": {"$ref": "#/$defs/AgentSnapshot"},
        "policy": {"$ref": "#/$defs/PolicySnapshot"},
        "predecessor_commits": {"type": "array", "items": sha},
        "target_execution_id": optional_uuid,
        "tree_sha": optional_sha,
        "integration_commits": {
            "type": "array",
            "maxItems": 100,
            "uniqueItems": True,
            "items": sha,
        },
        "repair_source_execution_id": uuid,
        "repair_feedback": {"type": "object"},
        "manual_resolution": {"type": "boolean"},
        "resolution_approved": {"type": "boolean"},
        "resolution_tree_sha": optional_sha,
        "resolution_approval_id": uuid,
    }
    required = [
        "schema_version",
        "execution_id",
        "run_id",
        "task_id",
        "node_run_id",
        "project_id",
        "lease_epoch",
        "operation",
        "agent_config_version",
        "policy_version",
        "root_base_sha",
        "execution_base_sha",
        "worktree_key",
        "git_branch",
        "task_prompt",
        "expected_files",
        "allowed_write_paths",
        "allowed_tool_ids",
        "check_ids",
        "env_allowlist",
        "timeout_sec",
        "max_steps",
        "max_output_bytes",
        "max_disk_bytes",
        "trace_id",
        "traceparent",
        "deadline_at",
        "project",
        "agent",
        "policy",
        "predecessor_commits",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ADF private nonterminal claimed execution request v1",
        "description": "API-created immutable overlay fetched by claim; Redis carries only IDs. Extension fields remain possible because ExecutionRequest allows extras. This schema does not grant permissions.",
        "type": "object",
        "additionalProperties": True,
        "properties": properties,
        "required": required,
        "$defs": definitions,
        "allOf": [
            {
                "if": {
                    "properties": {
                        "operation": {
                            "enum": [
                                "agent_task",
                                "test",
                                "review",
                                "git_commit",
                                "integrate",
                            ]
                        }
                    }
                },
                "then": {
                    "properties": {"root_base_sha": sha, "execution_base_sha": sha}
                },
            },
            {
                "if": {
                    "properties": {
                        "operation": {"enum": ["test", "review", "git_commit"]}
                    }
                },
                "then": {
                    "required": ["target_execution_id", "tree_sha"],
                    "properties": {"target_execution_id": uuid, "tree_sha": sha},
                },
            },
            {
                "if": {"properties": {"operation": {"const": "integrate"}}},
                "then": {
                    "required": ["integration_commits"],
                    "properties": {"integration_commits": {"minItems": 1}},
                },
            },
            {
                "if": {
                    "properties": {
                        "operation": {"enum": ["agent_task", "git_commit", "integrate"]}
                    }
                },
                "then": {
                    "properties": {
                        "policy": {
                            "properties": {
                                "approved": {"const": True},
                                "trusted_repository": {"const": True},
                            }
                        }
                    }
                },
            },
        ],
    }


def run_event_schema() -> dict[str, Any]:
    """Exact persisted event_view response; distinct from a producer WorkerEvent."""
    uuid = {"type": "string", "format": "uuid"}
    optional_uuid = {"anyOf": [uuid, {"type": "null"}]}
    nullable_sequence = {"type": ["integer", "null"], "minimum": 1}
    properties = {
        "schema_version": {"const": "1"},
        "event_id": uuid,
        "run_id": uuid,
        "run_sequence": {"type": "integer", "minimum": 1},
        "execution_id": optional_uuid,
        "epoch": nullable_sequence,
        "sequence": nullable_sequence,
        "type": {"type": "string", "minLength": 1, "maxLength": 128},
        "time": {"type": "string", "format": "date-time"},
        "payload": {"type": "object"},
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ADF persisted run event response v1",
        "description": "API event_view response carried by SSE data and event-history. run_sequence is the SSE cursor; execution context may be null.",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def snapshots() -> dict[str, dict[str, Any]]:
    source = load_sources()
    database = source["Database"]("sqlite+pysqlite:///:memory:")
    try:
        app = source["create_app"](source["Settings"](), database)
        document = app.openapi()
    finally:
        database.engine.dispose()
    workflow = model_schema(source["Workflow"], "ADF workflow DAG v1")
    workflow["description"] = (
        "Exported orchestrator model shape; validate_graph additionally enforces node config, ports, acyclicity, reachability, paired forks and writing gates."
    )
    return {
        "openapi.json": document,
        "run-event.schema.json": run_event_schema(),
        "workflow.schema.json": workflow,
        "execution-request.schema.json": claimed_job_schema(source),
        "execution-event.schema.json": model_schema(
            source["WorkerEvent"], "ADF normalized worker event ingestion v1"
        ),
        "worker-event-batch.schema.json": model_schema(
            source["EventBatch"], "ADF worker event batch ingestion v1"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail on snapshot drift; write nothing."
    )
    args = parser.parse_args()
    exported = snapshots()
    different = []
    for name, document in exported.items():
        destination = CONTRACTS / name
        if args.check:
            if (
                not destination.exists()
                or json.loads(destination.read_text(encoding="utf-8")) != document
            ):
                different.append(name)
        else:
            destination.write_text(
                json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
    if different:
        raise SystemExit(
            "Contract drift: "
            + ", ".join(different)
            + ". Run this exporter with the API dependency environment."
        )
    print(
        ("PASS: current" if args.check else "Exported")
        + f" {len(exported)} API/model snapshots; no services or credentials accessed."
    )


if __name__ == "__main__":
    main()
