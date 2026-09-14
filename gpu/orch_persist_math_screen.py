"""Bounded offline native portable37ec collection; no training or target admission."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import time

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_persist_math as curriculum


BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
PROTOCOL = 'research_notes/analysis/orch_persist_math_protocol.md'


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def helpers():
    return {name: portable.source.file_hash(path) for name, path in dict(
        driver=__file__, curriculum=curriculum.__file__,
        guard=Path(__file__).with_name('orch_persist_math_guard.sh'),
        protocol=Path(__file__).resolve().parents[1] / PROTOCOL).items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'model-dir', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'screen'), required=True)
    parser.add_argument('--arm', choices=('RICH', 'TERSE'), required=True)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline-epoch', type=int)
    options = parser.parse_args(argv)
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(arguments=vars(options), started_unix=started, fits=0, updates=0,
        admitted_targets=0, model_calls=0, helpers=helpers(),
        curriculum_sha256=curriculum.digest(curriculum.curriculum()), families=curriculum.FAMILIES)
    write(output / 'REQUEST.json', result)
    calls = []

    def check(label):
        if options.phase == 'screen' and (not options.deadline_epoch or time.time() >= options.deadline_epoch):
            raise ValueError('hard_native_deadline:' + label)

    try:
        if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
            raise ValueError('offline_environment_required')
        manifest = portable.read_manifest(options.bundle, expected_manifest_sha256=BUNDLE_SHA)
        result['base_verification'] = portable.verify_base_files(options.bundle, options.model_dir,
            expected_manifest_sha256=BUNDLE_SHA)
        result['bundle_manifest_sha256'] = BUNDLE_SHA
        result['source_contract'] = manifest['source_contract']
        write(output / 'CURRICULUM.json', curriculum.curriculum())
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            write(output / 'RESULT.json', result)
            return result
        if not options.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != options.gpu_uuid:
            raise ValueError('exclusive_physical_gpu_required')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=BUNDLE_SHA,
            model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, portable.source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
            if '.lora_A.' in name or '.lora_B.' in name}
        if not parameters or _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('mounted_adapter_state_drift')
        if any(parameter.requires_grad for parameter in engine.model.parameters()):
            raise ValueError('all_weights_must_be_frozen')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=portable.PARENT_STATE,
            native_pid=os.getpid(), cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'])
        write(output / 'LOADED.json', result)

        def generate(messages, **metadata):
            check('call')
            if len(calls) >= curriculum.MAX_CALLS:
                raise ValueError('native_call_budget')
            prompt_tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            if len(prompt_tokens) + curriculum.MAX_GENERATED > curriculum.MAX_CONTEXT:
                raise ValueError('context_plus_generation_exceeds_2048_no_truncation')
            capture = dict(call_index=len(calls), messages=deepcopy(messages), metadata=metadata,
                response=None, error=None, started_unix=time.time())
            calls.append(capture)
            try:
                capture['response'] = engine.generate(messages, max_new_tokens=curriculum.MAX_GENERATED)
                try:
                    prose = curriculum.project(capture['response']['raw'])['prose']
                    capture['prose_tokens'] = len(engine.tokenizer.encode(prose, add_special_tokens=False))
                except ValueError:
                    capture['prose_tokens'] = None
                return deepcopy(capture['response'])
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                capture['finished_unix'] = time.time()
                write(output / f"CALL_{capture['call_index']:03d}.json", capture)

        data = curriculum.screen(generate, options.arm, lambda name, value: write(output / name, value))
        write(output / 'DATA.json', data)
        engine.verify_base()
        if _state_hash(parameters) != portable.PARENT_STATE or helpers() != result['helpers']:
            raise ValueError('readonly_state_or_source_drift')
        result.update(status='COMPLETE', model_calls=len(calls), summary={key: value for key, value in data.items()
            if key != 'episodes'}, frozen_base_unchanged=True, adapter_state_after=portable.PARENT_STATE,
            finished_unix=time.time())
        write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error_type=type(error).__name__, error=str(error),
            model_calls=len(calls), finished_unix=time.time())
        write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
