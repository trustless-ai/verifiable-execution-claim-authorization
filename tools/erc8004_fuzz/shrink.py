"""Replay-based deletion and bounded value shrinking; infrastructure is never a witness."""
import copy

from erc8004_fuzz import generate
import agent_harness as h


def divergence(row, inp):
    if row.get('backend_conformance') != 'FAIL' or not row.get('observed_behavior'):
        return None
    expected = row['expected_behavior']['behavior']['steps']
    actual = row['observed_behavior']['behavior']['steps']
    if len(expected) != len(actual):
        return 'step_count'
    for op, want, got in zip(inp['sequence'], expected, actual):
        if want['status'] != got['status']:
            return 'status:' + op['kind']
        if want['events'] != got['events']:
            return 'events:' + op['kind']
        for key in ('agents', 'operators', 'requests', 'summaries'):
            if want['state'][key] != got['state'][key]:
                return 'state:' + key
    if row['expected_behavior']['authorization'] != row['observed_behavior']['authorization']:
        return 'authorization'
    return None


def deletions(inp):
    if len(inp['sequence']) <= 1:
        return []
    result = []
    for i in range(len(inp['sequence'])):
        value = copy.deepcopy(inp)
        del value['sequence'][i]
        result.append(value)
    return result


def simplifications(inp):
    result = []
    for i, op in enumerate(inp['sequence']):
        replacements = {key: value for key, value in (('uri', ''), ('tag', ''), ('value', '0x'),
                        ('key', ''), ('agent_id', 0), ('signed_agent', 0), ('metadata', [])) if key in op}
        if op.get('deadline_offset', 0) > 301:
            replacements['deadline_offset'] = 301
        if op.get('response', 0) > 101:
            replacements['response'] = 101
        for key, value in replacements.items():
            if op[key] != value:
                candidate = copy.deepcopy(inp)
                candidate['sequence'][i][key] = value
                result.append(candidate)
    # Only simplifications, never larger values; preserves termination.
    return result


def minimize(original, category, adapter, out):
    out.mkdir(parents=True, exist_ok=False)
    current = copy.deepcopy(original)
    attempts, rounds = [], 0

    def trial(values, stage):
        nonlocal rounds
        successful = []
        for start in range(0, len(values), 20):
            selected = values[start:start + 20]
            directory = out / ('round-%03d' % rounds)
            rounds += 1
            cases = [{'id': 'candidate-%03d' % i, 'input': value} for i, value in enumerate(selected)]
            suite = generate.write_suite(cases, directory)
            report = h.execute(suite, adapter, directory / 'run')
            if report['exit_code'] == 2 or len(report['rows']) != len(cases):
                h.write(out / 'incomplete.json', {'stage': stage, 'report': str(directory / 'run/report.json')})
                raise ValueError('shrinker infrastructure failure is not a counterexample')
            by_id = {r['id']: r for r in report['rows']}
            for case in cases:
                observed = divergence(by_id[case['id']], case['input'])
                retained = observed == category
                attempts.append({'stage': stage, 'input_sha256': h.sha(h.encode(case['input'])),
                                 'divergence': observed, 'retained': retained,
                                 'report': directory.name + '/run/report.json', 'case': case['id']})
                if retained:
                    successful.append(case['input'])
        return successful

    while True:
        smaller = trial(deletions(current), 'delete')
        if not smaller:
            break
        current = smaller[0]
    while True:
        simpler = trial(simplifications(current), 'simplify')
        if not simpler:
            break
        current = simpler[0]
    # Simplification can expose further deletion opportunities.
    while True:
        smaller = trial(deletions(current), 'final-delete')
        if not smaller:
            break
        current = smaller[0]
    final = trial([current], 'final-replay')
    if not final:
        raise ValueError('final witness lost its divergence')
    result = {'schema': 'erc8004.shrink.v0', 'category': category, 'original': original,
              'minimized': current, 'original_calls': len(original['sequence']),
              'minimized_calls': len(current['sequence']), 'attempts': attempts,
              'deletion_1_minimal': True, 'global_minimum_claimed': False,
              'infrastructure_failures_count_as_witnesses': False}
    h.write(out / 'result.json', result)
    return result
