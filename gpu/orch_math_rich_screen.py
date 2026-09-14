"""Bounded native public-math screen using the unchanged portable actor API."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_math_rich as math


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'bundle-sha', 'model-dir', 'tasks', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'screen'), required=True)
    parser.add_argument('--shard', type=int, choices=range(4), default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--seconds', type=int, default=2700)
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    document = json.loads(Path(options.tasks).read_text())
    tasks = document['tasks']
    assert len(tasks) == 32 and document['per_family'] == math.PER_FAMILY
    assert os.environ['HF_HUB_OFFLINE'] == os.environ['TRANSFORMERS_OFFLINE'] == '1'
    binding = dict(arguments=vars(options), started_unix=started,
                   pid=os.getpid(), cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                   tasks_sha256=hashlib.sha256(Path(options.tasks).read_bytes()).hexdigest(),
                   driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   policy_sha256=hashlib.sha256(Path(math.__file__).read_bytes()).hexdigest(),
                   trainingAllowed=False, fits=0, updates=0, fit_ready=False)
    write(output / 'REQUEST.json', binding)
    rows = []
    engine = None

    def check(label):
        if time.time() >= started + options.seconds:
            raise TimeoutError('bounded_screen:' + label)

    try:
        manifest = portable.read_manifest(options.bundle, expected_manifest_sha256=options.bundle_sha)
        assert manifest['parent_state'] == portable.PARENT_STATE
        binding['base_verification'] = portable.verify_base_files(options.bundle, options.model_dir,
                                                                 expected_manifest_sha256=options.bundle_sha)
        if options.phase == 'prepare':
            write(output / 'RESULT.json', dict(binding, status='PREPARED_NO_MODEL', model_calls=0))
            return
        assert os.environ['CUDA_VISIBLE_DEVICES'] == options.gpu_uuid
        assert ('CUDA_VISIBLE_DEVICES=' + options.gpu_uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=options.bundle_sha,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, portable.source.native.load_local_tokenizer(options.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        import peft
        assert _state_hash(peft.get_peft_model_state_dict(engine.model)) == portable.PARENT_STATE
        write(output / 'ACTOR_READY.json', dict(binding, runtime=engine.runtime, adapter_state=portable.PARENT_STATE))

        def generate(task, kind, previous=None):
            check('call')
            assert len(rows) < 32
            messages, student = math.prompt(task, kind, previous)
            encoded = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            assert len(encoded) <= 2048
            result = engine.generate(messages, max_new_tokens=64 if kind == 'terse' else 512)
            row = math.capture(task, kind, result, student)
            rows.append(row)
            write(output / f'CALL_{len(rows):04d}.json', row)
            return row

        for position, task in enumerate(tasks):
            if position % 4 != options.shard:
                continue
            order = ('rich', 'terse') if (position // 4) % 2 else ('terse', 'rich')
            calls = {kind: generate(task, kind) for kind in order}
            solved = calls['rich']
            if not solved['outcome_pass']:
                solved = generate(task, 'correction', solved['target'])
            if solved['outcome_pass']:
                generate(task, 'record', solved['target'])
        engine.verify_base()
        assert _state_hash(peft.get_peft_model_state_dict(engine.model)) == portable.PARENT_STATE
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', model_calls=len(rows),
              finished_unix=time.time(), adapter_state=portable.PARENT_STATE,
              summary=math.reduce_screen(tasks, rows)))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, status='FAILED', model_calls=len(rows),
                                          error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


if __name__ == '__main__':
    main()
