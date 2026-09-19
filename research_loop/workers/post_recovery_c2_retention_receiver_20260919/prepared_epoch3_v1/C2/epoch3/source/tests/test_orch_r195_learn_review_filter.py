"""Synthetic CPU review tests; no pretrained model, provider or live run."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import time
import unittest
from unittest.mock import patch

import torch

from gpu import orch_r125_continual_native as native
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6.orch_r125_plain_context import VERSION
from organism_v6 import orch_r194_code_target_filter as filters
import test_orch_r194_code_target_filter as fixtures
from test_orch_r197_correction_ledger import receipt as published_receipt


def reviewed_rows(text, first=fixtures.CLEAN_TARGET, start=40):
    rows = [fixtures.row('first', first, segment=start), fixtures.row('review', text, segment=start + 1)]
    rows[-1]['learn_review'] = dict(schema=filters.REVIEW_POLICY,
        candidate_source_sha256=[row['source_sha256'] for row in rows],
        review_source_sha256=rows[-1]['source_sha256'])
    return rows


def review_child(*, fullwidth=False, rehearsal=0):
    child, anchors = fixtures.child_fixture(enabled=fullwidth, rehearsal=rehearsal)
    child.plan['learn_review_filter'] = filters.REVIEW_POLICY
    return child, anchors


def attach_receipt(rows, *, import_error=False, empty=False):
    stderr = "Traceback (most recent call last):\nModuleNotFoundError: No module named 'synthetic_missing'\n" if import_error else ''
    outcome = published_receipt(rows[0]['target'], returncode=1 if import_error else 0, stderr=stderr)
    if empty:
        outcome['result']['stdout'] = ''
        outcome['result_sha256'] = hashlib.sha256(json.dumps(
            outcome['result'], sort_keys=True, indent=2).encode()).hexdigest()
    rows[-1]['learn_review_evidence'] = [dict(act_source_sha256=rows[0]['source_sha256'],
        response_origin=dict(record_sha256=outcome['origin']['record_sha256']), outcome=outcome)]
    return rows


class ReviewParserTests(unittest.TestCase):
    def apply(self, rows, old_rows=()):
        return filters.filter_learn_review_targets(rows, old_rows, filters.REVIEW_POLICY)

    def test_exact_segments_em_dash_ascii_dash_and_self_are_source_bound(self):
        for command in ('row 40', 'row 41', 'self', 'row self'):
            for separator in ('—', '-'):
                with self.subTest(command=command, separator=separator):
                    rows = reviewed_rows(f'Do not train: {command} {separator} I want to reconsider this.')
                    before = deepcopy(rows)
                    retained, old, proof = self.apply(rows)
                    excluded_index = 0 if command == 'row 40' else 1
                    self.assertEqual(rows, before)
                    self.assertEqual(old, ())
                    self.assertIs(retained[0], rows[1 - excluded_index])
                    self.assertEqual(proof['excluded'][0]['source_sha256'], rows[excluded_index]['source_sha256'])
                    self.assertEqual(proof['excluded'][0]['reason'], 'child_requested_do_not_train')
                    self.assertEqual(proof['exclusion_basis'], 'CHILD_REQUEST_NOT_VERIFIED_ERROR')
                    self.assertFalse(proof['raw_modified'])
                    self.assertFalse(proof['targets_normalized'])

    def test_multiple_directives_deduplicate_targets_but_preserve_every_reason(self):
        rows = reviewed_rows('Do not train: row 40 — first reason\n'
            'Do not train: row 40 - second reason\nDo not train: self — own review')
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, [])
        self.assertEqual(len(proof['excluded']), 2)
        self.assertEqual(len(proof['excluded'][0]['directives']), 2)
        self.assertEqual(proof['excluded_counts'], dict(NEW=2, REHEARSAL=0))

    def test_unknown_historical_future_and_malformed_ids_are_rejected_not_expanded(self):
        commands = ['Do not train: row 39 — historical', 'Do not train: row 42 — future',
            'Do not train: row -1 — negative', 'Do not train: row 040 — leading zero',
            'Do not train: row all — blanket', 'Do not train: row 40,41 — multiple',
            'Do not train: row 40 — ', 'Do not train: row ４０ — fullwidth identifier',
            'Do not train: row ' + '9' * 5000 + ' — oversized unknown']
        for command in commands:
            with self.subTest(command=command[:80]):
                rows = reviewed_rows(command)
                old = [fixtures.row('old', segment=39)]
                retained, retained_old, proof = self.apply(rows, old)
                self.assertEqual(retained, rows)
                self.assertIs(retained_old, old)
                self.assertEqual(proof['excluded'], [])
                self.assertEqual(len(proof['reviews'][0]['rejected']), 1)

    def test_fenced_quoted_and_prose_examples_are_not_directives(self):
        texts = ['```text\nDo not train: row 40 — example\n```',
            '~~~text\nDo not train: row 40 — unclosed example',
            '> Do not train: row 40 — quotation', '`Do not train: row 40 — quoted`',
            'An example: Do not train: row 40 — not my request']
        for text in texts:
            with self.subTest(text=text):
                rows = reviewed_rows(text)
                retained, _, proof = self.apply(rows)
                self.assertEqual(retained, rows)
                self.assertEqual(proof['reviews'][0]['accepted'], [])
                self.assertTrue(proof['reviews'][0]['rejected'])

    def test_directive_after_closed_code_is_parsed_and_unannotated_rows_are_not(self):
        text = '```text\nDo not train: self — quoted\n```\nDo not train: row 40 — actual request'
        rows = reviewed_rows(text)
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, rows[1:])
        self.assertEqual(len(proof['reviews'][0]['accepted']), 1)
        del rows[-1]['learn_review']
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, rows)
        self.assertEqual(proof['reviews'], [])

    def test_no_semantic_invented_result_classifier(self):
        rows = reviewed_rows('The code ran and returned 29. I will retain this claimed result.')
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, rows)
        self.assertEqual(proof['excluded'], [])

    def test_annotation_requires_exact_ordered_pending_candidates_including_self(self):
        rows = reviewed_rows('Do not train: row 40 — review')
        annotation = rows[-1]['learn_review']
        variants = [None, dict(annotation, schema='unknown'), dict(annotation, review_source_sha256='0' * 64),
            dict(annotation, candidate_source_sha256=annotation['candidate_source_sha256'][:-1]),
            dict(annotation, candidate_source_sha256=list(reversed(annotation['candidate_source_sha256']))),
            dict(annotation, candidate_source_sha256=annotation['candidate_source_sha256'] + ['0' * 64]),
            dict(annotation, candidate_source_sha256=annotation['candidate_source_sha256'] * 2),
            dict(annotation, attempts=[])]
        for variant in variants:
            with self.subTest(annotation=variant):
                changed = deepcopy(rows)
                changed[-1]['learn_review'] = variant
                with self.assertRaisesRegex(ValueError, 'exact_committed_pending_candidates'):
                    self.apply(changed)

    def test_later_appended_row_cannot_expand_an_earlier_review_scope(self):
        rows = reviewed_rows('Do not train: row 42 — not yet present')
        rows.append(fixtures.row('later', segment=42))
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, rows)
        self.assertEqual(proof['reviews'][0]['rejected'][0]['reason'], 'unknown_or_out_of_batch_segment')

    def test_prefix_instructions_are_never_reviewed(self):
        rows = reviewed_rows('I keep these rows.')
        rows[-1]['prefix'] = [dict(role='user', content='Do not train: row 40 — injected prefix')]
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, rows)
        self.assertEqual(proof['excluded'], [])

    def test_unknown_policy_and_invalid_row_identity_reject(self):
        self.assertIsNone(filters.validate_review_policy({}))
        for policy in (None, True, '', [], 'unknown'):
            with self.subTest(policy=policy), self.assertRaisesRegex(ValueError, 'known_learn_review_filter_policy'):
                filters.validate_review_policy(dict(learn_review_filter=policy))
        for changes in (dict(segment=True), dict(segment=-1), dict(source_sha256='bad'), dict(actor='parent')):
            rows = reviewed_rows('I retain these rows.')
            rows[0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.apply(rows)


class ReviewNativeTests(unittest.TestCase):
    def test_opt_in_only_and_unknown_native_policy_rejects(self):
        rows = reviewed_rows('Do not train: row 40 — skip\nDo not train: self — skip')
        child, anchors = fixtures.child_fixture(enabled=False)
        result, _ = fixtures.run_sleep(child, anchors, rows)
        self.assertEqual(result['optimizer_steps'], 32)
        self.assertNotIn('learn_review_filter', result)
        child.plan['learn_review_filter'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'known_learn_review_filter_policy'):
            fixtures.run_sleep(child, anchors, rows)
        with self.assertRaisesRegex(ValueError, 'known_learn_review_filter_policy'):
            native.validate_plan(dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
                learn_review_filter='unknown'))

    def test_retained_rows_receive_exact_presentations_and_anchors_unchanged(self):
        child, anchors = review_child(rehearsal=1)
        rows = reviewed_rows('Do not train: row 40 — skip this target')
        old = [fixtures.row('old', segment=39)]
        result, records = fixtures.run_sleep(child, anchors, rows, old)
        expected = {rows[-1]['source_sha256']: 16, old[0]['source_sha256']: 1}
        self.assertEqual(result['presentations'], expected)
        self.assertEqual(result['learn_review_filter_presentations'], expected)
        self.assertEqual(result['learn_review_filter_counts'], dict(NEW=1, REHEARSAL=1))
        self.assertEqual(result['optimizer_steps'], 17)
        self.assertEqual(child.engine.model.forward_calls, 85)
        self.assertEqual(records[0][1]['learn_review_filter'], filters.REVIEW_POLICY)
        self.assertNotIn('learn_review_zero_update', result)

    def test_all_vetoed_rows_use_generic_reason_without_any_learning(self):
        child, anchors = review_child()
        rows = reviewed_rows('Do not train: row 40 — skip\nDo not train: self - skip')
        before = deepcopy((rows, child.optimizer.state_dict()))
        rng, python_rng = torch.get_rng_state().clone(), random.getstate()
        result, _ = fixtures.run_sleep(child, anchors, rows)
        self.assertEqual(result['no_update_reason'], 'no_eligible_child_rows')
        self.assertEqual(result['no_update_subreason'], filters.REVIEW_FILTER_SUBREASON)
        self.assertEqual(result['optimizer_steps'], 0)
        self.assertEqual(result['child_token_exposures'], 0)
        self.assertEqual(result['anchor_token_exposures'], 0)
        self.assertEqual(child.engine.model.forward_calls, 0)
        child.optimizer.step.assert_not_called()
        self.assertEqual((rows, child.optimizer.state_dict()), before)
        self.assertTrue(torch.equal(torch.get_rng_state(), rng))
        self.assertEqual(random.getstate(), python_rng)

    def test_combined_fullwidth_and_review_exclusion_uses_one_bound_authorization(self):
        child, anchors = review_child(fullwidth=True)
        text = fixtures.BAD_TARGET + '\nDo not train: row 40 — skip this row'
        rows = reviewed_rows(text)
        result = fixtures.completed_receipt(child, anchors, rows)
        self.assertEqual(result['optimizer_steps'], 0)
        self.assertIn('learn_review_zero_update', result)
        self.assertNotIn('code_target_filter_zero_update', result)
        self.assertEqual([item['policy'] for item in result['excluded_rows']], [filters.REVIEW_POLICY, filters.POLICY])
        self.assertTrue(filters.validate_filter_zero_update_receipt(result, rows, []))

    def test_selected_rehearsal_prevents_anchor_only_zero_update_authorization(self):
        child, anchors = review_child(rehearsal=1)
        rows = reviewed_rows('Do not train: row 40 — skip\nDo not train: self — skip')
        old = [fixtures.row('old', segment=39)]
        result, _ = fixtures.run_sleep(child, anchors, rows, old)
        self.assertEqual(result['optimizer_steps'], 1)
        self.assertEqual(result['presentations'], {old[0]['source_sha256']: 1})
        self.assertNotIn('learn_review_zero_update', result)

    def test_no_review_leaves_training_identical_to_unfiltered_default(self):
        rows = reviewed_rows('These rows should remain.')
        child, anchors = review_child()
        legacy, legacy_anchors = fixtures.child_fixture(enabled=False)
        result, _ = fixtures.run_sleep(child, anchors, rows)
        legacy_result, _ = fixtures.run_sleep(legacy, legacy_anchors, rows)
        self.assertEqual({key: value for key, value in result.items() if not key.startswith('learn_review')}, legacy_result)


class ReceiptIntegrationTests(unittest.TestCase):
    def apply(self, rows, old_rows=()):
        return filters.filter_learn_review_targets(rows, old_rows, filters.REVIEW_POLICY)

    def test_matched_import_error_excludes_only_bound_act_without_mutating_raw(self):
        rows = attach_receipt(reviewed_rows('No result obtained.', first='```python\nimport synthetic_missing\n```'),
            import_error=True)
        before = deepcopy(rows)
        retained, _, proof = self.apply(rows)
        self.assertEqual(rows, before)
        self.assertEqual(retained, rows[1:])
        self.assertEqual(proof['excluded_counts'], dict(NEW=1, REHEARSAL=0))
        self.assertEqual(proof['excluded'][0]['reason'], 'receipt_bound_provisional_quarantine')
        self.assertEqual(proof['receipt_filter']['excluded'][0]['reason'], 'actual_receipt_import_error')
        self.assertFalse(proof['receipt_filter']['excluded'][0]['semantic_falsehood_claimed'])

    def test_empty_output_claim_quarantine_is_independent_of_child_review_annotation(self):
        rows = attach_receipt(reviewed_rows('The result was 29.', first='```python\nvalue = 29\n```'), empty=True)
        del rows[-1]['learn_review']
        retained, _, proof = self.apply(rows)
        self.assertEqual(retained, rows[:1])
        self.assertEqual(proof['reviews'], [])
        self.assertEqual(proof['receipt_filter']['excluded'][0]['reason'], 'numeric_result_claim_after_empty_output')
        self.assertFalse(proof['receipt_filter']['excluded'][0]['semantic_falsehood_claimed'])

    def test_unknown_unpublished_and_out_of_batch_receipts_never_expand_targets(self):
        rows = attach_receipt(reviewed_rows('The result was 29.', first='```python\nvalue = 29\n```'), empty=True)
        for variant in ('unpublished', 'different_act', 'different_response'):
            changed = deepcopy(rows)
            evidence = changed[-1]['learn_review_evidence'][0]
            if variant == 'unpublished':
                evidence['outcome']['status'] = 'PUBLICATION_UNKNOWN'
            elif variant == 'different_act':
                evidence['act_source_sha256'] = digest('historical_out_of_batch')
            else:
                evidence['response_origin']['record_sha256'] = '0' * 64
            old = [fixtures.row('historical_out_of_batch', segment=39)]
            with self.subTest(variant=variant):
                retained, retained_old, proof = self.apply(changed, old)
                self.assertEqual(retained, changed)
                self.assertIs(retained_old, old)
                self.assertEqual(proof['receipt_filter']['excluded'], [])
                self.assertTrue(proof['receipt_filter']['checks'])

    def test_receipt_and_child_vetoes_union_by_source_without_double_counting(self):
        rows = attach_receipt(reviewed_rows('Do not train: row 40 — skip\nDo not train: self — skip'), import_error=True)
        rows[-1]['learn_review_evidence'] *= 2
        child, anchors = review_child()
        before = deepcopy(rows)
        result = fixtures.completed_receipt(child, anchors, rows)
        self.assertEqual(rows, before)
        proof = result['learn_review_filter']
        self.assertEqual(proof['excluded_counts'], dict(NEW=2, REHEARSAL=0))
        self.assertEqual(len(proof['excluded']), 2)
        self.assertEqual(len(proof['excluded'][0]['receipt_exclusions']), 2)
        self.assertEqual(len(proof['excluded'][0]['directives']), 1)
        self.assertEqual(result['optimizer_steps'], 0)
        self.assertTrue(filters.validate_filter_zero_update_receipt(result, rows, []))
        child.optimizer.step.assert_not_called()
        rows[-1]['learn_review_evidence'][0]['outcome']['result']['stderr'] += 'changed receipt'
        with self.assertRaises(ValueError):
            filters.validate_filter_zero_update_receipt(result, rows, [])

    def test_receipt_plus_fullwidth_all_excluded_checkpoint_authorization(self):
        rows = attach_receipt(reviewed_rows(fixtures.BAD_TARGET), import_error=True)
        child, anchors = review_child(fullwidth=True)
        result = fixtures.completed_receipt(child, anchors, rows)
        self.assertEqual(result['optimizer_steps'], 0)
        self.assertEqual(result['no_update_reason'], 'no_eligible_child_rows')
        self.assertIn('receipt_filter', result['learn_review_filter'])
        self.assertEqual(result['code_target_filter']['excluded_counts'], dict(NEW=1, REHEARSAL=0))
        self.assertTrue(filters.validate_filter_zero_update_receipt(result, rows, []))
        self.assertEqual(child.engine.model.forward_calls, 0)

    def test_receipt_helper_receives_original_batch_before_child_vetoes(self):
        from organism_v6.orch_r195_receipt_target_filter import receipt_exclusions
        rows = attach_receipt(reviewed_rows('Do not train: row 40 — skip\nDo not train: self — skip'), import_error=True)
        with patch('organism_v6.orch_r195_receipt_target_filter.receipt_exclusions', wraps=receipt_exclusions) as receiver:
            self.apply(rows)
        self.assertEqual(receiver.call_args.args[0], rows)
        self.assertIsNot(receiver.call_args.args[0], rows)

    def test_consumer_rejects_helper_exclusions_with_unbound_or_rewritten_targets(self):
        rows = attach_receipt(reviewed_rows('No result obtained.'), import_error=True)
        proof = self.apply(rows)[2]['receipt_filter']
        for change in (dict(source_sha256=digest('outside')), dict(raw_target_sha256='0' * 64),
                dict(semantic_falsehood_claimed=True), dict(cohort='REHEARSAL')):
            changed = deepcopy(proof)
            changed['excluded'][0].update(change)
            with self.subTest(change=change), patch(
                    'organism_v6.orch_r195_receipt_target_filter.receipt_exclusions', return_value=changed), \
                    self.assertRaises(ValueError):
                self.apply(rows)


class ReviewJournalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(lambda: self.journal.close())
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Investigate.'),
            context_limit=8192, segment_tokens=512, segments_per_sleep=2,
            deadline_unix=time.time() + 600, model_state_sha256='f' * 64)
        self.child, self.anchors = review_child()

    def step(self, text, *, review=False, evidence=None):
        def recorded(kind, document):
            if kind == 'COMMITTED' and (review or evidence is not None):
                row = self.stream.rows[-1]
                if review:
                    row['learn_review'] = dict(schema=filters.REVIEW_POLICY,
                        candidate_source_sha256=[candidate['source_sha256'] for candidate in self.stream.pending_rows()],
                        review_source_sha256=row['source_sha256'])
                if evidence is not None:
                    row['learn_review_evidence'] = deepcopy(evidence)
                document = dict(document, state=self.stream.checkpoint())
            return self.journal.record(kind, document)

        self.stream.step(lambda *args, **kwargs: dict(raw=text,
            token_ids=[ord(character) + 100 for character in text] + [2], terminal=True, truncated=False),
            lambda messages: sum(len(message['content'].split()) + 4 for message in messages), recorded)

    def all_vetoed(self):
        self.step(fixtures.CLEAN_TARGET)
        self.step('Do not train: row 0 — review\nDo not train: self - review', review=True)
        return fixtures.completed_receipt(self.child, self.anchors, self.stream.pending_rows())

    def test_initial_commit_annotation_audit_only_record_checkpoint_reload_and_continue(self):
        self.all_vetoed()
        saved = self.journal.latest_checkpoint()
        proof = filters.filter_learn_review_targets(self.stream.pending_rows(), [], filters.REVIEW_POLICY)[2]
        self.journal.record('R195_LEARN_REVIEW', dict(proof=proof, state=self.stream.checkpoint()))
        self.assertEqual(self.journal.latest_checkpoint(), saved)
        before = deepcopy((self.stream.rows, self.stream.history.checkpoint()))
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            checkpoint = native.finish_sleep(self.child, self.stream, self.journal, self.anchors, self.root, 1)
        self.assertEqual(self.stream.sleep_frontier, 2)
        self.assertEqual((self.stream.rows, self.stream.history.checkpoint()), before)
        self.assertEqual(checkpoint['optimizer_steps'], 23)
        native.NativeChild.verify_checkpoint(checkpoint)
        self.journal.audit()
        self.journal.close()
        self.journal = StreamJournal(self.root / 'stream')
        self.stream = ContinualStream.restore(**self.journal.latest_checkpoint())
        self.assertEqual(self.stream.rows, before[0])
        self.step(fixtures.CLEAN_TARGET)
        self.step('I retain the pending rows.', review=True)
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            next_checkpoint = native.finish_sleep(self.child, self.stream, self.journal, self.anchors, self.root, 2)
        self.assertEqual(next_checkpoint['optimizer_steps'], 55)
        self.journal.audit()

    def test_post_commit_row_annotation_mutation_remains_forbidden(self):
        self.step('Own target.')
        row = self.stream.rows[-1]
        row['learn_review'] = dict(schema=filters.REVIEW_POLICY,
            candidate_source_sha256=[row['source_sha256']], review_source_sha256=row['source_sha256'])
        with self.assertRaisesRegex(ValueError, 'unexpected_stream_state_transition'):
            self.step('Next target.')

    def test_actual_receipt_annotation_is_persisted_and_zero_update_revalidated_on_reload(self):
        raw = '```python\nimport synthetic_missing\n```'
        self.step(raw)
        examples = attach_receipt([deepcopy(self.stream.rows[0]), fixtures.row('review', segment=1)], import_error=True)
        self.step('Do not train: self — skip my review', review=True,
            evidence=examples[-1]['learn_review_evidence'])
        before = deepcopy(self.stream.rows)
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            checkpoint = native.finish_sleep(self.child, self.stream, self.journal, self.anchors, self.root, 1)
        self.assertEqual(checkpoint['optimizer_steps'], 23)
        self.assertEqual(self.stream.sleep_frontier, 2)
        self.assertEqual(self.stream.rows, before)
        self.journal.audit()
        self.journal.close()
        self.journal = StreamJournal(self.root / 'stream')
        self.stream = ContinualStream.restore(**self.journal.latest_checkpoint())
        self.assertEqual(self.stream.rows, before)
        self.assertEqual(self.stream.sleep_receipts[-1]['optimizer_steps'], 0)

    def corruptions(self, original):
        paths = [(('learn_review_zero_update', 'schema'), 'unknown'),
            (('learn_review_zero_update', 'eligibility_sha256'), '0' * 64),
            (('learn_review_zero_update', 'optimizer_steps_before'), 24),
            (('learn_review_filter', 'excluded'), []), (('excluded_rows',), []),
            (('learn_review_filter_counts', 'NEW'), 1),
            (('learn_review_filter_presentations',), {'fake': 16}),
            (('optimizer_steps',), 1), (('anchor_token_exposures',), 1),
            (('no_update_reason',), filters.REVIEW_FILTER_SUBREASON),
            (('no_update_subreason',), 'unknown'), (('after_adapter_sha256',), '0' * 64),
            (('checkpoint', 'optimizer_steps'), 24)]
        for path, value in paths:
            candidate = deepcopy(original)
            destination = candidate
            for key in path[:-1]:
                destination = destination[key]
            destination[path[-1]] = value
            yield str(path), candidate
        candidate = deepcopy(original)
        del candidate['learn_review_zero_update']
        yield 'missing authorization', candidate
        candidate = deepcopy(candidate)
        del candidate['no_update_subreason']
        yield 'missing authorization and subreason', candidate
        candidate = deepcopy(original)
        candidate['code_target_filter_zero_update'] = {}
        yield 'conflicting authorizations', candidate

    def test_generic_reason_does_not_bypass_authorization_even_with_plain_presentation(self):
        self.stream.set_presentation(dict(version=VERSION, system_prompt='System.', birth_prompt='Investigate.'), 16384)
        original = self.all_vetoed()
        before = self.stream.checkpoint()
        for name, forged in self.corruptions(original):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.stream.commit_sleep(forged, self.journal.record)
            self.assertEqual(self.stream.checkpoint(), before)
        self.stream.commit_sleep(original, self.journal.record)
        self.journal.audit()

    def test_replay_independently_checks_bound_review_and_zero_update_authorization(self):
        original = self.all_vetoed()
        self.stream.commit_sleep(original, self.journal.record)
        self.journal.close()
        path = sorted((self.root / 'stream/records').glob('*.json'))[-1]
        baseline = json.loads(path.read_text())
        self.assertEqual(baseline['kind'], 'SLEEP_COMPLETE')
        intent = path.with_name(path.stem + '.intent.json')
        before_record, before_intent = path.read_bytes(), intent.read_bytes()
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
        path.write_bytes(before_record)
        intent.write_bytes(before_intent)
        self.journal = StreamJournal(self.root / 'stream')
        self.journal.audit()


if __name__ == '__main__':
    unittest.main()
