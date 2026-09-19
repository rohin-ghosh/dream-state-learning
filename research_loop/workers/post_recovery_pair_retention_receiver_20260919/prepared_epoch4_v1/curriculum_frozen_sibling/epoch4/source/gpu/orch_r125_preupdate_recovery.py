"""One-shot, node-local RNG replay for the run1 second-sleep encoding failure.

Non-material repair: no TRAIN writes, optimizer work, sleep, or pending-state
changes. Main must restore NativeChild from the supplied sleep1 COMMIT first
and call recover_rng before appending even metadata to the journal. A failed
attempt consumes its deterministic recovery directory; never reuse that child.

recovery_plan has exactly: schema (SCHEMA), recovery_root, sleep_request_sha256,
original_log, original_exit, native_source, checkpoint. Each original_* and
native_source reference is {path: absolute original path, sha256: file hash}.
checkpoint is the complete sleep1 COMMIT document, not a path. recovery_root
must be <child.plan.root>/recoveries/preupdate-<sleep_request_sha256>.

Verification is exact deterministic generation replay from the caller-restored
checkpoint, not a comparison to an unavailable original post-generation RNG
snapshot. Actual Python, CPU and CUDA RNG fingerprints are retained throughout.
"""

import ast
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import re
import textwrap
import time

from organism_v6.orch_r125_continual_stream import digest, require, valid_sha256


SCHEMA = 'R125_PREUPDATE_RECOVERY_V1'
_FIELDS = {'schema', 'recovery_root', 'sleep_request_sha256', 'original_log',
           'original_exit', 'native_source', 'checkpoint'}
_PRE_ENCODING = '''
from gpu.orch_r108_guided_native import validate_anchor_inventory
validate_anchor_inventory(anchors)
require(len(anchors) == 4, 'four_broad_anchor_families')
before = self.adapter_hash()
steps_before = self.optimizer_steps
schedule = presentation_schedule(new_rows, old_rows)
encoded = {row['source_sha256']:encode_own(row, self.tokenizer, self.plan['context_limit'])
           for row in new_rows+old_rows}
'''


def _ast(node):
    return ast.dump(node, include_attributes=False)


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _save_bytes(path, raw):
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    _sync_directory(path.parent)


def _save(path, document):
    _save_bytes(path, (json.dumps(document, sort_keys=True, indent=2,
                                allow_nan=False) + '\n').encode())


def _pinned(reference, destination):
    require(set(reference) == {'path', 'sha256'} and valid_sha256(reference['sha256']),
            'explicit_pinned_file')
    path = Path(reference['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'original_regular_file')
    raw = path.read_bytes()
    _save_bytes(destination, raw)
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'pinned_file_hash:' + path.name)
    return raw


def _verify_source(child, source, log, source_path):
    tree = ast.parse(source)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'NativeChild']
    require(len(classes) == 1, 'original_native_class')
    methods = {node.name: node for node in classes[0].body if isinstance(node, ast.FunctionDef)}
    original_generate = methods['generate']
    live_generate = ast.parse(textwrap.dedent(inspect.getsource(child.generate))).body[0]
    require(_ast(original_generate) == _ast(live_generate), 'unchanged_generate_AST')
    sleep = methods['sleep']
    prefix = ast.parse(textwrap.dedent(_PRE_ENCODING)).body
    require([_ast(node) for node in sleep.body[:len(prefix)]] == [_ast(node) for node in prefix],
            'encoding_before_sleep_optimizer_initialization')
    encoded = sleep.body[len(prefix)-1]
    encoders = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'encode_own']
    require(len(encoders) == 1, 'original_encode_own')
    guards = [node for node in ast.walk(encoders[0]) if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Name) and node.func.id == 'require'
              and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
              and node.args[1].value == 'no_special_token_target_injection']
    require(len(guards) == 1, 'original_special_token_guard')
    require(_ast(guards[0].args[0]) == _ast(ast.parse(
        'not set(tokenizer.all_special_ids).intersection(visible)', mode='eval').body),
        'original_unrepaired_special_token_guard')
    require(log.count('Traceback (most recent call last):') == 1
            and log.rstrip().endswith('ValueError: no_special_token_target_injection'),
            'specific_encode_own_traceback')
    frames = re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', log)
    own_frames = [(int(line), name.strip()) for path, line, name in frames if path == source_path]
    sleep_frames = [line for line, name in own_frames if name == 'sleep']
    encode_frames = [line for line, name in own_frames if name == 'encode_own']
    require(len(sleep_frames) == len(encode_frames) == 1
            and encoded.lineno <= sleep_frames[0] <= encoded.end_lineno
            and guards[0].lineno <= encode_frames[0] <= guards[0].end_lineno
            and [name for unused, name in own_frames].index('sleep')
                < [name for unused, name in own_frames].index('encode_own'),
            'traceback_bound_to_preupdate_encoding')
    return digest(_ast(original_generate))


def _rng(child):
    return dict(python=digest(random.getstate()), cpu=digest(child.torch.get_rng_state().tolist()),
                cuda=[digest(state.tolist()) for state in child.torch.cuda.get_rng_state_all()])


def _journal_records(journal):
    state = journal._scan()
    records = [journal._read_json(journal._records_fd, f'{index:020d}.json')
               for index in range(state['index'])]
    require(records and records[-1]['sha256'] == state['previous'], 'stable_journal_tail')
    return state, records


def _bind(child, stream, journal, plan):
    state, records = _journal_records(journal)
    require(state['request'] is None and state['response'] is None, 'no_pending_generation')
    require(records[-1]['kind'] == 'SLEEP_REQUEST'
            and records[-1]['sha256'] == plan['sleep_request_sha256'], 'latest_exact_SLEEP_REQUEST')
    require(state['sleep_request'] == {'cycle': 2}, 'specific_second_sleep_request')
    require(state['latest']['document'] == stream.checkpoint(), 'restored_stream_matches_journal')
    rows = deepcopy(stream.pending_rows())
    require(len(rows) == 3 and len(stream.sleep_receipts) == 1, 'exact_three_rows_after_sleep1')
    require(stream.pending == 'sleep:' + digest([row['source_sha256'] for row in rows]),
            'pending_rows_digest')
    checkpoint = plan['checkpoint']
    require(stream.sleep_receipts[0]['checkpoint'] == checkpoint
            and stream.sleep_receipts[0]['cycle'] == 1
            and stream.sleep_receipts[0]['checkpoint_sha256'] == checkpoint['checkpoint_sha256']
            and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']),
            'matching_last_committed_checkpoint')
    require(type(checkpoint['optimizer_steps']) is int and checkpoint['optimizer_steps'] == 48
            and child.optimizer_steps == 48
            and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'restored_adapter_optimizer')
    require(valid_sha256(checkpoint['adapter_state_sha256'])
            and set(checkpoint['checkpoint_sha256']) == {'adapter', 'optimizer', 'rng'}
            and all(valid_sha256(value) for value in checkpoint['checkpoint_sha256'].values()),
            'checkpoint_receipt_hashes')
    require(child.plan['segment_tokens'] == stream.segment_tokens
            and child.plan['hard_end_unix'] == stream.deadline_unix
            and child.plan['context_limit'] == stream.context_limit, 'replay_budget_deadline')
    require(child.plan['decoder'] == dict(temperature=0.7, top_p=0.95,
            repetition_penalty=1.05, no_repeat_ngram_size=16), 'exact_native_decoder')
    require(151643 in rows[1]['token_ids'][:-1] and '<|endoftext|>' in rows[1]['target']
            and len(rows[1]['token_ids']) == 512, 'specific_internal_endoftext_failure')
    completed = [index for index, record in enumerate(records) if record['kind'] == 'SLEEP_COMPLETE']
    require(len(completed) == 1, 'one_committed_sleep')
    suffix = records[completed[0]+1:]
    require(not any(record['kind'] in ('UPDATE', 'SLEEP_COMPLETE') for record in suffix),
            'no_postcheckpoint_UPDATE')
    require([record['kind'] for record in suffix].count('SLEEP_REQUEST') == 1,
            'one_unresolved_sleep_attempt')
    requests = [record['document'] for record in suffix if record['kind'] == 'REQUEST']
    responses = [record['document'] for record in suffix if record['kind'] == 'RESPONSE']
    commits = [record['document'] for record in suffix if record['kind'] == 'COMMITTED']
    require(len(requests) == len(responses) == len(commits) == 3, 'three_completed_generations_only')
    for row, request_document, response, commit in zip(rows, requests, responses, commits):
        request = {key: value for key, value in request_document.items() if key != 'resume_state'}
        output = response['response']
        require(request['segment'] == row['segment'] == commit['segment']
                and digest(request) == response['request_sha256']
                and digest(response) == row['source_sha256'] == commit['source_sha256']
                and response['raw_saved_before_validation'] is True, 'committed_raw_token_receipt')
        require(request['messages'] == row['prefix'] and request['split'] == 'TRAIN'
                and request['model_state_sha256'] == row['model_state_sha256'] == stream.model_state_sha256
                and request['max_new_tokens'] == child.plan['segment_tokens']
                and request['deadline_unix'] == child.plan['hard_end_unix']
                and request['retry_allowed'] is False, 'exact_prefix_and_generation_request')
        require(output['raw'] == row['target'] and output['token_ids'] == row['token_ids']
                and type(output['terminal']) is bool and output['terminal'] is row['terminal']
                and type(output['truncated']) is bool and output['truncated'] is row['truncated']
                and output['decoder'] == child.plan['decoder']
                and output['adapter_state_sha256'] == checkpoint['adapter_state_sha256']
                and output['base_sha256'] == checkpoint['base_sha256']
                and output['prompt_tokens'] == request['prompt_tokens']
                and valid_sha256(output['prompt_token_ids_sha256']), 'exact_original_generation_receipt')
    return rows, requests, responses, suffix


def recover_rng(child, stream, journal, recovery_plan):
    """Return COMPLETE only after all three exact replays; otherwise raise.

    Uses the already-held StreamJournal writer lock and its read-only validator.
    Main owns checkpoint restoration and the subsequent original pending sleep.
    This function never clears pending, records TRAIN events, or invokes sleep.
    """
    plan = deepcopy(recovery_plan)
    require(set(plan) == _FIELDS and plan['schema'] == SCHEMA, 'explicit_recovery_plan')
    require(valid_sha256(plan['sleep_request_sha256']), 'pinned_sleep_request_hash')
    root = Path(child.plan['root'])
    destination = Path(plan['recovery_root'])
    require(root.is_absolute() and destination.is_absolute(), 'absolute_local_recovery_root')
    require(journal.root.resolve() == (root / 'stream').resolve(), 'journal_run_root_binding')
    parent = root / 'recoveries'
    require(not parent.is_symlink() and destination.parent.resolve() == parent.resolve()
            and destination.name == 'preupdate-' + plan['sleep_request_sha256'],
            'deterministic_local_recovery_root')
    parent.mkdir(mode=0o700, exist_ok=True)
    destination.mkdir(mode=0o700, exist_ok=False)
    _sync_directory(parent)
    try:
        _save(destination / 'PLAN.json', plan)
        log = _pinned(plan['original_log'], destination / 'ORIGINAL_NATIVE.log').decode('utf-8')
        exited = json.loads(_pinned(plan['original_exit'], destination / 'ORIGINAL_EXIT.json'))
        require(Path(plan['original_log']['path']).name == 'NATIVE.log'
                and Path(plan['original_exit']['path']).name == 'EXIT.json'
                and Path(plan['original_log']['path']).parent == Path(plan['original_exit']['path']).parent,
                'same_original_failed_attempt')
        require(type(exited.get('exit_code')) is int and exited['exit_code'] == 1
                and exited.get('no_retry') is True, 'original_exit1_no_retry')
        source = _pinned(plan['native_source'], destination / 'ORIGINAL_NATIVE.py').decode('utf-8')
        recipe = _verify_source(child, source, log, plan['native_source']['path'])
        with journal._mutex:
            rows, requests, responses, suffix = _bind(child, stream, journal, plan)
            _save(destination / 'JOURNAL_EVIDENCE.json', suffix)
            original_stream = stream.checkpoint()
            original_plan = deepcopy(child.plan)
            before = _rng(child)
            _save(destination / 'STARTED.json', dict(status='STARTED', rng=before,
                generate_ast_sha256=recipe, no_retry=True, started_unix=time.time()))
            for index, (row, request, original) in enumerate(zip(rows, requests, responses)):
                require(time.time() < child.plan['hard_end_unix'], 'replay_deadline')
                messages = deepcopy(row['prefix'])
                _save(destination / f'{index:02d}_REQUEST.json', dict(row=row, original_request=request,
                    original_response=original, rng_before=_rng(child)))
                response = child.generate(messages, max_new_tokens=child.plan['segment_tokens'],
                                          deadline_unix=child.plan['hard_end_unix'])
                after = _rng(child)
                _save(destination / f'{index:02d}_RESPONSE.json', dict(response=response, rng_after=after))
                require(messages == row['prefix'], 'replay_cannot_mutate_prefix')
                require(digest(response) == digest(original['response']), 'bit_identical_generation:' + str(index))
                require(child.plan == original_plan and stream.checkpoint() == original_stream,
                        'replay_cannot_mutate_plan_or_stream')
                require(child.optimizer_steps == plan['checkpoint']['optimizer_steps']
                        and child.adapter_hash() == plan['checkpoint']['adapter_state_sha256'],
                        'replay_cannot_update_learning')
                require(time.time() < child.plan['hard_end_unix'], 'replay_finished_before_deadline')
                _save(destination / f'{index:02d}_MATCH.json', dict(status='MATCH',
                    source_sha256=row['source_sha256'], response_sha256=digest(response)))
            _bind(child, stream, journal, plan)
            require(recipe == _verify_source(child, source, log, plan['native_source']['path']),
                    'unchanged_replay_recipe')
            for key in ('original_log', 'original_exit', 'native_source'):
                require(hashlib.sha256(Path(plan[key]['path']).read_bytes()).hexdigest() == plan[key]['sha256'],
                        'original_evidence_unchanged:' + key)
            receipt = dict(schema=SCHEMA, status='COMPLETE', recovery_root=str(destination),
                sleep_request_sha256=plan['sleep_request_sha256'], recovery_plan_sha256=digest(plan),
                checkpoint_sha256=plan['checkpoint']['checkpoint_sha256'], matched_generations=3,
                new_row_sha256=[row['source_sha256'] for row in rows], optimizer_updates=0,
                rng_reconstruction_verified=True, verification='exact_committed_generation_replay',
                original_final_rng_snapshot_available=False, rng_before=before, rng_after=_rng(child),
                generate_ast_sha256=recipe, pending_unchanged=True, no_retry=True, finished_unix=time.time())
            _save(destination / 'COMPLETE.json', receipt)
            return receipt
    except BaseException as error:
        try:
            _save(destination / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
                error=str(error), no_retry=True, child_must_be_discarded=True, finished_unix=time.time()))
        except BaseException as evidence_error:
            error.add_note('Failed to persist recovery failure receipt: ' + str(evidence_error))
        raise
