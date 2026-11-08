"""Freshness checks exercise disposable copies of this repository's actual source bytes.
No application is imported, started or executed. Python stdlib and Git only.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='floorplan-freshness-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        shutil.copytree(HERE, self.root / 'docs/floorplan')
        self.manifest = json.loads((HERE / 'source-manifest.json').read_text())
        for name in self.manifest['source_files']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        subprocess.run(['git', '-C', str(self.root), 'add', '--all'], check=True, capture_output=True)

    def check(self):
        return subprocess.run([sys.executable, str(self.root / 'docs/floorplan/check_freshness.py'), '--root', str(self.root)], text=True, capture_output=True)

    def test_actual_source_and_reviewed_export_pass(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_integrity_rejects_source_and_export_drift(self):
        source = next(n for n in self.manifest['source_files'] if n.endswith(('.js', '.py', '.ts', '.tsx', '.mjs', '.cjs', '.html', '.php')))
        paths = {
            'source modification': self.root / source,
            'source addition': self.root / 'freshness_new_source.js',
            'source deletion': self.root / source,
            'export drift': self.root / 'docs/floorplan/index.html',
        }
        for kind, target in paths.items():
            with self.subTest(kind=kind):
                original = target.read_bytes() if target.exists() else None
                try:
                    if kind == 'source deletion':
                        target.unlink()
                    else:
                        target.write_bytes((original or b'') + b'\n/* freshness fixture change */\n')
                    result = self.check()
                    self.assertNotEqual(result.returncode, 0, kind + ' was silently accepted')
                finally:
                    if original is None:
                        target.unlink(missing_ok=True)
                    else:
                        target.write_bytes(original)

    def test_new_code_template_static_files_are_detected(self):
        for name in ('new.py', 'new.js', 'new.html', 'new.css', 'new.sql', 'new.service', 'new.ts', 'new.tsx', 'new.jsx', 'new.php', 'tsconfig.json', 'railway.json',
                     'templates/new.jinja2', 'static/new.asset'):
            with self.subTest(path=name):
                target = self.root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    target.write_text('fixture addition\n')
                    self.assertNotEqual(self.check().returncode, 0, name)
                finally:
                    target.unlink()

    def test_docs_policy_tests_and_caches_are_not_app_source(self):
        for name in ('docs/extra.py', 'policies/example.js', 'tests/example.py',
                     '.cache/generated.js', 'node_modules/vendor/index.js'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('excluded fixture\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reviewed_authoring_drift_is_rejected(self):
        target = self.root / 'docs/floorplan/architecture.json'
        target.write_bytes(target.read_bytes() + b'\n')
        self.assertNotEqual(self.check().returncode, 0)

if __name__ == '__main__':
    unittest.main()
