#!/usr/bin/env bash
# Diagnostics only. Does not install software, authenticate or execute agents.
set -euo pipefail
if [[ "$(uname -s)" != "Linux" ]]; then echo "Real worker runtime requires Ubuntu WSL2"; exit 1; fi
if [[ "$PWD" == /mnt/* ]]; then echo "Move runtime source/target repositories to WSL ext4"; exit 1; fi
grep -qi microsoft /proc/sys/kernel/osrelease || { echo "WSL2 environment expected"; exit 1; }
command -v git >/dev/null
command -v python3 >/dev/null
command -v docker >/dev/null
git --version
python3 --version
docker compose version
docker info --format '{{.ServerVersion}}'
curl --fail --silent --show-error http://127.0.0.1:8080/healthz
echo
echo "Scaffold only: readyz is expected to return 503. Authentication/DB/Redis/port-isolation tests remain MVP work."
