"""Stage one immutable R171 BT candidate, retaining all previous attempts."""

import json
from pathlib import Path
import shutil
import tarfile
import time

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_budget as budget
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_widegap_v2 as ranker
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_receiving_v2 as receiving


def build():
    work = Path(__file__).resolve().parent
    repo = work.parents[3]
    prior = work/'private/bt_qwen_v2/PAYLOAD'
    prepared = data.bound(data.file_ref(work/'rank200_reference_v3/private/PREPARED_DATA.private.json'))
    old = data.bound(data.file_ref(prior/'INVENTORY.json'))
    started = time.time()
    data.require(started+budget.ALLOCATION_SECONDS+budget.MARGIN_SECONDS < old['lease_safe_end_unix'], 'fresh_budget_inside_unchanged_machine_lease')
    root = work/'private/bt_widegap_v2'
    remote = Path('/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_v2')
    data.require(shutil.disk_usage(work).free > 3*1024**3, 'bounded_local_BT_staging_disk')
    root.mkdir(mode=0o700, exist_ok=False)
    payload, entries = root/'PAYLOAD', {}
    def add(name, value):
        reference = data.private_write(payload/name, value)
        entries[name] = dict(path=str(remote/name), sha256=reference['sha256'], bytes=reference['bytes'])
        return entries[name]
    for name, reference in old['files'].items():
        if name.startswith('data/rows/') or name in ('data/DATA_MANIFEST.private.json', 'TRAIN_CONFIG.json', 'EXPERIMENT_BUDGET.json', 'LOCAL_CPU_TESTS.json'):
            continue
        local = data.file_ref(prior/name)
        data.require(local['sha256'] == reference['sha256'] and local['bytes'] == reference['bytes'], 'preserved_prior_source_data_support_pin')
        if name.endswith('.py') and not name.startswith('support/'):
            data.require(data.file_ref(repo/name)['sha256'] == local['sha256'], 'local_test_dependency_matches_frozen_source')
        add(name, (prior/name).read_bytes())
    for name, entry in prepared['contests'].items():
        data.require(data.file_ref(entry['rows']['path']) == entry['rows'], 'exact_completed_rank200_preparation_rows')
        add('data/rows/'+name+'.jsonl', Path(entry['rows']['path']).read_bytes())
    manifest = data.bound(data.file_ref(prior/'data/DATA_MANIFEST.private.json'))
    plan = data.bound(data.file_ref(prior/'data/DEVELOPMENT_PLAN.private.json'))
    for names in plan['subsets'].values():
        for name in names:
            manifest['contests'][name]['rows'] = dict(manifest['contests'][name]['rows'], **entries['data/rows/'+name+'.jsonl'])
    manifest['judge_scene_catalog'] = entries['data/SCENE_CATALOG.private.json']
    manifest_ref = add('data/DATA_MANIFEST.private.json', manifest)
    reference_panel = add('data/REFERENCE_PANEL.private.json', Path(prepared['panel']['path']).read_bytes())
    add('data/RANK200_REGISTRATION.json', (work/'rank200_reference_v3/REGISTRATION.json').read_bytes())
    warm_start = add('data/WARM_START_RECEIPT.json', (work/'portable/bt_qwen_v2/judge_config.json').read_bytes())
    base = data.bound(data.file_ref(work/'QWEN_BT_BASE_MANIFEST_RECEIPT.json'))['reference']
    config = dict(schema='NY_WIDEGAP100K_TRAIN_CONFIG_V2', objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC',
        label_policy=ranker.LABEL_POLICY, pair_policy=ranker.PAIR_POLICY, reliability_policy=ranker.RELIABILITY_POLICY,
        base_model=base, warm_start=warm_start, reference_panel=reference_panel, optimizer_state_reset=True,
        quality_contract=ranker.quality.CONTRACT, evaluation_steps=ranker.widegap.EVALUATION_STEPS, data_manifest=manifest_ref, development_plan=entries['data/DEVELOPMENT_PLAN.private.json'],
        development_source_manifest=entries['data/ORIGINAL_MANIFEST.private.json'],
        frozen_scene_fit=dict(path='/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v6/training/judge_config.json',
            sha256='b6cdc59274d9e5ec6d1bf1b1adc073346cf35e31bc1e1e93115d2d80421cd0e7'),
        max_updates=6250, batch_pairs=16, gradient_accumulation=1, max_seconds=budget.RUN_SECONDS,
        calibration_reserve_seconds=budget.RESERVE_SECONDS, max_length=512, heldout_per_contest=256, seed=177, vote_cap=100,
        selection_sample_per_contest=256, inference_batch=16, learning_rate=0.00003, humor_soft_CE_used=False,
        image_judge_training=False, development_reuse_provisional=True)
    receiving.validate_config(config)
    sources = [str((work/name).relative_to(repo)) for name in
        ('bt_widegap_v2.py','widegap_pairs_v2.py','widegap_receiving_v2.py','widegap_budget.py','widegap_confinement.py',
         'test_widegap_pairs_v2.py','test_widegap_runtime_v2.py','rank200_calibration_v3.py','test_rank200_calibration_v3.py',
         'stage_widegap_v2.py','widegap_ops_v2.py','widegap_observe_v2.py','WIDEGAP100K_SCOPE.md','WIDEGAP100K_BUDGET_ADDENDUM.md','WIDEGAP100K_V2_ELIGIBILITY_ADDENDUM.md')]
    for name in sources:
        add(name, (repo/name).read_bytes())
    budget_ref = add('EXPERIMENT_BUDGET.json', dict(schema='NY_WIDEGAP100K_EXPERIMENT_BUDGET_V1',
        authority='Main/Astra Builder under user standing directives', machine_lease_extended=False,
        root=str(remote), lease=old['lease'], device_uuid='GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8',
        start_unix=started, deadline_unix=started+budget.ALLOCATION_SECONDS,
        max_gpu_seconds=budget.RUN_SECONDS, calibration_reserve_seconds=budget.RESERVE_SECONDS,
        source_sha256={name: reference['sha256'] for name, reference in entries.items() if name.endswith('.py') and not name.startswith('support/')}))
    config['experiment_budget'] = budget_ref
    config_ref = add('TRAIN_CONFIG.json', config)
    gate = add('LOCAL_CPU_TESTS.json', (work/'evidence/WIDEGAP100K_AUTHOR_CPU_V2.json').read_bytes())
    inventory = dict(schema='NY_R167_RELEASED_RECEIVING_V1', root=str(remote), files=entries, config=config_ref,
        local_CPU_gate=gate, test_support_directory='support', hostname_sha256=old['hostname_sha256'], lease=old['lease'],
        lease_safe_end_unix=old['lease_safe_end_unix'], allocation_end_unix=started+budget.ALLOCATION_SECONDS, experiment_budget=budget_ref,
        selected_contests=old['selected_contests'], permitted_caption_pools=['judge_train', 'judge_dev'],
        locked_validation_files_copied=False, FINAL_files_copied=False, images_copied=False, no_automatic_retry=True,
        objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC', scoped_device='NODE4_PHYSICAL2_ONLY')
    budget.validate(data.bound(data.file_ref(payload/'EXPERIMENT_BUDGET.json')), inventory, config, time.time())
    inventory_ref = data.private_write(payload/'INVENTORY.json', inventory)
    data.require(sum(reference['bytes'] for reference in entries.values()) <= 512*1024**2, 'unchanged512MiB_receiving_limit')
    archive = root/'PAYLOAD.tar.gz'
    with tarfile.open(archive, 'x:gz') as stream:
        for name in sorted(entries):
            stream.add(payload/name, arcname=name, recursive=False)
        stream.add(payload/'INVENTORY.json', arcname='INVENTORY.json', recursive=False)
    data.require(archive.stat().st_size <= 128*1024**2, 'unchanged128MiB_transport_limit')
    reference = data.private_write(root/'TRANSPORT.json', dict(remote_root=str(remote), archive=data.file_ref(archive),
        inventory=inventory_ref, config=config_ref, files=len(entries), declared_bytes=sum(row['bytes'] for row in entries.values())))
    print(json.dumps(dict(transport=reference, inventory_sha256=inventory_ref['sha256'], config=config_ref,
        archive=data.file_ref(archive), remote_root=str(remote))))


if __name__ == '__main__':
    build()
