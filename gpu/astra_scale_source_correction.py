"""Bounded public-receipt correction candidates, never replacement COLLECTIONs.

Prepare reads all eight original exposes and the portable actor locally without
loading a model. Correction requires that preparation and preserves every reply.
"""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import astra_goal_scale_collection as original


source = original.source
portable = original.portable
scale = original.scale
hop = original.breadth.goal.hop
require = source.require
SCHEMA = 'DEV_SCALE_SOURCE_CORRECTION_V1'
SOURCE_COMMIT = 'ff1af2c37003fd4f6d38ecbe7660fd94744c0e31'
PARENT_STATE = original.PARENT_STATE
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_scale_source_correction_protocol.md'
PROTOCOL_SHA = 'e6f4beca65fd3938cf6157c339117e6e8401ecc7623d257d53c6cc7aa47fd934'
FEEDBACK = ('Recorded EVENT identifiers do not exactly match the observed receipt. '
            'Recheck all identifiers and output one correct EVENT line, no other text.\n')
MAX_CALLS = 8
MAX_ATTEMPTS = 2
MAX_NEW_TOKENS = 160
MAX_SECONDS = 900
CLAIM = 'EXTERNALLY_TRIGGERED_PUBLIC_VALIDATION_NOT_AUTONOMOUS_CORRECTION_OR_REPAIR_PROMOTION'


def shard_root(path):
    path = Path(path)
    return (path.parent if path.name == 'expose' else path).resolve()


def select_records(exposure, inputs, root, result_sha):
    selected, failures, offset = [], [], 0
    for collection_index, collection in enumerate(exposure['collections']):
        split = 'TRAIN' if collection['master'] in scale.runtime(inputs['shard'])['TRAIN_MASTERS'] else 'PROBE'
        for record_index, record in enumerate(collection['records']):
            if record['accepted']:
                continue
            event = next((capture for capture in collection['captures']
                          if capture['record_index'] == record_index and capture['phase'] == 'event'), None)
            response = record['event']
            eligible = (record['transition'] is not None and event is not None and event['error'] is None
                        and type(response) is dict and type(response.get('raw')) is str
                        and response.get('terminal') is True and response.get('truncated') is False)
            failures.append(dict(shard=inputs['shard'], master=collection['master'], split=split,
                                 record_index=record_index, eligible=eligible, error=deepcopy(record['error'])))
            if not eligible:
                continue
            receipt = hop.micro.RECEIPT_WIRE.format(**record['transition'])
            require(event['messages'][-1]['content'].startswith(receipt), 'original_public_receipt_required')
            native_index = offset + event['call_index']
            reference = dict(shard=inputs['shard'], master=collection['master'], split=split,
                record_index=record_index, collection_index=collection_index,
                expose=str(root / 'expose'), result_sha256=result_sha,
                collection_sha256=collection['collection_sha256'],
                collection_file_sha256=source.file_hash(root / 'expose' / f'COLLECTION_{collection_index:02d}.json'),
                local_call_index=event['call_index'], native_call_index=native_index,
                native_call_sha256=source.file_hash(root / 'expose' / f'CALL_{native_index:03d}.json'))
            selected.append(dict(source=reference, original_record=deepcopy(record),
                original_event_capture=deepcopy(event), public_receipt=receipt))
        offset += len(collection['captures'])
    return selected, failures


def load_inputs(options):
    protocol = Path(__file__).resolve().parents[1] / PROTOCOL_PATH
    require(source.file_hash(protocol) == PROTOCOL_SHA, 'exact_correction_protocol_required')
    roots = [shard_root(path) for path in options.shard_roots]
    require(len(roots) == len(set(roots)) == 8, 'eight_unique_ordered_shard_roots_required')
    base = original.load_inputs(SimpleNamespace(shard=0, bundle=options.bundle,
        bundle_sha=options.bundle_sha, model_dir=options.model_dir))
    selected, failures, references = [], [], []
    routes = events = 0
    for shard, root in enumerate(roots):
        require((root / 'source_commit.txt').read_text().strip() == SOURCE_COMMIT, 'original_source_commit_required')
        marker = root / 'launch/source_commit.txt'
        if marker.exists():
            require(marker.read_text().strip() == SOURCE_COMMIT, 'original_launch_source_drift')
        inputs = dict(base, shard=shard, worlds=base['registry'][shard],
            binding=dict(base['binding'], shard=shard, worlds=base['registry'][shard]))
        directory = root / 'expose'
        result = source.read(directory / 'RESULT.json')
        require(result['entry_sha256'] == inputs['binding']['helpers']['driver'], 'original_driver_drift')
        exposure, result_sha = original.read_stage(directory, 'expose', inputs)
        for name, expected in (('INPUTS.json', inputs['binding']), ('WORLDS.json', inputs['worlds']),
                               ('REGISTRY.json', inputs['registry'])):
            original.same(source.read(directory / name), expected, 'original_input_drift:' + name)
        current, rejected = select_records(exposure, inputs, root, result_sha)
        selected.extend(current)
        failures.extend(rejected)
        routes += sum(record['transition'] is not None for collection in exposure['collections'] for record in collection['records'])
        events += sum(record['accepted'] for collection in exposure['collections'] for record in collection['records'])
        references.append(dict(shard=shard, root=str(root), result_sha256=result_sha,
            source_ready=exposure['source_ready'], model_calls=result['model_calls']))
    require(routes == 320 and events == 316 and len(failures) == len(selected) == 4
            and {case['source']['shard'] for case in selected} == {0, 1, 4, 6}
            and Counter(case['source']['split'] for case in selected) == dict(TRAIN=3, PROBE=1),
            'declared_four_witnessed_terminal_copy_failures_required')
    binding = dict(source_commit=SOURCE_COMMIT, original_exposes=references,
        bundle_sha256=options.bundle_sha, state=PARENT_STATE, source_contract=base['manifest']['source_contract'],
        original_helpers=original.helpers(), entry_sha256=source.file_hash(__file__), protocol_sha256=PROTOCOL_SHA,
        selection_sha256=scale.document_sha256(selected), routes=routes, valid_original_events=events,
        case_count=4, max_native_calls=MAX_CALLS, max_attempts=MAX_ATTEMPTS,
        max_new_tokens=MAX_NEW_TOKENS, max_context=2048)
    return dict(binding=binding, selected=selected, failures=failures, base_verification=base['base_verification'])


def execute(inputs, generate, emit=None):
    emit = emit or (lambda name, document: None)
    cases, captures = [], []
    require(len(inputs['selected']) == 4, 'four_case_denominator_required')
    for case_index, selected in enumerate(inputs['selected']):
        record = selected['original_record']
        messages = deepcopy(selected['original_event_capture']['messages'])
        messages.extend([dict(role='assistant', content=record['event']['raw']),
                         dict(role='user', content=FEEDBACK + selected['public_receipt'])])
        case = dict(case_index=case_index, source=deepcopy(selected['source']),
                    attempts=[], accepted=False, candidate=None)
        cases.append(case)
        for attempt in range(MAX_ATTEMPTS):
            require(len(captures) < MAX_CALLS, 'correction_call_cap')
            capture = dict(call_index=len(captures), case_index=case_index, attempt=attempt,
                source=deepcopy(selected['source']), messages=deepcopy(messages), response=None, error=None)
            captures.append(capture)
            validation_error = None
            try:
                capture['response'] = deepcopy(generate(deepcopy(messages), max_new_tokens=MAX_NEW_TOKENS))
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
            emit(f"CALL_{capture['call_index']:03d}.json", capture)
            valid = False
            if capture['error'] is None:
                try:
                    raw = hop._generation(capture['response'], messages)
                    parsed = hop.micro.parse_event_line(hop.micro.canonical_event(raw))
                    require(parsed == dict(event=record['edge']['event'], **record['transition']),
                            'EVENT_not_grounded_in_original_receipt_and_address')
                    valid = True
                except ValueError as error:
                    validation_error = str(error)
            case['attempts'].append(dict(call_index=capture['call_index'], accepted=valid,
                                         validation_error=validation_error, error=deepcopy(capture['error'])))
            if valid:
                case.update(accepted=True, candidate=dict(raw=capture['response']['raw'],
                    response=deepcopy(capture['response']), source=deepcopy(selected['source']),
                    correction_call=f"CALL_{capture['call_index']:03d}.json",
                    correction_capture_sha256=scale.document_sha256(capture)))
                break
            response = capture['response']
            if capture['error'] is not None or type(response) is not dict or type(response.get('raw')) is not str:
                break
            messages.extend([dict(role='assistant', content=response['raw']),
                             dict(role='user', content=FEEDBACK + selected['public_receipt'])])
        emit(f'CASE_{case_index:02d}.json', case)
    return dict(schema=SCHEMA, cases=cases, case_count=4, accepted=sum(case['accepted'] for case in cases),
                model_calls=len(captures), native_errors=sum(capture['error'] is not None for capture in captures),
                claim=CLAIM, trainingAllowed=False, repair_promotion=False, fits=0, updates=0)


def read_preparation(directory, inputs, gpu_uuid):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result['schema'] == SCHEMA
            and result['phase'] == 'prepare' and result['status'] == 'PREPARED_NO_MODEL'
            and result['model_calls'] == result['fits'] == result['updates'] == 0
            and result['trainingAllowed'] is False and result['arguments']['gpu_uuid'] == gpu_uuid,
            'matching_no_model_preparation_required')
    original.same(result['binding'], inputs['binding'], 'prepared_binding_drift')
    require(set(result['output_files']) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'preparation_inventory_drift')
    portable.transfer.verify_files(directory, result['output_files'])
    original.same(source.read(directory / 'SELECTION.json'), inputs['selected'], 'prepared_selection_drift')
    return source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'bundle-sha', 'model-dir', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--shard-roots', nargs=8, required=True)
    parser.add_argument('--phase', choices=('prepare', 'correct'), required=True)
    parser.add_argument('--prepared')
    options = parser.parse_args(argv)
    require(bool(options.prepared) == (options.phase == 'correct'), 'correction_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    require(not output.exists() and not output.is_symlink(), 'fresh_correction_output_required')
    for location in [*(shard_root(path) for path in options.shard_roots), Path(options.bundle), Path(options.model_dir)]:
        require(location.resolve() != output.resolve() and location.resolve() not in output.resolve().parents,
                'readonly_input_output_overlap')
    if options.prepared:
        require(Path(options.prepared).resolve() not in output.resolve().parents, 'readonly_preparation_overlap')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arguments=vars(options), started_unix=started,
        fits=0, updates=0, trainingAllowed=False, automatic_training=False, repair_promotion=False,
        model_calls=0, max_native_calls=0 if options.phase == 'prepare' else MAX_CALLS,
        max_new_tokens=MAX_NEW_TOKENS, max_context=2048, max_seconds=MAX_SECONDS,
        protocol_sha256=PROTOCOL_SHA, claim=CLAIM, feedback_present=True, task_or_score_inputs=False)
    source.write(output / 'REQUEST.json', result)
    engine, parameters = None, {}

    def check(label):
        require(time.time() < started + MAX_SECONDS, 'correction_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'], base_file_verification=inputs['base_verification'])
        source.write(output / 'SELECTION.json', inputs['selected'])
        source.write(output / 'ORIGINAL_FAILURES.json', inputs['failures'])
        if options.phase == 'prepare':
            result['status'] = 'PREPARED_NO_MODEL'
        else:
            result['preparation_sha256'] = read_preparation(options.prepared, inputs, options.gpu_uuid)
            check('before_model')
            arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=options.bundle_sha,
                model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
            engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
            from organism_v6.pcfl_vertical_train import _state_hash

            parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                          if '.lora_A.' in name or '.lora_B.' in name}
            require(bool(parameters) and _state_hash(parameters) == PARENT_STATE, 'mounted_37ec_state_required')
            require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
                    'correction_actor_must_be_frozen')
            result.update(runtime=engine.runtime, loaded_adapter_state_sha256=PARENT_STATE)

            def generate(messages, *, max_new_tokens):
                check('call')
                require(result['model_calls'] < MAX_CALLS, 'correction_call_cap')
                result['model_calls'] += 1
                return engine.generate(messages, max_new_tokens=max_new_tokens)

            document = execute(inputs, generate, lambda name, value: source.write(output / name, value))
            source.write(output / 'DATA.json', document)
            require(document['native_errors'] == 0, 'correction_native_errors_retained')
            engine.verify_base()
            final_state = _state_hash(parameters)
            require(final_state == PARENT_STATE, 'readonly_correction_state_drift')
            verified = load_inputs(options)
            original.same(verified['binding'], inputs['binding'], 'correction_source_or_runtime_drift')
            check('complete')
            source.write(output / 'STATES.json', dict(before=PARENT_STATE, after=final_state))
            result.update(status='COMPLETE', adapter_state_after=final_state, frozen_base_unchanged=True,
                case_count=document['case_count'], accepted=document['accepted'],
                data_status='CORRECTION_CANDIDATES_ONLY_NOT_PROMOTED')
        result.update(finished_unix=time.time())
        result['elapsed_seconds'] = result['finished_unix'] - started
        result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None and parameters:
            try:
                result['adapter_state_after'] = _state_hash(parameters)
                engine.verify_base()
                portable.verify_base_files(options.bundle, options.model_dir, expected_manifest_sha256=options.bundle_sha)
                result['frozen_base_unchanged'] = True
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
            source.write(output / 'STATES.json', dict(before=result.get('loaded_adapter_state_sha256'),
                expected=PARENT_STATE, after=result.get('adapter_state_after')))
        result.update(status='FAILED', error=repr(error), finished_unix=time.time())
        result['elapsed_seconds'] = result['finished_unix'] - started
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
