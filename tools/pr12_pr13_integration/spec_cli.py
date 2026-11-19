"""Select the explicit integration contract, then unchanged PR13 semantic APIs."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pr12_pr13_integration.preservation import check
from spec_drift_coverage import coverage, drift
from spec_drift_coverage.common import CONFIG, strict, write, require


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('coverage', 'drift'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--claims', type=Path)
    args = parser.parse_args()
    check()
    if args.operation == 'coverage':
        report = coverage.Reporter().build(strict((CONFIG/'catalog.json').read_bytes()),
                                          strict((CONFIG/'guard-bindings.json').read_bytes())['bindings'])
        if args.claims:
            coverage.check_claims(report, strict(args.claims.read_bytes()))
        write(args.out/'COVERAGE.json', report)
        (args.out/'OBLIGATION_COVERAGE.md').write_bytes(coverage.markdown(report).encode())
        print(json.dumps({'complete': report['complete']}))
        return 0 if report['complete'] else 2
    require(args.live != bool(args.snapshot), 'choose live or snapshot')
    pins = strict((CONFIG/'sources.json').read_bytes())['sources']
    snapshot = drift.capture(pins) if args.live else strict(args.snapshot.read_bytes())
    report = drift.report(pins, snapshot)
    write(args.out/'SOURCE_CAPTURE.json', snapshot)
    write(args.out/'SOURCE_DRIFT.json', report)
    print(json.dumps(report['counts'], sort_keys=True))
    return 2 if any(row['comparison'] in ('UNVERIFIABLE', 'SOURCE_MISSING') for row in report['results']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
