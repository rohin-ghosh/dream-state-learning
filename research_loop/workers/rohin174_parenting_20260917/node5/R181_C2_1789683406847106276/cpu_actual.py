"""Receiving-host CPU proof against actual predecessor and successor bytes."""

import argparse
import ast
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time
from types import SimpleNamespace


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def policy_tests(plan):
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r179_context_survival as policy
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    from organism_v6.orch_r125_plain_context import VERSION
    results = []
    for mode in ('retain', 'compact', 'empty'):
        with tempfile.TemporaryDirectory(prefix='r179-cpu-') as directory:
            history = TrainHistory(system_prompt='CPU fixture purpose', birth_prompt='CPU fixture birth')
            stream = ContinualStream(history, context_limit=16384, segment_tokens=512,
                segments_per_sleep=2, deadline_unix=time.time() + 300,
                model_state_sha256='a' * 64, allow_eviction=True)
            stream.set_presentation(dict(version=VERSION, system_prompt='CPU fixture purpose',
                                         birth_prompt='CPU fixture birth'), 16384)
            prompts = []

            def count(messages):
                return 12288 if mode == 'compact' else sum(len(message['content'].split()) for message in messages)

            def generate(messages, **options):
                prompts.append(deepcopy(messages))
                return dict(raw='' if mode == 'empty' else 'Fixture child remembers the unresolved object.',
                            token_ids=[101, 102, 2], terminal=True, truncated=False)

            child = SimpleNamespace(plan=plan, count_tokens=count, generate=generate)
            parent = TrainEvent(event_id='fixture-parent', actor='parent', split='TRAIN', phase='experience',
                episode_id='fixture', source_id='CPU_FIXTURE', source_sha256=digest('parent'),
                origin='TRAIN_COLLECTION', text='Fixture parent contribution is conditioning only.')
            with StreamJournal(Path(directory) / 'stream', create=True) as journal:
                stream.step(generate, count, journal.record, incoming=[parent])
                stream.step(generate, count, journal.record)
                prior_rows = deepcopy(stream.rows)
                if hasattr(native, 'prepare_sleep'):
                    native.prepare_sleep(child, stream, journal, 1)
                    integration = 'ACTUAL_PREPARE_SLEEP_EXECUTED'
                else:
                    stream.step(generate, count, journal.record)
                    latest = stream.history.events[-2]
                    if latest.text.strip():
                        summary = replace(latest, event_id='compaction:1', phase='compaction')
                        policy.retain_or_compact(child, stream, journal, summary, 1)
                    integration = 'INLINE_CALL_AST_BOUND_POLICY_EXECUTED'
                require(stream.rows[:-1] == prior_rows, 'prior_learning_rows_unchanged')
                require(stream.rows[-1]['prefix_loss'] is False and stream.rows[-1]['target_loss'] is True,
                        'only_child_target_loss')
                if mode == 'compact':
                    require(len(stream.history.operations) == 1
                            and stream.history.operations[-1]['kind'] == 'compaction', 'threshold_only_compaction')
                else:
                    require(stream.history.operations == (), 'sleep_preserves_active_history')
                before_history = stream.history.checkpoint()
                pending = stream.checkpoint()
                rows = stream.pending_rows()
                pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in rows])
                pending['sha256'] = digest(pending['state'])
                journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
                saved = stream.commit_sleep(dict(status='COMPLETE', cycle=1, optimizer_steps=1,
                    new_row_sha256=[row['source_sha256'] for row in rows],
                    checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64)), journal.record)
                restored = ContinualStream.restore(saved, expected_sha256=saved['sha256'])
                require(restored.checkpoint() == saved and restored.history.checkpoint() == before_history,
                        'complete_history_roundtrip')
                if mode == 'retain':
                    restored.step(generate, count, journal.record)
                    require(any(parent.text in message['content'] for message in prompts[-1]),
                            'post_sleep_parent_context_retained')
                results.append(dict(mode=mode, integration=integration, passed=True))
    return results


def prove(source, original, plan_path, boundary_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment')
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r181_newrows_only as policy
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    import torch
    require(Path(native.__file__).resolve() == source / 'gpu/orch_r125_continual_native.py', 'actual_successor_import')
    old = (original / 'gpu/orch_r125_continual_native.py').read_text()
    patched = (source / 'gpu/orch_r125_continual_native.py').read_text()
    require(policy.patch_native(old) == patched, 'only_exact_Main_patch')
    require(sha(source / 'gpu/orch_r181_newrows_only.py') ==
            'bd154636cc50b3ccf95029b8f0636b7f9cf257327729ec47706afebeddfe995f', 'exact_Main_policy')
    ast.parse(patched)
    plan = json.loads(plan_path.read_bytes())
    require(plan['rehearsal_presentations'] == 0 and plan['new_presentations'] == 16, 'R181_exact_plan')
    rows = [object()]
    require(native.select_rehearsal_rows(plan, rows) == [] and native.select_rehearsal_rows(dict(rehearsal_presentations=1), rows) is rows, 'actual_R181_selection')
    results = policy_tests(plan) if (source / 'gpu/orch_r179_context_survival.py').exists() else [dict(actual_R181_selection=True, original_retelling_preserved_by_exact_native_delta=True)]
    boundary = json.loads(boundary_path.read_bytes())
    envelope = boundary['record']['document']['resume_state']
    restored = ContinualStream.restore(envelope, expected_sha256=envelope['sha256'])
    require(restored.checkpoint() == envelope, 'full_real_saved_state_exact_roundtrip')
    checkpoint = boundary['record']['document']['checkpoint']
    native.NativeChild.verify_checkpoint(checkpoint)
    require(digest(checkpoint['checkpoint_sha256']) == restored.model_state_sha256, 'model_history_binding')
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload.get('experiment') == getattr(restored, 'experiment', None), 'optimizer_experiment_unchanged')
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0
            and payload['optimizer']['state'] and payload['optimizer']['param_groups']
            and payload['parameter_names'], 'full_saved_optimizer_not_reset')
    parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][index]['exp_avg']))
                  for index in range(len(payload['parameter_names']))]
    optimizer = torch.optim.AdamW(parameters)
    optimizer.load_state_dict(payload['optimizer'])
    restored_optimizer = optimizer.state_dict()
    require(restored_optimizer['param_groups'] == payload['optimizer']['param_groups'], 'optimizer_groups_exact')
    for index, values in payload['optimizer']['state'].items():
        for key, value in values.items():
            current = restored_optimizer['state'][index][key]
            require(torch.equal(value, current) if isinstance(value, torch.Tensor) else value == current,
                    'optimizer_tensor_and_step_exact')
    random.setstate(payload['python_rng'])
    require(random.getstate() == payload['python_rng'], 'python_rng_exact')
    torch.set_rng_state(payload['cpu_rng'])
    require(torch.equal(torch.get_rng_state(), payload['cpu_rng']), 'CPU_rng_exact')
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu'
            and payload['cuda_rng'][0].dtype == torch.uint8 and payload['cuda_rng'][0].numel() > 0,
            'saved_single_device_CUDA_rng_preserved_not_initialized')
    require(not torch.cuda.is_initialized(), 'no_GPU_model_or_context')
    return dict(status='PASS', policy_tests=results, optimizer_steps=checkpoint['optimizer_steps'],
        adapter_state_sha256=checkpoint['adapter_state_sha256'], checkpoint_bundle=checkpoint['checkpoint_sha256'],
        full_state_sha256=envelope['sha256'], full_history_sha256=restored.history.checkpoint()['state_sha256'],
        original_native_sha256=sha(original / 'gpu/orch_r125_continual_native.py'),
        successor_native_sha256=sha(source / 'gpu/orch_r125_continual_native.py'),
        optimizer_restored_exact=True, python_CPU_rng_restored_exact=True,
        CUDA_rng_bytes_preserved=True, cuda_initialized=False,
        GPU_restore_test='PENDING_ADMITTED_SUCCESSOR_LOAD', scientific_claim=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('source', 'original', 'plan', 'boundary'):
        parser.add_argument('--' + argument, type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(prove(arguments.source, arguments.original, arguments.plan, arguments.boundary), sort_keys=True))
