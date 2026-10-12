"""Tests for the public ``prepare`` function of scripts/init-local-env.py."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import secrets
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Protocol, cast

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
MODULE_PATH = SCRIPTS_DIR / "init-local-env.py"

ENV_EXAMPLE = "# comment=ignored\nALPHA=default-alpha\nBETA=default-beta\nGAMMA=default-gamma\n"

PASSWORD_FILES = {
    "adf_orchestrator": "redis-password",
    "adf_worker": "redis-worker-password",
    "adf_monitor": "redis-monitor-password",
}


class ConfigurationBootstrap(Protocol):
    SECRET_NAMES: tuple[str, ...]

    def prepare(self, root: Path) -> None: ...


def load_module() -> ConfigurationBootstrap:
    """Load the hyphenated script as a module without altering global import state."""
    spec = importlib.util.spec_from_file_location("adf_init_local_env_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("cannot create module spec for init-local-env.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(SCRIPTS_DIR))
    return cast(ConfigurationBootstrap, module)


def snapshot(root: Path) -> dict[str, bytes]:
    """Map every file under root (relative POSIX path) to its raw bytes."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class LocalConfigurationTests(unittest.TestCase):
    module: ConfigurationBootstrap

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / ".env.example").write_bytes(ENV_EXAMPLE.encode("utf-8"))
        self.secrets_dir = self.root / ".bootstrap" / "secrets"

    def run_prepare(self) -> str:
        """Run prepare and return captured stdout."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.module.prepare(self.root)
        return buffer.getvalue()

    def secret_names(self) -> tuple[str, ...]:
        names: tuple[str, ...] = tuple(self.module.SECRET_NAMES)
        return names

    def secret_values(self) -> list[str]:
        return [
            (self.secrets_dir / name).read_text(encoding="utf-8").strip()
            for name in self.secret_names()
        ]

    def test_prepare_on_empty_root_creates_all_secrets_and_acl(self) -> None:
        self.run_prepare()

        for name in self.secret_names():
            self.assertGreaterEqual(
                len((self.secrets_dir / name).read_text(encoding="utf-8").strip()), 32, name
            )
        self.assertTrue((self.secrets_dir / "redis-acl").is_file())
        self.assertTrue((self.root / ".env").is_file())

    def test_generated_secrets_are_unique(self) -> None:
        self.run_prepare()

        values = self.secret_values()
        self.assertEqual(len(values), len(set(values)))

    def test_generated_files_use_lf_only_line_endings(self) -> None:
        self.run_prepare()

        for name in (*self.secret_names(), "redis-acl"):
            data = (self.secrets_dir / name).read_bytes()
            self.assertNotIn(b"\r", data, f"{name} contains CR")
            self.assertTrue(data.endswith(b"\n"), f"{name} lacks trailing LF")
            self.assertFalse(data.endswith(b"\n\n"), f"{name} has extra blank line")

    def test_appended_env_lines_use_lf_only(self) -> None:
        (self.root / ".env").write_bytes(b"ALPHA=custom\n")

        self.run_prepare()

        self.assertNotIn(b"\r", (self.root / ".env").read_bytes())

    def test_preexisting_secret_value_is_preserved_byte_for_byte(self) -> None:
        self.secrets_dir.mkdir(parents=True)
        existing = (secrets.token_hex(24) + "\n").encode("utf-8")
        target = self.secrets_dir / "postgres-password"
        target.write_bytes(existing)

        self.run_prepare()

        self.assertEqual(target.read_bytes(), existing)

    def test_preexisting_env_override_is_preserved(self) -> None:
        override = "override-" + secrets.token_hex(8)
        (self.root / ".env").write_bytes(f"ALPHA={override}\n".encode("utf-8"))

        self.run_prepare()

        lines = (self.root / ".env").read_text(encoding="utf-8").splitlines()
        self.assertIn(f"ALPHA={override}", lines)
        self.assertNotIn("ALPHA=default-alpha", lines)
        self.assertEqual(sum(1 for line in lines if line.startswith("ALPHA=")), 1)

    def test_absent_env_variables_are_added_with_defaults(self) -> None:
        (self.root / ".env").write_bytes(b"ALPHA=custom\n")

        self.run_prepare()

        lines = (self.root / ".env").read_text(encoding="utf-8").splitlines()
        self.assertIn("BETA=default-beta", lines)
        self.assertIn("GAMMA=default-gamma", lines)
        self.assertFalse(any(line.startswith("#") for line in lines))
        self.assertEqual(sum(1 for line in lines if line.startswith("BETA=")), 1)

    def test_missing_env_is_created_from_example(self) -> None:
        self.run_prepare()

        self.assertEqual(
            (self.root / ".env").read_bytes(), (self.root / ".env.example").read_bytes()
        )

    def test_redis_acl_disables_default_user_and_defines_three_scoped_users(self) -> None:
        self.run_prepare()

        rows = (self.secrets_dir / "redis-acl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            rows[0],
            "user default off resetpass ~adf:executions +select +xclaim +xgroup|setid",
        )
        users = {row.split()[1]: row.split() for row in rows[1:]}
        self.assertEqual(set(users), set(PASSWORD_FILES))

        for username, tokens in users.items():
            self.assertIn("on", tokens, username)
            self.assertIn("~adf:*", tokens, username)
            key_patterns = [t for t in tokens if t.startswith(("~", "%", "&"))]
            self.assertEqual(key_patterns, ["~adf:*"], username)
            for forbidden in ("allkeys", "allcommands", "+@all", "nopass", "~*"):
                self.assertNotIn(forbidden, tokens, username)

    def test_redis_acl_stores_matching_hash_and_no_plaintext_password(self) -> None:
        self.run_prepare()

        acl_text = (self.secrets_dir / "redis-acl").read_text(encoding="utf-8")
        rows = {row.split()[1]: row.split() for row in acl_text.splitlines()[1:]}
        for username, password_file in PASSWORD_FILES.items():
            password = (self.secrets_dir / password_file).read_text(encoding="utf-8").strip()
            digest = hashlib.sha256(password.encode()).hexdigest()
            self.assertIn(f"#{digest}", rows[username], username)
            self.assertFalse(any(t.startswith(">") for t in rows[username]), username)
            self.assertNotIn(password, acl_text, f"plaintext password leaked for {username}")

    def test_redis_acl_commands_are_limited_to_each_role(self) -> None:
        self.run_prepare()

        rows = {
            row.split()[1]: set(row.split())
            for row in (self.secrets_dir / "redis-acl").read_text(encoding="utf-8").splitlines()[1:]
        }
        self.assertIn("+xadd", rows["adf_orchestrator"])
        self.assertNotIn("+xreadgroup", rows["adf_orchestrator"])
        self.assertIn("+xreadgroup", rows["adf_worker"])
        self.assertNotIn("+xadd", rows["adf_worker"])
        self.assertIn("+info", rows["adf_monitor"])
        for write_command in ("+xadd", "+xack", "+xreadgroup"):
            self.assertNotIn(write_command, rows["adf_monitor"])

    def test_short_credential_is_rejected_without_leaking_value(self) -> None:
        self.secrets_dir.mkdir(parents=True)
        short = secrets.token_hex(4)
        (self.secrets_dir / "admin-token").write_text(short + "\n", encoding="utf-8", newline="\n")

        with self.assertRaises(ValueError) as caught:
            self.run_prepare()

        self.assertNotIn(short, str(caught.exception))
        self.assertIn("admin-token", str(caught.exception))

    def test_short_credential_is_not_overwritten(self) -> None:
        self.secrets_dir.mkdir(parents=True)
        short = (secrets.token_hex(4) + "\n").encode("utf-8")
        target = self.secrets_dir / "worker-token"
        target.write_bytes(short)

        with self.assertRaises(ValueError):
            self.run_prepare()

        self.assertEqual(target.read_bytes(), short)

    def test_prepare_is_idempotent(self) -> None:
        self.run_prepare()
        first = snapshot(self.root)

        self.run_prepare()
        second = snapshot(self.root)

        self.assertEqual(first, second)

    def test_idempotent_with_partially_populated_env(self) -> None:
        (self.root / ".env").write_bytes(b"ALPHA=custom\n")
        self.run_prepare()
        first = snapshot(self.root)

        self.run_prepare()

        self.assertEqual(first, snapshot(self.root))

    def test_stdout_contains_no_credentials(self) -> None:
        pre_existing = secrets.token_hex(24)
        self.secrets_dir.mkdir(parents=True)
        (self.secrets_dir / "postgres-password").write_text(
            pre_existing + "\n", encoding="utf-8", newline="\n"
        )

        first = self.run_prepare()
        second = self.run_prepare()

        for output in (first, second):
            self.assertTrue(output.strip(), "expected a status message")
            for value in self.secret_values():
                self.assertNotIn(value, output)
            self.assertNotIn(pre_existing, output)

    def test_secret_symlink_is_rejected_before_access(self) -> None:
        self.secrets_dir.mkdir(parents=True)
        outside = self.root / "outside-secret"
        outside.write_text(secrets.token_hex(32), encoding="utf-8")
        try:
            (self.secrets_dir / "postgres-password").symlink_to(outside)
        except OSError:
            self.skipTest("Symlink creation unavailable for this platform/account")
        before = outside.read_bytes()
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_prepare()
        self.assertEqual(outside.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
