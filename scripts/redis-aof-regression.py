"""Reproduce Redis 7.4.5 AOF/ACL behavior with synthetic data in private namespaces."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any, BinaryIO, Callable

PUBLIC_HASHES = {
    "redis-server": "11ec731d40ed8266ec197f9b95d0e3ba6d76eb9b033d3145b4eaf8c0b76a3d90",
    "ld-musl-x86_64.so.1": "a3f9d4664f494ffd08fec303e9ad8e20561befe4f307343a00638f8e741d51b1",
    "libssl.so.3": "f93a7835597afc8f16b38a07e84f19e30c03595b87b0e75bbab2023a0e52dc5c",
    "libcrypto.so.3": "627932c3b6136fa930162c659c3fdb205aa40aad8b334de37c5e06604b15eaf7",
}
BWRAP_SHA = "77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c"
IDS = ["1700000000010-0", "1700000000020-0", "1700000000030-0"]


def require(condition: object) -> None:
    # Safety and result checks must remain active under python -O.
    if not condition:
        raise RuntimeError("SYNTHETIC_REDIS_REGRESSION_FAILED")


class RedisRejected(RuntimeError):
    def __init__(self, code: bytes) -> None:
        self.code = code if code in {b"WRONGPASS", b"NOAUTH", b"NOPERM"} else b"OTHER"
        super().__init__("FAKE_REDIS_REQUEST_REJECTED")


def resp(args: list[Any] | tuple[Any, ...]) -> bytes:
    values = [str(arg).encode() for arg in args]
    return (
        b"*"
        + str(len(values)).encode()
        + b"\r\n"
        + b"".join(b"$" + str(len(v)).encode() + b"\r\n" + v + b"\r\n" for v in values)
    )


def number(value: bytes) -> int:
    if not value or not (
        value.isdigit() or (value.startswith(b"-") and value[1:].isdigit())
    ):
        raise RuntimeError("FAKE_PROTOCOL_FAILED")
    return int(value)


def text(value: bytes) -> str:
    try:
        return value.decode()
    except UnicodeError:
        raise RuntimeError("FAKE_PROTOCOL_FAILED") from None


def read_value(source: BinaryIO, depth: int = 0) -> Any:
    require(depth <= 16)
    line = source.readline(4096)
    if not line.endswith(b"\r\n") or len(line) > 4095:
        raise RuntimeError("FAKE_PROTOCOL_FAILED")
    kind, value = line[:1], line[1:-2]
    if kind == b":":
        return number(value)
    if kind == b"+":
        return text(value)
    if kind == b"-":
        raise RedisRejected(value.split(b" ", 1)[0])
    if kind == b"$":
        size = number(value)
        if size == -1:
            return None
        if size < 0:
            raise RuntimeError("FAKE_PROTOCOL_FAILED")
        if size > 65536:
            raise RuntimeError("FAKE_PROTOCOL_FAILED")
        data = source.read(size)
        require(len(data) == size and source.read(2) == b"\r\n")
        return text(data)
    if kind == b"*":
        size = number(value)
        if size == -1:
            return None
        require(0 <= size <= 4096)
        return [read_value(source, depth + 1) for _ in range(size)]
    raise RuntimeError("FAKE_PROTOCOL_FAILED")


def require_disabled_default(call: Callable[..., Any]) -> None:
    try:
        call("AUTH", "default", "")
    except RedisRejected as error:
        require(error.code == b"WRONGPASS")
        return
    raise RuntimeError("SYNTHETIC_REDIS_REGRESSION_FAILED")


def synthetic_commands() -> list[list[Any]]:
    commands = [["SELECT", 0]] + [
        ["XADD", "adf:executions", identity, "body", "synthetic-only"]
        for identity in IDS
    ]
    commands += [
        ["XGROUP", "CREATE", "adf:executions", "adf-workers", 0],
        ["MULTI"],
        ["SELECT", 0],
        [
            "XCLAIM",
            "adf:executions",
            "adf-workers",
            "fake-consumer",
            0,
            *IDS,
            "TIME",
            1700000000040,
            "RETRYCOUNT",
            1,
            "FORCE",
            "JUSTID",
            "LASTID",
            IDS[-1],
        ],
        ["XGROUP", "SETID", "adf:executions", "adf-workers", IDS[-1], "ENTRIESREAD", 3],
        ["EXEC"],
    ]
    return commands


def inside() -> None:
    require(not Path("/home/adf-worker/ai-factory/config").exists())
    require(not Path("/home/adf-worker/ai-factory/provider-profiles").exists())
    require(not Path("/run").exists())
    interfaces = {
        line.split(":", 1)[0].strip()
        for line in Path("/proc/net/dev").read_text().splitlines()
        if ":" in line
    }
    require(interfaces == {"lo"})
    loader = "/redis-libs/ld-musl-x86_64.so.1"
    executable = "/redis-libs/redis-server"
    version = subprocess.check_output(
        [loader, "--library-path", "/redis-libs", executable, "--version"], text=True
    )
    require("v=7.4.5" in version)
    commands = synthetic_commands()
    rows = []
    for name, default in [
        ("current-default-off", "user default off"),
        (
            "candidate-narrow-disabled-default",
            "user default off resetpass ~adf:executions +select +xclaim +xgroup|setid",
        ),
    ]:
        root = Path(tempfile.mkdtemp(prefix="redis-fake-", dir="/tmp"))
        (root / "appendonly.aof").write_bytes(b"".join(resp(c) for c in commands))
        # Public fake observer, no password. It exists only in this private namespace.
        (root / "users.acl").write_text(
            default + "\nuser observer on nopass ~adf:* +xpending +xlen +xinfo +info\n"
        )
        socket_path = root / "server.sock"
        argv = [
            loader,
            "--library-path",
            "/redis-libs",
            executable,
            "--port",
            "0",
            "--unixsocket",
            str(socket_path),
            "--dir",
            str(root),
            "--appendonly",
            "yes",
            "--aof-use-rdb-preamble",
            "no",
            "--aclfile",
            str(root / "users.acl"),
            "--save",
            "",
            "--logfile",
            str(root / "server.log"),
        ]
        child = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            until = time.monotonic() + 8
            while not socket_path.exists():
                if child.poll() is not None or time.monotonic() > until:
                    raise RuntimeError("FAKE_REDIS_START_FAILED")
                time.sleep(0.02)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(3)
                connection.connect(str(socket_path))
                with connection.makefile("rb") as wire:

                    def call(*args: Any) -> Any:
                        connection.sendall(resp(args))
                        return read_value(wire)

                    require_disabled_default(call)
                    require(call("AUTH", "observer", "") == "OK")
                    length = call("XLEN", "adf:executions")
                    pending = call("XPENDING", "adf:executions", "adf-workers")
                    groups = call("XINFO", "GROUPS", "adf:executions")
                    values = dict(zip(groups[0][::2], groups[0][1::2]))
                    rows.append(
                        {
                            "case": name,
                            "stream_length": length,
                            "pending": pending[0],
                            "last_delivered_id": values["last-delivered-id"],
                            "entries_read": values["entries-read"],
                            "consumers": values["consumers"],
                            "default_empty_auth_rejected": True,
                        }
                    )
        finally:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        log = (root / "server.log").read_bytes()
        rows[-1]["aof_exec_noperm_errors"] = sum(
            b"AOF-loading-client" in line and b"NOPERM" in line
            for line in log.splitlines()
        )
    require(rows[0]["stream_length"] == rows[1]["stream_length"] == 3)
    require(rows[0]["pending"] == 0 and rows[0]["aof_exec_noperm_errors"] == 3)
    require(rows[1]["pending"] == 3 and rows[1]["aof_exec_noperm_errors"] == 0)
    require(rows[1]["last_delivered_id"] == IDS[-1] and rows[1]["consumers"] == 1)
    require(all(row["default_empty_auth_rejected"] is True for row in rows))
    print(
        json.dumps(
            {
                "passed": True,
                "redis_version": "7.4.5",
                "cases": rows,
                "synthetic_data_only": True,
                "real_secrets_or_aof_copied": False,
                "production_services_modified": False,
                "host_network_or_ipc_used": False,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside", action="store_true")
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--bwrap", type=Path)
    args = parser.parse_args()
    if args.inside:
        return inside()
    require(
        sys.platform == "linux" and os.geteuid() != 0 and args.public_dir and args.bwrap
    )
    require(hashlib.sha256(args.bwrap.read_bytes()).hexdigest() == BWRAP_SHA)
    argv = [
        str(args.bwrap),
        "--unshare-all",
        "--unshare-user",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--cap-drop",
        "ALL",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",  # noqa: S108 -- private namespace tmpfs
    ]
    for directory in ["/usr/bin", "/usr/lib", "/usr/lib64", str(Path(sys.base_prefix))]:
        argv += ["--ro-bind", directory, directory]
    for target, source in [
        ("/bin", "usr/bin"),
        ("/lib", "usr/lib"),
        ("/lib64", "usr/lib64"),
    ]:
        argv += ["--symlink", source, target]
    argv += ["--dir", "/redis-libs"]
    for name, expected in PUBLIC_HASHES.items():
        path = args.public_dir / name
        require(
            not path.is_symlink()
            and path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        )
        argv += ["--ro-bind", str(path), "/redis-libs/" + name]
    argv += [
        "--symlink",
        "ld-musl-x86_64.so.1",
        "/redis-libs/libc.musl-x86_64.so.1",
        "--ro-bind",
        str(Path(__file__).resolve()),
        "/probe.py",
        "--setenv",
        "HOME",
        "/tmp/fake-home",  # noqa: S108 -- private namespace tmpfs
        "--setenv",
        "LANG",
        "C.UTF-8",
        "--",
        str(Path(sys.base_prefix) / "bin/python3"),
        "-I",
        "-B",
        "/probe.py",
        "--inside",
    ]
    result = subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LANG": "C.UTF-8"},
        timeout=45,
    )
    if result.returncode:
        raise RuntimeError("SYNTHETIC_REDIS_REGRESSION_FAILED")
    value = json.loads(result.stdout)
    require(value.get("passed") is True)
    print(json.dumps(value))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(
            json.dumps(
                {
                    "passed": False,
                    "error": "SYNTHETIC_REDIS_REGRESSION_FAILED",
                    "raw_output_emitted": False,
                }
            )
        )
        raise SystemExit(1) from None
