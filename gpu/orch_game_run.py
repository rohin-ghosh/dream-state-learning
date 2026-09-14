"""Portable37ec inference-only deterministic game screen, never a fit launcher."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from organism_v6 import orch_game_screen as screen


BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
BANK_SHA = '8d12ddb1e71df09fde3bacbb7eed83cbf9ee1a88e557667a9209ee0d1455dbc1'


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')


def bank_from(path):
    if file_hash(path) != BANK_SHA:
        raise ValueError('frozen_bank_bytes_required')
    bank = json.loads(Path(path).read_text())
    if screen.digest(bank['transitions']) != bank['oracle_sha256']:
        raise ValueError('native_oracle_hash_mismatch')
    if screen.freeze(bank) != bank['instances']:
        raise ValueError('prospective_roster_mismatch')
    return bank


def verify_source(root, manifest):
    records = json.loads(Path(manifest).read_text())
    for name, expected in records.items():
        path = Path(root) / name
        if Path(name).is_absolute() or '..' in Path(name).parts or file_hash(path) != expected:
            raise ValueError('source_file_binding_mismatch:' + name)
    return dict(files=len(records), manifest_sha256=file_hash(manifest))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bank', 'bundle', 'model-dir', 'output', 'source-archive', 'source-sha', 'source-manifest'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', required=True, choices=['prepare', 'screen'])
    parser.add_argument('--shard', type=int, choices=range(4), default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline', type=int)
    options = parser.parse_args()
    if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
        raise ValueError('offline_only')
    if file_hash(options.source_archive) != options.source_sha:
        raise ValueError('archive_sha_required')
    source_binding = verify_source(Path(__file__).resolve().parents[1], options.source_manifest)
    output = Path(options.output)
    output.mkdir(exist_ok=False, parents=True)
    request = dict(arguments=vars(options), started_unix=time.time(), fit_ready=False, fits=0,
                   updates=0, base_downloads=0, source=source_binding, bank_sha256=BANK_SHA)
    write(output / 'REQUEST.json', request)
    try:
        from gpu import astra_portable_actor_bundle as portable

        bank = bank_from(options.bank)
        provenance = portable.verify_base_files(options.bundle, options.model_dir,
                                                expected_manifest_sha256=BUNDLE_SHA)
        if options.phase == 'prepare':
            write(output / 'RESULT.json', dict(status='PREPARED_NO_GPU', provenance=provenance,
                source=source_binding, bank_sha256=BANK_SHA, native_transitions_verified=3000,
                mining_instances=16, held_instances=16, fits=0, model_calls=0, fit_ready=False))
            return
        if not options.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != options.gpu_uuid:
            raise ValueError('exact_physical_uuid_binding_required')
        if not options.deadline or not time.time() < options.deadline <= time.time() + 2400:
            raise ValueError('bounded_absolute_deadline_required')

        def check(label):
            if time.time() >= options.deadline - 60:
                raise TimeoutError('screen_deadline:' + label)

        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=BUNDLE_SHA,
            model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, portable.source.native.load_local_tokenizer(options.model_dir),
                                        check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: value for name, value in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        if _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('loaded_portable37ec_mismatch')
        if any(value.requires_grad for value in engine.model.parameters()):
            raise ValueError('readonly_actor_required')
        write(output / 'LOADED.json', dict(pid=os.getpid(), cvd=os.environ['CUDA_VISIBLE_DEVICES'],
            adapter_state=portable.PARENT_STATE, runtime=engine.runtime, source_sha256=options.source_sha))
        calls, episodes = 0, []

        def generate(messages):
            nonlocal calls
            check('generate')
            if calls >= 48:
                raise ValueError('48_call_shard_cap')
            encoded = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            if len(encoded) > screen.MAX_CONTEXT:
                raise ValueError('2048_context_cap_no_truncation')
            call_index = calls
            calls += 1
            capture = dict(index=call_index, messages=messages, response=None, error=None)
            try:
                capture['response'] = engine.generate(messages, max_new_tokens=screen.MAX_NEW_TOKENS)
                return capture['response']
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(output / f'CALL_{call_index:03d}.json', capture)

        instances = [instance for instance in bank['instances']
                     if instance['split'] == 'mining' and instance['shard'] == options.shard]
        if len(instances) != 4:
            raise ValueError('four_frozen_pairs_per_shard')
        for index, instance in enumerate(instances):
            arms = ('RICH', 'TERSE') if (index + options.shard) % 2 == 0 else ('TERSE', 'RICH')
            for arm in arms:
                check('episode')
                prefix = instance['id'] + '_' + arm
                result = screen.episode(bank, instance, arm, generate,
                    lambda turn, record: write(output / f'{prefix}_TURN{turn}.json', record))
                write(output / f'{prefix}_EPISODE.json', result)
                episodes.append(result)
        check('readonly_verify')
        engine.verify_base()
        if _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('adapter_mutated')
        verify_source(Path(__file__).resolve().parents[1], options.source_manifest)
        write(output / 'RESULT.json', dict(status='COMPLETE', model_calls=calls, episodes=episodes,
            fits=0, updates=0, fit_ready=False, adapter_before=portable.PARENT_STATE,
            adapter_after=portable.PARENT_STATE, frozen_base_unchanged=True, finished_unix=time.time()))
    except Exception as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), unix=time.time()))
        raise


if __name__ == '__main__':
    main()
