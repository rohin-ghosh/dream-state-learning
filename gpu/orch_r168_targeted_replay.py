"""Inactive R168 schedule hook: bound historical own rows, explicit extra dose, no launcher."""

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time


SCHEMA = 'R168_TARGETED_REPLAY_SELECTION_V1'
GO_SCHEMA = 'R168_TARGETED_REPLAY_MAIN_GO_V1'
EXTRA = 'R168_EXPERIMENTAL_EXTRA_OWN'
MAX_ROWS = 2
MAX_DOSE = 4
MAX_EXTRA_STEPS = 8
MAX_METADATA_BYTES = 16 * 1024 * 1024
BASELINE = dict(new_presentations=16, rehearsal_presentations=1,
                own_weight=0.75, anchor_weights=[0.0625] * 4)
ROLE = 'PARENTED_NON_CONTROL'
RUNTIME = 'R125_NATIVE_UNMATCHED'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def valid_hash(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def canonical(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve(),
            'canonical_absolute_path')
    return path


def directory_fd(path):
    path = canonical(path)
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for component in path.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def reference_fields(reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}
            and valid_hash(reference['sha256']), 'exact_hash_reference')
    return canonical(reference['path'])


def read_bound(reference):
    path = reference_fields(reference)
    parent = directory_fd(path.parent)
    try:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_METADATA_BYTES,
                    'bounded_regular_metadata')
            raw = stream.read(MAX_METADATA_BYTES + 1)
            after = os.fstat(stream.fileno())
            require(len(raw) == before.st_size and all(getattr(before, field) == getattr(after, field)
                    for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                    'metadata_changed_during_read')
    finally:
        os.close(parent)
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'metadata_hash_mismatch')

    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError('nonfinite_JSON:' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def write_once(path, value):
    path = canonical(path)
    parent = directory_fd(path.parent)
    try:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(encoded(value) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)


def saved_boundary(own_root, boundary_ref, checkpoint_ref):
    root = canonical(own_root)
    boundary_path = reference_fields(boundary_ref)
    checkpoint_path = reference_fields(checkpoint_ref)
    require(boundary_path.parent == root / 'stream/records'
            and re.fullmatch(r'[0-9]{20}\.json', boundary_path.name) is not None,
            'own_journal_record_only')
    require(checkpoint_path.parent.parent == root / 'checkpoints'
            and re.fullmatch('sleep_[0-9]{6}', checkpoint_path.parent.name) is not None
            and checkpoint_path.name == 'COMMIT.json', 'own_completed_checkpoint_only')
    record = read_bound(boundary_ref)
    require(record['kind'] == 'SLEEP_COMPLETE' and type(record['index']) is int
            and record['index'] == int(boundary_path.stem)
            and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'bound_completed_journal_record')
    document = record['document']
    require(type(document['cycle']) is int and document['cycle'] > 0
            and checkpoint_path.parent.name == f"sleep_{document['cycle']:06d}"
            and document['status'] == 'COMPLETE', 'exact_completed_cycle')
    commit = read_bound(checkpoint_ref)
    require(commit == document['checkpoint'] and type(commit['optimizer_steps']) is int
            and commit['optimizer_steps'] > 0, 'nonfrozen_completed_checkpoint')
    require(canonical(commit['adapter_path']) == checkpoint_path.parent / 'adapter'
            and canonical(commit['optimizer_rng_path']) == checkpoint_path.parent / 'optimizer_rng.pt',
            'own_checkpoint_payload_paths')
    references = commit['checkpoint_sha256']
    require(set(references) == {'adapter', 'optimizer', 'rng'}
            and all(valid_hash(value) for value in references.values()), 'complete_state_references')
    snapshot = document['resume_state']
    state = snapshot['state']
    require(snapshot['sha256'] == digest(state) and state['pending'] is None
            and type(state['rows']) is list and state['rows']
            and type(state['sleep_frontier']) is int and state['sleep_frontier'] == len(state['rows'])
            and state['model_state_sha256'] == digest(references), 'clean_exact_saved_boundary')
    require('matched' not in state, 'matched_or_control_runtime_not_supported')
    return document['cycle'], snapshot


def own_row(row):
    require(type(row) is dict and row.get('actor') == 'child' and row.get('split') == 'TRAIN'
            and row.get('prefix_loss') is False and row.get('target_loss') is True
            and row.get('append_eos') is False, 'existing_own_generated_targets_only')
    require(type(row.get('segment')) is int and row['segment'] >= 0
            and valid_hash(row.get('source_sha256')) and type(row.get('event_id')) is str
            and type(row.get('target')) is str and type(row.get('prefix')) is list
            and row['prefix'] and type(row.get('token_ids')) is list and row['token_ids']
            and all(type(token) is int and token >= 0 for token in row['token_ids']),
            'exact_existing_row_identity')
    require(all(type(message) is dict and set(message) == {'role', 'content'}
            and message['role'] in ('system', 'user', 'assistant')
            and type(message['content']) is str for message in row['prefix']), 'recorded_prefix_only')


def selected_row(snapshot, segment):
    rows = snapshot['state']['rows']
    require(type(segment) is int and 0 <= segment < len(rows), 'historical_segment_only')
    row = rows[segment]
    own_row(row)
    require(row['segment'] == segment, 'original_segment_position')
    events = [event for event in snapshot['state']['history']['events']
              if event.get('event_id') == row['event_id']]
    require(len(events) == 1 and events[0]['actor'] == 'child' and events[0]['split'] == 'TRAIN'
            and events[0]['origin'] == 'TRAIN_COLLECTION' and events[0]['text'] == row['target']
            and events[0]['source_sha256'] == row['source_sha256'], 'original_child_event_binding')
    return row


def support_events(snapshot, identifiers):
    require(type(identifiers) is list and 1 <= len(identifiers) <= 4
            and all(type(identifier) is str for identifier in identifiers)
            and len(set(identifiers)) == len(identifiers), 'bounded_distinct_support_events')
    events = snapshot['state']['history']['events']
    result = []
    for identifier in identifiers:
        matches = [event for event in events if event.get('event_id') == identifier]
        require(len(matches) == 1 and matches[0].get('actor') in ('child', 'parent', 'environment')
                and matches[0].get('split') == 'TRAIN' and matches[0].get('origin') == 'TRAIN_COLLECTION'
                and valid_hash(matches[0].get('source_sha256')), 'existing_TRAIN_support_only')
        result.append(dict(event_id=identifier, source_sha256=matches[0]['source_sha256'],
                           event_sha256=digest(matches[0])))
    return result


def freeze_selection(*, own_root, boundary_ref, checkpoint_ref, row_objects, dose,
                     plan_sha256, runtime_sha256, frozen_unix):
    require(type(dose) is int and 1 <= dose <= MAX_DOSE, 'bounded_explicit_extra_dose')
    require(type(row_objects) is list and 1 <= len(row_objects) <= MAX_ROWS
            and dose * len(row_objects) <= MAX_EXTRA_STEPS, 'bounded_selected_rows')
    require(valid_hash(plan_sha256) and valid_hash(runtime_sha256), 'plan_and_runtime_pins')
    require(type(frozen_unix) in (int, float) and math.isfinite(frozen_unix) and frozen_unix >= 0,
            'finite_selection_time')
    cycle, snapshot = saved_boundary(own_root, boundary_ref, checkpoint_ref)
    selections = []
    for item in row_objects:
        require(type(item) is dict and set(item) == {'segment', 'object_id', 'selection_kind', 'support_event_ids'}
                and type(item['object_id']) is str
                and re.fullmatch('[a-z0-9][a-z0-9_-]{0,95}', item['object_id']), 'bounded_object_selector')
        require(item['selection_kind'] in ('OBJECT_REPLAY', 'ATTENTION_STRATEGY_REPLAY'),
                'object_or_strategy_not_correctness_claim')
        row = selected_row(snapshot, item['segment'])
        support = support_events(snapshot, item['support_event_ids'])
        require(item['selection_kind'] != 'ATTENTION_STRATEGY_REPLAY'
                or any(event['event_id'] != row['event_id'] for event in support),
                'strategy_requires_support_beyond_self_report')
        selections.append(dict(item, source_sha256=row['source_sha256'], row_sha256=digest(row),
                               extra_presentations=dose, support=support))
    require(len({item['source_sha256'] for item in selections}) == len(selections), 'unique_selected_rows')
    return dict(schema=SCHEMA, life_root=str(canonical(own_root)), life_role=ROLE, runtime_kind=RUNTIME,
                plan_sha256=plan_sha256, runtime_sha256=runtime_sha256, selection_split='TRAIN',
                boundary_ref=deepcopy(boundary_ref), checkpoint_ref=deepcopy(checkpoint_ref),
                boundary_state_sha256=snapshot['sha256'], source_cycle=cycle, target_cycle=cycle + 1,
                frozen_unix=frozen_unix, baseline=deepcopy(BASELINE), selected=selections)


def validate_selection(selection):
    require(type(selection) is dict and set(selection) == {
        'schema', 'life_root', 'life_role', 'runtime_kind', 'plan_sha256', 'runtime_sha256',
        'selection_split', 'boundary_ref', 'checkpoint_ref', 'boundary_state_sha256', 'source_cycle',
        'target_cycle', 'frozen_unix', 'baseline', 'selected'}, 'exact_selection_fields')
    items = selection['selected']
    require(type(items) is list and items and all(type(item) is dict and set(item) == {
        'segment', 'object_id', 'selection_kind', 'support_event_ids', 'support', 'source_sha256',
        'row_sha256', 'extra_presentations'} for item in items),
        'exact_frozen_selectors')
    dose = items[0]['extra_presentations']
    require(all(item['extra_presentations'] == dose for item in items), 'one_explicit_dose')
    rebuilt = freeze_selection(own_root=selection['life_root'], boundary_ref=selection['boundary_ref'],
        checkpoint_ref=selection['checkpoint_ref'], row_objects=[{key: item[key] for key in (
        'segment', 'object_id', 'selection_kind', 'support_event_ids')} for item in items],
        dose=dose, plan_sha256=selection['plan_sha256'],
        runtime_sha256=selection['runtime_sha256'], frozen_unix=selection['frozen_unix'])
    require(encoded(rebuilt) == encoded(selection), 'unchanged_frozen_selection')
    return selection


def preview_schedule(selection, *, new_rows, old_rows, baseline_schedule, encoded_rows, encoder,
                     plan_sha256, runtime_sha256, target_cycle, anchor_token_counts):
    validate_selection(selection)
    require(plan_sha256 == selection['plan_sha256'] and runtime_sha256 == selection['runtime_sha256']
            and type(target_cycle) is int and target_cycle == selection['target_cycle'],
            'exact_target_sleep_and_runtime')
    require(type(new_rows) is list and new_rows and type(old_rows) is list, 'normal_sleep_new_rows_required')
    require(type(anchor_token_counts) is list and len(anchor_token_counts) == 4
            and all(type(family) is list and family and all(type(count) is int and count > 0
                    for count in family) for family in anchor_token_counts), 'four_full_label_anchor_families')
    all_rows = new_rows + old_rows
    for row in all_rows:
        own_row(row)
    require(len({row['source_sha256'] for row in all_rows}) == len(all_rows), 'unique_baseline_rows')
    expected = [('NEW', row) for unused in range(16) for row in new_rows]
    expected += [('REHEARSAL', row) for row in old_rows]
    require(type(baseline_schedule) is list and len(baseline_schedule) == len(expected)
            and all(kind == wanted_kind and row is wanted_row
                    for (kind, row), (wanted_kind, wanted_row) in zip(baseline_schedule, expected)),
            'unchanged_NATIVE_NEW16_REHEARSAL1_order')
    available = {row['source_sha256']: row for row in old_rows}
    extra = []
    exposures = []
    for item in selection['selected']:
        require(item['source_sha256'] in available, 'selected_row_excluded_or_not_historical')
        row = available[item['source_sha256']]
        require(digest(row) == item['row_sha256'], 'selected_row_changed')
        require(row['source_sha256'] in encoded_rows, 'selected_row_not_natively_encoded')
        sample = encoder(row)
        cached = encoded_rows[row['source_sha256']]
        require(sample == cached and tuple(sample.target_ids) == tuple(row['token_ids'])
                and tuple(sample.input_ids[-len(row['token_ids']):]) == tuple(row['token_ids'])
                and tuple(sample.labels) == (-100,) * (len(sample.input_ids) - len(row['token_ids']))
                    + tuple(row['token_ids']), 'exact_native_prefix_tokens_and_masks')
        extra.extend([(EXTRA, row)] * item['extra_presentations'])
        exposures.append(dict(item, target_tokens=len(sample.target_ids),
            extra_child_token_exposures=len(sample.target_ids) * item['extra_presentations'],
            encoded_sha256=digest(dict(input_ids=list(sample.input_ids), labels=list(sample.labels),
                                       target_ids=list(sample.target_ids)))))
    baseline_anchor_tokens = sum(sum(family[index % len(family)] for family in anchor_token_counts)
                                for index in range(len(baseline_schedule)))
    extra_anchor_tokens = sum(sum(family[index % len(family)] for family in anchor_token_counts)
                             for index in range(len(baseline_schedule), len(baseline_schedule) + len(extra)))
    return baseline_schedule + extra, dict(schema='R168_PLANNED_EXPOSURE_V1', status='PLANNED_NOT_EXECUTED',
        selection_sha256=digest(selection), baseline=deepcopy(BASELINE), baseline_steps=len(baseline_schedule),
        extra_steps=len(extra), total_steps=len(baseline_schedule) + len(extra), selected=exposures,
        extra_anchor_samples=4 * len(extra),
        baseline_anchor_token_exposures=baseline_anchor_tokens,
        extra_anchor_token_exposures=extra_anchor_tokens,
        baseline_child_token_exposures=sum(len(row['token_ids']) for kind, row in baseline_schedule),
        extra_child_token_exposures=sum(len(row['token_ids']) for kind, row in extra),
        baseline_anchor_indices_unchanged=True, extra_anchor_index_start=len(baseline_schedule))


class AdmittedSchedule:
    def __init__(self, steps, planned, marker, encoded_rows):
        self._steps = tuple((kind, row, digest(row)) for kind, row in steps)
        self.planned = deepcopy(planned)
        self.marker = marker
        self.status = 'ADMITTED_NOT_EXECUTION_PROOF'
        self._used = False
        self._encoded_rows = encoded_rows
        self._encoded_hashes = {item['source_sha256']: item['encoded_sha256'] for item in planned['selected']}

    def __iter__(self):
        require(not self._used, 'admitted_schedule_never_replayed')
        self._used = True
        self.status = 'ITERATING_NOT_EXECUTION_PROOF'

        def iterate():
            try:
                for kind, row, checksum in self._steps:
                    require(digest(row) == checksum, 'row_mutated_after_admission')
                    if kind == EXTRA:
                        sample = self._encoded_rows[row['source_sha256']]
                        require(digest(dict(input_ids=list(sample.input_ids), labels=list(sample.labels),
                            target_ids=list(sample.target_ids))) == self._encoded_hashes[row['source_sha256']],
                            'encoded_row_mutated_after_admission')
                    yield kind, row
                self.status = 'EXHAUSTED_NOT_EXECUTION_PROOF'
            except BaseException:
                self.status = 'FAILED_OR_UNCERTAIN_NO_RETRY'
                raise

        return iterate()


def validate_go(go, selection_ref, selection, approved_intake_sha256, now):
    require(type(go) is dict and set(go) == {'schema', 'action', 'selection', 'life_root',
        'life_role', 'target_cycle', 'plan_sha256', 'runtime_sha256', 'approved_intake_sha256',
        'not_before', 'expires'}, 'exact_replay_GO')
    require(valid_hash(approved_intake_sha256) and go['approved_intake_sha256'] == approved_intake_sha256,
            'external_approved_intake_binding')
    require(go['schema'] == GO_SCHEMA and go['action'] == 'ONE_EXPERIMENTAL_TARGETED_REPLAY_SLEEP'
            and go['selection'] == selection_ref and all(go[key] == selection[key]
                for key in ('life_root', 'life_role', 'target_cycle', 'plan_sha256', 'runtime_sha256')),
            'exact_Main_replay_authority')
    require(all(type(go[key]) in (int, float) and math.isfinite(go[key]) for key in ('not_before', 'expires'))
            and selection['frozen_unix'] <= go['not_before'] <= now < go['expires'], 'current_replay_GO')


def consume_operation(root, cycle, receipt):
    target = canonical(root) / 'checkpoints' / f'sleep_{cycle:06d}'
    require(not target.exists() and not target.is_symlink(), 'existing_target_checkpoint_never_replayed')
    root_fd = directory_fd(root)
    try:
        try:
            os.mkdir('r168_targeted_replay', 0o700, dir_fd=root_fd)
            os.fsync(root_fd)
        except FileExistsError:
            pass
        parent = os.open('r168_targeted_replay', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                         dir_fd=root_fd)
        try:
            name = f'sleep_{cycle:06d}'
            os.mkdir(name, 0o700, dir_fd=parent)
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        os.close(root_fd)
    marker = canonical(root) / 'r168_targeted_replay' / name
    write_once(marker / 'CONSUMED.json', receipt)
    return marker


def admit_schedule(selection_ref, main_go_ref, *, approved_intake_sha256, now=time.time, **schedule_args):
    selection, go = read_bound(selection_ref), read_bound(main_go_ref)
    validate_go(go, selection_ref, selection, approved_intake_sha256, now())
    steps, planned = preview_schedule(selection, **schedule_args)
    require(read_bound(main_go_ref) == go, 'GO_unchanged_after_preparation')
    validate_go(go, selection_ref, selection, approved_intake_sha256, now())
    marker = consume_operation(selection['life_root'], selection['target_cycle'], dict(
        schema='R168_CONSUMED_SLEEP_V1', selection=selection_ref, main_go=main_go_ref,
        approved_intake_sha256=approved_intake_sha256, planned=planned, no_retry=True,
        status='ADMITTED_NOT_EXECUTION_PROOF'))
    return AdmittedSchedule(steps, planned, marker, schedule_args['encoded_rows'])


def verify_sleep_receipt(schedule, receipt):
    require(isinstance(schedule, AdmittedSchedule) and schedule.status == 'EXHAUSTED_NOT_EXECUTION_PROOF',
            'full_admitted_schedule_required')
    presentations = {}
    for kind, row, checksum in schedule._steps:
        source = row['source_sha256']
        presentations[source] = presentations.get(source, 0) + 1
    planned = schedule.planned
    require(type(receipt.get('optimizer_steps')) is int and receipt['optimizer_steps'] == planned['total_steps']
            and type(receipt.get('presentations')) is dict
            and all(type(count) is int for count in receipt['presentations'].values())
            and receipt['presentations'] == presentations, 'actual_step_and_presentation_accounting')
    require(type(receipt.get('child_token_exposures')) is int
            and receipt['child_token_exposures'] == planned['baseline_child_token_exposures']
                + planned['extra_child_token_exposures']
            and type(receipt.get('anchor_token_exposures')) is int
            and receipt['anchor_token_exposures'] == planned['baseline_anchor_token_exposures']
                + planned['extra_anchor_token_exposures'], 'actual_own_and_anchor_exposure_accounting')
    require(receipt.get('anchor_lambda') == 0.25
            and receipt.get('mix_kind') == 'OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION'
            and receipt.get('frozen_base_verified') is True, 'unchanged_anchor_objective_and_base')
    return dict(schema='R168_REPORTED_SLEEP_ACCOUNTING_V1', selection_sha256=planned['selection_sha256'],
        consumed_marker=str(schedule.marker), baseline_steps=planned['baseline_steps'],
        experimental_extra_steps=planned['extra_steps'], reported_total_steps=receipt['optimizer_steps'],
        experimental_extra_child_token_exposures=planned['extra_child_token_exposures'],
        experimental_extra_anchor_token_exposures=planned['extra_anchor_token_exposures'],
        claim='REPORTED_ACCOUNTING_ONLY_NOT_CHECKPOINT_OR_BEHAVIOR_VERIFICATION')


class SingleSleepArm:
    def __init__(self, selection_ref, main_go_ref, *, approved_intake_sha256, now=time.time):
        self.selection = validate_selection(read_bound(selection_ref))
        self.selection_ref = deepcopy(selection_ref)
        self.main_go_ref = deepcopy(main_go_ref)
        self.approved_intake_sha256 = approved_intake_sha256
        self.now = now
        self.status = 'INACTIVE_BEFORE_TARGET_SLEEP'
        self._admitted = None

    def schedule(self, **schedule_args):
        cycle = schedule_args['target_cycle']
        require(type(cycle) is int and cycle >= 1, 'actual_sleep_cycle')
        require(self.status != 'TARGET_ADMISSION_OR_UNCERTAINTY_NO_RETRY',
                'uncertain_arm_never_resumed')
        require(self._admitted is None or self._admitted.status == 'EXHAUSTED_NOT_EXECUTION_PROOF',
                'unfinished_or_uncertain_schedule_never_resumed')
        require(self.status != 'EXPIRED_SINGLE_SLEEP_ARM' or cycle > self.selection['target_cycle'],
                'expired_arm_never_reactivated')
        require(self.status != 'TARGET_CONSUMED_NO_RETRY' or cycle > self.selection['target_cycle'],
                'consumed_arm_never_reactivated')
        if cycle != self.selection['target_cycle']:
            self.status = ('EXPIRED_SINGLE_SLEEP_ARM' if cycle > self.selection['target_cycle']
                           else 'INACTIVE_BEFORE_TARGET_SLEEP')
            return schedule_args['baseline_schedule'], dict(schema='R168_ARM_DISPOSITION_V1',
                status=self.status, target_cycle=self.selection['target_cycle'], actual_cycle=cycle,
                experimental_extra_steps=0, baseline_unchanged=True)
        require(self.status == 'INACTIVE_BEFORE_TARGET_SLEEP', 'consumed_arm_never_reactivated')
        self.status = 'TARGET_ADMISSION_OR_UNCERTAINTY_NO_RETRY'
        schedule = admit_schedule(self.selection_ref, self.main_go_ref,
            approved_intake_sha256=self.approved_intake_sha256, now=self.now, **schedule_args)
        self._admitted = schedule
        self.status = 'TARGET_CONSUMED_NO_RETRY'
        return schedule, deepcopy(schedule.planned)
