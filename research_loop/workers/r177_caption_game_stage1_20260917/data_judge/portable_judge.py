"""Export a completed v6 judge without reading private scoring-error cases."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile

from gpu import ny_caption_data as data
from gpu import ny_caption_judge as judge


JUDGE_KEYS = ('schema', 'status', 'input_format', 'tau', 'calibration', 'scene_fit',
    'human_validated', 'final_release_authorized', 'evaluator_source_sha256', 'audit_mode',
    'locked_judge_validation_consumed', 'runtime_versions', 'model_token_accounting',
    'model_examples_charged', 'model_tokens_charged', 'completed_unix', 'model_selection',
    'validation', 'stress_summary', 'scene_fit_sampling_policy', 'calibration_stress_scene_swap_policy',
    'selected_step', 'completed_steps', 'humor_training_example_draws',
    'scene_fit_positive_example_draws', 'scene_fit_negative_example_draws')
TRAIN_KEYS = ('schema', 'input_format', 'pretrained_model', 'num_labels', 'scene_fit_num_labels',
    'trust_remote_code', 'seed', 'max_steps', 'max_seconds', 'batch_size', 'max_length',
    'per_contest_per_band', 'heldout_per_contest', 'evaluation_interval', 'stress_examples',
    'smoothing', 'vote_weight_cap', 'learning_rate', 'weight_decay', 'adam_betas', 'adam_epsilon',
    'max_grad_norm', 'temperature_grid', 'threshold_minimum_mean_positive_vote_mass',
    'threshold_minimum_coverage', 'scene_fit_sampling_policy', 'calibration_stress_scene_swap_policy',
    'development_only', 'locked_judge_validation_consumed', 'FINAL_consumed', 'scene_policy')


def portable_config(original, training_ref, checkpoint_root):
    checkpoint_root = Path(checkpoint_root).resolve()
    result = {key: original[key] for key in JUDGE_KEYS if key in original}
    result.update(training_config=training_ref, selected_checkpoint=str(checkpoint_root), checkpoint={})
    for name, before in original['checkpoint'].items():
        data.require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and Path(name).suffix not in ('.py', '.bin', '.pt', '.pkl'), 'portable_checkpoint_whitelist')
        reference = data.file_ref(checkpoint_root/name)
        data.require(reference['sha256'] == before['sha256'] and reference['bytes'] == before['bytes'],
            'portable_weights_unchanged')
        result['checkpoint'][name] = reference
    return result


def extract_checkpoint(archive, planned, checkpoint):
    checkpoint = Path(checkpoint)
    data.require(not checkpoint.exists(), 'fresh_checkpoint_extraction_preserves_partial_export')
    with tarfile.open(archive, 'r:') as stream:
        members = stream.getmembers()
        data.require(len(members) == len(planned) and {member.name for member in members} == set(planned),
            'exact_portable_archive_members')
        for member in members:
            data.require(not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                and member.isfile() and member.size == planned[member.name]['bytes'], 'regular_exact_checkpoint_member')
        checkpoint.mkdir(parents=True, mode=0o700, exist_ok=False)
        for member in members:
            target = checkpoint/member.name
            target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            checksum = hashlib.sha256()
            with stream.extractfile(member) as source, target.open('xb') as destination:
                for block in iter(lambda: source.read(1024**2), b''):
                    checksum.update(block)
                    destination.write(block)
            data.require(checksum.hexdigest() == planned[member.name]['sha256'], 'portable_checkpoint_transport_hash')


def export(resume_archive=False):
    work = Path(__file__).resolve().parent
    repo = work.parents[3]
    root = work/'portable/released_all_v6'
    remote = '/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v6'
    code = '''import hashlib,json
from pathlib import Path
root=Path(ROOT)
def read(path):
 assert path.is_file() and path.stat().st_size<65536
 raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body=json.loads(raw))
completed=read(root/'COMPLETED.json')
config=read(root/'training/judge_config.json')
assert completed['body']['judge_config']['sha256']==config['sha256']
assert config['body']['scene_fit_sampling_policy']=='UNIFORM_DISTINCT_SCENE_RECIPROCAL_PAIRS_V1'
assert config['body']['calibration_stress_scene_swap_policy']=='SEEDED_SCENE_COMPONENT_DERANGEMENT_EXACT_MARGINALS_V1'
assert config['body']['locked_judge_validation_consumed'] is False
training=read(root/'TRAIN_CONFIG.json')
assert config['body']['training_config']['sha256']==training['sha256']
report=read(root/'training/PUBLIC_SCORING_REPORT.json')
assert report['body']['judge_config_sha256']==config['sha256']
print(json.dumps(dict(completed=completed,config=config,training=training,report=report)))
'''.replace('ROOT', repr(remote), 1)
    result = subprocess.run(['bash', str(repo/'gpu/a40r_ssh.sh'), 'python3 -B -c '+shlex.quote(code)],
        capture_output=True, timeout=30, check=True)
    data.require(len(result.stdout) < 256*1024, 'bounded_completed_metadata_only')
    metadata = json.loads(result.stdout)
    original = metadata['config']['body']
    planned = original['checkpoint']
    data.require(0 < len(planned) <= 32 and sum(item['bytes'] for item in planned.values()) <= 600*1024**2,
        'bounded_portable_checkpoint_transfer')
    data.require(shutil.disk_usage(work).free > 2*1024**3, 'portable_disk_admission')
    selected = Path(original['selected_checkpoint'])
    data.require(selected.is_relative_to(Path(remote)/'training/checkpoints'), 'only_completed_selected_checkpoint')
    for name, reference in planned.items():
        data.require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and Path(reference['path']) == selected/name, 'explicit_checkpoint_member')
    archive = root/'CHECKPOINT.tar'
    if resume_archive:
        data.require(root.is_dir() and archive.is_file() and not archive.is_symlink()
            and {path.name for path in root.iterdir()} <= {'CHECKPOINT.tar', 'checkpoint'},
            'only_interrupted_archive_export_can_resume')
    else:
        root.mkdir(parents=True, mode=0o700, exist_ok=False)
        command = shlex.join(['tar', '-C', str(selected), '-cf', '-', *sorted(planned)])
        with archive.open('xb') as stream:
            subprocess.run(['bash', str(repo/'gpu/a40r_ssh.sh'), command], stdout=stream,
                stderr=subprocess.PIPE, timeout=180, check=True)
    data.require(archive.stat().st_size <= 601*1024**2, 'bounded_actual_checkpoint_transfer')
    checkpoint = root/('checkpoint_resumed_v1' if resume_archive else 'checkpoint')
    extract_checkpoint(archive, planned, checkpoint)
    training = {key: metadata['training']['body'][key] for key in TRAIN_KEYS if key in metadata['training']['body']}
    training['original_training_config_sha256'] = metadata['training']['sha256']
    training_ref = data.private_write(root/'training_config.json', training)
    config = portable_config(original, training_ref, checkpoint)
    config['portable_origin'] = dict(judge_config_sha256=metadata['config']['sha256'],
        original_training_config_sha256=metadata['training']['sha256'],
        scope='CHECKPOINT_BYTES_AND_SCORING_PARAMETERS_UNCHANGED_PRIVATE_CASE_REFS_OMITTED')
    reference = data.private_write(root/'judge_config.json', config)
    report_ref = data.private_write(root/'PUBLIC_SCORING_REPORT.json', judge.public_scoring_report(reference))
    for module in (data, judge):
        path = Path(module.__file__).resolve()
        data.require(data.file_ref(path)['sha256'] == original['evaluator_source_sha256'][path.name], 'portable_frozen_runtime_source')
        data.private_write(root/'runtime/gpu'/path.name, path.read_bytes())
    data.private_write(root/'runtime/gpu/__init__.py', b'')
    data.private_write(root/'ORIGINAL_PUBLIC_SCORING_REPORT.json', metadata['report']['body'])
    usable = config['tau']['threshold'] is not None
    if usable:
        judge.validate_checkpoint(reference)
    handoff = dict(schema='NY_PORTABLE_TRAINED_JUDGE_HANDOFF_V1',
        status='STRUCTURALLY_VALID_PROVISIONAL_JUDGE' if usable else 'TRAINED_BUT_ACCEPTANCE_THRESHOLD_NULL_NOT_USABLE',
        judge_config=reference, public_scoring_report=report_ref, checkpoint_archive=data.file_ref(archive),
        runtime_root=str(root/'runtime'), frozen_source_sha256=original['evaluator_source_sha256'],
        original_judge_config_sha256=metadata['config']['sha256'], original_public_report_sha256=metadata['report']['sha256'],
        private_scoring_errors_included=False, caption_texts_included=False, reserved_contest_ids_included=False,
        second_blind_comparator_complete=False, human_validated=False, final_release_authorized=False,
        smoke_interface='load_cpu_judge(judge_config_ref, max_model_examples=8, max_model_tokens=2048, max_seconds=120)',
        relocation='Call rebase_config with this bundle after moving; retain original configs rather than overwriting.')
    handoff_ref = data.private_write(work/'PORTABLE_JUDGE_HANDOFF_V6.json', handoff)
    print(json.dumps(dict(handoff=handoff_ref, status=handoff['status'], judge_config=reference, report=report_ref)))


def rebase_config(bundle, destination):
    bundle, destination = Path(bundle).resolve(), Path(destination).resolve()
    original = data.bound(data.file_ref(bundle/'judge_config.json'))
    training = data.file_ref(bundle/'training_config.json')
    data.require(training['sha256'] == original['training_config']['sha256'], 'portable_training_config_unchanged')
    selected_name = Path(original['selected_checkpoint']).name
    data.require(selected_name in ('checkpoint', 'checkpoint_resumed_v1'), 'known_portable_checkpoint_directory')
    result = portable_config(original, training, bundle/selected_name)
    result['relocated_from_config_sha256'] = data.file_ref(bundle/'judge_config.json')['sha256']
    return data.private_write(destination, result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('export', 'rebase'))
    parser.add_argument('--bundle')
    parser.add_argument('--destination')
    parser.add_argument('--resume-archive', action='store_true')
    args = parser.parse_args()
    if args.operation == 'export':
        export(args.resume_archive)
    else:
        data.require(args.bundle and args.destination, 'explicit_portable_relocation_paths')
        print(json.dumps(rebase_config(args.bundle, args.destination)))
