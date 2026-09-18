"""Exact teach-perception sleep15 RNG replay, derived from pinned kernel0 recovery.

No target encoding, stream mutation, learning, or held reads during replay.
Three exact original generations, including the excluded third, must match.
Native continuation applies separate pinned-row eligibility correction.
No retry/attempt2 path is authorized by this module.
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


SCHEMA = 'R141_PERCEPTION_EXCLUSION_RECOVERY_V1'
SOURCE_ROOT = '/localhome/local-rohing/orch_r136_node1_isolation_20260916_attempt2/source'
SLEEP_REQUEST_SHA256 = 'dd8530faf499c6cc4138958af33b55ec9ca4fa0cb28f2436a6b0e6da8b3aa1f6'
ADAPTER_STATE_SHA256 = '994e0e9b908d7bb79cc9bb523b2b47a310cf8346653527afa19e83407a485b9e'
CHECKPOINT_SHA256 = dict(adapter='91a10c91f3e3083aae8fd509c2437892182ca3f64e284f2b02ad667a28f8fa98',
    optimizer='286323206ed9351488cb501eab644d6b5fd72244805d7eafca5aa98bac19d59e',
    rng='286323206ed9351488cb501eab644d6b5fd72244805d7eafca5aa98bac19d59e')
ORIGINAL_PLAN_SHA256 = 'ff60807013aa006823e06a8d29e913ec15734c8179708fcd56bc7dd825c554c6'
ORIGINAL_LOG_SHA256 = '18e66135a40bb88a61fa0cc5c9b37654d88d3112a2338fbb8a9e3419335bdb2c'
ORIGINAL_EXIT_SHA256 = '3dbfd85622174ffe0d56385a54d26b445f1dc6c6567e679621fd0804fd2bafdd'
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
    from gpu.orch_r141_a100_perception_exclusion_20260916 import evidence
    state, records = previous._journal_records(journal)
    require(state['request'] is None and state['response'] is None
        and state['sleep_request'] == {'cycle': 16}
        and state['latest']['document'] == stream.checkpoint(), 'exact_pending_sleep16_journal')
    original_plan = json.loads(_raw(plan['original_plan']['path'], 32 * 1024 * 1024))
    require(hashlib.sha256(_raw(plan['original_plan']['path'], 32 * 1024 * 1024)).hexdigest()
        == ORIGINAL_PLAN_SHA256, 'original_perception_plan')
    checkpoint = plan['checkpoint']
    requests, responses = evidence.bind_live(records, checkpoint, original_plan)
    require(checkpoint['checkpoint_sha256'] == CHECKPOINT_SHA256
        and checkpoint['adapter_state_sha256'] == child.adapter_hash() == ADAPTER_STATE_SHA256
        and checkpoint['optimizer_steps'] == child.optimizer_steps == 1010
        and checkpoint['base_sha256'] == BASE_SHA256, 'exact_restored_sleep15_state')
    require(child.plan['decoder'] == original_plan['decoder'] == DECODER
        and child.plan['hard_end_unix'] == stream.deadline_unix == original_plan['hard_end_unix']
        and child.plan['segment_tokens'] == stream.segment_tokens == original_plan['segment_tokens']
        and child.plan['context_limit'] == stream.context_limit == original_plan['context_limit'],
        'exact_perception_replay_recipe')
    require(records[-1]['document']['raw_modified'] is False
        and records[-1]['document']['version'] == stream.presentation['version'],
        'original_eligibility_receipt_preserved')
    return deepcopy(stream.pending_rows()), requests, responses, records[1234:]


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




def _restore(child, checkpoint, root):
    saved = root / 'checkpoints' / 'sleep_000015'
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
    require(payload['optimizer_steps'] == 1010 and payload['parameter_names'] == list(child.parameters),
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
    require(type(plan) is dict and set(plan) == _FIELDS
        and plan['schema'] == SCHEMA, 'explicit_kernel_recovery_plan')
    require(plan['sleep_request_sha256'] == SLEEP_REQUEST_SHA256, 'pinned_kernel_sleep_request')
    for field, expected in (('original_plan', ORIGINAL_PLAN_SHA256), ('original_log', ORIGINAL_LOG_SHA256),
            ('original_exit', ORIGINAL_EXIT_SHA256)):
        require(plan[field]['sha256'] == expected, 'fixed_kernel_evidence:' + field)
    require(plan['native_source']['path'] == str(Path(SOURCE_ROOT) / 'gpu' / 'orch_r125_continual_native.py'),
        'original_source1_native_required')
    root, destination = Path(child.plan['root']), Path(plan['recovery_root'])
    attempt2 = False
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
            prior_evidence = None
            original_stream, original_child_plan = stream.checkpoint(), deepcopy(child.plan)
            optimizer = _restore(child, plan['checkpoint'], root)
            before = previous._rng(child)
            previous._save(destination / 'STARTED.json', dict(schema=SCHEMA, rng=before,
                optimizer_state_sha256=optimizer, optimizer_steps=1010, no_retry=True, generate_ast_sha256=recipe))
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
                require(child.optimizer_steps == 1010 and child.adapter_hash() == ADAPTER_STATE_SHA256
                    and _optimizer_fingerprint(child) == optimizer, 'replay_cannot_update_learning')
                child.engine.verify_base()
                require(time.time() < child.plan['hard_end_unix'], 'replay_finished_before_deadline')
                previous._save(destination / f'{index:02d}_MATCH.json', dict(status='MATCH',
                    source_sha256=row['source_sha256'], response_sha256=digest(response)))
            require(_bind(child, stream, journal, plan)[3] == suffix, 'journal_unchanged_after_replay')
            require(recipe == _verify_source(child, source, log, plan['native_source']['path']), 'unchanged_replay_recipe')
            _verify_original_plan(original_plan, child.plan)
            child.verify_checkpoint(plan['checkpoint'])
            for field in ('original_plan', 'original_log', 'original_exit', 'native_source'):
                require(hashlib.sha256(_raw(plan[field]['path'], 32 * 1024 * 1024)).hexdigest() == plan[field]['sha256'],
                    'original_evidence_unchanged:' + field)
            receipt = dict(schema=SCHEMA, status='COMPLETE', recovery_root=str(destination),
                sleep_request_sha256=SLEEP_REQUEST_SHA256, recovery_plan_sha256=digest(plan),
                checkpoint_sha256=CHECKPOINT_SHA256, matched_generations=3, optimizer_updates=0, optimizer_steps=1010,
                new_row_sha256=[row['source_sha256'] for row in rows], rng_before=before, rng_after=previous._rng(child),
                rng_reconstruction_verified=True, verification='exact_committed_generation_replay',
                original_final_rng_snapshot_available=False, generate_ast_sha256=recipe,
                stream_sha256=original_stream['sha256'], pending_unchanged=True, no_retry=True, finished_unix=time.time())
            previous._save(destination / 'COMPLETE.json', receipt)
            return receipt
    except BaseException as error:
        try:
            previous._save(destination / 'FAILED.json', dict(schema=SCHEMA, status='FAILED', error_type=type(error).__name__,
                error=str(error), no_retry=True, child_must_be_discarded=True, finished_unix=time.time()))
        except BaseException as evidence_error:
            error.add_note('Failed to save recovery failure receipt: ' + str(evidence_error))
        raise
