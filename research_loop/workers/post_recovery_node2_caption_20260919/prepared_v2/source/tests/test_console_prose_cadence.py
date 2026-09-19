from copy import deepcopy

import unittest

from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, STAGE_BOUNDARY_POLICY
from organism_v6 import orch_r194_code_target_filter as filters
from organism_v6 import orch_r203_prose_target_filter as prose
from test_existing_prose import row
from test_existing_driver import ThinkActLearnTests


def check_raw_english_own_row_excluded_without_normalization(text):
    candidate = row(0, text)
    before = deepcopy(candidate)
    retained, retained_old, proof = filters.filter_learn_review_targets(
        [candidate], [], filters.REVIEW_POLICY)
    assert retained == retained_old == []
    assert candidate == before
    assert proof['excluded'][0]['source_sha256'] == candidate['source_sha256']
    assert proof['excluded'][0]['reason'] == 'provisional_english_target_script_quarantine'
    assert proof['raw_modified'] is proof['targets_normalized'] is False


def test_english_names_math_punctuation_and_external_prefix_are_unchanged():
    candidate = row(0, 'C2 and Byte can disagree. LoRA, Astra, NASA, café, α + β — all remain.')
    candidate['prefix'] = [{'role': 'user', 'content': 'Rohin: 中文 ＡＢＣ'}]
    before = deepcopy(candidate)
    retained, unused_old, proof = filters.filter_learn_review_targets([candidate], [], filters.REVIEW_POLICY)
    assert retained == [before]
    assert candidate == before
    assert not proof['excluded']


def test_legacy_policy_and_unannotated_rows_preserve_previous_semantics():
    legacy = dict(row(0, 'Unchanged 中文'), prose_target_filter=prose.LEGACY_POLICY)
    unannotated = row(1, 'Unchanged 中文', annotated=False)
    retained, unused_old, proof = filters.filter_learn_review_targets(
        [legacy, unannotated], [], filters.REVIEW_POLICY)
    assert retained == [legacy, unannotated]
    assert not proof['excluded']


class ConsoleCadenceTests(ThinkActLearnTests):
    def configure_console(self):
        self.config.update(stage_boundary_policy=STAGE_BOUNDARY_POLICY,
            console_reply_policy=CONSOLE_REPLY_POLICY,
            pinned_messages_policy='R206_VERBATIM_ROHIN_MESSAGES_V1',
            prose_target_filter=prose.POLICY, learn_review_filter=filters.REVIEW_POLICY)

    def test_separate_replies_before_learn_and_corrupt_reply_veto(self):
        self.configure_console()
        publish_parent(self.root, 'Rohin', 'First distinct question.')
        publish_parent(self.root, 'Rohin', 'Second distinct question.')
        driver = self.driver(['First own answer. 中文', 'Second own answer.', 'My review.'])
        driver.generate_stage('LEARN')
        replies = self.records('R205_CONSOLE_REPLY')
        assert len(replies) == 2
        assert all(len(reply['source_inbox_events']) == 1 for reply in replies)
        assert len({reply['source_inbox_events'][0]['event_id'] for reply in replies}) == 2
        assert [entry['stage'] for entry in self.records('R184_STAGE')] == ['ACT', 'ACT', 'LEARN']
        assert all(not reply['outcome']['tool_execution_allowed'] for reply in replies)
        proof = self.records('R195_LEARN_REVIEW')[-1]['proof']
        assert proof['excluded'][0]['source_sha256'] == self.stream.rows[0]['source_sha256']
        assert self.stream.rows[0]['target'] == 'First own answer. 中文'
        driver.child.outputs = iter(['Another normal thought.'])
        driver.generate_stage('THINK')
        assert len(self.records('R205_CONSOLE_REPLY')) == 2

    def test_message_arriving_during_review_is_answered_before_training(self):
        self.configure_console()
        driver = self.driver(['First review.', 'My actual answer.', 'Review including my answer.'])
        generate = driver.child.generate
        published = False

        def arrive_during_review(messages, **limits):
            nonlocal published
            result = generate(messages, **limits)
            if not published:
                publish_parent(self.root, 'Rohin', 'Arrived while LEARN was generating.')
                published = True
            return result

        driver.child.generate = arrive_during_review
        driver.prepare_sleep(1)
        assert [entry['stage'] for entry in self.records('R184_STAGE')] == ['LEARN', 'ACT', 'LEARN']
        assert len(self.records('R205_CONSOLE_REPLY')) == 1
        assert self.records('R184_SLEEP_NOTICE')[-1]['new_rows'] == 3


class ProseRepairTests(unittest.TestCase):
    def test_scripts_preserve_raw(self):
        for text in ('I choose C2. 我会继续思考。', 'I choose C2. Ｔｈｉｓ is a fullwidth sentence.',
                'I choose C2. カタカナ', 'I choose C2. 한글'):
            with self.subTest(text=text):
                check_raw_english_own_row_excluded_without_normalization(text)

    def test_external_inputs_names_math_and_punctuation(self):
        test_english_names_math_punctuation_and_external_prefix_are_unchanged()

    def test_legacy_rows(self):
        test_legacy_policy_and_unannotated_rows_preserve_previous_semantics()
