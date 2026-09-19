"""Exact R132 kernel sleep3 RNG recovery; no journal writes or optimizer steps.

Drop-in call signature: recover_rng(child, stream, journal, recovery_plan).
Main first constructs NativeChild(resume_plan, sleep2_COMMIT), restoring the
adapter. This function verifies that adapter and reloads the hash-bound sleep2
AdamW/Python/CPU/CUDA state before three exact original generation calls.
It never invokes stream.step, sleep, encode_own, eligibility, or readouts.

recovery_plan fields: schema=R138_KERNEL_RECOVERY_V1, recovery_root,
sleep_request_sha256, checkpoint (complete sleep2 COMMIT), original_plan,
original_log, original_exit, native_source. File references are {path, sha256};
native_source is the ORIGINAL source1/gpu/orch_r125_continual_native.py, not the
repaired closure. The original PLAN/log/exit and checkpoint hashes are fixed
below. recovery_root is <child.plan.root>/recoveries/preupdate-<sleep hash>.
The resume plan may differ only in source_root, preupdate_recovery, and relocation
of startup_context.path to the exact same relative path in the new source root.
Startup version/hash and original/relocated birth bytes must match exactly.
Decoder, deadline, presentation, experiment, and other PLAN fields stay unchanged.

Call before adding ANY journal metadata. Tail must end at TARGET_ELIGIBILITY
140 after SLEEP_REQUEST139; sleep2 SLEEP_COMPLETE127 is the last saved learning
state, at 99 optimizer steps. The original source must prove that the logged
encode_own failure precedes all optimizer work. Generation AST cannot change.
Failure consumes the create-only recovery directory; discard the child, never
retry it. The sole explicit exception is a fresh child and recovery_root ending
in -attempt2, with prior_failed_attempt={recovery_root, plan, failed,
journal_evidence, native_log}. References use {path, sha256}; the first three
files are PLAN.json, FAILED.json, JOURNAL_EVIDENCE.json in the original recovery
root, and native_log is control_recovery1/NATIVE.log. Both failure hashes are
fixed below. The exact seven-file pre-replay inventory and unchanged journal
must validate before restoration and again before COMPLETE. No attempt3 or
automatic retry is permitted. Missing child.experiment is compatible only when
both saved checkpoint and payload omit experiment entirely.
Receipts preserve all original/replayed evidence. COMPLETE establishes
exact deterministic reconstruction, not comparison to an unavailable original
post-generation RNG capture. Original history/pending/OWN_CARRY are untouched.
"""

import ast
from copy import deepcopy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import random
import re
import textwrap
import time

from gpu import orch_r125_preupdate_recovery as previous
from gpu.orch_r127_pilot_console import _directory, _read
from organism_v6.orch_r125_continual_stream import digest, require, valid_sha256


SCHEMA = 'R138_KERNEL_RECOVERY_V1'
SOURCE_ROOT = '/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/source1'
SLEEP_REQUEST_SHA256 = '3ef3b37bb0ad580e30f60710a0e18b7029a7a3cbebdea6593e2a1f6f62f24974'
ADAPTER_STATE_SHA256 = 'ab87d0d57f082cc1b72f411add77fee0ae7ffadfe4acae2c78aaac883052bf3f'
CHECKPOINT_SHA256 = dict(adapter='e9decaaa726542967f2c266d6fc526741b6dcfd475da2bf2d086485e2169f20a',
    optimizer='0aa13501c6a73c2f46ff8eb37bd1924c613b27f66d01704c2a4cd5a6fe767f5c',
    rng='0aa13501c6a73c2f46ff8eb37bd1924c613b27f66d01704c2a4cd5a6fe767f5c')
ORIGINAL_PLAN_SHA256 = '48bad068326fb65ffec5f6ea3c49ddebb31ba5fcd9f036c28f0df2fe71c52550'
ORIGINAL_LOG_SHA256 = 'de3abb02437e7a03ffcf119361eea470bb96a5f846ddd3839c8e4803ec499139'
ORIGINAL_EXIT_SHA256 = 'dae901d166e5ef417d1d191504a84367f66a2d91f2f2697d72b244f819cc9e94'
PRIOR_FAILED_SHA256 = 'e9644e8ed2df0626b1de38e14a004f82c039b980af66aa01b767c34763f08481'
PRIOR_LOG_SHA256 = '434078886211e0912ee035be148532d068eaa9e1301cc26de33b7329d8e50429'
PRIOR_FAILURE_TIME = 1789556188.5977588
PRIOR_ERROR = "'NativeChild' object has no attribute 'experiment'"
BASE_SHA256 = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
DECODER = dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16)
TAIL = ('INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED', 'REQUEST', 'RESPONSE', 'COMMITTED',
    'REQUEST', 'RESPONSE', 'COMMITTED', 'COMPACTION', 'SLEEP_REQUEST', 'TARGET_ELIGIBILITY')
_FIELDS = previous._FIELDS | {'original_plan'}
_PRE_ENCODING = '''
from gpu.orch_r108_guided_native import validate_anchor_inventory
validate_anchor_inventory(anchors)
require(len(anchors) == 4, 'four_broad_anchor_families')
before = self.adapter_hash()
steps_before = self.optimizer_steps
exclusions = []
if self.plan.get('presentation_version'):
    from organism_v6.orch_r125_plain_context import eligible_rows
    presentation = dict(version=self.plan['presentation_version'],
        system_prompt=self.plan['system_prompt'], birth_prompt=self.plan['birth_prompt'])
    new_rows, rejected_new = eligible_rows(new_rows, presentation)
    old_rows, rejected_old = eligible_rows(old_rows, presentation)
    exclusions = [dict(row, cohort='NEW') for row in rejected_new] + [
        dict(row, cohort='REHEARSAL') for row in rejected_old]
    record('TARGET_ELIGIBILITY', dict(version=presentation['version'], excluded=exclusions,
        new_row_sha256=[row['source_sha256'] for row in new_rows],
        rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False))
schedule = (presentation_schedule(new_rows, old_rows) if new_rows else
            [('REHEARSAL', row) for row in old_rows])
if not schedule:
    self.engine.verify_base()
    return dict(optimizer_steps=0, total_optimizer_steps=self.optimizer_steps,
        before_adapter_sha256=before, after_adapter_sha256=before,
        no_update_reason='no_eligible_child_rows', child_token_exposures=0,
        anchor_token_exposures=0, presentations={}, excluded_rows=exclusions,
        anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION')
encoded = {row['source_sha256']:encode_own(row, self.tokenizer, self.plan['context_limit'])
           for row in new_rows+old_rows}
'''


def _raw(path, limit):
    path = Path(path)
    require(path.is_absolute(), 'absolute_evidence_path')
    with _directory(path.parent) as directory:
        return _read(directory, path.name, limit)


def _pinned(reference, destination, limit=32 * 1024 * 1024):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}
        and valid_sha256(reference['sha256']), 'explicit_pinned_file')
    raw = _raw(reference['path'], limit)
    previous._save_bytes(destination, raw)
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'pinned_file_hash:' + destination.name)
    return raw


def _verify_source(child, source, log, source_path):
    tree = ast.parse(source)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'NativeChild']
    require(len(classes) == 1, 'original_native_class')
    methods = {node.name: node for node in classes[0].body if isinstance(node, ast.FunctionDef)}
    generate = ast.parse(textwrap.dedent(inspect.getsource(child.generate))).body[0]
    require(previous._ast(methods['generate']) == previous._ast(generate), 'unchanged_generate_AST')
    prefix = ast.parse(textwrap.dedent(_PRE_ENCODING)).body
    require([previous._ast(node) for node in methods['sleep'].body[:len(prefix)]]
        == [previous._ast(node) for node in prefix], 'encoding_before_optimizer_work')
    encoded = methods['sleep'].body[len(prefix)-1]
    encoders = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'encode_own']
    require(len(encoders) == 1, 'original_encode_own')
    guards = [node for node in ast.walk(encoders[0]) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == 'require' and len(node.args) == 2
        and isinstance(node.args[1], ast.Constant) and node.args[1].value == 'no_special_token_target_injection']
    require(len(guards) == 1 and previous._ast(guards[0].args[0]) == previous._ast(ast.parse(
        'not (set(tokenizer.all_special_ids)-permitted).intersection(visible)', mode='eval').body),
        'original_im_start_encoding_guard')
    require(log.count('Traceback (most recent call last):') == 1
        and log.rstrip().endswith('ValueError: no_special_token_target_injection'), 'specific_encode_own_traceback')
    frames = [(int(line), name.strip()) for path, line, name in
        re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', log) if path == source_path]
    sleep_lines = [line for line, name in frames if name == 'sleep']
    encode_lines = [line for line, name in frames if name == 'encode_own']
    require(len(sleep_lines) == len(encode_lines) == 1
        and encoded.lineno <= sleep_lines[0] <= encoded.end_lineno
        and guards[0].lineno <= encode_lines[0] <= guards[0].end_lineno
        and [name for unused, name in frames].index('sleep') < [name for unused, name in frames].index('encode_own'),
        'traceback_bound_to_preupdate_encoding')
    return digest(previous._ast(generate))


def _bind(child, stream, journal, plan):
    state, records = previous._journal_records(journal)
    require(len(records) == 141 and records[127]['kind'] == 'SLEEP_COMPLETE'
        and tuple(record['kind'] for record in records[128:]) == TAIL, 'exact_kernel_127_140_tail')
    require(records[139]['sha256'] == plan['sleep_request_sha256'] == SLEEP_REQUEST_SHA256,
        'exact_kernel_sleep3_hash')
    require([record['document']['cycle'] for record in records if record['kind'] == 'SLEEP_COMPLETE'] == [1, 2]
        and state['sleep_request'] == {'cycle': 3}, 'sleep2_then_pending_sleep3')
    require(state['request'] is None and state['response'] is None
        and state['latest']['document'] == stream.checkpoint(), 'restored_stream_matches_journal')
    rows = deepcopy(stream.pending_rows())
    require(len(rows) == 3 and len(stream.sleep_receipts) == 2
        and stream.pending == 'sleep:' + digest([row['source_sha256'] for row in rows]), 'exact_pending_three_rows')
    checkpoint = plan['checkpoint']
    require(stream.sleep_receipts[-1]['cycle'] == 2
        and stream.sleep_receipts[-1]['checkpoint'] == checkpoint
        and stream.sleep_receipts[-1]['checkpoint_sha256'] == checkpoint['checkpoint_sha256'] == CHECKPOINT_SHA256
        and stream.model_state_sha256 == digest(CHECKPOINT_SHA256), 'exact_sleep2_checkpoint')
    require(type(checkpoint['optimizer_steps']) is int and checkpoint['optimizer_steps'] == child.optimizer_steps == 99
        and checkpoint['adapter_state_sha256'] == child.adapter_hash() == ADAPTER_STATE_SHA256
        and checkpoint['base_sha256'] == BASE_SHA256, 'restored_sleep2_adapter_99_steps_base')
    require(child.plan['segment_tokens'] == stream.segment_tokens
        and child.plan['hard_end_unix'] == stream.deadline_unix
        and child.plan['context_limit'] == stream.context_limit and child.plan['decoder'] == DECODER,
        'unchanged_replay_budget_decoder_deadline')
    requests, responses = [], []
    for row, request_index in zip(rows, (129, 132, 135)):
        request_document = records[request_index]['document']
        request = {key: value for key, value in request_document.items() if key != 'resume_state'}
        response, commit = records[request_index+1]['document'], records[request_index+2]['document']
        output = response['response']
        require(row['split'] == request['split'] == 'TRAIN' and row['actor'] == 'child'
            and row['prefix_loss'] is False and row['target_loss'] is True
            and request['segment'] == row['segment'] == commit['segment']
            and digest(request) == response['request_sha256']
            and digest(response) == row['source_sha256'] == commit['source_sha256']
            and response['raw_saved_before_validation'] is True, 'committed_TRAIN_raw_token_receipt')
        require(request['messages'] == row['prefix']
            and request['model_state_sha256'] == row['model_state_sha256'] == stream.model_state_sha256
            and request['max_new_tokens'] == child.plan['segment_tokens']
            and request['deadline_unix'] == child.plan['hard_end_unix']
            and request['retry_allowed'] is False, 'exact_original_request')
        require(output['raw'] == row['target'] and output['token_ids'] == row['token_ids']
            and type(output['terminal']) is bool and output['terminal'] is row['terminal']
            and type(output['truncated']) is bool and output['truncated'] is row['truncated']
            and output['decoder'] == DECODER and output['adapter_state_sha256'] == ADAPTER_STATE_SHA256
            and output['base_sha256'] == BASE_SHA256 and output['prompt_tokens'] == request['prompt_tokens']
            and valid_sha256(output['prompt_token_ids_sha256']), 'exact_original_generation_receipt')
        requests.append(request_document)
        responses.append(response)
    visible = rows[1]['token_ids'][:-1] if rows[1]['terminal'] else rows[1]['token_ids']
    require(151644 in visible and '<|im_start|>' in rows[1]['target']
        and 151644 in child.tokenizer.all_special_ids
        and child.tokenizer.decode([151644], skip_special_tokens=False,
            clean_up_tokenization_spaces=False) == '<|im_start|>', 'response133_im_start_failure')
    eligibility = records[140]['document']
    require(eligibility.get('raw_modified') is False and stream.presentation is not None
        and eligibility.get('version') == stream.presentation['version']
        and rows[1]['source_sha256'] in eligibility.get('new_row_sha256', []), 'original_target_eligibility')
    return rows, requests, responses, records[127:]


def _optimizer_fingerprint(child, state=None):
    def encode(value):
        if isinstance(value, child.torch.Tensor):
            tensor = value.detach().cpu().contiguous()
            raw = tensor.reshape(-1).view(child.torch.uint8).numpy().tobytes()
            return dict(dtype=str(tensor.dtype), shape=list(tensor.shape), sha256=hashlib.sha256(raw).hexdigest())
        if isinstance(value, dict):
            return [[repr(key), encode(item)] for key, item in sorted(value.items(), key=lambda pair: repr(pair[0]))]
        if isinstance(value, (list, tuple)):
            return [encode(item) for item in value]
        require(value is None or type(value) in (int, float, bool, str), 'optimizer_state_type')
        return value
    return digest(encode(child.optimizer.state_dict() if state is None else state))


def _verify_prior_attempt(plan, root, suffix):
    prior = plan['prior_failed_attempt']
    require(type(prior) is dict and set(prior) == {
        'recovery_root', 'plan', 'failed', 'journal_evidence', 'native_log'}, 'explicit_prior_failed_attempt')
    original_root = root / 'recoveries' / ('preupdate-' + SLEEP_REQUEST_SHA256)
    require(prior['recovery_root'] == str(original_root), 'prior_original_recovery_root')
    names = dict(plan='PLAN.json', failed='FAILED.json', journal_evidence='JOURNAL_EVIDENCE.json')
    copies = dict(original_plan='ORIGINAL_PLAN.json', original_log='ORIGINAL_NATIVE.log',
        original_exit='ORIGINAL_EXIT.json', native_source='ORIGINAL_NATIVE.py')
    inventory = set(names.values()) | set(copies.values())
    captured, hashes = {}, {}
    with _directory(original_root) as directory:
        require(set(os.listdir(directory)) == inventory, 'prior_exact_pre_replay_inventory')
        for field, name in names.items():
            reference = prior[field]
            require(type(reference) is dict and set(reference) == {'path', 'sha256'}
                and reference['path'] == str(original_root / name) and valid_sha256(reference['sha256']),
                'prior_evidence_reference:' + field)
            raw = _read(directory, name, 32 * 1024 * 1024)
            hashes[name] = hashlib.sha256(raw).hexdigest()
            require(hashes[name] == reference['sha256'], 'prior_evidence_hash:' + field)
            captured[field] = json.loads(raw)
        for field, name in copies.items():
            hashes[name] = hashlib.sha256(_read(directory, name, 32 * 1024 * 1024)).hexdigest()
            require(hashes[name] == plan[field]['sha256'], 'prior_original_evidence_hash:' + field)
        require(set(os.listdir(directory)) == inventory, 'prior_inventory_stable')
    require(hashes['FAILED.json'] == PRIOR_FAILED_SHA256, 'fixed_prior_failure_hash')
    require(captured['failed'] == dict(schema=SCHEMA, status='FAILED', error_type='AttributeError',
        error=PRIOR_ERROR, no_retry=True, child_must_be_discarded=True, finished_unix=PRIOR_FAILURE_TIME),
        'exact_prior_legacy_attribute_failure')
    expected_plan = deepcopy(plan)
    del expected_plan['prior_failed_attempt']
    expected_plan['recovery_root'] = str(original_root)
    require(captured['plan'] == expected_plan, 'prior_same_recovery_plan')
    require(captured['journal_evidence'] == suffix, 'prior_journal_unchanged')
    reference = prior['native_log']
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}
        and reference['path'] == str(Path(SOURCE_ROOT).parent / 'control_recovery1' / 'NATIVE.log')
        and reference['sha256'] == PRIOR_LOG_SHA256, 'fixed_prior_log_reference')
    raw = _raw(reference['path'], 32 * 1024 * 1024)
    require(hashlib.sha256(raw).hexdigest() == PRIOR_LOG_SHA256, 'fixed_prior_log_hash')
    log = raw.decode('utf-8')
    require(log.count('Traceback (most recent call last):') == 1
        and log.rstrip().endswith('AttributeError: ' + PRIOR_ERROR)
        and re.search(r'File "[^"]+", line \d+, in _restore\n', log) is not None,
        'prior_log_pre_replay_restore_failure')
    return dict(schema=SCHEMA, prior_failed_attempt=deepcopy(prior), file_sha256=hashes,
        journal_record_count=141, journal_head_sha256=suffix[-1]['sha256'],
        journal_records_unchanged=True, no_replay_artifacts=True,
        verification='pinned_failure_log_and_exact_pre_replay_inventory')


def _restore(child, checkpoint, root):
    saved = root / 'checkpoints' / 'sleep_000002'
    require(checkpoint['adapter_path'] == str(saved / 'adapter')
        and checkpoint['optimizer_rng_path'] == str(saved / 'optimizer_rng.pt'), 'sleep2_checkpoint_paths')
    files = checkpoint['adapter_files']
    require(type(files) is dict and 0 < len(files) <= 16
        and digest(files) == CHECKPOINT_SHA256['adapter'], 'exact_saved_adapter_inventory')
    with _directory(checkpoint['adapter_path']) as directory:
        require(set(os.listdir(directory)) == set(files), 'exact_saved_adapter_files')
        for name, expected in files.items():
            require(type(name) is str and Path(name).name == name and name not in ('.', '..')
                and valid_sha256(expected), 'adapter_filename_hash')
            require(hashlib.sha256(_read(directory, name, 512 * 1024 * 1024)).hexdigest() == expected,
                'saved_adapter_file_hash')
    raw = _raw(checkpoint['optimizer_rng_path'], 512 * 1024 * 1024)
    require(hashlib.sha256(raw).hexdigest() == CHECKPOINT_SHA256['optimizer'] == CHECKPOINT_SHA256['rng'],
        'saved_optimizer_rng_hash')
    require(isinstance(child.optimizer, child.torch.optim.AdamW), 'actual_AdamW_required')
    child.verify_checkpoint(checkpoint)
    payload = child.torch.load(io.BytesIO(raw), map_location='cpu', weights_only=False)
    missing = object()
    experiment = getattr(child, 'experiment', missing)
    if experiment is missing:
        require('experiment' not in checkpoint and 'experiment' not in payload,
            'legacy_checkpoint_payload_without_experiment')
    else:
        require(payload.get('experiment') == checkpoint.get('experiment') == experiment,
            'sleep2_optimizer_order_experiment')
    require(payload['optimizer_steps'] == 99 and payload['parameter_names'] == list(child.parameters),
        'sleep2_optimizer_order_experiment')
    child.engine.verify_base()
    require(child.adapter_hash() == ADAPTER_STATE_SHA256, 'restored_adapter_required')
    expected_optimizer = _optimizer_fingerprint(child, payload['optimizer'])
    child.optimizer.load_state_dict(payload['optimizer'])
    require(_optimizer_fingerprint(child) == expected_optimizer, 'exact_saved_AdamW_restored')
    child.torch.set_rng_state(payload['cpu_rng'])
    child.torch.cuda.set_rng_state_all(payload['cuda_rng'])
    random.setstate(payload['python_rng'])
    require(previous._rng(child) == dict(python=digest(payload['python_rng']), cpu=digest(payload['cpu_rng'].tolist()),
        cuda=[digest(item.tolist()) for item in payload['cuda_rng']]), 'exact_saved_rng_restored')
    require(hashlib.sha256(_raw(checkpoint['optimizer_rng_path'], 512 * 1024 * 1024)).hexdigest()
        == CHECKPOINT_SHA256['optimizer'], 'checkpoint_unchanged_during_restore')
    return _optimizer_fingerprint(child)


def _verify_original_plan(original_plan, resume_plan):
    normalized = deepcopy(resume_plan)
    startup = original_plan.get('startup_context')
    paths = None
    if startup is not None:
        relocated = resume_plan.get('startup_context')
        fields = {'version', 'path', 'sha256'}
        require(type(startup) is dict and set(startup) == fields
            and type(relocated) is dict and set(relocated) == fields, 'exact_startup_context_fields')
        require(startup['version'] == relocated['version'] == 'R127_STARTUP_V1'
            and valid_sha256(startup['sha256']) and startup['sha256'] == relocated['sha256'],
            'startup_context_same_version_sha')
        source_root, new_root = Path(original_plan['source_root']), Path(resume_plan['source_root'])
        original_path, relocated_path = Path(startup['path']), Path(relocated['path'])
        require(all(path.is_absolute() and '..' not in path.parts
            for path in (source_root, new_root, original_path, relocated_path)), 'absolute_startup_paths')
        require(original_path.is_relative_to(source_root) and original_path != source_root,
            'startup_original_within_source_root')
        require(relocated['path'] == str(new_root / original_path.relative_to(source_root)),
            'startup_exact_relative_relocation')
        normalized['startup_context']['path'] = startup['path']
        paths = (original_path, relocated_path)
    mutable = {'source_root', 'preupdate_recovery'}
    require({key: value for key, value in original_plan.items() if key not in mutable}
        == {key: value for key, value in normalized.items() if key not in mutable}, 'original_plan_semantics_unchanged')
    if paths is not None:
        expected = original_plan['birth_prompt'].encode('utf-8')
        require(0 < len(expected) <= 16384 and hashlib.sha256(expected).hexdigest() == startup['sha256'],
            'startup_birth_bytes_hash')
        for path in paths:
            require(_raw(path, 16384) == expected, 'startup_exact_birth_bytes')


def recover_rng(child, stream, journal, recovery_plan):
    """Restore saved AdamW/RNG, replay exactly three requests, or fail closed."""
    plan = deepcopy(recovery_plan)
    require(type(plan) is dict and set(plan) in (_FIELDS, _FIELDS | {'prior_failed_attempt'})
        and plan['schema'] == SCHEMA, 'explicit_kernel_recovery_plan')
    require(plan['sleep_request_sha256'] == SLEEP_REQUEST_SHA256, 'pinned_kernel_sleep_request')
    for field, expected in (('original_plan', ORIGINAL_PLAN_SHA256), ('original_log', ORIGINAL_LOG_SHA256),
            ('original_exit', ORIGINAL_EXIT_SHA256)):
        require(plan[field]['sha256'] == expected, 'fixed_kernel_evidence:' + field)
    require(plan['native_source']['path'] == str(Path(SOURCE_ROOT) / 'gpu' / 'orch_r125_continual_native.py'),
        'original_source1_native_required')
    root, destination = Path(child.plan['root']), Path(plan['recovery_root'])
    attempt2 = 'prior_failed_attempt' in plan
    name = 'preupdate-' + SLEEP_REQUEST_SHA256 + ('-attempt2' if attempt2 else '')
    require(root.is_absolute() and journal.root == root / 'stream'
        and destination == root / 'recoveries' / name, 'deterministic_recovery_root')
    with _directory(root):
        pass
    parent = root / 'recoveries'
    require(not parent.is_symlink(), 'recovery_parent_no_symlink')
    parent.mkdir(mode=0o700, exist_ok=True)
    destination.mkdir(mode=0o700, exist_ok=False)
    previous._sync_directory(parent)
    try:
        previous._save(destination / 'PLAN.json', plan)
        original_plan = json.loads(_pinned(plan['original_plan'], destination / 'ORIGINAL_PLAN.json'))
        _verify_original_plan(original_plan, child.plan)
        require(original_plan['source_root'] == SOURCE_ROOT, 'original_source_root_binding')
        log = _pinned(plan['original_log'], destination / 'ORIGINAL_NATIVE.log').decode()
        exited = json.loads(_pinned(plan['original_exit'], destination / 'ORIGINAL_EXIT.json'))
        require(Path(plan['original_log']['path']).name == 'NATIVE.log'
            and Path(plan['original_exit']['path']).name == 'EXIT.json'
            and Path(plan['original_log']['path']).parent == Path(plan['original_exit']['path']).parent,
            'same_original_failed_attempt')
        require(type(exited.get('exit_code')) is int and exited['exit_code'] == 1 and exited.get('no_retry') is True,
            'original_exit1_no_retry')
        source = _pinned(plan['native_source'], destination / 'ORIGINAL_NATIVE.py').decode()
        recipe = _verify_source(child, source, log, plan['native_source']['path'])
        with journal._mutex:
            rows, requests, responses, suffix = _bind(child, stream, journal, plan)
            previous._save(destination / 'JOURNAL_EVIDENCE.json', suffix)
            prior_evidence = _verify_prior_attempt(plan, root, suffix) if attempt2 else None
            if attempt2:
                previous._save(destination / 'PRIOR_FAILED_ATTEMPT.json', prior_evidence)
            original_stream, original_child_plan = stream.checkpoint(), deepcopy(child.plan)
            optimizer = _restore(child, plan['checkpoint'], root)
            before = previous._rng(child)
            previous._save(destination / 'STARTED.json', dict(schema=SCHEMA, rng=before,
                optimizer_state_sha256=optimizer, optimizer_steps=99, no_retry=True, generate_ast_sha256=recipe))
            for index, (row, request, original) in enumerate(zip(rows, requests, responses)):
                require(time.time() < child.plan['hard_end_unix'], 'replay_deadline')
                messages = deepcopy(request['messages'])
                previous._save(destination / f'{index:02d}_REQUEST.json', dict(original_request=request,
                    original_response=original, rng_before=previous._rng(child)))
                response = child.generate(messages, max_new_tokens=request['max_new_tokens'],
                    deadline_unix=request['deadline_unix'])
                previous._save(destination / f'{index:02d}_RESPONSE.json', dict(response=response, rng_after=previous._rng(child)))
                require(messages == request['messages'], 'replay_cannot_mutate_prefix')
                require(digest(response) == digest(original['response']), 'bit_identical_generation:' + str(index))
                require(stream.checkpoint() == original_stream and child.plan == original_child_plan,
                    'replay_cannot_mutate_stream_plan')
                require(child.optimizer_steps == 99 and child.adapter_hash() == ADAPTER_STATE_SHA256
                    and _optimizer_fingerprint(child) == optimizer, 'replay_cannot_update_learning')
                child.engine.verify_base()
                require(time.time() < child.plan['hard_end_unix'], 'replay_finished_before_deadline')
                previous._save(destination / f'{index:02d}_MATCH.json', dict(status='MATCH',
                    source_sha256=row['source_sha256'], response_sha256=digest(response)))
            require(_bind(child, stream, journal, plan)[3] == suffix, 'journal_unchanged_after_replay')
            if attempt2:
                require(_verify_prior_attempt(plan, root, suffix) == prior_evidence, 'prior_attempt_evidence_unchanged')
            require(recipe == _verify_source(child, source, log, plan['native_source']['path']), 'unchanged_replay_recipe')
            _verify_original_plan(original_plan, child.plan)
            child.verify_checkpoint(plan['checkpoint'])
            for field in ('original_plan', 'original_log', 'original_exit', 'native_source'):
                require(hashlib.sha256(_raw(plan[field]['path'], 32 * 1024 * 1024)).hexdigest() == plan[field]['sha256'],
                    'original_evidence_unchanged:' + field)
            receipt = dict(schema=SCHEMA, status='COMPLETE', recovery_root=str(destination),
                sleep_request_sha256=SLEEP_REQUEST_SHA256, recovery_plan_sha256=digest(plan),
                checkpoint_sha256=CHECKPOINT_SHA256, matched_generations=3, optimizer_updates=0, optimizer_steps=99,
                new_row_sha256=[row['source_sha256'] for row in rows], rng_before=before, rng_after=previous._rng(child),
                rng_reconstruction_verified=True, verification='exact_committed_generation_replay',
                original_final_rng_snapshot_available=False, generate_ast_sha256=recipe,
                stream_sha256=original_stream['sha256'], pending_unchanged=True, no_retry=True, finished_unix=time.time())
            if attempt2:
                receipt['prior_failed_attempt_sha256'] = digest(prior_evidence)
            previous._save(destination / 'COMPLETE.json', receipt)
            return receipt
    except BaseException as error:
        try:
            previous._save(destination / 'FAILED.json', dict(schema=SCHEMA, status='FAILED', error_type=type(error).__name__,
                error=str(error), no_retry=True, child_must_be_discarded=True, finished_unix=time.time()))
        except BaseException as evidence_error:
            error.add_note('Failed to save recovery failure receipt: ' + str(evidence_error))
        raise
