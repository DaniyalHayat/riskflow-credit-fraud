"""Create a portable project ZIP with a checksummed inventory, excluding local state."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'__pycache__','.git','.venv','venv','node_modules','dist','.pytest_cache'}


def included(path):
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if relative.parts[:2] in [('data','local'),('reports','summaries')]:
        return False
    if path.name.startswith('.env') and path.name != '.env.example':
        return False
    if path.suffix in ('.db','.pyc','.pyo') or path.name.endswith('.inspect.ndjson') or '.db-' in path.name:
        return False
    return path.is_file() and not path.is_symlink()


def package():
    files = sorted(p for p in ROOT.rglob('*') if included(p) and p.name != 'PROJECT_MANIFEST.json')
    manifest = {'project':'RiskFlow','version':'1.0.0','data':'Entirely synthetic','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    manifest_path = ROOT/'PROJECT_MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    destination = ROOT.parent/'RiskFlow_Complete_Project.zip'
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in files+[manifest_path]:
            archive.write(path,ROOT.name+'/'+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archive checksum check failed')
        names=archive.namelist()
        if not any(name.endswith('/.github/workflows/tests.yml') for name in names):
            raise RuntimeError('GitHub workflow missing from archive')
    print(f'Packaged {len(files)+1} files: {destination} ({destination.stat().st_size:,} bytes)')
    return destination


if __name__ == '__main__':
    package()
