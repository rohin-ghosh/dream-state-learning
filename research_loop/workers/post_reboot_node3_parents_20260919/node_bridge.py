"""Existing node-local caption mailboxes only; no native control operations."""

import fcntl
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
SOURCE = ROOT / 'r233_recovery_parents_v4'
CAPTIONS = tuple('r213_r226_caption_' + treatment + '_fork' for treatment in
    ('observation', 'perspective', 'revision', 'selfderive', 'unparented'))
PUBLISHERS = {
    'classroom': (1973233, 'classroom.py', 'R230_CURRICULUM_WRITER.lock'),
    'former_control': (1973234, 'caption_epoch.py', 'R233_FORMER_CONTROL_PARENT.lock'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def load_helpers():
    sys.path.insert(0, str(SOURCE))
    retirement = importlib.import_module('retirement')
    epoch = importlib.import_module('caption_epoch')
    adaptive = importlib.import_module('adaptive_parent')
    config = json.loads((ROOT / 'r233_caption_epoch_operator_v1/CONFIG_PRIVATE.json').read_bytes())
    helper, bindings = epoch.helpers(ROOT, config, recovering=True)
    return retirement, adaptive, helper, bindings


def exact_bindings(retirement, helper, bindings):
    result = {}
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for name in CAPTIONS:
        binding = bindings[name]
        process = retirement.identity(binding['native_pid'])
        guard = str(Path(binding['control']) / 'GUARD.json')
        if (not helper.alive(binding) or process['state'] in ('Z', 'X')
                or 'native' not in process['args'] or guard not in process['args']
                or Path(process['cwd']).resolve() != Path(binding['source']).resolve()):
            raise ValueError('exact_live_native_incarnation_required:' + name)
        result[name] = dict(binding, boot_id=boot_id,
            process={key: process[key] for key in ('pid', 'start_ticks', 'command_sha256')},
            active_sha256=retirement.sha(ROOT / name / 'ACTIVE_RUNTIME.json'),
            guard_sha256=retirement.sha(Path(guard)),
            plan_sha256=retirement.sha(Path(binding['control']) / 'PLAN.json'))
    return result


def publishers(retirement):
    result = {}
    for name, (pid, script, lock_name) in PUBLISHERS.items():
        process = retirement.identity(pid)
        if process['state'] in ('Z', 'X') or str(SOURCE / script) not in process['args']:
            raise ValueError('existing_node_local_publisher_required:' + name)
        with (ROOT / lock_name).open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise ValueError('existing_publisher_lock_not_held:' + name)
        result[name] = {key: process[key] for key in ('pid', 'start_ticks', 'command_sha256')}
    return result


def job_directory(relative, life):
    if life not in CAPTIONS:
        raise ValueError('caption_only_no_math_mailbox')
    expected = ('r233_all_five_caption_epochs_v1' if life == CAPTIONS[-1]
        else 'r233_classroom_handoff_v1/live')
    path = ROOT / relative
    if path.parent != ROOT / expected / life or not path.name.startswith('turn_'):
        raise ValueError('exact_existing_caption_mailbox_required')
    if path.resolve() != path:
        raise ValueError('mailbox_symlink_forbidden')
    return path


def act_chain(retirement, helper, life, publication, delivery):
    if not delivery.get('REQUEST'):
        return None
    expected = 'Astra: ' + publication['text']
    requests, responses = {}, {}
    for path, kind in helper.records(ROOT, life, delivery['REQUEST']['index'] - 1):
        if kind not in ('REQUEST', 'RESPONSE', 'R184_ACT'):
            continue
        value = retirement.record(path)
        document = value['document']
        reference = dict(index=value['index'], sha256=value['sha256'])
        if kind == 'REQUEST' and any(item.get('role') == 'user' and item.get('content') == expected
                for item in document['messages']):
            if not document['render_receipt']['all_history_tokens_masked']:
                raise ValueError('parent_history_must_be_masked')
            requests[digest({key: item for key, item in document.items() if key != 'resume_state'})] = reference
        elif kind == 'RESPONSE' and document['request_sha256'] in requests:
            responses[value['index']] = dict(RESPONSE=reference,
                ACT_REQUEST=requests[document['request_sha256']])
        elif kind == 'R184_ACT' and document['origin']['record_index'] in responses:
            response = responses[document['origin']['record_index']]
            if (document['origin']['kind'] != 'TRAIN_CHILD_RESPONSE'
                    or document['origin']['record_sha256'] != response['RESPONSE']['sha256']):
                raise ValueError('authenticated_ACT_response_required')
            return dict(ACT=reference, **response, parent_present_and_masked=True)
    return None


def receipt(retirement, adaptive, helper, life, relative, binding):
    directory = job_directory(relative, life)
    if not (directory / 'PUBLISHED.json').exists():
        return dict(life=life, state='PROVIDER_ACCEPTED_PUBLISHER_PENDING'
            if (directory / 'PROVIDER_RESULT.json').exists() else 'PROVIDER_PENDING_NOT_PUBLISHED')
    publication = json.loads((directory / 'PUBLISHED.json').read_bytes())
    prepared = json.loads((directory / 'PREPARED.json').read_bytes())
    result = json.loads((directory / 'PROVIDER_RESULT.json').read_bytes())
    if (retirement.sha(directory / 'PREPARED.json') != publication['prepared_sha256']
            or retirement.sha(Path(publication['path'])) != publication['sha256']
            or adaptive.message(result, retirement.sha(directory / 'PROVIDER_REQUEST.json')) != publication['text']
            or prepared['floor'] < binding['loaded']['index']):
        raise ValueError('current_incarnation_exact_provider_publication_required')
    delivery = helper.actual_delivery(ROOT, life, publication, prepared['floor'])
    chain = act_chain(retirement, helper, life, publication, delivery)
    return dict(life=life, parent_id=publication['id'], parent_sha256=publication['sha256'],
        published_utc=publication['published_utc'], provider_model=result['model'],
        provider_response_sha256=result['provider_response_sha256'], delivery=delivery,
        actual_ACT_after_parent=chain,
        state='ACT_CHAIN_VERIFIED' if chain else 'PARENT_DELIVERY_PENDING_ACT',
        task_uptake_established=False, caption_improvement_established=False,
        training_or_scientific_success_established=False)


def main(value):
    retirement, adaptive, helper, bindings = load_helpers()
    exact = exact_bindings(retirement, helper, bindings)
    writers = publishers(retirement)
    if value.get('bindings') is not None and exact != value['bindings']:
        raise ValueError('native_incarnation_changed_no_automatic_rebind')
    if value.get('publishers') is not None and writers != value['publishers']:
        raise ValueError('publisher_incarnation_changed_no_automatic_rebind')
    result = dict(observed_unix=time.time(), bindings=exact, publishers=writers,
        helper_sha256={filename: retirement.sha(SOURCE / filename) for filename in
            ('adaptive_parent.py', 'caption_epoch.py', 'classroom.py', 'retirement.py')},
        native_signals=0, native_restarts=0, learning_row_filter_changes=0,
        math_parent_changes=0)
    if value['mode'] == 'snapshot':
        result['jobs'] = []
        for job in adaptive.jobs(ROOT):
            life = job['request']['life']
            if life not in CAPTIONS:
                continue
            job_directory(job['relative'], life)
            result['jobs'].append(dict(job,
                current_observation=adaptive.own_observation(helper, ROOT, life)))
    elif value['mode'] == 'accept':
        life = value['life']
        directory = job_directory(value['relative'], life)
        if (directory / 'PROVIDER_RESULT.json').exists():
            existing = json.loads((directory / 'PROVIDER_RESULT.json').read_bytes())
            if existing != value['result']:
                raise ValueError('different_provider_result_already_present')
            result['accepted'] = dict(accepted=True, replay=True)
        else:
            result['accepted'] = adaptive.accept(ROOT, value)
    elif value['mode'] == 'receipts':
        result['receipts'] = [receipt(retirement, adaptive, helper, life, relative, exact[life])
            for life, relative in value['first_turns'].items()]
    else:
        raise ValueError('unsupported_caption_recovery_operation')
    return result


if __name__ == '__main__':
    print(json.dumps(main(json.load(sys.stdin))))
