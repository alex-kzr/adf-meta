"""Create local infra-only secrets; does not touch CLI credentials or start services."""
from pathlib import Path
import secrets
from repo_tools import ROOT

directory=ROOT/".bootstrap"/"secrets"
directory.mkdir(parents=True,exist_ok=True)
for name in ("postgres-password","redis-password"):
    path=directory/name
    if not path.exists():
        path.write_text(secrets.token_hex(32)+"\n",encoding="utf-8")
        path.chmod(0o600)
env=ROOT/".env"
if not env.exists():
    env.write_bytes((ROOT/".env.example").read_bytes())
print("Local infra files prepared without displaying credentials; existing files retained. Windows ACL protection requires operator verification.")
