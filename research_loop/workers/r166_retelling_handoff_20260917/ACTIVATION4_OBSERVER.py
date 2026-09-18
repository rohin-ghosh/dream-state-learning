import hashlib
import json
from pathlib import Path
import time

BASE = Path('/localhome/local-rohing')
remaining = 64 * 1024 * 1024
deadline = time.monotonic() + 1200
cache = {}
states = {agent: dict(cursor=None, previous=None, loaded=None, invocation=None,
    exposure=None, pending=None, committed=[], done=False) for agent in ('C1', 'C2', 'C4')}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def read(path):
    global remaining
    size = path.stat().st_size
    if size > min(remaining, 16 * 1024 * 1024):
        raise RuntimeError('observer_read_budget_exhausted')
    data = path.read_bytes()
    remaining -= len(data)
    return json.loads(data), dict(path=str(path), sha256=hashlib.sha256(data).hexdigest())


def fixed(path):
    if str(path) not in cache:
        cache[str(path)] = read(path)
    return cache[str(path)]


def identity(pid):
    global remaining
    proc = Path('/proc') / str(pid)
    try:
        stat = (proc / 'stat').read_bytes()
        argv = (proc / 'cmdline').read_bytes()
        cgroup = (proc / 'cgroup').read_bytes()
        remaining -= len(stat) + len(argv) + len(cgroup)
        assert remaining >= 0
        fields = stat.decode().rsplit(')', 1)[1].split()
        return dict(pid=pid, start_ticks=fields[19], state=fields[0], parent=int(fields[1]),
            group=int(fields[2]), uid=proc.stat().st_uid, cwd=str((proc / 'cwd').resolve()),
            argv=argv.rstrip(b'\0').decode().split('\0'), cgroup=cgroup.decode().strip())
    except FileNotFoundError:
        return None


def observe(agent, state):
    root = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation4')
    result = dict(agent=agent, observed_unix=time.time(), root=str(root), files={})
    values = {}
    for name in ('MAIN_DISPATCH.json', 'ACTUAL_BOUNDARY_READY.json', 'TERMINATION_INTENT.json',
                 'OWNER_RETIRED.json', 'ACTIVATION_FAILED.json', 'control/SAVED_PROOF.json',
                 'control/PREPARED.json', 'control/EFFECTIVE_POLICY.json', 'attempt/ADMISSION_TIME.json',
                 'attempt/LAUNCH.json', 'attempt/CONTAINMENT_VERIFIED.json', 'attempt/FAILED.json',
                 'attempt/NATIVE_EXIT.json', 'attempt/SERVICE_EXIT.json'):
        path = root / name
        if path.exists():
            value, reference = fixed(path)
            values[name] = value
            result['files'][name] = reference
            if name in ('ACTIVATION_FAILED.json', 'attempt/FAILED.json', 'attempt/NATIVE_EXIT.json',
                        'attempt/SERVICE_EXIT.json'):
                result.setdefault('failures', {})[name] = value
    dispatch = values['MAIN_DISPATCH.json']
    result['operator'] = identity(dispatch['pid'])
    if result['operator']:
        assert result['operator']['start_ticks'] == dispatch['start_ticks']
    request, unused = fixed(root / 'REQUEST.json')
    result['originals'] = {role: identity(item['pid']) for role, item in request['pair'].items()}
    for role, actual in result['originals'].items():
        if actual:
            assert actual['start_ticks'] == request['pair'][role]['start_ticks']
    actual = values.get('ACTUAL_BOUNDARY_READY.json')
    if actual:
        boundary = Path(actual['boundary']['path'])
        if state['cursor'] is None:
            prior, reference = fixed(boundary)
            assert reference['sha256'] == actual['boundary']['sha256']
            state['cursor'] = prior['index'] + 1
            state['previous'] = prior['sha256']
            result['saved_boundary'] = dict(reference=reference, index=prior['index'])
        policy = values['control/EFFECTIVE_POLICY.json']
        invitation = policy['invitation']
        assert hashlib.sha256(invitation.encode()).hexdigest() == policy['invitation_sha256']
        for unused_index in range(32):
            index = state['cursor']
            path = boundary.parent / ('%020d.json' % index)
            if not path.exists():
                break
            record, reference = read(path)
            assert record['index'] == index and record['previous_sha256'] == state['previous']
            assert record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
            intent, intent_ref = read(path.with_name(path.stem + '.intent.json'))
            assert intent['index'] == index and intent['record_sha256'] == record['sha256']
            assert intent['previous_sha256'] == state['previous']
            kind, document = record['kind'], record['document']
            state['previous'] = record['sha256']
            state['cursor'] += 1
            state['last_kind'] = kind
            if kind == 'LOADED':
                proof = values['control/SAVED_PROOF.json']
                launch = values['attempt/LAUNCH.json']
                config, config_ref = fixed(root / 'control/GUARD.json')
                plan, plan_ref = fixed(Path(config['plan_path']))
                native = identity(document['pid'])
                assert native and native['state'] not in ('T', 't', 'Z', 'X')
                timer = identity(native['parent'])
                assert timer and timer['pid'] == launch['pid']
                assert timer['start_ticks'] == launch['parent_start_ticks']
                assert native['group'] == timer['group'] == timer['pid']
                assert native['argv'] == [str(BASE / 'v2/venv/bin/python'), '-B', '-m',
                    'gpu.orch_r125_continual_guard', 'native', '--config', str(root / 'control/GUARD.json')]
                assert native['cwd'] == str(root / 'source') and native['uid'] == 2524
                assert native['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service'
                assert document['resume'] is True and document['optimizer_steps'] == proof['optimizer_steps']
                assert document['adapter_sha256'] == proof['adapter_state_sha256']
                assert config['resume'] is True and launch['guard_sha256'] == config_ref['sha256']
                assert launch['plan_sha256'] == plan_ref['sha256']
                assert plan['hard_end_unix'] == config['hard_end_unix'] == launch['hard_end_unix'] == 1789776000
                state['loaded'] = dict(record=reference, intent=intent_ref, index=index, document=document,
                    native=native, timer=timer, config=config_ref, plan=plan_ref,
                    saved_proof=result['files']['control/SAVED_PROOF.json'], continuity_verified=True)
            elif kind == 'PRESLEEP_RETELLING_INVITATION':
                assert document['invitation_sha256'] == policy['invitation_sha256']
                assert document['scope']['root'] == str(boundary.parent.parent.parent)
                state['invocation'] = dict(record=reference, index=index, cycle=document['cycle'],
                    invitation_sha256=document['invitation_sha256'])
            elif kind == 'REQUEST':
                payload = {key: value for key, value in document.items() if key != 'resume_state'}
                request_sha = digest(payload)
                assert document['split'] == 'TRAIN'
                assert document['resume_state']['state']['pending'] == request_sha
                state['pending'] = dict(request=payload, request_sha=request_sha, reference=reference, index=index)
                if state['invocation']:
                    spans = []
                    for message_index, message in enumerate(document['messages']):
                        content = message.get('content')
                        if isinstance(content, str) and invitation in content:
                            start = content.index(invitation)
                            spans.append(dict(message_index=message_index, role=message['role'], start=start,
                                end=start + len(invitation), content_sha256=hashlib.sha256(content.encode()).hexdigest()))
                    if spans:
                        assert document['render_receipt']['all_history_tokens_masked'] is True
                        state['exposure'] = dict(record=reference, index=index, request_sha256=request_sha,
                            segment=document['segment'], started_unix=document['started_unix'], spans=spans,
                            all_history_tokens_masked=True, semantic_adoption='NOT_ADJUDICATED')
            elif kind == 'RESPONSE':
                pending = state['pending']
                assert pending and document['request_sha256'] == pending['request_sha']
                pending.update(response=document, response_ref=reference, response_index=index)
            elif kind == 'COMMITTED':
                pending = state['pending']
                assert pending and 'response' in pending
                response = pending['response']
                response_sha = digest(response)
                assert document['source_sha256'] == response_sha
                saved_state = document['state']
                assert saved_state['sha256'] == digest(saved_state['state'])
                row = saved_state['state']['rows'][-1]
                assert row['source_sha256'] == response_sha and row['actor'] == 'child' and row['split'] == 'TRAIN'
                assert row['prefix'] == pending['request']['messages'] and row['target'] == response['response']['raw']
                assert row['token_ids'] == response['response']['token_ids']
                assert row['prefix_loss'] is False and row['target_loss'] is True
                state['committed'].append(dict(request=pending['reference'], response=pending['response_ref'],
                    committed=reference, request_index=pending['index'], response_index=pending['response_index'],
                    index=index, segment=row['segment'], terminal=row['terminal'], truncated=row['truncated'],
                    token_count=len(row['token_ids']), target_sha256=hashlib.sha256(row['target'].encode()).hexdigest()))
                state['pending'] = None
            if state['loaded'] and state['exposure']:
                state['done'] = True
                break
    result.update({key: state.get(key) for key in ('loaded', 'invocation', 'exposure', 'committed', 'last_kind')})
    result['last_record_index'] = state['cursor'] - 1 if state['cursor'] else None
    if state['loaded']:
        result['current_native'] = identity(state['loaded']['native']['pid'])
        assert result['current_native'] and result['current_native']['start_ticks'] == state['loaded']['native']['start_ticks']
    if result.get('failures') or result['operator'] is None:
        state['done'] = True
    result.update(remaining_read_bytes=remaining, no_signals=True, no_parent_action=True, no_retry=True)
    return result


while True:
    for agent, state in states.items():
        if state['done']:
            continue
        try:
            result = observe(agent, state)
        except Exception as error:
            state['done'] = True
            result = dict(agent=agent, observed_unix=time.time(), observer_error=type(error).__name__,
                reason=str(error), no_retry=True)
        print(json.dumps(result, sort_keys=True), flush=True)
    if all(state['done'] for state in states.values()) or time.monotonic() >= deadline:
        break
    time.sleep(min(15, max(0, deadline - time.monotonic())))
