#!/usr/bin/env bash
# Diagnostics only; no authentication, installations, services or settings changes.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Run doctor in the Ubuntu WSL2 worker account." >&2
  exit 1
fi
python3 "$script_dir/doctor.py" "$@"
