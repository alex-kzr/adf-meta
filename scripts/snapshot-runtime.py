"""Private quiescent ADF snapshots and explicitly isolated restore rehearsals.

No source runs, containers, volumes, credentials or Git refs are changed. Snapshot
is Windows-host orchestration; registered target repositories are read in Ubuntu
WSL ext4. Rehearsal creates new isolated resources and deliberately preserves them.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import shutil
import subprocess
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".bootstrap" / "runtime-snapshots"
IDENTIFIER = re.compile(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}")
SNAPSHOT_ID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}")
SHA256 = re.compile(r"[a-f0-9]{64}")
OBJECT_ID = re.compile(r"[a-f0-9]{40}|[a-f0-9]{64}")
MAX_JSON = 16 * 1024**2
MAX_ARTIFACT = 20 * 1024**2
MAX_ARCHIVE = 1024**3
MAX_TOTAL = 5 * 1024**3
TERMINAL_RUNS = {"completed", "failed", "cancelled"}
TERMINAL_EXECUTIONS = {"succeeded", "failed", "cancelled"}
FILE_PATTERN = re.compile(
    r"(?:database\.dump|inventory\.json|(?:artifacts|git)/"
    r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\.(?:bin|bundle))"
)


class SnapshotError(Exception):
    """Safe diagnostics never include response bodies, tokens or command output."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def identifier(value: object) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise SnapshotError("A canonical lowercase UUID is required")
    return str(UUID(value))


def no_links(path: Path) -> None:
    for current in (path, *path.parents):
        if current.is_symlink() or (
            hasattr(current, "is_junction") and current.is_junction()
        ):
            raise SnapshotError("Snapshot/configuration paths cannot contain links")


def private_path(path: Path, *, directory: bool = False) -> Path:
    no_links(path)
    resolved = path.resolve()
    if not resolved.is_relative_to((ROOT / ".bootstrap").resolve()):
        raise SnapshotError("Private files must stay inside umbrella .bootstrap")
    if path.exists():
        if directory and not path.is_dir():
            raise SnapshotError("Private directory is not a directory")
        if not directory and (not path.is_file() or path.stat().st_nlink != 1):
            raise SnapshotError("Private file is not a regular unlinked file")
        if os.name == "posix" and path.stat().st_mode & 0o077:
            raise SnapshotError("Private filesystem permissions must exclude others")
    return resolved


def make_directory(path: Path, *, exclusive: bool = False) -> None:
    private_path(path, directory=True)
    path.mkdir(mode=0o700, parents=True, exist_ok=not exclusive)
    if os.name == "posix":
        path.chmod(0o700)


def new_file(path: Path) -> BinaryIO:
    private_path(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(descriptor, "wb")


def write_json(path: Path, value: object) -> None:
    with new_file(path) as handle:
        handle.write(canonical(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def file_record(path: Path, base: Path) -> dict[str, Any]:
    private_path(path)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while block := handle.read(64 * 1024):
            size += len(block)
            if size > MAX_ARCHIVE:
                raise SnapshotError("Snapshot file exceeds the bounded archive budget")
            digest.update(block)
    return {
        "path": path.relative_to(base).as_posix(),
        "size": size,
        "sha256": digest.hexdigest(),
    }


def restricted_environment() -> dict[str, str]:
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "USERPROFILE",
        "LOCALAPPDATA",
        "HOME",
        "TEMP",
        "TMP",
        "LANG",
    }
    result = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    result.update({"GIT_TERMINAL_PROMPT": "0", "PGCONNECT_TIMEOUT": "5"})
    return result


def command(
    tool: str,
    arguments: list[str],
    *,
    timeout: int = 90,
    output: Path | None = None,
    input_file: Path | None = None,
    limit: int = MAX_JSON,
) -> bytes:
    executable = shutil.which(tool)
    if executable is None:
        raise SnapshotError("Required local administration tool is unavailable")
    if not 1 <= timeout <= 300:
        raise SnapshotError("Subprocess timeout must be bounded")
    captured = bytearray()
    failed = threading.Event()
    errors: list[BaseException] = []
    sink = new_file(output) if output is not None else None
    source = input_file.open("rb") if input_file is not None else None
    process: subprocess.Popen[bytes] | None = None

    def consume(stream: BinaryIO, target: BinaryIO | None, maximum: int) -> None:
        total = 0
        try:
            while block := stream.read(8192):
                total += len(block)
                if total > maximum:
                    failed.set()
                    return
                if target is not None:
                    target.write(block)
                elif process is not None and stream is process.stdout:
                    captured.extend(block)
        except (OSError, ValueError) as exc:
            errors.append(exc)
            failed.set()
        finally:
            stream.close()

    try:
        process = subprocess.Popen(  # noqa: S603 - fixed tools, shell=False
            [executable, *arguments],
            stdin=source or subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=restricted_environment(),
        )
        if process.stdout is None or process.stderr is None:
            raise SnapshotError("Subprocess pipes are unavailable")
        readers = [
            threading.Thread(
                target=consume, args=(process.stdout, sink, limit), daemon=True
            ),
            threading.Thread(
                target=consume, args=(process.stderr, None, 64 * 1024), daemon=True
            ),
        ]
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if failed.is_set() or time.monotonic() >= deadline:
                process.kill()  # Only this bounded administration helper.
                process.wait(timeout=10)
                raise SnapshotError("Administration helper exceeded time/output limits")
            time.sleep(0.02)
        for reader in readers:
            reader.join(timeout=5)
        if failed.is_set() or errors or any(reader.is_alive() for reader in readers):
            raise SnapshotError("Administration helper output was incomplete/oversized")
        if process.returncode:
            raise SnapshotError("Administration command failed; output withheld")
        if sink is not None:
            sink.flush()
            os.fsync(sink.fileno())
        return bytes(captured)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        if sink is not None:
            sink.close()
        if source is not None:
            source.close()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


@dataclass(frozen=True)
class Client:
    base_url: str
    token: str = field(repr=False)

    def __post_init__(self) -> None:
        parsed = urlsplit(self.base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise SnapshotError("Admin bearer tokens may be sent only to loopback HTTP")

    @classmethod
    def load(cls, base_url: str, token_file: Path) -> Client:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise SnapshotError("Admin bearer tokens may be sent only to loopback HTTP")
        expected = ROOT / ".bootstrap" / "secrets" / "admin-token"
        if private_path(token_file) != private_path(expected):
            raise SnapshotError("Use the generated umbrella admin-token file only")
        if token_file.stat().st_size > 256:
            raise SnapshotError("Generated admin token file exceeds its budget")
        token = token_file.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token):
            raise SnapshotError("Generated admin token file has an invalid format")
        return cls(base_url.rstrip("/"), token)

    def get(self, path: str, *, limit: int = MAX_JSON) -> bytes:
        if not path.startswith("/api/") or "#" in path:
            raise SnapshotError("Only the fixed read-only admin API routes are allowed")
        request = Request(  # noqa: S310 - validated loopback; no redirect/proxy
            self.base_url + path, headers={"Authorization": "Bearer " + self.token}
        )
        try:
            opener = build_opener(ProxyHandler({}), NoRedirect())
            with opener.open(request, timeout=15) as response:
                body: bytes = response.read(limit + 1)
            if len(body) > limit:
                raise SnapshotError("API response exceeds the bounded backup budget")
            return body
        except HTTPError as exc:
            raise SnapshotError(f"Read-only API returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, ConnectionError, http.client.HTTPException):
            raise SnapshotError("Read-only API is unavailable") from None

    def json(self, path: str) -> dict[str, Any]:
        value = json.loads(self.get(path))
        if not isinstance(value, dict):
            raise SnapshotError("API response must be an object")
        return value

    def pages(self, path: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(50):
            query = {"limit": "200"}
            if cursor is not None:
                query["cursor"] = cursor
            page = self.json(path + "?" + urlencode(query))
            items = page.get("items")
            if not isinstance(items, list) or any(
                not isinstance(v, dict) for v in items
            ):
                raise SnapshotError("API pagination shape is invalid")
            result.extend(items)
            next_cursor = page.get("next_cursor")
            if next_cursor is None:
                return result
            cursor = identifier(next_cursor)
            if cursor in seen:
                raise SnapshotError("API pagination cursor repeated")
            seen.add(cursor)
        raise SnapshotError("API inventory exceeds 10000 records")


@dataclass(frozen=True)
class Inventory:
    roots: list[str]
    projects: list[dict[str, Any]]
    runs: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    fingerprint: str


def collect(client: Client) -> Inventory:
    settings = client.json("/api/settings")
    roots = settings.get("allowed_roots")
    if (
        not isinstance(roots, list)
        or not roots
        or any(not isinstance(v, str) for v in roots)
    ):
        raise SnapshotError("Configured target roots are required")
    for value in roots:
        path = PurePosixPath(value)
        if (
            not path.is_absolute()
            or ".." in path.parts
            or len(path.parts) < 4
            or path.parts[1] != "home"
        ):
            raise SnapshotError(
                "Only configured regular-user ext4 target roots are allowed"
            )
    projects = client.pages("/api/projects")
    runs = client.pages("/api/runs")
    execution_counts: Counter[str] = Counter()
    artifacts: list[dict[str, Any]] = []
    if len({identifier(v.get("id")) for v in projects}) != len(projects):
        raise SnapshotError("Project identities are duplicated")
    if len({identifier(v.get("id")) for v in runs}) != len(runs):
        raise SnapshotError("Run identities are duplicated")
    for project in projects:
        identifier(project.get("id"))
        path = PurePosixPath(str(project.get("repo_path", "")))
        if not any(path.is_relative_to(PurePosixPath(root)) for root in roots):
            raise SnapshotError("Registered target repository escapes configured roots")
    for run in runs:
        run_id = identifier(run.get("id"))
        status = run.get("status")
        control = run.get("control", {})
        if status not in TERMINAL_RUNS and not (
            status == "paused"
            and isinstance(control, dict)
            and control.get("pause_requested") is True
        ):
            raise SnapshotError(
                f"Run {run_id} must be paused and drained before snapshot"
            )
        executions = client.json(f"/api/runs/{run_id}/executions").get("items")
        if not isinstance(executions, list):
            raise SnapshotError("Execution inventory is invalid")
        for execution in executions:
            if not isinstance(execution, dict):
                raise SnapshotError("Execution inventory is invalid")
            identifier(execution.get("id"))
            state = execution.get("status")
            if state not in TERMINAL_EXECUTIONS:
                raise SnapshotError(
                    "Active/created/uncertain executions block snapshots"
                )
            execution_counts[str(state)] += 1
        records = client.json(f"/api/runs/{run_id}/artifacts").get("items")
        if not isinstance(records, list):
            raise SnapshotError("Artifact inventory is invalid")
        for artifact in records:
            if not isinstance(artifact, dict):
                raise SnapshotError("Artifact inventory is invalid")
            identifier(artifact.get("id"))
            identifier(artifact.get("run_id"))
            identifier(artifact.get("execution_id"))
            size, digest = artifact.get("size"), artifact.get("sha256")
            if (
                not isinstance(size, int)
                or isinstance(size, bool)
                or not 0 <= size <= MAX_ARTIFACT
            ):
                raise SnapshotError("Artifact size exceeds the API limit")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                raise SnapshotError("Artifact checksum is invalid")
            artifacts.append(artifact)
    artifacts.sort(key=lambda row: row["id"])
    metrics = client.json("/api/metrics/overview")
    if metrics.get("active_executions") != 0 or metrics.get("executions") != dict(
        execution_counts
    ):
        raise SnapshotError("Global execution inventory is not fully drained")
    if len({v["id"] for v in artifacts}) != len(artifacts):
        raise SnapshotError("Artifact identities are duplicated")
    fingerprint = hashlib.sha256(
        canonical(
            {
                "settings": settings,
                "projects": projects,
                "runs": runs,
                "artifacts": artifacts,
            }
        )
    ).hexdigest()
    return Inventory(roots, projects, runs, artifacts, fingerprint)


# Fixed program, not a caller-supplied shell. It runs as the ordinary Ubuntu user.
WSL_PROGRAM = r"""
import json, os, pathlib, re, subprocess, sys, threading, time

mode, payload = sys.argv[1], json.loads(sys.argv[2])
if os.geteuid() == 0:
    raise SystemExit("Regular WSL user required")
home = pathlib.Path.home()
env = {
    "PATH": "/usr/bin:/bin",
    "HOME": str(home),
    "LANG": "C.UTF-8",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_OPTIONAL_LOCKS": "0",
}
base = [
    "/usr/bin/git",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "maintenance.auto=false",
    "-c",
    "gc.auto=0",
    "-c",
    "protocol.allow=never",
    "-c",
    "protocol.file.allow=always",
]


def run(argv, binary=False):
    p = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=False
    )
    out = bytearray()
    failed = threading.Event()

    def read(pipe, output):
        total = 0
        while True:
            block = pipe.read(8192)
            if not block:
                break
            total += len(block)
            if total > (1024**3 if binary and output else 2 * 1024**2):
                failed.set()
                break
            if output:
                if binary:
                    sys.stdout.buffer.write(block)
                else:
                    out.extend(block)
        pipe.close()

    ts = [
        threading.Thread(target=read, args=(p.stdout, True), daemon=True),
        threading.Thread(target=read, args=(p.stderr, False), daemon=True),
    ]
    for t in ts:
        t.start()
    deadline = time.monotonic() + 90
    while p.poll() is None:
        if failed.is_set() or time.monotonic() > deadline:
            p.kill()
            p.wait()
            raise SystemExit("Git helper budget exceeded")
        time.sleep(0.02)
    for t in ts:
        t.join(5)
    if p.returncode or failed.is_set() or any(t.is_alive() for t in ts):
        raise SystemExit("Git helper failed")
    return bytes(out)


def checked(path, roots, existing=True):
    p = pathlib.Path(path)
    if not p.is_absolute() or ".." in p.parts:
        raise SystemExit("Invalid target path")
    for x in [p, *p.parents]:
        if x.is_symlink():
            raise SystemExit("Target links are forbidden")
    resolved = p.resolve()
    if not any(resolved.is_relative_to(r) for r in roots):
        raise SystemExit("Target outside approved roots")
    anchor = resolved
    while not anchor.exists():
        anchor = anchor.parent
    if (
        run(["/usr/bin/findmnt", "-n", "-o", "FSTYPE", "-T", str(anchor)]).strip()
        != b"ext4"
    ):
        raise SystemExit("Target must be ext4")
    if existing and not resolved.exists():
        raise SystemExit("Target does not exist")
    return resolved


def git(path, args):
    return run(base + ["-C", str(path), *args])


def inspect(repo, roots):
    repo = checked(repo, roots)
    if git(repo, ["rev-parse", "--is-shallow-repository"]).strip() != b"false":
        raise SystemExit("Shallow backup is forbidden")
    common = pathlib.Path(
        git(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
        .decode()
        .strip()
    )
    checked(common, roots)
    if (repo / ".gitmodules").exists():
        raise SystemExit("Target submodules require a separate backup design")
    for part in git(repo, ["worktree", "list", "--porcelain"]).decode().split("\n\n"):
        lines = part.splitlines()
        if not lines:
            continue
        location = checked(lines[0].removeprefix("worktree "), [home / "ai-factory"])
        if git(location, ["status", "--porcelain", "--untracked-files=all"]):
            raise SystemExit("Dirty worktree must be preserved before backup")
        tip = git(location, ["rev-parse", "HEAD"]).decode().strip()
        uncovered = git(
            repo,
            ["rev-list", "--count", tip, "--not", "--single-worktree", "--all", "HEAD"],
        ).strip()
        if uncovered != b"0":
            raise SystemExit("Detached worktree HEAD needs a named ref before backup")
    refs = {"HEAD": git(repo, ["rev-parse", "HEAD"]).decode().strip()}
    for line in (
        git(repo, ["for-each-ref", "--format=%(objectname) %(refname)"])
        .decode()
        .splitlines()
    ):
        oid, name = line.split(" ", 1)
        refs[name] = oid
    return {
        "repo_path": str(repo),
        "refs": refs,
        "filesystem": "ext4",
        "clean_worktrees": True,
    }


if mode in {"inspect", "bundle"}:
    roots = [checked(v, [home / "ai-factory"]) for v in payload["roots"]]
    details = inspect(payload["repo_path"], roots)
    if mode == "inspect":
        print(json.dumps(details))
    else:
        run(
            base
            + [
                "-C",
                details["repo_path"],
                "bundle",
                "create",
                "--quiet",
                "-",
                "--single-worktree",
                "--all",
                "HEAD",
            ],
            binary=True,
        )
elif mode == "restore":
    sid = payload["snapshot_id"]
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}", sid):
        raise SystemExit("Invalid rehearsal id")
    parent = checked(
        home / "ai-factory" / "snapshot-rehearsals",
        [home / "ai-factory"],
        existing=False,
    )
    parent.mkdir(mode=0o700, exist_ok=True)
    destination = parent / sid
    if destination.exists():
        raise SystemExit("Rehearsal already exists")
    destination.mkdir(mode=0o700)
    source = pathlib.Path(payload["source"])
    if not source.is_absolute() or ".." in source.parts:
        raise SystemExit("Invalid bundle source")
    restored = {}
    for item in payload["projects"]:
        pid = item["id"]
        if not re.fullmatch(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", pid):
            raise SystemExit("Invalid project id")
        bundle = source / "git" / (pid + ".bundle")
        if bundle.is_symlink() or not bundle.is_file():
            raise SystemExit("Unsafe bundle source")
        target = destination / (pid + ".git")
        run(base + ["clone", "--mirror", "--no-hardlinks", str(bundle), str(target)])
        actual = {}
        for line in (
            git(target, ["for-each-ref", "--format=%(objectname) %(refname)"])
            .decode()
            .splitlines()
        ):
            oid, name = line.split(" ", 1)
            actual[name] = oid
        expected = {k: v for k, v in item["refs"].items() if k != "HEAD"}
        if actual != expected:
            raise SystemExit("Restored Git refs differ")
        git(target, ["cat-file", "-e", item["refs"]["HEAD"] + "^{commit}"])
        restored[pid] = {"path": str(target), "refs_verified": True}
    print(json.dumps({"destination": str(destination), "projects": restored}))
else:
    raise SystemExit("Invalid helper mode")
"""


def wsl(mode: str, payload: dict[str, Any], *, output: Path | None = None) -> bytes:
    if os.name != "nt":
        raise SnapshotError(
            "Run this contour's snapshot orchestrator on the Windows host"
        )
    return command(
        "wsl",
        [
            "-d",
            "Ubuntu",
            "--exec",
            "/usr/bin/python3",
            "-c",
            WSL_PROGRAM,
            mode,
            json.dumps(payload),
        ],
        timeout=300,
        output=output,
        limit=MAX_ARCHIVE if output else MAX_JSON,
    )


def postgres_image() -> str:
    for line in (ROOT / "infra/images.lock.env").read_text().splitlines():
        if line.startswith("POSTGRES_IMAGE="):
            image = line.split("=", 1)[1]
            if re.fullmatch(r"postgres:18[.][0-9]+@sha256:[a-f0-9]{64}", image):
                return image
    raise SnapshotError("Verified PostgreSQL 18 image digest is required")


def local_docker() -> None:
    host = json.loads(
        command(
            "docker",
            ["context", "inspect", "--format", "{{json .Endpoints.docker.Host}}"],
        )
    )
    if not isinstance(host, str) or not host.startswith(("npipe://", "unix://")):
        raise SnapshotError("Snapshot Docker context must be local")


def source_container() -> None:
    local_docker()
    data = json.loads(command("docker", ["inspect", "adf-postgres-1"]))[0]
    if (
        data.get("Config", {}).get("Labels", {}).get("com.docker.compose.project")
        != "adf"
        or data.get("Config", {}).get("Labels", {}).get("com.docker.compose.service")
        != "postgres"
        or data.get("Config", {}).get("Image") != postgres_image()
        or not data.get("State", {}).get("Running")
    ):
        raise SnapshotError("Source must be the locked running ADF PostgreSQL service")


INVENTORY_SQL = """
SELECT json_build_object(
'projects',COALESCE((SELECT json_agg(json_build_object(
'id',id,'repo_path',repo_path) ORDER BY id)
FROM control.projects),'[]'::json),
'runs',COALESCE((SELECT json_agg(json_build_object(
'id',id,'project_id',project_id,'status',status,'revision',revision,
'event_sequence',event_sequence,'pause_requested',pause_requested,
'cancel_requested',cancel_requested) ORDER BY id) FROM runtime.runs),'[]'::json),
'executions',COALESCE((SELECT json_agg(json_build_object(
'id',id,'run_id',run_id,'status',status,'epoch',epoch) ORDER BY id)
FROM runtime.executions),'[]'::json),
'artifacts',COALESCE((SELECT json_agg(json_build_object(
'id',id,'run_id',run_id,'execution_id',execution_id,'storage_key',storage_key,
'sha256',sha256,'size',size) ORDER BY id) FROM runtime.artifacts),'[]'::json));
"""


def database_inventory(container: str, *, rehearsal: bool = False) -> dict[str, Any]:
    user, database = (
        ("adf_restore", "adf_restore") if rehearsal else ("adf_bootstrap", "adf")
    )
    response = command(
        "docker",
        [
            "exec",
            "--user",
            "postgres",
            container,
            "psql",
            "--no-psqlrc",
            "--no-password",
            "--username",
            user,
            "--dbname",
            database,
            "--tuples-only",
            "--no-align",
            "--set",
            "ON_ERROR_STOP=1",
            "--command",
            INVENTORY_SQL,
        ],
    )
    data = json.loads(response)
    if not isinstance(data, dict):
        raise SnapshotError("Database inventory shape is invalid")
    return data


def validate_api_database(api: Inventory, database: dict[str, Any]) -> None:
    projects = [{key: row[key] for key in ("id", "repo_path")} for row in api.projects]
    runs = [
        {
            **{
                key: row[key]
                for key in ("id", "project_id", "status", "revision", "event_sequence")
            },
            "pause_requested": row["control"]["pause_requested"],
            "cancel_requested": row["control"]["cancel_requested"],
        }
        for row in api.runs
    ]
    executions = [
        {key: row[key] for key in ("id", "run_id", "status", "epoch")}
        for run in api.runs
        for row in run["executions"]
    ]
    artifacts = [
        {key: row[key] for key in ("id", "run_id", "execution_id", "sha256", "size")}
        for row in api.artifacts
    ]
    expected = {
        "projects": projects,
        "runs": runs,
        "executions": executions,
        "artifacts": artifacts,
    }
    for key, rows in expected.items():
        rows.sort(key=lambda row: row["id"])
        actual = database.get(key)
        if key == "artifacts" and isinstance(actual, list):
            actual = [
                {
                    name: value[name]
                    for name in ("id", "run_id", "execution_id", "sha256", "size")
                }
                for value in actual
            ]
        if rows != actual:
            raise SnapshotError(
                "API and source database referential inventories differ"
            )


def bundle_refs(path: Path) -> dict[str, str]:
    refs: dict[str, str] = {}
    with path.open("rb") as handle:
        first = handle.readline(256)
        if first not in {b"# v2 git bundle\n", b"# v3 git bundle\n"}:
            raise SnapshotError("Unsupported Git bundle header")
        for _ in range(10000):
            line = handle.readline(2048)
            if line == b"\n":
                return refs
            if not line or len(line) >= 2048 or line.startswith(b"-"):
                raise SnapshotError("Git bundle must be bounded and self-contained")
            if line.startswith(b"@"):
                continue
            parts = line.decode("ascii").strip().split(" ", 1)
            if (
                len(parts) != 2
                or not OBJECT_ID.fullmatch(parts[0])
                or not (parts[1] == "HEAD" or parts[1].startswith("refs/"))
            ):
                raise SnapshotError("Git bundle reference header is invalid")
            if parts[1] in refs:
                raise SnapshotError("Git bundle reference is duplicated")
            refs[parts[1]] = parts[0]
    raise SnapshotError("Git bundle reference count exceeds its budget")


def snapshot(client: Client) -> dict[str, Any]:
    before = collect(client)  # No private snapshot directory on a failed drain gate.
    source_container()
    git_before: dict[str, dict[str, Any]] = {}
    for project in before.projects:
        payload = {"repo_path": project["repo_path"], "roots": before.roots}
        git_before[project["id"]] = json.loads(wsl("inspect", payload))
    db_before = database_inventory("adf-postgres-1")
    validate_api_database(before, db_before)
    sid = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-") + os.urandom(4).hex()
    directory = PRIVATE / sid
    make_directory(PRIVATE)
    make_directory(directory, exclusive=True)
    make_directory(directory / "artifacts")
    make_directory(directory / "git")
    files: list[dict[str, Any]] = []
    total = 0
    for artifact in before.artifacts:
        data = client.get(
            f"/api/artifacts/{artifact['id']}/content", limit=MAX_ARTIFACT
        )
        if (
            len(data) != artifact["size"]
            or hashlib.sha256(data).hexdigest() != artifact["sha256"]
        ):
            raise SnapshotError("Downloaded artifact size/checksum differs from ledger")
        path = directory / "artifacts" / (artifact["id"] + ".bin")
        with new_file(path) as handle:
            handle.write(data)
        files.append(file_record(path, directory))
        total += len(data)
        if total > MAX_TOTAL:
            raise SnapshotError("Snapshot exceeds the total private disk budget")
    for project in before.projects:
        path = directory / "git" / (project["id"] + ".bundle")
        payload = {"repo_path": project["repo_path"], "roots": before.roots}
        wsl("bundle", payload, output=path)
        if bundle_refs(path) != git_before[project["id"]]["refs"]:
            raise SnapshotError("Git refs changed during bundle creation")
        files.append(file_record(path, directory))
        total += path.stat().st_size
        if total > MAX_TOTAL:
            raise SnapshotError("Snapshot exceeds the total private disk budget")
    dump = directory / "database.dump"
    command(
        "docker",
        [
            "exec",
            "--user",
            "postgres",
            "adf-postgres-1",
            "pg_dump",
            "--no-password",
            "--username",
            "adf_bootstrap",
            "--dbname",
            "adf",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--lock-wait-timeout=10s",
        ],
        timeout=300,
        output=dump,
        limit=MAX_ARCHIVE,
    )
    with dump.open("rb") as header:
        archive_header = header.read(5)
    if not dump.stat().st_size or archive_header != b"PGDMP":
        raise SnapshotError("PostgreSQL custom archive header is missing")
    files.append(file_record(dump, directory))
    db_after = database_inventory("adf-postgres-1")
    if db_before != db_after or before.fingerprint != collect(client).fingerprint:
        raise SnapshotError(
            "Runtime inventory changed during backup; snapshot is incomplete"
        )
    for project in before.projects:
        actual = json.loads(
            wsl("inspect", {"repo_path": project["repo_path"], "roots": before.roots})
        )
        if actual != git_before[project["id"]]:
            raise SnapshotError("Git refs/worktree state changed during backup")
    inventory_file = directory / "inventory.json"
    write_json(inventory_file, db_before)
    files.append(file_record(inventory_file, directory))
    if sum(item["size"] for item in files) > MAX_TOTAL:
        raise SnapshotError("Snapshot exceeds the total private disk budget")
    manifest = {
        "schema_version": 1,
        "snapshot_id": sid,
        "created_at": datetime.now(UTC).isoformat(),
        "complete": True,
        "consistency_strategy": "quiescence-and-pre-post-checks",
        "maintenance_fence": False,
        "postgres_image": postgres_image(),
        "source_database": "adf",
        "api_fingerprint": before.fingerprint,
        "projects": [{"id": p["id"], **git_before[p["id"]]} for p in before.projects],
        "artifacts": db_before["artifacts"],
        "files": files,
        "excluded": [
            "provider/OAuth credentials",
            "environment files",
            "database roles/passwords",
            "Redis transport",
            "Langfuse",
            "worker journals",
            "dirty/untracked/ignored worktree bytes",
            "hooks/repository configuration",
        ],
    }
    write_json(directory / "manifest.json", manifest)
    checksum = file_record(directory / "manifest.json", directory)["sha256"]
    with new_file(directory / "manifest.sha256") as handle:
        handle.write((checksum + "\n").encode())
    verify(directory)
    return {
        "snapshot_created": True,
        "snapshot_id": sid,
        "manifest": str(directory / "manifest.json"),
        "files": len(files),
        "bytes": sum(v["size"] for v in files),
        "services_changed": False,
        "restore_tested": False,
    }


def verify(directory: Path) -> dict[str, Any]:
    private_path(directory, directory=True)
    if directory.parent.resolve() != PRIVATE.resolve() or not SNAPSHOT_ID.fullmatch(
        directory.name
    ):
        raise SnapshotError("Select an existing named runtime snapshot only")
    manifest_path = directory / "manifest.json"
    private_path(manifest_path)
    checksum_path = directory / "manifest.sha256"
    private_path(checksum_path)
    if manifest_path.stat().st_size > MAX_JSON or checksum_path.stat().st_size > 128:
        raise SnapshotError("Manifest/checksum exceeds its budget")
    digest = checksum_path.read_text().strip()
    if (
        not SHA256.fullmatch(digest)
        or file_record(manifest_path, directory)["sha256"] != digest
    ):
        raise SnapshotError("Snapshot manifest checksum differs")
    manifest = json.loads(manifest_path.read_bytes())
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or manifest.get("complete") is not True
        or manifest.get("snapshot_id") != directory.name
    ):
        raise SnapshotError("Snapshot manifest is incomplete/unsupported")
    image = manifest.get("postgres_image")
    if not isinstance(image, str) or not re.fullmatch(
        r"postgres:18[.][0-9]+@sha256:[a-f0-9]{64}", image
    ):
        raise SnapshotError("Snapshot PostgreSQL image is not pinned")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) > 20000:
        raise SnapshotError("Snapshot file inventory is invalid")
    names: set[str] = set()
    total = 0
    for item in files:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not FILE_PATTERN.fullmatch(item["path"])
        ):
            raise SnapshotError("Snapshot contains an unsafe/unexpected relative path")
        name = item["path"]
        if name in names:
            raise SnapshotError("Snapshot file is duplicated")
        names.add(name)
        actual = file_record(directory / name, directory)
        if actual != item:
            raise SnapshotError("Snapshot file size/checksum differs")
        total += actual["size"]
    if not {"database.dump", "inventory.json"}.issubset(names) or total > MAX_TOTAL:
        raise SnapshotError("Snapshot is incomplete/oversized")
    inventory_path = directory / "inventory.json"
    if inventory_path.stat().st_size > MAX_JSON:
        raise SnapshotError("Referential inventory exceeds its budget")
    inventory = json.loads(inventory_path.read_bytes())
    if not isinstance(inventory, dict) or set(inventory) != {
        "projects",
        "runs",
        "executions",
        "artifacts",
    }:
        raise SnapshotError("Referential inventory shape is invalid")
    for rows in inventory.values():
        if not isinstance(rows, list) or len(rows) > 10000:
            raise SnapshotError("Referential inventory record budget exceeded")
        if any(not isinstance(row, dict) for row in rows):
            raise SnapshotError("Referential inventory records are invalid")
        ids = [identifier(row.get("id")) for row in rows]
        if len(ids) != len(set(ids)):
            raise SnapshotError("Referential inventory IDs are duplicated")
    projects = manifest.get("projects")
    artifacts = manifest.get("artifacts")
    if not isinstance(projects, list) or not isinstance(artifacts, list):
        raise SnapshotError("Manifest project/artifact inventories are invalid")
    project_paths = {
        identifier(row["id"]): row["repo_path"] for row in inventory["projects"]
    }
    manifest_paths = {
        identifier(row["id"]): row["repo_path"]
        for row in projects
        if isinstance(row, dict)
    }
    if len(manifest_paths) != len(projects) or manifest_paths != project_paths:
        raise SnapshotError("Manifest Git projects differ from database inventory")
    if artifacts != inventory["artifacts"]:
        raise SnapshotError("Manifest artifacts differ from database inventory")
    run_ids = {row["id"] for row in inventory["runs"]}
    execution_ids = {row["id"] for row in inventory["executions"]}
    for row in inventory["runs"]:
        if row.get("project_id") not in project_paths or (
            row.get("status") not in TERMINAL_RUNS
            and not (
                row.get("status") == "paused" and row.get("pause_requested") is True
            )
        ):
            raise SnapshotError("Restorable run references/state are not drained")
    for row in inventory["executions"]:
        if (
            row.get("run_id") not in run_ids
            or row.get("status") not in TERMINAL_EXECUTIONS
        ):
            raise SnapshotError(
                "Restorable execution references/state are not terminal"
            )
    for row in artifacts:
        if (
            row.get("run_id") not in run_ids
            or row.get("execution_id") not in execution_ids
        ):
            raise SnapshotError("Restorable artifact parent references are missing")
    expected_names = {"database.dump", "inventory.json"}
    expected_names.update(f"git/{pid}.bundle" for pid in project_paths)
    expected_names.update(f"artifacts/{identifier(row['id'])}.bin" for row in artifacts)
    if names != expected_names:
        raise SnapshotError("Manifest contains omitted or unexpected payload files")
    with (directory / "database.dump").open("rb") as archive:
        if archive.read(5) != b"PGDMP":
            raise SnapshotError("PostgreSQL custom archive header is missing")
    for project in manifest.get("projects", []):
        pid = identifier(project.get("id"))
        if f"git/{pid}.bundle" not in names or bundle_refs(
            directory / "git" / (pid + ".bundle")
        ) != project.get("refs"):
            raise SnapshotError("Snapshot Git refs differ from the bundle")
    for artifact in manifest.get("artifacts", []):
        aid = identifier(artifact.get("id"))
        identifier(artifact.get("storage_key"))
        record = next((v for v in files if v["path"] == f"artifacts/{aid}.bin"), None)
        if (
            record is None
            or record["sha256"] != artifact.get("sha256")
            or record["size"] != artifact.get("size")
        ):
            raise SnapshotError("Snapshot artifact bytes do not match ledger metadata")
    return manifest


def windows_to_wsl(path: Path) -> str:
    path = private_path(path, directory=True)
    if not path.drive or len(path.drive) != 2:
        raise SnapshotError("WSL snapshot transfer requires an ordinary Windows drive")
    return "/mnt/" + path.drive[0].lower() + "/" + "/".join(path.parts[1:])


def rehearse(directory: Path, *, explicitly_enabled: bool) -> dict[str, Any]:
    if not explicitly_enabled:
        raise SnapshotError("Isolated restore requires --allow-isolated-restore")
    manifest = verify(directory)
    local_docker()
    container = "adf-snapshot-qa-" + directory.name.lower()
    if len(container) > 63:
        raise SnapshotError("Generated QA resource name exceeds its limit")
    # Exclusive names, network none, no host ports or source-volume mounts.
    command(
        "docker",
        [
            "run",
            "--detach",
            "--name",
            container,
            "--network",
            "none",
            "--memory",
            "512m",
            "--cpus",
            "1",
            "--label",
            "adf.snapshot.rehearsal=" + directory.name,
            "--env",
            "POSTGRES_USER=adf_restore",
            "--env",
            "POSTGRES_DB=adf_restore",
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            manifest["postgres_image"],
        ],
    )
    deadline = time.monotonic() + 60
    while True:
        try:
            command(
                "docker",
                [
                    "exec",
                    container,
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
            break
        except SnapshotError:
            if time.monotonic() >= deadline:
                raise SnapshotError(
                    "Isolated PostgreSQL did not become ready"
                ) from None
            time.sleep(1)
    command(
        "docker",
        [
            "exec",
            "--interactive",
            "--user",
            "postgres",
            container,
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
        input_file=directory / "database.dump",
    )
    restored = database_inventory(container, rehearsal=True)
    expected = json.loads((directory / "inventory.json").read_bytes())
    if restored != expected:
        raise SnapshotError("Restored database referential inventory differs")
    artifacts = directory / "rehearsal-artifacts"
    make_directory(artifacts, exclusive=True)
    for row in restored.get("artifacts", []):
        source = directory / "artifacts" / (identifier(row["id"]) + ".bin")
        target = artifacts / identifier(row["storage_key"])
        with source.open("rb") as stream, new_file(target) as output:
            shutil.copyfileobj(stream, output, 64 * 1024)
        record = file_record(target, artifacts)
        if record["sha256"] != row["sha256"] or record["size"] != row["size"]:
            raise SnapshotError(
                "Restored artifact differs from restored database metadata"
            )
    git = json.loads(
        wsl(
            "restore",
            {
                "snapshot_id": directory.name,
                "source": windows_to_wsl(directory),
                "projects": manifest["projects"],
            },
        )
    )
    report = {
        "isolated_restore_verified": True,
        "snapshot_id": directory.name,
        "database_container": container,
        "database": "adf_restore",
        "database_inventory_matches": True,
        "artifact_count": len(restored.get("artifacts", [])),
        "git": git,
        "source_services_changed": False,
        "qa_resources_preserved": True,
        "runtime_recovery_verified": False,
    }
    write_json(directory / "rehearsal-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--snapshot", action="store_true")
    actions.add_argument("--verify", metavar="SNAPSHOT_ID")
    actions.add_argument("--rehearse", metavar="SNAPSHOT_ID")
    parser.add_argument("--allow-isolated-restore", action="store_true")
    parser.add_argument("--api-url", default="http://127.0.0.1:8080")
    parser.add_argument(
        "--admin-token-file", type=Path, default=ROOT / ".bootstrap/secrets/admin-token"
    )
    args = parser.parse_args()
    try:
        if args.verify or args.rehearse:
            sid = args.verify or args.rehearse
            if not SNAPSHOT_ID.fullmatch(sid):
                raise SnapshotError("Use a generated snapshot identifier, not a path")
            directory = PRIVATE / sid
            if args.rehearse:
                result = rehearse(
                    directory, explicitly_enabled=args.allow_isolated_restore
                )
            else:
                manifest = verify(directory)
                result = {
                    "manifest_verified": True,
                    "snapshot_id": sid,
                    "files": len(manifest["files"]),
                    "restore_tested": False,
                }
        else:
            if args.allow_isolated_restore:
                raise SnapshotError(
                    "Restore permission flag is valid only with --rehearse"
                )
            client = Client.load(args.api_url, args.admin_token_file)
            if args.snapshot:
                result = snapshot(client)
            else:
                inventory = collect(client)
                result = {
                    "api_drained": True,
                    "projects": len(inventory.projects),
                    "runs": len(inventory.runs),
                    "artifacts": len(inventory.artifacts),
                    "snapshot_created": False,
                    "git_clean_ext4_checked": False,
                }
        print(json.dumps(result, indent=2))
        return 0
    except SnapshotError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "Snapshot operation failed; private details withheld",
                }
            )
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
