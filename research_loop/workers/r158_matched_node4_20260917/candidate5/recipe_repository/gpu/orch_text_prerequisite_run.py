"""Bounded read-only portable37ec / native TextWorld screen."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import time

from organism_v6 import orch_text_prerequisite as protocol


BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')


def source_check(root):
    manifest = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
    for name, expected in manifest.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(root / name) != expected:
            raise ValueError('source_binding:' + name)
    return dict(files=len(manifest), manifest_sha256=sha(root / 'SOURCE_MANIFEST.json'))


class NativeEnvironment:
    def __init__(self, python, game):
        self.process = subprocess.Popen([python, '-B', str(Path(__file__).with_name('orch_text_prerequisite_env.py')),
            'serve', str(game)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
        self.state = self.read()

    def read(self):
        if not select.select([self.process.stdout], [], [], 30)[0]:
            raise TimeoutError('native_cpu_interface_timeout')
        return json.loads(self.process.stdout.readline())

    def step(self, action):
        self.process.stdin.write(json.dumps(dict(action=action)) + '\n')
        self.process.stdin.flush()
        self.state = self.read()
        return self.state

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=15)
        self.process.stdout.close()


def episode(task, arm, engine, options, output, calls):
    record = dict(task_id=task['id'], family=task['family'], arm=arm, turns=[], success=False,
                  error=None, admitted=False, semantic_status='UNRESOLVED', student_loss_targets=0)
    environment = None
    previous = None
    format_feedback = None
    try:
        environment = NativeEnvironment(options.env_python, Path(options.games) / task['game'])
        if environment.state != task['initial']:
            raise ValueError('native_initial_state_drift')
        for turn in range(protocol.MAX_TURNS):
            engine.check('turn')
            request = protocol.messages(task, environment.state, arm, turn, previous, format_feedback)
            tokens = engine.tokenizer.apply_chat_template(request, tokenize=True,
                add_generation_prompt=True, return_dict=False)
            if type(tokens) is not list or not 0 < len(tokens) <= protocol.MAX_CONTEXT:
                raise ValueError('context_bound_no_truncation')
            if len(calls) >= 24:
                raise ValueError('shard_call_cap')
            capture = dict(task_id=task['id'], arm=arm, turn=turn, messages=request,
                native_before=environment.state, student_prefix=protocol.student_prefix(task, environment.state),
                response=None, projection=None, format_error=None, prose_tokens=None,
                native_after=None, model_error=None, started_unix=time.time())
            calls.append(capture)
            try:
                capture['response'] = engine.generate(request, max_new_tokens=protocol.MAX_GENERATED)
            except Exception as error:
                capture['model_error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(output / f'CALL_{len(calls)-1:03d}.json', capture)
            response = capture['response']
            try:
                capture['projection'] = protocol.parse(response['raw'], arm, response['terminal'], response['truncated'])
            except ValueError as error:
                capture['format_error'] = str(error)
                format_feedback = 'Format rejected; no native action executed. ' + str(error)
            else:
                projection = capture['projection']
                capture['prose_tokens'] = len(engine.tokenizer.encode(projection['prose'], add_special_tokens=False))
                capture['native_after'] = environment.step(projection['action'])
                format_feedback = None
            capture['finished_unix'] = time.time()
            write(output / f"{task['id']}_{arm}_TURN{turn}.json", capture)
            record['turns'].append(capture)
            previous = dict(observation=request[-1]['content'], raw=response['raw'])
            if environment.state['won']:
                record['success'] = True
                break
            if environment.state['lost']:
                break
    except Exception as error:
        record['error'] = dict(type=type(error).__name__, message=str(error))
    finally:
        if environment:
            environment.close()
        write(output / f"{task['id']}_{arm}_EPISODE.json", record)
    return record


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'games', 'env-python', 'output', 'source-archive', 'source-sha'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=['prepare', 'screen'], required=True)
    parser.add_argument('--shard', type=int, choices=range(4), default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline', type=int)
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    source_root = Path(__file__).resolve().parents[1]
    calls = []
    result = dict(status='STARTING', options=vars(options), started_unix=time.time(), fits=0,
                  updates=0, model_calls=0, episodes=[], fit_ready=False)
    write(output / 'REQUEST.json', result)
    try:
        if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
            raise ValueError('offline_required')
        if sha(options.source_archive) != options.source_sha:
            raise ValueError('source_archive_mismatch')
        result['source'] = source_check(source_root)
        bank_path = Path(options.games) / 'BANK.json'
        if sha(bank_path) != protocol.BANK_SHA:
            raise ValueError('frozen_bank_mismatch')
        bank = json.loads(bank_path.read_text())
        for task in bank['tasks']:
            if sha(Path(options.games) / task['game']) != task['game_sha256']:
                raise ValueError('native_game_drift')
            if sha(Path(options.games) / task['game'].replace('.z8', '.json')) != task['json_sha256']:
                raise ValueError('native_game_metadata_drift')
        from gpu import astra_portable_actor_bundle as portable

        result['provenance'] = portable.verify_base_files(options.bundle, options.model_dir,
            expected_manifest_sha256=BUNDLE_SHA)
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_GPU', bank_sha256=protocol.BANK_SHA,
                          pairs=8, held=4, finished_unix=time.time())
            write(output / 'RESULT.json', result)
            return
        if not options.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != options.gpu_uuid:
            raise ValueError('physical_uuid_binding_required')
        if not options.deadline or not time.time() < options.deadline <= time.time() + 1800:
            raise ValueError('1800_second_bound_required')

        def check(label):
            if time.time() >= options.deadline - 60:
                raise TimeoutError('screen_deadline:' + label)

        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=BUNDLE_SHA,
            model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments,
            portable.source.native.load_local_tokenizer(options.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: value for name, value in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        if not parameters or _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('mounted_parameter_hash_mismatch')
        if any(value.requires_grad for value in engine.model.parameters()):
            raise ValueError('inference_only')
        write(output / 'LOADED.json', dict(pid=os.getpid(), cvd=os.environ['CUDA_VISIBLE_DEVICES'],
            adapter_state=portable.PARENT_STATE, runtime=engine.runtime))
        tasks = [task for task in bank['tasks'] if task['split'] == 'mining' and task['shard'] == options.shard]
        if len(tasks) != 2:
            raise ValueError('two_frozen_pairs_per_shard')
        arms = ('RICH', 'TERSE') if options.shard % 2 == 0 else ('TERSE', 'RICH')
        for task in tasks:
            for arm in arms:
                result['episodes'].append(episode(task, arm, engine, options, output, calls))
        engine.verify_base()
        if _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('adapter_mutated')
        source_check(source_root)
        result.update(status='COMPLETE', model_calls=len(calls), adapter_after=portable.PARENT_STATE,
                      base_unchanged=True, finished_unix=time.time())
        write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error_type=type(error).__name__, error=str(error),
                      model_calls=len(calls), finished_unix=time.time())
        write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
