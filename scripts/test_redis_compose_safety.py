"""Source-only tests: Docker, Redis, namespaces and real credentials are never used."""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
PRIVATE = "PRIVATE_SYNTHETIC_VALUE"


def load_script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(
        "adf_test_" + name.replace("-", "_"), SCRIPTS / (name + ".py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Fixed source module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_script("redis-aof-audit")
REGRESSION = load_script("redis-aof-regression")
COMPOSE = load_script("compose-adf")


def frames(*commands: list[Any]) -> bytes:
    return b"".join(REGRESSION.resp(command) for command in commands)


def symbolic_model() -> dict[str, Any]:
    services: dict[str, Any] = {
        name: {
            "image": "${PINNED_IMAGE:?required}",
            "environment": {"PASSWORD": "${PASSWORD:?required}"},
            "networks": {"default": {"aliases": ["existing-alias"]}},
        }
        for name in COMPOSE.SERVICE_MAP
    }
    services["langfuse-web"]["depends_on"] = {
        "postgres": {"condition": "service_healthy"}
    }
    services["langfuse-web"]["networks"]["telemetry"] = {"aliases": ["adf-langfuse"]}
    services["postgres"]["volumes"] = [
        {"type": "volume", "source": "database", "target": "/data"}
    ]
    return {
        "services": services,
        "volumes": {"database": {"name": "adf-langfuse_database"}},
        "networks": {
            "default": {"name": "adf-langfuse_default"},
            "telemetry": {"name": "adf-telemetry"},
        },
    }


def canonical_status() -> dict[str, Any]:
    rows = [
        {
            "id": str(number),
            "name": name,
            "project": "adf",
            "service": service,
            "state": "exited" if service == "migrator" else "running",
        }
        for number, (service, name) in enumerate(COMPOSE.CONTAINERS.items())
    ]
    return {
        "target_container_count": len(rows),
        "target_containers": rows,
        "migration_required": False,
        "extra_adf_label_members": [],
    }


class AuditSafetyTests(unittest.TestCase):
    def test_minid_threshold_is_not_delivery_and_payload_is_discarded(self):
        threshold, actual = "100-0", "200-0"
        retained = []
        original = AUDIT.Reader.bulk

        def record(reader, keep):
            value = original(reader, keep)
            if keep:
                retained.append(value)
            return value

        data = frames(
            [
                "XADD",
                "adf:executions",
                "NOMKSTREAM",
                "MINID",
                "~",
                threshold,
                "LIMIT",
                5,
                actual,
                PRIVATE,
                PRIVATE,
            ],
            ["XGROUP", "CREATECONSUMER", "adf:executions", "adf-workers", PRIVATE],
        )
        with mock.patch.object(AUDIT.Reader, "bulk", record):
            report = AUDIT.audit(io.BytesIO(data), [threshold, actual])
        self.assertEqual(report["target_deliveries"][threshold]["xadd"], 0)
        self.assertEqual(report["target_deliveries"][actual]["xadd"], 1)
        self.assertNotIn(PRIVATE.encode(), retained)
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_supported_xadd_trimming_forms(self):
        for options in (
            [],
            ["NOMKSTREAM"],
            ["MAXLEN", 50],
            ["MAXLEN", "=", 50],
            ["MAXLEN", "~", 50, "LIMIT", 2],
            ["MINID", "=", "10-0"],
        ):
            with self.subTest(options=options):
                data = frames(
                    ["XADD", "adf:executions", *options, "20-0", "body", PRIVATE]
                )
                report = AUDIT.audit(io.BytesIO(data), ["20-0"])
                self.assertEqual(report["target_deliveries"]["20-0"]["xadd"], 1)

    def test_invalid_xadd_options_fail_closed(self):
        for options in (
            ["MINID", PRIVATE],
            ["MINID", "1-0", "LIMIT", 3],
            ["MAXLEN", "~", "1-0"],
            ["NOMKSTREAM", "NOMKSTREAM"],
            ["LIMIT", 3],
            ["MAXLEN", 1, "MINID", "1-0"],
        ):
            with self.subTest(options=options):
                with self.assertRaises(AUDIT.AuditError) as error:
                    AUDIT.audit(
                        io.BytesIO(
                            frames(
                                [
                                    "XADD",
                                    "adf:executions",
                                    *options,
                                    "20-0",
                                    "body",
                                    PRIVATE,
                                ]
                            )
                        ),
                        ["20-0"],
                    )
                self.assertNotIn(PRIVATE, str(error.exception))

    def test_lastid_is_not_a_claim_and_consumer_is_private(self):
        data = frames(
            ["MULTI"],
            [
                "XCLAIM",
                "adf:executions",
                "adf-workers",
                PRIVATE,
                0,
                "10-0",
                "TIME",
                100,
                "LASTID",
                "20-0",
            ],
            ["EXEC"],
            ["XACK", "adf:executions", "adf-workers", "10-0"],
            ["XDEL", "adf:executions", "20-0"],
        )
        report = AUDIT.audit(io.BytesIO(data), ["10-0", "20-0"])
        self.assertEqual(report["target_deliveries"]["10-0"]["claim_in_multi"], 1)
        self.assertEqual(report["target_deliveries"]["20-0"]["claim_in_multi"], 0)
        self.assertEqual(report["target_deliveries"]["10-0"]["ack"], 1)
        self.assertEqual(report["target_deliveries"]["20-0"]["delete"], 1)
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_framing_transaction_and_quota_failures_are_closed(self):
        bad = (
            b"*4097\r\n",
            b"*1\r\n$5\r\nHELLO",
            b"*1\n",
            frames(["EXEC"]),
            frames(["MULTI"]),
            frames(["MULTI"], ["MULTI"]),
            frames(["MULTI", PRIVATE]),
        )
        for data in bad:
            with self.subTest(data=data):
                with self.assertRaises(AUDIT.AuditError) as error:
                    AUDIT.audit(io.BytesIO(data), [])
                self.assertNotIn(PRIVATE, str(error.exception))
        with mock.patch.object(AUDIT, "LIMIT", 8), self.assertRaises(AUDIT.AuditError):
            AUDIT.audit(io.BytesIO(frames(["SET", "key", PRIVATE])), [])
        for targets in (["1-0"] * 65, ["not-an-id"], ["\u0438"]):
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.audit(io.BytesIO(), targets)

    def test_blank_line_before_command_is_not_eof(self):
        data = b"\r\n" + frames(["XADD", "adf:executions", "20-0", "body", PRIVATE])
        with self.assertRaises(AUDIT.AuditError) as error:
            AUDIT.audit(io.BytesIO(data), ["20-0"])
        self.assertEqual(str(error.exception), "AOF_INVALID_FRAME")

    def test_trailing_blank_line_is_not_eof(self):
        data = frames(["XADD", "adf:executions", "20-0", "body", PRIVATE]) + b"\r\n"
        with self.assertRaises(AUDIT.AuditError) as error:
            AUDIT.audit(io.BytesIO(data), ["20-0"])
        self.assertEqual(str(error.exception), "AOF_INVALID_FRAME")

    def test_synthetic_transaction_has_select_and_three_replayed_commands(self):
        commands = REGRESSION.synthetic_commands()
        multi = commands.index(["MULTI"])
        self.assertEqual(commands[multi + 1], ["SELECT", 0])
        report = AUDIT.audit(io.BytesIO(frames(*commands)), REGRESSION.IDS)
        self.assertEqual(report["transactions"], 1)
        self.assertEqual(report["commands_inside_multi"]["SELECT"], 1)
        self.assertEqual(report["commands_inside_multi"]["XCLAIM"], 1)
        self.assertEqual(report["commands_inside_multi"]["XGROUP"], 1)
        self.assertTrue(
            all(
                row["claim_in_multi"] == 1
                for row in report["target_deliveries"].values()
            )
        )


class RegressionSafetyTests(unittest.TestCase):
    def test_checks_survive_optimized_compilation(self):
        path = SCRIPTS / "redis-aof-regression.py"
        source = path.read_text(encoding="utf-8")
        self.assertFalse(
            any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(source)))
        )
        namespace: dict[str, Any] = {
            "__name__": "optimized_synthetic_source",
            "__file__": str(path),
        }
        exec(compile(source, str(path), "exec", optimize=2), namespace)  # noqa: S102 -- fixed local source, no user input
        with self.assertRaises(RuntimeError):
            namespace["require"](False)
        with self.assertRaises(RuntimeError):
            namespace["read_value"](io.BytesIO(b"$1\r\nx??"))

    def test_default_auth_requires_wrongpass_and_never_emits_raw_error(self):
        calls = []

        def disabled(*args):
            calls.append(args)
            return REGRESSION.read_value(
                io.BytesIO(b"-WRONGPASS " + PRIVATE.encode() + b"\r\n")
            )

        REGRESSION.require_disabled_default(disabled)
        self.assertEqual(calls, [("AUTH", "default", "")])
        for call in (
            lambda *_: "OK",
            lambda *_: REGRESSION.read_value(io.BytesIO(b"-NOPERM private\r\n")),
        ):
            with self.assertRaises(RuntimeError) as error:
                REGRESSION.require_disabled_default(call)
            self.assertNotIn(PRIVATE, str(error.exception))

    def test_reply_framing_quotas_and_numeric_errors_are_closed(self):
        for data in (
            b"$65537\r\n",
            b"*4097\r\n",
            b"*-2\r\n",
            b"$1\r\nx??",
            b":" + PRIVATE.encode() + b"\r\n",
        ):
            with self.subTest(data=data), self.assertRaises(RuntimeError) as error:
                REGRESSION.read_value(io.BytesIO(data))
            self.assertNotIn(PRIVATE, str(error.exception))


class ComposeSafetyTests(unittest.TestCase):
    def setUp(self):
        COMPOSE.APPLY_ATTEMPTED = False

    def test_prepare_uses_only_blank_environment_and_symbolic_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vendor = root / "infra/vendor/langfuse/docker-compose.yml"
            vendor.parent.mkdir(parents=True)
            vendor.write_bytes(b"synthetic-public-compose")
            (root / "infra/langfuse-source.lock.json").write_text(
                json.dumps(
                    {"compose_sha256": hashlib.sha256(vendor.read_bytes()).hexdigest()}
                ),
                encoding="utf-8",
            )
            model = root / ".bootstrap/compose.adf-observability.json"
            paths = []

            def docker(argv):
                self.assertIn("--no-interpolate", argv)
                self.assertIn("--no-env-resolution", argv)
                self.assertEqual(argv.count("--env-file"), 1)
                blank = Path(argv[argv.index("--env-file") + 1])
                self.assertEqual(blank.read_bytes(), b"")
                paths.append(blank)
                return json.dumps(symbolic_model()).encode()

            with (
                mock.patch.object(COMPOSE, "ROOT", root),
                mock.patch.object(COMPOSE, "MODEL", model),
                mock.patch.object(COMPOSE, "docker", side_effect=docker),
            ):
                report = COMPOSE.prepare()
            self.assertEqual(len(paths), 1)
            self.assertFalse(paths[0].exists())
            self.assertFalse(report["real_credentials_resolved_or_copied"])
            self.assertIn("${PASSWORD:?required}", model.read_text(encoding="utf-8"))

    def test_symbolic_environment_aliases_and_external_references(self):
        original = symbolic_model()
        before = copy.deepcopy(original)
        result = COMPOSE.grouped_model(original)
        self.assertEqual(original, before)
        self.assertEqual(
            result["services"]["langfuse-web"]["environment"],
            {"PASSWORD": "${PASSWORD:?required}"},
        )
        self.assertEqual(
            result["services"]["langfuse-web"]["image"], "${PINNED_IMAGE:?required}"
        )
        self.assertEqual(
            set(result["services"]["langfuse-web"]["depends_on"]), {"langfuse-postgres"}
        )
        self.assertEqual(
            result["services"]["langfuse-postgres"]["networks"]["langfuse-existing"][
                "aliases"
            ],
            ["existing-alias", "postgres"],
        )
        self.assertEqual(
            result["volumes"],
            {"database": {"external": True, "name": "adf-langfuse_database"}},
        )
        self.assertEqual(
            result["networks"]["langfuse-existing"],
            {"external": True, "name": "adf-langfuse_default"},
        )

    def test_foreign_references_fail_closed(self):
        for mutation in (
            lambda m: m["services"]["langfuse-web"].update(depends_on={PRIVATE: {}}),
            lambda m: m["services"]["postgres"]["volumes"][0].update(source=PRIVATE),
            lambda m: m["services"]["postgres"].update(networks={PRIVATE: {}}),
            lambda m: m["volumes"]["database"].update(name="adf-langfuse_" + PRIVATE),
            lambda m: m["networks"]["default"].update(name="adf-telemetry"),
        ):
            source = symbolic_model()
            mutation(source)
            with self.assertRaises(COMPOSE.GroupError) as error:
                COMPOSE.grouped_model(source)
            self.assertNotIn(PRIVATE, str(error.exception))

    def test_exact_labels_for_all_thirteen_targets(self):
        status = canonical_status()
        self.assertEqual(len(status["target_containers"]), 13)
        rows = status["target_containers"]
        for changed in range(13):
            for label in ("project", "service"):
                bad = copy.deepcopy(rows)
                bad[changed][label] = PRIVATE
                text = "\n".join(
                    "|".join(
                        row[key]
                        for key in ("id", "name", "project", "service", "state")
                    )
                    for row in bad
                )
                with (
                    self.subTest(changed=changed, label=label),
                    mock.patch.object(COMPOSE, "docker", return_value=text.encode()),
                ):
                    with self.assertRaises(COMPOSE.GroupError) as error:
                        COMPOSE.inventory()
                    self.assertNotIn(PRIVATE, str(error.exception))
        text = "\n".join(
            "|".join(row[key] for key in ("id", "name", "project", "service", "state"))
            for row in rows
        )
        with mock.patch.object(COMPOSE, "docker", return_value=text.encode()):
            self.assertFalse(COMPOSE.inventory()["migration_required"])

    def test_start_is_closed_before_docker_for_missing_or_forged_members(self):
        mutations = (
            lambda s: s.update(migration_required=True),
            lambda s: s.update(extra_adf_label_members=[{}]),
            lambda s: s["target_containers"].pop(),
            lambda s: s["target_containers"][0].update(service=PRIVATE),
            lambda s: s["target_containers"][1].update(state="exited"),
        )
        for change in mutations:
            status = canonical_status()
            change(status)
            with mock.patch.object(
                COMPOSE,
                "docker",
                side_effect=AssertionError("Unexpected Docker access"),
            ) as docker:
                with self.assertRaises(COMPOSE.GroupError):
                    COMPOSE.start_guard(status)
                docker.assert_not_called()

    def test_stderr_loading_errors_are_captured_and_private(self):
        def fake_run(argv, **_kwargs):
            if "inspect" in argv:
                return subprocess.CompletedProcess(
                    argv, 0, b"2026-10-12T00:00:00Z\n", b""
                )
            return subprocess.CompletedProcess(
                argv,
                0,
                b"DB loaded from append only file: 0.1 seconds\nReady to accept connections\n",
                b"AOF-loading-client NOPERM " + PRIVATE.encode(),
            )

        with (
            mock.patch.object(COMPOSE.shutil, "which", return_value="synthetic-docker"),
            mock.patch.object(COMPOSE.subprocess, "run", side_effect=fake_run),
        ):
            with self.assertRaises(COMPOSE.GroupError) as error:
                COMPOSE.start_guard(canonical_status())
        self.assertNotIn(PRIVATE, str(error.exception))
        self.assertNotIn(PRIVATE, json.dumps(COMPOSE.failure_report()))

    def test_successful_load_and_ready_are_required_and_truncation_blocks(self):
        success = b"DB loaded from append only file: 0.1 seconds\nReady to accept connections\n"
        for log in (
            b"PONG",
            b"Ready to accept connections",
            b"DB loaded from append only file:",
            success + b"short read loading AOF",
            success + b"Truncating the AOF file",
            success + b"Error loading AOF",
        ):
            calls = []

            def docker(argv, *_args, **kwargs):
                calls.append((argv, kwargs))
                return b"started-at\n" if argv[0] == "inspect" else log

            with (
                self.subTest(log=log),
                mock.patch.object(COMPOSE, "docker", side_effect=docker),
            ):
                with self.assertRaises(COMPOSE.GroupError):
                    COMPOSE.start_guard(canonical_status())
            self.assertTrue(calls[-1][1]["capture_stderr"])

    def test_start_excludes_migrator_and_dependencies_without_real_docker(self):
        with (
            mock.patch.object(sys, "argv", ["compose-adf.py", "start"]),
            mock.patch.object(COMPOSE, "prepare", return_value={}),
            mock.patch.object(COMPOSE, "inventory", return_value=canonical_status()),
            mock.patch.object(COMPOSE, "start_guard"),
            mock.patch.object(COMPOSE, "docker", return_value=b"") as docker,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            COMPOSE.main()
        argv = docker.call_args.args[0]
        self.assertIn("--no-deps", argv)
        self.assertIn("--no-recreate", argv)
        self.assertNotIn("migrator", argv)
        self.assertEqual(argv[-12:], COMPOSE.START_SERVICES)

    def test_failed_up_reports_possible_partial_apply(self):
        for error in (
            COMPOSE.GroupError("DOCKER_COMMAND_FAILED_OUTPUT_WITHHELD"),
            subprocess.TimeoutExpired(PRIVATE, 240),
        ):
            with (
                self.subTest(error=type(error).__name__),
                mock.patch.object(sys, "argv", ["compose-adf.py", "start"]),
                mock.patch.object(COMPOSE, "prepare", return_value={}),
                mock.patch.object(
                    COMPOSE, "inventory", return_value=canonical_status()
                ),
                mock.patch.object(COMPOSE, "start_guard"),
                mock.patch.object(COMPOSE, "docker", side_effect=error),
            ):
                with self.assertRaises(type(error)):
                    COMPOSE.main()
            report = COMPOSE.failure_report()
            self.assertTrue(report["apply_attempted"])
            self.assertIsNone(report["containers_changed"])
            self.assertEqual(report["apply_outcome"], "partial_or_unknown")
            self.assertNotIn(PRIVATE, json.dumps(report))

    def test_plan_never_applies(self):
        with (
            mock.patch.object(sys, "argv", ["compose-adf.py", "plan"]),
            mock.patch.object(COMPOSE, "prepare", return_value={}),
            mock.patch.object(COMPOSE, "inventory", return_value=canonical_status()),
            mock.patch.object(
                COMPOSE,
                "docker",
                side_effect=AssertionError("Unexpected Docker access"),
            ) as docker,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            COMPOSE.main()
        docker.assert_not_called()
        self.assertFalse(COMPOSE.failure_report()["apply_attempted"])
        self.assertFalse(COMPOSE.failure_report()["containers_changed"])


if __name__ == "__main__":
    unittest.main()
