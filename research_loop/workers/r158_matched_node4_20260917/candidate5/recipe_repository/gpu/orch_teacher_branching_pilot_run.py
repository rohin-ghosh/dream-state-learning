"""Isolated teacher dose4 native fit/readout. Only the allocated guardian launches.

CPU preparation: --phase prepare --root NATIVE_ROOT --config CONFIG.json.
CONFIG supplies manifest, interface_ready, bundle, model_dir, initial_adapter,
rubric, and service_identity absolute paths. Raw inputs must already exist on
the node; this program never transfers them. --phase contract prints the pins.
No launch is authorized by compilation, interface readiness, or this module.
"""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu import orch_teacher_branching_pilot_interface as interface
from gpu.orch_l2_shared_run import legacy_encode
from gpu.orch_teacher_branching_pilot_compile import BUNDLE_SHA, read, sha
from organism_v6 import orch_combined_l1_behavior as behavior
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_math_rich as math
from organism_v6 import orch_teacher_branching_pilot as pilot
from organism_v6.orch_combined_l1_continual import atomic_json as write
from organism_v6.orch_combined_l1_dev import default_math_messages
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


PROGRAM = 'gpu.orch_teacher_branching_pilot_run'
CELLS = ('FULL', 'OFF')
MANIFEST_SHA = '976a0258d053f783c1cc3b5383614c7502e56d43d7e830c9782aaf9bba1fe527'
INTERFACE_SHA = '53a4ddb5a196f2c58a6e854a034184c6eac89fffc98c9800bed3d094dca11c8c'
POLICY_SHA = '6cd772819e54f54b7bb86d274fd1b64932c67500af5900a59692a6d31e64adf9'
PROTOCOL_SHA = 'a9cdf2934f2f5998ac1fe3e3a3ba98cc0db0226149d0f6a786d1ed88ea239085'
SEALED_SHA = '194176b99a09ad1e9bac02728332059aee666cabf8c444a1f7bc769493013062'
R106_SHA = '0745eafe29d42c54b46ed4d36beb055f5f265e71149f86efd1e94d5b77e443d1'
LIMITS = dict(math=16, route=48, legacy=48)
CAPS = dict(math=4096, route=4096, legacy=160)
RECIPE = {key: shared.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
require = pilot.require


def contract():
    return dict(schema='TEACHER_DOSE4_NATIVE_DRIVER_V1', source_label=pilot.LABEL,
        initial_state=pilot.STATE, initial_base=pilot.BASE, teacher_rows=16, legacy_rows=222,
        updates_per_cell=56, batch_size=4, cells=list(CELLS), max_calls=224,
        family_calls_per_cell=LIMITS, caps=CAPS, output_token_reservations_max=539648,
        seconds=7200, gpu_hours=4, lease_margin_seconds=21600, recipe=RECIPE,
        provider_calls=0, parent_calls=0, source_calls=0, continual_intake=False,
        requires_main_allocation=True, fifo_unchanged=True, terminal_continual_calls_unchanged=416,
        manifest_sha256=MANIFEST_SHA, interface_sha256=INTERFACE_SHA,
        rubric_sha256=R106_SHA, semantic_author_sample_math_positions=[0, 1, 2, 3],
        math_system='SOLVE_PLUS_FINAL_ONLY_NO_WAKE_RICH_CHECK_UNCERTAINTY_BOILERPLATE',
        immutable_task_check_requests_preserved=True, spontaneous_branching_claim=False)


def math_prompt_metadata(task):
    check_request = bool(re.search(r'\b(check|checks|checking|verify|verification|confirm|double-check)\b',
                                  task['question'], re.IGNORECASE))
    return dict(prompt_condition='MINIMAL_SYSTEM_TASK_CHECK_REQUEST_PRESERVED' if check_request else
        'MINIMAL_SYSTEM_ORIGINAL_TASK_PRESERVED', task_check_lexical_disclosure=check_request,
        disclosure_is_semantic_certification=False, original_task_verbatim=True,
        question_sha256=behavior.text_hash(task['question']), spontaneous_branching_claim=False)


def owned_root(root):
    require(root.is_absolute() and root.parent == Path('/localhome/local-rohing') and
        root.name.startswith('orch_teacher_branching_pilot_') and not root.is_symlink(), 'native_owned_root')


def replay_arm(cell):
    require(cell in CELLS, 'known_cell')
    return pilot.ARMS[CELLS.index(cell)]


def check_deadline(lifetime, label, now=None):
    require((time.time() if now is None else now) < lifetime['hard_deadline_unix'], 'deadline:' + label)


def source_hashes(root):
    return {str(path.relative_to(root)): sha(path) for folder in ('gpu', 'organism_v6')
            for path in (root / folder).rglob('*.py')}


def verify_refs(refs):
    for entry in refs.values():
        require(Path(entry['path']).is_absolute() and sha(entry['path']) == entry['sha256'], 'input_hash_drift')


def compiled_inputs(config):
    require(sha(config['manifest']) == MANIFEST_SHA, 'fixed_teacher16_manifest')
    require(sha(interface.__file__) == INTERFACE_SHA and sha(pilot.__file__) == POLICY_SHA, 'pinned_hubble_code')
    manifest = read(config['manifest'])
    require(manifest['source_label'] == pilot.LABEL and manifest['rows'] == 16 and
        manifest['math_rows'] == manifest['route_rows'] == 8 and
        manifest['training_application_allowed'] is False and manifest['ongoing_l1_allowed'] is False,
        'isolated_teacher_historical_pending_labels')
    require(source_hashes(Path(manifest['source_root'])) == manifest['runtime_source_files'], 'compiler_source_drift')
    verify_refs(manifest['files'])
    verify_refs(manifest['legacy_refs'])
    ready = read(config['interface_ready'])
    require(ready['compiled_manifest']['sha256'] == MANIFEST_SHA and
        ready['interface_source']['sha256'] == INTERFACE_SHA, 'interface_binding')
    verify_refs(ready['files'])
    require(ready['files']['PAIRED_PROTOCOL.json']['sha256'] == PROTOCOL_SHA and
        ready['files']['SEALED_READOUT_INPUTS.json']['sha256'] == SEALED_SHA, 'frozen_interface_panels')
    require(sha(config['rubric']) == R106_SHA, 'prospective_R106_rubric')
    require(ready['protocol']['optimizer'] == RECIPE and ready['protocol']['updates_per_arm'] == 56,
            'fixed_original_recipe')
    return manifest, ready


def encoded_inputs(manifest, tokenizer):
    legacy_root = Path(manifest['legacy_refs']['LEGACY_MATERIAL.json']['path']).parent
    legacy = legacy_encode(legacy_root, tokenizer)
    new = pilot.encode_rows(read(manifest['files']['ROWS.json']['path']), tokenizer)
    saved = read(manifest['files']['ENCODED_TEACHER.json']['path'])
    require(pilot.digest([asdict(row) for row in new]) == pilot.digest(saved), 'exact_compiled_encoder')
    layout = GoalReplayLayout(16, 4)
    encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy, eos_token_id=tokenizer.eos_token_id)
    return encoded, layout


def prepare(root, config_path):
    from transformers import AutoTokenizer
    owned_root(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_prepare')
    require(not (root / 'PREPARE.json').exists() and not (root / 'LIFETIME.json').exists(), 'fresh_preparation')
    config = read(config_path)
    manifest, ready = compiled_inputs(config)
    base = portable.verify_base_files(config['bundle'], config['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    identity = bridge.AdapterIdentity(config['initial_adapter'], pilot.STATE, pilot.BASE,
        tuple(tuple(entry) for entry in manifest['original_initial']['files'])).verify()
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    encoded, layout = encoded_inputs(manifest, tokenizer)
    totals = interface.paired_batches(encoded, tokenizer.pad_token_id)
    require(totals == ready['totals'] == dict(full_reference=42207, full_active=42207,
        masked_reference=42207, masked_active=3839), 'whole_pair_token_budget')
    panel = read(ready['files']['SEALED_READOUT_INPUTS.json']['path'])
    require(panel['training_allowed'] is False and panel['teacher_or_parent_access'] is False and
        len(panel['math_tasks']) == 16 and len(panel['route_collections']) == 2, 'frozen_parentfree_held')
    lengths = [len(tokenizer.apply_chat_template(default_math_messages(task), tokenize=True,
               add_generation_prompt=True, return_dict=False)) for task in panel['math_tasks']]
    require(all(length + CAPS['math'] <= pilot.CONTEXT for length in lengths), 'uncropped_default_prompts')
    legacy = read(manifest['legacy_refs']['LEGACY_READOUT.json']['path'])
    require(len(legacy['old_bank']) == len(legacy['old_episodes']) == len(legacy['held']['cases']) == 16,
            'exact48_legacy_readout')
    source = Path(__file__).resolve().parents[1]
    require(source == root / 'source', 'isolated_native_source_required')
    prepared = dict(status='CPU_READY_NOT_ALLOCATED', config=config, config_sha256=sha(config_path),
        initial=identity.document(), model_dir=config['model_dir'], verified_base=base,
        source_files=source_hashes(source), input_refs=dict(manifest=dict(path=config['manifest'], sha256=MANIFEST_SHA),
            interface_ready=dict(path=config['interface_ready'], sha256=sha(config['interface_ready'])),
            rubric=dict(path=config['rubric'], sha256=R106_SHA),
            service=dict(path=config['service_identity'], sha256=sha(config['service_identity']))),
        contract=contract(), totals=totals, layout={cell:layout.manifest(replay_arm(cell)) for cell in CELLS},
        math_prompt_lengths=lengths,
        math_prompt_metadata=[dict(task_id=task['id'], **math_prompt_metadata(task)) for task in panel['math_tasks']],
        model_calls=0, created_unix=time.time())
    write(root / 'PREPARE.json', prepared)
    return prepared


def validate_inputs(root):
    owned_root(root)
    prepared = read(root / 'PREPARE.json')
    require(prepared['status'] == 'CPU_READY_NOT_ALLOCATED' and prepared['contract'] == contract(), 'ready_contract')
    require(Path(__file__).resolve().parents[1] == root / 'source', 'frozen_source_location')
    require(source_hashes(root / 'source') == prepared['source_files'], 'native_source_drift')
    verify_refs(prepared['input_refs'])
    compiled_inputs(prepared['config'])
    return prepared


def authorize_child(root, cell, phase):
    from gpu import orch_teacher_branching_pilot_guard as guard
    prepared = validate_inputs(root)
    lifetime = read(root / 'LIFETIME.json')
    check_deadline(lifetime, phase)
    allocation = guard.validate_allocation(root, lifetime['allocation_sha256'], prepared)
    path = root / f'{cell}_{phase}_LAUNCH.json'
    until = min(time.time() + 15, lifetime['hard_deadline_unix'])
    while not path.exists() and time.time() < until:
        time.sleep(.05)
    receipt = read(path)
    require(receipt['identity'] == guard.identity(os.getpid()) and receipt['phase'] == phase and
        receipt['allocation_sha256'] == lifetime['allocation_sha256'], 'guardian_child_identity')
    uuid = allocation['devices'][cell]['uuid']
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'allocated_uuid_only')
    require(('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'),
            'actual_process_uuid_environment')
    return prepared, lifetime, uuid


def fit(root, cell):
    prepared, lifetime, uuid = authorize_child(root, cell, 'fit')
    output = root / cell / 'fit'
    output.mkdir(parents=True, exist_ok=False)
    identity = bridge.AdapterIdentity.from_document(prepared['initial'])
    binding = bridge.StageBinding(root.name, bridge.ARMS[2], 0, 'training', identity, False, False, sha(root / 'PREPARE.json'))
    plan = SimpleNamespace(binding=lambda unused: binding, lineage=SimpleNamespace(arm=bridge.ARMS[2]),
        contract=SimpleNamespace(manifest=lambda unused: dict(recipe=RECIPE)))
    write(output / 'REQUEST.json', dict(cell=cell, input_adapter=identity.document(),
        process=native.process_identity(), source_label=pilot.LABEL, fresh_optimizer=True, started_unix=time.time()))
    try:
        loaded = native.load_training(plan, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=lambda label:check_deadline(lifetime, label))
        write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(), loaded_unix=time.time()))
        manifest = read(prepared['config']['manifest'])
        encoded, layout = encoded_inputs(manifest, loaded.engine.tokenizer)
        require(interface.paired_batches(encoded, loaded.engine.tokenizer.pad_token_id) == prepared['totals'], 'native_pair_encoding')
        torch = loaded.engine.torch
        parameters = {name:parameter for name,parameter in loaded.engine.model.named_parameters() if native.is_lora(name)}
        counts, active_total, reference_total = [0] * 238, 0, 0
        with (output / 'LOSSES.jsonl').open('x') as stream:
            for update in range(1, 57):
                check_deadline(lifetime, 'optimizer_update')
                indexes, batch, reference, active, scale = native.training_batch(encoded, layout, update,
                    pad_id=loaded.engine.tokenizer.pad_token_id, replay_arm=replay_arm(cell))
                tensors = {name:torch.tensor(value, dtype=torch.long, device=loaded.engine.device) for name,value in batch.items()}
                loaded.optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                    loss = loaded.engine.model(**tensors, use_cache=False).loss * scale
                require(bool(torch.isfinite(loss)), 'finite_loss')
                loss.backward()
                require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                    for parameter in parameters.values()), 'finite_LoRA_gradients')
                loaded.optimizer.step()
                for index in indexes:
                    counts[index] += 1
                active_total += active
                reference_total += reference
                record = dict(update=update, rows=indexes, loss=loss.item(), active=active,
                              reference=reference, scale=scale, finished_unix=time.time())
                stream.write(json.dumps(record) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
                if update == 1:
                    write(output / 'FIRST_UPDATE.json', record)
        require(tuple(counts) == layout.presentation_counts(), 'actual56_update_dose')
        require(reference_total == 42207 and active_total == (42207 if cell == 'FULL' else 3839), 'actual_label_dose')
        require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'finite_saved_LoRA')
        loaded.engine.verify_base()
        check_deadline(lifetime, 'save')
        loaded.engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
        torch.save(loaded.optimizer.state_dict(), output / 'optimizer.pt')
        saved = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), pilot.BASE,
            tuple((path.name,sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
        require(native.observe_adapter(loaded.engine, saved) == saved, 'saved_observed_adapter')
        write(output / 'COMPLETE.json', dict(status='COMPLETE', source_label=pilot.LABEL, input_adapter=identity.document(),
            output_adapter=saved.document(), process=loaded.process, updates=56, exposure_counts=counts,
            reference_tokens=reference_total, supervised_tokens=active_total, optimizer_sha256=sha(output / 'optimizer.pt'),
            training_generation_calls=0, parent_calls=0, continual_intake_allowed=False, finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise


class ReadoutEngine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens):
        require(max_new_tokens in (160, 4096), 'registered_readout_cap')
        self.check('generate')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        require(0 < len(tokens) and len(tokens) + max_new_tokens <= pilot.CONTEXT, 'whole_context_no_crop')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), generation_config=config)
        require(generated[0,:len(tokens)].tolist() == tokens, 'exact_prompt_preserved')
        tail = generated[0,len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
            raw=self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                                     clean_up_tokenization_spaces=False),
            terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)


def reserve(root, cell, family, messages, metadata, lifetime):
    require(cell in CELLS and family in LIMITS, 'known_readout_bucket')
    check_deadline(lifetime, 'reserve')
    path = root / 'CALL_LEDGER.jsonl'
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        ledger = [json.loads(line) for line in stream if line.strip()]
        require(len(ledger) < 224 and sum(entry['cap'] for entry in ledger) + CAPS[family] <= 539648, 'pair_call_or_token_cap')
        require(sum(entry['cell'] == cell and entry['family'] == family for entry in ledger) < LIMITS[family], 'family_call_cap')
        record = dict(position=len(ledger), cell=cell, family=family, cap=CAPS[family], metadata=metadata,
                      status='RESERVED', parent_present=False, started_unix=time.time())
        stream.write(json.dumps(record) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    output = root / cell / 'readout' / f'CALL_{record["position"]:03d}.json'
    require(not output.exists(), 'no_call_retry')
    write(output, dict(record, messages=messages))
    return output, dict(record, messages=messages)


def richness(response):
    return dict(tokens=behavior.token_metrics(response, 4096), repetition=behavior.repetition(response['raw']),
        R106=dict(status='AUTHOR_REVIEW_PENDING_NOT_ZERO', departures_returns=None,
            mid_line_checks=None, terminal_checks=None, methods=None, rejections=None,
            coherence=None, branch_shape_independent_of_correctness=True),
        response_sha256=behavior.text_hash(response['raw']), used_for_training=False)


def readout(root, cell):
    from gpu import astra_goal_quality_train as old
    prepared, lifetime, uuid = authorize_child(root, cell, 'readout')
    completed = read(root / cell / 'fit/COMPLETE.json')
    require(completed['status'] == 'COMPLETE' and completed['updates'] == 56 and
        completed['input_adapter'] == prepared['initial'], 'one_complete_original37ec_fit')
    output = root / cell / 'readout'
    output.mkdir(exist_ok=False)
    failures = []
    try:
        identity = bridge.AdapterIdentity.from_document(completed['output_adapter']).verify()
        binding = bridge.StageBinding(root.name, bridge.ARMS[2], 1, 'sealed_readout', identity,
            False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_readout(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(), check=lambda label:check_deadline(lifetime, label),
            predecessor_processes=(tuple(completed['process']),), engine_factory=ReadoutEngine)
        write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
            parent_present=False, teacher_present=False, predecessor=completed['process'], loaded_unix=time.time()))
        def generate(family, messages, **metadata):
            path, record = reserve(root, cell, family, messages, metadata, lifetime)
            try:
                response = loaded.engine.generate(messages, max_new_tokens=CAPS[family])
                record.update(status='COMPLETE', response=response)
                if family == 'math':
                    record['richness'] = richness(response)
                return response
            except BaseException as error:
                failures.append(dict(path=str(path), error=type(error).__name__))
                record.update(status='FAILED', error=dict(type=type(error).__name__, message=str(error)))
                raise
            finally:
                record['finished_unix'] = time.time()
                write(path, record)
                if not (output / 'FIRST_CALL.json').exists():
                    write(output / 'FIRST_CALL.json', dict(path=str(path), sha256=sha(path), status=record['status']))
        ready = read(prepared['config']['interface_ready'])
        panel = read(ready['files']['SEALED_READOUT_INPUTS.json']['path'])
        math_rows = []
        for position, task in enumerate(panel['math_tasks']):
            elicitation = math_prompt_metadata(task)
            response = generate('math', default_math_messages(task), task_id=task['id'], math_position=position,
                                **elicitation)
            answer = math.final_value(response['raw'])
            math_rows.append(dict(task_id=task['id'], position=position, elicitation=elicitation, richness=richness(response),
                correct=answer is not None and answer == math.number(task['gold'])))
            write(output / 'MATH_ROWS.json', math_rows)
        routes = interface.evaluate_routes(panel['route_collections'],
            lambda messages: generate('route', messages), lambda name,value:write(output / name, value))
        manifest = read(prepared['config']['manifest'])
        legacy = read(manifest['legacy_refs']['LEGACY_READOUT.json']['path'])
        events = [dict(event=fact['event'], raw=episode['event']['raw'])
                  for fact,episode in zip(legacy['old_bank'],legacy['old_episodes'])]
        retention = old.memory.recall(events, lambda messages,**metadata:generate('legacy', messages, **metadata), output, 'OLD')
        audit = old.memory.audit.collect_cases(legacy['held'], lambda messages:generate('legacy', messages), coached=False)
        write(output / 'AUDIT.json', audit)
        ledger = [json.loads(line) for line in (root / 'CALL_LEDGER.jsonl').read_text().splitlines()]
        counts = {family:sum(entry['cell'] == cell and entry['family'] == family for entry in ledger) for family in LIMITS}
        require(counts['math'] == 16 and counts['legacy'] == 48 and counts['route'] == routes['actor_calls'] <= 48,
                'fixed_readout_completion_counts')
        require(not failures, 'generation_failures_preserved_no_retry')
        loaded.verify_unchanged()
        tokens = [row['richness']['tokens']['generated_tokens'] for row in math_rows]
        write(output / 'COMPLETE.json', dict(status='COMPLETE', source_label=pilot.LABEL, report_order=['richness','accuracy'],
            math_richness=dict(mean_tokens=statistics.mean(tokens), median_tokens=statistics.median(tokens),
                EOS=sum(row['richness']['tokens']['eos'] for row in math_rows),
                ceiling=sum(row['richness']['tokens']['ceiling'] for row in math_rows),
                author_semantics='PENDING_NOT_ZERO', author_sample_math_positions=[0,1,2,3]),
            elicitation_conditions=[row['elicitation']['prompt_condition'] for row in math_rows],
            spontaneous_branching_claim=False,
            math_accuracy=dict(correct=sum(row['correct'] for row in math_rows), denominator=16),
            routes=routes, retention=retention, audit=audit['summary'], calls=counts,
            process=loaded.process, adapter_unchanged=True, parent_calls=0, finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise


def author_annotation(text, annotation):
    require(annotation['response_sha256'] == behavior.text_hash(text) and annotation['full_output_read'] is True,
            'full_output_author_binding')
    require(annotation['reviewer'].strip() and annotation['rubric_sha256'] == R106_SHA, 'R106_author_rubric')
    def span(value):
        require(type(value['start']) is int and type(value['end']) is int and
            0 <= value['start'] < value['end'] <= len(text) and text[value['start']:value['end']] == value['text'],
            'exact_semantic_evidence_span')
    for branch in annotation['departures_returns']:
        for key in ('main_line','departure','resumption'):
            span(branch[key])
        require(branch['main_line']['start'] < branch['departure']['start'] < branch['resumption']['start'], 'departure_return_order')
        require(branch['reason'].strip(), 'departure_reason_not_marker')
    for check in annotation['checks']:
        span(check['evidence'])
        require(check['placement'] in ('MID_LINE','TERMINAL') and check['reason'].strip(), 'check_location_and_reason')
    for method in annotation['methods']:
        span(method['evidence'])
        require(method['distinctness_reason'].strip(), 'method_measurement_separate')
    for rejection in annotation.get('considered_rejections', []):
        span(rejection['considered'])
        span(rejection['rejection'])
        require(rejection['reason'].strip(), 'rejection_evidence_reason')
    pairs = [(branch['departure']['start'], branch['resumption']['start']) for branch in annotation['departures_returns']]
    require(len(set(pairs)) == len(pairs), 'duplicate_departure_return')
    require(annotation['coherence']['judgment'] in ('COHERENT','MIXED','INCOHERENT'), 'coherence_judgment')
    span(annotation['coherence']['evidence'])
    return dict(status='AUTHOR_DESCRIBED_NOT_INDEPENDENT_CERTIFICATION',
        departures_returns=len(annotation['departures_returns']),
        mid_line_checks=sum(check['placement'] == 'MID_LINE' for check in annotation['checks']),
        terminal_checks=sum(check['placement'] == 'TERMINAL' for check in annotation['checks']),
        methods=len(annotation['methods']), considered_rejections=len(annotation.get('considered_rejections', [])),
        coherence=annotation['coherence'], annotation=annotation,
        training_allowed=False, branch_shape_independent_of_correctness=True)


def reduce_annotations(root, cell, annotation_path):
    owned_root(root)
    annotations = read(annotation_path)
    require(set(annotations) == {'0','1','2','3'}, 'prospective_first_four_author_sample')
    output = root / cell / 'readout'
    result = []
    for path in sorted(output.glob('CALL_*.json')):
        record = read(path)
        if record['family'] != 'math' or str(record['metadata']['math_position']) not in annotations:
            continue
        require(record['status'] == 'COMPLETE' and record['parent_present'] is False, 'completed_parentfree_output')
        annotation = annotations[str(record['metadata']['math_position'])]
        result.append(dict(call_path=str(path), call_sha256=sha(path),
            measurement=author_annotation(record['response']['raw'],annotation)))
    require(len(result) == 4, 'four_completed_math_outputs_required')
    destination = output / ('R106_AUTHOR_' + sha(annotation_path) + '.json')
    require(not destination.exists(), 'immutable_author_measurement')
    write(destination, dict(source_label=pilot.LABEL, annotations_sha256=sha(annotation_path),
        results=result, new_model_calls=0, training_allowed=False, population_claim=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', required=True, choices=('contract','prepare','fit','readout','reduce'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--cell', choices=CELLS)
    parser.add_argument('--annotations', type=Path)
    args = parser.parse_args()
    if args.phase == 'contract':
        print(json.dumps(contract(), indent=2))
    elif args.phase == 'prepare':
        print(json.dumps(prepare(args.root, args.config), indent=2))
    elif args.phase == 'reduce':
        reduce_annotations(args.root, args.cell, args.annotations)
    else:
        (fit if args.phase == 'fit' else readout)(args.root, args.cell)
