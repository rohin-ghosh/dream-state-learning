"""Summarize saved goal-pair capsules without models or independent authentication.

Counts and scores are reported from saved documents, not rescored trajectories.
File/content matches do not authenticate tensors, custody, or native execution.
Missing, malformed, failed and unfinished stages remain visible in the output.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path


SCHEMA = 'DEV_GOAL_PAIR_COMPARISON_SUMMARY_V1'
DRIVER_SCHEMA = 'DEV_GOAL_PAIR_INCREMENTAL_FIT_V1'
ARMS = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')
PARENT_STATE = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
GROUPS = ('memory_rows', 'cue_rows', 'audit_rows', 'trajectory_rows', 'new_trajectory_rows')
GROUP_SIZES = (128, 20, 62, 12, 48)
ENGINEERING_TARGETS = dict(probe_pairs='at least 3/4 PROBE OWN_TEXT strict pairs',
    each_probe_world='at least 1/2 strict pairs in each PROBE world', old_w0='at least 15/16',
    old_w8='at least 15/16', audit='at least 15/16', taught='at least 3/4 OWN_TEXT',
    previous_fresh='at least 3/4 OWN_TEXT')
LIMITATION = ('Saved-document analysis only: no independent tensor/custody/native-call authentication, '
              'no trajectory rescoring, no independent learners, no clean-lineage or H1/H2 claim.')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def match(*values):
    return None if any(value is None for value in values) else all(value == values[0] for value in values[1:])


def reject_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


class Reader:
    def __init__(self, root):
        self.root = Path(root)
        self.references = {}
        self.issues = []

    def read(self, relative, *, text=False):
        relative = str(relative)
        path = self.root / relative
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            self.references[relative] = dict(status='MISSING')
            return None
        except OSError as error:
            self.references[relative] = dict(status='UNREADABLE', error=str(error))
            self.issues.append(dict(path=relative, error=str(error)))
            return None
        reference = dict(status='READ', sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        self.references[relative] = reference
        try:
            content = raw.decode('utf-8')
            return content if text else json.loads(content, parse_constant=reject_constant)
        except (ValueError, UnicodeError) as error:
            reference.update(status='MALFORMED', error=str(error))
            self.issues.append(dict(path=relative, error=str(error)))
            return None

    def document(self, relative):
        value = self.read(relative)
        if value is not None and not isinstance(value, dict):
            self.issues.append(dict(path=str(relative), error='expected JSON object'))
            return None
        return value


def stage(reader, relative, phase, arm=None):
    directory = reader.root / relative
    complete = reader.document(relative / 'RESULT.json')
    failed = reader.document(relative / 'FAILED.json')
    request = reader.document(relative / 'REQUEST.json')
    states = reader.document(relative / 'STATES.json')
    failed_exists = (directory / 'FAILED.json').exists()
    result = failed if failed_exists else complete
    record = result or request or {}
    status = ('FAILED' if failed_exists else complete.get('status', 'UNKNOWN') if complete is not None
              else 'NOT_YET_TERMINAL' if directory.exists() else 'NOT_STARTED')
    started, finished = record.get('started_unix'), record.get('finished_unix')
    valid_times = all(type(value) in (int, float) and math.isfinite(value) for value in (started, finished))
    losses = reader.read(relative / 'LOSSES.jsonl', text=True) if phase == 'train' else None
    checks = dict(schema=match(record.get('schema'), DRIVER_SCHEMA), phase=match(record.get('phase'), phase))
    if arm:
        checks['arm'] = match(record.get('arm'), arm)
    return dict(status=status, recorded_status=record.get('status'), failed_marker=failed_exists,
        result_and_failure_present=failed_exists and complete is not None, identity_matches=checks,
        error=record.get('error'), failure_verification_error=record.get('failure_verification_error'),
        loaded_state=record.get('loaded_adapter_state_sha256'), saved_state=record.get('adapter_state_after'),
        states=states, frozen_base_unchanged_reported=record.get('frozen_base_unchanged'),
        fits=record.get('fits'), updates=record.get('updates'), completed_updates_reported=record.get('completed_updates'),
        observed_loss_lines=None if losses is None else len([line for line in losses.splitlines() if line.strip()]),
        calls=dict(reported=record.get('model_calls'), saved_call_files=len(list(directory.glob('CALL_*.json'))),
                   cap=record.get('max_native_calls'), roles=record.get('role_calls')),
        started_unix=started, finished_unix=finished,
        wall_seconds=finished - started if valid_times and finished >= started else None), record


def counts_from_files(reader, pattern, field):
    records = [reader.document(path.relative_to(reader.root)) for path in sorted(reader.root.glob(pattern))]
    scores = []
    for record in records:
        value = record
        for key in field:
            value = value.get(key) if isinstance(value, dict) else None
        scores.append(value)
    valid = [score for score in scores if type(score) is bool]
    return None if not records else dict(correct=sum(valid), observed_denominator=len(valid),
        observed_files=len(records), completeness='PARTIAL_ARTIFACT_COUNTS_NOT_FULL_PANEL')


def panel_summary(panel):
    measured = panel.get('summary') or {}
    tasks = panel.get('tasks') or []
    return dict(master=panel.get('master'), condition=panel.get('condition'),
        individual=measured.get('individual'), paired=measured.get('paired'), pairs=measured.get('pairs'),
        tasks=[{key: task.get(key) for key in ('task_index', 'failure', 'terminal', 'actual_first_port', 'source_first_port')}
               for task in tasks if isinstance(task, dict)],
        collection_sha256=panel.get('collection_sha256'), shared_text_sha256=panel.get('shared_text_sha256'))


def readout(reader, relative, result):
    summary = reader.document(relative / 'SUMMARY.json')
    saved = summary if summary is not None else result
    panels = saved.get('panels')
    if not isinstance(panels, dict):
        panels = {split: [reader.document(path.relative_to(reader.root))
                          for path in sorted((reader.root / relative).glob(split + '_*_SUMMARY.json'))]
                  for split in ('TRAIN', 'PROBE')}
    actual = {split: [] for split in ('TRAIN', 'PROBE')}
    for split in actual:
        for panel in panels.get(split) or []:
            if not isinstance(panel, dict):
                continue
            actual[split].append(panel_summary(panel))
    references = saved.get('deterministic_first_port')
    if references is None:
        references = [reader.document(path.relative_to(reader.root))
                      for path in sorted((reader.root / relative).glob('PROBE_*_FIRST_PORT_REFERENCE.json'))]
    retention = saved.get('old_recall')
    if retention is None:
        retention = {str(view): counts_from_files(reader, str(relative / f'OLD_RECALL_W{view}_*.json'), ('correct',))
                     for view in (0, 8)}
    audited = saved.get('held_audit')
    if audited is None:
        audit = reader.document(relative / 'HELD_AUDIT.json')
        audited = audit.get('summary') if audit else None
    graphs = {}
    for field, graph in (('taught_graph', 'TAUGHT'), ('previous_fresh_graph', 'PREVIOUS_FRESH')):
        graphs[field] = saved.get(field)
        if graphs[field] is None:
            partial = counts_from_files(reader, str(relative / f'{graph}_OWN_TEXT_EPISODE_*.json'), ('score', 'correct'))
            graphs[field] = None if partial is None else dict(OWN_TEXT=partial)
    baseline = saved.get('baseline')
    return dict(label='ACTUAL_CHILD_READOUT_REPORTED_NOT_REEXECUTED', panels=actual, primary=saved.get('primary'),
        reused_37ec_probe_baseline=dict(label='REUSED_37EC_BASELINE_NOT_INDEPENDENT_LEARNER',
            panels=None if baseline is None else [panel_summary(panel) for panel in baseline if isinstance(panel, dict)]),
        deterministic_first_port=dict(label='ALGORITHMIC_REFERENCE_NOT_CHILD_NATIVE_OUTPUT',
            worlds=[{key: reference.get(key) for key in ('master', 'policy', 'native_calls', 'summary')}
                    for reference in references if isinstance(reference, dict)]),
        retention=dict(old_recall=retention, held_audit=audited, original_taught_text=graphs['taught_graph'],
                       previous_fresh_text=graphs['previous_fresh_graph']),
        engineering=dict(targets=ENGINEERING_TARGETS, reported_checks=saved.get('engineering_checks'),
                         reported_target_met=saved.get('engineering_target_met')),
        summary_matches_result=None if summary is None or not result.get('panels') else all(
            result.get(key) == value for key, value in summary.items()))


def row_counts(material):
    return ({key: len(material[key]) if isinstance(material.get(key), list) else None for key in GROUPS}
            if isinstance(material, dict) else None)


def mask_control_matches(reference, actual, arm):
    if reference is None or actual is None:
        return None
    if not isinstance(reference, list) or not isinstance(actual, list) or len(reference) != 270 or len(actual) != 270:
        return False
    for index, (full, controlled) in enumerate(zip(reference, actual)):
        if not isinstance(full, dict) or not isinstance(controlled, dict) or not isinstance(full.get('labels'), list):
            return False
        expected = dict(full)
        if arm == ARMS[1] and index >= 222:
            expected['labels'] = [-100] * len(full['labels'])
        if controlled != expected:
            return False
    return True


def summarize(root):
    reader = Reader(root)
    prepared, preparation = stage(reader, Path('prepare'), 'prepare')
    prepared_rows = reader.read('prepare/TRAINING_ROWS.json')
    prepared_recipes = reader.document('prepare/RECIPES.json') or {}
    prepared_binding = reader.document('prepare/INPUTS.json')
    arms, materials, references, recipes = {}, [], [], []
    for arm in ARMS:
        train_path, after_path = Path(arm) / 'train', Path(arm) / 'after'
        train, trained = stage(reader, train_path, 'train', arm)
        after, evaluated = stage(reader, after_path, 'after', arm)
        material = reader.read(train_path / 'TRAINING_ROWS.json')
        reference = reader.read(train_path / 'REFERENCE_MASKS.json')
        controlled = reader.read(train_path / 'MASKS.json')
        recipe = reader.document(train_path / 'RECIPE.json')
        materials.append(material)
        references.append(reference)
        recipes.append(recipe)
        train_hash = reader.references[str(train_path / 'RESULT.json')].get('sha256')
        states = train['states'] or {}
        after_states = after['states'] or {}
        arms[arm] = dict(train=train, after=after, measurements=readout(reader, after_path, evaluated),
            saved_material=dict(row_counts=row_counts(material), content_sha256=None if material is None else digest(material),
                reference_mask_rows=len(reference) if isinstance(reference, list) else None,
                recipe=None if recipe is None else {**{key: value for key, value in recipe.items() if key != 'schedule'},
                    'schedule_length': len(recipe['schedule']) if isinstance(recipe.get('schedule'), list) else None,
                    'schedule_content_sha256': None if recipe.get('schedule') is None else digest(recipe['schedule'])},
                actual_supervised_tokens=trained.get('actual_supervised_tokens'),
                reference_supervised_tokens=trained.get('reference_supervised_tokens')),
            matches=dict(rows_to_prepared=match(material, prepared_rows),
                row_layout_270=match(row_counts(material), dict(zip(GROUPS, GROUP_SIZES))),
                reference_mask_count_270=None if reference is None else isinstance(reference, list) and len(reference) == 270,
                controlled_masks=mask_control_matches(reference, controlled, arm),
                recipe_to_prepared=match(recipe, prepared_recipes.get(arm)),
                initial_37ec=match(train['loaded_state'], (recipe or {}).get('initial_state'),
                                   (trained.get('binding') or {}).get('initial_state'), PARENT_STATE),
                train_states_file=match(states.get('before'), train['loaded_state']) if states else None,
                train_saved_state=match(states.get('after'), train['saved_state']),
                trained_state_changed=None if train['saved_state'] is None or train['loaded_state'] is None
                else train['saved_state'] != train['loaded_state'],
                after_loaded_training_state=match(train['saved_state'], after['loaded_state']),
                after_readonly_state=match(after['loaded_state'], after['saved_state'],
                                           after_states.get('before'), after_states.get('after')),
                after_training_result_sha=match(evaluated.get('training_result_sha256'), train_hash),
                prepared_binding=match(prepared_binding, trained.get('binding'), evaluated.get('binding'))))
    statuses = [arms[arm][phase]['status'] for arm in ARMS for phase in ('train', 'after')]
    comparison = dict(training_rows=match(*materials), reference_masks=match(*references),
        schedule=match(*(recipe.get('schedule') if recipe else None for recipe in recipes)),
        initial_37ec=match(*(arms[arm]['train']['loaded_state'] for arm in ARMS), PARENT_STATE))
    for name, filename in (('training_rows_bytes', 'TRAINING_ROWS.json'), ('reference_masks_bytes', 'REFERENCE_MASKS.json')):
        comparison[name] = match(*(reader.references[str(Path(arm) / 'train' / filename)].get('sha256') for arm in ARMS))
    for name in ('learning_rate', 'seed', 'rank', 'optimizer', 'optimizer_kwargs', 'updates', 'batch_size', 'loss'):
        comparison[name] = match(*(recipe.get(name) if recipe else None for recipe in recipes))
    commit = reader.read('source_commit.txt', text=True)
    reader.read('source/gpu/astra_goal_pair_train.py', text=True)
    reader.read('source/organism_v6/experienced_event_goal_pairs.py', text=True)
    local_driver = Path(__file__).with_name('astra_goal_pair_train.py')
    failures = (['prepare'] if prepared['status'] == 'FAILED' else []) + [str(Path(arm) / phase)
        for arm in ARMS for phase in ('train', 'after') if arms[arm][phase]['status'] == 'FAILED']
    return dict(schema=SCHEMA, root=str(Path(root)), limitation=LIMITATION,
        status='FAILED' if failures else 'COMPLETE' if all(status == 'COMPLETE' for status in statuses)
        else 'NOT_YET_TERMINAL', all_runtime_stages_complete=all(status == 'COMPLETE' for status in statuses),
        prepared=prepared, prepared_initial_state=(prepared_binding or {}).get('initial_state'),
        prepared_row_counts=row_counts(prepared_rows), arms=arms, cross_arm_saved_matches=comparison,
        failed_stages=failures,
        source=dict(recorded_commit=None if commit is None else commit.strip(),
            analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            local_driver_schema_reference_sha256=hashlib.sha256(local_driver.read_bytes()).hexdigest()
            if local_driver.exists() else None, recorded_entry_sha256=preparation.get('entry_sha256'),
            prepared_binding_references={key: value for key, value in (prepared_binding or {}).items()
                                         if key.endswith('_sha256')}),
        input_references=reader.references, read_issues=reader.issues)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    options = parser.parse_args(argv)
    result = summarize(options.root)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return result


if __name__ == '__main__':
    main()
