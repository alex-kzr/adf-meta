"""Verify real Langfuse v4 ingestion, trace correlation and Collector privacy."""

from __future__ import annotations

import argparse
import base64
import copy
import json
import re
import secrets
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from http.client import HTTPException
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
MAX_RESPONSE = 4 * 1024 * 1024
TRACE_ID = re.compile(r"^[a-f0-9]{32}$")


class CheckError(RuntimeError):
    """Safe diagnostic; raw bodies and credentials are excluded from output."""


class NoRedirect(HTTPRedirectHandler):
    """Prevent private authorization from following any backend redirect."""

    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def local_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "http" or parsed.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise CheckError("Telemetry validation must use an explicit loopback HTTP URL")
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise CheckError("Telemetry URL cannot contain credentials, queries or a path")
    return value.rstrip("/")


@dataclass(frozen=True)
class ClientConfig:
    base_url: str
    project_id: str
    authorization: str = field(repr=False)

    @classmethod
    def read(cls, path: Path, base_url: str | None) -> ClientConfig:
        if path.is_symlink():
            raise CheckError("Credential configuration cannot be a symlink")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise CheckError("Invalid generated Langfuse project configuration")
        project = data.get("project_id")
        public = data.get("public_key")
        private = data.get("secret_key")
        target = base_url or data.get("base_url")
        if not isinstance(project, str) or not re.fullmatch(
            r"[a-zA-Z0-9_-]{1,80}", project
        ):
            raise CheckError("Invalid Langfuse project ID")
        if not isinstance(public, str) or not public.startswith("pk-lf-"):
            raise CheckError("Invalid generated Langfuse project public key")
        if not isinstance(private, str) or not private.startswith("sk-lf-"):
            raise CheckError("Invalid generated Langfuse project secret key")
        if not isinstance(target, str):
            raise CheckError("Missing local Langfuse URL")
        authorization = (
            "Basic " + base64.b64encode(f"{public}:{private}".encode()).decode()
        )
        return cls(local_url(target), project, authorization)


def request_json(
    url: str, *, body: dict[str, Any] | None = None, authorization: str | None = None
) -> dict[str, Any]:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
    ):
        raise CheckError("Telemetry HTTP request escaped its loopback origin")
    headers = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    request = Request(  # noqa: S310 -- validated loopback HTTP origin
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )  # noqa: S310 -- validated loopback HTTP origin
    try:
        opener = build_opener(ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=5) as response:
            raw = response.read(MAX_RESPONSE + 1)
    except HTTPError as error:
        # Never print backend bodies; they may echo sensitive input.
        raise CheckError(
            f"Telemetry HTTP request failed with status {error.code}"
        ) from None
    except (URLError, TimeoutError, ConnectionError, HTTPException):
        raise CheckError("Telemetry endpoint is unavailable") from None
    if len(raw) > MAX_RESPONSE:
        raise CheckError("Telemetry response exceeded its size limit")
    decoded = json.loads(raw or b"{}")
    if not isinstance(decoded, dict):
        raise CheckError("Telemetry endpoint returned an unexpected response")
    return decoded


@dataclass(frozen=True)
class Fixture:
    trace_id: str
    root_span_id: str
    child_span_id: str
    run_id: str
    execution_id: str
    excluded_trace_ids: tuple[str, ...]
    sentinel: str = field(repr=False)
    body: dict[str, Any] = field(repr=False)


def attribute(key: str, value: str | int | bool) -> dict[str, Any]:
    payload: dict[str, str | bool]
    if isinstance(value, bool):
        payload = {"boolValue": value}
    elif isinstance(value, int):
        payload = {"intValue": str(value)}
    else:
        payload = {"stringValue": value}
    return {"key": key, "value": payload}


def fixture() -> Fixture:
    """Inject secrets into normal unsafe surfaces and verify they cannot export."""
    sentinel = "ADF_TELEMETRY_SENTINEL_" + secrets.token_hex(16)
    trace_id, root_id, child_id = (
        secrets.token_hex(16),
        secrets.token_hex(8),
        secrets.token_hex(8),
    )
    run_id, execution_id = str(uuid4()), str(uuid4())
    now = time.time_ns()
    ids = {
        "project_id": str(uuid4()),
        "task_id": str(uuid4()),
        "run_id": run_id,
        "execution_id": execution_id,
        "agent_id": str(uuid4()),
        "node_run_id": str(uuid4()),
    }
    attrs = [attribute(key, value) for key, value in ids.items()]
    attrs += [attribute("adf.telemetry.eligible", True), attribute("provider", "mock")]
    unsafe = [
        "prompt",
        "code",
        "stdout",
        "tool.arguments",
        "authorization",
        "gen_ai.prompt",
        "langfuse.observation.input",
        "langfuse.observation.output",
        "langfuse.trace.metadata.secret",
        "langfuse.trace.name",
        "langfuse.user.id",
        "langfuse.session.id",
        "adf.usage.input_tokens",
    ]
    attrs += [attribute(key, sentinel) for key in unsafe]

    def span(span_id: str, name: str, parent: str | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": name,
            "kind": 1,
            "startTimeUnixNano": str(now),
            "endTimeUnixNano": str(now + 1_000_000),
            "traceState": "unsafe=" + sentinel,
            "attributes": copy.deepcopy(attrs),
            "status": {"code": 2, "message": sentinel},
            "events": [
                {
                    "name": sentinel,
                    "timeUnixNano": str(now),
                    "attributes": [attribute("unsafe", sentinel)],
                }
            ],
        }
        if parent:
            data["parentSpanId"] = parent
        return data

    spans = [span(root_id, "workflow.run"), span(child_id, "cli.session", root_id)]
    linked = span(secrets.token_hex(8), "tool.call", root_id)
    linked["links"] = [
        {
            "traceId": secrets.token_hex(16),
            "spanId": secrets.token_hex(8),
            "attributes": [attribute("unsafe", sentinel)],
        }
    ]
    spans.append(linked)
    invalid_id = span(secrets.token_hex(8), "agent.execution", root_id)
    invalid_id["attributes"] = [
        attribute("run_id", sentinel),
        attribute("adf.telemetry.eligible", True),
    ]
    spans.append(invalid_id)
    ineligible_id, unknown_service_id = secrets.token_hex(16), secrets.token_hex(16)
    ineligible = span(secrets.token_hex(8), "api.request")
    ineligible["traceId"] = ineligible_id
    ineligible["attributes"] = [
        attribute("run_id", run_id),
        attribute("adf.telemetry.eligible", False),
    ]
    unknown = span(secrets.token_hex(8), "agent.execution")
    unknown["traceId"] = unknown_service_id

    def resource(service: str, values: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "resource": {
                "attributes": [
                    attribute("service.name", service),
                    attribute("secret", sentinel),
                ]
            },
            "scopeSpans": [
                {
                    "scope": {
                        "name": sentinel,
                        "version": sentinel,
                        "attributes": [attribute("secret", sentinel)],
                    },
                    "spans": values,
                }
            ],
        }

    body = {
        "resourceSpans": [
            resource("adf-orchestrator", spans),
            resource("adf-api", [ineligible]),
            resource("untrusted-producer", [unknown]),
        ]
    }
    return Fixture(
        trace_id,
        root_id,
        child_id,
        run_id,
        execution_id,
        (ineligible_id, unknown_service_id),
        sentinel,
        body,
    )


def observations(client: ClientConfig, trace_id: str) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    query = urlencode(
        {
            "traceId": trace_id,
            "fields": "core,basic,metadata,io,trace_context",
            "limit": 100,
            "fromStartTime": (now - timedelta(days=1)).isoformat(),
            "toStartTime": (now + timedelta(days=1)).isoformat(),
        }
    )
    result = request_json(
        client.base_url + "/api/public/v2/observations?" + query,
        authorization=client.authorization,
    )
    data = result.get("data")
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise CheckError("Langfuse v4 observations response has an unexpected shape")
    return data


def validate_observations(
    client: ClientConfig, sample: Fixture, timeout: int
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    values: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        values = observations(client, sample.trace_id)
        if len(values) >= 2:
            break
        time.sleep(1)
    if len(values) != 2:
        raise CheckError(
            "Expected two eligible spans; missing/duplicate/unfiltered observations"
        )
    by_id = {item.get("id"): item for item in values}
    if set(by_id) != {sample.root_span_id, sample.child_span_id}:
        raise CheckError("Langfuse span IDs differ from OTel correlation IDs")
    root, child = by_id[sample.root_span_id], by_id[sample.child_span_id]
    if (
        root.get("parentObservationId") is not None
        or child.get("parentObservationId") != sample.root_span_id
    ):
        raise CheckError("Parent/child correlation was not preserved")
    if any(
        item.get("traceId") != sample.trace_id or item.get("sessionId") != sample.run_id
        for item in values
    ):
        raise CheckError("Run and trace correlation was not preserved on every span")
    serialized = json.dumps(values)
    if sample.sentinel in serialized:
        raise CheckError("Sentinel leaked into Langfuse observations")
    for item in values:
        if item.get("input") or item.get("output") or item.get("statusMessage"):
            raise CheckError(
                "Sensitive/default input, output or status text was exported"
            )
        metadata = item.get("metadata")
        if (
            not isinstance(metadata, dict)
            or metadata.get("run_id") != sample.run_id
            or metadata.get("execution_id") != sample.execution_id
        ):
            raise CheckError("Run/execution correlation metadata was not mapped")
    for excluded in sample.excluded_trace_ids:
        if observations(client, excluded):
            raise CheckError("An ineligible producer or span was exported")
    return {
        "ingestion_verified": True,
        "privacy_sentinel_verified": True,
        "duplicate_spans": False,
        "parent_child_verified": True,
        "observations": len(values),
        "trace_id": sample.trace_id,
        "run_id": sample.run_id,
        "execution_id": sample.execution_id,
        "trace_url": (
            f"{client.base_url}/project/{client.project_id}/traces/{sample.trace_id}"
        ),
    }


def existing_trace(client: ClientConfig, trace_id: str) -> dict[str, Any]:
    if not TRACE_ID.fullmatch(trace_id):
        raise CheckError("Trace ID must contain 32 lowercase hexadecimal characters")
    values = observations(client, trace_id)
    if not values:
        raise CheckError("No real Langfuse observations exist for this trace")
    ids = [value.get("id") for value in values]
    if len(ids) != len(set(ids)):
        raise CheckError("Duplicate observation IDs")
    return {
        "existing_trace_verified": True,
        "trace_id": trace_id,
        "observations": len(values),
        "span_names": sorted(
            {
                str(value.get("name"))
                if value.get("name")
                in {
                    "api.request",
                    "workflow.run",
                    "workflow.node",
                    "agent.execution",
                    "cli.session",
                    "tool.call",
                    "git.operation",
                    "test.run",
                }
                else "unrecognized"
                for value in values
            }
        ),
        "trace_url": (
            f"{client.base_url}/project/{client.project_id}/traces/{trace_id}"
        ),
    }


def outage_run(
    client: ClientConfig, run_id: str, api_url: str, token_file: Path, timeout: int
) -> dict[str, Any]:
    """Observe live core completion while Langfuse stays unavailable; no mutations."""
    if not re.fullmatch(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", run_id
    ):
        raise CheckError("Outage run ID must be a UUID")
    api = local_url(api_url)
    if token_file.is_symlink() or not token_file.resolve().is_relative_to(
        (ROOT / ".bootstrap").resolve()
    ):
        raise CheckError("ADF admin token file must stay inside ignored .bootstrap")
    token = token_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,200}", token):
        raise CheckError("Invalid generated ADF admin token file")

    def backend_unavailable() -> None:
        try:
            request_json(
                client.base_url + "/api/public/health?failIfDatabaseUnavailable=true"
            )
        except CheckError:
            return
        raise CheckError("Langfuse is available; an outage test was not established")

    def status() -> str:
        value = request_json(
            api + "/api/runs/" + run_id, authorization="Bearer " + token
        ).get("status")
        if not isinstance(value, str) or value not in {
            "queued",
            "running",
            "paused",
            "completed",
            "failed",
            "cancelled",
        }:
            raise CheckError("Controlled run response has an unexpected status")
        return value

    backend_unavailable()
    initial = status()
    if initial not in {"queued", "running"}:
        raise CheckError(
            "Outage validation requires an active run, not a previously completed run"
        )
    started = time.monotonic()
    deadline = started + timeout
    checks = 0
    while time.monotonic() < deadline:
        backend_unavailable()
        checks += 1
        current = status()
        if current == "completed":
            backend_unavailable()
            return {
                "core_completion_during_langfuse_outage_verified": True,
                "run_id": run_id,
                "initial_status": initial,
                "final_status": current,
                "backend_outage_checks": checks + 2,
                "observation_seconds": round(time.monotonic() - started, 3),
            }
        if current in {"failed", "cancelled"}:
            raise CheckError(
                "Controlled workflow did not complete during the telemetry outage"
            )
        time.sleep(1)
    raise CheckError(
        "Controlled workflow did not complete within the outage test timeout"
    )


def write_report(path: Path, value: dict[str, Any]) -> None:
    target = path.resolve()
    if (
        not target.is_relative_to((ROOT / ".bootstrap").resolve())
        or target.is_symlink()
    ):
        raise CheckError("QA reports must stay inside ignored .bootstrap")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--credentials",
        type=Path,
        default=ROOT / ".bootstrap/langfuse/project-credentials.json",
    )
    parser.add_argument("--collector-url", default="http://127.0.0.1:4318")
    parser.add_argument("--langfuse-url")
    parser.add_argument(
        "--outage-run",
        help="Observe an active controlled run while Langfuse is unavailable",
    )
    parser.add_argument("--api-url", default="http://127.0.0.1:8080")
    parser.add_argument(
        "--admin-token-file",
        type=Path,
        help="Generated ADF token, never provider credentials",
    )
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument(
        "--existing-trace",
        help="Verify a real ADF run trace instead of sending a smoke fixture",
    )
    parser.add_argument(
        "--report", type=Path, default=ROOT / ".bootstrap/telemetry-validation.json"
    )
    arguments = parser.parse_args()
    try:
        if not 1 <= arguments.timeout <= 180:
            raise CheckError("Timeout must be between 1 and 180 seconds")
        client = ClientConfig.read(arguments.credentials, arguments.langfuse_url)
        if arguments.outage_run:
            if arguments.admin_token_file is None or arguments.existing_trace:
                raise CheckError(
                    "Outage mode requires an explicit ADF admin file "
                    "and no existing-trace mode"
                )
            result = outage_run(
                client,
                arguments.outage_run,
                arguments.api_url,
                arguments.admin_token_file,
                arguments.timeout,
            )
        elif arguments.existing_trace:
            result = existing_trace(client, arguments.existing_trace)
        else:
            collector = local_url(arguments.collector_url)
            sample = fixture()
            request_json(collector + "/v1/traces", body=sample.body)
            result = validate_observations(client, sample, arguments.timeout)
        write_report(arguments.report, result)
        print(json.dumps(result, indent=2))
        return 0
    except CheckError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError):
        print(
            "Telemetry check failed to read validated local configuration or response.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
