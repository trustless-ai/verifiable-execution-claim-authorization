"""Resealing attempts against disposable copies, with restored positive controls."""
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from second_backend_integration import preservation as p

class TransitionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.check();cls.parent=Path(tempfile.gettempdir()).resolve();cls.temp=tempfile.TemporaryDirectory(prefix='veca-second-',dir=cls.parent);cls.root=Path(cls.temp.name).resolve()
        cls.original=(p.ROOT/'artifacts.sha256.json').read_bytes()
        for name in [*p.strict(cls.original)['files'],'artifacts.sha256.json']:
            path=cls.root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p.ROOT/name,path)
        gitdir=p.git(p.ROOT,'rev-parse','--absolute-git-dir').decode().strip();(cls.root/'.git').write_bytes(('gitdir: '+gitdir+'\n').encode());p.check(cls.root)
    @classmethod
    def tearDownClass(cls):
        if cls.root.parent!=cls.parent or not cls.root.name.startswith('veca-second-'):raise RuntimeError('unsafe cleanup')
        cls.temp.cleanup()
    def tamper(self,name,raw,reason):
        path=self.root/name;old=path.read_bytes() if path.exists() else None;manifest=p.strict(self.original)
        try:
            if raw is None:path.unlink();manifest['files'].pop(name,None)
            else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);manifest['files'][name]=p.sha(raw)
            (self.root/'artifacts.sha256.json').write_bytes((json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode())
            with self.assertRaisesRegex(ValueError,reason):p.check(self.root)
        finally:
            if old is None:path.unlink(missing_ok=True)
            else:path.write_bytes(old)
            (self.root/'artifacts.sha256.json').write_bytes(self.original)
        self.assertTrue(p.check(self.root)['passed'])
        if old is not None:self.assertEqual(path.read_bytes(),old)
    def test_pristine(self):self.assertTrue(p.check(self.root)['passed'])
    def test_historical_evidence_resealed(self):self.tamper('evidence/erc8004-property-fuzz-v0/SUMMARY.json',b'{"fabricated":true}\n','inventory_transition')
    def test_historical_file_deleted(self):self.tamper('research/OPEN_PROOF_OBLIGATIONS.md',None,'inventory_transition')
    def test_unapproved_addition_resealed(self):self.tamper('research/unapproved-new-file.md',b'not approved\n','inventory_transition')
    def test_transition_manifest_resealed(self):self.tamper(p.POLICY,(self.root/p.POLICY).read_bytes()+b'\n','transition_manifest_identity')
    def test_pilot_executable_resealed(self):self.tamper('tools/erc8004_second_backend/adapter.py',b'print("fake")\n','inventory_transition')
    def test_pilot_historical_report_resealed(self):self.tamper('research/erc8004-second-backend-v0/RESULTS.md',b'fabricated\n','inventory_transition')
    def test_new_ci_executable_resealed(self):self.tamper('tools/second_backend_integration/ci.py',b'print("skip")\n','inventory_transition')
    def test_old_guard_resealed(self):self.tamper('tools/documentation_refresh/preservation.py',b'print("pass")\n','inventory_transition')
    def test_readme_resealed(self):self.tamper('README.md',b'# unsupported claim\n','inventory_transition')
    def test_archive_resealed(self):self.tamper(p.ARCHIVE,b'# invented history\n','README_archive_identity')
    def test_workflow_command_removed(self):
        name='.github/workflows/erc8004-property-fuzz.yml';raw=(self.root/name).read_bytes();before=b'      - run: python -B tools/pr12_pr13_integration/fuzz_validate.py\n';self.assertEqual(raw.count(before),1)
        self.tamper(name,raw.replace(before,b'      - run: echo skipped\n'),'inventory_transition')
    def test_unlisted_file(self):
        path=self.root/'unlisted.txt'
        try:
            path.write_bytes(b'not listed\n')
            with self.assertRaisesRegex(ValueError,'file_membership'):p.check(self.root)
        finally:path.unlink(missing_ok=True)
        self.assertTrue(p.check(self.root)['passed'])
    def test_duplicate_manifest_key(self):
        with self.assertRaisesRegex(ValueError,'duplicate JSON key'):p.strict(b'{"files":{},"files":{}}')
    def test_inherited_commands_pins_and_platforms(self):
        base=p.strict(p.git(self.root,'show',p.BASE+':artifacts.sha256.json'))
        for name in base['files']:
            if not name.startswith('.github/workflows/'):continue
            old=p.git(self.root,'show',p.BASE+':'+name).decode();new=(self.root/name).read_text(encoding='utf-8')
            if name in p.UNTOUCHED:self.assertEqual(old,new);continue
            commands=lambda x:re.findall(r'^\s+(?:- )?run: (.*)$',x,re.M)
            if name.endswith('/documentation-refresh.yml'):new_commands=[v for v in commands(new) if 'tools/second_backend_integration/replay.py' not in v]
            else:new_commands=[v.replace('tools/second_backend_integration/replay.py','tools/documentation_refresh/replay.py') for v in commands(new)]
            self.assertEqual(commands(old),new_commands,name)
            self.assertEqual(re.findall(r'uses: (.*)',old),re.findall(r'uses: (.*)',new),name)
            self.assertEqual(re.findall(r'runs-on: (.*)',old),re.findall(r'runs-on: (.*)',new),name)
            self.assertIn(p.RECEIPT,new)
    def test_local_readme_links(self):
        for target in re.findall(r'\[[^\]\n]+\]\(([^)\s]+)\)',(self.root/'README.md').read_text(encoding='utf-8')):
            if not re.match(r'^[a-zA-Z]+:',target):self.assertTrue((self.root/target.split('#')[0]).exists(),target)
if __name__=='__main__':unittest.main(verbosity=2)
