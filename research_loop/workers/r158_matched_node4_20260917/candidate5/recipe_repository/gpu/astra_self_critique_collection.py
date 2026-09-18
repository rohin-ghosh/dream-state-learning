"""Readonly common-initial and paired critique/repeat native collection."""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time

from gpu import astra_rich_action_first_collection as reuse
from organism_v6 import experienced_event_self_critique as lesson


source = reuse.source
portable = reuse.portable
require = source.require
PARENT_STATE = reuse.original.PARENT_STATE
SCHEMA = 'DEV_SELF_CRITIQUE_REPEAT_NATIVE_V1'
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_self_critique_repeat_collection_protocol.md'
PROTOCOL_SHA = '154b7642113e48068e7357efb6a1d4c956dc151e030472fcb3f6ac98e696883a'


def helpers():
    return dict(driver=source.file_hash(__file__), helper=source.file_hash(lesson.__file__),
                guard=source.file_hash(Path(__file__).with_name('astra_self_critique_collection_guard.sh')),
                reuse=reuse.helpers())


def summary(document):
    return dict(goals=sum(item['individual']['correct'] for item in document['summaries']),
                pairs=sum(item['paired']['correct'] for item in document['summaries']),
                task_denominator=16, pair_denominator=8, attempted_tasks=len(document['episodes']),
                candidate_rows=len(document['candidate_rows']),
                outcome_eligible_episodes=sum(item['outcome_eligible'] for item in document['episodes']),
                stops=dict(Counter(item['episode']['terminal_reason'] for item in document['episodes'])),
                fit_ready=False, semantic_pass=False)


def read_initial(directory, inputs):
    directory = Path(directory)
    result = source.read(directory/'RESULT.json')
    require(not (directory/'FAILED.json').exists() and result.get('schema') == SCHEMA
            and result.get('phase') == lesson.INITIAL and result.get('status') == 'COMPLETE'
            and result.get('fits') == result.get('updates') == 0
            and result.get('trainingAllowed') is False and result.get('parent_present') is False
            and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == PARENT_STATE
            and result.get('frozen_base_unchanged') is True, 'complete_readonly_shared_initial_required')
    reuse.original.same(result['binding'], inputs['binding'], 'shared_initial_binding_drift')
    require(set(result['output_files']) == {path.name for path in directory.glob('*.json')
                                           if path.name != 'RESULT.json'}, 'shared_initial_inventory')
    portable.transfer.verify_files(directory, result['output_files'])
    require(source.read(directory/'STATES.json') == dict(before=PARENT_STATE, after=PARENT_STATE),
            'shared_initial_state_join')
    document = lesson.replay_initial(source.read(directory/'DATA.json'))
    require(document['collections'] == inputs['collections'] and document['old_ids'] == inputs['old_ids'],
            'shared_initial_source_drift')
    require(result['model_calls'] == document['model_calls'] and result['max_native_calls'] == 96,
            'shared_initial_call_count')
    require({path.name for path in directory.glob('CALL_*.json')}
            == {f'CALL_{index:03d}.json' for index in range(document['model_calls'])}, 'shared_initial_call_inventory')
    for capture in document['captures']:
        native = source.read(directory/f"CALL_{capture['call_index']:03d}.json")
        require(native == dict({key: value for key, value in capture.items() if key != 'document_sha256'},
                               max_new_tokens=512), 'shared_initial_actual_capture_join')
    reuse.original.same(summary(document), result['summary'], 'shared_initial_summary_join')
    return document, source.file_hash(directory/'RESULT.json')


def load_inputs(options):
    require(source.file_hash(Path(__file__).resolve().parents[1]/PROTOCOL_PATH) == PROTOCOL_SHA,
            'exact_prospective_protocol_required')
    original = reuse.load_inputs(options)
    collections = original['exposure']['collections'][:4]
    lesson._collections(collections, original['old_ids'])
    binding = dict(protocol_sha256=PROTOCOL_SHA, helpers=helpers(), reuse_binding=original['binding'],
                   projection_policy=lesson.PROJECTION_POLICY,
                   train_source_sha256=[item['collection_sha256'] for item in collections],
                   state=PARENT_STATE, shard=0)
    inputs = dict(collections=collections, old_ids=original['old_ids'], binding=binding)
    if options.initial:
        inputs['initial'], inputs['initial_result_sha256'] = read_initial(options.initial, inputs)
    return inputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'bundle-sha', 'model-dir', 'exposure', 'output'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--shard', type=int, choices=(0,), default=0)
    parser.add_argument('--phase', choices=('prepare', lesson.INITIAL, *lesson.ARMS), required=True)
    parser.add_argument('--initial')
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline-epoch', type=float)
    options = parser.parse_args(argv)
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    native = options.phase != 'prepare'
    require(not native or options.gpu_uuid and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid,
            'exact_gpu_required')
    require(not native or options.deadline_epoch is not None
            and 0 < options.deadline_epoch - time.time() <= 6900, 'bounded_native_deadline_required')
    require(options.phase not in lesson.ARMS or options.initial, 'paired_arm_requires_common_initial')
    require(options.phase != lesson.INITIAL or not options.initial, 'initial_cannot_consume_initial')
    output = Path(options.output).resolve()
    for location in (options.bundle, options.model_dir, options.exposure, options.initial):
        if location:
            reference = Path(location).resolve()
            require(output != reference and reference not in output.parents, 'source_overlap_forbidden')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, started_unix=started, arguments=vars(options),
                  model_calls=0, max_native_calls=lesson.CAPS.get(options.phase, 0), max_new_tokens=512,
                  fits=0, updates=0, trainingAllowed=False, parent_present=False, fit_ready=False,
                  projection_policy=lesson.PROJECTION_POLICY,
                  semantic_pass=False, protocol_sha256=PROTOCOL_SHA, entry_sha256=source.file_hash(__file__))
    source.write(output/'REQUEST.json', result)
    captures, cap_hit = [], False

    def check(label):
        require(time.time() < options.deadline_epoch, 'self_critique_deadline:'+label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'], initial_result_sha256=inputs.get('initial_result_sha256'))
        source.write(output/'INPUTS.json', inputs['binding'])
        if not native:
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
        else:
            check('before_load')
            arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=options.bundle_sha,
                                             model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
            engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
            from organism_v6.pcfl_vertical_train import _state_hash

            parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                          if '.lora_A.' in name or '.lora_B.' in name}
            require(parameters and _state_hash(parameters) == PARENT_STATE, 'mounted_37ec_required')
            require(not any(parameter.requires_grad for name, parameter in engine.model.named_parameters()),
                    'readonly_actor_required')
            result.update(runtime=engine.runtime, loaded_adapter_state_sha256=PARENT_STATE)

            def generate(messages, **metadata):
                nonlocal cap_hit
                check('call')
                if len(captures) >= result['max_native_calls']:
                    cap_hit = True
                    raise ValueError('self_critique_call_cap')
                capture = dict(call_index=len(captures), messages=deepcopy(messages), **metadata,
                               response=None, error=None, max_new_tokens=512)
                captures.append(capture)
                try:
                    capture['response'] = deepcopy(engine.generate(deepcopy(messages), max_new_tokens=512))
                    return deepcopy(capture['response'])
                except Exception as error:
                    capture['error'] = dict(type=type(error).__name__, message=str(error))
                    raise
                finally:
                    source.write(output/f"CALL_{capture['call_index']:03d}.json", capture)

            if options.phase == lesson.INITIAL:
                document = lesson.collect_initial(inputs['collections'], generate, old_ids=inputs['old_ids'])
                lesson.replay_initial(document)
            else:
                document = lesson.collect_arm(options.phase, inputs['initial'], generate)
                lesson.replay_arm(document, inputs['initial'])
            source.write(output/'DATA.json', document)
            require(not cap_hit and len(captures) == document['model_calls'], 'actual_call_count_required')
            for actual, captured in zip(captures, document['captures']):
                require(actual == dict({key: value for key, value in captured.items() if key != 'document_sha256'},
                                       max_new_tokens=512), 'actual_capture_join')
            check('complete')
            engine.verify_base()
            final = _state_hash(parameters)
            require(final == PARENT_STATE, 'readonly_state_drift')
            portable.verify_base_files(options.bundle, options.model_dir, expected_manifest_sha256=options.bundle_sha)
            reuse.original.same(helpers(), inputs['binding']['helpers'], 'runtime_source_drift')
            source.write(output/'STATES.json', dict(before=PARENT_STATE, after=final))
            source.write(output/'NATIVE_METRICS.json', reuse.original.native_metrics(captures))
            result.update(status='COMPLETE', model_calls=len(captures), summary=summary(document),
                          role_calls=dict(Counter(item['role'] for item in captures)),
                          native_errors=sum(item['error'] is not None for item in captures),
                          adapter_state_after=final, frozen_base_unchanged=True, finished_unix=time.time())
        result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
        source.write(output/'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), finished_unix=time.time())
        source.write(output/'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
