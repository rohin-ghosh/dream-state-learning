"""Replay archived Q0 full-dose margins without importing a model or producer.

This post-terminal arithmetic replay does not bind a new experiment, classify
trajectories, repair missing readouts, or change any primary claim.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import sys
import tarfile

from gpu.q1_map_dynamics_math import reduce_arm, reduce_pair


SIDECAR = "Q1_MAP_DYNAMICS_SIDECAR_v1"
SIDECAR_SHA256 = "2cee7e3757d31903d31fea9afee45a4c716dbd360d712e6e077842fd4a91d15b"
CAMPAIGN_SHA256 = "1f29967875bb7e84fd479c25a1a54aed59405675c9bccc74305be8449d7884df"
ROOTS = {
    "R0": (18153, "52c21a6e1ba5fa786a652998eacb91b348ab1da685a335e7b90494ca1383097d"),
    "R1": (17567, "006c21d38b763953e5a59ef5641d3fe7683e3e32f71a84bb879c7de667a9db87"),
    "R2": (18153, "350befebaa2a31768b05254c98443435c58d5d8610c6f1515e89218afd2a14dc"),
}
ORIENTATION = (0, 1, 1, 0, 1, 0, 0, 1)
ARMS = ("P_AUTH", "P_DERANGED")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_bytes(content):
    return hashlib.sha256(content).hexdigest()


def load_archive(path, replica, expected_count, expected_digest):
    prefix = f"q0_fulldose_{replica}_20260913_attempt1/"
    hashes, selected = {}, {}
    with tarfile.open(path, mode="r|", bufsize=1024 * 1024) as archive:
        for member in archive:
            require(member.isdir() or member.isfile(), "non-regular archived entry")
            if member.isdir() and member.name == prefix.rstrip("/"):
                continue
            require(member.name.startswith(prefix), "unexpected root prefix")
            relative = member.name[len(prefix):]
            require(not any(character in relative for character in "\\\n\r"), "escaped hash-stream filename")
            require(".." not in PurePosixPath(relative).parts, "parent traversal")
            if member.isdir():
                continue
            require(relative and relative not in hashes, "duplicate or empty archived file")
            keep = relative in ("manifest.json", "prepared.json", "STARTED.json", "FINALIZED.json", "SEAL.json", "reduction.json")
            keep = keep or ("/events/" in relative and relative.endswith(".json")
                            and "/00_audit/" not in relative)
            chunks = []
            hasher = hashlib.sha256()
            with archive.extractfile(member) as stream:
                while content := stream.read(8 * 1024 * 1024):
                    hasher.update(content)
                    if keep:
                        chunks.append(content)
            hashes[relative] = hasher.hexdigest()
            if keep:
                selected[relative] = json.loads(b"".join(chunks))
    stream = "".join(f"{hashes[name]}  ./{name}\n" for name in sorted(hashes)).encode()
    require(len(hashes) == expected_count, "complete-root file count differs")
    require(digest_bytes(stream) == expected_digest, "external complete-root digest differs")
    for name in ("manifest.json", "prepared.json", "FINALIZED.json", "SEAL.json", "reduction.json"):
        require(name in selected, f"missing terminal source {name}")
    require(selected["FINALIZED.json"]["seal_sha256"] == hashes["SEAL.json"], "terminal seal binding")
    require(all(hashes.get(name) == value for name, value in selected["SEAL.json"]["files"].items()),
            "sealed source differs")
    return selected, hashes


def events(selected, stage, suffix):
    prefix = f"stages/{stage}/events/"
    return [(name, selected[name]) for name in sorted(selected)
            if name.startswith(prefix) and name.endswith(suffix)]


def one_event(selected, stage, suffix):
    found = events(selected, stage, suffix)
    require(len(found) == 1, f"expected one {stage}/{suffix}")
    return found[0][1]


def branch_choice_counts(auth, deranged):
    require(len(auth) == len(deranged) and len(auth) in (4, 128), "paired branch surface size")
    signs = (1, -1, -1, 1) * (len(auth) // 4)
    return {
        "strict_positive_signed_margin_both": sum(
            sign * first > 0 and -sign * second > 0
            for sign, first, second in zip(signs, auth, deranged)),
        "argmax_tie_to_mem2reg_both": sum(
            (first >= 0) == (sign == 1) and (second >= 0) == (sign == -1)
            for sign, first, second in zip(signs, auth, deranged)),
        "argmax_tie_to_gvn_both": sum(
            (first > 0) == (sign == 1) and (second > 0) == (sign == -1)
            for sign, first, second in zip(signs, auth, deranged)),
        "either_arm_zero_margin": sum(first == 0 or second == 0 for first, second in zip(auth, deranged)),
        "total": len(auth),
        "interpretation": "labeled arithmetic conventions, not a new gate or observed greedy generation",
    }


def collect_prefixes(selected, stage, row_ids, state, snapshot, prepared_sha256):
    found = {}
    for _, event in events(selected, stage, "_readout.json"):
        require(event["state"] == state and event["snapshot"] == snapshot,
                "readout state/checkpoint differs")
        require(event["material_sha256"] == prepared_sha256 and event["attempts"] == 1,
                "readout material/attempt differs")
        if event["operation"] != "prefix" or event["row_id"] not in row_ids:
            continue
        require(event["row_id"] not in found, "duplicate exact prefix")
        output = event["output"]
        require(output["d"] == output["z0"] - output["z1"], "margin primitives differ")
        require(all(type(output[key]) in (int, float) and math.isfinite(output[key])
                    for key in ("d", "z0", "z1", "q", "M")), "nonfinite prefix")
        found[event["row_id"]] = output
    require(set(found) == set(row_ids), "incomplete exact margin surface")
    return [found[row_id] for row_id in row_ids]


def reduce_root(replica, selected, hashes):
    prepared = selected["prepared.json"]
    manifest = selected["manifest.json"]
    root_number = int(replica[1])
    require(prepared["allocation"] == dict(replica=replica, identifier_seed=501 + root_number,
                                           learner_seed=1 + root_number), "fixed root allocation differs")
    require(manifest["allocation"] == prepared["allocation"], "manifest allocation differs")
    require(prepared["campaign_sha256"] == manifest["campaign_sha256"] == CAMPAIGN_SHA256,
            "campaign differs")
    require(prepared["version"] == "astra-pairwise-q0-fulldose-v2", "wrong executor version")
    rows = {row["id"]: row for row in prepared["rows"]}
    quartets = [quartet["rows"] for quartet in prepared["quartets"]]
    require(len(quartets) == 32 and all(len(quartet) == 4 for quartet in quartets), "quartet count")
    row_ids = [row_id for quartet in quartets for row_id in quartet]
    require(len(set(row_ids)) == 128, "quartet coverage")
    require(set(row_ids) == {row_id for row_id, row in rows.items() if row["panel"] == "exact"},
            "exact panel differs")
    for quartet in quartets:
        require([(ORIENTATION[rows[row_id]["slot"]], rows[row_id]["mode"]) for row_id in quartet]
                == [(0, 0), (0, 1), (1, 0), (1, 1)], "Walsh quartet order differs")
    require(prepared["training_order"] == quartets * 4, "fixed four-sweep order differs")
    off_records = collect_prefixes(selected, "01_eval_OFF_0", row_ids, "OFF", 0, hashes["prepared.json"])
    off = [record["d"] for record in off_records]
    report = {
        "allocation": prepared["allocation"], "row_ids": row_ids,
        "primary_candidate_label": selected["reduction.json"]["candidate"]["label"],
        "row_bindings": [{key: rows[row_id][key] for key in
                          ("id", "slot", "mode", "template", "decision_prefix_hash", "branch_ids", "candidate_hashes")}
                         for row_id in row_ids],
        "checkpoints": {"0": {"surface": "OFF_exact_prefix", "row_count": 128,
                               "raw_prefixes": off_records, "decomposition": reduce_pair(off, off, off)}},
        "fit_losses": {}, "missing": [],
    }
    before, after, bounds = {}, {}, {}
    for arm, stage in zip(ARMS, ("02_fit_P_AUTH", "06_fit_P_DERANGED")):
        steps = [event for _, event in events(selected, stage, "_step.json")]
        require([step["update"] for step in steps] == list(range(1, 129)), "fit update sequence differs")
        require([step["row_ids"] for step in steps] == prepared["training_order"], "fit quartet sequence differs")
        losses = [step["loss"] for step in steps]
        require(all(type(loss) in (int, float) and math.isfinite(loss) for loss in losses), "nonfinite loss")
        report["fit_losses"][arm] = dict(vector=losses, first32_mean=statistics.mean(losses[:32]),
                                         last32_mean=statistics.mean(losses[-32:]))
        before_rows = one_event(selected, stage, "_canary_before.json")["surfaces"]
        after_rows = one_event(selected, stage, "_canary_after.json")["surfaces"]
        before[arm] = [row["d_canary64"] for row in before_rows]
        after[arm] = [row["d_canary64"] for row in after_rows]
        bounds[arm] = {"before": [row["bound"] for row in before_rows],
                       "after": [row["bound"] for row in after_rows]}
    require(before["P_AUTH"] == before["P_DERANGED"], "initial canary surfaces differ")
    report["checkpoints"]["1"] = dict(
        surface="canary64_after_minus_own_preupdate_canary64_not_bf16_OFF",
        row_count=4, row_ids=quartets[0], before=before, after=after, recorded_bounds=bounds,
        decomposition=reduce_pair(before["P_AUTH"], after["P_AUTH"], after["P_DERANGED"]),
        branch_choice_counts=branch_choice_counts(after["P_AUTH"], after["P_DERANGED"]),
    )
    for update, auth_stage, deranged_stage in ((32, "03_eval_P_AUTH_32", "07_eval_P_DERANGED_32"),
                                               (64, "04_eval_P_AUTH_64", "08_eval_P_DERANGED_64"),
                                               (128, "05_eval_P_AUTH_128", "09_eval_P_DERANGED_128")):
        records, margins = {}, {}
        for arm, stage in zip(ARMS, (auth_stage, deranged_stage)):
            if replica == "R1" and arm == "P_DERANGED" and update == 128:
                require(not events(selected, stage, "_readout.json"), "unexpected primary R1 terminal readout")
                report["missing"].append(dict(arm=arm, update=update, reason="archived primary runtime abort"))
                continue
            records[arm] = collect_prefixes(selected, stage, row_ids, arm, update, hashes["prepared.json"])
            margins[arm] = [record["d"] for record in records[arm]]
        checkpoint = dict(surface="exact_prefix_minus_OFF_exact_prefix", row_count=128,
                          raw_prefixes=records, paired=len(margins) == 2)
        if checkpoint["paired"]:
            checkpoint["decomposition"] = reduce_pair(off, margins["P_AUTH"], margins["P_DERANGED"])
            checkpoint["branch_choice_counts"] = branch_choice_counts(margins["P_AUTH"], margins["P_DERANGED"])
        else:
            checkpoint["unpaired_arm_decompositions"] = {
                arm: reduce_arm(off, vector, arm) for arm, vector in margins.items()}
        report["checkpoints"][str(update)] = checkpoint
    report["coverage"] = "SIDECAR_INCOMPLETE" if report["missing"] else "REQUESTED_MARGIN_SURFACES_COMPLETE"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "output must be a new file")
    root = Path(__file__).resolve().parents[1]
    memo = root / "research_notes/analysis/2026-09-13_q0_map_closeness_and_q1_trajectory_sidecar.md"
    require(digest_bytes(memo.read_bytes()) == SIDECAR_SHA256, "sidecar memo changed")
    loaded, custody = {}, {}
    for replica, (count, expected) in ROOTS.items():
        archive = options.archive_dir / f"{replica}_attempt1.tar"
        print(f"Verifying complete archived {replica} file stream", file=sys.stderr, flush=True)
        selected, hashes = load_archive(archive, replica, count, expected)
        loaded[replica] = (selected, hashes)
        custody[replica] = dict(archive=str(archive), regular_files=count, complete_root_stream_sha256=expected,
                               consumed_json_hashes={name: hashes[name] for name in selected})
    report = dict(
        sidecar=SIDECAR, declared_memo_sha256=SIDECAR_SHA256,
        replay_kind="POST_TERMINAL_OFFLINE_ARITHMETIC_ONLY_NOT_A_NEW_PROSPECTIVE_BINDING",
        chronology={
            "local_memo_commit": "5695d65ac7543ed2dec328528712390035fe87f0",
            "local_memo_author_utc": "2026-09-13T04:56:08Z",
            "local_memo_commit_utc": "2026-09-13T05:03:15Z",
            "prelaunch_binding": "NOT_ESTABLISHED_BY_LOCAL_COMMIT; laptop 00e11cc2 unavailable",
            "archived_started_unix": {replica: loaded[replica][0]["STARTED.json"]["started"] for replica in ROOTS},
        },
        source_hashes={str(path.relative_to(root)): digest_bytes(path.read_bytes()) for path in
                       (Path(__file__).resolve(), root / "gpu/q1_map_dynamics_math.py")},
        custody=custody, roots={replica: reduce_root(replica, *loaded[replica]) for replica in ROOTS},
        trajectory_classifications="NOT_RECOMPUTED; no new numerical/shortcut rules introduced",
        optional_parameter_cosine="NOT_COMPUTED", extra_fits=0, extra_model_forwards=0,
        extra_gpu_hours=0, primary_labels_changed=False,
    )
    content = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with options.output.open("xb") as stream:
        stream.write(content)
    print(json.dumps(dict(output=str(options.output), sha256=digest_bytes(content)), sort_keys=True))


if __name__ == "__main__":
    main()
