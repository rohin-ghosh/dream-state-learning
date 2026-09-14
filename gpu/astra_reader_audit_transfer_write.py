"""One counterfactual selector-material fit in the unchanged shared A3 writer."""

import argparse
from importlib import import_module
import os
from pathlib import Path
import time

from gpu import astra_fresh_reader_cycle as fresh
from gpu import astra_reader_audit_matched_replay as replay
from gpu import astra_selected_reader_repair_train as trainer


source = fresh.source
require = source.require
SCHEMA = 'DEV_READER_AUDIT_TRANSFER_WRITE_V1'
ARM = 'LOSS_OFF_SELECTOR'
CLAIM = 'COUNTERFACTUAL_SELECTOR_MATERIAL_SHARED_WRITER_DEV'
INITIAL_STATE = '48dc1d6d77852bddba75e04ee7442f4ef2a8e72bce5719d39ade4ed974a2b042'
SFT_CHOICES = [1, 0, 1, 0, 3, 2, 3, 2]
OFF_CHOICES = [1, None, 1, None, None, None, None, None]
BUDGETS = dict(memory_presentations=100, behavior_presentations=100, cue_presentations=38,
               lesson_presentations=62, new_memory_presentations=200)


def kernel_hashes():
    from organism_v6 import pcfl_vertical_train as writer

    modules = dict(trainer=trainer, memory_and_new_encoder=source, cue_encoder=trainer.cue_material,
        lesson_encoder=import_module(trainer.audit.LESSON_MODULE), mask_validator=trainer.audit,
        adapter_setup=trainer.development, native_recipe=source.native, state_hash=writer)
    return {name: source.file_hash(module.__file__) for name, module in modules.items()}


def expected_recipe(material_arm, selected, rows):
    config = trainer.recipe(material_arm, selected, memory_count=96)
    config['new_source_events'] = [row['event'] for row in rows['new_rows'][:4]]
    return config


def check_writer(directory, result, rows, selected, material_arm, initial_state):
    directory = Path(directory)
    require(result.get('updates') == 100 and result.get('fits') == 1
        and result.get('adapter_state_before') == initial_state
        and bool(result.get('adapter_state_after')) and result['adapter_state_after'] != initial_state
        and result.get('selected_source_indexes') == selected and result.get('budgets') == BUDGETS,
        'shared_writer_state_selection_or_budget_drift')
    config = expected_recipe(material_arm, selected, rows)
    require(source.native._digest(result.get('recipe')) == source.native._digest(config)
        and source.native._digest(source.read(directory / 'RECIPE.json')) == source.native._digest(config)
        and source.read(directory / 'TRAINING_ROWS.json') == rows, 'shared_writer_rows_or_recipe_drift')
    require({name: entry['sha256'] for name, entry in result.get('code_provenance', {}).items()} == kernel_hashes()
        and result.get('trainer_sha256') == source.file_hash(trainer.__file__), 'shared_writer_kernel_drift')
    for field, required, base in (
            ('adapter_files', {'adapter_model.safetensors', 'adapter_config.json'}, directory / 'adapter'),
            ('training_artifact_sha256', {'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'}, directory)):
        require(required <= set(result.get(field, {})), 'shared_writer_inventory_required')
        for name, digest in result[field].items():
            require(Path(name).name == name and source.file_hash(base / name) == digest, 'shared_writer_file_drift')
    provenance = source.read(directory / 'ADAPTER_PROVENANCE.json')
    require(provenance.get('schema') == trainer.SCHEMA and all(provenance.get(key) == result.get(key) for key in
        ('adapter_state_before', 'adapter_state_after', 'adapter_files', 'code_provenance',
         'training_artifact_sha256', 'material_arm')), 'shared_writer_adapter_provenance_drift')


def read_replay(directory, expected, arm):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_transfer_audit_forbidden')
    result = source.read(directory / 'RESULT.json')
    auditor = expected['auditor']
    require(result.get('schema') == replay.SCHEMA and result.get('status') == 'COMPLETE'
        and result.get('arm') == arm and result.get('fits') == 0 and result.get('model_calls') == 14
        and result.get('evaluated_auditor') == auditor and result.get('stimuli') == expected['stimuli']
        and result.get('adapter_state_before') == auditor['adapter_state_sha256']
        and result.get('adapter_state_after') == auditor['adapter_state_sha256']
        and result.get('adapter_files_after') == auditor['adapter_files']
        and all(result.get(key) is True for key in ('adapter_unchanged', 'adapter_files_unchanged', 'frozen_base_unchanged')),
        'original_complete_unchanged_transfer_auditor_required')
    require(result.get('code_provenance') == {name: source.file_hash(module.__file__) for name, module in
        (('entry', replay), ('lesson_driver', replay.lesson), ('fresh_driver', fresh),
         ('audit_evaluator', replay.audit), ('native_engine', source))}, 'transfer_audit_code_drift')
    require(source.read(directory / 'INPUTS.json') == dict(evaluated_auditor=auditor, stimuli=expected['stimuli'])
        and source.read(directory / 'CASES.json')['packets'] == expected['packets'], 'transfer_input_case_drift')
    files = {name: source.file_hash(directory / name) for name in ('RESULT.json', 'INPUTS.json', 'CASES.json')}
    summaries, choices, call_index = [], [], 0
    for packet in expected['packets']:
        name = packet['packet'].replace('/', '_') + '_AUDIT.json'
        wrapped = source.read(directory / name)
        require(wrapped.get('training_allowed') is False and wrapped.get('interpretation') == replay.CLAIM
            and wrapped.get('source_actor_state_sha256') == packet['source_actor_state_sha256'],
            'transfer_source_actor_drift')
        document = wrapped['audit']
        replay.replay_captures(packet['cases'], document)
        for packet_index, capture in enumerate(document['captures']):
            call_name = 'CALL_%03d.json' % call_index
            saved = source.read(directory / call_name)
            require(saved == dict(call_index=call_index, packet=packet['packet'], packet_call_index=packet_index,
                messages=capture['messages'], prompt_sha256=replay.audit.document_sha256(capture['messages']),
                response=capture['response'], error=None) and capture['error'] is None, 'transfer_raw_call_drift')
            files[call_name] = source.file_hash(directory / call_name)
            call_index += 1
        files[name] = source.file_hash(directory / name)
        summaries.append(dict(packet=packet['packet'], summary=document['summary'],
            chosen_source_indexes=document['chosen_source_indexes'], audit_file=name,
            audit_file_sha256=files[name], prompt_multiplicity=packet['prompt_multiplicity'],
            unique_prompts=packet['unique_prompts'], calls=document['model_calls']))
        if packet['packet'] == 'before':
            choices = document['chosen_source_indexes']
    require(call_index == 14 and len(list(directory.glob('CALL_*.json'))) == 14
        and result.get('packets') == summaries, 'transfer_call_count_or_summary_drift')
    return choices, dict(files=files, evaluated_auditor=auditor, stimuli=expected['stimuli'])


def load_inputs(options):
    inputs = fresh.load_parent(options)
    require(inputs['initial_state'] == INITIAL_STATE, 'frozen_A3_initial_writer_required')
    cycle = Path(options.cycle_root)
    collection, new_rows, collection_sha = fresh.read_collection(cycle / 'collect', inputs)
    selected, before_sha = fresh.read_before(cycle / 'before', inputs, collection, collection_sha)
    rows = dict(memory_rows=inputs['memory_rows'], cue_rows=inputs['cue_rows'],
                lesson_rows=inputs['lesson_rows'], new_rows=new_rows)
    trainer.validate_row_layout(**rows, memory_count=96)
    own_choices = source.read(cycle / 'before/ACTUAL_READERS.json')['chosen_source_indexes']
    require(own_choices == SFT_CHOICES and selected == SFT_CHOICES, 'frozen_A3_before_roster_required')
    transfers, raw_choices = {}, {}
    for arm in replay.lesson.ARMS:
        expected = replay.load_inputs(options.base_after, options.campaign, options.cycle_root, arm)
        require(expected['stimuli']['source'] == inputs['fresh_source']
            and expected['packets'][0]['source_actor_state_sha256'] == INITIAL_STATE
            and expected['packets'][0]['cases'] == source.read(cycle / 'before/ACTUAL_CASES.json'),
            'same_A3_stimulus_source_required')
        raw_choices[arm], transfers[arm] = read_replay(Path(options.replay_root) / arm, expected, arm)
    require(raw_choices['AUDIT_SFT'] == own_choices, 'SFT_transfer_must_exactly_match_own_before')
    require(raw_choices['AUDIT_LOSS_OFF'] == OFF_CHOICES, 'frozen_OFF_transfer_roster_required')
    chosen = [index for index in raw_choices['AUDIT_LOSS_OFF'] if index is not None]
    references = {}
    for arm in ('SELECTED', 'UNIFORM'):
        directory = cycle / arm / 'train'
        trained, digest = fresh.read_training(directory, inputs, arm, collection_sha, before_sha)
        check_writer(directory, trained, rows, selected, arm, INITIAL_STATE)
        references[arm] = dict(training_result_sha256=digest, adapter_state_after=trained['adapter_state_after'],
            masks_sha256=trained['training_artifact_sha256']['MASKS.json'],
            training_rows_sha256=source.file_hash(directory / 'TRAINING_ROWS.json'),
            adapter_provenance_sha256=source.file_hash(directory / 'ADAPTER_PROVENANCE.json'),
            reference_supervised_tokens=trained['reference_supervised_tokens'])
    require(references['SELECTED']['masks_sha256'] == references['UNIFORM']['masks_sha256']
        and references['SELECTED']['reference_supervised_tokens'] == references['UNIFORM']['reference_supervised_tokens'],
        'reference_encoding_or_denominator_drift')
    binding = dict(fresh_source=inputs['fresh_source'], collection_result_sha256=collection_sha,
        before_result_sha256=before_sha, transfer_sources=transfers, raw_source_choices=raw_choices,
        selected_source_indexes=chosen, reused_references=references, kernel_hashes=kernel_hashes(),
        training_rows_sha256=source.native._digest(rows), claim=CLAIM,
        choice_policy='SOURCE_VALID_POINTERS_ONLY_KEEP_DUPLICATES_AND_WRONG_CHOICES_NO_TRUTH_FILTER',
        common_lesson_rehearsal=True, selector_is_writer_on_policy=False)
    inputs.update(collection=collection, rows=rows, selected=chosen, transfer_source=binding)
    return inputs


def checked_training(directory, inputs):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_transfer_fit_forbidden')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'train' and result.get('status') == 'COMPLETE'
        and result.get('arm') == ARM and result.get('material_arm') == 'SELECTED'
        and result.get('source') == inputs['transfer_source'] and result.get('frozen_base_unchanged') is True,
        'own_completed_transfer_fit_required')
    check_writer(directory, result, inputs['rows'], inputs['selected'], 'SELECTED', INITIAL_STATE)
    require(result['training_artifact_sha256']['MASKS.json'] == inputs['transfer_source']['reused_references']['UNIFORM']['masks_sha256']
        and result['reference_supervised_tokens'] == inputs['transfer_source']['reused_references']['UNIFORM']['reference_supervised_tokens'],
        'transfer_shared_denominator_drift')
    return result, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'replay-root', 'gpu-uuid', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'train', 'after'), required=True)
    parser.add_argument('--training')
    options = parser.parse_args(argv)
    require(bool(options.training) == (options.phase == 'after'), 'training_path_only_for_after')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arm=ARM, arguments=vars(options).copy(),
        started_unix=started, fits=0, max_fits=1, max_updates=100, max_train_seconds=7440, model_calls=0,
        parent_present=False, on_policy=False, claim=CLAIM, entry_sha256=source.file_hash(__file__),
        audit_policy=fresh.AUDIT_POLICY, audit_helper_sha256=source.file_hash(fresh.audit.__file__))
    source.write(output / 'REQUEST.json', result)
    captures = []

    def check(label):
        require(time.time() < started + (7440 if options.phase == 'train' else 1800), 'transfer_write_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result['source'] = inputs['transfer_source']
        source.write(output / 'INPUTS.json', inputs['transfer_source'])
        check('prepared')
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = argparse.Namespace(**inputs['after']['arguments'])
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = inputs['adapter_dir']
        expected_state = INITIAL_STATE
        if options.phase == 'after':
            trained, training_sha = checked_training(options.training, inputs)
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
            expected_state = trained['adapter_state_after']
            result['training_result_sha256'] = training_sha
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: value for name, value in engine.model.named_parameters() if '.lora_A.' in name or '.lora_B.' in name}
        state = _state_hash(parameters)
        require(bool(parameters) and state == expected_state, 'shared_writer_loaded_state_drift')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages):
            check('readout')
            require(len(captures) < 24, 'transfer_readout_callback_cap')
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
            source.write(output / 'TRAINING_ROWS.json', inputs['rows'])
            result['fits'] = 1
            result.update(trainer.train(engine, **inputs['rows'], output=output, material_arm='SELECTED',
                selected_source_indexes=inputs['selected'], memory_count=96))
            result.update(schema=SCHEMA, trainer_sha256=source.file_hash(trainer.__file__))
            check_writer(output, result, inputs['rows'], inputs['selected'], 'SELECTED', INITIAL_STATE)
            reference = inputs['transfer_source']['reused_references']['UNIFORM']
            require(result['training_artifact_sha256']['MASKS.json'] == reference['masks_sha256']
                and result['reference_supervised_tokens'] == reference['reference_supervised_tokens'],
                'transfer_shared_denominator_drift')
        else:
            source.write(output / 'HELD_AUDIT.json', fresh.repair.prior.lesson.collect_cases(inputs['held'], generate, coached=False))
            result.update(fresh.evaluate(engine, inputs['collection'], inputs, output))
            cases = fresh.audit.build_cases(inputs['collection'], result['panels']['OWN_PARAMETRIC']['episodes'])
            source.write(output / 'ACTUAL_CASES.json', cases)
            source.write(output / 'ACTUAL_READERS.json', fresh.audit.collect_audit(cases, generate))
        engine.verify_base()
        if options.phase == 'after':
            result['adapter_state_after'] = _state_hash(parameters)
            require(result['adapter_state_after'] == state, 'readonly_transfer_after_changed_adapter')
        engine.check('transfer_write_final')
        result['model_calls'] += len(captures)
        result.update(status='COMPLETE', frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), captured_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
