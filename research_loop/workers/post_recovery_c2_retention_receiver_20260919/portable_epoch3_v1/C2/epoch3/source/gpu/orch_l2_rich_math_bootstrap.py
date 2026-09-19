"""Paired FULL/OFF bootstrap in separate bounded native processes."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_math_rich_source import verify_archive
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_rich_math as policy
from organism_v6 import orch_l2_shared as existing
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
UUID = 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8'
SCANNER_SHA = '6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b'
SERVICES_SHA = '4a96b33797ab47ed7a1685de0ffe6c7ec4d210c143b720b85519b0ca05265391'
LEASE_END = 1790463900


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.partial')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def sha(path):
    return bridge.file_sha256(path)


def prepare(root, bundle, model_dir):
    assert not (root / 'PREPARE.json').exists()
    assert sha(root / 'ADMITTED.json') == policy.PACKET_SHA
    packet = read(root / 'ADMITTED.json')
    validated = policy.validate_packet(packet)
    manifest = portable.read_manifest(bundle, expected_manifest_sha256=BUNDLE_SHA)
    base = portable.verify_base_files(bundle, model_dir, expected_manifest_sha256=BUNDLE_SHA)
    identity = bridge.AdapterIdentity(str(bundle / 'adapter'), portable.PARENT_STATE,
        manifest['expected_base_sha256'], tuple(manifest['adapter_files'].items())).verify()
    tokenizer = native.source.native.load_local_tokenizer(str(model_dir))
    new = policy.encode_packet(packet, tokenizer)
    legacy = legacy_encode(root, tokenizer)
    layout = GoalReplayLayout(16, policy.BOOTSTRAP_PRESENTATIONS)
    native.assemble_replay(legacy, new, layout, legacy_reference=legacy, eos_token_id=tokenizer.eos_token_id)
    write(root / 'NEW_MASKS.json', [asdict(row) for row in new])
    write(root / 'COHORT.json', policy.cohort())
    write(root / 'INITIAL.json', identity.document())
    prepared = dict(packet=validated, packet_sha256=policy.PACKET_SHA, initial=identity.document(),
        model_dir=str(model_dir), bundle=str(bundle), verified_base=base,
        source_files_verified=verify_archive(root / 'source.tar', root / 'source'),
        source_sha256=sha(root / 'source.tar'),
        files={name: sha(root / name) for name in ('ADMITTED.json', 'LEGACY_MATERIAL.json',
            'OLD_MASKS.json', 'LEGACY_READOUT.json', 'NEW_MASKS.json', 'COHORT.json', 'INITIAL.json')},
        full=layout.manifest('FULL_TARGET'), off=layout.manifest('NEW_TRAJECTORY_LOSS_OFF'),
        recipe=existing.RECIPE, hours=policy.HOURS, aggregate_gpu_hours=policy.GPU_HOURS,
        learner_calls=policy.LEARNER_CALLS, parent_provider_calls=policy.PARENT_CALLS,
        prepared_unix=time.time(), native_calls=0, updates=0)
    write(root / 'PREPARE.json', prepared)


def train(root, arm):
    prepared, lifetime = read(root / 'PREPARE.json'), read(root / 'LIFETIME.json')
    output = root / arm
    output.mkdir(exist_ok=False)
    assert os.environ['CUDA_VISIBLE_DEVICES'] == UUID
    assert ('CUDA_VISIBLE_DEVICES=' + UUID).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files_verified']
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    identity = bridge.AdapterIdentity.from_document(prepared['initial'])
    binding = bridge.StageBinding(root.name, bridge.ARMS[2], 0, 'training', identity,
                                  False, False, sha(root / 'PREPARE.json'))
    recipe = {key: existing.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
    plan = SimpleNamespace(binding=lambda unused: binding,
        contract=SimpleNamespace(manifest=lambda unused: dict(recipe=recipe)),
        lineage=SimpleNamespace(arm=bridge.ARMS[2]))

    def check(label):
        assert time.time() < lifetime['deadline_unix'], 'pilot_deadline:' + label

    started = time.time()
    write(output / 'REQUEST.json', dict(arm=arm, input_adapter=identity.document(),
          process=native.process_identity(), started_unix=started, uuid=UUID))
    try:
        loaded = native.load_training(plan, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=UUID,
            context=native.StageContext(), check=check)
        write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
                                          started_unix=started, uuid=UUID))
        new = policy.encode_packet(read(root / 'ADMITTED.json'), loaded.engine.tokenizer)
        assert policy.digest([asdict(row) for row in new]) == policy.digest(read(root / 'NEW_MASKS.json'))
        legacy = legacy_encode(root, loaded.engine.tokenizer)
        layout = GoalReplayLayout(16, policy.BOOTSTRAP_PRESENTATIONS)
        encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy,
                                        eos_token_id=loaded.engine.tokenizer.eos_token_id)
        replay_arm = 'FULL_TARGET' if arm == 'FULL' else 'NEW_TRAJECTORY_LOSS_OFF'
        write(output / 'RECIPE.json', dict(layout=layout.manifest(replay_arm), recipe=recipe,
                                           packet_sha256=policy.PACKET_SHA, input_adapter=identity.document()))
        torch = loaded.engine.torch
        parameters = {name: parameter for name, parameter in loaded.engine.model.named_parameters() if native.is_lora(name)}
        with (output / 'LOSSES.jsonl').open('x') as stream:
            for update in range(1, layout.updates + 1):
                check('update')
                indexes, batch, reference, active, scale = native.training_batch(encoded, layout, update,
                    pad_id=loaded.engine.tokenizer.pad_token_id, replay_arm=replay_arm)
                tensors = {name: torch.tensor(value, dtype=torch.long, device=loaded.engine.device) for name, value in batch.items()}
                loaded.optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                    loss = loaded.engine.model(**tensors, use_cache=False).loss * scale
                assert bool(torch.isfinite(loss))
                loss.backward()
                assert all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in parameters.values())
                loaded.optimizer.step()
                stream.write(json.dumps(dict(update=update, loss=loss.item(), rows=indexes,
                                              reference=reference, active=active, scale=scale)) + '\n')
                stream.flush()
        assert all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values())
        loaded.engine.verify_base()
        loaded.engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
        saved = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
            tuple((path.name, sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
        assert native.observe_adapter(loaded.engine, saved) == saved
        write(output / 'COMPLETE.json', dict(status='COMPLETE', input_adapter=identity.document(),
            output_adapter=saved.document(), process=loaded.process, started_unix=started,
            finished_unix=time.time(), updates=layout.updates, learner_calls=0,
            layout=layout.manifest(replay_arm), unchanged=saved.state_sha256 == identity.state_sha256))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


def launch(root):
    prepared, publication = read(root / 'PREPARE.json'), read(root / 'PUBLICATION.json')
    assert publication['prepare_sha256'] == sha(root / 'PREPARE.json') and publication['cpu_tests_passed']
    assert prepared['source_sha256'] == sha(root / 'source.tar')
    assert sha(root / 'scanner.py') == SCANNER_SHA and sha(root / 'service_exceptions.json') == SERVICES_SHA
    started = time.time()
    assert started + policy.HOURS * 3600 < LEASE_END - 21600
    child = None
    child_identity = None
    try:
        for arm in ('FULL', 'OFF'):
            with (root / 'service_exceptions.json').open() as services:
                result = subprocess.run(['python3', str(root / 'scanner.py'), '3', UUID],
                    stdin=services, capture_output=True, text=True, timeout=40,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
            write(root / f'{arm}_ADMISSION.json', dict(code=result.returncode, stdout=result.stdout, stderr=result.stderr))
            assert result.returncode == 0 and json.loads(result.stdout)['clear'], 'physical_admission_failed'
            if arm == 'FULL':
                started = time.time()
                with (root / 'LIFETIME.json').open('x') as stream:
                    json.dump(dict(started_unix=started, deadline_unix=started + policy.HOURS * 3600 - 30,
                        hard_deadline_unix=started + policy.HOURS * 3600, aggregate_gpu_hours=16,
                        learner_call_cap=1536, parent_provider_call_cap=192), stream)
            deadline = read(root / 'LIFETIME.json')['deadline_unix']
            with (root / f'{arm}.log').open('x') as log:
                child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_l2_rich_math_bootstrap', 'train',
                    '--root', str(root), '--arm', arm], cwd=root / 'source',
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=UUID), stdout=log, stderr=subprocess.STDOUT)
                child_identity = Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
                write(root / f'{arm}_LAUNCH.json', dict(pid=child.pid, start_ticks=child_identity,
                                                       uuid=UUID, started_unix=time.time(), deadline_unix=deadline))
                assert child.wait(timeout=max(1, deadline - time.time())) == 0, 'bootstrap_failed_no_retry'
        snapshot = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory',
                                   '--format=csv,noheader'], capture_output=True, text=True, check=True)
        assert UUID not in snapshot.stdout, 'bootstrap_gpu_not_released'
        write(root / 'BOOTSTRAP_TERMINAL.json', dict(status='COMPLETE', started_unix=started,
            finished_unix=time.time(), assigned_gpu_hours=(time.time() - started) / 3600,
            a100_device3_released=True, release_compute_inventory=snapshot.stdout,
            learner_calls=0, parent_calls=0, next_phase='TRANSFER_SAVED_FULL_OFF_THEN_NODE2_4_7'))
    finally:
        if child is not None and child.poll() is None:
            assert Path(f'/proc/{child.pid}').stat().st_uid == os.getuid()
            assert Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19] == child_identity
            child.send_signal(signal.SIGKILL)
            child.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'train', 'launch'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--arm', choices=('FULL', 'OFF'))
    options = parser.parse_args()
    root = options.root.resolve()
    assert root.parent == Path('/localhome/local-rohing') and root.name.startswith('orch_l2_rich_math_')
    if options.phase == 'prepare':
        prepare(root, options.bundle, options.model_dir)
    elif options.phase == 'train':
        train(root, options.arm)
    else:
        launch(root)


if __name__ == '__main__':
    main()
