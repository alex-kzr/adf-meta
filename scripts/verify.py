"""Static foundation checks; secret patterns are heuristic, not a full audit."""
import ast
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote
from repo_tools import ROOT, MODULES, git, digest

def main() -> None:
    errors: list[str]=[]
    count=0
    ignored={".git",".bootstrap",".idea",".vscode","node_modules","dist","build","__pycache__",".venv",".pytest_cache"}
    for base,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in ignored and not d.endswith('.egg-info')]
        for name in names:
            path=Path(base)/name
            if path.suffix not in {'.md','.py','.json','.toml','.yaml','.yml','.ts','.tsx','.css','.html','.txt','.lock'}:continue
            count+=1
            try:
                text=path.read_text(encoding='utf-8-sig')
                if path.suffix=='.py':ast.parse(text,filename=str(path))
                if path.suffix=='.toml':tomllib.loads(text)
                if path.suffix=='.json':json.loads(text)
                if path.suffix=='.md':
                    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
                        target=target.strip('<>').split('#')[0]
                        if not target or re.match(r'^[a-z]+:',target):continue
                        if not (path.parent/unquote(target)).resolve().exists():errors.append(f'Broken link: {path.relative_to(ROOT)} -> {target}')
            except (ValueError,SyntaxError,OSError) as exc:errors.append(f'{path.relative_to(ROOT)}: {exc}')
    if digest(ROOT/'SPEC.md')!='3494049865774af023fa49427feb3f71b8865dc82adcac3d7e5bc6a81cdde5a2':errors.append('Source SPEC changed')
    try:
        stages=git(ROOT,'ls-files','--stage').splitlines()
        gitlinks={line.split('\t')[1]:line.split()[1] for line in stages if line.startswith('160000 ')}
        if set(gitlinks)!=dict(MODULES).keys():errors.append('Expected exactly four gitlinks')
        paths=git(ROOT,'config','-f','.gitmodules','--get-regexp',r'^submodule\..*\.path$').splitlines()
        if {line.split(' ',1)[1] for line in paths}!=set(dict(MODULES)):errors.append('.gitmodules paths mismatch')
        for path,_ in MODULES:
            if gitlinks.get(path)!=git(ROOT/path,'rev-parse','HEAD'):errors.append(f'Gitlink HEAD mismatch: {path}')
        for repo in [ROOT]+[ROOT/path for path,_ in MODULES]:
            for line in git(repo,'ls-files','--stage').splitlines():
                if line.startswith('160000 '):continue
                relative=line.split('\t')[1]
                path=repo/relative
                if any(part in {'.bootstrap','.idea','.venv','node_modules','dist'} for part in Path(relative).parts):errors.append(f'Generated state tracked: {relative}')
                if path.name=='.env' or (path.name.startswith('.env.') and path.name!='.env.example') or path.suffix in {'.pem','.key'} or path.name in {'auth.json','credentials.json'}:errors.append(f'Sensitive file tracked: {relative}')
                if path.is_file() and path.stat().st_size<2_000_000:
                    text=path.read_text(encoding='utf-8',errors='replace')
                    if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|sk-(?:proj-|ant-)[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}',text):errors.append(f'Suspicious secret pattern: {relative}')
    except (RuntimeError,IndexError) as exc:errors.append(str(exc))
    document=json.loads((ROOT/'packages/contracts/openapi.json').read_text())
    def refs(value: object) -> None:
        if isinstance(value,dict):
            if '$ref' in value:
                target=value['$ref']
                if not target.startswith('#/'):errors.append(f'Non-local OpenAPI ref: {target}')
                else:
                    item=document
                    try:
                        for key in target[2:].split('/'):item=item[key.replace('~1','/').replace('~0','~')]
                    except (KeyError,TypeError):errors.append(f'Broken OpenAPI ref: {target}')
            for item in value.values():refs(item)
        elif isinstance(value,list):
            for item in value:refs(item)
    refs(document)
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        for stem in ('workflow','execution-request','execution-event'):
            schema=json.loads((ROOT/f'packages/contracts/{stem}.schema.json').read_text())
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema,format_checker=FormatChecker()).validate(json.loads((ROOT/f'packages/contracts/examples/{stem}.json').read_text()))
    except ImportError:errors.append('Install requirements-dev.txt to validate schemas')
    except Exception as exc:errors.append(f'Schema validation: {exc}')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'PASS: {count} source files; Markdown links, Python/TOML/JSON, schema fixtures, OpenAPI refs, four gitlinks and heuristic secret checks; SPEC unchanged.')

if __name__=='__main__':main()
