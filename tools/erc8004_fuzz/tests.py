"""Research infrastructure checks; independent of the EVM observation stream."""
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from erc8004_fuzz import generate, model
from erc8004_fuzz.shrink import divergence, deletions, simplifications


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = generate.build()

    def test_exact_seed_budget_and_unique_cases(self):
        self.assertEqual(self.fixture['seeds'], [8004, 8299, 8274])
        self.assertEqual(len(self.fixture['cases']), 300)
        self.assertEqual(len({c['id'] for c in self.fixture['cases']}), 300)
        for seed in generate.SEEDS:
            self.assertEqual(sum(c['seed'] == seed for c in self.fixture['cases']), 100)

    def test_inputs_are_reproducible_and_preserved(self):
        self.assertEqual(h.encode(generate.build()), h.encode(self.fixture))
        self.assertEqual((generate.PROFILE_DIR / 'fixtures.json').read_bytes(), h.encode(self.fixture))

    def test_all_structured_families_exercised_by_each_seed(self):
        for seed in generate.SEEDS:
            self.assertEqual({c['family'] for c in self.fixture['cases'] if c['seed'] == seed}, set(generate.FAMILIES))

    def test_oracle_does_not_mutate_inputs(self):
        for case in self.fixture['cases']:
            before = h.encode(case['input'])
            model.expected(case['input'])
            self.assertEqual(before, h.encode(case['input']))

    def test_rejected_calls_preserve_model_state(self):
        refused = 0
        for case in self.fixture['cases']:
            oracle = model.Model(case['input']['sequence'])
            for op in case['input']['sequence']:
                before = oracle.snapshot()
                step = oracle.step(op)
                if step['status'] == 'REJECTED':
                    refused += 1
                    self.assertEqual(step['state'], before)
                    self.assertEqual(step['events'], [])
        self.assertGreater(refused, 100)

    def test_expectation_free_transport(self):
        corpus = json.loads((generate.PROFILE_DIR / 'vectors.json').read_bytes())
        request = h.detached_request(corpus)
        self.assertEqual(len(request['cases']), 300)
        for case in request['cases']:
            self.assertEqual(set(case), {'id', 'input'})
            self.assertEqual(set(case['input']), {'sequence', 'claim', 'supply_receipt'})
            self.assertTrue(all('expected' not in op for op in case['input']['sequence']))

    def test_oracle_imports_no_implementation_or_observations(self):
        source = (h.ROOT / 'tools/erc8004_fuzz/model.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {'copy', 'hashlib', 'json'})
        self.assertFalse(any(isinstance(n, ast.ImportFrom) for n in ast.walk(tree)))

    def test_adapter_imports_no_model_or_generator(self):
        source = (h.ROOT / 'tools/erc8004_fuzz/adapter.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn('erc8004_fuzz.model', imports)
        self.assertNotIn('erc8004_fuzz.generate', imports)
        self.assertNotIn('expectations.json', source)
        self.assertNotIn('expected(', (h.ROOT / 'tools/erc8004_fuzz/sequence.mjs').read_text(encoding='utf-8'))

    def test_obligations_are_applicable_not_blanket_catalog(self):
        all_ids = set(json.loads((generate.PROFILE_DIR / 'obligations.json').read_bytes()))
        visited = set()
        for case in self.fixture['cases']:
            ids = set(generate.obligations_for(case['input']))
            self.assertLess(ids, all_ids)
            visited.update(ids)
        self.assertEqual(visited, all_ids)

    def test_correct_refusal_and_unknown_remain_separate_from_conformance(self):
        statuses = {model.expected(c['input'])['authorization']['status'] for c in self.fixture['cases']}
        self.assertEqual(statuses, {'VERIFIED', 'REFUTED', 'UNVERIFIABLE'})

    def test_deliberately_wrong_expectation_fails_grader(self):
        # Exercise the actual pinned grader with a synthetic projection and a
        # conflicting expectation. This is a grader control, not an EVM replay.
        grader = h.grader()
        corpus = json.loads((generate.PROFILE_DIR / 'vectors.json').read_bytes())
        case = copy.deepcopy(corpus['vectors'][0])
        original = copy.deepcopy(case['expected'])
        case['expected']['authorization']['status'] = 'FABRICATED'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'projected.json'
            h.write(path, {case['name']: original})
            import subprocess
            command = subprocess.list2cmdline([sys.executable, '-B', str(h.ROOT / 'tools/harness_v0/replay.py'), str(path)])
            result = grader._run_reporter(h.ROOT, command, 'oracle-control', h.encode({**corpus, 'vectors': [case]}), 'vectors.json')
            self.assertFalse(result.ok)
            self.assertIn(result.kind, grader.DETERMINATE)

    def test_pin_tamper_rejected_before_adapter_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            suite = generate.write_suite(self.fixture['cases'][:1], folder)
            with (folder / 'vectors.json').open('ab') as stream:
                stream.write(b' ')
            with patch.object(h.subprocess, 'run', side_effect=AssertionError('adapter must not run')):
                report = h.execute(suite, generate.PROFILE_DIR / 'adapter.json', folder / 'run')
            self.assertEqual(report['exit_code'], 2)
            self.assertIn('suite pin mismatch', report['error'])

    def test_shrink_deletions_nonempty_and_no_input_mutation(self):
        inp = copy.deepcopy(self.fixture['cases'][3]['input'])
        original = h.encode(inp)
        self.assertTrue(all(len(v['sequence']) == len(inp['sequence']) - 1 for v in deletions(inp)))
        self.assertEqual(h.encode(inp), original)
        inp['sequence'] = inp['sequence'][:1]
        self.assertEqual(deletions(inp), [])

    def test_infrastructure_is_not_a_counterexample(self):
        inp = self.fixture['cases'][0]['input']
        self.assertIsNone(divergence({'backend_conformance': 'UNVERIFIABLE'}, inp))
        self.assertIsNone(divergence({'backend_conformance': 'FAIL', 'observed_behavior': None}, inp))

    def test_value_simplification_is_finite_and_distinct(self):
        inp = self.fixture['cases'][4]['input']
        values = simplifications(inp)
        self.assertLess(len(values), 30)
        self.assertTrue(all(v != inp for v in values))


if __name__ == '__main__':
    unittest.main()
