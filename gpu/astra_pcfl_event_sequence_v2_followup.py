"""Standalone prepare/run helper; native runtime stays in the immutable source root.

Invoke by script path, not -m from a different checkout. CPU tests inject an
explicitly nonnative runtime; they are not acquisition or GPU evidence.
"""

import argparse
import ast
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

SOURCE = Path('/tmp/astra_pcfl_sequence_v2_source_20260913_attempt2')
REPAIR_SOURCE = Path('/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix4')
PHASES = ('B200_NEW_DOSE', 'B400_FIXED_WORK', 'REPLAY400', 'CLEAN_CUM600')
COUNTS = dict(fits=4, updates=1600, presentations=6400, calls=64,
              initial_updates=200, total_updates=1800)
SCHEMA = 'pcfl.event_sequence.v2.followup.v1'
REPAIR_SCOPE = 'warm_receipt_and_readonly_predecessor_split'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked(binding):
    require(pin(binding['path']) == binding, 'file/source pin drift')
    return json.loads(Path(binding['path']).read_bytes())


def validate_repair(original, replacement, *, outer=False):
    texts = [Path(path).read_text() for path in (original, replacement)]
    trees = [ast.parse(text) for text in texts]
    functions = [{node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)} for tree in trees]
    allowed = ('_inputs', 'controller') if outer else ('validate_warm_tensors', 'validate_predecessor', 'run_phase')
    for tree in trees:
        for name in allowed:
            require(sum(isinstance(node, ast.FunctionDef) and node.name == name for node in tree.body) == 1,
                    'exact scoped functions required')
    if outer:
        require(ast.get_source_segment(texts[0], functions[0]['_inputs'])
                == ast.get_source_segment(texts[1], functions[1]['_inputs']), 'read-only _inputs bytes changed')
        wrappers = [node for node in trees[1].body if isinstance(node, ast.FunctionDef) and node.name == '_inputs_for_write']
        require(len(wrappers) == 1 and '_inputs_for_write' not in functions[0], 'exact new outer write wrapper required')
        expected = ast.parse('''def _inputs_for_write(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, *, stage="fit", state=None, output=None):
    inputs, allocation, material = _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256,
                                         outer_sha256, phase, deadline, stage=stage, state=state, output=output)
    if stage == "fit":
        config = fit.sequence.training_config(phase, inputs["model_path"], learner_seed=inputs["learner_seed"], device="cuda")
        fit.validate_predecessor_for_write(inputs, material, phase, output, config, "NATIVE")
    return inputs, allocation, material
''').body[0]
        require(ast.dump(wrappers[0]) == ast.dump(expected), 'outer write wrapper differs from exact boundary')
        trees[1].body.remove(wrappers[0])
        calls = sorted((node for node in ast.walk(functions[1]['controller']) if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name) and node.func.id in ('_inputs', '_inputs_for_write')),
                       key=lambda node: (node.lineno, node.col_offset))
        require([node.func.id for node in calls] == ['_inputs_for_write', '_inputs_for_write', '_inputs'],
                'only first two controller prefit calls may change; postflight must stay read-only')
        for node in calls[:2]:
            node.func.id = '_inputs'
        require(ast.dump(trees[0]) == ast.dump(trees[1]), 'repair changed code outside explicit AST boundaries')
        return
    if not outer:
        wrappers = [node for node in trees[1].body if isinstance(node, ast.FunctionDef)
                    and node.name == 'validate_predecessor_for_write']
        require(len(wrappers) == 1 and 'validate_predecessor_for_write' not in functions[0], 'exact new write wrapper required')
        wrapper = wrappers[0]
        if isinstance(wrapper.body[0], ast.Expr) and isinstance(wrapper.body[0].value, ast.Constant) and isinstance(wrapper.body[0].value.value, str):
            wrapper.body.pop(0)
        expected = ast.parse('''def validate_predecessor_for_write(inputs, material, phase, root, config, kind):
    parent, prior, before = validate_predecessor(inputs, material, phase, root, config, kind)
    if parent is not None:
        v3._warm_parent(parent, root / "checkpoint", config)
    return parent, prior, before
''').body[0]
        require(ast.dump(wrapper) == ast.dump(expected), 'write wrapper differs from exact boundary')
        trees[1].body.remove(wrapper)
        require(not any(isinstance(node, ast.Attribute) and node.attr == '_warm_parent'
                        or isinstance(node, ast.Name) and node.id == '_warm_parent'
                        for node in ast.walk(functions[1]['validate_predecessor'])),
                'read-only predecessor must not call warm preparation')
        for mapping in functions:
            for name in ('validate_warm_tensors', 'validate_predecessor'):
                mapping[name].body = [ast.Pass()]
    caller = functions[1]['run_phase']
    calls = [node.func for node in ast.walk(caller) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'validate_predecessor_for_write']
    require(len(calls) == 1, 'exact single prefit call rename required')
    calls[0].id = 'validate_predecessor'
    require(ast.dump(trees[0]) == ast.dump(trees[1]), 'repair changed code outside explicit AST boundaries')


def load_runtime(source_root):
    root = Path(source_root)
    require(root in (SOURCE, REPAIR_SOURCE) and root.resolve() == root and root.is_dir(), 'explicit immutable source root required')
    repair = None
    if root == REPAIR_SOURCE:
        receipt = pin(root / 'warm_repair.json')
        repair = checked(receipt)
        require(repair['schema'] == 'pcfl.event_sequence.v2.warm_repair.v1'
                and repair['original_root'] == str(SOURCE) and repair['source_root'] == str(root), 'repair root identity')
        relative = 'gpu/astra_pcfl_event_sequence_v2_fit.py'
        outer_relative = 'gpu/astra_pcfl_event_sequence_v2_outer.py'
        require(repair['original'] == pin(SOURCE / relative)
                and repair['replacement'] == pin(root / relative), 'repair source identity')
        require(repair['scope'] == REPAIR_SCOPE, 'validation-only repair required')
        validate_repair(repair['original']['path'], repair['replacement']['path'])
        require(repair['outer_original'] == pin(SOURCE / outer_relative)
                and repair['outer_replacement'] == pin(root / outer_relative), 'outer replacement identity')
        validate_repair(repair['outer_original']['path'], repair['outer_replacement']['path'], outer=True)
        require(repair['original_modified'] is False and repair['material_reexported'] is False,
                'immutable acquisition required')
        inventory = {str(path.relative_to(SOURCE)): pin(path) for path in SOURCE.rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts}
        require(repair['original_inventory'] == inventory, 'original inventory drift')
        for path in SOURCE.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.relative_to(SOURCE).as_posix() not in (relative, outer_relative):
                alias = root / path.relative_to(SOURCE)
                require(alias.is_symlink() and alias.resolve() == path.resolve(), 'immutable source alias mismatch')
        repair = {**repair, 'receipt': receipt}
    sys.dont_write_bytecode = True
    for name, module in tuple(sys.modules.items()):
        if name.split('.')[0] in ('gpu', 'organism_v6') and getattr(module, '__file__', None):
            require(Path(module.__file__).resolve().is_relative_to(SOURCE)
                    or (repair is not None and str(Path(module.__file__).resolve()) in (repair['replacement']['path'], repair['outer_replacement']['path'])),
                    'preloaded runtime source mismatch; use standalone script')
    sys.path.insert(0, str(root))
    runtime = SimpleNamespace(**{name: importlib.import_module('gpu.astra_pcfl_event_sequence_v2_' + name)
                                 for name in ('fit', 'readout', 'outer', 'acquisition', 'campaign')})
    for module in vars(runtime).values():
        require(Path(module.__file__).resolve().is_relative_to(SOURCE)
                or (repair is not None and str(Path(module.__file__).resolve()) in (repair['replacement']['path'], repair['outer_replacement']['path'])), 'runtime source mismatch')
    if repair is not None:
        require(Path(runtime.fit.__file__).resolve() == Path(repair['replacement']['path']), 'patched fit was not loaded')
        require(Path(runtime.outer.__file__).resolve() == Path(repair['outer_replacement']['path']), 'patched outer was not loaded')
    runtime.repair = repair
    return runtime


def original_sources(sources, runtime):
    repair = getattr(runtime, 'repair', None)
    if repair is None:
        return sources
    original, replacement = repair['original'], repair['replacement']
    require(sources.get(replacement['path']) == replacement['sha256'] and original['path'] not in sources,
            'exact single repaired source required')
    result = {**{path: checksum for path, checksum in sources.items() if path != replacement['path']},
              original['path']: original['sha256']}
    outer_original, outer_replacement = repair['outer_original'], repair['outer_replacement']
    require(outer_original['path'] not in result, 'ambiguous outer source')
    if outer_replacement['path'] in result:
        require(result.pop(outer_replacement['path']) == outer_replacement['sha256'], 'outer source drift')
        result[outer_original['path']] = outer_original['sha256']
    return result


def budget(initial, started, allocation):
    require(7200 - initial - (time.monotonic() - started) >= 1800, 'budget lacks full 30min stage cap')
    require(time.time() + 1800 <= allocation['lease_end'] - max(21600, allocation['lease_margin_seconds']), 'lease sixhour finish margin')


def validate_failure(binding, kind, entry, directory, runtime, initial, source, preserve, output_root):
    require(kind in ('preworker', 'warm-prefix-validation', 'collector-predecessor-validation'), 'explicit supported failure kind')
    stopped = checked(binding)
    previous_root = Path(binding['path']).parent
    require(not output_root.is_relative_to(previous_root) and not previous_root.is_relative_to(output_root),
            'output overlaps immutable failed attempt')
    previous_pin = pin(previous_root / 'manifest.json')
    previous = checked(previous_pin)
    started_pin = pin(previous_root / 'started.json')
    require(checked(started_pin)['manifest'] == previous_pin, 'failed attempt started manifest drift')
    require(previous['entry'] == entry and previous['seed'] == entry['seed']
            and previous['root'] == str(previous_root), 'prior failure seed/source/ancestry mismatch')
    repair = getattr(runtime, 'repair', None)
    compatible = previous['source_root'] == str(source)
    if repair is not None:
        attempt = {'preworker': 2, 'warm-prefix-validation': 3, 'collector-predecessor-validation': 4}[kind]
        require(previous_root.name == f'pcfl_sequence_v2_followup_seed{entry["seed"]}_20260913_attempt{attempt}',
                'exact failed attempt2/3/4 chain required')
        compatible = (previous['source_root'] == '/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix'
                      + ('3' if kind == 'collector-predecessor-validation' else '2')
                      and previous['repair']['original'] == repair['original']
                      and previous['repair']['outer_original'] == repair['outer_original'])
    require(compatible, 'prior failure seed/source/ancestry mismatch')
    require(stopped['status'] == 'STOPPED' and stopped['phase'] == 'B200_NEW_DOSE'
            and stopped['stage'] == 'fit' and len(stopped['results']) == 1, 'only first-stage failure supported')
    require(not (previous_root / 'completed.json').exists()
            and sorted(path.name for path in (previous_root / 'runs').iterdir()) == ['B200_NEW_DOSE_fit_outer'],
            'failed attempt must have no later stages or readouts')
    result = stopped['results'][0]
    collection_pin = result['collection']
    failed_root = previous_root / 'runs/B200_NEW_DOSE_fit_outer'
    require(collection_pin['path'] == str(failed_root / 'collection.json'), 'failed collection root mismatch')
    collection = checked(collection_pin)
    runtime.fit.prefix.unseal(collection, collection['sha256'])
    require(collection['status'] == 'FAILED' and collection['retries'] == 0, 'failed attempt without retries required')
    require(collection['inputs'] == previous['fit_inputs'][0] == result['inputs']
            and result['phase'] == collection['phase'] == 'B200_NEW_DOSE' and result['stage'] == 'fit',
            'failed stage input identity mismatch')
    inputs = checked(collection['inputs'])
    parent_pin = pin(directory / 'fit_outer/fit/completed.json')
    require(inputs['learner_seed'] == entry['seed'] and inputs['material'] == entry['material']
            and inputs['predecessor'] == parent_pin, 'failed fit measured parent/seed/material mismatch')
    allocation = checked(entry['allocation'])
    require(inputs['gpu_uuid'] == allocation['gpu_uuid']
            and collection['allocation_file_sha256'] == entry['allocation']['sha256']
            and collection['outer_source_sha256'] == allocation['outer_sha256'], 'failed GPU/source identity mismatch')
    inventory = runtime.acquisition.inventory(failed_root)
    require({name: value for name, value in inventory.items() if name != 'collection.json'} == collection['files'],
            'failed attempt inventory drift')
    work = dict(fits=0, updates=0, presentations=0, readout_calls=0)
    prior = previous.get('prior_failure')
    if kind == 'preworker':
        require(prior is None, 'preworker must terminate failure ancestry')
        require(collection['worker_identity'] is None and collection['returncode'] is None
                and collection['stage_inventory'] == {} and not (failed_root / 'fit').exists(),
                'prior attempt may have executed a worker')
    else:
        require(prior is not None, 'exact attempt3 -> attempt2 ancestry required')
        prior_kind = 'preworker' if kind == 'warm-prefix-validation' else 'warm-prefix-validation'
        initial, work = validate_failure(prior, prior_kind, entry, directory, runtime, initial, source, preserve, output_root)
        stage_root = failed_root / 'fit'
        require(collection['worker_identity'] is not None and collection['gpu_released'] is True,
                'failed worker must be released and unqualified')
        manifest_pin = pin(stage_root / 'checkpoint/train_manifest.json')
        manifest = checked(manifest_pin)
        require(manifest['steps'] == 200 and manifest['config']['seed'] == entry['seed'], 'failed fit dose/seed mismatch')
        require(manifest['warm_start']['parent_path'] == str(directory / 'fit_outer/fit/checkpoint'), 'failed fit parent mismatch')
        if kind == 'warm-prefix-validation':
            failure = checked(pin(stage_root / 'failure.json'))
            require(failure == dict(kind='NATIVE', message='full parent tensor coverage differs',
                    partial_checkpoint_not_eligible=True, phase='B200_NEW_DOSE', status='FAILED', type='ActorError'),
                    'only diagnosed warm-prefix validator failure eligible for rerun')
            require(collection['returncode'] == 1 and not (stage_root / 'completed.json').exists(),
                    'failed worker must be released and unqualified')
        else:
            require(entry['seed'] == 0, 'collector failure is seed0 attempt4 only')
            errors = [dict(error='warm start: output must be fresh', phase='stage_evidence', type='ValueError')]
            require(collection['returncode'] == 0 and collection['errors'] == errors
                    and checked(pin(failed_root / 'failure.json')) == dict(errors=errors)
                    and collection['completed_sha256'] is None and collection['full_contract_released'] is False
                    and collection['automatic_promotion'] is False and not (stage_root / 'failure.json').exists(),
                    'only diagnosed collector-predecessor failure eligible for rerun')
            completed_pin = pin(stage_root / 'completed.json')
            completed = checked(completed_pin)
            runtime.fit.prefix.unseal(completed, completed['sha256'])
            require(pin(failed_root / 'fit_completed.json')['sha256'] == completed_pin['sha256']
                    and completed['kind'] == 'NATIVE' and completed['status'] == 'COMPLETE'
                    and completed['phase'] == 'B200_NEW_DOSE' and completed['updates'] == 200
                    and completed['learner_seed'] == 0 and completed['predecessor'] == parent_pin
                    and completed['inputs'] == collection['inputs'], 'failed collector worker receipt mismatch')
            require(collection['stage_inventory'] == runtime.acquisition.inventory(stage_root), 'failed stage inventory drift')
            worker_exit = checked(pin(failed_root / 'worker_exit.json'))
            released = checked(pin(failed_root / 'worker_release.json'))['value']
            require(worker_exit['returncode'] == 0 and worker_exit['identity'] == collection['worker_identity']
                    and released['identity'] == collection['worker_identity'] and released['owned_group_released'] is True,
                    'failed collector worker release mismatch')
        preserve(manifest_pin)
    require(previous.get('prior_failed_work', work) == work, 'prior failed physical-work accounting mismatch')
    require(previous['initial_outer_seconds'] == initial, 'prior failure elapsed ancestry mismatch')
    if kind != 'preworker':
        work = {name: value + dict(fits=1, updates=200, presentations=800, readout_calls=0)[name]
                for name, value in work.items()}
    elapsed, stage_elapsed = stopped['elapsed_seconds'], collection['elapsed_seconds']
    require(type(elapsed) in (int, float) and math.isfinite(elapsed)
            and type(stage_elapsed) in (int, float) and math.isfinite(stage_elapsed)
            and elapsed >= stage_elapsed >= 0, 'invalid prior failure cost')
    preserve([binding, started_pin, previous_pin, previous, collection_pin, collection['inputs']])
    for name in collection['files']:
        preserve(pin(failed_root / name))
    return initial + elapsed, work


def prepare(args, runtime):
    root, source = Path(args.root).resolve(), Path(args.source_root)
    require(not root.exists() and not root.is_symlink(), 'fresh output root required')
    campaign_pin = dict(path=args.campaign, sha256=args.campaign_sha256)
    campaign = checked(campaign_pin)
    campaign_root = Path(args.campaign).parent
    require(campaign['schema'] == runtime.campaign.SCHEMA and campaign['budget'] == runtime.campaign.BUDGET,
            'original acquisition campaign identity mismatch')
    entries = [entry for entry in campaign['entries'] if entry['seed'] == args.seed]
    require(len(entries) == 1, 'seed identity mismatch')
    entry = entries[0]
    trained, cold, allocation, material = (checked(entry[name]) for name in ('fit_inputs', 'c0_inputs', 'allocation', 'material'))
    require(entry['gpu'] == args.gpu == allocation['gpu_index'], 'GPU identity mismatch')
    require([trained['learner_seed'], cold['learner_seed'], material['spec']['learner_seed']] == [args.seed] * 3, 'seed identity mismatch')
    require(trained['gpu_uuid'] == cold['gpu_uuid'] == allocation['gpu_uuid'], 'GPU UUID identity mismatch')
    sources = {**runtime.readout.source_files(), **{str(Path(module.__file__).resolve()): pin(module.__file__)['sha256']
               for module in (runtime.outer, runtime.outer.lifecycle)}}
    require(all(campaign['source_files'].get(path) == checksum for path, checksum in original_sources(sources, runtime).items()), 'campaign source identity mismatch')
    require(trained['source_files'] == original_sources(runtime.fit.source_files(), runtime)
            and cold['source_files'] == original_sources(runtime.readout.source_files(), runtime), 'input source identity mismatch')
    outer_original = runtime.repair['outer_original'] if getattr(runtime, 'repair', None) is not None else pin(runtime.outer.__file__)
    require(allocation['outer_sha256'] == outer_original['sha256'], 'outer source identity mismatch')
    require(runtime.outer.TOTAL_SECONDS == 1800, 'fixed stage cap required')
    require(trained['predecessor'] is None and cold['fit_receipt'] is None, 'original C0/A200 inputs required')
    for field in ('material', 'model_path', 'model_binding', 'base_state_receipt', 'archive', 'replay_receipt', 'environment'):
        require(trained[field] == cold[field], 'fit/cold identity mismatch: ' + field)
    require(trained['material'] == entry['material'] and material['spec']['sha256'] == entry['spec_sha256'], 'material identity mismatch')
    pins = [campaign_pin, pin(__file__)]

    def preserve(value):
        if isinstance(value, dict):
            if set(value) == {'path', 'sha256'}:
                require(pin(value['path']) == value, 'original input pin drift')
                pins.append(value)
            else:
                for child in value.values():
                    preserve(child)
        elif isinstance(value, list):
            for child in value:
                preserve(child)

    for path, checksum in sources.items():
        require(Path(path).resolve().is_relative_to(source)
                or (getattr(runtime, 'repair', None) is not None and Path(path).resolve().is_relative_to(SOURCE)),
                'runtime source outside immutable root')
        preserve(dict(path=path, sha256=checksum))
    if getattr(runtime, 'repair', None) is not None:
        preserve(runtime.repair['receipt'])
    preserve(pin(runtime.campaign.__file__))
    for value in (entry, trained, cold):
        preserve(value)
    for path, checksum in campaign['source_files'].items():
        preserve(dict(path=path, sha256=checksum))
    runs_root = Path(campaign.get('runs_root', campaign_root / 'runs'))
    directory = Path(entry.get('run_root', entry.get('runs_root', runs_root / f'seed{args.seed}'))).resolve()
    require(not root.is_relative_to(campaign_root) and not campaign_root.is_relative_to(root)
            and not root.is_relative_to(source) and not source.is_relative_to(root), 'output overlaps immutable evidence/source')
    originals, initial = [], 0
    for stage, state, name in (('fit', None, 'fit'), ('readout', 'NO_WRITE', 'no_write'), ('readout', 'A200', 'a200')):
        binding = pin(directory / f'{name}_outer/collection.json')
        collection = checked(binding)
        runtime.fit.prefix.unseal(collection, collection['sha256'])
        require(collection['status'] == 'COMPLETED' and collection['gpu_released'] is True
                and collection['errors'] == [] and collection['returncode'] == 0 and collection['retries'] == 0, 'failed/unreleased initial stage')
        selection = {'phase': 'A200'} if stage == 'fit' else {'stage': stage, 'state': state}
        require(all(collection.get(key) == value for key, value in selection.items()), 'initial stage identity mismatch')
        require(collection['allocation_file_sha256'] == entry['allocation']['sha256']
                and collection['outer_source_sha256'] == allocation['outer_sha256'], 'initial GPU/source identity mismatch')
        captured = checked(collection['inputs'])
        require(captured['gpu_uuid'] == allocation['gpu_uuid'] and captured['learner_seed'] == args.seed, 'captured seed/GPU identity mismatch')
        expected = trained if stage == 'fit' else {**cold, 'fit_receipt': None if state == 'NO_WRITE' else pin(directory / 'fit_outer/fit/completed.json')}
        require(captured == expected and (stage != 'fit' or collection['inputs'] == entry['fit_inputs']), 'initial input source mismatch')
        require(state != 'NO_WRITE' or collection['inputs'] == entry['c0_inputs'], 'original C0 input identity mismatch')
        if stage == 'fit':
            inventory = runtime.acquisition.inventory(Path(binding['path']).parent)
            require({name: value for name, value in inventory.items() if name != 'collection.json'} == collection['files'], 'initial fit inventory drift')
            require(not any(Path(name).name in ('failure.json', 'collection_failure.json') for name in inventory), 'failed initial fit archive')
        elapsed = collection['elapsed_seconds']
        require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= 1800, 'invalid initial outer elapsed')
        initial += elapsed
        originals.append(binding)
    preserve(originals)
    prior_failure = None
    prior_failed_work = dict(fits=0, updates=0, presentations=0, readout_calls=0)
    if getattr(args, 'prior_failure', None) is not None:
        prior_failure = dict(path=args.prior_failure, sha256=args.prior_failure_sha256)
        kind = getattr(args, 'prior_failure_kind', 'preworker')
        initial, prior_failed_work = validate_failure(prior_failure, kind, entry, directory, runtime, initial, source, preserve, root)
    root.mkdir(parents=True)
    (root / 'inputs').mkdir()
    (root / 'runs').mkdir()
    request = dict(schema=runtime.acquisition.SCHEMA + '/request', no_write_collection=originals[1], a200_collection=originals[2])
    runtime.fit.write(root / 'inputs/acquisition_request.json', request)
    request_pin = pin(root / 'inputs/acquisition_request.json')
    receipt = runtime.acquisition.validate(request_pin, material, trained)
    runtime.fit.write(root / 'inputs/acquisition_receipt.json', receipt)
    require(receipt['a200_fit_receipt'] == pin(directory / 'fit_outer/fit/completed.json'), 'measured A200 identity mismatch')
    ready = receipt['observed_gate'] is True
    runtime_cold = {**cold, 'source_files': runtime.readout.source_files()}
    runtime.fit.write(root / 'inputs/runtime_c0_inputs.json', runtime_cold)
    runtime_allocation = {**allocation, 'outer_sha256': pin(runtime.outer.__file__)['sha256']}
    runtime.fit.write(root / 'inputs/runtime_allocation.json', runtime_allocation)
    plan = dict(schema=SCHEMA, status='READY' if ready else 'WITHHELD', seed=args.seed, gpu=args.gpu,
                source_root=str(source), root=str(root), phases=list(PHASES) if ready else [],
                counts=COUNTS if ready else {**dict.fromkeys(COUNTS, 0), 'initial_updates': 200, 'total_updates': 200}, initial_outer_seconds=initial,
                remaining_seconds=7200-initial, originals=originals, entry=entry, pins=pins,
                acquisition_request=request_pin, acquisition_receipt=pin(root / 'inputs/acquisition_receipt.json'),
                runtime_c0_inputs=pin(root / 'inputs/runtime_c0_inputs.json'), repair=getattr(runtime, 'repair', None),
                runtime_allocation=pin(root / 'inputs/runtime_allocation.json'),
                prior_failure=prior_failure,
                prior_failure_kind=getattr(args, 'prior_failure_kind', 'preworker') if prior_failure else None,
                prior_failed_work=prior_failed_work,
                automatic_promotion=False, no_automatic_retry=True, retention=None, fit_inputs=[])
    if ready:
        budget(initial, time.monotonic(), allocation)
        for phase in PHASES:
            inputs = {**trained, 'acquisition_receipt': request_pin,
                      'source_files': runtime.fit.source_files(),
                      'predecessor': receipt['a200_fit_receipt'] if phase != 'CLEAN_CUM600' else None}
            runtime.fit.write(root / f'inputs/{phase}_inputs.json', inputs)
            plan['fit_inputs'].append(pin(root / f'inputs/{phase}_inputs.json'))
    runtime.fit.write(root / 'manifest.json', plan)
    return pin(root / 'manifest.json')


def run(args, runtime):
    root = Path(args.root).resolve()
    manifest_pin = dict(path=str(root / 'manifest.json'), sha256=args.manifest_sha256)
    plan = checked(manifest_pin)
    require(plan['schema'] == SCHEMA and plan['status'] == 'READY', 'WITHHELD or non-ready plan; zero fits')
    require(plan['root'] == str(root) and plan['source_root'] == args.source_root, 'source/output identity mismatch')
    require(plan['phases'] == list(PHASES) and plan['counts'] == COUNTS and len(plan['fit_inputs']) == 4, 'fixed four fits required')
    require(not any((root / name).exists() for name in ('started.json', 'stopped.json', 'completed.json')), 'already started; no resume')
    require(not any((root / f'runs/{phase}_{stage}_outer').exists() for phase in PHASES for stage in ('fit', 'readout')), 'already-existing stage output')
    entry, results, started = plan['entry'], [], time.monotonic()
    allocation, cold = checked(plan['runtime_allocation']), checked(plan['runtime_c0_inputs'])
    require(allocation == {**checked(entry['allocation']), 'outer_sha256': pin(runtime.outer.__file__)['sha256']},
            'runtime allocation may change only outer source pin')
    require(plan['repair'] == getattr(runtime, 'repair', None), 'runtime repair identity mismatch')
    os.environ.update({name: '1' for name in runtime.fit.OFFLINE})
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    runtime.fit.write(root / 'started.json', dict(manifest=manifest_pin, started_at=time.time()))
    try:
        for phase, fit_pin in zip(PHASES, plan['fit_inputs']):
            for stage in ('fit', 'readout'):
                for binding in [manifest_pin, *plan['pins'], *plan['fit_inputs'], plan['acquisition_request'], plan['acquisition_receipt'], plan['runtime_c0_inputs'], plan['runtime_allocation']]:
                    require(pin(binding['path']) == binding, 'pinned provenance drift')
                inputs = checked(fit_pin)
                receipt = runtime.acquisition.validate(plan['acquisition_request'], checked(entry['material']), inputs)
                require(receipt == checked(plan['acquisition_receipt']) and receipt['observed_gate'] is True, 'acquisition drift; no rescue')
                require(inputs['predecessor'] == (None if phase == 'CLEAN_CUM600' else receipt['a200_fit_receipt']), 'fixed measured parent required')
                require(inputs['learner_seed'] == plan['seed'] == entry['seed'] and inputs['gpu_uuid'] == allocation['gpu_uuid']
                        and plan['gpu'] == entry['gpu'] == allocation['gpu_index'], 'seed/GPU identity mismatch')
                require(inputs['source_files'] == runtime.fit.source_files() and cold['source_files'] == runtime.readout.source_files(), 'runtime source identity mismatch')
                input_pin = fit_pin
                if stage == 'readout':
                    measured = pin(root / f'runs/{phase}_fit_outer/fit/completed.json')
                    read_inputs = {**cold, 'fit_receipt': measured}
                    runtime.fit.write(root / f'inputs/{phase}_readout_inputs.json', read_inputs)
                    input_pin = pin(root / f'inputs/{phase}_readout_inputs.json')
                budget(plan['initial_outer_seconds'], started, allocation)
                output = root / f'runs/{phase}_{stage}_outer'
                result = runtime.outer.controller(input_pin['path'], input_pin['sha256'], plan['runtime_allocation']['path'],
                    plan['runtime_allocation']['sha256'], str(output), outer_sha256=allocation['outer_sha256'],
                    phase=phase, stage=stage, state=phase if stage == 'readout' else None)
                results.append(dict(phase=phase, stage=stage, inputs=input_pin, collection=pin(output / 'collection.json')))
                require(result == checked(results[-1]['collection']), 'returned collection drift')
                require(result['status'] == 'COMPLETED' and result['gpu_released'] is True and result['errors'] == [], 'failed/unreleased stage; no retry')
                require(time.monotonic() - started + plan['initial_outer_seconds'] <= 7200, 'perseed budget exceeded')
        runtime.fit.write(root / 'completed.json', dict(status='CAPTURED_NOT_PROMOTED', results=results,
                          elapsed_seconds=time.monotonic()-started, automatic_promotion=False))
    except BaseException as error:
        runtime.fit.write(root / 'stopped.json', dict(status='STOPPED', results=results, error=str(error),
                          phase=phase, stage=stage, elapsed_seconds=time.monotonic()-started, no_automatic_retry=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'run'):
        command = commands.add_parser(name)
        for field in ('root', 'source-root', *(('campaign', 'campaign-sha256') if name == 'prepare' else ('manifest-sha256',))):
            command.add_argument('--' + field, required=True)
        if name == 'prepare':
            command.add_argument('--seed', type=int, choices=(0, 1, 2), required=True)
            command.add_argument('--gpu', type=int, required=True)
            command.add_argument('--prior-failure')
            command.add_argument('--prior-failure-sha256')
            command.add_argument('--prior-failure-kind', choices=('preworker', 'warm-prefix-validation', 'collector-predecessor-validation'), default='preworker')
    args = parser.parse_args()
    result = (prepare if args.command == 'prepare' else run)(args, load_runtime(args.source_root))
    if result:
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
