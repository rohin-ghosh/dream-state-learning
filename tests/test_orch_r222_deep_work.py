import json
import unittest

from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r205_reading_policy import DISCUSSION_POLICY, ReadingPolicy, is_reading
import test_orch_r205_reading_policy as reading_fixture


class DeepWorkTests(unittest.TestCase):
    first = 'The thesis needs evidence from repeated experience. I will separate the hypothesis from results.'
    second = 'The game counts distinct accepted ideas over a horizon. I will compare the same budgets.'
    artifact = 'We investigate whether parent-guided experience yields retained improvements through adapter learning.'
    limitations = 'Controlled retention and a long matched exploration curve are still missing.'
    change = 'I will report exploratory observations separately from demonstrated effects.'

    def setUp(self):
        self.fixture = reading_fixture.ReadingPolicyTests('test_exact_classification_boundary_and_phrase')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def driver(self, outputs):
        driver = self.fixture.driver(outputs)
        driver.readings = ReadingPolicy(self.fixture.journal, discussion_policy=DISCUSSION_POLICY)
        return driver

    def question(self):
        return publish_parent(self.fixture.root, 'Rohin',
            'Draft an abstract for this project. Really think about this one; work through it with your parent.')['id']

    def review(self, identifier, turn, restatement, change, *, release=False, artifact=None, limitations=None):
        text = (f'Reading: {identifier}\nSection: {turn["section"]}\n'
            f'Child response: {turn["response"]["record_index"]}\nJudgment: substantive\n'
            f'Restatement: {restatement}\nBehavior change: {change}')
        if release:
            text += (f'\nRelease reading: {identifier}\nArtifact response: {turn["response"]["record_index"]}'
                f'\nArtifact: {json.dumps(artifact)}\nLimitations: {json.dumps(limitations)}')
        publish_parent(self.fixture.root, 'Astra', text)

    def exchange(self, driver, identifier, section):
        self.fixture.prompt(identifier, section)
        driver.generate_stage('THINK')
        return self.fixture.turns(driver, identifier)[-1]

    def test_explicit_deep_work_phrases_are_not_ordinary_console_messages(self):
        for text in ('Think about this.', 'Really think about this one.',
                     'Work through it with your parent.', 'Work this through with your parent.'):
            with self.subTest(text=text):
                self.assertTrue(is_reading(text))
        self.assertFalse(is_reading('Who are you?'))

    def test_three_real_thinks_and_source_bound_artifact_required(self):
        identifier = self.question()
        third = self.artifact + ' ' + self.limitations + ' ' + self.change
        driver = self.driver([self.first, self.second, 'An ordinary action.', third,
                              'Worked revision: ' + self.artifact, 'Another ordinary action.'])
        first = self.exchange(driver, identifier, 1)
        self.review(identifier, first, 'The thesis needs evidence from repeated experience.',
                    'I will separate the hypothesis from results.')
        second = self.exchange(driver, identifier, 2)
        self.review(identifier, second, 'The game counts distinct accepted ideas over a horizon.',
                    'I will compare the same budgets.', release=True,
                    artifact='The game counts distinct accepted ideas over a horizon.',
                    limitations='I will compare the same budgets.')
        driver.generate_stage('ACT')
        self.assertEqual(self.fixture.records('R205_CONSOLE_REPLY'), [])
        self.assertFalse(self.fixture.records('R205_READING_PARENT_RECEIPT')[-1]['release_accepted'])
        third_turn = self.exchange(driver, identifier, 3)
        self.review(identifier, third_turn, self.artifact, self.change, release=True,
                    artifact=self.artifact, limitations=self.limitations)
        driver.generate_stage('ACT')
        replies = self.fixture.records('R205_CONSOLE_REPLY')
        self.assertEqual(len(replies), 1)
        evidence = replies[0]['reading_evidence']
        self.assertEqual(evidence['minimum_substantive_exchanges'], 3)
        self.assertEqual(len(evidence['substantive_exchanges']), 3)
        self.assertTrue(evidence['artifact']['accepted'])
        self.assertEqual(evidence['artifact']['word_limit'], 150)

    def test_invented_artifact_cannot_release_three_thinks(self):
        identifier = self.question()
        third = self.artifact + ' ' + self.limitations + ' ' + self.change
        driver = self.driver([self.first, self.second, third, 'An ordinary action.'])
        first = self.exchange(driver, identifier, 1)
        self.review(identifier, first, 'The thesis needs evidence from repeated experience.',
                    'I will separate the hypothesis from results.')
        second = self.exchange(driver, identifier, 2)
        self.review(identifier, second, 'The game counts distinct accepted ideas over a horizon.',
                    'I will compare the same budgets.')
        third_turn = self.exchange(driver, identifier, 3)
        self.review(identifier, third_turn, self.artifact, self.change, release=True,
                    artifact='An invented draft not authored by this child.', limitations=self.limitations)
        driver.generate_stage('ACT')
        self.assertEqual(self.fixture.records('R205_CONSOLE_REPLY'), [])
        self.assertFalse(self.fixture.records('R205_READING_PARENT_RECEIPT')[-1]['artifact']['accepted'])

    def test_worked_revision_preserves_original_reply_and_survives_restore(self):
        identifier = self.question()
        old_config = {key: value for key, value in self.fixture.config.items() if key != 'reading_reply_policy'}
        old = self.fixture.driver(['An unsupported early abstract.', 'An ordinary thought.'], old_config)
        old.generate_stage('THINK')
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_REPLY')), 1)
        driver = self.driver([self.first])
        publish_parent(self.fixture.root, 'Astra', f'Rework reading: {identifier}\nSection: 1\n'
                       'Return to the actual thesis and distinguish evidence from the intended experiment.')
        driver.generate_stage('THINK')
        entry = driver.readings.entries['parent:inbox:' + identifier]
        self.assertEqual(entry['status'], 'DISCUSSING')
        self.assertEqual(len(entry['turns']), 1)
        self.assertGreater(entry['revision_of_reply_index'], 0)
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_REPLY')), 1)
        restored = ReadingPolicy(self.fixture.journal, discussion_policy=DISCUSSION_POLICY)
        self.assertEqual(restored.entries['parent:inbox:' + identifier]['status'], 'DISCUSSING')
        original = next(event for event in self.fixture.journal.read_inbox()
                        if event.event_id == 'parent:inbox:' + identifier)
        self.assertFalse(restored.ready(original, set()))
        self.assertIn('Worked revision:', restored.reply_instruction(original))

    def test_abstract_word_limit_accepts_150_but_not_151_words(self):
        identifier = self.question()
        artifact = ' '.join(f'evidence{number}' for number in range(151))
        third = artifact + ' ' + self.limitations + ' ' + self.change
        driver = self.driver([self.first, self.second, third, 'An ordinary action.',
                              'A completed abstract.', 'Another ordinary action.'])
        first = self.exchange(driver, identifier, 1)
        self.review(identifier, first, 'The thesis needs evidence from repeated experience.',
                    'I will separate the hypothesis from results.')
        second = self.exchange(driver, identifier, 2)
        self.review(identifier, second, 'The game counts distinct accepted ideas over a horizon.',
                    'I will compare the same budgets.')
        third_turn = self.exchange(driver, identifier, 3)
        self.review(identifier, third_turn, artifact, self.change, release=True,
                    artifact=artifact, limitations=self.limitations)
        driver.generate_stage('ACT')
        rejected = self.fixture.records('R205_READING_PARENT_RECEIPT')[-1]
        self.assertFalse(rejected['release_accepted'])
        self.assertEqual(rejected['artifact']['word_count'], 151)
        self.assertEqual(self.fixture.records('R205_CONSOLE_REPLY'), [])
        bounded_artifact = artifact.rsplit(' ', 1)[0]
        publish_parent(self.fixture.root, 'Astra',
            f'Release reading: {identifier}\nArtifact response: {third_turn["response"]["record_index"]}'
            f'\nArtifact: {json.dumps(bounded_artifact)}\nLimitations: {json.dumps(self.limitations)}')
        driver.generate_stage('ACT')
        evidence = self.fixture.records('R205_CONSOLE_REPLY')[0]['reading_evidence']
        self.assertTrue(evidence['artifact']['accepted'])
        self.assertEqual(evidence['artifact']['word_count'], 150)

    def test_reopened_revision_releases_once_after_three_reviewed_thinks(self):
        identifier = self.question()
        old_config = {key: value for key, value in self.fixture.config.items() if key != 'reading_reply_policy'}
        old = self.fixture.driver(['An unsupported early abstract.', 'An ordinary thought.'], old_config)
        old.generate_stage('THINK')
        original_reply_index = ReadingPolicy(self.fixture.journal).latest_reply_indices['parent:inbox:' + identifier]
        third = self.artifact + ' ' + self.limitations + ' ' + self.change
        driver = self.driver([self.first, self.second, third, 'Worked revision: ' + self.artifact,
                              'An ordinary action.', 'A later ordinary action.'])
        publish_parent(self.fixture.root, 'Astra', f'Rework reading: {identifier}\nSection: 1\n'
                       'Restate the thesis and distinguish evidence from the intended experiment.')
        driver.generate_stage('THINK')
        first = self.fixture.turns(driver, identifier)[-1]
        self.review(identifier, first, 'The thesis needs evidence from repeated experience.',
                    'I will separate the hypothesis from results.')
        second = self.exchange(driver, identifier, 2)
        self.review(identifier, second, 'The game counts distinct accepted ideas over a horizon.',
                    'I will compare the same budgets.')
        third_turn = self.exchange(driver, identifier, 3)
        self.review(identifier, third_turn, self.artifact, self.change, release=True,
                    artifact=self.artifact, limitations=self.limitations)
        driver.generate_stage('ACT')
        replies = self.fixture.records('R205_CONSOLE_REPLY')
        self.assertEqual(len(replies), 2)
        evidence = replies[-1]['reading_evidence']
        self.assertEqual(evidence['revision_of_reply_index'], original_reply_index)
        self.assertEqual(len(evidence['substantive_exchanges']), 3)
        restored = ReadingPolicy(self.fixture.journal, discussion_policy=DISCUSSION_POLICY)
        self.assertEqual(restored.entries['parent:inbox:' + identifier]['status'], 'REPLIED')
        driver.readings = restored
        driver.generate_stage('ACT')
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_REPLY')), 2)

    def test_unknown_discussion_policy_fails(self):
        with self.assertRaisesRegex(ValueError, 'known_deep_work'):
            ReadingPolicy(self.fixture.journal, discussion_policy='invented')


if __name__ == '__main__':
    unittest.main()
