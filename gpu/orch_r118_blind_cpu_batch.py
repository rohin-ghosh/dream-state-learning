"""Prospective CPU-only blind DEV batching; no implicit allocation or replay.

Prepare a new node-local root using Main's collector, then require a separately
published allocation before run. Prior roots must be terminal. Exact request,
model-file and decoder bindings alone permit cache reuse; other prior attempts
remain UNRESOLVED without another charged invocation. Raw responses/token IDs
stay in the node-local cache; ROWS retains every original provenance record.

PUBLICATION.json must contain authorized=true, the exact plan_sha256, the same
absolute deadline_unix, and an integer max_new_calls. The public run command
uses a private timeout worker; it never extends that deadline. Prior roots must
be explicitly enumerated and finalized at preparation. Legacy unbatched calls
are not relabelled as this decoder's results or automatically reattempted.
SUCCESSOR_SELECTION.json selects only never-attempted exact requests after
terminal/process release. Original annotations remain separately source-bound;
legacy-contract results are not inherited as new batched annotations.
"""

import argparse
from collections import OrderedDict
from copy import deepcopy
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r118_cpu_readout_judge as original


judge = original.judge
require = original.require
read, write, sha = original.read, original.write, original.sha
SCHEMA = 'R118_BLIND_CPU_BATCH_V1'
SOURCE = Path(__file__).resolve().parents[1]
MAX_BATCH = 4


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def unresolved(reason):
    return dict(status='UNRESOLVED', reason=reason, departures_and_returns=None, shifts=None)


def source_pins():
    paths = [Path(__file__), Path(original.__file__), Path(judge.__file__),
        Path(judge.previous.__file__), judge.PROMPT_PATH,
        judge.previous.PROMPT_PATH]
    return {str(path.resolve().relative_to(SOURCE)): sha(path) for path in paths}


def decoder_contract(model_manifest_sha256, batch_size, max_new_tokens, context_limit, call_seconds,
                     *, versions, eos_token_ids, pad_token_id):
    require(type(batch_size) is int and 1 <= batch_size <= MAX_BATCH, 'bounded_batch_size')
    require(type(max_new_tokens) is int and 1 <= max_new_tokens <= original.MAX_NEW_TOKENS,
        'bounded_output_tokens')
    require(type(context_limit) is int and 1 <= context_limit <= original.CONTEXT_LIMIT,
        'bounded_context')
    require(type(call_seconds) in (int, float) and math.isfinite(call_seconds)
        and 0 < call_seconds <= original.CALL_SECONDS, 'bounded_call_seconds')
    require(len(model_manifest_sha256) == 64
        and all(char in '0123456789abcdef' for char in model_manifest_sha256), 'model_manifest_hash')
    require(eos_token_ids and all(type(token) is int and token >= 0 for token in eos_token_ids)
        and type(pad_token_id) is int and pad_token_id >= 0, 'special_token_ids')
    require(set(versions) == {'torch', 'transformers'} and all(versions.values()), 'runtime_versions')
    return dict(schema=SCHEMA, model=judge.MODEL, revision=original.REVISION,
        model_manifest_sha256=model_manifest_sha256, device='cpu', dtype='bfloat16', threads=16,
        interop_threads=1, temperature=0, do_sample=False, source_files=source_pins(),
        algorithm='LEFT_PAD_GREEDY_KV_V1', batch_size=batch_size,
        max_new_tokens=max_new_tokens, context_limit=context_limit, call_seconds=call_seconds,
        eos_token_ids=sorted(set(eos_token_ids)), pad_token_id=pad_token_id,
        versions=dict(versions), attn_implementation='sdpa',
        comparison='Batched_CPU_not_assumed_bit_identical_to_unbatched_or_GPU')


def group_documents(documents, contract):
    require(documents and len(documents) <= 64, 'bounded_DEV_inventory')
    groups = OrderedDict()
    for index, item in enumerate(documents):
        require(set(item) == {'document', 'request', 'private_provenance'}, 'collected_document_shape')
        require(item['document'].get('kind') == 'held', 'DEV_readout_only')
        require(item['private_provenance'].get('parent_free') is True
            and item['private_provenance'].get('training_buffer') is False, 'parent_free_annotation_only')
        request = judge.request(item['document'])
        require(request == item['request'], 'exact_blind_request')
        key = digest(dict(request=request, contract=contract))
        if key not in groups:
            groups[key] = dict(key=key, request=deepcopy(request), document=deepcopy(item['document']),
                contract=deepcopy(contract), members=[])
        require(groups[key]['request'] == request, 'no_hash_only_join')
        groups[key]['members'].append(dict(index=index, private_provenance=deepcopy(item['private_provenance']),
            document_sha256=digest(item)))
    return list(groups.values())


def tokenize_request(tokenizer, request):
    tokens = tokenizer.apply_chat_template(request['messages'], tokenize=True,
        add_generation_prompt=True, truncation=False, return_dict=False)
    require(type(tokens) is list and tokens
        and all(type(token) is int and token >= 0 for token in tokens),
        'exact_flat_token_list_before_claim')
    return tokens


def left_pad(rows, pad_token_id):
    require(rows and all(row and all(type(token) is int and token >= 0 for token in row)
        for row in rows), 'nonempty_exact_token_inputs')
    width = max(map(len, rows))
    return dict(input_ids=[[pad_token_id] * (width-len(row)) + list(row) for row in rows],
        attention_mask=[[0] * (width-len(row)) + [1] * len(row) for row in rows],
        position_ids=[[0] * (width-len(row)) + list(range(len(row))) for row in rows])


def decode_batch(rows, caps, backend, *, eos_token_ids, pad_token_id, context_limit, deadline,
                 clock=None, on_step=None):
    clock = time.time if clock is None else clock
    require(0 < len(rows) == len(caps) <= MAX_BATCH, 'batch_shape')
    require(all(type(cap) is int and 1 <= cap <= original.MAX_NEW_TOKENS for cap in caps), 'per_sequence_caps')
    require(math.isfinite(deadline) and type(context_limit) is int and context_limit > 0, 'finite_decode_bound')
    left_pad(rows, pad_token_id)
    require(eos_token_ids and all(type(token) is int and token >= 0 for token in eos_token_ids), 'EOS_required')
    results = [dict(token_ids=[], termination=None) for row in rows]
    selected = []
    for index, row in enumerate(rows):
        if len(row) + caps[index] > context_limit:
            results[index]['termination'] = 'input_context_bound'
        else:
            selected.append(index)
    if not selected:
        return results
    batch = left_pad([rows[index] for index in selected], pad_token_id)
    if len(batch['input_ids'][0]) + max(caps[index] for index in selected) > context_limit:
        for index in selected:
            results[index]['termination'] = 'padded_batch_context_bound'
        return results
    masks = batch['attention_mask']
    first = True
    while any(results[index]['termination'] is None for index in selected):
        if clock() >= deadline:
            for index in selected:
                if results[index]['termination'] is None:
                    results[index]['termination'] = 'deadline'
            break
        try:
            predicted = backend.step(**batch, prefill=first)
            require(len(predicted) == len(selected)
                and all(type(token) is int and token >= 0 for token in predicted), 'greedy_batch_output_shape')
        except Exception as error:
            for index in selected:
                if results[index]['termination'] is None:
                    results[index].update(termination='backend_error', error_type=type(error).__name__)
            break
        first = False
        late = clock() >= deadline
        emitted = []
        for index, token in zip(selected, predicted):
            result = results[index]
            if result['termination'] is not None:
                continue
            result['token_ids'].append(token)
            if late:
                result['termination'] = 'deadline'
            elif len(result['token_ids']) >= caps[index]:
                result['termination'] = 'output_cap'
            elif token in eos_token_ids:
                result['termination'] = 'eos'
            emitted.append(dict(index=index, token_id=token, termination=result['termination']))
        if on_step is not None:
            on_step(emitted)
        next_tokens, positions = [], []
        for offset, index in enumerate(selected):
            active = results[index]['termination'] is None
            masks[offset].append(int(active))
            next_tokens.append([results[index]['token_ids'][-1] if active else pad_token_id])
            positions.append([len(rows[index]) + len(results[index]['token_ids']) - 1 if active else 0])
        batch = dict(input_ids=next_tokens, attention_mask=masks, position_ids=positions)
    return results


class TorchGreedy:
    def __init__(self, model, torch):
        self.model, self.torch = model, torch
        self.cache, self.cache_length = None, 0

    def step(self, input_ids, attention_mask, position_ids, *, prefill):
        if prefill:
            self.cache, self.cache_length = None, 0
        torch = self.torch
        count = len(input_ids[0])
        arguments = {name: torch.tensor(value, dtype=torch.long, device='cpu') for name, value in
            dict(input_ids=input_ids, attention_mask=attention_mask, position_ids=position_ids).items()}
        arguments.update(past_key_values=self.cache, use_cache=True, return_dict=True,
            cache_position=torch.arange(self.cache_length, self.cache_length+count, device='cpu'))
        with torch.inference_mode():
            output = self.model(**arguments)
        self.cache = output.past_key_values
        self.cache_length += count
        require(output.logits.device.type == 'cpu', 'CPU_logits_only')
        return output.logits[:, -1, :].argmax(dim=-1).tolist()


def classify(document, tokens, tokenizer):
    raw = tokenizer.decode(tokens['token_ids'], skip_special_tokens=True)
    result = original.interpret(document, raw, True) if tokens['termination'] == 'eos' else unresolved(tokens['termination'])
    return dict(raw=raw, token_ids=tokens['token_ids'], termination=tokens['termination'], result=result)


def prior_attempts(roots):
    entries = {}
    pending, seen = list(map(Path, roots)), set()
    while pending:
        root = pending.pop(0).resolve()
        if root in seen:
            continue
        seen.add(root)
        require_prior_released(root)
        if (root / 'PLAN.json').exists():
            plan = read(root / 'PLAN.json')
            if plan.get('schema') == SCHEMA:
                for prior in plan['prior_roots']:
                    require(prior_inventory(prior) == plan['prior_bindings'][prior], 'prior_lineage_binding')
                    pending.append(Path(prior))
        for request_path in sorted(root.glob('call_*/REQUEST.json')):
            request = read(request_path)
            entries.setdefault(digest(request), []).append(dict(request=request,
                legacy=True, path=str(request_path), response=str(request_path.parent / 'RESPONSE.json')))
        for claim_path in sorted(root.glob('cache/*/CLAIM.json')):
            claim = read(claim_path)
            entries.setdefault(digest(claim['request']), []).append(dict(claim,
                legacy=False, path=str(claim_path), response=str(claim_path.parent / 'RESPONSE.json')))
    return entries


def require_prior_released(root):
    root = Path(root)
    require((root / 'TERMINAL.json').is_file(), 'prior_run_must_be_terminal_no_live_replay')
    for name in ('STARTED.json', 'LOADED.json', 'GUARD_STARTED.json'):
        path = root / name
        if not path.exists():
            continue
        pid = read(path).get('pid')
        if pid is None:
            continue
        require(type(pid) is int and pid > 0, 'prior_process_identity')
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except PermissionError:
            require(False, 'prior_process_release_unverified')
        require(False, 'prior_process_still_present_no_successor')
    for name in ('RUNNER.lock', 'GUARD.lock'):
        lock_path = root / name
        if not lock_path.exists():
            continue
        with lock_path.open('r') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                require(False, 'prior_runner_lock_not_released')


def prior_inventory(root):
    root = Path(root)
    require_prior_released(root)
    paths = [root / 'TERMINAL.json', *root.glob('call_*/REQUEST.json'), *root.glob('call_*/RESPONSE.json'),
        *root.glob('cache/*/CLAIM.json'), *root.glob('cache/*/RESPONSE.json'), *root.glob('cache/*/RESULT.json')]
    for name in ('PLAN.json', 'STARTED.json', 'LOADED.json', 'GUARD_STARTED.json', 'DECODER.json'):
        if (root / name).exists():
            paths.append(root / name)
    return {str(path.relative_to(root)): sha(path) for path in sorted(paths)}


def select_successor(documents, roots):
    require(roots, 'explicit_prior_run_inventory_required')
    entries = prior_attempts(roots)
    groups = group_documents(documents, {'selection_only': True})
    selected = []
    for group in groups:
        request_sha256 = digest(group['request'])
        previous = entries.get(request_sha256, [])
        require(all(entry['request'] == group['request'] for entry in previous), 'exact_prior_request_join')
        selected.append(dict(request_sha256=request_sha256,
            disposition='PREVIOUSLY_ATTEMPTED_NO_DISPATCH' if previous else 'NEVER_ATTEMPTED',
            members=deepcopy(group['members']), prior_attempts=[preserved_attempt(entry) for entry in previous]))
    return dict(schema='R118_NEVER_ATTEMPTED_SELECTION_V1', groups=selected,
        unique_blind_inputs=len(groups), member_rows=len(documents),
        never_attempted_inputs=sum(not row['prior_attempts'] for row in selected),
        previously_attempted_inputs=sum(bool(row['prior_attempts']) for row in selected),
        comparison='Prior annotations retain their original decoder; no batched bit-identity claim')


def preserved_attempt(entry):
    response_path = Path(entry['response'])
    result = dict(request=reference(Path(entry['path'])),
        source_contract=deepcopy(entry.get('contract')),
        contract_kind='LEGACY_UNBATCHED' if entry['legacy'] else 'EXACT_BOUND_BATCH',
        legacy_contract_not_inferred=entry['legacy'], eligible_for_new_dispatch=False)
    source_root = Path(entry['path']).parent.parent if entry['legacy'] else Path(entry['path']).parents[2]
    result['source_bindings'] = {name: reference(source_root / name)
        for name in ('PLAN.json', 'DECODER.json', 'TERMINAL.json') if (source_root / name).is_file()}
    if response_path.is_file():
        result.update(response=reference(response_path), original_result=deepcopy(read(response_path)['result']))
    else:
        result['status'] = 'CHARGED_WITHOUT_RESPONSE'
    return result


def cached_result(group, entries):
    previous = entries.get(digest(group['request']), [])
    for entry in previous:
        require(entry['request'] == group['request'], 'exact_prior_request_join')
        if entry.get('key') != group['key'] or entry.get('contract') != group['contract']:
            continue
        path = Path(entry['response'])
        if not path.exists():
            continue
        receipt_path = path.parent / 'RESULT.json'
        require(receipt_path.exists() and read(receipt_path)['response_sha256'] == sha(path), 'cached_response_hash')
        response = read(path)
        require(response['key'] == group['key'], 'cache_response_identity')
        tokens = response['token_ids']
        require(isinstance(tokens, list) and all(type(token) is int and token >= 0 for token in tokens)
            and len(tokens) <= group['contract']['max_new_tokens'], 'cached_exact_token_bounds')
        if response['termination'] == 'eos':
            require(tokens and tokens[-1] in group['contract']['eos_token_ids']
                and len(tokens) < group['contract']['max_new_tokens'], 'cached_actual_EOS')
        validated = original.interpret(group['document'], response['raw'], True) if response['termination'] == 'eos' else unresolved(response['termination'])
        require(validated == response['result'], 'cached_annotation_validation')
        return dict(result=deepcopy(response['result']), response=reference(path), disposition='EXACT_CACHE')
    if previous:
        return dict(result=unresolved('prior_attempt_not_exact_reusable_no_replay'), disposition='PRIOR_ATTEMPT_BLOCKED',
            preserved_prior_annotations=[preserved_attempt(entry) for entry in previous],
            prior_requests=[reference(Path(entry['path'])) for entry in previous],
            prior_responses=[reference(Path(entry['response'])) for entry in previous if Path(entry['response']).exists()])
    return None


def expand_rows(groups, results):
    rows = []
    for group in groups:
        for member in group['members']:
            rows.append(dict(member, cache_key=group['key'], annotation=deepcopy(results[group['key']]),
                semantic_labels_are_model_judgments=True, training_buffer=False))
    return sorted(rows, key=lambda row: row['index'])


def node_environment(root):
    original.cpu_environment()
    root = Path(root).resolve()
    require(root.is_relative_to('/localhome') and not any((parent / '.git').exists()
        for parent in (root, *root.parents, SOURCE, *SOURCE.parents)), 'immutable_node_local_raw_only')


def execution_groups(documents, contract, selection, *, never_attempted_only):
    groups = group_documents(documents, contract)
    if never_attempted_only:
        allowed = {item['request_sha256'] for item in selection['groups']
            if item['disposition'] == 'NEVER_ATTEMPTED'}
        groups = [group for group in groups if digest(group['request']) in allowed]
    return groups


def prepare(root, child_root, cycles, model_dir, source_manifest, deadline_unix, *, prior_roots=(),
            batch_size=4, never_attempted_only=False):
    root = Path(root)
    node_environment(root)
    require(type(batch_size) is int and 1 <= batch_size <= MAX_BATCH, 'bounded_batch_size')
    require(math.isfinite(deadline_unix) and deadline_unix > time.time(),
        'finite_original_absolute_deadline')
    require(not root.exists(), 'new_scope_root_only')
    require(prior_roots, 'explicit_prior_run_inventory_required')
    require(all(Path(prior).resolve() != root.resolve() for prior in prior_roots), 'distinct_predecessor_roots')
    prior_bindings = {}
    for prior in prior_roots:
        node_environment(prior)
        prior_bindings[str(Path(prior).resolve())] = prior_inventory(prior)
    require(all(read(source_manifest).get(name) == expected for name,expected in source_pins().items()),
        'all_helper_judge_sources_bound')
    original.prepare(root / 'inputs', child_root, cycles, model_dir, source_manifest)
    inputs = read(root / 'inputs/PLAN.json')
    selection = select_successor(read(root / 'inputs/DOCUMENTS.json'), prior_roots)
    write(root / 'SUCCESSOR_SELECTION.json', selection)
    groups = execution_groups(read(root / 'inputs/DOCUMENTS.json'), {'selection_only': True},
        selection, never_attempted_only=never_attempted_only)
    write(root / 'EXECUTION_SELECTION.json', dict(never_attempted_only=never_attempted_only,
        request_sha256s=[digest(group['request']) for group in groups],
        member_indices=[member['index'] for group in groups for member in group['members']],
        unique_inputs=len(groups), member_rows=sum(len(group['members']) for group in groups),
        legacy_annotations_inherited=False,
        changed_contract='LEFT_PAD_GREEDY_KV_V1; batched CPU not assumed bit-identical to legacy'))
    write(root / 'PLAN.json', dict(schema=SCHEMA, original_inputs=reference(root / 'inputs/PLAN.json'),
        successor_selection=reference(root / 'SUCCESSOR_SELECTION.json'),
        execution_selection=reference(root / 'EXECUTION_SELECTION.json'),
        never_attempted_only=never_attempted_only,
        input_root=str((root / 'inputs').resolve()), source_files=source_pins(),
        deadline_unix=deadline_unix, max_wall_seconds=original.MAX_SECONDS,
        batch_size=batch_size, prior_roots=[str(Path(path).resolve()) for path in prior_roots],
        prior_bindings=prior_bindings,
        max_new_calls=selection['never_attempted_inputs'], threads=16, device='cpu', parent_calls=0,
        optimizer_updates=0, annotation_only=True, DEV_only=True))


def run(root):
    root = Path(root)
    node_environment(root)
    plan = read(root / 'PLAN.json')
    require(plan['schema'] == SCHEMA and plan['source_files'] == source_pins(), 'pinned_helper_scope')
    permission = read(root / 'PUBLICATION.json')
    require(permission.get('authorized') is True and permission.get('plan_sha256') == sha(root / 'PLAN.json')
        and permission.get('deadline_unix') == plan['deadline_unix'], 'new_explicit_published_allocation')
    require((root / 'GUARD_STARTED.json').is_file()
        and os.environ.get('ORCH_R118_CPU_GUARD_SHA256') == sha(root / 'GUARD_STARTED.json'), 'bounded_parent_guard_required')
    require(type(permission.get('max_new_calls')) is int and 0 <= permission['max_new_calls'] <= plan['max_new_calls'],
        'no_extra_call_pool')
    require(time.time() < plan['deadline_unix'], 'deadline_not_reset')
    require(plan['prior_roots'], 'explicit_prior_run_inventory_required')
    for prior in plan['prior_roots']:
        node_environment(prior)
        require(prior_inventory(prior) == plan['prior_bindings'][prior], 'prior_charges_and_results_unchanged')
    require(sha(plan['original_inputs']['path']) == plan['original_inputs']['sha256'], 'input_plan_binding')
    inputs = read(plan['original_inputs']['path'])
    input_root = Path(plan['input_root'])
    require(sha(input_root / 'DOCUMENTS.json') == inputs['documents_sha256']
        and sha(input_root / 'MODEL_SHA256.json') == inputs['model_manifest_sha256'], 'bound_inventory_model')
    require(inputs['model'] == judge.MODEL and inputs['revision'] == original.REVISION
        and inputs['threads'] == 16 and inputs['device'] == 'cpu', 'fixed_CPU14B')
    model_dir = Path(inputs['model_dir'])
    for name, expected in read(input_root / 'MODEL_SHA256.json').items():
        require(Path(name).name == name and sha(model_dir / name) == expected, 'model_bytes_unchanged')
    previous = prior_attempts(plan['prior_roots'])
    selection_ref = plan['successor_selection']
    require(sha(selection_ref['path']) == selection_ref['sha256'], 'successor_selection_binding')
    selection = select_successor(read(input_root / 'DOCUMENTS.json'), plan['prior_roots'])
    require(selection == read(selection_ref['path']), 'successor_selection_unchanged')
    execution_ref = plan['execution_selection']
    require(sha(execution_ref['path']) == execution_ref['sha256'], 'execution_selection_binding')
    allowed_requests = {item['request_sha256'] for item in selection['groups']
        if item['disposition'] == 'NEVER_ATTEMPTED'}
    with (root / 'RUNNER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(root / 'STARTED.json', dict(started_unix=time.time(), pid=os.getpid(), deadline_unix=plan['deadline_unix']))
        require(time.time() < plan['deadline_unix'], 'wall_bound_before_model_load')
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        require(not torch.cuda.is_initialized(), 'no_CUDA_initialization')
        torch.set_num_threads(16)
        torch.set_num_interop_threads(1)
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
        tokenizer.padding_side = 'left'
        model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.bfloat16,
            device_map={'': 'cpu'}, local_files_only=True, trust_remote_code=False, attn_implementation='sdpa')
        model.requires_grad_(False)
        model.eval()
        require(all(parameter.device.type == 'cpu' and not parameter.requires_grad for parameter in model.parameters())
            and not torch.cuda.is_initialized() and torch.get_num_threads() == 16, 'frozen_CPU_parameters')
        versions = {name:parameter._version for name,parameter in model.named_parameters()}
        write(root / 'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(), device='cpu', threads=16,
            cuda_initialized=False, trainable_parameters=0, model_manifest_sha256=inputs['model_manifest_sha256']))
        eos = model.generation_config.eos_token_id
        eos = eos if isinstance(eos, list) else [eos]
        pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos[0]
        require(inputs['context_limit'] <= model.config.max_position_embeddings, 'native_context_config')
        contract = decoder_contract(inputs['model_manifest_sha256'], plan['batch_size'], inputs['max_new_tokens'],
            inputs['context_limit'], inputs['call_seconds'],
            versions={name:importlib.metadata.version(name) for name in ('torch', 'transformers')},
            eos_token_ids=eos, pad_token_id=pad)
        groups = execution_groups(read(input_root / 'DOCUMENTS.json'), contract, selection,
            never_attempted_only=plan['never_attempted_only'])
        execution = read(execution_ref['path'])
        require([digest(group['request']) for group in groups] == execution['request_sha256s']
            and [member['index'] for group in groups for member in group['members']] == execution['member_indices'],
            'exact_execution_members')
        write(root / 'GROUPS.json', groups)
        write(root / 'DECODER.json', contract)
        results, pending = {}, []
        for group in groups:
            cached = cached_result(group, previous)
            if cached is not None:
                results[group['key']] = cached
            else:
                require(digest(group['request']) in allowed_requests, 'never_attempted_only_dispatch')
                pending.append(group)
        attempts = 0
        for offset in range(0, len(pending), plan['batch_size']):
            chosen = pending[offset:offset+plan['batch_size']]
            allowance = max(0, permission['max_new_calls']-attempts) if time.time() < plan['deadline_unix']-5 else 0
            for group in chosen[allowance:]:
                results[group['key']] = dict(result=unresolved('unattempted_wall_or_call_bound'), disposition='UNATTEMPTED')
            chosen = chosen[:allowance]
            if not chosen:
                continue
            rows = [tokenize_request(tokenizer, group['request']) for group in chosen]
            started = time.time()
            for group in chosen:
                write(root / 'cache' / group['key'] / 'CLAIM.json', dict(key=group['key'], request=group['request'],
                    contract=contract, attempts=1, reserved_unix=started))
            attempts += len(chosen)
            with (root / f'batch_{offset:04d}.tokens.jsonl').open('x') as token_log:
                token_log.write(json.dumps(dict(batch_keys=[group['key'] for group in chosen],
                    input_tokens=[len(row) for row in rows], started_unix=started))+'\n')
                token_log.flush()
                def capture_tokens(emitted):
                    token_log.write(json.dumps(dict(observed_unix=time.time(), emitted=emitted))+'\n')
                    token_log.flush()
                decoded = decode_batch(rows, [inputs['max_new_tokens']]*len(chosen), TorchGreedy(model, torch),
                    eos_token_ids=eos, pad_token_id=pad, context_limit=inputs['context_limit'],
                    deadline=min(plan['deadline_unix']-5, started+inputs['call_seconds']), on_step=capture_tokens)
            for group, tokens, input_ids in zip(chosen, decoded, rows):
                response = dict(classify(group['document'], tokens, tokenizer), key=group['key'], input_tokens=len(input_ids),
                    started_unix=started, finished_unix=time.time(), batch_keys=[item['key'] for item in chosen])
                path = root / 'cache' / group['key'] / 'RESPONSE.json'
                write(path, response)
                write(path.parent / 'RESULT.json', dict(response_sha256=sha(path), key=group['key']))
                results[group['key']] = dict(result=response['result'], response=reference(path), disposition='NEW_SINGLE_ATTEMPT')
        require(all(parameter._version == versions[name] for name,parameter in model.named_parameters())
            and not torch.cuda.is_initialized(), 'CPU_judge_unchanged')
        expanded = expand_rows(groups, results)
        write(root / 'ROWS.json', expanded)
        write(root / 'TERMINAL.json', dict(status='WALL_OR_CALL_BOUND' if any(value['disposition'] == 'UNATTEMPTED'
            for value in results.values()) else 'COMPLETE', finished_unix=time.time(), expected_rows=len(expanded),
            unique_blind_inputs=len(groups), new_charged_calls=attempts, deadline_unix=plan['deadline_unix'],
            complete_unique=sum(value['result']['status'] == 'COMPLETE' for value in results.values()),
            unresolved_unique=sum(value['result']['status'] == 'UNRESOLVED' for value in results.values()),
            optimizer_updates=0, parent_calls=0, raw_node_only=True))


def run_bounded(root):
    root = Path(root)
    node_environment(root)
    plan = read(root / 'PLAN.json')
    publication = read(root / 'PUBLICATION.json')
    require(publication.get('authorized') is True and publication.get('plan_sha256') == sha(root / 'PLAN.json')
        and publication.get('deadline_unix') == plan['deadline_unix'], 'new_explicit_published_allocation')
    remaining = plan['deadline_unix'] - time.time()
    require(math.isfinite(remaining) and remaining > 0, 'finite_remaining_wall')
    remaining = min(remaining, original.MAX_SECONDS)
    require(not (root / 'STARTED.json').exists(), 'no_automatic_annotation_replay')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining)+'s', sys.executable, '-B',
        '-m', 'gpu.orch_r118_blind_cpu_batch', 'run', '--root', str(root), '--worker']
    with (root / 'GUARD.lock').open('a') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(root / 'GUARD_STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), deadline_unix=plan['deadline_unix'], command=command))
        completed = subprocess.run(command, check=False, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
            PYTHONPATH=str(SOURCE), OMP_NUM_THREADS='16', MKL_NUM_THREADS='16', TOKENIZERS_PARALLELISM='false',
            ORCH_R118_CPU_GUARD_SHA256=sha(root / 'GUARD_STARTED.json')))
        if not (root / 'TERMINAL.json').exists():
            write(root / 'TERMINAL.json', dict(status='WALL_BOUND' if completed.returncode in (124, 137) else 'FAILED',
                exit_code=completed.returncode, finished_unix=time.time(), deadline_unix=plan['deadline_unix'],
                charged_claims=len(list(root.glob('cache/*/CLAIM.json'))), no_automatic_retry=True))
        return completed.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--child-root', type=Path)
    parser.add_argument('--cycles', type=int, nargs='+')
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--source-manifest', type=Path)
    parser.add_argument('--deadline-unix', type=float)
    parser.add_argument('--prior-root', type=Path, action='append', default=[])
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--never-attempted-only', action='store_true')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.action == 'prepare':
        require(all(value is not None for value in (args.child_root, args.cycles, args.model_dir,
            args.source_manifest, args.deadline_unix)), 'prepare_arguments_required')
        prepare(args.root, args.child_root, args.cycles, args.model_dir, args.source_manifest,
            args.deadline_unix, prior_roots=args.prior_root, batch_size=args.batch_size,
            never_attempted_only=args.never_attempted_only)
    else:
        if args.worker:
            run(args.root)
        else:
            raise SystemExit(run_bounded(args.root))


if __name__ == '__main__':
    main()
