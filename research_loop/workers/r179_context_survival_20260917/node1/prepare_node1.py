"""Build a local, non-executable A100 handoff proposal from pinned metadata."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
MAX_RECEIPT_BYTES = 512 * 1024
SOURCE_BASE = "/localhome/local-rohing/orch_r144_target_rollout_a100_suffix_20260916t1643z"
LANES = {
    2: "teach_replay",
    3: "teach_perception",
    4: "teach_parenting",
    5: "classroom_brain",
    6: "classroom_creative",
    7: "classroom_support",
}
SOURCE_FILES = {
    "history": "organism_v6/orch_r124_train_history.py",
    "native": "gpu/orch_r125_continual_native.py",
    "presentation": "organism_v6/orch_r125_plain_context.py",
    "stream": "organism_v6/orch_r125_continual_stream.py",
}
INPUTS = {
    "census": (
        "research_loop/workers/rohin162_context_console_20260917/SOURCE_CENSUS_1789663949490665603.json",
        "83375f2fb0b39a5acecf244737ee4fa5ab38138676793544f3ad3a00ac7694b1",
    ),
    "console": (
        "research_loop/workers/rohin162_console_route_20260917/a100.json",
        "0015b1acaf01787d9486024a683e39cd797031e86708b3181f39e27b7c1f7e8a",
    ),
    "roster": (
        "research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json",
        "71f5e62821adb90b9d260810386362959c6215f5ac2dbba0c7f22f89c56df93a",
    ),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference_valid(reference):
    require(isinstance(reference, dict), "reference_object")
    require(isinstance(reference.get("path"), str)
            and reference["path"].startswith("/localhome/local-rohing/")
            and ".." not in Path(reference["path"]).parts, "remote_metadata_reference_path")
    require(re.fullmatch(r"[0-9a-f]{64}", reference.get("sha256", "")), "reference_sha256")


def load_inputs():
    documents = {}
    references = {}
    for name, (relative, expected) in INPUTS.items():
        path = REPOSITORY / relative
        require(not path.is_symlink() and path.resolve() == path, "canonical_local_receipt")
        require(path.stat().st_size <= MAX_RECEIPT_BYTES, "local_metadata_read_cap")
        with path.open("rb") as stream:
            data = stream.read(MAX_RECEIPT_BYTES + 1)
        require(len(data) <= MAX_RECEIPT_BYTES, "local_metadata_read_cap")
        require(hashlib.sha256(data).hexdigest() == expected, "pinned_local_receipt:" + name)
        documents[name] = json.loads(data)
        references[name] = dict(path=relative, sha256=expected, bytes=len(data))
    return documents, references


def unique_rows(rows, key):
    result = {}
    for row in rows:
        require(row[key] not in result, "duplicate_life_root")
        result[row[key]] = row
    return result


def build_proposal(documents, references):
    census = documents["census"]
    console = documents["console"]
    roster = documents["roster"]
    require(census["schema"] == "ROHIN162_READONLY_SOURCE_CENSUS_V1", "census_schema")
    require(console["node"] == "a100", "a100_console_only")
    census_nodes = [node for node in census["nodes"] if node["node"] == "a100"]
    require(len(census_nodes) == 1, "one_a100_census")
    census_rows = unique_rows(census_nodes[0]["rows"], "life_root")
    console_rows = unique_rows(console["rows"], "actual_root")
    roster_rows = unique_rows([
        row for row in roster["rows"]
        if row["node"] == "a100" and row["training"].get("training_enabled") is True
    ], "life_root")
    expected_roots = {
        f"/localhome/local-rohing/orch_r136_a100_{label}_20260916_attempt1/run1"
        for label in LANES.values()
    }
    require(set(census_rows) == set(console_rows) == set(roster_rows) == expected_roots,
            "exact_six_learning_lives_no_controls")
    lives = []
    for physical, label in LANES.items():
        root = f"/localhome/local-rohing/orch_r136_a100_{label}_20260916_attempt1/run1"
        observed = console_rows[root]
        registered = roster_rows[root]
        current = census_rows[root]
        require(registered["status"] == "LIVE" and registered["physical"] == physical
                and current["registered_identity_live"] is True, "registered_live_lane")
        require(len(registered["natives"]) == 1, "single_registered_native")
        native = registered["natives"][0]
        identity = native["identity"]
        require(native["module"] == "gpu.orch_r125_continual_guard", "original_guard_native")
        require(observed["status"] == "LIVE_NATIVE_OPEN_INBOX_AND_SOURCE_VERIFIED"
                and observed["original_pid_source_match"] is True, "console_identity_verified")
        require(all(identity[key] == observed[key] for key in ("pid", "start_ticks", "uid")),
                "cross_receipt_actor_identity")
        source = f"{SOURCE_BASE}/lane{physical}/source"
        require(current["plan"]["root"] == native["plan"]["root"] == root
                and current["plan"]["source_root"] == native["plan"]["source_root"]
                == observed["source_root"] == identity["cwd"] == source, "same_life_current_source")
        require(current["plan_ref"] == native["plan_ref"], "exact_current_plan_reference")
        require(all(current["plan"][key] == value for key, value in native["plan"].items()
                    if key in current["plan"]), "consistent_plan_metadata")
        reference_valid(native["config_ref"])
        reference_valid(current["plan_ref"])
        source_pins = {}
        for role, relative in SOURCE_FILES.items():
            reference = current["source"][role]
            reference_valid(reference)
            require(reference["path"] == source + "/" + relative, "source_path_binding")
            source_pins[relative] = reference["sha256"]
        require(source_pins[SOURCE_FILES["native"]]
                == observed["source_files"][SOURCE_FILES["native"]]["sha256"], "native_source_cross_check")
        lives.append(dict(
            physical=physical, label=label, life_root=root,
            original_actor=dict(deepcopy(identity), boot_id=observed["boot_id"]),
            original_guard=deepcopy(native["config_ref"]),
            original_plan=deepcopy(current["plan_ref"]),
            plan_metadata=dict(native["plan"], **current["plan"]),
            source_root=source, partial_source_pins=source_pins,
            interpreter=observed["python"], wrapper="gpu/a100_ssh.sh",
            console_root=observed["actual_root"],
            console_module_sha256=observed["source_files"]["gpu/orch_r127_pilot_console.py"]["sha256"],
            observed_unix=current["observed_unix"],
            console_observed_unix=observed["observed_unix"],
            proposed_successor_source=f"/localhome/local-rohing/orch_r179_context_survival_a100_20260917/lane{physical}/source",
            successor_source_staged=False, saved_boundary=None, receiving_cpu_proof=None,
            supervisor_identity=None, timer_identity=None,
        ))
    return dict(
        schema="R179_NODE1_METADATA_PREPARATION_V1", node="a100", lives=lives,
        status="PREPARED_LOCALLY_WAITING_MAIN_PATCH_AND_CPU_GO",
        execution_authorized=False, actor_pause_allowed=False, rollout_ready=False,
        remote_actions_performed=0, gpu_actions_performed=0, signals_sent=0,
        messages_sent=0, sealed_content_reads=0, old_journal_mutations=0,
        full_plan_bytes_loaded=False, full_source_closure_verified=False,
        metadata_observations_not_current_execution_admission=True,
        input_receipts=references,
        unresolved=[
            "Main exact core patch/source closure and CPU GO",
            "A100-specific operator and independently bound operator tests",
            "Fresh receiving CPU proof against actual staged source",
            "Fresh exact actor/timer/supervisor/device ownership and resource admission",
            "Per-life completed quiescent boundary and full adapter/AdamW/RNG/history proof",
            "Actual successor loaded/resumed proof; never inferred from CPU passes",
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    output = Path(arguments.output)
    require(output.parent.resolve() == HERE and not output.is_symlink(), "own_node1_output_only")
    documents, references = load_inputs()
    proposal = build_proposal(documents, references)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(proposal, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(path=str(output), status=proposal["status"], lives=len(proposal["lives"]))))


if __name__ == "__main__":
    main()
