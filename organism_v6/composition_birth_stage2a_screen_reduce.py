"""Non-material, pure BASE/D1 or BASE/D2 criteria; never native admission.

The post_seq195 critical-path efficiency note supplies the integer thresholds.
Caller-bound BASE and ATOM_LOCAL identities must be distinct and use the same
master. BASE always uses D1 slots; ATOM_LOCAL uses the selected D1 or D2 slots
and their own decode seeds without relabeling. Identity agreement does not authenticate model weights,
training, source eligibility, tokenizer, losses, nulls or persisted custody.
ReceiptVerification is deliberately not accepted: its encoded events are not
joined to these live objects or an authenticated checkpoint. Parent integration
must establish that authority separately, without caller-provided green flags.

Existing CPU drivers replay only supplied captures, never a model or external
callback. All original runs, UNUSED slots, native objects and exceptions remain
available by reference, including when a run is nonreportable. The caller must
exclude concurrent mutation while reducing and retaining this evidence.
"""

from collections import Counter
from dataclasses import dataclass, replace

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_canaries as canary_api
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime


STATUS = "PURE_REDUCED_CRITERIA_ONLY"
SCIENCE_GATES = screen.SCIENCE_GATES


@dataclass(frozen=True)
class Accounting:
    observed_reservations: int
    dispositions: tuple[tuple[str, int], ...]
    custody_records: int
    physical_calls: int
    native_records: int
    failures: int
    expected_reservations: int = 280


@dataclass(frozen=True)
class StateMetrics:
    skill_pairs: tuple[tuple[str, int], ...]
    typed_interventions: int
    whole_chains: int
    useful_reads: int
    typed_steps: int
    canaries: int
    intervention_scores: tuple
    chain_scores: tuple
    canary_matches: tuple[bool, ...]


@dataclass(frozen=True)
class StateReduction:
    run: runtime.ScreenRun
    accounting: Accounting
    metrics: StateMetrics | None
    issues: tuple[str, ...]

    @property
    def reportable(self):
        return self.metrics is not None and not self.issues


@dataclass(frozen=True)
class Criterion:
    name: str
    count: int
    denominator: int
    minimum: int

    @property
    def passed(self):
        return self.count >= self.minimum


@dataclass(frozen=True)
class ReducedResult:
    base: StateReduction
    atom_local: StateReduction
    criteria: tuple[Criterion, ...]
    status: str = STATUS

    @property
    def reportable(self):
        return self.base.reportable and self.atom_local.reportable

    @property
    def criteria_passed(self):
        return all(item.passed for item in self.criteria) if self.reportable else None

    @property
    def native_authorized(self):
        return False

    @property
    def persisted_custody_verified(self):
        return False


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _identity(value):
    return type(value) is str and bool(value.strip()) and value.isascii() and "\0" not in value


def _same_slot(actual, expected):
    return (type(actual) is primitives.LogicalSlot and type(actual.panel_label) is str
            and type(actual.global_ordinal) is int and actual == expected)


def _accounting(run):
    rows = tuple(row for row in run.reservations if type(row) is runtime.Reservation)
    captures = tuple(row.custody for row in rows if type(row.custody) is runtime.CallCustody)
    counts = Counter(row.disposition if type(row.disposition) is str else "INVALID" for row in rows)
    if len(rows) != len(run.reservations):
        counts["INVALID_RESERVATION"] = len(run.reservations) - len(rows)
    return Accounting(len(run.reservations), tuple(sorted(counts.items())), len(captures),
                      sum(item.physical_call is not None for item in captures),
                      sum(len(item.native_records) for item in captures
                          if type(item.native_records) is tuple), len(run.failures))


def _captures(run, expected_id, seeds, seen, *, stage="D1"):
    _require(stage in ("D1", "D2") and run.state_id == expected_id and run.stage == stage,
             "state_or_stage_identity_mismatch")
    _require(run.status == runtime.STATUS, "unexpected_runtime_status")
    _require(type(run.counter_provenance) is str and bool(run.counter_provenance.strip()),
             "counter_provenance_required_not_authenticated")
    _require(not run.failures and run.terminal_reason == "completed_unscored",
             "failed_or_incomplete_run")
    _require(len(run.reservations) == 280, "exact_280_reservations_required")
    captures = []
    first_actor_index = None
    for row, entry, seed in zip(run.reservations, screen.reduced_screen(stage), seeds):
        _require(type(row) is runtime.Reservation and type(row.entry) is screen.ScreenEntry
                 and row.entry == entry and type(row.entry.index) is int
                 and type(row.entry.member) is type(entry.member)
                 and _same_slot(row.entry.slot, entry.slot),
                 "ordered_slot_identity_mismatch")
        _require(type(row.seed) is int and row.seed == seed, "reservation_seed_mismatch")
        if row.disposition == "UNUSED":
            _require(entry.kind == "CHAIN" and row.custody is None, "unused_slot_has_capture")
            continue
        capture = row.custody
        _require(type(capture) is runtime.CallCustody, "missing_capture")
        _require(capture.state_id == expected_id and _same_slot(capture.slot, entry.slot),
                 "foreign_capture_identity")
        _require(all(error is None for error in (capture.actor_error, capture.capture_error,
                                                 capture.sink_error)), "capture_failure")
        _require(type(capture.physical_call) is int and capture.physical_call == len(captures),
                 "physical_calls_not_contiguous")
        _require(type(capture.actor_call_index) is int and capture.actor_call_index >= 0,
                 "invalid_actor_call_index")
        if first_actor_index is None:
            first_actor_index = capture.actor_call_index
        _require(capture.actor_call_index == first_actor_index + len(captures),
                 "actor_calls_not_contiguous")
        request, generation = capture.request, capture.generation
        _require(type(request) is rollout.DecodeRequest and type(request.seed) is int
                 and request.seed == seed, "request_seed_mismatch")
        _require(type(request.context_tokens) is int and 0 <= request.context_tokens < wire.CONTEXT_CAP
                 and type(request.max_new_tokens) is int and 0 < request.max_new_tokens <= 256,
                 "invalid_request_caps")
        _require(type(generation) is rollout.Generation, "invalid_generation_capture")
        _require(runtime._transport_fault(capture) is None, "generation_transport_fault")
        _require(type(capture.native_records) is tuple and len(capture.native_records) == 1,
                 "one_native_record_per_call_required")
        native = capture.native_records[0]
        _require(type(native) is dict and native.get("request") is request
                 and native.get("generation") is generation and native.get("error") is None,
                 "native_capture_join_mismatch")
        _require(("raw" not in native or native["raw"] == generation.raw)
                 and ("raw_bytes" not in native or native["raw_bytes"] == wire._raw_bytes(generation.raw)),
                 "native_raw_join_mismatch")
        for kind, value in (("custody", capture), ("request", request), ("native", native)):
            key = (kind, id(value))
            _require(key not in seen, "duplicate_capture_object:" + kind)
            seen.add(key)
        captures.append(capture)
    return tuple(captures)


def _replay(run, captures, *, master, chains, interventions, canaries, stage="D1"):
    position = 0
    records = []

    def count_context(prefix):
        _require(position < len(captures), "missing_replay_capture")
        request = captures[position].request
        _require(prefix == request.prefix, "captured_public_prefix_mismatch")
        return request.context_tokens

    def captured_actor(request):
        nonlocal position
        _require(position < len(captures), "extra_replay_call")
        capture = captures[position]
        _require(request == capture.request, "captured_request_mismatch")
        position += 1
        records.append(dict(request=request, generation=capture.generation, error=None))
        return capture.generation

    replayed = runtime.run_reduced_state(
        state_id=run.state_id, stage=stage, master=master, chains=chains,
        interventions=interventions, canaries=canaries, actor=captured_actor,
        actor_calls=records, count_context=count_context,
        counter_provenance=run.counter_provenance, custody_sink=lambda event, payload: None)
    _require(not replayed.failures and replayed.terminal_reason == run.terminal_reason
             and position == len(captures), "captured_replay_incomplete")
    _require(type(run.chain_runs) is tuple and type(run.probe_runs) is tuple
             and run.chain_runs == replayed.chain_runs and run.probe_runs == replayed.probe_runs,
             "driver_run_join_mismatch")
    for index, (original, expected) in enumerate(zip(run.reservations, replayed.reservations)):
        _require(original.disposition == expected.disposition
                 and original.driver_record == expected.driver_record, "driver_slot_join_mismatch")
        driver = (run.chain_runs[index // 29].calls[index % 29] if index < 232
                  else run.probe_runs[index - 232])
        _require(original.driver_record is driver and _same_slot(driver.slot, expected.entry.slot),
                 "driver_record_identity_mismatch")
        if index < 232:
            _require(type(driver.seed) is int, "invalid_driver_seed_type")
        if original.custody is not None:
            _require(original.driver_record.request is original.custody.request,
                     "driver_request_identity_mismatch")


def _metrics(run, *, chains, interventions, canaries):
    chain_scores = tuple(scoring.score_chain(chain.attempts, chains[task].members[task % 2])
                         for task, chain in zip(screen.CHAIN_TASKS, run.chain_runs))
    pair_scores = []
    for position, (transition, pair_index) in enumerate(
            (transition, index) for transition in primitives.TRANSITIONS for index in screen.INTERVENTION_PAIRS):
        probes = run.probe_runs[position * 2:position * 2 + 2]
        outputs = tuple(run.reservations[232 + position * 2 + member].custody.generation.raw
                        for member in range(2))
        score = scoring.score_intervention_pair(outputs, interventions[(transition, pair_index)])
        members = tuple(replace(member, typed_valid=member.typed_valid and probe.generation_valid,
                                exact_member_correct=member.exact_member_correct and probe.generation_valid)
                        for member, probe in zip(score.members, probes))
        pair_scores.append(replace(score, members=members,
                                   typed_both=all(member.typed_valid for member in members),
                                   pair_both_correct=all(member.exact_member_correct for member in members)))
    matches = tuple(probe.generation_valid and canary_api.exact_copy_match(canary, row.custody.generation.raw)
                    for canary, probe, row in zip(canaries, run.probe_runs[32:], run.reservations[264:]))
    return StateMetrics(
        tuple((transition, sum(score.pair_both_correct for score in pair_scores[index * 4:index * 4 + 4]))
              for index, transition in enumerate(primitives.TRANSITIONS)),
        sum(member.typed_valid for score in pair_scores for member in score.members),
        sum(score.whole_chain_success for score in chain_scores),
        sum(score.useful_pre_first_step_read for score in chain_scores),
        sum(score.strict_typing for score in chain_scores), sum(matches),
        tuple(pair_scores), chain_scores, matches)


def _reduce_state(run, expected_id, seeds, seen, *, master, chains, interventions, canaries, stage="D1"):
    accounting = _accounting(run)
    try:
        captures = _captures(run, expected_id, seeds, seen, stage=stage)
        _replay(run, captures, master=master, chains=chains, interventions=interventions,
                canaries=canaries, stage=stage)
        metrics = _metrics(run, chains=chains, interventions=interventions, canaries=canaries)
    except (ValueError, TypeError, AttributeError, IndexError, KeyError) as error:
        return StateReduction(run, accounting, None, (str(error),))
    return StateReduction(run, accounting, metrics, ())


def reduce_base_d1(*, base, atom_local, base_state_id, atom_local_state_id,
                   master, chains, interventions, canaries):
    """Return reportable numerical criteria or nonreportable retained evidence.

    Both inputs are exact in-memory ScreenRuns from run_reduced_state. Supply
    the parent's distinct expected state/attempt IDs and original reduced held
    bindings. No D2, fitted CLOSED, receipt flag or checkpoint is accepted.
    The typed_steps count reuses ChainScore.strict_typing: the upstream bound
    per-chain strict typed validity, not route correctness or STEP count.
    Complete malformed/length-limited generations remain scored misses, not
    dropped rows. External parser/loss/null/native gates are not asserted here.
    """
    return _reduce_base(base=base, atom_local=atom_local, base_state_id=base_state_id,
                        atom_local_state_id=atom_local_state_id, master=master,
                        chains=chains, interventions=interventions, canaries=canaries, atom_stage="D1")


def reduce_base_d2(*, base, atom_local, base_state_id, atom_local_state_id,
                   master, chains, interventions, canaries):
    """Apply unchanged reduced thresholds to retained BASE D1 versus ATOM D2.

    Both are exact ScreenRuns with distinct expected identities and the original
    master/held bindings. BASE is validated/replayed against D1 slots and seeds;
    ATOM_LOCAL against D2 slots and seeds. No stage or capture is relabeled.
    This is numerical reduction only, not conditional-continuation eligibility,
    checkpoint/training validation or native/scientific authorization.
    """
    return _reduce_base(base=base, atom_local=atom_local, base_state_id=base_state_id,
                        atom_local_state_id=atom_local_state_id, master=master,
                        chains=chains, interventions=interventions, canaries=canaries, atom_stage="D2")


def _reduce_base(*, base, atom_local, base_state_id, atom_local_state_id,
                 master, chains, interventions, canaries, atom_stage):
    _require(_identity(base_state_id) and _identity(atom_local_state_id)
             and base_state_id != atom_local_state_id, "distinct_explicit_state_identities_required")
    _require(type(base) is runtime.ScreenRun and type(atom_local) is runtime.ScreenRun,
             "live_screen_runs_required_not_receipt_verification")
    _require(all(type(run.reservations) is tuple and type(run.failures) is tuple
                 for run in (base, atom_local)), "immutable_run_collections_required")
    bindings = runtime._bindings(screen.reduced_screen("D1"), chains, interventions, canaries)
    for canary in bindings[2]:
        _require(canary.user_text == "CANARY\nCOPY EXACTLY\n" + canary.target,
                 "canary_target_public_prompt_mismatch")
        wire.parse_action(canary.target)
    options = dict(master=master, chains=bindings[0], interventions=bindings[1], canaries=bindings[2])
    base_seeds = screen.reduced_decode_seeds("D1", master=master)
    atom_seeds = screen.reduced_decode_seeds(atom_stage, master=master)
    seen = set()
    baseline = _reduce_state(base, base_state_id, base_seeds, seen, stage="D1", **options)
    fitted = _reduce_state(atom_local, atom_local_state_id, atom_seeds, seen, stage=atom_stage, **options)
    criteria = ()
    if baseline.reportable and fitted.reportable:
        metrics = fitted.metrics
        criteria = tuple(Criterion(name, count, 4, 3) for name, count in metrics.skill_pairs) + (
            Criterion("typed_interventions", metrics.typed_interventions, 32, 30),
            Criterion("whole_chains", metrics.whole_chains, 8, 6),
            Criterion("useful_reads", metrics.useful_reads, 8, 7),
            Criterion("typed_steps", metrics.typed_steps, 8, 7),
            Criterion("canaries", metrics.canaries, 16, 15),
            Criterion("chain_gain", metrics.whole_chains - baseline.metrics.whole_chains, 8, 2),
        )
    return ReducedResult(baseline, fitted, criteria)
