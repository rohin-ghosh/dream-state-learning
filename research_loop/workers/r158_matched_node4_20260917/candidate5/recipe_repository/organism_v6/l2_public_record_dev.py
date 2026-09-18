"""Pure exploratory DEV loop: public evidence, exact targets, and routing intent.

No model, tokenizer, file, process, or network operations. Receipt hashes bind
bytes; the runtime must independently retain those pins and authenticate the
environment/capture channel. State transitions are not native-load proof.
"""
from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from hashlib import sha256
import json
from math import isfinite
import re


SCHEMA = "l2_public_record_dev_v0"
POLICIES = ("PROMOTE", "SHADOW")
PUBLIC_LAW = (
    "For each key exactly one of the two listed actions succeeds. The mapping "
    "is deterministic and does not change. SUCCESS means the executed action "
    "is the successful one; FAILURE means the other listed action is the successful one."
)
PROCESS_TAPE = (
    "Compare the executed action with its public outcome under the stated law. "
    "Write only the action that should succeed for this key. Do not invent feedback."
)


class IntegrityError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise IntegrityError(message)


def canonical(value):
    def encode(item):
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, bytes):
            return {"raw_hex": item.hex()}
        raise TypeError("unsupported canonical value")
    return json.dumps(value, default=encode, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value):
    return sha256(canonical(value)).hexdigest()


def _pin(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             "expected SHA256 pin")


@dataclass(frozen=True)
class Slot:
    slot_id: str
    key: str
    block: int
    index: int


@dataclass(frozen=True)
class PublicWorld:
    root_id: str
    actions: tuple[str, str]
    slots: tuple[Slot, ...]
    law: str = PUBLIC_LAW


@dataclass(frozen=True)
class World:
    public: PublicWorld
    success_actions: tuple[str, ...]


@dataclass(frozen=True)
class Receipt:
    root_id: str
    slot_id: str
    lineage: str
    kind: str
    sequence: int
    raw: bytes
    previous_sha256: str | None
    sha256: str


@dataclass(frozen=True)
class Episode:
    action: Receipt
    outcome: Receipt | None = None
    record: Receipt | None = None


@dataclass(frozen=True)
class CapturedBlock:
    root_id: str
    block: int
    lineage: str
    episodes: tuple[Episode, ...]


@dataclass(frozen=True)
class TrainingRow:
    root_id: str
    slot_id: str
    source_slot_id: str
    prompt: str
    target: bytes
    action: str
    episode_sha256: str
    record_sha256: str


@dataclass(frozen=True)
class Rejection:
    slot_id: str
    reason: str


@dataclass(frozen=True)
class Corpus:
    root_id: str
    lineage: str
    captures: tuple[CapturedBlock, ...]
    capture_hashes: tuple[str, ...]
    rows: tuple[TrainingRow, ...]
    rejected: tuple[Rejection, ...]
    kind: str = "AUTHENTIC"
    permutation: tuple[int, ...] = ()
    changed_targets: int = 0
    no_op: bool = False


@dataclass(frozen=True)
class Sleep:
    block: int
    corpus_sha256: str
    candidate_sha256: str | None
    initialized_from_sha256: str
    mounted: bool


@dataclass(frozen=True)
class LoopState:
    public_sha256: str
    policy: str
    base_sha256: str
    mounted_sha256: str
    phase: str = "AWAIT_BLOCK_1"
    corpus: Corpus | None = None
    sleeps: tuple[Sleep, ...] = ()


_WIRE_TYPES = {kind.__name__: kind for kind in (
    Slot, PublicWorld, World, Receipt, Episode, CapturedBlock, TrainingRow,
    Rejection, Corpus, Sleep, LoopState)}


def _pack(value):
    if type(value).__name__ in _WIRE_TYPES and type(value) is _WIRE_TYPES[type(value).__name__]:
        return {"record": type(value).__name__,
                "fields": {field.name: _pack(getattr(value, field.name)) for field in fields(value)}}
    if type(value) is bytes:
        return {"bytes": value.hex()}
    if type(value) in (tuple, list):
        return {"tuple" if type(value) is tuple else "list": [_pack(item) for item in value]}
    if type(value) is dict:
        _require(all(type(key) is str for key in value), "wire dictionary keys")
        return {"dict": [[key, _pack(value[key])] for key in sorted(value)]}
    _require(value is None or type(value) in (str, int, bool) or
             type(value) is float and isfinite(value), "unsupported wire value")
    return value


def _unpack(value):
    if type(value) is not dict:
        _require(value is None or type(value) in (str, int, bool) or
                 type(value) is float and isfinite(value), "invalid wire primitive")
        return value
    if set(value) == {"record", "fields"}:
        _require(type(value["record"]) is str and value["record"] in _WIRE_TYPES and
                 type(value["fields"]) is dict, "unknown wire record")
        kind = _WIRE_TYPES[value["record"]]
        _require(set(value["fields"]) == {field.name for field in fields(kind)}, "wire record fields")
        return kind(**{key: _unpack(item) for key, item in value["fields"].items()})
    if set(value) == {"bytes"}:
        _require(type(value["bytes"]) is str and re.fullmatch(r"(?:[0-9a-f]{2})*", value["bytes"]) is not None,
                 "wire byte encoding")
        return bytes.fromhex(value["bytes"])
    for tag, factory in (("tuple", tuple), ("list", list)):
        if set(value) == {tag}:
            _require(type(value[tag]) is list, "wire sequence")
            return factory(_unpack(item) for item in value[tag])
    if set(value) == {"dict"}:
        _require(type(value["dict"]) is list, "wire dictionary")
        result = {}
        for pair in value["dict"]:
            _require(type(pair) is list and len(pair) == 2 and type(pair[0]) is str and pair[0] not in result,
                     "wire dictionary duplicate/invalid key")
            result[pair[0]] = _unpack(pair[1])
        return result
    raise IntegrityError("invalid wire tag")


def to_data(value) -> dict:
    """JSON-safe wire envelope preserving dataclass, tuple and exact-byte types."""
    return {"schema": SCHEMA, "wire_version": 1, "value": _pack(value)}


def from_data(payload: dict, *, expected_type: type | None = None):
    """Decode allowlisted data only; callers still verify retained pins/invariants."""
    _require(type(payload) is dict and set(payload) == {"schema", "wire_version", "value"} and
             payload["schema"] == SCHEMA and type(payload["wire_version"]) is int and
             payload["wire_version"] == 1, "wire envelope/version")
    result = _unpack(payload["value"])
    _require(expected_type is None or type(result) is expected_type, "unexpected decoded type")
    return result


def _public(public):
    _require(type(public) is PublicWorld and public.law == PUBLIC_LAW, "public world/law")
    _require(re.fullmatch(r"root_[0-9a-f]{24}", public.root_id) is not None, "root identity")
    _require(type(public.actions) is tuple and len(public.actions) == 2 and
             len(set(public.actions)) == 2 and all(re.fullmatch(r"move_[0-9a-f]{12}", action)
                                                 for action in public.actions), "action vocabulary")
    _require(type(public.slots) is tuple and len(public.slots) == 16, "fixed16 source slots")
    _require(len({slot.slot_id for slot in public.slots}) == 16 and
             len({slot.key for slot in public.slots}) == 16, "unique slots and keys")
    for index, slot in enumerate(public.slots):
        _require(type(slot) is Slot and slot.index == index and slot.block == index // 8 + 1 and
                 re.fullmatch(r"slot_[0-9a-f]{24}", slot.slot_id) is not None and
                 re.fullmatch(r"key_[0-9a-f]{24}", slot.key) is not None, "slot schedule")


def build_world(vocab_seed: int, truth_seed: int) -> World:
    _require(all(type(seed) is int and 0 <= seed < 2**32 for seed in (vocab_seed, truth_seed)), "seed range")
    root = "root_" + digest([SCHEMA, "vocabulary", vocab_seed])[:24]
    actions = tuple("move_" + digest([root, "action", index])[:12] for index in range(2))
    slots = tuple(Slot("slot_" + digest([root, "slot", index])[:24],
                       "key_" + digest([root, "key", index])[:24], index // 8 + 1, index)
                  for index in range(16))
    public = PublicWorld(root, actions, slots)
    success = []
    for block in (1, 2):
        order = sorted(range(8), key=lambda index: digest([SCHEMA, "truth", truth_seed, block, index]))
        first = set(order[:4])
        success.extend(actions[0 if index in first else 1] for index in range(8))
    _public(public)
    return World(public, tuple(success))


def public_view(world: World) -> PublicWorld:
    _public(world.public)
    _require(len(world.success_actions) == 16 and all(
        Counter(world.success_actions[start:start + 8]) == dict.fromkeys(world.public.actions, 4)
        for start in (0, 8)), "private world balance")
    return world.public


def _slot(public, slot_id):
    _public(public)
    found = [slot for slot in public.slots if slot.slot_id == slot_id]
    _require(len(found) == 1, "unknown/cross-root slot")
    return found[0]


def action_prompt(public: PublicWorld, slot_id: str, *, view="wake") -> str:
    slot = _slot(public, slot_id)
    _require(view in ("wake", "train", "readout"), "prompt view")
    request = (f"Key {slot.key}: choose the successful action." if view != "readout" else
               f"For {slot.key}, which listed action succeeds?")
    return (public.law + "\nLegal actions: " + ", ".join(public.actions) + "\n" + request +
            "\nReply with only the action name; one terminal newline is optional.")


def _action(public, raw):
    for action in public.actions:
        if raw in (action.encode("ascii"), action.encode("ascii") + b"\n"):
            return action
    return None


def _receipt_hash(receipt):
    return digest(replace(receipt, sha256=""))


def _check_receipt(public, receipt):
    _require(type(receipt) is Receipt and receipt.root_id == public.root_id, "receipt root/type")
    _slot(public, receipt.slot_id)
    _require(receipt.lineage in ("SHARED", *POLICIES), "receipt lineage")
    _require(receipt.kind in ("action", "outcome", "record", "readout"), "receipt kind")
    _require(type(receipt.sequence) is int and receipt.sequence >= 0 and type(receipt.raw) is bytes,
             "raw bytes/sequence")
    _require(receipt.sha256 == _receipt_hash(receipt), "raw receipt hash mismatch")
    if receipt.kind in ("action", "readout"):
        _require(receipt.previous_sha256 is None, "unexpected predecessor")
    else:
        _pin(receipt.previous_sha256)


def _link(public, receipt, previous):
    _check_receipt(public, receipt)
    _check_receipt(public, previous)
    _require((receipt.slot_id, receipt.lineage) == (previous.slot_id, previous.lineage),
             "cross-slot/lineage receipt link")
    _require(receipt.previous_sha256 == previous.sha256 and receipt.sequence > previous.sequence,
             "chronology/predecessor mismatch")
    _require((previous.kind, receipt.kind) in (("action", "outcome"), ("outcome", "record")),
             "receipt phase order")


def make_receipt(public: PublicWorld, slot_id: str, kind: str, raw: bytes, *, sequence: int,
                 lineage: str, previous=None) -> Receipt:
    receipt = Receipt(public.root_id, slot_id, lineage, kind, sequence, raw,
                      previous.sha256 if previous is not None else None, "")
    receipt = replace(receipt, sha256=_receipt_hash(receipt))
    _check_receipt(public, receipt)
    if previous is not None:
        _link(public, receipt, previous)
    return receipt


def feedback(world: World, action: Receipt, *, sequence: int) -> Receipt:
    public = public_view(world)
    _check_receipt(public, action)
    _require(action.kind == "action", "feedback requires committed action")
    selected = _action(public, action.raw)
    _require(selected is not None, "invalid action has no binary feedback")
    expected = world.success_actions[_slot(public, action.slot_id).index]
    outcome = b"SUCCESS" if selected == expected else b"FAILURE"
    return make_receipt(public, action.slot_id, "outcome", outcome, sequence=sequence,
                        lineage=action.lineage, previous=action)


def process_prompt(public: PublicWorld, action: Receipt, outcome: Receipt) -> str:
    _link(public, outcome, action)
    _require(_action(public, action.raw) is not None and outcome.raw in (b"SUCCESS", b"FAILURE"),
             "process prompt needs valid public evidence")
    return (action_prompt(public, action.slot_id) + "\nExecuted action: " + action.raw.decode("ascii") +
            "\nPublic outcome: " + outcome.raw.decode("ascii") + "\n" + PROCESS_TAPE)


def _episode(public, episode):
    action, outcome, record = episode.action, episode.outcome, episode.record
    _check_receipt(public, action)
    _require(action.kind == "action", "episode action kind")
    if outcome is not None:
        _link(public, outcome, action)
        _require(outcome.raw in (b"SUCCESS", b"FAILURE"), "nonbinary public outcome")
    if record is not None:
        _require(outcome is not None, "orphan record")
        _link(public, record, outcome)
    selected = _action(public, action.raw)
    if selected is None:
        return None, "INVALID_ACTION"
    if outcome is None:
        return None, "MISSING_OUTCOME"
    if record is None:
        return None, "MISSING_RECORD"
    authored = _action(public, record.raw)
    if authored is None:
        return None, "INVALID_RECORD_ACTION"
    supported = (authored == selected) if outcome.raw == b"SUCCESS" else (authored != selected)
    if not supported:
        return None, "UNSUPPORTED_RECORD"
    return TrainingRow(public.root_id, action.slot_id, action.slot_id,
                       action_prompt(public, action.slot_id, view="train"), record.raw, authored,
                       digest(episode), record.sha256), None


def _block(public, capture):
    _require(type(capture) is CapturedBlock and capture.root_id == public.root_id, "capture root/type")
    _require(type(capture.block) is int and capture.block in (1, 2), "block number")
    _require(capture.lineage == "SHARED" if capture.block == 1 else capture.lineage in POLICIES,
             "block lineage")
    _require(type(capture.episodes) is tuple and len(capture.episodes) == 8, "fixed eight-slot capture")
    rows, rejected = [], []
    previous_sequence = -1
    slots = public.slots[(capture.block - 1) * 8:capture.block * 8]
    for slot, episode in zip(slots, capture.episodes):
        _require(type(episode) is Episode and episode.action.slot_id == slot.slot_id and
                 episode.action.lineage == capture.lineage, "capture order/lineage")
        row, reason = _episode(public, episode)
        _require(episode.action.sequence > previous_sequence, "block receipt chronology")
        last = episode.record or episode.outcome or episode.action
        previous_sequence = last.sequence
        if row is not None:
            rows.append(row)
        else:
            rejected.append(Rejection(slot.slot_id, reason))
    return tuple(rows), tuple(rejected), previous_sequence


def capture_block(public: PublicWorld, block: int, lineage: str, episodes: tuple[Episode, ...]) -> CapturedBlock:
    _public(public)
    capture = CapturedBlock(public.root_id, block, lineage, episodes)
    _block(public, capture)
    return capture


def compile_corpus(public: PublicWorld, captures: tuple[CapturedBlock, ...], *, expected_hashes: tuple[str, ...]) -> Corpus:
    _public(public)
    _require(type(captures) is tuple and len(captures) in (1, 2) and
             type(expected_hashes) is tuple and len(expected_hashes) == len(captures), "capture inventory")
    rows, rejected = [], []
    previous_sequence = -1
    for block, (capture, expected) in enumerate(zip(captures, expected_hashes), 1):
        _pin(expected)
        _require(digest(capture) == expected, "external capture hash mismatch")
        _require(capture.block == block, "cumulative blocks must be 1 then 2")
        admitted, refusals, last = _block(public, capture)
        _require(capture.episodes[0].action.sequence > previous_sequence, "cumulative chronology")
        previous_sequence = last
        rows.extend(admitted)
        rejected.extend(refusals)
    return Corpus(public.root_id, captures[-1].lineage, captures, expected_hashes, tuple(rows), tuple(rejected))


def _misbound(authentic):
    count = len(authentic.rows)
    permutation = tuple((index + 1) % count for index in range(count))
    rows = []
    for row, donor_index in zip(authentic.rows, permutation):
        donor = authentic.rows[donor_index]
        rows.append(replace(row, source_slot_id=donor.source_slot_id, target=donor.target,
                            action=donor.action, episode_sha256=donor.episode_sha256,
                            record_sha256=donor.record_sha256))
    changed = sum(row.action != original.action for row, original in zip(rows, authentic.rows))
    return replace(authentic, rows=tuple(rows), kind="MISBOUND", permutation=permutation,
                   changed_targets=changed, no_op=changed == 0)


def _validate_corpus(public, corpus, expected):
    _pin(expected)
    _require(type(corpus) is Corpus and digest(corpus) == expected, "corpus hash mismatch")
    authentic = compile_corpus(public, corpus.captures, expected_hashes=corpus.capture_hashes)
    rebuilt = authentic if corpus.kind == "AUTHENTIC" else _misbound(authentic)
    _require(corpus == rebuilt, "corpus rows differ from captured child spans/control")


def misbind_corpus(public: PublicWorld, corpus: Corpus, *, expected_sha256: str) -> Corpus:
    _validate_corpus(public, corpus, expected_sha256)
    _require(corpus.kind == "AUTHENTIC", "control needs authentic source")
    return _misbound(corpus)


def training_items(public: PublicWorld, corpus: Corpus, *, expected_sha256: str) -> list[dict]:
    _validate_corpus(public, corpus, expected_sha256)
    return [dict(spans=[[row.prompt, False, "context"],
                        [row.target.decode("ascii"), True, "child_action"]],
                 group=row.slot_id, view="source_withdrawn_action", order=index,
                 meta=dict(schema=SCHEMA, root_id=public.root_id, corpus_kind=corpus.kind,
                           source_slot_id=row.source_slot_id, record_sha256=row.record_sha256,
                           episode_sha256=row.episode_sha256, target_sha256=sha256(row.target).hexdigest(),
                           target_byte_span=[0, len(row.target)], native_tokenization_verified=False))
            for index, row in enumerate(corpus.rows)]


def start_pair(public: PublicWorld, base_sha256: str) -> dict[str, LoopState]:
    _public(public)
    _pin(base_sha256)
    return {policy: LoopState(digest(public), policy, base_sha256, base_sha256) for policy in POLICIES}


def _state(public, state):
    _require(type(state) is LoopState and state.public_sha256 == digest(public) and
             state.policy in POLICIES, "state public identity/policy")
    _pin(state.base_sha256)
    _pin(state.mounted_sha256)
    _require(len(state.sleeps) <= 2, "two-sleep cap")
    _require(state.phase in ("AWAIT_BLOCK_1", "AWAIT_SLEEP_1", "AWAIT_BLOCK_2", "AWAIT_SLEEP_2",
                             "COMPLETE", "FORMATION_SHORTAGE"), "state phase")
    if state.corpus is not None:
        _validate_corpus(public, state.corpus, digest(state.corpus))
        _require(state.corpus.kind == "AUTHENTIC", "MISBOUND cannot become authentic lineage")
        _require(state.corpus.lineage == ("SHARED" if len(state.corpus.captures) == 1 else state.policy),
                 "state contains another branch corpus")
    captured = len(state.corpus.captures) if state.corpus else 0
    completed = len(state.sleeps)
    if state.phase.startswith("AWAIT_BLOCK_"):
        _require(captured == completed < 2 and state.phase == f"AWAIT_BLOCK_{completed + 1}",
                 "state collection phase/count")
    elif state.phase.startswith("AWAIT_SLEEP_"):
        _require(captured == completed + 1 and state.phase == f"AWAIT_SLEEP_{captured}",
                 "state sleep phase/count")
    elif state.phase == "COMPLETE":
        _require(captured == completed == 2 and all(sleep.candidate_sha256 for sleep in state.sleeps),
                 "incomplete endpoint state")
    else:
        _require(captured == completed > 0 and not state.corpus.rows and
                 state.sleeps[-1].candidate_sha256 is None, "formation shortage state")
    expected_mount = state.base_sha256
    for block, sleep in enumerate(state.sleeps, 1):
        _require(sleep.block == block and sleep.initialized_from_sha256 == state.base_sha256,
                 "sleep order/initialization")
        _require(sleep.mounted == (state.policy == "PROMOTE" and sleep.candidate_sha256 is not None),
                 "publication policy")
        prior = compile_corpus(public, state.corpus.captures[:block],
                               expected_hashes=state.corpus.capture_hashes[:block])
        _require(sleep.corpus_sha256 == digest(prior) and
                 bool(prior.rows) == (sleep.candidate_sha256 is not None), "sleep corpus binding")
        if sleep.candidate_sha256 is not None:
            _pin(sleep.candidate_sha256)
        if sleep.mounted:
            expected_mount = sleep.candidate_sha256
    _require(state.mounted_sha256 == expected_mount, "mounted state drift")


def close_block(public: PublicWorld, state: LoopState, capture: CapturedBlock, *, expected_sha256: str) -> LoopState:
    _state(public, state)
    block = len(state.sleeps) + 1
    _require(block <= 2 and state.phase == f"AWAIT_BLOCK_{block}", "not awaiting this capture")
    _require(capture.block == block and capture.lineage == ("SHARED" if block == 1 else state.policy),
             "capture belongs to another branch/block")
    prior = state.corpus.captures if state.corpus is not None else ()
    hashes = state.corpus.capture_hashes if state.corpus is not None else ()
    corpus = compile_corpus(public, prior + (capture,), expected_hashes=hashes + (expected_sha256,))
    return replace(state, corpus=corpus, phase=f"AWAIT_SLEEP_{block}")


def complete_sleep(public: PublicWorld, state: LoopState, *, corpus_sha256: str, candidate_sha256: str | None,
                   initialized_from_sha256: str) -> LoopState:
    _state(public, state)
    block = len(state.sleeps) + 1
    _require(block <= 2 and state.phase == f"AWAIT_SLEEP_{block}", "not awaiting sleep")
    _require(initialized_from_sha256 == state.base_sha256, "cumulative write must start from frozen base")
    _validate_corpus(public, state.corpus, corpus_sha256)
    if not state.corpus.rows:
        _require(candidate_sha256 is None, "empty corpus cannot fabricate a candidate")
        phase = "FORMATION_SHORTAGE"
    else:
        _pin(candidate_sha256)
        phase = "AWAIT_BLOCK_2" if block == 1 else "COMPLETE"
    mounted = state.policy == "PROMOTE" and candidate_sha256 is not None
    sleep = Sleep(block, corpus_sha256, candidate_sha256, initialized_from_sha256, mounted)
    return replace(state, phase=phase, sleeps=state.sleeps + (sleep,),
                   mounted_sha256=candidate_sha256 if mounted else state.mounted_sha256)


def routing(state: LoopState) -> dict:
    return dict(policy=state.policy, phase=state.phase, requested_artifact_sha256=state.mounted_sha256,
                frozen_start_sha256=state.base_sha256, native_verified=False)


def check_pair(public: PublicWorld, states: dict[str, LoopState]) -> None:
    _require(set(states) == set(POLICIES), "exact PROMOTE/SHADOW pair")
    for policy, state in states.items():
        _state(public, state)
        _require(state.policy == policy, "policy dictionary mismatch")
    promote, shadow = (states[policy] for policy in POLICIES)
    _require(promote.base_sha256 == shadow.base_sha256, "different starting bases")
    if promote.corpus is not None and shadow.corpus is not None:
        _require(promote.corpus.capture_hashes[0] == shadow.corpus.capture_hashes[0],
                 "first material must be shared")
    if promote.sleeps and shadow.sleeps:
        first, other = promote.sleeps[0], shadow.sleeps[0]
        _require((first.corpus_sha256, first.candidate_sha256) ==
                 (other.corpus_sha256, other.candidate_sha256), "first candidate must be byte-identical")


def reduce_pair(world: World, states: dict[str, LoopState], readouts: dict[str, tuple[Receipt | None, ...]]) -> dict:
    public = public_view(world)
    check_pair(public, states)
    _require(set(readouts) == set(POLICIES), "readout policies")
    cells, indicators = {}, {}
    for policy in POLICIES:
        records = readouts[policy]
        _require(type(records) is tuple and len(records) == 16, "fixed16 readout denominator")
        passed, legal, missing = [], 0, 0
        last_sequence = (_block(public, states[policy].corpus.captures[-1])[2]
                         if states[policy].corpus else -1)
        for slot, expected, receipt in zip(public.slots, world.success_actions, records):
            if receipt is None:
                missing += 1
                passed.append(False)
                continue
            _check_receipt(public, receipt)
            _require(receipt.kind == "readout" and receipt.slot_id == slot.slot_id and
                     receipt.lineage == policy, "readout identity/order")
            _require(receipt.sequence > last_sequence, "stale/unordered readout sequence")
            last_sequence = receipt.sequence
            selected = _action(public, receipt.raw)
            legal += selected is not None
            passed.append(selected == expected)
        complete = states[policy].phase == "COMPLETE" and missing == 0
        cells[policy] = dict(total=16, observed_correct=sum(passed), legal=legal, missing=missing,
                             endpoint_evaluable=complete, accuracy=sum(passed) / 16 if complete else None,
                             old_correct=sum(passed[:8]), new_correct=sum(passed[8:]),
                             accepted=len(states[policy].corpus.rows) if states[policy].corpus else 0,
                             rejected=len(states[policy].corpus.rejected) if states[policy].corpus else 0,
                             state_sha256=digest(states[policy]), readout_sha256=digest(records))
        indicators[policy] = passed
    promote, shadow = (indicators[policy] for policy in POLICIES)
    pairs = Counter((left, right) for left, right in zip(promote, shadow))
    paired = dict(promote_only=pairs[True, False], shadow_only=pairs[False, True],
                  both=pairs[True, True], neither=pairs[False, False], total=16,
                  net=sum(promote) - sum(shadow))
    return dict(schema=SCHEMA, public_sha256=digest(public), cells=cells, paired=paired,
                endpoint_evaluable=all(cell["endpoint_evaluable"] for cell in cells.values()),
                scientific_pass=None, native_verified=False,
                claim="Exploratory partial DEV loop only; no birth promotion, internalization or H1/H2 claim.")
