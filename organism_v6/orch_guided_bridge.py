"""Preparation-only CPU contracts; no model loading, task generation or launch.

Hashes establish consistency, not native actor authentication or qualification.
The caller must observe loaded weights, admit child records, and implement the
existing tokenizer/mask protocol in a separately authorized native process.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path

from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


ARMS = ('GUIDED+SLEEP', 'GUIDED+FROZEN', 'UNPARENTED+SLEEP')
FAMILY = 'ROUTE_GUIDED_CYCLES_L2_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def document_sha256(document):
    return sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def valid_hash(value):
    return type(value) is str and len(value) == 64 and all(char in '0123456789abcdef' for char in value)


def file_sha256(path):
    digest = sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_path(value):
    require(type(value) is str and Path(value).is_absolute()
            and str(Path(value).resolve()) == value, 'canonical_absolute_path_required')
    return Path(value)


@dataclass(frozen=True)
class AdapterIdentity:
    path: str
    state_sha256: str
    base_sha256: str
    files: tuple

    def verify(self):
        root = canonical_path(self.path)
        require(valid_hash(self.state_sha256) and valid_hash(self.base_sha256), 'state_and_base_hash_required')
        require(type(self.files) is tuple and bool(self.files), 'immutable_adapter_manifest_required')
        names = []
        for entry in self.files:
            require(type(entry) is tuple and len(entry) == 2, 'immutable_file_entry_required')
            name, digest = entry
            require(type(name) is str and name and not Path(name).is_absolute()
                    and '..' not in Path(name).parts and valid_hash(digest), 'safe_adapter_file_required')
            target = root / name
            require(target.is_file() and target.resolve() == target
                    and target.resolve().is_relative_to(root), 'adapter_file_path_drift')
            require(file_sha256(target) == digest, 'adapter_file_hash_drift')
            names.append(name)
        require(len(names) == len(set(names)), 'duplicate_adapter_file')
        actual = {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}
        require(actual == set(names), 'exact_adapter_manifest_required')
        return self

    def document(self):
        return dict(path=self.path, state_sha256=self.state_sha256,
                    base_sha256=self.base_sha256, files=[list(entry) for entry in self.files])

    @classmethod
    def from_document(cls, document):
        require(set(document) == {'path', 'state_sha256', 'base_sha256', 'files'}, 'exact_adapter_identity_required')
        return cls(document['path'], document['state_sha256'], document['base_sha256'],
                   tuple(tuple(entry) for entry in document['files'])).verify()


@dataclass(frozen=True)
class ReceiptRef:
    path: str
    sha256: str

    def read(self):
        path = canonical_path(self.path)
        require(valid_hash(self.sha256) and path.is_file(), 'completed_receipt_required')
        raw = path.read_bytes()
        require(sha256(raw).hexdigest() == self.sha256, 'prior_receipt_hash_drift')
        return json.loads(raw)


@dataclass(frozen=True)
class CallerContract:
    new_trajectory_rows: int
    trajectory_presentations: int
    optimizer_lifecycle: str
    recipe_json: str
    family: str = FAMILY
    family_status: str = 'PENDING'

    def manifest(self, arm):
        require(arm in ARMS, 'exact_loop_arm_required')
        require(self.family == FAMILY and self.family_status == 'PENDING', 'preparation_only_pending_family')
        require(self.optimizer_lifecycle == 'RESET_EACH_CYCLE', 'optimizer_restore_not_implemented')
        recipe = json.loads(self.recipe_json)
        require(set(recipe) == {'optimizer', 'optimizer_kwargs', 'learning_rate', 'seed', 'native_protocol_sha256'},
                'explicit_native_recipe_required')
        require(recipe['optimizer'] == 'AdamW' and type(recipe['optimizer_kwargs']) is dict
                and bool(recipe['optimizer_kwargs']) and valid_hash(recipe['native_protocol_sha256'])
                and type(recipe['learning_rate']) in (int, float) and 0 < recipe['learning_rate'] < 1
                and type(recipe['seed']) is int, 'invalid_native_recipe')
        kwargs = recipe['optimizer_kwargs']
        require(set(kwargs) == {'betas', 'eps', 'weight_decay', 'amsgrad', 'foreach', 'fused'},
                'all_adamw_options_must_be_explicit')
        require(type(kwargs['betas']) is list and len(kwargs['betas']) == 2
                and all(type(value) in (int, float) and 0 <= value < 1 for value in kwargs['betas'])
                and all(type(kwargs[name]) is bool for name in ('amsgrad', 'foreach', 'fused'))
                and all(type(kwargs[name]) in (int, float) and math.isfinite(kwargs[name])
                        for name in ('eps', 'weight_decay'))
                and kwargs['eps'] > 0 and kwargs['weight_decay'] >= 0, 'invalid_adamw_options')
        layout = GoalReplayLayout(self.new_trajectory_rows, self.trajectory_presentations)
        frozen = arm == ARMS[1]
        return dict(family=self.family, family_status=self.family_status, launch_authorized=False,
                    recipe=recipe, optimizer_lifecycle='NONE' if frozen else self.optimizer_lifecycle,
                    optimizer_checkpoint=None, zero_yield='STOP_WITHOUT_FABRICATED_ROWS',
                    declared_layout=layout.manifest('FULL_TARGET'),
                    executed_updates=0 if frozen else layout.updates,
                    executed_new_presentations=0 if frozen else self.new_trajectory_rows * self.trajectory_presentations,
                    actual_token_equality_claim=False)


@dataclass(frozen=True)
class ArmLineage:
    run_id: str
    arm: str
    output_root: str
    initial: AdapterIdentity
    receipts: tuple = ()


@dataclass(frozen=True)
class StageBinding:
    run_id: str
    arm: str
    cycle: int
    phase: str
    adapter: AdapterIdentity
    parent_present: bool
    fresh_process: bool
    plan_sha256: str
    receipt_refs: tuple = ()

    def verify_loaded(self, *, adapter, base_sha256, parent_present, fresh_process,
                      transient_context, sleep_prompt):
        for reference in self.receipt_refs:
            reference.read()
        self.adapter.verify()
        adapter.verify()
        require(adapter == self.adapter, 'loaded_adapter_state_path_or_files_drift')
        require(base_sha256 == self.adapter.base_sha256, 'frozen_base_identity_drift')
        require(type(parent_present) is bool and parent_present == self.parent_present, 'parent_visibility_drift')
        require(type(fresh_process) is bool and (fresh_process or not self.fresh_process), 'fresh_readout_required')
        if self.phase == 'sealed_readout':
            require(transient_context == () and sleep_prompt is None, 'clean_readout_context_required')


@dataclass(frozen=True)
class CyclePlan:
    lineage: ArmLineage
    contract: CallerContract
    cycle: int
    input_adapter: AdapterIdentity

    def document(self):
        return dict(schema='ORCH_GUIDED_BRIDGE_PLAN_V1', run_id=self.lineage.run_id,
                    arm=self.lineage.arm, cycle=self.cycle, output_root=self.lineage.output_root,
                    initial=self.lineage.initial.document(),
                    input_adapter=self.input_adapter.document(), output_path=self.output_path,
                    prior_receipts=[asdict(receipt) for receipt in self.lineage.receipts],
                    contract=self.contract.manifest(self.lineage.arm))

    @property
    def output_path(self):
        if self.lineage.arm == ARMS[1]:
            return self.lineage.initial.path
        return str(Path(self.lineage.output_root) / self.lineage.run_id / self.lineage.arm
                   / ('cycle-' + str(self.cycle)) / 'adapter')

    def binding(self, phase):
        require(self == plan_cycle(self.lineage, self.contract), 'stale_or_forged_plan')
        require(phase in ('collection', 'training'), 'collection_or_training_phase_required')
        require(phase != 'training' or self.lineage.arm != ARMS[1], 'frozen_training_forbidden')
        return StageBinding(self.lineage.run_id, self.lineage.arm, self.cycle, phase,
                            self.input_adapter, phase == 'collection' and self.lineage.arm != ARMS[2],
                            False, document_sha256(self.document()), self.lineage.receipts)


def _completed_output(plan, reference, seen):
    expected_receipt = Path(plan.lineage.output_root) / plan.lineage.run_id / plan.lineage.arm / ('cycle-' + str(plan.cycle)) / 'COMPLETE.json'
    require(reference.path == str(expected_receipt), 'own_arm_cycle_receipt_path_required')
    receipt = reference.read()
    require(set(receipt) == {'schema', 'status', 'plan_sha256', 'run_id', 'arm', 'cycle',
                             'input_adapter', 'output_adapter', 'contract'}, 'exact_completion_receipt_required')
    require(receipt['schema'] == 'ORCH_GUIDED_BRIDGE_COMPLETION_V1' and receipt['status'] == 'COMPLETE',
            'incomplete_or_foreign_receipt')
    require(receipt['run_id'] == plan.lineage.run_id and receipt['arm'] == plan.lineage.arm
            and type(receipt['cycle']) is int and receipt['cycle'] == plan.cycle, 'same_arm_monotone_cycle_required')
    require(receipt['plan_sha256'] == document_sha256(plan.document()), 'completion_plan_drift')
    require(receipt['input_adapter'] == plan.input_adapter.document(), 'completion_input_drift')
    require(receipt['contract'] == plan.contract.manifest(plan.lineage.arm), 'completion_dose_or_optimizer_drift')
    output = AdapterIdentity.from_document(receipt['output_adapter'])
    require(output.base_sha256 == plan.lineage.initial.base_sha256, 'frozen_base_identity_drift')
    require(output.path == plan.output_path, 'own_arm_cycle_output_path_required')
    if plan.lineage.arm == ARMS[1]:
        require(output == plan.lineage.initial, 'frozen_weights_must_remain_initial')
    else:
        require(output.state_sha256 not in {adapter.state_sha256 for adapter in seen}
                and output.files not in {adapter.files for adapter in seen}, 'sleep_reset_or_stale_weights')
    return output


def plan_cycle(lineage, contract):
    require(lineage.arm in ARMS, 'exact_loop_arm_required')
    require(type(lineage.run_id) is str and bool(lineage.run_id)
            and all(char.isalnum() or char in '-_' for char in lineage.run_id), 'safe_run_id_required')
    canonical_path(lineage.output_root)
    require(type(lineage.receipts) is tuple and len(lineage.receipts) < 3, 'three_cycles_only')
    contract.manifest(lineage.arm)
    current = lineage.initial.verify()
    seen = [current]
    for index, reference in enumerate(lineage.receipts):
        prefix = ArmLineage(lineage.run_id, lineage.arm, lineage.output_root, lineage.initial, lineage.receipts[:index])
        prior = CyclePlan(prefix, contract, index + 1, current)
        current = _completed_output(prior, reference, seen)
        seen.append(current)
    return CyclePlan(lineage, contract, len(lineage.receipts) + 1, current)


def complete_cycle(plan, reference):
    require(plan == plan_cycle(plan.lineage, plan.contract), 'stale_or_forged_plan')
    seen = [plan.lineage.initial]
    seen.extend(AdapterIdentity.from_document(receipt.read()['output_adapter']) for receipt in plan.lineage.receipts)
    output = _completed_output(plan, reference, seen)
    lineage = ArmLineage(plan.lineage.run_id, plan.lineage.arm, plan.lineage.output_root,
                         plan.lineage.initial, plan.lineage.receipts + (reference,))
    readout = StageBinding(lineage.run_id, lineage.arm, plan.cycle, 'sealed_readout', output,
                           False, True, document_sha256(plan.document()), lineage.receipts)
    return lineage, readout


def initial_readout(lineage, contract):
    require(not lineage.receipts, 'initial_readout_before_cycles_only')
    plan = plan_cycle(lineage, contract)
    return StageBinding(lineage.run_id, lineage.arm, 0, 'sealed_readout', lineage.initial,
                        False, True, document_sha256(plan.document()))


def project_child_capture(capture, expected_sha256, binding, *, private_guidance):
    """Copy recorded public prefix and exact child bytes; reject, never scrub.

The caller supplies complete private-guidance strings and authenticates native
capture/admission upstream. Hashes and declared origins alone cannot do that.
"""
    require(binding.phase == 'collection', 'collection_binding_required')
    binding.adapter.verify()
    require(document_sha256(capture) == expected_sha256, 'child_capture_hash_drift')
    require(capture['run_id'] == binding.run_id and capture['arm'] == binding.arm
            and type(capture['cycle']) is int and capture['cycle'] == binding.cycle
            and capture['actor'] == binding.adapter.document(), 'own_cycle_child_capture_required')
    require(capture['origin'] in ('ACTUAL_CHILD_OUTPUT', 'CHILD_PRODUCED_RECORD')
            and capture['complete'] is True and capture['admitted'] is True
            and capture['error'] is None, 'admitted_complete_child_capture_required')
    require(type(private_guidance) is tuple and all(type(text) is str and text for text in private_guidance),
            'explicit_private_guidance_required')
    require(bool(private_guidance) == binding.parent_present, 'guidance_inventory_visibility_drift')
    prefix, target = capture['student_prefix'], capture['response']['raw']
    require(type(prefix) is list and len(prefix) >= 2 and len(prefix) % 2 == 0, 'public_prefix_required')
    require([message['role'] for message in prefix] == ['system', 'user']
            + ['assistant', 'user'] * ((len(prefix) - 2) // 2), 'public_prefix_roles_required')
    require(type(target) is str and bool(target), 'actual_nonempty_child_bytes_required')
    forbidden = private_guidance + ('PARENT PROCEDURAL GUIDANCE',)
    for text in [message['content'] for message in prefix] + [target]:
        require(type(text) is str and all(guidance not in text for guidance in forbidden), 'parent_text_in_student_data')
    return dict(prefix=[dict(role=message['role'], content=message['content']) for message in prefix],
                assistant=target, capture_sha256=expected_sha256, plan_sha256=binding.plan_sha256,
                target_eot='<|im_end|>', loss_policy=dict(prefix='MASK_ALL', assistant='TRAIN',
                                                       eot='TRAIN', suffix='MASK_ALL'))


def validate_encoding_boundary(encoded, *, prefix_ids, target_ids, suffix_ids, eos_token_id, validate_masks):
    """Caller supplies exact untruncated tokenizer roundtrips and existing validator.

This checks token boundaries, not the caller's text-to-token correspondence.
It intentionally does not adapt the frozen 1452-row native encoder.
"""
    require(bool(prefix_ids) and bool(target_ids) and eos_token_id not in target_ids,
            'nonempty_prefix_target_and_separate_eot_required')
    supervised = tuple(target_ids) + (eos_token_id,)
    require(tuple(encoded.input_ids) == tuple(prefix_ids) + supervised + tuple(suffix_ids), 'exact_token_sequence_required')
    require(tuple(encoded.labels) == (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix_ids)
            and tuple(encoded.target_ids) == supervised, 'exact_prefix_target_eot_suffix_masks_required')
    validate_masks((encoded,), eos_token_id)
