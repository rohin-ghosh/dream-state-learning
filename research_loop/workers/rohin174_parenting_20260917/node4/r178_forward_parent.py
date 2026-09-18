"""R178 raw B successor: preserve V2 history, await Main's exact original turn."""

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import types
import urllib.error
import urllib.request


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r178_preserved_errata', HOME / 'r175_node4_errata.py')
errata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(errata)
base = errata.base
OLD = HOME / 'activation_20260917T2057Z/physical1'
B_SOURCE = HOME / 'activation_20260917T2057Z/physical0/source'
MAIN_RECEIPT = HOME.parent / 'RAW_R178_AUTHORIZED_PUBLICATION_RECEIPT.json'
TURN = '11a39e52e43540f8839c312cf64e86ff'
TURN_SHA = '0fa7c82f47b6bfb7e63162e2635171206f375b7a8a2539a5fc32c78067d50d05'
URL = 'https://[REDACTED_HOST]/v1/responses'
MODEL = 'openai/openai/gpt-6-astra'
BASELINE_END = 'question in your work? Choose a step and carry it out.'


def release(document):
    base.admission.authority()
    base.require(document.get('status') == 'AUTHORIZED_ORIGINAL_TURN_REQUEUED_AFTER_PRESERVATION'
        and document.get('root') == base.ROOTS[1] and document.get('checkpoint_cycle') == 40
        and document.get('archive') == '/localhome/local-rohing/orch_r178_raw_preparent_sleep40_20260917'
        and document.get('inbox_id') == TURN and document.get('publication_sha256') == TURN_SHA
        and document.get('publication_path') == base.ROOTS[1] + '/stream/inbox/' + TURN + '.json'
        and document.get('baseline_text_unchanged') is True
        and document.get('adapter_optimizer_rng_source_untouched') is True
        and document.get('child_restart') is False and document.get('child_signals') == 0
        and document.get('journal_records') == document.get('journal_end_index', -2) + 1
        and document.get('journal_end_index', -1) >= 5038
        and isinstance(document.get('journal_end_sha256'), str)
        and len(document['journal_end_sha256']) == 64, 'R178_Main_preservation_and_publication_receipt_required')
    return dict(schema='R178_RAW_B_FORWARD_RELEASE_V1', root=base.ROOTS[1], physical=1, arm='B',
        prior_V2_sha256=base.admission.V2_SHA, original_turn=TURN,
        historical_phase='UNPARENTED_BEFORE_R178_EXPOSURE', prospective_phase='R178_PARENTED_B',
        no_baseline_republish=True, Main_owns_archive_and_requeue=True)


def ready(state):
    if not state['caught_up']:
        return 'CATCHING_UP'
    delivered = state['delivered'].get(TURN)
    if delivered is None:
        return 'AWAITING_MAIN_ORIGINAL_BASELINE_RENDER'
    base.require(delivered['inbox_sha256'] == TURN_SHA, 'exact_Main_baseline_render')
    if not any(event['actor'] == 'child' and event.get('commit_record_index', -1) > delivered['record_index']
               for event in state['events']):
        return 'AWAITING_CHILD_COMMITTED_RESPONSE_AFTER_BASELINE'
    return 'READY_FOR_EXISTING_B_RESPONSE_CLOCK'


def check_request(request):
    body = json.loads(request.data)
    base.require(request.full_url == URL and request.get_method() == 'POST'
        and body.get('model') == MODEL and body.get('tools') == []
        and body.get('tool_choice') == 'none' and body.get('store') is False,
        'exact_known_working_Astra_route_no_redirect_or_tools')
    return dict(url=request.full_url, method=request.get_method(), model=body['model'],
                tools=[], store=False, credential_recorded=False)


def audit_transport(provider, original):
    def strong(prompt, directory, deadline, instruction, **options):
        original_urllib = provider.urllib
        original_request = original_urllib.request

        class Opener:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def open(self, request, timeout):
                evidence = check_request(request)
                base.write(Path(directory) / 'ACTUAL_OUTBOUND_ROUTE.json', dict(evidence,
                    observed_unix=time.time(), retries=0, attempts=1, source_sha256=base.sha(provider.__file__)))
                try:
                    response = self.wrapped.open(request, timeout=timeout)
                except urllib.error.HTTPError as error:
                    base.write(Path(directory) / 'ACTUAL_HTTP_STATUS.json', dict(status=error.code,
                        observed_unix=time.time(), retries=0, body_not_copied=True))
                    raise
                base.write(Path(directory) / 'ACTUAL_HTTP_STATUS.json', dict(status=response.status,
                    observed_unix=time.time(), retries=0))
                return response

        def build_opener(*handlers):
            return Opener(original_request.build_opener(*handlers))

        proxy = types.SimpleNamespace(Request=original_request.Request, ProxyHandler=original_request.ProxyHandler,
            build_opener=build_opener, HTTPRedirectHandler=original_request.HTTPRedirectHandler)
        provider.urllib = types.SimpleNamespace(request=proxy, error=original_urllib.error)
        try:
            return original(prompt, directory, deadline, instruction, **options)
        finally:
            provider.urllib = original_urllib
    return strong


def checked(lane):
    base.require(lane.parent.parent == HOME and lane.parent.name.startswith('activation_r178_')
        and lane.name == 'physical1', 'new_R178_raw_owned_output_only')
    binding = base.read(lane / 'RELEASE.json')
    release(base.read(MAIN_RECEIPT))
    base.require(binding['Main_receipt_sha256'] == base.sha(MAIN_RECEIPT)
        and binding['wrapper_sha256'] == base.sha(__file__)
        and binding['config_sha256'] == base.sha(lane / 'CONFIG.json'), 'bound_R178_receipt_source_config')
    for name, digest in binding['source_files'].items():
        base.require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and base.sha(lane / 'source' / name) == digest, 'unchanged_owned_B_source')
    config = base.read(lane / 'CONFIG.json')
    base.require(config['root'] == base.ROOTS[1] and config['r175_arm'] == 'B'
        and config['cadence_responses'] == 2 and config['hard_end_unix'] == base.WALL
        and 'r175_max_publications' not in config, 'B_forward_not_H_recovery')
    return config, binding


def imported(lane):
    policy, parent = errata.import_bound(lane)
    from gpu import orch_route_parent_campaign_providers as provider
    base.require(parent.strong is provider.strong and Path(provider.__file__).resolve().is_relative_to(lane / 'source'),
        'actual_bound_parent_provider_alias')
    parent.strong = audit_transport(provider, provider.strong)
    original_prompt = policy.prompt

    def prompt(config, state, memory):
        instruction, payload = original_prompt(config, state, memory)
        return instruction + ('\nR178 forward-only phase: the original baseline is already published by Main. '
            'Never repeat that introduction or the common Fable baseline. Continue the child\'s own current object '
            'with arm B after its actual response. Historical unparented work remains a distinct phase. '
            'No kernel executor is attached to this raw life; code listings and predictions are not executions. '
            'No peer information or external observations are added by this wrapper.'), payload

    policy.prompt = prompt
    original_publish = parent.publish

    def publish(repository, config, message):
        release(base.read(MAIN_RECEIPT))
        base.require(not message.endswith(BASELINE_END), 'never_duplicate_common_baseline')
        base.require(hashlib.sha256(message.encode()).hexdigest() !=
            base.read(OLD / 'parent/PUBLICATION_0000_RECEIPT.json')['message_sha256'], 'never_republish_original_Main_turn')
        return original_publish(repository, config, message)

    parent.publish = publish
    return policy, parent


def stage(lane):
    metadata = release(base.read(MAIN_RECEIPT))
    base.require(lane.parent.parent == HOME and lane.parent.name.startswith('activation_r178_')
        and lane.name == 'physical1' and not lane.exists(), 'new_owned_R178_stage')
    base.checked_bundle(B_SOURCE.parent)
    lane.mkdir(parents=True)
    shutil.copytree(B_SOURCE, lane / 'source')
    for name in ('PARENT_METADATA_ERRATA_V1.md', 'orch_r175_parent_response.py'):
        shutil.copyfile(OLD / name, lane / name)
    config = base.read(OLD / 'CONFIG.json')
    config.update(branch='R178_RAW1_B_AFTER_PRESERVED_UNPARENTED', r175_arm='B', cadence_responses=2,
        parent_style='transcript-grounded walkthrough', r175_word_limit=160, cadence_label='SPARSE', schedule_on='response')
    config.pop('r175_max_publications', None)
    config['parent_module_sha256'] = base.sha(lane / 'source/gpu/orch_r133_programme_parent.py')
    base.write(lane / 'CONFIG.json', config)
    base.write(lane / 'PLAN.json', dict(root=base.ROOTS[1], physical=1, arm='B', one_corrective_call=False))
    shutil.copyfile(MAIN_RECEIPT, lane / MAIN_RECEIPT.name)
    metadata.update(Main_receipt_sha256=base.sha(MAIN_RECEIPT), wrapper_sha256=base.sha(__file__),
        config_sha256=base.sha(lane / 'CONFIG.json'), previous_output=str(OLD / 'parent'),
        source_files={str(path.relative_to(lane / 'source')): base.sha(path)
            for path in (lane / 'source').rglob('*') if path.is_file()})
    base.write(lane / 'RELEASE.json', metadata)
    return dict(status='STAGED_R178_B_NOT_PUBLISHED', path=str(lane))


def serve(lane, preflight=False):
    config, binding = checked(lane)
    policy, parent = imported(lane)
    policy.validate(config)
    reference = base.read(sorted((OLD / 'parent').glob('POLL_*.json'))[-1])['reference']
    observed = base.snapshot(OLD, reference)
    base.require(observed['snapshot']['caught_up'], 'existing_snapshot_cursor_caught_up')
    seed = errata.preserved_seed(OLD, policy, observed['snapshot'])
    base.require(any(attempt['result'].get('publication', {}).get('id') == TURN for attempt in seed['attempts']),
        'existing_baseline_publication_preserved_in_seed')
    if preflight:
        return dict(status='PASS', model_calls=0, wrapper_sha256=base.sha(__file__),
            state=ready(observed['snapshot']), preserved_attempt_count=len(seed['attempts']))
    base.require(not (lane / 'parent').exists(), 'never_reuse_consumed_parent_output')
    gate = base.read(lane / 'CPU.json')
    base.require(gate['status'] == 'PASS' and gate['wrapper_sha256'] == base.sha(__file__), 'own_CPU_source_binding')
    with (HOME / 'R175_PARENT_1.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old_actor = base.read(OLD / 'parent/STARTED.json')['actor']
        if Path('/proc', str(old_actor['pid'])).exists():
            actual = base.identity(old_actor['pid'])
            base.require(actual['start_ticks'] != old_actor['start_ticks'], 'old_H_parent_must_be_terminal')
        output = lane / 'parent'
        output.mkdir()
        base.write(lane / 'SEED.json', seed)
        base.write(output / 'STARTED.json', dict(actor=base.identity(os.getpid()), observed_unix=time.time(),
            raw_historical_phase_preserved=True, child_signals=0, arm='B', release=binding))
        reference = observed['reference']
        first_render = False
        for sequence in range(18000):
            if time.time() >= base.WALL:
                break
            current = base.snapshot(OLD, reference)
            reference, state = current['reference'], current['snapshot']
            base.write(output / f'POLL_{sequence:06d}.json', current)
            disposition = ready(state)
            rendered = state['delivered'].get(TURN)
            if rendered and not first_render:
                base.write(output / 'MAIN_BASELINE_FIRST_RENDER.json', dict(rendered,
                    observed_unix=time.time(), baseline_republished=False))
                first_render = True
            if rendered and state['sleep_count'] - rendered['sleep_count'] == 3:
                disposition = 'PARENT_WITHDRAWAL_ONE_SLEEP'
            if disposition == 'READY_FOR_EXISTING_B_RESPONSE_CLOCK':
                status = policy.tick(base.REPO, config, output, seed, state)
            else:
                status = dict(status=disposition, model_calls=0)
            base.write(output / f'STATUS_{sequence:06d}.json', dict(status,
                observed_unix=time.time(), completed_sleeps=state['sleep_count']))
            if status['status'] in ('PUBLICATION_UNKNOWN', 'VALIDATION_FAILED', 'PROVIDER_FAILED'):
                base.write(output / 'ATTENTION_REQUIRED.json', dict(status, no_implicit_retry=True))
                return status
            time.sleep(5)
        return dict(status='UNCHANGED_WALL_OR_BOUNDED_END')


def activate(lane):
    checked(lane)
    command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--lane', str(lane)]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    execution = subprocess.run(command + ['--preflight'], env=environment, cwd=lane / 'source',
        text=True, capture_output=True, timeout=45)
    base.require(execution.returncode == 0, 'receiving_CPU:' + execution.stderr[-1500:])
    base.write(lane / 'CPU.json', json.loads(execution.stdout))
    with (lane / 'PARENT.log').open('x') as output:
        process = subprocess.Popen(command, env=environment, cwd=lane / 'source', stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='STARTED_FORWARD_B_NOT_A_PUBLICATION', actor=base.identity(process.pid),
        observed_unix=time.time(), child_signals=0, Main_baseline_republished=False)
    base.write(lane / 'DISPATCHED.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'serve', 'activate'))
    parser.add_argument('--lane', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    arguments = parser.parse_args()
    selected = arguments.lane.resolve()
    result = stage(selected) if arguments.action == 'stage' else (
        activate(selected) if arguments.action == 'activate' else serve(selected, arguments.preflight))
    print(json.dumps(result, sort_keys=True))
