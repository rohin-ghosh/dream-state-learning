"""Separate free-endpoint DEV successor; reuse saved IDs, never solve or redraw.

The failed candidate/null generator attempt remains closed. This material makes
no claim of original P-CHAIN-2 protocol compliance or shortcut-null clearance.
Only the caller CLI loads a local tokenizer; no path loads a model or fits.
"""

import argparse
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import signal
import time

from gpu import astra_pchain2_native as native
from gpu import astra_pchain2_prepare as source


MATERIAL_KIND = "PCHAIN2_FREE_ENDPOINT_DEV_V1"
CLAIM_BOUNDARY = dict(original_pchain2_protocol_compliance=False, null_clearance=False,
                      predecessor_generator_attempt="closed_without_assignment",
                      endpoint_assignment="endpoints[i]", endpoint_permutation="i^1",
                      scoring="exact_free_output_bytes_with_terminal_eot_no_truncation")


def validate_saved_identifiers(receipt, tokenizer, *, check=lambda: None):
    native._require(type(receipt) is dict and receipt.get("master") == source.MATERIAL_MASTER.decode("ascii"),
                    "saved_identifier_master_mismatch")
    identifiers, salts = receipt.get("identifiers"), receipt.get("accepted_salts")
    native._require(type(identifiers) is list and len(identifiers) == native.IDENTIFIER_COUNT
                    and all(type(identifier) is str and re.fullmatch("[a-z]{16}", identifier)
                            for identifier in identifiers), "exact_192_lowercase_16letter_identifiers_required")
    native._require(len(set(identifiers)) == native.IDENTIFIER_COUNT, "saved_identifier_collision")
    limit = receipt.get("salt_limit")
    native._require(type(limit) is int and 1 <= limit <= 2**32
                    and type(salts) is list and len(salts) == native.IDENTIFIER_COUNT
                    and all(type(salt) is int and 0 <= salt < limit for salt in salts),
                    "saved_salt_receipt_required")
    native._require(type(receipt.get("native_length")) is int and receipt["native_length"] == 8,
                    "saved_native_length_mismatch")
    specials = set(tokenizer.all_special_ids)
    for serial, (identifier, salt) in enumerate(zip(identifiers, salts)):
        check()
        native._require(native.identifier_candidate(serial, salt) == identifier, "saved_identifier_stream_mismatch")
        encoded = native._encode(tokenizer, identifier)
        native._require(len(encoded) == 8 and not specials.intersection(encoded), "saved_identifier_not_native_L8")
        native._require(native._decode(tokenizer, encoded) == identifier, "saved_identifier_roundtrip_mismatch")
    return tuple(identifiers)


def free_two_hop_user(chain, *, direct=False, supplied=None):
    prefix = ""
    if supplied is True:
        prefix = f"AVAILABLE RELATIONS\nNEXT {chain.source} => {chain.middle}\nNEXT {chain.middle} => {chain.endpoint}\n"
    elif supplied is False:
        prefix = "AVAILABLE RELATIONS\nNONE\n"
    output = "Return exactly one ANSWER line.\n" if direct else "Return exactly two MEMORY lines followed by one ANSWER line.\n"
    return prefix + f"QUERY\nStarting at {chain.source}, apply NEXT exactly twice.\nOUTPUT\n" + output


def prepare_free_evaluation(*, fact_chains, prompt_chains):
    fact_ids, prompt_ids = source._fact_chains(fact_chains), source._fact_chains(prompt_chains)
    source._identifiers(fact_ids + prompt_ids)
    native._require(not set(fact_ids) & set(prompt_ids), "fact_prompt_identifier_overlap")
    permutation = source.SECOND_HOP_PERMUTATION
    calls = []
    for slot in source.d1_readout_slots():
        if slot.panel == "canary":
            calls.append(source.ReadoutCall(slot, None, None))
            continue
        if slot.panel == "one_hop":
            index = slot.index % 16
            chain = fact_chains[index]
            endpoint = fact_chains[permutation[index]].endpoint if slot.state == "DERANGED-JUNCTION" else chain.endpoint
            origin, target = (chain.source, chain.middle) if slot.index < 16 else (chain.middle, endpoint)
            user = f"QUERY\nRecall NEXT for {origin}.\nOUTPUT\nReturn exactly one MEMORY line.\n"
            expected = source._memory(origin, target)
        else:
            prompt = slot.panel in ("prompt_trace", "prompt_empty")
            chain = (prompt_chains if prompt else fact_chains)[slot.index]
            endpoint = (fact_chains[permutation[slot.index]].endpoint
                        if slot.state == "DERANGED-JUNCTION" and not prompt else chain.endpoint)
            direct = slot.panel == "eval_direct"
            user = free_two_hop_user(chain, direct=direct,
                                    supplied=(slot.panel == "prompt_trace") if prompt else None)
            expected = f"ANSWER {endpoint}\n" if direct else source._trace(source.Chain(chain.source, chain.middle, endpoint))
        calls.append(source.ReadoutCall(slot, user, expected.encode("ascii")))
    return source.EvaluationPreparation(tuple(calls), source._binding(fact_chains, permutation), fact_ids, prompt_ids)


def generate_material(tokenizer, *, saved_identifiers, max_context=16384, canaries=None, check=lambda: None):
    native._require(type(max_context) is int and max_context > 0, "positive_context_limit_required")
    identifiers = validate_saved_identifiers(saved_identifiers, tokenizer, check=check)
    signature = native.tokenizer_signature(tokenizer)
    fact_roles, prompt_roles, skill_roles = native._domain_roles(identifiers)
    facts = tuple(source.Chain(fact_roles[index], fact_roles[16 + index], fact_roles[32 + index]) for index in range(16))
    prompts = tuple(source.Chain(prompt_roles[index], prompt_roles[16 + index], prompt_roles[32 + index]) for index in range(16))
    skills = tuple(source.Chain(skill_roles[index], skill_roles[32 + index], skill_roles[64 + index]) for index in range(32))
    prepared = source.prepare_training(fact_chains=facts, junction_examples=skills)
    evaluation = prepare_free_evaluation(fact_chains=facts, prompt_chains=prompts)
    source.check_cross_corpus(prepared, evaluation)
    evaluation = native._bind_canaries(evaluation, canaries, identifiers)
    encoded = {}
    for state in prepared.states:
        encoded[state.name] = []
        for row in state.rows:
            check()
            encoded[state.name].append(native.encode_training_row(row.messages(), tokenizer, max_context=max_context))
    for batch in prepared.states[0].batches:
        authentic = [token for row in batch for token in encoded["ATOM-JUNCTION"][row].target_ids]
        deranged = [token for row in batch for token in encoded["DERANGED-JUNCTION"][row].target_ids]
        local = [token for row in batch for token in encoded["ATOM-LOCAL"][row].target_ids]
        native._require(Counter(authentic) == Counter(deranged), "coupled_batch_target_token_multiset_mismatch")
        native._require(len(local) == len(authentic), "LOCAL_JUNCTION_batch_target_token_count_mismatch")
    prompt_lengths = []
    for call in evaluation.calls:
        check()
        if call.user is None:
            continue
        native._require("ENDPOINT CANDIDATES" not in call.user, "candidate_block_not_allowed")
        ids = tokenizer.apply_chat_template(call.actor_messages(), tokenize=True, add_generation_prompt=True,
                                             return_dict=False, truncation=False, padding=False)
        native._require(isinstance(ids, (list, tuple)) and all(type(token) is int for token in ids),
                        "prompt_token_ids_required")
        native._require(len(ids) + call.slot.max_new_tokens <= max_context, "readout_context_overflow")
        prompt_lengths.append(len(ids))
    common = dict(schema=native.SCHEMA, material_kind=MATERIAL_KIND, tokenizer=signature,
                  max_context=max_context, claim_boundary=CLAIM_BOUNDARY,
                  identifier_receipt_sha256=native._digest(saved_identifiers))
    training = {state.name: {**state.trainer_manifest(), **common, "status": MATERIAL_KIND,
                             "encoded_rows": [asdict(row) for row in encoded[state.name]]}
                for state in prepared.states}
    for manifest in training.values():
        manifest.pop("native_ready")
    readouts = {state: dict(**common, state=state,
                           calls=[dict(slot=asdict(call.slot), user=call.user,
                                       expected=None if call.expected is None else call.expected.decode("ascii"))
                                  for call in evaluation.calls if call.slot.state == state]) for state in source.STATES}
    return dict(training=training, evaluation=readouts,
                summary=dict(**common, status="FREE_ENDPOINT_MATERIAL_COMPLETE", model_calls=0, fits=0,
                             solver_calls=0, identifier_allocation_calls=0, budget=source.build_d1_plan()["budget"],
                             max_prompt_tokens=max(prompt_lengths),
                             missing_canary_calls=sum(call.user is None for call in evaluation.calls),
                             blocked_bindings=[] if canaries is not None else [
                                 dict(code="GENERIC_CANARY_BYTES", owner="Main", blocks="learned_arm_readout")],
                             tape_sha256=source.presentation_tape_sha256(source.build_presentation_tape())))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifiers-file", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--canaries", help="JSON list of 16 canonical {user, expected} objects")
    parser.add_argument("--max-context", type=int, default=16384)
    parser.add_argument("--deadline-seconds", type=float, default=180)
    args = parser.parse_args(argv)
    native._require(math.isfinite(args.deadline_seconds) and args.deadline_seconds > 0 and args.max_context > 0,
                    "positive_finite_limits_required")
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()

    def check():
        if time.monotonic() - started >= args.deadline_seconds:
            raise TimeoutError("caller_deadline_exceeded")

    def expire(signum, frame):
        raise TimeoutError("caller_deadline_exceeded")

    previous_handler = signal.signal(signal.SIGALRM, expire)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, args.deadline_seconds)
    try:
        raw = Path(args.identifiers_file).read_bytes()
        saved = json.loads(raw)
        native._write(output / "REQUEST.json", dict(material_kind=MATERIAL_KIND, claim_boundary=CLAIM_BOUNDARY,
                      arguments=vars(args), identifiers_file_sha256=sha256(raw).hexdigest(),
                      source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                      native_sha256=sha256(Path(native.__file__).read_bytes()).hexdigest(),
                      prepare_sha256=sha256(Path(source.__file__).read_bytes()).hexdigest()))
        tokenizer = native.load_local_tokenizer(args.model_dir)
        check()
        material = generate_material(tokenizer, saved_identifiers=saved, max_context=args.max_context,
                                     canaries=None if args.canaries is None else native._read(args.canaries), check=check)
        check()
        with (output / "identifiers.json").open("xb") as stream:
            stream.write(raw)
        for namespace in ("training", "evaluation"):
            (output / namespace).mkdir()
            for state, manifest in material[namespace].items():
                check()
                native._write(output / namespace / (state + ".json"), manifest)
        check()
        native._write(output / "RESULT.json", material["summary"])
    except BaseException as error:
        native._write(output / "FAILED.json", dict(material_kind=MATERIAL_KIND, error=repr(error), retried=False))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, max(0.000001, previous_timer[0] - (time.monotonic() - started)), previous_timer[1])


if __name__ == "__main__":
    main()
