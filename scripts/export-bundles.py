"""Export only clean committed umbrella/module state into trusted offline bundles."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from repo_tools import ROOT, MODULES, git, digest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".bootstrap"):
        raise SystemExit("Export directory must be inside umbrella .bootstrap; copy the completed export elsewhere afterwards.")
    repos = [(".", "adf")] + list(MODULES)
    for path, _ in repos:
        if git(ROOT / path, "status", "--porcelain"):
            raise SystemExit(f"Refusing to export dirty repository: {path}")
        git(ROOT / path, "rev-parse", "HEAD")
    for path, _ in MODULES:
        pinned = git(ROOT, "ls-tree", "HEAD", path).split()[2]
        if pinned != git(ROOT / path, "rev-parse", "HEAD"):
            raise SystemExit(f"Uncommitted gitlink update: {path}")
    output.mkdir(parents=True, exist_ok=True)
    records=[]
    for path, name in repos:
        bundle = output / f"{name}.bundle"
        git(ROOT / path, "bundle", "create", str(bundle), "--all", "HEAD")
        git(ROOT / path, "bundle", "verify", str(bundle))
        records.append({"name":name,"path":path,"bundle":bundle.name,"sha256":digest(bundle),"head":git(ROOT/path,"rev-parse","HEAD")})
    manifest={"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),"repositories":records}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"Exported {len(records)} verified bundles to {output}; ignored files and dirty state are excluded.")

if __name__ == "__main__":
    main()
