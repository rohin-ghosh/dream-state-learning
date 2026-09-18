"""Finite NODE2 parent delivery using the existing operator's inbox transport."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ARMS = ('math_d1', 'repo_c1', 'creative_d1', 'math_transfer_c1')
OBJECTS = {
    'math_d1': 'a fresh mathematical conjecture and one real confined sandbox check',
    'repo_c1': 'one concrete question about the visible repository and an actual read_file result',
    'creative_d1': 'a new short creative scene and one deliberate revision',
    'math_transfer_c1': 'a fresh divisibility conjecture and a real confined sandbox check',
}


def read(path):
    return json.loads(path.read_bytes())


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)


def verified(path):
    if path.is_symlink() or path.stat().st_size > 32 * 1024 ** 2:
        raise ValueError('bounded_regular_record_required')
    record = read(path)
    if digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']:
        raise ValueError('record_hash_mismatch')
    return record


def metadata(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        tail = stream.read()
    marker = tail.rfind(b',"index":')
    if marker < 0:
        raise ValueError('existing_operator_record_layout')
    return json.loads(b'{' + tail[marker + 1:])


def identity(arm):
    bound = read(HERE / 'BEFORE_CURRENT.json')['arms'][arm]
    hashes = read(HERE / 'BEFORE_STATE.json')['arms'][arm]
    root = Path(bound['current_control']).parent.parent
    receiver = root / 'r210_filter_saved_boundary_20260918_v3'
    if (receiver / 'DISPATCHED.json').exists():
        ready = read(receiver / 'READY.json')
        control = receiver / 'control'
        guard = read(control / 'GUARD.json')
        if file_sha(control / 'GUARD.json') != ready['new_guard_sha256']:
            raise ValueError('receiving_guard_changed')
        if file_sha(control / 'PLAN.json') != guard['plan_sha256']:
            raise ValueError('receiving_plan_changed')
        plan = read(control / 'PLAN.json')
        loaded = next((verified(path) for path, meta in reversed(recent(root, 700))
                       if meta['kind'] == 'LOADED'), None)
        if loaded is None:
            raise ValueError('receiving_LOADED_not_yet_observed')
        process = Path('/proc') / str(loaded['document']['pid'])
        arguments = (process / 'cmdline').read_bytes().decode().split('\0')
        if str(control / 'GUARD.json') not in arguments:
            raise ValueError('receiving_LOADED_not_current_control')
        fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        bound = dict(bound, current_control=str(control), source_root=plan['source_root'],
                     native=dict(pid=loaded['document']['pid'], start_ticks=fields[19], state=fields[0],
                                 loaded_index=loaded['index'], loaded_sha256=loaded['sha256'],
                                 alive=fields[0] not in ('Z', 'X'), guard_matches=True,
                                 cwd=os.readlink(process / 'cwd')))
        hashes = dict(plan_sha256=guard['plan_sha256'], guard_sha256=ready['new_guard_sha256'])
    actor = bound['native']
    process = Path('/proc') / str(actor['pid'])
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    arguments = (process / 'cmdline').read_bytes().decode().split('\0')
    control = Path(bound['current_control'])
    if (process.stat().st_uid != os.getuid() or fields[19] != actor['start_ticks']
            or fields[0] in ('Z', 'X') or str(control / 'GUARD.json') not in arguments
            or 'native' not in arguments or 'gpu.orch_r125_continual_guard' not in arguments
            or os.readlink(process / 'cwd') != bound['source_root']
            or file_sha(control / 'PLAN.json') != hashes['plan_sha256']
            or file_sha(control / 'GUARD.json') != hashes['guard_sha256']):
        raise ValueError('owned_native_identity_or_control_changed')
    bound = dict(bound, native=dict(actor, state=fields[0], start_ticks=fields[19],
                                   uid=process.stat().st_uid, alive=True, observed_unix=time.time()))
    return bound, control.parent.parent


def recent(root, count=400):
    return [(path, metadata(path)) for path in sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))[-count:]]


def preserve(root, complete, destination):
    checkpoint = root / 'raw/checkpoints' / f'sleep_{complete["document"]["cycle"]:06d}'
    commit = read(checkpoint / 'COMMIT.json')
    if commit != complete['document']['checkpoint']:
        raise ValueError('checkpoint_commit_not_bound_to_complete')
    expected = {f'adapter/{name}': value for name, value in commit['adapter_files'].items()}
    expected['optimizer_rng.pt'] = commit['checkpoint_sha256']['optimizer']
    before = {name: file_sha(checkpoint / name) for name in expected}
    if before != expected:
        raise ValueError('checkpoint_files_mismatch')
    subprocess.run(['cp', '-a', '--reflink=auto', str(checkpoint), str(destination)], check=True, timeout=60)
    if {name: file_sha(destination / name) for name in expected} != expected:
        raise ValueError('preserved_checkpoint_mismatch')
    return dict(path=str(destination), cycle=complete['document']['cycle'],
                complete_index=complete['index'], complete_sha256=complete['sha256'],
                files=expected, commit_sha256=file_sha(destination / 'COMMIT.json'))


def first_text(arm):
    return ('Astra here, operator-authored guidance, not a message from Rohin. We are now in the R210 '
            'parented enrichment phase, separate from the preserved earlier withdrawn comparison. '
            'Your carried state still lists V. Let us settle this with at most two short prose turns, '
            'not another Python syntax loop. The fourth-power sum formula is S_n = '
            'n*(n+1)*(2*n+1)*(3*n*n + V*n - 1)/30. At n=3, the direct sum is '
            '1^4 + 2^4 + 3^4 = 1 + 16 + 81; the formula is 84*(26 + 3*V)/30. '
            'The number 14 is the sum of squares, not this sum. In plain English, give V and '
            'substitute it back to check both sides. Do not claim a tool ran. Then move to '
            + OBJECTS[arm] + '. My supplied words remain external context, not your own result. '
            'Please use ordinary English prose; retain raw prior attempts without rewriting history.')


def publish(arm, number, text):
    bound, root = identity(arm)
    output = HERE / arm
    output.mkdir(exist_ok=True)
    destination = output / f'PARENT_{number}.json'
    if destination.exists():
        raise ValueError('publication_already_recorded_no_duplicate')
    if (output / f'INTENT_{number}.json').exists():
        raise ValueError('publication_intent_exists_inspect_before_retry')
    rows = recent(root)
    write(output / f'INTENT_{number}.json', dict(arm=arm, text=text, native=bound['native'],
        current_control=bound['current_control'], head=rows[-1][1], created_unix=time.time()))
    sys.path.insert(0, bound['source_root'])
    from gpu.orch_r127_pilot_console import publish_parent
    identity(arm)
    publication = publish_parent(root / 'raw', 'Astra', text)
    receipt = dict(arm=arm, phase='R210_PARENTED_ENRICHMENT_NOT_UNPARENTED_COMPARISON',
        number=number, text=text, publication=publication, published_unix=time.time(),
        native=bound['native'], floor=rows[-1][1]['index'], real_render_verified=False)
    write(destination, receipt)
    return receipt


def begin(arm):
    bound, root = identity(arm)
    output = HERE / arm
    output.mkdir(exist_ok=True)
    rows = recent(root, 1200)
    complete_path = next(path for path, meta in reversed(rows) if meta['kind'] == 'SLEEP_COMPLETE')
    complete = verified(complete_path)
    prior = root / 'r209_parent_reattachment_20260918'
    prior_publications = [read(path) for path in sorted(prior.glob('PUBLICATION_*.json'))]
    prior_time = min((item['published_unix'] for item in prior_publications), default=None)
    last_withdrawn = next((verified(path) for path, meta in reversed(rows)
                          if meta['kind'] == 'SLEEP_COMPLETE'
                          and (prior_time is None or path.stat().st_mtime < prior_time)), None)
    preserved = preserve(root, complete, output / 'checkpoint_before_R210')
    withdrawn_preserved = preserved
    if last_withdrawn and last_withdrawn['index'] != complete['index']:
        withdrawn_preserved = preserve(root, last_withdrawn, output / 'checkpoint_before_R209_parent')
    write(output / 'PHASE_END.json', dict(arm=arm, observed_unix=time.time(), native=bound['native'],
        prior_withdrawal_ended_by='R209_FIRST_PARENT_PUBLICATION' if prior_time else 'R210_FIRST_PARENT_PUBLICATION_PENDING',
        prior_parent_first_published_unix=prior_time, earlier_parent_count=len(prior_publications),
        checkpoint_before_R210=preserved, checkpoint_before_parent_reattachment=withdrawn_preserved,
        withdrawn_boundary_found=last_withdrawn is not None, immutable_raw_retained=True,
        post_parent_data_not_unparented_comparison=True, checkpoint_not_atomic_live_sidecar_snapshot=True))
    return publish(arm, 1, first_text(arm))


def verify(arm):
    bound, root = identity(arm)
    rows = recent(root, 500)
    result = dict(arm=arm, observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  native=bound['native'], publications=[])
    for receipt_path in sorted((HERE / arm).glob('PARENT_*.json')):
        publication = read(receipt_path)
        proof = dict(number=publication['number'], id=publication['publication']['id'], rendered=False)
        for path, meta in rows:
            if meta['index'] <= publication['floor'] or meta['kind'] != 'REQUEST':
                continue
            request = verified(path)
            document = request['document']
            request_digest = digest({key: value for key, value in document.items() if key != 'resume_state'})
            if not any(message.get('content') == 'Astra: ' + publication['text']
                       for message in document['messages']):
                continue
            proof.update(rendered=True, request_index=request['index'], request_sha256=request['sha256'],
                         request_document_sha256=request_digest,
                         started_unix=document['started_unix'], segment=document['segment'],
                         all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked'])
            responses = []
            for candidate, candidate_meta in rows:
                if candidate_meta['kind'] != 'RESPONSE' or candidate_meta['index'] <= request['index']:
                    continue
                response = verified(candidate)
                if (response['document']['request_sha256'] == request_digest
                        and response['index'] == request['index'] + 1
                        and response['previous_sha256'] == request['sha256']):
                    responses.append(dict(index=response['index'], sha256=response['sha256'],
                        finished_unix=response['document']['finished_unix'],
                        raw=response['document']['response']['raw']))
                    break
            proof['responses'] = responses
            break
        result['publications'].append(proof)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['begin', 'publish', 'verify'])
    parser.add_argument('--arm', choices=ARMS, required=True)
    parser.add_argument('--number', type=int)
    parser.add_argument('--text-file', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if args.mode == 'begin':
        result = begin(args.arm)
    elif args.mode == 'publish':
        result = publish(args.arm, args.number, args.text_file.read_text())
    else:
        result = verify(args.arm)
    print(json.dumps(result))
