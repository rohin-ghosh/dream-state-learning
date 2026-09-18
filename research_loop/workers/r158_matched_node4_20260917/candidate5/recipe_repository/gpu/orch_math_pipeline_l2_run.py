"""CPU-verified handoff and one bounded, no-retry, three-lane native lifetime."""

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
from gpu.orch_rich_hot_a100_scan import host_identity, identity as process_identity
from gpu.orch_math_pipeline_l2_scan import scan
from gpu.orch_math_rich_source import verify_archive
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_math_pipeline_l2 as policy


ROOT = Path('/localhome/local-rohing/orch_math_pipeline_l2_20260915_attempt1')
PILOT = Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
INITIAL_SHA = '12354524c434be91deaeae74f411091bc70b4e38c003fd4f800aea797cc770c8'


def stop_owned(child, identity):
    if child.poll() is not None:
        return
    descriptor = os.pidfd_open(child.pid)
    try:
        assert process_identity(Path('/proc') / str(child.pid)) == identity and identity['uid'] == os.getuid()
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            child.wait(timeout=10)
    finally:
        os.close(descriptor)


def verify_release(document):
    assert set(document['releases']) == set(policy.ARMS)
    for arm, reference in document['releases'].items():
        path = Path(reference['path'])
        assert path.is_absolute() and sha(path) == reference['sha256']
        report = read(path)
        index, uuid = policy.DEVICES[arm]
        assert report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
        assert report['gpu']['index'] == index and report['gpu']['uuid'] == uuid
        assert report['host_sha256'] == policy.HOST_SHA and 'device_minor' in report


def verify_saved(document):
    from safetensors.torch import load_file
    identity = bridge.AdapterIdentity.from_document(document)
    assert identity.base_sha256 == policy.BASE_SHA
    tensors = load_file(str(Path(identity.path) / 'adapter_model.safetensors'), device='cpu')
    mapped = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): tensor
        for name, tensor in tensors.items()}
    assert mapped and all(native.is_lora(name) for name in mapped)
    assert native.state_hash(mapped) == identity.state_sha256, 'saved_native_tensor_identity_mismatch'
    return identity


def check_handoff(document, cohort):
    assert set(document) == {'schema', 'complete_receipt', 'source_snapshot', 'output_adapter',
        'source_task_ids', 'source_question_hashes', 'updates', 'presentations', 'rows'}
    assert document['schema'] == 'ORCH_MATH_PIPELINE_L1_FULL_HANDOFF_V1'
    for key in ('complete_receipt', 'source_snapshot'):
        path = Path(document[key]['path'])
        assert path.is_absolute() and path.resolve() == path and sha(path) == document[key]['sha256']
    receipt = read(document['complete_receipt']['path'])
    assert receipt['status'] == 'COMPLETE' and receipt['output_adapter'] == document['output_adapter']
    assert receipt['updates'] == document['updates'] > 0 and document['presentations'] == 16
    assert isinstance(document['rows'], int) and document['rows'] > 0
    assert receipt['layout']['new_supervised_presentations'] == document['rows'] * document['presentations']
    assert receipt['layout']['new_target_presentations'] == document['rows'] * document['presentations']
    tasks = [task for group in cohort['train'] + cohort['held'] for task in group]
    assert document['source_task_ids'] and document['source_question_hashes']
    assert not set(document['source_task_ids']).intersection(task['id'] for task in tasks)
    assert not set(document['source_question_hashes']).intersection(task['question_sha256'] for task in tasks)
    assert len(receipt['process']) == 3
    return receipt


def validate(root):
    assert root == ROOT and root.resolve() == root and host_identity() == policy.HOST_SHA
    prepared = read(root / 'PREPARE.json')
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    assert sha(root / 'source.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source.tar', root / 'source') == prepared['source_files']
    return prepared


def initialize(root, name, receipt, source_receipt):
    campaign = root / name
    campaign.mkdir(exist_ok=False)
    cohort = read(root / 'COHORT.json')
    write(campaign / 'COHORT.json', cohort)
    identity = verify_saved(receipt['output_adapter'])
    write(campaign / 'INITIAL.json', dict(output_adapter=identity.document(), process=receipt['process'],
        source_receipt=source_receipt, cohort_sha256=sha(campaign / 'COHORT.json'),
        same_child_all_arms=True, score_gate=False, prepared_unix=time.time()))
    (campaign / 'parent_queue').mkdir()
    return campaign


def prepare(root):
    assert root == ROOT and host_identity() == policy.HOST_SHA and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert not (root / 'PREPARE.json').exists()
    prior = read(PILOT / 'PREPARE.json')
    base = portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    receipt = read(PILOT / 'FULL/COMPLETE.json')
    assert receipt['status'] == 'COMPLETE' and receipt['updates'] == 224
    assert receipt['output_adapter']['state_sha256'] == INITIAL_SHA
    assert receipt['layout']['new_supervised_presentations'] == 256
    initialize(root, 'campaign_01_existing_rich', receipt,
        dict(path=str(PILOT / 'FULL/COMPLETE.json'), sha256=sha(PILOT / 'FULL/COMPLETE.json')))
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    from gpu.orch_math_pipeline_l2_native import encode_row
    from gpu.orch_l2_shared_run import legacy_encode
    legacy = legacy_encode(root, tokenizer)
    assert len(legacy) == 222
    task = read(root / 'COHORT.json')['train'][0][0]
    raw = 'Recorded erroneous reasoning. FINAL: -999'
    call = dict(task_id=task['id'], purpose='experience', response=dict(raw=raw),
        target_sha256=policy.text_sha(raw), relative_path='SYNTHETIC_NOT_EXPERIENCE.json')
    episode = dict(task=task, trace=raw, outcome=dict(status='INCORRECT', correct=False))
    row = policy.recorded_row(episode, 'past_attempt', raw, call, '0' * 64)
    encoded = encode_row(row, tokenizer)
    assert len(encoded.target_ids) == sum(label != -100 for label in encoded.labels)
    names = ('COHORT.json', 'DATA_PROVENANCE.json', 'PROTOCOL.md', 'SERVICE_IDENTITY.json',
        'LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json', 'PARENT_PROBE.json', 'CPU_TESTS.log')
    write(root / 'PREPARE.json', dict(status='CPU_PREPARED_NO_MODEL', model_dir=prior['model_dir'],
        bundle=prior['bundle'], base_verification=base, source_sha256=sha(root / 'source.tar'),
        source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in names}, tokenizer_masks_verified=True,
        legacy_rows=222, native_calls=0, initial_native_tensor_verified=True))
    print(json.dumps(dict(prepare_sha256=sha(root / 'PREPARE.json'), status='CPU_PREPARED_NO_MODEL')))


def new_lifetime(root):
    started = time.time()
    assert started + policy.HOURS * 3600 < LEASE_END - 21600
    document = dict(started_unix=started, hard_deadline_unix=started + policy.HOURS * 3600,
        native_deadline_unix=started + policy.HOURS * 3600 - 180,
        max_campaigns=2, max_calls_per_arm_campaign=policy.MAX_CALLS_PER_ARM,
        max_calls=2 * 3 * policy.MAX_CALLS_PER_ARM, gpu_hours_ceiling=3 * policy.HOURS,
        ready_sha256=sha(root / 'READY.json'), retries=0, parent_cli_invocations_ceiling=12)
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(document, stream, indent=2)
    return document


def release(root, label):
    results = {}
    for arm, (index, unused) in policy.DEVICES.items():
        try:
            snapshot = scan(index, root / 'SERVICE_IDENTITY.json', timeout_seconds=30)
            results[arm] = bool(snapshot['clear'])
        except Exception as error:
            snapshot = dict(clear=False, error=str(error))
            results[arm] = False
        write(root / f'{label}_RELEASE_{arm}.json', snapshot)
    return results


def run_campaign(root, campaign, lifetime):
    stages = [(0, 'readout')] + [(cycle, phase) for cycle in range(1, 4) for phase in ('experience', 'readout')]
    children, cursors, failed = {}, {arm: 0 for arm in policy.ARMS}, {}
    try:
        while len(failed) + sum(position == len(stages) for position in cursors.values()) < 3:
            assert time.time() < lifetime['hard_deadline_unix'] - 120, 'original_lifetime_expired'
            for arm in policy.ARMS:
                if arm in failed or cursors[arm] == len(stages):
                    continue
                if arm in children:
                    child, identity, log = children[arm]
                    if child.poll() is None:
                        continue
                    log.close()
                    del children[arm]
                    cycle, phase = stages[cursors[arm]]
                    if child.returncode or not (campaign / arm / f'cycle{cycle}' / phase / 'COMPLETE.json').exists():
                        failed[arm] = dict(cycle=cycle, phase=phase, returncode=child.returncode)
                        continue
                    cursors[arm] += 1
                    if cursors[arm] == len(stages):
                        continue
                cycle, phase = stages[cursors[arm]]
                index, uuid = policy.DEVICES[arm]
                admission = scan(index, root / 'SERVICE_IDENTITY.json')
                write(campaign / f'ADMISSION_{arm}_C{cycle}_{phase}.json', admission)
                if not admission['clear'] or admission['scanner_euid'] != 0:
                    failed[arm] = dict(cycle=cycle, phase=phase, error='physical_admission_failed')
                    continue
                log = (campaign / f'{arm}_C{cycle}_{phase}.log').open('x')
                child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_math_pipeline_l2_native',
                    '--root', str(campaign), '--arm', arm, '--cycle', str(cycle), '--phase', phase],
                    cwd=root / 'source', start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                        TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT)
                identity = process_identity(Path('/proc') / str(child.pid))
                children[arm] = child, identity, log
                write(campaign / f'LAUNCH_{arm}_C{cycle}_{phase}.json', dict(identity=identity, uuid=uuid, started_unix=time.time()))
            write(campaign / 'PROGRESS.json', dict(stage_cursors=cursors, failed=failed, observed_unix=time.time()))
            time.sleep(2)
    finally:
        for child, identity, log in children.values():
            stop_owned(child, identity)
            log.close()
    write(campaign / 'TERMINAL.json', dict(status='COMPLETE' if not failed else 'FAILED',
        failed=failed, stage_cursors=cursors, finished_unix=time.time(),
        planned_tasks_per_arm=56, planned_calls_per_arm=272, no_retries=True))
    return not failed


def launch(root):
    validate(root)
    ready = read(root / 'READY.json')
    assert ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed']
    assert ready['builder_receipt'] and ready['generator_release_sha256'] == sha(root / 'GENERATOR_RELEASE.json')
    verify_release(read(root / 'GENERATOR_RELEASE.json'))
    lifetime = new_lifetime(root)
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    status = 'FAILED'
    try:
        assert run_campaign(root, root / 'campaign_01_existing_rich', lifetime), 'existing_child_campaign_failed'
        first_release = release(root, 'CAMPAIGN01')
        write(root / 'AWAITING_COMBINED.json', dict(released=first_release,
            handoff_path=str(root / 'L1_FULL_HANDOFF.json'), no_model_wait=True))
        while time.time() < lifetime['native_deadline_unix'] - 600:
            handoff = root / 'L1_FULL_HANDOFF.json'
            if handoff.exists():
                document = read(handoff)
                receipt = check_handoff(document, read(root / 'COHORT.json'))
                assert receipt['output_adapter']['state_sha256'] != INITIAL_SHA
                write(root / 'COMBINED_HANDOFF_VERIFIED.json', dict(handoff_sha256=sha(handoff),
                    ready_for_release=True, verified_unix=time.time()))
                if not (root / 'COMBINED_GENERATOR_RELEASE.json').exists():
                    time.sleep(5)
                    continue
                verify_release(read(root / 'COMBINED_GENERATOR_RELEASE.json'))
                campaign = initialize(root, 'campaign_02_combined', receipt, document['complete_receipt'])
                assert run_campaign(root, campaign, lifetime), 'combined_child_campaign_failed'
                status = 'COMPLETE_TWO_CAMPAIGNS'
                break
            time.sleep(5)
        else:
            status = 'COMPLETE_EXISTING_COMBINED_NOT_AVAILABLE_WITHIN_BOUND'
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error), observed_unix=time.time()))
        raise
    finally:
        releases = release(root, 'FINAL')
        write(root / 'TERMINAL.json', dict(status=status, releases=releases, finished_unix=time.time(),
            lifetime_sha256=sha(root / 'LIFETIME.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'launch'))
    parser.add_argument('--root', type=Path, default=ROOT)
    options = parser.parse_args()
    (prepare if options.phase == 'prepare' else launch)(options.root)
