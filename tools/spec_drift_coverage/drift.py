"""Byte identity monitor. Drift is a review signal, never a conformance verdict."""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spec_drift_coverage.common import CONFIG, Reader, require, sha, strict, write

STATES = ('UNCHANGED', 'UPSTREAM_MOVED_CONTENT_UNCHANGED',
          'SOURCE_CHANGED_REVIEW_REQUIRED', 'SOURCE_MISSING', 'UNVERIFIABLE')


def fetch(url):
    """Public GitHub sources only; retain response bytes, never request credentials."""
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'VECA-spec-monitor-v0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            status, raw = response.status, response.read()
        error = None
    except urllib.error.HTTPError as exc:
        status, raw, error = exc.code, exc.read(), 'HTTP_ERROR'
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        status, raw, error = None, b'', type(exc).__name__
    return {'url': url, 'http_status': status, 'body_base64': base64.b64encode(raw).decode(),
            'body_sha256': sha(raw), 'error': error}


def urls(pin, commit=None):
    repo = pin['repository']
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo), 'invalid repository')
    if commit is None:
        return 'https://api.github.com/repos/' + repo + '/commits/' + urllib.parse.quote(pin['upstream_branch'], safe='')
    require(re.fullmatch(r'[0-9a-f]{40}', commit), 'invalid commit')
    return 'https://raw.githubusercontent.com/' + repo + '/' + commit + '/' + urllib.parse.quote(pin['path'], safe='/')


def response_bytes(response, expected_url):
    require(response['url'] == expected_url, 'response URL mismatch')
    raw = base64.b64decode(response['body_base64'], validate=True)
    require(sha(raw) == response['body_sha256'], 'response byte digest mismatch')
    return raw


def capture(pins, get=fetch):
    responses = {}
    for pin in pins:
        url = urls(pin)
        branch = responses.setdefault(url, get(url)) if url not in responses else responses[url]
        if branch['http_status'] != 200:
            continue
        try:
            commit = strict(response_bytes(branch, url))['sha']
            url = urls(pin, commit)
        except (ValueError, KeyError, TypeError):
            continue
        if url not in responses:
            responses[url] = get(url)
    return {'schema': 'veca.spec-source-capture.v0',
            'observed_at': datetime.now(timezone.utc).isoformat(),
            'evidence_source': 'GitHub public HTTPS API and exact-commit raw content',
            'responses': responses}


def compare(pin, snapshot, pinned_bytes):
    result = {'source_id': pin['id'], 'erc': pin['erc'], 'repository': pin['repository'],
              'path': pin['path'], 'pinned_commit': pin['commit'], 'pinned_file_sha256': pin['sha256'],
              'upstream_branch': pin['upstream_branch'], 'latest_observed_commit': None,
              'latest_file_sha256': None, 'comparison': 'UNVERIFIABLE',
              'observed_at': snapshot['observed_at'], 'evidence_source': snapshot['evidence_source'],
              'response_evidence': [], 'affected_profiles': pin['profiles'],
              'affected_obligations': pin.get('obligations', []),
              'review_required': False, 'implementation_failure_proven': False,
              'historical_execution_invalidated': False, 'pins_updated': False}
    try:
        require(sha(pinned_bytes) == pin['sha256'], 'pinned bytes mismatch')
        url = urls(pin)
        response = snapshot['responses'][url]
        raw = response_bytes(response, url)
        result['response_evidence'].append({'url': url, 'sha256': sha(raw), 'http_status': response['http_status']})
        require(response['http_status'] == 200, 'upstream ref unavailable')
        commit = strict(raw)['sha']
        url = urls(pin, commit)
        result['latest_observed_commit'] = commit
        response = snapshot['responses'][url]
        raw = response_bytes(response, url)
        result['response_evidence'].append({'url': url, 'sha256': sha(raw), 'http_status': response['http_status']})
        if response['http_status'] == 404:
            result['comparison'] = 'SOURCE_MISSING'
        else:
            require(response['http_status'] == 200, 'normative bytes unavailable')
            result['latest_file_sha256'] = sha(raw)
            if raw != pinned_bytes:
                result['comparison'] = 'SOURCE_CHANGED_REVIEW_REQUIRED'
            else:
                result['comparison'] = 'UNCHANGED' if commit == pin['commit'] else 'UPSTREAM_MOVED_CONTENT_UNCHANGED'
    except (ValueError, KeyError, TypeError) as exc:
        result['reason'] = str(exc)
    result['review_required'] = result['comparison'] in ('SOURCE_CHANGED_REVIEW_REQUIRED', 'SOURCE_MISSING', 'UNVERIFIABLE')
    return result


def report(pins, snapshot, reader=None):
    reader = reader or Reader()
    results = [compare(p, snapshot, reader.raw(p['bytes'])) for p in pins]
    return {'schema': 'veca.spec-drift-report.v0', 'results': results,
            'counts': dict(Counter(r['comparison'] for r in results)),
            'conformance_verdict': 'NOT_EVALUATED', 'authorization_verdict': 'NOT_EVALUATED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    from spec_drift_coverage.integrity import check
    check()
    pins = strict((CONFIG / 'sources.json').read_bytes())['sources']
    require(args.live != bool(args.snapshot), 'choose live or snapshot')
    snapshot = capture(pins) if args.live else strict(args.snapshot.read_bytes())
    output = report(pins, snapshot)
    write(args.out / 'SOURCE_CAPTURE.json', snapshot)
    write(args.out / 'SOURCE_DRIFT.json', output)
    print(__import__('json').dumps(output['counts'], sort_keys=True))
    # Review-required source changes are distinct from infrastructure uncertainty.
    return 2 if any(r['comparison'] in ('UNVERIFIABLE', 'SOURCE_MISSING') for r in output['results']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
