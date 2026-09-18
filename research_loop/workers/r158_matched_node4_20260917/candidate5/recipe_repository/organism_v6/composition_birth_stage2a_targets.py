"""Paired source-only birth prefixes; tokenization and loss masks are absent."""

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
CLARIFICATION_SHA256 = "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9"
SCIENCE_GATES = MappingProxyType({name: False for name in (
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM",
)})


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class TargetUnit:
    unit_id: str
    phase: str
    target_bytes: bytes
    target_sha256: str
    command: str
    operand: str | None
    selection_index: int | None


@dataclass(frozen=True)
class ArmRecord:
    arm: str
    unit: TargetUnit
    prefix: tuple[Message, ...]
    prefix_sha256: str
    content_bytes: int
    serialized_bytes: int

    @property
    def training_messages(self):
        return self.prefix + (Message("assistant", self.unit.target_bytes.decode("ascii")),)

    @property
    def supervised_message_index(self):
        return len(self.prefix)


@dataclass(frozen=True)
class PairedTarget:
    closed: ArmRecord
    atom_local: ArmRecord
    status: str = STATUS


def messages_bytes(messages):
    if type(messages) not in (tuple, list) or any(type(message) is not Message for message in messages):
        raise ValueError("typed_messages_required")
    for message in messages:
        if message.role not in ("system", "user", "assistant") or type(message.role) is not str:
            raise ValueError("invalid_message_role")
    return canonical_json([{"role": message.role, "content": message.content} for message in messages])


def latest_public_task(prefix):
    messages_bytes(prefix)
    if (len(prefix) < 2 or prefix[0] != Message("system", wire.SYSTEM_MESSAGE)
            or prefix[1].role != "user"):
        raise ValueError("system_and_task_required")
    task = wire.parse_task(prefix[1].content)
    current = task.current
    for index, message in enumerate(prefix[2:]):
        if message.role != ("assistant" if index % 2 == 0 else "user"):
            raise ValueError("invalid_prefix_role_sequence")
        if message.role == "assistant":
            wire.parse_action(message.content)
        elif message.content.startswith("WORLD\n"):
            current = wire.parse_world(message.content)
        elif message.content != "ACK" and not message.content.startswith("SERVICE\n"):
            raise ValueError("invalid_host_message")
    if prefix[-1].role != "user":
        raise ValueError("prefix_must_end_before_assistant")
    return wire.TaskState(task.start, task.goal, current)


def _turn_messages(turns):
    messages = []
    for turn in turns:
        messages.append(Message("assistant", turn.action))
        if turn.response:
            messages.append(Message("user", turn.response))
    return tuple(messages)


def _atom_turn_indices(case, target):
    index = target.trace_index
    if target.phase == "CONTINUE":
        return ()
    if target.phase in ("READ_CHECK", "PROSPECT"):
        return (index - 1,)
    if target.phase == "STEP_CHECK":
        return (index - 2, index - 1)
    if target.phase == "SEEK":
        if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH":
            return (index - 3, index - 2, index - 1)
        return (0,)
    raise ValueError("unsupported_target_phase")


def _arm_record(arm, unit, prefix, expected_task):
    if latest_public_task(prefix) != expected_task:
        raise ValueError("prefix_public_state_mismatch")
    raw = messages_bytes(prefix)
    return ArmRecord(arm, unit, prefix, sha256(raw).hexdigest(),
                     sum(len(message.content.encode("ascii")) for message in prefix), len(raw))


def serialize_birth_case(case, *, role_tokens):
    """Bind one shared target per decision to the two exact causal-prefix views."""
    birth.validate_birth_case(case, role_tokens=role_tokens)
    system = Message("system", wire.SYSTEM_MESSAGE)
    pairs = []
    for target in case.targets:
        unit = TargetUnit(f"{case.descriptor.world}/{case.descriptor.member}/u{target.ordinal}",
                          target.phase, target.target_bytes, target.target_sha256,
                          target.command, target.operand, target.selection_index)
        closed = (system, Message("user", case.task_text)) + _turn_messages(case.trace[:target.trace_index])
        indices = _atom_turn_indices(case, target)
        if any(index < 0 or index >= target.trace_index for index in indices):
            raise ValueError("invalid_retained_boundary")
        retained = tuple(case.trace[index] for index in indices)
        current = retained[0].current_before if retained else target.current_before
        task_text = f"TASK\nSTART {case.task.start}\nGOAL {case.task.goal}\nCURRENT {current}"
        atom = (system, Message("user", task_text)) + _turn_messages(retained)
        expected = wire.TaskState(case.task.start, case.task.goal, target.current_before)
        pairs.append(PairedTarget(_arm_record("CLOSED", unit, closed, expected),
                                  _arm_record("ATOM_LOCAL", unit, atom, expected)))
    return tuple(pairs)


def validate_paired_targets(pairs, case, *, role_tokens):
    """Compare exact prospective rendering; not the independent material checker."""
    expected = serialize_birth_case(case, role_tokens=role_tokens)
    if type(pairs) is not tuple or pairs != expected:
        raise ValueError("paired_target_render_mismatch")
    if any(pair.closed.unit is not pair.atom_local.unit for pair in pairs):
        raise ValueError("shared_target_unit_required")
    return True
