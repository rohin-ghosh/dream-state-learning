"""Bounded developmental reader-audit teaching with parent-free readouts."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_corrective_reselect as recurrent
from gpu import astra_experienced_event_adult_cycle as driver
from organism_v6 import experienced_event_reader_audit_lesson as lesson


source = driver.source
require = source.require
SCHEMA = 'DEV_READER_AUDIT_LESSON_RUN_V1'
ARMS = ('AUDIT_SFT', 'AUDIT_LOSS_OFF')


def events_from_rows(rows):
    events = []
    seen = set()
    for row in rows:
        if row['event'] not in seen:
            seen.add(row['event'])
            events.append(dict(event=row['event'], raw=row['messages'][-1]['content']))
    return events


def load_inputs(after_directory):
    after, unused_cases, ancestry = recurrent.load_inputs(after_directory)
    args = after['arguments']
    old_bank, old_episodes, old_rows, memory_source = source.load_collection(args['collection'],
        serialization='FINAL_LF_ONLY')
    cue_rows, cue_source = driver.cue_material.load_cue_rows(args['cue_collection'],
        expected_actor_sha256=driver.access.ADAPTER_SHA256)
    receipt, prior, prior_rows, prior_source = driver.load_cycle2_initial(args['initial_adapter_dir'],
        args['prior_adult_collection'], arm='CUE_REPLAY', expected_base_sha256=args['expected_base_sha256'],
        memory_source=memory_source, cue_source=cue_source)
    require(receipt == after['initial_training_result_sha256'] and memory_source == after['memory_source']
            and cue_source == after['cue_source'] and prior_source == after['prior_adult_source'],
            'lesson_own_source_lineage_drift')
    collection, new_rows, adult_source = driver.read_adult_collection(args['adult_collection'], receipt,
        cycle=2, prior_adult_source=prior_source)
    require(adult_source == after['adult_source'], 'lesson_held_source_drift')
    old_rows = old_rows + prior_rows
    selected_events = {collection['episodes'][index]['fact']['event']
                       for index in after['selected_source_indexes']}
    retained = [row for row in new_rows if row['event'] in selected_events]
    require(len(old_rows) == 64 and len(retained) == 16 and len(cue_rows) == 20,
            'lesson_retains_only_eight_old_and_two_written_new_facts')
    dev = lesson.build_cases(events_from_rows(old_rows), split='DEV')
    held = lesson.build_cases(events_from_rows(new_rows), split='HELD')
    provenance = dict(ancestry=ancestry, dev_source_events=events_from_rows(old_rows),
        held_source_events=events_from_rows(new_rows), retained_new_events=sorted(selected_events),
        lesson_helper_sha256=source.file_hash(lesson.__file__),
        recurrent_helper_sha256=source.file_hash(recurrent.__file__),
        driver_sha256=source.file_hash(driver.__file__),
        input_document_sha256=source.native._digest(collection))
    return dict(after=after, provenance=provenance, dev=dev, held=held,
        memory_rows=old_rows + retained, cue_rows=cue_rows, collection=collection,
        old_bank=old_bank + prior['bank'], old_episodes=old_episodes + prior['episodes'])


def replay_lesson(directory, inputs):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_lesson_not_trainable')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'collect'
            and result.get('status') == 'LESSON_READY' and result.get('fits') == 0
            and result.get('source') == inputs['provenance']
            and result.get('loaded_adapter_state_sha256') == inputs['after']['loaded_adapter_state_sha256']
            and result.get('frozen_base_unchanged') is True, 'same_child_ready_lesson_required')
    document = source.read(directory / 'LESSON.json')
    require(source.file_hash(directory / 'LESSON.json') == result['lesson_sha256'], 'lesson_file_drift')
    captures = iter(document['captures'])

    def generate(messages):
        capture = next(captures)
        require(capture['messages'] == messages and capture['error'] is None,
                'replayed_lesson_prompt_or_infrastructure_error')
        return capture['response']

    replayed = lesson.collect_cases(inputs['dev'], generate, coached=True)
    require(next(captures, None) is None and replayed == document and replayed['ready'],
            'child_lesson_capture_or_coverage_drift')
    return replayed['rows'], source.file_hash(directory / 'RESULT.json')


def checked_training(directory, inputs, arm, lesson_sha256):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_lesson_fit_forbidden')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'train'
            and result.get('status') == 'COMPLETE' and result.get('arm') == arm
            and result.get('updates') == 200 and result.get('lesson_result_sha256') == lesson_sha256
            and result.get('source') == inputs['provenance'] and result.get('frozen_base_unchanged') is True
            and result.get('adapter_state_before') == inputs['after']['loaded_adapter_state_sha256'],
            'completed_matched_lesson_fit_required')
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(result.get('adapter_files', {})),
            'lesson_adapter_files_required')
    for name, digest in result['adapter_files'].items():
        require(Path(name).name == name and source.file_hash(directory / 'adapter' / name) == digest,
                'lesson_adapter_file_drift')
    return result, source.file_hash(directory / 'RESULT.json')


def actual_cases(directory, inputs, arm, training_sha256, expected_state):
    from organism_v6 import experienced_event_actual_reader_audit as actual

    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_actual_after_forbidden')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'after'
            and result.get('status') == 'COMPLETE' and result.get('arm') == arm
            and result.get('source') == inputs['provenance'] and result.get('fits') == 0
            and result.get('training_result_sha256') == training_sha256
            and result.get('loaded_adapter_state_sha256') == expected_state
            and result.get('frozen_base_unchanged') is True, 'own_actual_after_actor_required')
    panel = result['panels']['OWN_PARAMETRIC']
    require(source.read(directory / 'new_task/PANELS.json')['OWN_PARAMETRIC'] == panel,
            'actual_panel_file_drift')
    names = ['new_task/OWN_PARAMETRIC_EPISODE_%02d.json' % index for index in range(1, 5)]
    records = [source.read(directory / name) for name in names]
    require(records == panel['episodes'] and panel['denominator'] == 4, 'all_own_actual_routes_required')
    cases = actual.build_cases(inputs['collection'], records)
    provenance = dict(directory=str(directory), helper_sha256=source.file_hash(actual.__file__),
        source_files={name: source.file_hash(directory / name)
                      for name in ['RESULT.json', 'new_task/PANELS.json', *names]})
    return cases, provenance


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'train', 'after', 'actual'), required=True)
    parser.add_argument('--after-source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--lesson')
    parser.add_argument('--training')
    parser.add_argument('--own-after')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--arm', choices=ARMS)
    options = parser.parse_args(argv)
    require((options.phase in ('train', 'after', 'actual')) == bool(options.lesson) == bool(options.arm),
            'explicit_paired_lesson_arm_required')
    require((options.phase in ('after', 'actual')) == bool(options.training), 'after_requires_own_training')
    require((options.phase == 'actual') == bool(options.own_after), 'actual_requires_own_after')
    require(not options.prepare_only or options.phase == 'actual', 'prepare_only_for_actual')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1',
            'offline_required')
    require(options.phase == 'prepare' or options.prepare_only
            or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid,
            'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arm=options.arm, arguments=vars(options).copy(),
        entry_sha256=source.file_hash(__file__), started_unix=started, fits=0, model_calls=0,
        claim='DEV_COACHED_READER_AUDIT_BEHAVIOR_NOT_AUTONOMOUS_EXTRACTION_OR_H1_H2')
    source.write(output / 'REQUEST.json', result)
    captures = []

    def check(label):
        require(time.time() < started + (5400 if options.phase == 'train' else 1800),
                'lesson_deadline:' + label)

    try:
        inputs = load_inputs(options.after_source)
        result['source'] = inputs['provenance']
        source.write(output / 'INPUTS.json', inputs['provenance'])
        source.write(output / 'DEV_CASES.json', inputs['dev'])
        source.write(output / 'HELD_CASES.json', inputs['held'])
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return
        arguments = argparse.Namespace(**inputs['after']['arguments'])
        arguments.phase = 'readout'
        arguments.device = 'cuda:0'
        arguments.gpu_uuid = options.gpu_uuid
        expected_state = inputs['after']['loaded_adapter_state_sha256']
        if options.lesson:
            rows, lesson_sha256 = replay_lesson(options.lesson, inputs)
            result['lesson_result_sha256'] = lesson_sha256
        if options.phase in ('after', 'actual'):
            trained, train_sha256 = checked_training(options.training, inputs, options.arm, lesson_sha256)
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
            expected_state = trained['adapter_state_after']
            result['training_result_sha256'] = train_sha256
        if options.phase == 'actual':
            cases, provenance = actual_cases(options.own_after, inputs, options.arm, train_sha256, expected_state)
            source.write(output / 'ACTUAL_CASES.json', cases)
            result['actual_source'] = provenance
            if options.prepare_only:
                result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
                source.write(output / 'RESULT.json', result)
                return
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        before = _state_hash(parameters)
        require(bool(parameters) and before == expected_state, 'loaded_expected_lesson_actor_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=before)

        def generate(messages):
            require(len(captures) < 80, 'lesson_generation_budget')
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
            held = lesson.collect_cases(inputs['held'], generate, coached=False)
            source.write(output / 'BEFORE_HELD.json', held)
            collected = lesson.collect_cases(inputs['dev'], generate, coached=True)
            source.write(output / 'LESSON.json', collected)
            result.update(status='LESSON_READY' if collected['ready'] else 'LESSON_INCOMPLETE_NO_FIT',
                          lesson_sha256=source.file_hash(output / 'LESSON.json'), parent_present=True)
        elif options.phase == 'train':
            from gpu import astra_reader_audit_lesson_train as trainer

            source.write(output / 'TRAINING_ROWS.json', dict(memory=inputs['memory_rows'],
                                                           cue=inputs['cue_rows'], lesson=rows))
            result.update(trainer.train(engine, inputs['memory_rows'], inputs['cue_rows'], rows,
                                        output, arm=options.arm))
            result.update(schema=SCHEMA, status='COMPLETE', fits=1, arm=options.arm,
                          trainer_sha256=source.file_hash(trainer.__file__), parent_present=False)
        elif options.phase == 'actual':
            from organism_v6 import experienced_event_actual_reader_audit as actual

            selected = actual.collect_cases(cases, generate)
            source.write(output / 'ACTUAL_READERS.json', selected)
            result.update(status='COMPLETE', parent_present=False,
                          claim='PARENT_FREE_CLASSIFICATION_OF_OWN_READER_REPLIES_NOT_WRITE_UTILITY')
        else:
            held = lesson.collect_cases(inputs['held'], generate, coached=False)
            source.write(output / 'AFTER_HELD.json', held)
            result.update(driver.evaluate(engine, inputs['collection'], inputs['old_bank'],
                                           inputs['old_episodes'], output, reader_wrapper=0))
            result.update(status='COMPLETE', parent_present=False)
        engine.verify_base()
        if options.phase != 'train':
            require(_state_hash(parameters) == before, 'readonly_lesson_changed_adapter')
        result['model_calls'] = result.get('model_calls', 0) + len(captures)
        result.update(frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), captured_lesson_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
