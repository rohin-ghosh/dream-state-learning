"""Frozen recovery helpers; original bodies, local contract dependency only."""

from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path

from pending_sleep_contract import require

def _write_once(path, document):
    raw = json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    with path.open('xb') as output:
        output.write(raw + b'\n')
        output.flush()
        os.fsync(output.fileno())
    _sync_directory(path.parent)


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _committed_checkpoint(native, checkpoint, directory):
    require(Path(checkpoint['adapter_path']) == directory / 'adapter'
        and Path(checkpoint['optimizer_rng_path']) == directory / 'optimizer_rng.pt',
        'exact_checkpoint_namespace')
    require(json.loads((directory / 'COMMIT.json').read_bytes()) == checkpoint,
        'checkpoint_must_have_exact_COMMIT')
    native.NativeChild.verify_checkpoint(checkpoint)


class RecoveryRecorder:
    def __init__(self, candidate, journal, check_wall):
        self.candidate = candidate
        self.journal = journal
        self.check_wall = check_wall
        self.phase = 'SLEEP_RECIPE'
        self.counts = Counter()
        self.references = []

    def __call__(self, kind, document):
        self.check_wall()
        contract = self.candidate['contract']['contract']
        require(kind in ('SLEEP_RECIPE', 'TARGET_ELIGIBILITY', 'UPDATE'),
            'no_historical_generation_tool_or_other_publication')
        if kind == 'SLEEP_RECIPE':
            require(self.phase == kind and document == self.candidate['recipe'],
                'unchanged_original_sleep_recipe')
        elif kind == 'TARGET_ELIGIBILITY':
            require(self.phase == kind and document == self.candidate['eligibility'],
                'unchanged_all_rows_target_eligibility')
        else:
            require(self.phase == 'UPDATE', 'recipe_and_eligibility_before_training')
            source = document['source_sha256']
            require(source in contract['pending_row_sha256']
                and self.counts[source] < contract['new_presentations']
                and document['optimizer_step']
                == contract['durable_optimizer_steps'] + len(self.references) + 1,
                'new_recovery_updates_not_unsaved_counter_continuation')
        annotated = deepcopy(document)
        annotated['interrupted_sleep_restart'] = dict(
            epoch_sha256=self.candidate['contract']['sha256'],
            attempt_key=self.candidate['attempt_key'], compute_origin='NEW_RECOVERY_COMPUTE')
        reference = self.journal.record(kind, annotated)
        if kind == 'UPDATE':
            self.counts[document['source_sha256']] += 1
            self.references.append(reference)
        else:
            self.phase = 'TARGET_ELIGIBILITY' if kind == 'SLEEP_RECIPE' else 'UPDATE'
        return reference

    def verify_finished(self, child, receipt):
        contract = self.candidate['contract']['contract']
        expected = {source: contract['new_presentations'] for source in contract['pending_row_sha256']}
        steps = sum(expected.values())
        require(self.phase == 'UPDATE' and dict(self.counts) == expected
            and receipt['presentations'] == expected and receipt['excluded_rows'] == [],
            'full_pending_sleep_without_exclusions')
        require(receipt['optimizer_steps'] == steps
            and receipt['total_optimizer_steps'] == child.optimizer_steps
            == contract['durable_optimizer_steps'] + steps,
            'full_new_recovery_compute_accounting')
        require(receipt['frozen_base_verified'] is True
            and receipt['before_adapter_sha256'] == self.candidate['durable_checkpoint']['adapter_state_sha256']
            and receipt['after_adapter_sha256'] == child.adapter_hash()
            and receipt['after_adapter_sha256'] != receipt['before_adapter_sha256'],
            'original_learning_and_frozen_base_receipt')

