"""Explicit fresh-process DEV adapter readout; no fit, BASE rerun or promotion.

The original pilot must already be complete. Caller pins RESULT and TRAINING
bytes, owns exclusive input custody and launches a new process with a hard
external timeout. Only safetensors adapter weights are restored; no optimizer
or full-resume claim. Exact comparison covers public requests/generations and
scored metrics, not native diagnostic tensors or bitwise kernel determinism.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time

from gpu import astra_stage2a_compare as comparison
from gpu import astra_stage2a_outcome_distill as pilot
from gpu import astra_stage2a_replay_baseline as replay
from organism_v6 import composition_birth_stage2a_screen as screen


require = pilot.require
CLAIM = "DEV_SAVED_ADAPTER_FITTED_READOUT_NOT_TRANSFER_OR_SCIENTIFIC_PROMOTION"
CHECKPOINT_KIND = "PEFT_ADAPTER_ONLY_NOT_FULL_RESUME_STATE"


def _document(path, expected=None):
    document = comparison._request(Path(path))
    if expected is not None:
        require(pilot.training._sha(expected) and document['sha256'] == expected,
                'document_hash_mismatch:' + str(path))
    return document


def _adapter_pin(directory, files):
    descriptor = os.open(directory, comparison.checkpoint._directory_flags())
    try:
        require(set(os.listdir(descriptor)) == set(files) | {'TRAINING.json'}, 'adapter_file_inventory_mismatch')
        rows = []
        for name in sorted(set(files) | {'TRAINING.json'}):
            limit = 512 * 1024 ** 2 if name == 'adapter_model.safetensors' else comparison.REQUEST_LIMIT
            size, digest, unused = comparison.checkpoint._read_file(descriptor, name, limit)
            rows.append(dict(name=name, size_bytes=size, sha256=digest))
    finally:
        os.close(descriptor)
    return dict(path=str(directory), files=rows,
                tree_sha256=sha256(pilot._json_bytes(rows)).hexdigest())


def load_original(directory, *, result_sha256, training_sha256):
    """Pure preflight; refuse incomplete or altered artifacts before native imports."""
    root = Path(directory).absolute()
    result = _document(root / 'RESULT.json', result_sha256)
    request = _document(root / 'REQUEST.json')
    trained = _document(root / 'adapter' / 'TRAINING.json', training_sha256)
    values, options, receipt = result['values'], request['values'], trained['values']
    require(values.get('status') == 'DEV_OUTCOME_SFT_COMPLETE'
            and values.get('reportable') is True, 'completed_original_pilot_required')
    require(values.get('claim') == pilot.CLAIM and options.get('method') == pilot.CLAIM
            and receipt.get('claim') == pilot.CLAIM, 'original_method_binding_mismatch')
    require(values.get('master_hex') == options.get('master_hex') == pilot.EVAL_MASTER.hex()
            and values.get('base_state_id') == options.get('base_state_id') == pilot.BASE_ID
            and values.get('fitted_state_id') == options.get('atom_state_id') == pilot.FITTED_ID,
            'original_eval_identity_mismatch')
    for key, expected in dict(completed_updates=pilot.UPDATES, seed=pilot.SEED,
                              batch_size=pilot.BATCH_SIZE).items():
        require(type(values.get(key)) is int and values[key] == expected
                and type(receipt.get(key)) is int and receipt[key] == expected,
                'original_training_recipe_mismatch:' + key)
    require(receipt.get('checkpoint_kind') == CHECKPOINT_KIND, 'saved_checkpoint_kind_mismatch')
    pilot._same(receipt.get('optimizer'), dict(pilot.training.OPTIMIZER_RECIPE), 'saved_training_recipe_mismatch')
    require(pilot.training._sha(values.get('adapter_sha256'))
            and receipt.get('adapter_sha256') == values['adapter_sha256'], 'adapter_digest_binding_mismatch')
    require(receipt.get('rows_sha256') == values['collection']['rows_sha256']
            and pilot.training._sha(receipt.get('rows_sha256'))
            and receipt.get('source_label') == values.get('source_label'), 'saved_source_binding_mismatch')
    expected_base = options.get('expected_base_sha256')
    require(pilot.training._sha(expected_base), 'expected_frozen_base_required')
    require(all(values.get('frozen_base_hashes', {}).get(phase) == expected_base for phase in
                ('before_training', 'after_training', 'after_base_evaluation', 'after_fitted_evaluation')),
            'original_frozen_base_hash_mismatch')
    files = values.get('adapter_files_sha256')
    require(type(files) is dict and files == receipt.get('files_sha256')
            and {'adapter_model.safetensors', 'adapter_config.json'} <= set(files)
            and 'TRAINING.json' not in files, 'adapter_file_manifest_required')
    for name, digest in files.items():
        require(type(name) is str and Path(name).name == name and name not in ('.', '..')
                and pilot.training._sha(digest), 'invalid_adapter_manifest_entry')
    adapter_pin = _adapter_pin(root / 'adapter', files)
    actual = {row['name']: row['sha256'] for row in adapter_pin['files']}
    require(actual == dict(files, **{'TRAINING.json': training_sha256}), 'adapter_files_hash_mismatch')
    require((root / 'adapter' / 'adapter_model.safetensors').stat().st_size > 0, 'empty_saved_adapter')
    return dict(result=result, request=request, training=trained, adapter=adapter_pin,
                fitted=comparison._custody_pin(root / 'FITTED'))


def restore_saved_adapter(initialized, directory, *, torch, peft, expected_sha256, load_file=None):
    """Populate the existing rank-eight shell from CPU safetensors, never fit."""
    if load_file is None:
        from safetensors.torch import load_file
    directory = Path(directory)
    expected_config = _document(initialized.directory / 'adapter_config.json')['values']
    saved_config = _document(directory / 'adapter_config.json')['values']
    require(saved_config == expected_config, 'saved_adapter_config_mismatch')
    state = load_file(str(directory / 'adapter_model.safetensors'), device='cpu')
    model = initialized.model
    expected = peft.get_peft_model_state_dict(model, adapter_name='default')
    require(set(state) == set(expected), 'saved_adapter_tensor_names_mismatch')
    for name, tensor in state.items():
        require(tensor.device.type == 'cpu' and tensor.dtype == expected[name].dtype == torch.float32
                and tuple(tensor.shape) == tuple(expected[name].shape)
                and bool(torch.isfinite(tensor).all()), 'saved_adapter_tensor_invalid:' + name)
    loaded = peft.set_peft_model_state_dict(model, state, adapter_name='default')
    require(not loaded.unexpected_keys and not any('.lora_' in name for name in loaded.missing_keys),
            'saved_adapter_load_incomplete')
    digest = pilot.training.adapter_sha256(model, initialized.observation.trainable_roster)
    require(digest == expected_sha256, 'restored_adapter_hash_mismatch')
    pilot.models.verify_retained_base(initialized, base_state_hash=pilot._state_hash)
    return digest


def _reduce(observed, held):
    reduced = pilot.reducer._reduce_state(observed, pilot.FITTED_ID,
        screen.reduced_decode_seeds('D1', master=pilot.EVAL_MASTER), set(),
        master=pilot.EVAL_MASTER, chains=held.chains, interventions=held.interventions, canaries=held.canaries)
    require(reduced.reportable, 'fitted_reduction_not_reportable:' + repr(reduced.issues))
    return dict(accounting=asdict(reduced.accounting), issues=reduced.issues,
                metrics={name: getattr(reduced.metrics, name) for name in comparison.METRICS})


def compare_readouts(original, reloaded, *, original_metrics, reloaded_metrics):
    """Compare retained public captures, not timing/diagnostic tensor sidecars."""
    def captures(observed):
        return [dict(state_id=call.state_id, slot=call.slot, physical_call=call.physical_call,
                     actor_call_index=call.actor_call_index, request=call.request,
                     generation=call.generation) for call in observed.calls]

    previous, current = captures(original), captures(reloaded)
    mismatches = [index for index in range(max(len(previous), len(current)))
                  if index >= len(previous) or index >= len(current)
                  or pilot._json_bytes(previous[index]) != pilot._json_bytes(current[index])]
    return dict(exact_captures_equal=not mismatches, mismatched_call_indexes=mismatches,
        original_calls=len(previous), reloaded_calls=len(current),
        original_capture_sha256=sha256(pilot._json_bytes(previous)).hexdigest(),
        reloaded_capture_sha256=sha256(pilot._json_bytes(current)).hexdigest(),
        exact_metrics_accounting_equal=pilot._json_bytes(original_metrics) == pilot._json_bytes(reloaded_metrics))


def run(options, *, libraries=None, clock=time.time):
    started = clock()
    root, original = Path(options.output), Path(options.original_run)
    require(not root.resolve().is_relative_to(original.resolve())
            and not original.resolve().is_relative_to(root.resolve()), 'separate_output_directory_required')
    root.mkdir(exist_ok=False)
    summary = dict(status='INCOMPLETE', claim=CLAIM, started_unix=started, pid=os.getpid(),
        master_hex=pilot.EVAL_MASTER.hex(), fitted_state_id=pilot.FITTED_ID,
        checkpoint_kind=CHECKPOINT_KIND, new_updates=0, base_rerun=False,
        process_evidence='Explicit CLI process; original pilot does not retain its PID',
        limitations=['Same held panel, not new transfer.', 'No optimizer/full-state resume.',
                     'No scientific promotion.', 'Hard-killed processes may lack terminal JSON; inspect custody.'])
    hook = None

    def check(phase):
        summary['phase'] = phase
        require(type(options.deadline_unix) in (int, float) and math.isfinite(options.deadline_unix)
                and clock() < options.deadline_unix <= started + pilot.MAX_SECONDS,
                'finite_max_5400s_deadline:' + phase)

    try:
        check('preflight')
        pilot.collector.write_json(root / 'REQUEST.json', vars(options))
        evidence = load_original(original, result_sha256=options.result_sha256,
                                 training_sha256=options.training_sha256)
        summary['original'] = evidence
        values, request = evidence['result']['values'], evidence['request']['values']
        require(started >= values['finished_unix'], 'original_must_complete_before_reload')
        require(type(options.gpu_uuid) is str and options.gpu_uuid.startswith('GPU-')
                and ',' not in options.gpu_uuid and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid,
                'one_explicit_gpu_required')
        check('native_imports')
        if libraries is None:
            import torch
            import peft
            import transformers
        else:
            torch, peft, transformers = libraries
        require(all(str(library.__version__) == pilot.tokens.RUNTIME_VERSIONS[name]
                    for name, library in (('torch', torch), ('peft', peft), ('transformers', transformers))),
                'native_runtime_changed')
        require(not torch.cuda.is_initialized(), 'fresh_exclusive_process_required')
        summary['runtime'] = {name: str(library.__version__) for name, library in
                              (('torch', torch), ('peft', peft), ('transformers', transformers))}
        summary['cuda_initialized_at_entry'] = False
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        check('held_and_original_replay')
        held = pilot.prepare.prepare_reduced_held(bound_allocation=pilot.prepare.allocate_source(master=pilot.EVAL_MASTER))
        require(held.receipt_sha256 == values['eval_held_sha256'], 'original_held_binding_mismatch')
        original_run = replay.replay_state(original / 'FITTED', state_id=pilot.FITTED_ID,
                                            master=pilot.EVAL_MASTER, held=held)
        original_metrics = _reduce(original_run, held)
        pilot._same(original_metrics, values['screens']['FITTED'], 'original_fitted_metrics_mismatch')
        official_path = Path(pilot.tokens.__file__).resolve().parents[1] / (
            'research_notes/astra_memos/receipts_20260912/astra_qwen_public_binding_receipt_20260913_attempt1.json')
        official = _document(official_path, pilot.tokens.OFFICIAL_RECEIPT_SHA256)['values']
        check('tokenizer')
        tokenizer = transformers.AutoTokenizer.from_pretrained(request['model_dir'], local_files_only=True,
            trust_remote_code=False, use_fast=True, padding_side='right')
        summary['tokenizer'] = pilot.tokens.restore_official_backend(tokenizer, request['model_dir'],
                                                                    official['files'], root / 'backend')
        for key in ('after_sha256', 'official_sha256', 'wrapper', 'chat_template_return_dict'):
            pilot._same(summary['tokenizer'][key], values['tokenizer'][key], 'original_tokenizer_mismatch:' + key)
        check('base_load')
        base = transformers.AutoModelForCausalLM.from_pretrained(request['model_dir'], local_files_only=True,
            trust_remote_code=False, torch_dtype=torch.bfloat16, device_map=None,
            attn_implementation='sdpa', use_safetensors=True)
        initialized = pilot.initialize_student(base, torch=torch, peft=peft, directory=root / 'initial',
                                              expected_base_sha256=request['expected_base_sha256'])
        check('restore_saved_adapter')
        summary['adapter_pre'] = restore_saved_adapter(initialized, original / 'adapter', torch=torch,
                                                       peft=peft, expected_sha256=values['adapter_sha256'])
        model = initialized.model
        pilot.training._validate_model(model, initialized.observation.trainable_roster,
                                       initialized.observation.layer_count, 'default')
        model.requires_grad_(False)
        check('placement')
        torch.cuda.init()
        require(torch.cuda.device_count() == 1, 'exactly_one_visible_gpu_required')
        properties = torch.cuda.get_device_properties(0)
        summary['device'] = dict(name=properties.name, total_memory=properties.total_memory, uuid=options.gpu_uuid)
        model.to('cuda:0')
        hook = model.register_forward_pre_hook(lambda module, inputs: check('forward'))
        summary['base_pre'] = pilot.models.verify_retained_base(initialized, base_state_hash=pilot._state_hash)
        observed = pilot._evaluate(initialized, tokenizer, held, torch=torch, directory=root / 'FITTED',
                                   state_id=pilot.FITTED_ID, check=check)
        summary['fitted'] = _reduce(observed, held)
        summary['comparison'] = compare_readouts(original_run, observed,
            original_metrics=original_metrics, reloaded_metrics=summary['fitted'])
        summary['adapter_post'] = pilot.training.adapter_sha256(model, initialized.observation.trainable_roster)
        summary['base_post'] = pilot.models.verify_retained_base(initialized, base_state_hash=pilot._state_hash)
        require(summary['adapter_post'] == summary['adapter_pre'], 'readout_changed_adapter')
        check('source_recheck')
        require(evidence == load_original(original, result_sha256=options.result_sha256,
                                          training_sha256=options.training_sha256), 'original_evidence_changed')
        equal = summary['comparison']['exact_captures_equal'] and summary['comparison']['exact_metrics_accounting_equal']
        summary.update(status='SAVED_ADAPTER_READOUT_EXACT_MATCH' if equal else 'SAVED_ADAPTER_READOUT_MISMATCH',
                       finished_unix=clock())
        pilot.collector.write_json(root / 'RESULT.json', summary)
        return summary
    except BaseException as error:
        summary.update(status='FAILED_NO_COMPLETION', error_type=type(error).__name__, error=str(error),
                       finished_unix=clock())
        pilot.collector.write_json(root / 'FAILED.json', summary)
        raise
    finally:
        if hook is not None:
            hook.remove()
        for path in root.rglob('*'):
            if path.is_file() and not path.is_symlink():
                path.chmod(0o444)
        for path in sorted(root.rglob('*'), reverse=True):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o555)
        root.chmod(0o555)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original-run', 'output', 'gpu-uuid', 'result-sha256', 'training-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--deadline-unix', required=True, type=float)
    return parser.parse_args(argv)


if __name__ == '__main__':
    result = run(parse_args())
    raise SystemExit(0 if result['status'] == 'SAVED_ADAPTER_READOUT_EXACT_MATCH' else 1)
