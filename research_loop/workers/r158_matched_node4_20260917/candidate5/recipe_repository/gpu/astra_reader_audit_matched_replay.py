"""Zero-fit original-parent audit of postselected, third-party A3 read captures."""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time

from gpu import astra_fresh_reader_cycle as fresh
from gpu import astra_reader_audit_lesson as lesson
from organism_v6 import experienced_event_fresh_reader_audit as audit


source = lesson.source
require = source.require
SCHEMA = 'DEV_READER_AUDIT_MATCHED_REPLAY_V1'
MAX_CALLS = 14
MAX_SECONDS = 1800
PACKETS = (('before', 'before', 8, 'fault'), ('SELECTED/after', 'after', 6, 'true'))
CLAIM = 'POSTSELECTED_DEV_THIRD_PARTY_STIMULI_FRESH_OUTPUTS_NOT_ON_POLICY_OR_HELD_OUT_CONFIRMATION_NOT_H1_H2'


def replay_captures(cases, document):
    captures = iter(document['captures'])

    def generate(messages):
        capture = next(captures)
        require(capture['messages'] == messages, 'source_audit_prompt_drift')
        if capture['error'] is not None:
            error = capture['error']
            raise type(error['type'], (Exception,), {})(error['message'])
        return deepcopy(capture['response'])

    replayed = audit.collect_audit(cases, generate)
    require(next(captures, None) is None and replayed == document, 'source_audit_capture_drift')


def load_stimuli(root):
    root = Path(root)
    collection_result = source.read(root / 'collect/RESULT.json')
    provenance = collection_result['source']
    inputs = dict(fresh_source=provenance, initial_state=provenance['initial_adapter_state_sha256'])
    collection, unused_rows, collection_sha = fresh.read_collection(root / 'collect', inputs)
    before_sha = source.file_hash(root / 'before/RESULT.json')
    training, training_sha = fresh.read_training(root / 'SELECTED/train', inputs, 'SELECTED',
                                                collection_sha, before_sha)
    packets = []
    files = {name: source.file_hash(root / name) for name in
             ('collect/RESULT.json', 'collect/COLLECTION.json', 'SELECTED/train/RESULT.json')}
    for relative, phase, count, kind in PACKETS:
        directory = root / relative
        result, unused_sha = fresh.read_stage(directory, inputs, phase)
        actor = inputs['initial_state'] if phase == 'before' else training['adapter_state_after']
        require(result.get('fits') == 0 and result.get('loaded_adapter_state_sha256') == actor
                and result.get('collection_result_sha256') == collection_sha, 'stimulus_source_actor_drift')
        require(result.get('arm') == (None if phase == 'before' else 'SELECTED'), 'stimulus_arm_drift')
        if phase == 'after':
            require(result.get('before_result_sha256') == before_sha
                    and result.get('training_result_sha256') == training_sha, 'stimulus_after_receipt_drift')
        panel = result['panels']['OWN_PARAMETRIC']
        names = ['new_task/OWN_PARAMETRIC_EPISODE_%02d.json' % index for index in range(1, 5)]
        require(source.read(directory / 'new_task/PANELS.json')['OWN_PARAMETRIC'] == panel
                and [source.read(directory / name) for name in names] == panel['episodes'],
                'stimulus_route_file_drift')
        cases = audit.build_cases(collection, panel['episodes'])
        require(source.read(directory / 'ACTUAL_CASES.json') == cases, 'stimulus_case_drift')
        require(cases['expected_calls'] == count and all(case['kind'] == kind for case in cases['cases']),
                'fixed_eight_fault_six_true_packets_required')
        document = source.read(directory / 'ACTUAL_READERS.json')
        replay_captures(cases, document)
        for index, capture in enumerate(document['captures'], 16):
            name = 'CALL_%03d.json' % index
            saved = source.read(directory / name)
            require(saved['messages'] == capture['messages'] and saved['response'] == capture['response']
                    and (saved['error'] is None) == (capture['error'] is None), 'stimulus_call_file_drift')
            names.append(name)
        for name in ['RESULT.json', 'new_task/PANELS.json', 'ACTUAL_CASES.json', 'ACTUAL_READERS.json', *names]:
            files[relative + '/' + name] = source.file_hash(directory / name)
        prompts = [audit.document_sha256(case['messages']) for case in cases['cases']]
        packets.append(dict(packet=relative, cases=cases, source_actor_state_sha256=actor,
            source_choices=document['chosen_source_indexes'], source_summary=document['summary'],
            prompt_sha256=prompts, prompt_multiplicity=dict(Counter(prompts)),
            unique_prompts=len(set(prompts)), calls=count, stratum=kind))
    prompts = [digest for packet in packets for digest in packet['prompt_sha256']]
    binding = dict(source=provenance, source_files=files,
        dataset_sha256=audit.document_sha256([packet['cases'] for packet in packets]),
        ordered_prompts_sha256=audit.document_sha256(prompts),
        prompt_multiplicity=dict(Counter(prompts)), unique_prompts=len(set(prompts)),
        unique_addresses=len({case['address'] for packet in packets for case in packet['cases']['cases']}),
        observations='14_CALLS_WITH_REPEATED_PROMPTS_NOT_14_INDEPENDENT_OBSERVATIONS')
    return packets, binding


def load_inputs(after_source, campaign, stimulus_root, arm):
    require(arm in lesson.ARMS, 'original_auditor_arm_required')
    campaign = Path(campaign)
    inputs = lesson.load_inputs(after_source)
    unused_rows, lesson_sha = lesson.replay_lesson(campaign / 'collect', inputs)
    training_dir = campaign / arm / 'train'
    trained, train_sha = lesson.checked_training(training_dir, inputs, arm, lesson_sha)
    require(bool(trained.get('adapter_state_after'))
            and trained['adapter_state_after'] != trained['adapter_state_before'], 'original_fitted_auditor_required')
    sft_sha = train_sha
    if arm != 'AUDIT_SFT':
        unused_sft, sft_sha = lesson.checked_training(campaign / 'AUDIT_SFT/train', inputs, 'AUDIT_SFT', lesson_sha)
    packets, stimuli = load_stimuli(stimulus_root)
    parent = stimuli['source']['parent_source']
    require(parent.get('parent_arm') == 'AUDIT_SFT' and parent.get('prior_source') == inputs['provenance']
            and parent.get('lesson_result_sha256') == lesson_sha
            and parent.get('initial_training_result_sha256') == sft_sha, 'stimulus_original_campaign_join_drift')
    auditor = dict(arm=arm, adapter_dir=str(training_dir / 'adapter'),
        training_result_sha256=train_sha, lesson_result_sha256=lesson_sha,
        adapter_files=trained['adapter_files'], adapter_state_sha256=trained['adapter_state_after'],
        expected_base_sha256=inputs['after']['arguments']['expected_base_sha256'], source=inputs['provenance'])
    return dict(arguments=inputs['after']['arguments'], auditor=auditor, packets=packets, stimuli=stimuli)


def dispatch(engine, packets, output, captures, check):
    results = []
    for packet in packets:
        def generate(messages):
            check('audit_call')
            require(len(captures) < MAX_CALLS, 'matched_audit_call_budget')
            capture = dict(call_index=len(captures), packet=packet['packet'],
                packet_call_index=sum(item['packet'] == packet['packet'] for item in captures),
                messages=deepcopy(messages), prompt_sha256=audit.document_sha256(messages), response=None, error=None)
            captures.append(capture)
            try:
                capture['response'] = engine.generate(messages, max_new_tokens=audit.MAX_NEW_TOKENS)
                return capture['response']
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                source.write(output / ('CALL_%03d.json' % capture['call_index']), capture)

        document = audit.collect_audit(packet['cases'], generate)
        name = packet['packet'].replace('/', '_') + '_AUDIT.json'
        source.write(output / name, dict(interpretation=CLAIM, training_allowed=False,
            source_actor_state_sha256=packet['source_actor_state_sha256'], audit=document))
        results.append(dict(packet=packet['packet'], summary=document['summary'],
            chosen_source_indexes=document['chosen_source_indexes'], audit_file=name,
            audit_file_sha256=source.file_hash(output / name), prompt_multiplicity=packet['prompt_multiplicity'],
            unique_prompts=packet['unique_prompts'], calls=document['model_calls']))
    return results


def verify_unchanged(engine, parameters, auditor, result):
    from organism_v6.pcfl_vertical_train import _state_hash

    result['adapter_state_after'] = _state_hash(parameters)
    result['adapter_unchanged'] = result['adapter_state_after'] == auditor['adapter_state_sha256']
    result['adapter_files_after'] = {name: source.file_hash(Path(auditor['adapter_dir']) / name)
                                     for name in auditor['adapter_files']}
    result['adapter_files_unchanged'] = result['adapter_files_after'] == auditor['adapter_files']
    engine.verify_base()
    result['frozen_base_unchanged'] = True
    require(result['adapter_unchanged'] and result['adapter_files_unchanged'], 'readonly_auditor_changed')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('after-source', 'campaign', 'stimulus-root', 'gpu-uuid', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--arm', choices=lesson.ARMS, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    options = parser.parse_args(argv)
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.prepare_only or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, arguments=vars(options).copy(), arm=options.arm, started_unix=started,
        fits=0, model_calls=0, max_calls=MAX_CALLS, max_seconds=MAX_SECONDS, training_allowed=False,
        parent_present=False, on_policy=False, claim=CLAIM,
        code_provenance={name: source.file_hash(path) for name, path in
            (('entry', __file__), ('lesson_driver', lesson.__file__), ('fresh_driver', fresh.__file__),
             ('audit_evaluator', audit.__file__), ('native_engine', source.__file__))})
    source.write(output / 'REQUEST.json', result)
    captures = []
    engine = parameters = auditor = None

    def check(label):
        require(time.time() < started + MAX_SECONDS, 'matched_audit_deadline:' + label)

    try:
        inputs = load_inputs(options.after_source, options.campaign, options.stimulus_root, options.arm)
        auditor = inputs['auditor']
        result.update(evaluated_auditor=auditor, stimuli=inputs['stimuli'])
        source.write(output / 'INPUTS.json', dict(evaluated_auditor=auditor, stimuli=inputs['stimuli']))
        source.write(output / 'CASES.json', dict(packets=inputs['packets'], evaluator_only=True,
                                               training_allowed=False, claim=CLAIM))
        check('prepared')
        if options.prepare_only:
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = argparse.Namespace(**inputs['arguments'])
        arguments.phase, arguments.device = 'readout', 'cuda:0'
        arguments.gpu_uuid, arguments.adapter_dir = options.gpu_uuid, auditor['adapter_dir']
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        state = _state_hash(parameters)
        result.update(runtime=engine.runtime, adapter_state_before=state)
        require(bool(parameters) and state == auditor['adapter_state_sha256'], 'original_auditor_state_required')
        result['packets'] = dispatch(engine, inputs['packets'], output, captures, check)
        verify_unchanged(engine, parameters, auditor, result)
        engine.check('matched_audit_final')
        require(len(captures) == MAX_CALLS, 'fourteen_audit_calls_required')
        require(not any(capture['error'] for capture in captures), 'audit_generation_errors_captured')
        result.update(status='COMPLETE', model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None and parameters:
            try:
                verify_unchanged(engine, parameters, auditor, result)
            except BaseException as verification_error:
                result['unchanged_check_error'] = repr(verification_error)
        result.update(status='FAILED', error=repr(error), model_calls=len(captures),
                      captured_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
