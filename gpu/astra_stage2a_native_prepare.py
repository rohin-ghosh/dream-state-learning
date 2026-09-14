"""Source-only conductor adapters; importing this file never prepares a corpus.

No CLI, loading, writing, allocation retry, training, scoring, or native entry
point is provided. Callers supply an already validated curriculum and tokenizer.
Representation checks and receipts do not authenticate either. Source custody,
native token pins, actual preparation and initial-adapter provenance remain the
calling main's obligations. Upstream qualification is not inferred here.

Padding policy must be chosen explicitly: PER_ARM_MAX or SHARED_MAX measures
the four complete sequences in each batch, never a guessed context budget.
Both arms and all 512 conditional tape entries are retained; the convenience
slice describes only the later D1 ATOM_LOCAL 256 updates and executes nothing.
Receipts are evaluator-only, not actor/parent projections or admission evidence.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_allocation as allocation
from organism_v6 import composition_birth_stage2a_canaries as canary_api
from organism_v6 import composition_birth_stage2a_curriculum as curriculum_api
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_tape as tape
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_tokenization as tokenization
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "SOURCE_ONLY_PREPARATION_GLUE"
COUNT_BASIS = "UNAUTHENTICATED_CALLER_TOKENIZER"
PADDING_POLICIES = ("PER_ARM_MAX", "SHARED_MAX")
CALLER_OBLIGATIONS = (
    "validated source custody and curriculum",
    "native tokenizer files, template and token pins",
    "actual native preparation and execution authorization",
    "initial-adapter provenance",
    "upstream full qualification, including harness defects",
)


@dataclass(frozen=True, repr=False)
class PreparedBirth:
    """Exact bytes/IDs live in rows and batches; receipt hashes bind those bytes."""

    paired_targets: tuple
    tokenized_pairs: tuple
    batches: tuple
    tape_fingerprint: str
    receipt_bytes: bytes
    receipt_sha256: str

    @property
    def d1_atom_local_batches(self):
        """Descriptive 256-update slice, not permission or a training entry point."""
        return tuple(batch.atom_local for batch in self.batches[:256])


@dataclass(frozen=True, repr=False)
class ReducedHeld:
    chains: Mapping
    interventions: Mapping
    canaries: tuple
    receipt_bytes: bytes
    receipt_sha256: str


def allocate_source(*, master):
    """Explicit future call only: delegate once, with no root or extra roles."""
    return allocation.allocate_stage2a(master=master)


def compile_source_curriculum(*, bound_allocation, master):
    """Consume existing birth bindings; never allocate or select a new master."""
    return curriculum_api.compile_birth_curriculum(
        role_tokens_by_world=bound_allocation.role_tokens_by_world("birth_train"),
        master=master,
    )


def _byte_receipt(raw):
    return {"byte_count": len(raw), "sha256": sha256(raw).hexdigest()}


def _token_receipt(ids):
    return {"token_count": len(ids), "ids_sha256": sha256(canonical_json(list(ids))).hexdigest()}


def _row_receipt(row):
    components = {}
    for name, raw, ids in (
        ("context", row.context_roundtrip_bytes, row.context_ids),
        ("target_with_eos", row.target_roundtrip_bytes, row.target_ids),
        ("suffix", row.suffix_roundtrip_bytes, row.suffix_ids),
        ("sequence", row.sequence_roundtrip_bytes, row.input_ids),
    ):
        components[name] = {**_byte_receipt(raw), **_token_receipt(ids)}
    return {
        "arm": row.record.arm,
        "prefix": _byte_receipt(targets.messages_bytes(row.record.prefix)),
        "prefix_content_bytes": row.record.content_bytes,
        "target_start": row.target_start,
        "target_end": row.target_end,
        "eos_token_id": row.eos_token_id,
        "pad_token_id": row.pad_token_id,
        "labels_sha256": sha256(canonical_json(list(row.labels))).hexdigest(),
        "attention_mask_sha256": sha256(canonical_json(list(row.attention_mask))).hexdigest(),
        "components": components,
    }


def _curriculum_pairs(compiled, master):
    if type(compiled) is not curriculum_api.BirthCurriculum:
        raise ValueError("caller_validated_birth_curriculum_required")
    expected = tape.build_presentation_tape(master=master, unit_ids=tape.unit_identifiers())
    if compiled.master_sha256 != sha256(master).hexdigest() or compiled.batches != expected:
        raise ValueError("curriculum_master_or_tape_mismatch")
    pairs = compiled.paired_targets
    if (type(pairs) is not tuple or len(pairs) != 256
            or any(type(pair) is not targets.PairedTarget for pair in pairs)
            or tuple(pair.closed.unit.unit_id for pair in pairs) != tape.unit_identifiers()):
        raise ValueError("exact_256_paired_target_roster_required")
    if (dict(compiled.target_hashes) != {
            pair.closed.unit.unit_id: pair.closed.unit.target_sha256 for pair in pairs}
            or dict(compiled.command_counts) != dict(Counter(
                pair.closed.unit.command for pair in pairs))):
        raise ValueError("curriculum_target_receipt_mismatch")
    return pairs


def prepare_birth(*, validated_curriculum, tokenizer, master, padding_policy):
    """Plan exact paired batches using existing mechanics and an injected interface.

    Does not load or authenticate a tokenizer, validate scientific source
    qualification, allocate bindings, create an adapter, or run any updates.
    Token IDs are hashed as canonical JSON integer arrays; byte hashes are over
    unmodified bytes. Repeated presentations count repeatedly in accounting.
    """
    if type(padding_policy) is not str or padding_policy not in PADDING_POLICIES:
        raise ValueError("explicit_measured_padding_policy_required")
    pairs = _curriculum_pairs(validated_curriculum, master)
    measured = tuple(tokenization.TokenizedPair(
        tokenization.tokenize_arm_record(pair.closed, tokenizer=tokenizer, count_basis=COUNT_BASIS),
        tokenization.tokenize_arm_record(pair.atom_local, tokenizer=tokenizer, count_basis=COUNT_BASIS),
    ) for pair in pairs)
    by_id = {pair.closed.unit.unit_id: (pair, rows) for pair, rows in zip(pairs, measured)}
    batches = []
    batch_receipts = []
    totals = {stage: {arm: Counter() for arm in ("CLOSED", "ATOM_LOCAL")}
              for stage in ("D1", "D2")}
    for presentation in validated_curriculum.batches:
        selected = tuple(by_id[unit] for unit in presentation.unit_ids)
        closed_width = max(len(rows.closed.input_ids) for _, rows in selected)
        atom_width = max(len(rows.atom_local.input_ids) for _, rows in selected)
        if padding_policy == "SHARED_MAX":
            closed_width = atom_width = max(closed_width, atom_width)
        batch = tokenization.prepare_paired_batch(
            presentation, tuple(pair for pair, _ in selected), tokenizer=tokenizer,
            count_basis=COUNT_BASIS, closed_padding_length=closed_width,
            atom_local_padding_length=atom_width,
        )
        for arm, prepared in (("CLOSED", batch.closed), ("ATOM_LOCAL", batch.atom_local)):
            for row, (_, measured_pair) in zip(prepared.records, selected):
                expected_row = measured_pair.closed if arm == "CLOSED" else measured_pair.atom_local
                if row != expected_row:
                    raise ValueError("tokenizer_changed_after_measurement")
            totals[presentation.stage][arm].update(prepared.accounting)
        batches.append(batch)
        batch_receipts.append({
            "update_number": presentation.update_number, "stage": presentation.stage,
            "presentation_index": presentation.presentation_index,
            "unit_ids": list(presentation.unit_ids), "rng_start_seed": presentation.rng_start_seed,
            "padding_lengths": {"CLOSED": closed_width, "ATOM_LOCAL": atom_width},
            "accounting": {"CLOSED": dict(batch.closed.accounting),
                           "ATOM_LOCAL": dict(batch.atom_local.accounting)},
        })
    batches = tuple(batches)
    fingerprint = training.validate_batches(batches, master=master)
    units = [{
        "unit_id": pair.closed.unit.unit_id,
        "command": pair.closed.unit.command,
        "target_bytes_hex": pair.closed.unit.target_bytes.hex(),
        "target": _byte_receipt(pair.closed.unit.target_bytes),
        "arms": {"CLOSED": _row_receipt(rows.closed), "ATOM_LOCAL": _row_receipt(rows.atom_local)},
    } for pair, rows in zip(pairs, measured)]
    receipt = canonical_json({
        "schema": "ASTRA_STAGE2A_SOURCE_PREPARATION_V1", "status": STATUS,
        "count_basis": COUNT_BASIS, "caller_obligations": list(CALLER_OBLIGATIONS),
        "master_sha256": sha256(master).hexdigest(), "padding_policy": padding_policy,
        "tape_fingerprint": fingerprint, "paired_target_count": len(pairs),
        "planned_paired_batch_count": len(batches), "executed_updates": 0,
        "later_requested_slice": {"stage": "D1", "arm": "ATOM_LOCAL", "updates": 256},
        "units": units, "batches": batch_receipts,
        "accounting_by_stage": {stage: {arm: dict(counts) for arm, counts in arms.items()}
                                for stage, arms in totals.items()},
    })
    return PreparedBirth(pairs, measured, batches, fingerprint, receipt, sha256(receipt).hexdigest())


def prepare_reduced_held(*, bound_allocation):
    """Construct the existing reduced objects from bound roles, never new pools.

    Maps directly into screen_runtime.run_reduced_state's chains/interventions/
    canaries arguments, but never invokes that runtime or any scorer. Canary
    c12..c15 are STOP and receive no newly invented role or identifier.
    """
    chain_tokens = bound_allocation.role_tokens_by_world("dose_chain")
    intervention_tokens = bound_allocation.role_tokens_by_world("dose_intervention")
    canary_tokens = bound_allocation.role_tokens_by_domain["generic_canary"]
    chain_names = {task: f"h{task // 2:02d}" for task in screen.CHAIN_TASKS}
    intervention_names = {(transition.upper(), pair): f"{transition}_k{pair}"
                          for transition in held.TRANSITIONS for pair in screen.INTERVENTION_PAIRS}
    selected = []
    for mappings, names in ((chain_tokens, chain_names), (intervention_tokens, intervention_names)):
        if not isinstance(mappings, Mapping) or any(name not in mappings for name in names.values()):
            raise ValueError("bound_reduced_world_roles_required")
        for name in names.values():
            selected.append({"world": name, "roles": _byte_receipt(canonical_json(dict(mappings[name])))})
    chains = {task: held.build_chain_world(world=name, role_tokens=chain_tokens[name])
              for task, name in chain_names.items()}
    interventions = {key: held.build_intervention_pair(world=name, role_tokens=intervention_tokens[name])
                     for key, name in intervention_names.items()}
    canaries = canary_api.build_canaries(role_tokens=canary_tokens)
    receipt = canonical_json({
        "schema": "ASTRA_STAGE2A_REDUCED_HELD_SOURCE_V1", "status": STATUS,
        "caller_obligations": list(CALLER_OBLIGATIONS), "role_bindings": selected,
        "chains": [{"task": task, "world": name, "member": task % 2}
                   for task, name in chain_names.items()],
        "interventions": [{"transition": transition, "pair": pair, "world": name}
                          for (transition, pair), name in intervention_names.items()],
        "generic_canary_roles": _byte_receipt(canonical_json(dict(canary_tokens))),
        "canaries": [{"index": item.index, "target_bytes_hex": item.target.encode("ascii").hex(),
                      "target": _byte_receipt(item.target.encode("ascii")),
                      "user": _byte_receipt(item.user_text.encode("ascii")),
                      "system": _byte_receipt(item.system_text.encode("ascii"))} for item in canaries],
    })
    return ReducedHeld(MappingProxyType(chains), MappingProxyType(interventions), canaries,
                       receipt, sha256(receipt).hexdigest())
