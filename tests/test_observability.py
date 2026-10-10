"""Bootstrap preservation and telemetry privacy contracts; no subscription required."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load checked-in observability script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare = load_script("adf_prepare_langfuse", "prepare-langfuse.py")
check = load_script("adf_check_telemetry", "check-telemetry.py")


class BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="adf-observability-test-")
        self.root = Path(self.directory.name)
        self.override = patch.multiple(
            prepare,
            ROOT=self.root,
            PRIVATE=self.root / ".bootstrap/langfuse",
            VENDOR=self.root / "infra/vendor/langfuse",
        )
        self.override.start()
        self.lock = prepare.SourceLock.read(ROOT / "infra/langfuse-source.lock.json")

    def tearDown(self) -> None:
        self.override.stop()
        self.directory.cleanup()

    def test_generated_credentials_are_distinct_preserved_and_not_printed(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            first = prepare.prepare_configuration(self.lock)
            hashes = {
                path.name: path.read_bytes()
                for path in prepare.PRIVATE.iterdir()
                if path.is_file()
            }
            second = prepare.prepare_configuration(self.lock)
        self.assertEqual(first, second)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(
            hashes,
            {path.name: path.read_bytes() for path in prepare.PRIVATE.iterdir()},
        )
        generated = json.loads((prepare.PRIVATE / "generated-secrets.json").read_text())
        self.assertEqual(len(generated), len(set(generated.values())))
        self.assertTrue(all(len(value) >= 40 for value in generated.values()))
        for name in ("POSTGRES_PASSWORD", "CLICKHOUSE_PASSWORD", "REDIS_AUTH", "SALT"):
            self.assertNotIn(
                first[name], {"postgres", "clickhouse", "myredissecret", "mysalt"}
            )
        client = check.ClientConfig.read(
            prepare.PRIVATE / "project-credentials.json", None
        )
        self.assertNotIn(generated["secret_key"], repr(client))
        self.assertNotIn(client.authorization, repr(client))

    def test_existing_operator_edit_is_preserved_and_rejected(self) -> None:
        prepare.prepare_configuration(self.lock)
        path = prepare.PRIVATE / ".env"
        path.write_text("OPERATOR_EDIT=preserve\n", encoding="utf-8")
        with self.assertRaises(prepare.PreparationError):
            prepare.prepare_configuration(self.lock)
        self.assertEqual(path.read_text(), "OPERATOR_EDIT=preserve\n")

    def test_checksum_mismatch_never_overwrites_vendor_file(self) -> None:
        prepare.VENDOR.mkdir(parents=True)
        source = prepare.VENDOR / "docker-compose.yml"
        source.write_bytes(b"operator-owned tampered source")
        with self.assertRaises(prepare.PreparationError):
            prepare.fetch_source(self.lock)
        self.assertEqual(source.read_bytes(), b"operator-owned tampered source")

    def test_unpinned_image_is_rejected_before_docker_or_secrets(self) -> None:
        source = json.loads((ROOT / "infra/langfuse-source.lock.json").read_text())
        source["images"]["LANGFUSE_WEB_IMAGE"] = "langfuse/langfuse:latest"
        path = self.root / "invalid-lock.json"
        path.write_text(json.dumps(source), encoding="utf-8")
        with self.assertRaises(prepare.PreparationError):
            prepare.SourceLock.read(path)
        self.assertFalse(prepare.PRIVATE.exists())

    def test_docker_failure_does_not_echo_resolved_secret(self) -> None:
        completed = subprocess.CompletedProcess(
            [], 1, stdout="secret-body", stderr="secret-body"
        )
        with (
            patch.object(prepare.shutil, "which", return_value="/usr/bin/docker"),
            patch.object(prepare.subprocess, "run", return_value=completed),
            self.assertRaises(prepare.PreparationError) as error,
        ):
            prepare.docker(["compose", "config"])
        self.assertNotIn("secret-body", str(error.exception))

    def test_low_resource_budget_is_reported_without_starting_services(self) -> None:
        with patch.object(
            prepare,
            "docker",
            return_value=json.dumps({"MemTotal": 8 * 1024**3, "NCPU": 2}),
        ):
            report = prepare.resource_report()
        self.assertFalse(report["local_smoke_budget_sufficient"])
        self.assertFalse(report["services_started"])


class TelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample = check.fixture()
        self.client = check.ClientConfig(
            "http://localhost:3000", "adf-local", "not-a-real-key"
        )

    def valid_observations(self) -> list[dict[str, Any]]:
        return [
            {
                "id": self.sample.root_span_id,
                "traceId": self.sample.trace_id,
                "parentObservationId": None,
                "sessionId": self.sample.run_id,
                "metadata": {
                    "run_id": self.sample.run_id,
                    "execution_id": self.sample.execution_id,
                },
                "input": None,
                "output": None,
            },
            {
                "id": self.sample.child_span_id,
                "traceId": self.sample.trace_id,
                "parentObservationId": self.sample.root_span_id,
                "sessionId": self.sample.run_id,
                "metadata": {
                    "run_id": self.sample.run_id,
                    "execution_id": self.sample.execution_id,
                },
                "input": None,
                "output": None,
            },
        ]

    def observations_for(
        self, values: list[dict[str, Any]]
    ) -> Callable[[object, str], list[dict[str, Any]]]:
        def read(client: object, trace_id: str) -> list[dict[str, Any]]:
            return values if trace_id == self.sample.trace_id else []

        return read

    def test_retrieval_requires_real_parent_ids_and_safe_metadata(self) -> None:
        with patch.object(
            check,
            "observations",
            side_effect=self.observations_for(self.valid_observations()),
        ):
            report = check.validate_observations(self.client, self.sample, 1)
        self.assertTrue(report["privacy_sentinel_verified"])
        self.assertTrue(report["parent_child_verified"])
        self.assertEqual(report["observations"], 2)
        self.assertNotIn(self.sample.sentinel, json.dumps(report))

    def test_sensitive_metadata_in_actual_backend_response_fails(self) -> None:
        values = self.valid_observations()
        values[1]["metadata"]["secret"] = self.sample.sentinel
        with (
            patch.object(
                check, "observations", side_effect=self.observations_for(values)
            ),
            self.assertRaises(check.CheckError),
        ):
            check.validate_observations(self.client, self.sample, 1)

    def test_duplicate_or_extra_observation_fails(self) -> None:
        values = self.valid_observations()
        values.append(values[0])
        with (
            patch.object(
                check, "observations", side_effect=self.observations_for(values)
            ),
            self.assertRaises(check.CheckError),
        ):
            check.validate_observations(self.client, self.sample, 1)

    def test_wrong_parent_correlation_fails(self) -> None:
        values = self.valid_observations()
        values[1]["parentObservationId"] = "unrelated"
        with (
            patch.object(
                check, "observations", side_effect=self.observations_for(values)
            ),
            self.assertRaises(check.CheckError),
        ):
            check.validate_observations(self.client, self.sample, 1)

    def test_wrong_execution_correlation_fails(self) -> None:
        values = self.valid_observations()
        values[1]["metadata"]["execution_id"] = str(uuid4())
        with (
            patch.object(
                check, "observations", side_effect=self.observations_for(values)
            ),
            self.assertRaises(check.CheckError),
        ):
            check.validate_observations(self.client, self.sample, 1)

    def test_non_loopback_credential_url_is_rejected(self) -> None:
        for value in (
            "https://cloud.langfuse.com",
            "http://user:secret@localhost:3000",
            "file:///tmp/secret",
            "http://localhost/path",
        ):
            with self.subTest(value=value), self.assertRaises(check.CheckError):
                check.local_url(value)

    def test_authorization_never_follows_backend_redirect(self) -> None:
        requests: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                requests.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/would-copy-authorization")
                self.end_headers()

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(check.CheckError):
                check.request_json(
                    f"http://127.0.0.1:{server.server_port}/", authorization="private"
                )
            self.assertEqual(requests, ["/"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class LiveOutageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="adf-outage-test-")
        self.root = Path(self.directory.name)
        self.token_file = self.root / ".bootstrap/secrets/admin-token"
        self.token_file.parent.mkdir(parents=True)
        self.token_file.write_text("test-" + "a" * 40, encoding="utf-8")
        self.override = patch.object(check, "ROOT", self.root)
        self.override.start()
        self.client = check.ClientConfig(
            "http://localhost:3000", "adf-local", "unused-key"
        )
        self.run_id = "11111111-1111-1111-1111-111111111111"

    def tearDown(self) -> None:
        self.override.stop()
        self.directory.cleanup()

    def response(
        self, statuses: list[str], backend_available: bool = False
    ) -> Callable[..., dict[str, Any]]:
        sequence = iter(statuses)

        def request(url: str, **kwargs: object) -> dict[str, Any]:
            if "/health" in url:
                if backend_available:
                    return {"status": "ok"}
                raise check.CheckError("Unavailable")
            if "/api/runs/" in url:
                return {"status": next(sequence)}
            raise RuntimeError("Unexpected outage-check URL")

        return request

    def test_live_completion_is_observed_only_while_backend_unavailable(self) -> None:
        with (
            patch.object(
                check,
                "request_json",
                side_effect=self.response(["queued", "running", "completed"]),
            ),
            patch.object(check.time, "sleep"),
        ):
            report = check.outage_run(
                self.client, self.run_id, "http://127.0.0.1:8080", self.token_file, 1
            )
        self.assertTrue(report["core_completion_during_langfuse_outage_verified"])
        self.assertEqual(report["initial_status"], "queued")
        self.assertEqual(report["final_status"], "completed")
        self.assertNotIn(self.token_file.read_text(), json.dumps(report))

    def test_previously_completed_run_is_not_an_outage_proof(self) -> None:
        with (
            patch.object(
                check, "request_json", side_effect=self.response(["completed"])
            ),
            self.assertRaises(check.CheckError),
        ):
            check.outage_run(
                self.client, self.run_id, "http://127.0.0.1:8080", self.token_file, 1
            )

    def test_healthy_backend_is_not_an_outage_proof(self) -> None:
        with (
            patch.object(
                check, "request_json", side_effect=self.response(["queued"], True)
            ),
            self.assertRaises(check.CheckError),
        ):
            check.outage_run(
                self.client, self.run_id, "http://127.0.0.1:8080", self.token_file, 1
            )

    def test_workflow_failure_during_outage_is_not_reported_as_success(self) -> None:
        with (
            patch.object(
                check, "request_json", side_effect=self.response(["queued", "failed"])
            ),
            self.assertRaises(check.CheckError),
        ):
            check.outage_run(
                self.client, self.run_id, "http://127.0.0.1:8080", self.token_file, 1
            )


@unittest.skipUnless(
    os.environ.get("ADF_TEST_OTEL_DOCKER") == "1",
    "Set ADF_TEST_OTEL_DOCKER=1 for the real isolated Docker export contract",
)
class CollectorDockerPrivacyTests(unittest.TestCase):
    """Capture actual OTLP export before Langfuse can discard unmapped fields."""

    def test_actual_export_removes_sentinel_and_preserves_parent_context(self) -> None:
        sample = check.fixture()
        identifier = uuid4().hex[:10]
        network = "adf-otel-test-" + identifier
        capture_name, collector_name = network + "-capture", network + "-collector"
        python_image = (
            "python:3.12.9-slim@sha256:"
            "48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44"
        )
        lock = prepare.SourceLock.read(ROOT / "infra/langfuse-source.lock.json")
        collector_image = next(
            pin.reference for pin in lock.images if pin.variable == "OTEL_IMAGE"
        )
        server_source = """from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json,time
root=Path('/qa')
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  count=int(self.headers.get('Content-Length','0'))
  if count>1048576:
   self.send_response(413);self.end_headers();return
  data=self.rfile.read(count)
  json.loads(data)
  (root/('export-'+str(time.time_ns())+'.json')).write_bytes(data)
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{}')
 def do_GET(self):
  data=[json.loads(p.read_bytes()) for p in root.glob('export-*.json')]
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'payloads':data}).encode())
 def log_message(self,*args):pass
HTTPServer(('0.0.0.0',8080),Handler).serve_forever()
"""

        def docker(arguments: list[str], timeout: int = 45) -> str:
            result = prepare.docker(arguments, timeout)
            if not isinstance(result, str):
                raise TypeError("Docker command returned a non-text result")
            return result

        def port() -> int:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                return int(sock.getsockname()[1])

        collector_port, capture_port = port(), port()
        started: list[str] = []
        network_created = False
        with tempfile.TemporaryDirectory(prefix="adf-otel-docker-test-") as temporary:
            directory = Path(temporary).resolve()
            if not directory.is_relative_to(Path(tempfile.gettempdir()).resolve()):
                self.fail("Docker QA directory escaped the intended temporary root")
            (directory / "capture.py").write_text(server_source, encoding="utf-8")
            fragment = {
                "exporters": {
                    "otlphttp/langfuse": {
                        "endpoint": "http://capture:8080/api/public/otel",
                        "encoding": "json",
                        "compression": "none",
                    }
                }
            }
            (directory / "collector-qa.yaml").write_text(
                json.dumps(fragment), encoding="utf-8"
            )
            try:
                docker(["pull", python_image], 300)
                docker(["pull", collector_image], 300)
                docker(["network", "create", network])
                network_created = True
                docker(
                    [
                        "run",
                        "-d",
                        "--name",
                        capture_name,
                        "--network",
                        network,
                        "--network-alias",
                        "capture",
                        "--memory",
                        "128m",
                        "--cpus",
                        "0.25",
                        "-p",
                        f"127.0.0.1:{capture_port}:8080",
                        "--mount",
                        f"type=bind,source={directory},target=/qa",
                        python_image,
                        "python",
                        "/qa/capture.py",
                    ]
                )
                started.append(capture_name)
                docker(
                    [
                        "run",
                        "-d",
                        "--name",
                        collector_name,
                        "--network",
                        network,
                        "--memory",
                        "384m",
                        "--cpus",
                        "0.5",
                        "-p",
                        f"127.0.0.1:{collector_port}:4318",
                        "--mount",
                        (
                            f"type=bind,source={ROOT / 'infra/otel-collector.yaml'},"
                            "target=/etc/otelcol/config.yaml,readonly"
                        ),
                        "--mount",
                        (
                            f"type=bind,source={directory / 'collector-qa.yaml'},"
                            "target=/etc/otelcol/qa.yaml,readonly"
                        ),
                        collector_image,
                        "--config=/etc/otelcol/config.yaml",
                        "--config=/etc/otelcol/qa.yaml",
                    ]
                )
                started.append(collector_name)
                deadline = time.monotonic() + 30
                while True:
                    try:
                        check.request_json(
                            f"http://127.0.0.1:{collector_port}/v1/traces",
                            body=sample.body,
                        )
                        break
                    except check.CheckError:
                        if time.monotonic() > deadline:
                            self.fail(
                                "Isolated Collector did not accept the test trace"
                            )
                        time.sleep(0.5)
                exported: list[dict[str, Any]] = []
                while time.monotonic() < deadline:
                    try:
                        exported = check.request_json(
                            f"http://127.0.0.1:{capture_port}/"
                        )["payloads"]
                    except check.CheckError:
                        exported = []
                    if exported:
                        break
                    time.sleep(0.5)
                if not exported:
                    self.fail("No actual export reached the isolated capture backend")
                if sample.sentinel in json.dumps(exported):
                    self.fail("Sentinel appeared in actual Collector export")
                spans: list[dict[str, Any]] = []
                for payload in exported:
                    for resource in payload.get("resourceSpans", []):
                        self.assertEqual(
                            {
                                item["key"]
                                for item in resource["resource"]["attributes"]
                            },
                            {"service.name"},
                        )
                        for scope in resource.get("scopeSpans", []):
                            self.assertEqual(scope["scope"]["name"], "adf")
                            spans.extend(scope.get("spans", []))
                self.assertEqual(len(spans), 2)
                by_id = {span["spanId"]: span for span in spans}
                self.assertEqual(
                    set(by_id), {sample.root_span_id, sample.child_span_id}
                )
                self.assertEqual(
                    by_id[sample.child_span_id]["parentSpanId"], sample.root_span_id
                )
                for span in spans:
                    self.assertFalse(span.get("events"))
                    self.assertFalse(span.get("links"))
                    self.assertFalse(span.get("traceState"))
                    self.assertFalse(span.get("status", {}).get("message"))
                    attrs = {item["key"]: item["value"] for item in span["attributes"]}
                    self.assertEqual(
                        attrs["langfuse.trace.metadata.run_id"]["stringValue"],
                        sample.run_id,
                    )
                    self.assertEqual(
                        attrs["langfuse.session.id"]["stringValue"], sample.run_id
                    )
                # QA containers have no credential mounts; logs still remain private.
                executable = prepare.shutil.which("docker")
                if executable is None:
                    self.fail("Docker executable disappeared during the test")
                logs = subprocess.run(  # noqa: S603 -- fixed QA container name
                    [executable, "logs", collector_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                    shell=False,
                )
                if sample.sentinel in logs.stdout + logs.stderr:
                    self.fail("Sentinel appeared in Collector logs")
            finally:
                for name in reversed(started):
                    docker(["rm", "-f", name])
                if network_created:
                    docker(["network", "rm", network])


if __name__ == "__main__":
    unittest.main()
