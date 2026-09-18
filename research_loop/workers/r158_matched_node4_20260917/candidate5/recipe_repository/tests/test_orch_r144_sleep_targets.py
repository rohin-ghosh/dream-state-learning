from copy import deepcopy
from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

from gpu import orch_r125_continual_native as native
from gpu.orch_r144_sleep_targets import POLICY, REJECTION, encode_sleep_targets


class Tokenizer:
    eos_token_id = 2
    pad_token_id = 0
    all_special_ids = [0, 1, 2]

    def apply_chat_template(self, prefix, **kwargs):
        return [1, 197]

    def decode(self, tokens, **kwargs):
        return ''.join({0: '<|endoftext|>', 1: '<|im_start|>', 2: '<|im_end|>'}.get(
            token, chr(token)) for token in tokens)


def row(name, tokens=None, **changes):
    tokens = [97, 2] if tokens is None else tokens
    value = dict(source_sha256=name, split='TRAIN', actor='child', prefix_loss=False,
        target_loss=True, prefix=[dict(role='user', content='Original parent context')],
        token_ids=tokens, terminal=True, target=Tokenizer().decode(tokens[:-1]))
    value.update(changes)
    return value


class SleepTargetTests(unittest.TestCase):
    def setUp(self):
        runtime = patch('gpu.orch_r145_suffix_boundary.prepare_sleep')
        runtime.start()
        self.addCleanup(runtime.stop)

    def encode(self, new_rows, old_rows=(), encoder=native.encode_own):
        return encode_sleep_targets(new_rows, old_rows, Tokenizer(), 100, encoder)

    def test_excludes_only_guard_rejections_in_both_cohorts_without_mutation(self):
        new_rows = [row('new-ok'), row('new-bad', [97, 1, 2])]
        old_rows = [row('old-bad', [1, 97, 2]), row('old-ok')]
        before = deepcopy((new_rows, old_rows))
        new, old, encoded, excluded = self.encode(new_rows, old_rows)
        self.assertEqual((new_rows, old_rows), before)
        self.assertEqual(new, [new_rows[0]])
        self.assertIs(new[0], new_rows[0])
        self.assertEqual(old, [old_rows[1]])
        self.assertEqual(set(encoded), {'new-ok', 'old-ok'})
        self.assertEqual(excluded, [dict(source_sha256='new-bad', cohort='NEW',
            reason=REJECTION, policy=POLICY), dict(source_sha256='old-bad',
            cohort='REHEARSAL', reason=REJECTION, policy=POLICY)])
        self.assertEqual(native.presentation_schedule(new, old),
            [('NEW', new[0])] * 16 + [('REHEARSAL', old[0])])

    def test_encoder_itself_still_rejects_role_tokens(self):
        with self.assertRaisesRegex(ValueError, REJECTION):
            native.encode_own(row('bad', [97, 1, 2]), Tokenizer(), 100)

    def test_preserves_actual_terminal_eos_and_genuine_endoftext(self):
        value = row('valid', [97, 0, 2])
        new, old, encoded, excluded = self.encode([value])
        self.assertEqual(new, [value])
        self.assertEqual(excluded, [])
        self.assertEqual(encoded['valid'].target_ids, (97, 0, 2))
        self.assertEqual(encoded['valid'].labels[:2], (-100, -100))

    def test_does_not_classify_role_like_plain_text_as_special_tokens(self):
        value = row('plain', [ord(character) for character in 'Astra: hello'] + [2])
        self.assertEqual(self.encode([value])[0], [value])

    def test_unrelated_encoder_and_visibility_errors_remain_fatal(self):
        variants = [dict(split='DEV'), dict(split='FINAL'), dict(actor='parent'),
            dict(prefix_loss=True), dict(target_loss=False), dict(token_ids=[]),
            dict(target='rewritten'), dict(terminal=True, token_ids=[97])]
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.encode([row('invalid', **changes)])
        with self.assertRaisesRegex(ValueError, 'whole_source_no_training_trim'):
            encode_sleep_targets([row('long')], [], Tokenizer(), 1, native.encode_own)

    def test_catches_exact_error_only(self):
        errors = [ValueError(REJECTION + ':other'), ValueError(REJECTION, 'extra'),
            RuntimeError(REJECTION), MemoryError('OOM')]
        for error in errors:
            with self.subTest(error=repr(error)), self.assertRaises(type(error)):
                self.encode([row('valid')], encoder=Mock(side_effect=error))

    def test_empty_or_all_rejected_returns_no_training_targets(self):
        self.assertEqual(self.encode([]), ([], [], {}, []))
        new, old, encoded, excluded = self.encode([row('bad', [1, 2])])
        self.assertEqual((new, old, encoded), ([], [], {}))
        self.assertEqual(len(excluded), 1)

    def test_sleep_logs_all_rejected_and_preserves_optimizer_without_training(self):
        child = object.__new__(native.NativeChild)
        child.plan = dict(context_limit=100)
        child.tokenizer = Tokenizer()
        child.optimizer_steps = 123
        child.adapter_hash = Mock(return_value='unchanged')
        child.engine = SimpleNamespace(verify_base=Mock())
        records = []
        rows = [row('bad', [1, 2])]
        before = deepcopy(rows)
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            result = child.sleep(rows, [], dict(a=[], b=[], c=[], d=[]),
                lambda kind, document: records.append((kind, document)))
        self.assertEqual(rows, before)
        self.assertEqual(child.optimizer_steps, 123)
        self.assertEqual(result['optimizer_steps'], 0)
        self.assertEqual(result['child_token_exposures'], 0)
        self.assertEqual(result['anchor_token_exposures'], 0)
        self.assertEqual(result['anchor_lambda'], 0.25)
        self.assertEqual(result['no_update_reason'], 'no_eligible_child_rows')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][0], 'TARGET_ELIGIBILITY')
        self.assertEqual(records[0][1]['runtime_policy'], POLICY)
        self.assertFalse(records[0][1]['raw_modified'])
        self.assertEqual(records[0][1]['new_row_sha256'], [])
        self.assertEqual(records[0][1]['excluded'], result['excluded_rows'])

    def training_child(self):
        child = object.__new__(native.NativeChild)
        child.plan = dict(context_limit=100)
        child.tokenizer = Tokenizer()
        child.optimizer_steps = 123
        child.adapter_hash = Mock(side_effect=['before', 'after'])
        parameter = Mock(grad=Mock())
        child.parameters = {'adapter': parameter}
        child.optimizer = Mock()
        child.check = Mock()
        loss = Mock()
        loss.item.return_value = 1.0
        loss.__mul__ = Mock(return_value=Mock())
        model = Mock(return_value=SimpleNamespace(loss=loss))
        model.named_parameters.return_value = []
        child.engine = SimpleNamespace(model=model, verify_base=Mock())
        child.native = SimpleNamespace(is_lora=lambda name: name == 'adapter')
        child.torch = Mock()
        child.torch.tensor.return_value = MagicMock()
        child.torch.autocast.side_effect = lambda **kwargs: nullcontext()
        child.torch.isfinite.return_value.all.return_value = True
        sample = native.encode_own(row('anchor'), child.tokenizer, 100)
        anchors = {name: [dict(encoded=sample)] for name in ('a', 'b', 'c', 'd')}
        return child, anchors

    def test_actual_sleep_omits_bad_new_and_old_from_updates_and_counts(self):
        child, anchors = self.training_child()
        rows = [row('new'), row('bad-new', [1, 2])]
        old = [row('bad-old', [1, 2]), row('old')]
        before = deepcopy((rows, old))
        records = []
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            result = child.sleep(rows, old, anchors,
                lambda kind, document: records.append((kind, document)))
        self.assertEqual((rows, old), before)
        self.assertEqual(result['presentations'], {'new': 16, 'old': 1})
        self.assertEqual(result['optimizer_steps'], 17)
        self.assertEqual(result['total_optimizer_steps'], 140)
        self.assertEqual(result['child_token_exposures'], 34)
        self.assertEqual(result['anchor_token_exposures'], 136)
        self.assertEqual(child.optimizer.step.call_count, 17)
        updates = [document for kind, document in records if kind == 'UPDATE']
        self.assertEqual([item['source_sha256'] for item in updates], ['new'] * 16 + ['old'])
        self.assertEqual(records[0][0], 'TARGET_ELIGIBILITY')
        self.assertEqual(records[0][1]['new_row_sha256'], ['new'])
        self.assertEqual(records[0][1]['rehearsal_row_sha256'], ['old'])
        for update in updates:
            self.assertEqual([loss['objective_weight'] for loss in update['losses']],
                [0.75, 0.0625, 0.0625, 0.0625, 0.0625])

    def test_existing_presentation_exclusion_is_combined_with_encoder_exclusions(self):
        child, anchors = self.training_child()
        child.plan.update(presentation_version='existing', system_prompt='same', birth_prompt='same')
        discarded = row('old-presentation')
        bad = row('special', [1, 2])
        valid = row('old-valid')
        records = []
        def eligibility(rows, presentation):
            return [item for item in rows if item['source_sha256'] != 'old-presentation'], [
                dict(source_sha256=item['source_sha256'], reason='existing_reason')
                for item in rows if item['source_sha256'] == 'old-presentation']
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'), \
                patch('organism_v6.orch_r125_plain_context.eligible_rows', side_effect=eligibility):
            result = child.sleep([discarded, bad], [valid], anchors,
                lambda kind, document: records.append((kind, document)))
        self.assertEqual(result['presentations'], {'old-valid': 1})
        self.assertEqual(result['optimizer_steps'], 1)
        self.assertEqual(len(records[0][1]['excluded']), 2)
        self.assertEqual(records[0][1]['excluded'][0], dict(
            source_sha256='old-presentation', reason='existing_reason', cohort='NEW'))
        self.assertEqual(records[0][1]['version'], 'existing')


if __name__ == '__main__':
    unittest.main()
