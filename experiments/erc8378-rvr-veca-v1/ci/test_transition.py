"""Physical resealing controls for the current-to-historical replay boundary."""
from pathlib import Path
import json
import os
import re
import shutil
import tempfile
import unittest
from unittest import mock
import subprocess
import sys
import replay as r
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


class ReproductionPreflight(unittest.TestCase):
    def test_python3_only_path_is_refused(self):
        with tempfile.TemporaryDirectory(prefix='veca-python3-only-') as directory:
            # A python3 filename or shell alias cannot satisfy vm.ffi's python argv.
            (Path(directory)/'python3').write_bytes(b'placeholder')
            with self.assertRaisesRegex(r.ReproductionError, 'FFI_PYTHON_REQUIRED.*python3'):
                r.ffi_python({'PATH': directory})

    def test_python_must_use_current_environment(self):
        probe = subprocess.CompletedProcess([], 0,
            json.dumps([sys.executable, '/different-environment']).encode(), b'')
        with mock.patch.object(r.shutil, 'which', return_value=sys.executable), \
             mock.patch.object(r.subprocess, 'run', return_value=probe):
            with self.assertRaisesRegex(r.ReproductionError, 'FFI_PYTHON_ENVIRONMENT'):
                r.ffi_python(dict(os.environ))

    def test_current_python_real_probe(self):
        with mock.patch.object(r.shutil, 'which', return_value=sys.executable):
            self.assertEqual(r.ffi_python(dict(os.environ)), sys.executable)

    def test_offline_missing_compiler_is_actionable(self):
        with tempfile.TemporaryDirectory(prefix='veca-no-solc-') as directory:
            with self.assertRaisesRegex(r.ReproductionError, 'SOLC_REQUIRED.*offline Foundry cannot download'):
                r.offline_solc({'PATH': ''}, Path(directory))

    def test_wrong_compiler_hash_is_refused_before_execution(self):
        with tempfile.TemporaryDirectory(prefix='veca-bad-solc-') as directory:
            binary = Path(directory)/'solc'
            binary.write_bytes(b'not a compiler')
            with mock.patch.object(r.subprocess, 'run') as execute:
                with self.assertRaisesRegex(r.ReproductionError, 'SOLC_SHA256'):
                    r.offline_solc({'PATH': '', 'FOUNDRY_SOLC': str(binary)})
                execute.assert_not_called()

    def compiler_fixture(self, directory):
        binary = Path(directory)/'.svm/0.8.30/solc-0.8.30'
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b'tool selection fixture; never executed')
        return binary, r.t.sha(binary.read_bytes())

    def test_compiler_version_mismatch(self):
        with tempfile.TemporaryDirectory(prefix='veca-version-solc-') as directory:
            binary, digest = self.compiler_fixture(directory)
            probe = subprocess.CompletedProcess([], 0, b'Version: 0.8.29', b'')
            with mock.patch.object(r, 'SOLC_SHA256', {sys.platform: digest}), \
                 mock.patch.object(r.subprocess, 'run', return_value=probe):
                with self.assertRaisesRegex(r.ReproductionError, 'SOLC_VERSION'):
                    r.offline_solc({'PATH': '', 'FOUNDRY_SOLC': str(binary)})

    def test_verified_svm_compiler_is_explicitly_selected(self):
        with tempfile.TemporaryDirectory(prefix='veca-cache-solc-') as directory:
            binary, digest = self.compiler_fixture(directory)
            probe = subprocess.CompletedProcess([], 0, ('Version: '+r.SOLC_VERSION).encode(), b'')
            env = {'PATH': ''}
            with mock.patch.object(r, 'SOLC_SHA256', {sys.platform: digest}), \
                 mock.patch.object(r.subprocess, 'run', return_value=probe):
                result = r.offline_solc(env, Path(directory))
            self.assertEqual(Path(env['FOUNDRY_SOLC']), binary.resolve())
            self.assertEqual(result, {'version': r.SOLC_VERSION, 'sha256': digest})

    def test_reused_label_preserves_evidence(self):
        with tempfile.TemporaryDirectory(prefix='veca-label-') as directory:
            root = Path(directory)
            build = r.fresh_run(root, 'review-01')
            old = build/'runtime/gate-v2/runs/review-01-normal/evidence.json'
            old.parent.mkdir(parents=True)
            old.write_bytes(b'original evidence')
            with self.assertRaisesRegex(r.ReproductionError, 'RUN_LABEL_IN_USE.*new-unique-label'):
                r.fresh_run(root, 'review-01')
            self.assertEqual(old.read_bytes(), b'original evidence')
            self.assertNotEqual(r.fresh_run(root, 'review-02'), build)

    def test_partial_tool_run_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix='veca-partial-') as directory:
            root = Path(directory)
            build = r.fresh_run(root, 'ci-current')
            tool = build/'tools/solc'
            tool.parent.mkdir(parents=True)
            tool.write_bytes(b'preserved partial setup')
            with self.assertRaisesRegex(r.ReproductionError, 'RUN_LABEL_IN_USE'):
                r.fresh_run(root, 'ci-current')
            self.assertEqual(tool.read_bytes(), b'preserved partial setup')

    def test_run_label_cannot_escape_build(self):
        for label in ['../outside', 'space label', '', 'a'*49]:
            with self.subTest(label=label), self.assertRaisesRegex(r.ReproductionError, 'RUN_LABEL:'):
                r.fresh_run(Path(tempfile.gettempdir()), label)


if __name__=='__main__':
    unittest.main(verbosity=2)
