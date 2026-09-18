"""Isolated q14 reasoning policy, slot and source gate; not a runner/launch path.

Integration: source-match each NOTE_AFTER to one recorded ACT in the external
preschool gate, then call facts_from_act on that ACT, never on embedded note
measurements. Render outcome_block at the post-outcome slot and apply
judge_record to the child's unchanged text. Its content_eligible result is
necessary, NOT sufficient: source/occurrence matching, delivered-text exclusion,
duplicate checks, split isolation and the existing minimum count are enforced by
gate_sleep here; ancestry authentication and trainer/reload checks remain external.
Use facts.measured for the numeric-event denominator; an empty invalid attempt
has no measured score even though the gym returns a fallback numeric zero.

Integration contract (no runner changes are made here):
  facts = facts_from_act(source_matched_act)
  prompt_suffix = outcome_block(facts, label="NOTE_AFTER")
  judgment = judge_record(unchanged_child_text, facts)
  item = RECORD_ITEM.format(eid=facts.episode_id, text=unchanged_child_text)
Only build item after BOTH judgment["content_eligible"] and every external gate
pass. Catch InvalidFeedback as a rejection, never fall back to compiler parsing.
Persist lesson_receipt(mode, completed_sleeps) to lesson_deliveries.jsonl before
delivery, when non-None, and expose exactly its text. Include the policy version
and source hash in run/probe identities; do not reuse compiler probe caches.

Trainer integration initially requires support: train_adapter.child_record_prefix_length
accepts only "Program " wrappers, whereas RECORD_ITEM uses domain-neutral
"Situation ". Main must explicitly support this wrapper with child-body-only
masking and test token-boundary/truncation behavior before training. Do not rename
the corpus recipe to escape masking or add compiler vocabulary as a workaround.
The lineage validator must likewise support this exact wrapper, occurrence rows,
and reasoning ACT feedback (raw ACT rows historically lack a status field).
deliver_lesson additionally requires ledger=the_life_ledger for lesson/sham; its
teacher parent_turn is an influence, never an admission source. Neutral probes
raise NotImplementedError until main provides a separate trait-only implementation.

Generation contract: generation_identity() must return backend="vllm", the
actual model_input, adapter_input (None for base), adapter_files (filename ->
SHA256), default_max_tokens and default_temperature. The returned dictionary is
preserved unchanged. Missing identity is UNAVAILABLE; marked mocks are TEST_MOCK;
neither can be admitted. RECORDED_BACKEND means recorded configured inputs, NOT
authenticated base weights or introspection of loaded GPU state. That remains
the lineage/loader boundary. Per note, generation contains the exact batch user
prompt and its UTF-8 SHA256, unchanged output SHA256, requested max_tokens/seed,
temperature, identity/hash, and a ledger-prefix-bound complete-batch receipt.
The prompt hash is BEFORE backend chat templating, not a rendered-token digest.
No deterministic-training or universal reproducibility claim follows from a seed.

Gate publication reserves reasoning_gate_transaction.json exclusively, writes
and fsyncs all artifacts, then publishes gate_receipt.json LAST as the enforce
commit. verify_gate_commit(sdir), also called by training_skipped, must succeed
before resume training. Interrupted transactions cannot be automatically reused;
preserve partial artifacts and inspect them. Prior sleeps are hash-checked and
all candidate records rejudged, never silently trusted from cached gate state.

The source's score is authoritative for acceptance, but its feedback displays
only two decimal places. Records are judged against that displayed scalar, not
an invented higher-precision observation. The parser supports literal own-action
descriptions and numeric score statements, not arbitrary semantic entailment,
historical comparisons, or quantified hypotheses. Unsupported forms fail closed.

This module does not select probes, families, curricula, counts or training
recipes. Main must retain reasoning_gym_families.json and existing split guards,
choose a trait-only neutral panel explicitly, and retain separate probe ledgers.
Static lessons are teacher-authored illustrations, never observation evidence;
persist lesson_receipt before delivery. Match lesson/sham token budgets using
the actual tokenizer before launch: no word-count or token-equivalence claim.
Scope is grounded record production, not discretionary memory or general H1.
The upstream gym currently turns verifier exceptions into numeric zero without
an error flag. This policy cannot distinguish those from genuine zero scores;
that requires upstream evidence rather than another interpretation of the text.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import unicodedata
import zlib

from .gym_backend import DEPLOYMENT_LEAK_TERMS
from .preschool import PostOutcomeSlot as _BaseSlot, SKIP_MARKER

POLICY_VERSION = "reasoning-record-q14-v1-2026-09-12"
FAMILIES_FILE = Path(__file__).with_name("reasoning_gym_families.json")
SLOT_SENTENCE = "This field is available after the execution result."
RECORD_ITEM = "Situation {eid}.\nMy measured action record: {text}"
POLICY_SCOPE = "grounded record production; not discretionary memory or general H1"
_LEDGER_PROVENANCE_FIELDS = ("gym", "exposure_domain", "clone_id")

LESSON_PARAGRAPH = (
    "A useful thing to leave yourself is a measured action record: what you actually "
    "tried and what you actually observed, in your own voice. An expectation is not "
    "yet a result. A poor result can still make a good record. Keep observations "
    "separate from guesses, and do not claim a solution the feedback did not reveal. "
    "These illustrations name possible attempts, not answers you should use.")
LESSON_EXAMPLES = (
    "I submitted 'blue amber'. The verifier reported a score of 0.50; this attempt "
    "was not accepted. I would consider a different arrangement next.",
    "I tried 'north'. The verifier reported a score of 0.00; this attempt was not "
    "accepted. I had hoped it would work, but that was only my expectation.",
    "My answer was 'left right'. The reported score was 1.00 and this attempt was "
    "accepted. That observation belongs to this attempt, not every future situation.",
)
REFRESHER_LINE = (
    "A measured action record distinguishes the attempt you made from the feedback "
    "you observed. Here is another teacher-authored illustration, not workshop evidence:")
REFRESHER_EXAMPLES = (
    "I submitted 'amber blue'. The verifier reported a score of 0.25; this attempt "
    "was not accepted. I have not yet tested another arrangement.",
    "I tried 'east'. The verifier reported a score of 1.00 and accepted this attempt. "
    "I should not assume other situations will behave the same way.",
    "My answer was 'right left'. The reported score was 0.00; this attempt was not "
    "accepted. A different attempt remains an untested possibility.",
)
SHAM_PARAGRAPH = (
    "You can take a moment to look over the situation in front of you. Puzzles can "
    "involve different relationships, and the same surface appearance need not mean "
    "the same underlying constraints. Consider how the parts fit together and keep "
    "the whole situation in view. It is fine to pause and consider another possibility. "
    "These general illustrations offer encouragement, not answers you should use.")
SHAM_EXAMPLES = (
    "An arrangement with several pieces may be easier to consider one relationship "
    "at a time while keeping the overall constraints in view.",
    "Two situations can look similar at first glance yet depend on different "
    "relationships between the pieces they contain.",
    "A possibility that seems natural initially is not the only possibility worth "
    "considering when several constraints apply together.",
)
SHAM_REFRESHER_LINE = (
    "Take a moment to consider the whole situation and how its parts fit together. "
    "Here is another general teacher-authored illustration, not workshop evidence:")
SHAM_REFRESHER_EXAMPLES = (
    "Several local relationships may need to be considered together before a whole "
    "arrangement feels consistent with the situation.",
    "A pause can make room for another possibility without requiring an immediate "
    "choice between all the alternatives.",
    "An unfamiliar arrangement can still contain relationships similar to ones "
    "that were easier to notice in another setting.",
)

_FEEDBACK = re.compile(r"attempt ([1-9]\d*): verifier score ([01]\.\d{2}) "
                       r"\((accepted|not accepted; partial credit|not accepted)\)\Z")
_EMPTY = re.compile(r"INVALID: attempt ([1-9]\d*) was empty\Z")
_FOREIGN = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(
    re.escape(term) for term in DEPLOYMENT_LEAK_TERMS + ["compiler"])
    + r")(?![A-Za-z0-9_])", re.I)
_ACTION = re.compile(r"\b(?:I\s+(?:submitted|tried|entered|gave|answered(?:\s+with)?)"
                     r"|my\s+(?:answer|attempt|submission)\s+was)\s*:?\s*", re.I)
_NUMBER = r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
_SCORES = [re.compile(pattern, re.I) for pattern in (
    r"\b(?:verifier(?:'s)?\s+(?:reported\s+)?score|reported\s+score|score)"
    r"\s*(?:was|is|of|:|=)?\s*(?P<score>" + _NUMBER + r")(?!\w|\.\d)",
    r"\b(?:got|received|earned)\s+(?P<score>" + _NUMBER + r")\s+from\s+the\s+verifier\b",
    r"\bverifier\s+(?:reported|returned|gave\s+me)\s+(?P<score>" + _NUMBER + r")(?!\w|\.\d)",
)]
_NUMERIC = re.compile(r"(?<![\w.])" + _NUMBER + r"(?!\w|\.\d)")
_ATTEMPT = re.compile(r"\battempt\s+(\d+)\b", re.I)
_NEGATIVE = re.compile(r"\b(?:(?:not|never)\s+(?:fully\s+)?accepted|"
                       r"(?:wasn't|isn't)\s+accepted|rejected)\b", re.I)
_POSITIVE = re.compile(r"\b(?:accepted|full\s+credit|fully\s+correct)\b", re.I)
_REFERENCE = re.compile(r"\b(?:(?:correct|reference|expected|actual)\s+answer|answer\s+key|"
                        r"answer\s+should\s+be|solution\s+is)\b", re.I)
_NEGATED_SCORE = re.compile(r"\b(?:did\s+not|didn't|never)\s+(?:receive|get|earn|observe|see)"
                            r"\s+(?:a\s+)?(?:verifier\s+)?(?:score\b|" + _NUMBER + r")", re.I)


class InvalidFeedback(ValueError):
    pass


@dataclass(frozen=True)
class RecordFacts:
    episode_id: str
    execution_id: str
    tick: int
    action: str
    attempt: int
    reported_score: str | None
    score: float | None
    verdict: str

    @property
    def measured(self) -> bool:
        return self.reported_score is not None


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).translate(
        str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})).split())


def facts_from_act(act: dict) -> RecordFacts:
    """Project an externally source-verified ACT, excluding all answer-key fields."""
    if act.get("kind") != "act":
        raise InvalidFeedback("not-an-act")
    episode = act.get("episode_id")
    if not isinstance(episode, str) or not re.fullmatch(r"rg/[a-z0-9_]+/\d+", episode):
        raise InvalidFeedback("not-a-reasoning-episode")
    if not isinstance(act.get("execution_id"), str) or not act["execution_id"]:
        raise InvalidFeedback("missing-execution-id")
    if type(act.get("tick")) is not int or act["tick"] < 1:
        raise InvalidFeedback("invalid-tick")
    action, outcome = act.get("action"), act.get("outcome")
    if not isinstance(action, str) or not isinstance(outcome, str):
        raise InvalidFeedback("missing-action-or-feedback")
    if _FOREIGN.search(action + "\n" + outcome):
        raise InvalidFeedback("foreign-domain-content")
    empty = _EMPTY.fullmatch(outcome)
    if empty:
        return RecordFacts(episode, act["execution_id"], act["tick"], action,
                           int(empty[1]), None, None, "unmeasured")
    match = _FEEDBACK.fullmatch(outcome)
    if not match or not action.strip():
        raise InvalidFeedback("unrecognized-or-unmeasured-feedback")
    score = act.get("score")
    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
        raise InvalidFeedback("invalid-authoritative-score")
    expected = "accepted" if score == 1 else "not accepted; partial credit" if score > 0 else "not accepted"
    if f"{score:.2f}" != match[2] or expected != match[3]:
        raise InvalidFeedback("feedback-score-or-verdict-mismatch")
    return RecordFacts(episode, act["execution_id"], act["tick"], action,
                       int(match[1]), match[2], float(score), match[3])


def outcome_block(facts: RecordFacts, label: str = "NOTE_AFTER") -> str:
    """Render only own action, identifiers and observed feedback, never a task key."""
    if label not in ("NOTE_AFTER", "Scratchpad"):
        raise ValueError("unsupported record field")
    lines = [f"Situation: {facts.episode_id}", f"Execution: {facts.execution_id}",
             f"Attempt: {facts.attempt}", "ACT submitted: " + json.dumps(facts.action, ensure_ascii=False)]
    if facts.measured:
        lines += [f"Displayed verifier score: {facts.reported_score}", f"Feedback: {facts.verdict}"]
    else:
        lines += ["Measured feedback: unavailable", "This attempt has no measured score."]
    return "\n".join(lines + ["", label + ":"])


def _teacher_echo(text: str) -> bool:
    canonical = lambda value: " ".join(re.findall(r"\w+", _normalize(value).casefold()))
    normalized = " " + canonical(text) + " "
    payloads = (LESSON_PARAGRAPH, REFRESHER_LINE, SHAM_PARAGRAPH, SHAM_REFRESHER_LINE,
                *LESSON_EXAMPLES, *REFRESHER_EXAMPLES, *SHAM_EXAMPLES, *SHAM_REFRESHER_EXAMPLES)
    return any(" " + canonical(payload) + " " in normalized for payload in payloads)


def judge_record(text: str, facts: RecordFacts) -> dict:
    """Conservative single-event content judgment; never an admission/count bypass."""
    def result(reason, eligible=False):
        return dict(content_eligible=eligible, reason=reason, policy_version=POLICY_VERSION,
                    scope=POLICY_SCOPE, requires_external_source_match=True)
    if not facts.measured:
        return result("unmeasured-feedback")
    if not isinstance(text, str) or not text.strip():
        return result("empty-record")
    if _FOREIGN.search(text):
        return result("foreign-domain-content")
    if _teacher_echo(text):
        return result("teacher-illustration-echo")
    if _REFERENCE.search(text):
        return result("unsupported-reference-answer-claim")
    normalized, action = _normalize(text), _normalize(facts.action)
    masked = list(normalized)
    descriptions = list(_ACTION.finditer(normalized))
    if not descriptions:
        return result("missing-first-person-action")
    for description in descriptions:
        prefix = normalized[:description.start()]
        if not re.search(r"(?:^|[.!?;]\s+)(?:(?:After|When|Then|Next|Previously|Earlier|This time)\s+"
                         r"|On attempt\s+\d+,?\s+)?$", prefix, re.I):
            return result("unsupported-first-person-context")
        start = description.end()
        quoted = start < len(normalized) and normalized[start] in ('"', "'", "`")
        quote = normalized[start] if quoted else None
        start += int(quoted)
        end = start + len(action)
        if normalized[start:end] != action:
            return result("action-mismatch")
        rest = normalized[end:]
        if quoted and not rest.startswith(quote):
            return result("action-mismatch")
        if not quoted and rest and not re.match(
                r"[.!?](?:\s|$)|[,;]\s*(?:and|then|but|the|it|this|I|score|verifier|reported)\b"
                r"|\s+(?:and|then|but|with|which)\b", rest, re.I):
            return result("ambiguous-action-description")
        masked[start:end] = " " * (end - start)
    remainder = "".join(masked)
    if _NEGATED_SCORE.search(remainder):
        return result("unsupported-negated-score-claim")
    scores = [match for pattern in _SCORES for match in pattern.finditer(remainder)]
    if not scores:
        return result("missing-numeric-verifier-score")
    for match in scores:
        if Decimal(match["score"]) != Decimal(facts.reported_score):
            return result("score-mismatch")
        if remainder[match.end("score"):].lstrip().startswith("%"):
            return result("unsupported-score-unit")
        masked[match.start("score"):match.end("score")] = " " * len(match["score"])
    for match in _ATTEMPT.finditer(remainder):
        if int(match[1]) != facts.attempt:
            return result("attempt-mismatch")
        masked[match.start(1):match.end(1)] = " " * len(match[1])
    if _NUMERIC.search("".join(masked)):
        return result("unsupported-numeric-claim")
    if _NEGATIVE.search(remainder) and facts.verdict == "accepted":
        return result("verdict-mismatch")
    if _POSITIVE.search(_NEGATIVE.sub("", remainder)) and facts.verdict != "accepted":
        return result("verdict-mismatch")
    if re.search(r"\bpartial credit\b", remainder, re.I) and facts.verdict != "not accepted; partial credit":
        return result("verdict-mismatch")
    if re.search(r"\bno credit\b", remainder, re.I) and facts.score != 0:
        return result("verdict-mismatch")
    return result("faithful-single-event-record", True)


def lesson_block(mode: str, completed_sleeps: int) -> str | None:
    """Fixed q14 delivery timing; mode/phase only, never conditioned on child scores."""
    if mode not in ("none", "lesson", "sham") or type(completed_sleeps) is not int or completed_sleeps < 0:
        raise ValueError("invalid teaching mode or phase")
    if mode == "none" or completed_sleeps >= 4:
        return None
    sham = mode == "sham"
    if completed_sleeps == 0:
        paragraph = SHAM_PARAGRAPH if sham else LESSON_PARAGRAPH
        examples = SHAM_EXAMPLES if sham else LESSON_EXAMPLES
    else:
        paragraph = SHAM_REFRESHER_LINE if sham else REFRESHER_LINE
        examples = [(SHAM_REFRESHER_EXAMPLES if sham else REFRESHER_EXAMPLES)[completed_sleeps - 1]]
    return "\n".join(["=== A NOTE FROM YOUR TEACHER ===", paragraph,
                      "Teacher-authored illustrations only; invented, not observations from this life.",
                      *("- " + example for example in examples)])


def lesson_receipt(mode: str, completed_sleeps: int) -> dict | None:
    """Pure receipt constructor: caller persists it before exposing these bytes."""
    text = lesson_block(mode, completed_sleeps)
    if text is None:
        return None
    return dict(kind="teacher_illustration", source="q14 intent, trait-domain adaptation",
                source_path="organism_v6/preschool_reasoning.py",
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                version=POLICY_VERSION, mode=mode, sleeps_done=completed_sleeps,
                teacher_authored=True, factual_evidence=False, text=text,
                text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                token_budget_match="unverified; requires actual tokenizer before launch")


class ReasoningGateError(RuntimeError):
    """Missing or contradictory evidence; the caller must not train on failure."""


def _require(condition, reason):
    if not condition:
        raise ReasoningGateError(reason)


def _encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(content):
    return hashlib.sha256(content).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _bad_constant(value):
    raise ReasoningGateError("nonfinite JSON constant: " + value)


def _json(content):
    try:
        return json.loads(content, object_pairs_hook=_object, parse_constant=_bad_constant)
    except (ValueError, UnicodeError) as error:
        raise ReasoningGateError("invalid JSON evidence") from error


def _read(path):
    path = Path(path).absolute()
    _require(not any(part.is_symlink() for part in (path, *path.parents)), "symlink evidence")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        _require(stat.S_ISREG(before.st_mode), "evidence must be a regular file")
        content = source.read()
        after = os.fstat(source.fileno())
    _require((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
             == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "evidence changed during read")
    return content


def _lines(content):
    lines = content.splitlines(keepends=True)
    _require(all(line.endswith(b"\n") and not line.endswith(b"\r\n") for line in lines),
             "evidence requires complete LF-delimited lines")
    rows = [_json(line) for line in lines]
    _require(all(isinstance(row, dict) for row in rows), "evidence rows must be objects")
    return lines, rows


def _immutable(path, content):
    path = Path(path).absolute()
    _require(not any(part.is_symlink() for part in path.parents), "symlink output directory")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(content)
        target.flush()
        os.fsync(target.fileno())
        os.fchmod(target.fileno(), 0o444)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _measurement(facts):
    return dict(attempt=facts.attempt, reported_score=facts.reported_score,
                verifier_score=facts.score, verdict=facts.verdict, measured=facts.measured,
                status="success" if facts.measured else "unmeasured")


def _identity_status(identity):
    if not isinstance(identity, dict):
        return "UNAVAILABLE"
    if identity.get("test_mock") is True or identity.get("backend") in ("mock", "fake", "test_mock"):
        return "TEST_MOCK"
    if identity.get("backend") != "vllm":
        return "UNAVAILABLE"
    if not isinstance(identity.get("model_input"), str) or not identity["model_input"].strip():
        return "UNAVAILABLE"
    if "adapter_input" not in identity:
        return "UNAVAILABLE"
    adapter, files = identity["adapter_input"], identity.get("adapter_files")
    if not isinstance(files, dict):
        return "UNAVAILABLE"
    if adapter is None:
        if files:
            return "UNAVAILABLE"
    else:
        weight_names = {"adapter_model.safetensors", "adapter_model.bin"} & files.keys()
        if (not isinstance(adapter, str) or not adapter.strip() or len(weight_names) != 1
                or files.keys() != weight_names | {"adapter_config.json"}):
            return "UNAVAILABLE"
    if any(not isinstance(name, str) or not isinstance(digest, str)
           or not re.fullmatch(r"[0-9a-f]{64}", digest) for name, digest in files.items()):
        return "UNAVAILABLE"
    if type(identity.get("default_max_tokens")) is not int or identity["default_max_tokens"] < 1:
        return "UNAVAILABLE"
    temperature = identity.get("default_temperature")
    if type(temperature) not in (int, float) or not math.isfinite(temperature) or temperature < 0:
        return "UNAVAILABLE"
    return "RECORDED_BACKEND"


def _capture_identity(model):
    method = getattr(model, "generation_identity", None)
    if not callable(method):
        return {"backend": "unavailable", "reason": "missing-generation-identity"}
    try:
        identity = method()
        return _json(_encoded(identity))
    except Exception as error:
        return {"backend": "unavailable", "reason": type(error).__name__}


def _append_generation(ledger, records, expected_bytes):
    import fcntl
    descriptor = os.open(ledger.path, os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "a+b") as target:
        fcntl.flock(target.fileno(), fcntl.LOCK_EX)
        target.seek(0)
        _require(target.read() == expected_bytes, "ledger changed during generation")
        target.write(b"".join(_encoded(record) for record in records))
        target.flush()
        os.fsync(target.fileno())


def _generation_rejection(record, facts, batch_records):
    generation = record.get("generation")
    if not isinstance(generation, dict):
        return "generation-missing"
    if (generation.get("schema") != "reasoning-post-outcome-generation-v1"
            or generation.get("prompt_scope") != "batch_user_text_before_chat_template"):
        return "generation-unsupported-schema"
    identity = generation.get("backend_identity")
    status = _identity_status(identity)
    if generation.get("provenance_status") != status or status != "RECORDED_BACKEND":
        return "generation-not-real-provenance"
    if generation.get("backend_identity_sha256") != _sha(_encoded(identity)):
        return "generation-identity-hash-mismatch"
    prompt = generation.get("prompt")
    if not isinstance(prompt, str) or generation.get("prompt_sha256") != _sha(prompt.encode()):
        return "generation-prompt-hash-mismatch"
    if not prompt.endswith("\n\n" + outcome_block(facts, "NOTE_AFTER")):
        return "generation-prompt-outcome-mismatch"
    if generation.get("output_sha256") != _sha(record["text"].encode()):
        return "generation-output-hash-mismatch"
    if type(generation.get("max_tokens")) is not int or generation["max_tokens"] < 1:
        return "generation-invalid-token-budget"
    if generation.get("temperature") != identity["default_temperature"]:
        return "generation-sampling-mismatch"
    base_seed, salt = generation.get("base_seed"), generation.get("seed_salt")
    if type(salt) is not int or base_seed is not None and type(base_seed) is not int:
        return "generation-invalid-seed"
    seed = None if base_seed is None else (zlib.crc32(facts.execution_id.encode()) ^ base_seed ^ salt) & 0x7fffffff
    if _encoded(generation.get("seed")) != _encoded(seed):
        return "generation-seed-mismatch"
    count, index = generation.get("batch_size"), generation.get("batch_index")
    if type(count) is not int or count < 1 or type(index) is not int or not 0 <= index < count:
        return "generation-invalid-cardinality"
    batch_id = generation.get("batch_id")
    if not isinstance(batch_id, str) or not re.fullmatch(r"[0-9a-f]{64}", batch_id):
        return "generation-invalid-batch-id"
    group = batch_records.get(batch_id, [])
    if len(group) != count:
        return "generation-incomplete-batch"
    indices = [row["generation"].get("batch_index") for row in group]
    if any(type(value) is not int for value in indices) or indices != list(range(count)):
        return "generation-ambiguous-batch"
    for row in group:
        evidence = row["generation"]
        for field in ("backend_identity_sha256", "max_tokens", "temperature", "base_seed", "seed_salt",
                      "batch_size", "ledger_prefix_sha256"):
            if _encoded(evidence.get(field)) != _encoded(generation.get(field)):
                return "generation-batch-config-mismatch"
    expected_id = _sha(_encoded(dict(ledger_sha256=generation.get("ledger_prefix_sha256"),
                                    execution_ids=[row["execution_id"] for row in group],
                                    prompt_sha256=[row["generation"].get("prompt_sha256") for row in group],
                                    output_sha256=[row["generation"].get("output_sha256") for row in group],
                                    identity=identity, max_tokens=generation["max_tokens"],
                                    seeds=None if base_seed is None else [row["generation"].get("seed") for row in group])))
    if batch_id != expected_id:
        return "generation-batch-hash-mismatch"
    return None


class PostOutcomeSlot(_BaseSlot):
    """Reasoning-only slot; pending entries MUST contain the exact appended act_row.

    Durable occurrence reservation/seed derivation are shared with the original
    slot. No compiler facts are read, and model output bytes are never truncated.
    The inherited block API is intentionally disabled: use outcome_block instead.
    """

    def block(self, *args, **kwargs):
        raise ReasoningGateError("reasoning slot requires raw ACT via run_round")

    def run_round(self, model, drivers, ledger, gen_seed) -> int:
        _require((self.label, self.kind) in (("NOTE_AFTER", "note_after"),
                                           ("Scratchpad", "scratchpad")), "invalid slot configuration")
        ledger_bytes = _read(ledger.path)
        _raw_lines, recorded = _lines(ledger_bytes)
        _ledger_provenance(recorded, getattr(ledger, "prov", {}))
        executions = {}
        for row in recorded:
            if row.get("kind") == "act":
                executions.setdefault(row.get("execution_id"), []).append(row)
        requests = []
        pending_ids = set()
        for driver in drivers:
            for pending in driver.pending_after:
                action = pending.get("act_row")
                _require(isinstance(action, dict), "batch_loop must supply pending['act_row']")
                facts = facts_from_act(action)
                matches = executions.get(facts.execution_id, [])
                _require(len(matches) == 1 and _encoded(matches[0]) == _encoded(action),
                         "pending ACT is not uniquely recorded")
                _require(facts.execution_id not in pending_ids, "duplicate pending execution")
                _require(not any(row.get("kind") == self.kind
                                 and row.get("execution_id") == facts.execution_id for row in recorded),
                         "execution already has a post-outcome record")
                pending_ids.add(facts.execution_id)
                for field in ("episode_id", "execution_id", "tick", "action", "outcome",
                              "occurrence_id", "occurrence_index"):
                    _require(field in action and pending.get(field) == action[field],
                             "pending ACT mismatch: " + field)
                context = getattr(driver, "_last_prompt", "")
                prompt = context.rstrip("\n") + "\n\n" + outcome_block(facts, self.label)
                _require(not _FOREIGN.search(prompt), "foreign-domain slot prompt")
                requests.append((action, facts, prompt))
        if not requests:
            return 0
        seeds = None if gen_seed is None else [
            (zlib.crc32(facts.execution_id.encode()) ^ gen_seed ^ self.seed_salt) & 0x7fffffff
            for _action, facts, _prompt in requests]
        identity = _capture_identity(model)
        identity_status = _identity_status(identity)
        temperature = identity.get("default_temperature") if isinstance(identity, dict) else None
        started = time.monotonic()
        outputs = model.batch([prompt for _action, _facts, prompt in requests],
                              max_tokens=self.max_tokens, seeds=seeds)
        elapsed = time.monotonic() - started
        _require(isinstance(outputs, (list, tuple)) and len(outputs) == len(requests)
                 and all(isinstance(text, str) for text in outputs), "incomplete slot generation batch")
        _require(_encoded(_capture_identity(model)) == _encoded(identity), "backend identity changed during generation")
        batch_id = _sha(_encoded(dict(ledger_sha256=_sha(ledger_bytes),
                                     execution_ids=[facts.execution_id for _act, facts, _prompt in requests],
                                     prompt_sha256=[_sha(prompt.encode()) for _act, _facts, prompt in requests],
                                     output_sha256=[_sha(text.encode()) for text in outputs],
                                     identity=identity, max_tokens=self.max_tokens, seeds=seeds)))
        records = []
        for index, ((action, facts, prompt), text) in enumerate(zip(requests, outputs)):
            record = {field: action[field] for field in
                      ("episode_id", "execution_id", "tick", "occurrence_id", "occurrence_index",
                       "action", "outcome", "score")}
            record.update({field: action[field] for field in _LEDGER_PROVENANCE_FIELDS if field in action})
            record.update(_measurement(facts))
            record.update(kind=self.kind, speaker="child", label=self.label, text=text,
                          policy_version=POLICY_VERSION, gen_seconds=elapsed / len(requests),
                          n_chars=len(text))
            record["generation"] = dict(schema="reasoning-post-outcome-generation-v1",
                                        prompt_scope="batch_user_text_before_chat_template",
                                        prompt=prompt, prompt_sha256=_sha(prompt.encode()),
                                        output_sha256=_sha(text.encode()), max_tokens=self.max_tokens,
                                        seed=seeds[index] if seeds is not None else None,
                                        base_seed=gen_seed, seed_salt=self.seed_salt, temperature=temperature,
                                        backend_identity=identity, backend_identity_sha256=_sha(_encoded(identity)),
                                        provenance_status=identity_status, batch_id=batch_id,
                                        batch_size=len(requests), batch_index=index,
                                        ledger_prefix_sha256=_sha(ledger_bytes))
            records.append(record)
        _append_generation(ledger, records, ledger_bytes)
        for driver in drivers:
            driver.pending_after = []
        self.n_calls += 1
        self.n_generations += len(requests)
        self.total_seconds += elapsed
        self.total_chars += sum(len(text) for text in outputs)
        return len(requests)


def _lesson_rows(content):
    _raw, receipts = _lines(content)
    phases = set()
    modes = set()
    for receipt in receipts:
        phase, mode = receipt.get("sleeps_done"), receipt.get("mode")
        _require(type(phase) is int and phase not in phases, "ambiguous teaching phase")
        try:
            expected = lesson_receipt(mode, phase)
        except ValueError as error:
            raise ReasoningGateError("invalid teaching receipt") from error
        _require(expected is not None and receipt == expected, "teaching receipt content/hash mismatch")
        phases.add(phase)
        modes.add(mode)
    _require(len(modes) <= 1, "teaching mode changed within life")
    return receipts


def _ledger_provenance(rows, declared=None):
    """Bind exact stamps, without dropping missing, extra or contradictory metadata."""
    stamps = [{field: row[field] for field in _LEDGER_PROVENANCE_FIELDS if field in row} for row in rows]
    if declared is None:
        expected = next((stamp for stamp in stamps if stamp), {})
    else:
        _require(isinstance(declared, dict) and declared.keys() <= set(_LEDGER_PROVENANCE_FIELDS),
                 "unsupported declared ledger provenance")
        expected = dict(declared)
    if expected:
        families = _json(_read(FAMILIES_FILE))
        _require(expected.get("gym") == "reasoning_gym"
                 and expected.get("exposure_domain") == "reasoning_gym:" + ",".join(families["train_families"]),
                 "wrong ledger gym or exposure domain")
        if "clone_id" in expected:
            _require(type(expected["clone_id"]) is int and expected["clone_id"] >= 0,
                     "invalid ledger clone identity")
    _require(all(_encoded(stamp) == _encoded(expected) for stamp in stamps),
             "contradictory or missing ledger provenance stamps")
    return dict(expected)


def _teacher_row(receipt, provenance=None):
    row = dict(kind="parent_turn", speaker="teacher", teacher_authored=True,
               factual_evidence=False, text=receipt["text"],
               lesson_receipt_sha256=_sha(_encoded(receipt)), policy_version=POLICY_VERSION)
    row.update(provenance or {})
    return row


def deliver_lesson(life: str, mode: str, sleeps_done: int, log=None, *, ledger=None) -> str | None:
    """Append/fsync receipt AND teacher influence before delivery; reject resume drift."""
    import fcntl
    expected = lesson_receipt(mode, sleeps_done)
    if expected is not None:
        _require(ledger is not None, "teaching requires the append-only life ledger")
        _require(Path(ledger.path).absolute().parent == Path(life).absolute(), "teaching ledger outside life")
    path = Path(life) / "lesson_deliveries.jsonl"
    _require(path.parent.is_dir() and not any(part.is_symlink() for part in
                                            (path, *path.absolute().parents)), "invalid teaching path")
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+b") as target:
        fcntl.flock(target.fileno(), fcntl.LOCK_EX)
        receipts = _lesson_rows(target.read())
        _require(all(row["mode"] == mode for row in receipts), "teaching mode changed within life")
        if expected is None:
            return None
        prior = [row for row in receipts if row["sleeps_done"] == sleeps_done]
        before_rows = ledger.rows()
        provenance = _ledger_provenance(before_rows, getattr(ledger, "prov", {}))
        teacher = _teacher_row(expected, provenance)
        matches = [row for row in before_rows
                   if row.get("lesson_receipt_sha256") == teacher["lesson_receipt_sha256"]]
        _require((len(matches) == 1 and _encoded(matches[0]) == _encoded(teacher)) if prior else not matches,
                 "incomplete or ambiguous prior teaching influence")
        if not prior:
            _require(not receipts or sleeps_done > max(row["sleeps_done"] for row in receipts),
                     "teaching phases out of order")
            stored = ledger.append(teacher)
            _require(isinstance(stored, dict) and _encoded(stored) == _encoded(teacher),
                     "stored teacher row contradicts declared provenance")
            _raw, after_rows = _lines(_read(ledger.path))
            _require(len(after_rows) == len(before_rows) + 1
                     and _encoded(after_rows[:-1]) == _encoded(before_rows)
                     and _encoded(after_rows[-1]) == _encoded(stored), "teacher append receipt differs from ledger")
            with open(ledger.path, "rb") as source:
                os.fsync(source.fileno())
            target.seek(0, os.SEEK_END)
            target.write(_encoded(expected))
            target.flush()
            os.fsync(target.fileno())
    if log:
        log(f"[reasoning preschool] teaching mode={mode} phase={sleeps_done}")
    return expected["text"]


def _copy_key(text):
    return " ".join(re.findall(r"\w+", _normalize(text).casefold()))


def _train_id(episode, families):
    match = re.fullmatch(r"rg/([a-z0-9_]+)/([0-9]+)", episode or "")
    lower, upper = families["seed_ranges"]["train"]
    return bool(match and match[1] in families["train_families"] and lower <= int(match[2]) < upper)


def _validate_child_notes(rows, families):
    """NOTE is ledger-bound child-visible state, not a grounded write record.

    The producer supplies episode/tick/note and ledger stamps, not an ACT link
    or generation receipt. Validate that shape without inventing either. An
    omitted speaker is the producer's implicit child; explicit others reject.
    """
    _require(bool(_ledger_provenance(rows)), "NOTE requires ledger provenance stamps")
    allowed = {"kind", "episode_id", "tick", "note", "speaker", "exposure_status",
               *_LEDGER_PROVENANCE_FIELDS}
    reservations = {}
    for row in rows:
        episode = row.get("episode_id")
        if row.get("kind") == "episode_occurrence" and isinstance(episode, str):
            reservations[episode] = row
        if row.get("kind") != "note":
            continue
        _require(row.keys() <= allowed, "unsupported NOTE fields")
        _require(row.get("speaker", "child") == "child", "NOTE is not child-authored")
        _require(isinstance(row.get("note"), str) and row["note"].strip(), "missing NOTE text")
        _require(type(row.get("tick")) is int and row["tick"] > 0, "invalid NOTE tick")
        _require(isinstance(episode, str) and _train_id(episode, families),
                 "non-training NOTE episode")
        visit = reservations.get(episode, {})
        occurrence_index = visit.get("occurrence_index")
        _require(type(occurrence_index) is int and occurrence_index > 0
                 and visit.get("occurrence_id") == f"{episode}#occ{occurrence_index}"
                 and visit.get("slot_kind") == "note_after",
                 "NOTE requires preceding episode reservation")


def _validate_influences(rows, families):
    allowed = {"episode_occurrence", "act", "note_after", "note", "thought", "parent_turn"}
    if any(row.get("kind") == "note" for row in rows):
        _validate_child_notes(rows, families)
    for row in rows:
        _require(row.get("kind") in allowed, "unknown or probe ledger influence")
        _require(row.get("exposure_status", "UNEXPOSED") == "UNEXPOSED", "tainted ledger influence")
        content = _encoded(row).decode()
        _require(not _FOREIGN.search(content) and not re.search(
            r"QUARANTINE_TASK_EXPOSED|DEV_UNVERIFIED_PROVENANCE|bootstrap[ _-]*v[123]", content, re.I),
            "foreign or quarantined ledger influence")
        if "episode_id" in row:
            _require(_train_id(row["episode_id"], families), "non-training episode in life ledger")
        for episode in re.findall(r"rg/[a-z0-9_]+/[0-9]+", content):
            _require(_train_id(episode, families), "held-out episode reference in life ledger")
        if row["kind"] == "parent_turn":
            _require(isinstance(row.get("text"), str) and row["text"].strip(), "missing parent text")


def _judge_source(record_index, rows, executions, notes, reservations, lesson_payloads, batch_records):
    record = rows[record_index]
    execution = record.get("execution_id")
    sources = executions.get(execution, [])
    if not sources:
        return "provenance-orphan", None
    if len(sources) != 1 or len(notes.get(execution, [])) != 1:
        return "provenance-ambiguous-execution", None
    source_index = sources[0]
    if source_index >= record_index:
        return "provenance-pre-outcome-record", None
    source = rows[source_index]
    for field in ("episode_id", "execution_id", "tick", "action", "outcome", "score",
                  "occurrence_id", "occurrence_index"):
        if (field not in record or field not in source
                or _encoded(record[field]) != _encoded(source[field])):
            return "provenance-mismatch-" + field, None
    visits = reservations.get(source.get("occurrence_id"), [])
    if len(visits) != 1 or visits[0] >= source_index:
        return "provenance-missing-or-ambiguous-visit", None
    visit = rows[visits[0]]
    if type(source.get("occurrence_index")) is not int or type(source.get("tick")) is not int:
        return "provenance-invalid-occurrence-or-tick", None
    if any(source.get(field) != visit.get(field) for field in
           ("episode_id", "occurrence_id", "occurrence_index")):
        return "provenance-visit-mismatch", None
    if not re.fullmatch(re.escape(source["occurrence_id"]) + rf"#t{source['tick']}a[1-9]\d*", execution):
        return "provenance-execution-id-mismatch", None
    try:
        facts = facts_from_act(source)
    except InvalidFeedback as error:
        return "provenance-" + str(error), None
    for field, value in _measurement(facts).items():
        if field not in record or _encoded(record[field]) != _encoded(value):
            return "provenance-mismatch-" + field, None
    if "status" in source and source["status"] != record["status"]:
        return "provenance-source-status-mismatch", None
    if record.get("speaker") != "child" or record.get("policy_version") != POLICY_VERSION:
        return "provenance-not-current-child-record", None
    text = record.get("text")
    if not isinstance(text, str):
        return "empty-record", None
    normalized = " " + _copy_key(text) + " "
    if any(" " + payload + " " in normalized for payload in lesson_payloads):
        return "provenance-lesson-echo", None
    verdict = judge_record(text, facts)
    if not verdict["content_eligible"]:
        return verdict["reason"], None
    rejection = _generation_rejection(record, facts, batch_records)
    return (rejection, None) if rejection else (None, source_index)


def gate_sleep(rows: list, life: str, sdir: str, mode: str, min_items: int = 64, log=None,
               slot_stats: dict | None = None, *, ledger_path: str,
               previous_manifest_sha256: str, exposure_status: str) -> dict:
    """Recheck ALL records and publish immutable, physical-line-bound gate evidence.

    Required keyword arguments are caller claims, not ancestry authentication.
    ledger_path must be the actual append-only training ledger, with rows equal
    to its parsed bytes. UNEXPOSED and the previous manifest pin must come from
    verified ancestry, never be inferred from this gate. A report is diagnostic
    until life_lineage and the trainer accept the returned hash-bound evidence.

    Each NEW sleep directory gets reasoning_ledger.jsonl, reasoning_lessons.jsonl,
    reasoning_gate_details.json and gate_receipt.json (enforce only). Receipts
    bind exact LF-inclusive physical row bytes and exact corpus bytes. Outputs
    are exclusive/read-only; retries or partial output require manual inspection.
    Shadow never edits corpus.json and cannot issue an ADMIT receipt. Insufficient
    records produce SKIP, not lineage admission, and preserve the min_items gate.
    Normalized text is deduplicated across the whole cumulative ledger, not just
    the latest batch. All previous admissions are recomputed against current rows.
    The returned source_gate_passed is NOT ancestry authentication or launch approval.
    Neutral probe APIs are intentionally unsupported in this module.
    """
    _require(mode in ("shadow", "enforce"), "reasoning gate requires shadow or enforce")
    _require(type(min_items) is int and min_items >= 64, "minimum record count cannot be lowered below 64")
    _require(exposure_status == "UNEXPOSED", "clean reasoning gate requires verified UNEXPOSED ancestry")
    _require(isinstance(previous_manifest_sha256, str)
             and re.fullmatch(r"[0-9a-f]{64}", previous_manifest_sha256), "missing previous manifest pin")
    life, sleep_dir = Path(life).absolute(), Path(sdir).absolute()
    _require(sleep_dir.parent == life and re.fullmatch(r"sleep_[0-9]+", sleep_dir.name)
             and sleep_dir.is_dir(), "expected existing life/sleep_N directory")
    outputs = ("reasoning_ledger.jsonl", "reasoning_lessons.jsonl", "reasoning_gate_details.json",
               "gate_receipt.json", "corpus_legacy.json", SKIP_MARKER,
               "reasoning_gate_transaction.json", "reasoning_corpus.pending")
    _require(not any((sleep_dir / name).exists() or (sleep_dir / name).is_symlink() for name in outputs),
             "sleep gate artifacts already exist; do not overwrite evidence")
    ledger_bytes = _read(ledger_path)
    lines, recorded = _lines(ledger_bytes)
    _require(_encoded(rows) == _encoded(recorded), "supplied rows differ from raw ledger")
    families_bytes = _read(FAMILIES_FILE)
    families = _json(families_bytes)
    _validate_influences(recorded, families)
    ledger_provenance = _ledger_provenance(recorded)
    teaching_path = life / "lesson_deliveries.jsonl"
    teaching_bytes = _read(teaching_path) if teaching_path.exists() or teaching_path.is_symlink() else b""
    teaching = _lesson_rows(teaching_bytes)
    expected_teachers = [_teacher_row(receipt, ledger_provenance) for receipt in teaching]
    actual_teachers = [row for row in recorded if row["kind"] == "parent_turn"]
    _require(_encoded(actual_teachers) == _encoded(expected_teachers),
             "teaching receipts and ledger influence inventory disagree")
    identity = dict(policy_version=POLICY_VERSION, policy_sha256=_sha(_read(__file__)),
                    families_sha256=_sha(families_bytes), ledger_provenance=ledger_provenance)
    previous = None
    earlier_dirs = [path for path in life.glob("sleep_*") if re.fullmatch(r"sleep_[0-9]+", path.name)]
    for earlier in sorted(earlier_dirs, key=lambda path: int(path.name.split("_")[-1])):
        if earlier == sleep_dir or not re.fullmatch(r"sleep_[0-9]+", earlier.name):
            continue
        if int(earlier.name.split("_")[-1]) >= int(sleep_dir.name.split("_")[-1]):
            _require(not (earlier / "reasoning_gate_details.json").exists(), "out-of-order gate sleep")
            continue
        snapshot = earlier / "reasoning_ledger.jsonl"
        detail = earlier / "reasoning_gate_details.json"
        if not snapshot.exists() and not detail.exists() and not (earlier / "reasoning_gate_transaction.json").exists():
            continue
        _require(snapshot.exists() and detail.exists(), "incomplete prior gate artifacts")
        candidate = verify_gate_commit(str(earlier))
        old_ledger, old_teaching = _read(snapshot), _read(earlier / "reasoning_lessons.jsonl")
        _require(candidate["identity"] == identity and candidate["mode"] == mode
                 and candidate["min_items"] == min_items, "gate policy/config changed across sleeps")
        _require(_sha(old_ledger) == candidate["ledger_sha256"]
                 and _sha(old_teaching) == candidate["lesson_sha256"], "prior evidence hash mismatch")
        _require(ledger_bytes.startswith(old_ledger) and teaching_bytes.startswith(old_teaching),
                 "ledger or teaching history is not append-only")
        if previous is None or candidate["rows_now"] > previous["rows_now"]:
            previous = candidate
    lesson_payloads = []
    for text in [receipt["text"] for receipt in teaching] + [row["text"] for row in recorded
                                                           if row["kind"] == "parent_turn"]:
        lesson_payloads.extend(_copy_key(part.removeprefix("- ")) for part in [text, *text.splitlines()]
                               if len(_copy_key(part).split()) >= 8)
    executions, notes, reservations, batch_records = {}, {}, {}, {}
    occurrence_indices = set()
    prefix_digest = hashlib.sha256()
    batch_prefixes = {}
    for index, row in enumerate(recorded):
        generation = row.get("generation")
        if row["kind"] == "note_after" and isinstance(generation, dict) and isinstance(generation.get("batch_id"), str):
            batch_prefixes.setdefault(generation["batch_id"], prefix_digest.hexdigest())
            batch_records.setdefault(generation["batch_id"], []).append(row)
        prefix_digest.update(lines[index])
        target = {"act": executions, "note_after": notes, "episode_occurrence": reservations}.get(row["kind"])
        if target is not None:
            key = row.get("occurrence_id" if row["kind"] == "episode_occurrence" else "execution_id")
            _require(isinstance(key, str) and key, "missing event identity")
            target.setdefault(key, []).append(index)
        if row["kind"] == "episode_occurrence":
            occurrence_index = row.get("occurrence_index")
            _require(type(occurrence_index) is int and occurrence_index > 0
                     and occurrence_index not in occurrence_indices, "ambiguous occurrence reservation")
            _require(row["occurrence_id"] == f"{row['episode_id']}#occ{occurrence_index}",
                     "invalid occurrence reservation")
            occurrence_indices.add(occurrence_index)
    items, admissions, judged, reasons = [], [], [], {}
    seen_text = set()
    since = previous["rows_now"] if previous else 0
    n_new = 0
    for record_index, record in enumerate(recorded):
        if record["kind"] != "note_after":
            continue
        rejection, source_index = _judge_source(record_index, recorded, executions, notes,
                                                reservations, lesson_payloads, batch_records)
        if rejection is None and record["generation"].get("ledger_prefix_sha256") != batch_prefixes[record["generation"]["batch_id"]]:
            rejection = "generation-ledger-prefix-mismatch"
        if rejection is None:
            canonical = _copy_key(record["text"])
            if canonical in seen_text:
                rejection = "duplicate-record"
            else:
                seen_text.add(canonical)
        judgment = dict(record_line=record_index, record_sha256=_sha(lines[record_index]),
                        execution_id=record.get("execution_id"), admitted=rejection is None,
                        reason=rejection or "admitted")
        if rejection:
            reasons[rejection] = reasons.get(rejection, 0) + 1
        else:
            admission = dict(record_line=record_index, record_sha256=_sha(lines[record_index]),
                             source_line=source_index, source_sha256=_sha(lines[source_index]))
            judgment.update(admission)
            admissions.append(admission)
            items.append(RECORD_ITEM.format(eid=record["episode_id"], text=record["text"]))
            n_new += int(record_index >= since)
        judged.append(judgment)
    corpus_path = sleep_dir / "corpus.json"
    legacy_bytes = _read(corpus_path) if corpus_path.exists() or corpus_path.is_symlink() else None
    legacy = _json(legacy_bytes) if legacy_bytes is not None else {"corpus": []}
    _require(isinstance(legacy, dict) and isinstance(legacy.get("corpus"), list), "invalid legacy corpus")
    corpus = dict(recipe="preschool_records_v1", corpus=items, principles=[],
                  n_new=n_new, n_dropped_legacy=len(legacy["corpus"]))
    corpus_bytes = _encoded(corpus)
    skipped = len(items) < min_items
    receipt = dict(schema_version=1, recipe="preschool_records_v1",
                   decision="SKIP" if skipped else "ADMIT", exposure_status=exposure_status,
                   previous_manifest_sha256=previous_manifest_sha256,
                   ledger_sha256=_sha(ledger_bytes), corpus_sha256=_sha(corpus_bytes), admissions=admissions)
    summary = dict(mode=mode, enforced=mode == "enforce", min_items=min_items,
                   training_skipped=skipped if mode == "enforce" else False,
                   source_gate_passed=mode == "enforce" and not skipped, ancestry_authenticated=False,
                   rows_since=since, rows_now=len(recorded), n_admitted_new=n_new,
                   n_admitted_total=len(items), record_items=len(items),
                   rejection_families=reasons, judged=judged, identity=identity,
                   ledger_sha256=_sha(ledger_bytes), lesson_sha256=_sha(teaching_bytes),
                   corpus_sha256=_sha(corpus_bytes) if mode == "enforce" else None,
                   gate_receipt_sha256=_sha(_encoded(receipt)) if mode == "enforce" else None,
                   gate_receipt_path=str(sleep_dir / "gate_receipt.json") if mode == "enforce" else None,
                   ledger_snapshot_path=str(sleep_dir / "reasoning_ledger.jsonl"),
                   slot=slot_stats, scope=POLICY_SCOPE)
    _require(_read(ledger_path) == ledger_bytes, "ledger changed during gate")
    _require(_sha(_read(__file__)) == identity["policy_sha256"]
             and _read(FAMILIES_FILE) == families_bytes, "policy changed during gate")
    current_teaching = _read(teaching_path) if teaching_path.exists() else b""
    _require(current_teaching == teaching_bytes, "teaching history changed during gate")
    artifact_hashes = {"reasoning_ledger.jsonl": _sha(ledger_bytes),
                       "reasoning_lessons.jsonl": _sha(teaching_bytes),
                       "reasoning_gate_details.json": _sha(_encoded(summary))}
    if mode == "enforce":
        artifact_hashes.update({"corpus.json": _sha(corpus_bytes), "gate_receipt.json": _sha(_encoded(receipt))})
        if legacy_bytes is not None:
            artifact_hashes["corpus_legacy.json"] = _sha(legacy_bytes)
        if skipped:
            artifact_hashes[SKIP_MARKER] = _sha(f"{len(items)} admitted records < {min_items}\n".encode())
    elif legacy_bytes is not None:
        artifact_hashes["corpus.json"] = _sha(legacy_bytes)
    transaction = dict(schema_version=1, mode=mode, artifacts=artifact_hashes,
                       previous_manifest_sha256=previous_manifest_sha256,
                       exposure_status=exposure_status, min_items=min_items, identity=identity)
    _immutable(sleep_dir / "reasoning_gate_transaction.json", _encoded(transaction))
    _immutable(sleep_dir / "reasoning_ledger.jsonl", ledger_bytes)
    _immutable(sleep_dir / "reasoning_lessons.jsonl", teaching_bytes)
    if mode == "enforce":
        if legacy_bytes is not None:
            _immutable(sleep_dir / "corpus_legacy.json", legacy_bytes)
        temporary = sleep_dir / "reasoning_corpus.pending"
        _immutable(temporary, corpus_bytes)
        os.replace(temporary, corpus_path)
        if skipped:
            _immutable(sleep_dir / SKIP_MARKER, f"{len(items)} admitted records < {min_items}\n".encode())
    _immutable(sleep_dir / "reasoning_gate_details.json", _encoded(summary))
    if mode == "enforce":
        _immutable(sleep_dir / "gate_receipt.json", _encoded(receipt))
    verify_gate_commit(str(sleep_dir))
    if log:
        log(f"[reasoning gate {mode}] records={len(items)} min={min_items} skipped={skipped}")
    return summary


def verify_gate_commit(sdir: str) -> dict:
    """Verify the complete transaction on resume; partial/corrupt output cannot train."""
    directory = Path(sdir)
    try:
        transaction = _json(_read(directory / "reasoning_gate_transaction.json"))
        _require(transaction.get("schema_version") == 1, "unsupported gate transaction")
        artifacts = transaction.get("artifacts")
        _require(isinstance(artifacts, dict) and artifacts, "missing transaction artifacts")
        for name, digest in artifacts.items():
            _require(isinstance(name, str) and Path(name).name == name, "invalid transaction artifact path")
            _require(_sha(_read(directory / name)) == digest, "gate transaction artifact mismatch: " + name)
        report = _json(_read(directory / "reasoning_gate_details.json"))
        _require(report["mode"] == transaction["mode"] and report["identity"] == transaction["identity"]
                 and report["min_items"] == transaction["min_items"], "gate transaction config mismatch")
        _require({"reasoning_ledger.jsonl", "reasoning_lessons.jsonl", "reasoning_gate_details.json"} <= artifacts.keys(),
                 "incomplete gate transaction inventory")
        if report["mode"] == "enforce":
            _require({"corpus.json", "gate_receipt.json"} <= artifacts.keys(), "missing admission transaction artifacts")
            receipt_bytes = _read(directory / "gate_receipt.json")
            receipt = _json(receipt_bytes)
            _require(_sha(receipt_bytes) == report["gate_receipt_sha256"]
                     and receipt["previous_manifest_sha256"] == transaction["previous_manifest_sha256"]
                     and receipt["exposure_status"] == transaction["exposure_status"]
                     and receipt["ledger_sha256"] == artifacts["reasoning_ledger.jsonl"]
                     and receipt["corpus_sha256"] == artifacts["corpus.json"], "gate receipt transaction mismatch")
            _require((receipt["decision"] == "ADMIT") == report["source_gate_passed"]
                     and (receipt["decision"] == "SKIP") == report["training_skipped"], "gate decision mismatch")
            _require((directory / SKIP_MARKER).exists() == report["training_skipped"], "skip marker mismatch")
        return report
    except (OSError, KeyError, TypeError) as error:
        raise ReasoningGateError("incomplete gate transaction") from error


def training_skipped(sdir: str) -> bool:
    report = verify_gate_commit(sdir)
    return report["mode"] != "enforce" or report["training_skipped"]


def neutral_probe(*args, **kwargs):
    raise NotImplementedError("reasoning neutral probes require separate trait-only integration; no compiler fallback")
