"""CPU-only exact-source integration and complete saved-state roundtrip proof."""

import argparse
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def presleep_function(native):
    if hasattr(native, 'prepare_sleep'):
        return native.prepare_sleep, 'ACTUAL_PREPARE_SLEEP'
    tree = ast.parse(Path(native.__file__).read_text())
    candidates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        starts = [index for index, item in enumerate(node.body) if isinstance(item, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'invitation' for target in item.targets)]
        ends = [index for index, item in enumerate(node.body) if isinstance(item, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'new_rows' for target in item.targets)]
        if len(starts) == len(ends) == 1 and starts[0] < ends[0]:
            candidates.append(node.body[starts[0]:ends[0]])
    require(len(candidates) == 1, 'one_exact_inline_presleep_block')
    function = ast.parse('def actual_inline(child, stream, journal, cycle):\n    pass\n').body[0]
    function.body = candidates[0]
    namespace = dict(vars(native))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 '<actual-native-inline-presleep>', 'exec'), namespace)
    return namespace['actual_inline'], 'ACTUAL_INLINE_AST_EXECUTED'


def prove(source, predecessor, plan_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment')
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r179_context_survival as policy
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    from organism_v6.orch_r125_plain_context import VERSION
    import torch
    require(Path(native.__file__).resolve() == source / 'gpu/orch_r125_continual_native.py', 'actual_successor_import')
    require(Path(policy.__file__).resolve() == source / 'gpu/orch_r179_context_survival.py', 'actual_policy_import')
    require(policy.patch_native((predecessor / 'gpu/orch_r125_continual_native.py').read_text()) ==
            Path(native.__file__).read_text(), 'only_exact_Main_patch')
    prepare, integration = presleep_function(native)
    plan = json.loads(plan_path.read_text())
    results = []
    for prompt_tokens in (20, 12287, 12288, 15000):
        for empty in (False, True):
            with tempfile.TemporaryDirectory(prefix='r179-node4-cpu-') as directory:
                history = TrainHistory(system_prompt='Fixture purpose', birth_prompt='Fixture birth')
                stream = ContinualStream(history, context_limit=16384, segment_tokens=512,
                    segments_per_sleep=2, deadline_unix=time.time() + 300,
                    model_state_sha256='a' * 64, allow_eviction=True)
                stream.set_presentation(dict(version=VERSION, system_prompt='Fixture purpose',
                    birth_prompt='Fixture birth'), 16384)
                prompts = []

                def count(messages):
                    return prompt_tokens

                def generate(messages, **options):
                    prompts.append(deepcopy(messages))
                    return dict(raw='' if empty else 'Fixture child keeps an unresolved object.',
                        token_ids=[101, 102, 2], terminal=True, truncated=False)

                child = SimpleNamespace(plan=plan, generate=generate, count_tokens=count)
                event = TrainEvent(event_id='fixture-parent', actor='parent', split='TRAIN',
                    phase='experience', episode_id='fixture', source_id='CPU_FIXTURE',
                    source_sha256=digest('fixture-parent'), origin='TRAIN_COLLECTION',
                    text='Fixture parent contributes conditioning only.')
                with StreamJournal(Path(directory) / 'stream', create=True) as journal:
                    stream.step(generate, count, journal.record, incoming=[event])
                    stream.step(generate, count, journal.record)
                    previous_rows = deepcopy(stream.rows)
                    prepare(child, stream, journal, 1)
                    require(stream.rows[:-1] == previous_rows, 'all_previous_rows_unchanged')
                    require(stream.rows[-1]['prefix_loss'] is False and stream.rows[-1]['target_loss'] is True,
                            'same_own_child_target_loss')
                    compact = prompt_tokens >= 12288 and not empty
                    require(len(stream.history.operations) == int(compact), 'only_threshold_compaction')
                    before_history = stream.history.checkpoint()
                    rows = stream.pending_rows()
                    pending = stream.checkpoint()
                    pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in rows])
                    pending['sha256'] = digest(pending['state'])
                    journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
                    saved = stream.commit_sleep(dict(status='COMPLETE', cycle=1, optimizer_steps=1,
                        new_row_sha256=[row['source_sha256'] for row in rows],
                        checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64)), journal.record)
                    restored = ContinualStream.restore(saved, expected_sha256=saved['sha256'])
                    require(restored.checkpoint() == saved and restored.history.checkpoint() == before_history,
                            'all_state_history_masks_frontiers_roundtrip')
                    if not compact:
                        restored.step(generate, count, journal.record)
                        require(any(event.text in message['content'] for message in prompts[-1]),
                                'retained_context_in_actual_postsleep_prompt')
                    results.append(dict(prompt_tokens=prompt_tokens, empty=empty, compact=compact, passed=True))
    require(not torch.cuda.is_initialized(), 'no_model_or_CUDA_calls')
    return dict(status='PASS', cases=len(results), results=results, integration=integration,
                source=str(source), actual_source=True, model_calls=0, cuda_initialized=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'predecessor', 'plan'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prove(args.source, args.predecessor, args.plan), sort_keys=True))
