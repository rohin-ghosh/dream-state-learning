"""CPU-only test fixtures using hash-verified original receiving transition code."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

from research_loop.workers.post_recovery_node2_sleep_20260919 import restart_contract as contract


EVIDENCE = Path(__file__).resolve().parents[1] / 'replay_validation/source_evidence_1789790199409689539'
SOURCE_PINS = {
    'organism_v6/orch_r124_train_history.py': '1211c8f312f8572dd51938ffde4806f7171e6368f1c5ea12a296ff02567e4625',
    'organism_v6/orch_r125_continual_stream.py': '8f22a5754a0cf3a806d552064fe25d4069021e74fff3329c5a7e74e3d226ca33',
    'gpu/orch_r125_stream_journal.py': '0b0d309cbb0399be3b9488fab0eb049063e321b927bf5b4b2c43369448bdf06f',
    'gpu/orch_r125_continual_native.py': '4092dd4355dbb4c6d2ecbcb2f48ad08b23af4e37817b949c54ad31d6f5bc03c0',
}


def load_receiving_sources(life='C0'):
    modules = []
    with patch.dict(sys.modules):
        for relative, expected in SOURCE_PINS.items():
            path = EVIDENCE / life / relative
            raw = path.read_bytes()
            contract.require(hashlib.sha256(raw).hexdigest() == expected, 'pinned_receiving_source')
            if relative.endswith('continual_native.py'):
                tree = ast.parse(raw, filename=str(path))
                finish = next(item for item in tree.body if isinstance(item, ast.FunctionDef)
                    and item.name == 'finish_sleep')
                namespace = dict(require=contract.require, digest=contract.digest)
                exec(compile(ast.Module(body=[finish], type_ignores=[]), str(path), 'exec'), namespace)
                original_finish = namespace['finish_sleep']
            else:
                name = relative.removesuffix('.py').replace('/', '.')
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                modules.append(module)
    return SimpleNamespace(history=modules[0], stream=modules[1], journal=modules[2],
        original_finish=original_finish)


def record(index, kind, document, previous='0' * 64):
    result = dict(index=index, journal_id='a' * 32, kind=kind, document=deepcopy(document),
        previous_sha256=previous)
    result['sha256'] = contract.digest(result)
    return result


class ReceivingJournal:
    """In-memory I/O with the unmodified original _advance validation body."""
    def __init__(self, sources, pending, head):
        self.original = sources.journal.StreamJournal.__new__(sources.journal.StreamJournal)
        before = deepcopy(pending['document']['resume_state'])
        before['state']['pending'] = None
        before['sha256'] = contract.digest(before['state'])
        self.state = dict(index=pending['index'], previous=pending['previous_sha256'],
            latest=self.original._checkpoint(before), request=None, response=None,
            sleep_request=None, inbox={})
        self.original._advance(self.state, 'SLEEP_REQUEST', pending['document'])
        self.state.update(index=head['index'] + 1, previous=head['sha256'])
        self.records = []
        self.fail_kind = None

    def audit(self):
        return dict(record_count=self.state['index'], head_sha256=self.state['previous'])

    def latest_checkpoint(self):
        return deepcopy(self.state['latest'])

    def record(self, kind, document):
        if kind == self.fail_kind:
            raise OSError('synthetic_publication_failure')
        self.original._advance(self.state, kind, document)
        result = record(self.state['index'], kind, document, self.state['previous'])
        self.state.update(index=result['index'] + 1, previous=result['sha256'])
        self.records.append(result)
        return dict(index=result['index'], sha256=result['sha256'])


def make_checkpoint(directory, *, steps, experiment, adapter_state=None):
    directory.mkdir(parents=True, exist_ok=False)
    adapter = directory / 'adapter'
    adapter.mkdir()
    (adapter / 'fixture.bin').write_bytes(f'synthetic_adapter_{steps}'.encode())
    optimizer = directory / 'optimizer_rng.pt'
    optimizer.write_bytes(f'synthetic_optimizer_python_CPU_CUDA_RNG_{steps}'.encode())
    files = {'fixture.bin': hashlib.sha256((adapter / 'fixture.bin').read_bytes()).hexdigest()}
    optimizer_sha = hashlib.sha256(optimizer.read_bytes()).hexdigest()
    result = dict(adapter_path=str(adapter), optimizer_rng_path=str(optimizer),
        adapter_files=files, base_sha256='a' * 64,
        checkpoint_sha256=dict(adapter=contract.digest(files), optimizer=optimizer_sha, rng=optimizer_sha),
        optimizer_steps=steps, experiment=deepcopy(experiment),
        adapter_state_sha256=adapter_state or contract.digest(['synthetic_adapter_state', steps]))
    (directory / 'COMMIT.json').write_text(json.dumps(result))
    return result


def build_fixture(root, life, sources):
    saved_steps, frontier, saved_cycle, complete_index, pending_index, count = (
        (8412, 441, 145, 6631, 6660, 48) if life == 'C0'
        else (9644, 450, 146, 7750, 7776, 29))
    plan = dict(root=str(root), new_presentations=16, rehearsal_presentations=0,
        learn_row_policy=contract.ROW_POLICY,
        think_act_learn=dict(learn_row_policy=contract.ROW_POLICY),
        hard_end_unix=1789927200, seed=1, system_prompt='fixture system', birth_prompt='fixture birth',
        presleep_variant='free_distillation',
        compaction_invitation=sources.stream.PRESLEEP_INVITATIONS['free_distillation'])
    experiment = sources.stream.experiment_binding(plan)
    checkpoint = make_checkpoint(root / 'checkpoints' / f'sleep_{saved_cycle:06d}',
        steps=saved_steps, experiment=experiment)
    history = sources.history.TrainHistory(system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
    event = sources.history.TrainEvent(event_id='child:working', actor='child', text='keep all my work',
        split='TRAIN', phase='experience', episode_id='continual_stream', source_id='fixture',
        source_sha256=contract.digest('working-source'), origin='TRAIN_COLLECTION')
    history.append(event)
    history.update_working_state(event, entries=[sources.history.WorkingStateSpan(
        id='remember', kind='note', start=0, end=len(event.text))])
    stream = sources.stream.ContinualStream(history, context_limit=2048, segment_tokens=16,
        segments_per_sleep=3, deadline_unix=plan['hard_end_unix'],
        model_state_sha256=contract.digest(checkpoint['checkpoint_sha256']), experiment=experiment)
    rows = [dict(segment=position, split='TRAIN', actor='child', event_id=f'fixture:{position}',
        prefix=[dict(role='user', content='retain masked context')], target=f'raw child {position}',
        token_ids=[position + 1], append_eos=False, prefix_loss=False, target_loss=True,
        source_sha256=contract.digest(['row', position]), model_state_sha256=stream.model_state_sha256,
        terminal=True, truncated=False) for position in range(frontier + 3)]
    stream.rows = deepcopy(rows[:frontier])
    stream.sleep_frontier = frontier
    stream.sleep_receipts = [dict(status='COMPLETE', cycle=saved_cycle)]
    complete = record(complete_index, 'SLEEP_COMPLETE', dict(status='COMPLETE', cycle=saved_cycle,
        checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'],
        total_optimizer_steps=saved_steps, resume_state=stream.checkpoint()))
    stream.rows = deepcopy(rows)
    pending_sources = [row['source_sha256'] for row in rows[frontier:]]
    stream.pending = 'sleep:' + contract.digest(pending_sources)
    pending = record(pending_index, 'SLEEP_REQUEST', dict(cycle=saved_cycle + 1, resume_state=stream.checkpoint()))
    recipe = record(pending_index + 1, 'SLEEP_RECIPE', dict(policy='R181_NEW_ONLY_V1',
        new_presentations=16, new_rows=3, available_old_rows=frontier, selected_old_rows=0,
        learn_row_policy=contract.ROW_POLICY, active_semantic_filters=[], semantic_row_exclusion=False), pending['sha256'])
    eligibility = record(pending_index + 2, 'TARGET_ELIGIBILITY', dict(new_row_sha256=pending_sources,
        rehearsal_row_sha256=[], excluded=[], raw_modified=False, learn_row_policy=contract.ROW_POLICY,
        active_semantic_filters=[], semantic_row_exclusion=False), recipe['sha256'])
    updates = []
    previous = eligibility
    for position in range(count):
        previous = record(pending_index + 3 + position, 'UPDATE', dict(optimizer_step=saved_steps + position + 1,
            source_sha256=pending_sources[position % 3], losses=[], finished_unix=1000 + position), previous['sha256'])
        updates.append(previous)
    return SimpleNamespace(plan=plan, plan_bytes=json.dumps(plan).encode(), complete=complete,
        pending=pending, recipe=recipe, eligibility=eligibility, updates=updates, checkpoint=checkpoint,
        journal=ReceivingJournal(sources, pending, updates[-1]), sources=sources, root=root)


def make_native(fixture):
    instances = []
    behavior = SimpleNamespace(fail_at_step=None, raise_after_step=None, steps=48,
        fail_save=False, missing_commit=False, corrupt_commit=False,
        recipe_change=None, eligibility_change=None, wrong_counter=False,
        receipt_change=None, init_step_delta=0)

    class CPUChild:
        def __init__(self, plan, checkpoint):
            self.plan = plan
            self.input_checkpoint = deepcopy(checkpoint)
            self.optimizer_steps = checkpoint['optimizer_steps'] + behavior.init_step_delta
            self.rng_source_bytes = Path(checkpoint['optimizer_rng_path']).read_bytes()
            self.saved_adapter = checkpoint['adapter_state_sha256']
            self.start_steps = self.optimizer_steps
            self.calls = []
            instances.append(self)

        @staticmethod
        def verify_checkpoint(checkpoint):
            optimizer_sha = hashlib.sha256(Path(checkpoint['optimizer_rng_path']).read_bytes()).hexdigest()
            files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in Path(checkpoint['adapter_path']).iterdir()}
            contract.require(optimizer_sha == checkpoint['checkpoint_sha256']['optimizer']
                == checkpoint['checkpoint_sha256']['rng'] and files == checkpoint['adapter_files']
                and contract.digest(files) == checkpoint['checkpoint_sha256']['adapter'], 'binary_file_binding')

        def adapter_hash(self):
            return self.saved_adapter if self.optimizer_steps == self.start_steps else contract.digest(['recovery', self.optimizer_steps])

        def sleep(self, new_rows, old_rows, anchors, publish):
            self.calls.append(dict(new_rows=deepcopy(new_rows), old_rows=deepcopy(old_rows), anchors=anchors))
            recipe = deepcopy(fixture.recipe['document'])
            recipe.update(behavior.recipe_change or {})
            publish('SLEEP_RECIPE', recipe)
            eligibility = deepcopy(fixture.eligibility['document'])
            eligibility.update(behavior.eligibility_change or {})
            publish('TARGET_ELIGIBILITY', eligibility)
            counts = {}
            for position in range(behavior.steps):
                if behavior.fail_at_step == position:
                    raise RuntimeError('synthetic_training_failure')
                self.optimizer_steps += 1
                if behavior.raise_after_step == position:
                    raise RuntimeError('synthetic_mutation_before_publication_failure')
                source = new_rows[position % len(new_rows)]['source_sha256']
                counts[source] = counts.get(source, 0) + 1
                publish('UPDATE', dict(optimizer_step=self.optimizer_steps + int(behavior.wrong_counter),
                    source_sha256=source, losses=[], finished_unix=10000 + position))
            result = dict(optimizer_steps=self.optimizer_steps - self.start_steps,
                total_optimizer_steps=self.optimizer_steps, before_adapter_sha256=self.saved_adapter,
                after_adapter_sha256=self.adapter_hash(), frozen_base_verified=True,
                presentations=counts, excluded_rows=[], child_token_exposures=48, anchor_token_exposures=192)
            result.update(behavior.receipt_change or {})
            return result

        def checkpoint(self, directory):
            if behavior.fail_save:
                directory.mkdir()
                (directory / 'optimizer_rng.pt').write_bytes(b'incomplete-new-recovery')
                raise OSError('synthetic_ENOSPC')
            result = make_checkpoint(directory, steps=self.optimizer_steps,
                experiment=fixture.checkpoint['experiment'], adapter_state=self.adapter_hash())
            if behavior.missing_commit:
                (directory / 'COMMIT.json').unlink()
            if behavior.corrupt_commit:
                (directory / 'COMMIT.json').write_text('{}')
            return result

    return SimpleNamespace(NativeChild=CPUChild, ContinualStream=fixture.sources.stream.ContinualStream,
        verify_experiment_resume=fixture.sources.stream.verify_experiment_resume,
        instances=instances, behavior=behavior)
