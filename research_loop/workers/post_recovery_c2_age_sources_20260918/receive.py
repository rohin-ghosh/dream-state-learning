"""Materialize only adapter files for later, separately admitted age evaluation."""

import json
from pathlib import Path
import time

import sources


def require_judge(judge):
    if (judge['step'], judge['rank'], judge['adapter_sha256']) != (15625, 8, sources.JUDGE_ADAPTER):
        raise ValueError('same_adopted_judge_epoch')
    if judge['config']['adapter']['adapter_model.safetensors']['sha256'] != sources.JUDGE_ADAPTER:
        raise ValueError('same_adopted_judge_model_bytes')


def finish(root):
    if time.time() >= sources.OVX4_END:
        raise ValueError('receiving_conservative_lease_bound')
    inputs = json.loads((root / 'INPUTS.private.json').read_text())
    data = json.loads((root / 'CAPTURED.private.json').read_text())
    sources.validate_baseline(inputs)
    judge = inputs['adopted_judge']
    require_judge(judge)
    primary = Path('/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-base-v1/primary_scalar.json')
    if sources.sha(primary) != judge['config_sha256']:
        raise ValueError('primary_epoch_config_unchanged')
    for reference in judge['config']['adapter'].values():
        if sources.sha(reference['path']) != reference['sha256']:
            raise ValueError('adopted_judge_adapter_file_unchanged')
    baseline = data['baseline']
    current = data['current']
    incoming = root / 'incoming' / current['source_relative']
    if json.loads((incoming / 'SOURCE.json').read_text()) != current:
        raise ValueError('exact_transferred_capture')
    rows = []
    for label, source, exposure, directory in (
        ('C2_NOW', current, data['current_exposure'], incoming),
        ('C2_SLEEP51', baseline, data['baseline_exposure'],
            Path('/localhome/local-rohing/orch_r232_age_probe_20260918/sources/sleep_000051'))):
        if not exposure['eligible'] or exposure['source_cut_sha256'] != source['sleep_complete_sha256']:
            raise ValueError('same_source_eligible_exposure')
        name = label + '_sleep_' + str(source['absolute_sleep']).zfill(6) + '_' + source['sleep_complete_sha256'][:16]
        destination = root / 'sources' / name
        safety = sources.stage_adapter(directory, destination, source)
        public_source = dict(source, source_name=label, source_relative=name,
            eligibility='ELIGIBLE_RECORDED_EXPOSURE_AUDIT', evaluation='NOT_ENROLLED',
            source_context_copied_or_loaded=False, optimizer_rng_copied_or_loaded=False,
            baseline_archive_reused=label == 'C2_SLEEP51')
        sources.write_once(destination / 'SOURCE.json', public_source)
        sources.write_once(destination / 'EXPOSURE.json', exposure)
        row = dict(label=label, source_relative='sources/' + name, adapter_relative='sources/' + name + '/adapter',
            source_sha256=sources.sha(destination / 'SOURCE.json'), exposure_sha256=sources.sha(destination / 'EXPOSURE.json'),
            absolute_sleep=source['absolute_sleep'], optimizer_steps=source['optimizer_steps'],
            adapter_state_sha256=source['adapter_state_sha256'], sleep_complete_index=source['sleep_complete_index'],
            sleep_complete_sha256=source['sleep_complete_sha256'], adapter_file_sha256=source['copy_files']['adapter/adapter_model.safetensors']['sha256'],
            copy_files=source['copy_files'], existing_archive_reused=label == 'C2_SLEEP51',
            source_status='CPU_SOURCE_READY_NOT_ENROLLED_NOT_EVALUATED', **safety)
        rows.append(row)
    result = dict(schema='C2_AGE_ADAPTER_ONLY_SOURCES_READY_V1', prepared_unix=time.time(),
        receiver_alias='ovx4', receiving_root_relative='orch_post_recovery_c2_age_sources_20260918',
        selection=data['selected'], sources=rows, exposure=dict(current=data['current_exposure'], baseline=data['baseline_exposure']),
        original_scene_pins=inputs['pins'], judge_epoch=dict(name='judge15625-base-v1', rank=8, step=15625,
            primary_config_sha256=judge['config_sha256'], adapter_sha256=sources.JUDGE_ADAPTER,
            actual_gpu_epoch_loaded_by_this_task=False), future_eval_contract=dict(parent_tokens=0,
            source_context_loaded=False, optimizer_loaded=False, rng_loaded=False, training_updates=0,
            token_budget=6144, seeds=[23201, 23202], scenes=3, new_batch_admission_required=True),
        authority=dict(node5_source_cutoff_utc='2026-09-20T18:00:00Z',
            ovx4_preparation_conservative_cutoff_utc='2026-09-30T00:00:00Z', lease_extension=False),
        no_gpu_dispatch=True, learner_signals=[], existing_attempt3_modified=False,
        raw_records_or_panels_published=False, context_optimizer_rng_loaded=False)
    sources.write_once(root / 'READY.json', result)
    return result
