"""Read-only actual retained-sleep and subsequent generation custody receipts."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


BASE = Path('/localhome/local-rohing')
HELPERS_SHA = '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270'
POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
LIVES = {
    0: 'orch_r132_kernel_child_20260916_attempt1',
    1: 'orch_r136_raw_unparented_a40r1_20260916_attempt1',
    3: 'orch_r136_raw_parented_seed1_a40r3_20260916_attempt1',
    4: 'orch_r136_kernel_parented_a40r4_20260916_attempt1',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verified_state(document, key):
    envelope = document[key]
    state = envelope['state']
    require(envelope['sha256'] == digest(state), 'actual_stream_envelope_hash')
    history = state['history']
    require(history['state_sha256'] == digest({name: value for name, value in history.items()
            if name != 'state_sha256'}), 'actual_history_envelope_hash')
    return state


def verify_cycle(retained, requested, completed, post_request, response, committed, render_messages):
    before = verified_state(requested, 'resume_state')
    after = verified_state(completed, 'resume_state')
    post = verified_state(post_request, 'resume_state')
    generated = verified_state(committed, 'state')
    cycle = retained['cycle']
    threshold = min(before['context_limit'] * 3 // 4, before['context_limit'] - before['segment_tokens'])
    history = before['history']
    frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
    require(retained['schema'] == 'R179_CONTEXT_SURVIVES_SLEEP_V1'
            and retained['action'] == 'RETAIN_CONTEXT_ACROSS_SLEEP'
            and retained['threshold_tokens'] == threshold
            and 0 <= retained['visible_prompt_tokens'] < threshold
            and retained['context_limit'] == before['context_limit'], 'actual_below_threshold_retention')
    require(retained['history_sha256_before'] == retained['history_sha256_after'] == history['state_sha256']
            and retained['visible_frontier_before'] == frontier
            and retained['raw_event_count'] == len(history['events'])
            and retained['targets_rewritten'] is False and retained['optimizer_recipe_changed'] is False,
            'unchanged_actual_presleep_context_and_recipe')
    require(requested['cycle'] == completed['cycle'] == cycle
            and completed['status'] == 'COMPLETE' and completed['optimizer_steps'] > 0
            and after['pending'] is None and after['sleep_frontier'] == len(after['rows'])
            and after['history'] == history and after['rows'] == before['rows'], 'completed_positive_sleep_preserved_history_rows')
    require(before['pending'] == 'sleep:' + digest([row['source_sha256'] for row in before['rows'][before['sleep_frontier']:]])
            and completed['new_row_sha256'] == [row['source_sha256'] for row in before['rows'][before['sleep_frontier']:]],
            'same_training_frontier_no_replay')
    require(after['sleep_receipts'][:-1] == before['sleep_receipts']
            and after['sleep_receipts'][-1] == {key: value for key, value in completed.items() if key != 'resume_state'}
            and after['model_state_sha256'] == digest(completed['checkpoint_sha256']), 'actual_completed_model_and_receipt')
    require(post['history']['events'][:len(history['events'])] == history['events']
            and post['history']['operations'] == history['operations']
            and post['rows'] == after['rows'] and post['sleep_frontier'] == after['sleep_frontier']
            and post['sleep_receipts'] == after['sleep_receipts'], 'all_retained_context_visible_in_postsleep_request')
    require(post_request['history_sha256'] == digest(post['history'])
            and post_request['model_state_sha256'] == post['model_state_sha256'] == after['model_state_sha256']
            and post_request['deadline_unix'] == post['deadline_unix'] == after['deadline_unix'] == before['deadline_unix']
            and post_request['render_receipt']['all_history_tokens_masked'] is True, 'actual_postsleep_request_model_wall_masks')
    require(post['pending'] == digest({key: value for key, value in post_request.items() if key != 'resume_state'})
            and response['request_sha256'] == post['pending'], 'actual_request_response_binding')
    require(post_request['messages'] == render_messages(post, post_request['prompt_tokens']), 'canonical_postsleep_history_render')
    require(generated['pending'] is None and len(generated['rows']) == len(after['rows']) + 1
            and generated['rows'][:-1] == after['rows']
            and generated['rows'][-1]['prefix'] == post_request['messages']
            and generated['rows'][-1]['source_sha256'] == committed['source_sha256'] == digest(response)
            and generated['rows'][-1]['prefix_loss'] is False and generated['rows'][-1]['target_loss'] is True,
            'actual_committed_postsleep_generation_and_loss_masks')
    return dict(status='ACTUAL_COMPLETED_RETAINED_SLEEP_AND_POSTSLEEP_GENERATION', cycle=cycle,
        optimizer_steps_in_sleep=completed['optimizer_steps'], retained_history_sha256=history['state_sha256'],
        retained_raw_events=len(history['events']), unchanged_visible_frontier=frontier,
        post_sleep_history_sha256=post['history']['state_sha256'], actual_prompt_messages_sha256=digest(post_request['messages']),
        actual_response_sha256=digest(response), retained_learning_claim=False,
        native_recorded_prompt_tokens=post_request['prompt_tokens'], tokenizer_independently_recomputed=False)


def candidate(records):
    retained = requested = completed = post_request = response = None
    for record in records:
        kind, document = record['kind'], record['document']
        if kind == 'CONTEXT_RETAINED':
            retained, requested, completed, post_request, response = record, None, None, None, None
        elif retained and kind == 'SLEEP_REQUEST' and document['cycle'] == retained['document']['cycle']:
            requested = record
        elif requested and kind == 'SLEEP_COMPLETE' and document['cycle'] == retained['document']['cycle']:
            completed = record
        elif completed and kind == 'REQUEST' and post_request is None:
            post_request = record
        elif post_request and kind == 'RESPONSE' and response is None:
            response = record
        elif response and kind == 'COMMITTED':
            return retained, requested, completed, post_request, response, record
    return None


def load_helpers(lane):
    require(lane.parent.parent == BASE and lane.parent.name.startswith('orch_r179_node4_')
            and lane.name in ('lane0', 'lane1', 'lane3', 'lane4'), 'four_scoped_NODE4_preparations_only')
    path = lane.parent / 'r144_helpers.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == HELPERS_SHA, 'exact_readonly_helper_bytes')
    spec = importlib.util.spec_from_file_location('r179_proof_helpers', path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    return helpers


def canonical_messages(source, state, recorded_count):
    require(type(recorded_count) is int and 0 <= recorded_count <= state['context_limit'] - state['segment_tokens'],
            'bounded_actual_native_recorded_prompt_count')
    sys.path.insert(0, str(source))
    from organism_v6 import orch_r124_train_history as history_module
    require(Path(history_module.__file__).resolve() == source / 'organism_v6/orch_r124_train_history.py',
            'render_from_exact_actual_source_not_cached_other_lane')
    history = history_module.TrainHistory.restore(state['history'])
    rendered = history.render(lambda messages: recorded_count, state['context_limit'] - state['segment_tokens'],
        presentation=state.get('presentation'))
    require(all(label == -100 for label in rendered.labels), 'canonical_actual_history_prefix_masks')
    return rendered.messages


def identity_live(expected, helpers):
    try:
        return helpers.identity(expected['pid']) == expected
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return False


def inspect(lane, helpers):
    request = helpers.read(lane / 'STAGED.json')
    physical = int(lane.name[-1])
    root = BASE / LIVES[physical] / 'run1'
    require(request['physical'] == physical and request['old_plan']['root'] == str(root)
            and request['source_root'] == str(lane / 'source'), 'exact_original_life_and_successor_source')
    loaded_path = lane / 'LOADED_RECEIPT.json'
    if not loaded_path.exists():
        alive = identity_live(request['processes']['actor'], helpers)
        consumed = any((lane / name).exists() for name in ('RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json'))
        failed = any((lane / 'control' / name).exists() for name in ('FAILED.json', 'EXIT.json', 'SERVICE_EXIT.json'))
        failed = failed or (lane / 'RECOVERY_FAILED_BEFORE_NATIVE.json').exists()
        if consumed:
            failed = failed or any(helpers.read(path).get('retirement_started') is True
                                   for path in lane.glob('ERROR_*.json'))
        status = 'WAITING_FOR_ACTUAL_R179_LOAD'
        if not alive:
            status = ('PLANNED_HANDOFF_WAITING_FOR_LOAD' if consumed and not failed
                      else 'ORIGINAL_OWNER_REQUIRES_REVALIDATION_OR_RECOVERY')
        return dict(status=status, physical=physical, original_identity_live=alive,
            recovery_or_owner_revalidation_needed=not alive and (not consumed or failed))
    loaded = helpers.read(loaded_path)
    proof = helpers.read(lane / 'SOURCE_PROOF.json')
    require(helpers.sha(lane / 'SOURCE_PROOF.json') == request['source_proof_sha256']
            and helpers.inventory_files(request['source_root']) == proof['new_inventory']
            and proof['new_inventory']['gpu/orch_r179_context_survival.py'] == POLICY_SHA,
            'actual_immutable_policy_source_closure')
    require(loaded['physical'] == physical and loaded['actor']['cwd'] == request['source_root'], 'actual_loaded_source_binding')
    admission = helpers.read(lane / 'control/ADMISSION.json')
    require(admission['clear'] is True and not admission['blocking_reasons'] and admission['scanner_euid'] == 0
            and admission['gpu']['uuid'] == request['old_plan']['gpu_uuid'], 'original_actual_clear_admission')
    paths = [path for path in helpers.records(root) if int(path.stem) >= loaded['record_index']]
    require(len(paths) <= 2000, 'bounded_postload_record_scan')
    records = []
    previous = None
    for path in paths:
        record = helpers.read(path)
        require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'actual_record_hash')
        if previous is None:
            require(record['kind'] == 'LOADED' and record['sha256'] == loaded['record_sha256']
                    and record['document']['pid'] == loaded['actor']['pid'] and record['document']['resume'] is True,
                    'actual_same_successor_load_record')
        else:
            require(record['previous_sha256'] == previous['sha256'] and record['index'] == previous['index'] + 1
                    and record['journal_id'] == previous['journal_id'], 'contiguous_actual_same_life_journal_chain')
        records.append(record)
        previous = record
    found = candidate(records)
    if found is None:
        retained = [record for record in records if record['kind'] == 'CONTEXT_RETAINED']
        alive = identity_live(loaded['actor'], helpers)
        return dict(status=('WAITING_FOR_COMPLETED_RETAINED_SLEEP_AND_POSTSLEEP_GENERATION' if alive
            else 'LOADED_OWNER_REQUIRES_REVALIDATION_OR_RECOVERY'), physical=physical,
            loaded_record_index=loaded['record_index'], successor_pid=loaded['actor']['pid'], successor_identity_live=alive,
            recovery_or_owner_revalidation_needed=not alive,
            actual_retained_record_indices=[record['index'] for record in retained])
    require(found[0]['document']['cycle'] > loaded['saved']['cycle'], 'prospective_sleep_after_exact_resume_only')
    receipt = verify_cycle(*(record['document'] for record in found),
        lambda state, count: canonical_messages(Path(request['source_root']), state, count))
    checkpoint_path = root / 'checkpoints' / f"sleep_{receipt['cycle']:06d}" / 'COMMIT.json'
    checkpoint = helpers.read(checkpoint_path)
    completed = found[2]['document']
    require(checkpoint == completed['checkpoint'] and checkpoint['checkpoint_sha256'] == completed['checkpoint_sha256']
            and checkpoint['optimizer_steps'] > loaded['saved']['optimizer_steps'], 'actual_further_optimizer_progress')
    require(Path(checkpoint['optimizer_rng_path']).parent == checkpoint_path.parent
            and Path(checkpoint['adapter_path']) == checkpoint_path.parent / 'adapter', 'same_life_checkpoint_files')
    require(helpers.sha(checkpoint['optimizer_rng_path']) == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'actual_optimizer_RNG_file_hash')
    adapter_files = {path.name: helpers.sha(path) for path in Path(checkpoint['adapter_path']).iterdir() if path.is_file()}
    require(adapter_files == checkpoint['adapter_files'] and digest(adapter_files) == checkpoint['checkpoint_sha256']['adapter'],
            'actual_adapter_file_hashes')
    receipt.update(physical=physical, loaded_receipt_sha256=helpers.sha(loaded_path), source_proof_sha256=request['source_proof_sha256'],
        checkpoint_path=str(checkpoint_path), checkpoint_sha256=helpers.sha(checkpoint_path),
        successor_identity_live=identity_live(loaded['actor'], helpers),
        records=[dict(index=record['index'], kind=record['kind'], sha256=record['sha256']) for record in found])
    return receipt


def watch(lane, seconds):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_proof_collector')
    require(type(seconds) is int and 0 <= seconds <= 86400, 'bounded_readonly_proof_monitor')
    helpers = load_helpers(lane)
    request = helpers.read(lane / 'STAGED.json')
    deadline = min(time.monotonic() + seconds, time.monotonic() + request['old_plan']['hard_end_unix'] - time.time())
    previous = None
    while True:
        receipt = inspect(lane, helpers)
        if receipt != previous or time.monotonic() >= deadline:
            print(json.dumps(dict(receipt, observed_unix=time.time(), signals_sent=0, journal_writes=0,
                model_calls=0, sealed_output_reads=0), sort_keys=True), flush=True)
            previous = receipt
        if receipt['status'] == 'ACTUAL_COMPLETED_RETAINED_SLEEP_AND_POSTSLEEP_GENERATION' or time.monotonic() >= deadline:
            return
        time.sleep(min(10, max(0, deadline - time.monotonic())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lane', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=0)
    args = parser.parse_args()
    watch(args.lane.resolve(), args.seconds)
