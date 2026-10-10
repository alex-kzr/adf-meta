"""Prepare the pinned official Langfuse Compose stack without starting services."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".bootstrap" / "langfuse"
VENDOR = ROOT / "infra" / "vendor" / "langfuse"
SERVICES = {
    "langfuse-web",
    "langfuse-worker",
    "clickhouse",
    "minio",
    "postgres",
    "redis",
}
IMAGE_REPOSITORIES = {
    "LANGFUSE_WEB_IMAGE": "docker.langfuse.com/langfuse/langfuse",
    "LANGFUSE_WORKER_IMAGE": "docker.langfuse.com/langfuse/langfuse-worker",
    "LANGFUSE_CLICKHOUSE_IMAGE": "docker.io/clickhouse/clickhouse-server",
    "LANGFUSE_MINIO_IMAGE": "cgr.dev/chainguard/minio",
    "LANGFUSE_POSTGRES_IMAGE": "docker.io/postgres",
    "LANGFUSE_REDIS_IMAGE": "docker.io/redis",
    "OTEL_IMAGE": "otel/opentelemetry-collector-contrib",
}
TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,160}$")


class PreparationError(RuntimeError):
    """An actionable error whose message never includes secret values."""


@dataclass(frozen=True)
class ImagePin:
    variable: str
    reference: str


@dataclass(frozen=True)
class SourceLock:
    revision: str
    compose_sha256: str
    images: tuple[ImagePin, ...]

    @classmethod
    def read(cls, path: Path) -> SourceLock:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise PreparationError("Unsupported Langfuse lock schema")
        revision = value.get("upstream_revision")
        digest = value.get("compose_sha256")
        image_values = value.get("images")
        if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise PreparationError("Invalid upstream revision")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise PreparationError("Invalid upstream Compose checksum")
        if not isinstance(image_values, dict):
            raise PreparationError("Missing image pins")
        if set(image_values) != set(IMAGE_REPOSITORIES):
            raise PreparationError("Official component image set changed")
        images = []
        for variable, reference in image_values.items():
            if not isinstance(variable, str) or not isinstance(reference, str):
                raise PreparationError("Invalid image pin")
            if not re.fullmatch(r"[A-Z_]+", variable) or not re.fullmatch(
                r"[a-z0-9./_-]+(?::[A-Za-z0-9._-]+)?@sha256:[a-f0-9]{64}", reference
            ):
                raise PreparationError(
                    "Images must be locked to immutable registry digests"
                )
            repository = reference.split("@", 1)[0].split(":", 1)[0]
            if repository != IMAGE_REPOSITORIES[variable]:
                raise PreparationError(
                    "Image repository is not an approved official component"
                )
            images.append(ImagePin(variable, reference))
        return cls(revision, digest, tuple(images))


def private_directory(path: Path) -> None:
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise PreparationError("Private directory escapes the umbrella root")
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)


def write_private(path: Path, content: str) -> None:
    """Preserve existing operator edits; generated files are not silently rotated."""
    if path.is_symlink():
        raise PreparationError(f"Refusing a symlink at {path.name}")
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise PreparationError(
                f"Existing {path.name} differs; preserve it and review configuration"
            )
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def fetch_source(lock: SourceLock) -> Path:
    private_directory(VENDOR)
    path = VENDOR / "docker-compose.yml"
    if path.is_symlink():
        raise PreparationError("Refusing a symlink for upstream Compose")
    if path.exists():
        data = path.read_bytes()
    else:
        url = f"https://raw.githubusercontent.com/langfuse/langfuse/{lock.revision}/docker-compose.yml"
        request = Request(url, headers={"User-Agent": "adf-local-bootstrap"})  # noqa: S310 -- fixed official HTTPS origin
        with urlopen(request, timeout=30) as response:  # noqa: S310 -- fixed official HTTPS origin
            data = response.read(256_001)
        if len(data) > 256_000:
            raise PreparationError("Upstream Compose exceeds the permitted size")
    if hashlib.sha256(data).hexdigest() != lock.compose_sha256:
        raise PreparationError(
            "Upstream Compose checksum mismatch; no file was replaced"
        )
    if not path.exists():
        path.write_bytes(data)
    return path


def load_or_generate_secrets() -> dict[str, str]:
    path = PRIVATE / "generated-secrets.json"
    expected = {
        "postgres_password",
        "salt",
        "encryption_key",
        "nextauth_secret",
        "clickhouse_password",
        "minio_password",
        "redis_password",
        "public_key",
        "secret_key",
        "user_password",
    }
    if path.is_symlink():
        raise PreparationError("Refusing a symlink for generated secrets")
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or set(raw) != expected:
            raise PreparationError(
                "Existing generated secret configuration is incompatible"
            )
        for value in raw.values():
            if not isinstance(value, str) or not TOKEN.fullmatch(value):
                raise PreparationError(
                    "Existing generated secret configuration is invalid"
                )
        result = cast(dict[str, str], raw)
    else:
        result = {name: secrets.token_urlsafe(36) for name in expected}
        result["encryption_key"] = secrets.token_hex(32)
        result["public_key"] = "pk-lf-" + secrets.token_hex(24)
        result["secret_key"] = "sk-lf-" + secrets.token_hex(32)
        write_private(path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    if not re.fullmatch(r"[a-f0-9]{64}", result["encryption_key"]):
        raise PreparationError("Encryption key must be a 32-byte hex value")
    return result


def prepare_configuration(lock: SourceLock) -> dict[str, str]:
    private_directory(PRIVATE)
    values = load_or_generate_secrets()
    environment = {
        "DATABASE_URL": f"postgresql://langfuse:{values['postgres_password']}@postgres:5432/langfuse",
        "POSTGRES_USER": "langfuse",
        "POSTGRES_DB": "langfuse",
        "POSTGRES_PASSWORD": values["postgres_password"],
        "POSTGRES_VERSION": "17",
        "SALT": values["salt"],
        "ENCRYPTION_KEY": values["encryption_key"],
        "NEXTAUTH_SECRET": values["nextauth_secret"],
        "NEXTAUTH_URL": "http://localhost:3000",
        "CLICKHOUSE_USER": "langfuse",
        "CLICKHOUSE_PASSWORD": values["clickhouse_password"],
        "CLICKHOUSE_CLUSTER_ENABLED": "false",
        "MINIO_ROOT_USER": "adf-langfuse",
        "MINIO_ROOT_PASSWORD": values["minio_password"],
        "REDIS_AUTH": values["redis_password"],
        "TELEMETRY_ENABLED": "false",
        "LANGFUSE_IN_APP_AGENT_ENABLED": "false",
        "LANGFUSE_INIT_ORG_ID": "adf-local",
        "LANGFUSE_INIT_ORG_NAME": "ADF Local",
        "LANGFUSE_INIT_PROJECT_ID": "adf-local",
        "LANGFUSE_INIT_PROJECT_NAME": "ADF",
        "LANGFUSE_INIT_PROJECT_RETENTION": "30",
        "LANGFUSE_INIT_PROJECT_PUBLIC_KEY": values["public_key"],
        "LANGFUSE_INIT_PROJECT_SECRET_KEY": values["secret_key"],
        "LANGFUSE_INIT_USER_EMAIL": "operator@adf.local",
        "LANGFUSE_INIT_USER_NAME": "ADF Operator",
        "LANGFUSE_INIT_USER_PASSWORD": values["user_password"],
        "LANGFUSE_S3_MEDIA_UPLOAD_ENDPOINT": "http://localhost:39090",
        "LANGFUSE_S3_BATCH_EXPORT_EXTERNAL_ENDPOINT": "http://localhost:39090",
    }
    for purpose in ("EVENT", "MEDIA", "BATCH_EXPORT"):
        prefix = (
            f"LANGFUSE_S3_{purpose}_UPLOAD"
            if purpose != "BATCH_EXPORT"
            else "LANGFUSE_S3_BATCH_EXPORT"
        )
        environment[prefix + "_ACCESS_KEY_ID"] = "adf-langfuse"
        environment[prefix + "_SECRET_ACCESS_KEY"] = values["minio_password"]
    environment.update({image.variable: image.reference for image in lock.images})
    write_private(
        PRIVATE / ".env",
        "".join(f"{key}={value}\n" for key, value in sorted(environment.items())),
    )
    authorization = (
        "Basic "
        + base64.b64encode(
            f"{values['public_key']}:{values['secret_key']}".encode()
        ).decode()
    )
    auth = {
        "exporters": {
            "otlphttp/langfuse": {
                "headers": {
                    "Authorization": authorization,
                    "x-langfuse-ingestion-version": "4",
                }
            }
        }
    }
    write_private(PRIVATE / "collector-auth.yaml", json.dumps(auth, indent=2) + "\n")
    client = {
        "base_url": "http://localhost:3000",
        "project_id": "adf-local",
        "public_key": values["public_key"],
        "secret_key": values["secret_key"],
    }
    write_private(
        PRIVATE / "project-credentials.json", json.dumps(client, indent=2) + "\n"
    )
    write_private(
        PRIVATE / "operator-login.txt",
        f"Email: operator@adf.local\nPassword: {values['user_password']}\n",
    )
    return environment


def docker(command: list[str], timeout: int = 30) -> str:
    executable = shutil.which("docker")
    if executable is None:
        raise PreparationError("Docker executable is unavailable")
    completed = subprocess.run(  # noqa: S603 -- fixed argv and validated pins
        [executable, *command],
        capture_output=True,
        text=True,  # noqa: S603 -- fixed commands and validated immutable pins
        timeout=timeout,
        check=False,
        shell=False,
    )
    if completed.returncode:
        # Resolved Docker configuration/errors can include credentials; do not echo.
        raise PreparationError(
            "Docker command failed; inspect service without dumping configuration"
        )
    return completed.stdout


def resource_report() -> dict[str, object]:
    info = json.loads(docker(["info", "--format", "{{json .}}"], 15))
    memory = info.get("MemTotal")
    cpus = info.get("NCPU")
    if not isinstance(memory, int) or not isinstance(cpus, int):
        raise PreparationError("Docker resource information is unavailable")
    return {
        "docker_memory_gib": round(memory / 1024**3, 2),
        "docker_cpus": cpus,
        "official_vm_recommendation": "4 cores / 16 GiB; plus space for ADF",
        "local_smoke_budget_sufficient": cpus >= 4 and memory >= 12 * 1024**3,
        "official_memory_recommendation_met": memory >= 16 * 1024**3,
        "langfuse_container_memory_caps_gib": 8.75,
        "services_started": False,
    }


def validate_compose() -> dict[str, object]:
    command = [
        "compose",
        "--project-name",
        "adf-langfuse",
        "--env-file",
        str(PRIVATE / ".env"),
        "-f",
        str(VENDOR / "docker-compose.yml"),
        "-f",
        str(ROOT / "infra" / "compose.langfuse.yaml"),
        "--profile",
        "observability",
        "config",
        "--format",
        "json",
    ]
    model = json.loads(docker(command))
    services = model.get("services")
    if not isinstance(services, dict) or set(services) != SERVICES:
        raise PreparationError("Official Langfuse component set changed")
    defaults = {
        "mysalt",
        "mysecret",
        "myredissecret",
        "miniosecret",
        "clickhouse",
        "postgres",
    }
    secret_names = {
        "SALT",
        "NEXTAUTH_SECRET",
        "POSTGRES_PASSWORD",
        "REDIS_AUTH",
        "MINIO_ROOT_PASSWORD",
        "CLICKHOUSE_PASSWORD",
    }
    for name, service in services.items():
        for port in service.get("ports", []):
            if port.get("host_ip") != "127.0.0.1" or name not in {
                "minio",
                "langfuse-web",
            }:
                raise PreparationError("Non-loopback or unexpected Langfuse port")
        for variable, value in service.get("environment", {}).items():
            if variable in secret_names and value in defaults:
                raise PreparationError("Upstream default credential was not replaced")
        for volume in service.get("volumes", []):
            source = str(volume.get("source", ""))
            if "docker.sock" in source or any(
                part in source for part in ("/.codex", "/.claude")
            ):
                raise PreparationError("Forbidden credential or Docker mount")
        if not service.get("healthcheck") or not service.get("mem_limit"):
            raise PreparationError("Missing healthcheck or local resource cap")
    network = model.get("networks", {}).get("telemetry", {})
    if network.get("name") != "adf-telemetry" or not network.get("external"):
        raise PreparationError("Telemetry must use the dedicated external network")
    return {
        "compose_valid": True,
        "official_services": sorted(services),
        "loopback_published_services": ["langfuse-web", "minio"],
        "credential_defaults_removed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull immutable pins; never start containers",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate resolved Compose privately"
    )
    parser.add_argument(
        "--check-resources", action="store_true", help="Report Docker resource budget"
    )
    arguments = parser.parse_args()
    try:
        lock = SourceLock.read(ROOT / "infra" / "langfuse-source.lock.json")
        fetch_source(lock)
        prepare_configuration(lock)
        report: dict[str, object] = {
            "prepared": True,
            "upstream_revision": lock.revision,
            "compose_checksum_verified": True,
            "services_started": False,
        }
        if arguments.check_resources:
            report["resources"] = resource_report()
        if arguments.validate:
            report["validation"] = validate_compose()
        if arguments.pull:
            for image in lock.images:
                docker(["pull", image.reference], 900)
            report["pinned_images_pulled"] = len(lock.images)
        print(json.dumps(report, indent=2))
        return 0
    except PreparationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, subprocess.TimeoutExpired):
        # User-owned secret values must not appear in exception messages/tracebacks.
        print(
            "Langfuse preparation failed. Check local files, checksum/pins "
            "and Docker availability.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
