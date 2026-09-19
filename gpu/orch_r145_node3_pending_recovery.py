"""Local-testable exact renewed5/6 recovery core, NOT an admission adapter.

No CLI, subprocess, transport, model construction or standalone GPU launcher.
Raw evidence, the original admission adapter and actual runtime/probe gates are
still required for any eventual execution. Local tests use synthetic children.
"""

import ast
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import time
import textwrap

from gpu import orch_r145_node3_capacity_recovery as capacity


SCHEMA = 'R145_RENEWED_NODE3_PENDING_CORE_V1'
SUMMARY_SHA = 'd66d437efcd52ffdc17532b5267d3931b0fbc971c896d70888408552674452cb'
INVENTORY_SHA = 'b629e7ca3e2b15e664a2fd3cc54ff5d8b37c57b00ab55ff0a37a6c23390f6548'
ORIGIN = Path('/localhome/local-rohing')
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
CAPTURE_BINDINGS = {5: '6e6aba4319ca372e138000f52fc8445a2e9c452d18022c3c589cd249b19fadbd',
                    6: '8a6bc97be5559df5a77b9ff3e0358cb35154ab6a8e0a6a68aab29bdb3857130a'}
EXPECTED_REPLACEMENT_UPDATES = {5: 64, 6: 58}
require = capacity.require
digest = capacity.digest


@dataclass(frozen=True)
class CapturedLane:
    physical: int
    summary_json: str
    inventory_json: str

    @property
    def spec(self):
        return deepcopy(capacity.LANES[self.physical])

    @property
    def summary(self):
        return json.loads(self.summary_json)

    @property
    def inventory(self):
        return json.loads(self.inventory_json)

    @property
    def root(self):
        return Path(self.inventory['root'])

    @property
    def checkpoint(self):
        return self.inventory['exited_suffix_from_last_sleep'][0]['metadata']['checkpoint']

    @property
    def eligibility(self):
        return next(item['metadata'] for item in self.summary['suffix'] if item['kind'] == 'TARGET_ELIGIBILITY')

    @property
    def expected_sources(self):
        eligibility = self.eligibility
        return eligibility['new_row_sha256'] * 16 + eligibility['rehearsal_row_sha256']

    @property
    def binding(self):
        return digest(dict(schema=SCHEMA, physical=self.physical, summary=self.summary, inventory=self.inventory))


def load_lane(physical, summary_path, inventory_path):
    require(type(physical) is int and physical in capacity.LANES, 'only_exact_physical5_6')
    require(capacity.file_sha(summary_path) == SUMMARY_SHA, 'immutable_compact_summary_file_pin')
    require(capacity.file_sha(inventory_path) == INVENTORY_SHA, 'immutable_inventory_file_pin')
    summaries = [item for item in json.loads(Path(summary_path).read_text()) if item['physical'] == physical]
    inventories = [item for item in json.loads(Path(inventory_path).read_text())['lanes'] if item['physical'] == physical]
    require(len(summaries) == len(inventories) == 1, 'one_exact_capture_per_lane')
    lane = CapturedLane(physical, json.dumps(summaries[0], sort_keys=True), json.dumps(inventories[0], sort_keys=True))
    validate_capture(lane)
    return lane


def validate_capture(lane):
    require(type(lane.physical) is int and lane.physical in CAPTURE_BINDINGS
            and lane.binding == CAPTURE_BINDINGS[lane.physical], 'exact_lane_capture_binding')
    spec, summary, inventory, saved = lane.spec, lane.summary, lane.inventory, lane.checkpoint
    capacity.owned_plan(dict(physical=lane.physical, gpu_uuid=inventory['gpu_uuid'], root=str(lane.root)))
    require(inventory['minor'] == lane.physical and inventory['live'] is False
            and inventory['exit_receipt']['exit_code'] == 1, 'captured_failed_owned_lane_not_liveness_claim')
    require(summary['saved_cycle'] == spec['saved_cycle'] and summary['saved_steps'] == spec['saved_steps']
            and summary['commit_sha256'] == spec['commit_sha256'], 'exact_renewed_saved_state')
    directory = lane.root / 'checkpoints' / f"sleep_{spec['saved_cycle']:06d}"
    require(summary['commit_path'] == str(directory / 'COMMIT.json')
            and saved['adapter_path'] == str(directory / 'adapter')
            and saved['optimizer_rng_path'] == str(directory / 'optimizer_rng.pt')
            and saved['optimizer_steps'] == spec['saved_steps'] and saved['base_sha256'] == BASE_SHA,
            'same_saved_adapter_optimizer_base_paths')
    hashes = saved['checkpoint_sha256']
    require(set(hashes) == {'adapter', 'optimizer', 'rng'} and hashes['adapter'] == digest(saved['adapter_files'])
            and hashes['optimizer'] == hashes['rng'], 'checkpoint_metadata_internal_hash_bindings')
    suffix = summary['suffix']
    require([int(Path(item['path']).stem) for item in suffix] == list(range(spec['start'], spec['end'])),
            'exact_contiguous_suffix_indices')
    kinds = ['SLEEP_COMPLETE'] + (['LOADED'] if lane.physical == 5 else []) + [
        'INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED', 'REQUEST', 'RESPONSE', 'COMMITTED',
        'SLEEP_REQUEST', 'TARGET_ELIGIBILITY', 'UPDATE']
    require([item['kind'] for item in suffix] == kinds, 'exact_renewed_suffix_kind_sequence')
    for item, other in zip(suffix, inventory['exited_suffix_from_last_sleep'], strict=True):
        require(item['path'] == str(lane.root / 'stream' / 'records' / Path(item['path']).name)
                and item['path'] == other['path'] and item['kind'] == other['kind']
                and item['sha256'] == other['sha256'], 'capture_sources_agree_on_raw_file_hashes')
    require(inventory['journal_head'] == {key: suffix[-1][key] for key in ('path', 'kind', 'sha256')},
            'captured_external_head_binding')
    require(suffix[-1]['metadata']['optimizer_step'] == spec['saved_steps'] + 1
            and suffix[-1]['metadata']['source_sha256'] == lane.eligibility['new_row_sha256'][0],
            'one_abandoned_unsaved_update')
    require(len(lane.eligibility['new_row_sha256']) == 2
            and len(lane.eligibility['rehearsal_row_sha256']) == 2 * spec['saved_cycle']
            and len(lane.expected_sources) == EXPECTED_REPLACEMENT_UPDATES[lane.physical], 'unchanged_16_new_1_rehearsal')
    require(inventory['old_native_sha256'] == capacity.NATIVE_SHA
            and inventory['source_pins']['gpu/orch_r125_continual_native.py'] == capacity.NATIVE_SHA
            and inventory['source_pins']['gpu/orch_r133_node3_programmes.py'] == capacity.LAUNCHER_SHA,
            'original_native_launcher_pins')
    return dict(physical=lane.physical, binding=lane.binding, saved_cycle=spec['saved_cycle'],
                saved_steps=spec['saved_steps'], pending_cycle=spec['saved_cycle'] + 1,
                replacement_updates=len(lane.expected_sources), prospective_total=spec['saved_steps'] + len(lane.expected_sources),
                matched_suffix_file_pins=len(suffix), raw_chain_verified=False, runtime_verified=False,
                admission_performed=False, launch_performed=False, checkpoint_payloads_verified=False)


class LocalCaptureStore:
    """Explicit offline relocation, never fallback to a live absolute path."""

    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        require('..' not in self.directory.parts, 'no_capture_directory_traversal')
        self.path(ORIGIN)

    def path(self, original):
        original = Path(original)
        require(original.is_absolute() and '..' not in original.parts and original.is_relative_to(ORIGIN),
                'only_canonical_captured_origin')
        destination = self.directory / original.relative_to(ORIGIN)
        require(not any(part.is_symlink() for part in (destination, *destination.parents)), 'no_capture_symlink')
        return destination

    def raw(self, original, expected=None):
        path = self.path(original)
        require(path.is_file(), 'missing_raw_capture:' + str(original))
        value = path.read_bytes()
        if expected is not None:
            require(hashlib.sha256(value).hexdigest() == expected, 'captured_raw_file_hash:' + str(original))
        return value


def verify_saved_files(lane, store):
    checkpoint = lane.checkpoint
    commit = json.loads(store.raw(lane.summary['commit_path'], lane.summary['commit_sha256']))
    require(commit == checkpoint, 'raw_COMMIT_matches_captured_checkpoint_document')
    directory = store.path(checkpoint['adapter_path'])
    require({path.name for path in directory.iterdir()} == set(checkpoint['adapter_files']), 'exact_saved_adapter_inventory')
    for name, expected in checkpoint['adapter_files'].items():
        require(Path(name).name == name and name not in ('.', '..'), 'adapter_file_basename')
        store.raw(Path(checkpoint['adapter_path']) / name, expected)
    store.raw(checkpoint['optimizer_rng_path'], checkpoint['checkpoint_sha256']['optimizer'])
    return checkpoint


def verify_source_and_plan(lane, store, proposed_plan):
    inventory = lane.inventory
    original = json.loads(store.raw(inventory['plan_path'], inventory['plan_sha256']))
    guard = json.loads(store.raw(inventory['guard_path'], inventory['guard_sha256']))
    require(guard['plan_sha256'] == inventory['plan_sha256'] and guard['source_pins'] == inventory['source_pins'],
            'captured_guard_plan_source_binding')
    source = Path(inventory['source_root'])
    actual = {str(path.relative_to(store.path(source))) for path in store.path(source).rglob('*.py')}
    require(actual == set(inventory['source_pins']), 'complete_original_source_closure')
    for name, expected in inventory['source_pins'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative_source_file')
        store.raw(source / name, expected)
    capacity.owned_plan(proposed_plan)
    proposed_source = Path(proposed_plan['source_root'])
    require(proposed_source.parent == lane.root.parent and proposed_source.name.startswith('source_r145_')
            and proposed_source != source, 'new_isolated_R145_source_only')
    original_native = store.raw(source / 'gpu/orch_r125_continual_native.py', capacity.NATIVE_SHA).decode()
    runtime_path = proposed_source / 'gpu' / capacity.RUNTIME_FILENAME
    runtime_sha = hashlib.sha256(store.raw(runtime_path)).hexdigest()
    prospective_native = store.raw(proposed_source / 'gpu/orch_r125_continual_native.py').decode()
    require(prospective_native == capacity.patch_source(original_native, runtime_sha), 'exact_prospective_child_only_patch')
    for module in (capacity,):
        require(store.raw(proposed_source / 'gpu' / Path(module.__file__).name) == Path(module.__file__).read_bytes(),
                'executing_capacity_helper_exact_source')
    require(store.raw(proposed_source / 'gpu' / Path(__file__).name) == Path(__file__).read_bytes(),
            'executing_pending_wrapper_exact_source')
    normalized = deepcopy(proposed_plan)
    normalized['source_root'] = original['source_root']
    if 'startup_context' in original:
        relative = Path(original['startup_context']['path']).relative_to(source)
        proposed_path = Path(proposed_plan['source_root']) / relative
        require(proposed_plan['startup_context']['path'] == str(proposed_path)
                and store.raw(proposed_path) == store.raw(source / relative), 'same_bytes_startup_relocation_only')
        normalized['startup_context']['path'] = original['startup_context']['path']
    require(normalized == original, 'no_recipe_generation_deadline_parent_changes')
    return original


def verify_child_methods(child, lane, store):
    sources = {'original': store.raw(Path(lane.inventory['source_root']) / 'gpu/orch_r125_continual_native.py').decode(),
               'prospective': store.raw(Path(child.plan['source_root']) / 'gpu/orch_r125_continual_native.py').decode()}
    for name in ('generate', 'checkpoint', 'verify_checkpoint', 'sleep'):
        tree = ast.parse(sources['prospective' if name == 'sleep' else 'original'])
        definition = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'NativeChild')
        method = next(node for node in definition.body if isinstance(node, ast.FunctionDef) and node.name == name)
        current = ast.parse(textwrap.dedent(inspect.getsource(getattr(child, name)))).body[0]
        require(ast.dump(method, include_attributes=False) == ast.dump(current, include_attributes=False),
                'exact_original_generation_and_prospective_sleep:' + name)


def save_raw_once(path, value):
    path = Path(path)
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_archive_symlink')
    with path.open('xb') as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def scan_records(journal):
    state = journal._scan()
    records = [journal._read_json(journal._records_fd, f'{index:020d}.json') for index in range(state['index'])]
    require(records and state['previous'] == records[-1]['sha256'], 'stable_internal_chain_head')
    return state, records


def bind_pending(lane, store, child, stream, journal):
    spec, checkpoint = lane.spec, verify_saved_files(lane, store)
    require(journal.root == store.path(lane.root / 'stream') and child.plan['root'] == str(lane.root), 'same_life_captured_journal')
    state, records = scan_records(journal)
    require(len(records) == spec['end'], 'exact_original_record_count_no_appended_retry')
    for item in lane.summary['suffix']:
        raw = store.raw(item['path'], item['sha256'])
        index = int(Path(item['path']).stem)
        require(json.loads(raw) == records[index] and records[index]['kind'] == item['kind'], 'raw_and_scanned_record_agree')
    require(state['request'] is None and state['response'] is None
            and state['sleep_request'] == {'cycle': spec['saved_cycle'] + 1}
            and state['latest']['document'] == stream.checkpoint(), 'exact_pending_sleep_stream')
    require(len(stream.sleep_receipts) == spec['saved_cycle']
            and stream.sleep_receipts[-1]['checkpoint'] == checkpoint
            and records[spec['start']]['document']['checkpoint'] == checkpoint
            and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']), 'last_durable_checkpoint_only')
    require(child.optimizer_steps == checkpoint['optimizer_steps']
            and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'loaded_saved_not_unsaved_adapter')
    require(child.plan['segment_tokens'] == stream.segment_tokens and child.plan['context_limit'] == stream.context_limit
            and child.plan['hard_end_unix'] == stream.deadline_unix
            and checkpoint.get('experiment') == stream.experiment == getattr(child, 'experiment', None),
            'unchanged_budget_and_experiment')
    presentation = dict(version=child.plan['presentation_version'], system_prompt=child.plan['system_prompt'],
                        birth_prompt=child.plan['birth_prompt'])
    require(stream.presentation == presentation, 'unchanged_presentation')
    rows = stream.pending_rows()
    require(len(rows) == 2 and stream.pending == 'sleep:' + digest([row['source_sha256'] for row in rows]),
            'two_committed_pending_children')
    for row, index in zip(rows, spec['requests'], strict=True):
        request = {key: value for key, value in records[index]['document'].items() if key != 'resume_state'}
        response, commit = records[index + 1]['document'], records[index + 2]['document']
        output = response['response']
        require(request['split'] == row['split'] == 'TRAIN' and row['actor'] == 'child'
                and row['prefix_loss'] is False and row['target_loss'] is True, 'TRAIN_child_replay_only')
        require(request['segment'] == row['segment'] == commit['segment']
                and digest(request) == response['request_sha256']
                and digest(response) == row['source_sha256'] == commit['source_sha256']
                and response['raw_saved_before_validation'] is True, 'request_response_commit_chain')
        require(request['messages'] == row['prefix'] and request['retry_allowed'] is False
                and request['max_new_tokens'] == child.plan['segment_tokens']
                and request['deadline_unix'] == child.plan['hard_end_unix']
                and request['model_state_sha256'] == row['model_state_sha256'] == stream.model_state_sha256,
                'original_generation_request_no_context_change')
        require(output['raw'] == row['target'] and output['token_ids'] == row['token_ids']
                and type(output['terminal']) is bool and output['terminal'] is row['terminal']
                and type(output['truncated']) is bool and output['truncated'] is row['truncated']
                and output['decoder'] == child.plan['decoder'] and output['prompt_tokens'] == request['prompt_tokens']
                and output['adapter_state_sha256'] == checkpoint['adapter_state_sha256']
                and output['base_sha256'] == checkpoint['base_sha256'], 'original_generation_response')
    eligibility = records[spec['eligibility']]['document']
    require(eligibility['excluded'] == [] and eligibility['raw_modified'] is False
            and eligibility['version'] == presentation['version']
            and eligibility['new_row_sha256'] == lane.eligibility['new_row_sha256'] == [row['source_sha256'] for row in rows]
            and eligibility['rehearsal_row_sha256'] == lane.eligibility['rehearsal_row_sha256']
            == [row['source_sha256'] for row in stream.rows[:stream.sleep_frontier]], 'all_original_target_eligibility')
    abandoned = records[spec['abandoned']]['document']
    require(abandoned['optimizer_step'] == spec['saved_steps'] + 1
            and abandoned['source_sha256'] == rows[0]['source_sha256'], 'one_unsaved_historical_update')
    return records


def optimizer_sha(child):
    return digest(capacity.tensor_tree_fingerprint(child.torch, child.optimizer.state_dict()))


def restore_saved(child, lane, store):
    checkpoint = verify_saved_files(lane, store)
    require(isinstance(child.optimizer, child.torch.optim.AdamW), 'original_AdamW')
    require(child.adapter_hash() == checkpoint['adapter_state_sha256']
            and child.optimizer_steps == lane.spec['saved_steps'], 'fresh_saved_adapter_child_required')
    payload = child.torch.load(io.BytesIO(store.raw(checkpoint['optimizer_rng_path'], checkpoint['checkpoint_sha256']['optimizer'])),
                               map_location='cpu', weights_only=False)
    require(payload['parameter_names'] == list(child.parameters)
            and payload['optimizer_steps'] == lane.spec['saved_steps']
            and payload.get('experiment') == checkpoint.get('experiment') == getattr(child, 'experiment', None),
            'saved_parameter_order_steps_experiment')
    child.optimizer.load_state_dict(payload['optimizer'])
    expected = digest(capacity.tensor_tree_fingerprint(child.torch, payload['optimizer']))
    require(optimizer_sha(child) == expected, 'exact_saved_optimizer_restoration')
    state = dict(python=payload['python_rng'], cpu=payload['cpu_rng'], cuda=payload['cuda_rng'])
    capacity.restore_rng(child.torch, state)
    require(capacity.rng_fingerprint(capacity.rng_state(child.torch)) == capacity.rng_fingerprint(state), 'exact_saved_all_RNG')
    child.engine.verify_base()
    return expected


class PendingRecovery:
    """Core state machine. Caller admission/runtime authorization is not supplied here."""

    def __init__(self, lane, store, child, stream, journal, output):
        validate_capture(lane)
        self.lane, self.store, self.child, self.stream, self.journal = lane, store, child, stream, journal
        self.output = Path(output)
        require(self.output.is_absolute() and '..' not in self.output.parts
                and self.output.is_relative_to(store.path(lane.root / 'recoveries'))
                and self.output.name.startswith('r145-'), 'new_owned_recovery_namespace')
        self.phase = 'NEW'
        self.original_records = None
        self.original_files = None
        self.replayed_rng = None
        self.replayed_optimizer = None

    def _failure(self, error):
        self.phase = 'FAILED'
        capacity.save_once(self.output / 'FAILED.json', dict(schema=SCHEMA, binding=self.lane.binding,
            error_type=type(error).__name__, error=str(error), child_must_be_discarded=True,
            retry_allowed=False, failed_unix=time.time()))

    def _files(self):
        return {name: capacity.file_sha(self.journal.root / 'records' / name)
                for index in range(self.lane.spec['end'])
                for name in (f'{index:020d}.json', f'{index:020d}.intent.json')}

    def prepare_and_probe(self, anchors, probe):
        require(self.phase == 'NEW', 'recovery_session_single_use')
        require(not self.output.exists() and not any(parent.is_symlink() for parent in (self.output, *self.output.parents)),
                'new_no_symlink_attempt')
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.mkdir()
        try:
            with self.journal._mutex:
                verify_source_and_plan(self.lane, self.store, self.child.plan)
                verify_child_methods(self.child, self.lane, self.store)
                self.original_records = bind_pending(self.lane, self.store, self.child, self.stream, self.journal)
                self.original_files = self._files()
                capacity.save_once(self.output / 'ORIGINAL_PREFIX_FILE_PINS.json', self.original_files)
                capacity.save_once(self.output / 'CAPTURE_BINDING.json', dict(schema=SCHEMA, binding=self.lane.binding,
                    summary=self.lane.summary, inventory=self.lane.inventory, no_admission_authority=True))
                for item in self.lane.summary['suffix']:
                    origin = Path(item['path'])
                    save_raw_once(self.output / origin.name, self.store.raw(origin, item['sha256']))
                    intent = origin.with_name(origin.stem + '.intent.json')
                    save_raw_once(self.output / intent.name, self.store.raw(intent))
                before_stream = deepcopy(self.stream.checkpoint())
                before_plan = deepcopy(self.child.plan)
                before_anchors = deepcopy(anchors)
                restored_optimizer = restore_saved(self.child, self.lane, self.store)
                restored_rng = capacity.rng_fingerprint(capacity.rng_state(self.child.torch))
                runtime_path = Path(self.child.plan['source_root']) / 'gpu' / capacity.RUNTIME_FILENAME
                runtime_sha = hashlib.sha256(self.store.raw(runtime_path)).hexdigest()
                proof = probe(self.child, self.stream, anchors)
                require(proof['status'] == 'PASS' and proof['state_restored'] is True
                        and proof['schema'] == capacity.SCHEMA and proof['train_only'] is True
                        and proof['exact_learning_trajectory_claim'] is False
                        and proof['runtime_pin_sha256'] == runtime_sha
                        and proof['adapter_sha256'] == self.lane.checkpoint['adapter_state_sha256']
                        and proof['optimizer_sha256'] == restored_optimizer and proof['rng_sha256'] == restored_rng
                        and proof['optimizer_updates'] == 0, 'successful_state_restoring_TRAIN_probe_required')
                require(self.stream.checkpoint() == before_stream and self.child.plan == before_plan and anchors == before_anchors
                        and self._files() == self.original_files and optimizer_sha(self.child) == restored_optimizer
                        and capacity.rng_fingerprint(capacity.rng_state(self.child.torch)) == restored_rng
                        and self.child.adapter_hash() == self.lane.checkpoint['adapter_state_sha256']
                        and self.child.optimizer_steps == self.lane.spec['saved_steps'], 'probe_did_not_mutate_saved_state')
                capacity.save_once(self.output / 'BOUND_PROBE.json', proof)
                restore_saved(self.child, self.lane, self.store)
                bind_pending(self.lane, self.store, self.child, self.stream, self.journal)
                self.phase = 'PROBED'
        except BaseException as error:
            self._failure(error)
            raise

    def replay(self):
        require(self.phase == 'PROBED', 'replay_requires_successful_probe_once')
        try:
            with self.journal._mutex:
                verify_source_and_plan(self.lane, self.store, self.child.plan)
                verify_child_methods(self.child, self.lane, self.store)
                bind_pending(self.lane, self.store, self.child, self.stream, self.journal)
                require(self._files() == self.original_files, 'unchanged_prefix_before_any_replay')
                stream_before, plan_before = deepcopy(self.stream.checkpoint()), deepcopy(self.child.plan)
                restored_optimizer = restore_saved(self.child, self.lane, self.store)
                for number, index in enumerate(self.lane.spec['requests']):
                    require(time.time() < self.child.plan['hard_end_unix'], 'replay_within_original_wall')
                    request = deepcopy(self.original_records[index]['document'])
                    expected = self.original_records[index + 1]['document']['response']
                    messages = deepcopy(request['messages'])
                    response = self.child.generate(messages, max_new_tokens=request['max_new_tokens'],
                                                   deadline_unix=request['deadline_unix'])
                    capacity.save_once(self.output / f'REPLAY_{number}.json', dict(response=response,
                        rng_after=capacity.rng_fingerprint(capacity.rng_state(self.child.torch))))
                    require(digest(response) == digest(expected), 'exact_generation_response:' + str(number))
                    require(messages == request['messages'] and self.stream.checkpoint() == stream_before
                            and self.child.plan == plan_before and optimizer_sha(self.child) == restored_optimizer
                            and self.child.optimizer_steps == self.lane.spec['saved_steps']
                            and self.child.adapter_hash() == self.lane.checkpoint['adapter_state_sha256'],
                            'no_replay_plan_history_learning_mutation')
                    self.child.engine.verify_base()
                require(self._files() == self.original_files
                        and bind_pending(self.lane, self.store, self.child, self.stream, self.journal) == self.original_records,
                        'original_pending_journal_preserved_after_replay')
                self.replayed_rng = capacity.rng_fingerprint(capacity.rng_state(self.child.torch))
                self.replayed_optimizer = restored_optimizer
                capacity.save_once(self.output / 'GENERATIONS_VERIFIED.json', dict(schema=SCHEMA, binding=self.lane.binding,
                    matched_generations=2, optimizer_updates=0, historical_abandoned_updates=1,
                    saved_steps=self.lane.spec['saved_steps'], rng_after=self.replayed_rng,
                    missing_original_postgeneration_RNG_not_claimed=True, unavailable_postupdate_weights_not_claimed=True,
                    bitwise_learning_trajectory_claim=False))
                self.phase = 'REPLAYED'
        except BaseException as error:
            self._failure(error)
            raise

    def recompute(self, anchors):
        require(self.phase == 'REPLAYED', 'recompute_requires_two_verified_generations_once')
        try:
            with self.journal._mutex:
                verify_source_and_plan(self.lane, self.store, self.child.plan)
                verify_child_methods(self.child, self.lane, self.store)
                spec = self.lane.spec
                require(capacity.rng_fingerprint(capacity.rng_state(self.child.torch)) == self.replayed_rng
                        and optimizer_sha(self.child) == self.replayed_optimizer, 'no_interposed_RNG_or_optimizer_changes')
                bind_pending(self.lane, self.store, self.child, self.stream, self.journal)
                destination = self.store.path(self.lane.root / 'checkpoints' / f"sleep_{spec['saved_cycle'] + 1:06d}")
                require(not destination.exists(), 'never_overwrite_saved_replacement')
                accounting = dict(schema=SCHEMA, binding=self.lane.binding, attempt=self.output.name,
                    historical_abandoned_updates=1, abandoned_record=spec['abandoned'],
                    abandoned_optimizer_step=spec['saved_steps'] + 1, saved_steps=spec['saved_steps'],
                    replacement_starts_at=spec['saved_steps'] + 1, bitwise_learning_trajectory_claim=False,
                    unavailable_postupdate_weights_not_claimed=True)
                self.journal.record('CHECKPOINT_METADATA', dict(r145_recovery=accounting))
                updates = []
                eligibility_count = 0

                def record(kind, document):
                    nonlocal eligibility_count
                    if kind == 'TARGET_ELIGIBILITY':
                        require(eligibility_count == 0 and not updates
                                and document == self.original_records[spec['eligibility']]['document'],
                                'exact_unchanged_training_eligibility')
                        eligibility_count += 1
                    elif kind == 'UPDATE':
                        position = len(updates)
                        require(eligibility_count == 1 and position < len(self.lane.expected_sources)
                                and document['optimizer_step'] == spec['saved_steps'] + position + 1
                                and document['source_sha256'] == self.lane.expected_sources[position],
                                'exact_replacement_update_step_and_schedule')
                        updates.append(deepcopy(document))
                        document = dict(document, r145_recovery=accounting)
                    else:
                        require(False, 'unexpected_sleep_record_kind')
                    self.journal.record(kind, document)

                self.child.check('r145_recompute_pending_sleep')
                receipt = self.child.sleep(self.stream.pending_rows(), self.stream.rows[:self.stream.sleep_frontier], anchors, record)
                total = spec['saved_steps'] + len(self.lane.expected_sources)
                require(len(updates) == receipt['optimizer_steps'] == len(self.lane.expected_sources)
                        and receipt['total_optimizer_steps'] == self.child.optimizer_steps == total,
                        'complete_exact_recipe_update_count')
                saved = self.child.checkpoint(destination)
                require(saved['optimizer_steps'] == total and saved.get('experiment') == self.stream.experiment,
                        'replacement_checkpoint_steps_and_experiment')
                receipt.update(status='COMPLETE', cycle=spec['saved_cycle'] + 1, checkpoint=saved,
                    checkpoint_sha256=saved['checkpoint_sha256'],
                    new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()], r145_recovery=accounting)
                self.stream.pending = None
                self.stream.commit_sleep(receipt, self.journal.record)
                require(self._files() == self.original_files
                        and scan_records(self.journal)[1][:spec['end']] == self.original_records,
                        'original_history_bytes_preserved_after_replacement')
                verify_saved_files(self.lane, self.store)
                capacity.save_once(self.output / 'SLEEP_RECOMPUTED.json', dict(schema=SCHEMA, accounting=accounting,
                    status='REPLACEMENT_SAVED', cycle=spec['saved_cycle'] + 1, optimizer_steps=total,
                    replacement_updates=len(updates), original_prefix_preserved=True))
                self.phase = 'SAVED'
                return saved
        except BaseException as error:
            self._failure(error)
            raise
