"""Private container-local HTTP/Redis tunnel for isolated recovery QA only."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sys
from pathlib import Path
from typing import Any, BinaryIO
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX = 30 * 1024**2
ROOT = Path("/run/qa")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_: Any, **__: Any) -> None:
        return None


def redis_reply(stream: BinaryIO, depth: int = 0) -> Any:
    if depth > 12:
        raise ValueError("Redis depth budget")
    line = stream.readline(1024)
    if not line.endswith(b"\r\n"):
        raise ValueError("Redis line budget")
    marker, value = line[:1], line[1:-2]
    if marker == b"+":
        return value.decode()
    if marker == b"-":
        raise ValueError("Redis rejected operation")
    size = int(value)
    if marker == b":":
        return size
    if size == -1:
        return None
    if size < 0 or size > MAX:
        raise ValueError("Redis size budget")
    if marker == b"$":
        value = stream.read(size + 2)
        if len(value) != size + 2 or not value.endswith(b"\r\n"):
            raise ValueError("Redis bulk response")
        return value[:-2].decode()
    if marker == b"*" and size <= 10000:
        return [redis_reply(stream, depth + 1) for _ in range(size)]
    raise ValueError("Redis shape")


def redis_command(arguments: list[str]) -> Any:
    fixed = {
        ("PING",),
        ("XLEN", "adf:executions"),
        ("XGROUP", "CREATE", "adf:executions", "adf-workers", "0", "MKSTREAM"),
        (
            "XREADGROUP",
            "GROUP",
            "adf-workers",
            "recovery",
            "COUNT",
            "1",
            "BLOCK",
            "100",
            "STREAMS",
            "adf:executions",
            ">",
        ),
    }
    fixed.add(
        (
            "XREADGROUP",
            "GROUP",
            "adf-workers",
            "recovery",
            "COUNT",
            "100",
            "BLOCK",
            "100",
            "STREAMS",
            "adf:executions",
            ">",
        )
    )
    if tuple(arguments) not in fixed and not (
        4 <= len(arguments) <= 103
        and arguments[:3] == ["XACK", "adf:executions", "adf-workers"]
        and all(re.fullmatch(r"[0-9]+-[0-9]+", item) for item in arguments[3:])
    ):
        raise ValueError("Redis command outside QA allowlist")
    host = os.environ["ADF_QA_REDIS_HOST"]
    if not re.fullmatch(r"adf-recovery-[a-f0-9]{8}-[ab]-redis", host):
        raise ValueError("QA Redis hostname required")
    password = (ROOT / "redis-password").read_text().strip()
    with socket.create_connection((host, 6379), timeout=3) as connection:
        stream = connection.makefile("rb")
        for command in (["AUTH", "adf_orchestrator", password], arguments):
            fields = [part.encode() for part in command]
            encoded = b"*" + str(len(fields)).encode() + b"\r\n"
            encoded += b"".join(
                b"$" + str(len(part)).encode() + b"\r\n" + part + b"\r\n"
                for part in fields
            )
            connection.sendall(encoded)
            result = redis_reply(stream)
        return result


def http(value: dict[str, Any]) -> dict[str, Any]:
    method, path = value["method"], value["path"]
    if (
        ".." in path
        or method not in {"GET", "POST", "PATCH"}
        or not re.fullmatch(
            r"/(?:api|internal)/[A-Za-z0-9_/?=&.-]+|/(?:healthz|readyz)", path
        )
    ):
        raise ValueError("QA HTTP route required")
    worker = path.startswith("/internal/workers") or (
        path.startswith("/internal/executions/")
        and path.split("?", 1)[0].rsplit("/", 1)[-1]
        in {
            "claim",
            "heartbeat",
            "control",
            "events",
            "artifacts",
            "result",
            "reconcile",
        }
    )
    role = (
        "worker"
        if worker
        else "orchestrator"
        if path.startswith("/internal/")
        else "admin"
    )
    headers = {"Content-Type": "application/json"}
    key = value.get("idempotency_key")
    if key is not None:
        if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9-]{36}", key):
            raise ValueError("Generated QA idempotency identity required")
        headers["Idempotency-Key"] = key
    if path not in {"/healthz", "/readyz"}:
        headers["Authorization"] = (
            "Bearer " + (ROOT / (role + "-token")).read_text().strip()
        )
    body = value.get("body")
    request = Request(
        "http://127.0.0.1:8080" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(MAX + 1)
        if len(raw) > MAX:
            raise ValueError("QA HTTP response budget")
        if path.endswith("/content"):
            data: Any = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        else:
            data = json.loads(raw)
        return {"status": response.status, "data": data}


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX + 1)
        if len(raw) > MAX:
            raise ValueError("QA request budget")
        value = json.loads(raw)
        if value.get("kind") in {"frontend", "orchestrator"}:
            opener = build_opener(ProxyHandler({}), NoRedirect())
            origin = (
                "http://frontend/"
                if value["kind"] == "frontend"
                else "http://orchestrator:8081/readyz"
            )
            with opener.open(origin, timeout=10) as response:
                raw = response.read(MAX + 1)
                if len(raw) > MAX:
                    raise ValueError("QA frontend response budget")
                print(json.dumps({"status": response.status, "bytes": len(raw)}))
                return 0
        result = (
            {"data": redis_command(value["arguments"])}
            if value.get("kind") == "redis"
            else http(value)
        )
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except Exception:
        print('{"qa_tunnel_failed":true}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
