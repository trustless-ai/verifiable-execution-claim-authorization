"""Physical resealing controls for the current-to-historical replay boundary."""
from pathlib import Path
import re
import shutil
import tempfile
import unittest
import transition as t


class TransitionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t.check()
        cls.parent = Path(tempfile.gettempdir()).resolve()
        cls.temp = tempfile.TemporaryDirectory(prefix='veca-erc8378-transition-', dir=cls.parent)
        cls.root = Path(cls.temp.name).resolve()
        cls.raw = (t.ROOT/'artifacts.sha256.json').read_bytes()
        cls.manifest = t.strict(cls.raw)
        for name in [*cls.manifest['files'], 'artifacts.sha256.json']:
            dest = cls.root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(t.ROOT/name, dest)
        gitdir = t.git(t.ROOT, 'rev-parse', '--absolute-git-dir').decode().strip()
        (cls.root/'.git').write_text('gitdir: '+gitdir+'\n', encoding='utf8')
        t.check(cls.root)

    @classmethod
    def tearDownClass(cls):
        if cls.root.parent != cls.parent or not cls.root.name.startswith('veca-erc8378-transition-'):
            raise RuntimeError('unsafe_test_cleanup')
        cls.temp.cleanup()

    def tamper(self, name, value, reason, reseal=True):
        path = self.root/name
        old = path.read_bytes() if path.exists() else None
        manifest = t.strict(self.raw)
        try:
            if value is None:
                path.unlink()
                manifest['files'].pop(name, None)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
                manifest['files'][name] = t.sha(value)
            if reseal:
                (self.root/'artifacts.sha256.json').write_bytes(t.canonical(manifest))
            with self.assertRaisesRegex(ValueError, reason):
                t.check(self.root)
        finally:
            if old is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(old)
            (self.root/'artifacts.sha256.json').write_bytes(self.raw)
        self.assertTrue(t.check(self.root)['passed'])

    def test_positive(self):
        self.assertEqual(t.check(self.root)['review_payload_files_unchanged'],33)

    def test_payload_solidity_resealed(self):
        self.tamper(t.PREFIX+'/evm/src/EvidenceGateV2.sol', b'// gate replaced\n', 'inventory_transition')

    def test_payload_evidence_resealed(self):
        self.tamper(t.PREFIX+'/evidence/native-payout.json', b'{"paid":true}\n', 'inventory_transition')

    def test_payload_file_deleted(self):
        self.tamper(t.PREFIX+'/FORMAT.md', None, 'inventory_transition')

    def test_core_resealed(self):
        name=next(p for p in self.manifest['files'] if p.startswith('evidence/erc8404/core/') and p.endswith('.py'))
        self.tamper(name, b'# substituted Core\n', 'inventory_transition')

    def test_historical_evidence_resealed(self):
        self.tamper('evidence/documentation-refresh-v1/RESULTS.json', b'{}\n', 'inventory_transition')

    def test_old_checker_resealed(self):
        self.tamper('tools/documentation_refresh/preservation.py', b'# weakened\n', 'inventory_transition')

    def test_root_readme_resealed(self):
        self.tamper('README.md', b'# substituted\n', 'inventory_transition')

    def test_extra_listed_file(self):
        self.tamper(t.PREFIX+'/extra.txt', b'extra\n', 'inventory_transition')

    def test_extra_unlisted_file(self):
        self.tamper('unlisted.txt', b'extra\n', 'file_membership', False)

    def test_policy_resealed(self):
        self.tamper(t.PREFIX+'/CI_TRANSITION.json', b'{}\n', 'transition_policy_identity')

    def test_workflow_command_removed(self):
        name='.github/workflows/coverage-v4.yml'
        raw=(self.root/name).read_bytes()
        before=b'      - run: python -B tools/v4/validate.py\n'
        self.assertEqual(raw.count(before),1)
        self.tamper(name,raw.replace(before,b'      - run: echo bypass\n'),'inventory_transition')

    def test_workflow_pin_changed(self):
        name='.github/workflows/coverage-v4.yml'
        raw=(self.root/name).read_bytes()
        self.tamper(name,raw.replace(b'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683', b'actions/checkout@main'),'inventory_transition')

    def test_native_job_replaced(self):
        self.tamper(t.WORKFLOW,b'name: false green\n','inventory_transition')

    def test_workflow_routes_preserve_commands_and_pins(self):
        _, _, _, policy=t.contract(str(self.root))
        for name in policy['workflow_routes']:
            old=t.git(self.root,'show',t.BASE+':'+name).decode()
            new=(self.root/name).read_text(encoding='utf8')
            commands=lambda x:re.findall(r'^\s+(?:- )?run: (.*)$',x,re.M)
            self.assertEqual(commands(old),[c for c in commands(new) if not c.startswith('python -B '+t.PREFIX+'/ci/transition.py ')],name)
            self.assertEqual(re.findall(r'uses: ([^\n]+)',old),re.findall(r'uses: ([^\n]+)',new),name)
            self.assertEqual(new.count('/ci/transition.py prepare'),new.count('    steps:'),name)
            self.assertEqual(new.count('/ci/transition.py check'),new.count('    steps:'),name)

    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(ValueError,'duplicate_JSON_key'):
            t.strict(b'{"files":{},"files":{}}')


if __name__=='__main__':
    unittest.main(verbosity=2)
