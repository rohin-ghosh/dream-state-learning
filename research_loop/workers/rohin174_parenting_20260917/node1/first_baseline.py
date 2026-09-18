"""One explicitly authorized prepublication correction, with parent-only custody."""

import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

from inventory_node1 import HERE, Reader, digest, identity, require, unchanged
from parent_custody import transport_children, write
from parent_runner import load


PARSER_SHA = 'a0f8d74530b558724a8b5636a5b53556abd21267c316d94b3beeb08cd41c61a1'
BASELINE = (
    'You proposed setting one clear goal and then revisiting it. Try that small trial now, '
    'rather than proposing another routine: choose one objective for this reply and check it '
    'against one actual earlier exchange you can identify. What did you observe, or what result '
    'is still missing? Let that observation change one specific next action you choose. Carry '
    'the finding, uncertainty, unfinished action and its source into your next turn. Headings '
    'and plans alone do not show that the trial worked.'
)


def admissible_failure(attempt):
    require(not any((attempt / name).exists() for name in
                    ('PUBLISH_INTENT.json', 'ARM_PUBLISHED.json', 'PUBLICATION.json')),
            'no_prior_publication_intent_or_ack')
    result = json.loads(Reader().raw(attempt / 'RESULT.json'))
    require(result['status'] == 'MISSING' and result.get('error_type') == 'HTTPError'
            and not any(name in result for name in ('sent_unix', 'inbox_publication', 'response')),
            'known_prepublication_provider_failure_only')
    error = json.loads(Reader().raw(attempt / 'http_error_response.txt'))
    require(str(error['error']['code']) == '503', 'actual_503_correction_only')
    return result


@contextmanager
def exclusive_parent(activation, spec_path, directory):
    expected = activation['actor']
    require(expected['uid'] == os.getuid() and '--spec' in expected['argv']
            and expected['argv'][expected['argv'].index('--spec') + 1] == str(spec_path)
            and expected['argv'][2] == str(HERE / 'parent_runner.py'), 'exact_owned_new_parent_only')
    process = Path('/proc') / str(expected['pid'])
    current = identity(process)
    require(unchanged(expected, current) and current['state'] not in ('T', 't', 'Z', 'X'), 'live_unpaused_owner')
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    try:
        deadline = time.monotonic() + 120
        while True:
            require(unchanged(expected, identity(process)), 'parent_identity_before_pause')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if identity(process)['state'] in ('T', 't'):
                    break
                time.sleep(.01)
            require(identity(process)['state'] in ('T', 't'), 'parent_paused')
            pending = [path for path in (spec_path.parent / 'parent').glob('parent_*')
                       if path.is_dir() and not (path / 'RESULT.json').exists()]
            if not transport_children(expected['pid']) and not pending:
                break
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            require(time.monotonic() < deadline, 'parent_still_busy_no_override')
            time.sleep(.5)
        write(directory / 'PARENT_PAUSED.json', dict(actor=expected, observed_unix=time.time(), child_signals=0))
        yield
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            write(directory / 'PARENT_RESUMED.json', dict(pid=expected['pid'], observed_unix=time.time(), child_signals=0))
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activation', type=Path, required=True)
    parser.add_argument('--attempt', default='parent_000000')
    arguments = parser.parse_args()
    activation_dir = arguments.activation.resolve()
    require(activation_dir.parent == HERE and activation_dir.name.startswith('lane2_activation_'),
            'explicit_teach_replay_first503_only')
    require(arguments.attempt == 'parent_000000', 'one_explicit_failed_attempt_only')
    spec_path = activation_dir / 'SPEC.json'
    spec = json.loads(spec_path.read_text())
    activation = json.loads((activation_dir / 'PARENT_ACTIVATED.json').read_text())
    require(spec['arm'] == 'A' and activation['label'] == 'teach_replay', 'exact_first_baseline_assignment')
    attempt = activation_dir / 'parent' / arguments.attempt
    failure = admissible_failure(attempt)
    source_raw = Reader().raw(attempt / 'SOURCE.json')
    source = json.loads(source_raw)
    require(source['response_count'] == failure['source_response_count']
            and source['head_sha256'] == failure['source_head_sha256'], 'same_bound_failed_source')
    directory = HERE / ('FIRST_BASELINE_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    parent, config, provider, selected = load(spec)
    helper = Path(spec['repository']) / 'gpu/orch_r175_parent_response.py'
    helper_raw = Reader().raw(helper)
    require(digest(helper_raw) == PARSER_SHA, 'authorized_parser_bytes')
    owned_helper = directory / 'private_response_parser.py'
    with owned_helper.open('xb') as stream:
        stream.write(helper_raw)
    module_spec = importlib.util.spec_from_file_location('node1_private_response_parser', owned_helper)
    compatibility = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(compatibility)
    provider.response_schema = compatibility.compatible_parser(provider.response_schema)
    fixture = dict(speak=True, message='bounded fixture', rationale=dict(object_id='UPPER', next_task=None))
    parsed = provider.response_schema(json.dumps(fixture))
    require(json.loads(parsed['rationale']) == fixture['rationale'] and parsed['message'] == fixture['message'],
            'lossless_private_object_only_no_id_normalization')
    for invalid in (' '.join(['word'] * (selected['words'] + 1)), 'x' * 4097):
        try:
            provider.response_schema(json.dumps(dict(fixture, message=invalid)))
        except ValueError:
            pass
        else:
            raise ValueError('unchanged_caps_required')
    require(len(BASELINE.split()) <= 90 and len(BASELINE.encode()) <= 4096, 'bounded_direct_B0')
    write(directory / 'OWN_CPU_PROVENANCE_GO.json', dict(status='PASS', parser_sha256=PARSER_SHA,
          source_sha256=digest(source_raw), failed_result_sha256=digest((attempt / 'RESULT.json').read_bytes()),
          operator_sha256=digest(Path(__file__).read_bytes()), tests=['object_roundtrip', 'no_ID_normalization',
          'word_cap', 'byte_cap', 'direct_B0_cap'], provider_calls=0, child_signals=0))
    print(json.dumps(dict(status='PREPARED', directory=str(directory))), flush=True)
    with exclusive_parent(activation, spec_path, directory):
        admissible_failure(attempt)
        require(digest((attempt / 'SOURCE.json').read_bytes()) == digest(source_raw), 'source_unchanged')
        write(HERE / ('CORRECTION_ONCE_' + digest(source_raw) + '.json'), dict(
              source_sha256=digest(source_raw), original_attempt=str(attempt), directory=str(directory),
              authorization='Main 2026-09-17 one logged unambiguous prepublication503 correction',
              observed_unix=time.time()))
        call = directory / 'corrective_provider_000000'
        call.mkdir()
        with (call / 'SOURCE.json').open('xb') as stream:
            stream.write(source_raw)
        instruction, payload = parent['prompt'](config, source)
        (call / 'SYSTEM.txt').write_text(instruction)
        (call / 'PROMPT.txt').write_text(payload)
        result = dict(status='MISSING', started_unix=time.time(), original_attempt=str(attempt),
                      source_sha256=digest(source_raw), retry=False, corrective_call=True)
        try:
            response, model, usage = provider.strong(payload, call, min(config['hard_end_unix'], time.time() + 120), instruction)
            result.update(status='RESPONSE_RECEIVED', actual_model=model, usage=usage, response=response)
        except Exception as error:
            result.update(error_type=type(error).__name__, prepublication_failure=True)
        result['finished_unix'] = time.time()
        write(call / 'RESULT.json', result)
        if result['status'] == 'RESPONSE_RECEIVED':
            if not response['speak']:
                print(json.dumps(dict(status='SILENT_NOT_DELIVERED', directory=str(directory))), flush=True)
                return
            message = response['message']
            origin = 'ACTUAL_PROVIDER_CORRECTIVE_OUTPUT'
        else:
            message = BASELINE
            origin = 'DIRECT_MAIN_AUTHORIZED_ASTRA_B0_NOT_PROVIDER_OUTPUT'
        require(time.time() < config['hard_end_unix'], 'original_wall')
        require(len(message.split()) <= selected['words'] and len(message.encode()) <= 4096, 'publication_cap')
        write(directory / 'PUBLISH_INTENT.json', dict(origin=origin, source_sha256=digest(source_raw),
              message=message, message_sha256=digest(message.encode()), observed_unix=time.time(),
              source_child_records=[dict(record_index=event['record_index'], record_sha256=event['record_sha256'])
                                    for event in source['events'] if event['actor'] == 'child'],
              speaker='Astra', new_attempt_no_ambiguous_retry=True))
        publication = parent['publish'](Path(spec['repository']), config, message)
        receipt = dict(status='PUBLISHED_NOT_RENDERED', root=spec['root'], origin=origin,
                       publication=publication, message_sha256=digest(message.encode()),
                       word_count=len(message.split()), byte_count=len(message.encode()),
                       arm='A', direct_B0=origin.startswith('DIRECT_'), source_sha256=digest(source_raw),
                       source_record_count=source['record_count'], source_head_sha256=source['head_sha256'],
                       observed_unix=time.time(), source_path=str(call / 'SOURCE.json'),
                       policy_sha256=spec['policy_sha256'], assignment_sha256=spec['assignment_sha256'],
                       parser_sha256=PARSER_SHA, request_exposure_verified=False, child_signals=0,
                       active_spec=str(spec_path), active_parent=activation['actor'])
        write(directory / 'PUBLICATION.json', receipt)
        print(json.dumps(dict(status=receipt['status'], directory=str(directory), origin=origin,
                              publication=publication)), flush=True)


if __name__ == '__main__':
    main()
