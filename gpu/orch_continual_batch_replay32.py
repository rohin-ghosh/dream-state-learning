"""Native-only preparation, shared reservation and conditional replay compilation."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import orch_continual_batch_publish as publisher
from gpu.orch_continual_batch_handoff import wrap_row
from gpu.orch_continual_batch_remote_feed import read, sha, write_once, reserve_budget
from organism_v6 import orch_continual_batch as policy
from organism_v6 import orch_continual_batch_replay32 as arm
from organism_v6 import orch_continual_batch_replay_compile as compiler


SOURCE = Path('/localhome/local-rohing/orch_rich_hot_node2_checkpoint99_20260915_attempt1')
LEDGER = Path('/localhome/local-rohing/orch_continual_batch_20260915_segment2_disk_native1')


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def tokenizer(prepared):
    from gpu import astra_portable_actor_bundle as portable
    return portable.source.native.load_local_tokenizer(prepared['model_dir'])


def check_runtime(root):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    policy.require(root.resolve().is_relative_to('/localhome/local-rohing') and
                   root.name.startswith('orch_continual_batch_replay32_'), 'owned_native_only_root')
    policy.require(all(sha(root / name) == digest for name, digest in read(root / 'SOURCE_FREEZE.json').items()),
                   'native_runtime_hash_drift')


def prepare(root):
    check_runtime(root)
    prepared = read(SOURCE / 'PREPARE.json')
    registry = read(root / 'SOURCE_REGISTRY.json')
    source = registry['sources'][str(SOURCE)]
    policy.require(prepared['identity']['state_sha256'] == arm.STATE and
                   sha(SOURCE / 'PREPARE.json') == source['prepare_sha256'] and
                   sha(SOURCE / 'source.tar') == source['source_code_sha256'] and
                   all(sha(SOURCE / name) == digest for name, digest in prepared['files'].items()), 'exact_source_inputs')
    for origin, name in ((LEDGER / 'EXCLUSIONS.json', 'EXCLUSIONS.json'),
                         (SOURCE / 'shard0/LOADED.json', 'LOADED.json'),
                         (SOURCE / 'SELECTED_FULL_HANDOFF.json', 'CHECKPOINT.json')):
        with (root / name).open('xb') as stream:
            stream.write(origin.read_bytes())
    loaded, exclusions = read(root / 'LOADED.json'), read(root / 'EXCLUSIONS.json')
    policy.require(loaded['observed'] == prepared['identity'] and
                   sha(root / 'EXCLUSIONS.json') == source['exclusions_sha256'], 'identity_exclusions')
    encoder = tokenizer(prepared)
    registration = dict(source, arm=arm.ARM, native_root=str(SOURCE), allowlisted_generation_roots=[str(SOURCE)],
        eos_token_id=encoder.eos_token_id, batch_size=32, sample_size=12, sample_seed=arm.SEED,
        deadline_unix=read(LEDGER / 'REGISTRATION.json')['segment_deadline_unix'],
        review_invocations=2, shared_limit=128, selection='FIRST32_OF39_BY_FINISHED_UNIX_THEN_NATIVE_PATH_BEFORE_SEMANTICS',
        registered_unix=time.time(), fit_scope='PENDING_LAPLACE_ISOLATED_PAIRED_WINDOW',
        lineage=dict(child_state_sha256=arm.STATE, checkpoint_manifest_sha256=sha(root / 'CHECKPOINT.json'),
                     checkpoint_commit_sha256=prepared['lineage']['commit_sha256']))
    write_once(root / 'REGISTRATION.json', registration)
    records = [json.loads(line) for line in (SOURCE / 'gsm8k_train.jsonl').read_text().splitlines()]
    candidates, tasks = [], {}
    for path in sorted((SOURCE / 'shard0').glob('*.json')):
        call = read(path)
        if call.get('family') != 'math' or 'response' not in call:
            continue
        record = records[int(call['source_task_id'].rsplit('-', 1)[1])]
        task = dict(id=call['source_task_id'], family='math', question=record['question'],
            gold=record['answer'].rsplit('####', 1)[1].strip(),
            question_sha256=policy.math.digest(' '.join(record['question'].lower().split())))
        tasks[task['id']] = task
        intent_path = SOURCE / 'reservations' / f'0_{call["task_id"]}_{call["stage"]}.json'
        policy.require(all(call.get(key) == value for key, value in read(intent_path).items()), 'native_intent_binding')
        provenance = dict(original_native_task_id=call['task_id'], source_native_path=str(path), raw_call_path=str(path),
            raw_call_sha256=sha(path), native_intent_ref=reference(intent_path), native_finished_unix=call['finished_unix'],
            registered_source_purpose=policy.PURPOSE, source_registry_sha256=sha(root / 'SOURCE_REGISTRY.json'),
            source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False, instruction_regime='STEERED',
            instruction_amount_tokens=len(encoder.encode(call['messages'][0]['content'], add_special_tokens=False)),
            mechanical_branch_counts=None, self_reported_branch_counts=None)
        normalized = compiler.normalize_native_call(call, task, registration, provenance)
        candidates.append(policy.mechanical(normalized, task, loaded, dict(initial=prepared['identity']), encoder,
                                            exclusions, provenance))
    rows = arm.first32(candidates)
    write_once(root / 'TASKS.json', dict(tasks=list(tasks.values())))
    write_once(root / 'CANDIDATES.json', rows)
    selected = arm.sample(rows)
    write_once(root / 'SAMPLE_REGISTRATION.json', dict(semantic_results_seen=False, registered_unix=time.time(),
        sample_target_sha256s=[row['target_sha256'] for row in selected],
        candidates_sha256=sha(root / 'CANDIDATES.json'), registration_sha256=sha(root / 'REGISTRATION.json')))
    checks = dict(arm=arm.ARM, source_count=len(candidates), selected_count=len(rows), sample_count=len(selected),
        all39_exact_encoder_pass=True, source_state_sha256=arm.STATE, exclusions_sha256=sha(root / 'EXCLUSIONS.json'),
        candidates_sha256=sha(root / 'CANDIDATES.json'), sample_sha256=sha(root / 'SAMPLE_REGISTRATION.json'),
        first_native_capture_unix=min(row['provenance']['native_finished_unix'] for row in rows),
        last_native_capture_unix=max(row['provenance']['native_finished_unix'] for row in rows),
        source_generated_tokens=sum(row['generated_tokens'] for row in rows), raw_storage='NATIVE_ONLY', gpu_calls=0)
    write_once(root / 'SOURCE_CHECKS.json', checks)
    request = dict(native_evidence_root=str(root), **{key: reference(root / name) for key, name in
        (('registration', 'REGISTRATION.json'), ('source_registry', 'SOURCE_REGISTRY.json'), ('exclusions', 'EXCLUSIONS.json'),
         ('checkpoint_handoff', 'CHECKPOINT.json'), ('loaded', 'LOADED.json'), ('tasks', 'TASKS.json'),
         ('candidates', 'CANDIDATES.json'), ('sample', 'SAMPLE_REGISTRATION.json'))})
    write_once(root / 'COMPILE_REQUEST_BASE.json', request)
    packets = []
    for group in range(2):
        packet = [dict(target_source_lines=policy.source_lines(row['target']), student_prefix=row['student_prefix'],
            question=row['question'], gold=row['gold'], target_sha256=row['target_sha256'],
            raw_call_sha256=row['provenance']['raw_call_sha256'], student_prefix_sha256=row['student_prefix_sha256'])
            for row in selected[group * 6:(group + 1) * 6]]
        write_once(root / f'PACKET_{group}.json', packet)
        packets.append(packet)
    return dict(native_root=str(root), checks=checks, packets=packets)


def packets(root):
    check_runtime(root)
    return dict(native_root=str(root), checks=read(root / 'SOURCE_CHECKS.json'),
                packets=[read(root / f'PACKET_{group}.json') for group in range(2)])


def reserve(root):
    check_runtime(root)
    policy.require(not (root / 'RESERVING.json').exists(), 'one_reservation_attempt_only_reconcile_existing')
    with (LEDGER / 'BUDGET.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        before = read(LEDGER / 'BUDGET.json')
        after = reserve_budget(before, read(root / 'REGISTRATION.json')['deadline_unix'], time.time())
        rows = read(root / 'CANDIDATES.json')
        seen = set(read(LEDGER / 'SEEN.json'))
        policy.require(not seen.intersection(row['target_sha256'] for row in rows), 'previously_seen_target_no_mix')
        write_once(root / 'RESERVING.json', dict(before=before, after=after, sample_sha256=sha(root / 'SAMPLE_REGISTRATION.json')))
        publisher.write(LEDGER / 'BUDGET.json', after)
        publisher.write(LEDGER / 'SEEN.json', sorted(seen | {row['target_sha256'] for row in rows}))
        receipt = dict(arm=arm.ARM, before=before, after=after, invocations=2,
                       deadline_unix=read(root / 'REGISTRATION.json')['deadline_unix'], reset=False)
        write_once(root / 'RESERVATION.json', receipt)
    return receipt


def finalize(root):
    check_runtime(root)
    upload = root / 'PROVIDER_UPLOAD'
    inventory = read(upload / 'UPLOAD_INVENTORY.json')
    policy.require(all((upload / name).resolve().is_relative_to(upload.resolve()) and sha(upload / name) == digest
                       for name, digest in inventory.items()), 'provider_upload_hash_mismatch')
    transfer = dict(verified=True, inventory_sha256=sha(upload / 'UPLOAD_INVENTORY.json'), files=len(inventory))
    write_once(root / 'PROVIDER_UPLOAD_VERIFIED.json', transfer)
    rows = read(root / 'CANDIDATES.json'); selected = arm.sample(rows)
    reviews, usage = [], []
    for group in range(2):
        directory = upload / f'batch_000_{group}'
        measured = read(directory / 'USAGE.json')
        policy.require(not measured['tool_events'], 'provider_tools_forbidden')
        subset = selected[group * 6:(group + 1) * 6]
        result = policy.resolve_line_reviews(subset, read(directory / 'reader/result.json'))
        reviews.extend(policy.validate_review(subset, result)); usage.append(measured)
    decision, exported = arm.adjudicate(rows, reviews)
    write_once(root / 'SAMPLED_REVIEWS.json', reviews)
    write_once(root / 'PROVIDER_USAGE.json', usage)
    write_once(root / 'BATCH_DECISION.json', decision)
    result = dict(decision=decision, transfer=transfer, native_root=str(root),
        sampled_pass=sum(review['status'] == 'PASS' for review in reviews), admitted_rows=0,
        source_state_sha256=arm.STATE, fit_executed=False, held_readout_executed=False,
        reported_provider_components={key: sum(item['reported_components'].get(key, 0) for item in usage)
            for key in {key for item in usage for key in item['reported_components']}},
        branch_measurements=[dict(target_sha256=review['target_sha256'], branch_metrics=review.get('branch_metrics'),
            has_meaningful_branch=review['has_meaningful_branch'], semantic_novelty=review['semantic_novelty']) for review in reviews])
    if decision['accepted']:
        request = dict(read(root / 'COMPILE_REQUEST_BASE.json'), reviews=reference(root / 'SAMPLED_REVIEWS.json'))
        write_once(root / 'COMPILE_REQUEST.json', request)
        compiled = compiler.compile_bound_batch(request, tokenizer(read(SOURCE / 'PREPARE.json')))
        write_once(root / 'BATCH_BINDING.json', dict(admission_mode=policy.MODE, batch_author_accepted=True,
            candidates_sha256=sha(root / 'CANDIDATES.json'), reviews_sha256=sha(root / 'SAMPLED_REVIEWS.json'),
            sample_sha256=sha(root / 'SAMPLE_REGISTRATION.json'), arm=arm.ARM))
        wrappers = [wrap_row(row, sha(root / 'BATCH_BINDING.json')) for row in compiled['rows']]
        write_once(root / 'ROWS.json', wrappers)
        handoff = compiler.handoff(compiled['compiled'], compiled['registration'], str(root / 'ROWS.json'), sha(root / 'ROWS.json'))
        handoff.update(input_bindings=request, arm=arm.ARM)
        write_once(root / 'COMPILE_HANDOFF.json', handoff)
        manifest = dict(schema=policy.SCHEMA, batch_id=root.name, arm=arm.ARM, encoding='math_content_v2',
            admission_mode=policy.MODE, batch_author_accepted=True, population=32, sample_size=12,
            row_count=len(wrappers), rows_path='ROWS.json', rows_sha256=sha(root / 'ROWS.json'),
            source_kind='CHECKPOINT_DERIVED_TRAIN', source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False,
            source_state_sha256=arm.STATE, individual_semantic_status='SAMPLED_PASS_UNSAMPLED_UNREVIEWED',
            fit_scope='PENDING_LAPLACE_ISOLATED_PAIRED_WINDOW', training_application_allowed=False,
            compile_handoff=reference(root / 'COMPILE_HANDOFF.json'), trainer_ingested=False)
        write_once(root / 'MANIFEST.json', manifest)
        result.update(admitted_rows=len(wrappers), accepted_sample_pass=decision['sample_pass'], unsampled_unreviewed=20,
                      native_manifest=reference(root / 'MANIFEST.json'), native_handoff=reference(root / 'COMPILE_HANDOFF.json'))
    write_once(root / 'RESULT_REDUCTION.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'packets', 'reserve', 'finalize'))
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(globals()[options.phase](options.root)))
