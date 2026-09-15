"""Exact JSON framing repair and preserved-episode resume for one failed lane."""

from copy import deepcopy
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from organism_v6 import orch_route_parent_campaign as policy


MODE = 'FROZEN_C1_JSON_CLOSURE'


def close_rationale_quote(envelope):
    policy.require(envelope.get('type') == 'result' and not envelope.get('is_error')
        and envelope.get('num_turns') == 1 and envelope.get('stop_reason') == 'end_turn', 'complete_wire_envelope')
    models = envelope.get('modelUsage', {})
    policy.require('claude-sonnet-5[1m]' in models and models['claude-sonnet-5[1m]']['outputTokens'] < 1024,
        'observed_untruncated_sonnet')
    raw = envelope['result']
    try:
        json.loads(raw)
    except json.JSONDecodeError as error:
        policy.require(error.msg.startswith('Unterminated string') and raw[error.pos - 13:error.pos].strip().endswith('"rationale":'),
            'only_unclosed_final_rationale_string')
    else:
        raise ValueError('already_valid_not_a_repair')
    policy.require(raw.endswith('.}'), 'complete_sentence_final_brace')
    fixed = raw[:-1] + '"}'
    response = json.loads(fixed)
    policy.require(set(response) == {'speak', 'message', 'rationale'} and type(response['speak']) is bool
        and isinstance(response['message'], str) and isinstance(response['rationale'], str), 'exact_parent_schema')
    return response, dict(offset=len(raw) - 1, inserted='"', deleted_bytes=0, provider_calls=0,
        rationale_words_changed=False, message_words_changed=False)


def active():
    value = os.environ.get('ROUTE_PARENT_WIRE_RESUME')
    if value:
        policy.require(value == MODE, 'known_wire_repair_scope')
    return bool(value)


def history(root, arm, cycle, phase, output, identity):
    if not active() or cycle != 1 or phase != 'experience':
        return None
    from gpu import orch_route_parent_campaign_run as run

    policy.require(arm == 'FROZEN' and root.name == 'orch_route_parent_campaign_20260915_segment2', 'only_failed_frozen_life')
    plan = run.read(root / 'WIRE_RESUME_PLAN.json')
    archive = root / plan['archived_experience']
    policy.require(plan['archived_experience'] == 'FROZEN/cycle1/experience_original_wire_failure', 'fixed_archive_path')
    for name, expected in plan['files'].items():
        policy.require(run.sha(archive / name) == expected, 'preserved_history_hash')
    policy.require(run.read(archive / 'LOADED.json')['observed'] == identity.document(), 'same_loaded_child_history')
    for path in archive.glob('CALL_*.json'):
        shutil.copyfile(path, output / path.name)
    run.write(output / 'RESUME_PROVENANCE.json', dict(plan_sha256=run.sha(root / 'WIRE_RESUME_PLAN.json'),
        archived_experience=str(archive), model_calls_regenerated=0, original_child=identity.document(),
        scope='PRESERVE_SEVEN_EPISODES_SIX_REFLECTIONS_REPAIR_ONLY_FINAL_RATIONALE_QUOTE'))
    return dict(plan=plan, archive=archive)


def cached(history, name):
    if history is None:
        return None
    path = history['archive'] / name
    return json.loads(path.read_text()) if path.exists() else None


def advice(history, ordinal, payload):
    prior = cached(history, f'SLEEP_COACH_{ordinal:02d}.json')
    if prior is not None:
        return prior
    if history is not None and ordinal == history['plan']['repair_ordinal']:
        policy.require(policy.digest(policy.parent_payload(payload)) == history['plan']['payload_sha256'],
            'exact_original_failed_parent_payload')
        return deepcopy(history['plan']['response'])
    return None


def prepare(root):
    from gpu import orch_route_parent_campaign_run as run

    policy.require(root.name == 'orch_route_parent_campaign_20260915_segment2', 'only_existing_segment2')
    original = run.read(root / 'PREPARE.json')
    for name, expected in original['source_files'].items():
        policy.require(run.sha(root / 'source' / name) == expected, 'original_source_unchanged')
    for name, expected in original['inputs'].items():
        policy.require(run.sha(root / name) == expected, 'original_input_unchanged')
    identity = run.bridge.AdapterIdentity.from_document(original['initial']).verify()
    failed = root / 'FROZEN/cycle1/experience'
    failure = run.read(failed / 'FAILED.json')
    policy.require(failure['error'] == 'parent_provider_failed_no_substitute', 'exact_failed_boundary')
    process = failure['process']
    proc = Path(f'/proc/{process[1]}/stat')
    if proc.exists():
        current_start = int(proc.read_text().rsplit(')', 1)[1].split()[19])
        policy.require(current_start != process[2], 'failed_native_process_must_have_exited')
    raw = run.read(root / 'WIRE_PROVIDER_RAW.json')
    response, insertion = close_rationale_quote(raw)
    request = run.read(root / 'parent_queue/0026_FROZEN_C1.request.json')
    records = [run.read(path) for path in sorted(failed.glob('EPISODE_*.json'))]
    policy.require(len(records) == 7 and len(list(failed.glob('REFLECTION_*.json'))) == 6, 'exact_failure_progress')
    record = records[-1]
    telemetry = dict(cycle=1, experienced_episodes=6,
        algorithm='All sourced good/bad outcomes to own reflection; failed actions never gold.',
        recent_outcomes=[item['correct'] for item in records[:-1][-2:]])
    payload = dict(kind='coach', turn=6, task=deepcopy(record['task']),
        public_messages=policy.reflection_prefix(record), prior_parent_messages=record['parent_messages'], learner=telemetry)
    policy.require(policy.parent_payload(payload) == request['payload'], 'exact_original_resume_context')
    policy.require(run.read(failed / 'LOADED.json')['observed'] == identity.document(), 'same_original_child')
    run.admit(root, 2, root / 'WIRE_PREPARE_ADMISSION.json', run.read(root / 'START.json')['hard_deadline_unix'])
    archive = root / 'FROZEN/cycle1/experience_original_wire_failure'
    policy.require(not archive.exists(), 'never_overwrite_original_failure')
    failed.rename(archive)
    plan = dict(archived_experience=str(archive.relative_to(root)), repair_ordinal=7,
        files={path.name: run.sha(path) for path in archive.iterdir() if path.is_file()},
        payload_sha256=policy.digest(request['payload']), response=response, insertion=insertion,
        original_provider_raw_sha256=run.sha(root / 'WIRE_PROVIDER_RAW.json'),
        previous_experiences_regenerated=0, original_child=identity.document())
    run.write(root / 'WIRE_RESUME_PLAN.json', plan)
    prepared = deepcopy(original)
    prepared['original_prepare_sha256'] = run.sha(root / 'PREPARE.json')
    prepared['inputs'].update({name: run.sha(root / name) for name in ('WIRE_RESUME_PLAN.json', 'WIRE_PROVIDER_RAW.json')})
    prepared['source_files'] = {str(path.relative_to(run.TREE)): run.sha(path)
        for folder in ('gpu', 'organism_v6') for path in sorted((run.TREE / folder).iterdir())
        if path.is_file() and path.suffix in ('.py', '.sh')}
    run.write(root / 'PREPARE_WIRE_RESUME.json', prepared)
    print(json.dumps(dict(cpu_provenance_pass=True, plan_sha256=run.sha(root / 'WIRE_RESUME_PLAN.json'),
        prepare_sha256=run.sha(root / 'PREPARE_WIRE_RESUME.json'), original_deadline=run.read(root / 'START.json')['hard_deadline_unix'],
        restored_episodes=7, restored_reflections=6, new_provider_calls=0)))


def main():
    from gpu import orch_route_parent_campaign_run as run

    root = Path(os.environ['ROUTE_PARENT_CONFIG']).parent
    policy.activate(run.read(root / 'CONFIG.json'))
    run.ROOT = root
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare(root)
        return
    prepared = run.verify(root)
    publication = run.read(root / 'WIRE_PUBLICATION.json')
    policy.require(publication['own_cpu_tests_passed'] and publication['prepare_sha256'] ==
        run.sha(root / 'PREPARE_WIRE_RESUME.json'), 'wire_pre_gpu_gate')
    deadline = run.read(root / 'START.json')['hard_deadline_unix']
    run.write(root / 'REPAIR_ACTIVE.json', dict(mode=MODE, started_unix=time.time(),
        original_deadline=deadline, other_lanes_unchanged=True, original_prepare_sha256=prepared['original_prepare_sha256']))
    with (root / 'FROZEN_wire_resume_guardian.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_route_parent_campaign_run',
            '--phase', 'lane', '--arm', 'FROZEN', '--resume'], cwd=run.TREE, env=dict(os.environ,
            CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(run.TREE)), stdout=log, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True)
    run.write(root / 'WIRE_LAUNCH.json', dict(pid=child.pid, started_unix=time.time(), original_deadline=deadline))
    try:
        while child.poll() is None or not (root / 'TERMINAL.json').exists():
            policy.require(time.time() < deadline - 120, 'original_wire_resume_deadline')
            time.sleep(2)
        original = run.read(root / 'TERMINAL.json')
        codes = list(original['exit_codes'])
        codes[2] = child.returncode
        run.write(root / 'TERMINAL_REPAIR.json', dict(exit_codes=codes, original_exit_codes=original['exit_codes'],
            original_terminal_sha256=run.sha(root / 'TERMINAL.json'), finished_unix=time.time(),
            model_calls_regenerated=0, original_deadline=deadline))
    finally:
        if child.poll() is None:
            run.guardian.stop_owned(child)


if __name__ == '__main__':
    main()
