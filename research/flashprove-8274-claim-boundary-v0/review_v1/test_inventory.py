"""Real unchanged root-checker controls in a complete disposable repository view."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREFIX='research/flashprove-8274-claim-boundary-v0/'
sys.path.insert(0,str(HERE))
from integrity import check


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='flashprove-inventory-');cls.root=Path(cls.temp.name).resolve()
        cls.out=Path(os.environ.get('FLASHPROVE_INVENTORY_OUT',ROOT/'build/flashprove-8274/inventory-controls'))
        cls.out.mkdir(parents=True,exist_ok=True)
        manifest=json.loads((ROOT/'artifacts.sha256.json').read_bytes())
        for name in [*manifest['files'],'artifacts.sha256.json']:
            dest=cls.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def root_check(self,name):
        command=[sys.executable,'-B',*(['-O'] if sys.flags.optimize else []),'tools/verify_artifacts.py']
        p=subprocess.run(command,cwd=self.root,capture_output=True,timeout=120)
        (self.out/(name+'.stdout')).write_bytes(p.stdout);(self.out/(name+'.stderr')).write_bytes(p.stderr)
        result=json.loads(p.stdout)
        (self.out/(name+'.json')).write_bytes((json.dumps({'command':command,'exit_code':p.returncode,'result':result},indent=2)+'\n').encode())
        return p.returncode,result

    def test_01_registered_baseline(self):
        code,r=self.root_check('baseline');self.assertEqual(code,0);self.assertTrue(r['passed'])
        self.assertTrue(check(self.root,False)['passed'])

    def tamper(self,name,change):
        target=PREFIX+'policy.py';p=self.root/target;original=p.read_bytes()
        try:
            change(p)
            code,r=self.root_check(name);self.assertEqual(code,1);self.assertEqual(r['mismatches'],[target])
        finally:p.write_bytes(original)

    def test_02_missing_research_file(self):self.tamper('missing',lambda p:p.unlink())
    def test_03_modified_research_file(self):self.tamper('modified',lambda p:p.write_bytes(p.read_bytes()+b'\n# deliberate tamper\n'))
    def test_04_substituted_research_file(self):self.tamper('substituted',lambda p:p.write_bytes((self.root/(PREFIX+'adapter.py')).read_bytes()))

    def test_05_unregistered_extra_file(self):
        name=PREFIX+'unexpected.py';p=self.root/name;p.write_bytes(b'pass\n')
        try:
            code,r=self.root_check('extra');self.assertEqual(code,1);self.assertEqual(r['mismatches'],[name])
        finally:p.unlink()

    def test_06_historical_repin_is_not_allowed(self):
        name='tools/verify_artifacts.py';p=self.root/name;original=p.read_bytes();m=self.root/'artifacts.sha256.json';old=m.read_bytes()
        try:
            import hashlib
            p.write_bytes(original+b'\n# unauthorized historical change\n');data=json.loads(old);data['files'][name]=hashlib.sha256(p.read_bytes()).hexdigest();m.write_bytes(json.dumps(data).encode())
            r=check(self.root,False);self.assertFalse(r['passed']);self.assertIn('historical_entry:'+name,r['mismatches'])
            (self.out/'historical-repin.json').write_bytes((json.dumps(r,indent=2)+'\n').encode())
        finally:p.write_bytes(original);m.write_bytes(old)

    def test_07_historical_snapshot_tamper(self):
        p=self.root/(PREFIX+'review_v1/baseline-inventory.json');old=p.read_bytes()
        try:
            p.write_bytes(old+b' ');r=check(self.root,False);self.assertFalse(r['passed']);self.assertIn('snapshot:baseline-inventory.json',r['mismatches'])
        finally:p.write_bytes(old)

    def test_08_research_guard_change_and_repin(self):
        target=PREFIX+'policy.py';p=self.root/target;old=p.read_bytes();m=self.root/'artifacts.sha256.json';raw=m.read_bytes()
        try:
            import hashlib
            p.write_bytes(old.replace(b"'authorized': False",b"'authorized': True"));data=json.loads(raw);data['files'][target]=hashlib.sha256(p.read_bytes()).hexdigest();m.write_bytes(json.dumps(data).encode())
            r=check(self.root,False);self.assertFalse(r['passed']);self.assertIn('research_bytes:policy.py',r['mismatches'])
        finally:p.write_bytes(old);m.write_bytes(raw)


if __name__=='__main__':unittest.main(verbosity=2)
