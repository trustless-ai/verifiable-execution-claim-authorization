"""Exact, versioned PR11 documentation transition; never a blanket exception.

Historical Git inventories remain the source of the original identities. The
13-file supplemental payload is required as a whole for the integrated state.
This verifies preservation, not the truth of a historical execution claim.
"""
import hashlib
import json
from pathlib import Path
import subprocess

VERSION = 'veca-pr11-baseline-reconciliation-v1'
HARNESS = '0e17c97e896916b4d9505072cc9ebe2018329b01'
PILOT = '80c91a09095eca362dbfb69d39d0c01fc31130cf'
REVIEW = 'e5263f47325a81b0647f3de3a7bc36ad858aea5a'
MANIFESTS = {
    HARNESS: '8b8db7a4ca33d452f5c8695c78130dcc6b8ee1f8573545a7de12d5eff8b8d820',
    PILOT: '46f11963412be66b3b0602c2f2da93a706c516ce844eff0c71ef1472cbbb9719',
    REVIEW: '0c461c1296c1a5f11206eb904b76d1c4ad19ff7ab6d5fc353a2c62fd84f96c50',
}
DOCUMENTS = ('conformance/agent-harness-v0/README.md', 'research/harness-v0/LIMITATIONS.md')
BRIDGE = 'tools/erc8004/integrity.py'
# Exact reviewed preservation-checker integration, separate from PR11's docs.
# The old checker remains available at PILOT; no source lock is changed.
BRIDGE_SHA256 = '7a784a8188daef3e4b7a6501fd6574895b82d5729bdb9ef5541ecbdd6a2c54b7'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest(root, ref):
    if ref not in MANIFESTS:
        raise ValueError('unsupported historical baseline')
    raw = subprocess.check_output(['git', 'show', ref + ':artifacts.sha256.json'], cwd=root)
    if sha(raw) != MANIFESTS[ref]:
        raise ValueError('historical manifest identity mismatch')
    return json.loads(raw)['files']


def context(root, base):
    historical = manifest(root, base)
    original = manifest(root, HARNESS)
    reviewed = manifest(root, REVIEW)
    changes = {p for p in original if original[p] != reviewed.get(p)}
    payload = {p: reviewed[p] for p in reviewed.keys() - original.keys()}
    if changes != set(DOCUMENTS) or len(payload) != 13:
        raise ValueError('unexpected PR11 inventory transition')
    for path in DOCUMENTS:
        if historical.get(path) != original[path]:
            raise ValueError('unsupported document starting identity')
    return historical, original, reviewed, payload


def evaluate(historical, original, reviewed, payload, observed, inventory):
    """Pure hash comparison, also used for deterministic adversarial controls."""
    bad = []
    old_docs = all(observed.get(p) == original[p] for p in DOCUMENTS)
    new_docs = all(observed.get(p) == reviewed[p] for p in DOCUMENTS)
    mode = 'ORIGINAL_DOCUMENTS' if old_docs else 'PR11_DOCUMENTS' if new_docs else 'INVALID'
    if mode == 'INVALID':
        bad.append('document_transition')
    if old_docs and any(observed.get(p) is not None or p in inventory for p in payload):
        bad.append('partial_or_mixed_pr11_composition')
    expected = dict(historical)
    if new_docs:
        expected.update({p: reviewed[p] for p in DOCUMENTS})
        expected.update(payload)
    # This is an expressly versioned checker update, not an ERC/consumer change.
    expected[BRIDGE] = BRIDGE_SHA256
    for path, digest in sorted(expected.items()):
        if observed.get(path) != digest:
            bad.append('bytes:' + path)
        if inventory.get(path) != digest:
            bad.append('inventory:' + path)
    transitions = {p: {'historical_sha256': digest, 'required_sha256': expected[p]}
                   for p, digest in historical.items() if expected[p] != digest}
    return {'schema': VERSION, 'passed': not bad, 'document_state': mode,
            'historical_files': len(historical),
            'unchanged_baseline_files': sum(observed.get(p) == digest for p, digest in historical.items()),
            'reviewed_transitions': transitions, 'pr11_payload_files': len(payload) if new_docs else 0,
            'mismatches': sorted(bad), 'conformance_claim': False}


def check(root, base):
    root = Path(root)
    historical, original, reviewed, payload = context(root, base)
    paths = set(historical) | set(payload) | {BRIDGE}
    observed = {p: sha((root / p).read_bytes()) if (root / p).is_file() else None for p in paths}
    inventory = json.loads((root / 'artifacts.sha256.json').read_bytes())['files']
    result = evaluate(historical, original, reviewed, payload, observed, inventory)
    return {**result, 'historical_base': base, 'historical_inventory_sha256': MANIFESTS[base],
            'pr11_source': REVIEW, 'checker_sha256': BRIDGE_SHA256}
