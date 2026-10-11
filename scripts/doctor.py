"""Read-only WSL/runtime diagnostics. Never installs, authenticates or starts agents."""
from __future__ import annotations

import argparse
import grp
import json
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import SplitResult, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


def loopback_url(value: str, scheme: str) -> SplitResult:
    parsed = urlsplit(value)
    if parsed.scheme != scheme or parsed.hostname not in {'localhost', '127.0.0.1', '::1'} or parsed.username and scheme != 'redis' or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Expected a loopback URL without password, query or fragment')
    return parsed


def command(argv: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)  # noqa: S603 - Fixed diagnostic verbs or explicitly selected worker executable; no shell.
        if result.returncode:
            return {'ok': False, 'error': 'COMMAND_FAILED', 'exit_code': result.returncode}
        if len(result.stdout) > 262144:
            return {'ok': False, 'error': 'DIAGNOSTIC_TOO_LARGE'}
        return {'ok': True, 'value': result.stdout.strip()}
    except (OSError, subprocess.TimeoutExpired):
        return {'ok': False, 'error': 'COMMAND_UNAVAILABLE_OR_TIMEOUT'}


def http_probe(url: str) -> dict[str, Any]:
    try:
        loopback_url(url, 'http')
        with build_opener(NoRedirect(), ProxyHandler({})).open(Request(url), timeout=3) as response:  # noqa: S310 - loopback_url rejects all other schemes/hosts; redirects and proxies disabled.
            body = json.loads(response.read(65536))
            return {'ok': response.status == 200, 'status_code': response.status, 'state': body.get('status') if isinstance(body, dict) else None}
    except HTTPError as exc:
        return {'ok': False, 'status_code': exc.code}
    except (URLError, ValueError, OSError):
        return {'ok': False, 'error': 'SERVICE_UNAVAILABLE'}


def redis_probe(url: str, password_file: Path) -> dict[str, Any]:
    try:
        parsed = loopback_url(url, 'redis')
        if password_file.is_symlink():
            raise ValueError('Secret file must not be a symlink')
        password = password_file.read_text(encoding='utf-8').strip()
        if len(password) < 32:
            raise ValueError('Password too short')
        arguments = ['AUTH', parsed.username or 'adf_worker', password]
        request = f'*{len(arguments)}\r\n'.encode()
        for argument in arguments:
            encoded = argument.encode()
            request += f'${len(encoded)}\r\n'.encode() + encoded + b'\r\n'
        with socket.create_connection((parsed.hostname, parsed.port or 6380), timeout=3) as client:
            client.settimeout(3)
            client.sendall(request)
            if client.recv(1024) != b'+OK\r\n':
                return {'ok': False, 'error': 'AUTH_REJECTED'}
            client.sendall(b'*1\r\n$4\r\nPING\r\n')
            return {'ok': client.recv(1024) == b'+PONG\r\n'}
    except (ValueError, OSError):
        return {'ok': False, 'error': 'REDIS_UNAVAILABLE_OR_SECRET_INVALID'}


def container_bindings() -> dict[str, Any]:
    found = command(['docker', 'ps', '--filter', 'label=com.docker.compose.project=adf', '--format', '{{.ID}}'])
    if not found['ok']:
        return found
    ids = found['value'].splitlines()
    ports: list[dict[str, str]] = []
    for container_id in ids:
        inspected = command(['docker', 'inspect', '--format', '{{json .NetworkSettings.Ports}}', container_id])
        if not inspected['ok']:
            return inspected
        try:
            bindings = json.loads(inspected['value']) or {}
            for container_port, addresses in bindings.items():
                for address in addresses or []:
                    ports.append({'container_port': container_port, 'host_ip': address['HostIp'], 'host_port': address['HostPort']})
        except (ValueError, KeyError, TypeError):
            return {'ok': False, 'error': 'INVALID_DOCKER_INSPECT'}
    return {'ok': bool(ids) and all(item['host_ip'] in {'127.0.0.1', '::1'} for item in ports), 'bindings': ports, 'external_host_denial': 'unverified'}


def worker_doctor_argv(args: argparse.Namespace, canonical: Path) -> list[str]:
    argv = [str(args.worker), 'doctor', '--root', str(canonical)]
    for flag, value in (('--node', args.node), ('--codex', args.codex), ('--claude', args.claude),
                        ('--codex-home', args.codex_home), ('--claude-config-dir', args.claude_config_dir)):
        if value is not None:
            argv.extend([flag, str(value)])
    return argv


def diagnose(args: argparse.Namespace) -> dict[str, Any]:
    runtime = args.root.expanduser()
    linux = platform.system() == 'Linux'
    canonical = runtime.resolve()
    filesystem = command(['findmnt', '--noheadings', '--output', 'FSTYPE', '--target', str(canonical)]) if linux else {'ok': False}
    root_ok = runtime.exists() and not runtime.is_symlink() and not str(canonical).startswith('/mnt/') and canonical != Path('/') and filesystem.get('value') == 'ext4'
    wsl = linux and 'microsoft' in platform.release().lower()
    groups = sorted(grp.getgrgid(group).gr_name for group in os.getgroups()) if linux else []
    socket_access = any(os.access(path, os.W_OK) for path in ('/var/run/docker.sock', '/run/docker.sock'))
    privilege = {'process_unprivileged': linux and os.geteuid() != 0, 'groups': groups, 'docker_socket_access': socket_access, 'dedicated_account_verified': False, 'least_privilege_verified': False}
    report: dict[str, Any] = {'schema_version': 1, 'wsl2': wsl, 'ext4_runtime': {'ok': root_ok, 'root': str(canonical), 'filesystem': filesystem.get('value')}, 'privileges': privilege}
    worker = command(worker_doctor_argv(args, canonical), timeout=45)
    if worker['ok']:
        try:
            worker = {'ok': True, 'report': json.loads(worker['value'])}
        except ValueError:
            worker = {'ok': False, 'error': 'INVALID_WORKER_DIAGNOSTIC'}
    report['worker'] = worker
    report['api'] = http_probe(args.api_url.rstrip('/') + '/readyz')
    report['redis'] = redis_probe(args.redis_url, args.redis_password_file) if args.redis_password_file else {'ok': False, 'error': 'SECRET_FILE_REQUIRED'}
    report['docker'] = command(['docker', 'version', '--format', '{{.Server.Version}}'])
    report['compose'] = command(['docker', 'compose', 'version', '--short'])
    report['ports'] = container_bindings()
    provider_ready = worker.get('report', {}).get('execution_capabilities_available') is True
    report['runtime_healthy'] = all([wsl, root_ok, privilege['process_unprivileged'], provider_ready, report['api']['ok'], report['redis']['ok'], report['ports']['ok']])
    report['mvp_ready'] = False
    report['remaining_acceptance'] = ['dedicated least-privilege account', 'external-host negative connection test', 'umbrella acceptance matrix']
    return report


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.home() / 'ai-factory')
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--node', type=Path)
    parser.add_argument('--codex')
    parser.add_argument('--claude')
    parser.add_argument('--codex-home', type=Path)
    parser.add_argument('--claude-config-dir', type=Path)
    parser.add_argument('--api-url', default='http://127.0.0.1:8080')
    parser.add_argument('--redis-url', default='redis://adf_worker@127.0.0.1:6380/0')
    parser.add_argument('--redis-password-file', type=Path)
    return parser


def main() -> None:
    args = argument_parser().parse_args()
    args.worker = args.worker or args.root.expanduser() / 'tools/worker-venv/bin/adf-worker'
    report = diagnose(args)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['runtime_healthy'] else 1)


if __name__ == '__main__':
    main()
