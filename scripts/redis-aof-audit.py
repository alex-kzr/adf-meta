"""Read-only RESP AOF framing audit; payloads and credentials are discarded."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import subprocess
import sys
from typing import IO, Any

LIMIT = 64 * 1024 * 1024
COMMANDS = {
    b"SELECT",
    b"MULTI",
    b"EXEC",
    b"DISCARD",
    b"XADD",
    b"XGROUP",
    b"XCLAIM",
    b"XACK",
    b"XDEL",
    b"XTRIM",
    b"DEL",
    b"SET",
}
ID = re.compile(rb"[0-9]{1,20}-[0-9]{1,20}")
KEY = b"adf:executions"
GROUP = b"adf-workers"


class AuditError(Exception):
    """A closed message never includes untrusted source bytes."""


class Reader:
    def __init__(self, source: IO[bytes]) -> None:
        self.source, self.total = source, 0

    def exact(self, length: int) -> bytes:
        if length < 0 or self.total + length > LIMIT:
            raise AuditError("AOF_QUOTA_EXCEEDED")
        pieces = []
        remaining = length
        while remaining:
            data = self.source.read(min(8192, remaining))
            if not data:
                raise AuditError("AOF_TRUNCATED")
            pieces.append(data)
            self.total += len(data)
            remaining -= len(data)
        return b"".join(pieces)

    def discard(self, length: int) -> None:
        if length < 0 or self.total + length > LIMIT:
            raise AuditError("AOF_QUOTA_EXCEEDED")
        while length:
            size = min(length, 8192)
            self.exact(size)
            length -= size

    def line(self, *, eof: bool = False) -> bytes:
        data = self.source.readline(64)
        self.total += len(data)
        if not data and eof:
            return data
        if data == b"\r\n":
            raise AuditError("AOF_INVALID_FRAME")
        if self.total > LIMIT or not data.endswith(b"\r\n") or len(data) > 63:
            raise AuditError("AOF_INVALID_FRAME")
        return data[:-2]

    def bulk(self, keep: bool) -> bytes:
        header = self.line()
        if not header.startswith(b"$") or not header[1:].isdigit():
            raise AuditError("AOF_INVALID_BULK")
        size = int(header[1:])
        if keep and size <= 128:
            value = self.exact(size)
        else:
            self.discard(size)
            value = b""
        if self.exact(2) != b"\r\n":
            raise AuditError("AOF_INVALID_BULK")
        return value


def audit(source: IO[bytes], deliveries: list[str]) -> dict[str, Any]:
    try:
        valid_targets = len(deliveries) <= 64 and all(
            ID.fullmatch(item.encode("ascii")) for item in deliveries
        )
    except (AttributeError, UnicodeError):
        valid_targets = False
    if not valid_targets:
        raise AuditError("AOF_INVALID_TARGET")
    expected = set(deliveries)
    observations = {
        key: {
            "xadd": 0,
            "claim_in_multi": 0,
            "claim_outside_multi": 0,
            "ack": 0,
            "delete": 0,
        }
        for key in deliveries
    }
    reader = Reader(source)
    counts: Counter[str] = Counter()
    transactional: Counter[str] = Counter()
    in_multi = False
    transaction_count = 0
    group_creates = 0
    group_setids_in_multi = 0
    unknown_commands = 0
    while header := reader.line(eof=True):
        if not header.startswith(b"*") or not header[1:].isdigit():
            raise AuditError("AOF_INVALID_ARRAY")
        argc = int(header[1:])
        if not 1 <= argc <= 4096:
            raise AuditError("AOF_INVALID_ARGC")
        first = reader.bulk(True).upper()
        known = first in COMMANDS
        command = first.decode("ascii") if known else "OTHER"
        counts[command] += 1
        if in_multi:
            transactional[command] += 1
        if not known:
            unknown_commands += 1
        fields: dict[int, bytes] = {}
        xadd_id = b""
        if first == b"XADD":
            fields, xadd_id = xadd_header(reader, argc)
        for position in range(1, argc) if first != b"XADD" else ():
            keep = known and (
                (first == b"XGROUP" and position <= 3)
                or (first == b"XCLAIM" and position != 3)
                or first in {b"XACK", b"XDEL"}
            )
            fields[position] = reader.bulk(keep)
        if first == b"MULTI":
            if argc != 1 or in_multi:
                raise AuditError("AOF_NESTED_MULTI")
            in_multi = True
            transaction_count += 1
        elif first in {b"EXEC", b"DISCARD"}:
            if argc != 1 or not in_multi:
                raise AuditError("AOF_UNMATCHED_EXEC")
            in_multi = False
        elif first == b"XGROUP" and fields.get(2) == KEY and fields.get(3) == GROUP:
            if fields.get(1, b"").upper() == b"CREATE":
                group_creates += 1
            elif fields.get(1, b"").upper() == b"SETID" and in_multi:
                group_setids_in_multi += 1
        elif fields.get(1) == KEY:
            if first == b"XADD":
                identity = xadd_id
                if ID.fullmatch(identity) and identity.decode() in expected:
                    observations[identity.decode()]["xadd"] += 1
            elif first in {b"XCLAIM", b"XACK", b"XDEL"}:
                if first != b"XDEL" and fields.get(2) != GROUP:
                    continue
                minimum = 5 if first == b"XCLAIM" else (2 if first == b"XDEL" else 3)
                for position, identity in fields.items():
                    if (
                        first == b"XCLAIM"
                        and position >= minimum
                        and not ID.fullmatch(identity)
                    ):
                        break  # TIME/RETRYCOUNT/LASTID values are not claimed IDs.
                    if (
                        position >= minimum
                        and ID.fullmatch(identity)
                        and identity.decode() in expected
                    ):
                        name = (
                            "claim_in_multi"
                            if first == b"XCLAIM" and in_multi
                            else "claim_outside_multi"
                            if first == b"XCLAIM"
                            else "ack"
                            if first == b"XACK"
                            else "delete"
                        )
                        observations[identity.decode()][name] += 1
    if in_multi:
        raise AuditError("AOF_OPEN_TRANSACTION")
    return {
        "bytes_scanned": reader.total,
        "command_counts": dict(counts),
        "commands_inside_multi": dict(transactional),
        "transactions": transaction_count,
        "target_group_creates": group_creates,
        "target_group_setids_inside_multi": group_setids_in_multi,
        "target_deliveries": observations,
        "unknown_commands_discarded": unknown_commands,
        "payloads_credentials_or_consumer_values_emitted": False,
    }


def xadd_header(reader: Reader, argc: int) -> tuple[dict[int, bytes], bytes]:
    """Consume supported XADD grammar before discarding every field/value byte."""
    remaining = argc - 1

    def take() -> bytes:
        nonlocal remaining
        if remaining <= 0:
            raise AuditError("AOF_INVALID_XADD_HEADER")
        remaining -= 1
        return reader.bulk(True)

    key = take()
    token = take()
    if token.upper() == b"NOMKSTREAM":
        token = take()
    if token.upper() in {b"MAXLEN", b"MINID"}:
        trimming = token.upper()
        token = take()
        approximate = token == b"~"
        if token in {b"~", b"="}:
            token = take()
        if not (token.isdigit() if trimming == b"MAXLEN" else ID.fullmatch(token)):
            raise AuditError("AOF_INVALID_XADD_HEADER")
        token = take()
        if token.upper() == b"LIMIT":
            if not approximate or not take().isdigit():
                raise AuditError("AOF_INVALID_XADD_HEADER")
            token = take()
    if not ID.fullmatch(token) or remaining < 2 or remaining % 2:
        # AOF replay uses explicit IDs. Unsupported forms fail closed.
        raise AuditError("AOF_INVALID_XADD_HEADER")
    for _ in range(remaining):
        reader.bulk(False)
    return {1: key}, token


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", action="append", default=[])
    parser.add_argument("--production-container", action="store_true")
    args = parser.parse_args()
    try:
        if args.production_container:
            # Fixed read-only source; never accepts a shell or arbitrary container/path.
            with subprocess.Popen(
                [
                    "docker",
                    "exec",
                    "adf-redis-1",
                    "/bin/cat",
                    "/data/appendonlydir/appendonly.aof.1.incr.aof",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            ) as child:
                try:
                    if child.stdout is None:
                        raise AuditError("AOF_SOURCE_UNAVAILABLE")
                    result = audit(child.stdout, args.delivery)
                    if child.wait(timeout=5):
                        raise AuditError("AOF_SOURCE_UNAVAILABLE")
                finally:
                    if child.poll() is None:
                        child.terminate()
                        child.wait(timeout=5)
        else:
            result = audit(sys.stdin.buffer, args.delivery)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (AuditError, OSError, subprocess.TimeoutExpired, UnicodeError):
        print(json.dumps({"error": "AOF_AUDIT_STOPPED", "raw_data_emitted": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
