"""Bounded same-child TRAIN/review/fit integration; no loader, reviewer or launcher."""

from copy import deepcopy
import inspect
import math
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import orch_r161_reviewed_packet_fit as fit
from gpu import orch_r125_stream_journal as journal_module
from organism_v6 import orch_r125_continual_stream as stream_module


SCHEMA = 'R164_GUIDED_CYCLE_V1'
ARMS = ('parented_learning', 'parented_frozen', 'unparented_learning')
require, capture, gym = fit.require, fit.capture, fit.capture.gym
FROZEN_EVENT = 'R164_FROZEN_COMPLETE'


def source_paths():
    return tuple(Path(inspect.getfile(module)).resolve() for module in
                 (inspect.getmodule(source_paths), fit, capture, gym, gym.console,
                  journal_module, stream_module))


def validate_curriculum(curriculum, expected_sha256, authority, expected_authority_sha256):
    require(type(curriculum) is dict and fit.digest(curriculum) == expected_sha256,
            'independently_pinned_curriculum_required')
    require(set(curriculum) == {'schema', 'authority_sha256', 'plan', 'capture_root',
            'hard_end_unix', 'tasks', 'capture_specs', 'max_output_bytes'}, 'exact_curriculum_fields')
    require(curriculum['schema'] == SCHEMA and curriculum['authority_sha256'] == expected_authority_sha256
            and fit.digest(authority) == expected_authority_sha256, 'curriculum_fork_policy_binding')
    require(authority['evidence_mode'] == fit.DYNAMIC and authority['allow_off_policy_new'] is False,
            'continuing_own_fork_dynamic_policy_only')
    root = capture.canonical(authority['fork_root'])
    require(root.parent.name.startswith('orch_r158_') and root.name in ARMS, 'isolated_R158_labelled_fork')
    require(authority['mode'] == ('frozen' if root.name == 'parented_frozen' else 'learning'), 'arm_mode_binding')
    output = capture.canonical(curriculum['capture_root'])
    protected = [root, *(capture.canonical(value) for value in authority['protected_roots'])]
    require(all(not output.is_relative_to(path) and not path.is_relative_to(output) for path in protected),
            'captures_separate_from_learner_and_protected_lives')
    wall = curriculum['hard_end_unix']
    require(type(wall) in (int, float) and math.isfinite(wall) and wall > 0, 'finite_cycle_wall')
    require(type(curriculum['max_output_bytes']) is int
            and 16384 <= curriculum['max_output_bytes'] <= 32 * 1024**2, 'bounded_cycle_output')
    tasks = curriculum['tasks']
    require(type(tasks) is list and 0 < len(tasks) <= 16, 'bounded_curriculum')
    indices = []
    for task in tasks:
        require(type(task) is dict and set(task) == {'task_index', 'guidance'}, 'exact_curriculum_task')
        identifier = gym.task_id(task['task_index'])
        require(identifier not in authority['excluded_task_ids'], 'curriculum_task_excluded')
        indices.append(task['task_index'])
        guidance = task['guidance']
        require(guidance is None or type(guidance) is dict and set(guidance) == {'speaker', 'text'}
                and guidance['speaker'] in ('Astra', 'Fable', 'Rohin') and type(guidance['text']) is str
                and 0 < len(guidance['text']) <= 12000, 'explicit_original_parent_guidance')
        require(root.name != 'unparented_learning' or guidance is None, 'unparented_has_no_parent_guidance')
    require(len(set(indices)) == len(indices), 'curriculum_no_task_replay')
    specs = curriculum['capture_specs']
    require(type(specs) is list and 0 < len(specs) <= 2, 'bounded_explicit_capture_specs')
    for spec in specs:
        require(type(spec) is dict and set(spec) == {'response', 'target_kind', 'label', 'feedback'},
                'exact_capture_spec')
        require(spec['response'] in ('answer', 'followup') and spec['target_kind'] in capture.eligibility.TARGET_KINDS
                and spec['label'] in capture.eligibility.LABELS and type(spec['feedback']) is bool,
                'supported_capture_spec')
        require(spec['target_kind'] != 'POST_FEEDBACK_REFLECTION' or spec['response'] == 'followup',
                'reflection_after_real_answer_only')
        require(spec['feedback'] == (spec['label'] == 'feedback_use')
                and (not spec['feedback'] or spec['response'] == 'followup'), 'real_prior_feedback_binding')
    require(len({fit.digest(spec) for spec in specs}) == len(specs), 'duplicate_capture_spec')
    return dict(root=str(root), capture_root=str(output), runnable=True,
                journal_requirement='GuidedJournal' if authority['mode'] == 'frozen' else 'StreamJournal')


def validate_matched(curricula, curriculum_hashes, authorities, authority_hashes):
    require(all(set(group) == set(ARMS) for group in
                (curricula, curriculum_hashes, authorities, authority_hashes)), 'exact_three_matched_arms')
    reports = {arm: validate_curriculum(curricula[arm], curriculum_hashes[arm], authorities[arm],
                                       authority_hashes[arm]) for arm in ARMS}
    require(all(Path(reports[arm]['root']).name == arm for arm in ARMS), 'matched_arm_identity')
    require(len({str(Path(item['root']).parent) for item in reports.values()}) == 1, 'one_isolated_matched_cohort')
    for field in ('initializer', 'tokenizer_sha256', 'anchors_sha256', 'generator_binding',
                  'excluded_task_ids', 'context_limit', 'fit_limits', 'reader_limits'):
        require(all(authorities[arm][field] == authorities[ARMS[0]][field] for arm in ARMS),
                'matched_common_' + field)
    require(all([task['task_index'] for task in curricula[arm]['tasks']]
                == [task['task_index'] for task in curricula[ARMS[0]]['tasks']] for arm in ARMS),
            'matched_task_sequence')
    for field in ('capture_specs', 'hard_end_unix'):
        require(all(curricula[arm][field] == curricula[ARMS[0]][field] for arm in ARMS),
                'matched_all_arms_' + field)
    for field in ('tasks', 'capture_specs', 'hard_end_unix'):
        require(curricula['parented_learning'][field] == curricula['parented_frozen'][field],
                'matched_parented_' + field)
    require(len({report['capture_root'] for report in reports.values()}) == 3, 'disjoint_capture_outputs')
    return dict(schema=SCHEMA, status='CONFIGURATION_COMPARISON_NOT_ADMISSION', arms=reports,
                all_three_interfaces_supported=True, scientific_claim=False)


class GuidedJournal(journal_module.StreamJournal):
    def __init__(self, root, *, expected_authority_sha256, create=False):
        root = capture.canonical(root)
        require(root.name == 'stream', 'exact_frozen_stream_directory')
        self.fork_root = root.parent
        require(self.fork_root.name == 'parented_frozen'
                and self.fork_root.parent.name.startswith('orch_r158_'), 'isolated_frozen_journal_only')
        self.policy_sha = expected_authority_sha256
        reader = capture.Reader(capture.Limits())
        self.policy = capture.decode(reader.read(self.fork_root/'AUTHORITY.json')[0])
        require(fit.digest(self.policy) == self.policy_sha and self.policy['mode'] == 'frozen'
                and self.policy['fork_root'] == str(self.fork_root) and self.policy['evidence_mode'] == fit.DYNAMIC,
                'frozen_journal_independent_policy_pin')
        fit.verify_authority(self.policy, self.policy_sha, reader=reader)
        require(str(Path(__file__).resolve()) in self.policy['source_pins'], 'frozen_journal_source_pin')
        super().__init__(root, create=create)

    def _advance(self, state, kind, document):
        require(kind not in ('SLEEP_COMPLETE', 'UPDATE'), 'frozen_journal_no_native_update_boundary')
        if kind != FROZEN_EVENT:
            return super()._advance(state, kind, document)
        require(set(document) == {'status', 'cycle', 'optimizer_steps', 'total_optimizer_steps',
            'new_row_sha256', 'checkpoint', 'checkpoint_sha256', 'reviewed_fit_commit', 'raw_rows_modified',
            'anchor_lambda', 'mix_kind', 'presentations', 'child_token_exposures', 'anchor_token_exposures',
            'no_update_reason', 'resume_state'}, 'exact_frozen_boundary_record')
        require(state['latest'] is not None and state['sleep_request'] is not None
                and state['request'] is None and state['response'] is None, 'frozen_boundary_after_sleep_request_only')
        checkpoint = self._checkpoint(document['resume_state'])
        current, previous = checkpoint['document']['state'], state['latest']['document']['state']
        self._unchanged(previous, current, {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'})
        receipt = {key: value for key, value in document.items() if key != 'resume_state'}
        require(current['pending'] is None and previous['pending'] == 'sleep:'+fit.digest(
                    [row['source_sha256'] for row in previous['rows'][previous['sleep_frontier']:]])
                and current['sleep_frontier'] == len(previous['rows']) > previous['sleep_frontier']
                and current['sleep_receipts'] == previous['sleep_receipts']+[receipt]
                and receipt['new_row_sha256'] == [row['source_sha256'] for row in previous['rows'][previous['sleep_frontier']:]],
                'frozen_exact_raw_frontier_no_rewrite')
        index = len(previous['sleep_receipts'])
        require(type(receipt['cycle']) is int and receipt['cycle'] == index+1 == state['sleep_request']['cycle'],
                'frozen_cycle_binding')
        reader = capture.Reader(capture.Limits(**self.policy['reader_limits']))
        require(capture.decode(reader.read(self.fork_root/'AUTHORITY.json')[0]) == self.policy,
                'frozen_policy_unchanged')
        reference = receipt['reviewed_fit_commit']
        path = self.fork_root/f'batch{index:04d}'/'COMMIT.json'
        require(type(reference) is dict and set(reference) == {'path', 'sha256'} and reference['path'] == str(path)
                and not os.path.lexists(path.parent/'FAILED.json'), 'frozen_actual_committed_fit_path')
        commit = capture.decode(fit._ref(reader, reference))
        require(commit['schema'] == fit.SCHEMA and commit['status'] == 'COMMITTED'
                and commit['authority_sha256'] == self.policy_sha and type(commit['batch_index']) is int
                and commit['batch_index'] == index and commit['evidence_mode'] == fit.DYNAMIC,
                'frozen_fit_policy_and_index')
        prior_sha = previous['sleep_receipts'][-1]['reviewed_fit_commit']['sha256'] if index else None
        require(commit['previous_commit_sha256'] == prior_sha, 'frozen_prior_fit_chain')
        before, after = fit._state(commit['before_state']), fit._state(commit['after_state'])
        require(before == after and all(after[key] == self.policy['initializer']['state'][key]
                for key in after if key != 'rng_sha256'), 'frozen_exact_adapter_AdamW_base_no_updates')
        require(commit['training_performed'] is False and type(commit['updates']) is int and commit['updates'] == 0
                and receipt['status'] == 'COMPLETE' and type(receipt['optimizer_steps']) is int
                and receipt['optimizer_steps'] == receipt['total_optimizer_steps'] == 0
                and receipt['no_update_reason'] == 'frozen_control' and receipt['raw_rows_modified'] is False,
                'truthful_frozen_zero_update_receipt')
        require(all(commit[key] == receipt[key] == empty for key, empty in
                (('presentations', {}), ('child_token_exposures', 0), ('anchor_token_exposures', 0)))
                and receipt['anchor_lambda'] == .25
                and receipt['mix_kind'] == 'OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION', 'frozen_zero_exposures')
        saved = fit._checkpoint(reader, commit['checkpoint'], after, directory=path.parent/'checkpoint')
        require(saved == receipt['checkpoint'] and saved.get('experiment') == current.get('experiment')
                and receipt['checkpoint_sha256'] == saved['checkpoint_sha256']
                and current['model_state_sha256'] == fit.digest(saved['checkpoint_sha256']),
                'frozen_saved_checkpoint_and_generation_state')
        state['sleep_request'], state['latest'] = None, checkpoint

    def commit_frozen(self, stream, receipt):
        require(stream.pending is None and receipt['no_update_reason'] == 'frozen_control', 'clean_frozen_stream')
        candidate = stream.checkpoint()
        candidate['state']['sleep_frontier'] = len(stream.rows)
        candidate['state']['sleep_receipts'].append(deepcopy(receipt))
        candidate['state']['model_state_sha256'] = fit.digest(receipt['checkpoint_sha256'])
        candidate['sha256'] = fit.digest(candidate['state'])
        try:
            self.record(FROZEN_EVENT, dict(receipt, resume_state=candidate))
        except BaseException:
            stream.pending = 'sleep:'+fit.digest(receipt)
            raise
        stream.sleep_frontier = len(stream.rows)
        stream.sleep_receipts.append(deepcopy(receipt))
        stream.model_state_sha256 = candidate['state']['model_state_sha256']
        return stream.checkpoint()


class GuidedCycle:
    def __init__(self, *, child, stream, journal, executor, anchors, authority,
                 expected_authority_sha256, curriculum, expected_curriculum_sha256):
        checked = validate_curriculum(curriculum, expected_curriculum_sha256, authority, expected_authority_sha256)
        require(authority['mode'] != 'frozen' or isinstance(journal, GuidedJournal)
                and journal.policy_sha == expected_authority_sha256, 'frozen_requires_bound_GuidedJournal')
        self.authority, self.curriculum = deepcopy(authority), deepcopy(curriculum)
        self.policy_sha, self.curriculum_sha = expected_authority_sha256, expected_curriculum_sha256
        self.root, self.capture_root = Path(checked['root']), Path(checked['capture_root'])
        self.child, self.stream, self.journal, self.executor = child, stream, journal, executor
        self.anchors = anchors
        self.fit_limits = fit.Limits(**authority['fit_limits'])
        self.reader_limits = capture.Limits(**authority['reader_limits'])
        self.phase, self.index, self.prior = 'READY', 0, None
        self.pending = None
        self.remaining_output = curriculum['max_output_bytes']
        self.control = self.root/'guided_cycles'
        self._bindings()
        require(isinstance(journal, journal_module.StreamJournal) and isinstance(stream, stream_module.ContinualStream)
                and journal.root == self.root/'stream', 'same_owned_native_journal_and_stream')
        require(stream.pending is None and not stream.rows and not stream.sleep_receipts
                and stream.sleep_frontier == 0, 'new_fork_birth_only_no_resume_or_raw_history')
        require(executor.snapshot() == authority['initializer']['state']
                and executor.verify_checkpoint(authority['initializer']['commit']) == authority['initializer']['state'],
                'resident_admitted_common_initializer')
        self.parent_checkpoint = deepcopy(authority['initializer']['commit'])
        self.parent_state = deepcopy(authority['initializer']['state'])
        self._stream_boundary()
        require(not self.control.exists() and not self.capture_root.exists(), 'create_only_cycle_custody_no_retry')
        with gym.console._directory(self.capture_root.parent) as directory:
            os.mkdir(self.capture_root.name, mode=0o700, dir_fd=directory)
            os.fsync(directory)
        with gym.console._directory(self.root) as directory:
            os.mkdir(self.control.name, mode=0o700, dir_fd=directory)
            os.fsync(directory)
        self._write(self.control/'STARTED.json', dict(schema=SCHEMA, authority_sha256=self.policy_sha,
            curriculum_sha256=self.curriculum_sha, curriculum=self.curriculum, pid=os.getpid(),
            synthetic_fixture=authority['execution_kind'] == 'CPU_TEST_ONLY', scientific_claim=False))

    def _reader(self):
        return capture.Reader(self.reader_limits)

    def _write(self, path, document):
        size = len(capture.encoded(document))
        require(size <= self.remaining_output, 'cycle_output_budget')
        self.remaining_output -= size
        gym.write(path, document)
        with gym.console._directory(path.parent) as directory:
            os.fsync(directory)
        return dict(path=str(path), sha256=gym.sha(path))

    def _bindings(self):
        reader = self._reader()
        fit.verify_authority(self.authority, self.policy_sha, reader=reader)
        require(capture.decode(reader.read(self.root/'AUTHORITY.json')[0]) == self.authority,
                'existing_fork_authority_exact')
        pins = self.authority['source_pins']
        required = {*source_paths(), Path(inspect.getfile(type(self.child))).resolve()}
        require(all(str(path) in pins for path in required), 'cycle_and_child_source_closure_pins')
        plan = capture.decode(fit._ref(reader, self.curriculum['plan']))
        require(plan == self.child.plan and plan['root'] == str(self.root)
                and plan['matched_arm'] == self.root.name, 'same_pinned_child_plan')
        variant = plan.get('presleep_variant', 'free_distillation')
        require(variant in ('free_distillation', 'no_distillation'), 'original_native_presleep_variant')
        require(variant == 'no_distillation' or type(plan.get('compaction_invitation')) is str
                and bool(plan['compaction_invitation'].strip()), 'original_compaction_invitation')
        require(getattr(self.executor, 'child', None) is self.child
                and self.executor.contract == fit.CONTRACT
                and self.executor.execution_kind == self.authority['execution_kind'], 'same_child_executor')
        require(self.stream.experiment == getattr(self.child, 'experiment', None), 'same_stream_model_experiment')
        require(self.executor.fork_binding == dict(fork_root=str(self.root), mode=self.authority['mode'],
                authority_sha256=self.policy_sha,
                initializer_commit_sha256=self.authority['initializer']['commit']['sha256']), 'executor_policy_binding')
        require(self.stream.context_limit == plan['context_limit'] == self.authority['context_limit']
                and self.stream.segment_tokens == plan['segment_tokens']
                and self.stream.segments_per_sleep == plan['segments_per_sleep'] == 2,
                'two_segment_original_context_and_budget')
        require(time.time() < self.curriculum['hard_end_unix'] == plan['hard_end_unix'] == self.stream.deadline_unix,
                'same_unexpired_assigned_wall_no_extension')
        fit._implementation(self.executor, pins)
        fit._implementation(self.child.tokenizer, pins)
        require(fit.implementation_name(self.executor) == self.authority['executor_class']
                and fit.implementation_name(self.child.tokenizer) == self.authority['tokenizer_class'],
                'exact_authorized_executor_and_tokenizer_class')
        require(fit.fingerprint_tokenizer(self.child.tokenizer) == self.authority['tokenizer_sha256']
                and fit.digest(fit.anchor_document(self.anchors)) == self.authority['anchors_sha256'],
                'unchanged_tokenizer_and_full_anchor_inventory')
        expected_presentation = (dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
            birth_prompt=plan['birth_prompt']) if plan.get('presentation_version') else None)
        require(self.stream.presentation == expected_presentation, 'original_native_presentation')
        prompts = self.stream.presentation or self.stream.history.checkpoint()
        require(all(prompts[key] == plan[key] for key in ('system_prompt', 'birth_prompt')), 'original_native_prompts')

    def _stream_boundary(self):
        require(self.stream.pending is None and self.journal.latest_checkpoint()['document'] == self.stream.checkpoint(),
                'exact_clean_owned_journal_state')
        document = capture.decode(fit._ref(self._reader(), self.parent_checkpoint))
        require(self.stream.model_state_sha256 == fit.digest(document['checkpoint_sha256']),
                'stream_generating_parent_checkpoint')
        return document

    def _fail(self, error):
        self.phase = 'FAILED'
        try:
            self._write(self.control/f'FAILED{self.index:04d}.json', dict(error_type=type(error).__name__,
                retry_allowed=False, uncertain=True, batch_index=self.index, scientific_claim=False))
        except BaseException:
            pass

    def _incoming(self):
        incoming = self.journal.read_inbox()
        require(self.root.name != 'unparented_learning' or all(event.actor != 'parent' for event in incoming),
                'unparented_inbox_contamination')
        return incoming

    def _generate(self):
        require(time.time() < self.curriculum['hard_end_unix'] and self.stream.pending is None,
                'clean_generation_within_wall')
        incoming = self._incoming()
        records = []

        def record(kind, document):
            receipt = self.journal.record(kind, document)
            records.append((kind, receipt))
            return receipt

        self.stream.step(self.child.generate, self.child.count_tokens, record, incoming=incoming, now=time.time)
        require([kind for kind, unused in records] == ['REQUEST', 'RESPONSE', 'COMMITTED'],
                'one_actual_committed_child_generation')
        return records[1][1]['index']

    def collect_next(self):
        require(self.phase == 'READY' and self.index < len(self.curriculum['tasks']), 'cycle_not_ready')
        self._bindings()
        require(self.executor.snapshot() == self.parent_state, 'no_learning_or_rng_drift_between_rounds')
        self._stream_boundary()
        require(self.stream.sleep_frontier == len(self.stream.rows), 'prior_cycle_published_before_generation')
        task = self.curriculum['tasks'][self.index]
        directory = self.control/f'cycle{self.index:04d}'
        self.phase = 'COLLECTING'
        try:
            directory.mkdir(mode=0o700)
            self._write(directory/'INTENT.json', dict(task=task, curriculum_sha256=self.curriculum_sha,
                parent_checkpoint=self.parent_checkpoint, parent_state_sha256=fit.digest(self.parent_state),
                previous_fit_commit_sha256=self.prior['sha256'] if self.prior else None, replay_allowed=False))
            unused_source, unused_entry, binding = gym.dataset(task['task_index'])
            require(binding == self.authority['generator_binding'], 'actual_installed_TRAIN_generator_authority')
            offered = gym.offer(self.root, task['task_index'])
            self._write(directory/'OFFER.json', offered)
            if task['guidance'] is not None:
                publication = gym.console.publish_parent(self.root, **task['guidance'])
                self._write(directory/'GUIDANCE_PUBLICATION.json', publication)
            answer = self._generate()
            checked_answer = gym.check(self.root, task['task_index'], answer)
            self._write(directory/'ANSWER_CHECK.json', checked_answer)
            followup = self._generate()
            checked_followup = gym.check(self.root, task['task_index'], followup)
            self._write(directory/'FOLLOWUP_CHECK.json', checked_followup)
            require(self.stream.sleep_due and self.stream.pending is None, 'completed_native_sleep_boundary')
            presleep_journal = SimpleNamespace(record=self.journal.record, read_inbox=self._incoming)
            fit.native.prepare_sleep(self.child, self.stream, presleep_journal, self.index+1)
            bundles, references, unavailable = [], [], []
            indices = dict(answer=answer, followup=followup)
            checks = dict(answer=checked_answer, followup=checked_followup)
            for number, spec in enumerate(self.curriculum['capture_specs']):
                dependencies = [spec['response']] if spec['target_kind'] == 'ANSWER' else ['answer']
                if spec['feedback']:
                    dependencies.append('answer')
                if any(checks[name]['status'] != 'CHECKED' for name in dependencies):
                    unavailable.append(dict(spec=spec, reason='NO_ACTUAL_CHECK_FOR_CAPTURE'))
                    continue
                options = dict(target_kind=spec['target_kind'], label=spec['label'],
                    generator_binding=self.authority['generator_binding'], excluded_task_ids=self.authority['excluded_task_ids'],
                    limits=self.reader_limits)
                if spec['target_kind'] == 'POST_FEEDBACK_REFLECTION':
                    options['anchor_response_index'] = answer
                if spec['feedback']:
                    options['feedback_response_index'] = answer
                bundle = capture.assemble(self.root, task['task_index'], indices[spec['response']], **options)
                reserved = 2*sum(len(artifact['raw']) for artifact in bundle['artifacts'].values()) + 65536
                reserved += len(capture.encoded(bundle['review_template']))
                require(reserved <= self.remaining_output, 'capture_and_cycle_output_budget')
                self.remaining_output -= reserved
                references.append(capture.write_capture(bundle, self.capture_root/f'cycle{self.index:04d}_packet{number}'))
                bundles.append(bundle)
            generation_root = self.root/'generation_boundaries'
            if self.index == 0:
                generation_root.mkdir(mode=0o700)
            start_state = self.executor.snapshot()
            require(all(start_state[key] == value for key, value in self.parent_state.items() if key != 'rng_sha256'),
                    'generation_changes_rng_not_learning_state')
            start = self.executor.checkpoint(generation_root/f'cycle{self.index:04d}')
            require(self.executor.verify_checkpoint(start) == start_state and self.executor.snapshot() == start_state,
                    'saved_actual_postgeneration_state')
            self.pending = dict(bundles=bundles, checkpoint=start, state=start_state,
                stream=self.stream.checkpoint(), answer_index=answer, followup_index=followup)
            receipt = dict(schema=SCHEMA, status='AWAITING_EXTERNAL_REVIEWS_AND_MAIN_AUTHORITY',
                task_index=task['task_index'], answer_response_index=answer, followup_response_index=followup,
                answer_check=checked_answer, followup_check=checked_followup, captures=references,
                unavailable=unavailable, parent_checkpoint=self.parent_checkpoint,
                fit_start_checkpoint=start, fit_start_state=start_state, eligible=False,
                presleep_variant=self.child.plan.get('presleep_variant', 'free_distillation'),
                pending_raw_rows=len(self.stream.pending_rows()),
                scientific_claim=False, synthetic_fixture=self.authority['execution_kind'] == 'CPU_TEST_ONLY')
            self._write(directory/'CAPTURED.json', receipt)
            self.phase = 'AWAITING_REVIEW'
            return deepcopy(receipt)
        except BaseException as error:
            self._fail(error)
            raise

    def fit_pending(self, new_candidates, replay_candidates, *, batch_authorization,
                    expected_batch_authorization_sha256):
        require(self.phase == 'AWAITING_REVIEW', 'no_pending_review_boundary')
        self._bindings()
        require(self.stream.checkpoint() == self.pending['stream']
                and self.journal.latest_checkpoint()['document'] == self.pending['stream']
                and self.executor.snapshot() == self.pending['state'], 'paused_learner_exact_state')
        require(type(new_candidates) is list and all(type(candidate) is dict
                and set(candidate) == {'packet', 'reviews'} and any(candidate['packet'] == bundle['packet']
                    for bundle in self.pending['bundles']) for candidate in new_candidates),
                'only_this_cycles_original_captures_as_NEW')
        require(batch_authorization['fit_start_checkpoint'] == self.pending['checkpoint']
                and batch_authorization['fit_start_state'] == self.pending['state'], 'actual_saved_fit_start_authority')
        options = dict(authority=self.authority, expected_authority_sha256=self.policy_sha,
            batch_index=self.index, previous_commit_sha256=self.prior['sha256'] if self.prior else None,
            tokenizer=self.child.tokenizer, anchors=self.anchors, limits=self.fit_limits,
            batch_authorization=batch_authorization,
            expected_batch_authorization_sha256=expected_batch_authorization_sha256)
        batches, unused_preflight = fit.prepare_fit(new_candidates, replay_candidates, reader=self._reader(), **options)
        require(self.authority['mode'] == 'frozen' or batches or self.stream.presentation is not None,
                'native_zero_update_boundary_requires_presentation')
        self.phase = 'FITTING'
        try:
            pending = self.stream.checkpoint()
            pending['state']['pending'] = 'sleep:'+fit.digest([row['source_sha256'] for row in self.stream.pending_rows()])
            pending['sha256'] = fit.digest(pending['state'])
            self.journal.record('SLEEP_REQUEST', dict(cycle=self.index+1, resume_state=pending))
            result = fit.fit_batch(new_candidates, replay_candidates, executor=self.executor, reader=self._reader(), **options)
            commit = result['commit']
            checkpoint = capture.decode(fit._ref(self._reader(), commit['checkpoint']))
            receipt = dict(status='COMPLETE', cycle=self.index+1, optimizer_steps=commit['updates'],
                total_optimizer_steps=commit['after_state']['optimizer_steps'],
                new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
                checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'],
                reviewed_fit_commit=dict(path=result['path'], sha256=result['sha256']), raw_rows_modified=False,
                anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION',
                presentations=commit['presentations'], child_token_exposures=commit['child_token_exposures'],
                anchor_token_exposures=commit['anchor_token_exposures'])
            if self.authority['mode'] == 'frozen':
                receipt['no_update_reason'] = 'frozen_control'
                self.journal.commit_frozen(self.stream, receipt)
            elif not commit['updates']:
                receipt['no_update_reason'] = 'no_eligible_child_rows'
                self.stream.commit_sleep(receipt, self.journal.record)
            else:
                self.stream.commit_sleep(receipt, self.journal.record)
            self.parent_checkpoint, self.parent_state = deepcopy(commit['checkpoint']), deepcopy(commit['after_state'])
            self._stream_boundary()
            self._write(self.control/f'cycle{self.index:04d}'/'COMPLETE.json', dict(schema=SCHEMA,
                fit_commit=receipt['reviewed_fit_commit'], stream_sha256=self.stream.checkpoint()['sha256'],
                updates=commit['updates'], training_performed=commit['training_performed'], scientific_claim=False))
            self.prior, self.pending = result, None
            self.index += 1
            self.phase = 'READY' if self.index < len(self.curriculum['tasks']) else 'COMPLETE'
            return deepcopy(result)
        except BaseException as error:
            self._fail(error)
            raise
