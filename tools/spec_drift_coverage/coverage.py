"""Reconcile preserved harness/grader evidence with explicit, reviewed guard mappings."""
import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as harness
from spec_drift_coverage.common import CONFIG, Reader, encode, require, sha, strict, write

LEVELS = ('DECLARED', 'REFERENCED_BY_TEST', 'EXECUTED_AND_MATCHED',
          'ENFORCEMENT_DEMONSTRATED', 'INDEPENDENTLY_REPLAYED', 'NOT_COVERED', 'UNVERIFIABLE')


class Reporter:
    def __init__(self, reader=None):
        self.reader = reader or Reader()
        self.grader = harness.grader()  # Fails when missing or changed; never a successful setup.
        self.canon = self.grader._grader_canon()

    def unit(self, refs):
        r = self.reader
        suite, vectors, obligations = [r.json(refs[k]) for k in ('suite', 'vectors', 'obligations')]
        require(suite['vectors']['sha256'] == refs['vectors']['sha256'], 'suite vectors pin')
        require(suite['obligations']['sha256'] == refs['obligations']['sha256'], 'suite obligations pin')
        self.grader._reporter_corpus(harness.encode(vectors))
        request = r.json(refs['request'])
        require(encode(request) == encode(harness.detached_request(vectors)), 'expectations or non-fixture input sent to adapter')
        data = r.json(refs['observations'])
        harness.validate_observations(data)
        report = r.json(refs['report'])
        require(report['schema'] == 'agent-harness.report.v0' and report['adapter_exit_code'] == 0,
                'missing/completed adapter evidence')
        require(report['exit_code'] in (0, 1) and report['backend_conformance'] in ('PASS', 'FAIL'), 'indeterminate execution')
        for key, source in [('suite_sha256', 'suite'), ('vectors_sha256', 'vectors'),
                            ('request_sha256', 'request'), ('observation_sha256', 'observations')]:
            require(report[key] == refs[source]['sha256'], 'report digest disagreement: ' + key)
        rows = {row['id']: row for row in report['rows']}
        ids = {v['name'] for v in vectors['vectors']}
        require(len(rows) == len(report['rows']) == len(ids) and set(rows) == ids == set(data['observations']), 'case identities')
        for vector in vectors['vectors']:
            row = rows[vector['name']]
            require(vector['obligations'] and all(o in obligations for o in vector['obligations']), 'undefined obligation')
            obs = data['observations'][vector['name']]
            projection = {k: obs[k] for k in ('behavior', 'authorization')}
            require(encode(row['expected_behavior']) == encode(vector['expected']), 'expectation drift')
            require(encode(row['observed_behavior']) == encode(projection), 'observation drift')
            require(row['requirements'] == {o: obligations[o] for o in vector['obligations']}, 'obligation metadata drift')
            matched = self.canon(projection) == self.canon(vector['expected'])
            require(row['backend_conformance'] == ('PASS' if matched else 'FAIL'), 'grader row disagreement')
        all_pass = all(row['backend_conformance'] == 'PASS' for row in rows.values())
        require(report['backend_conformance'] == ('PASS' if all_pass else 'FAIL'), 'grader aggregate disagreement')
        require(report['exit_code'] == (0 if all_pass else 1), 'grader exit disagreement')
        return report, rows, vectors

    def mutation(self, population, descriptor, record, binding):
        """All predicates required; a crash, report label or fixture marker cannot substitute."""
        require(binding['id'] == descriptor['binding'] == population['id'] + '/' + descriptor['id'], 'unrelated mutation binding')
        require(binding['profile'] == population['profile'], 'cross-profile mutation binding')
        require(record.get('id', record.get('guard')) == descriptor['id'] == binding['guard'], 'guard mismatch')
        require(record['classification'] == 'KILLED', 'mutation not KILLED')
        require(record.get('witness', record.get('witness_id')) == binding['witness'], 'witness mismatch')
        source = self.reader.raw(descriptor['source'])
        require(sha(source) == record['original_sha256'] == binding['source_sha256'], 'original source identity')
        before, after = binding['before'].encode(), binding['after'].encode()
        require(record.get('before', record.get('old')) == binding['before'] and
                record.get('after', record.get('new')) == binding['after'], 'physical change mismatch')
        require(before != after, 'no physical change')
        if 'source_window' in binding:
            begin, end = [s.encode() for s in binding['source_window']]
            left = source.index(begin)
            right = source.index(end, left)
            section = source[left:right]
            require(section.count(before) == 1, 'physical mutation not uniquely applied in function')
            mutant = source[:left] + section.replace(before, after, 1) + source[right:]
        else:
            require(source.count(before) == 1, 'physical mutation not uniquely applied')
            mutant = source.replace(before, after, 1)
        if 'infrastructure_relocation' in binding:
            relocation = binding['infrastructure_relocation']
            require(mutant.count(relocation['before'].encode()) == 1, 'relocation not unique')
            mutant = mutant.replace(relocation['before'].encode(), relocation['after'].encode(), 1)
        require(sha(mutant) == record['mutant_sha256'] == binding['mutant_sha256'] != sha(source), 'mutant identity')
        if 'mutant_source' in descriptor:
            require(mutant == self.reader.raw(descriptor['mutant_source']), 'retained mutant bytes mismatch')
        elif descriptor.get('mutant_source_derivation') != 'exact_unique_replacement_from_retained_original':
            raise ValueError('missing physical mutant bytes')
        phases = {p: self.unit(descriptor[p]) for p in ('baseline', 'mutated', 'restored')}
        require(len({sha(encode(phases[p][2])) for p in phases}) == 1,
                'mutation phases do not execute the same input/expectation corpus')
        require(phases['baseline'][0]['exit_code'] == phases['restored'][0]['exit_code'] == 0, 'failed positive/restoration control')
        require(phases['mutated'][0]['exit_code'] == 1, 'no determinate mutant failure')
        witness = binding['witness']
        baseline = phases['baseline'][1][witness]
        changed = phases['mutated'][1][witness]
        restored = phases['restored'][1][witness]
        require(binding['obligation'] in baseline['requirements'], 'witness does not reference mapped obligation')
        require(changed['backend_conformance'] == 'FAIL' and baseline['backend_conformance'] == restored['backend_conformance'] == 'PASS', 'not a distinguishing witness')
        require(encode(baseline['observed_behavior']) == encode(restored['observed_behavior']), 'restored behavior differs')
        require(binding['positive_controls'] and witness not in binding['positive_controls'], 'no separate positive control')
        for positive in binding['positive_controls']:
            require(all(phases[p][1][positive]['backend_conformance'] == 'PASS' for p in phases), 'positive control failed')
        require(record.get('restored_sha256', record['original_sha256']) == record['original_sha256'], 'restored source digest')
        require(record.get('restored_pass', True) and record.get('restored_source_bytes', True), 'restoration not established')
        output = {'binding': binding['id'], 'obligation': binding['obligation'], 'guard': binding['guard'],
                  'classification': 'KILLED', 'evidence_level': 'ENFORCEMENT_DEMONSTRATED',
                  'witness': witness, 'positive_controls': binding['positive_controls'],
                  'source_sha256': sha(source), 'mutant_sha256': sha(mutant),
                  'source_restoration': descriptor.get('restoration_mode', 'Preserved pristine bytes and restored report match; same-copy restoration only where historical record states it.'),
                  'baseline_expected': baseline['expected_behavior'], 'mutated_observed': changed['observed_behavior'],
                  'limitation': binding['supported_claim'], 'evidence': descriptor}
        if 'original_matrix' in descriptor:
            old = self.reader.json(descriptor['original_matrix']['report'])
            require(old['exit_code'] == 0 and len(old['rows']) == 29 and
                    all(r['backend_conformance'] == 'PASS' for r in old['rows']), 'original matrix comparison mismatch')
            output['original_29_case_comparison'] = 'MUTATION_MISSED'
            shrink = self.reader.json(descriptor['minimized'])
            output['minimization'] = {k: shrink[k] for k in ('deletion_1_minimal', 'global_minimum_claimed')}
        return output

    def build(self, catalog, bindings):
        binding_map = {b['id']: b for b in bindings}
        require(len(binding_map) == len(bindings), 'duplicate binding')
        populations = []
        for population in catalog['populations']:
            records = self.reader.json(population['report'])
            for key in population['selector']:
                records = records[key]
            record_map = {r.get('id', r.get('guard')): r for r in records}
            require(len(record_map) == len(records) == len(population['mutations']), 'mutation population incomplete')
            results = []
            for desc in population['mutations']:
                try:
                    result = self.mutation(population, desc, record_map[desc['id']], binding_map[desc['binding']])
                except (ValueError, KeyError, TypeError, OSError) as exc:
                    result = {'binding': desc['binding'], 'classification': 'UNVERIFIABLE',
                              'evidence_level': 'UNVERIFIABLE', 'reason': str(exc)}
                results.append(result)
            populations.append({'id': population['id'], 'profile': population['profile'],
                                'source_commit': population['source_commit'],
                                'counts': dict(Counter(x['classification'] for x in results)), 'results': results})
        profiles = []
        for profile in catalog['profiles']:
            require(profile['independent_replay']['status'] == 'NOT_COVERED',
                    'independent reviewer evidence is not admitted by this v0 importer')
            obligations = self.reader.json(profile['obligations'])
            vectors = self.reader.json(profile['vectors'])
            suite = self.reader.json(profile['suite'])
            require(suite['vectors']['sha256'] == profile['vectors']['sha256'] and
                    suite['obligations']['sha256'] == profile['obligations']['sha256'], 'profile suite identity')
            fixtures = {v['name']: v for v in vectors['vectors']}
            require(fixtures and len(fixtures) == len(vectors['vectors']), 'empty/duplicate fixtures')
            rows, errors = {}, []
            for refs in profile['runs']:
                try:
                    report, local_rows, corpus = self.unit(refs)
                    require(not set(rows) & set(local_rows), 'duplicate execution')
                    for v in corpus['vectors']:
                        require(v['name'] in fixtures and encode(v) == encode(fixtures[v['name']]), 'run input/expectation differs from profile')
                    rows.update({name: {**row, 'report_ref': refs['report']} for name, row in local_rows.items()})
                except (ValueError, KeyError, TypeError, OSError) as exc:
                    errors.append(str(exc))
            matched = {name for name, row in rows.items() if row['backend_conformance'] == 'PASS'}
            case_outcomes = {name: {'expected': row['expected_behavior'], 'observed': row['observed_behavior'],
                                   'conformance': row['backend_conformance'], 'authorization': row['observed_behavior']['authorization'],
                                   'report_ref': row['report_ref']} for name, row in rows.items()}
            entries = []
            for oid, obligation in sorted(obligations.items()):
                referencing = sorted(v['name'] for v in fixtures.values() if oid in v['obligations'])
                executed = sorted(set(referencing) & set(rows))
                matches = sorted(set(referencing) & matched)
                enforcement = [m for p in populations if p['profile'] == profile['id'] for m in p['results']
                               if m.get('obligation') == oid and m['classification'] == 'KILLED']
                levels = ['DECLARED']
                if referencing: levels.append('REFERENCED_BY_TEST')
                if matches: levels.append('EXECUTED_AND_MATCHED')
                if enforcement: levels.append('ENFORCEMENT_DEMONSTRATED')
                if errors: levels.append('UNVERIFIABLE')
                entries.append({'id': oid, 'classification': obligation['kind'], 'declared_source_clause_or_policy': obligation,
                                'evidence_commit': profile['source_commit'], 'source_ids': profile['source_ids'],
                                'source_pin_and_clause': profile['traceability'][oid],
                                'fixture_ids': referencing, 'executed_fixture_ids': executed, 'matched_fixture_ids': matches,
                                'outcomes': executed, 'outcomes_resolve_to': 'profile.case_outcomes',
                                'evidence_levels': levels, 'highest_supported_level': levels[-1],
                                'positive_controls': sorted({v for m in enforcement for v in m['positive_controls']}),
                                'negative_or_distinguishing_witnesses': sorted({m['witness'] for m in enforcement}),
                                'physical_mutation_bindings': [m['binding'] for m in enforcement],
                                'enforcement_status': 'ENFORCEMENT_DEMONSTRATED' if enforcement else 'NOT_COVERED',
                                'independent_replay': profile['independent_replay'],
                                'limitations': profile['limitations'] + ['No one-to-one obligation/guard completeness assumption.']})
            profiles.append({'id': profile['id'], 'source_commit': profile['source_commit'],
                             'integrated_into_base': profile['integrated_into_base'], 'source_ids': profile['source_ids'],
                             'errors': errors, 'fixture_count': len(fixtures), 'executed_count': len(rows), 'matched_count': len(matched),
                             'obligations': entries, 'case_outcomes': case_outcomes,
                             'coverage_summary': dict(Counter(e['highest_supported_level'] for e in entries))})
        return {'schema': 'veca.obligation-evidence-report.v0', 'base': catalog['base'],
                'profiles': profiles, 'mutation_populations': populations, 'input_sha256': dict(sorted(self.reader.used.items())),
                'independent_replay': 'NOT_COVERED', 'new_backend_execution': False,
                'conformance_verdict': 'NOT_EVALUATED', 'authorization_credential': False,
                'complete': not any(p['errors'] for p in profiles) and
                            all(all(r['classification'] == 'KILLED' for r in p['results']) for p in populations)}


def check_claims(report, claims):
    """Untrusted coverage assertions cannot promote evidence, including independence."""
    known = {(p['id'], o['id']): o for p in report['profiles'] for o in p['obligations']}
    for claim in claims:
        row = known[(claim['profile'], claim['obligation'])]
        require(claim['level'] in row['evidence_levels'], 'unsupported claimed evidence level')
        require(set(claim.get('mutation_bindings', [])) <= set(row['physical_mutation_bindings']), 'unrelated claimed mutation')
    return True


def markdown(report):
    lines = ['# Evidence-based obligation checklist', '', 'Generated from hash-bound historical reports; no new backend execution or independent reviewer claim.', '',
             '| Profile / obligation | Classification | Referenced / executed / matched | Evidence level | Specific physical bindings |',
             '| --- | --- | --- | --- | --- |']
    for p in report['profiles']:
        for o in p['obligations']:
            counts = ' / '.join(str(len(o[k])) for k in ('fixture_ids', 'executed_fixture_ids', 'matched_fixture_ids'))
            lines.append('| '+p['id']+' / '+o['id']+' | '+o['classification']+' | '+counts+' | '+o['highest_supported_level']+' | '+', '.join(o['physical_mutation_bindings'])+' |')
    lines += ['', 'All independent replay statuses: NOT_COVERED. Author fresh-checkout and CI executions do not establish reviewer independence.',
              '', 'Full clauses, source pins, case outcomes, controls, limitations and evidence locators are in COVERAGE.json.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--claims', type=Path)
    args = parser.parse_args()
    from spec_drift_coverage.integrity import check
    check()
    report = Reporter().build(strict((CONFIG/'catalog.json').read_bytes()), strict((CONFIG/'guard-bindings.json').read_bytes())['bindings'])
    if args.claims:check_claims(report, strict(args.claims.read_bytes()))
    write(args.out/'COVERAGE.json', report)
    (args.out/'OBLIGATION_COVERAGE.md').write_bytes(markdown(report).encode())
    print(__import__('json').dumps({'complete': report['complete'], 'profiles': {p['id']: p['coverage_summary'] for p in report['profiles']}}))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
