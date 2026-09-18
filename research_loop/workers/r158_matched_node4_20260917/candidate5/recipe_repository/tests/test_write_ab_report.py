"""write_ab_report: the GPU-hour estimate from compile manifests and the
A/B/C/OFF/brief summary table with ritual metrics from synthetic probe files.

  <python> tests/test_write_ab_report.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import v3_fixtures as fx  # noqa: E402
from organism_v6 import write_ab_report as war  # noqa: E402
from organism_v6 import sleep_compile_v3 as sc3  # noqa: E402

PANEL8 = ["cbench-v1/susan", "cbench-v1/sha", "cbench-v1/dijkstra", "cbench-v1/patricia",
          "cbench-v1/jpeg-c", "cbench-v1/tiff2bw", "cbench-v1/gsm", "cbench-v1/stringsearch"]
# twelve notes with no word in common (consecutive Jaccard 0 for a "varied" child)
VARIED_NOTES = ["loops dominate", "memory bound", "branchy control", "tiny kernel", "recursive descent",
                "hash tables", "string scans", "float heavy", "bit twiddling", "matrix walks",
                "pointer chasing", "table lookups"]


def _probe(path, means, panel, first_act="-mem2reg, -sroa", vary=False, adapter=None, brief=False):
    panels = [{e: m for e in panel} for m in means]
    with open(path, "w") as f:
        json.dump(dict(adapter=adapter, panel=panel, gen_seed=4242, brief_file="b.txt" if brief else None,
                       budget_ticks=16, panels=panels, means=means, mean=sum(means) / len(means)), f)
    for k in range(len(means)):
        with open(f"{path}.rep{k}.ledger.jsonl", "w") as f:
            for i, e in enumerate(panel):
                act = f"-licm{i}" if vary else first_act
                note = VARIED_NOTES[i % len(VARIED_NOTES)] if vary \
                    else "The standard recipe works well; keep using it."
                f.write(json.dumps(dict(kind="thought", episode_id=e, tick=1,
                                        note=f"PREDICT: 0.3\nACT: {act}\nNOTE: {note}\nRECALL: best passes")) + "\n")
                f.write(json.dumps(dict(kind="act", episode_id=e, tick=1, action=act, outcome="x", score=0.3)) + "\n")


def _setup():
    root = tempfile.mkdtemp(prefix="war_")
    out = os.path.join(root, "pretest_write_ab", "R2_B_seed0")
    for d in ("corpora", "adapters", "probes"):
        os.makedirs(os.path.join(out, d))
    rows = fx.make_rows()
    rows, _n, _ids = sc3.exclude_rows(rows, sc3.default_exclusions("compiler"))
    for v in "ABC":
        d = os.path.join(out, "corpora", v)
        if v == "A":
            sc3.compile_legacy(rows, d)
        elif v == "B":
            sc3.compile_two_scale(rows, d)
        else:
            sc3.compile_tmem_qa(rows, d)
    for v, toks in (("A_v3", 900), ("B", 4000), ("C", 120)):
        ad = os.path.join(out, "adapters", v)
        os.makedirs(ad)
        with open(os.path.join(ad, "train_manifest.json"), "w") as f:
            json.dump(dict(recipe="v3_masked_packed", tokens=dict(target=toks, total=toks * 2),
                           train_tokens_seen=7500,
                           steps=10, epochs_run=1, config=dict(epochs=1, seed=0, lr=1e-4, pack=True),
                           tokens_per_s=1234.5, wall_seconds=60.0, final_loss=1.5,
                           truncation=dict(target_tokens_dropped=0, items_split=0),
                           packing=dict(mode="block4d_by_group", isolation_check=dict(verdict="isolated")),
                           lora=dict(rank=32, alpha=64, scaling=2.0), empty=False, note=f"cell {v}"), f)
        with open(os.path.join(ad, "DONE"), "w") as f:
            f.write("ok\n")
    # A = the frozen v1 trainer's cell: train_meta.json only (no train_manifest.json)
    ad = os.path.join(out, "adapters", "A")
    os.makedirs(ad)
    with open(os.path.join(ad, "train_meta.json"), "w") as f:
        json.dump(dict(recipe="v1_frozen", n_texts=355, steps=267, tokens=51191, rank=32, epochs=3, lr=1e-4,
                       final_loss=1.9), f)
    with open(os.path.join(ad, "DONE"), "w") as f:
        f.write("ok\n")
    disj = [f"npb-v0/{i}" for i in range(12)]
    pr = os.path.join(out, "probes")
    _probe(os.path.join(pr, "OFF_report.json"), [0.470, 0.474], PANEL8, vary=True)
    _probe(os.path.join(pr, "OFF_disjoint.json"), [0.255, 0.259], disj, vary=True)
    _probe(os.path.join(pr, "A_report.json"), [0.5291, 0.5291], PANEL8, adapter="/x/adapters/A")
    _probe(os.path.join(pr, "A_disjoint.json"), [0.2731, 0.2731], disj, adapter="/x/adapters/A")
    _probe(os.path.join(pr, "B_report.json"), [0.51, 0.50], PANEL8, vary=True, adapter="/x/adapters/B")
    _probe(os.path.join(pr, "B_disjoint.json"), [0.26, 0.20], disj, vary=True, adapter="/x/adapters/B")  # one collapsed rep
    _probe(os.path.join(pr, "C_report.json"), [0.48, 0.49], PANEL8, adapter="/x/adapters/C")
    _probe(os.path.join(pr, "A_v3_report.json"), [0.50, 0.51], PANEL8, adapter="/x/adapters/A_v3")
    # no C_disjoint: a missing cell must not break the table
    # the mid-life brief cell probed by write_ab.sh (frozen + sleep_0512/waking_brief.txt)
    _probe(os.path.join(pr, "brief_mid_report.json"), [0.52, 0.53], PANEL8, brief=True)
    _probe(os.path.join(pr, "brief_mid_disjoint.json"), [0.27, 0.28], disj, brief=True)
    brief_dir = os.path.join(root, "brief_baseline")
    os.makedirs(brief_dir)
    _probe(os.path.join(brief_dir, "R2_B_seed0_brief_report.json"), [0.5291, 0.5291], PANEL8, brief=True)
    _probe(os.path.join(brief_dir, "R2_B_seed0_brief_disjoint.json"), [0.2731, 0.2731], disj, brief=True)
    with open(os.path.join(out, "timings.jsonl"), "w") as f:
        for step, sec in (("compile", 30), ("train_A", 600), ("train_B", 3600), ("probe_A_report", 720)):
            f.write(json.dumps(dict(step=step, seconds=sec, rc=0)) + "\n")
    return root, out, brief_dir


def test_estimate_from_compile_manifests():
    _root, out, _b = _setup()
    est = war.estimate(os.path.join(out, "corpora"), epochs=3, reps=2)
    assert set(est["cells"]) == {"A", "B", "C"}
    for c, d in est["cells"].items():
        m = json.load(open(os.path.join(out, "corpora", c, "compile_manifest.json")))
        assert d["est_tokens_total"] == m["est_tokens_total"]
        assert abs(d["train_hours"] - round(m["est_tokens_total"] * 3 / 1200 / 3600, 2)) < 1e-9
    assert est["cells"]["B"]["train_hours"] > est["cells"]["C"]["train_hours"]
    assert est["probe_hours"] > 0 and est["total_gpu_hours"] == round(est["train_hours"] + est["probe_hours"], 2)
    with open(os.path.join(out, "estimate.json"), "w") as f:
        json.dump(est, f)
    # the CLI entry point
    war.main(["estimate", "--corpora", os.path.join(out, "corpora"), "--epochs", "2", "--cells", "A,B"])


def test_summarize_builds_the_table_with_deltas_ritual_and_brief():
    root, out, brief_dir = _setup()
    est = war.estimate(os.path.join(out, "corpora"), epochs=3)
    with open(os.path.join(out, "estimate.json"), "w") as f:
        json.dump(est, f)
    s = war.summarize(out, os.path.join(root, "v6_out", "R2_B_seed0"), brief_dir, ["A", "A_v3", "B", "C", "C_tmem"])
    assert os.path.exists(os.path.join(out, "summary.json")) and os.path.exists(os.path.join(out, "table.md"))
    cells = s["cells"]
    assert set(cells) == {"A", "A_v3", "B", "C", "C_tmem", "OFF", "brief", "brief_mid"}
    off_r = cells["OFF"]["report"]["mean"]
    assert abs(cells["A"]["report"]["delta_vs_off"] - (0.5291 - off_r)) < 1e-9
    assert abs(cells["brief"]["disjoint"]["delta_vs_off"] - (0.2731 - 0.257)) < 1e-9
    assert abs(cells["brief_mid"]["disjoint"]["delta_vs_off"] - (0.275 - 0.257)) < 1e-9
    assert cells["brief_mid"]["report"]["brief_file"] and "sleep_<horizon>" in cells["brief_mid"]["source"]
    assert "FINAL" in cells["brief"]["source"]
    assert cells["B"]["disjoint"]["collapsed_reps"] == [0.20], "a rep below paired OFF - 0.04 is flagged"
    assert cells["B"]["disjoint"]["collapsed_rep_indices"] == [1]
    assert cells["B"]["disjoint"]["collapse_pairing_status"] == "paired_by_rep_index"
    assert cells["A"]["report"]["collapsed_reps"] == []
    # ritual metrics from the existing code: the recipe cell locks, the varied OFF does not
    assert cells["A"]["report"]["ritual"]["recipe_share"] == 1.0
    assert cells["OFF"]["report"]["ritual"]["recipe_share"] < 0.5
    assert cells["A"]["report"]["ritual"]["note_jaccard"] == 1.0 and cells["OFF"]["report"]["ritual"]["note_jaccard"] < 0.5
    assert cells["A"]["report"]["ritual"]["recall_modal"] == 1.0
    assert cells["A"]["report"]["ritual"]["per_rep"][0]["n_episodes"] == 8
    # missing cells are marked, not fatal
    assert cells["C"]["disjoint"]["missing"] and cells["C_tmem"]["report"]["missing"]
    assert cells["C_tmem"]["train"] is None and cells["C_tmem"]["compile"]["recipe"] == sc3.RECIPES["C"]
    assert cells["A_v3"]["compile"]["recipe"] == sc3.RECIPES["A"], "a derived cell falls back to its base corpus"
    assert cells["B"]["train"]["target_tokens"] == 4000 and cells["B"]["train"]["isolation"] == "isolated"
    assert cells["B"]["train"]["steps"] == 10 and cells["B"]["train"]["epochs_run"] == 1
    assert cells["B"]["train"]["token_passes"] == 7500 and cells["B"]["train"]["note"] == "cell B"
    assert not cells["B"]["train"]["token_passes_estimated"]
    assert cells["B"]["compile"]["view_share"] and cells["B"]["compile"]["by_category"]
    assert cells["B"]["compile"]["token_measure"] and cells["B"]["compile"]["exposures"]["rows_as_target_twice"] > 0
    # the v1-trained A: train_meta.json + the step's wall clock stand in for the v3 manifest
    ta = cells["A"]["train"]
    assert ta["trainer"] == "v1_frozen" and ta["steps"] == 267
    assert ta["target_tokens"] is None and ta["total_tokens"] is None
    assert ta["wall_s"] == 600 and ta["epochs_run"] == 3 and ta["token_passes"] == 51191
    assert ta["tokens_per_s"] == round(51191 / 600, 1) and ta["packing"].startswith("v1")
    assert abs(s["measured_gpu_hours"] - (30 + 600 + 3600 + 720) / 3600) < 1e-6
    assert s["estimate"]["total_gpu_hours"] == est["total_gpu_hours"]
    md = open(os.path.join(out, "table.md")).read()
    for c in ("| A |", "| A_v3 |", "| B |", "| C |", "| OFF |", "| brief |", "| brief_mid |"):
        assert c in md, c
    assert "0.5291" in md and "budget" in md.lower() and "B_match" in md
    for col in ("| steps |", "| token-passes |", "| total tokens |", "| epochs |", "| flags |"):
        assert col in md, col
    assert "267" in md and "51191" in md
    war.main(["summarize", "--out-dir", out, "--life", os.path.join(root, "v6_out", "R2_B_seed0"),
              "--brief-dir", brief_dir])


def test_collapse_uses_paired_off_rep_not_off_mean():
    root = tempfile.mkdtemp(prefix="war_pair_")
    off_path = os.path.join(root, "off.json")
    cell_path = os.path.join(root, "cell.json")
    _probe(off_path, [0.10, 0.50], PANEL8, vary=True)
    _probe(cell_path, [0.20, 0.47], PANEL8, vary=True)
    off = war.probe_cell(off_path)
    cell = war.probe_cell(cell_path, off)
    # Comparing 0.20 to OFF's 0.30 mean would falsely call it collapsed.
    # Same-index comparisons are 0.20 vs 0.10 and 0.47 vs 0.50: neither
    # crosses the 0.04 adverse threshold.
    assert cell["collapsed_reps"] == []
    assert cell["collapsed_rep_indices"] == []
    assert cell["collapse_pairing_status"] == "paired_by_rep_index"


def test_collapse_is_unavailable_when_pairing_contract_differs():
    root = tempfile.mkdtemp(prefix="war_unpaired_")
    off_path = os.path.join(root, "off.json")
    cell_path = os.path.join(root, "cell.json")
    _probe(off_path, [0.50, 0.50], PANEL8, vary=True)
    _probe(cell_path, [0.10], PANEL8, vary=True)
    off = war.probe_cell(off_path)
    cell = war.probe_cell(cell_path, off)
    assert cell["collapsed_reps"] == []
    assert cell["collapse_pairing_status"] == "unavailable:rep_count_mismatch_or_empty"

    # Equal-length results still fail closed when seed or panel differs.
    _probe(cell_path, [0.10, 0.10], PANEL8, vary=True)
    cell_json = json.load(open(cell_path))
    cell_json["gen_seed"] = 999
    with open(cell_path, "w") as f:
        json.dump(cell_json, f)
    cell = war.probe_cell(cell_path, off)
    assert cell["collapse_pairing_status"] == "unavailable:gen_seed_mismatch"

    cell_json["gen_seed"] = 4242
    cell_json["panel"] = list(reversed(PANEL8))
    with open(cell_path, "w") as f:
        json.dump(cell_json, f)
    cell = war.probe_cell(cell_path, off)
    assert cell["collapse_pairing_status"] == "unavailable:panel_mismatch"

    # Matching absent metadata is not evidence of pairing.
    off_json = json.load(open(off_path))
    cell_json = json.load(open(cell_path))
    for obj in (off_json, cell_json):
        obj.pop("gen_seed", None)
        obj.pop("panel", None)
    with open(off_path, "w") as f:
        json.dump(off_json, f)
    with open(cell_path, "w") as f:
        json.dump(cell_json, f)
    off_missing = war.probe_cell(off_path)
    cell_missing = war.probe_cell(cell_path, off_missing)
    assert cell_missing["collapsed_reps"] == []
    assert cell_missing["collapse_pairing_status"] == \
        "unavailable:missing_gen_seed,missing_panel"


def test_old_v3_manifest_token_passes_fallback_is_visible():
    root, out, brief_dir = _setup()
    path = os.path.join(out, "adapters", "A_v3", "train_manifest.json")
    manifest = json.load(open(path))
    manifest.pop("train_tokens_seen")
    with open(path, "w") as f:
        json.dump(manifest, f)
    row = war.train_row(out, "A_v3", [])
    assert row["token_passes"] == 1800
    assert row["token_passes_estimated"]
    war.summarize(out, os.path.join(root, "v6_out", "R2_B_seed0"), brief_dir,
                  ["A_v3"])
    rendered = open(os.path.join(out, "table.md")).read()
    assert "token_passes_estimated" in rendered


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
