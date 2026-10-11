"""Mock-only ext4 execution against a disconnected QA API through Docker exec."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

MAX = 30 * 1024**2
HOME: Path = Path.home()
BASE: Path = HOME / "ai-factory" / "recovery-rehearsals"
CURRENT_ROOT: Path | None = None


def canonical_id(value: Any) -> str:
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError("Canonical UUID required")
    return value


def environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(HOME),
        "LANG": "C.UTF-8",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "ADF_TELEMETRY_ENABLED": "false",
        "LANGSMITH_TRACING": "false",
    }


def command(
    arguments: list[str], *, body: bytes | None = None, maximum: int = MAX
) -> bytes:
    if arguments[0] not in {"/usr/bin/git", "/usr/bin/docker", "/usr/bin/findmnt"}:
        raise ValueError("Fixed local QA administration executable required")
    spec = importlib.util.spec_from_file_location(
        "adf_recovery_bound", Path(__file__).with_name("snapshot-runtime.py")
    )
    if spec is None or spec.loader is None:
        raise ValueError("Bounded helper unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    setattr(module, "restricted_environment", environment)
    source = None
    if body is not None:
        if CURRENT_ROOT is None or not CURRENT_ROOT.exists():
            raise ValueError("Validated QA root required for private request bytes")
        requests = CURRENT_ROOT / ".requests"
        requests.mkdir(mode=0o700, exist_ok=True)
        source = requests / (uuid4().hex + ".json")
        descriptor = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(body)
    result: bytes = module.command(
        arguments[0], arguments[1:], timeout=90, input_file=source, limit=maximum
    )
    return result


def git(root: Path, *arguments: str) -> bytes:
    return command(
        [
            "/usr/bin/git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "protocol.allow=never",
            "-c",
            "protocol.file.allow=always",
            "-C",
            str(root),
            *arguments,
        ]
    )


def root_for(value: dict[str, Any]) -> Path:
    namespace, stage = value["namespace"], value["stage"]
    if (
        not re.fullmatch(r"[a-f0-9]{8}", namespace)
        or stage not in {"a", "b"}
        or getattr(os, "geteuid", lambda: 0)() == 0
    ):
        raise ValueError("Regular user and generated QA namespace required")
    root: Path = BASE / namespace / ("stage-" + stage)
    for path in (root, *root.parents):
        if path.is_symlink():
            raise ValueError("QA path links forbidden")
    anchor = root
    while not anchor.exists():
        anchor = anchor.parent
    if (
        command(["/usr/bin/findmnt", "-n", "-o", "FSTYPE", "-T", str(anchor)]).strip()
        != b"ext4"
    ):
        raise ValueError("QA root must be ext4")
    return root


def tunnel(container: str, value: dict[str, Any]) -> dict[str, Any]:
    if not re.fullmatch(r"adf-recovery-[a-f0-9]{8}-[ab]-api", container):
        raise ValueError("QA API container required")
    result = json.loads(
        command(
            [
                "/usr/bin/docker",
                "exec",
                "--interactive",
                container,
                "python",
                "/opt/adf-recovery-http.py",
            ],
            body=json.dumps(value).encode(),
        )
    )
    if not isinstance(result, dict) or result.get("qa_tunnel_failed"):
        raise ValueError("QA tunnel shape")
    return result


def prepare(value: dict[str, Any], root: Path) -> dict[str, Any]:
    if root.exists():
        raise ValueError("QA root already exists")
    root.mkdir(mode=0o700, parents=True)
    for name in ("projects", "worktrees", "journals", "locks", "config"):
        (root / name).mkdir(mode=0o700)
    source = Path(value["source"])
    if not source.is_absolute() or ".." in source.parts or source.is_symlink():
        raise ValueError("Verified private bundle source required")
    repos = {}
    for project in value["projects"]:
        project_id = canonical_id(project["id"])
        repo = root / "projects" / project_id / "repo"
        repo.mkdir(mode=0o700, parents=True)
        bundle = source / "git" / (project_id + ".bundle")
        if bundle.is_symlink() or not bundle.is_file():
            raise ValueError("Unsafe bundle source")
        git(
            repo, "clone", "--mirror", "--no-hardlinks", str(bundle), str(repo / ".git")
        )
        git(repo, "config", "--local", "core.bare", "false")
        head = project["refs"]["HEAD"]
        if not re.fullmatch(r"[a-f0-9]{40}", head):
            raise ValueError("Pinned SHA-1 HEAD required")
        git(repo, "checkout", "--force", "--detach", head)
        if git(repo, "rev-parse", "HEAD").decode().strip() != head:
            raise ValueError("Restored QA HEAD mismatch")
        for name, oid in project["refs"].items():
            if (
                name.startswith("refs/")
                and git(repo, "rev-parse", name).decode().strip() != oid
            ):
                raise ValueError("Restored QA ref mismatch")
        repos[project_id] = str(repo)
    token = value["worker_token"]
    if not isinstance(token, str) or not re.fullmatch(r"[a-f0-9]{64}", token):
        raise ValueError("Fresh generated worker token required")
    path = root / "config" / "worker-token"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(token + "\n")
    return {
        "root": str(root),
        "repos": repos,
        "ext4": True,
        "source_refs_changed": False,
    }


def execute(value: dict[str, Any], root: Path) -> dict[str, Any]:
    import adf_runtime_worker.executor as executor_module
    import httpx
    from adf_runtime_worker.adapters import MockAdapter
    from adf_runtime_worker.client import ApiClient
    from adf_runtime_worker.executor import Executor
    from adf_runtime_worker.models import WorkerError
    from adf_runtime_worker.supervisor import ExecutionSupervisor

    container = value["container"]
    execution_id, run_id = (
        canonical_id(value["execution_id"]),
        canonical_id(value["run_id"]),
    )
    worker_id = canonical_id(value["worker_id"])

    class Transport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            raw = request.read()
            reply = tunnel(
                container,
                {
                    "method": request.method,
                    "path": str(request.url.raw_path.decode()),
                    "body": json.loads(raw) if raw else None,
                },
            )
            return httpx.Response(reply["status"], json=reply["data"], request=request)

    def only_mock(provider: str, executable: str | None = None) -> MockAdapter:
        if provider != "mock":
            raise WorkerError(
                "PERMISSION_DENIED", "Recovery never invokes provider CLIs"
            )
        return MockAdapter()

    setattr(executor_module, "provider_adapter", only_mock)
    os.environ["ADF_TELEMETRY_ENABLED"] = "false"
    os.environ["LANGSMITH_TRACING"] = "false"
    executor = Executor(
        root,
        provider_paths={
            "codex": "/nonexistent/recovery-no-provider",
            "claude": "/nonexistent/recovery-no-provider",
        },
    )
    with ApiClient(
        "http://127.0.0.1:8080",
        root / "config/worker-token",
        worker_id,
        transport=Transport(),
    ) as ledger:
        detail = tunnel(
            container, {"method": "GET", "path": "/internal/executions/" + execution_id}
        )["data"]
        if detail.get("run_id") != run_id:
            raise ValueError("Only the controlled QA run can execute")
        claim = ledger.claim(execution_id)
        if claim.get("terminal"):
            return {
                "execution_id": execution_id,
                "terminal_duplicate_acknowledged": True,
                "adapter_invocations": 0,
            }
        job = claim["request"]
        repo = Path(job["project"]["repo_path"])
        if not repo.is_relative_to(root / "projects") or not job["project"][
            "allowed_root"
        ] == str(root / "projects"):
            raise ValueError("Restored execution path escapes QA root")
        if (
            job["operation"] in {"agent_task", "planner", "review"}
            and job.get("agent", {}).get("provider") != "mock"
        ):
            raise ValueError("Only controlled mock agents may execute")
        if (
            job.get("agent", {}).get("skills")
            or job.get("agent", {}).get("mcp_servers")
            or job.get("agent", {}).get("tools")
        ):
            raise ValueError("Recovery mock has no external registries")
        supervisor = ExecutionSupervisor(
            ledger, executor, executor.workspaces.journal_for(execution_id)
        )
        result = supervisor.run(claim)
        return {
            "execution_id": execution_id,
            "status": result.get("status"),
            "operation": job["operation"],
            "error_code": result.get("error_code"),
            "commit_sha": result.get("commit_sha"),
            "integration_status": result.get("integration_status"),
            "process_stopped": result.get("process_stopped"),
            "paid_provider_calls": 0,
        }


def missing(value: dict[str, Any], root: Path) -> dict[str, Any]:
    from adf_runtime_worker.executor import Executor
    from adf_runtime_worker.models import WorkerError
    from adf_runtime_worker.service import WorkerService

    execution_id = canonical_id(value["execution_id"])
    service = object.__new__(WorkerService)
    service.executor = Executor(root, provider_paths={})
    service.worker_id = canonical_id(value["worker_id"])
    try:
        service._reconcile(execution_id)
    except WorkerError as error:
        if error.code != "EXECUTION_UNCERTAIN":
            raise
        return {
            "missing_journal_fail_closed": True,
            "error_code": error.code,
            "provider_spawned": False,
        }
    raise ValueError("Missing journal unexpectedly reconciled")


def main() -> int:
    global CURRENT_ROOT
    try:
        raw = sys.stdin.buffer.read(MAX + 1)
        if len(raw) > MAX:
            raise ValueError("QA payload budget")
        value = json.loads(raw)
        root = root_for(value)
        CURRENT_ROOT = root
        mode = value["mode"]
        if mode == "prepare":
            result = prepare(value, root)
        elif mode == "execute":
            result = execute(value, root)
        elif mode == "missing":
            result = missing(value, root)
        elif mode == "bundle":
            repo = root / "projects" / canonical_id(value["project_id"]) / "repo"
            sys.stdout.buffer.write(
                git(
                    repo,
                    "bundle",
                    "create",
                    "--quiet",
                    "-",
                    "--single-worktree",
                    "--all",
                    "HEAD",
                )
            )
            return 0
        elif mode == "inspect":
            repo = root / "projects" / canonical_id(value["project_id"]) / "repo"
            result = {
                "main_sha": git(repo, "rev-parse", "refs/heads/main").decode().strip(),
                "clean_main_checkout": not bool(git(repo, "status", "--porcelain")),
                "journal_count": len(list((root / "journals").glob("*.json"))),
            }
        else:
            raise ValueError("Fixed recovery mode required")
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except Exception:
        print('{"qa_worker_failed":true}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
