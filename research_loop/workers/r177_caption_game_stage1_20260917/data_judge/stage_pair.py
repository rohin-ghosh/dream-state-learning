"""Fresh V9/V10 receiving payloads for the preserved V7/V8 scientific plan."""

import argparse
import json
from pathlib import Path
import shutil
import tarfile
import time

from gpu import ny_caption_data as data
from gpu import ny_caption_judge as judge


def build(version):
    data.require(version in (9, 10), 'fresh_support_repaired_pair_versions_only')
    repo = Path(__file__).resolve().parents[4]
    work = Path(__file__).resolve().parent
    root = work/f'private/released_all_receiving_v{version}'
    remote = Path(f'/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v{version}')
    status = json.loads((work/'private/released_all_v1/PUBLIC_STATUS.json').read_bytes())
    manifest = data.load_manifest(status['data_manifest'])
    plan = data.load_development_plan(status['development_plan'], status['source_manifest'])
    names = [name for values in plan['subsets'].values() for name in values]
    data.require(sum(manifest['contests'][name]['rows']['bytes'] for name in names) < 400*1024**2,
        'bounded_train_dev_only_payload')
    data.require(shutil.disk_usage(work).free >= 3*1024**3, 'local_staging_disk')
    previous = json.loads((work/'evidence/RECEIVING_V4_OBSERVATION_1789671611293554849.json').read_bytes())
    allocation_end = previous['receipts']['ADMISSION.json']['body']['end_unix']
    data.require(time.time()+1860 < allocation_end, 'new_attempt_must_fit_original_allocation')
    root.mkdir(mode=0o700, exist_ok=False)
    payload, entries = root/'PAYLOAD', {}

    def add(name, value):
        local = data.private_write(payload/name, value)
        reference = dict(path=str(remote/name), sha256=local['sha256'], bytes=local['bytes'])
        entries[name] = reference
        return reference

    def copy(name, reference):
        data.require(data.file_ref(reference['path'])['sha256'] == reference['sha256'], 'immutable_source_before_staging')
        return add(name, Path(reference['path']).read_bytes())

    original = copy('data/ORIGINAL_MANIFEST.private.json', status['source_manifest'])
    planned = copy('data/DEVELOPMENT_PLAN.private.json', status['development_plan'])
    catalog = copy('data/SCENE_CATALOG.private.json', status['scene_catalog'])
    for name in names:
        before = manifest['contests'][name]['rows']
        after = copy('data/rows/'+name+'.jsonl', before)
        manifest['contests'][name]['rows'] = dict(before, **after)
    manifest['judge_scene_catalog'] = catalog
    manifest['receiving_relocation'] = dict(original_manifest=status['data_manifest'],
        selected_row_bytes_unchanged=True, unselected_files_not_copied=True)
    ready = add('data/DATA_MANIFEST.private.json', manifest)
    model = copy('MODEL_MANIFEST.json', data.file_ref(work/'RECEIVING_MODEL_MANIFEST_20260917_v1.json'))
    config = json.loads((work/'TRAIN_CONFIG_TEMPLATE.json').read_bytes())
    config.pop('template_status')
    config.update(data_manifest=ready, development_plan=planned, development_source_manifest=original,
        local_model_manifest=model, scene_policy=data.RELEASED_JUDGE_SCENE_POLICY,
        scene_fit_sampling_policy=judge.SCENE_FIT_SAMPLING_POLICY,
        calibration_stress_scene_swap_policy=judge.SCENE_SWAP_POLICY,
        fitting_policy=judge.FULL_FITTING_POLICY, ranking_policy=judge.RANKING_POLICY,
        ranking_auxiliary_weight=1.0 if version == 9 else 0.0,
        model_selection_policy=judge.RANK_SELECTION_POLICY, independent_scene_fit_selection=True,
        development_reuse_provisional=True, max_steps=5000, max_seconds=1800, evaluation_interval=250,
        development_only=True, locked_judge_validation_consumed=False, FINAL_consumed=False)
    judge.validate_config(config)
    config_ref = add('TRAIN_CONFIG.json', config)
    source_paths = ['gpu/ny_caption_data.py', 'gpu/ny_caption_judge.py', 'tests/test_ny_caption_data.py',
        'tests/test_ny_caption_judge.py', str(Path(__file__).relative_to(repo))]
    source_paths += [str((work/name).relative_to(repo)) for name in
        ('released_receiving.py', 'receiving_cpu.py', 'physical2_confinement.py', 'NEXT_CANDIDATE_V7.md', 'V7_CPU_SUPPORT_REPAIR.md')]
    for name in source_paths:
        copy(name, data.file_ref(repo/name))
    support_transport = data.bound(data.file_ref(work/'NODE4_CPU_STAGE_TRANSPORT_20260917_v1.json'))
    support_inventory = data.bound(support_transport['inventory'])
    data.require(data.file_ref(support_transport['archive']['path']) == support_transport['archive'], 'original_pinned_CPU_support_archive')
    with tarfile.open(support_transport['archive']['path'], 'r:') as stream:
        for name, reference in support_inventory['files'].items():
            if name.startswith('support/'):
                member = stream.getmember(name)
                data.require(member.isfile() and member.size == reference['bytes'], 'exact_CPU_support_member')
                raw = stream.extractfile(member).read(reference['bytes']+1)
                result = add(name, raw)
                data.require(result['sha256'] == reference['sha256'] and result['bytes'] == reference['bytes'], 'pinned_CPU_support_bytes')
    gate = copy('LOCAL_CPU_TESTS.json', data.file_ref(work/'evidence/CPU_TESTS_R167_PAIR_v9.json'))
    inventory = dict(schema='NY_R167_RELEASED_RECEIVING_V1', root=str(remote), files=entries, config=config_ref,
        local_CPU_gate=gate, hostname_sha256='e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b',
        lease=dict(path='/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json',
            sha256='ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2'),
        lease_safe_end_unix=1789754400, allocation_end_unix=allocation_end,
        preserved_prior_admission={name: previous['receipts']['ADMISSION.json'][name] for name in ('path', 'sha256')},
        selected_contests=status['selected_contests'], permitted_caption_pools=['judge_train', 'judge_dev'],
        locked_validation_files_copied=False, FINAL_files_copied=False, images_copied=False, no_automatic_retry=True,
        test_support_directory='support', prior_CPU_support_inventory=support_transport['inventory'],
        pair=dict(scope='R177_PREDECLARED_FULL_FITTING_QDIFF_PAIR_V1', seed=177,
            variant='q_difference_auxiliary' if version == 9 else 'lambda_zero_control'))
    inventory_ref = data.private_write(payload/'INVENTORY.json', inventory)
    archive = root/'PAYLOAD.tar.gz'
    with tarfile.open(archive, 'x:gz') as stream:
        for name in sorted(entries):
            stream.add(payload/name, arcname=name, recursive=False)
        stream.add(payload/'INVENTORY.json', arcname='INVENTORY.json', recursive=False)
    reference = data.private_write(root/'TRANSPORT.json', dict(remote_root=str(remote), inventory=inventory_ref,
        archive=data.file_ref(archive), config=config_ref, files=len(entries), bytes=sum(row['bytes'] for row in entries.values()),
        selected_contests=status['selected_contests']))
    print(json.dumps(dict(transport=reference, inventory_sha256=inventory_ref['sha256'], config=config_ref,
        archive=data.file_ref(archive), remote_root=str(remote), selected_contests=status['selected_contests'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, choices=(9, 10), required=True)
    arguments = parser.parse_args()
    build(arguments.version)
