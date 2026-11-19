"""Authored transition oracle. Never imports the adapter or reads EVM observations."""
import copy
import hashlib
import json

POLICY = 'erc8004-registry-observation-v0'
PROFILE = 'erc8004-sequence-observation-v0'


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def role(op):
    return 'validation' if op['kind'] in ('request', 'respond') else 'identity'


class Model:
    def __init__(self, sequence):
        self.agents = {}
        self.operators = set()
        self.requests = {}
        self.keys = sorted({o['key'] for o in sequence if o['kind'] == 'metadata' and o['key'] != 'agentWallet'} |
                           {m['key'] for o in sequence for m in o.get('metadata', []) if m['key'] != 'agentWallet'})

    def allowed(self, actor, agent):
        return agent is not None and (actor == agent['owner'] or actor == agent['approved'] or
                                      (agent['owner'], actor) in self.operators)

    def snapshot(self):
        summaries = {}
        for aid in self.agents:
            values = [r['response'] for r in self.requests.values() if r['agent_id'] == int(aid) and r['responded']]
            summaries[aid] = {'count': len(values), 'average': sum(values) // len(values) if values else 0}
        return copy.deepcopy({'agents': self.agents, 'operators': sorted(f'{a}:{b}' for a, b in self.operators),
                              'requests': self.requests, 'summaries': summaries})

    def step(self, op):
        k, actor, aid = op['kind'], op['actor'], str(op['agent_id'])
        agent = self.agents.get(aid)
        allowed = self.allowed(actor, agent)
        events = []
        accepted = False
        if k == 'register':
            meta = op.get('metadata', [])
            accepted = all(m['key'] != 'agentWallet' for m in meta)
            if accepted:
                target = str(len(self.agents))
                values = {key: '0x' for key in self.keys}
                values.update({m['key']: m['value'] for m in meta})
                self.agents[target] = {'owner': actor, 'wallet': actor, 'approved': None,
                                       'uri': op['uri'] if op['overload'] else '', 'metadata': values}
                events = ['Transfer', 'Registered', 'MetadataSet'] + ['MetadataSet'] * len(meta)
        elif k == 'operator':
            accepted = op['operator'] is not None
            if accepted:
                pair = (actor, op['operator'])
                if op['enabled']: self.operators.add(pair)
                else: self.operators.discard(pair)
                events = ['ApprovalForAll']
        elif k == 'approve':
            accepted = agent is not None and (actor == agent['owner'] or (agent['owner'], actor) in self.operators)
            if accepted: agent['approved'] = op['operator']; events = ['Approval']
        elif k == 'uri':
            accepted = allowed
            if accepted: agent['uri'] = op['uri']; events = ['URIUpdated']
        elif k == 'metadata':
            accepted = allowed and op['key'] != 'agentWallet'
            if accepted: agent['metadata'][op['key']] = op['value']; events = ['MetadataSet']
        elif k == 'unset':
            accepted = allowed
            if accepted: agent['wallet'] = None; events = ['MetadataSet']
        elif k == 'wallet':
            accepted = (allowed and op['wallet'] is not None and 0 <= op['deadline_offset'] <= 300 and
                        op['signature_actor'] == op['wallet'] and op['signature_chain'] == 31337 and
                        op['signature_registry'] == 'identity' and op['signed_agent'] == op['agent_id'] and
                        op['signed_owner'] == agent['owner'])
            if accepted: agent['wallet'] = op['wallet']; events = ['MetadataSet']
        elif k == 'transfer':
            accepted = allowed and op['from'] == agent['owner'] and op['to'] is not None
            if accepted:
                agent.update(owner=op['to'], wallet=None, approved=None)
                events = ['MetadataSet', 'Transfer']
        elif k == 'request':
            accepted = allowed and op['validator'] is not None and op['label'] not in self.requests
            if accepted:
                self.requests[op['label']] = {'agent_id': int(aid), 'validator': op['validator'], 'response': 0,
                                              'responded': False, 'response_hash': '0x' + '00' * 32, 'tag': ''}
                events = ['ValidationRequest']
        elif k == 'respond':
            req = self.requests.get(op['label'])
            accepted = req is not None and actor == req['validator'] and 0 <= op['response'] <= 100
            if accepted:
                req.update(response=op['response'], responded=True, response_hash=op['response_hash'], tag=op['tag'])
                events = ['ValidationResponse']
        else:
            raise ValueError('operation outside oracle domain: ' + k)
        return {'status': 'ACCEPTED' if accepted else 'REJECTED', 'events': events, 'state': self.snapshot()}


def expected(inp):
    model = Model(inp['sequence'])
    steps = [model.step(op) for op in inp['sequence']]
    op, claim = inp['sequence'][-1], inp['claim']
    permitted_fields = {'type', 'policy', 'agent_id', 'operation', 'chain_id', 'registry_role'}
    bindings = {'type': 'LAB_REGISTRY_TRANSITION', 'policy': POLICY, 'agent_id': op['agent_id'],
                'operation': op['kind'], 'chain_id': 31337, 'registry_role': role(op)}
    # Separately authored policy oracle; does not import production authorize().
    if set(claim) != permitted_fields or claim != bindings:
        status = 'REFUTED'
    elif not inp.get('supply_receipt', True):
        status = 'UNVERIFIABLE'
    elif steps[-1]['status'] == 'REJECTED':
        status = 'REFUTED'
    else:
        status = 'VERIFIED'
    scope = {**claim, 'operation_sha256': hashlib.sha256(canon(op)).hexdigest()} if status == 'VERIFIED' else None
    return {'behavior': {'steps': steps}, 'authorization': {'status': status, 'authorized': status == 'VERIFIED', 'scope': scope}}
