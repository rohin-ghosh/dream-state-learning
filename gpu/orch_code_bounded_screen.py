"""Read-only portable37ec paired MBPP screen; no fit or generated execution."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from organism_v6 import orch_code_bounded as code


MANIFEST = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def mounted_parameters(model):
    parameters = {name: value for name, value in model.named_parameters()
                  if '.lora_A.' in name or '.lora_B.' in name}
    if not parameters or any(value.requires_grad for name, value in model.named_parameters()):
        raise ValueError('readonly mounted parameters required')
    return parameters


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'tasks', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'screen'), required=True)
    parser.add_argument('--shard', type=int, choices=range(4), default=0)
    parser.add_argument('--gpu-uuid')
    options = parser.parse_args()
    from gpu import astra_portable_actor_bundle as portable
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    start = time.time()
    tasks = json.loads(Path(options.tasks).read_text())['tasks']
    assert len(tasks) == 8
    binding = dict(arguments=vars(options), started_unix=start, pid=os.getpid(), fits=0,
                   tasks_sha256=hashlib.sha256(Path(options.tasks).read_bytes()).hexdigest(),
                   source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   policy_sha256=hashlib.sha256(Path(code.__file__).read_bytes()).hexdigest())
    write(output / 'REQUEST.json', binding)
    rows = []
    engine = None

    def deadline(label):
        if time.time() >= start + 1680:
            raise TimeoutError(label)

    try:
        binding['base_verification'] = portable.verify_base_files(options.bundle, options.model_dir,
                                                                 expected_manifest_sha256=MANIFEST)
        if options.phase == 'prepare':
            write(output / 'RESULT.json', dict(binding, status='PREPARED', model_calls=0))
            return
        assert os.environ['CUDA_VISIBLE_DEVICES'] == options.gpu_uuid
        assert ('CUDA_VISIBLE_DEVICES=' + options.gpu_uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=MANIFEST,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, portable.source.native.load_local_tokenizer(options.model_dir), check=deadline)
        from organism_v6.pcfl_vertical_train import _state_hash
        assert _state_hash(mounted_parameters(engine.model)) == portable.PARENT_STATE
        write(output / 'ACTOR_READY.json', dict(binding, runtime=engine.runtime, adapter_state=portable.PARENT_STATE))
        for position, task in enumerate(tasks):
            if position % 4 != options.shard:
                continue
            for arm in (('terse', 'rich') if position % 2 == 0 else ('rich', 'terse')):
                history = []
                record = False
                for turn in range(4):
                    deadline('call')
                    assert len(rows) < 16
                    messages, student = code.prompt(task, arm, history, record)
                    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                                add_generation_prompt=True, return_dict=False)
                    if len(tokens) > 2048:
                        write(output / f'CONTEXT_STOP_{task["id"]}_{arm}.json', dict(task_id=task['id'], arm=arm, tokens=len(tokens)))
                        break
                    result = engine.generate(messages, max_new_tokens=512)
                    text = result['raw']
                    try:
                        action, rationale = code.parse_action(text, record)
                        feedback = dict(success=True, record=True) if record else code.check(task, action)
                    except Exception as error:
                        rationale = ''
                        feedback = dict(success=False, error=str(error))
                    count = len(result['token_ids']) - int(result['terminal'])
                    row = dict(task_id=task['id'], family=task['family'], arm=arm, turn=turn,
                               kind='record' if record else 'correction' if history else 'solution',
                               target=text, target_sha256=code.sha(text), student_prefix=student,
                               feedback=feedback, generated_tokens=count,
                               rationale_tokens=len(engine.tokenizer.encode(rationale, add_special_tokens=False)),
                               token_contract=150 <= count <= 400 and result['terminal'] and not result['truncated'],
                               semantic_status='UNREVIEWED', admitted=False, call=result)
                    rows.append(row)
                    history.append(row)
                    write(output / f'CALL_{len(rows):03d}.json', row)
                    if record or turn == 2 and not feedback['success']:
                        break
                    record = feedback['success']
        engine.verify_base()
        assert _state_hash(mounted_parameters(engine.model)) == portable.PARENT_STATE
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', model_calls=len(rows),
                                          finished_unix=time.time(), adapter_state=portable.PARENT_STATE))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, model_calls=len(rows), error=repr(error), finished_unix=time.time()))
        raise
if __name__ == '__main__':
    main()
