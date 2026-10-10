"""Restore a trusted ADF export to a new checkout; never use guessed/network remotes."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from repo_tools import MODULES, git, digest

def clone(*args: str) -> None:
    subprocess.run(["git", "-c", "protocol.file.allow=always", "clone", *args], check=True)

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export",type=Path)
    parser.add_argument("destination",type=Path)
    args=parser.parse_args()
    export=args.export.resolve()
    destination=args.destination.resolve()
    if destination.exists() or destination.is_relative_to(export):
        raise SystemExit("Destination must be a new non-existing directory outside export.")
    manifest=json.loads((export/"manifest.json").read_text(encoding="utf-8"))
    expected={".":"adf",**dict(MODULES)}
    rows=manifest.get("repositories",[])
    if manifest.get("schema_version")!=1 or len(rows)!=len(expected) or {r.get("path") for r in rows}!=set(expected):
        raise SystemExit("Invalid repository manifest.")
    by_path={row["path"]:row for row in rows}
    for row in rows:
        if row["name"]!=expected[row["path"]] or row["bundle"]!=row["name"]+".bundle" or not re.fullmatch(r"[0-9a-f]{40}",row["head"]):
            raise SystemExit("Invalid bundle name or commit pin.")
        if digest(export/row["bundle"])!=row["sha256"]:
            raise SystemExit(f"Checksum mismatch for {row['bundle']}")
    clone("--no-checkout",str(export/by_path["."]["bundle"]),str(destination))
    git(destination,"checkout","-B","main",by_path["."]["head"])
    mirrors=destination/".bootstrap"/"remotes"
    mirrors.mkdir(parents=True)
    for path,name in MODULES:
        row=by_path[path]
        pinned=git(destination,"ls-tree","HEAD",path).split()
        if len(pinned)<3 or pinned[0]!="160000" or pinned[2]!=row["head"]:
            raise SystemExit(f"Umbrella gitlink does not match manifest: {path}")
        mirror=mirrors/f"{name}.git"
        clone("--bare",str(export/row["bundle"]),str(mirror))
        git(mirror,"cat-file","-e",row["head"]+"^{commit}")
        # This changes only the fresh checkout's local config, not .gitmodules or global settings.
        git(destination,"config",f"submodule.{path}.url",str(mirror))
    git(destination,"-c","protocol.file.allow=always","submodule","update","--init")
    for path,_ in MODULES:
        if git(destination/path,"rev-parse","HEAD")!=by_path[path]["head"]:
            raise SystemExit(f"Restored commit mismatch: {path}")
    if git(destination,"status","--porcelain"):
        raise SystemExit("Restored umbrella is unexpectedly dirty.")
    (destination/".bootstrap"/"restore-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"Restored clean checkout and four exact module pins to {destination}.")
    print("Origins are real local bundle/mirror paths. Assign actual GitHub URLs only when available.")

if __name__=="__main__":
    main()
