from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from organism_v6 import orch_r108_corrected_l2_selection as selection


class FixtureTokenizer:
    eos_token = '<eos>'
    eos_token_id = 1
    all_special_ids = [1]
    name_or_path = 'SYNTHETIC_TEST_TOKENIZER_NOT_NATIVE_PROOF'

    def encode(self, text, **kwargs):
        result = []
        while text:
            if text.startswith(self.eos_token):
                result.append(1)
                text = text[len(self.eos_token):]
            else:
                result.append(ord(text[0]) + 10)
                text = text[1:]
        return result

    def decode(self, ids, **kwargs):
        return ''.join(self.eos_token if value == 1 else chr(value - 10) for value in ids)

    def apply_chat_template(self, messages, add_generation_prompt, **kwargs):
        text = ''.join('<' + message['role'] + '>' + message['content'] + self.eos_token + '\n' for message in messages)
        return text + '<assistant>' if add_generation_prompt else text


class CorrectedL2Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='r108_contract_fixture_')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        state = 'a' * 64
        before = dict(raw='I will guess.', child_id='fixture_child', state_sha256=state, finished_unix=1)
        parent = dict(text='Consider what evidence to inspect.', started_unix=2, finished_unix=3,
            request_visibility='OWN_TRAIN_PUBLIC_ONLY', teacher_exemplar=False)
        continuation = dict(raw='The missing observation matters. I inspect the relevant memory next.',
            child_id='fixture_child', state_sha256=state, started_unix=4, terminal=True, truncated=False)
        prefix = [dict(role='system', content='Use real observations.'), dict(role='user', content='TRAIN task'),
            dict(role='assistant', content=before['raw']), dict(role='user', content=parent['text'])]
        self.case = dict(source_root=str(self.root), split='TRAIN', task_id='TRAIN_case_1', contamination_family='TRAIN_world_A',
            child_state=dict(base_sha256=selection.BASE, state_sha256=state, child_id='fixture_child'),
            before=before, parent=parent, continuation=continuation, prefix=prefix, parent_message_indices=[3],
            original_labels=dict(semantic_status='UNREVIEWED', admitted=False), bindings={})
        self.registry = dict(schema=selection.SCHEMA, sink=selection.SINK, source_purpose='L2_PARENTED_TRAIN',
            sources={str(self.root):dict(purpose='L2_PARENTED_TRAIN', split='TRAIN', teacher_exemplars=False,
                tasks={'TRAIN_case_1':'TRAIN_world_A'})}, artifacts={}, child_states=[state],
            train_families=['TRAIN_world_A'], held_families=['HELD_world_B'], fixed_capability_families=['R107_FIXED32'])
        self.save_sources()

    def save_sources(self):
        groups = [('identity', 'CHILD_LOADED_IDENTITY', ['child_state']),
                  ('before', 'CHILD_NATIVE_CALL', ['before']), ('parent', 'PARENT_INTERVENTION', ['parent']),
                  ('after', 'CHILD_NATIVE_CALL', ['continuation', 'prefix'])]
        for name, kind, fields in groups:
            path = self.root / (name + '.json')
            path.write_text(json.dumps({field:self.case[field] for field in fields},sort_keys=True))
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            self.registry['artifacts'][str(path)] = dict(kind=kind, split='TRAIN', source_root=str(self.root), sha256=sha)
            for field in fields:
                self.case['bindings'][field] = dict(path=str(path), sha256=sha, pointer=[field])

    def review(self):
        return dict(case_sha256=selection.digest(self.case), registry_sha256=selection.digest(self.registry),
            reviewer='SYNTHETIC_FIXTURE_AUTHOR_NOT_NATIVE_REVIEW', full_text_read=True, outcome_used=False,
            functional_status='PASS', grounding_status='PASS', reason='Fixture: a realized evidence gap redirects continuation.',
            prior=[dict(start=0,end=12)], realization=[dict(start=0,end=32)],
            changed_continuation=[dict(start=33,end=len(self.case['continuation']['raw']))], perception_hops=[])

    def test_UNKNOWN_without_review_is_not_supervision(self):
        result = selection.select(self.case,self.registry)
        self.assertEqual(result['selection_status'],'UNKNOWN')
        self.assertFalse(result['trainingAllowed'])

    def test_candidate_preserves_original_labels_and_separate_sink(self):
        result = selection.select(self.case,self.registry,self.review())
        self.assertEqual(result['selection_status'],'CANDIDATE')
        self.assertEqual(result['sink'],selection.SINK)
        self.assertFalse(result['historical_continual_allowed'])
        self.assertEqual(result['original_labels'],self.case['original_labels'])
        self.assertEqual(result['causal_effect'],'UNMEASURED')

    def test_no_hop_branch_method_minimum(self):
        self.assertEqual(selection.select(self.case,self.registry,self.review())['perception_hops'],[])

    def test_perception_and_hops_are_evidence_not_count_threshold(self):
        review = self.review()
        review['perception_hops'] = [dict(kind='PERCEPTION_UPDATE',reason='Fixture changes represented relevance.',
            evidence=[dict(start=0,end=32)]), dict(kind='EVIDENCE_HOP_REDIRECT',reason='Fixture redirects the next evidence hop.',
            evidence=[dict(start=33,end=60)])]
        result = selection.select(self.case,self.registry,review)
        self.assertEqual(len(result['perception_hops']),2)

    def test_failed_and_unknown_not_positive_or_negative_targets(self):
        for status in ('FAIL','UNKNOWN'):
            review = self.review(); review['grounding_status'] = status
            result = selection.select(self.case,self.registry,review)
            self.assertEqual(result['selection_status'],'FAILED' if status=='FAIL' else 'UNKNOWN')
            self.assertEqual(result['supervision_status'],'NONE')
            with self.assertRaisesRegex(ValueError,'no_failed_unknown'):
                selection.encode_candidate(self.case,self.registry,review,FixtureTokenizer(),8192)

    def test_parent_and_all_prior_child_tokens_masked(self):
        result = selection.encode_candidate(self.case,self.registry,self.review(),FixtureTokenizer(),8192)
        self.assertTrue(all(label==-100 for label in result['labels'][:result['context_length']]))
        active = [value for value in result['labels'] if value!=-100]
        self.assertEqual(FixtureTokenizer().decode(active),self.case['continuation']['raw']+'<eos>')
        self.assertFalse(result['trainingAllowed'])
        self.assertTrue(result['parent_context_masked'])

    def test_context_overflow_skips_without_crop(self):
        raw = self.case['continuation']['raw']
        result = selection.encode_candidate(self.case,self.registry,self.review(),FixtureTokenizer(),8)
        self.assertEqual(result['encoding_status'],'SKIP_UNSUPPORTED_TRAIN_CONTEXT')
        self.assertNotIn('labels',result)
        self.assertEqual(self.case['continuation']['raw'],raw)

    def test_source_hash_change_fails(self):
        (self.root/'after.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'native_artifact_hash'):
            selection.select(self.case,self.registry)

    def test_rewritten_target_is_not_actual_native_continuation(self):
        self.case['continuation']['raw'] += ' repaired answer'
        with self.assertRaisesRegex(ValueError,'actual_native_field'):
            selection.select(self.case,self.registry)

    def test_teacher_artifact_cannot_be_child_target(self):
        self.registry['artifacts'][str(self.root/'after.json')]['kind'] = 'TEACHER_EXEMPLAR'
        with self.assertRaisesRegex(ValueError,'native_role'):
            selection.select(self.case,self.registry)

    def test_parent_artifact_cannot_be_child_target(self):
        self.registry['artifacts'][str(self.root/'after.json')]['kind'] = 'PARENT_INTERVENTION'
        with self.assertRaisesRegex(ValueError,'native_role'):
            selection.select(self.case,self.registry)

    def test_held_artifact_and_family_excluded(self):
        self.registry['artifacts'][str(self.root/'after.json')]['split'] = 'HELD'
        with self.assertRaisesRegex(ValueError,'native_role'):
            selection.select(self.case,self.registry)
        self.registry['artifacts'][str(self.root/'after.json')]['split'] = 'TRAIN'
        self.registry['held_families'].append('TRAIN_world_A')
        with self.assertRaisesRegex(ValueError,'contamination_family'):
            selection.select(self.case,self.registry)

    def test_fixed_capability_family_excluded(self):
        self.registry['fixed_capability_families'].append('TRAIN_world_A')
        with self.assertRaisesRegex(ValueError,'contamination_family'):
            selection.select(self.case,self.registry)

    def test_original_L1_sink_cannot_be_used(self):
        self.registry['sink'] = 'ORIGINAL_CONTINUAL'
        with self.assertRaisesRegex(ValueError,'separate_registered'):
            selection.select(self.case,self.registry)

    def test_source_child_changed_by_fit_not_parent_only_continuation(self):
        self.case['continuation']['state_sha256'] = 'b'*64
        self.save_sources()
        with self.assertRaisesRegex(ValueError,'same_actual_child'):
            selection.select(self.case,self.registry)

    def test_parent_after_continuation_is_not_intervention(self):
        self.case['parent']['finished_unix'] = 5
        self.save_sources()
        with self.assertRaisesRegex(ValueError,'intervention_order'):
            selection.select(self.case,self.registry)

    def test_parent_must_be_present_in_actual_prefix(self):
        self.case['prefix'][3]['content'] = 'not the parent message'
        self.save_sources()
        with self.assertRaisesRegex(ValueError,'actual_parent_intervention'):
            selection.select(self.case,self.registry)

    def test_changed_continuation_evidence_not_parent_realization(self):
        review = self.review(); review['changed_continuation'] = []
        with self.assertRaisesRegex(ValueError,'actual_changed_continuation'):
            selection.select(self.case,self.registry,review)

    def test_review_cannot_use_outcome_or_branch_gate(self):
        for change in (dict(outcome_used=True),dict(branch_count=2),dict(case_sha256='0'*64)):
            with self.assertRaises(ValueError):
                selection.select(self.case,self.registry,dict(self.review(),**change))

    def test_schema_is_separate_and_TRAIN_only(self):
        self.assertEqual(selection.case_schema()['properties']['split'],dict(const='TRAIN'))
        self.assertEqual(selection.protocol()['source_label'],'CORRECTED_L2_CHILD_CONTINUATION')


if __name__ == '__main__':
    unittest.main()
