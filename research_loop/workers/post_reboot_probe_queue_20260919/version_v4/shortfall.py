"""Authenticate the original pre-model input-length guard without model/scoring calls."""

import hashlib
from pathlib import Path
import sys

import admission as rules
import probe_runtime as runtime


BASE_ROOT = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28')


def guard_classification(outcome, tokens, limit):
    error = outcome.get("error")
    return (isinstance(error, dict) and error.get("code") == "provider_error"
        and outcome.get("ok") is False and outcome.get("pause_required") is True
        and outcome.get("status") == "error"
        and not any(field in outcome for field in ("rank", "raw_score", "accepted", "submission_id"))
        and type(tokens) is int and type(limit) is int and limit == 512 and tokens > limit)


def authenticate(config, unknowns):
    root = Path(config["root"])
    runtime.verify_source_closure(root)
    rules.require(runtime.sha(root / "SOURCE_MANIFEST.json") == rules.SOURCE_MANIFEST_SHA, "original_diagnostic_source_closure")
    sys.path.insert(0, str(root / "source"))
    from gpu.ny_caption_judge import canonical_input
    from gpu.ny_caption_scalar_judge import read_config
    from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
    from transformers import AutoTokenizer
    scalar_path = root / "judge/scalar_runtime.json"
    loaded = runtime.read(root / "JUDGE_LOADED.json")
    rules.require(loaded["scalar"]["sha256"] == runtime.sha(scalar_path), "actually_loaded_scalar_config")
    scalar, base, reference = read_config(scalar_path)
    original_base = runtime.read(root / "assets/base_manifest.json")
    rules.require(all(base[key] == value for key, value in original_base.items() if key != "root")
        and Path(base["root"]) == BASE_ROOT, "original_base_manifest_for_tokenizer")
    limit = scalar["config"]["max_length"]
    rules.require(limit == runtime.read(root / "assets/RULE.json")["max_length"] == 512, "original_512_guard")
    tokenizer_hashes = {}
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "merges.txt", "vocab.json"):
        tokenizer_hashes[name] = runtime.sha(BASE_ROOT / name)
        rules.require(tokenizer_hashes[name] == base["files"][name]["sha256"], "bound_original_tokenizer_files")
    tokenizer = AutoTokenizer.from_pretrained(str(BASE_ROOT), local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    scenes = {row["contest_id"]: row for row in runtime.read(root / "GAME_MANIFEST.json")["contests"]}
    evidence = []
    for unknown in unknowns:
        result_path = runtime.inside(root, unknown["path"])
        request_path = result_path.with_name(result_path.name.replace(".result.json", ".request.json"))
        request = runtime.read(request_path)
        result = runtime.read(result_path)
        rules.require(result["request_sha256"] == rules.digest(request), "diagnostic_request_result_join")
        scene = scenes[request["identity"]["contest_id"]]
        actions, parsed = extract_batches(request["raw"], [dict(contest_id=scene["contest_id"], canonical_scene=scene["canonical_scene"])],
            active_scene=scene["contest_id"], explicit_candidates_only=request["origin"]["stage"] == "THINK")
        captions = [caption for action in actions for caption in action["captions"]]
        rules.require(len(captions) == len(result["results"]), "exact_original_caption_extraction")
        ordinal = unknown["ordinal"]
        row = result["results"][ordinal]
        caption = captions[ordinal]
        rules.require(row["result"] == unknown["outcome"] and row["caption_sha256"]
            == hashlib.sha256(caption.encode()).hexdigest(), "exact_failed_caption_join")
        canonical = canonical_input(scene["canonical_scene"], caption)
        count = len(tokenizer(canonical, truncation=False)["input_ids"])
        verified = guard_classification(row["result"], count, limit)
        evidence.append(dict(result_path=unknown["path"], result_sha256=runtime.sha(result_path), ordinal=ordinal,
            caption_sha256=row["caption_sha256"], canonical_input_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            input_tokens=count, max_length=limit, verified_model_free_length_guard=verified, raw_outcome=row["result"]))
    return dict(all_verified=bool(evidence) and all(row["verified_model_free_length_guard"] for row in evidence),
        method="EXACT_ORIGINAL_CANONICAL_INPUT_TOKENIZATION_PRE_MODEL_GUARD", model_loaded=False, scoring_called=False,
        scalar_config_sha256=reference["sha256"], tokenizer_files=tokenizer_hashes, outcomes=evidence,
        confidence_boundary="Deterministic pre-model guard reproduction; original generic handler discarded the traceback.")
