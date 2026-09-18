"""Build one byte-pinned, train/dev-only receiving payload without remote I/O."""

import json
from pathlib import Path
import shutil
import tarfile

from gpu import ny_caption_data as data


def build():
    repo = Path(__file__).resolve().parents[4]
    work = Path(__file__).resolve().parent
    root = work/'private/released_all_receiving_v6'
    remote = Path('/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v6')
    status = json.loads((work/'private/released_all_v1/PUBLIC_STATUS.json').read_bytes())
    manifest = data.load_manifest(status['data_manifest'])
    plan = data.load_development_plan(status['development_plan'], status['source_manifest'])
    names = [name for values in plan['subsets'].values() for name in values]
    data.require(sum(manifest['contests'][name]['rows']['bytes'] for name in names) < 400*1024**2,
        'bounded_train_dev_only_payload')
    data.require(shutil.disk_usage(work).free >= 2*1024**3, 'local_staging_disk')
    root.mkdir(mode=0o700, exist_ok=False)
    payload = root/'payload'
    entries = {}
    def add(name, raw):
        reference = data.private_write(payload/name, raw)
        entries[name] = dict(bytes=reference['bytes'], sha256=reference['sha256'])
        return dict(reference, path=str(remote/name))
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
        scene_fit_sampling_policy='UNIFORM_DISTINCT_SCENE_RECIPROCAL_PAIRS_V1',
        calibration_stress_scene_swap_policy='SEEDED_SCENE_COMPONENT_DERANGEMENT_EXACT_MARGINALS_V1',
        max_seconds=6000,
        development_only=True, locked_judge_validation_consumed=False, FINAL_consumed=False)
    config_ref = add('TRAIN_CONFIG.json', config)
    source_paths = ['gpu/ny_caption_data.py', 'gpu/ny_caption_judge.py', 'tests/test_ny_caption_data.py',
        'tests/test_ny_caption_judge.py', str(Path(__file__).relative_to(repo)),
        'research_loop/workers/r177_caption_game_stage1_20260917/data_judge/released_receiving.py',
        'research_loop/workers/r177_caption_game_stage1_20260917/data_judge/receiving_cpu.py',
        'research_loop/workers/r177_caption_game_stage1_20260917/data_judge/physical2_confinement.py']
    for name in source_paths:
        copy(name, data.file_ref(repo/name))
    gate = copy('LOCAL_CPU_TESTS.json', data.file_ref(work/'evidence/CPU_TESTS_R167_RELEASED_v6.json'))
    inventory = dict(schema='NY_R167_RELEASED_RECEIVING_V1', root=str(remote), files=entries, config=config_ref,
        local_CPU_gate=gate, hostname_sha256='e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b',
        lease=dict(path='/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json',
            sha256='ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2'),
        lease_safe_end_unix=1789754400, selected_contests=status['selected_contests'],
        permitted_caption_pools=['judge_train', 'judge_dev'], locked_validation_files_copied=False,
        FINAL_files_copied=False, images_copied=False, no_automatic_retry=True)
    previous = json.loads((work/'evidence/RECEIVING_V4_OBSERVATION_1789671611293554849.json').read_bytes())
    inventory['allocation_end_unix'] = previous['receipts']['ADMISSION.json']['body']['end_unix']
    inventory['preserved_prior_admission'] = {name: previous['receipts']['ADMISSION.json'][name] for name in ('path', 'sha256')}
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
    build()
