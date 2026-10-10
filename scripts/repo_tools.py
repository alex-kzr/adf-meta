"""Shared local-only repository utilities; no network or global Git configuration."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[1]
UMBRELLA_NAME = "adf-meta"
MODULES = (("frontend", "adf-web"), ("services/api", "adf-api"), ("services/orchestrator", "adf-orchestrator"), ("services/runtime-worker", "adf-runtime-worker"))

def git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], text=True, encoding="utf-8", capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"Git {args[0]} failed in {path}: {result.stderr.strip()}")
    return result.stdout.strip()

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
