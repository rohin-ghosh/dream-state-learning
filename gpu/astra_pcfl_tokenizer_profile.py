"""Fixed offline tokenizer cost observation, never identifier qualification.

No model/vLLM import, allocation, search, redraw, or tokenizer load at import.
"""

import argparse
from collections import Counter
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from organism_v6 import pcfl_tokenizer_qualification as qualifier_api


SCHEMA = "pcfl.offline_tokenizer_cost_profile.v1"
SALT_COUNT = 4096
TOKENIZER_NAMES = ("config.json", "tokenizer_config.json", "tokenizer.json",
                   "vocab.json", "merges.txt", "special_tokens_map.json",
                   "added_tokens.json", "chat_template.jinja")
PACKAGES = ("transformers", "tokenizers", "huggingface-hub")


class ProfileError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProfileError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        result = hashlib.sha256()
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def write_once(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def offline_environment():
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CUDA_VISIBLE_DEVICES must be explicitly empty")
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        require(os.environ.get(name) == "1", name + " must be 1")
    return {"CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1"}


def environment_identity():
    return {"python": str(Path(sys.executable).resolve()), "version": sys.version,
            "packages": {name: importlib.metadata.version(name) for name in PACKAGES}}


def load_offline_tokenizer(model_path):
    offline_environment()
    require(Path(model_path).is_absolute() and Path(model_path).is_dir(), "cached local model directory required")
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False)


def tokenizer_file_pins(model_path):
    model = Path(model_path)
    require((model / "tokenizer_config.json").is_file() and (model / "tokenizer.json").is_file(),
            "cached tokenizer_config.json and tokenizer.json required")
    files = {}
    for name in TOKENIZER_NAMES:
        path = model / name
        if path.exists():
            require(path.is_file(), "tokenizer pin is not a file")
            files[name] = file_hash(path)
    for directory_name in ("chat_templates", "additional_chat_templates"):
        template_directory = model / directory_name
        if template_directory.exists():
            require(template_directory.is_dir(), "template path is not a directory")
            for path in sorted(template_directory.rglob("*.jinja")):
                require(path.is_file(), "template is not a file")
                files[str(path.relative_to(model))] = file_hash(path)
    return files


def _encoded(tokenizer, text, clock_ns):
    started = clock_ns()
    ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    ended = clock_ns()
    require(type(started) is int and type(ended) is int and 0 <= started <= ended, "invalid profiling clock")
    require(isinstance(ids, (list, tuple)) and ids and all(type(token) is int and token >= 0 for token in ids),
            "invalid actual tokenizer IDs")
    ids = list(ids)
    return {"text": text, "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "token_ids": ids, "token_ids_sha256": digest(ids), "token_count": len(ids),
            "encode_elapsed_ns": ended - started}


def _summary(records):
    lengths = Counter(record["token_count"] for record in records)
    elapsed = [record["encode_elapsed_ns"] for record in records]
    return {"records": len(records), "distinct_candidates": len({record["text"] for record in records}),
            "distinct_token_sequences": len({tuple(record["token_ids"]) for record in records}),
            "token_length_distribution": {str(length): lengths[length] for length in sorted(lengths)},
            "token_count_total": sum(record["token_count"] for record in records),
            "encode_elapsed_ns_total": sum(elapsed), "encode_elapsed_ns_min": min(elapsed) if elapsed else None,
            "encode_elapsed_ns_max": max(elapsed) if elapsed else None}


def run_profile(model_path, output_dir, *, include_provisional_roots=False, expected_pins=None,
                tokenizer_loader=None, environment_reader=environment_identity, clock_ns=time.perf_counter_ns):
    """Exactly salts 0..4095, no warmup/selection; optional roots are separate.

    Injection is for synthetic CPU tests. A profile cannot authorize a model
    call, certify a manifest or alter the qualifier's production allocator.
    """
    require(type(include_provisional_roots) is bool, "provisional flag must be Boolean")
    flags = offline_environment()
    model, output = Path(model_path), Path(output_dir)
    require(model.is_absolute() and model.is_dir(), "actual cached absolute model path required")
    require(output.is_absolute() and not output.exists() and not output.is_symlink(), "fresh absolute output directory required")
    require(output.parent.is_dir() and output.parent.resolve() == output.parent, "output parent must exist without aliases")
    model_resolved = model.resolve()
    require(model_resolved != output and model_resolved not in output.parents and output not in model_resolved.parents,
            "output and cached model must be disjoint")
    expected = copy.deepcopy(expected_pins)
    if expected is not None:
        require(type(expected) is dict and set(expected) == {"files", "chat_template_sha256"}, "expected pin schema")
    output.mkdir()
    loader = load_offline_tokenizer if tokenizer_loader is None else tokenizer_loader
    kind = "OFFLINE_TOKENIZER_MEASUREMENT" if tokenizer_loader is None else "SYNTHETIC_CPU_FIXTURE"
    records, provisional = [], []
    attempts = 0
    phase = "identity"
    started = clock_ns()
    try:
        source_paths = {"profile": Path(__file__).resolve(), "qualifier": Path(qualifier_api.__file__).resolve()}
        if include_provisional_roots:
            from organism_v6 import pcfl_vertical_dev as core_api
            source_paths["provisional_core"] = Path(core_api.__file__).resolve()
        source_pins = {name: {"path": str(path), "sha256": file_hash(path)} for name, path in source_paths.items()}
        files = tokenizer_file_pins(model)
        if expected is not None:
            require(expected["files"] == files, "expected tokenizer file pins differ")
        identity = {"schema": SCHEMA, "kind": kind, "model_path": str(model), "resolved_model_path": str(model_resolved),
                    "files": files, "sources": source_pins, "environment": environment_reader(), "offline_flags": flags,
                    "candidate_domain": {"root": "excluded/0", "namespace": "node", "index": 0,
                                         "salt_start": 0, "salt_stop_exclusive": SALT_COUNT},
                    "include_provisional_roots": include_provisional_roots,
                    "encoding": {"add_special_tokens": False, "truncation": False},
                    "qualified": False, "ready_for_model_calls": False}
        write_once(output / "identity.json", identity)
        phase = "tokenizer_load"
        load_started = clock_ns()
        tokenizer = loader(str(model))
        load_ended = clock_ns()
        require(Path(tokenizer.name_or_path).resolve() == model_resolved, "loaded tokenizer path differs")
        template = tokenizer.chat_template
        require(type(template) is str and bool(template), "exact loaded chat template required")
        template_hash = hashlib.sha256(template.encode("utf-8")).hexdigest()
        if expected is not None:
            require(expected["chat_template_sha256"] == template_hash, "expected chat template differs")
        pins = {"files": files, "chat_template_sha256": template_hash}
        write_once(output / "tokenizer.json", {"pins": pins, "chat_template": template,
                                              "class": type(tokenizer).__module__ + "." + type(tokenizer).__qualname__,
                                              "load_elapsed_ns": load_ended - load_started})
        require(tokenizer_file_pins(model) == files, "tokenizer files changed during load")
        require(offline_environment() == flags, "offline environment changed during load")
        phase = "candidate_encode"
        pool_started = clock_ns()
        with (output / "candidates.jsonl").open("xb") as stream:
            for salt in range(SALT_COUNT):
                candidate = qualifier_api.opaque_candidate("excluded/0", "node", 0, salt)
                attempts += 1
                record = {"root": "excluded/0", "namespace": "node", "index": 0, "salt": salt,
                          **_encoded(tokenizer, candidate, clock_ns)}
                stream.write(canonical(record) + b"\n")
                records.append(record)
            stream.flush()
            os.fsync(stream.fileno())
        pool_ended = clock_ns()
        provisional_summary = None
        if include_provisional_roots:
            phase = "provisional_root_encode"
            roots = [core_api.build_root(f"excluded/{index}") for index in range(4)]
            write_once(output / "provisional_roots.json", {"status": "UNQUALIFIED", "roots": [core_api.to_data(root) for root in roots]})
            with (output / "provisional_tokens.jsonl").open("xb") as stream:
                for root in roots:
                    for namespace, slots in root.inventory:
                        for slot, identifier in slots:
                            record = {"status": "UNQUALIFIED", "root": root.label, "namespace": namespace, "slot": slot,
                                      **_encoded(tokenizer, identifier, clock_ns)}
                            stream.write(canonical(record) + b"\n")
                            provisional.append(record)
                stream.flush()
                os.fsync(stream.fileno())
            provisional_summary = {"status": "UNQUALIFIED", "root_count": 4, "total": _summary(provisional),
                "per_namespace": {namespace: _summary([record for record in provisional if record["namespace"] == namespace])
                                  for namespace in sorted({record["namespace"] for record in provisional})},
                "per_root_namespace": {root.label: {namespace: _summary([record for record in provisional if record["root"] == root.label and record["namespace"] == namespace])
                                                   for namespace, _ in root.inventory} for root in roots},
                "receipts_sha256": file_hash(output / "provisional_tokens.jsonl")}
        phase = "final_identity_check"
        require(tokenizer_file_pins(model) == files, "tokenizer files changed during profiling")
        require(tokenizer.chat_template == template, "loaded chat template changed during profiling")
        require(all(file_hash(source_paths[name]) == pin["sha256"] for name, pin in source_pins.items()), "profile/candidate/core source drift")
        require(offline_environment() == flags, "offline environment changed")
        require(attempts == len(records) == SALT_COUNT, "fixed candidate denominator differs")
        report = {"schema": SCHEMA, "kind": kind, "status": "PROFILE_COMPLETE_UNQUALIFIED",
                  "planned_candidates": SALT_COUNT, "encode_attempts": attempts, "candidate_summary": _summary(records),
                  "candidate_receipts_sha256": file_hash(output / "candidates.jsonl"),
                  "identity_sha256": file_hash(output / "identity.json"), "tokenizer_receipt_sha256": file_hash(output / "tokenizer.json"),
                  "tokenizer_pins": pins, "provisional_roots": provisional_summary,
                  "timing": {"clock": "perf_counter_ns" if clock_ns is time.perf_counter_ns else "injected_clock_ns",
                             "tokenizer_load_elapsed_ns": load_ended - load_started,
                             "candidate_loop_elapsed_ns": pool_ended - pool_started,
                             "observation_elapsed_ns": clock_ns() - started,
                             "encode_scope": "individual encode calls only; loop includes candidate/hash/receipt overhead; no warmup"},
                  "qualified": False, "selection_performed": False, "allocator_changed": False,
                  "ready_for_model_calls": False,
                  "limitations": ["single finite CPU timing observation, not an allocator throughput guarantee",
                                  "salt pool is measured without filtering, searching, redraw or qualification",
                                  "no full manifest, joint substitution or production release certification",
                                  "no model weights read, model/vLLM load or GPU work"]}
        write_once(output / "profile.json", report)
        return copy.deepcopy(report)
    except Exception as error:
        write_once(output / "failure.json", {"schema": SCHEMA, "kind": kind, "status": "FAILED_INCOMPLETE_NO_RETRY",
                                           "phase": phase, "error_type": type(error).__name__, "planned_candidates": SALT_COUNT,
                                           "candidate_encode_attempts": attempts, "candidate_records_written": len(records),
                                           "provisional_records_written": len(provisional), "qualified": False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure exactly 4096 fixed candidate encodings offline; no qualification or model load.")
    parser.add_argument("--model", required=True, help="absolute cached local model/tokenizer directory")
    parser.add_argument("--output", required=True, help="absolute fresh output directory")
    parser.add_argument("--expected-pins", help="optional JSON with exact files and chat_template_sha256")
    parser.add_argument("--include-provisional-roots", action="store_true", help="also encode raw excluded/0..3 IDs, explicitly UNQUALIFIED")
    args = parser.parse_args(argv)
    try:
        expected = None if args.expected_pins is None else json.loads(Path(args.expected_pins).read_bytes())
        report = run_profile(args.model, args.output, include_provisional_roots=args.include_provisional_roots, expected_pins=expected)
    except Exception as error:
        print(json.dumps({"status": "FAILED", "error_type": type(error).__name__, "output": args.output}), file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "output": args.output, "profile_sha256": file_hash(Path(args.output) / "profile.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
