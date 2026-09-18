import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('c2_age_source_sidecar', HERE / 'sources.py')
sources = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sources)
CAPTURE_PATH = HERE.parent / 'rohin233_kept_age_probe_20260918/capture_retained.py'
READER_PATH = HERE.parent / 'rohin232_correction_audit_20260918/reader.py'
EXPOSURE_PATH = HERE.parent / 'rohin233_kept_age_probe_20260918/source_exposure.py'
if (HERE / 'operator').exists():
    CAPTURE_PATH, READER_PATH, EXPOSURE_PATH = (HERE / 'operator' / name for name in
        ('capture_retained.py', 'reader.py', 'source_exposure.py'))
capture = sources.load_module('test_original_capture', CAPTURE_PATH)
reader = sources.load_module('test_original_reader', READER_PATH)
exposure = sources.load_module('test_original_exposure', EXPOSURE_PATH)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.life = self.root / 'life'
        self.records = self.life / 'stream/records'
        self.records.mkdir(parents=True)
        previous = None
        self.rows = {}
        for index, kind in enumerate(('LOADED', 'REQUEST', 'UPDATE', 'REQUEST', 'SLEEP_COMPLETE'), 1):
            document = dict(messages=[dict(role='user', content='A safe synthetic arithmetic lesson.')])
            if kind == 'LOADED':
                document = dict(base_sha256=capture.BASE)
            if kind == 'SLEEP_COMPLETE':
                document = dict(status='COMPLETE', cycle=51, total_optimizer_steps=10,
                    after_adapter_sha256='adapter-state', resume_state=dict(state=dict(history=[])))
            row = dict(index=index, journal_id='test-journal', kind=kind, document=document, previous_sha256=previous)
            row['sha256'] = sources.digest(row)
            self.rows[index] = row
            self.save(index)
            previous = row['sha256']
        contests = [dict(contest_id='agentdev_' + hashlib.sha256(identifier.encode()).hexdigest()[:20],
            split='agent_development', image='image-' + identifier,
            canonical_scene=f'An astronaut balances a wooden chair beside a giant clock number {identifier}.')
            for identifier in ('564', '654', '703')]
        scenes = dict(contests=contests)
        self.inputs = dict(scenes=scenes, selection=dict(selected=['564', '654', '703']),
            baseline_capture=dict(head_index=2, head_sha256=self.rows[2]['sha256'],
                exposure=dict(complete=True, matches={})),
            baseline_exposure=dict(eligible=True, source_cut_index=2, source_cut_sha256=self.rows[2]['sha256'],
                requests_scanned=1, scenes_sha256=hashlib.sha256(json.dumps(scenes, sort_keys=True).encode()).hexdigest()),
            image_packet=dict(images=[dict(handle=row['image'], sha256='image-sha-' + row['image']) for row in contests]),
            pins={'FRESHNESS_VERIFIED.json':'prior-exposure-sha', 'sources/CAPTURE.json':'prior-capture-sha'})
        self.source = dict(journal_id='test-journal', sleep_complete_index=5, sleep_complete_sha256=self.rows[5]['sha256'])

    def save(self, index):
        (self.records / f'{index:020d}.json').write_text(json.dumps(self.rows[index], sort_keys=True, separators=(',', ':')))

    def audit(self):
        return sources.audit_exposure(self.life, self.source, self.inputs, reader, exposure)

    def test_bounded_tail_includes_inherited_without_old_body_replay(self):
        result = self.audit()
        self.assertTrue(result['eligible'])
        self.assertEqual([3, 5], result['incremental_range'])
        self.assertEqual(1, result['canonical_record_counts']['REQUEST'])
        self.assertEqual(1, result['canonical_record_counts']['LOADED'])
        self.assertEqual(1, result['canonical_record_counts']['SLEEP_COMPLETE'])
        self.assertEqual(1, result['header_only_noninput_records'])

    def test_prior_ineligible_never_overridden(self):
        self.inputs['baseline_exposure']['eligible'] = False
        with self.assertRaisesRegex(ValueError, 'eligible_original_exposure'):
            self.audit()

    def test_different_scene_selection_rejected(self):
        self.inputs['selection']['selected'][0] = '513'
        with self.assertRaisesRegex(ValueError, 'original_three_scenes'):
            self.audit()

    def test_unknown_request_content_is_not_fresh(self):
        self.rows[4]['document']['messages'][0]['content'] = [{'type':'unknown_image'}]
        self.rehash_from(4)
        self.assertFalse(self.audit()['eligible'])

    def rehash_from(self, start):
        for index in range(start, 6):
            row = self.rows[index]
            row['previous_sha256'] = self.rows[index - 1]['sha256']
            row['sha256'] = sources.digest({key:value for key,value in row.items() if key != 'sha256'})
            self.save(index)
        self.source['sleep_complete_sha256'] = self.rows[5]['sha256']

    def test_inherited_scene_rejected(self):
        self.rows[5]['document']['resume_state']['state']['history'] = [self.inputs['scenes']['contests'][0]['canonical_scene']]
        self.rehash_from(5)
        self.assertFalse(self.audit()['eligible'])

    def test_identifier_exposure_rejected(self):
        self.rows[4]['document']['messages'][0]['content'] = 'Please consider scene: 564.'
        self.rehash_from(4)
        self.assertFalse(self.audit()['eligible'])

    def test_header_gap_rejected(self):
        (self.records / f'{3:020d}.json').unlink()
        with self.assertRaisesRegex(ValueError, 'contiguous_tail_headers'):
            self.audit()

    def test_latest_does_not_select_partial_sleep(self):
        result = sources.latest(self.life, reader, dict(journal_id='test-journal'))
        self.assertEqual(5, result['record_index'])
        self.rows[5]['document']['status'] = 'PENDING'
        self.rehash_from(5)
        with self.assertRaisesRegex(ValueError, 'no_completed_source'):
            sources.latest(self.life, reader, dict(journal_id='test-journal'))

    def test_exact_capture_and_receiving_copy_exclude_optimizer_context(self):
        checkpoint = self.life / 'checkpoints/sleep_000051'
        adapter = checkpoint / 'adapter'
        adapter.mkdir(parents=True)
        for name in ('README.md', 'adapter_config.json', 'adapter_model.safetensors'):
            (adapter / name).write_bytes(name.encode())
        commit = dict(base_sha256=capture.BASE, adapter_state_sha256='adapter-state', optimizer_steps=10,
            adapter_files={path.name:sources.sha(path) for path in adapter.iterdir()})
        (checkpoint / 'COMMIT.json').write_text(json.dumps(commit))
        (checkpoint / 'optimizer_rng.pt').write_bytes(b'provenance only, not copied')
        target = dict(root=str(self.life), journal_id='test-journal', label='TEST',
            initial_loaded=dict(index=1, sha256=self.rows[1]['sha256']))
        entry = dict(record_index=5, record_sha256=self.rows[5]['sha256'])
        result = capture.capture(target, entry, self.root / 'queue')
        copied = self.root / 'queue' / result['source_relative']
        self.assertFalse((copied / 'optimizer_rng.pt').exists())
        self.assertTrue(result['before_after_equal'])
        staged = self.root / 'receiving'
        sources.stage_adapter(copied, staged, result)
        self.assertFalse((staged / 'optimizer_rng.pt').exists())
        (copied / 'adapter/README.md').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'immutable_prior_capture_changed'):
            capture.capture(target, entry, self.root / 'queue')

    def test_receiving_rejects_optimizer_payload(self):
        with self.assertRaisesRegex(ValueError, 'adapter_only_source_allowlist'):
            sources.stage_adapter(self.root, self.root / 'destination', dict(copy_files={'optimizer_rng.pt':{}}))

    def test_receiving_requires_same_judge_not_old_ranker(self):
        with patch.dict(sys.modules, {'sources': sources}):
            receiver = sources.load_module('c2_age_receiving_test', HERE / 'receive.py')
        judge = dict(step=15625, rank=8, adapter_sha256=sources.JUDGE_ADAPTER,
            config=dict(adapter={'adapter_model.safetensors':dict(sha256=sources.JUDGE_ADAPTER)}))
        receiver.require_judge(judge)
        judge['step'] = 0
        with self.assertRaisesRegex(ValueError, 'same_adopted_judge_epoch'):
            receiver.require_judge(judge)


if __name__ == '__main__':
    unittest.main()
