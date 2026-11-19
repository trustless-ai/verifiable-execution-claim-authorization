"""Physical disposable-copy witnesses, with positive/restoration checks."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from documentation_refresh import preservation as p


class DocumentationTransition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.check()
        cls.temp_parent = Path(tempfile.gettempdir()).resolve()
        cls.temp = tempfile.TemporaryDirectory(prefix='veca-docs-', dir=cls.temp_parent)
        cls.root = Path(cls.temp.name).resolve()
        cls.original_manifest = (p.ROOT/'artifacts.sha256.json').read_bytes()
        files = p.strict(cls.original_manifest)['files']
        for name in [*files, 'artifacts.sha256.json']:
            target = cls.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p.ROOT/name, target)
        # Both linked worktrees (.git file) and ordinary CI clones (.git
        # directory) use the same read-only Git object store in this copy.
        gitdir = p.git(p.ROOT, 'rev-parse', '--absolute-git-dir').decode().strip()
        (cls.root/'.git').write_bytes(('gitdir: ' + gitdir + '\n').encode())
        p.check(cls.root)

    @classmethod
    def tearDownClass(cls):
        # The only recursive removal is this fresh, task-owned temporary copy.
        if cls.root.parent != cls.temp_parent or not cls.root.name.startswith('veca-docs-'):
            raise RuntimeError('unsafe temporary cleanup path')
        cls.temp.cleanup()

    def tamper(self, name, raw, reason):
        path = self.root/name
        old = path.read_bytes() if path.exists() else None
        current = p.strict(self.original_manifest)
        try:
            if raw is None:
                path.unlink()
                current['files'].pop(name, None)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                current['files'][name] = p.sha(raw)
            # Resealing the ordinary inventory must not conceal the mutation.
            (self.root/'artifacts.sha256.json').write_bytes((json.dumps(current, indent=2, sort_keys=True)+'\n').encode())
            with self.assertRaisesRegex(ValueError, reason):
                p.check(self.root)
        finally:
            if old is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(old)
            (self.root/'artifacts.sha256.json').write_bytes(self.original_manifest)
        self.assertTrue(p.check(self.root)['passed'])
        if old is not None:
            self.assertEqual(path.read_bytes(), old)

    def test_current_positive(self):
        self.assertTrue(p.check(self.root)['passed'])

    def test_arbitrary_readme_resealed(self):
        self.tamper('README.md', b'# Unapproved replacement\n', 'inventory_transition')

    def test_historical_evidence_resealed(self):
        self.tamper('evidence/erc8004-property-fuzz-v0/SUMMARY.json', b'{"fabricated":true}\n', 'inventory_transition')

    def test_protected_file_deleted_and_unlisted(self):
        self.tamper('research/OPEN_PROOF_OBLIGATIONS.md', None, 'inventory_transition')

    def test_unapproved_file_added_and_listed(self):
        self.tamper('research/unapproved-docs-file.md', b'not authorized\n', 'inventory_transition')

    def test_transition_manifest_resealed(self):
        raw=(self.root/p.POLICY).read_bytes()
        self.tamper(p.POLICY, raw+b'\n', 'transition_manifest_identity')

    def test_archived_readme_resealed(self):
        self.tamper(p.ARCHIVE, b'# Invented history\n', 'README_archive_identity')

    def test_workflow_verification_removed_and_resealed(self):
        name='.github/workflows/erc8004-property-fuzz.yml'
        raw=(self.root/name).read_bytes()
        before=b'      - run: python -B tools/pr12_pr13_integration/fuzz_validate.py\n'
        self.assertEqual(raw.count(before), 1)
        self.tamper(name, raw.replace(before, b'      - run: echo no-replay\n'), 'inventory_transition')

    def test_external_executable_resealed(self):
        self.tamper('tools/erc8004/evm.mjs', b'// substituted external backend\n', 'inventory_transition')

    def test_unlisted_file_without_reseal(self):
        path=self.root/'unlisted.txt'
        try:
            path.write_bytes(b'unlisted\n')
            with self.assertRaisesRegex(ValueError, 'file_membership'):
                p.check(self.root)
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(p.check(self.root)['passed'])

    def test_duplicate_manifest_key_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            p.strict(b'{"files":{},"files":{}}')

    def test_workflow_commands_and_pins_preserved(self):
        _, base=p.baseline(self.root)
        for name in base['files']:
            if not name.startswith('.github/workflows/'):
                continue
            old=p.git(self.root,'show',p.BASE+':'+name).decode()
            new=(self.root/name).read_text(encoding='utf8')
            if name in p.UNCHANGED_WORKFLOWS:
                self.assertEqual(old,new,name)
                continue
            self.assertEqual(new, p.workflow(old.encode()).decode())
            # Independently inspect command lines and action pins, rather than
            # counting regeneration by the transformer as sufficient evidence.
            command=lambda s: re.findall(r'^\s+(?:- )?run: (.*)$',s,re.M)
            filtered=[s for s in command(new) if not s.startswith('python -B tools/documentation_refresh/')]
            self.assertEqual(command(old),filtered,name)
            self.assertEqual(re.findall(r'uses: ([^\n]+)',old),re.findall(r'uses: ([^\n]+)',new),name)
            for action in ['prepare','check']:
                self.assertEqual(new.count('tools/documentation_refresh/replay.py '+action),new.count('    steps:'),name)
            self.assertIn('            '+p.RECEIPT,new,name)
            self.assertNotIn(p.VIEW+'/'+p.VIEW,new,name)
            self.assertEqual(new.count('      run:\n        working-directory: '+p.VIEW+'\n'),new.count('    steps:'),name)

    def test_readme_local_links(self):
        text=(self.root/'README.md').read_text(encoding='utf8')
        for target in re.findall(r'\[[^\]\n]+\]\(([^)\s]+)\)',text):
            if not re.match(r'^[a-zA-Z]+:',target):
                self.assertTrue((self.root/target.split('#')[0]).exists(),target)


if __name__=='__main__':
    unittest.main(verbosity=2)
