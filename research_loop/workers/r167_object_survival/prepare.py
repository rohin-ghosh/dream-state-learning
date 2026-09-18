import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def prepare(source):
    source = Path(source).resolve()
    sys.path.insert(0, str(source))
    from gpu import orch_r167_object_survival_eval as evaluator
    root = evaluator.CAMPAIGN
    output = root / 'control_generation3'
    output.mkdir(mode=0o700)
    environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    tested = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(source / 'tests'),
        '-p', 'test_orch_r167_object_survival_eval.py', '-v'], cwd=source, env=environment, capture_output=True)
    log_ref = evaluator.write(output / 'CPU_TESTS.txt', tested.stdout + tested.stderr)
    assert tested.returncode == 0
    launcher_test = subprocess.run([sys.executable, '-B', str(source.parent / 'test_launch.py'), '-v'],
        cwd=source, env=environment, capture_output=True)
    launcher_log = evaluator.write(output / 'LAUNCHER_CPU_TESTS.txt', launcher_test.stdout + launcher_test.stderr)
    assert launcher_test.returncode == 0
    old = evaluator.read(root / 'R159_REFERENCE_CONFIG.json')
    cpu_gate = evaluator.write(output / 'CPU_GATE.json', dict(status='PASS',
        helper_sha256=evaluator.sha(source / 'gpu/orch_r167_object_survival_eval.py'),
        test_sha256=evaluator.sha(source / 'tests/test_orch_r167_object_survival_eval.py'),
        test_log=log_ref, launcher_test_log=launcher_log, observed_unix=time.time(), model_calls=0))
    freeze_ref = evaluator.ref(root / 'audit_generation1' / 'FREEZE.json')
    plan_ref = evaluator.write(output / 'PLAN.json', evaluator.make_plan(freeze_ref))
    methods_ref = evaluator.write(output / 'METHODS.json', evaluator.METHODS)
    scorer_freeze = evaluator.write(output / 'SCORER_FREEZE.json', dict(schema=evaluator.SCHEMA,
        status='PRE_OUTPUT_SCORER_FREEZE', plan=plan_ref, methods=methods_ref, original_TRAIN_audit=freeze_ref,
        scorer_sha256=evaluator.read(plan_ref['path'])['scorer_sha256'],
        helper=evaluator.ref(source / 'gpu/orch_r167_object_survival_eval.py'),
        semantic_protocol=evaluator.ref(source.parent / 'SEMANTIC_ADJUDICATION_PROTOCOL.md'),
        model_calls=0, created_unix=time.time(), old_generations_preserved=True))
    forks_path = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
    forks = evaluator.read(forks_path)
    lease = evaluator.write(output / 'LEASE.proposed.json', dict(node='node2', physical_slots=[0, 1],
        lease_end_unix=forks['lease_end_unix'], evidence=evaluator.ref(forks_path), observed_unix=time.time()))
    visibility = evaluator.write(output / 'VISIBILITY.proposed.json', dict(schema=evaluator.SCHEMA, root=str(root),
        parent_ingestion=False, detailed_appendix='PRIVATE_EVALUATOR_ONLY', public_fields=['status', 'counts', 'hashes', 'paths']))
    builder = evaluator.write(output / 'BUILDER.json', dict(status='CPU_AND_PROVENANCE_PASS',
        plan=plan_ref, cpu_gate=cpu_gate, created_unix=time.time(), author='Euclid',
        scope='R167_new114call_empty_context_probe_only_no_GPU_GO', visibility=visibility, scorer_freeze=scorer_freeze))
    sources = {str(path.relative_to(source)): evaluator.sha(path)
               for directory in ('gpu', 'organism_v6') for path in (source / directory).rglob('*.py')}
    sources['tests/test_orch_r167_object_survival_eval.py'] = evaluator.sha(source / 'tests/test_orch_r167_object_survival_eval.py')
    jobs = []
    for milestone in evaluator.ORDER:
        label = 'initial' if milestone == 0 else f'sleep_{milestone:06d}'
        for physical, condition in enumerate(evaluator.CONDITIONS):
            config = dict(schema=evaluator.SCHEMA, plan=plan_ref, campaign_root=str(root),
                manifest=evaluator.ref(root / 'inputs' / label / 'manifest.json'), milestone=milestone, condition=condition,
                physical=physical, gpu_uuid=forks['uuid_by_index'][physical], source_root=str(source), sources=sources,
                python=old['python'], python_sha256=old['python_sha256'], model_dir=old['model_dir'],
                service_path=old['service_path'], lease=lease, cpu_gate=cpu_gate, builder=builder,
                release=evaluator.ref(root / 'R159_FINAL_RECEIPT.json'), private_visibility=visibility, max_job_seconds=900)
            key = f'{milestone}_{condition}'
            config_ref = evaluator.write(output / (key + '.CONFIG.json'), config)
            evaluator.validate(config_ref['path'], None)
            jobs.append(dict(key=key, physical=physical, execution=config_ref))
    manifest = dict(schema=evaluator.SCHEMA, status='CPU_PREFLIGHT_PASS_NO_GPU_GO', plan=plan_ref,
        jobs=jobs, calls=114, generated_token_cap=58368, checkpoint_cap=19, job_cap=38,
        maximum_wall_seconds=10800, helper=evaluator.ref(source / 'gpu/orch_r167_object_survival_eval.py'),
        tests=evaluator.ref(source / 'tests/test_orch_r167_object_survival_eval.py'), cpu_gate=cpu_gate,
        builder=builder, lease=lease, visibility=visibility, freeze=freeze_ref,
        scorer_freeze=scorer_freeze,
        launcher=evaluator.ref(source.parent / 'launch.py'), model_calls=0, observed_unix=time.time())
    reference = evaluator.write(output / 'MANIFEST.json', manifest)
    return dict(status=manifest['status'], manifest=reference, plan=plan_ref, cpu_gate=cpu_gate,
                jobs=38, calls=114, checkpoints=19, model_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.source), sort_keys=True))
    except BaseException as error:
        print(json.dumps(dict(status='PREPARATION_FAILED_NO_GPU', error_type=type(error).__name__)))
        raise SystemExit(1)
