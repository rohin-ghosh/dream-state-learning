"""Opt-in, per-instance scheduling around an unchanged pinned native sleep method."""

from copy import deepcopy
import hashlib
import importlib
import os
import stat
import sys
import types

from gpu import orch_r168_targeted_replay as replay


NATIVE_SHA256 = 'cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48'
ARM_SHA256 = '4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3'
ROW_SHA256 = '564f8a4f585ecc2eb4bfb16fb0efb390cf8014050fd761dadc93b4773ecd7e6d'
SOURCE_SHA256 = '1d721f3be5a40bac051f0c132451d7bb1e6bec428eec63327b26f64432ae17d7'
DEPENDENCIES = ('gpu.orch_r108_guided_native', 'gpu.orch_r144_sleep_targets',
                'organism_v6.orch_r125_plain_context')


def _source_bytes(module, checksum):
    path = replay.canonical(module.__file__)
    parent = replay.directory_fd(path.parent)
    try:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            replay.require(stat.S_ISREG(before.st_mode) and before.st_size <= 1024 * 1024,
                           'bounded_native_source')
            raw = stream.read(1024 * 1024 + 1)
            after = os.fstat(stream.fileno())
            replay.require(len(raw) == before.st_size and all(getattr(before, field) == getattr(after, field)
                for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                'native_source_changed_during_read')
    finally:
        os.close(parent)
    replay.require(replay.valid_hash(checksum) and hashlib.sha256(raw).hexdigest() == checksum,
                   'native_source_pin')
    return raw


def _code(parent, name):
    matches = [value for value in parent.co_consts if isinstance(value, types.CodeType)
               and value.co_name == name]
    replay.require(len(matches) == 1, 'unique_pinned_native_method')
    return matches[0]


class NativeReplaySleep:
    def __init__(self, native_module, child, *, arm=None, plan_ref=None, runtime_ref=None):
        self.native = native_module
        self.child = child
        self.arm = arm
        self.plan_ref = deepcopy(plan_ref)
        self.runtime_ref = deepcopy(runtime_ref)
        self.uncertain = False
        self._schedule = None

    def _bind(self):
        replay.require(isinstance(self.arm, replay.SingleSleepArm), 'existing_single_sleep_arm')
        selection = self.arm.selection
        plan = replay.read_bound(self.plan_ref)
        runtime = replay.read_bound(self.runtime_ref)
        replay.require(self.plan_ref['sha256'] == selection['plan_sha256']
            and self.runtime_ref['sha256'] == selection['runtime_sha256']
            and replay.encoded(plan) == replay.encoded(self.child.plan)
            and plan['root'] == selection['life_root'] and plan['presleep_variant'] == 'reread_select'
            and plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1
            and plan['anchor_lambda'] == 0.25, 'exact_live_plan_runtime_and_arm')
        items = selection['selected']
        replay.require(len(items) == 1 and items[0]['source_sha256'] == SOURCE_SHA256
            and items[0]['row_sha256'] == ROW_SHA256 and items[0]['extra_presentations'] == 4
            and items[0]['selection_kind'] == 'OBJECT_REPLAY', 'one_exact_object_row_four_extras')
        replay.require(set(runtime) == {'schema', 'native_sha256', 'arm_sha256',
            'integration_sha256', 'dependencies'} and runtime['schema'] == 'R168_NATIVE_SLEEP_RUNTIME_V1'
            and runtime['native_sha256'] == NATIVE_SHA256
            and runtime['arm_sha256'] == ARM_SHA256
            and set(runtime['dependencies']) == set(DEPENDENCIES), 'exact_native_runtime_manifest')
        raw = _source_bytes(self.native, NATIVE_SHA256)
        compiled = compile(raw, self.native.__file__, 'exec')
        for function, expected in (
                (self.native.NativeChild.sleep, _code(_code(compiled, 'NativeChild'), 'sleep')),
                (self.native.finish_sleep, _code(compiled, 'finish_sleep')),
                (self.native.encode_own, _code(compiled, 'encode_own')),
                (self.native.presentation_schedule, _code(compiled, 'presentation_schedule'))):
            replay.require(function.__code__ == expected and function.__globals__ is self.native.__dict__
                and function.__closure__ is None, 'live_native_method_matches_pinned_bytes')
        _source_bytes(replay, runtime['arm_sha256'])
        _source_bytes(sys.modules[__name__], runtime['integration_sha256'])
        for name in DEPENDENCIES:
            _source_bytes(importlib.import_module(name), runtime['dependencies'][name])

    def _fail(self, error):
        self.uncertain = True
        if self._schedule is not None:
            self._schedule.status = 'FAILED_OR_UNCERTAIN_NO_RETRY'
            try:
                replay.write_once(self._schedule.marker / 'FAILED_OR_UNCERTAIN.json',
                    dict(schema='R168_NATIVE_SLEEP_FAILURE_V1', error_type=type(error).__name__,
                         no_retry=True, checkpoint_completion_claim=False))
            except BaseException:
                pass

    def finish_sleep(self, stream, journal, anchors, root, cycle):
        if self.arm is None:
            return self.native.finish_sleep(self.child, stream, journal, anchors, root, cycle)
        replay.require(not self.uncertain, 'native_replay_uncertain_no_retry')
        try:
            self._bind()
            replay.require(replay.canonical(root) == replay.canonical(self.child.plan['root']),
                           'exact_own_checkpoint_root')
            proxy = types.SimpleNamespace(checkpoint=self.child.checkpoint,
                sleep=lambda new, old, selected_anchors, record: self.sleep(
                    new, old, selected_anchors, record, cycle=cycle))
            return self.native.finish_sleep(proxy, stream, journal, anchors, root, cycle)
        except BaseException as error:
            self._fail(error)
            raise

    def sleep(self, new_rows, old_rows, anchors, record, *, cycle=None):
        if self.arm is None:
            return self.native.NativeChild.sleep(self.child, new_rows, old_rows, anchors, record)
        replay.require(not self.uncertain, 'native_replay_uncertain_no_retry')
        self.uncertain = True
        self._schedule = None
        try:
            self._bind()
            replay.require(type(cycle) is int and cycle > 0, 'explicit_actual_sleep_cycle')
            if cycle != self.arm.selection['target_cycle']:
                self.arm.schedule(target_cycle=cycle, baseline_schedule=[])
                receipt = self.native.NativeChild.sleep(self.child, new_rows, old_rows, anchors, record)
            else:
                receipt = self._target_sleep(new_rows, old_rows, anchors, record, cycle)
            self.uncertain = False
            return receipt
        except BaseException as error:
            self._fail(error)
            raise

    def _target_sleep(self, new_rows, old_rows, anchors, record, cycle):
        child = self.child
        steps_before = child.optimizer_steps
        encoded_rows = {}
        updates = []
        families = sorted(anchors)
        anchor_counts = []
        for family in families:
            counts = []
            for item in anchors[family]:
                sample = item['encoded']
                replay.require(tuple(sample.labels) == tuple(sample.input_ids)
                    and tuple(sample.target_ids) == tuple(sample.labels), 'full_label_native_anchors')
                counts.append(len(sample.labels))
            anchor_counts.append(counts)

        def capture_encode(row, tokenizer, context_limit):
            sample = self.native.encode_own(row, tokenizer, context_limit)
            encoded_rows[row['source_sha256']] = sample
            return sample

        def schedule_rows(retained_new, retained_old):
            baseline = self.native.presentation_schedule(retained_new, retained_old)
            schedule, planned = self.arm.schedule(new_rows=retained_new, old_rows=retained_old,
                baseline_schedule=baseline, encoded_rows=encoded_rows,
                encoder=lambda row: self.native.encode_own(row, child.tokenizer, child.plan['context_limit']),
                plan_sha256=self.plan_ref['sha256'], runtime_sha256=self.runtime_ref['sha256'],
                target_cycle=cycle, anchor_token_counts=anchor_counts)
            self._schedule = schedule
            replay.require(planned['extra_steps'] == 4 and planned['selected'][0]['target_tokens'] == 199,
                           'exact_199_token_object_dose')
            return schedule

        def record_finished(kind, document):
            if kind == 'TARGET_ELIGIBILITY':
                replay.require(document['raw_modified'] is False and document['new_row_sha256']
                    and SOURCE_SHA256 in document['rehearsal_row_sha256'],
                    'selected_historical_row_must_pass_native_eligibility')
            if kind == 'UPDATE':
                replay.require(self._schedule is not None, 'no_update_before_replay_admission')
                position = len(updates)
                expected_kind, row, checksum = self._schedule._steps[position]
                replay.require(document['optimizer_step'] == steps_before + position + 1
                    == child.optimizer_steps and document['source_sha256'] == row['source_sha256']
                    and replay.digest(row) == checksum, 'actual_finished_native_update_order')
                losses = document['losses']
                expected_kinds = [expected_kind] + ['ANCHOR:' + family for family in families]
                expected_counts = [len(row['token_ids'])] + [counts[position % len(counts)]
                                                            for counts in anchor_counts]
                replay.require([loss['kind'] for loss in losses] == expected_kinds
                    and [loss['objective_weight'] for loss in losses] == [0.75] + [0.0625] * 4
                    and [loss['target_tokens'] for loss in losses] == expected_counts,
                    'actual_native_microbatch_and_exposure_accounting')
                saved = deepcopy(document)
                record(kind, document)
                replay.require(document == saved, 'update_receipt_mutated_by_recorder')
                updates.append(saved)
            else:
                record(kind, document)

        private_globals = dict(self.native.NativeChild.sleep.__globals__)
        private_globals.update(encode_own=capture_encode, presentation_schedule=schedule_rows)
        method = types.FunctionType(self.native.NativeChild.sleep.__code__, private_globals)
        receipt = method(child, new_rows, old_rows, anchors, record_finished)
        replay.require(self._schedule is not None, 'target_schedule_must_be_admitted')
        accounting = replay.verify_sleep_receipt(self._schedule, receipt)
        replay.require(len(updates) == receipt['optimizer_steps'] == child.optimizer_steps - steps_before,
                       'finished_updates_match_actual_native_counter')
        finished = dict(schema='R168_NATIVE_FINISHED_UPDATES_V1',
            status='FINISHED_UPDATES_NOT_CHECKPOINT_COMMIT', cycle=cycle,
            plan_ref=deepcopy(self.plan_ref), runtime_ref=deepcopy(self.runtime_ref),
            selection_ref=deepcopy(self.arm.selection_ref), main_go_ref=deepcopy(self.arm.main_go_ref),
            optimizer_steps_before=steps_before, optimizer_steps_after=child.optimizer_steps,
            native_update_records_sha256=replay.digest(updates), accounting=accounting)
        replay.write_once(self._schedule.marker / 'FINISHED_UPDATES.json', finished)
        return dict(receipt, r168_targeted_replay=finished)
