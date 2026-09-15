import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_r118_dev_judge_reduction as reduction


class SummaryTests(unittest.TestCase):
    def rows(self):
        return [dict(cycle=cycle, task_id=f'task{task}', input_sha256=f'input{task}',
            checkpoint_sha256=f'checkpoint{cycle}', native_calls=2, child_token_ids=20+cycle,
            child_output_truncated=False, status='UNATTEMPTED', departures_and_returns=None,
            shifts=None, annotation_sha256=None) for cycle in (0, 1) for task in range(8)]

    def complete(self, row, departures=0, shifts=0):
        row.update(status='COMPLETE', departures_and_returns=departures, shifts=shifts,
            annotation_sha256=f'annotation{departures}:{shifts}')

    def test_missing_is_unknown_not_zero(self):
        summary = reduction.summarize(self.rows())
        self.assertEqual(summary['exact_unique_inputs'], 8)
        for cycle in summary['cycles']:
            self.assertEqual(cycle['coverage']['UNATTEMPTED'], 8)
            self.assertIsNone(cycle['complete_only_mean_shifts'])
            self.assertIsNone(cycle['paired_mean_shift_delta'])
            self.assertFalse(cycle['complete_eight_task_comparison'])

    def test_only_matching_completed_tasks_are_paired(self):
        rows = self.rows()
        self.complete(rows[0])
        self.complete(rows[8], departures=1, shifts=2)
        self.complete(rows[9], departures=6, shifts=7)
        cycle = reduction.summarize(rows)['cycles'][1]
        self.assertEqual(cycle['paired_completed_tasks'], 1)
        self.assertEqual(cycle['paired_mean_departure_delta'], 1)
        self.assertEqual(cycle['paired_mean_shift_delta'], 2)
        self.assertEqual(cycle['paired_mean_token_delta'], 1)
        self.assertEqual(cycle['complete_only_mean_departures_and_returns'], 3.5)

    def test_unresolved_retained_and_not_imputed_from_duplicate(self):
        rows = self.rows()
        self.complete(rows[0])
        rows[8]['status'] = 'UNRESOLVED'
        summary = reduction.summarize(rows)
        self.assertEqual(summary['cycles'][1]['coverage']['UNRESOLVED'], 1)
        self.assertEqual(summary['cycles'][1]['paired_completed_tasks'], 0)
        self.assertEqual(summary['cached_or_imputed_annotations'], 0)

    def test_disagreeing_duplicate_annotations_are_exposed(self):
        rows = self.rows()
        self.complete(rows[0])
        self.complete(rows[8], shifts=1)
        summary = reduction.summarize(rows)
        self.assertEqual(len(summary['duplicate_input_annotation_disagreements']), 1)
        self.assertFalse(summary['disagreements_silently_resolved'])

    def test_full_coverage_is_not_a_retention_claim(self):
        rows = self.rows()
        for row in rows:
            self.complete(row)
        summary = reduction.summarize(rows)
        self.assertTrue(summary['cycles'][1]['complete_eight_task_comparison'])
        self.assertFalse(summary['retained_learning_established'])
        self.assertFalse(summary['FINAL_read'])

    def test_different_held_ids_rejected(self):
        rows = self.rows()
        rows[8]['task_id'] = 'different_task'
        with self.assertRaisesRegex(ValueError, 'same_eight'):
            reduction.summarize(rows)

    def test_duplicate_task_rejected(self):
        rows = self.rows()
        rows[1]['task_id'] = rows[0]['task_id']
        with self.assertRaisesRegex(ValueError, 'unique_cycle_task'):
            reduction.summarize(rows)

    def test_unknown_with_zero_metric_rejected(self):
        rows = self.rows()
        rows[0]['shifts'] = 0
        with self.assertRaisesRegex(ValueError, 'unknown_not_zero'):
            reduction.summarize(rows)


class ReductionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.original = reduction.original
        self.original.write(self.root/'model/generation_config.json', dict(eos_token_id=[151645]))
        self.original.write(self.root/'MODEL_SHA256.json', {'generation_config.json':
            self.original.sha(self.root/'model/generation_config.json')})
        self.original.write(self.root/'source/source.txt', {'immutable': True})
        self.original.write(self.root/'SOURCE.json', {'source.txt':self.original.sha(self.root/'source/source.txt')})
        self.original.write(self.root/'native/CALL.json', {'raw': 'READ EVENT X'})
        self.original.write(self.root/'native/HELD.json', {'scope': 'dev'})
        documents = []
        for task in range(8):
            document = dict(kind='held', task_text=f'Public task {task}', child_text='READ EVENT X')
            request = self.original.judge.request(document)
            documents.append(dict(document=document, request=request, private_provenance=dict(
                cycle=0, task_id=f'task{task}', checkpoint_sha256='checkpoint', native_calls=1,
                child_token_ids=2, child_output_truncated=False, parent_free=True, training_buffer=False,
                sources=[dict(path=str(self.root/'native/CALL.json'),sha256=self.original.sha(self.root/'native/CALL.json'))],
                held_path=str(self.root/'native/HELD.json'),held_sha256=self.original.sha(self.root/'native/HELD.json'))))
        self.original.write(self.root/'DOCUMENTS.json', documents)
        self.original.write(self.root/'PLAN.json', dict(schema='R118_CPU_DEV_JUDGE_V1',
            exploratory_DEV_not_FINAL=True, documents_sha256=self.original.sha(self.root/'DOCUMENTS.json'),
            documents=8, model_manifest_sha256=self.original.sha(self.root/'MODEL_SHA256.json'),
            source_manifest=str(self.root/'SOURCE.json'),source_manifest_sha256=self.original.sha(self.root/'SOURCE.json'),
            source_root=str(self.root/'source'),model_dir=str(self.root/'model'),
            prompt_sha256=self.original.sha(self.original.judge.PROMPT_PATH), max_new_tokens=4096,context_limit=16384))
        self.original.write(self.root/'PUBLICATION.json', {'plan_sha256':self.original.sha(self.root/'PLAN.json')})
        self.original.write(self.root/'LOADED.json', dict(device='cpu',cuda_initialized=False,trainable_parameters=0))
        annotation = dict(status='COMPLETE',reason='',sentences=[dict(index=0,label='MAIN',
            legacy_template_check=False,evidence='READ EVENT X')],shift_sentence_indices=[],classes=[])
        raw = json.dumps(annotation)
        result = self.original.interpret(documents[0]['document'],raw,True)
        self.original.write(self.root/'call_0000/REQUEST.json',documents[0]['request'])
        self.original.write(self.root/'call_0000/RESPONSE.json',dict(raw=raw,token_ids=[111,151645],
            result=result,started_unix=1,finished_unix=2,input_tokens=100))
        self.original.write(self.root/'progress/0000.json',dict(index=0,
            input_sha256=documents[0]['request']['input_sha256'],status='COMPLETE',
            response_path=str(self.root/'call_0000/RESPONSE.json'),
            response_sha256=self.original.sha(self.root/'call_0000/RESPONSE.json')))

    def replace(self, path, **updates):
        content=self.original.read(path)
        content.update(updates)
        path.write_text(json.dumps(content))

    def test_actual_receipt_reduction_preserves_unattempted(self):
        result=reduction.reduce_root(self.root)
        self.assertEqual(result['cycles'][0]['coverage'],dict(COMPLETE=1,UNRESOLVED=0,UNATTEMPTED=7))
        self.assertEqual(result['attempted_snapshot'],1)
        self.assertIsNone(result['terminal'])
        self.assertNotIn('child_text',json.dumps(result))

    def test_tampered_response_rejected(self):
        self.replace(self.root/'call_0000/RESPONSE.json',raw='changed')
        with self.assertRaisesRegex(ValueError,'response_binding'):
            reduction.reduce_root(self.root)

    def test_false_metric_rejected_even_with_rehashed_receipt(self):
        response=self.root/'call_0000/RESPONSE.json'
        value=self.original.read(response)
        value['result']['shifts']=8
        response.write_text(json.dumps(value))
        self.replace(self.root/'progress/0000.json',response_sha256=self.original.sha(response))
        with self.assertRaisesRegex(ValueError,'recomputed_annotation'):
            reduction.reduce_root(self.root)

    def test_native_capture_change_rejected(self):
        self.replace(self.root/'native/CALL.json',raw='changed')
        with self.assertRaisesRegex(ValueError,'source_capture'):
            reduction.reduce_root(self.root)

    def test_foreign_response_path_rejected(self):
        self.replace(self.root/'progress/0000.json',response_path=str(self.root/'native/CALL.json'))
        with self.assertRaisesRegex(ValueError,'response_binding'):
            reduction.reduce_root(self.root)

    def test_progress_index_mismatch_rejected(self):
        self.replace(self.root/'progress/0000.json',index=1)
        with self.assertRaisesRegex(ValueError,'progress_name_binding'):
            reduction.reduce_root(self.root)


if __name__ == '__main__':
    unittest.main()
