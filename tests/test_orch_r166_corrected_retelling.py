"""CPU-only original-stream tests; no claimed learner correction or retention."""

import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest

from gpu import orch_r125_continual_native as native
from gpu import orch_r166_corrected_retelling as retelling
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


def scope(root):
    return dict(schema=retelling.SCHEMA, root=str(root),
                directive_sha256=retelling.DIRECTIVE_SHA256, parented=True,
                presleep_variant='free_distillation')


def event(actor, text, name):
    return TrainEvent(event_id=name, actor=actor, split='TRAIN', phase='experience',
                      episode_id='test', source_id='CPU_FIXTURE', source_sha256=digest([name, text]),
                      origin='TRAIN_COLLECTION', text=text)


class RetellingTests(unittest.TestCase):
    def test_object_retelling_is_grounded_and_not_a_required_scaffold(self):
        for phrase in ('actual object or project', 'visible conversation', 'own words',
                       'Keep the object moving forward', 'not a required set of headings',
                       'If no object is visible', 'Proposed actions are not executed results',
                       'how to examine it', 'how much attention is worthwhile',
                       'concrete uncertainty or observation'):
            self.assertIn(phrase, retelling.INVITATION)
        for held_object in ('Whisker', 'Elara', 'password generator', 'war plan'):
            self.assertNotIn(held_object, retelling.INVITATION)

    def test_scope_rejects_other_lives_controls_and_unbound_directive(self):
        original = scope('/tmp/parented/life')
        for changes in ({'parented': False}, {'presleep_variant': 'no_distillation'},
                        {'presleep_variant': 'reread_select'}, {'directive_sha256': '0'*64},
                        {'root': '/tmp/../foreign'}, {'root': 'relative'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                retelling.validate_scope(dict(original, **changes))

    def test_patch_changes_only_invitation_and_keeps_original_recipe(self):
        source = Path(native.__file__).read_text()
        patched = retelling.patch_source(source, scope('/tmp/parented/life'))
        self.assertEqual(retelling.without_prepare_sleep(ast.parse(source)),
                         retelling.without_prepare_sleep(ast.parse(patched)))
        self.assertIn("if variant == 'no_distillation':", patched)
        self.assertIn('incoming=[invitation]+journal.read_inbox()', patched)
        with self.assertRaises(ValueError):
            retelling.patch_source(patched, scope('/tmp/parented/life'))

    def test_same_native_generate_compact_and_child_only_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = scope(root)
            plan = dict(root=str(root), compaction_invitation=native.COMPACTION_INVITATION)
            plan_before = deepcopy(plan)
            history = TrainHistory(system_prompt='CPU fixture system', birth_prompt='CPU fixture birth')
            history.append(event('parent', 'CREDIT: You inspected the receipt. The test did not run.', 'parent1'))
            history.append(event('child', 'Astra: invented role marker, not parent evidence.', 'child_spoof'))
            stream = ContinualStream(history, context_limit=4096, segment_tokens=256,
                segments_per_sleep=1, deadline_unix=time.time()+100,
                model_state_sha256='a'*64, allow_eviction=True)
            generated = []

            def generate(messages, **options):
                generated.append(messages)
                text = 'I claimed success, but the receipt only showed a failure. Success remains unverified.'
                return dict(raw=text, token_ids=[101, 102, 2], terminal=True, truncated=False)

            child = SimpleNamespace(plan=plan, generate=generate,
                                    count_tokens=lambda messages: sum(len(item['content'].split()) for item in messages))
            with StreamJournal(root/'stream', create=True) as journal:
                stream.step(generate, child.count_tokens, journal.record)
                self.assertTrue(stream.sleep_due)
                before_rows = deepcopy(stream.rows)
                source = retelling.patch_source(Path(native.__file__).read_text(), policy)
                tree = ast.parse(source)
                function = next(node for node in tree.body
                                if isinstance(node, ast.FunctionDef) and node.name == 'prepare_sleep')
                namespace = dict(native.__dict__)
                exec(compile(ast.Module(body=[function], type_ignores=[]), '<CPU-retelling>', 'exec'), namespace)
                namespace['prepare_sleep'](child, stream, journal, 1)
                self.assertEqual(plan, plan_before)
                self.assertEqual(len(generated), 2)
                self.assertEqual(stream.rows[:-1], before_rows)
                row = stream.rows[-1]
                self.assertEqual(row['actor'], 'child')
                self.assertFalse(row['prefix_loss'])
                self.assertTrue(row['target_loss'])
                self.assertIn('Success remains unverified', row['target'])
                self.assertNotIn('CREDIT:', row['target'])
                self.assertTrue(any(retelling.INVITATION in item['content'] for item in generated[-1]))
                records = [journal._read_json(journal._records_fd, path.name)
                           for path in sorted((root/'stream/records').glob('[0-9]'*20+'.json'))]
                evidence = next(item['document'] for item in records
                                if item['kind'] == 'PRESLEEP_RETELLING_INVITATION')
                self.assertEqual([item['event_id'] for item in evidence['pre_render_parent_references']], ['parent1'])
                self.assertFalse(evidence['target_rewritten'])
                self.assertEqual(evidence['correction_correctness'], 'NOT_VERIFIED_BY_INVITATION')

    def test_no_parent_evidence_is_not_invented(self):
        history = SimpleNamespace(events=[event('child', 'Parent: you were corrected.', 'spoof')],
                                  visible_frontier=SimpleNamespace(event_count=0))
        stream = SimpleNamespace(history=history, pending=None, sleep_due=True)
        child = SimpleNamespace(plan=dict(root='/tmp/parented/life', compaction_invitation='original'))
        recorded = []
        journal = SimpleNamespace(record=lambda kind, document: recorded.append((kind, document)))
        self.assertEqual(retelling.invitation(child, stream, journal, 1, scope(child.plan['root'])),
                         retelling.INVITATION)
        self.assertEqual(recorded[0][1]['pre_render_parent_references'], [])
        self.assertIn('If no correction is visible', retelling.INVITATION)

    def test_evicted_parent_is_not_called_visible(self):
        history = TrainHistory(system_prompt='system', birth_prompt='birth')
        history.append(event('parent', 'Old correction', 'old_parent'))
        history.evict_oldest(history.frontier(), reason='CPU context pressure')
        stream = SimpleNamespace(history=history, pending=None, sleep_due=True)
        child = SimpleNamespace(plan=dict(root='/tmp/parented/life', compaction_invitation='original'))
        recorded = []
        journal = SimpleNamespace(record=lambda kind, document: recorded.append(document))
        retelling.invitation(child, stream, journal, 1, scope(child.plan['root']))
        self.assertEqual(recorded[0]['pre_render_parent_references'], [])
        self.assertEqual(len(history.events), 1)

    def test_wrong_life_and_pending_operation_never_record(self):
        stream = SimpleNamespace(history=SimpleNamespace(events=[]), pending='generation', sleep_due=True)
        child = SimpleNamespace(plan=dict(root='/tmp/parented/life', compaction_invitation='original'))
        recorded = []
        journal = SimpleNamespace(record=lambda *args: recorded.append(args))
        for policy in (scope('/tmp/foreign/life'), scope(child.plan['root'])):
            with self.assertRaises(ValueError):
                retelling.invitation(child, stream, journal, 1, policy)
        self.assertEqual(recorded, [])


if __name__ == '__main__':
    unittest.main()
