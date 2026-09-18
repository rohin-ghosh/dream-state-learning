"""Additive, fail-closed teach-perception sleep16 repair; no launch entry point."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path


ROOT = Path('/localhome/local-rohing/orch_r136_a100_teach_perception_20260916_attempt1')
SOURCE = Path('/localhome/local-rohing/orch_r136_node1_isolation_20260916_attempt2/source')
PLAN_SHA = 'ff60807013aa006823e06a8d29e913ec15734c8179708fcd56bc7dd825c554c6'
NATIVE_SHA = '6b46401e5f8ff92d95e018b481d2303a55a3ce7c8e617aec65faa64bbc8381c7'
COMMIT_SHA = 'd1cb96869780fb288937e38c1d43117e6773fa9e9dd9223e789e61f9052c4576'
HEAD = 'f5df91f24dc33b15e388285886531d5de1818bf3f7f990e9fd56db7312931e8c'
SLEEP_REQUEST = 'dd8530faf499c6cc4138958af33b55ec9ca4fa0cb28f2436a6b0e6da8b3aa1f6'
STATE_SHA = 'ab8f869db2cc5745969ec9109385261fd030bb9e1de001f0fe7954220d6aaf2d'
STEPS = 1010


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def decode(tokenizer, tokens):
    return tokenizer.decode(list(tokens), skip_special_tokens=False, clean_up_tokenization_spaces=False)


def literal_target(row, tokenizer):
    require(row['split'] == 'TRAIN' and row['actor'] == 'child'
            and row['prefix_loss'] is False and row['target_loss'] is True, 'child_targets_only')
    require(type(row['terminal']) is bool and type(row['truncated']) is bool, 'exact_terminal_flags')
    generated = tuple(row['token_ids'])
    require(generated and all(type(token) is int and token >= 0 for token in generated), 'actual_native_target_ids')
    require(not row['terminal'] or generated[-1] == tokenizer.eos_token_id, 'actual_terminal_eos')
    visible = generated[:-1] if row['terminal'] else generated
    require(decode(tokenizer, visible) == row['target'], 'original_generated_target_roundtrip')
    special = set(tokenizer.all_special_ids)
    result, mappings = [], []
    for offset, token in enumerate(visible):
        if token not in special:
            result.append(token)
            continue
        spelling = decode(tokenizer, [token])
        replacement = tuple(tokenizer.encode(spelling, add_special_tokens=False,
            truncation=False, split_special_tokens=True))
        require(replacement and all(type(item) is int and item >= 0 for item in replacement)
                and not special.intersection(replacement), 'literal_spelling_has_no_special_ids')
        require(decode(tokenizer, replacement) == spelling, 'literal_spelling_roundtrip')
        mappings.append(dict(generated_offset=offset, generated_token_id=token,
                             replacement_token_ids=list(replacement)))
        result.extend(replacement)
    require(not special.intersection(result), 'no_visible_special_training_ids')
    require(decode(tokenizer, result) == row['target'], 'whole_literal_target_roundtrip')
    if row['terminal']:
        result.append(tokenizer.eos_token_id)
    return tuple(result), mappings


def encode_own(row, tokenizer, context_limit):
    from gpu.astra_pchain2_native import EncodedRow
    before = digest(row)
    target, unused = literal_target(row, tokenizer)
    prefix = tuple(tokenizer.apply_chat_template(row['prefix'], tokenize=True,
        add_generation_prompt=True, return_dict=False))
    require(len(prefix) + len(target) <= context_limit, 'whole_source_no_training_trim')
    require(digest(row) == before, 'raw_history_generated_ids_unchanged')
    return EncodedRow(prefix + target, (-100,) * len(prefix) + target, target)


def validate_replay_rows(suffix, state, checkpoint, plan):
    require(not any(record['kind'] in ('UPDATE', 'SLEEP_COMPLETE', 'LOADED', 'TERMINAL')
                    for record in suffix), 'no_postcheckpoint_learning_or_restart')
    requests = [record['document'] for record in suffix if record['kind'] == 'REQUEST']
    responses = [record['document'] for record in suffix if record['kind'] == 'RESPONSE']
    commits = [record['document'] for record in suffix if record['kind'] == 'COMMITTED']
    rows = state['rows'][state['sleep_frontier']:]
    require(len(requests) == len(responses) == len(commits) == len(rows) == 3, 'exact_three_committed_generations')
    require(state['pending'] == 'sleep:' + digest([row['source_sha256'] for row in rows]), 'exact_pending_rows')
    require(state['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'checkpoint_stream_binding')
    require(checkpoint.get('experiment') == state.get('experiment'), 'saved_experiment_binding')
    require(state['presentation'] == dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
        birth_prompt=plan['birth_prompt']) and state['context_limit'] == plan['context_limit'], 'unchanged_presentation')
    require(state['deadline_unix'] == plan['hard_end_unix'] and state['segment_tokens'] == plan['segment_tokens'],
            'unchanged_deadline_segment_budget')
    for row, request_document, response, commit in zip(rows, requests, responses, commits):
        request = {key: value for key, value in request_document.items() if key != 'resume_state'}
        output = response['response']
        require(row['split'] == request['split'] == 'TRAIN' and row['actor'] == 'child'
                and row['prefix_loss'] is False and row['target_loss'] is True, 'TRAIN_child_only')
        require(request['segment'] == row['segment'] == commit['segment']
                and digest(request) == response['request_sha256']
                and digest(response) == row['source_sha256'] == commit['source_sha256']
                and response['raw_saved_before_validation'] is True, 'exact_durable_response_binding')
        require(request['messages'] == row['prefix'] and request['retry_allowed'] is False
                and request['model_state_sha256'] == row['model_state_sha256'] == state['model_state_sha256']
                and request['max_new_tokens'] == plan['segment_tokens']
                and request['deadline_unix'] == plan['hard_end_unix'], 'exact_original_generation_request')
        require(output['raw'] == row['target'] and output['token_ids'] == row['token_ids']
                and output['terminal'] is row['terminal'] and output['truncated'] is row['truncated']
                and output['decoder'] == plan['decoder']
                and output['adapter_state_sha256'] == checkpoint['adapter_state_sha256']
                and output['base_sha256'] == checkpoint['base_sha256']
                and output['prompt_tokens'] == request['prompt_tokens'], 'exact_original_generation_response')
    return deepcopy(requests), deepcopy(responses)


def bind_live(records, checkpoint, plan):
    require(len(records) == 1250 and records[-1]['sha256'] == HEAD
            and records[-1]['kind'] == 'TARGET_ELIGIBILITY', 'exact_original_1250_tail')
    require(records[1248]['sha256'] == SLEEP_REQUEST and records[1248]['document']['cycle'] == 16,
            'exact_sleep16_request')
    state_document = records[1248]['document']['resume_state']
    require(state_document['sha256'] == digest(state_document['state']) == STATE_SHA, 'exact_pending_stream_state')
    state = state_document['state']
    require(records[1234]['kind'] == 'SLEEP_COMPLETE' and records[1234]['document']['cycle'] == 15
            and state['sleep_receipts'][-1]['checkpoint'] == checkpoint
            and checkpoint['optimizer_steps'] == STEPS, 'exact_sleep15_checkpoint')
    require(str(plan['root']) == str(ROOT / 'run1') and plan['source_root'] == str(SOURCE), 'same_life_original_source')
    return validate_replay_rows(records[1235:], state, checkpoint, plan)


def cpu_report():
    import os
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_no_GPU_visibility')
    from gpu.astra_pchain2_native import load_local_tokenizer
    from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
    guard = json.loads((ROOT / 'control2/GUARD.json').read_text())
    require(sha(guard['plan_path']) == PLAN_SHA, 'original_plan_file')
    require(sha(SOURCE / 'gpu/orch_r125_continual_native.py') == NATIVE_SHA, 'original_native_file')
    plan = json.loads(Path(guard['plan_path']).read_text())
    path = ROOT / 'run1/checkpoints/sleep_000015/COMMIT.json'
    require(sha(path) == COMMIT_SHA, 'original_commit_file')
    checkpoint = json.loads(path.read_text())
    require(sha(checkpoint['optimizer_rng_path']) == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'saved_optimizer_rng_bytes')
    files = {path.name: sha(path) for path in Path(checkpoint['adapter_path']).iterdir() if path.is_file()}
    require(files == checkpoint['adapter_files'] and digest(files) == checkpoint['checkpoint_sha256']['adapter'],
            'saved_adapter_bytes')
    records = []
    with _open_stream_directory(plan['root'], 'records') as (directory, unused):
        while True:
            record = _read_record(directory, len(records))
            if record is None:
                break
            if records:
                require(record['previous_sha256'] == records[-1]['sha256']
                    and record['journal_id'] == records[-1]['journal_id'], 'journal_chain')
            records.append(record)
    requests, responses = bind_live(records, checkpoint, plan)
    tokenizer = load_local_tokenizer(plan['model_dir'])
    state = records[1248]['document']['resume_state']['state']
    eligibility = records[-1]['document']
    rows = {row['source_sha256']: row for row in state['rows']}
    encoded_rows = []
    for source_sha in eligibility['new_row_sha256'] + eligibility['rehearsal_row_sha256']:
        row = rows[source_sha]
        encoded = encode_own(row, tokenizer, plan['context_limit'])
        target, mappings = literal_target(row, tokenizer)
        encoded_rows.append(dict(source_sha256=source_sha, input_tokens=len(encoded.input_ids),
            generated_tokens=len(row['token_ids']), training_tokens=len(target), mappings=mappings,
            training_target_sha256=digest(target), row_unchanged=digest(row) == digest(rows[source_sha])))
    return dict(schema='R141_PERCEPTION_ADDITIVE_CPU_REPAIR_V1', status='CPU_ENCODING_AND_DURABLE_REPLAY_BINDING_VERIFIED',
        original_head_sha256=HEAD, checkpoint_file_sha256=COMMIT_SHA, optimizer_steps=STEPS,
        replay_request_sha256=[digest(request) for request in requests],
        replay_response_sha256=[digest(response) for response in responses],
        rows=encoded_rows, matched_GPU_replays=0, GPU_launch_ready=False,
        raw_history_generated_ids_unchanged=True, prefix_and_recipe_unchanged=True,
        held_contents_read=False, limitations=['No postgeneration RNG snapshot exists; exact GPU replay still required.',
            'No launch entry point or pending-state gate bypass is installed.'])


if __name__ == '__main__':
    print(json.dumps(cpu_report(), sort_keys=True, indent=2))
