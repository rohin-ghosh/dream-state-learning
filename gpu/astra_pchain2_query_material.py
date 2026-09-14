"""Material-only COPY_TO_RECALL precursor using prior captured synthetic facts.

Only atomic user prompts change. Evaluation files are copied byte-for-byte,
including their original free-endpoint kind. No outcome files are consumed and
no fitting, model loading, identifier allocation, or null solving occurs.
"""

import argparse
from copy import deepcopy
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
from gpu.astra_pchain2_free_material import MATERIAL_KIND as SOURCE_KIND


MATERIAL_KIND = "PCHAIN2_QUERY_ONLY_DEV_V1"


def query_atomic_row(row):
    """Extract only from the original structured training row, never evaluation."""
    messages = row["messages"]
    match = re.fullmatch(r"MEMORY NEXT ([a-z]{16}) => ([a-z]{16})\n", messages[-1]["content"])
    native._require(match is not None, "canonical_atomic_assistant_required")
    origin, target = match.groups()
    native._require(origin != target and messages == source._atomic_row(row["row_id"], origin, target).messages(),
                    "original_atomic_source_row_mismatch")
    changed = deepcopy(row)
    changed["messages"][1]["content"] = f"QUERY\nRecall NEXT for {origin}.\nOUTPUT\nReturn exactly one MEMORY line.\n"
    native._require(target not in changed["messages"][1]["content"], "target_present_in_query_user")
    return changed


def generate_material(tokenizer, *, training_files, evaluation_files, max_context=16384, check=lambda: None):
    """Inputs are exact file bytes; retain originals and return re-encoded training."""
    native._require(set(training_files) == set(source.STATES[1:]) and set(evaluation_files) == set(source.STATES),
                    "complete_prior_training_and_evaluation_required")
    native._require(all(type(raw) is bytes for raw in (*training_files.values(), *evaluation_files.values())),
                    "exact_source_file_bytes_required")
    native._require(type(max_context) is int and max_context > 0, "positive_context_limit_required")
    training = {}
    provenance = {}
    identifier_receipt = None
    for state in source.STATES[1:]:
        check()
        original = json.loads(training_files[state])
        native._require(original["material_kind"] == SOURCE_KIND, "original_free_training_required")
        if identifier_receipt is None:
            identifier_receipt = original["identifier_receipt_sha256"]
        native._require(original["identifier_receipt_sha256"] == identifier_receipt, "mixed_source_identifier_receipts")
        old_encoded, tape = native.validate_training_manifest(original, tokenizer, state=state, max_context=max_context)
        changed = deepcopy(original)
        for index in range(32):
            changed["rows"][index] = query_atomic_row(original["rows"][index])
        encoded = []
        for index, row in enumerate(changed["rows"]):
            check()
            encoded.append(native.encode_training_row(row["messages"], tokenizer, max_context=max_context))
            native._require(encoded[-1].target_ids == old_encoded[index].target_ids,
                            "original_assistant_target_tokens_changed")
        changed["encoded_rows"] = json.loads(native._json_bytes([asdict(row) for row in encoded]))
        native._require(changed["rows"][32:] == original["rows"][32:]
                        and changed["encoded_rows"][32:] == original["encoded_rows"][32:], "skill_rows_or_encoding_changed")
        changed.update(material_kind=MATERIAL_KIND, status=MATERIAL_KIND, max_context=max_context)
        original_hash = sha256(training_files[state]).hexdigest()
        changed["source_training_file_sha256"] = original_hash
        training[state] = changed
        provenance[state] = dict(source_file_sha256=original_hash,
                                 original_rows_file=f"original_training/{state}.json",
                                 original_rows_sha256=native._digest(original["rows"]),
                                 changed_user_row_ids=list(range(32)),
                                 assistant_target_tokens_identical=True, query_targets_are_original_captured_facts=True,
                                 targets_absent_from_atomic_users=True, updates=len(tape),
                                 target_tokens=sum(len(encoded[index].target_ids) for batch in tape for index in batch.row_ids))
    evaluation_hashes = {}
    for state in source.STATES:
        check()
        manifest = json.loads(evaluation_files[state])
        native._require(manifest["material_kind"] == SOURCE_KIND
                        and manifest["identifier_receipt_sha256"] == identifier_receipt, "original_free_evaluation_required")
        native.validate_readout_manifest(manifest, tokenizer, state=state, max_context=max_context)
        evaluation_hashes[state] = sha256(evaluation_files[state]).hexdigest()
    receipt = dict(material_kind=MATERIAL_KIND, status="QUERY_ONLY_MATERIAL_COMPLETE", source_material_kind=SOURCE_KIND,
                   evaluation_material_kind=SOURCE_KIND, evaluation_files_byte_identical=True,
                   evaluation_file_sha256=evaluation_hashes, source_training=provenance,
                   identifier_receipt_sha256=identifier_receipt, max_context=max_context,
                   fits=0, model_calls=0, solver_calls=0, identifier_allocation_calls=0,
                   initial_fit_state_selected_by_Main="ATOM-JUNCTION", other_cells_material_only=True,
                   original_protocol_compliance_claimed=False,
                   tape_sha256=source.presentation_tape_sha256(source.build_presentation_tape()))
    return dict(training=training, original_training_files=dict(training_files),
                evaluation_files=dict(evaluation_files), receipt=receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-material-dir", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--output", required=True)
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
        root = Path(args.source_material_dir)
        training_files = {state: (root / "training" / (state + ".json")).read_bytes() for state in source.STATES[1:]}
        evaluation_files = {state: (root / "evaluation" / (state + ".json")).read_bytes() for state in source.STATES}
        native._write(output / "REQUEST.json", dict(material_kind=MATERIAL_KIND, arguments=vars(args),
                      source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                      native_sha256=sha256(Path(native.__file__).read_bytes()).hexdigest(),
                      prepare_sha256=sha256(Path(source.__file__).read_bytes()).hexdigest(),
                      training_file_sha256={state: sha256(raw).hexdigest() for state, raw in training_files.items()},
                      evaluation_file_sha256={state: sha256(raw).hexdigest() for state, raw in evaluation_files.items()}))
        check()
        tokenizer = native.load_local_tokenizer(args.model_dir)
        material = generate_material(tokenizer, training_files=training_files, evaluation_files=evaluation_files,
                                     max_context=args.max_context, check=check)
        for namespace in ("training", "original_training", "evaluation"):
            (output / namespace).mkdir()
        for state, manifest in material["training"].items():
            check()
            native._write(output / "training" / (state + ".json"), manifest)
        for namespace, key in (("original_training", "original_training_files"), ("evaluation", "evaluation_files")):
            for state, raw in material[key].items():
                check()
                with (output / namespace / (state + ".json")).open("xb") as stream:
                    stream.write(raw)
        check()
        native._write(output / "RESULT.json", material["receipt"])
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
