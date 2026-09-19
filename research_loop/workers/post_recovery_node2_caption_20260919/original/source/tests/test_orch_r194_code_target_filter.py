"""Synthetic CPU-only target filtering and checkpoint regressions; no live model."""

from contextlib import nullcontext
from copy import deepcopy
import builtins
import hashlib
import json
from pathlib import Path
import random
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import torch

from gpu import orch_r125_continual_native as native
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6 import orch_r194_code_target_filter as target_filter


BAD_TARGET = '```python\nprint(１ + ２)\n```'
CLEAN_TARGET = '```python\nprint(1 + 2)\n```'


class Tokenizer:
    eos_token_id = 2
    all_special_ids = [0, 1, 2]

    def apply_chat_template(self, messages, **kwargs):
        return [1] + [ord(character) + 100 for message in messages for character in message['content']]

    def decode(self, tokens, **kwargs):
        return ''.join(chr(token - 100) for token in tokens)


def row(name, target=CLEAN_TARGET, **changes):
    return dict(dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
        append_eos=False, terminal=True, truncated=False, prefix=[dict(role='user', content='Think.')],
        target=target, token_ids=[ord(character) + 100 for character in target] + [2],
        source_sha256=digest(name)), **changes)


class CpuTorch:
    cuda = SimpleNamespace(get_rng_state_all=lambda: [])

    def __getattr__(self, name):
        return getattr(torch, name)

    def tensor(self, values, *, device, **kwargs):
        if device != 'cuda:0':
            raise AssertionError('unexpected native device contract')
        return torch.tensor(values, device='cpu', **kwargs)

    def autocast(self, **kwargs):
        if kwargs != dict(device_type='cuda', dtype=torch.bfloat16):
            raise AssertionError('unexpected native autocast contract')
        return nullcontext()


class SyntheticModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.lora_weight = torch.nn.Parameter(torch.tensor(0.5), requires_grad=False)
        self.base_weight = torch.nn.Parameter(torch.tensor(1.0), requires_grad=False)
        self.forward_calls = 0

    def forward(self, **kwargs):
        self.forward_calls += 1
        return SimpleNamespace(loss=self.lora_weight.square() + self.base_weight)

    def save_pretrained(self, directory, **kwargs):
        Path(directory).mkdir()
        torch.save(self.state_dict(), Path(directory) / 'synthetic_adapter.pt')


def child_fixture(*, enabled=True, rehearsal=0):
    child = object.__new__(native.NativeChild)
    child.plan = dict(context_limit=8192, new_presentations=16, rehearsal_presentations=rehearsal)
    if enabled:
        child.plan['code_target_filter'] = target_filter.POLICY
    child.plasticity = None
    child.experiment = None
    child.tokenizer = Tokenizer()
    child.optimizer_steps = 23
    child.engine = SimpleNamespace(model=SyntheticModel(), verify_base=Mock())
    child.parameters = {'lora_weight': child.engine.model.lora_weight}
    child.optimizer = torch.optim.SGD(child.parameters.values(), lr=0.01, momentum=0.5)
    child.optimizer.state[child.engine.model.lora_weight]['momentum_buffer'] = torch.tensor(0.25)
    child.optimizer.step = Mock(wraps=child.optimizer.step)
    child.optimizer.zero_grad = Mock(wraps=child.optimizer.zero_grad)
    child.adapter_hash = lambda: digest(child.engine.model.lora_weight.detach().tolist())
    child.native = SimpleNamespace(is_lora=lambda name: name == 'lora_weight')
    child.torch = CpuTorch()
    child.check = Mock()
    sample = native.encode_own(row('anchor', 'Ordinary anchor.'), child.tokenizer, 8192)
    anchors = {family: [dict(encoded=sample)] for family in ('a', 'b', 'c', 'd')}
    return child, anchors


def run_sleep(child, anchors, new_rows, old_rows=()):
    records = []
    with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
        receipt = child.sleep(new_rows, old_rows, anchors,
            lambda kind, document: records.append((kind, deepcopy(document))))
    return receipt, records


def completed_receipt(child, anchors, new_rows, old_rows=()):
    receipt, _ = run_sleep(child, anchors, new_rows, old_rows)
    receipt.update(status='COMPLETE', new_row_sha256=[item['source_sha256'] for item in new_rows],
        checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64),
        checkpoint=dict(optimizer_steps=child.optimizer_steps, adapter_state_sha256=child.adapter_hash()))
    return receipt


class ScannerTests(unittest.TestCase):
    def test_all_fullwidth_ascii_range_and_separate_ideographic_space(self):
        for point in range(0xFF01, 0xFF5F):
            with self.subTest(codepoint=hex(point)):
                evidence = target_filter.scan_target('```python\n' + chr(point) + '\n```')
                self.assertEqual(evidence['codepoints'], [dict(codepoint=f'U+{point:04X}', count=1,
                    category='FULLWIDTH_ASCII_RANGE')])
                self.assertEqual(evidence['affected_blocks'], [1])
        self.assertEqual(target_filter.scan_target('```\n　\n```')['codepoints'],
            [dict(codepoint='U+3000', count=1, category='IDEOGRAPHIC_SPACE')])

    def test_prose_inline_code_and_non_ascii_natural_language_do_not_trigger(self):
        texts = ['Prose ＡＢ１２ and　space.', '`print(１)`', '``print(１)``',
            '```python\n# 中文 Ελληνικά 😀 é ∑\nprint("日本語")\n```',
            '```语言\nprint(1)\n```\nOutside ２', '```fullwidth_Ａ_info_only\npass\n```',
            '```python\n' + chr(0xFF00) + chr(0xFF5F) + '\n```']
        for text in texts:
            with self.subTest(text=text):
                self.assertEqual(target_filter.scan_target(text)['glyph_count'], 0)

    def test_all_blocks_including_later_and_unclosed(self):
        text = CLEAN_TARGET + '\nProse ７\n~~~python\nprint(３)\n~~~\n```python\nx = ４'
        evidence = target_filter.scan_target(text)
        self.assertEqual(evidence['fenced_blocks'], 3)
        self.assertEqual(evidence['affected_blocks'], [2, 3])
        self.assertEqual(evidence['glyph_count'], 2)
        self.assertTrue(evidence['unclosed_fenced_block'])

    def test_fence_lengths_characters_and_trailing_content_do_not_close_early(self):
        texts = ['````python\n```\nprint(１)\n````',
            '~~~python\n```\nprint(１)\n~~~', '```python\n``` not a close\nprint(１)\n```']
        for text in texts:
            with self.subTest(text=text):
                evidence = target_filter.scan_target(text)
                self.assertEqual(evidence['glyph_count'], 1)
                self.assertFalse(evidence['unclosed_fenced_block'])

    def test_same_line_fences_indentation_quotes_and_lists(self):
        texts = ['```print(１)```', '  ~~~print(１)~~~',
            '\t```python\r\nprint(１)\r\n\t```', '> ```python\n> print(１)\n> ```',
            '- ```python\n  print(１)\n  ```', '> 1. ```python\n>    print(１)\n>    ```']
        for text in texts:
            with self.subTest(text=text):
                evidence = target_filter.scan_target(text)
                self.assertEqual(evidence['glyph_count'], 1)
                self.assertFalse(evidence['unclosed_fenced_block'])

    def test_literals_and_comments_are_excluded_without_normalization(self):
        for body in ('print("Ａ")', '# fullwidth ２', 'value = "　"'):
            with self.subTest(body=body):
                self.assertGreater(target_filter.scan_target('```python\n' + body + '\n```')['glyph_count'], 0)

    def test_policy_is_opt_in_and_unknown_values_fail_closed(self):
        self.assertIsNone(target_filter.validate_policy({}))
        self.assertEqual(target_filter.validate_policy(dict(code_target_filter=target_filter.POLICY)), target_filter.POLICY)
        for policy in (None, False, True, '', 'NFKC', [], {}, target_filter.POLICY + '_V2'):
            with self.subTest(policy=policy), self.assertRaisesRegex(ValueError, 'known_code_target_filter_policy'):
                target_filter.validate_policy(dict(code_target_filter=policy))
        with self.assertRaisesRegex(ValueError, 'raw_text_required'):
            target_filter.scan_target(None)

    def test_source_bound_exclusions_keep_row_identity_order_and_raw_bytes(self):
        new_rows = [row('new_bad', BAD_TARGET), row('new_clean'), row('prose', '１ in prose')]
        old_rows = [row('old_clean'), row('old_bad', BAD_TARGET)]
        before = deepcopy((new_rows, old_rows))
        retained_new, retained_old, proof = target_filter.filter_sleep_targets(new_rows, old_rows, target_filter.POLICY)
        self.assertEqual((new_rows, old_rows), before)
        self.assertIs(retained_new[0], new_rows[1])
        self.assertIs(retained_new[1], new_rows[2])
        self.assertIs(retained_old[0], old_rows[0])
        self.assertEqual(proof['retained_counts'], dict(NEW=2, REHEARSAL=1))
        self.assertEqual(proof['excluded_counts'], dict(NEW=1, REHEARSAL=1))
        self.assertEqual(proof['input_row_sha256'], dict(NEW=[item['source_sha256'] for item in new_rows],
            REHEARSAL=[item['source_sha256'] for item in old_rows]))
        self.assertEqual([item['source_sha256'] for item in proof['excluded']], [digest('new_bad'), digest('old_bad')])
        self.assertTrue(all(item['raw_target_sha256'] == hashlib.sha256(BAD_TARGET.encode()).hexdigest()
            for item in proof['excluded']))
        self.assertFalse(proof['raw_modified'])
        self.assertFalse(proof['targets_normalized'])

    def test_prefixes_are_masked_not_scanned_as_targets(self):
        clean = row('clean', prefix=[dict(role='user', content=BAD_TARGET)])
        retained, _, proof = target_filter.filter_sleep_targets([clean], [], target_filter.POLICY)
        self.assertIs(retained[0], clean)
        self.assertEqual(proof['excluded'], [])

    def test_target_row_and_source_contracts_stay_strict(self):
        changes = [dict(split='FINAL'), dict(actor='parent'), dict(prefix_loss=True),
            dict(target_loss=False), dict(source_sha256='invented'), dict(source_sha256=None)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                target_filter.filter_sleep_targets([row('bad', **change)], [], target_filter.POLICY)


class NativeSleepTests(unittest.TestCase):
    def test_disabled_native_validation_and_sleep_do_not_import_optional_helper(self):
        original_import = builtins.__import__

        def without_filter(name, *args, **kwargs):
            if name == 'organism_v6.orch_r194_code_target_filter':
                raise ImportError('helper unavailable in a legacy closure')
            return original_import(name, *args, **kwargs)

        plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
            system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
            compaction_invitation=native.COMPACTION_INVITATION,
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
            seed=0, segments_per_sleep=2, segment_tokens=16, context_limit=8192,
            max_sleeps=2, physical=0, gpu_uuid='GPU-synthetic',
            hard_end_unix=time.time() + 600, lease_end_unix=time.time() + 1000,
            decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
            root='/tmp/r194-synthetic-life', model_dir='/tmp/r194-synthetic-model',
            anchors='/tmp/r194-synthetic-anchors', source_root='/tmp/r194-synthetic-source')
        child, anchors = child_fixture(enabled=False)
        with patch('builtins.__import__', side_effect=without_filter):
            self.assertIs(native.validate_plan(plan), plan)
            receipt, _ = run_sleep(child, anchors, [row('bad', BAD_TARGET)])
        self.assertEqual(receipt['optimizer_steps'], 16)

    def test_plan_validator_rejects_unknown_policy_before_other_plan_checks(self):
        plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256, code_target_filter='unknown')
        with self.assertRaisesRegex(ValueError, 'known_code_target_filter_policy'):
            native.validate_plan(plan)
        child, anchors = child_fixture()
        child.plan['code_target_filter'] = None
        with self.assertRaisesRegex(ValueError, 'known_code_target_filter_policy'):
            run_sleep(child, anchors, [row('bad', BAD_TARGET)])
        child.optimizer.step.assert_not_called()

    def test_default_still_trains_fullwidth_targets_without_new_metadata(self):
        child, anchors = child_fixture(enabled=False)
        receipt, records = run_sleep(child, anchors, [row('bad', BAD_TARGET)])
        self.assertEqual(receipt['optimizer_steps'], 16)
        self.assertEqual(receipt['presentations'], {digest('bad'): 16})
        for document in [receipt] + [document for _, document in records]:
            self.assertFalse(any(key.startswith('code_target_filter') for key in document))

    def test_clean_opt_in_matches_legacy_loss_order_weights_and_learning_state(self):
        child, anchors = child_fixture()
        legacy, legacy_anchors = child_fixture(enabled=False)
        receipt, records = run_sleep(child, anchors, [row('clean')])
        old_receipt, old_records = run_sleep(legacy, legacy_anchors, [row('clean')])
        self.assertEqual({key: value for key, value in receipt.items() if not key.startswith('code_target_filter')}, old_receipt)
        updates = [document for kind, document in records if kind == 'UPDATE']
        old_updates = [document for kind, document in old_records if kind == 'UPDATE']
        self.assertEqual([{key: value for key, value in document.items() if key != 'finished_unix'} for document in updates],
            [{key: value for key, value in document.items() if key != 'finished_unix'} for document in old_updates])
        self.assertEqual([loss['objective_weight'] for loss in updates[0]['losses']], [0.75] + [0.0625] * 4)
        self.assertEqual(child.optimizer.state_dict(), legacy.optimizer.state_dict())

    def test_mixed_new_and_rehearsal_rows_count_only_retained_presentations(self):
        child, anchors = child_fixture(rehearsal=1)
        new_rows = [row('new_bad', BAD_TARGET), row('new_good')]
        old_rows = [row('old_good'), row('old_bad', BAD_TARGET)]
        before = deepcopy((new_rows, old_rows))
        receipt, records = run_sleep(child, anchors, new_rows, old_rows)
        self.assertEqual((new_rows, old_rows), before)
        self.assertEqual(receipt['presentations'], {digest('new_good'): 16, digest('old_good'): 1})
        self.assertEqual(receipt['code_target_filter_presentations'], receipt['presentations'])
        self.assertEqual(receipt['code_target_filter_counts'], dict(NEW=1, REHEARSAL=1))
        self.assertEqual(receipt['optimizer_steps'], 17)
        self.assertEqual(child.optimizer.step.call_count, 17)
        self.assertEqual(child.engine.model.forward_calls, 17 * 5)
        self.assertEqual([document['source_sha256'] for kind, document in records if kind == 'UPDATE'],
            [digest('new_good')] * 16 + [digest('old_good')])
        self.assertEqual(records[0][1]['code_target_filter'], target_filter.POLICY)
        self.assertEqual(records[1][1]['code_target_filter'], receipt['code_target_filter'])
        self.assertNotIn('code_target_filter_zero_update', receipt)

    def test_new_only_does_not_scan_or_encode_any_old_rows(self):
        child, anchors = child_fixture(rehearsal=0)
        receipt, _ = run_sleep(child, anchors, [row('bad', BAD_TARGET)], [dict(unusable='not selected')])
        self.assertEqual(receipt['code_target_filter']['input_row_sha256']['REHEARSAL'], [])
        self.assertEqual(receipt['code_target_filter_zero_update']['rehearsal_presentations'], 0)
        child.optimizer.step.assert_not_called()

    def test_all_excluded_means_no_forward_anchor_updates_optimizer_or_rng_changes(self):
        child, anchors = child_fixture(rehearsal=1)
        adapter = child.adapter_hash()
        optimizer = deepcopy(child.optimizer.state_dict())
        cpu_rng, python_rng = torch.get_rng_state().clone(), random.getstate()
        receipt, records = run_sleep(child, anchors, [row('bad_new', BAD_TARGET)], [row('bad_old', BAD_TARGET)])
        self.assertEqual(child.adapter_hash(), adapter)
        self.assertEqual(child.optimizer.state_dict(), optimizer)
        self.assertEqual(child.optimizer_steps, 23)
        self.assertTrue(torch.equal(torch.get_rng_state(), cpu_rng))
        self.assertEqual(random.getstate(), python_rng)
        child.optimizer.step.assert_not_called()
        child.optimizer.zero_grad.assert_not_called()
        self.assertEqual(child.engine.model.forward_calls, 0)
        self.assertIsNone(child.engine.model.lora_weight.grad)
        self.assertFalse(child.engine.model.lora_weight.requires_grad)
        self.assertEqual(receipt['no_update_reason'], target_filter.NO_UPDATE_REASON)
        self.assertEqual(receipt['optimizer_steps'], 0)
        self.assertEqual(receipt['child_token_exposures'], 0)
        self.assertEqual(receipt['anchor_token_exposures'], 0)
        self.assertEqual(receipt['presentations'], {})
        self.assertEqual([kind for kind, _ in records], ['SLEEP_RECIPE', 'TARGET_ELIGIBILITY'])

    def test_clean_rehearsal_still_trains_when_all_new_targets_excluded(self):
        child, anchors = child_fixture(rehearsal=1)
        receipt, _ = run_sleep(child, anchors, [row('bad_new', BAD_TARGET)], [row('good_old')])
        self.assertEqual(receipt['optimizer_steps'], 1)
        self.assertEqual(receipt['presentations'], {digest('good_old'): 1})
        self.assertNotIn('code_target_filter_zero_update', receipt)

    def test_other_exclusions_cannot_borrow_r194_zero_update_authorization(self):
        child, anchors = child_fixture()
        receipt, _ = run_sleep(child, anchors,
            [row('bad', BAD_TARGET), row('special', token_ids=[1, 2])])
        self.assertEqual(receipt['optimizer_steps'], 0)
        self.assertEqual(receipt['no_update_reason'], 'no_eligible_child_rows')
        self.assertNotIn('code_target_filter_zero_update', receipt)
        self.assertEqual(len(receipt['excluded_rows']), 2)


class JournalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(lambda: self.journal.close())
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Investigate.'),
            context_limit=8192, segment_tokens=512, segments_per_sleep=2,
            deadline_unix=time.time() + 600, model_state_sha256='f' * 64)
        self.child, self.anchors = child_fixture()

    def step(self, target=BAD_TARGET):
        return self.stream.step(lambda *args, **kwargs: dict(raw=target,
            token_ids=[ord(character) + 100 for character in target] + [2], terminal=True, truncated=False),
            lambda messages: sum(len(message['content'].split()) + 4 for message in messages), self.journal.record)

    def receipt(self):
        return completed_receipt(self.child, self.anchors, self.stream.pending_rows(),
            self.stream.rows[:self.stream.sleep_frontier])

    def test_all_excluded_real_checkpoint_audit_reload_and_next_clean_sleep(self):
        self.step()
        self.step()
        rows_before = deepcopy(self.stream.rows)
        history_before = self.stream.history.checkpoint()
        cpu_rng, python_rng = torch.get_rng_state().clone(), random.getstate()
        optimizer_before = deepcopy(self.child.optimizer.state_dict())
        pending = self.stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([item['source_sha256'] for item in self.stream.pending_rows()])
        pending['sha256'] = digest(pending['state'])
        self.journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            checkpoint = native.finish_sleep(self.child, self.stream, self.journal, self.anchors, self.root, 1)
        native.NativeChild.verify_checkpoint(checkpoint)
        self.assertEqual(self.stream.rows, rows_before)
        self.assertEqual(self.stream.history.checkpoint(), history_before)
        self.assertEqual(self.stream.sleep_frontier, 2)
        self.assertEqual(self.stream.pending_rows(), [])
        self.assertEqual(self.stream.sleep_receipts[-1]['optimizer_steps'], 0)
        self.assertEqual(self.stream.sleep_receipts[-1]['new_row_sha256'], [item['source_sha256'] for item in rows_before])
        self.assertTrue(torch.equal(torch.get_rng_state(), cpu_rng))
        self.assertEqual(random.getstate(), python_rng)
        payload = torch.load(checkpoint['optimizer_rng_path'], weights_only=False, map_location='cpu')
        self.assertEqual(payload['optimizer'], optimizer_before)
        self.assertEqual(payload['optimizer_steps'], 23)
        self.assertTrue(torch.equal(payload['cpu_rng'], cpu_rng))
        self.assertEqual(payload['python_rng'], python_rng)
        self.journal.audit()
        self.journal.close()
        self.journal = StreamJournal(self.root / 'stream')
        self.stream = ContinualStream.restore(**self.journal.latest_checkpoint())
        self.child, self.anchors = child_fixture()
        self.child.engine.model.load_state_dict(torch.load(Path(checkpoint['adapter_path']) / 'synthetic_adapter.pt',
            weights_only=True, map_location='cpu'))
        self.child.optimizer.load_state_dict(payload['optimizer'])
        self.child.optimizer_steps = payload['optimizer_steps']
        self.assertEqual(self.child.adapter_hash(), checkpoint['adapter_state_sha256'])
        self.assertEqual(self.stream.rows, rows_before)
        self.step(CLEAN_TARGET)
        self.step(CLEAN_TARGET)
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            next_checkpoint = native.finish_sleep(self.child, self.stream, self.journal, self.anchors, self.root, 2)
        self.assertEqual(self.stream.sleep_frontier, 4)
        self.assertEqual(self.stream.sleep_receipts[-1]['optimizer_steps'], 32)
        self.assertEqual(next_checkpoint['optimizer_steps'], 55)
        self.assertEqual(self.stream.rows[:2], rows_before)
        self.journal.audit()

    def corruptions(self, original):
        paths = [
            (('code_target_filter_zero_update', 'schema'), 'unknown'),
            (('code_target_filter_zero_update', 'policy'), 'unknown'),
            (('code_target_filter_zero_update', 'eligibility_sha256'), '0' * 64),
            (('code_target_filter_zero_update', 'rehearsal_presentations'), True),
            (('code_target_filter_zero_update', 'optimizer_steps_before'), 24),
            (('code_target_filter_zero_update', 'adapter_sha256'), '0' * 64),
            (('code_target_filter', 'excluded'), []),
            (('excluded_rows',), []),
            (('code_target_filter', 'retained_counts', 'NEW'), 1),
            (('code_target_filter_counts', 'NEW'), 1),
            (('code_target_filter_presentations',), {digest('fake'): 16}),
            (('optimizer_steps',), 1), (('optimizer_steps',), -1), (('optimizer_steps',), False),
            (('child_token_exposures',), 1), (('anchor_token_exposures',), 1),
            (('presentations',), {digest('fake'): 16}), (('no_update_reason',), 'unknown'),
            (('after_adapter_sha256',), '0' * 64), (('total_optimizer_steps',), 24),
            (('checkpoint', 'optimizer_steps'), 24), (('checkpoint', 'adapter_state_sha256'), '0' * 64),
            (('checkpoint',), None),
        ]
        for path, value in paths:
            modified = deepcopy(original)
            destination = modified
            for key in path[:-1]:
                destination = destination[key]
            destination[path[-1]] = value
            yield str(path) + '=' + str(value), modified
        modified = deepcopy(original)
        del modified['code_target_filter_zero_update']
        yield 'missing authorization', modified
        modified = deepcopy(original)
        del modified['code_target_filter_zero_update']['schema']
        yield 'missing authorization schema', modified

    def test_commit_rejects_forged_authorizations_without_mutating_frontier(self):
        self.step()
        original = self.receipt()
        before = self.stream.checkpoint()
        for name, forged in self.corruptions(original):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.stream.commit_sleep(forged, self.journal.record)
            self.assertEqual(self.stream.checkpoint(), before)
        self.stream.commit_sleep(original, self.journal.record)
        self.journal.audit()

    def test_journal_replay_independently_rejects_rehashed_forged_authorizations(self):
        self.step()
        original = self.receipt()
        self.stream.commit_sleep(original, self.journal.record)
        self.journal.close()
        path = sorted((self.root / 'stream/records').glob('*.json'))[-1]
        self.assertNotIn('.intent.', path.name)
        baseline = json.loads(path.read_text())
        self.assertEqual(baseline['kind'], 'SLEEP_COMPLETE')
        intent = path.with_name(path.stem + '.intent.json')
        record_bytes, intent_bytes = path.read_bytes(), intent.read_bytes()
        for name, forged in self.corruptions(original):
            record = deepcopy(baseline)
            saved = record['document']['resume_state']
            saved['state']['sleep_receipts'][-1] = forged
            saved['sha256'] = digest(saved['state'])
            record['document'] = dict(forged, resume_state=saved)
            record['sha256'] = digest({key: value for key, value in record.items() if key != 'sha256'})
            path.write_text(json.dumps(record))
            intent.write_text(json.dumps(StreamJournal._intent(record)))
            with self.subTest(name=name), self.assertRaises(ValueError):
                StreamJournal(self.root / 'stream')
        path.write_bytes(record_bytes)
        intent.write_bytes(intent_bytes)
        self.journal = StreamJournal(self.root / 'stream')
        self.journal.audit()

    def test_clean_raw_target_cannot_be_misrepresented_as_excluded(self):
        self.step(CLEAN_TARGET)
        fake_rows = deepcopy(self.stream.pending_rows())
        fake_rows[0]['target'] = BAD_TARGET
        forged = completed_receipt(self.child, self.anchors, fake_rows)
        with self.assertRaisesRegex(ValueError, 'r194_actual_raw_exclusions_required'):
            self.stream.commit_sleep(forged, self.journal.record)

    def test_retained_rehearsal_cannot_authorize_zero_update(self):
        self.step(CLEAN_TARGET)
        completed = dict(status='COMPLETE', optimizer_steps=1,
            new_row_sha256=[item['source_sha256'] for item in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        self.stream.commit_sleep(completed, self.journal.record)
        self.step()
        forged = self.receipt()
        forged['code_target_filter_zero_update']['rehearsal_presentations'] = 1
        with self.assertRaisesRegex(ValueError, 'r194_actual_raw_exclusions_required'):
            self.stream.commit_sleep(forged, self.journal.record)

    def test_other_no_update_reasons_still_require_legacy_presentation_contract(self):
        self.step(CLEAN_TARGET)
        forged = dict(status='COMPLETE', optimizer_steps=0, presentations={}, child_token_exposures=0,
            anchor_token_exposures=0, no_update_reason='no_eligible_child_rows',
            new_row_sha256=[item['source_sha256'] for item in self.stream.pending_rows()])
        with self.assertRaisesRegex(ValueError, 'sleep_actual_positive_optimizer_steps'):
            self.stream.commit_sleep(forged, self.journal.record)

    def test_legacy_commit_and_journal_replay_do_not_import_optional_helper(self):
        self.step(CLEAN_TARGET)
        receipt = dict(status='COMPLETE', optimizer_steps=1,
            new_row_sha256=[item['source_sha256'] for item in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        original_import = builtins.__import__

        def without_filter(name, *args, **kwargs):
            if name == 'organism_v6.orch_r194_code_target_filter':
                raise ImportError('helper unavailable in a legacy closure')
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=without_filter):
            self.stream.commit_sleep(receipt, self.journal.record)
            self.journal.audit()
            self.journal.close()
            self.journal = StreamJournal(self.root / 'stream')
            self.assertEqual(self.journal.latest_checkpoint()['document'], self.stream.checkpoint())


if __name__ == '__main__':
    unittest.main()
