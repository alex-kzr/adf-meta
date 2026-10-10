#!/usr/bin/env bash
# Prepare the host-worker environment; never installs/authenticates provider CLIs.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$(cd -- "$script_dir/.." && pwd)"
root="$HOME/ai-factory"
token_file=""
redis_file=""
doctor_args=()
while (($#)); do
  case "$1" in
    --root) root="$2"; shift 2 ;;
    --token-file) token_file="$2"; shift 2 ;;
    --redis-password-file) redis_file="$2"; shift 2 ;;
    --codex|--claude|--api-url|--redis-url) doctor_args+=("$1" "$2"); shift 2 ;;
    *) echo "Unknown bootstrap option: $1" >&2; exit 2 ;;
  esac
done
[[ "$(uname -s)" == "Linux" && "$(id -u)" != "0" ]] || { echo "A regular WSL Linux account is required." >&2; exit 1; }
command -v uv >/dev/null || { echo "Install the pinned uv prerequisite using official instructions." >&2; exit 1; }
[[ -n "$token_file" && -n "$redis_file" ]] || { echo "Supply generated worker token and worker Redis password files." >&2; exit 2; }
python3 - "$root" "$token_file" "$redis_file" <<'PY'
import os
import sys
from pathlib import Path
root = Path(sys.argv[1]).expanduser()
if not root.is_absolute() or root.is_symlink() or str(root.resolve()).startswith('/mnt/') or root.resolve() in {Path('/'), Path.home()}:
    raise SystemExit('Runtime must be a dedicated absolute ext4 path without symlink indirection.')
for parent in [root, *root.parents]:
    if parent.is_symlink():
        raise SystemExit('Runtime parent symlink is forbidden.')
root.mkdir(parents=True, exist_ok=True, mode=0o700)
for name in ('projects', 'config', 'tools', 'journals', 'locks', 'worktrees'):
    path = root / name
    if path.is_symlink():
        raise SystemExit('Runtime directory symlink is forbidden.')
    path.mkdir(exist_ok=True, mode=0o700)
for source, name in zip(sys.argv[2:], ('worker-token', 'redis-worker-password'), strict=True):
    source_path = Path(source)
    if source_path.is_symlink():
        raise SystemExit('Source secret symlink is forbidden.')
    value = source_path.read_bytes().strip()
    if len(value) < 32:
        raise SystemExit('Generated secret is missing or invalid.')
    destination = root / 'config' / name
    if destination.is_symlink():
        raise SystemExit('Destination secret symlink is forbidden.')
    if destination.exists():
        if destination.read_bytes().strip() != value:
            raise SystemExit('Existing runtime secret differs; rotate explicitly before recreating services.')
    else:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as output:
            output.write(value + b'\n')
PY
venv="$root/tools/worker-venv"
if [[ ! -x "$venv/bin/python" ]]; then
  uv venv --python 3.12.9 "$venv"
fi
uv pip sync --python "$venv/bin/python" "$source_dir/services/runtime-worker/requirements.lock"
uv pip install --python "$venv/bin/python" --no-deps "$source_dir/services/runtime-worker"
printf '%s\n' "Worker installed from this source snapshot. CLI login remains an interactive operator step."
bash "$script_dir/doctor.sh" --root "$root" --worker "$venv/bin/adf-worker" --redis-password-file "$root/config/redis-worker-password" "${doctor_args[@]}"
