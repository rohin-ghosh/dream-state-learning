"""Offline fixed-L8 C0 inventory, not the original full-assay allocator."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gpu import astra_pcfl_tokenizer_profile as profile
from gpu import astra_pcfl_zero_fit_dev as driver
from organism_v6 import pcfl_tokenizer_qualification as qualifier


SCHEMA = "SCOPED_C0_FIXED_L8_NOT_FULL_ALLOCATOR"
ROOTS = tuple(f"excluded/{index}" for index in range(4))
LENGTH = 8
SALT_LIMIT = 1000000
POLICY_PATH = driver.ROOT / "research_notes/astra_memos/ASTRA_PCFL_C0_INVENTORY_POLICY_2026-09-13.md"
POLICY_SHA256 = "afdcf27496bdaccb7188760959d3c38f7000d00ae96e428167c052b08644b1bb"
RESERVED = ("EVENT", "AT", "DID", "GOT", "EVIDENCE", "LINK", "FROM", "THEN", "VIA",
            "RECEIPT", "READ", "EVENTS_AT", "LINKS_FROM", "ROUTE", "EXPLORE", "PROBE", "RESULT", "TESTED", "TO",
            "AVAILABLE", "PORT", "MEMORY", "MISS", "EDGE", "TASK", "START", "GOAL", "PROBES", "TESTS", "SOURCE",
            "DESTINATION", "OPTIONS", "TEST", "USING", "PORTS", "COMMIT", "ADDRESS")
canonical, digest = profile.canonical, profile.digest
require, file_hash, write_once = profile.require, profile.file_hash, profile.write_once


def reserved_literals():
    return {"prompt_keywords": list(RESERVED), "parser_prefixes": [], "canary_ids": [], "other": []}


def _hash(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "invalid SHA256")
    return value


def _read_bound(path, expected):
    require(Path(path).is_absolute() and Path(path).is_file(), "absolute bound input file required")
    data = Path(path).read_bytes()
    require(hashlib.sha256(data).hexdigest() == _hash(expected), "bound input hash differs: " + str(path))
    return data


def _identity(model, pins, public):
    require(type(pins) is dict and set(pins) == {"files", "chat_template_sha256"}, "tokenizer pins schema")
    _hash(pins["chat_template_sha256"])
    require(pins["files"] == profile.tokenizer_file_pins(model), "exact tokenizer file inventory/hash differs")
    require(driver.native.TOKENIZER_FILES <= set(pins["files"]), "missing native tokenizer files")
    require(public["repository"] == driver.native.MODEL_NAME and public["revision"] == driver.native.REVISION
            and public["status"] == "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING"
            and Path(public["model"]).resolve() == model, "public C0 receipt binding differs")
    require(type(public["file_count"]) is int and public["file_count"] == len(public["files"]) == 14,
            "public 14-file receipt required")
    for name, entry in public["files"].items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and "adapter" not in name.lower(), "invalid public file name")
        _hash(entry["sha256"])
        require(entry["public_match"] in ("GIT_BLOB_SHA1", "LFS_SHA256")
                and type(entry["size"]) is int and entry["size"] >= 0, "invalid public file receipt")
    for name, expected in pins["files"].items():
        require(name in public["files"] and public["files"][name]["sha256"] == expected
                and public["files"][name]["size"] == (model / name).stat().st_size, "tokenizer/public receipt mismatch")


def _tokens(tokenizer, text):
    tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    require(type(tokens) in (list, tuple) and tokens and all(type(token) is int and token >= 0 for token in tokens), "invalid token IDs")
    return list(tokens)


def allocate(tokenizer, candidate_sink, choice_sink, choices, *, deadline=None):
    """Deterministic CPU seam; sinks preserve every attempt, including failures."""
    require(type(choices) is list and not choices, "fresh choice list required")
    raw_seen, token_seen = set(), set()
    reserved = reserved_literals()
    for root in ROOTS:
        for namespace, slots in driver.core.SLOTS.items():
            for index, slot in enumerate(slots):
                for salt in range(SALT_LIMIT):
                    require(deadline is None or time.monotonic() < deadline, "180s preparation envelope exhausted")
                    text = qualifier.opaque_candidate(root, namespace, index, salt)
                    row = {"root": root, "namespace": namespace, "index": index, "slot": slot, "salt": salt,
                           "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
                    try:
                        qualifier.validate_identifier(text, namespace)
                        tokens = _tokens(tokenizer, text)
                    except Exception as error:
                        candidate_sink({**row, "accepted": False, "reasons": ["ENCODING_ERROR"],
                                        "exception_type": type(error).__name__, "exception": str(error),
                                        "traceback": traceback.format_exc()})
                        raise
                    reasons = []
                    if len(tokens) != LENGTH:
                        reasons.append("NOT_L8")
                    if text in raw_seen:
                        reasons.append("RAW_COLLISION")
                    if tuple(tokens) in token_seen:
                        reasons.append("TOKEN_COLLISION")
                    if qualifier._reserved(text, reserved):
                        reasons.append("RESERVED_COLLISION")
                    row.update(token_ids=tokens, token_ids_sha256=digest(tokens), token_count=len(tokens),
                               accepted=not reasons, reasons=reasons)
                    candidate_sink(row)
                    if reasons:
                        continue
                    choice = {**row, "candidate_sha256": digest(row)}
                    choice["choice_sha256"] = digest(choice)
                    choice_sink(choice)
                    choices.append(choice)
                    raw_seen.add(text)
                    token_seen.add(tuple(tokens))
                    break
                else:
                    raise ValueError(f"SALT_EXHAUSTED: {root}/{namespace}/{slot}; no redraw")
    inventories = {root: {namespace: {} for namespace in driver.core.SLOTS} for root in ROOTS}
    for choice in choices:
        inventories[choice["root"]][choice["namespace"]][choice["slot"]] = choice["text"]
    return [driver.core.to_data(driver.core.build_root(root, inventories[root])) for root in ROOTS]


def run_inventory(model_path, policy_path, policy_sha256, tokenizer_pins_path, tokenizer_pins_sha256,
                  public_receipt_path, public_receipt_sha256, output_dir, *, tokenizer_loader=None):
    """Production loads only AutoTokenizer; explicit injection is synthetic only."""
    flags = profile.offline_environment()
    deadline = time.monotonic() + 180
    model, output = Path(model_path).resolve(), Path(output_dir)
    require(Path(model_path).is_absolute() and model.is_dir(), "absolute cached model required")
    require(output.is_absolute() and not output.exists() and not output.is_symlink(), "fresh absolute output required")
    require(output.parent.is_dir() and output.parent.resolve() == output.parent, "output parent must exist without aliases")
    require(model != output and model not in output.parents and output not in model.parents, "model/output overlap")
    bindings = {str(Path(path)): expected for path, expected in
                ((policy_path, policy_sha256), (tokenizer_pins_path, tokenizer_pins_sha256),
                 (public_receipt_path, public_receipt_sha256))}
    require(len(bindings) == 3, "distinct binding files required")
    for path, expected in bindings.items():
        _read_bound(path, expected)
    synthetic = tokenizer_loader is not None
    if not synthetic:
        require(POLICY_SHA256 is not None and policy_sha256 == POLICY_SHA256, "policy not frozen or hash differs")
    policy = _read_bound(policy_path, policy_sha256)
    pins = json.loads(_read_bound(tokenizer_pins_path, tokenizer_pins_sha256))
    public = json.loads(_read_bound(public_receipt_path, public_receipt_sha256))
    sources = driver.source_snapshot()
    for path in (__file__, profile.__file__, qualifier.__file__):
        sources[str(Path(path).resolve())] = file_hash(path)
    output.mkdir()
    choices, phase = [], "IDENTITY"
    try:
        write_once(output / "inputs.json", {"schema": SCHEMA, "kind": "SYNTHETIC_CPU_FIXTURE" if synthetic else "ACTUAL_OFFLINE",
                   "model_path": str(model), "bindings": bindings, "tokenizer_pins": pins,
                   "source_files": sources, "offline_flags": flags, "reserved_literals": reserved_literals(),
                   "root_order": list(ROOTS), "slots": {name: list(slots) for name, slots in driver.core.SLOTS.items()},
                   "length": LENGTH, "salt_limit_exclusive": SALT_LIMIT, "policy_text_sha256": hashlib.sha256(policy).hexdigest()})
        _identity(model, pins, public)
        phase = "TOKENIZER_LOAD"
        loader = profile.load_offline_tokenizer if tokenizer_loader is None else tokenizer_loader
        tokenizer = loader(str(model))
        require(Path(tokenizer.name_or_path).resolve() == model, "loaded tokenizer path differs")
        require(type(tokenizer.chat_template) is str and hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()
                == pins["chat_template_sha256"], "loaded chat template differs")
        _identity(model, pins, public)
        write_once(output / "tokenizer.json", {"pins": pins, "chat_template": tokenizer.chat_template,
                   "class": type(tokenizer).__module__ + "." + type(tokenizer).__qualname__,
                   "environment": {"kind": "SYNTHETIC_CPU_FIXTURE"} if synthetic else profile.environment_identity(),
                   "encoding": {"add_special_tokens": False, "truncation": False}})
        phase = "FIXED_ALLOCATION"
        with (output / "candidates.jsonl").open("xb") as candidates, (output / "choices.jsonl").open("xb") as selected:
            def candidate_sink(row):
                candidates.write(canonical(row) + b"\n")
                candidates.flush()

            def choice_sink(row):
                selected.write(canonical(row) + b"\n")
                selected.flush()

            roots = allocate(tokenizer, candidate_sink, choice_sink, choices, deadline=deadline)
            os.fsync(candidates.fileno())
            os.fsync(selected.fileno())
        write_once(output / "roots.json", roots)
        write_once(output / "choices.json", choices)
        phase = "USED_SURFACE_MEASUREMENT"
        plan = driver.build_tasks(roots)
        write_once(output / "plan.json", plan)
        binding = {"model_path": str(model), "tokenizer_files": {name: pins["files"][name] for name in sorted(driver.native.TOKENIZER_FILES)},
                   "chat_template_sha256": pins["chat_template_sha256"]}
        measurements = driver.measure_tokenizer(plan, tokenizer, binding, synthetic=synthetic)
        write_once(output / "measurements.json", measurements)
        initial = [row for row in measurements["measurements"] if row["id"].startswith("initial/")]
        require(all(len(row["token_ids"]) <= 14336 and len(row["token_ids"]) + 2048 <= driver.native.ENGINE["max_model_len"]
                    for row in initial), "initial context/output budget exceeded")
        phase = "FINAL_CUSTODY"
        _identity(model, pins, public)
        require(profile.offline_environment() == flags, "offline flags drift")
        require(time.monotonic() < deadline, "180s preparation envelope exhausted")
        for path, expected in {**sources, **bindings}.items():
            require(file_hash(path) == expected, "source/input changed during allocation")
        report = {"schema": SCHEMA, "kind": "SYNTHETIC_CPU_FIXTURE" if synthetic else "ACTUAL_OFFLINE",
                  "status": "USED_SURFACES_PASSED", "selected_ids": len(choices), "roots": len(roots),
                  "choice_values_sha256": digest(choices), "plan_sha256": plan["sha256"],
                  "measurements_sha256": measurements["sha256"], "model_calls": 0, "fits": 0, "updates": 0,
                  "full_allocator_qualified": False, "full_v22_release": False, "ready_for_model_calls": False,
                  "policy_sha256": policy_sha256,
                  "files": {name: file_hash(output / name) for name in
                            ("inputs.json", "tokenizer.json", "candidates.jsonl", "choices.jsonl", "choices.json", "roots.json", "plan.json", "measurements.json")}}
        write_once(output / "receipt.json", report)
        return report
    except Exception as error:
        write_once(output / "unqualified_choices.json", choices)
        write_once(output / "failure.json", {"schema": SCHEMA, "status": "UNQUALIFIED_NO_RESELECTION", "phase": phase,
                   "kind": "SYNTHETIC_CPU_FIXTURE" if synthetic else "ACTUAL_OFFLINE", "exception_type": type(error).__name__,
                   "exception": str(error), "traceback": traceback.format_exc(), "selected_ids": len(choices),
                   "files": {path.name: file_hash(path) for path in sorted(output.iterdir()) if path.is_file()},
                   "model_calls": 0, "fits": 0, "updates": 0, "full_allocator_qualified": False, "ready_for_model_calls": False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model", "policy", "policy-sha256", "tokenizer-pins", "tokenizer-pins-sha256",
                 "public-receipt", "public-receipt-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    report = run_inventory(args.model, args.policy, args.policy_sha256, args.tokenizer_pins, args.tokenizer_pins_sha256,
                           args.public_receipt, args.public_receipt_sha256, args.output)
    print(canonical(report).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
