"""Meaningful fail-closed snapshot, credential and archive consistency checks."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_snapshot() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "adf_runtime_snapshot", ROOT / "scripts/snapshot-runtime.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Snapshot script is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


snapshot = load_snapshot()
PID = "11111111-1111-1111-1111-111111111111"
RID = "22222222-2222-2222-2222-222222222222"
EID = "33333333-3333-3333-3333-333333333333"
AID = "44444444-4444-4444-4444-444444444444"
KEY = "55555555-5555-5555-5555-555555555555"
OID = "a" * 40
IMAGE = "postgres:18.0@sha256:" + "a" * 64


class DrainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = snapshot.Client("http://127.0.0.1:8080", "unit-token-private")
        self.run_record: dict[str, Any] = {
            "id": RID,
            "project_id": PID,
            "status": "completed",
            "revision": 2,
            "event_sequence": 7,
            "control": {"pause_requested": False, "cancel_requested": False},
            "executions": [],
        }
        self.states: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {"active_executions": 0, "executions": {}}

    def response(self, client: object, route: str) -> dict[str, Any]:
        if route == "/api/settings":
            return {"allowed_roots": ["/home/alex/ai-factory/projects"]}
        if route.endswith("/executions"):
            return {"items": self.states, "next_cursor": None}
        if route.endswith("/artifacts"):
            return {"items": [], "next_cursor": None}
        if route == "/api/metrics/overview":
            return self.metrics
        raise AssertionError("Unexpected read-only route")

    def pages(self, client: object, route: str) -> list[dict[str, Any]]:
        if route == "/api/projects":
            return [{"id": PID, "repo_path": "/home/alex/ai-factory/projects/example"}]
        return [self.run_record]

    def collect(self) -> Any:
        with (
            patch.object(
                snapshot.Client, "json", autospec=True, side_effect=self.response
            ),
            patch.object(
                snapshot.Client, "pages", autospec=True, side_effect=self.pages
            ),
        ):
            return snapshot.collect(self.client)

    def test_terminal_runs_are_drained(self) -> None:
        self.assertEqual(len(self.collect().runs), 1)

    def test_paused_run_requires_pause_dispatch_fence(self) -> None:
        self.run_record["status"] = "paused"
        with self.assertRaises(snapshot.SnapshotError):
            self.collect()
        self.run_record["control"]["pause_requested"] = True
        self.assertEqual(len(self.collect().runs), 1)

    def test_running_or_queued_run_blocks_snapshot_before_mutation(self) -> None:
        for status in ("running", "queued"):
            with self.subTest(status=status):
                self.run_record["status"] = status
                with (
                    patch.object(
                        snapshot.Client,
                        "json",
                        autospec=True,
                        side_effect=self.response,
                    ),
                    patch.object(
                        snapshot.Client, "pages", autospec=True, side_effect=self.pages
                    ),
                    patch.object(snapshot, "command") as command,
                    self.assertRaises(snapshot.SnapshotError),
                ):
                    snapshot.snapshot(self.client)
                command.assert_not_called()

    def test_all_created_active_cancelling_uncertain_states_are_rejected(self) -> None:
        for state in (
            "created",
            "leased",
            "starting",
            "running",
            "validating",
            "committing",
            "cancelling",
            "uncertain",
        ):
            with self.subTest(state=state):
                self.states = [{"id": EID, "status": state}]
                with self.assertRaises(snapshot.SnapshotError):
                    self.collect()

    def test_global_unseen_execution_blocks_snapshot(self) -> None:
        self.metrics["executions"] = {"created": 1}
        with self.assertRaises(snapshot.SnapshotError):
            self.collect()

    def test_configured_root_escape_is_rejected(self) -> None:
        with (
            patch.object(
                snapshot.Client, "json", autospec=True, side_effect=self.response
            ),
            patch.object(
                snapshot.Client,
                "pages",
                return_value=[{"id": PID, "repo_path": "/home/alex/.codex"}],
            ),
            self.assertRaises(snapshot.SnapshotError),
        ):
            snapshot.collect(self.client)


class PrivateSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="adf-snapshot-test-")
        self.root = Path(self.directory.name)
        self.private = self.root / ".bootstrap/runtime-snapshots"
        self.override = patch.multiple(snapshot, ROOT=self.root, PRIVATE=self.private)
        self.override.start()
        snapshot.make_directory(self.root / ".bootstrap")
        snapshot.make_directory(self.private)
        self.inventory: dict[str, Any] = {
            "projects": [
                {"id": PID, "repo_path": "/home/alex/ai-factory/projects/example"}
            ],
            "runs": [
                {
                    "id": RID,
                    "project_id": PID,
                    "status": "completed",
                    "revision": 1,
                    "event_sequence": 5,
                    "pause_requested": False,
                    "cancel_requested": False,
                }
            ],
            "executions": [
                {"id": EID, "run_id": RID, "status": "succeeded", "epoch": 1}
            ],
            "artifacts": [
                {
                    "id": AID,
                    "run_id": RID,
                    "execution_id": EID,
                    "storage_key": KEY,
                    "size": 5,
                    "sha256": snapshot.hashlib.sha256(b"hello").hexdigest(),
                }
            ],
        }
        self.path = self.private / "20261010T000000Z-aabbccdd"
        snapshot.make_directory(self.path, exclusive=True)
        snapshot.make_directory(self.path / "artifacts")
        snapshot.make_directory(self.path / "git")
        payloads = {
            "database.dump": b"PGDMP-unit-only",
            "artifacts/" + AID + ".bin": b"hello",
            "git/" + PID + ".bundle": (
                "# v2 git bundle\n"
                + OID
                + " HEAD\n"
                + OID
                + " refs/heads/main\n\nPACK-unit-only"
            ).encode(),
        }
        for name, body in payloads.items():
            with snapshot.new_file(self.path / name) as handle:
                handle.write(body)
        snapshot.write_json(self.path / "inventory.json", self.inventory)
        self.manifest: dict[str, Any] = {
            "schema_version": 1,
            "snapshot_id": self.path.name,
            "complete": True,
            "postgres_image": IMAGE,
            "projects": [
                {
                    "id": PID,
                    "repo_path": self.inventory["projects"][0]["repo_path"],
                    "refs": {"HEAD": OID, "refs/heads/main": OID},
                }
            ],
            "artifacts": self.inventory["artifacts"],
            "files": [
                snapshot.file_record(self.path / name, self.path)
                for name in [*payloads, "inventory.json"]
            ],
        }
        snapshot.write_json(self.path / "manifest.json", self.manifest)
        with snapshot.new_file(self.path / "manifest.sha256") as handle:
            handle.write(
                (
                    snapshot.file_record(self.path / "manifest.json", self.path)[
                        "sha256"
                    ]
                    + "\n"
                ).encode()
            )

    def tearDown(self) -> None:
        self.override.stop()
        self.directory.cleanup()

    def resign(self) -> None:
        (self.path / "manifest.json").write_bytes(
            snapshot.canonical(self.manifest) + b"\n"
        )
        (self.path / "manifest.sha256").write_text(
            snapshot.file_record(self.path / "manifest.json", self.path)["sha256"]
            + "\n"
        )

    def execute_snapshot(
        self, *, changed: bool = False, corrupt: bool = False
    ) -> dict[str, Any]:
        before = snapshot.Inventory(
            roots=["/home/alex/ai-factory/projects"],
            projects=self.inventory["projects"],
            runs=[
                {
                    **self.inventory["runs"][0],
                    "control": {"pause_requested": False, "cancel_requested": False},
                    "executions": self.inventory["executions"],
                }
            ],
            artifacts=[
                {key: value for key, value in row.items() if key != "storage_key"}
                for row in self.inventory["artifacts"]
            ],
            fingerprint="a" * 64,
        )
        after = snapshot.Inventory(
            roots=before.roots,
            projects=before.projects,
            runs=before.runs,
            artifacts=before.artifacts,
            fingerprint=("b" if changed else "a") * 64,
        )
        details = {
            "repo_path": self.inventory["projects"][0]["repo_path"],
            "refs": {"HEAD": OID, "refs/heads/main": OID},
            "filesystem": "ext4",
            "clean_worktrees": True,
        }

        def fake_wsl(mode: str, payload: dict[str, Any], **kwargs: Any) -> bytes:
            if mode == "inspect":
                return json.dumps(details).encode()
            self.assertEqual(mode, "bundle")
            with snapshot.new_file(kwargs["output"]) as handle:
                handle.write((self.path / "git" / (PID + ".bundle")).read_bytes())
            return b""

        def fake_command(tool: str, arguments: list[str], **kwargs: Any) -> bytes:
            self.assertEqual(tool, "docker")
            self.assertIn("pg_dump", arguments)
            self.assertNotIn("stop", arguments)
            self.assertNotIn("rm", arguments)
            with snapshot.new_file(kwargs["output"]) as handle:
                handle.write(b"PGDMP-unit-only")
            return b""

        client = snapshot.Client("http://127.0.0.1:8000", "a" * 48)
        with (
            patch.object(snapshot, "collect", side_effect=[before, after]),
            patch.object(snapshot, "source_container"),
            patch.object(snapshot, "postgres_image", return_value=IMAGE),
            patch.object(snapshot, "database_inventory", return_value=self.inventory),
            patch.object(snapshot, "wsl", side_effect=fake_wsl),
            patch.object(snapshot, "command", side_effect=fake_command),
            patch.object(
                snapshot.Client, "get", return_value=b"wrong" if corrupt else b"hello"
            ),
        ):
            result: dict[str, Any] = snapshot.snapshot(client)
        return result

    def test_staged_snapshot_coordinates_artifact_database_and_git_inventory(
        self,
    ) -> None:
        result = self.execute_snapshot()
        self.assertTrue(result["snapshot_created"])
        self.assertFalse(result["services_changed"])
        self.assertFalse(result["restore_tested"])
        manifest = snapshot.verify(Path(result["manifest"]).parent)
        self.assertEqual(manifest["artifacts"], self.inventory["artifacts"])
        self.assertEqual(
            manifest["projects"][0]["refs"], self.manifest["projects"][0]["refs"]
        )

    def test_concurrent_inventory_change_preserves_incomplete_bytes_without_manifest(
        self,
    ) -> None:
        with self.assertRaises(snapshot.SnapshotError):
            self.execute_snapshot(changed=True)
        partial = [path for path in self.private.iterdir() if path != self.path]
        self.assertEqual(len(partial), 1)
        self.assertTrue((partial[0] / "database.dump").is_file())
        self.assertFalse((partial[0] / "manifest.json").exists())

    def test_download_corruption_never_marks_snapshot_complete(self) -> None:
        with self.assertRaises(snapshot.SnapshotError):
            self.execute_snapshot(corrupt=True)
        partial = [path for path in self.private.iterdir() if path != self.path]
        self.assertEqual(len(partial), 1)
        self.assertFalse((partial[0] / "manifest.json").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits only")
    def test_fixture_is_private_and_permissive_existing_directory_is_rejected(
        self,
    ) -> None:
        for directory in (self.root / ".bootstrap", self.private):
            self.assertEqual(directory.stat().st_mode & 0o077, 0)
        self.private.chmod(0o750)
        try:
            with self.assertRaises(snapshot.SnapshotError):
                snapshot.make_directory(self.private)
        finally:
            self.private.chmod(0o700)

    def test_consistent_private_manifest_verifies_without_runtime_commands(
        self,
    ) -> None:
        with patch.object(snapshot, "command") as command:
            self.assertTrue(snapshot.verify(self.path)["complete"])
        command.assert_not_called()

    def test_real_git_bundle_excludes_worktree_pseudo_refs_and_detects_unreachable_tip(
        self,
    ) -> None:
        repo = self.private / "git-fixture"
        repo.mkdir()
        worktree = self.private / "linked-git-fixture"
        options = [
            "-c",
            "user.name=Snapshot Fixture",
            "-c",
            "user.email=snapshot@example.invalid",
            "-c",
            "core.hooksPath=" + os.devnull,
            "-C",
            str(repo),
        ]

        def git(*arguments: str) -> bytes:
            result: bytes = snapshot.command("git", [*options, *arguments])
            return result

        git("init", "--initial-branch=main")
        git("commit", "--allow-empty", "--message", "Initial fixture")
        git("worktree", "add", "--detach", str(worktree), "HEAD")
        body = git(
            "bundle", "create", "--quiet", "-", "--single-worktree", "--all", "HEAD"
        )
        target = self.private / "real.bundle"
        with snapshot.new_file(target) as output:
            output.write(body)
        refs = snapshot.bundle_refs(target)
        tip = git("rev-parse", "HEAD").decode().strip()
        self.assertEqual(refs, {"HEAD": tip, "refs/heads/main": tip})
        snapshot.command(
            "git",
            [
                *options[:-2],
                "-C",
                str(worktree),
                "commit",
                "--allow-empty",
                "--message",
                "Detached-only fixture",
            ],
        )
        detached = (
            snapshot.command("git", ["-C", str(worktree), "rev-parse", "HEAD"])
            .decode()
            .strip()
        )
        self.assertEqual(
            git(
                "rev-list",
                "--count",
                detached,
                "--not",
                "--single-worktree",
                "--all",
                "HEAD",
            ).strip(),
            b"1",
        )
        self.assertIn('"--single-worktree"', snapshot.WSL_PROGRAM)
        self.assertIn(
            "Detached worktree HEAD needs a named ref before backup",
            snapshot.WSL_PROGRAM,
        )

    def test_payload_tampering_is_rejected(self) -> None:
        (self.path / "database.dump").write_bytes(b"PGDMP-tampered")
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.verify(self.path)

    def test_resigned_manifest_cannot_hide_artifact_or_git_parent_inventory(
        self,
    ) -> None:
        for field in ("artifacts", "projects"):
            original = copy.deepcopy(self.manifest)
            self.manifest[field] = []
            self.resign()
            with self.subTest(field=field), self.assertRaises(snapshot.SnapshotError):
                snapshot.verify(self.path)
            self.manifest = original

    def test_resigned_manifest_cannot_introduce_path_traversal(self) -> None:
        self.manifest["files"][0]["path"] = "../../secrets/admin-token"
        self.resign()
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.verify(self.path)

    def test_incremental_bundle_prerequisite_is_rejected(self) -> None:
        bundle = self.path / "git" / (PID + ".bundle")
        bundle.write_text("# v2 git bundle\n-" + OID + " prerequisite\n\nPACK")
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.bundle_refs(bundle)

    def test_hardlink_is_rejected(self) -> None:
        target = self.path / "database.dump"
        link = self.path / "linked-copy"
        try:
            os.link(target, link)
        except OSError:
            self.skipTest("This filesystem cannot create test hardlinks")
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.private_path(target)

    def test_symlink_is_rejected(self) -> None:
        link = self.private / "linked-snapshot"
        try:
            link.symlink_to(self.path, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation is unavailable to this test account")
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.private_path(link, directory=True)

    def test_rehearsal_requires_explicit_flag_before_any_mutation(self) -> None:
        with (
            patch.object(snapshot, "command") as command,
            self.assertRaises(snapshot.SnapshotError),
        ):
            snapshot.rehearse(self.path, explicitly_enabled=False)
        command.assert_not_called()

    def test_outside_private_destination_is_rejected(self) -> None:
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.make_directory(self.root / "outside")
        self.assertFalse((self.root / "outside").exists())


class CredentialBoundaryTests(unittest.TestCase):
    def test_uppercase_windows_systemroot_survives_restricted_environment(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SYSTEMROOT": "C:\\Windows",
                "PATH": "trusted-path",
                "OPENAI_API_KEY": "sentinel",
            },
            clear=True,
        ):
            environment = snapshot.restricted_environment()
        self.assertEqual(environment["SYSTEMROOT"], "C:\\Windows")
        self.assertEqual(environment["PATH"], "trusted-path")
        self.assertNotIn("OPENAI_API_KEY", environment)

    def test_provider_and_database_secrets_are_not_in_subprocess_environment(
        self,
    ) -> None:
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "sentinel",
                "OPENAI_API_KEY": "sentinel",
                "CLAUDE_CODE_OAUTH_TOKEN": "sentinel",
                "PGPASSWORD": "sentinel",
                "PATH": "trusted-path",
            },
            clear=True,
        ):
            environment = snapshot.restricted_environment()
        self.assertEqual(environment["PATH"], "trusted-path")
        self.assertNotIn("sentinel", environment.values())

    def test_token_is_not_in_repr_and_external_url_is_rejected(self) -> None:
        client = snapshot.Client("http://127.0.0.1:8080", "credential-sentinel")
        self.assertNotIn("credential-sentinel", repr(client))
        for url in (
            "https://example.com",
            "http://localhost@evil.example",
            "file:///secret",
            "http://localhost:8080/path",
        ):
            with self.subTest(url=url), self.assertRaises(snapshot.SnapshotError):
                snapshot.Client(url, "credential-sentinel")

    def test_redirect_never_receives_a_second_authorization_request(self) -> None:
        paths: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                paths.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/api/redirect-target")
                self.end_headers()

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = snapshot.Client(
                f"http://127.0.0.1:{server.server_port}", "unit-token"
            )
            with self.assertRaises(snapshot.SnapshotError):
                client.get("/api/runs")
            self.assertEqual(paths, ["/api/runs"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_failing_command_never_echoes_private_stderr(self) -> None:
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            self.assertRaises(snapshot.SnapshotError) as error,
        ):
            snapshot.command(
                sys.executable,
                [
                    "-c",
                    "import sys; sys.stderr.write('credential-sentinel'); sys.exit(1)",
                ],
            )
        self.assertNotIn("credential-sentinel", str(error.exception))
        self.assertEqual(output.getvalue(), "")

    def test_actual_subprocess_output_limit_is_enforced(self) -> None:
        with self.assertRaises(snapshot.SnapshotError):
            snapshot.command(
                sys.executable,
                ["-c", "import sys; sys.stdout.buffer.write(b'x'*200000)"],
                limit=1024,
            )

    def test_remote_docker_context_is_rejected_before_inspect_or_dump(self) -> None:
        with (
            patch.object(
                snapshot, "command", return_value=b'"tcp://remote.example:2376"'
            ) as command,
            self.assertRaises(snapshot.SnapshotError),
        ):
            snapshot.source_container()
        self.assertEqual(command.call_count, 1)

    def test_embedded_wsl_helper_is_valid_python(self) -> None:
        compile(snapshot.WSL_PROGRAM, "fixed-wsl-program", "exec")


if __name__ == "__main__":
    unittest.main()
