"""One fresh bank collected and audited by the repaired child, then matched writes."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_selected_reader_repair as repair
from gpu import astra_experienced_event_cue_collect as collector
from organism_v6 import experienced_event_fresh_reader_cycle as fresh
from organism_v6 import experienced_event_fresh_reader_audit as audit


source = repair.source
driver = repair.driver
require = source.require
SCHEMA = 'DEV_FRESH_READER_AUDIT_CYCLE_V1'
AUDIT_POLICY = 'ALL_CAPTURED_READS_WITHOUT_SYNTHETIC_TRANSITION_V2'


def load_parent(options):
    inputs = repair.load_inputs(options.base_after, options.campaign, options.audit_root, 'AUDIT_SFT')
    parent = Path(options.repair_root) / 'AUDIT_SFT_SELECTED'
    trained, train_sha = repair.checked_training(parent / 'train', inputs, 'AUDIT_SFT', 'SELECTED')
    after = source.read(parent / 'after/RESULT.json')
    require(not (parent / 'after/FAILED.json').exists()
        and after.get('schema') == repair.SCHEMA and after.get('phase') == 'after'
        and after.get('status') == 'COMPLETE' and after.get('fits') == 0
        and after.get('parent_arm') == 'AUDIT_SFT' and after.get('material_arm') == 'SELECTED'
        and after.get('source') == inputs['repair_source']
        and after.get('loaded_adapter_state_sha256') == trained['adapter_state_after']
        and after.get('training_result_sha256') == train_sha
        and after.get('frozen_base_unchanged') is True, 'own_terminal_repaired_parent_required')
    inputs['memory_rows'] = inputs['memory_rows'][:64] + inputs['new_rows']
    inputs['old_bank'] = inputs['old_bank'] + inputs['collection']['bank']
    inputs['old_episodes'] = inputs['old_episodes'] + inputs['collection']['episodes']
    require(len(inputs['memory_rows']) == 96 and len(inputs['old_bank']) == 12
        and len({fact['event'] for fact in inputs['old_bank']}) == 12, 'all_twelve_prior_facts_required')
    exclusions = list(inputs['old_bank'])
    for bank in collector.training_banks():
        exclusions.extend(bank)
    for index in range(2):
        exclusions.extend(source.material.build_bank(driver.development.HELD_MASTER + '-' + str(index)))
    exclusions.extend(source.material.build_bank(source.MASTER + '-UNSEEN-MISS'))
    keys = ('world', 'event', 'node', 'port', 'outcome', 'receipt')
    previous = {fact[key] for fact in exclusions for key in keys}
    proposed = {fact[key] for fact in fresh.build_bank() for key in keys}
    require(not previous.intersection(proposed), 'fresh_bank_identity_overlap')
    inputs.update(initial_state=trained['adapter_state_after'], adapter_dir=str(parent / 'train/adapter'))
    inputs['fresh_source'] = dict(parent_source=inputs['repair_source'],
        parent_training_result_sha256=train_sha,
        parent_after_result_sha256=source.file_hash(parent / 'after/RESULT.json'),
        initial_adapter_state_sha256=trained['adapter_state_after'], initial_adapter_files=trained['adapter_files'],
        master=fresh.MASTER, prior_event_ids=[fact['event'] for fact in inputs['old_bank']],
        memory_rows_sha256=source.native._digest(inputs['memory_rows']),
        fresh_helper_sha256=source.file_hash(fresh.__file__))
    return inputs


def read_stage(directory, inputs, phase):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_fresh_stage_forbidden')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == phase
        and result.get('status') == 'COMPLETE' and result.get('source') == inputs['fresh_source']
        and result.get('frozen_base_unchanged') is True
        and result.get('parent_present') is False, 'own_complete_fresh_stage_required')
    if phase != 'collect':
        require(result.get('audit_policy') == AUDIT_POLICY
            and result.get('audit_helper_sha256') == source.file_hash(audit.__file__), 'fresh_audit_policy_binding_required')
    return result, source.file_hash(directory / 'RESULT.json')


def read_collection(directory, inputs):
    result, digest = read_stage(directory, inputs, 'collect')
    document = source.read(Path(directory) / 'COLLECTION.json')
    require(result.get('loaded_adapter_state_sha256') == inputs['initial_state']
        and result.get('fits') == 0 and result.get('collection_sha256') == source.file_hash(Path(directory) / 'COLLECTION.json'),
        'own_fresh_collection_actor_required')
    rows = fresh.replay_collection(document)
    require(len(rows) == 32 and document['accepted_events'] == 4, 'all_four_fresh_events_required')
    return document, rows, digest


def read_before(directory, inputs, collection, collection_sha):
    result, digest = read_stage(directory, inputs, 'before')
    require(result.get('loaded_adapter_state_sha256') == inputs['initial_state'] and result.get('fits') == 0
        and result.get('collection_result_sha256') == collection_sha, 'own_fresh_before_required')
    cases = audit.build_cases(collection, result['panels']['OWN_PARAMETRIC']['episodes'])
    require(source.read(Path(directory) / 'ACTUAL_CASES.json') == cases, 'fresh_before_case_drift')
    document = source.read(Path(directory) / 'ACTUAL_READERS.json')
    captures = iter(document['captures'])

    def generate(messages):
        capture = next(captures)
        require(capture['messages'] == messages and capture['error'] is None, 'fresh_before_capture_drift')
        return capture['response']

    replayed = audit.collect_audit(cases, generate)
    require(next(captures, None) is None and replayed == document, 'fresh_before_audit_drift')
    selected = [index for index in document['chosen_source_indexes'] if index is not None]
    require(1 <= len(selected) <= 8, 'no_source_selection_no_matched_fit')
    return selected, digest


def read_training(directory, inputs, arm, collection_sha, before_sha):
    result, digest = read_stage(directory, inputs, 'train')
    require(result.get('arm') == arm and result.get('material_arm') == arm and result.get('fits') == 1
        and result.get('updates') == 100 and result.get('adapter_state_before') == inputs['initial_state']
        and bool(result.get('adapter_state_after')) and result['adapter_state_after'] != inputs['initial_state']
        and result.get('collection_result_sha256') == collection_sha
        and result.get('before_result_sha256') == before_sha, 'own_matched_fresh_training_required')
    for field, required, base in (('adapter_files', {'adapter_model.safetensors', 'adapter_config.json'}, Path(directory) / 'adapter'),
        ('training_artifact_sha256', {'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'}, Path(directory))):
        require(required <= set(result.get(field, {})), 'fresh_training_inventory_required')
        for name, expected in result[field].items():
            require(Path(name).name == name and source.file_hash(base / name) == expected, 'fresh_training_file_drift')
    return result, digest


def evaluate(engine, collection, inputs, output):
    result = driver.evaluate(engine, collection, inputs['old_bank'][:8], inputs['old_episodes'][:8], output, reader_wrapper=0)
    for view in (0, 8):
        panel = result['panels']['OLD_RECALL_W%d' % view]
        for fact, episode in zip(inputs['old_bank'][8:], inputs['old_episodes'][8:]):
            messages = [dict(role='system', content=source.world.MEMORY_SYSTEM),
                dict(role='user', content=source.world.WRAPPERS[view].replace('{REQUEST}', 'READ EVENT ' + fact['event']))]
            generation = engine.generate(messages)
            expected = source.material.canonical_event(episode['event']['raw'])
            row = dict(event=fact['event'], generation=generation, expected=expected,
                correct=generation['terminal'] and not generation['truncated'] and generation['raw'] == expected)
            panel['rows'].append(row)
            source.write(output / ('OLD_RECALL_W%d_%02d.json' % (view, len(panel['rows']))), row)
        panel.update(denominator=12, correct=sum(row['correct'] for row in panel['rows']))
    result['model_calls'] += 8
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'before', 'train', 'after'), required=True)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    for name in ('collection', 'before', 'training'):
        parser.add_argument('--' + name)
    parser.add_argument('--arm', choices=('SELECTED', 'UNIFORM'))
    options = parser.parse_args(argv)
    require(bool(options.collection) == (options.phase in ('before', 'train', 'after'))
        and bool(options.before) == (options.phase in ('train', 'after'))
        and bool(options.training) == (options.phase == 'after')
        and bool(options.arm) == (options.phase in ('train', 'after')), 'fresh_phase_inputs_required')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arm=options.arm, arguments=vars(options).copy(),
        entry_sha256=source.file_hash(__file__), started_unix=started, fits=0, model_calls=0, parent_present=False,
        audit_policy=AUDIT_POLICY, audit_helper_sha256=source.file_hash(audit.__file__),
        claim='ONE_FRESH_BANK_SAME_FAMILY_DEV_CONTINUATION_NOT_H1_H2')
    source.write(output / 'REQUEST.json', result)
    captures = []

    def check(label):
        require(time.time() < started + (5400 if options.phase == 'train' else 1800), 'fresh_deadline:' + label)

    try:
        inputs = load_parent(options)
        result['source'] = inputs['fresh_source']
        source.write(output / 'INPUTS.json', inputs['fresh_source'])
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return
        collection = new_rows = selected = None
        if options.collection:
            collection, new_rows, collection_sha = read_collection(options.collection, inputs)
            result['collection_result_sha256'] = collection_sha
        if options.before:
            selected, before_sha = read_before(options.before, inputs, collection, collection_sha)
            result['before_result_sha256'] = before_sha
        arguments = argparse.Namespace(**inputs['after']['arguments'])
        arguments.phase, arguments.device = 'readout', 'cuda:0'
        arguments.adapter_dir, arguments.gpu_uuid = inputs['adapter_dir'], options.gpu_uuid
        expected_state = inputs['initial_state']
        if options.phase == 'after':
            training, train_sha = read_training(options.training, inputs, options.arm, collection_sha, before_sha)
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
            expected_state = training['adapter_state_after']
            result['training_result_sha256'] = train_sha
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: value for name, value in engine.model.named_parameters() if '.lora_A.' in name or '.lora_B.' in name}
        state = _state_hash(parameters)
        require(bool(parameters) and state == expected_state, 'own_fresh_actor_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages):
            require(len(captures) < (8 if options.phase == 'collect' else 24), 'fresh_callback_cap')
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

        if options.phase == 'collect':
            collection = fresh.collect(generate)
            source.write(output / 'COLLECTION.json', collection)
            result.update(collection_sha256=source.file_hash(output / 'COLLECTION.json'), accepted_events=collection['accepted_events'])
            require(collection['accepted_events'] == 4, 'incomplete_fresh_collection_no_fit')
        elif options.phase == 'train':
            from gpu import astra_selected_reader_repair_train as trainer

            source.write(output / 'TRAINING_ROWS.json', dict(memory_rows=inputs['memory_rows'], cue_rows=inputs['cue_rows'],
                lesson_rows=inputs['lesson_rows'], new_rows=new_rows))
            result.update(trainer.train(engine, inputs['memory_rows'], inputs['cue_rows'], inputs['lesson_rows'], new_rows,
                output, material_arm=options.arm, selected_source_indexes=selected, memory_count=96))
            result.update(schema=SCHEMA, fits=1, trainer_sha256=source.file_hash(trainer.__file__))
        else:
            source.write(output / 'HELD_AUDIT.json', repair.prior.lesson.collect_cases(inputs['held'], generate, coached=False))
            result.update(evaluate(engine, collection, inputs, output))
            cases = audit.build_cases(collection, result['panels']['OWN_PARAMETRIC']['episodes'])
            source.write(output / 'ACTUAL_CASES.json', cases)
            source.write(output / 'ACTUAL_READERS.json', audit.collect_audit(cases, generate))
        engine.verify_base()
        if options.phase != 'train':
            require(_state_hash(parameters) == state, 'readonly_fresh_stage_changed_adapter')
        result['model_calls'] += len(captures)
        result.update(status='COMPLETE', frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), captured_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
