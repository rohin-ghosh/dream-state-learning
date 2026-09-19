"""One bounded repair sleep from each child's actual source-pointer selections."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_reader_audit_lesson as prior
from organism_v6 import experienced_event_actual_reader_audit as actual


source = prior.source
driver = prior.driver
require = source.require
SCHEMA = 'DEV_SELECTED_ACTUAL_READER_REPAIR_V1'


def load_inputs(base_after, campaign, audit_root, parent_arm):
    inputs = prior.load_inputs(base_after)
    campaign, audit_root = Path(campaign), Path(audit_root)
    rows, lesson_sha = prior.replay_lesson(campaign / 'collect', inputs)
    trained, train_sha = prior.checked_training(campaign / parent_arm / 'train', inputs, parent_arm, lesson_sha)
    cases, actual_source = prior.actual_cases(campaign / parent_arm / 'after', inputs, parent_arm,
                                            train_sha, trained['adapter_state_after'])
    audit_dir = audit_root / parent_arm
    require(not (audit_dir / 'FAILED.json').exists(), 'failed_actual_audit_forbidden')
    result = source.read(audit_dir / 'RESULT.json')
    require(result.get('schema') == prior.SCHEMA and result.get('phase') == 'actual'
            and result.get('status') == 'COMPLETE' and result.get('arm') == parent_arm
            and result.get('source') == inputs['provenance'] and result.get('fits') == 0
            and result.get('actual_source') == actual_source
            and result.get('training_result_sha256') == train_sha
            and result.get('loaded_adapter_state_sha256') == trained['adapter_state_after']
            and result.get('frozen_base_unchanged') is True, 'own_terminal_actual_audit_required')
    record = source.read(audit_dir / 'ACTUAL_READERS.json')
    require(source.read(audit_dir / 'ACTUAL_CASES.json') == cases, 'actual_cases_file_drift')
    captures = iter(record['captures'])

    def generate(messages):
        capture = next(captures)
        require(capture['messages'] == messages and capture['error'] is None, 'actual_capture_prompt_drift')
        return capture['response']

    replayed = actual.collect_cases(cases, generate)
    require(next(captures, None) is None and replayed == record, 'actual_capture_replay_drift')
    selected = [index for index in record['chosen_source_indexes'] if index is not None]
    require(1 <= len(selected) <= 8, 'nonempty_actual_source_choices_required')
    require(len(rows) == 62, 'fixed_released_62_lesson_rows_required')
    inputs.update(lesson_rows=rows, new_rows=driver.adult.replay_collection(inputs['collection']),
                  selected=selected, adapter_dir=str(campaign / parent_arm / 'train/adapter'),
                  initial_state=trained['adapter_state_after'])
    inputs['repair_source'] = dict(parent_arm=parent_arm, prior_source=inputs['provenance'],
        initial_training_result_sha256=train_sha, initial_adapter_state_sha256=trained['adapter_state_after'],
        initial_adapter_files=trained['adapter_files'], lesson_result_sha256=lesson_sha,
        actual_source=actual_source, audit_files={name: source.file_hash(audit_dir / name)
            for name in ('RESULT.json', 'ACTUAL_CASES.json', 'ACTUAL_READERS.json')},
        selected_source_indexes=selected, actual_helper_sha256=source.file_hash(actual.__file__))
    return inputs


def checked_training(directory, inputs, parent_arm, material_arm):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_repair_fit_forbidden')
    trained = source.read(directory / 'RESULT.json')
    require(trained.get('schema') == SCHEMA and trained.get('phase') == 'train'
            and trained.get('status') == 'COMPLETE' and trained.get('updates') == 100
            and trained.get('parent_arm') == parent_arm and trained.get('material_arm') == material_arm
            and trained.get('source') == inputs['repair_source']
            and trained.get('adapter_state_before') == inputs['initial_state']
            and isinstance(trained.get('adapter_state_after'), str)
            and bool(trained['adapter_state_after'])
            and trained['adapter_state_after'] != inputs['initial_state']
            and trained.get('frozen_base_unchanged') is True, 'matched_repair_fit_required')
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(trained.get('adapter_files', {})),
            'repair_adapter_inventory_required')
    for name, digest in trained['adapter_files'].items():
        require(Path(name).name == name and source.file_hash(directory / 'adapter' / name) == digest,
                'repair_adapter_file_drift')
    require({'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'} <= set(trained.get('training_artifact_sha256', {})),
            'repair_training_artifact_inventory_required')
    for name, digest in trained.get('training_artifact_sha256', {}).items():
        require(Path(name).name == name and source.file_hash(directory / name) == digest,
                'repair_training_artifact_drift')
    return trained, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('prepare', 'train', 'after'), required=True)
    for name in ('base-after', 'campaign', 'audit-root', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--parent-arm', choices=prior.ARMS, required=True)
    parser.add_argument('--material-arm', choices=('SELECTED', 'UNIFORM'), required=True)
    parser.add_argument('--training')
    options = parser.parse_args(argv)
    require((options.phase == 'after') == bool(options.training), 'own_repair_training_required_for_after')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid,
            'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, parent_arm=options.parent_arm,
        material_arm=options.material_arm, arguments=vars(options).copy(), started_unix=started,
        entry_sha256=source.file_hash(__file__), fits=0, model_calls=0, parent_present=False,
        claim='SINGLE_LINEAGE_ACTUAL_SELECTED_REPAIR_NOT_H1_H2_OR_LEARNING_RATE')
    source.write(output / 'REQUEST.json', result)
    captures = []

    def check(label):
        require(time.time() < started + (5400 if options.phase == 'train' else 1800), 'repair_deadline:' + label)

    try:
        inputs = load_inputs(options.base_after, options.campaign, options.audit_root, options.parent_arm)
        result['source'] = inputs['repair_source']
        source.write(output / 'INPUTS.json', inputs['repair_source'])
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return
        arguments = argparse.Namespace(**inputs['after']['arguments'])
        arguments.phase, arguments.device = 'readout', 'cuda:0'
        arguments.adapter_dir = inputs['adapter_dir']
        arguments.gpu_uuid = options.gpu_uuid
        expected_state = inputs['initial_state']
        if options.phase == 'after':
            trained, train_sha = checked_training(options.training, inputs, options.parent_arm, options.material_arm)
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
            expected_state = trained['adapter_state_after']
            result['training_result_sha256'] = train_sha
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        before = _state_hash(parameters)
        require(bool(parameters) and before == expected_state, 'own_repair_actor_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=before)

        def generate(messages):
            require(len(captures) < 24, 'repair_audit_24_call_budget')
            capture = dict(messages=messages, response=None, error=None)
            captures.append(capture)
            try:
                capture['response'] = engine.generate(messages, max_new_tokens=source.MAX_NEW_TOKENS)
                return capture['response']
            except Exception as error:
                capture['error'] = repr(error)
                raise
            finally:
                source.write(output / ('CALL_%03d.json' % (len(captures) - 1)), capture)

        if options.phase == 'train':
            from gpu import astra_selected_reader_repair_train as trainer

            source.write(output / 'TRAINING_ROWS.json', {key: inputs[key] for key in
                         ('memory_rows', 'cue_rows', 'lesson_rows', 'new_rows')})
            result.update(trainer.train(engine, inputs['memory_rows'], inputs['cue_rows'], inputs['lesson_rows'],
                inputs['new_rows'], output, material_arm=options.material_arm, selected_source_indexes=inputs['selected']))
            result.update(schema=SCHEMA, fits=1, trainer_sha256=source.file_hash(trainer.__file__))
        else:
            held = prior.lesson.collect_cases(inputs['held'], generate, coached=False)
            source.write(output / 'AFTER_HELD.json', held)
            result.update(driver.evaluate(engine, inputs['collection'], inputs['old_bank'], inputs['old_episodes'],
                                          output, reader_wrapper=0))
            cases = actual.build_cases(inputs['collection'], result['panels']['OWN_PARAMETRIC']['episodes'])
            source.write(output / 'NEXT_ACTUAL_CASES.json', cases)
            source.write(output / 'NEXT_ACTUAL_READERS.json', actual.collect_cases(cases, generate))
        engine.verify_base()
        if options.phase != 'train':
            require(_state_hash(parameters) == before, 'readonly_repair_stage_changed_adapter')
        result['model_calls'] += len(captures)
        result.update(status='COMPLETE', frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), captured_audit_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
