"""Canonical ADF Compose entrypoint; existing-data migration is fail-closed."""

from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / ".bootstrap/compose.adf-observability.json"
SERVICE_MAP = {
    "langfuse-web": "langfuse-web",
    "langfuse-worker": "langfuse-worker",
    "postgres": "langfuse-postgres",
    "redis": "langfuse-redis",
    "minio": "langfuse-minio",
    "clickhouse": "langfuse-clickhouse",
}
CORE = [
    "postgres",
    "redis",
    "migrator",
    "api",
    "orchestrator",
    "frontend",
    "otel-collector",
]
CONTAINERS = {
    **{name: "adf-" + name + "-1" for name in CORE},
    **{new: "adf-langfuse-" + old + "-1" for old, new in SERVICE_MAP.items()},
}
START_SERVICES = [name for name in CORE if name != "migrator"] + list(
    SERVICE_MAP.values()
)
APPLY_ATTEMPTED = False


class GroupError(Exception):
    """Closed errors never echo resolved environments or Docker configuration."""


def docker(
    args: list[str], timeout: float = 45, *, capture_stderr: bool = False
) -> bytes:
    executable = shutil.which("docker")
    if executable is None:
        raise GroupError("DOCKER_UNAVAILABLE")
    result = subprocess.run(
        [executable, *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if result.returncode:
        raise GroupError("DOCKER_COMMAND_FAILED_OUTPUT_WITHHELD")
    # Docker logs puts container stderr in its own stderr pipe. Keep both
    # streams private so durability errors cannot disappear from the guard.
    return result.stdout + (b"\n" + result.stderr if capture_stderr else b"")


def grouped_model(original: dict[str, Any]) -> dict[str, Any]:
    if set(original.get("services", {})) != set(SERVICE_MAP):
        raise GroupError("LANGFUSE_COMPONENT_SET_CHANGED")
    model: dict[str, Any] = {
        "name": "adf",
        "services": {},
        "volumes": {},
        "networks": {},
    }
    for old, new in SERVICE_MAP.items():
        service = copy.deepcopy(original["services"][old])
        service["container_name"] = CONTAINERS[new]
        dependencies = service.get("depends_on", {})
        if not isinstance(dependencies, dict) or set(dependencies) - set(SERVICE_MAP):
            raise GroupError("UNEXPECTED_SERVICE_REFERENCE")
        service["depends_on"] = {
            SERVICE_MAP[name]: settings for name, settings in dependencies.items()
        }
        for volume in service.get("volumes", []):
            if (
                not isinstance(volume, dict)
                or volume.get("type") != "volume"
                or volume.get("source") not in original.get("volumes", {})
            ):
                raise GroupError("UNEXPECTED_VOLUME_REFERENCE")
        networks = service.get("networks", {"default": None})
        if not isinstance(networks, dict) or set(networks) - set(
            original.get("networks", {})
        ):
            raise GroupError("UNEXPECTED_NETWORK_REFERENCE")
        translated = {}
        for name, settings in networks.items():
            selected = "langfuse-existing" if name == "default" else name
            values = copy.deepcopy(settings or {})
            values["aliases"] = sorted(set(values.get("aliases", [])) | {old})
            translated[selected] = values
        service["networks"] = translated
        model["services"][new] = service
    for name, volume in original.get("volumes", {}).items():
        existing = volume.get("name")
        if existing != "adf-langfuse_" + name:
            raise GroupError("UNEXPECTED_EXISTING_VOLUME")
        model["volumes"][name] = {"external": True, "name": existing}
    for name, network in original.get("networks", {}).items():
        existing = network.get("name")
        if {"default": "adf-langfuse_default", "telemetry": "adf-telemetry"}.get(
            name
        ) != existing:
            raise GroupError("UNEXPECTED_SHARED_NETWORK")
        model["networks"]["langfuse-existing" if name == "default" else name] = {
            "external": True,
            "name": existing,
        }
    return model


def prepare() -> dict[str, Any]:
    lock = json.loads((ROOT / "infra/langfuse-source.lock.json").read_text())
    vendor = ROOT / "infra/vendor/langfuse/docker-compose.yml"
    if (
        not vendor.is_file()
        or vendor.is_symlink()
        or hashlib.sha256(vendor.read_bytes()).hexdigest() != lock["compose_sha256"]
    ):
        raise GroupError("PREPARE_CHECKSUM_PINNED_LANGFUSE_SOURCE_FIRST")
    with tempfile.NamedTemporaryFile(suffix=".env", delete=False) as blank:
        empty = Path(blank.name)
    try:
        raw = docker(
            [
                "compose",
                "--project-name",
                "adf-langfuse",
                "--env-file",
                str(empty),
                "-f",
                str(vendor),
                "-f",
                str(ROOT / "infra/compose.langfuse.yaml"),
                "--profile",
                "observability",
                "config",
                "--no-interpolate",
                "--no-env-resolution",
                "--format",
                "json",
            ]
        )
    finally:
        empty.unlink()
    model = grouped_model(json.loads(raw))
    MODEL.parent.mkdir(exist_ok=True)
    if MODEL.is_symlink():
        raise GroupError("DERIVED_MODEL_SYMLINK_FORBIDDEN")
    MODEL.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    return {
        "project": "adf",
        "source_derived_symbolic_model": str(MODEL.relative_to(ROOT)),
        "langfuse_services": sorted(model["services"]),
        "existing_external_volumes": sorted(
            v["name"] for v in model["volumes"].values()
        ),
        "real_credentials_resolved_or_copied": False,
        "containers_changed": False,
    }


def inventory() -> dict[str, Any]:
    text = docker(
        [
            "ps",
            "--all",
            "--format",
            '{{.ID}}|{{.Names}}|{{.Label "com.docker.compose.project"}}|{{.Label "com.docker.compose.service"}}|{{.State}}',
        ]
    ).decode()
    rows = []
    extra = []
    other = 0
    expected = set(CONTAINERS.values())
    seen = set()
    for line in text.splitlines():
        identity, name, project, service, state = line.split("|", 4)
        if name in expected:
            if name in seen or not valid_labels(name, project, service):
                raise GroupError("TARGET_CONTAINER_LABELS_CHANGED")
            seen.add(name)
            rows.append(
                {
                    "id": identity,
                    "name": name,
                    "project": project,
                    "service": service,
                    "state": state,
                }
            )
        elif project == "adf":
            extra.append(
                {
                    "name": name,
                    "state": state,
                    "kind": "legacy_qa_or_unexpected_project_member",
                }
            )
        else:
            other += 1
    return {
        "target_container_count": len(rows),
        "target_containers": rows,
        "extra_adf_label_members": extra,
        "other_containers_untouched": other,
        "migration_required": any(row["project"] != "adf" for row in rows),
        "containers_changed": False,
    }


def valid_labels(name: str, project: str, service: str) -> bool:
    canonical = next((key for key, value in CONTAINERS.items() if value == name), None)
    if canonical is None:
        return False
    if (project, service) == ("adf", canonical):
        return True
    old = next((key for key, value in SERVICE_MAP.items() if value == canonical), None)
    return old is not None and (project, service) == ("adf-langfuse", old)


def canonical_argv() -> list[str]:
    return [
        "compose",
        "--project-name",
        "adf",
        "--env-file",
        str(ROOT / ".env"),
        "--env-file",
        str(ROOT / "infra/images.lock.env"),
        "--env-file",
        str(ROOT / ".bootstrap/langfuse/.env"),
        "-f",
        str(ROOT / "infra/compose.yaml"),
        "-f",
        str(MODEL),
        "--profile",
        "observability",
    ]


def start_guard(status: dict[str, Any]) -> None:
    if status["migration_required"]:
        raise GroupError(
            "EXISTING_GROUP_MIGRATION_REQUIRES_REVIEWED_BACKUP_AND_REDIS_RESOLUTION"
        )
    if status["extra_adf_label_members"]:
        raise GroupError(
            "LEGACY_QA_LABELS_MUST_BE_RESOLVED_WITHOUT_TOUCHING_FOREIGN_CONTAINERS"
        )
    # Cold-start durability is mandatory. Never proceed on healthy PONG alone.
    if any(
        row["name"] == "adf-redis-1" and row["state"] != "running"
        for row in status["target_containers"]
    ):
        raise GroupError("REDIS_RESTART_REQUIRES_PRESERVATION_PREFLIGHT")
    rows = status["target_containers"]
    if (
        status["target_container_count"] != len(CONTAINERS)
        or len(rows) != len(CONTAINERS)
        or {row["name"] for row in rows} != set(CONTAINERS.values())
    ):
        raise GroupError("COMPLETE_MANAGED_STACK_REQUIRED_BEFORE_START")
    if any(
        row["project"] != "adf"
        or not valid_labels(row["name"], row["project"], row["service"])
        for row in rows
    ):
        raise GroupError("TARGET_CONTAINER_LABELS_CHANGED")
    since = (
        docker(["inspect", "--format", "{{.State.StartedAt}}", "adf-redis-1"])
        .decode()
        .strip()
    )
    if not since:
        raise GroupError("REDIS_START_IDENTITY_UNAVAILABLE")
    logs = docker(
        ["logs", "--since", since, "adf-redis-1"], capture_stderr=True
    ).lower()
    failures = (
        b"noperm",
        b"truncat",
        b"short read",
        b"bad file format",
        b"error loading",
        b"errors loading",
        b"failed loading",
        b"fatal error",
        b"unexpected end",
        b"error reading",
        b"could not be loaded",
        b"can't open",
        b"cannot open",
    )
    if any(token in logs for token in failures):
        raise GroupError("REDIS_AOF_ACL_DURABILITY_GATE_FAILED")
    if (
        b"db loaded from append only file:" not in logs
        or b"ready to accept connections" not in logs
    ):
        raise GroupError("REDIS_AOF_LOAD_AND_READY_PROOF_REQUIRED")


def failure_report() -> dict[str, Any]:
    if APPLY_ATTEMPTED:
        return {
            "error": "GROUPING_START_FAILED_APPLY_UNCERTAIN",
            "apply_attempted": True,
            "containers_changed": None,
            "apply_outcome": "partial_or_unknown",
            "raw_output_emitted": False,
        }
    return {
        "error": "GROUPING_PREFLIGHT_FAILED_NO_APPLY",
        "apply_attempted": False,
        "containers_changed": False,
        "raw_output_emitted": False,
    }


def main() -> None:
    global APPLY_ATTEMPTED
    APPLY_ATTEMPTED = False
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=["status", "prepare", "plan", "start"],
        nargs="?",
        default="status",
    )
    args = parser.parse_args()
    if args.action == "status":
        return print(json.dumps(inventory()))
    report = prepare()
    if args.action == "prepare":
        return print(json.dumps(report))
    status = inventory()
    if args.action == "plan":
        return print(
            json.dumps(
                {
                    **report,
                    "inventory": status,
                    "apply_performed": False,
                    "blocked_until": "Redis preservation resolution; agreed backup; six Langfuse containers recreated by Compose; legacy QA labels separately resolved",
                }
            )
        )
    start_guard(status)
    APPLY_ATTEMPTED = True
    docker(
        [
            *canonical_argv(),
            "up",
            "--detach",
            "--no-build",
            "--pull",
            "never",
            "--no-recreate",
            "--no-deps",
            *START_SERVICES,
        ],
        240,
    )
    print(
        json.dumps(
            {
                "project": "adf",
                "images_rebuilt": False,
                "containers_recreated": False,
                "apply_attempted": True,
                "one_shot_migrator_started": False,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (GroupError, OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        print(json.dumps(failure_report()))
        raise SystemExit(1) from None
