"""Meaningful security fixtures for disconnected recovery orchestration."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError("Fixture module missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


recovery = load("test_adf_recovery", "rehearse-recovery.py")
http = load("test_adf_recovery_http", "recovery-http.py")
worker = load("test_adf_recovery_worker", "recovery-worker.py")


class RecoverySafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        module = Mock()
        module.new_file.side_effect = lambda path: path.open("xb")
        module.command.return_value = json.dumps(
            {"adf.recovery.namespace": "1234abcd"}
        ).encode()
        self.module = module
        self.qa = recovery.Rehearsal(
            "1234abcd",
            "20261010T185527Z-9e8590ed",
            module,
            {
                "admin-token": "a" * 64,
                "orchestrator-token": "b" * 64,
                "worker-token": "c" * 64,
                "api-password": "d" * 64,
                "redis-password": "e" * 64,
            },
            {
                key: "sha256:" + "f" * 64
                for key in ("api", "orch", "frontend", "pg", "redis")
            },
            self.root,
            "00000000-0000-0000-0000-000000000001",
            roots={"a": "/home/test/ai-factory/recovery-rehearsals/1234abcd/stage-a"},
        )

    def test_explicit_flag_precedes_snapshot_and_docker(self) -> None:
        with patch.object(recovery, "snapshot_module") as helper:
            with self.assertRaises(recovery.RecoveryError):
                recovery.run("untrusted", enabled=False)
            helper.assert_not_called()

    def test_source_or_foreign_name_refused_before_inspect(self) -> None:
        for name in (
            "adf-api-1",
            "adf-recovery-ffffffff-a-api",
            "adf-recovery-1234abcd-a-api/../../adf-api-1",
        ):
            with self.assertRaises(recovery.RecoveryError):
                self.qa.guard(name)
        self.module.command.assert_not_called()

    def test_foreign_label_refused(self) -> None:
        self.module.command.return_value = b'{"adf.recovery.namespace":"ffffffff"}'
        with self.assertRaises(recovery.RecoveryError):
            self.qa.guard(self.qa.name("a", "api"))

    def test_network_external_or_foreign_label_refused(self) -> None:
        self.module.command.return_value = json.dumps(
            {"Internal": False, "Labels": {"adf.recovery.namespace": "1234abcd"}}
        ).encode()
        with self.assertRaises(recovery.RecoveryError):
            self.qa.isolation("a")
        self.assertEqual(self.module.command.call_count, 1)

    def test_host_port_refused_from_actual_inspection(self) -> None:
        self.module.command.side_effect = [
            json.dumps(
                {"Internal": True, "Labels": {"adf.recovery.namespace": "1234abcd"}}
            ).encode(),
            json.dumps({"adf.recovery.namespace": "1234abcd"}).encode(),
            json.dumps(
                {
                    "host": {"PortBindings": {"5432/tcp": [{"HostPort": "5432"}]}},
                    "mounts": [],
                    "networks": {},
                }
            ).encode(),
        ]
        with self.assertRaises(recovery.RecoveryError):
            self.qa.isolation("a")

    def test_bind_mount_refused(self) -> None:
        self.module.command.side_effect = [
            json.dumps(
                {"Internal": True, "Labels": {"adf.recovery.namespace": "1234abcd"}}
            ).encode(),
            json.dumps({"adf.recovery.namespace": "1234abcd"}).encode(),
            json.dumps(
                {
                    "host": {"PortBindings": {}, "Binds": None},
                    "mounts": [{"Type": "bind", "Destination": "/source"}],
                    "networks": {},
                }
            ).encode(),
        ]
        with self.assertRaises(recovery.RecoveryError):
            self.qa.isolation("a")

    def test_psql_variables_refuse_noncanonical_or_injection_before_command(
        self,
    ) -> None:
        for value in (
            "-' OR true --",
            "a" * 36,
            "00000000-0000-0000-0000-00000000000A",
        ):
            with self.assertRaises(recovery.RecoveryError):
                self.qa.sql("a", "SELECT 1", run_id=value)
        self.module.command.assert_not_called()

    def test_terminal_duplicate_batch_never_relaunches_executor(self) -> None:
        qa = Mock()
        execution = "00000000-0000-0000-0000-000000000002"
        qa.worker_id = self.qa.worker_id
        qa.roots = {"b": "/private/qa/projects"}
        qa.projects = {"b": {self.qa.worker_id: "/private/qa/projects/repo"}}
        qa.http.side_effect = [
            {},
            {"executions": []},
            {"status": "running"},
            {"status": "completed"},
        ]
        message = [
            [
                "adf:executions",
                [
                    ["1-0", ["execution_id", execution]],
                    ["1-1", ["execution_id", execution]],
                ],
            ]
        ]
        qa.redis.side_effect = ["OK", message, 2]
        qa.worker.return_value = {"execution_id": execution, "status": "succeeded"}
        result = recovery.drive(qa, {"run_id": self.qa.worker_id})
        self.assertEqual(qa.worker.call_count, 1)
        self.assertEqual(result["duplicate_messages_acknowledged"], 1)
        self.assertEqual(len(result["executed"]), 1)
        self.assertEqual(qa.redis.call_args.args[1][-2:], ["1-0", "1-1"])

    def test_credentials_absent_from_dataclass_repr(self) -> None:
        self.assertNotIn("a" * 64, repr(self.qa))
        self.assertNotIn("e" * 64, repr(self.qa))

    def test_create_no_ports_mounts_or_cli_credentials(self) -> None:
        self.qa.create("a", "api")
        argv = self.module.command.call_args_list[0].args[1]
        self.assertEqual(argv[0], "create")
        self.assertIn("--pull=never", argv)
        self.assertNotIn("--publish", argv)
        self.assertNotIn("--mount", argv)
        self.assertNotIn("--volume", argv)
        self.assertIn("adf-recovery-1234abcd-a-network", argv)
        self.assertNotIn("a" * 64, " ".join(argv))
        self.assertNotIn("e" * 64, " ".join(argv))
        self.assertIn("ADF_TELEMETRY_ENABLED=false", argv)

    def test_secret_archive_owned_private_only_expected_files(self) -> None:
        path = self.qa.secret_archive("a", "api")
        with tarfile.open(path) as archive:
            entries = archive.getmembers()
            self.assertEqual(entries[0].mode, 0o700)
            for item in entries[1:]:
                self.assertEqual(item.mode, 0o600)
                self.assertEqual(item.uid, 10001)
                self.assertTrue(item.name.startswith("run/qa/"))
                self.assertNotIn("..", item.name)
            self.assertEqual(len(entries), 6)

    def test_capacity_measured_before_qa(self) -> None:
        self.module.command.side_effect = [
            b"10000000000",
            b"one\ntwo\n",
            b'{"MemUsage":"1.0GiB / 10GiB"}\n',
        ]
        data = recovery.resource_preflight(self.module)
        self.assertEqual(data["running_container_count"], 2)
        self.assertEqual(data["measured_used_bytes"], 1024**3)

    def test_insufficient_memory_refused(self) -> None:
        self.module.command.side_effect = [
            b"4000000000",
            b"one\n",
            b'{"MemUsage":"3.0GiB / 4GiB"}\n',
        ]
        with self.assertRaises(recovery.RecoveryError):
            recovery.resource_preflight(self.module)

    def test_redis_destructive_or_other_stream_commands_refused_before_socket(
        self,
    ) -> None:
        with patch.object(http.socket, "create_connection") as connection:
            for args in (
                ["FLUSHALL"],
                ["XACK", "source", "adf-workers", "1-0"],
                ["XACK", "adf:executions", "adf-workers", "1-0;bad"],
            ):
                with self.assertRaises(ValueError):
                    http.redis_command(args)
            connection.assert_not_called()

    def test_resp_size_depth_truncation(self) -> None:
        for raw in (b"$999999999\r\n", b"$2\r\nx\r\n", b"*10001\r\n"):
            with self.assertRaises(ValueError):
                http.redis_reply(io.BytesIO(raw))
        self.assertEqual(
            http.redis_reply(io.BytesIO(b"*2\r\n+OK\r\n:3\r\n")), ["OK", 3]
        )
        with self.assertRaises(ValueError):
            http.redis_reply(io.BytesIO(b"+OK\r\n"), 13)

    def test_http_other_origin_path_or_method_refused(self) -> None:
        with patch.object(http, "build_opener") as opener:
            for method, path in (
                ("DELETE", "/api/runs/x"),
                ("GET", "http://source/"),
                ("POST", "/internal/../../source"),
            ):
                with self.assertRaises(ValueError):
                    http.http({"method": method, "path": path})
            opener.assert_not_called()

    def test_worker_query_route_uses_worker_token(self) -> None:
        opener = Mock()
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"cancel_requested":false}'
        response.status = 200
        opener.open.return_value = response
        with (
            patch.object(http, "build_opener", return_value=opener),
            patch.object(
                Path,
                "read_text",
                autospec=True,
                return_value="sentinel-private-worker-token",
            ) as read,
        ):
            http.http(
                {
                    "method": "GET",
                    "path": (
                        "/internal/executions/00000000-0000-0000-0000-000000000001/"
                        "control?worker_id=qa&epoch=1"
                    ),
                }
            )
            self.assertEqual(read.call_args.args[0].name, "worker-token")

    def test_worker_command_arbitrary_executable_refused(self) -> None:
        with self.assertRaises(ValueError):
            worker.command(["/bin/sh", "-c", "echo forbidden"])
        self.assertNotIn("OPENAI_API_KEY", worker.environment())
        self.assertEqual(worker.environment()["GIT_TERMINAL_PROMPT"], "0")

    def test_uuid_and_relocation_program_compile(self) -> None:
        self.assertEqual(worker.canonical_id(self.qa.worker_id), self.qa.worker_id)
        with self.assertRaises(ValueError):
            worker.canonical_id("not-an-id")
        compile(recovery.REMAP_PROGRAM, "private-qa-relocation", "exec")
        self.assertIn(
            "Only never-spawned QA fixture may relocate", recovery.REMAP_PROGRAM
        )


if __name__ == "__main__":
    unittest.main()
