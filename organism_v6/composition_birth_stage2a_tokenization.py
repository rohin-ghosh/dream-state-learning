"""Bounded in-memory Stage2A tokenization mechanics, never native qualification.

Only caller-supplied tokenizer interfaces are used; nothing is loaded or written.
The interface supplies encode, decode, apply_chat_template and declared special
IDs. Labels are unshifted causal-LM labels: only final content plus EOS survives.
Exact render and token concatenation must agree, without stripping, truncating,
or inserting EOS. The pinned template's final LF is preserved as a loss-masked
host-template suffix. This is a non-material integration repair based on the
2026-09-13 read-only config receipt, not native-tokenizer validation. Batch widths
must be supplied explicitly: this module does not choose shared versus per-arm
padding or authenticate a tokenizer.
"""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_tape as tape


STATUS = "PARTIAL_SOURCE_ONLY"
MAX_CONTEXT_TOKENS = 16384
BATCH_SIZE = 4
IGNORE_INDEX = -100
TEMPLATE_SUFFIX = "\n"
TEMPLATE_CONFIG_SHA256 = "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583"
TEMPLATE_RECEIPT_SHA256 = "a69112b534e33e7949a5d1747ce810558585b0842bcaf10f212080acca506227"
COUNT_BASES = ("SYNTHETIC_FIXTURE", "UNAUTHENTICATED_CALLER_TOKENIZER")
SCIENCE_GATES = MappingProxyType(dict.fromkeys(targets.SCIENCE_GATES, False))
SPEC_SHA256 = MappingProxyType({
    "v2": "dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74",
    "v3": "da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1",
    "v4": "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1",
    "v5": "6ebefdba31de6f14416105c9509dbba06319f306bdd3472259a8d072ba9877e7",
    "builder": "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9",
})
_IDENTIFIER = re.compile("|".join(wire.IDENTIFIERS.values()))
_UNIT_IDS = frozenset(tape.unit_identifiers())


@dataclass(frozen=True)
class IdentifierTokens:
    identifier: str
    byte_start: int
    byte_end: int
    standalone_ids: tuple[int, ...]
    target_token_indices: tuple[int, ...]
    target_token_ids: tuple[int, ...]


@dataclass(frozen=True)
class TokenizedArm:
    record: targets.ArmRecord
    context_ids: tuple[int, ...]
    target_ids: tuple[int, ...]
    input_ids: tuple[int, ...]
    labels: tuple[int, ...]
    attention_mask: tuple[int, ...]
    context_roundtrip_bytes: bytes
    target_roundtrip_bytes: bytes
    sequence_roundtrip_bytes: bytes
    identifier_tokenization: tuple[IdentifierTokens, ...]
    eos_token_id: int
    pad_token_id: int
    count_basis: str
    suffix_ids: tuple[int, ...]
    suffix_roundtrip_bytes: bytes

    @property
    def target_start(self):
        return len(self.context_ids)

    @property
    def target_end(self):
        return self.target_start + len(self.target_ids)

    @property
    def status(self):
        return STATUS

    @property
    def native_tokenizer_validated(self):
        return False


@dataclass(frozen=True)
class TokenizedPair:
    closed: TokenizedArm
    atom_local: TokenizedArm


@dataclass(frozen=True)
class ArmBatch:
    arm: str
    records: tuple[TokenizedArm, ...]
    input_ids: tuple[tuple[int, ...], ...]
    labels: tuple[tuple[int, ...], ...]
    attention_mask: tuple[tuple[int, ...], ...]
    padding_length: int

    @property
    def accounting(self):
        roles = Counter(message.role for row in self.records for message in row.record.prefix)
        return MappingProxyType({
            "prefix_content_bytes": sum(row.record.content_bytes for row in self.records),
            "prefix_serialized_bytes": sum(row.record.serialized_bytes for row in self.records),
            "prefix_tokens": sum(len(row.context_ids) for row in self.records),
            "prefix_identifier_occurrences": sum(len(_IDENTIFIER.findall(message.content))
                                                 for row in self.records for message in row.record.prefix),
            **{f"prefix_{role}_messages": roles[role] for role in ("system", "user", "assistant")},
            "target_tokens": sum(len(row.target_ids) for row in self.records),
            "suffix_tokens": sum(len(row.suffix_ids) for row in self.records),
            "padding_tokens": sum(self.padding_length - len(row.input_ids) for row in self.records),
            "sequence_tokens": sum(len(row.input_ids) for row in self.records),
            "total_sequence_tokens": BATCH_SIZE * self.padding_length,
        })


@dataclass(frozen=True)
class PairedBatch:
    presentation: tape.PresentationBatch
    closed: ArmBatch
    atom_local: ArmBatch
    target_hashes: tuple[str, ...]
    target_token_counts: tuple[int, ...]

    @property
    def residuals(self):
        closed, atom = self.closed.accounting, self.atom_local.accounting
        return MappingProxyType({key: closed[key] - atom[key] for key in closed})

    @property
    def status(self):
        return STATUS

    @property
    def rng_start_state_sha256(self):
        """The tape seed is not an observed CPU/CUDA generator-state hash."""
        return None


def _ids(value, *, name):
    if (type(value) not in (tuple, list) or not value or len(value) > MAX_CONTEXT_TOKENS
            or any(type(token) is not int or token < 0 for token in value)):
        raise ValueError(f"invalid_or_over_context_{name}_ids")
    return tuple(value)


def _decode(tokenizer, token_ids):
    text = tokenizer.decode(list(token_ids), skip_special_tokens=False,
                            clean_up_tokenization_spaces=False)
    if type(text) is not str:
        raise ValueError("decoded_text_required")
    return text


def _encode(tokenizer, text, *, name):
    token_ids = _ids(tokenizer.encode(text, add_special_tokens=False, truncation=False), name=name)
    if _decode(tokenizer, token_ids) != text:
        raise ValueError(f"{name}_roundtrip_mismatch")
    return token_ids


def _specials(tokenizer):
    eos = getattr(tokenizer, "eos_token_id", None)
    pad = getattr(tokenizer, "pad_token_id", None)
    eos_text = getattr(tokenizer, "eos_token", None)
    pad_text = getattr(tokenizer, "pad_token", None)
    specials = getattr(tokenizer, "all_special_ids", None)
    if (type(eos) is not int or eos < 0 or type(eos_text) is not str or not eos_text
            or type(pad) is not int or pad < 0 or type(pad_text) is not str or not pad_text):
        raise ValueError("invalid_declared_eos_or_pad")
    if (type(specials) not in (tuple, list) or not specials
            or any(type(token) is not int or token < 0 for token in specials)
            or eos not in specials or pad not in specials):
        raise ValueError("invalid_declared_special_ids")
    if getattr(tokenizer, "padding_side", None) != "right":
        raise ValueError("right_padding_required")
    if (_encode(tokenizer, eos_text, name="eos") != (eos,)
            or _encode(tokenizer, pad_text, name="pad") != (pad,)):
        raise ValueError("invalid_eos_or_pad_encoding")
    return eos, pad, eos_text, frozenset(specials)


def _validate_record(record):
    if type(record) is not targets.ArmRecord or type(record.unit) is not targets.TargetUnit:
        raise ValueError("arm_record_required")
    unit = record.unit
    if (type(record.arm) is not str or record.arm not in ("CLOSED", "ATOM_LOCAL")
            or type(unit.unit_id) is not str or unit.unit_id not in _UNIT_IDS):
        raise ValueError("invalid_arm_or_unit")
    if type(unit.target_bytes) is not bytes or not unit.target_bytes.isascii():
        raise ValueError("ascii_target_bytes_required")
    action = wire.parse_action(unit.target_bytes.decode("ascii"))
    if (sha256(unit.target_bytes).hexdigest() != unit.target_sha256
            or (action.operation, action.operand) != (unit.command, unit.operand)):
        raise ValueError("target_provenance_mismatch")
    if type(record.prefix) is not tuple or any(type(message) is not targets.Message
                                              or type(message.content) is not str
                                              or not message.content.isascii() for message in record.prefix):
        raise ValueError("immutable_ascii_prefix_required")
    public_task = targets.latest_public_task(record.prefix)
    serialized = targets.messages_bytes(record.prefix)
    if (sha256(serialized).hexdigest() != record.prefix_sha256
            or len(serialized) != record.serialized_bytes
            or sum(len(message.content.encode("ascii")) for message in record.prefix) != record.content_bytes):
        raise ValueError("prefix_provenance_mismatch")
    return public_task


def _identifier_tokens(tokenizer, text, content_ids, specials):
    spans = []
    previous = 0
    for end in range(1, len(content_ids) + 1):
        decoded = _decode(tokenizer, content_ids[:end])
        if not text.startswith(decoded) or len(decoded) <= previous:
            raise ValueError("inexact_target_token_byte_boundary")
        spans.append((previous, len(decoded)))
        previous = len(decoded)
    result = []
    for match in _IDENTIFIER.finditer(text):
        standalone = _encode(tokenizer, match.group(), name="identifier")
        if specials.intersection(standalone):
            raise ValueError("identifier_special_contamination")
        indices = tuple(index for index, (start, end) in enumerate(spans)
                        if start < match.end() and end > match.start())
        result.append(IdentifierTokens(match.group(), match.start(), match.end(), standalone,
                                       indices, tuple(content_ids[index] for index in indices)))
    return tuple(result)


def tokenize_arm_record(record, *, tokenizer, count_basis):
    """Check exact template/content/EOS boundaries using an injected interface.

    Full encoded IDs are returned as well as both boundary slices and decoded
    bytes. Count labels are mandatory; neither permitted label authenticates a
    native tokenizer. The caller retains responsibility for template/file pins.
    """
    if type(count_basis) is not str or count_basis not in COUNT_BASES:
        raise ValueError("explicit_non_native_count_basis_required")
    _validate_record(record)
    eos, pad, eos_text, specials = _specials(tokenizer)
    for message in record.training_messages:
        if specials.intersection(_encode(tokenizer, message.content, name="message")):
            raise ValueError("message_special_contamination")
    prefix = [{"role": message.role, "content": message.content} for message in record.prefix]
    text = record.unit.target_bytes.decode("ascii")
    training = prefix + [{"role": "assistant", "content": text}]
    context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True)
    full = tokenizer.apply_chat_template(training, tokenize=False, add_generation_prompt=False)
    if type(context) is not str or not context or type(full) is not str:
        raise ValueError("chat_template_text_required")
    if full != context + text + eos_text + TEMPLATE_SUFFIX:
        raise ValueError("inexact_chat_template_boundary_or_pinned_suffix")
    context_ids = _encode(tokenizer, context, name="context")
    content_ids = _encode(tokenizer, text, name="target")
    if specials.intersection(content_ids):
        raise ValueError("target_special_contamination")
    target_ids = content_ids + (eos,)
    suffix_ids = _encode(tokenizer, TEMPLATE_SUFFIX, name="suffix")
    if specials.intersection(suffix_ids):
        raise ValueError("suffix_special_contamination")
    input_ids = _encode(tokenizer, full, name="sequence")
    if input_ids != context_ids + target_ids + suffix_ids:
        raise ValueError("inexact_context_target_eos_suffix_token_boundary")
    for messages, generation, expected in ((prefix, True, context_ids), (training, False, input_ids)):
        rendered_ids = _ids(tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=generation,
            truncation=False, padding=False), name="chat_template")
        if rendered_ids != expected:
            raise ValueError("chat_template_tokenization_mismatch")
    target_roundtrip = _decode(tokenizer, target_ids)
    if target_roundtrip != text + eos_text:
        raise ValueError("target_eos_roundtrip_mismatch")
    return TokenizedArm(record, context_ids, target_ids, input_ids,
                        (IGNORE_INDEX,) * len(context_ids) + target_ids + (IGNORE_INDEX,) * len(suffix_ids),
                        (1,) * len(input_ids),
                        context.encode("utf-8"), target_roundtrip.encode("utf-8"), full.encode("utf-8"),
                        _identifier_tokens(tokenizer, text, content_ids, specials), eos, pad, count_basis,
                        suffix_ids, TEMPLATE_SUFFIX.encode("utf-8"))


def tokenize_paired_target(pair, *, tokenizer, count_basis):
    """Prepare both authentic source views without equating their prefix costs."""
    if type(pair) is not targets.PairedTarget:
        raise ValueError("paired_target_required")
    closed_task = _validate_record(pair.closed)
    atom_task = _validate_record(pair.atom_local)
    if (pair.closed.arm != "CLOSED" or pair.atom_local.arm != "ATOM_LOCAL"
            or pair.closed.unit is not pair.atom_local.unit or closed_task != atom_task):
        raise ValueError("paired_source_identity_or_state_mismatch")
    closed = tokenize_arm_record(pair.closed, tokenizer=tokenizer, count_basis=count_basis)
    atom = tokenize_arm_record(pair.atom_local, tokenizer=tokenizer, count_basis=count_basis)
    if (closed.target_ids != atom.target_ids
            or closed.identifier_tokenization != atom.identifier_tokenization
            or closed.target_roundtrip_bytes != atom.target_roundtrip_bytes
            or (closed.eos_token_id, closed.pad_token_id) != (atom.eos_token_id, atom.pad_token_id)):
        raise ValueError("paired_target_tokenization_mismatch")
    if (closed.suffix_ids != atom.suffix_ids
            or closed.suffix_roundtrip_bytes != atom.suffix_roundtrip_bytes):
        raise ValueError("paired_template_suffix_tokenization_mismatch")
    return TokenizedPair(closed, atom)


def _batch(rows, width):
    if (type(width) is not int or not 1 <= width <= MAX_CONTEXT_TOKENS
            or any(len(row.input_ids) > width for row in rows)):
        raise ValueError("invalid_padding_width_or_truncation")
    return ArmBatch(rows[0].record.arm, rows,
                    tuple(row.input_ids + (row.pad_token_id,) * (width - len(row.input_ids)) for row in rows),
                    tuple(row.labels + (IGNORE_INDEX,) * (width - len(row.input_ids)) for row in rows),
                    tuple(row.attention_mask + (0,) * (width - len(row.input_ids)) for row in rows), width)


def prepare_paired_batch(presentation, paired_targets, *, tokenizer, count_basis,
                         closed_padding_length, atom_local_padding_length):
    """Prepare exactly four ordered pairs, without packing or choosing widths.

    Pass the four raw PairedTargets selected by the existing curriculum's tape,
    in tape slot order. D2 entries are descriptive, not authorization to run D2.
    The upstream tape/compiler owns master authentication and whole-dose order.
    No RNG state is created or restored here; only the supplied seed is retained.
    """
    if (type(presentation) is not tape.PresentationBatch
            or type(presentation.update_number) is not int or not 1 <= presentation.update_number <= 512
            or type(presentation.presentation_index) is not int
            or presentation.presentation_index != (presentation.update_number - 1) // 64
            or type(presentation.rng_start_seed) is not int or not 0 <= presentation.rng_start_seed < 2**64
            or type(presentation.unit_ids) is not tuple or len(presentation.unit_ids) != BATCH_SIZE
            or any(type(unit) is not str or unit not in _UNIT_IDS for unit in presentation.unit_ids)
            or len(set(presentation.unit_ids)) != BATCH_SIZE):
        raise ValueError("invalid_presentation_batch")
    if (type(paired_targets) not in (tuple, list) or len(paired_targets) != BATCH_SIZE
            or any(type(pair) is not targets.PairedTarget for pair in paired_targets)):
        raise ValueError("exactly_four_paired_targets_required")
    for pair in paired_targets:
        _validate_record(pair.closed)
        _validate_record(pair.atom_local)
    if tuple(pair.closed.unit.unit_id for pair in paired_targets) != presentation.unit_ids:
        raise ValueError("paired_batch_slot_order_mismatch")
    prepared = tuple(tokenize_paired_target(pair, tokenizer=tokenizer, count_basis=count_basis)
                     for pair in paired_targets)
    closed = _batch(tuple(pair.closed for pair in prepared), closed_padding_length)
    atom = _batch(tuple(pair.atom_local for pair in prepared), atom_local_padding_length)
    if len({(row.eos_token_id, row.pad_token_id) for row in closed.records + atom.records}) != 1:
        raise ValueError("batch_special_id_drift")
    return PairedBatch(presentation, closed, atom,
                       tuple(row.record.unit.target_sha256 for row in closed.records),
                       tuple(len(row.target_ids) for row in closed.records))
