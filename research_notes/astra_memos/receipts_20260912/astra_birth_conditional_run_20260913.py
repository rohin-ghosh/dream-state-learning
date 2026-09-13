"""Main-operated BIRTH diagnostics; immutable phases, owned workers, metadata custody."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import signal
import stat
import sys
import threading
import time

sys.dont_write_bytecode = True
SELF = Path(os.path.abspath(__file__))
PROTOCOL = 'authored_birth_conditional_run_v1_20260913'
ARMS, CELLS = ('AUTH', 'DERANGED'), ('OFF', 'AUTH', 'DERANGED')
CAPS = {'fit': 1800, 'readout': 2700}
WORKER, CLEANUP, COLLECTION, LEASE_MARGIN = 600, 140, 300, 21600
GENERATION = dict(temperature=0.0, seed=20260912, max_tokens=64)
DEFAULT_CONFIG = dict(seed=0, lr=1e-4, epochs=4, batch_size=8, fit_seconds=1800,
    readout_seconds=2700, max_updates_per_arm=128)
ORIGIN = 'UNRESOLVED_LOCAL_HASHES_ONLY'
CLAIMS = 'AUTHORED_NOT_CLEAN_NOT_OWN_WAKE; no automatic L1/full-core/bit-triple-gym readiness claim'
PRIMARY = dict(conditional_metric='own_map_strict_joint', conditional_fraction=[9, 10],
    twin_metric='own_map_strict_pass', twin_fraction=[9, 10], anchor_metric='instruction_compliant',
    anchor_fraction=[95, 100], max_anchor_loss_from_OFF=1, anchor_tag_spill=0,
    scope='conditional/locality birth component only', automatic_L1_pass=False)
COMMON = Path('/tmp/astra_rulegame_process_write_collect_20260912.py')
COMMON_SHA = 'e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def path(value):
    result = Path(os.path.abspath(Path(value).expanduser()))
    require(not any(item.is_symlink() for item in (result, *result.parents)), 'symlink path rejected')
    return result


def raw(value, limit=32*1024*1024):
    source = path(value)
    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, 'unsafe/oversized input')
        data = stream.read(limit+1)
        after = os.fstat(stream.fileno())
        require(len(data) == before.st_size and all(getattr(before, key) == getattr(after, key) == getattr(source.stat(), key)
            for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'input changed while reading')
    return data


def digest(value):
    return hashlib.sha256(raw(value)).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def load_file(source, pin, name):
    data = raw(source, 2*1024*1024)
    require(hashlib.sha256(data).hexdigest() == pin, 'helper source pin changed')
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(source), 'exec'), module.__dict__)
    return module


common = load_file(COMMON, COMMON_SHA, 'birth_run_safe_io')
read, write_json, write_new = common.read, common.write_json, common.write_new


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timezone-aware deadline required')
    return parsed.timestamp()


def fresh(value, protected=()):
    result = path(value)
    require(not result.exists(), 'fresh output required; no overwrite or in-place restart')
    for source in protected:
        source = path(source)
        require(result != source and result not in source.parents and source not in result.parents, 'output overlaps protected input')
    return result


def validate_config(config):
    require(set(config) == set(DEFAULT_CONFIG), 'explicit fixed config fields required')
    require(type(config['seed']) is int and config['seed'] == 0 and config['lr'] == 1e-4,
        'Main seed0/LR1e-4 fixed; no automatic dose selection')
    require(type(config['epochs']) is int and config['epochs'] > 0 and config['batch_size'] == 8,
        'positive epochs and owner GROUP_SIZE8 required')
    require(type(config['max_updates_per_arm']) is int and config['max_updates_per_arm'] > 0, 'finite explicit update ceiling required')
    for phase in CAPS:
        require(type(config[phase+'_seconds']) is int and CLEANUP < config[phase+'_seconds'] <= CAPS[phase], 'phase cap exceeds Main limit')
    return config


def tokenizer_files(model):
    required = {'config.json', 'tokenizer.json', 'tokenizer_config.json'}
    optional = {'vocab.json', 'merges.txt', 'special_tokens_map.json', 'added_tokens.json', 'chat_template.jinja', 'chat_template.json'}
    return {name: digest(os.path.realpath(path(model)/name))
        for name in sorted(required | {name for name in optional if (path(model)/name).exists()})}


def make_plan(root, phase, source, module_pin, model, device, deadline, lease_end, config, api):
    validate_config(config)
    end, lease = timestamp(deadline), timestamp(lease_end)
    require(time.time()+config[phase+'_seconds'] < end <= lease-LEASE_MARGIN, 'full phase window and six-hour lease margin required')
    require(isinstance(device, str) and re.fullmatch(r'(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})', device), 'one explicit device required')
    return dict(protocol=PROTOCOL, phase=phase, root=str(root), source_root=str(path(source)), module_sha256=module_pin,
        sidecar=str(SELF), sidecar_sha256=digest(SELF), python=os.path.abspath(sys.executable), source_hashes=source_pins(source, api),
        model=str(path(model)), model_files=api[1].model_hashes(model), device=device, deadline=end, real_lease_end=lease,
        lease_cutoff=lease-LEASE_MARGIN, controller_seconds=config[phase+'_seconds'], worker_seconds=WORKER,
        cleanup_seconds=CLEANUP, collection_seconds=COLLECTION, main_config=config, primary_criteria=PRIMARY,
        primary_criteria_sha256=value_hash(PRIMARY), generation=GENERATION, origin=ORIGIN, claims=CLAIMS,
        automatic_pass=False, members=list(ARMS if phase == 'fit' else CELLS), input_hashes={})


def prepare_fit(source, module_sha256, model, out, device, deadline, lease_end, config=None, restart_release=None, restart_sha256=None):
    root = fresh(out, (source, model, SELF))
    root.mkdir(mode=0o700)
    write_json(root/'preparation.started.json', dict(started_wall=time.time(), phase='fit', retry=False))
    try:
        return _prepare_fit(source, module_sha256, model, root, device, deadline, lease_end, config, restart_release, restart_sha256)
    except BaseException as error:
        if not (root/'prepare_failure.json').exists():
            write_json(root/'prepare_failure.json', dict(error_type=type(error).__name__, retry=False))
        raise


def _prepare_fit(source, module_sha256, model, out, device, deadline, lease_end, config=None, restart_release=None, restart_sha256=None):
    config = dict(DEFAULT_CONFIG if config is None else config)
    api = source_api(source, module_sha256)
    corpus, base, trainer, capture = api
    root = path(out)
    plan = make_plan(root, 'fit', source, module_sha256, model, device, deadline, lease_end, config, api)
    candidate = corpus.build_candidate(root=0)
    audit = corpus.audit_candidate(candidate)
    require(len(candidate['train']['AUTH']) == len(candidate['train']['DERANGED']) == 256
        and len(candidate['dev']) == 128 and audit['batch_size'] == 8, 'Main-approved256/128 birth inventory changed')
    recipe = corpus.training_recipe(learning_rate=config['lr'], seed=config['seed'], epochs=config['epochs'])
    require(recipe['batch_size'] == config['batch_size'] and recipe['rank'] == 8 and recipe['alpha'] == 16,
        'birth isolated batch/LoRA recipe mismatch')
    native = corpus.audit_native(candidate, model, tokenizer_files(model), recipe=recipe)
    require(native['status'] == 'NATIVE_TOKEN_MATCH_VERIFIED' and native['birth_source_sha256'] == module_sha256
        and native['recipe'] == recipe and native['audited_epochs'] == config['epochs']
        and native['no_truncation'] is True and native['loss_bearing_padding'] is False, 'native token audit incomplete')
    steps = native['updates_per_audited_seed']
    require(steps == 256//8*config['epochs'] <= config['max_updates_per_arm']
        and len(native['optimizer_update_rows']['0']) == steps, 'audited update ceiling/count mismatch')
    plan.update(recipe=recipe, train_config=asdict(trainer.TrainConfig(**recipe, model=str(path(model)))),
        expected_rows=256, expected_steps=steps, candidate_sha256=corpus.digest(candidate),
        expected_tokens={arm: dict(total=native['input_tokens_per_epoch'][arm], target=native['target_tokens_per_epoch'][arm],
            context=native['input_tokens_per_epoch'][arm]-native['target_tokens_per_epoch'][arm]) for arm in ARMS},
        dose_limitation='Same conditional presentation count as SEQ108; truthful anchors change gradient dilution and cost, not isolated.')
    if restart_release is not None:
        plan['restart_of'] = check_restart(restart_release, restart_sha256, plan)
    try:
        material = root/'material'
        material.mkdir()
        for name, value in {'candidate.json': candidate, 'candidate_audit.json': audit, 'native_audit.json': native,
            'recipe.json': recipe, **{arm+'.json': {'corpus': native['corpora'][arm]} for arm in ARMS}}.items():
            write_json(material/name, value)
        plan['materialroot'] = str(material)
        plan['material_files'] = base.tree_hashes(material)
        plan['input_hashes'] = {str(material/name): pin for name, pin in plan['material_files'].items()}
        verify_pins(plan['source_hashes'])
        require(base.model_hashes(model) == plan['model_files'] and time.time() < plan['deadline']-plan['controller_seconds'],
            'preparation source/model/window changed')
        return seal_plan(root, plan)
    except BaseException as error:
        write_json(root/'prepare_failure.json', dict(error_type=type(error).__name__, retry=False))
        raise


def fixed_requests(corpus, candidate):
    cases = corpus.readout_cases(candidate, split='dev')
    require(len(cases) == 128 and len({case['id'] for case in cases}) == 128, 'full dev/anchor panel required')
    return [dict(call_id=f'{index:04d}', case_id=case['id'], role='readout', arm='readout', prompt=case['context'], **GENERATION)
        for index, case in enumerate(cases)]


def prepare_readout(fit_root, fit_plan_sha256, fit_release, fit_release_sha256, out, deadline, lease_end,
                    restart_release=None, restart_sha256=None):
    fit_root, fitted = read_plan(fit_root, fit_plan_sha256)
    root = fresh(out, (fit_root, fitted['source_root'], fitted['model'], SELF))
    require(root.parent == fit_root.parent, 'fresh sibling readout required')
    root.mkdir(mode=0o700)
    write_json(root/'preparation.started.json', dict(started_wall=time.time(), phase='readout', retry=False))
    try:
        return _prepare_readout(fit_root, fit_plan_sha256, fit_release, fit_release_sha256, root, deadline, lease_end,
            restart_release, restart_sha256)
    except BaseException as error:
        write_json(root/'prepare_failure.json', dict(error_type=type(error).__name__, retry=False))
        raise


def _prepare_readout(fit_root, fit_plan_sha256, fit_release, fit_release_sha256, out, deadline, lease_end,
                     restart_release=None, restart_sha256=None):
    fit_root, fitted, api = verify_plan(fit_root, fit_plan_sha256)
    require(fitted['phase'] == 'fit', 'paired fit plan required')
    root = path(out)
    require(root.parent == fit_root.parent, 'fresh sibling readout required')
    release = accepted_release(fit_release, fit_release_sha256, fitted, fit_plan_sha256)
    require(release['phase_complete'] is True, 'both complete released fits required')
    terminal = read(fit_root/'run/result.json')
    require(not (fit_root/'run/failure.json').exists() and terminal['phase'] == 'fit' and set(terminal['members']) == set(ARMS),
        'both fit captures required')
    audit_terminal(fit_root, fitted, api, fit_plan_sha256)
    fits = {arm: verify_fit(fit_root, fitted, api, arm) for arm in ARMS}
    candidate = read(Path(fitted['materialroot'])/'candidate.json')
    requests = fixed_requests(api[0], candidate)
    tokenizer = api[1].native_tokenizer(fitted['model'])
    native_inputs = api[3].native_inputs(tokenizer, requests)
    plan = make_plan(root, 'readout', fitted['source_root'], fitted['module_sha256'], fitted['model'], fitted['device'],
        deadline, lease_end, fitted['main_config'], api)
    plan.update(fit_root=str(fit_root), fit_plan_sha256=fit_plan_sha256, fit_release=str(path(fit_release)),
        fit_release_sha256=fit_release_sha256, fit_receipts=fits, candidate_path=str(Path(fitted['materialroot'])/'candidate.json'),
        candidate_sha256=fitted['candidate_sha256'], requests=requests, native_inputs=native_inputs,
        calls_per_cell=128, total_calls=384, output_token_ceiling=384*64, eos_token_id=tokenizer.eos_token_id)
    plan['input_hashes'] = dict(fitted['input_hashes']) | {str(fit_root/'plan.json'): fit_plan_sha256,
        str(path(fit_release)): fit_release_sha256, str(fit_root/'run/result.json'): digest(fit_root/'run/result.json')}
    for fit in fits.values():
        plan['input_hashes'].update({str(Path(fit['adapter'])/name): pin for name, pin in fit['adapter_files'].items()
                                    if not name.endswith('.safetensors')})
    if restart_release is not None:
        plan['restart_of'] = check_restart(restart_release, restart_sha256, plan)
    require(time.time()+plan['controller_seconds'] < plan['deadline'], 'readout preparation exhausted window')
    return seal_plan(root, plan)


def make_worker_spec(root, plan, member, hard_end):
    spec = {key: plan[key] for key in ('phase', 'model', 'model_files', 'device', 'python', 'source_root',
        'source_hashes', 'module_sha256', 'sidecar_sha256')}
    spec.update(protocol=PROTOCOL, member=member, root=str(root), hard_end=hard_end, nonce=secrets.token_hex(16))
    if plan['phase'] == 'fit':
        corpus = Path(plan['materialroot'])/(member+'.json')
        spec.update(corpus=str(corpus), corpus_sha256=digest(corpus), train_config=plan['train_config'],
            audit_path=str(Path(plan['materialroot'])/'native_audit.json'),
            audit_sha256=plan['material_files']['native_audit.json'], adapter_out=str(root/'run'/member/'adapter'))
    else:
        fitted = plan['fit_receipts'].get(member)
        adapter, files = (fitted['adapter'], fitted['adapter_files']) if fitted else (None, {})
        spec.update(adapter=adapter, adapter_files=files, requests=plan['requests'], native_inputs=plan['native_inputs'],
            data=str(root/'run'/member/'data'))
    return spec


def load_native(model):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, 'prepared distinct EOS/PAD required')
    base = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.bfloat16, device_map='cuda',
        local_files_only=True, trust_remote_code=False)
    require(not hasattr(base, 'peft_config'), 'fresh base must not carry adapter')
    return tokenizer, base


def worker(spec, spec_sha256, allow_gpu=False):
    require(allow_gpu, 'Main-only worker --allow-gpu required')
    spec_path = path(spec)
    require(digest(spec_path) == spec_sha256, 'worker spec pin changed')
    spec = read(spec_path)
    require(spec['protocol'] == PROTOCOL and spec['sidecar_sha256'] == digest(SELF)
        and spec['python'] == os.path.abspath(sys.executable) and os.environ.get('CUDA_VISIBLE_DEVICES') == spec['device'],
        'worker code/interpreter/device mismatch')
    phase_keys = {'corpus', 'corpus_sha256', 'train_config', 'audit_path', 'audit_sha256', 'adapter_out'} if spec['phase'] == 'fit' else {
        'adapter', 'adapter_files', 'requests', 'native_inputs', 'data'}
    require(set(spec) == {'phase', 'model', 'model_files', 'device', 'python', 'source_root', 'source_hashes',
        'module_sha256', 'sidecar_sha256', 'protocol', 'member', 'root', 'hard_end', 'nonce'} | phase_keys, 'extra worker context/fields')
    stage = path(spec['root'])/'run'/spec['member']
    require(spec_path == stage.parent/(spec['member']+'.spec.json'), 'worker spec location mismatch')
    with owned_worker(stage/'worker', spec['hard_end']):
        verify_pins(spec['source_hashes'])
        corpus, base, trainer, capture = source_api(spec['source_root'], spec['module_sha256'])
        require(base.model_hashes(spec['model']) == spec['model_files'], 'worker base changed')
        if spec['phase'] == 'fit':
            require(spec['member'] in ARMS and digest(spec['corpus']) == spec['corpus_sha256']
                and digest(spec['audit_path']) == spec['audit_sha256'], 'fit corpus/audit changed')
            require(spec['adapter_out'] == str(stage/'adapter'), 'adapter output escaped member scope')
            tokenizer, model = load_native(spec['model'])
            items = trainer.normalize_items(read(spec['corpus']))
            expected = read(spec['audit_path'])['rows'][spec['member']]
            require(len(items) == len(expected) == 256, 'fit row count changed')
            for index, (item, saved) in enumerate(zip(items, expected, strict=True)):
                segments = trainer.encode_item_segments(item, tokenizer, 512, False, True, index, overflow='truncate')
                require(len(segments) == 1 and segments[0].ids == saved['input_ids'] and segments[0].labels == saved['labels']
                    and segments[0].context_dropped == segments[0].target_dropped == 0, 'actual fit encoding/mask changed')
            trainer.run_training(items, tokenizer, model, trainer.TrainConfig(**spec['train_config']), spec['adapter_out'],
                corpus_sha=spec['corpus_sha256'], corpus_name=Path(spec['corpus']).name)
        else:
            require(spec['phase'] == 'readout' and spec['member'] in CELLS and spec['data'] == str(stage/'data'), 'readout output/member mismatch')
            require(spec['adapter'] is None and spec['adapter_files'] == {} if spec['member'] == 'OFF' else
                bool(spec['adapter'] and spec['adapter_files']), 'OFF/ON adapter mismatch')
            require((base.tree_hashes(spec['adapter']) if spec['adapter'] else {}) == spec['adapter_files'], 'worker adapter changed')
            capture_plan = dict(spec, identity=base.expected_identity(spec, spec['adapter']))
            data = fresh(spec['data'], (spec['model'], spec['source_root']))
            data.mkdir()
            write_json(data/'isolation.json', dict(pid=os.getpid(), pgid=os.getpgrp(), parent_pid=os.getppid(),
                spec_sha256=spec_sha256, parent_calls=0, task_prefix='', online_updates=False))
            capture.capture(capture_plan, data)
        verify_pins(spec['source_hashes'])
        require(digest(spec_path) == spec_sha256 and base.model_hashes(spec['model']) == spec['model_files'], 'worker inputs changed')
    return dict(status='WORKER_COMPLETE', member=spec['member'])


def verify_fit(root, plan, api, arm):
    adapter = root/'run'/arm/'adapter'
    base, trainer = api[1:3]
    require((adapter/'DONE').is_file() and not (adapter/'EMPTY_CORPUS').exists(), 'incomplete adapter')
    manifest = read(adapter/'train_manifest.json')
    require(manifest['config'] == plan['train_config'] and manifest['recipe'] == trainer.RECIPE
        and manifest['base_model'] == plan['model'] and 'warm_start' not in manifest and 'svd_init' not in manifest
        and manifest['empty'] is False and manifest['steps'] == manifest['micro_batches'] == plan['expected_steps']
        and manifest['epochs_run'] == plan['main_config']['epochs'] and manifest['nonfinite_batches'] == 0
        and math.isfinite(manifest['final_loss']) and len(manifest['mean_loss_per_epoch']) == plan['main_config']['epochs']
        and all(math.isfinite(value) for value in manifest['mean_loss_per_epoch']), 'fit config/count/loss/freshness mismatch')
    require(manifest['corpus'] == dict(file=arm+'.json', sha256=plan['material_files'][arm+'.json'],
        n_items=256, n_encoded=256, n_skipped_no_target=0), 'fit corpus mismatch')
    require(all(manifest['tokens'][key] == value for key, value in plan['expected_tokens'][arm].items())
        and manifest['train_tokens_seen'] == plan['expected_tokens'][arm]['total']*plan['main_config']['epochs'], 'fit token exposure mismatch')
    require(read(adapter/'train_meta.json') == dict(recipe=trainer.RECIPE, n_texts=256, steps=plan['expected_steps'],
        tokens=manifest['train_tokens_seen'], rank=8, epochs=plan['main_config']['epochs'], lr=1e-4, seed=0,
        final_loss=manifest['final_loss']), 'saved train metadata join mismatch')
    require(all(manifest['truncation'][key] == 0 for key in ('items_truncated', 'context_tokens_dropped',
        'target_tokens_dropped', 'items_split', 'segments_from_splits'))
        and manifest['packing']['mode'] == 'one_item_per_sequence' and manifest['packing']['n_sequences'] == 256,
        'fit truncation/packing changed')
    saved = read(adapter/'adapter_config.json')
    require(saved['r'] == 8 and saved['lora_alpha'] == 16 and saved['lora_dropout'] == .05 and saved['bias'] == 'none'
        and saved['peft_type'] == 'LORA' and set(saved['target_modules']) == set(trainer.ALL_PROJ)
        and saved['base_model_name_or_path'] == plan['model'] and not any(saved.get(key) for key in
            ('modules_to_save', 'rank_pattern', 'alpha_pattern', 'layers_to_transform', 'use_dora', 'use_rslora', 'fan_in_fan_out')),
        'saved adapter/base/config mismatch')
    files = base.tree_hashes(adapter)
    allowed = {'DONE', 'README.md', 'adapter_config.json', 'adapter_model.safetensors', 'train_manifest.json', 'train_meta.json'}
    require(set(files) <= allowed and 'adapter_model.safetensors' in files, 'unexpected checkpoint files')
    finite = common.finite_weights(adapter/'adapter_model.safetensors', files['adapter_model.safetensors'])
    costs = read(Path(plan['materialroot'])/'native_audit.json')['group_costs']['0']
    return dict(arm=arm, adapter=str(adapter), adapter_files=files, finite_weights=finite, steps=manifest['steps'],
        tokens=manifest['tokens'], train_tokens_seen=manifest['train_tokens_seen'], final_loss=manifest['final_loss'],
        mean_loss_per_epoch=manifest['mean_loss_per_epoch'], target_tokens_seen=plan['expected_tokens'][arm]['target']*manifest['epochs_run'],
        padded_input_tokens_seen=sum(row['padded_input_tokens'] for row in costs),
        padding_tokens_seen=sum(row['padding_tokens'] for row in costs), eos_tokens_seen=sum(row['eos_tokens'] for row in costs),
        exposure_source='pinned native eight-row optimizer schedule; receipt actual processed counts cross-checked',
        initialization='fresh base one LoRA; pinned V3 freezing path, not independent full-base tensor dump')


def capture_receipt(root, plan, api, member):
    base = api[1]
    data = root/'run'/member/'data'
    fitted = plan['fit_receipts'].get(member)
    adapter, files = (fitted['adapter'], fitted['adapter_files']) if fitted else (None, {})
    identity = base.expected_identity(plan, adapter)
    require(read(data/'manifest.json')['files'] == base.tree_hashes(data, ('manifest.json',))
        and not (data/'failure.json').exists() and read(data/'backend.cleanup.json')['closed'] is True
        and read(data/'backend.cleanup.json')['error'] is None,
        'incomplete/changed native capture')
    process = read(root/'run'/member/'worker/process.json')
    supervision = read(root/'run'/member/'worker/supervision.json')
    controller = read(root/'run/controller.json')
    isolation = read(data/'isolation.json')
    ready = read(data/'backend.ready.json')
    require(isolation == dict(pid=process['pid'], pgid=process['pgid'], parent_pid=controller['pid'],
        spec_sha256=digest(root/'run'/(member+'.spec.json')), parent_calls=0, task_prefix='', online_updates=False),
        'fresh-process isolation/spec/parent join mismatch')
    require(ready['pid'] == process['pid'] and math.isfinite(ready['ready'])
        and process['started'] <= ready['ready'] <= process['started']+180, 'native load/ownership limit mismatch')
    require(read(data/'usage.json') == base.usage(data), 'saved raw usage mismatch')
    require(read(data/'identity.json') == dict(backend=identity, model_files=plan['model_files'], adapter_files=files), 'readout identity mismatch')
    expected_names = {request['call_id']+suffix for request in plan['requests'] for suffix in ('.request.json', '.response.json')}
    require({entry.name for entry in (data/'calls').iterdir()} == expected_names, 'missing/extra call pairs; no reduced panel')
    output, flags, previous = {}, {}, ready['ready']
    costs = dict(calls=0, input_tokens=0, output_tokens=0, output_token_ceiling=0, call_seconds=0.0)
    for request, native in zip(plan['requests'], plan['native_inputs'], strict=True):
        sent, received = read(data/'calls'/(request['call_id']+'.request.json')), read(data/'calls'/(request['call_id']+'.response.json'))
        response = received['response']
        require(sent['request'] == request and sent['identity'] == identity and sent['prompt_sha256'] == base.value_hash(request['prompt'])
            and received['response_sha256'] == base.value_hash(response), 'raw request/response/identity changed')
        require(math.isfinite(sent['started']) and math.isfinite(received['ended']) and previous <= sent['started'] <= received['ended']
            <= process['started']+supervision['reserved_seconds'] and received['ended']-sent['started'] <= 120, 'call clock/cap mismatch')
        previous = received['ended']
        base.validate_response(request, response)
        require(all(response[key] == native[key] for key in ('rendered_prompt', 'prompt_token_ids'))
            and len(response['output_token_ids']) <= 64, 'native input/limit changed')
        output[request['case_id']] = response['text']
        flags[request['case_id']] = dict(finish_reason=response['finish_reason'], stop_reason=response['stop_reason'],
            token_count=len(response['output_token_ids']), hit_token_limit=len(response['output_token_ids']) == 64,
            length_finish=response['finish_reason'] == 'length', tokenizer_eos_id=plan['eos_token_id'],
            tokenizer_eos_in_raw_ids=plan['eos_token_id'] in response['output_token_ids'],
            tokenizer_eos_stop_reason=response['stop_reason'] == plan['eos_token_id'])
        costs['calls'] += 1
        costs['input_tokens'] += len(response['prompt_token_ids'])
        costs['output_tokens'] += len(response['output_token_ids'])
        costs['output_token_ceiling'] += 64
        costs['call_seconds'] += received['ended']-sent['started']
    require(costs['calls'] == 128, 'full heldout panel required')
    return dict(capture_sha256=digest(data/'manifest.json'), outputs=output, flags=flags, costs=costs, identity=identity)


def verify_member(root, plan, api, member):
    stage = root/'run'/member
    process, supervision = read(stage/'worker/process.json'), read(stage/'worker/supervision.json')
    spec = root/'run'/(member+'.spec.json')
    require(process['argv'] == worker_command(plan['python'], spec, digest(spec)) and process['pid'] == process['pgid'] > 1
        and process['device'] == plan['device'] and 0 < process['timeout'] <= WORKER, 'worker command/ownership/cap mismatch')
    require(supervision['returncode'] == 0 and supervision['error'] is None and supervision['device'] == plan['device'] and
        math.isfinite(supervision['reserved_seconds']) and 0 < supervision['reserved_seconds'] <= process['timeout']+CLEANUP and
        all(supervision.get(key) is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified')),
        'worker completion/release mismatch')
    actual = read(spec)
    expected = make_worker_spec(root, plan, member, read(root/'run/controller.json')['hard_end'])
    expected['nonce'] = actual['nonce']
    require(re.fullmatch(r'[0-9a-f]{32}', actual['nonce']) and actual == expected, 'worker spec custody changed')
    return verify_fit(root, plan, api, member) if plan['phase'] == 'fit' else capture_receipt(root, plan, api, member)


def reduce_completed(root, plan, api):
    receipts = {member: verify_member(root, plan, api, member) for member in plan['members']}
    require(set(receipts) == set(plan['members']), 'capture barrier before reducers')
    if plan['phase'] == 'fit':
        return dict(optimizer_updates=sum(row['steps'] for row in receipts.values()),
            target_tokens_seen=sum(row['target_tokens_seen'] for row in receipts.values()), efficacy=None)
    corpus = api[0]
    candidate = read(plan['candidate_path'])
    scores = {cell: corpus.score_outputs(candidate, receipts[cell]['outputs'], split='dev',
        assigned_arm='DERANGED' if cell == 'DERANGED' else 'AUTH') for cell in CELLS}
    components = {}
    for cell in ARMS:
        score = scores[cell]
        operations = {name: dict(count=score['operations'][name]['own_map_strict_joint'],
            total=score['operations'][name]['total'], required=(9*score['operations'][name]['total']+9)//10)
            for name in ('PROSPECT', 'REVISE')}
        twins = {name: dict(count=value['own_map_strict_pass'], total=value['total'], required=(9*value['total']+9)//10)
            for name, value in score['twins'].items()}
        anchors = {name: dict(count=score['operations'][name]['instruction_compliant'], total=score['operations'][name]['total'],
            required=max((95*score['operations'][name]['total']+99)//100, scores['OFF']['operations'][name]['instruction_compliant']-1),
            tag_spill=score['operations'][name]['tag_spill'], allowed_tag_spill=0) for name in ('ADDITION', 'COPY')}
        components[cell] = dict(operations=operations, twins=twins, anchors=anchors)
    return dict(scores=scores, registered_component_counts=components, primary_criteria=PRIMARY,
        costs={key: sum(receipts[cell]['costs'][key] for cell in CELLS) for key in receipts['OFF']['costs']},
        flags={cell: receipts[cell]['flags'] for cell in CELLS}, automatic_L1_pass=False,
        scope='Conditional/locality birth component; not full core or existing bit-triple gym readiness')


def source_api(source, module_sha256):
    source = path(source)
    target = source/'organism_v6/birth_conditional_corpus.py'
    require(digest(target) == module_sha256, 'birth corpus module hash mismatch')
    sys.path.insert(0, str(source))
    modules = [importlib.import_module('organism_v6.'+name) for name in
        ('birth_conditional_corpus', 'rulegame_parenting_diagnostic', 'train_adapter_v3', 'fundamental_teaching_readout')]
    require(all(path(module.__file__).parent.parent == source for module in modules), 'wrong imported source snapshot')
    corpus, base, trainer, capture = modules
    require(base.REPO == source and (base.WORKER_SECONDS, base.CLEANUP_RESERVE, base.LOAD_SECONDS, base.CALL_SECONDS)
        == (600, 140, 180, 120), 'supervisor bounds/source changed')
    require(corpus.GROUP_SIZE == 8 and corpus.MAX_LEN == 512 and tuple(corpus.ARMS) == ARMS, 'birth corpus contract changed')
    return corpus, base, trainer, capture


def source_pins(source, api):
    corpus, base, trainer, capture = api
    names = set(base.sources()) | {'birth_conditional_corpus.py', 'conditional_behavior_corpus.py',
        'train_adapter_v3.py', 'fundamental_teaching_readout.py', 'model_backend.py', 'reasoning_neutral_probe.py'}
    return {str(path(source)/'organism_v6'/name): digest(path(source)/'organism_v6'/name) for name in sorted(names)}


def verify_pins(pins):
    require(isinstance(pins, dict) and pins, 'empty source pins')
    require(all(digest(name) == pin for name, pin in pins.items()), 'source/input pin changed')


def seal_plan(root, plan):
    write_json(root/'plan.json', plan)
    pin = digest(root/'plan.json')
    write_json(root/'plan.sha256.json', dict(sha256=pin))
    return dict(root=str(root), plan_sha256=pin, phase=plan['phase'], status='PREPARED_NOT_LAUNCHED')


def read_plan(root, plan_sha256):
    root = path(root)
    require(digest(root/'plan.json') == read(root/'plan.sha256.json')['sha256'] == plan_sha256, 'immutable plan pin mismatch')
    plan = read(root/'plan.json')
    require(plan['protocol'] == PROTOCOL and plan['phase'] in CAPS and plan['root'] == str(root)
        and plan['sidecar'] == str(SELF) and plan['sidecar_sha256'] == digest(SELF), 'plan protocol/root/sidecar changed')
    require(plan['python'] == os.path.abspath(sys.executable), 'concrete native interpreter changed; never resolve venv symlink')
    validate_config(plan['main_config'])
    require(plan['controller_seconds'] == plan['main_config'][plan['phase']+'_seconds']
        and plan['worker_seconds'] == WORKER and plan['cleanup_seconds'] == CLEANUP and plan['collection_seconds'] == COLLECTION
        and plan['deadline'] <= plan['lease_cutoff'] == plan['real_lease_end']-LEASE_MARGIN,
        'phase/worker/cleanup/lease bounds changed')
    require(plan['origin'] == ORIGIN and plan['claims'] == CLAIMS and plan['automatic_pass'] is False
        and plan['generation'] == GENERATION and plan['primary_criteria'] == PRIMARY
        and plan['primary_criteria_sha256'] == value_hash(PRIMARY), 'claim/generation/primary boundary changed')
    require(plan['members'] == list(ARMS if plan['phase'] == 'fit' else CELLS), 'phase member order changed')
    return root, plan


def verify_plan(root, pin, check_model=True):
    root, plan = read_plan(root, pin)
    verify_pins(plan['source_hashes'])
    verify_pins(plan['input_hashes'])
    api = source_api(plan['source_root'], plan['module_sha256'])
    require(source_pins(plan['source_root'], api) == plan['source_hashes'], 'source inventory changed')
    if check_model:
        require(api[1].model_hashes(plan['model']) == plan['model_files'], 'base model inventory changed')
    require(not (root/'prepare_failure.json').exists(), 'failed preparation is not launchable')
    if plan['phase'] == 'fit':
        material = path(plan['materialroot'])
        require(material == root/'material' and api[1].tree_hashes(material) == plan['material_files'], 'material inventory mismatch')
        candidate = read(material/'candidate.json')
        require(candidate == api[0].build_candidate(root=0) and api[0].digest(candidate) == plan['candidate_sha256']
            and read(material/'candidate_audit.json') == api[0].audit_candidate(candidate), 'authored candidate/source mismatch')
        recipe = api[0].training_recipe(learning_rate=1e-4, seed=0, epochs=plan['main_config']['epochs'])
        require(plan['recipe'] == read(material/'recipe.json') == recipe
            and plan['train_config'] == asdict(api[2].TrainConfig(**recipe, model=plan['model'])), 'native recipe mismatch')
        native = read(material/'native_audit.json')
        require(native['candidate_sha256'] == plan['candidate_sha256'] and native['recipe'] == recipe
            and native['birth_source_sha256'] == plan['module_sha256'] and native['status'] == 'NATIVE_TOKEN_MATCH_VERIFIED'
            and native['no_truncation'] is True and native['loss_bearing_padding'] is False
            and native['audited_epochs'] == recipe['epochs'] and native['updates_per_audited_seed'] == plan['expected_steps']
            == 32*recipe['epochs'] <= plan['main_config']['max_updates_per_arm'] and plan['expected_rows'] == 256,
            'native audit/count binding mismatch')
        require(all(plan['source_hashes'][str(path(plan['source_root'])/'organism_v6'/name)] == pin
            for name, pin in native['source_sha256'].items()), 'native source join mismatch')
        for arm in ARMS:
            require(read(material/(arm+'.json')) == {'corpus': native['corpora'][arm]}
                and len(native['rows'][arm]) == len(native['corpora'][arm]) == 256, 'native exported row mismatch')
            total = sum(row['input_tokens'] for row in native['rows'][arm])
            target = sum(row['target_tokens'] for row in native['rows'][arm])
            require(plan['expected_tokens'][arm] == dict(total=total, target=target, context=total-target), 'native token exposure mismatch')
    else:
        require(plan['requests'] == fixed_requests(api[0], read(plan['candidate_path'])) and plan['calls_per_cell'] == 128
            and plan['total_calls'] == 384 and plan['output_token_ceiling'] == 384*64
            and len(plan['native_inputs']) == 128 and type(plan['eos_token_id']) is int, 'readout panel/cap mismatch')
        for request, native in zip(plan['requests'], plan['native_inputs'], strict=True):
            require(native['call_id'] == request['call_id'] and native['prompt_token_ids'] and
                len(native['prompt_token_ids'])+64 <= api[1].MAX_MODEL_LEN, 'native request token binding mismatch')
        for arm in ARMS:
            require(api[1].tree_hashes(plan['fit_receipts'][arm]['adapter']) == plan['fit_receipts'][arm]['adapter_files'],
                'prepared adapter changed')
    return root, plan, api


@contextmanager
def work_window(hard_end):
    require(threading.current_thread() is threading.main_thread() and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0),
        'exclusive main-thread timer required')
    remaining = hard_end-time.time()-CLEANUP
    require(remaining > 0, 'cleanup reserve exhausted')
    previous = {number: signal.getsignal(number) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    def interrupted(number, frame):
        raise TimeoutError('owned controller interrupted or work window exhausted')
    for number in previous:
        signal.signal(number, interrupted)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for number, handler in previous.items():
            signal.signal(number, handler)


@contextmanager
def supervisor_window(hard_end):
    signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        yield
    finally:
        remaining = hard_end-time.time()-CLEANUP
        if remaining > 0:
            signal.setitimer(signal.ITIMER_REAL, remaining)


def process_identity(pid):
    source = Path('/proc')/str(pid)
    fields = (source/'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, ppid=int(fields[1]), pgid=int(fields[2]), session=int(fields[3]), start_ticks=int(fields[19]),
        argv=[part.decode() for part in (source/'cmdline').read_bytes().split(b'\0') if part])


@contextmanager
def owned_worker(stage, hard_end):
    until = time.monotonic()+5
    while not (stage/'process.json').exists() and time.monotonic() < until:
        time.sleep(.05)
    receipt = read(stage/'process.json')
    require(receipt['pid'] == receipt['pgid'] == os.getpid() == os.getpgrp() == os.getsid(0), 'fresh owned worker session required')
    parent, stop = os.getppid(), threading.Event()
    require(parent > 1, 'live supervisor parent required')
    def watch():
        while not stop.wait(.2):
            if os.getppid() != parent or time.time() >= hard_end-10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return
    def interrupted(number, frame):
        raise RuntimeError('owned worker interrupted')
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        yield
    finally:
        stop.set()
        watcher.join(timeout=1)
        for number, handler in handlers.items():
            signal.signal(number, handler)


def controller_command(root, pin, phase, python=None):
    return [python or os.path.abspath(sys.executable), '-B', str(SELF), phase, '--root', str(root),
            '--plan-sha256', pin, '--allow-gpu']


def worker_command(python, spec, pin):
    return [python, '-B', str(SELF), '_worker', '--spec', str(spec), '--spec-sha256', pin, '--allow-gpu']


def status(root, plan_sha256, launch_root=None, launch_sha256=None):
    root, plan = read_plan(root, plan_sha256)
    controller_path = root/'run/controller.json'
    controller = read(controller_path) if controller_path.exists() else None
    owned, launch = set(), None
    if launch_root is not None:
        require(launch_sha256 is not None and digest(path(launch_root)/'launch.json') == launch_sha256, 'launch pin mismatch')
        launch = read(path(launch_root)/'launch.json')
        require(launch['root'] == str(root) and launch['plan_sha256'] == plan_sha256 and
            launch['driver_sha256'] == plan['sidecar_sha256'] and type(launch['pid']) is int and launch['pid'] > 1,
            'launch ownership/plan mismatch')
        owned.add(launch['pid'])
        require(launch['pid'] == launch['pgid'] == launch['session'] and type(launch['launcher_pid']) is int
            and launch['launcher_pid'] > 1 and launch['launcher_pid'] != launch['pid']
            and launch['launcher_pid'] == launch['launcher_pgid'] == launch['launcher_session'], 'isolated launcher/controller scopes required')
        owned.add(launch['launcher_pid'])
    if controller is not None:
        require(controller['plan_sha256'] == plan_sha256 and controller['pid'] == controller['pgid'] == controller['session']
            and controller['pid'] > 1 and (launch is None or launch['pid'] == controller['pid']), 'controller identity mismatch')
        owned.add(controller['pid'])
    expected = {root/'run'/member/'worker/process.json' for member in plan['members']}
    require(set(root.glob('**/process.json')) <= expected, 'unexpected process receipt')
    for receipt in expected:
        if path(receipt).exists():
            process = read(receipt)
            require(type(process['pid']) is int and process['pid'] == process['pgid'] > 1 and process['pid'] not in owned,
                'worker ownership/PID reuse')
            owned.add(process['pid'])
    snapshot = common.process_snapshot()
    descendants = set(owned)
    while True:
        extended = descendants | {row['pid'] for row in snapshot if row['ppid'] in descendants}
        if extended == descendants:
            break
        descendants = extended
    live = [row for row in snapshot if row['pid'] in descendants or any(row[key] in owned for key in ('pgid', 'session'))]
    markers = {name: path(root/'run'/name).is_file() for name in ('result.json', 'failure.json')}
    return dict(phase=plan['phase'], ready=not live and sum(markers.values()) == 1, owned_ids=sorted(owned),
        live_owned=live, terminal_markers=markers, terminal_bodies_read=False, launch=launch)


def stop(root, plan_sha256):
    root, plan = read_plan(root, plan_sha256)
    before = status(root, plan_sha256)
    if not before['live_owned']:
        return dict(status='NO_LIVE_OWNED_SCOPE', full_release=False, collection_required=True)
    controller = read(root/'run/controller.json')
    actual = process_identity(controller['pid'])
    require(all(actual[key] == controller[key] for key in ('pid', 'pgid', 'session', 'start_ticks'))
        and actual['argv'] == controller_command(root, plan_sha256, plan['phase'], plan['python']),
        'refuse signalling mismatched/reused controller')
    write_json(root/'run/stop.request.json', dict(pid=actual['pid'], start_ticks=actual['start_ticks'],
        plan_sha256=plan_sha256, requested_wall=time.time(), signal='SIGTERM', retry=False))
    os.kill(actual['pid'], signal.SIGTERM)
    until = time.monotonic()+CLEANUP
    while time.monotonic() < until:
        observed = status(root, plan_sha256)
        if not observed['live_owned']:
            return dict(status='OWNED_SCOPE_STOPPED', full_release=False, collection_required=True)
        time.sleep(.1)
    raise TimeoutError('owned stop not verified within140s; retain reservation, no restart')


def supervise_member(root, plan, api, member, spec, spec_sha256, hard_end):
    base = api[1]
    stage = root/'run'/member
    command = worker_command(plan['python'], spec, spec_sha256)
    with supervisor_window(hard_end):
        receipt = base.supervise(stage, dict(model=plan['model'], device=plan['device'], lease_end=hard_end),
            stage/'worker', command, stage/'data/calls' if plan['phase'] == 'readout' else None)
    require(all(receipt.get(key) is True for key in ('ok', 'reservation_release_verified', 'owned_group_empty', 'gpu_processes_absent')),
        'worker failed or cleanup unverified')
    return receipt


def run_controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, 'Main-only allocation and --allow-gpu required')
    started, wall = time.monotonic(), time.time()
    root, preliminary = read_plan(root, plan_sha256)
    hard_end = min(wall+preliminary['controller_seconds'], preliminary['deadline'], preliminary['lease_cutoff'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == preliminary['device'], 'continuous Main device reservation required')
    require(os.getpid() == os.getpgrp() == os.getsid(0), 'Main must launch a fresh controller session')
    run = fresh(root/'run')
    run.mkdir()
    completed = {}
    try:
        with work_window(hard_end):
            root, plan, api = verify_plan(root, plan_sha256)
            identity = process_identity(os.getpid())
            write_json(run/'controller.json', dict(identity, plan_sha256=plan_sha256, started_wall=wall,
                started_monotonic=started, hard_end=hard_end, cleanup_reserve=CLEANUP, continuous_reservation=True))
            for member in plan['members']:
                require(time.time() < hard_end-CLEANUP, 'no remaining work window')
                verify_plan(root, plan_sha256)
                stage = run/member
                stage.mkdir()
                spec = make_worker_spec(root, plan, member, hard_end)
                spec_path = run/(member+'.spec.json')
                write_json(spec_path, spec)
                spec_pin = digest(spec_path)
                supervision = supervise_member(root, plan, api, member, spec_path, spec_pin, hard_end)
                receipt = verify_member(root, plan, api, member)
                write_json(stage/'receipt.json', receipt)
                completed[member] = dict(receipt_sha256=digest(stage/'receipt.json'),
                    spec_sha256=spec_pin, supervision_sha256=digest(stage/'worker/supervision.json'))
            require(set(completed) == set(plan['members']), 'all-member barrier incomplete')
            verify_plan(root, plan_sha256)
            for member in plan['members']:
                require(read(run/member/'receipt.json') == verify_member(root, plan, api, member), 'earlier member changed')
            aggregate = reduce_completed(root, plan, api)
        require(time.monotonic()-started <= preliminary['controller_seconds'] and time.time() <= hard_end, 'inclusive phase cap exceeded')
        result = dict(status='COMPLETE', phase=plan['phase'], members=completed, aggregate=aggregate,
            controller_seconds=time.monotonic()-started, ended_wall=time.time(), plan_sha256=plan_sha256,
            automatic_pass=False, origin=ORIGIN, claims=CLAIMS)
        write_json(run/'result.json', result)
        return result
    except BaseException as error:
        write_json(run/'failure.json', dict(status='FAILED_PARTIAL', completed=list(completed), aggregate=None,
            error_type=type(error).__name__, controller_seconds=time.monotonic()-started, retry=False))
        raise


def audit_terminal(root, plan, api, pin):
    run = root/'run'
    success = (run/'result.json').is_file()
    require(success != (run/'failure.json').is_file(), 'one unambiguous terminal required')
    controller = read(run/'controller.json') if (run/'controller.json').exists() else None
    terminal = read(run/('result.json' if success else 'failure.json'))
    require(math.isfinite(terminal['controller_seconds']) and terminal['controller_seconds'] >= 0, 'invalid controller clock')
    if not success:
        require(terminal['status'] == 'FAILED_PARTIAL' and terminal['aggregate'] is None and terminal['retry'] is False,
            'failed phase must remain incomplete')
        return dict(phase_complete=False, failure=terminal, aggregate=None, native_replay=False, reducers_run=False)
    require(controller is not None and terminal['status'] == 'COMPLETE' and terminal['phase'] == plan['phase']
        and terminal['plan_sha256'] == pin and terminal['automatic_pass'] is False and terminal['origin'] == ORIGIN
        and terminal['claims'] == CLAIMS and set(terminal['members']) == set(plan['members'])
        and 0 < terminal['controller_seconds'] <= plan['controller_seconds']
        and controller['started_wall'] <= terminal['ended_wall'] <= controller['hard_end']
        and controller['hard_end'] <= min(controller['started_wall']+plan['controller_seconds'], plan['deadline'], plan['lease_cutoff']),
        'complete terminal phase/cost/member mismatch')
    previous_end, pids, nonces = controller['started_monotonic'], {controller['pid']}, set()
    for member in plan['members']:
        stage = run/member
        spec, process, supervision = read(run/(member+'.spec.json')), read(stage/'worker/process.json'), read(stage/'worker/supervision.json')
        require(process['pid'] not in pids and spec['nonce'] not in nonces and math.isfinite(process['started'])
            and previous_end <= process['started'] and process['started']+supervision['reserved_seconds']
            <= controller['started_monotonic']+terminal['controller_seconds'], 'distinct sequential owned windows required')
        pids.add(process['pid'])
        nonces.add(spec['nonce'])
        previous_end = process['started']+supervision['reserved_seconds']
        require(terminal['members'][member] == dict(receipt_sha256=digest(stage/'receipt.json'),
            spec_sha256=digest(run/(member+'.spec.json')), supervision_sha256=digest(stage/'worker/supervision.json')),
            'terminal/member custody join changed')
        require(read(stage/'receipt.json') == verify_member(root, plan, api, member), 'saved member receipt changed')
    aggregate = reduce_completed(root, plan, api)
    require(terminal['aggregate'] == aggregate, 'saved aggregate mismatch')
    return dict(phase_complete=True, aggregate=aggregate, controller_seconds=terminal['controller_seconds'],
        native_replay=False, all_members_before_reducers=True, automatic_L1_pass=False)


def launch_contract(root, plan, pin, launcher, launcher_sha256):
    require(digest(launcher) == launcher_sha256, 'reviewed launcher pin mismatch')
    return dict(protocol=PROTOCOL, phase=plan['phase'], root=str(root), plan_sha256=pin,
        driver_sha256=plan['sidecar_sha256'], launcher=str(path(launcher)), launcher_sha256=launcher_sha256,
        command=controller_command(root, pin, plan['phase'], plan['python']), device=plan['device'],
        controller_seconds=plan['controller_seconds'], continuous_reservation=True)


def validate_launch(root, plan, pin, logs, launch_pin, launcher, launcher_pin):
    require(digest(logs/'launch.json') == launch_pin, 'launcher receipt changed')
    launch = read(logs/'launch.json')
    expected = launch_contract(root, plan, pin, launcher, launcher_pin)
    require(all(launch.get(key) == value for key, value in expected.items()), 'launcher/source/command/cap binding mismatch')
    require(set(launch) == set(expected) | {'pid', 'pgid', 'session', 'launcher_pid', 'launcher_pgid', 'launcher_session',
        'started_wall', 'gpu_uuid'} and math.isfinite(launch['started_wall']) and launch['started_wall'] <= time.time(),
        'launcher exact fields/clock mismatch')
    finished = read(logs/'exit.json')
    require(set(finished) == {'launch_sha256', 'returncode', 'ended_wall'} and finished['launch_sha256'] == launch_pin
        and type(finished['returncode']) is int and math.isfinite(finished['ended_wall'])
        and launch['started_wall'] <= finished['ended_wall'] <= time.time(), 'launcher exit binding mismatch')
    if (root/'run/controller.json').exists():
        controller = read(root/'run/controller.json')
        require(all(controller[key] == launch[key] for key in ('pid', 'pgid', 'session'))
            and controller['argv'] == expected['command'] and launch['started_wall'] <= controller['started_wall']
            <= finished['ended_wall'], 'actual controller launcher join mismatch')
    require((finished['returncode'] == 0) == (root/'run/result.json').exists(), 'launcher returncode/terminal mismatch')
    return launch, finished


def allowed_files(plan):
    names = {'plan.json', 'plan.sha256.json', 'preparation.started.json', 'prepare_failure.json', 'collection.claim.json',
        'run/controller.json', 'run/result.json', 'run/failure.json', 'run/stop.request.json'}
    weights = set()
    if plan['phase'] == 'fit':
        names.update('material/'+name for name in plan['material_files'])
    for member in plan['members']:
        names.add('run/'+member+'.spec.json')
        prefix = 'run/'+member+'/'
        names.update(prefix+name for name in ('receipt.json', 'worker/process.json', 'worker/supervision.json', 'worker/stdout.log'))
        if plan['phase'] == 'fit':
            names.update(prefix+'adapter/'+name for name in ('DONE', 'README.md', 'adapter_config.json',
                'adapter_model.safetensors', 'train_manifest.json', 'train_meta.json'))
            weights.add(prefix+'adapter/adapter_model.safetensors')
        else:
            names.update(prefix+'data/'+name for name in ('isolation.json', 'identity.json', 'backend.ready.json',
                'backend.cleanup.json', 'usage.json', 'manifest.json', 'failure.json'))
            names.update(prefix+'data/calls/'+request['call_id']+suffix for request in plan['requests']
                for suffix in ('.request.json', '.response.json'))
    return names, weights


def inventory(root, plan, logs):
    allowed, weights = allowed_files(plan)
    files, hashes, excluded, total, count = {}, {}, {}, 0, 0
    for directory, prefix, permitted in ((root, 'run', allowed),
        (logs, 'launch', {'launch.json', 'exit.json', 'gpu.xml', 'controller.log', 'launcher.log'})):
        folders = {str(parent) for name in permitted for parent in PurePosixPath(name).parents if str(parent) != '.'}
        def inaccessible(error):
            raise error
        for current, children, names in os.walk(directory, followlinks=False, onerror=inaccessible):
            for name in children+names:
                count += 1
                require(count <= 2048, 'too many metadata entries')
                item = path(Path(current)/name)
                relative = item.relative_to(directory).as_posix()
                if name in children:
                    require(relative in folders and item.is_dir(), 'unknown artifact directory')
                    continue
                require(relative in permitted, 'unknown file rejected: '+relative)
                archive_name = 'metadata/'+prefix+'/'+relative
                if prefix == 'run' and relative in weights:
                    excluded[archive_name] = dict(sha256=common.file_hash(item), bytes=item.stat().st_size,
                        archived=False, reason='adapter bytes deliberately excluded; no weights-in-capsule promise')
                    continue
                data = raw(item)
                common.scan_text(data, archive_name)
                total += len(data)
                require(total <= 256*1024*1024, 'metadata total limit')
                files[archive_name], hashes[archive_name] = item, hashlib.sha256(data).hexdigest()
    return files, hashes, excluded


def vacancy(plan, expected_uuid):
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'collect with CUDA_VISIBLE_DEVICES unset')
    checker = load_file(path(plan['source_root'])/'gpu/astra_mini_sudoku_diagnostic.py', CHECK_SHA, 'birth_release_vacancy')
    gpu, xml = checker.check_free(plan['device'])
    common.check_uuid(gpu, xml, expected_uuid)
    return gpu, xml


@contextmanager
def collection_window():
    require(threading.current_thread() is threading.main_thread() and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0),
        'exclusive300s collector main thread required')
    def expired(number, frame):
        raise TimeoutError('300s collection limit; preserve attempt, no blind retry')
    previous = {number: signal.signal(number, expired) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    signal.setitimer(signal.ITIMER_REAL, COLLECTION)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for number, handler in previous.items():
            signal.signal(number, handler)


def collect(root, plan_sha256, launch_root, launch_sha256, launcher, launcher_sha256, out):
    started, wall = time.monotonic(), time.time()
    root, logs = path(root), path(launch_root)
    output = fresh(out, (root, logs, SELF, launcher))
    require(output.parent == root.parent == logs.parent, 'separate sibling collection/launch roots required')
    require('CUDA_VISIBLE_DEVICES' not in os.environ, 'collect with reservation environment unset after launcher exits')
    output.mkdir(mode=0o700)
    try:
        with collection_window():
            write_json(output/'started.json', dict(root=str(root), plan_sha256=plan_sha256, started_wall=wall,
                collector_sha256=digest(SELF), collection_seconds=COLLECTION, retry=False))
            write_json(root/'collection.claim.json', dict(output=str(output), collector_sha256=digest(SELF), started_wall=wall))
            observed = status(root, plan_sha256, logs, launch_sha256)
            require(observed['ready'], 'whole owned launcher/controller/worker/session exit before reading results')
            root, plan, api = verify_plan(root, plan_sha256)
            launch, finished = validate_launch(root, plan, plan_sha256, logs, launch_sha256, launcher, launcher_sha256)
            gpu, xml = vacancy(plan, launch['gpu_uuid'])
            write_new(output/'initial_vacancy.xml', xml.encode())
            files, hashes, excluded = inventory(root, plan, logs)
            evidence = audit_terminal(root, plan, api, plan_sha256)
            require(time.time() <= plan['lease_cutoff'], 'six-hour lease cutoff passed; no accepted release')
            report = dict(protocol=PROTOCOL, phase=plan['phase'], root=str(root), plan_sha256=plan_sha256,
                evidence=evidence, excluded_weights=excluded, initial_vacancy=gpu, launcher_exit=finished,
                origin=ORIGIN, claims=CLAIMS, cost_scope='worker/load/call/training are nested in controller, not additive',
                output_policy='metadata and raw responses only; adapter bytes excluded')
            write_json(output/'audit.json', report)
            for name in ('started.json', 'initial_vacancy.xml', 'audit.json'):
                item = output/name
                common.scan_text(raw(item), name)
                files['metadata/collection/'+name], hashes['metadata/collection/'+name] = item, digest(item)
            evidence_hashes = {str(item): hashes[name] for name, item in files.items()}
            archive = output/'capsule.tgz'
            archive_pin = common.pack(archive, files, hashes)
            require(status(root, plan_sha256, logs, launch_sha256)['ready'], 'owned process/session reappeared')
            final_gpu, final_xml = vacancy(plan, launch['gpu_uuid'])
            write_new(output/'final_vacancy.xml', final_xml.encode())
            verify_pins(evidence_hashes)
            require(inventory(root, plan, logs)[2] == excluded, 'excluded weights changed during collection')
            verify_pins(plan['source_hashes'])
            previous = 0.0
            if plan['phase'] == 'readout':
                fitted = read(path(plan['fit_root'])/'plan.json')
                prior = accepted_release(plan['fit_release'], plan['fit_release_sha256'], fitted, plan['fit_plan_sha256'])
                require(prior['phase_complete'] is True and prior['released_wall'] <= launch['started_wall'],
                    'fit release must precede fresh readout launch')
                previous = prior['launch_to_release_seconds']
            require(common.file_hash(archive) == archive_pin, 'archive changed at final release')
            released, duration = time.time(), time.monotonic()-started
            full = released-launch['started_wall']
            require(0 <= duration <= COLLECTION and 0 <= full <= plan['controller_seconds']+COLLECTION
                and full+previous <= 5100 and released <= plan['lease_cutoff'], 'inclusive phase/pair/collection/lease bound exceeded')
            validation = dict(protocol=PROTOCOL, status='COLLECTED_RELEASED', phase=plan['phase'], root=str(root),
                output=str(output), plan_sha256=plan_sha256, collector_sha256=digest(SELF),
                phase_complete=evidence['phase_complete'], full_release=True, final_vacancy=final_gpu,
                final_vacancy_sha256=digest(output/'final_vacancy.xml'), archive=str(archive), archive_sha256=archive_pin,
                archive_files=hashes, evidence_hashes=evidence_hashes, released_wall=released,
                collection_seconds=duration, launch_to_release_seconds=full, paired_launch_to_release_seconds=full+previous,
                costs_nested_not_added=True, no_native_replay=True, automatic_L1_pass=False,
                launcher=str(path(launcher)), launcher_sha256=launcher_sha256, origin=ORIGIN, claims=CLAIMS)
            write_json(output/'validation.json', validation)
            return dict(validation=str(output/'validation.json'), validation_sha256=digest(output/'validation.json'),
                archive=str(archive), archive_sha256=archive_pin, phase_complete=validation['phase_complete'])
    except BaseException as error:
        if not (output/'collection_failure.json').exists():
            write_json(output/'collection_failure.json', dict(error_type=type(error).__name__, error=str(error),
                retry=False, accepted_release=False, elapsed_seconds=time.monotonic()-started,
                partial_capsule_preserved=(output/'capsule.tgz').exists()))
        raise


def accepted_release(release, release_sha256, plan, plan_sha256):
    release = path(release)
    require(release.name == 'validation.json' and digest(release) == release_sha256, 'release pin mismatch')
    receipt = read(release)
    require(receipt['protocol'] == PROTOCOL and receipt['status'] == 'COLLECTED_RELEASED'
        and receipt['phase'] == plan['phase'] and receipt['root'] == plan['root'] and receipt['plan_sha256'] == plan_sha256
        and receipt['collector_sha256'] == digest(SELF) and receipt['full_release'] is True and receipt['automatic_L1_pass'] is False
        and receipt['output'] == str(release.parent) and not (release.parent/'collection_failure.json').exists(),
        'release protocol/phase/custody mismatch')
    require(receipt['archive'] == str(release.parent/'capsule.tgz')
        and common.file_hash(path(receipt['archive'])) == receipt['archive_sha256']
        and digest(release.parent/'final_vacancy.xml') == receipt['final_vacancy_sha256'], 'release archive/vacancy changed')
    common.validate_archive(path(receipt['archive']), receipt['archive_files'])
    common.check_uuid(receipt['final_vacancy'], raw(release.parent/'final_vacancy.xml').decode(), receipt['final_vacancy']['gpu_uuid'])
    verify_pins(receipt['evidence_hashes'])
    require(0 <= receipt['collection_seconds'] <= COLLECTION and 0 <= receipt['launch_to_release_seconds']
        <= plan['controller_seconds']+COLLECTION and receipt['paired_launch_to_release_seconds'] <= 5100,
        'release phase cost invalid')
    return receipt


def check_restart(release, release_sha256, plan):
    require(release_sha256 is not None, 'restart requires exact prior release pin')
    previous = read(path(release))
    old_root, old = read_plan(previous['root'], previous['plan_sha256'])
    receipt = accepted_release(release, release_sha256, old, previous['plan_sha256'])
    require(receipt['phase_complete'] is False and old['phase'] == plan['phase'] and str(old_root) != plan['root'],
        'only explicit fresh-root failed-phase restart allowed; no favorable rerun')
    for key in ('model', 'model_files', 'module_sha256', 'source_hashes', 'main_config', 'primary_criteria', 'candidate_sha256', 'device'):
        require(old[key] == plan[key], 'restart material/config changed')
    return dict(root=str(old_root), plan_sha256=previous['plan_sha256'], release=str(path(release)),
        release_sha256=release_sha256, prior_cost_seconds=receipt['launch_to_release_seconds'], automatic_retry=False)


def collection_command(root, pin, launch_root, launch_pin, launcher, launcher_pin, out, python=None):
    return [python or os.path.abspath(sys.executable), '-B', str(SELF), 'collect', '--root', str(root), '--plan-sha256', pin,
        '--launch-root', str(launch_root), '--launch-sha256', launch_pin, '--launcher', str(launcher),
        '--launcher-sha256', launcher_pin, '--out', str(out)]


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare-fit')
    for name in ('source', 'module-sha256', 'model', 'out', 'device', 'deadline', 'lease-end'):
        prepare.add_argument('--'+name, required=True)
    prepare.add_argument('--config', help='Main-authored complete fixed configuration JSON')
    prepare.add_argument('--restart-release')
    prepare.add_argument('--restart-sha256')
    prepare = commands.add_parser('prepare-readout')
    for name in ('fit-root', 'fit-plan-sha256', 'fit-release', 'fit-release-sha256', 'out', 'deadline', 'lease-end'):
        prepare.add_argument('--'+name, required=True)
    prepare.add_argument('--restart-release')
    prepare.add_argument('--restart-sha256')
    for phase in ('fit', 'readout', 'status', 'stop', 'collect'):
        command = commands.add_parser(phase)
        command.add_argument('--root', required=True)
        command.add_argument('--plan-sha256', required=True)
        if phase in CAPS:
            command.add_argument('--allow-gpu', action='store_true')
        if phase in ('collect', 'status'):
            command.add_argument('--launch-root', required=phase == 'collect')
            command.add_argument('--launch-sha256', required=phase == 'collect')
        if phase == 'collect':
            for name in ('launcher', 'launcher-sha256', 'out'):
                command.add_argument('--'+name, required=True)
    child = commands.add_parser('_worker')
    child.add_argument('--spec', required=True)
    child.add_argument('--spec-sha256', required=True)
    child.add_argument('--allow-gpu', action='store_true')
    return parser


def main(argv=None):
    args = vars(build_parser().parse_args(argv))
    command = args.pop('command')
    if command == 'prepare-fit':
        if args['config'] is not None:
            args['config'] = read(path(args['config']))
        result = prepare_fit(**args)
    elif command == 'prepare-readout':
        result = prepare_readout(**args)
    elif command in CAPS:
        require(read_plan(args['root'], args['plan_sha256'])[1]['phase'] == command, 'wrong explicit phase command')
        result = run_controller(**args)
    else:
        result = {'status': status, 'stop': stop, 'collect': collect, '_worker': worker}[command](**args)
    print(encoded(result).decode(), end='')
    return result


if __name__ == '__main__':
    main()
