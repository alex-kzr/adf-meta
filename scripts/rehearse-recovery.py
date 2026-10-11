"""Nondestructive isolated runtime recovery from a trusted private ADF snapshot.

Creates two private QA generations, never changes source services or provider auth.
The pending mock fixture is created in generation A, not claimed to have existed in
the source snapshot. Generation B restores its checkpoint/outbox into empty Redis.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import secrets
import sys
import tarfile
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
MAX = 30 * 1024**2
NAMESPACE = re.compile(r"[a-f0-9]{8}")
STAGES = {"a", "b"}
PROOF_FILE = "recovery-proof.txt"
PROOF_CONTENT = "recovered mock work\n"
CHECKS = [
    {
        "id": "recovery-proof",
        "argv": [
            "python",
            "-c",
            "from pathlib import Path; assert "
            "Path('recovery-proof.txt').read_text() == 'recovered mock work\\n'",
        ],
        "timeout_sec": 30,
    }
]


class RecoveryError(Exception):
    """Safe diagnostics contain no API bodies, credentials or subprocess output."""


def snapshot_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "adf_recovery_snapshot", ROOT / "scripts/snapshot-runtime.py"
    )
    if spec is None or spec.loader is None:
        raise RecoveryError("Snapshot helper unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def local_image(module: ModuleType, source: str) -> str:
    if source not in {"adf-api-1", "adf-orchestrator-1", "adf-frontend-1"}:
        raise RecoveryError("Only known source image metadata may be read")
    image = (
        module.command("docker", ["inspect", source, "--format", "{{.Image}}"])
        .decode()
        .strip()
    )
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
        raise RecoveryError("Existing local application image ID required")
    return str(image)


def locked_image(key: str) -> str:
    for line in (ROOT / "infra/images.lock.env").read_text().splitlines():
        if line.startswith(key + "="):
            image = line.split("=", 1)[1]
            if re.fullmatch(
                r"(?:postgres|redis):[A-Za-z0-9.-]+@sha256:[a-f0-9]{64}", image
            ):
                return image
    raise RecoveryError("Verified local infrastructure image digest required")


@dataclass
class Rehearsal:
    namespace: str
    snapshot_id: str
    module: ModuleType = field(repr=False)
    credentials: dict[str, str] = field(repr=False)
    images: dict[str, str]
    directory: Path
    worker_id: str
    roots: dict[str, str] = field(default_factory=dict)
    projects: dict[str, dict[str, str]] = field(default_factory=dict)
    fixture_run_id: str | None = None

    def __post_init__(self) -> None:
        if not NAMESPACE.fullmatch(self.namespace):
            raise RecoveryError("Generated QA namespace required")

    def name(self, stage: str, service: str) -> str:
        if stage not in STAGES or service not in {
            "pg",
            "api",
            "orch",
            "redis",
            "frontend",
            "network",
        }:
            raise RecoveryError("Fixed QA generation/service required")
        return f"adf-recovery-{self.namespace}-{stage}-{service}"

    def guard(self, name: str) -> None:
        if not re.fullmatch(
            f"adf-recovery-{self.namespace}-[ab]-(?:pg|api|orch|redis|frontend)", name
        ):
            raise RecoveryError("Source or foreign resource mutation refused")
        labels = json.loads(
            self.module.command(
                "docker", ["inspect", name, "--format", "{{json .Config.Labels}}"]
            )
        )
        if (
            not isinstance(labels, dict)
            or labels.get("adf.recovery.namespace") != self.namespace
        ):
            raise RecoveryError("QA resource ownership label required")

    def isolation(self, stage: str) -> dict[str, Any]:
        network = json.loads(
            self.module.command(
                "docker",
                [
                    "network",
                    "inspect",
                    self.name(stage, "network"),
                    "--format",
                    "{{json .}}",
                ],
            )
        )
        if (
            not network.get("Internal")
            or network.get("Labels", {}).get("adf.recovery.namespace") != self.namespace
        ):
            raise RecoveryError("Owned disconnected QA network required")
        records = []
        for service in ("pg", "api", "orch", "redis", "frontend"):
            name = self.name(stage, service)
            self.guard(name)
            record = json.loads(
                self.module.command(
                    "docker",
                    [
                        "inspect",
                        name,
                        "--format",
                        '{"host":{{json .HostConfig}},"mounts":{{json .Mounts}},'
                        '"networks":{{json .NetworkSettings.Networks}}}',
                    ],
                )
            )
            host = record["host"]
            mounts = record["mounts"]
            if host.get("PortBindings") or host.get("Privileged") or host.get("Binds"):
                raise RecoveryError("QA host exposure refused")
            if any(m.get("Type") != "volume" for m in mounts):
                raise RecoveryError("QA source/bind mounts refused")
            if mounts and (
                service not in {"pg", "redis"}
                or len(mounts) != 1
                or mounts[0].get("Destination")
                != ("/var/lib/postgresql" if service == "pg" else "/data")
                or not re.fullmatch(r"[a-f0-9]{64}", mounts[0].get("Name", ""))
            ):
                raise RecoveryError(
                    "Only fresh anonymous infrastructure volume allowed"
                )
            if set(record["networks"]) != {self.name(stage, "network")}:
                raise RecoveryError("QA network attachment escaped isolation")
            expected = (128 if service in {"redis", "frontend"} else 512) * 1024**2
            if host.get("Memory") != expected or host.get("NanoCpus") != 1000000000:
                raise RecoveryError("QA resource caps differ from bounded plan")
            records.append(
                {
                    "service": service,
                    "memory_bytes": expected,
                    "mount_count": len(mounts),
                    "published_ports": 0,
                }
            )
        return {"internal_network": True, "containers": records}

    def frontend(self, stage: str) -> dict[str, Any]:
        self.guard(self.name(stage, "api"))
        raw = self.module.command(
            "docker",
            [
                "exec",
                "--interactive",
                self.name(stage, "api"),
                "python",
                "/opt/adf-recovery-http.py",
            ],
            input_file=self.request_file({"kind": "frontend"}),
            limit=MAX,
        )
        data = json.loads(raw)
        if data.get("status") != 200 or data.get("bytes", 0) < 100:
            raise RecoveryError("QA frontend did not serve the application")
        return dict(data)

    def request_file(self, body: object) -> Path:
        path = self.directory / "requests" / (uuid4().hex + ".json")
        self.module.write_json(path, body)
        return path

    def http_raw(
        self, stage: str, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        name = self.name(stage, "api")
        self.guard(name)
        raw = self.module.command(
            "docker",
            ["exec", "--interactive", name, "python", "/opt/adf-recovery-http.py"],
            input_file=self.request_file(
                {
                    "method": method,
                    "path": path,
                    "body": body,
                    "idempotency_key": str(uuid4()) if method == "POST" else None,
                }
            ),
            limit=MAX,
        )
        reply = json.loads(raw)
        if not isinstance(reply, dict) or reply.get("qa_tunnel_failed"):
            raise RecoveryError("Private QA HTTP tunnel failed")
        return reply

    def http(
        self, stage: str, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        reply = self.http_raw(stage, method, path, body)
        if not 200 <= reply.get("status", 0) < 300 or not isinstance(
            reply.get("data"), dict
        ):
            code = (
                reply.get("data", {}).get("code")
                if isinstance(reply.get("data"), dict)
                else None
            )
            safe = (
                code
                if isinstance(code, str) and re.fullmatch("[A-Z0-9_]{1,80}", code)
                else "QA_HTTP_REJECTED"
            )
            raise RecoveryError(str(safe))
        return dict(reply["data"])

    def redis(self, stage: str, arguments: list[str]) -> Any:
        name = self.name(stage, "api")
        self.guard(name)
        raw = self.module.command(
            "docker",
            ["exec", "--interactive", name, "python", "/opt/adf-recovery-http.py"],
            input_file=self.request_file({"kind": "redis", "arguments": arguments}),
            limit=MAX,
        )
        reply = json.loads(raw)
        if "data" not in reply:
            raise RecoveryError("Private QA Redis tunnel failed")
        return reply["data"]

    def sql(self, stage: str, sql: str, *, run_id: str | None = None) -> bytes:
        variable: list[str] = []
        if run_id is not None:
            try:
                canonical = str(UUID(run_id))
            except ValueError:
                raise RecoveryError("Canonical controlled run ID required") from None
            if canonical != run_id:
                raise RecoveryError("Canonical controlled run ID required")
            variable = ["--set", "qa_run=" + canonical]
        name = self.name(stage, "pg")
        self.guard(name)
        path = self.directory / "requests" / (uuid4().hex + ".sql")
        with self.module.new_file(path) as stream:
            stream.write(sql.encode())
        result: bytes = self.module.command(
            "docker",
            [
                "exec",
                "--interactive",
                "--user",
                "postgres",
                name,
                "psql",
                "--no-psqlrc",
                "--no-password",
                "--username",
                "adf_restore",
                "--dbname",
                "adf_restore",
                "--tuples-only",
                "--no-align",
                "--set",
                "ON_ERROR_STOP=1",
                *variable,
            ],
            input_file=path,
        )
        return result

    def worker(
        self,
        stage: str,
        mode: str,
        extra: dict[str, Any],
        *,
        output: Path | None = None,
    ) -> Any:
        value = {"namespace": self.namespace, "stage": stage, "mode": mode, **extra}
        helper = (
            "/mnt/"
            + ROOT.drive[0].lower()
            + "/"
            + "/".join(ROOT.parts[1:])
            + "/scripts/recovery-worker.py"
        )
        argv = [
            "-d",
            "Ubuntu",
            "--exec",
            "/home/alex/ai-factory/tools/worker-venv/bin/python",
            helper,
        ]
        raw = self.module.command(
            "wsl",
            argv,
            timeout=300,
            input_file=self.request_file(value),
            output=output,
            limit=self.module.MAX_ARCHIVE if output else MAX,
        )
        if output:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("qa_worker_failed"):
            raise RecoveryError("Private mock-only WSL helper failed")
        return data

    def secret_archive(self, stage: str, service: str) -> Path:
        names = {
            "pg": ["bootstrap-password"],
            "api": [
                "admin-token",
                "orchestrator-token",
                "worker-token",
                "api-password",
                "redis-password",
            ],
            "orch": ["orchestrator-token", "checkpoint-password", "redis-password"],
            "redis": ["redis.acl"],
        }[service]
        uid = 999 if service in {"pg", "redis"} else 10001
        path = self.directory / f"{stage}-{service}-private.tar"
        with (
            self.module.new_file(path) as stream,
            tarfile.open(fileobj=stream, mode="w") as archive,
        ):
            directory = tarfile.TarInfo("run/qa")
            directory.type, directory.mode, directory.uid, directory.gid = (
                tarfile.DIRTYPE,
                0o700,
                uid,
                uid,
            )
            archive.addfile(directory)
            for name in names:
                body = (self.credentials[name] + "\n").encode()
                item = tarfile.TarInfo("run/qa/" + name)
                item.mode, item.uid, item.gid, item.size = 0o600, uid, uid, len(body)
                archive.addfile(item, io.BytesIO(body))
        return path

    def create(self, stage: str, service: str) -> None:
        name, network = self.name(stage, service), self.name(stage, "network")
        alias = {"pg": "postgres", "orch": "orchestrator"}.get(service, service)
        argv = [
            "create",
            "--pull=never",
            "--name",
            name,
            "--network",
            network,
            "--network-alias",
            alias,
            "--label",
            "adf.recovery.namespace=" + self.namespace,
            "--label",
            "adf.recovery.stage=" + stage,
            "--memory",
            "128m" if service in {"redis", "frontend"} else "512m",
            "--cpus",
            "1",
        ]
        common = [
            "--env",
            "ADF_TELEMETRY_ENABLED=false",
            "--env",
            "LANGSMITH_TRACING=false",
        ]
        if service == "pg":
            argv += [
                "--env",
                "POSTGRES_USER=adf_restore",
                "--env",
                "POSTGRES_DB=adf_restore",
                "--env",
                "POSTGRES_PASSWORD_FILE=/run/qa/bootstrap-password",
                self.images["pg"],
            ]
        elif service == "redis":
            argv += [
                "--user",
                "999:999",
                "--entrypoint",
                "redis-server",
                self.images["redis"],
                "--aclfile",
                "/run/qa/redis.acl",
                "--appendonly",
                "no",
                "--save",
                "",
            ]
        elif service == "api":
            argv += common + [
                "--env",
                "DATABASE_URL=postgresql+psycopg://adf_api@postgres:5432/adf_restore",
                "--env",
                "ADF_DB_PASSWORD_FILE=/run/qa/api-password",
                "--env",
                "ADF_ADMIN_TOKEN_FILE=/run/qa/admin-token",
                "--env",
                "ADF_ORCHESTRATOR_TOKEN_FILE=/run/qa/orchestrator-token",
                "--env",
                "ADF_WORKER_TOKEN_FILE=/run/qa/worker-token",
                "--env",
                "ADF_ALLOWED_ROOTS=" + json.dumps([self.roots[stage] + "/projects"]),
                "--env",
                "ADF_ARTIFACT_ROOT=/app/artifacts",
                "--env",
                "ORCHESTRATOR_URL=http://orchestrator:8081",
                "--env",
                "ADF_QA_REDIS_HOST=" + self.name(stage, "redis"),
                "--env",
                "ADF_LANGFUSE_URL=",
                self.images["api"],
            ]
        elif service == "orch":
            argv += common + [
                "--env",
                "ADF_API_URL=http://api:8080",
                "--env",
                "ADF_ORCHESTRATOR_TOKEN_FILE=/run/qa/orchestrator-token",
                "--env",
                "DATABASE_URL=postgresql://adf_orchestrator@postgres:5432/adf_restore?options=-csearch_path%3Dcheckpoints",
                "--env",
                "ADF_DB_PASSWORD_FILE=/run/qa/checkpoint-password",
                "--env",
                "ADF_REDIS_URL=redis://adf_orchestrator@redis:6379/0",
                "--env",
                "ADF_REDIS_PASSWORD_FILE=/run/qa/redis-password",
                self.images["orch"],
            ]
        else:
            argv += [self.images["frontend"]]
        self.module.command("docker", argv)
        self.guard(name)
        if service != "frontend":
            self.module.command(
                "docker",
                ["cp", "--archive", "-", name + ":/"],
                input_file=self.secret_archive(stage, service),
            )
        if service == "api":
            self.module.command(
                "docker",
                [
                    "cp",
                    str(ROOT / "scripts/recovery-http.py"),
                    name + ":/opt/adf-recovery-http.py",
                ],
            )

    def start(self, stage: str, service: str) -> None:
        name = self.name(stage, service)
        self.guard(name)
        self.module.command("docker", ["start", name])

    def wait_database(self, stage: str) -> None:
        deadline = time.monotonic() + 60
        while True:
            try:
                self.module.command(
                    "docker",
                    [
                        "exec",
                        self.name(stage, "pg"),
                        "pg_isready",
                        "--host",
                        "127.0.0.1",
                        "--username",
                        "adf_restore",
                        "--dbname",
                        "adf_restore",
                    ],
                    timeout=5,
                )
                return
            except Exception:
                if time.monotonic() > deadline:
                    raise RecoveryError("QA PostgreSQL readiness deadline") from None
                time.sleep(1)

    def stop_generation(self, stage: str) -> None:
        names = [
            self.name(stage, service)
            for service in ("orch", "frontend", "api", "redis", "pg")
        ]
        for name in names:
            self.guard(name)
        self.module.command("docker", ["stop", "--time", "10", *names], timeout=60)

    def prepare_generation(
        self,
        stage: str,
        manifest: dict[str, Any],
        source: Path,
        dump: Path,
        *,
        previous_root: str | None = None,
    ) -> None:
        prepared = self.worker(
            stage,
            "prepare",
            {
                "source": self.module.windows_to_wsl(source),
                "projects": manifest["projects"],
                "worker_token": self.credentials["worker-token"],
            },
        )
        self.roots[stage], self.projects[stage] = prepared["root"], prepared["repos"]
        self.module.command(
            "docker",
            [
                "network",
                "create",
                "--internal",
                "--label",
                "adf.recovery.namespace=" + self.namespace,
                self.name(stage, "network"),
            ],
        )
        self.create(stage, "pg")
        self.start(stage, "pg")
        self.wait_database(stage)
        self.module.command(
            "docker",
            [
                "exec",
                "--interactive",
                "--user",
                "postgres",
                self.name(stage, "pg"),
                "pg_restore",
                "--no-password",
                "--username",
                "adf_restore",
                "--dbname",
                "adf_restore",
                "--no-owner",
                "--no-privileges",
                "--exit-on-error",
                "--single-transaction",
            ],
            timeout=300,
            input_file=dump,
        )
        roles = self.credentials
        grants = f"""
CREATE ROLE adf_api LOGIN PASSWORD '{roles["api-password"]}'
NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE adf_orchestrator LOGIN PASSWORD '{roles["checkpoint-password"]}'
NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE adf_restore TO adf_api, adf_orchestrator;
GRANT USAGE ON SCHEMA control, runtime, audit, public TO adf_api;
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA control, runtime, audit TO adf_api;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO adf_api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA control, runtime, audit TO adf_api;
GRANT USAGE, CREATE ON SCHEMA checkpoints TO adf_orchestrator;
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA checkpoints TO adf_orchestrator;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA checkpoints TO adf_orchestrator;
"""
        self.sql(stage, grants)
        for service in ("redis", "api", "orch", "frontend"):
            self.create(stage, service)
        for artifact in manifest["artifacts"]:
            self.module.command(
                "docker",
                [
                    "cp",
                    str(source / "artifacts" / (artifact["id"] + ".bin")),
                    self.name(stage, "api")
                    + ":/app/artifacts/"
                    + artifact["storage_key"],
                ],
            )
        self.isolation(stage)
        self.start(stage, "api")
        self.module.command(
            "docker",
            [
                "exec",
                "--user",
                "0",
                self.name(stage, "api"),
                "chown",
                "-R",
                "10001:10001",
                "/app/artifacts",
            ],
        )
        relocation = {
            "repos": self.projects[stage],
            "root": self.roots[stage],
            "previous_root": previous_root,
            "fixture_run_id": self.fixture_run_id,
            "checks": CHECKS,
        }
        self.module.command(
            "docker",
            [
                "exec",
                "--interactive",
                self.name(stage, "api"),
                "python",
                "-c",
                REMAP_PROGRAM,
            ],
            input_file=self.request_file(relocation),
        )
        deadline = time.monotonic() + 90
        while True:
            try:
                self.http(stage, "GET", "/readyz")
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise RecoveryError("QA API readiness deadline") from None
                time.sleep(1)
        self.start(stage, "redis")
        deadline = time.monotonic() + 30
        while True:
            try:
                if self.redis(stage, ["PING"]) == "PONG":
                    break
            except Exception:  # noqa: S110 -- dependency backoff omits private errors
                time.sleep(0.1)
            if time.monotonic() > deadline:
                raise RecoveryError("QA Redis readiness deadline")
            time.sleep(1)
        if self.redis(stage, ["XLEN", "adf:executions"]) != 0:
            raise RecoveryError("Recovered transport must initially be empty")
        self.start(stage, "frontend")
        self.frontend(stage)
        if stage == "a":
            self.start(stage, "orch")
            deadline = time.monotonic() + 60
            while True:
                try:
                    self.module.command(
                        "docker",
                        [
                            "exec",
                            "--interactive",
                            self.name(stage, "api"),
                            "python",
                            "/opt/adf-recovery-http.py",
                        ],
                        input_file=self.request_file({"kind": "orchestrator"}),
                    )
                    break
                except Exception:
                    if time.monotonic() > deadline:
                        raise RecoveryError(
                            "QA workflow validator readiness deadline"
                        ) from None
                    time.sleep(1)

    def approve_pending(self, stage: str, run_id: str) -> None:
        for approval in self.http(stage, "GET", f"/api/runs/{run_id}/approvals")[
            "items"
        ]:
            if approval.get("status") == "pending":
                self.http(
                    stage,
                    "POST",
                    "/api/approvals/" + approval["id"] + "/decision",
                    {
                        "decision": "approve",
                        "snapshot_hash": approval["snapshot_hash"],
                        "revision": approval["revision"],
                    },
                )

    def seed(self) -> dict[str, Any]:
        project_id = sorted(self.projects["a"])[0]
        project = self.http("a", "GET", "/api/projects/" + project_id)
        developer = self.http(
            "a",
            "POST",
            "/api/agents",
            {
                "name": "Recovery QA developer " + self.namespace,
                "role": "Developer",
                "provider": "mock",
                "permission_profile": "trusted-development",
            },
        )
        reviewer = self.http(
            "a",
            "POST",
            "/api/agents",
            {
                "name": "Recovery QA reviewer " + self.namespace,
                "role": "Reviewer",
                "provider": "mock",
                "permission_profile": "observe",
            },
        )
        self.http(
            "a",
            "POST",
            "/api/agents",
            {
                "name": "Recovery QA integrator " + self.namespace,
                "role": "Integrator",
                "provider": "mock",
                "permission_profile": "trusted-development",
            },
        )
        policy = self.http(
            "a",
            "POST",
            "/api/policies",
            {
                "name": "Recovery QA policy " + self.namespace,
                "manifest": {
                    "allow_commit": True,
                    "trusted_repository": True,
                    "allowed_write_paths": [PROOF_FILE],
                    "provider_pin": "mock",
                    "max_retries": 0,
                    "max_execution_minutes": 2,
                    "max_run_minutes": 10,
                },
            },
        )
        nodes = [
            {"id": "s", "type": "start", "config": {}},
            {
                "id": "approve",
                "type": "approval",
                "config": {"action": "trusted-development", "expires_in_sec": 3600},
            },
            {
                "id": "dev",
                "type": "agent_task",
                "config": {
                    "agent_config_version_id": developer["config_version_id"],
                    "description": json.dumps(
                        {"mock_files": {PROOF_FILE: PROOF_CONTENT}}
                    ),
                    "expected_files": [PROOF_FILE],
                },
            },
            {
                "id": "test",
                "type": "test",
                "config": {
                    "target_node": "dev",
                    "check_ids": ["recovery-proof"],
                },
            },
            {
                "id": "review",
                "type": "review",
                "config": {
                    "target_node": "dev",
                    "agent_config_version_id": reviewer["config_version_id"],
                },
            },
            {
                "id": "commit",
                "type": "git_commit",
                "config": {
                    "target_node": "dev",
                    "review_node": "review",
                    "test_node": "test",
                },
            },
            {
                "id": "e",
                "type": "end",
                "config": {},
            },
        ]
        workflow = self.http(
            "a",
            "POST",
            "/api/workflows",
            {
                "name": "Recovery QA workflow " + self.namespace,
                "graph_json": {
                    "schema_version": "1",
                    "nodes": nodes,
                    "edges": [
                        {"source": left["id"], "target": right["id"]}
                        for left, right in zip(nodes, nodes[1:])
                    ],
                },
            },
        )
        version = self.http(
            "a", "POST", "/api/workflows/" + workflow["id"] + "/versions"
        )
        task = self.http(
            "a",
            "POST",
            "/api/tasks",
            {
                "project_id": project_id,
                "title": "Restore mock task " + self.namespace,
                "description": json.dumps(
                    {"review": {"approved": True, "findings": []}}
                ),
                "expected_files": [PROOF_FILE],
                "status": "ready",
            },
        )
        before = self.worker("a", "inspect", {"project_id": project_id})
        run = self.http(
            "a",
            "POST",
            "/api/runs",
            {
                "task_id": task["id"],
                "workflow_version_id": version["id"],
                "agent_config_version_id": developer["config_version_id"],
                "policy_id": policy["id"],
                "root_base_sha": before["main_sha"],
            },
        )
        return {
            "run_id": run["id"],
            "project_id": project["id"],
            "source_main_sha": before["main_sha"],
        }


REMAP_PROGRAM = r"""
import json, sys
from sqlalchemy import select
from adf_api.config import Settings
from adf_api.db import Database
from adf_api.models import Project, Run, Execution

value = json.loads(sys.stdin.buffer.read(1024 * 1024))
db = Database(Settings.from_environment().database_url)
old = value["previous_root"]


def relocate(data):
    if isinstance(data, str) and old and (data == old or data.startswith(old + "/")):
        return value["root"] + data[len(old) :]
    if isinstance(data, list):
        return [relocate(x) for x in data]
    if isinstance(data, dict):
        return {k: relocate(v) for k, v in data.items()}
    return data


with db.transaction() as session:
    for project in session.scalars(select(Project)):
        if project.id not in value["repos"]:
            raise ValueError("Unmapped QA project")
        project.repo_path = value["repos"][project.id]
        project.data = {
            **project.data,
            "repo_path": project.repo_path,
            "allowed_root": value["root"] + "/projects",
            "checks": value["checks"],
        }
    if old:
        for run in session.scalars(
            select(Run).where(Run.id == value["fixture_run_id"])
        ):
            if any(
                x.status != "created"
                for x in session.scalars(
                    select(Execution).where(Execution.run_id == run.id)
                )
            ):
                raise ValueError("Only never-spawned QA fixture may relocate")
            run.snapshot = relocate(run.snapshot)
            for execution in session.scalars(
                select(Execution).where(Execution.run_id == run.id)
            ):
                execution.request = relocate(execution.request)
db.engine.dispose()
print('{"qa_paths_relocated":true}')
"""


def durable_state(rehearsal: Rehearsal, stage: str, run_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9-]{36}", run_id):
        raise RecoveryError("Canonical controlled run ID required")
    raw = rehearsal.sql(
        stage,
        """SELECT json_build_object(
    'checkpoint_count',(SELECT count(*) FROM checkpoints.checkpoints
        WHERE thread_id=:'qa_run'),
    'created_execution_ids',(SELECT json_agg(id ORDER BY id)
        FROM runtime.executions WHERE run_id=:'qa_run' AND status='created'),
    'outbox_ids',(SELECT json_agg(o.id ORDER BY o.id)
        FROM runtime.outbox o JOIN runtime.executions e ON e.id=o.execution_id
        WHERE e.run_id=:'qa_run'),
    'execution_count',(SELECT count(*) FROM runtime.executions
        WHERE run_id=:'qa_run'));""",
        run_id=run_id,
    )
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise RecoveryError("Controlled durable state shape")
    return data


def drive(rehearsal: Rehearsal, seed: dict[str, Any]) -> dict[str, Any]:
    run_id = seed["run_id"]
    rehearsal.http(
        "b",
        "POST",
        "/internal/workers/register",
        {
            "worker_id": rehearsal.worker_id,
            "capabilities": {
                "contract_version": "1",
                "providers": {"mock": {"health": "ready", "auth": "offline"}},
                "operations": [
                    "repo_inspect",
                    "planner",
                    "agent_task",
                    "test",
                    "review",
                    "git_commit",
                    "integrate",
                ],
            },
            "allowed_roots": [rehearsal.roots["b"] + "/projects"],
            "project_ids": list(rehearsal.projects["b"]),
        },
    )
    rehearsal.redis(
        "b", ["XGROUP", "CREATE", "adf:executions", "adf-workers", "0", "MKSTREAM"]
    )
    initial = rehearsal.http("b", "GET", "/api/runs/" + run_id)
    executions: dict[str, dict[str, Any]] = {
        item["id"]: item
        for item in initial.get("executions", [])
        if item["status"] == "succeeded"
    }
    duplicates = 0
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        rehearsal.approve_pending("b", run_id)
        run = rehearsal.http("b", "GET", "/api/runs/" + run_id)
        if run["status"] in {"completed", "failed", "cancelled"}:
            if run["status"] != "completed":
                raise RecoveryError("Recovered mock run did not complete")
            return {
                "run": run,
                "executed": executions,
                "duplicate_messages_acknowledged": duplicates,
            }
        if run["status"] == "paused":
            raise RecoveryError("Recovered fixture paused unexpectedly")
        message = rehearsal.redis(
            "b",
            [
                "XREADGROUP",
                "GROUP",
                "adf-workers",
                "recovery",
                "COUNT",
                "100",
                "BLOCK",
                "100",
                "STREAMS",
                "adf:executions",
                ">",
            ],
        )
        if not message:
            time.sleep(0.2)
            continue
        acknowledged = []
        for message_id, raw in message[0][1]:
            fields = dict(zip(raw[::2], raw[1::2]))
            execution_id = fields.get("execution_id")
            if not isinstance(execution_id, str):
                raise RecoveryError("Recovered transport payload shape")
            if execution_id in executions:
                duplicates += 1
                acknowledged.append(message_id)
                continue
            result = rehearsal.worker(
                "b",
                "execute",
                {
                    "container": rehearsal.name("b", "api"),
                    "run_id": run_id,
                    "execution_id": execution_id,
                    "worker_id": rehearsal.worker_id,
                },
            )
            if result.get("terminal_duplicate_acknowledged"):
                duplicates += 1
            else:
                if result.get("status") != "succeeded":
                    code = result.get("error_code")
                    safe = (
                        code
                        if isinstance(code, str)
                        and re.fullmatch(r"[A-Z0-9_]{1,80}", code)
                        else "FAILED_OR_REPEATED"
                    )
                    raise RecoveryError("Recovered execution: " + safe)
                executions[execution_id] = result
            acknowledged.append(message_id)
        rehearsal.redis("b", ["XACK", "adf:executions", "adf-workers", *acknowledged])
    raise RecoveryError("Recovered mock workflow deadline")


def resource_preflight(module: ModuleType) -> dict[str, Any]:
    memory = int(module.command("docker", ["info", "--format", "{{.MemTotal}}"]))
    running = module.command("docker", ["ps", "--quiet"]).splitlines()
    if memory < 4 * 1024**3 or len(running) > 40:
        raise RecoveryError("Docker capacity/container count outside bounded QA gate")
    # Current usage is measured; stopped A is preserved before B is created.
    raw = module.command(
        "docker", ["stats", "--no-stream", "--format", "{{json .}}"], timeout=30
    )
    used = 0.0
    for line in raw.splitlines():
        text = json.loads(line)["MemUsage"].split(" / ", 1)[0]
        match = re.fullmatch(r"([0-9.]+)(B|KiB|MiB|GiB|kB|MB|GB)", text)
        if not match:
            raise RecoveryError("Docker memory measurement format unsupported")
        units = {
            "B": 1,
            "KiB": 1024,
            "MiB": 1024**2,
            "GiB": 1024**3,
            "kB": 1000,
            "MB": 1000**2,
            "GB": 1000**3,
        }
        used += float(match[1]) * units[match[2]]
    budget = 1792 * 1024**2
    if memory - used < budget + 512 * 1024**2:
        raise RecoveryError("Insufficient measured Docker headroom for QA caps")
    return {
        "docker_memory_bytes": memory,
        "running_container_count": len(running),
        "measured_used_bytes": int(used),
        "generation_memory_cap_bytes": budget,
    }


def run(snapshot_id: str, *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        raise RecoveryError("Isolated runtime requires --allow-isolated-runtime")
    if os.name != "nt":
        raise RecoveryError("Run the recovery orchestrator on the Windows host")
    module = snapshot_module()
    if not module.SNAPSHOT_ID.fullmatch(snapshot_id):
        raise RecoveryError("Select a generated complete snapshot ID")
    source = module.PRIVATE / snapshot_id
    manifest = module.verify(source)
    inventory = json.loads((source / "inventory.json").read_bytes())
    if any(
        row["status"] not in module.TERMINAL_RUNS
        and not (row["status"] == "paused" and row.get("pause_requested") is True)
        for row in inventory["runs"]
    ):
        raise RecoveryError("Source snapshot must be terminal or paused/drained")
    if not 1 <= len(manifest["projects"]) <= 10:
        raise RecoveryError("Bounded QA restores between one and ten projects")
    module.local_docker()
    images = {
        "pg": manifest["postgres_image"],
        "redis": locked_image("REDIS_IMAGE"),
        "api": local_image(module, "adf-api-1"),
        "orch": local_image(module, "adf-orchestrator-1"),
        "frontend": local_image(module, "adf-frontend-1"),
    }
    resources = resource_preflight(module)
    namespace = secrets.token_hex(4)
    directory = ROOT / ".bootstrap/runtime-recovery" / namespace
    module.make_directory(directory, exclusive=True)
    module.make_directory(directory / "requests")
    credentials = {
        name: secrets.token_hex(32)
        for name in (
            "bootstrap-password",
            "api-password",
            "checkpoint-password",
            "redis-password",
            "admin-token",
            "orchestrator-token",
            "worker-token",
        )
    }
    credentials["redis.acl"] = (
        "user default off\nuser adf_orchestrator on >"
        + credentials["redis-password"]
        + " ~adf:executions +ping +xadd +xlen +xgroup +xreadgroup +xack"
    )
    rehearsal = Rehearsal(
        namespace, snapshot_id, module, credentials, images, directory, str(uuid4())
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "started_at": datetime.now(UTC).isoformat(),
        "resource_preflight": resources,
        "namespace": namespace,
        "source_snapshot_id": snapshot_id,
        "source_snapshot_manifest_sha256": hashlib.sha256(
            (source / "manifest.json").read_bytes()
        ).hexdigest(),
        "isolated_runtime_recovery_verified": False,
        "pending_fixture_provenance": "created only in isolated generation A",
        "source_services_changed": False,
        "source_credentials_copied": False,
        "paid_provider_calls": 0,
        "langfuse_restored": False,
        "source_unfinished_cli_recovery_verified": False,
        "qa_resources_preserved": True,
        "images": images,
    }
    try:
        rehearsal.prepare_generation("a", manifest, source, source / "database.dump")
        seed = rehearsal.seed()
        rehearsal.fixture_run_id = seed["run_id"]
        rehearsal.start("a", "orch")
        deadline = time.monotonic() + 90
        while True:
            rehearsal.approve_pending("a", seed["run_id"])
            state = durable_state(rehearsal, "a", seed["run_id"])
            if state["checkpoint_count"] > 0 and state["created_execution_ids"]:
                break
            if time.monotonic() > deadline:
                raise RecoveryError("Controlled pending checkpoint/outbox deadline")
            time.sleep(0.5)
        for service in ("orch", "frontend", "api", "redis"):
            rehearsal.guard(rehearsal.name("a", service))
            module.command(
                "docker",
                ["stop", "--time", "10", rehearsal.name("a", service)],
                timeout=30,
            )
        state = durable_state(rehearsal, "a", seed["run_id"])
        staged = directory / "durable-fixture"
        module.make_directory(staged)
        module.make_directory(staged / "git")
        module.make_directory(staged / "artifacts")
        # Preserve bytes already verified against the trusted private manifest.
        for artifact in manifest["artifacts"]:
            with (
                (source / "artifacts" / (artifact["id"] + ".bin")).open("rb") as stream,
                module.new_file(
                    staged / "artifacts" / (artifact["id"] + ".bin")
                ) as target,
            ):
                target.write(stream.read(module.MAX_ARTIFACT + 1))
        for project in manifest["projects"]:
            rehearsal.worker(
                "a",
                "bundle",
                {"project_id": project["id"]},
                output=staged / "git" / (project["id"] + ".bundle"),
            )
        dump = staged / "database.dump"
        module.command(
            "docker",
            [
                "exec",
                "--user",
                "postgres",
                rehearsal.name("a", "pg"),
                "pg_dump",
                "--no-password",
                "--username",
                "adf_restore",
                "--dbname",
                "adf_restore",
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--lock-wait-timeout=10s",
            ],
            output=dump,
            timeout=300,
            limit=module.MAX_ARCHIVE,
        )
        module.command(
            "docker", ["stop", "--time", "10", rehearsal.name("a", "pg")], timeout=30
        )
        module.write_json(
            staged / "checksums.json",
            {
                "provenance": "controlled pending fixture created only in generation A",
                "files": [
                    module.file_record(path, staged)
                    for path in sorted(staged.rglob("*"))
                    if path.is_file()
                ],
                "checkpoint_outbox": state,
            },
        )
        # No journal/process exists: the fixture was created, never claimed or spawned.
        rehearsal.prepare_generation(
            "b", manifest, staged, dump, previous_root=rehearsal.roots["a"]
        )
        restored = durable_state(rehearsal, "b", seed["run_id"])
        if state != restored:
            raise RecoveryError(
                "Restored checkpoint/outbox IDs differ from durable fixture"
            )
        report["checkpoint_outbox_restored"] = restored
        report["redis_initially_empty"] = True
        rehearsal.start("b", "orch")
        completed = drive(rehearsal, seed)
        jobs = completed["run"]["executions"]
        operations = {job["operation"] for job in jobs}
        if not {"agent_task", "test", "review", "git_commit", "integrate"}.issubset(
            operations
        ) or any(job["status"] != "succeeded" for job in jobs):
            raise RecoveryError("Recovered workflow evidence incomplete")
        after = rehearsal.worker("b", "inspect", {"project_id": seed["project_id"]})
        if (
            after["main_sha"] != seed["source_main_sha"]
            or not after["clean_main_checkout"]
        ):
            raise RecoveryError("QA main checkout changed")
        original_artifacts = 0
        for artifact in manifest["artifacts"]:
            data = rehearsal.http(
                "b", "GET", "/api/artifacts/" + artifact["id"] + "/content"
            )
            if (
                data["sha256"] != artifact["sha256"]
                or data["bytes"] != artifact["size"]
            ):
                raise RecoveryError("Original restored artifact mismatch")
            original_artifacts += 1
        historical = []
        for old in inventory["runs"]:
            current = rehearsal.http("b", "GET", "/api/runs/" + old["id"])
            expected = {
                item["id"]
                for item in inventory["executions"]
                if item["run_id"] == old["id"]
            }
            if {item["id"] for item in current["executions"]} != expected or any(
                item["status"] not in module.TERMINAL_EXECUTIONS
                for item in current["executions"]
            ):
                raise RecoveryError(
                    "Historical source work executed unexpectedly in QA"
                )
            historical.append(
                {
                    "id": old["id"],
                    "snapshot_status": old["status"],
                    "qa_status": current["status"],
                    "execution_ids_unchanged": True,
                }
            )
        report["historical_source_runs"] = historical
        missing = rehearsal.worker(
            "b",
            "missing",
            {
                "execution_id": str(uuid4()),
                "worker_id": rehearsal.worker_id,
            },
        )
        if not missing.get("missing_journal_fail_closed") or missing.get(
            "provider_spawned"
        ):
            raise RecoveryError("Missing supervisor journal did not fail closed")
        report.update(
            finished_at=datetime.now(UTC).isoformat(),
            isolation={stage: rehearsal.isolation(stage) for stage in ("a", "b")},
            frontend=rehearsal.frontend("b"),
            missing_journal=missing,
            isolated_runtime_recovery_verified=True,
            run_id=seed["run_id"],
            run_status="completed",
            recovered_execution_ids=restored["created_execution_ids"],
            completed_execution_ids=[job["id"] for job in jobs],
            completed_operations=sorted(operations),
            execution_count=len(jobs),
            original_artifacts_verified=original_artifacts,
            new_artifacts=len(
                rehearsal.http(
                    "b", "GET", "/api/runs/" + seed["run_id"] + "/artifacts"
                )["items"]
            ),
            duplicate_messages_acknowledged=completed[
                "duplicate_messages_acknowledged"
            ],
            main_unchanged=True,
            integration_status=completed["run"]["integration_status"],
            ext4_roots=rehearsal.roots,
            no_host_ports=True,
            no_source_mounts=True,
            mock_executor_supervisor_used=True,
            worker_consumer_network_tunnel=(
                "Docker-exec HTTP/Redis QA tunnel; production host networking untested"
            ),
        )
        module.write_json(directory / "report.json", report)
        return report
    except Exception as error:
        safe = (
            str(error)
            if isinstance(error, RecoveryError)
            else "QA administration failed; private output withheld"
        )
        report["failure"] = safe
        module.write_json(directory / "failed-report.json", report)
        raise RecoveryError(safe) from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--allow-isolated-runtime", action="store_true")
    arguments = parser.parse_args()
    try:
        result = run(arguments.snapshot, enabled=arguments.allow_isolated_runtime)
        # Print bounded metadata; API records and fresh tokens stay private.
        print(json.dumps(result, indent=2))
        return 0
    except RecoveryError as error:
        print(json.dumps({"ok": False, "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
