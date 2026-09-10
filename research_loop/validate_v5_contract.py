from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

from alchemy.backend import HFBackend, VLLMBackend


def main() -> int:
    failures = []
    root = Path(__file__).resolve().parents[1]
    source = (root / "alchemy/run_lands_v02_dreamladder.py").read_text()
    thinker_source = (root / "alchemy/run_lands_v02_organism.py").read_text()
    backend_source = (root / "alchemy/backend.py").read_text()
    spec = json.loads(
        (root / "research_loop/workflows/dream_ladder_v5.remote.json").read_text()
    )
    workflow = json.loads(
        (root / "research_loop/workflows/dream_ladder_v5.json").read_text()
    )
    for backend in (HFBackend, VLLMBackend):
        parameters = inspect.signature(backend.generate).parameters
        for name in ("temperature", "seed"):
            if name not in parameters:
                failures.append(f"{backend.__name__}.generate lacks {name}")
    required_source = (
        "roles_by_prefix[sample_index]",
        "temperature=a.temperature",
        "seed=sample_seed",
        '"retained_true"',
        '"retained_total"',
        '"unique_proposed_total"',
        '"malformed_total"',
        '"public_evidence_exact_gate": True',
        '"source": "run_lands_v02_dreamladder"',
        "candidate_lines_with_budget",
        "not 2 <= len(raw_parents) <= 5",
        '"status": "contradicted"',
        '"token_count_source": usage["source"]',
        '"overflow_candidates"',
        '"ordinary_source_lands_only"',
        '"role_discovery_evidence"',
        '"excluded_target_evidence_ids"',
        '"blind_comparison_evidence"',
        '"retained_truth_presence"',
        '"candidate_ceiling_per_target"',
        '"matched_compute_to_v4": False',
    )
    failures.extend(
        f"dream ladder missing contract: {text}"
        for text in required_source if text not in source
    )
    if "return_dict=False" not in backend_source:
        failures.append("vLLM chat IDs do not force list output")
    if '"offline_parent_exact"' in source:
        failures.append("unsafe parent-exact truth-presence label remains")
    for text in ("canonical_label_answer", "public_canonical_labels(rows)",
                 "parse_thinker_operation(raw_out)",
                 "score_canonical_answer(final, public_labels, want)",
                 '"raw_completion": raw_out',
                 '"thinker_generation_calls"',
                 '"memory_query_operations"',
                 '"token_count_source": "model_token_ids"',
                 '"malformed_outputs"'):
        if text not in thinker_source:
            failures.append(f"thinker missing exact-score contract: {text}")
    if 'len(markers) != 1' not in thinker_source:
        failures.append("thinker does not reject additional operation markers")
    dream_argv = next(stage["argv"] for stage in spec["stages"]
                      if stage["id"] == "dream_v5")
    for token in ("--samples", "4", "--temperature", "0.7", "--sample-seed", "28001"):
        if token not in dream_argv:
            failures.append(f"remote dream argv missing {token}")
    if "corpus = json.load(open(path))" in source:
        failures.append("dream ladder still consumes ambient organism corpus")
    freeze_argv = workflow["nodes"]["freeze_review_inputs"]["argv"]
    locally_locked = {
        freeze_argv[index + 1]
        for index, value in enumerate(freeze_argv[:-1]) if value == "--file"
    }
    remote_required = set(spec["freeze_inputs"]) | {
        "research_loop/workflows/dream_ladder_v5.remote.json"
    }
    missing_lock_coverage = sorted(remote_required - locally_locked)
    if missing_lock_coverage:
        failures.append(
            f"remote inputs absent from local review lock: {missing_lock_coverage}"
        )
    stage_ids = [stage["id"] for stage in spec["stages"]]
    if stage_ids != [
        "runtime_preflight", "capture_environment", "dream_v5",
        "think_dreamtext",
    ]:
        failures.append(f"unexpected remote stage order: {stage_ids}")
    launch = workflow["nodes"]["launch_h100"]["argv"][-1]
    if ("v2node_start_research_job.sh" not in launch
            or "{fresh_sol_review_binding_sha256}" not in launch):
        failures.append("launch is not bound to the approved receipt digest")
    if failures:
        print(json.dumps({"ok": False, "failures": failures}, indent=2))
        return 1
    print(json.dumps({"ok": True, "checks": 21}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
