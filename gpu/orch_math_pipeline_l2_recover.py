"""Forensic replay of logged optimizer steps; never regenerate experience."""

import argparse
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu import orch_l2_shared_run as legacy
from gpu import orch_math_pipeline_l2_native as source
from gpu import orch_math_pipeline_l2_run as common
from organism_v6 import orch_guided_bridge as bridge


def admission_module():
    specification = importlib.util.spec_from_file_location('math_recovery_lane', Path(__file__).with_name('orch_math_pipeline_l2_lane.py'))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_steps(records):
    assert records and [record['update'] for record in records] == list(range(1, len(records) + 1))
    assert all(record['matched_learning_rate'] == 3e-5 and record['supervised_tokens'] > 0 for record in records)
    assert all(record['source']['kind'] in ('past_attempt', 'past_reflection', 'canonical_legacy') for record in records)


def require_identical_loss(actual, expected):
    assert actual == expected, f'reconstruction_loss_mismatch_no_tolerance_waiver:{actual.hex()}:{expected.hex()}'


def materials(root, arm, tokenizer):
    campaign = root / 'campaign_01_existing_rich'
    original = campaign / arm / 'cycle1/experience'
    records = [json.loads(line) for line in (original / 'LOSSES.jsonl').read_text().splitlines()]
    validate_steps(records)
    rows = common.read(original / 'ROWS.json')
    encoded = {}
    tasks = common.read(campaign / 'COHORT.json')['train'][0]
    positions = {task['id']: index for index, task in enumerate(tasks)}
    references = {str(original / 'LOSSES.jsonl'): common.sha(original / 'LOSSES.jsonl'),
        str(original / 'ROWS.json'): common.sha(original / 'ROWS.json')}
    for row in rows:
        source.source_row(campaign, row)
        mask = source.encode_row(row, tokenizer)
        path = original / f'MASK_{positions[row["episode_id"]]:02d}_{row["kind"]}.json'
        assert json.loads(json.dumps(asdict(mask))) == common.read(path), 'original_mask_mismatch'
        references[str(path)] = common.sha(path)
        references[str(campaign / row['source_call_path'])] = row['source_call_sha256']
        encoded[(row['episode_id'], row['kind'])] = mask
    old = legacy.legacy_encode(root, tokenizer)
    joined = []
    for record in records:
        label = record['source']
        if label['kind'] == 'canonical_legacy':
            mask = old[label['row']]
        else:
            row = next(row for row in rows if row['episode_id'] == label['episode_id'] and row['kind'] == label['kind'])
            assert row['source_call_sha256'] == label['source_call_sha256']
            mask = encoded[(label['episode_id'], label['kind'])]
        assert sum(value != -100 for value in mask.labels[1:]) == record['supervised_tokens']
        joined.append(mask)
    return original, records, joined, references


def prepare(root, arm):
    prepared = common.validate(root)
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    tokenizer = native.source.native.load_local_tokenizer(prepared['model_dir'])
    original, records, unused, references = materials(root, arm, tokenizer)
    assert not (original / 'adapter').exists() and not (original / 'COMPLETE.json').exists()
    destination = root / f'RECOVERY_READY_{arm}.json'
    assert not destination.exists()
    common.write(destination, dict(source_sha256=common.sha(Path(__file__)), lane_sha256=common.sha(Path(__file__).with_name('orch_math_pipeline_l2_lane.py')),
        original_lifetime_sha256=common.sha(root / 'LIFETIME.json'), references=references,
        original_updates=len(records), native_generation_calls=0, source_masks_verified=True,
        original_final_state_hash_unavailable=True, acceptance='ALL_LOGGED_LOSSES_BITWISE_FLOAT_EQUAL_NO_TOLERANCE',
        not_a_new_foundation_or_epoch=True, l2_only_quarantine=True))
    print(json.dumps(dict(arm=arm, updates=len(records), ready_sha256=common.sha(destination))))


def run(root, arm):
    ready = common.read(root / f'RECOVERY_READY_{arm}.json')
    assert ready['source_sha256'] == common.sha(Path(__file__))
    assert all(common.sha(path) == digest for path, digest in ready['references'].items())
    prepared = common.validate(root)
    lifetime = common.read(root / 'LIFETIME.json')
    assert ready['original_lifetime_sha256'] == common.sha(root / 'LIFETIME.json')
    uuid = common.policy.DEVICES[arm][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    output = root / f'RECOVERY_{arm}'
    output.mkdir(exist_ok=False)
    campaign = root / 'campaign_01_existing_rich'
    initial = common.read(campaign / 'INITIAL.json')
    identity = bridge.AdapterIdentity.from_document(initial['output_adapter'])
    original_request = common.read(campaign / arm / 'cycle1/experience/REQUEST.json')
    binding = bridge.StageBinding('FORENSIC_RECOVERY_' + arm, bridge.ARMS[2], 1, 'training', identity,
        False, True, common.sha(root / f'RECOVERY_READY_{arm}.json'))
    recipe = {key: source.recipe_source.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
    plan = SimpleNamespace(binding=lambda unused: binding, contract=SimpleNamespace(manifest=lambda unused: dict(recipe=recipe)),
        lineage=SimpleNamespace(arm=binding.arm))
    def check(label):
        assert time.time() < lifetime['native_deadline_unix'], 'original_lifetime:' + label
    counter = campaign / ('CALLS_NATIVE_' + arm + '.jsonl')
    counter_before = common.sha(counter)
    try:
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=common.BUNDLE_SHA)
        loaded = native.load_training(plan, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=check, engine_factory=source.Engine,
            predecessor_processes=(tuple(original_request['process']),))
        engine = loaded.engine
        common.write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process, uuid=uuid))
        unused, records, encoded, references = materials(root, arm, engine.tokenizer)
        assert references == ready['references']
        parameters = {name: parameter for name, parameter in engine.model.named_parameters() if native.is_lora(name)}
        with (output / 'REPLAYED_UPDATES.jsonl').open('x') as log:
            for record, mask in zip(records, encoded):
                check('reconstruct_recorded_step')
                engine.model.train()
                tensors = dict(input_ids=engine.torch.tensor([mask.input_ids], dtype=engine.torch.long, device=engine.device),
                    labels=engine.torch.tensor([mask.labels], dtype=engine.torch.long, device=engine.device))
                tensors['attention_mask'] = engine.torch.ones_like(tensors['input_ids'])
                loaded.optimizer.zero_grad(set_to_none=True)
                with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
                    loss = engine.model(**tensors, use_cache=False).loss
                assert bool(engine.torch.isfinite(loss))
                actual = loss.item()
                require_identical_loss(actual, record['loss'])
                loss.backward()
                assert all(parameter.grad is not None and bool(engine.torch.isfinite(parameter.grad).all()) for parameter in parameters.values())
                loaded.optimizer.step()
                log.write(json.dumps(dict(logical_update=record['update'], physical_reconstruction_update=record['update'],
                    actual_loss=actual, original_loss=record['loss'], exact_loss_match=True, observed_unix=time.time())) + '\n')
                log.flush()
        engine.verify_base()
        engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
        saved = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
            tuple((path.name, common.sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
        assert native.observe_adapter(engine, saved) == saved
        engine.torch.save(loaded.optimizer.state_dict(), output / 'optimizer.pt')
        engine.torch.save(dict(cpu=engine.torch.get_rng_state(), cuda=engine.torch.cuda.get_rng_state()), output / 'rng.pt')
        assert counter_before == common.sha(counter), 'reconstruction_must_not_generate_or_reserve_experience'
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=common.BUNDLE_SHA)
        common.write(output / 'COMPLETE.json', dict(status='RECONSTRUCTION_VERIFIED', arm=arm,
            output_adapter=saved.document(), process=loaded.process, original_updates=len(records),
            physical_reconstruction_updates=len(records), native_generation_calls=0,
            all_logged_losses_exact=True, original_final_state_hash_unavailable=True,
            not_a_claim_of_original_saved_identity=True, optimizer_sha256=common.sha(output / 'optimizer.pt'),
            rng_sha256=common.sha(output / 'rng.pt'), finished_unix=time.time()))
        common.write(output / 'AFTER.json', dict(observed=saved.document(), process=loaded.process,
            mounted_and_frozen_base_verified=True))
    except BaseException as error:
        common.write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error),
            native_generation_calls=0, no_state_accepted=True, finished_unix=time.time()))
        raise


def launch(root, arm):
    ready = root / f'RECOVERY_READY_{arm}.json'
    document = common.read(ready)
    assert common.sha(Path(__file__)) == document['source_sha256']
    assert common.sha(Path(__file__).with_name('orch_math_pipeline_l2_lane.py')) == document['lane_sha256']
    lifetime = common.read(root / 'LIFETIME.json')
    with (root / f'RECOVERY_CLAIM_{arm}.json').open('x') as stream:
        json.dump(dict(ready_sha256=common.sha(ready), started_unix=time.time()), stream)
    admission_module().admit(root, arm, 1, 'forensic_recovery', lifetime['native_deadline_unix'])
    log = (root / f'RECOVERY_{arm}.log').open('x')
    child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'run', '--root', str(root), '--arm', arm],
        cwd=root / 'source', start_new_session=True,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES=common.policy.DEVICES[arm][1], PYTHONPATH=str(root / 'source'),
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
            TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT)
    identity = common.process_identity(Path('/proc') / str(child.pid))
    common.write(root / f'RECOVERY_LAUNCH_{arm}.json', dict(identity=identity, uuid=common.policy.DEVICES[arm][1], launched_unix=time.time()))
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        assert child.wait(timeout=max(1, lifetime['native_deadline_unix'] - time.time())) == 0, 'reconstruction_failed_no_experience_replay'
    finally:
        common.stop_owned(child, identity)
        log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'launch'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--arm', choices=('GUIDED_SLEEP', 'UNPARENTED_SLEEP'), required=True)
    options = parser.parse_args()
    {'prepare': prepare, 'run': run, 'launch': launch}[options.phase](options.root, options.arm)
