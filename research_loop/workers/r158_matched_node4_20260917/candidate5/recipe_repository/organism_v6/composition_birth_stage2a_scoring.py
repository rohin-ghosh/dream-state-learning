"""SOURCE-ONLY offline Stage2A intervention and chain diagnostics.

Authority: v2 sections 9--11, inherited by v4/v5 (pins below). V4 corrects
first-hop placement and v5 corrects intervention row ordering; scoring never
guesses display positions or changes their thresholds. No aggregate null gate,
scientific certification, model, runner, actor callback, file or GPU is invoked.

API:
  score_intervention_member(output, member): output is an exact raw str or a
    wire.Attempt; member is evaluator-only held.InterventionMember.
  score_intervention_pair(outputs, pair): exactly two outputs in m0,m1 order.
  score_chain(attempts, member): the exact tuple of wire.Attempt from
    wire.Session.attempts / rollout.ChainRun.attempts, plus held.ChainMember.
  score_chain_pair(runs, members): two attempt tuples and two ChainMembers.
All results are frozen source-only diagnostics; every science gate is false.
Wrong container/record types, inconsistent captures, or an incoherent witness
raise ScoreInputError. Captured malformed/length-limited actions instead return
unsuccessful metrics. Empty attempts are a failed/incomplete run, not success.
At most 30 attempts are admitted: the 29-call budget plus its first violation.

The witness is EVALUATOR-ONLY. Never pass it, these scores, sufficient READs, or
expected targets to an actor. Validate its public-row/outcome self-consistency,
then compare actual captures; do not replay the witness as a policy. It cannot
authenticate execution, the registry, provenance, tokenizer counts or custody.

READ classification is descriptive: SUFFICIENT / INITIAL_CANDIDATE_OTHER /
OTHER, with returned kind, relevant-row count, repeat and useful-read flags
reported separately. A useful read actually returned a unique GOAL+CURRENT
row. Completing a route additionally requires the witness's exact public READ
responses at the appropriate CURRENT before each corresponding STEP. Thus a
hidden-port guess cannot become whole-chain success merely by reaching GOAL.

CHECK command and operand are separate diagnostics, evaluated on the single
THINK strictly between first and second STEP (or the end of an incomplete run).
Whole success requires exactly that one intervening THINK, the two witness STEPs/outcomes, required READ
evidence, <=1 pre-first-STEP READ outside the sufficient set, strict typing,
accepted execution, valid generation metadata, existing wire budgets, and STOP
as the very next and final call after the second STEP at GOAL. Mechanical
goal_arrival_stop is retained separately and never substituted for this test.

Smallest unresolved ordering question: does a sufficient query guessed before
its directory, but subsequently backed by both public returns before STEP,
invalidate success? The bound text specifies a READ set, not that extra order
rule; this scorer does not invent it. Repeated in-set READs and READs between
first STEP and its CHECK are not separately prohibited within existing caps.
It reports repeats; extra STEPs, duplicate intervening CHECKs, or any delay after
the arrival STEP fail. Pre-first-STEP THINKs remain subject to the existing cap,
not a new prohibition; they are not first-outcome CHECKs.
"""

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held


STATUS = "PARTIAL_SOURCE_ONLY"
CONTRACT_HASHES = MappingProxyType({
    "v2": "dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74",
    "v4": "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1",
    "v5": "6ebefdba31de6f14416105c9509dbba06319f306bdd3472259a8d072ba9877e7",
})
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
SCIENCE_GATES = MappingProxyType(dict.fromkeys((*wire.SCIENCE_GATES,
    "GO_WRITE_ROOT", "GO_MATERIALIZE", "GO_MODEL_TOKENIZER", "GO_FIT_OR_GPU", "GO_CLAIM"), False))


class ScoreInputError(ValueError):
    """Wrong input shape/capture integrity or inconsistent evaluator witness."""


def _require(condition, message):
    if not condition:
        raise ScoreInputError(message)


class _SourceOnly:
    status = STATUS
    science_gates = SCIENCE_GATES
    contract_hashes = CONTRACT_HASHES


@dataclass(frozen=True)
class InterventionScore(_SourceOnly):
    typed_valid: bool
    command_correct: bool
    operand_correct: bool
    exact_member_correct: bool
    execution_valid: bool | None


@dataclass(frozen=True)
class InterventionPairScore(_SourceOnly):
    members: tuple[InterventionScore, InterventionScore]
    typed_both: bool
    command_both: bool
    operand_both: bool
    pair_both_correct: bool


@dataclass(frozen=True)
class ReadScore(_SourceOnly):
    call_index: int
    read_class: str
    returned_kind: str
    pre_first_step: bool
    in_sufficient_set: bool
    initial_candidate: bool
    repeated: bool
    relevant_rows: int
    useful: bool


@dataclass(frozen=True)
class ChainScore(_SourceOnly):
    attempt_count: int
    reads: tuple[ReadScore, ...]
    pre_first_step_outside_sufficient_reads: int
    pre_first_step_read_limit: bool
    useful_pre_first_step_read: bool
    sufficient_reads_complete: bool
    public_read_evidence_before_steps: bool
    first_step_correct: bool
    full_route_correct: bool
    first_outcome_check_count: int
    first_outcome_check_command_correct: bool
    first_outcome_check_operand_correct: bool
    first_outcome_check_correct: bool
    strict_typing: bool
    execution_valid: bool
    generation_valid: bool
    within_budgets: bool
    goal_arrival: bool
    exact_stop: bool
    stop_immediately_after_second_step: bool
    mechanical_goal_arrival_stop: bool
    whole_chain_success: bool


@dataclass(frozen=True)
class ChainPairScore(_SourceOnly):
    members: tuple[ChainScore, ChainScore]
    pair_both_correct: bool


def _command(action):
    return action.operation + (" " + action.verb if action.verb is not None else "")


def _parse(raw):
    try:
        return wire.parse_action(raw)
    except ValueError:
        return None


def _immutable(value, depth=0):
    _require(depth <= 32, "capture nesting limit")
    if type(value) is tuple:
        for item in value:
            _immutable(item, depth + 1)
    else:
        _require(type(value) in (str, bytes, int, bool, type(None)), "mutable or unsupported capture")


def _scalar(value, kind):
    if type(value) is tuple and len(value) == 2 and value[0] == kind.__name__ and type(value[1]) is kind:
        return value[1]
    return None


def _snapshot(value):
    _require(type(value) is wire.Snapshot, "wire.Snapshot required")
    try:
        wire.parse_world("WORLD\nCURRENT " + value.current)
    except (TypeError, ValueError) as error:
        raise ScoreInputError("invalid snapshot CURRENT") from error
    _require(type(value.counts) is tuple, "immutable snapshot counts required")
    _require(all(type(item) is tuple and len(item) == 2 and type(item[0]) is str
                 and type(item[1]) is int and item[1] >= 0 for item in value.counts), "invalid counts")
    _require(len(value.counts) == len(wire.LIMITS) and set(dict(value.counts)) == set(wire.LIMITS),
             "incorrect count keys")
    _require(type(value.actual_tokens) is int and value.actual_tokens >= 0, "invalid token count")
    _require(type(value.terminated) is bool and type(value.goal_arrival_stop) is bool,
             "invalid snapshot flags")
    _require(value.terminal_reason is None or type(value.terminal_reason) is str, "invalid terminal reason")
    _require(value.terminated == (value.terminal_reason is not None), "inconsistent termination")


def _attempt(attempt):
    _require(type(attempt) is wire.Attempt and type(attempt.capture) is wire.RawAttempt,
             "immutable wire.Attempt/RawAttempt required")
    capture = attempt.capture
    _require(type(capture.call_index) is int and capture.call_index >= 0, "invalid call index")
    for value in (capture.raw, capture.generation_request, capture.declared_tokens,
                  capture.actual_tokens, capture.context_tokens, capture.truncated, capture.finish_reason):
        _immutable(value)
    _snapshot(capture.pre_state)
    _snapshot(attempt.post_state)
    _require(type(attempt.response_bytes) is bytes and type(attempt.accepted) is bool, "invalid outcome types")
    _require(attempt.terminal_reason is None or type(attempt.terminal_reason) is str, "invalid attempt reason")
    raw = _scalar(capture.raw, str)
    if raw is not None:
        try:
            expected_bytes = raw.encode("utf-8")
        except UnicodeEncodeError:
            expected_bytes = None
        _require(capture.raw_bytes == expected_bytes, "raw capture bytes mismatch")
    else:
        _require(capture.raw_bytes is None or type(capture.raw_bytes) is bytes, "invalid raw bytes")
    parsed = _parse(raw)
    _require(attempt.parser_disposition in ("valid", "invalid", "not_parsed"), "unknown parser disposition")
    if attempt.parser_disposition == "valid":
        _require(parsed is not None and type(attempt.action) is wire.Action and attempt.action == parsed,
                 "parsed action disagrees with raw capture")
    else:
        _require(attempt.action is None and not attempt.accepted, "invalid action accepted")
        _require(attempt.parser_disposition != "invalid" or parsed is None, "parser disposition mismatch")
    before, after = capture.pre_state, attempt.post_state
    if before.terminated:
        _require(not attempt.accepted and after == before and attempt.terminal_reason == "session_terminated",
                 "post-terminal attempt changed state")
    elif attempt.accepted:
        _require(attempt.parser_disposition == "valid", "accepted unparsed action")
        counts = dict(before.counts)
        counts[parsed.operation] += 1
        _require(dict(after.counts) == counts, "accepted action count mismatch")
        actual = _scalar(capture.actual_tokens, int)
        _require(actual is not None and after.actual_tokens == before.actual_tokens + actual,
                 "accepted token count mismatch")
        if parsed.operation == "STEP":
            try:
                destination = wire.parse_world(attempt.response_bytes.decode("ascii"))
            except (UnicodeError, ValueError) as error:
                raise ScoreInputError("invalid STEP outcome") from error
            _require(destination == after.current, "STEP response/state mismatch")
        else:
            _require(after.current == before.current, "non-STEP changed CURRENT")
        if parsed.operation == "THINK":
            _require(attempt.response_bytes == b"ACK", "THINK response must be ACK")
        if parsed.operation == "STOP":
            _require(attempt.response_bytes == b"" and after.terminated
                     and attempt.terminal_reason == after.terminal_reason
                     and after.terminal_reason in ("goal_arrival_stop", "premature_stop"), "invalid STOP receipt")
        else:
            _require(attempt.terminal_reason is None and not after.terminated, "nonterminal action terminated")
    else:
        _require(after.terminated and attempt.terminal_reason is not None and after.current == before.current,
                 "rejected attempt must terminate without transition")
    return raw, parsed


def _generation_valid(attempt):
    capture = attempt.capture
    actual = _scalar(capture.actual_tokens, int)
    declared = _scalar(capture.declared_tokens, int)
    context = _scalar(capture.context_tokens, int)
    if (actual is None or declared != actual or context is None or not 0 <= context <= wire.CONTEXT_CAP
            or _scalar(capture.truncated, bool) is not False or _scalar(capture.finish_reason, str) != "stop"):
        return False
    allowance = min(256, wire.TOKEN_CAP - capture.pre_state.actual_tokens, wire.CONTEXT_CAP - context)
    request = capture.generation_request
    if type(request) is not tuple or len(request) != 2 or request[0] != "dict" or type(request[1]) is not tuple:
        return False
    maxima = [item[1] for item in request[1] if type(item) is tuple and len(item) == 2
              and item[0] == ("str", "max_new_tokens")]
    return (len(maxima) == 1 and _scalar(maxima[0], int) == allowance and 0 < actual <= allowance)


def score_intervention_member(output, member):
    """Separate syntax, command, operand and exact outcome; no actor is called."""
    _require(type(member) is held.InterventionMember, "held.InterventionMember required")
    target = member.expected_target
    _require(type(target) is held.ExpectedTarget, "typed expected target required")
    expected = _parse(target.bytes)
    _require(expected is not None and target.command == _command(expected) and target.operand == expected.operand,
             "inconsistent expected target")
    _require(target.sha256 == sha256(target.bytes.encode("ascii")).hexdigest(), "target hash mismatch")
    if type(output) is wire.Attempt:
        raw, action = _attempt(output)
        execution = output.accepted and _generation_valid(output)
        typed = action is not None and output.parser_disposition == "valid"
    else:
        raw, action = output, _parse(output)
        execution = None
        typed = action is not None
    command = typed and _command(action) == target.command
    operand = typed and action.operand == target.operand
    exact = typed and command and operand and raw == target.bytes and execution is not False
    return InterventionScore(typed, command, operand, exact, execution)


def score_intervention_pair(outputs, pair):
    """Score m0/m1 separately, then conjunctions; never apply a panel threshold."""
    _require(type(outputs) is tuple and len(outputs) == 2, "two ordered outputs required")
    _require(type(pair) is held.InterventionPair and type(pair.members) is tuple and len(pair.members) == 2,
             "held.InterventionPair required")
    _require(all(type(member) is held.InterventionMember for member in pair.members), "typed intervention members required")
    _require(tuple(member.member for member in pair.members) == ("m0", "m1"), "pair member order")
    _require(pair.members[0].transition_name == pair.members[1].transition_name
             and pair.members[0].pair_index == pair.members[1].pair_index, "mixed intervention pair")
    scores = tuple(score_intervention_member(output, member) for output, member in zip(outputs, pair.members))
    return InterventionPairScore(scores, all(score.typed_valid for score in scores),
                                 all(score.command_correct for score in scores),
                                 all(score.operand_correct for score in scores),
                                 all(score.exact_member_correct for score in scores))


def _service(response):
    _require(type(response) is str and response.startswith("SERVICE\n"), "public SERVICE response required")
    for skin in (0, 1):
        try:
            return wire.parse_service(response[len("SERVICE\n"):], skin=skin)
        except ValueError:
            pass
    raise ScoreInputError("invalid public service rows")


def _matching(block, current, goal):
    rows = [row for row in block.rows if row.node == current and row.goal == goal]
    _require(len(rows) == 1, "witness must have one relevant public row")
    return rows[0]


def _witness(member):
    _require(type(member) is held.ChainMember and type(member.task) is wire.TaskState, "held.ChainMember required")
    _require(member.member in ("m0", "m1"), "invalid chain member")
    task = member.task
    try:
        wire.parse_task(f"TASK\nSTART {task.start}\nGOAL {task.goal}\nCURRENT {task.current}")
    except ValueError as error:
        raise ScoreInputError("invalid witness task") from error
    _require(task.start == task.current and task.goal != task.current, "chain must start unresolved")
    trace = member.expected_trace
    _require(type(trace) is tuple and len(trace) in (7, 8), "bounded two-step witness required")
    _require(all(type(turn) is held.WitnessTurn for turn in trace), "immutable WitnessTurn required")
    _require(all(type(turn.action) is str and type(turn.current_before) is str
                 and type(turn.current_after) is str and (turn.response is None or type(turn.response) is str)
                 for turn in trace), "invalid witness field types")
    _require(type(member.sufficient_reads) is frozenset, "immutable sufficient READ set required")
    actions = tuple(_parse(turn.action) for turn in trace)
    _require(all(action is not None for action in actions), "invalid witness action")
    expected_ops = (("READ", "READ", "STEP", "THINK", "READ", "READ", "STEP", "STOP")
                    if len(trace) == 8 else ("READ", "READ", "STEP", "THINK", "READ", "STEP", "STOP"))
    _require(tuple(action.operation for action in actions) == expected_ops, "wrong witness operation sequence")
    current = task.current
    blocks = {}
    for index, (turn, action) in enumerate(zip(trace, actions)):
        _require(turn.current_before == current, "discontinuous witness CURRENT")
        if action.operation == "READ":
            _require(turn.current_after == current, "witness READ changed CURRENT")
            blocks[index] = _service(turn.response)
            _require(blocks[index].kind == ("ROUTES" if action.verb == "INDEX" else "EVENTS"),
                     "witness READ response kind mismatch")
        elif action.operation == "STEP":
            _require(turn.response == "WORLD\nCURRENT " + turn.current_after, "witness WORLD mismatch")
            current = turn.current_after
        elif action.operation == "THINK":
            _require(turn.response == "ACK" and turn.current_after == current, "witness CHECK response mismatch")
        else:
            _require(turn.action == "STOP" and turn.response is None and turn.current_after == current,
                     "witness STOP mismatch")
    first, second = trace[2], trace[-2]
    _require(first.current_after not in (task.current, task.goal) and second.current_after == task.goal,
             "witness must have unresolved first and reached second STEP")
    _require(trace[0].action == "READ INDEX " + task.current, "witness initial INDEX mismatch")
    first_route = _matching(blocks[0], task.current, task.goal)
    _require(trace[1].action == "READ RELATION " + first_route.query, "witness first relation mismatch")
    first_event = _matching(blocks[1], task.current, task.goal)
    _require(first.action == "STEP " + first_event.port, "witness first port mismatch")
    match = first.current_after == first_event.got
    check = "THINK " + ("KEEP " if match else "REVISE ") + first_event.event
    _require(trace[3].action == check and len(trace) == (8 if match else 7), "witness first-outcome CHECK mismatch")
    if match:
        _require(trace[4].action == "READ INDEX " + first.current_after, "witness second INDEX mismatch")
        second_route = _matching(blocks[4], first.current_after, task.goal)
        _require(trace[5].action == "READ RELATION " + second_route.query, "witness second relation mismatch")
    else:
        _require(trace[4].action == "READ RELATION " + first_event.recover, "witness RECOVER mismatch")
    second_event = _matching(blocks[len(trace) - 3], first.current_after, task.goal)
    _require(second.action == "STEP " + second_event.port and second_event.got == task.goal,
             "witness second port/goal mismatch")
    reads = frozenset(turn.action for turn, action in zip(trace, actions) if action.operation == "READ")
    _require(member.sufficient_reads == reads and len(reads) == (4 if match else 3), "witness sufficient READ mismatch")
    candidates = frozenset("READ RELATION " + row.query for row in blocks[0].rows)
    _require(len(candidates) == 24, "witness needs 24 distinct initial candidate queries")
    return trace, candidates


def _trace(attempts, member):
    _require(type(attempts) is tuple and len(attempts) <= wire.CALL_CAP + 1, "bounded attempts tuple required")
    parsed = []
    previous = None
    for index, attempt in enumerate(attempts):
        raw, action = _attempt(attempt)
        before = attempt.capture.pre_state
        _require(attempt.capture.call_index == index, "attempt call indices must start at zero without gaps")
        if previous is None:
            _require(before.current == member.task.current and not before.terminated
                     and before.actual_tokens == 0 and not any(dict(before.counts).values())
                     and not before.goal_arrival_stop, "attempts must start at task boundary")
        else:
            _require(before == previous, "attempt state discontinuity")
        if attempt.accepted and action.operation == "STOP":
            reached = before.current == member.task.goal
            _require(attempt.post_state.goal_arrival_stop == reached
                     and attempt.terminal_reason == ("goal_arrival_stop" if reached else "premature_stop"),
                     "mechanical STOP flag inconsistent with goal")
        parsed.append((raw, action))
        previous = attempt.post_state
    return tuple(parsed)


def _agrees(attempt, raw, turn):
    return (attempt.accepted and raw == turn.action and attempt.capture.pre_state.current == turn.current_before
            and attempt.post_state.current == turn.current_after
            and attempt.response_bytes == (turn.response or "").encode("ascii"))


def score_chain(attempts, member):
    """Score captured calls after execution; the witness never reaches an actor."""
    witness, candidates = _witness(member)
    parsed = _trace(attempts, member)
    steps = [index for index, (_, action) in enumerate(parsed) if action is not None and action.operation == "STEP"]
    first_index = steps[0] if steps else len(attempts)
    second_index = steps[1] if len(steps) >= 2 else len(attempts)
    reads = []
    seen = set()
    sufficient_executed = set()
    for index, (attempt, (raw, action)) in enumerate(zip(attempts, parsed)):
        if action is None or action.operation != "READ":
            continue
        kind, relevant = "NOT_ACCEPTED", 0
        if attempt.accepted:
            try:
                block = _service(attempt.response_bytes.decode("ascii"))
            except UnicodeError as error:
                raise ScoreInputError("non-ASCII READ response") from error
            _require(block.kind in ("MISS", "ROUTES" if action.verb == "INDEX" else "EVENTS"),
                     "captured READ kind mismatch")
            kind = block.kind
            relevant = sum(row.node == attempt.capture.pre_state.current and row.goal == member.task.goal
                           for row in block.rows)
            if raw in member.sufficient_reads:
                sufficient_executed.add(raw)
        sufficient = raw in member.sufficient_reads
        initial = raw in candidates
        read_class = "SUFFICIENT" if sufficient else "INITIAL_CANDIDATE_OTHER" if initial else "OTHER"
        reads.append(ReadScore(index, read_class, kind, index < first_index, sufficient, initial,
                               raw in seen, relevant, attempt.accepted and relevant == 1))
        seen.add(raw)
    outside = sum(read.pre_first_step and not read.in_sufficient_set for read in reads)
    useful = any(read.pre_first_step and read.useful and read.returned_kind == "EVENTS" for read in reads)
    first_correct = bool(steps) and _agrees(attempts[first_index], parsed[first_index][0], witness[2])
    route = (len(steps) == 2 and first_correct
             and _agrees(attempts[second_index], parsed[second_index][0], witness[-2]))
    required_first = witness[:2]
    required_second = witness[4:-2]
    evidence = bool(steps) and len(steps) >= 2 and all(
        any(_agrees(attempts[index], parsed[index][0], turn) for index in indices)
        for turns, indices in ((required_first, range(first_index)),
                               (required_second, range(first_index + 1, second_index))) for turn in turns
    )
    thinks = [index for index, (_, action) in enumerate(parsed) if action is not None and action.operation == "THINK"]
    between = [index for index in thinks if first_index < index < second_index]
    command = operand = False
    if steps and len(between) == 1:
        check_index = between[0]
        expected_check = wire.parse_action(witness[3].action)
        command = attempts[check_index].accepted and _command(parsed[check_index][1]) == _command(expected_check)
        operand = attempts[check_index].accepted and parsed[check_index][1].operand == expected_check.operand
    check_correct = (command and operand
                     and _agrees(attempts[between[0]], parsed[between[0]][0], witness[3]))
    typing = bool(attempts) and all(action is not None and attempt.parser_disposition == "valid"
                                   for attempt, (_, action) in zip(attempts, parsed))
    execution = bool(attempts) and all(attempt.accepted for attempt in attempts)
    generation = bool(attempts) and all(_generation_valid(attempt) for attempt in attempts)
    budgets = (len(attempts) <= wire.CALL_CAP
               and all(attempt.post_state.actual_tokens <= wire.TOKEN_CAP
                       and all(count <= wire.LIMITS[name] for name, count in attempt.post_state.counts)
                       for attempt in attempts))
    arrival = any(attempts[index].accepted and attempts[index].post_state.current == member.task.goal for index in steps)
    stops = [index for index, (_, action) in enumerate(parsed) if action is not None and action.operation == "STOP"]
    exact_stop = (len(stops) == 1 and stops[0] == len(attempts) - 1
                  and attempts[stops[0]].accepted and parsed[stops[0]][0] == "STOP")
    immediate = (len(steps) == 2 and exact_stop and stops[0] == second_index + 1
                 and attempts[second_index].accepted and attempts[second_index].post_state.current == member.task.goal)
    mechanical = bool(attempts) and attempts[-1].post_state.goal_arrival_stop
    complete_reads = sufficient_executed == member.sufficient_reads
    whole = all((outside <= 1, useful, complete_reads, evidence, route, check_correct,
                 typing, execution, generation, budgets, arrival, exact_stop, immediate, mechanical))
    return ChainScore(len(attempts), tuple(reads), outside, outside <= 1, useful, complete_reads, evidence,
                      first_correct, route, len(between), command, operand, check_correct, typing, execution, generation,
                      budgets, arrival, exact_stop, immediate, mechanical, whole)


def score_chain_pair(runs, members):
    """Causal-twin conjunction only, with no aggregate scientific gate."""
    _require(type(runs) is tuple and len(runs) == 2 and type(members) is tuple and len(members) == 2,
             "two ordered runs and members required")
    _require(all(type(member) is held.ChainMember for member in members)
             and tuple(member.member for member in members) == ("m0", "m1"), "chain pair member order")
    _require(members[0].task.start == members[1].task.start and members[0].task.goal != members[1].task.goal,
             "chain twins must share start and differ in goal")
    scores = tuple(score_chain(attempts, member) for attempts, member in zip(runs, members))
    return ChainPairScore(scores, all(score.whole_chain_success for score in scores))
