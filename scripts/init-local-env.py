"""Prepare private ADF infrastructure configuration without exposing credentials."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import secrets

from repo_tools import ROOT

SECRET_NAMES = (
    "postgres-password", "migrator-password", "api-db-password", "checkpoint-db-password",
    "redis-password", "redis-worker-password", "redis-monitor-password",
    "admin-token", "orchestrator-token", "worker-token",
)


def prepare(root: Path) -> None:
    directory = root / ".bootstrap" / "secrets"
    if (root / ".bootstrap").is_symlink() or directory.is_symlink():
        raise ValueError("Private configuration directory cannot be a symlink")
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        directory.chmod(0o700)
    for name in SECRET_NAMES:
        path = directory / name
        if path.is_symlink():
            raise ValueError(f"Private file {name} cannot be a symlink")
        if not path.exists():
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(secrets.token_hex(32) + "\n")
            if os.name == "posix":
                path.chmod(0o600)
        if len(path.read_text(encoding="utf-8").strip()) < 32:
            raise ValueError(f"Private file {name} must contain at least 32 characters")
    acl = directory / "redis-acl"
    if acl.is_symlink():
        raise ValueError("Redis ACL file cannot be a symlink")
    if not acl.exists():
        # EXEC checks the disabled default user's ACL while replaying stream claims.
        # Authentication stays disabled; only this stream's loader commands are granted.
        rows = ["user default off resetpass ~adf:executions +select +xclaim +xgroup|setid"]
        roles = (
            ("adf_orchestrator", "redis-password", "+ping +hello +client|setname +client|setinfo +xadd +xlen +xgroup|create"),
            ("adf_worker", "redis-worker-password", "+ping +hello +client|setname +client|setinfo +xreadgroup +xack +xpending +xautoclaim +xgroup|create"),
            ("adf_monitor", "redis-monitor-password", "+ping +hello +client|setname +client|setinfo +info +xlen +xrange"),
        )
        for username, password_file, commands in roles:
            password = (directory / password_file).read_text(encoding="utf-8").strip()
            digest = hashlib.sha256(password.encode()).hexdigest()
            rows.append(f"user {username} on #{digest} ~adf:* {commands}")
        with acl.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(rows) + "\n")
        if os.name == "posix":
            acl.chmod(0o600)
    env = root / ".env"
    if env.is_symlink():
        raise ValueError("Environment configuration cannot be a symlink")
    if not env.exists():
        with env.open("xb") as handle:
            handle.write((root / ".env.example").read_bytes())
    existing_keys = {line.split("=", 1)[0] for line in env.read_text(encoding="utf-8").splitlines() if "=" in line and not line.lstrip().startswith("#")}
    defaults = (root / ".env.example").read_text(encoding="utf-8").splitlines()
    missing = [line for line in defaults if "=" in line and not line.lstrip().startswith("#") and line.split("=", 1)[0] not in existing_keys]
    if missing:
        with env.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n" + "\n".join(missing) + "\n")
    print("Private ADF files prepared; existing values retained. No credentials displayed.")


if __name__ == "__main__":
    prepare(ROOT)
