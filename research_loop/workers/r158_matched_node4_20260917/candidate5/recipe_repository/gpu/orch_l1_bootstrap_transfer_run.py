"""One immutable, read-only, three-state native comparison; no parent or fit."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, LEASE_END, read, sha, write
from gpu.orch_l1_bootstrap_transfer_scan import host_identity, identity as process_identity, scan
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_intensity_screen import Engine
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l1_bootstrap_transfer as policy


ROOT = Path('/localhome/local-rohing/orch_l1_bootstrap_transfer_20260915_attempt1')
PILOT = Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
COHORT_SHA = '3530b667828373408ec6de97f9080c9c1e7a692ee617a90930ce8a9aa1adcbe4'


def validate_inputs(root):
    assert root == ROOT and not root.is_symlink() and host_identity() == policy.HOST_SHA
    prepared = read(root / 'PREPARE.json')
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    assert sha(root / 'source.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files']
    assert all(sha(Path(path)) == digest for path, digest in prepared['pilot_files'].items())
    return prepared


def prepare(root):
    from safetensors.torch import load_file

    assert root == ROOT and host_identity() == policy.HOST_SHA and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert not (root / 'PREPARE.json').exists() and sha(root / 'COHORT.json') == COHORT_SHA
    prior = read(PILOT / 'PREPARE.json')
    manifest = portable.read_manifest(prior['bundle'], expected_manifest_sha256=BUNDLE_SHA)
    base = portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    assert sha(PILOT / 'ADMITTED.json') == policy.PACKET_SHA
    identities = {'ORIGINAL37EC': prior['initial']}
    receipts = {}
    for arm in ('FULL', 'OFF'):
        path = PILOT / arm / 'COMPLETE.json'
        receipt = read(path)
        assert receipt['status'] == 'COMPLETE' and receipt['updates'] == 224
        assert receipt['input_adapter'] == prior['initial'] and receipt['learner_calls'] == 0
        assert receipt['layout']['new_target_presentations'] == 256
        assert receipt['layout']['new_supervised_presentations'] == (256 if arm == 'FULL' else 0)
        identities[arm] = receipt['output_adapter']
        receipts[arm] = receipt
    assert receipts['FULL']['layout']['row_presentations'] == receipts['OFF']['layout']['row_presentations']
    for arm, document in identities.items():
        identity = bridge.AdapterIdentity.from_document(document)
        assert identity.state_sha256 == policy.STATES[arm] and identity.base_sha256 == manifest['expected_base_sha256']
        parameters = load_file(str(Path(identity.path) / 'adapter_model.safetensors'), device='cpu')
        mounted_names = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): tensor
                         for name, tensor in parameters.items()}
        assert native.state_hash(mounted_names) == identity.state_sha256, 'saved_tensor_identity_mismatch'
    cohort = read(root / 'COHORT.json')
    assert not set(manifest['old_ids']).intersection(task['id'] for task in cohort['tasks'])
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    token_counts = [len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
        return_dict=False)) for messages in cohort['prompts']]
    assert max(token_counts) <= 2048 and len(token_counts) == 32
    names = ('COHORT.json', 'DATA_PROVENANCE.json', 'PROTOCOL.md', 'SERVICE_IDENTITY.json')
    pilot_names = ('PREPARE.json', 'ADMITTED.json', 'FULL/COMPLETE.json', 'OFF/COMPLETE.json', 'BOOTSTRAP_TERMINAL.json')
    prepared = dict(status='CPU_PREPARED_NO_MODEL', native_calls=0, training_updates=0,
        prepared_unix=time.time(), model_dir=prior['model_dir'], bundle=prior['bundle'],
        base_verification=base, identities=identities, prompt_token_counts=token_counts,
        source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in names},
        pilot_files={str(PILOT / name): sha(PILOT / name) for name in pilot_names},
        old_ids=manifest['old_ids'], checkpoint_tensor_hashes_verified=True)
    write(root / 'PREPARE.json', prepared)
    print(json.dumps(dict(status=prepared['status'], prepare_sha256=sha(root / 'PREPARE.json'),
        source_sha256=prepared['source_sha256'], source_files=prepared['source_files'],
        prompt_tokens_range=[min(token_counts), max(token_counts)])))


def reserve(output, position, arm, task, messages):
    assert 0 <= position < 32 and arm in policy.ARMS
    path = output / f'CALL_{position:02d}.json'
    row = dict(arm=arm, task_id=task['id'], position=position, messages=messages,
        max_new_tokens=policy.CAP, started_unix=time.time())
    with path.open('x') as stream:
        json.dump(row, stream)
    return path, row


def run(root, arm):
    prepared = validate_inputs(root)
    lifetime = read(root / 'LIFETIME.json')
    uuid = policy.DEVICES[arm][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    output = root / arm
    output.mkdir(exist_ok=False)
    loaded = None
    status = 'FAILED'

    def check(label):
        assert time.time() < lifetime['native_deadline_unix'], 'original_lifetime_expired:' + label

    try:
        check('load')
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
        identity = bridge.AdapterIdentity.from_document(prepared['identities'][arm])
        binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'sealed_readout', identity,
            False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=check, engine_factory=Engine)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
            uuid=uuid, physical_index=policy.DEVICES[arm][0], native_calls=0))
        cohort = read(root / 'COHORT.json')
        for position, (task, messages) in enumerate(zip(cohort['tasks'], cohort['prompts'])):
            check('reserve')
            path, row = reserve(output, position, arm, task, messages)
            try:
                row['response'] = loaded.engine.generate(messages, max_new_tokens=policy.CAP)
                row['score'] = policy.score(task, row['response'])
            except Exception as error:
                row['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                row['finished_unix'] = time.time()
                write(path, row)
        status = 'COMPLETE'
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if loaded is not None:
            try:
                observed = loaded.verify_unchanged()
                portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
                write(output / 'AFTER.json', dict(observed=observed.document(), process=loaded.process,
                    unchanged=True, finished_unix=time.time()))
            except BaseException as error:
                status = 'IDENTITY_VERIFICATION_FAILED'
                write(output / 'AFTER_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        write(output / 'TERMINAL.json', dict(status=status, denominator=32, finished_unix=time.time()))
    assert status == 'COMPLETE'


def reduce(root):
    records = [read(path) for arm in policy.ARMS for path in sorted((root / arm).glob('CALL_*.json'))]
    result = policy.summarize(read(root / 'COHORT.json'), records)
    result['state_verification'] = {arm: (root / arm / 'AFTER.json').exists() for arm in policy.ARMS}
    result['all_states_verified'] = all(result['state_verification'].values())
    write(root / 'SUMMARY.json', result)
    return result


def stop_owned(child, identity):
    if child.poll() is not None:
        return
    assert process_identity(Path('/proc') / str(child.pid)) == identity
    assert identity['uid'] == os.getuid() and os.getpgid(child.pid) == child.pid
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        assert process_identity(Path('/proc') / str(child.pid)) == identity
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=10)


def launch(root, acknowledgment):
    validate_inputs(root)
    ready = read(root / 'READY.json')
    ack = read(acknowledgment)
    assert ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed']
    assert ack['ready_sha256'] == sha(root / 'READY.json') and ack['acknowledged_by'] == 'Main'
    assert ack['dated_builder_line'] and ack['logged_receipt_acknowledged'] is True
    assert ready['cpu_test_log_sha256'] == sha(root / 'CPU_TESTS.log')
    started = time.time()
    assert started + policy.SECONDS < LEASE_END - 21600
    lifetime = dict(started_unix=started, hard_deadline_unix=started + policy.SECONDS,
        native_deadline_unix=started + policy.SECONDS - 180, max_calls=96, assigned_gpu_hours_ceiling=4.5,
        acknowledgment=ack, ready_sha256=sha(root / 'READY.json'))
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, indent=2)
    children, logs = {}, []
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for arm, (index, uuid) in policy.DEVICES.items():
            admission = scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{arm}.json', admission)
            assert admission['clear'] and admission['scanner_euid'] == 0, 'full_proc_admission_failed:' + arm
            assert time.time() < lifetime['native_deadline_unix']
            log = (root / f'{arm}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_l1_bootstrap_transfer_run', 'run',
                '--root', str(root), '--arm', arm], cwd=root / 'source', start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT)
            identity = process_identity(Path('/proc') / str(child.pid))
            children[arm] = (child, identity)
            write(root / f'LAUNCH_{arm}.json', dict(identity=identity, uuid=uuid, started_unix=time.time()))
        while any(child.poll() is None for child, unused in children.values()):
            if time.time() >= lifetime['hard_deadline_unix'] - 90:
                raise TimeoutError('original_90minute_lifetime')
            time.sleep(2)
        status = 'COMPLETE' if all(child.returncode == 0 for child, unused in children.values()) else 'NATIVE_FAILURE'
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children.values():
            stop_owned(child, identity)
        for log in logs:
            log.close()
        summary = reduce(root)
        releases = {}
        for arm, (index, unused) in policy.DEVICES.items():
            try:
                remaining = lifetime['hard_deadline_unix'] - time.time() - 2
                assert remaining > 1, 'release_verification_budget_expired'
                snapshot = scan(index, root / 'SERVICE_IDENTITY.json',
                    timeout_seconds=min(15, remaining / (len(policy.ARMS) - len(releases))))
                write(root / f'RELEASE_{arm}.json', snapshot)
                releases[arm] = snapshot['clear']
            except Exception as error:
                releases[arm] = False
                write(root / f'RELEASE_{arm}.json', dict(clear=False, error=str(error)))
        write(root / 'TERMINAL.json', dict(status=status, releases=releases,
            finished_unix=time.time(), assigned_gpu_hours=3 * (time.time() - started) / 3600,
            reserved_calls=summary['reserved_calls'], all_states_verified=summary['all_states_verified']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'launch', 'reduce'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--arm', choices=policy.ARMS)
    parser.add_argument('--acknowledgment', type=Path)
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'run':
        run(options.root, options.arm)
    elif options.phase == 'launch':
        launch(options.root, options.acknowledgment)
    else:
        print(json.dumps(reduce(options.root), indent=2))
