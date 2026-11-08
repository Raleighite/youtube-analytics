"""Check pinned source and reviewed map bytes without importing application code.
Python standard library and Git only. Never regenerate/rebaseline on failure.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

EXCLUDED = {'.git', 'docs', 'policies', 'policy', 'tests', 'test', '__pycache__',
            '.cache', '.floorplan', 'floorplan', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', 'coverage'}
EXTENSIONS = {'.py', '.js', '.mjs', '.cjs', '.html', '.css', '.sql', '.service', '.ts', '.tsx', '.jsx', '.php'}
CONFIGS = {'Procfile', 'Dockerfile', 'package.json', 'package-lock.json', 'requirements.txt',
           'docker-compose.yml', 'docker-compose.yaml', 'tsconfig.json', 'railway.json'}

def selected(name):
    path = Path(name)
    if any(part in EXCLUDED for part in path.parts) or path.name.startswith(('test_', 'conftest.')):
        return False
    return (path.suffix.lower() in EXTENSIONS or path.name in CONFIGS
            or bool({'templates', 'static'} & set(path.parts)))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked_path(root, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe manifest path')
    target = root / relative
    for part in [target, *target.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('Symlink is not an admitted regular file')
    if not target.is_file():
        raise ValueError('Missing regular file: ' + name)
    return target

def verify(root):
    docs = root / 'docs/floorplan'
    manifest = json.loads(checked_path(docs, 'source-manifest.json').read_text())
    if manifest.get('schema') != 'floorplan/source-manifest@1':
        raise ValueError('Unsupported manifest schema')
    inventory = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others',
                                '--exclude-standard', '-z'], check=True, capture_output=True).stdout
    names = {n.decode('utf-8') for n in inventory.split(b'\0') if n and selected(n.decode('utf-8'))}
    expected = manifest['source_files']
    if not expected:
        raise ValueError('Empty source inventory')
    if names != set(expected):
        raise ValueError('Source file-set drift: added=' + ','.join(sorted(names-set(expected)))
                         + '; removed=' + ','.join(sorted(set(expected)-names)))
    for name, pin in expected.items():
        if digest(checked_path(root, name)) != pin:
            raise ValueError('Source bytes drift: ' + name)
    artifacts = manifest['artifacts']
    if 'index.html' not in artifacts:
        raise ValueError('Missing export pin')
    for name, pin in artifacts.items():
        if digest(checked_path(docs, name)) != pin:
            raise ValueError('Reviewed artifact drift: ' + name)
    return len(expected), len(artifacts)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        source_count, artifact_count = verify(args.root.resolve())
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print('FRESHNESS FAIL: ' + str(error), file=sys.stderr)
        return 1
    print(f'FRESHNESS PASS: {source_count} RAW source files; {artifact_count} reviewed artifacts')
    return 0

if __name__ == '__main__':
    sys.exit(main())
