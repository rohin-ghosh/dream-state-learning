"""Bounded P-CHAIN-2 source preparation, not scientific material admission.

Caller IDs are rendered against Main's fixed tape and matched-skill construction.
No allocation, seed search,
tokenizer, model, filesystem export, or execution is provided. The CLI emits a
symbolic D1 plan. Trainer projections deliberately exclude evaluation material.
Structural checks do not certify native tokens, shortcut nulls, or custody.
"""

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import sys

from organism_v6.composition_birth_stage2a_primitives import canonical_json, low64, u32


STATUS = "PARTIAL_SOURCE_ONLY"
SUCCESSOR_FILE = "2026-09-13_parametric_two_hop_ceiling_binding_successor_v1.md"
ORIGINAL_FILE = "2026-09-13_smallest_parametric_two_hop_composition_ceiling.md"
SUCCESSOR_SHA256 = "be0778733d59f32d9d3810d2fc54b4f7c4f0ed8e8168b3471504600e312fb85c"
ORIGINAL_SHA256 = "93a6a2e75254c67503b26acda1659007dea6035b02d8f94ce55bb8ee0924fa01"
MATERIAL_MASTER = b"ASTRA-PCHAIN2-DEV-20260914-A1"
LEARNER_SEED = 0
SECOND_HOP_PERMUTATION = tuple(index ^ 1 for index in range(16))
NORMAL_GROUPS = (0, 1, 2, 3)
SWAPPED_GROUPS = (1, 0, 3, 2)
SYSTEM = "You work with opaque NEXT relations. Return only the requested canonical lines.\n"
STATES = ("BASE", "LR0", "ATOM-LOCAL", "ATOM-JUNCTION", "DERANGED-JUNCTION")
PANELS = ("one_hop", "eval_trace", "eval_direct", "prompt_trace", "prompt_empty", "canary")
PANEL_COUNTS = ((32, 16, 0, 16, 16, 0), (32, 16, 0, 16, 16, 0),
                (32, 16, 0, 16, 16, 16), (32, 16, 16, 16, 16, 16),
                (32, 16, 16, 0, 0, 16))
OPEN_BINDINGS = (
    "Main binds the 16 exact generic canary prompts/answers.",
    "Main binds the remaining native runtime/optimizer and runner inputs.",
)
RUNNER_OBLIGATIONS = (
    "Main supplies role-blind 16-lowercase-letter identifiers from the bound SHA "
    "stream, native L8 qualification with bounded per-ID salt, and independent "
    "role/domain permutations. This module never allocates identifiers.",
    "Dewey supplies the separate prelabel null registry/constraint solver; "
    "no null clearance is inferred here.",
    "Exact pinned base/tokenizer/template/runtime and numerical optimizer recipe.",
    "Response-only assistant-content plus terminal EOT masks, measured context "
    "fit, no truncation, matched target tokens per batch and coupled RNG tape.",
    "Independent substring/token/pair/rooted-signature/role-aware contamination "
    "and null/oracle checks over the prospectively fixed material.",
    "Four isolated immutable roots: training, evaluation, raw outputs, scores; "
    "trainer process mount/environment/open-file custody, including DERANGED.",
    "Complete the first three D1 fits before evaluation exposure; use the primary "
    "D1 gates to select dose before launching DERANGED from the coupled clean start.",
    "LR0 bitwise-zero effective deltas and 80 common BASE/LR0 raw-byte identities.",
    "Preserve D1 adapter/optimizer/cursor/RNG/raw outputs; any conditional D2 "
    "requires its presealed uninterrupted tape and a new isolated trainer.",
    "Fresh conversations/KV for every greedy call; retain malformed, truncated, "
    "nonterminal, and missing responses without retries or answer repair.",
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_protocol_bytes(successor, original):
    _require(type(successor) is bytes and type(original) is bytes, "protocol_bytes_required")
    _require(sha256(successor).hexdigest() == SUCCESSOR_SHA256
             and sha256(original).hexdigest() == ORIGINAL_SHA256, "protocol_hash_mismatch")
    return {SUCCESSOR_FILE: SUCCESSOR_SHA256, ORIGINAL_FILE: ORIGINAL_SHA256}


def _identifiers(values):
    _require(bool(values), "identifiers_required")
    for value in values:
        _require(type(value) is str and bool(value)
                 and all(33 <= ord(character) <= 126 and character not in "<>" for character in value),
                 "single_ascii_identifier_required")
    _require(len({len(value) for value in values}) == 1, "identifier_byte_lengths_differ")


@dataclass(frozen=True)
class Chain:
    source: str
    middle: str
    endpoint: str

    @property
    def identifiers(self):
        return (self.source, self.middle, self.endpoint)


@dataclass(frozen=True)
class LocalExample:
    first_source: str
    first_target: str
    query_source: str
    query_target: str

    @property
    def identifiers(self):
        return (self.first_source, self.first_target, self.query_source, self.query_target)


@dataclass(frozen=True)
class TrainingRow:
    row_id: int
    user: str
    assistant: str
    assistant_identifiers: tuple

    def messages(self):
        return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": self.user},
                {"role": "assistant", "content": self.assistant}]


@dataclass(frozen=True)
class TrainingState:
    name: str
    rows: tuple
    batches: tuple
    dropout_seeds: tuple

    def trainer_manifest(self):
        """Training-only projection; no coordinator or evaluation receipt is included."""
        return {"status": STATUS, "state": self.name, "dose": "D1", "recipe": fit_recipe(self.name),
                "rows": [{"row_id": row.row_id, "messages": row.messages()} for row in self.rows],
                "batches": [list(batch) for batch in self.batches], "learner_seed": LEARNER_SEED,
                "dropout_seeds": list(self.dropout_seeds), "native_ready": False}


@dataclass(frozen=True)
class PresentationBatch:
    update_number: int
    round_number: int
    row_ids: tuple
    dropout_seed: int

    @property
    def stage(self):
        return "D1" if self.update_number <= 384 else "D2"


@dataclass(frozen=True)
class TrainingPreparation:
    states: tuple
    fact_binding_sha256: str
    fact_identifiers: tuple
    skill_identifiers: tuple


@dataclass(frozen=True)
class ReadoutSlot:
    state: str
    panel: str
    index: int
    max_new_tokens: int


@dataclass(frozen=True)
class ReadoutCall:
    slot: ReadoutSlot
    user: str | None
    expected: bytes | None

    def actor_messages(self):
        _require(self.user is not None, "unbound_canary_bytes")
        return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": self.user}]


@dataclass(frozen=True)
class EvaluationPreparation:
    calls: tuple
    fact_binding_sha256: str
    fact_identifiers: tuple
    prompt_identifiers: tuple


def fit_recipe(state):
    _require(state in STATES[1:], "training_state_required")
    return {"base": "Qwen/Qwen2.5-7B-Instruct", "base_frozen": True, "lora_layers": "all",
            "rank": 8, "alpha": 16, "dropout": "0.05", "learning_rate": "0" if state == "LR0" else "0.00003",
            "batch_size": 4, "loss": "assistant_content_plus_terminal_eot",
            "optimizer": None, "runtime_binding": None}


def d1_readout_slots():
    """Canonical ledger enumeration, not a newly selected native dispatch order."""
    return tuple(ReadoutSlot(state, panel, index, 256 if panel in (
        "eval_trace", "prompt_trace", "prompt_empty") else 128)
        for state, counts in zip(STATES, PANEL_COUNTS)
        for panel, count in zip(PANELS, counts) for index in range(count))


def build_d1_plan():
    slots = d1_readout_slots()
    tape = build_presentation_tape()
    return {"status": STATUS, "protocol": {SUCCESSOR_FILE: SUCCESSOR_SHA256, ORIGINAL_FILE: ORIGINAL_SHA256},
            "prospective_bindings": {
                "material_master": MATERIAL_MASTER.decode("ascii"), "learner_seed": LEARNER_SEED,
                "second_hop_permutation": list(SECOND_HOP_PERMUTATION),
                "identifier_alphabet": "abcdefghijklmnopqrstuvwxyz", "identifier_width": 16,
                "native_identifier_tokens": 8, "identifier_allocation_implemented": False,
                "matched_local": "(E_i,E_(i^1),D_i,F_i)",
                "round_modes": ["normal/normal"] * 20 + ["normal/swap"] * 10 + ["swap/normal"] * 10,
                "skill_rounds_per_stage": list(range(5, 41, 5)),
                "per_chain_lags_per_stage": {"3": 10, "4": 20, "5": 10},
                "presealed_updates": len(tape), "tape_sha256": presentation_tape_sha256(tape),
                "dropout_seed_preimage": "master || NUL || dropout || NUL || u32be(global_update_1_based)",
                "dropout_seed_digest": "SHA256 low64, big-endian", "null_solver_owner": "Dewey"},
            "gates": {name: False for name in ("GO_MATERIALIZE", "GO_TOKENIZER_MODEL", "GO_GPU", "GO_CLAIM")},
            "fit_invocations": [{"state": state, "updates": 384, "atomic_presentations": 1280,
                                 "skill_presentations": 256, "recipe": fit_recipe(state),
                                 "release": "selected_D1_only" if state == "DERANGED-JUNCTION"
                                 else "before_D1_evaluation"} for state in STATES[1:]],
            "readout_slots": [asdict(slot) for slot in slots],
            "budget": {"fit_invocations": 4, "optimizer_updates": 1536, "presentations": 6144,
                       "model_calls": len(slots), "generated_tokens_max": sum(slot.max_new_tokens for slot in slots),
                       "external_reader_calls": 0},
            "executed": {"fits": 0, "updates": 0, "model_calls": 0, "tokenizer_calls": 0},
            "open_bindings": list(OPEN_BINDINGS), "runner_obligations": list(RUNNER_OBLIGATIONS)}


def _chains(chains, count):
    _require(type(chains) is tuple and len(chains) == count and all(type(chain) is Chain for chain in chains),
             "exact_chain_tuple_required")
    identifiers = tuple(identifier for chain in chains for identifier in chain.identifiers)
    _identifiers(identifiers)
    _require(all(len(set(chain.identifiers)) == 3 for chain in chains), "distinct_chain_identifiers_required")
    return identifiers


def _fact_chains(chains):
    identifiers = _chains(chains, 16)
    _require(len(set(identifiers)) == 48, "fact_domain_requires_48_distinct_identifiers")
    return identifiers


def _permutation(permutation):
    _require(type(permutation) is tuple and len(permutation) == 16
             and all(type(value) is int and 0 <= value < 16 for value in permutation),
             "exact_permutation_tuple_required")
    _require(all(value != index and value // 8 == index // 8 and permutation[value] == index
                 for index, value in enumerate(permutation)), "four_transpositions_per_block_required")
    _require(permutation == SECOND_HOP_PERMUTATION, "bound_xor_one_permutation_required")


def build_matched_skills(junction_examples):
    """Return (JUNCTION, LOCAL) over supplied D/E/F triples, without allocating IDs."""
    identifiers = _chains(junction_examples, 32)
    _require(len(set(identifiers)) == 96, "ninety_six_distinct_skill_identifiers_required")
    local = tuple(LocalExample(chain.middle, junction_examples[index ^ 1].middle,
                               chain.source, chain.endpoint)
                  for index, chain in enumerate(junction_examples))
    return junction_examples, local


def dropout_seed(update_number, *, master=MATERIAL_MASTER):
    """Same hash/u32 convention as Stage2A, extended to the bound 768 updates."""
    _require(type(master) is bytes and master == MATERIAL_MASTER, "bound_material_master_required")
    _require(type(update_number) is int and 1 <= update_number <= 768, "update_number_out_of_range")
    return low64(master + b"\0dropout\0" + u32(update_number))


def build_presentation_tape(*, master=MATERIAL_MASTER):
    """Preseal D1 and conditional D2; stages repeat row order, never dropout seeds.

    Rows 2*i/2*i+1 are the first/second fact for chain i; rows 32..63 are
    skill examples 0..31. Per stage, rounds 1..20 are normal/normal,
    21..30 normal/swap, and 31..40 swap/normal. Skills follow rounds 5,10,..40.
    """
    _require(type(master) is bytes and master == MATERIAL_MASTER, "bound_material_master_required")
    result = []
    for round_index in range(80):
        local_round = round_index % 40
        first = NORMAL_GROUPS if local_round < 30 else SWAPPED_GROUPS
        second = SWAPPED_GROUPS if 20 <= local_round < 30 else NORMAL_GROUPS
        rows = [tuple(2 * index + hop for index in range(4 * group, 4 * group + 4))
                for hop, groups in enumerate((first, second)) for group in groups]
        if (local_round + 1) % 5 == 0:
            rows.extend(tuple(range(start, start + 4)) for start in range(32, 64, 4))
        for row_ids in rows:
            update = len(result) + 1
            result.append(PresentationBatch(update, round_index + 1, row_ids,
                                            dropout_seed(update, master=master)))
    _require(len(result) == 768 and len({batch.dropout_seed for batch in result}) == 768,
             "invalid_bound_tape_or_dropout_collision")
    return tuple(result)


def presentation_tape_sha256(tape):
    _require(type(tape) is tuple and all(type(batch) is PresentationBatch for batch in tape),
             "presentation_batch_tuple_required")
    return sha256(canonical_json([{"update_number": batch.update_number,
                                  "round_number": batch.round_number, "row_ids": list(batch.row_ids),
                                  "dropout_seed": batch.dropout_seed} for batch in tape])).hexdigest()


def _binding(chains, permutation):
    return sha256(canonical_json({"facts": [list(chain.identifiers) for chain in chains],
                                  "second_hop_permutation": list(permutation)})).hexdigest()


def _memory(source, target):
    return f"MEMORY NEXT {source} => {target}\n"


def _trace(chain):
    return _memory(chain.source, chain.middle) + _memory(chain.middle, chain.endpoint) + f"ANSWER {chain.endpoint}\n"


def _atomic_row(row_id, source, target):
    return TrainingRow(row_id, f"OBSERVED RELATION\nNEXT {source} => {target}\nTASK\nStore exactly this one relation.\n",
                       _memory(source, target), (source, target))


def _junction_row(row_id, chain):
    user = (f"AVAILABLE RELATIONS\nNEXT {chain.source} => {chain.middle}\nNEXT {chain.middle} => {chain.endpoint}\n"
            f"QUERY\nStarting at {chain.source}, apply NEXT exactly twice.\nOUTPUT\n"
            "Return exactly two MEMORY lines followed by one ANSWER line.\n")
    return TrainingRow(row_id, user, _trace(chain),
                       (chain.source, chain.middle, chain.middle, chain.endpoint, chain.endpoint))


def _local_row(row_id, example):
    user = (f"AVAILABLE RELATIONS\nNEXT {example.first_source} => {example.first_target}\n"
            f"NEXT {example.query_source} => {example.query_target}\nQUERY\n"
            f"Starting at {example.query_source}, apply NEXT exactly once.\nOUTPUT\n"
            "Return exactly two MEMORY lines followed by one ANSWER line.\n")
    target = (_memory(example.first_source, example.first_target)
              + _memory(example.query_source, example.query_target) + f"ANSWER {example.query_target}\n")
    return TrainingRow(row_id, user, target, (*example.identifiers, example.query_target))


def _validate_tape(batches, permutation):
    _require(type(batches) is tuple and len(batches) == 384, "exact_384_update_tape_required")
    counts = Counter()
    previous = set()
    for batch in batches:
        _require(type(batch) is tuple and len(batch) == 4
                 and all(type(row) is int and 0 <= row < 64 for row in batch), "four_valid_row_ids_required")
        present = set(batch)
        for row in present:
            if row < 32:
                _require(row ^ 1 not in present and row ^ 1 not in previous, "paired_atoms_same_or_adjacent_update")
        batch_counts = Counter(batch)
        for index, partner in enumerate(permutation):
            _require(batch_counts[2 * index + 1] == batch_counts[2 * partner + 1],
                     "transposed_second_hops_must_share_batch_shard")
        counts.update(batch)
        previous = present
    _require(counts == Counter({row: 40 if row < 32 else 8 for row in range(64)}),
             "exact_per_row_D1_presentations_required")
    _require(batches == tuple(batch.row_ids for batch in build_presentation_tape()[:384]),
             "bound_D1_presentation_order_required")


def prepare_training(*, fact_chains, junction_examples, permutation=SECOND_HOP_PERMUTATION,
                     local_examples=None, batches=None):
    """Render caller IDs using the prospectively bound matched skills and D1 tape."""
    fact_ids = _fact_chains(fact_chains)
    _permutation(permutation)
    junction_examples, expected_local = build_matched_skills(junction_examples)
    junction_ids = tuple(identifier for chain in junction_examples for identifier in chain.identifiers)
    full_tape = build_presentation_tape()
    if local_examples is None:
        local_examples = expected_local
    if batches is None:
        batches = tuple(batch.row_ids for batch in full_tape[:384])
    _require(type(local_examples) is tuple and len(local_examples) == 32
             and all(type(example) is LocalExample for example in local_examples), "exact_local_tuple_required")
    local_ids = tuple(identifier for example in local_examples for identifier in example.identifiers)
    _identifiers(fact_ids + junction_ids + local_ids)
    _require(all(len(set(example.identifiers)) == 4 for example in local_examples), "local_relations_must_not_join")
    _require(not set(fact_ids) & set(junction_ids + local_ids), "fact_skill_identifier_overlap")
    _require(local_examples == expected_local, "bound_matched_local_examples_required")
    _validate_tape(batches, permutation)
    junction = tuple(_junction_row(32 + index, chain) for index, chain in enumerate(junction_examples))
    local = tuple(_local_row(32 + index, example) for index, example in enumerate(local_examples))
    _require(Counter(identifier for row in junction for identifier in row.assistant_identifiers)
             == Counter(identifier for row in local for identifier in row.assistant_identifiers),
             "skill_assistant_identifier_marginals_differ")
    authentic, deranged = [], []
    for index, chain in enumerate(fact_chains):
        first = _atomic_row(2 * index, chain.source, chain.middle)
        authentic.extend((first, _atomic_row(2 * index + 1, chain.middle, chain.endpoint)))
        deranged.extend((first, _atomic_row(2 * index + 1, chain.middle, fact_chains[permutation[index]].endpoint)))
    states = tuple(TrainingState(state, tuple(deranged if state == "DERANGED-JUNCTION" else authentic)
                                 + (local if state == "ATOM-LOCAL" else junction), batches,
                                 tuple(batch.dropout_seed for batch in full_tape[:384])) for state in STATES[1:])
    return TrainingPreparation(states, _binding(fact_chains, permutation), fact_ids,
                               tuple(sorted(set(junction_ids + local_ids))))


def _candidates(chains, orders, permutation=None):
    _require(type(orders) is tuple and len(orders) == 16, "sixteen_candidate_orders_required")
    positions, alternate_positions = Counter(), Counter()
    for index, (chain, order) in enumerate(zip(chains, orders)):
        _require(type(order) is tuple and len(order) == len(set(order)) == 8, "eight_distinct_candidates_required")
        endpoints = {item.endpoint for item in chains[index // 8 * 8:index // 8 * 8 + 8]}
        _require(set(order) == endpoints, "candidate_block_endpoints_required")
        positions[order.index(chain.endpoint)] += 1
        if permutation is not None:
            alternate_positions[order.index(chains[permutation[index]].endpoint)] += 1
    balanced = Counter({position: 2 for position in range(8)})
    _require(positions == balanced and (permutation is None or alternate_positions == balanced),
             "candidate_positions_not_exactly_balanced")


def _two_hop_user(chain, order, *, direct=False, supplied=None):
    prefix = ""
    if supplied is True:
        prefix = f"AVAILABLE RELATIONS\nNEXT {chain.source} => {chain.middle}\nNEXT {chain.middle} => {chain.endpoint}\n"
    elif supplied is False:
        prefix = "AVAILABLE RELATIONS\nNONE\n"
    output = "Return exactly one ANSWER line.\n" if direct else "Return exactly two MEMORY lines followed by one ANSWER line.\n"
    return (prefix + f"QUERY\nStarting at {chain.source}, apply NEXT exactly twice.\nENDPOINT CANDIDATES\n"
            + "\n".join(order) + "\nOUTPUT\n" + output)


def prepare_evaluation(*, fact_chains, permutation, prompt_chains, fact_candidates, prompt_candidates):
    """Build evaluator-only calls; all 48 canary slots deliberately remain unbound."""
    fact_ids, prompt_ids = _fact_chains(fact_chains), _fact_chains(prompt_chains)
    _identifiers(fact_ids + prompt_ids)
    _require(not set(fact_ids) & set(prompt_ids), "fact_prompt_identifier_overlap")
    _permutation(permutation)
    _candidates(fact_chains, fact_candidates, permutation)
    _candidates(prompt_chains, prompt_candidates)
    calls = []
    for slot in d1_readout_slots():
        if slot.panel == "canary":
            calls.append(ReadoutCall(slot, None, None))
            continue
        if slot.panel == "one_hop":
            index = slot.index % 16
            chain = fact_chains[index]
            endpoint = fact_chains[permutation[index]].endpoint if slot.state == "DERANGED-JUNCTION" else chain.endpoint
            source, target = (chain.source, chain.middle) if slot.index < 16 else (chain.middle, endpoint)
            user = f"QUERY\nRecall NEXT for {source}.\nOUTPUT\nReturn exactly one MEMORY line.\n"
            expected = _memory(source, target)
        else:
            prompt = slot.panel in ("prompt_trace", "prompt_empty")
            chain = (prompt_chains if prompt else fact_chains)[slot.index]
            order = (prompt_candidates if prompt else fact_candidates)[slot.index]
            endpoint = fact_chains[permutation[slot.index]].endpoint if slot.state == "DERANGED-JUNCTION" else chain.endpoint
            direct = slot.panel == "eval_direct"
            user = _two_hop_user(chain, order, direct=direct,
                                 supplied=(slot.panel == "prompt_trace") if prompt else None)
            expected = f"ANSWER {endpoint}\n" if direct else _trace(Chain(chain.source, chain.middle, endpoint))
        calls.append(ReadoutCall(slot, user, expected.encode("ascii")))
    return EvaluationPreparation(tuple(calls), _binding(fact_chains, permutation), fact_ids, prompt_ids)


def check_cross_corpus(training, evaluation):
    """Coordinator-only structural diagnostic; not a native contamination gate."""
    _require(type(training) is TrainingPreparation and type(evaluation) is EvaluationPreparation,
             "source_preparations_required")
    _require(training.fact_binding_sha256 == evaluation.fact_binding_sha256, "fact_bindings_differ")
    _require(not set(evaluation.prompt_identifiers) & set(training.fact_identifiers + training.skill_identifiers),
             "prompt_identifiers_in_training")
    held = tuple(call for call in evaluation.calls if call.slot.panel in ("eval_trace", "eval_direct"))
    for state in training.states:
        for row in state.rows:
            visible = (row.user + row.assistant).encode("ascii")
            _require(not any(identifier.encode("ascii") in visible for identifier in evaluation.prompt_identifiers),
                     "prompt_identifier_bytes_in_training")
            _require(not any(call.user.encode("ascii") in visible or call.expected in visible for call in held),
                     "scored_question_or_completion_in_training")
    return {"status": "STRUCTURAL_CHECKS_ONLY", "native_ready": False,
            "unbound_canary_calls": sum(call.expected is None for call in evaluation.calls),
            "open_bindings": list(OPEN_BINDINGS), "runner_obligations": list(RUNNER_OBLIGATIONS)}


def strict_match(call, raw, *, terminal, truncated):
    """No stripping, extraction, normalization, or repair; EOS is supplied separately."""
    _require(type(call) is ReadoutCall and call.expected is not None, "bound_readout_required")
    _require(type(terminal) is bool and type(truncated) is bool, "explicit_terminal_and_truncation_required")
    return type(raw) is bytes and terminal and not truncated and raw == call.expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", required=True, help="print symbolic D1 plan only")
    parser.parse_args(argv)
    notes = Path(__file__).resolve().parents[1] / "research_notes" / "analysis"
    verify_protocol_bytes((notes / SUCCESSOR_FILE).read_bytes(), (notes / ORIGINAL_FILE).read_bytes())
    sys.stdout.write(canonical_json(build_d1_plan()).decode("ascii") + "\n")


if __name__ == "__main__":
    main()
