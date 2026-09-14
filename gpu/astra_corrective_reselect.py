"""One read-only corrective selection from the actual post-sleep actor."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_experienced_event_adult_cycle as driver
from organism_v6 import experienced_event_corrective_replay as selector


source = driver.source
require = driver.require
SCHEMA = 'DEV_POST_CORRECTIVE_SLEEP_RESELECTION_V1'


def prepare_after(collection, after, request, panels, records, train, train_sha256):
    require(after.get('schema') == driver.SCHEMA and after.get('status') == 'COMPLETE'
            and after.get('phase') == 'readout_corrective' and after.get('state') == 'AFTER'
            and after.get('cycle') == 2 and after.get('development_arm') == 'CUE_REPLAY'
            and after.get('replay_arm') == 'CHILD_CORRECTIVE' and after.get('fits') == 0
            and after.get('frozen_base_unchanged') is True and after.get('reader_wrapper') == 0,
            'complete_corrective_own_after_required')
    arguments = after['arguments']
    require(arguments.get('phase') == 'readout_corrective' and arguments.get('state') == 'AFTER'
            and arguments.get('replay_arm') == 'CHILD_CORRECTIVE'
            and request.get('arguments') == arguments, 'after_request_arguments_drift')
    require(all(request.get(key) == after.get(key) for key in
                ('schema', 'phase', 'state', 'cycle', 'master', 'development_arm',
                 'runner_sha256', 'material_sha256')), 'after_request_identity_drift')
    require(after.get('loaded_adapter_state_sha256') == train['adapter_state_after']
            and after.get('corrective_training_result_sha256') == train_sha256,
            'after_generating_actor_drift')
    panel = after.get('panels', {}).get('OWN_PARAMETRIC')
    require(type(panel) is dict and panel.get('denominator') == 4
            and panels.get('OWN_PARAMETRIC') == panel and records == panel.get('episodes'),
            'all_four_actual_after_routes_required')
    return selector.prepare_cases(collection, records)


def load_inputs(directory):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_after_forbidden')
    after = source.read(directory / 'RESULT.json')
    arguments = after['arguments']
    initial = source.read(Path(arguments['initial_adapter_dir']).parent / 'RESULT.json')
    require(source.file_hash(Path(arguments['initial_adapter_dir']) / 'adapter_model.safetensors')
            == arguments['expected_initial_adapter_sha256'], 'initial_adapter_changed')
    collection, rows, adult_source = driver.read_adult_collection(arguments['adult_collection'],
        after['initial_training_result_sha256'], cycle=2, prior_adult_source=after['prior_adult_source'])
    require(adult_source == after['adult_source'], 'after_collection_drift')
    selected, selection_source = driver.load_corrective_selection(arguments['corrective_selection'],
        arguments['correction_before'], collection, after,
        expected_adapter_state_sha256=initial['adapter_state_after'])
    require(selection_source == after['corrective_selection_source'], 'after_selection_source_drift')
    train_sha256 = driver.check_corrective_training(arguments['adapter_dir'], after,
        replay_arm='CHILD_CORRECTIVE', selected_source_indexes=selected,
        expected_adapter_state_sha256=initial['adapter_state_after'])
    train = source.read(Path(arguments['adapter_dir']).parent / 'RESULT.json')
    names = ['RESULT.json', 'REQUEST.json', 'new_task/PANELS.json'] + [
        'new_task/OWN_PARAMETRIC_EPISODE_%02d.json' % index for index in range(1, 5)]
    require(sorted(path.name for path in (directory / 'new_task').glob('OWN_PARAMETRIC_EPISODE_*.json'))
            == [Path(name).name for name in names[3:]], 'after_episode_inventory_drift')
    documents = {name: source.read(directory / name) for name in names}
    cases = prepare_after(collection, after, documents['REQUEST.json'], documents['new_task/PANELS.json'],
        [documents[name] for name in names[3:]], train, train_sha256)
    provenance = dict(after_directory=str(directory), source_files={
        name: source.file_hash(directory / name) for name in names},
        train_result_sha256=train_sha256, adapter_files=train['adapter_files'],
        expected_actor_state_sha256=train['adapter_state_after'], previous_selected_source_indexes=selected,
        adult_source=adult_source, selection_source=selection_source,
        selector_sha256=source.file_hash(selector.__file__), driver_sha256=source.file_hash(driver.__file__))
    return after, cases, provenance


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--after', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--prepare-only', action='store_true')
    options = parser.parse_args(argv)
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1',
            'offline_required')
    require(options.prepare_only or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid,
            'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, arguments=vars(options).copy(), started_unix=started, fits=0,
                  runner_sha256=source.file_hash(__file__), parent_present=False)
    source.write(output / 'REQUEST.json', result)

    def check(label):
        require(time.time() < started + 1800, 'reselection_deadline:' + label)

    try:
        after, cases, provenance = load_inputs(options.after)
        source.write(output / 'INPUTS.json', provenance)
        result.update(source=provenance, expected_calls=cases['expected_calls'])
        if options.prepare_only:
            source.write(output / 'CORRECTION_CASES.json', cases)
            result.update(status='PREPARED_NO_MODEL', model_calls=0)
        else:
            arguments = argparse.Namespace(**after['arguments'])
            arguments.phase = 'readout'
            arguments.device = 'cuda:0'
            arguments.gpu_uuid = options.gpu_uuid
            tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
            lengths = [len(tokenizer.apply_chat_template(case['messages'], tokenize=True,
                add_generation_prompt=True, return_dict=False, truncation=False, padding=False))
                for case in cases['cases']]
            require(all(0 < length <= source.MAX_CONTEXT for length in lengths), 'context_bound')
            engine = source.Engine(arguments, tokenizer, check=check)
            from organism_v6.pcfl_vertical_train import _state_hash

            parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                          if '.lora_A.' in name or '.lora_B.' in name}
            before = _state_hash(parameters)
            require(bool(parameters) and before == provenance['expected_actor_state_sha256'],
                    'actual_after_actor_required')
            result.update(driver.select_corrective(engine, cases, output, provenance))
            engine.verify_base()
            require(_state_hash(parameters) == before, 'read_only_adapter_changed')
            for name, digest in provenance['adapter_files'].items():
                require(source.file_hash(Path(arguments.adapter_dir) / name) == digest, 'adapter_artifact_changed')
            require(all(source.file_hash(Path(options.after) / name) == digest
                        for name, digest in provenance['source_files'].items()), 'after_artifact_changed')
            result.update(status='RESELECTION_CAPTURED_NO_FIT', loaded_adapter_state_sha256=before,
                          runtime=engine.runtime, prompt_tokens=lengths, frozen_base_unchanged=True)
        result['finished_unix'] = time.time()
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
