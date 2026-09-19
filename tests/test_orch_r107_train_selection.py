from copy import deepcopy
import unittest

from gpu import orch_r107_train_selection as selection


class TrainSelectionTests(unittest.TestCase):
    def fixture(self):
        task = dict(node='start', goal='end', ports=['port'], events=['event'])
        task_id = 'route-train-display-' + selection.digest(task)
        world = dict(master=selection.MASTERS[0], edges=['hidden_edge_never_projected'])
        messages = [dict(role='system', content='PRIVATE_STEERING_DO_NOT_PROJECT'),
                    dict(role='user', content='CURRENT start\nAn event is available.\n')]
        raw = 'I planned to route.\nThe event can resolve my uncertainty.\nI will inspect it first.\nREAD EVENT event'
        response = dict(raw=raw, messages=messages, terminal=True, truncated=False, token_ids=[12, 13])
        call = dict(task_id=task_id, family='route', source_state=selection.BASE, adapter_state=None,
            phase_version=selection.PHASE, arm=selection.ARMS[4], physical_index=4,
            source_events_sha256=selection.PINS['SOURCE_EVENTS.json'], messages=messages,
            response=response, semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
            generated_tokens=1)
        episode = dict(world=world, task=task, task_id=task_id, phase_version=selection.PHASE,
            semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False, actor_calls=1,
            captures=[dict(response=response, messages=messages, command=dict(kind='READ EVENT', value='event'))],
            correct=False, terminal_reason='PRIVATE_HIDDEN_OUTCOME')
        reference = dict(source_root=selection.ROOT, source_phase=selection.PHASE,
            source_purpose='SELF_GENERATED_BASE_TRAIN_EPISODES', parenting_experience=False,
            teacher_target=False, held_readout=False, checkpoint_derived=False,
            family='route', split='TRAIN_SCREEN_NO_FIT', world_master=selection.MASTERS[0],
            task_id=task_id, source_state=selection.BASE, adapter_state=None, index=4,
            episode_path=selection.ROOT+'/shard4/EPISODE_0_3.json', episode_sha256='a'*64,
            finished_unix=1.0, calls=[dict(path='native_call', sha256='b'*64)])
        roster = dict(task=task, task_id=task_id)
        document = selection.bind_episode(episode, [call], reference, roster, world)
        return document, episode, call, roster, world

    def span(self, document, line_id):
        line = document['lines'][line_id - 1]
        return [dict(line_id=line_id, start=0, end=len(line['text']))]

    def annotation(self, document, registration):
        return dict(episode_sha256=document['reference']['episode_sha256'],
            registration_sha256=selection.digest(registration), lines_sha256=document['lines_sha256'],
            reviewer='SYNTHETIC_TEST_AUTHOR_NOT_REAL_REVIEW', full_episode_read=True, outcome_used=False,
            functional_change=dict(status='PASS', reason='Fixture: the uncertainty changes a route plan into a read.',
                prior=self.span(document, 3), observation=self.span(document, 2),
                realization=self.span(document, 4), continuation=self.span(document, 6)),
            ordinary_anchor=dict(status='UNKNOWN', reason='Not assessed in this fixture.', observation=[], reasoning=[]),
            grounding=dict(status='PASS', reason='Fixture evidence is only the displayed event.',
                evidence=self.span(document, 2)))

    def selected(self, document, annotation):
        registration = selection.freeze([document])
        annotations = {} if annotation is None else {document['reference']['episode_sha256']: annotation}
        return selection.select(registration, [document], annotations)['rows'][0]

    def test_native_public_projection_excludes_steering_world_outcomes(self):
        document, *_ = self.fixture()
        payload = str(document)
        for secret in ('PRIVATE_STEERING', 'hidden_edge_never_projected', 'PRIVATE_HIDDEN_OUTCOME', "'correct'"):
            self.assertNotIn(secret, payload)
        self.assertIn('READ EVENT event', payload)

    def test_unreviewed_is_UNKNOWN_not_negative_or_positive_supervision(self):
        document, *_ = self.fixture()
        result = self.selected(document, None)
        self.assertEqual(result['selection_tag'], 'UNKNOWN')
        self.assertEqual(result['supervision_status'], 'NONE')
        self.assertFalse(result['trainingAllowed'])

    def test_functional_change_is_candidate_never_training_or_causal_proof(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        result = self.selected(document, annotation)
        self.assertEqual(result['selection_tag'], 'FUNCTIONAL_CHANGE_CANDIDATE')
        self.assertEqual(result['causal_effect'], 'UNMEASURED')
        self.assertEqual(result['original_semantic_status'], 'UNREVIEWED')
        self.assertFalse(result['labels_exported'])

    def test_ordinary_anchor_needs_no_realization_or_branch(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['functional_change'].update(status='FAIL', reason='Routine reasoning, not reallocation.')
        annotation['ordinary_anchor'] = dict(status='PASS', reason='Ordinary source-grounded next action.',
            observation=self.span(document, 2), reasoning=self.span(document, 5))
        result = self.selected(document, annotation)
        self.assertEqual(result['selection_tag'], 'ORDINARY_ANCHOR_CANDIDATE')
        self.assertEqual(result['functional_status'], 'FAIL')

    def test_failed_grounding_preserves_positive_claim_without_training(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['grounding'].update(status='FAIL', reason='Fixture wrong claim.', evidence=self.span(document, 4))
        result = self.selected(document, annotation)
        self.assertEqual(result['selection_tag'], 'FAILED')
        self.assertEqual(result['functional_status'], 'PASS')
        self.assertFalse(result['trainingAllowed'])
        self.assertTrue(result['failed_is_not_negative_supervision'])

    def test_unknown_grounding_does_not_become_candidate(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['grounding'].update(status='UNKNOWN', reason='Insufficient evidence.', evidence=[])
        self.assertEqual(self.selected(document, annotation)['selection_tag'], 'UNKNOWN')

    def test_announcement_without_observed_followthrough_cannot_PASS(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['functional_change']['continuation'] = []
        with self.assertRaisesRegex(ValueError, 'bound_evidence_required'):
            self.selected(document, annotation)

    def test_return_before_realization_rejected(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['functional_change']['continuation'] = self.span(document, 3)
        with self.assertRaisesRegex(ValueError, 'observed_realization'):
            self.selected(document, annotation)

    def test_self_report_cannot_be_public_observation(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['functional_change']['observation'] = self.span(document, 3)
        with self.assertRaisesRegex(ValueError, 'evidence_visibility'):
            self.selected(document, annotation)

    def test_invented_retyped_or_out_of_bounds_evidence_rejected(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        for selector in (dict(line_id=999, start=0, end=1), dict(line_id=3, start=0, end=999),
                         dict(line_id=True, start=0, end=1), dict(line_id=3, start=0, end=1, text='invented')):
            changed = deepcopy(annotation)
            changed['functional_change']['prior'] = [selector]
            with self.assertRaises(ValueError):
                self.selected(document, changed)

    def test_current_wrong_outcome_does_not_gate_grounded_candidate(self):
        document, episode, call, roster, world = self.fixture()
        episode['correct'] = True
        second = selection.bind_episode(episode, [call], document['reference'], roster, world)
        self.assertEqual(document, second)

    def test_no_token_minimum_voice_heading_or_considered_path_gate(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        annotation['functional_change']['reason'] = 'Considered and rejected the initial plan; changed the next action.'
        self.assertEqual(document['mechanical']['generated_content_tokens'], 1)
        self.assertEqual(self.selected(document, annotation)['selection_tag'], 'FUNCTIONAL_CHANGE_CANDIDATE')

    def test_branchcount_or_outcome_criterion_is_not_part_of_contract(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        for change in (dict(branch_count=2), dict(outcome_used=True), dict(full_episode_read=False)):
            with self.assertRaises(ValueError):
                self.selected(document, dict(annotation, **change))

    def test_held_world_and_same_family_descendants_excluded(self):
        document, *_ = self.fixture()
        for change in (dict(world_master='ORCH-FULL-RICH-HELD-WORLD-0'), dict(split='HELD'), dict(held_readout=True)):
            with self.assertRaises(ValueError):
                selection.check_lineage(dict(document['reference'], **change))

    def test_all_fixed_capability_families_and_ids_excluded(self):
        document, *_ = self.fixture()
        for family in selection.CAPABILITY_FAMILIES:
            with self.assertRaisesRegex(ValueError, 'family_world_allowlist'):
                selection.check_lineage(dict(document['reference'], family=family))
        with self.assertRaisesRegex(ValueError, 'capability_tasks_excluded'):
            selection.check_lineage(dict(document['reference'], task_id='R107_CODE_00'))

    def test_root_purpose_teacher_L2_adapter_checkpoint_fail_closed(self):
        document, *_ = self.fixture()
        for change in (dict(source_root='/tmp/untrusted'), dict(source_purpose='L2_PARENTING'),
                       dict(parenting_experience=True), dict(teacher_target=True), dict(checkpoint_derived=True),
                       dict(adapter_state='37ec'), dict(source_state='37ec')):
            with self.assertRaises(ValueError):
                selection.check_lineage(dict(document['reference'], **change))

    def test_actor_requires_actual_no_adapter_counts(self):
        actor = dict(actual_base_sha256=selection.BASE, adapter_state=None,
            loading_mode='DIRECT_BASE_NO_ADAPTER', phase_version=selection.PHASE,
            no_adapter=dict(adapter_parameter_count=0, peft_wrapper_count=0,
                            trainable_parameter_count=0, hf_peft_config_loaded=False))
        selection.check_actor(actor)
        actor['no_adapter']['peft_wrapper_count'] = 1
        with self.assertRaisesRegex(ValueError, 'no_adapter'):
            selection.check_actor(actor)

    def test_native_CALL_and_episode_target_join_required(self):
        document, episode, call, roster, world = self.fixture()
        changed = deepcopy(call)
        changed['response']['raw'] = 'different source'
        with self.assertRaisesRegex(ValueError, 'CALL_episode_join'):
            selection.bind_episode(episode, [changed], document['reference'], roster, world)

    def test_task_or_world_relabel_is_not_enough(self):
        document, episode, call, roster, world = self.fixture()
        changed = deepcopy(episode)
        changed['task']['goal'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'roster_task_binding'):
            selection.bind_episode(changed, [call], document['reference'], roster, world)

    def test_registration_caps_and_order_do_not_use_outcomes(self):
        document, *_ = self.fixture()
        documents = []
        for index in (4, 5):
            for ordinal in range(12):
                copied = deepcopy(document)
                copied['reference'].update(index=index, episode_sha256=selection.digest([index, ordinal]),
                    task_id='route-train-display-'+selection.digest([index, ordinal]), finished_unix=ordinal)
                documents.append(copied)
        registered = selection.freeze(list(reversed(documents)))
        self.assertEqual(len(registered['rows']), 16)
        self.assertEqual([row['reference']['finished_unix'] for row in registered['rows']], list(range(8))*2)

    def test_prior_audit_not_relabelled_or_reused(self):
        document, *_ = self.fixture()
        prior = deepcopy(document)
        prior['reference']['episode_sha256'] = selection.PREVIOUSLY_AUDITED[0]
        registered = selection.freeze([prior, document])
        self.assertEqual(len(registered['rows']), 1)
        with self.assertRaisesRegex(ValueError, 'unregistered_or_old_review'):
            selection.select(registered, [document], {selection.PREVIOUSLY_AUDITED[0]: {}})

    def test_wrong_registration_and_source_hashes_rejected(self):
        document, *_ = self.fixture()
        annotation = self.annotation(document, selection.freeze([document]))
        for key in ('registration_sha256', 'lines_sha256', 'episode_sha256'):
            with self.assertRaisesRegex(ValueError, 'review_binding'):
                self.selected(document, dict(annotation, **{key: '0'*64}))

    def test_missing_annotations_preserve_all_episode_denominators(self):
        document, *_ = self.fixture()
        result = selection.select(selection.freeze([document]), [document], {})
        self.assertEqual(result['denominator_episodes'], 1)
        self.assertEqual(result['reviewed_episodes'], 0)
        self.assertEqual(result['supervision_rows'], 0)
        self.assertEqual(result['selection_counts'], {'UNKNOWN': 1})

    def test_retyped_source_lines_cannot_reuse_stored_hash(self):
        document, *_ = self.fixture()
        registered = selection.freeze([document])
        document['lines'][0]['text'] = 'forged public observation'
        with self.assertRaisesRegex(ValueError, 'actual_public_line_hash'):
            selection.select(registered, [document], {})
        with self.assertRaisesRegex(ValueError, 'actual_public_line_hash'):
            selection.freeze([document])

    def test_duplicate_registration_rows_do_not_expand_denominator(self):
        document, *_ = self.fixture()
        registered = selection.freeze([document])
        registered['rows'].append(deepcopy(registered['rows'][0]))
        with self.assertRaisesRegex(ValueError, 'caps_no_duplicates'):
            selection.select(registered, [document], {})

    def test_incomplete_snapshot_exclusions_remain_unknown_not_failed_targets(self):
        document, *_ = self.fixture()
        excluded = [dict(path='native/incomplete', tag='UNKNOWN_INCOMPLETE_CALL_CAPTURE_NOT_SUPERVISION')]
        registered = selection.freeze([document], excluded)
        self.assertEqual(registered['snapshot_exclusions'], excluded)
        self.assertEqual(selection.select(registered, [document], {})['supervision_rows'], 0)


if __name__ == '__main__':
    unittest.main()
