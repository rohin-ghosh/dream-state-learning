"""Synthetic CPU-only facts; no live life, provider, GPU, or code execution."""

from copy import deepcopy
import hashlib
import json
import unittest

from gpu import orch_r153_code_blocks as blocks
from gpu.orch_r197_correction_ledger import FAULTS, STAGES, UNKNOWN, update_ledger


RAW = '```python\nprint(1)\n```'
THINK = 'The earlier block used glyphs. I choose plain ASCII for this attempt.'


def evidence(fault_id='raw_code_glyphs'):
    return dict(fault_id=fault_id,
        noticed=dict(value=True, source='THINK', index=0, quote='The earlier block used glyphs.'),
        chosen=dict(value=True, source='THINK', index=0, quote='I choose plain ASCII for this attempt.'))


def receipt(raw=RAW, *, returncode=0, stderr='', policy=blocks.POLICY):
    report = blocks.extract(raw, policy=policy)
    origin = dict(kind='TRAIN_CHILD_RESPONSE', child_generated=True, journal_id='fixture-journal',
        record_sha256='a' * 64, request_record_sha256='b' * 64, commit_record_sha256='c' * 64,
        code_transformation=blocks.metadata(report))
    result = dict(schema='R125_CPU_EXPERIMENT_RESULT_V1', request_id='fixture-request',
        origin=origin, source_sha256=report.get('source_sha256'), launch_attempted=True,
        status='COMPLETE' if returncode == 0 else 'PROCESS_FAILED', returncode=returncode,
        stderr=stderr, stdout='fixture output')
    result_bytes = json.dumps(result, sort_keys=True, indent=2).encode('utf-8')
    return dict(schema='R153_CPU_DELIVERY_V1', request_id=result['request_id'],
        journal_id=origin['journal_id'], origin=deepcopy(origin), status='PUBLISHED', executed=True,
        source_sha256=result['source_sha256'], result_status=result['status'],
        result_sha256=hashlib.sha256(result_bytes).hexdigest(), result=result)


def advance(state=None, **changes):
    arguments = dict(life_id='fixture-life', cycle=1, raw_think=THINK, raw_act=RAW,
                     completed_sleeps=0, parent_interventions=[], child_evidence=[evidence()])
    arguments.update(changes)
    return update_ledger(state, **arguments)


def opportunity(state, cycle=1, fault_id='raw_code_glyphs'):
    return next(row for row in state['opportunities'] if row['cycle'] == cycle and row['fault_id'] == fault_id)


class CorrectionLedgerTests(unittest.TestCase):
    def test_four_stages_and_no_held_without_followup(self):
        state = advance()
        row = opportunity(state)
        self.assertEqual([row[stage] for stage in STAGES], ['YES', 'YES', 'YES', UNKNOWN])
        self.assertFalse(state['causality_claimed'])
        self.assertEqual(state['retained_in_weights'], UNKNOWN)

    def test_keywords_are_not_explicit_child_evidence(self):
        state = advance(raw_act='```python\nｘ = 1\n```', child_evidence=None)
        state = advance(state, cycle=2,
                        raw_think='noticed chosen enacted correct equation reasoning import failed',
                        child_evidence=None)
        row = opportunity(state, cycle=2)
        self.assertEqual([row[stage] for stage in STAGES], [UNKNOWN, UNKNOWN, 'YES', UNKNOWN])
        self.assertEqual(row['fault_present'], 'NO')
        self.assertEqual(row['child_evidence_adjudication'], 'UNADJUDICATED')

    def test_unextractable_conflicting_or_misattributed_evidence_is_unknown(self):
        prior = advance(raw_act='```python\nｘ = 1\n```', child_evidence=None)
        variants = [dict(quote='not in raw'), dict(quote=''), dict(source='PARENT'),
                    dict(index=4), dict(index=-1), dict(index=True), dict(value='true')]
        for variant in variants:
            with self.subTest(variant=variant):
                entry = evidence()
                entry['noticed'].update(variant)
                state = advance(prior, cycle=2, child_evidence=[entry])
                self.assertEqual(opportunity(state, cycle=2)['NOTICED'], UNKNOWN)
        state = advance(prior, cycle=2, child_evidence=[evidence(), evidence()])
        self.assertEqual(opportunity(state, cycle=2)['NOTICED'], UNKNOWN)
        self.assertEqual(opportunity(state, cycle=2)['CHOSEN'], UNKNOWN)

    def test_multiple_thinks_and_act_quotes_are_bound_verbatim(self):
        entry = evidence()
        entry['noticed']['index'] = 1
        entry['chosen'] = dict(value=True, source='ACT', quote='I choose plain ASCII.')
        raw = 'I choose plain ASCII.\n' + RAW
        state = advance(raw_think=['earlier', THINK], raw_act=raw, child_evidence=[entry])
        self.assertEqual(opportunity(state)['ENACTED'], 'YES')
        self.assertEqual(len(state['cycles'][0]['raw_think_sha256']), 2)

    def test_explicit_negative_is_not_missing_evidence(self):
        entry = evidence()
        entry['chosen'] = dict(value=False, source='THINK', quote='I have not chosen a change.')
        state = advance(raw_think=THINK + ' I have not chosen a change.', child_evidence=[entry])
        self.assertEqual(opportunity(state)['CHOSEN'], 'NO')
        self.assertEqual(opportunity(state)['ENACTED'], 'YES')

    def test_nfkc_execution_success_does_not_repair_raw_glyph_measure(self):
        raw = '```python\nｘ = 1\nprint(ｘ)\n```'
        state = advance(raw_act=raw, execution=receipt(raw, policy=blocks.NFKC_POLICY))
        self.assertEqual(opportunity(state)['fault_present'], 'YES')
        self.assertEqual(opportunity(state)['ENACTED'], 'NO')
        self.assertEqual(state['cycles'][0]['faults']['execution_failure'], 'NO')
        record = state['cycles'][0]
        self.assertEqual(record['raw_check']['raw_source_sha256'], blocks.sha('ｘ = 1\nprint(ｘ)\n'))
        self.assertEqual(record['raw_check']['fullwidth_codepoints'], ['U+FF58'])
        self.assertNotEqual(record['execution_check']['execution_source_sha256'],
                            record['raw_check']['raw_source_sha256'])

    def test_only_raw_first_block_is_inspected(self):
        raw = '```python\nprint("Ａ")\n```\n' + RAW
        self.assertEqual(opportunity(advance(raw_act=raw))['fault_present'], 'YES')
        self.assertEqual(opportunity(advance(raw_act=RAW + '\n' + raw))['fault_present'], 'NO')
        self.assertEqual(opportunity(advance(raw_act='Ａ outside code\n' + RAW))['fault_present'], 'NO')

    def test_missing_empty_unsupported_or_unclosed_first_block_is_unknown(self):
        for raw in (None, '', 'no code', '```python\n```\n' + RAW,
                    '```json\n{}\n```\n' + RAW, '```python\nprint(1)'):
            with self.subTest(raw=raw):
                state = advance(raw_act=raw)
                self.assertEqual(opportunity(state)['fault_present'], UNKNOWN)
                self.assertEqual(opportunity(state)['ENACTED'], UNKNOWN)

    def test_non_fullwidth_unicode_is_not_a_raw_glyph_fault(self):
        for source in ('λ = 1\nprint(λ)\n', '# λ🙂\nprint(1)\n', 'print("λ café 你好 🙂")\n',
                       '𝑥 = 1\nprint(𝑥)\n', 'print(“hello”)\n'):
            with self.subTest(source=source):
                state = advance(raw_act='~~~python\n' + source + '~~~')
                self.assertEqual(opportunity(state)['fault_present'], 'NO')
                self.assertEqual(state['cycles'][0]['raw_check']['fullwidth_codepoints'], [])
                self.assertEqual(state['cycles'][0]['raw_check']['raw_source_sha256'], blocks.sha(source))
                self.assertEqual(state['counts']['by_fault']['raw_code_glyphs']['failures'], 0)
        self.assertEqual(opportunity(advance(raw_act='```python\nthis is not valid !!!\n```'))['fault_present'], 'NO')

    def test_exact_fullwidth_range_and_explicit_ideographic_space(self):
        for codepoint in [*range(0xFF01, 0xFF5F), 0x3000]:
            with self.subTest(codepoint=codepoint):
                source = '# guard ' + chr(codepoint) + '\nprint(1)\n'
                state = advance(raw_act='```python\n' + source + '```')
                self.assertEqual(opportunity(state)['fault_present'], 'YES')
                self.assertEqual(opportunity(state)['ENACTED'], 'NO')
                check = state['cycles'][0]['raw_check']
                self.assertEqual(check['fullwidth_codepoints'], [f'U+{codepoint:04X}'])
                self.assertEqual(check['scope'], 'FULLWIDTH_ASCII_U+FF01..U+FF5E_PLUS_U+3000'
                                                 '_INCLUDING_LITERALS_AND_COMMENTS')
        for codepoint in (0xFF00, 0xFF5F, 0x2FFF, 0x3001):
            with self.subTest(outside_range=codepoint):
                state = advance(raw_act='```python\n# ' + chr(codepoint) + '\nprint(1)\n```')
                self.assertEqual(opportunity(state)['fault_present'], 'NO')

    def test_nfkc_changes_outside_fullwidth_guard_do_not_create_a_fault(self):
        raw = '```python\n𝑥 = 1\nprint(𝑥)\n```'
        state = advance(raw_act=raw, execution=receipt(raw, policy=blocks.NFKC_POLICY))
        record = state['cycles'][0]
        self.assertEqual(opportunity(state)['fault_present'], 'NO')
        self.assertEqual(record['raw_check']['fullwidth_codepoints'], [])
        self.assertNotEqual(record['execution_check']['execution_source_sha256'],
                            record['raw_check']['raw_source_sha256'])

    def test_non_fullwidth_unicode_followup_does_not_block_held(self):
        state = advance()
        state = advance(state, cycle=2, completed_sleeps=1,
                        raw_act='```python\nλ = "café"\nprint(λ)  # 🙂\n```')
        self.assertEqual(opportunity(state)['HELD'], 'YES')
        self.assertEqual(state['counts']['by_fault']['raw_code_glyphs']['failures'], 0)

    def test_real_result_failure_and_import_trace_are_counted(self):
        stderr = 'Traceback (most recent call last):\n  File "payload.py", line 1\nModuleNotFoundError: No module named missing\n'
        outcome = receipt(returncode=1, stderr=stderr)
        state = advance(execution=outcome, child_evidence=None)
        self.assertEqual(state['opportunities'], [])
        state = advance(state, cycle=2, execution=outcome, child_evidence=None)
        for fault in ('execution_failure', 'import_error'):
            row = opportunity(state, cycle=2, fault_id=fault)
            self.assertEqual(row['fault_present'], 'YES')
            self.assertEqual(row['ENACTED'], 'NO')
            self.assertEqual(state['counts']['by_fault'][fault]['failures'], 1)
            self.assertEqual(state['counts']['observed_by_fault'][fault]['failures'], 2)
        self.assertEqual(state['cycles'][0]['input']['execution'], outcome)

    def test_prose_printed_keywords_or_unbound_errors_are_not_import_errors(self):
        outcomes = [None, dict(status='PUBLISHED', executed=True),
                    dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None),
                    receipt(returncode=1, stderr='ModuleNotFoundError: printed text\n'),
                    receipt(returncode=1, stderr='Traceback (most recent call last):\nValueError: ModuleNotFoundError\n')]
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                state = advance(raw_think='ModuleNotFoundError: I executed this', execution=outcome)
                self.assertEqual(state['cycles'][0]['faults']['import_error'], UNKNOWN)

    def test_receipt_hash_source_origin_and_response_joins_are_required(self):
        mutations = [dict(result_sha256='bad'), dict(source_sha256='d' * 64),
                     dict(request_id='different'), dict(origin={}), dict(journal_id='different'),
                     dict(executed=False), dict(result_status='MADE_UP')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                outcome = receipt()
                outcome.update(mutation)
                state = advance(execution=outcome)
                self.assertEqual(state['cycles'][0]['faults']['execution_failure'], UNKNOWN)
        state = advance(execution=receipt(), source=dict(response=dict(record_sha256='d' * 64)))
        self.assertEqual(state['cycles'][0]['execution_check']['provenance'], UNKNOWN)
        state = advance(raw_act=RAW + '\nchanged', execution=receipt())
        self.assertEqual(state['cycles'][0]['execution_check']['provenance'], UNKNOWN)

    def test_unknown_execution_and_noncomplete_zero_exit_are_not_success(self):
        outcome = receipt()
        outcome['result']['status'] = outcome['result_status'] = 'TEARDOWN_UNVERIFIED'
        state = advance(execution=outcome)
        self.assertEqual(state['cycles'][0]['faults']['execution_failure'], UNKNOWN)
        state = advance(execution=dict(status='NO_CPU_ATTEMPT', executed=False))
        self.assertEqual(state['cycles'][0]['faults']['execution_failure'], UNKNOWN)

    def test_equation_and_reasoning_checks_remain_unknown_even_on_success(self):
        for fault in ('equation_correctness', 'reasoning'):
            with self.subTest(fault=fault):
                state = advance(execution=receipt(), child_evidence=[evidence(fault)])
                row = opportunity(state, fault_id=fault)
                self.assertEqual(row['NOTICED'], 'YES')
                self.assertEqual(row['fault_present'], UNKNOWN)
                self.assertEqual(row['ENACTED'], UNKNOWN)

    def test_held_needs_next_cycle_and_a_completed_sleep(self):
        state = advance()
        state = advance(state, cycle=2)
        self.assertEqual(opportunity(state)['HELD'], UNKNOWN)
        state = advance(state, cycle=3, completed_sleeps=1)
        row = opportunity(state)
        self.assertEqual(row['HELD'], 'YES')
        self.assertEqual(row['hold_window']['following_action']['cycle'], 2)
        self.assertEqual(row['hold_window']['after_sleep']['cycle'], 3)

    def test_one_next_action_after_sleep_can_witness_both_conditions(self):
        state = advance(cycle=41, completed_sleeps=40)
        state = advance(state, cycle=42, completed_sleeps=41)
        self.assertEqual(opportunity(state, cycle=41)['HELD'], 'YES')

    def test_same_fault_reminder_blocks_held_but_other_fault_does_not(self):
        for interventions, expected in [([], 'YES'),
                ([dict(reminder=True, fault_ids=['raw_code_glyphs'])], 'NO'),
                ([dict(reminder=True, fault_ids=['import_error'])], 'YES'),
                ([dict(reminder=False, text='Unrelated input, classified by Main')], 'YES'),
                (None, UNKNOWN), ([dict(text='ordinary unclassified parent input')], UNKNOWN),
                ([dict(reminder=True)], UNKNOWN)]:
            with self.subTest(interventions=interventions):
                state = advance()
                state = advance(state, cycle=2, completed_sleeps=1, parent_interventions=interventions)
                self.assertEqual(opportunity(state)['HELD'], expected)

    def test_original_parent_correction_is_not_a_followup_reminder(self):
        state = advance(parent_interventions=[dict(reminder=True, fault_ids=['raw_code_glyphs'])])
        state = advance(state, cycle=2, completed_sleeps=1)
        self.assertEqual(opportunity(state)['HELD'], 'YES')

    def test_recurrence_or_reminder_before_sleep_cannot_be_laundered(self):
        changes_list = [dict(raw_act='```python\nｘ = 1\n```'),
                        dict(parent_interventions=[dict(reminder=True, fault_ids=['raw_code_glyphs'])])]
        for changes in changes_list:
            with self.subTest(changes=changes):
                state = advance()
                state = advance(state, cycle=2, **changes)
                state = advance(state, cycle=3, completed_sleeps=1)
                self.assertEqual(opportunity(state)['HELD'], 'NO')

    def test_gaps_or_unknown_intervals_do_not_establish_held(self):
        for changes in (dict(raw_act=None), dict(parent_interventions=None)):
            with self.subTest(changes=changes):
                state = advance()
                state = advance(state, cycle=2, **changes)
                state = advance(state, cycle=3, completed_sleeps=1)
                self.assertEqual(opportunity(state)['HELD'], UNKNOWN)
        state = advance()
        state = advance(state, cycle=3, completed_sleeps=1)
        self.assertEqual(opportunity(state)['HELD'], UNKNOWN)

    def test_held_is_historical_not_permanent_retention(self):
        state = advance()
        state = advance(state, cycle=2, completed_sleeps=1)
        state = advance(state, cycle=3, completed_sleeps=2, raw_act='```python\nｘ = 1\n```')
        self.assertEqual(opportunity(state)['HELD'], 'YES')
        self.assertEqual(opportunity(state, cycle=3)['ENACTED'], 'NO')
        self.assertEqual(state['counts']['by_fault']['raw_code_glyphs']['failures'], 1)

    def test_counts_include_failures_and_unknowns_without_success_selection(self):
        state = advance(child_evidence=None, raw_act='```python\nｘ = 1\n```')
        state = advance(state, cycle=2, child_evidence=None, raw_act='```python\nｘ = 1\n```')
        state = advance(state, cycle=3, child_evidence=None, raw_act=None)
        state = advance(state, cycle=4, child_evidence=None)
        counts = state['counts']['by_fault']['raw_code_glyphs']
        self.assertEqual((counts['opportunities'], counts['measured'], counts['failures'], counts['unknown']),
                         (2, 1, 1, 1))
        self.assertEqual(state['counts']['opportunities'], 2)
        self.assertEqual(state['counts']['cycles'], 4)
        self.assertEqual(state['counts']['observed_by_fault']['raw_code_glyphs'],
                         dict(cycles=4, measured=3, failures=2, unknown=1))

    def test_clean_or_no_code_cycles_are_observations_not_missed_corrections(self):
        for raw in (RAW, None, '', 'no code'):
            with self.subTest(raw=raw):
                state = advance(raw_act=raw, child_evidence=None)
                state = advance(state, cycle=2, raw_act=raw, child_evidence=None)
                self.assertEqual(state['counts']['cycles'], 2)
                self.assertEqual(state['counts']['opportunities'], 0)
                self.assertEqual(state['opportunities'], [])
                for fault in FAULTS:
                    counts = state['counts']['by_fault'][fault]
                    self.assertEqual(counts['opportunities'], 0)
                    self.assertEqual(counts['failures'], 0)
                    self.assertEqual(counts['unknown'], 0)
                    self.assertEqual(state['counts']['observed_by_fault'][fault]['cycles'], 2)
                    for stage in STAGES:
                        self.assertEqual(counts['stages'][stage], dict(YES=0, NO=0, UNKNOWN=0))

    def test_prior_fault_admits_one_correction_with_unknown_child_intentions(self):
        state = advance(raw_act='```python\nｘ = 1\n```', child_evidence=None)
        self.assertEqual(state['counts']['opportunities'], 0)
        state = advance(state, cycle=2, child_evidence=None)
        row = opportunity(state, cycle=2)
        self.assertEqual(row['opportunity_basis'], dict(prior_fault_cycle=1, explicit_noticed=False))
        self.assertEqual([row[stage] for stage in STAGES], [UNKNOWN, UNKNOWN, 'YES', UNKNOWN])
        state = advance(state, cycle=3, completed_sleeps=1, child_evidence=None)
        self.assertEqual(state['counts']['opportunities'], 1)
        self.assertEqual(opportunity(state, cycle=2)['HELD'], 'YES')

    def test_explicit_bound_notice_admits_once_without_prior_observed_fault(self):
        state = advance()
        self.assertEqual(state['counts']['opportunities'], 1)
        row = opportunity(state)
        self.assertEqual(row['opportunity_basis'], dict(prior_fault_cycle=None, explicit_noticed=True))
        self.assertEqual(row['child_evidence_adjudication'], 'UNADJUDICATED')
        prior = advance(raw_act='```python\nｘ = 1\n```', child_evidence=None)
        state = advance(prior, cycle=2)
        self.assertEqual(state['counts']['opportunities'], 1)
        self.assertEqual(opportunity(state, cycle=2)['opportunity_basis'],
                         dict(prior_fault_cycle=1, explicit_noticed=True))

    def test_invalid_or_missing_notice_does_not_admit_from_clean_first_cycle(self):
        invalid = evidence()
        invalid['noticed']['quote'] = 'not present in the raw THINK'
        chosen_only = dict(fault_id='raw_code_glyphs', chosen=evidence()['chosen'])
        for entries in (None, [invalid], [chosen_only], [evidence(), evidence()]):
            with self.subTest(entries=entries):
                state = advance(child_evidence=entries)
                self.assertEqual(state['counts']['opportunities'], 0)
                self.assertEqual(state['cycles'][0]['input']['child_evidence'], entries)

    def test_unknown_or_missing_previous_cycle_cannot_admit_from_stale_fault(self):
        prior = advance(raw_act='```python\nｘ = 1\n```', child_evidence=None)
        state = advance(prior, cycle=3, child_evidence=None)
        self.assertEqual(state['counts']['opportunities'], 0)
        state = advance(raw_act=None, child_evidence=None)
        state = advance(state, cycle=2, child_evidence=None)
        self.assertEqual(state['counts']['opportunities'], 0)

    def test_persisted_state_and_input_are_detached_and_exact(self):
        outcome = receipt()
        source = dict(response=dict(record_sha256='a' * 64), extra='  no normalization λ\n')
        state = advance(execution=outcome, source=source)
        saved = json.loads(json.dumps(state, ensure_ascii=False))
        updated = advance(saved, cycle=2, completed_sleeps=1)
        self.assertEqual(saved, state)
        self.assertEqual(opportunity(saved)['HELD'], UNKNOWN)
        self.assertEqual(opportunity(updated)['HELD'], 'YES')
        outcome['result']['stdout'] = 'mutated'
        source['extra'] = 'mutated'
        self.assertEqual(state['cycles'][0]['input']['source']['extra'], '  no normalization λ\n')
        self.assertEqual(state['cycles'][0]['input']['execution']['result']['stdout'], 'fixture output')
        self.assertEqual(state['cycles'][0]['raw_act_sha256'], blocks.sha(RAW))
        self.assertEqual(state['cycles'][0]['raw_think_sha256'], [blocks.sha(THINK)])

    def test_idempotence_conflicts_and_cross_life_are_explicit(self):
        state = advance()
        replay = advance(json.loads(json.dumps(state)))
        self.assertEqual(replay, state)
        self.assertIsNot(replay, state)
        with self.assertRaisesRegex(ValueError, 'conflicting_cycle_retry'):
            advance(state, raw_act=RAW + '\n')
        with self.assertRaisesRegex(ValueError, 'same_ledger_schema_and_life'):
            advance(state, life_id='other-life')
        state = advance(state, cycle=3, completed_sleeps=2)
        with self.assertRaisesRegex(ValueError, 'increasing_cycle'):
            advance(state, cycle=2)
        with self.assertRaisesRegex(ValueError, 'nondecreasing_completed_sleeps'):
            advance(state, cycle=4, completed_sleeps=1)

    def test_cycle_and_sleep_counters_are_integers_not_booleans(self):
        for changes in (dict(cycle=True), dict(cycle=0), dict(completed_sleeps=True),
                        dict(completed_sleeps=-1)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                advance(**changes)


if __name__ == '__main__':
    unittest.main()
