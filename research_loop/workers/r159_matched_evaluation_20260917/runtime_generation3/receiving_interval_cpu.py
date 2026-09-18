import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu import orch_r159_matched_evaluation as subject


class ReceivingIntervalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='r159_interval_cpu_')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        now = time.time()
        self.frozen = now-100
        self.observed = now-1
        freeze = self.store('FREEZE.json', dict(frozen_unix=self.frozen))
        self.plan = dict(freeze=freeze)
        self.config = dict(campaign_root=str(self.root), campaign=dict(sha256='a'*64))
        old = subject.ORIGINAL_FREEZE_SHA256, subject.ORIGINAL_PLAN_SHA256
        self.addCleanup(setattr, subject, 'ORIGINAL_FREEZE_SHA256', old[0])
        self.addCleanup(setattr, subject, 'ORIGINAL_PLAN_SHA256', old[1])
        subject.ORIGINAL_FREEZE_SHA256, subject.ORIGINAL_PLAN_SHA256 = freeze['sha256'], 'a'*64
        self.candidate = dict(cohort=dict(sha256='b'*64), initial_commit=dict(sha256='c'*64),
                              initialized=dict(sha256='d'*64))
        self.initial = dict(created_unix=now-150)
        self.initialized = dict(initialized_unix=now-50)
        self.events = {arm: {kind: dict(schema='R159_FIRST_EXPOSURE_V1', cohort_sha256='b'*64,
            arm=arm, kind=kind, coverage_complete=True, observed_unix=self.observed,
            status='OBSERVED', first_unix=now-10) for kind in ('birth', 'train', 'evaluation')}
            for arm in subject.ARMS}

    def store(self, name, value):
        path = self.inputs / name
        path.write_text(json.dumps(value))
        return subject.ref(path)

    def interval(self, arm='parented_learning', kind='birth'):
        witness = self.store(f'{arm}_{kind}_WITNESS.json', dict(metadata_only=True))
        event = self.events[arm][kind]
        event.pop('first_unix', None)
        event.update(status='OBSERVED_INTERVAL', first_earliest_unix=self.frozen+1,
                     first_latest_unix=self.observed, source_evidence=[witness])
        return event, witness

    def validate(self):
        events = {arm: {kind: self.store(f'{arm}_{kind}.json', event) for kind, event in kinds.items()}
                  for arm, kinds in self.events.items()}
        timing = dict(schema=subject.TIMESTAMP_SCHEMA, status='TRUSTED_SOURCE_OWNER_ATTESTED',
            campaign_sha256='a'*64, freeze=self.plan['freeze'], cohort_sha256='b'*64,
            initial_commit_sha256='c'*64, initialized_sha256='d'*64, initializer_lifecycle_sha256='e'*64,
            initial_created_unix=self.initial['created_unix'], initialized_unix=self.initialized['initialized_unix'],
            enrollment_unix=self.observed-1, observed_unix=self.observed,
            saved_initial_generation_calls=0, saved_initial_optimizer_updates=0,
            saved_initial_training_exposure=False, saved_initial_evaluation_exposure=False, arm_exposures=events)
        owner = dict(timestamp_custody=self.store('TIMESTAMP.json', timing),
                     initializer_lifecycle=dict(sha256='e'*64))
        return subject.timestamp_custody(self.config, self.plan, self.candidate, owner,
                                         self.initial, self.initialized, recovery={})

    def test_all_nine_intervals(self):
        for arm in subject.ARMS:
            for kind in ('birth', 'train', 'evaluation'):
                self.interval(arm, kind)
        self.validate()

    def test_exact_and_not_occurred_preserved(self):
        self.validate()
        event = self.events['parented_frozen']['train']
        event.update(status='NOT_OCCURRED', first_unix=None)
        self.validate()
        event['first_unix'] = self.observed
        with self.assertRaises(ValueError):
            self.validate()

    def test_invalid_bounds(self):
        for earliest, latest in ((self.frozen-1, self.observed), (self.frozen, self.observed),
                (self.observed, self.frozen+1), (self.frozen+1, self.observed+1),
                (float('nan'), self.observed), (self.frozen+1, float('inf')),
                (True, self.observed), (self.frozen+1, 'invalid')):
            with self.subTest(earliest=earliest, latest=latest):
                event, _ = self.interval()
                event.update(first_earliest_unix=earliest, first_latest_unix=latest)
                with self.assertRaises(ValueError):
                    self.validate()

    def test_missing_changed_evidence(self):
        event, witness = self.interval()
        Path(witness['path']).write_text('changed')
        with self.assertRaises(ValueError):
            self.validate()
        event['source_evidence'] = []
        with self.assertRaises(ValueError):
            self.validate()
        event.pop('source_evidence')
        with self.assertRaises(ValueError):
            self.validate()

    def test_equal_interval_endpoints(self):
        event, _ = self.interval()
        event['first_latest_unix'] = event['first_earliest_unix']
        self.validate()

    def test_missing_kind(self):
        self.interval()
        self.events['parented_learning'].pop('evaluation')
        with self.assertRaises(ValueError):
            self.validate()

    def test_coverage_and_exact_extra_fields(self):
        event, _ = self.interval()
        event['coverage_complete'] = False
        with self.assertRaises(ValueError):
            self.validate()
        event['coverage_complete'] = True
        event['first_unix'] = self.observed
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReceivingIntervalTests)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    print(json.dumps(dict(status='PASS' if result.wasSuccessful() else 'FAIL', tests_run=result.testsRun,
        helper_sha256=subject.sha(subject.__file__), synthetic_metadata_only=True,
        model_calls=0, checkpoint_enrollments=0)))
    raise SystemExit(0 if result.wasSuccessful() else 1)
