#!/usr/bin/env bash
# Read-only preparation check; no sudo, package installation or credential changes.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$script_dir/doctor.sh"
echo "Follow docs/local-development.md for separate CLI login and future worker setup."
