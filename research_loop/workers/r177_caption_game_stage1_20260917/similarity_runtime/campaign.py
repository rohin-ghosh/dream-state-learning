"""R167-authorized TRAIN-only similarity calibration, never FINAL or child state."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from gpu import ny_caption_similarity as runtime
from gpu.ny_caption_pixels import LabeledPair, PixelArchive, PixelConfig, calibrate_pairs, cosine, embedding_text


ROOT = HERE / 'campaign1'
SOURCE_INPUT_SHA = 'ab14d9424a5d998e7fb64afbee34dc14d35ffbd111e1fb6776e31c5d0cff0d06'
ENCODER_SHA = '110116b20f71ecbd1149332d0fabbeb1bf15a48d51ff8bc0f80b52eee1f1e2a6'


def prepare():
    os.umask(0o077)
    ROOT.mkdir(mode=0o700, exist_ok=False)
    handoff_path = HERE.parent / 'data_judge/SIMILARITY_TRAIN_HANDOFF.json'
    handoff_ref = runtime.file_pin(handoff_path)
    handoff = runtime.bound(handoff_ref)
    runtime.require(handoff['status'] == 'READY_TRAIN_ONLY_NO_JUDGE_CHECKPOINT_DEPENDENCY'
        and not handoff['FINAL_included'] and not handoff['locked_validation_included']
        and not handoff['uncanny_included'] and handoff['private_input']['sha256'] == SOURCE_INPUT_SHA,
        'exact_Ampere_TRAIN_only_handoff')
    packet_ref = handoff['private_input']
    packet = runtime.bound(packet_ref)
    runtime.require(packet['schema'] == 'NY_SIMILARITY_TRAIN_INPUT_V1' and packet['permitted_pool'] == 'judge_train'
        and not any(packet[field] for field in ('FINAL_used', 'judge_dev_used', 'locked_validation_used', 'prior_judge_checkpoint_used')),
        'no_other_pools_or_trained_judge')
    roles = packet['partitions']
    runtime.require(not set(roles['fitting']) & set(roles['calibration_holdout']), 'disjoint_whole_contest_partitions')
    groups_by_role = {}
    for role in ('fitting', 'calibration_holdout'):
        members = set(roles[role])
        groups = [sorted(group) for group in packet['scene_groups'] if set(group) <= members]
        runtime.require({contest for group in groups for contest in group} == members, 'whole_scene_groups_preserved')
        groups.sort(key=lambda group: runtime.sha(runtime.canonical(group)))
        random.Random(177).shuffle(groups)
        groups_by_role[role] = groups[:24 if role == 'fitting' else 6]
    runtime.require(len(groups_by_role['fitting']) == 24 and len(groups_by_role['calibration_holdout']) == 6,
        'thirty_available_independent_groups')
    selected_groups = groups_by_role['fitting'] + groups_by_role['calibration_holdout']
    runtime.require(all(len(group) == 1 for group in selected_groups), 'fixed_thirty_contest_design_no_group_splitting')
    aliases = [f'opaque_scene_group_{index:03d}' for index in range(30)]
    shuffled = list(aliases)
    random.Random(177).shuffle(shuffled)
    held_aliases = sorted(shuffled[:6])
    fit_aliases = sorted(set(aliases) - set(held_aliases))
    alias_map = {}
    for role, available_aliases in (('fitting', fit_aliases), ('calibration_holdout', held_aliases)):
        for group, alias in zip(groups_by_role[role], available_aliases):
            for contest in group:
                alias_map[contest] = alias
    selected = [group[0] for group in selected_groups]
    row_refs = {contest: packet['contests'][contest]['rows'] for contest in selected}
    source_bytes = sum(reference['bytes'] for reference in row_refs.values())
    runtime.require(source_bytes <= 512 * 1024 * 1024, 'finite_selected_TRAIN_row_read_envelope')
    plan = dict(schema='NY_SIMILARITY_FROZEN_SELECTION_V1', input=packet_ref, handoff=handoff_ref,
        seed=177, heldout_fraction=.2, groups_by_role=groups_by_role, contest_group_aliases=alias_map,
        requested_pairs=300, natural_pair_slots=150, generated_variant_pair_slots=150,
        row_refs=row_refs, source_read_precharge_bytes=source_bytes, replacement_after_labels=False,
        group_alias_policy='Bijective opaque aliases fixed before data/labels so unchanged PixelArchive calibrator '
            'implements exactly Ampere fitting versus calibration_holdout; no contest/group is split or merged.',
        selected_before_caption_or_label_reads=True, label_source='provisional_model_not_human_truth')
    plan_ref = runtime.private_write(ROOT / 'SELECTION_PLAN.private.json', plan)
    scope = dict(schema='NY_SIMILARITY_BOUNDED_SCOPE_V1', label_call_cap=360, verification_call_cap=32,
        pair_label_cap=360, active_seconds_max=3600, absolute_end_unix=1789673400, retries=0,
        provider_model=runtime.LABEL_MODEL, allowed_pool='judge_train', locked_validation_reads=0, FINAL_reads=0,
        lane_id='similarity_calibration', task_started_utc='2026-09-17T18:40:17Z',
        admitted_wall_choice='R177 CPU-only campaign independently clipped at 19:30UTC; not reuse of R176 budget',
        label_generation_requests_count_against_label_call_cap=True, parallel_request_cap=3,
        max_completion_tokens_per_request=8192, source_input=packet_ref, selection_plan=plan_ref,
        encoder_manifest=dict(path=str(HERE / 'encoder_acquisition1/ENCODER_MANIFEST.json'), sha256=ENCODER_SHA))
    runtime.private_write(ROOT / 'SCOPE.json', scope)
    seeds = []
    natural = []
    missing = []
    for ordinal, contest in enumerate(selected):
        entry = packet['contests'][contest]
        reference = row_refs[contest]
        path = Path(reference['path'])
        runtime.require(path.is_absolute() and path == path.resolve() and path.stat().st_size == reference['bytes'], 'exact_TRAIN_rows_size')
        runtime.private_write(ROOT / f'SOURCE_READ_{ordinal:03d}.json', dict(reference=reference,
            charged_before_read_bytes=reference['bytes'], pool='judge_train'))
        rng = random.Random(177 + ordinal)
        reservoir = []
        seen = set()
        eligible = 0
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for raw in stream:
                runtime.require(len(raw) <= 128 * 1024, 'bounded_TRAIN_row')
                digest.update(raw)
                row = json.loads(raw)
                runtime.require(str(row['contest_id']) == str(contest), 'TRAIN_contest_join')
                caption = row['caption']
                if type(caption) is not str or not 1 <= len(caption.split()) <= 50 or len(caption) > 1200 or caption in seen:
                    continue
                seen.add(caption)
                eligible += 1
                if len(reservoir) < 10:
                    reservoir.append(caption)
                else:
                    replacement = rng.randrange(eligible)
                    if replacement < 10:
                        reservoir[replacement] = caption
        runtime.require(digest.hexdigest() == reference['sha256'], 'actual_TRAIN_rows_hash')
        if len(reservoir) != 10:
            missing.append(dict(contest_id=contest, reason='INSUFFICIENT_SELECTED_TRAIN_CAPTIONS_NO_REPLACEMENT'))
            continue
        for position in range(5):
            seed_id = runtime.sha(runtime.canonical([contest, position, 'seed']))
            base = dict(contest_id=contest, scene=entry['canonical_scene'], caption_a=reservoir[position],
                group_id=alias_map[contest], source_rows=reference)
            seeds.append(dict(base, seed_id=seed_id))
            natural.append(dict(base, pair_id=runtime.sha(runtime.canonical([contest, position, 'natural'])),
                caption_b=reservoir[position + 5], pair_kind='sampled_distinct_TRAIN_captions'))
    payload = dict(seeds=seeds, natural_pairs=natural, missing=missing, source_input=packet_ref, selection_plan=plan_ref)
    input_ref = runtime.private_write(ROOT / 'PREPARED_INPUT.private.json', payload)
    summary = dict(status='EXACT_TRAIN_SAMPLE_AND_PARTITION_FROZEN', observed_utc=datetime.now(timezone.utc).isoformat(),
        selected_contests=30, fitting_contests=24, heldout_contests=6, seed_count=len(seeds),
        natural_pair_count=len(natural), missing_contests=len(missing), source_read_bytes=source_bytes,
        source_input=packet_ref, selection_plan=plan_ref, prepared_input=input_ref,
        provider_calls=0, locked_validation_reads=0, FINAL_reads=0, R176_reads=0, GPU_calls=0)
    runtime.private_write(ROOT / 'PREPARATION_PUBLIC.json', summary)
    print(json.dumps(summary, sort_keys=True))


def bindings():
    return {name: runtime.file_pin(REPO / name) for name in ('gpu/ny_caption_similarity.py',
        'gpu/ny_caption_pixels.py', 'gpu/ny_caption_game.py', 'tests/test_ny_caption_similarity.py')}


def cpu_gate():
    scope_ref = runtime.file_pin(ROOT / 'SCOPE.json')
    scope = runtime.bound(scope_ref)
    encoder = runtime.FrozenCPUEncoder(scope['encoder_manifest'])
    first = encoder.encode_many(['A synthetic CPU provenance check.', 'A synthetic CPU provenance check.'])
    runtime.require(first[0] == first[1] and len(first[0]) == 384, 'actual_deterministic_frozen_sentence_encoder')
    inputs = runtime.bound(runtime.file_pin(ROOT / 'PREPARED_INPUT.private.json'))
    probe_texts = [embedding_text(item['scene'], item['caption_a']) for item in inputs['seeds']]
    encoder.encode_many(probe_texts)
    results = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_ny_caption_similarity.py',
        'tests/test_ny_caption_pixels.py', 'tests/test_ny_caption_game.py'], cwd=REPO, capture_output=True)
    test_ref = runtime.private_write(ROOT / 'CPU_TESTS_01.txt', results.stdout + results.stderr)
    runtime.require(results.returncode == 0, 'own_CPU_contract_tests_before_real_calls')
    receipt = dict(status='ACTUAL_CPU_AND_PROVENANCE_GATE_PASS', observed_utc=datetime.now(timezone.utc).isoformat(),
        source_pins=bindings(), encoder=encoder.provenance, tests=test_ref,
        actual_TRAIN_seed_embeddings=len(probe_texts), actual_deterministic_check=True,
        provider_calls=0, GPU_calls=0, scope=scope_ref)
    runtime.private_write(ROOT / 'CPU_GATE.json', receipt)
    print(json.dumps(dict(status=receipt['status'], actual_TRAIN_seed_embeddings=len(probe_texts),
        CPU_gate=runtime.file_pin(ROOT / 'CPU_GATE.json'), source_pins=receipt['source_pins']), sort_keys=True))


def annotate():
    scope_ref = runtime.file_pin(ROOT / 'SCOPE.json')
    gate = runtime.bound(runtime.file_pin(ROOT / 'CPU_GATE.json'))
    runtime.require(gate['status'] == 'ACTUAL_CPU_AND_PROVENANCE_GATE_PASS' and gate['source_pins'] == bindings()
        and gate['scope'] == scope_ref, 'exact_CPU_source_scope_before_dispatch')
    start = ROOT / 'ANNOTATION_ONCE.json'
    runtime.private_write(start, dict(started_unix=time.time(), no_retry=True, scope=scope_ref))
    budget = runtime.CallBudget(ROOT / 'calls', scope_ref)
    annotator = runtime.AstraAnnotator(budget)
    runtime.require(bool(annotator._key), 'fresh_environment_key_required_no_dispatch')
    prepared = runtime.bound(runtime.file_pin(ROOT / 'PREPARED_INPUT.private.json'))
    seed_batches = [prepared['seeds'][index:index + 10] for index in range(0, len(prepared['seeds']), 10)]
    generated = {}
    failures = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(annotator.variants, f'variants_{index:03d}',
            [dict(seed_id=item['seed_id'], scene=item['scene'], caption=item['caption_a']) for item in batch]): index
            for index, batch in enumerate(seed_batches)}
        for future in as_completed(pending):
            try:
                generated.update(future.result())
            except Exception as error:
                failures.append(dict(phase='variants', batch=pending[future], error_type=type(error).__name__))
    pairs = list(prepared['natural_pairs'])
    for seed in prepared['seeds']:
        if seed['seed_id'] in generated:
            pairs.append(dict(seed, pair_id=runtime.sha(runtime.canonical([seed['seed_id'], 'variant'])),
                caption_b=generated[seed['seed_id']], pair_kind='generated_paraphrase_intent_not_ground_truth'))
    runtime.private_write(ROOT / 'FROZEN_UNLABELLED_PAIRS.private.json', dict(pairs=pairs,
        generated_variant_count=len(generated), missing_generated_variants=len(prepared['seeds']) - len(generated)))
    labeled = []
    batches = [pairs[index:index + 10] for index in range(0, len(pairs), 10)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(annotator.labels, f'labels_{index:03d}',
            [{key: item[key] for key in ('pair_id', 'scene', 'caption_a', 'caption_b')} for item in batch]): index
            for index, batch in enumerate(batches)}
        for future in as_completed(pending):
            index = pending[future]
            try:
                labels, receipt = future.result()
                for item in batches[index]:
                    pair = {key: item[key] for key in ('pair_id', 'contest_id', 'scene', 'caption_a', 'caption_b', 'group_id')}
                    pair.update(labels=labels[item['pair_id']], label_source='llm', labeler_id=runtime.LABEL_MODEL,
                        labeler_revision=runtime.sha(runtime.LABEL_SYSTEM.encode()))
                    labeled.append(pair)
            except Exception as error:
                failures.append(dict(phase='labels', batch=index, error_type=type(error).__name__))
            print(json.dumps(dict(phase='annotation_progress', finished_batches=index + 1,
                valid_labeled_pairs=len(labeled), failure_batches=len(failures))), flush=True)
    pair_document = dict(allowed_pool='judge_train', locked_validation_reads=0, FINAL_reads=0,
        source_input=prepared['source_input'], selection_plan=prepared['selection_plan'],
        seed=177, heldout_fraction=.2, pairs=sorted(labeled, key=lambda pair: pair['pair_id']), provisional_model_labels=True)
    reference = runtime.private_write(ROOT / 'LABELED_PAIRS.private.json', pair_document)
    runtime.private_write(ROOT / 'ANNOTATION_FAILURES.private.json', failures)
    summary = dict(status='ANNOTATION_COMPLETE_PROVISIONAL', valid_labeled_pairs=len(labeled),
        intended_pair_slots=300, unavailable_or_failed_pair_slots=300 - len(labeled),
        generated_variants=len(generated), failure_batches=len(failures), labels=reference,
        budget=budget.summary(), human_truth=False, private_content_disclosed=False)
    runtime.private_write(ROOT / 'ANNOTATION_PUBLIC.json', summary)
    print(json.dumps(summary, sort_keys=True))


def verifier_smokes():
    scope_ref = runtime.file_pin(ROOT / 'SCOPE.json')
    budget = runtime.CallBudget(ROOT / 'calls', scope_ref)
    annotator = runtime.AstraAnnotator(budget)
    report = runtime.bound(runtime.file_pin(ROOT / 'calibration1/CALIBRATION.private.json'))
    config_path = ROOT / 'calibration1/FROZEN_RUNTIME_CONFIG.json'
    runtime.require(config_path.exists(), 'calibrated_threshold_required_for_smokes')
    config_ref = runtime.file_pin(config_path)
    runtime_config = runtime.bound(config_ref)
    document = runtime.bound(runtime.file_pin(ROOT / 'LABELED_PAIRS.private.json'))
    holdout_ids = set(report['heldout_pair_ids'])
    heldout = [item for item in document['pairs'] if item['pair_id'] in holdout_ids]
    same = [item for item in heldout if item['labels']['primary'] is True]
    different = [item for item in heldout if item['labels']['primary'] is False]
    selected = same[:15] + different[:15]
    runtime.private_write(ROOT / 'VERIFIER_SMOKE_SELECTION.private.json', dict(pair_ids=[item['pair_id'] for item in selected],
        maximum_verifier_requests=32, selection_from='frozen calibration holdout only',
        labels_used_only_for_stratification_not_threshold_tuning=True))
    results = []
    verifier = runtime.SameJokeVerifier(annotator, lane_id='similarity_calibration')
    for item in selected:
        try:
            prediction = verifier(item['scene'], item['caption_b'], item['caption_a'])
            results.append(dict(pair_id=item['pair_id'], expected=item['labels']['primary'], predicted=prediction))
        except Exception as error:
            results.append(dict(pair_id=item['pair_id'], expected=item['labels']['primary'], predicted=None,
                error_type=type(error).__name__))
    encoder = runtime.FrozenCPUEncoder(runtime_config['encoder_manifest'])
    integration = []
    for item in same[15:]:
        if len(integration) == 2:
            break
        vectors = encoder.encode_many([embedding_text(item['scene'], item['caption_a']), embedding_text(item['scene'], item['caption_b'])])
        if cosine(*vectors) < runtime_config['pixel_config']['rho_primary']:
            continue
        archive = runtime.archive_from_config(config_ref, encoder, verifier, agent_id='similarity_calibration',
            contest_id=item['contest_id'], scene=item['scene'])
        archive.submit(item['caption_b'], accepted=True, q=.8)
        before = budget.summary()['verification_calls_charged']
        try:
            second = archive.submit(item['caption_a'], accepted=True, q=.8)
            after = budget.summary()['verification_calls_charged']
            replay = archive.submit(item['caption_a'], accepted=True, q=.8)
            runtime.require(replay == second and budget.summary()['verification_calls_charged'] == after,
                'actual_idempotent_archive_replay_no_extra_provider_call')
            integration.append(dict(status='ACTUAL_PIXEL_ARCHIVE_INTEGRATION_PASS',
                verifier_called=after == before + 1, final_pixel_count=archive.pixel_count))
        except Exception as error:
            integration.append(dict(status='ACTUAL_PIXEL_ARCHIVE_INTEGRATION_FAILED_CHARGED', error_type=type(error).__name__))
    valid = [item for item in results if type(item['predicted']) is bool]
    positives = sum(item['expected'] for item in valid)
    negatives = len(valid) - positives
    false_merge = sum(not item['expected'] and item['predicted'] for item in valid)
    false_split = sum(item['expected'] and not item['predicted'] for item in valid)
    runtime.private_write(ROOT / 'VERIFIER_SMOKES.private.json', dict(results=results, integration=integration))
    summary = dict(status='ACTUAL_VERIFIER_SMOKES_COMPLETE_PROVISIONAL', valid_smokes=len(valid),
        missing_smokes=len(results) - len(valid), same_reference_count=positives, different_reference_count=negatives,
        false_merge_count=false_merge, false_split_count=false_split,
        false_merge_rate=false_merge / negatives if negatives else None,
        false_split_rate=false_split / positives if positives else None,
        archive_integration_smokes=len(integration), archive_integration_passes=sum(item['status'] == 'ACTUAL_PIXEL_ARCHIVE_INTEGRATION_PASS' for item in integration),
        budget=budget.summary(), provisional=True, human_truth=False,
        limitation='Same provider/model/instruction repeat annotations with caption order reversed, not independent human truth or full archive false-merge/split rates.',
        private_content_disclosed=False)
    runtime.private_write(ROOT / 'VERIFIER_SMOKES_PUBLIC.json', summary)
    print(json.dumps(summary, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'cpu-gate', 'annotate', 'verifier-smokes'])
    action = parser.parse_args().action
    {'prepare': prepare, 'cpu-gate': cpu_gate, 'annotate': annotate, 'verifier-smokes': verifier_smokes}[action]()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='CAMPAIGN_STEP_FAILED_PRESERVED_NO_RETRY', error_type=type(error).__name__,
            private_content_disclosed=False)))
        raise SystemExit(2)
