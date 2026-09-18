"""Pretest P1 (write A/B/C) — the CPU side of gpu/write_ab.sh.

  python -m organism_v6.write_ab_report estimate  --corpora <OUT>/corpora --epochs 3
  python -m organism_v6.write_ab_report summarize --out-dir <OUT> --life <life_dir> \
      [--brief-dir ~/v6_out/brief_baseline] [--cells A,B,C,C_tmem]

estimate: GPU-hours from the compile manifests' token estimates (chars/4)
at an ASSUMED 1,200 training tokens/s on one A40 (PRETESTS_2026-09-11
yardstick; the trainer's manifest records the measured tokens/s) plus the
probe cost (8-panel ~6 min/rep, disjoint panel ~8 min/rep, engine load ~4 min).

summarize: reads <OUT>/probes/<cell>_{report,disjoint}.json (probe_adapter
output), the OFF cell, the life's FINAL-brief cells from brief_baseline.sh
(referenced, not re-run), the mid-life brief cell write_ab.sh probes
(brief_mid: frozen + sleep_<horizon>/waking_brief.txt), the train manifests
(train_manifest.json from the v3 trainer, or train_meta.json + the step's
wall clock for the frozen v1 trainer's cells) and compile manifests (derived
cells such as A_v3 / C_tmem fall back to their base corpus), timings.jsonl,
and computes the ritual metrics on every probe ledger with the EXISTING code
(parent_brief.ritual_metrics: modal first-action share = "recipe share",
first-note consecutive Jaccard, recall modal share, predict SD). The table
reports encoded target/total tokens when the manifest supports them, plus
epochs, steps and realized token-passes per cell (the budget confound in the
open), and flags (target tokens dropped by
the trainer, head_missing items, chars/3 token estimates, packing fallback).
Writes <OUT>/summary.json and <OUT>/table.md.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import statistics

from .parent_brief import ritual_metrics

TOK_PER_S = 1200.0
PROBE_MIN = dict(report=6.0, disjoint=8.0)
ENGINE_LOAD_MIN = 4.0
COLLAPSE_BELOW_OFF = 0.04


def _load(p):
    return json.load(open(p)) if p and os.path.exists(p) else None


def estimate(corpora_dir: str, epochs: int, reps: int = 2, tok_per_s: float = TOK_PER_S,
             cells=None, extra_probe_cells: int = 1) -> dict:
    out = dict(assumed_tokens_per_s=tok_per_s, epochs=epochs, reps=reps, cells={},
               note="training tokens = context + target (the forward pass reads both); exact when the "
                    "compile ran with a tokenizer (token_measure per cell), else chars/3 estimates; "
                    "hours = tokens x epochs / assumed tok/s (the trainer reports the measured tok/s)")
    total_train = 0.0
    n_cells = 0
    for d in sorted(glob.glob(os.path.join(corpora_dir, "*"))):
        cell = os.path.basename(d)
        if cells and cell not in cells:
            continue
        m = _load(os.path.join(d, "compile_manifest.json"))
        if not m:
            continue
        toks = int(m.get("est_tokens_total") or 0)
        hours = toks * epochs / tok_per_s / 3600.0
        out["cells"][cell] = dict(est_tokens_total=toks, est_target_tokens=m.get("est_target_tokens"),
                                  token_measure=m.get("token_measure"),
                                  n_items=m.get("n_items"), train_hours=round(hours, 2),
                                  empty=m.get("empty", False))
        total_train += hours
        n_cells += 1
    probe_h = (n_cells + extra_probe_cells) * (reps * (PROBE_MIN["report"] + PROBE_MIN["disjoint"])
                                               + 2 * ENGINE_LOAD_MIN) / 60.0
    out.update(train_hours=round(total_train, 2), probe_hours=round(probe_h, 2),
               total_gpu_hours=round(total_train + probe_h, 2))
    return out


def probe_cell(path: str, off_reference=None, n_panel: int = 8) -> dict:
    """One probe_adapter output + its rep ledgers -> means, reps, collapsed
    reps, ritual metrics per rep."""
    pj = _load(path)
    if not pj:
        return dict(missing=True, file=os.path.basename(path))
    reps = pj.get("means") or []
    rit = []
    for k in range(len(pj.get("panels") or [])):
        lp = f"{path}.rep{k}.ledger.jsonl"
        if os.path.exists(lp):
            rows = [json.loads(l) for l in open(lp) if l.strip()]
            m = ritual_metrics(rows, max(4, n_panel))
            rit.append(dict(rep=k, recipe_share=m.get("modal_first_act_share"),
                            note_jaccard=m.get("note_consecutive_jaccard"),
                            recall_modal=m.get("recall_modal_share"), predict_sd=m.get("predict_sd"),
                            flags=m.get("flags"), n_episodes=m.get("n_episodes")))

    def _mean(key):
        v = [r[key] for r in rit if isinstance(r.get(key), (int, float))]
        return round(statistics.mean(v), 3) if v else None
    panel_ids = pj.get("panel") or []
    collapsed = []
    collapsed_indices = []
    pairing_status = "not_requested"
    if off_reference is not None:
        off_reps = off_reference.get("reps") or []
        seed_present = (pj.get("gen_seed") is not None and
                        off_reference.get("gen_seed") is not None)
        off_panel_ids = off_reference.get("panel_ids") or []
        panel_present = bool(panel_ids) and bool(off_panel_ids)
        same_seed = seed_present and pj.get("gen_seed") == off_reference.get("gen_seed")
        same_panel = panel_present and panel_ids == off_panel_ids
        same_n = len(reps) == len(off_reps) and bool(reps)
        if same_seed and same_panel and same_n:
            pairing_status = "paired_by_rep_index"
            for k, (value, off_value) in enumerate(zip(reps, off_reps)):
                if value < off_value - COLLAPSE_BELOW_OFF:
                    collapsed.append(value)
                    collapsed_indices.append(k)
        else:
            reasons = []
            if not seed_present:
                reasons.append("missing_gen_seed")
            elif not same_seed:
                reasons.append("gen_seed_mismatch")
            if not panel_present:
                reasons.append("missing_panel")
            elif not same_panel:
                reasons.append("panel_mismatch")
            if not same_n:
                reasons.append("rep_count_mismatch_or_empty")
            pairing_status = "unavailable:" + ",".join(reasons)
    return dict(file=os.path.basename(path), mean=pj.get("mean"), reps=reps,
                panel_n=len(pj.get("panel") or []), gen_seed=pj.get("gen_seed"),
                panel_ids=panel_ids,
                adapter=os.path.basename(str(pj.get("adapter"))) if pj.get("adapter") else None,
                brief_file=bool(pj.get("brief_file")),
                collapsed_reps=collapsed, collapsed_rep_indices=collapsed_indices,
                collapse_pairing_status=pairing_status,
                ritual=dict(recipe_share=_mean("recipe_share"), note_jaccard=_mean("note_jaccard"),
                            recall_modal=_mean("recall_modal"), predict_sd=_mean("predict_sd"),
                            per_rep=rit))


def _compile_manifest_for(out_dir: str, cell: str):
    """corpora/<cell> first; derived cells fall back to their base corpus
    (A_v3 -> A, C_tmem -> C); B_match / Bs have their own corpora."""
    for name in (cell, cell.split("_")[0]):
        m = _load(os.path.join(out_dir, "corpora", name, "compile_manifest.json"))
        if m:
            return m
    return None


def train_row(out_dir: str, cell: str, timings: list) -> dict:
    """train_manifest.json (v3 trainer) or, for the frozen v1 trainer's
    cells, train_meta.json + the step's wall clock from timings.jsonl."""
    ad = os.path.join(out_dir, "adapters", cell)
    tm = _load(os.path.join(ad, "train_manifest.json"))
    if tm:
        tr = (tm.get("truncation") or {})
        tokens = tm.get("tokens") or {}
        train_tokens_seen = tm.get("train_tokens_seen")
        token_passes_estimated = train_tokens_seen is None
        if train_tokens_seen is None:
            train_tokens_seen = (tokens.get("total") or 0) * (tm.get("epochs_run") or 0) or None
        return dict(trainer=tm.get("recipe"), target_tokens=tokens.get("target"),
                    total_tokens=(tm.get("tokens") or {}).get("total"),
                    epochs=(tm.get("config") or {}).get("epochs"), epochs_run=tm.get("epochs_run"),
                    token_passes=train_tokens_seen,
                    token_passes_estimated=token_passes_estimated,
                    steps=tm.get("steps"), tokens_per_s=tm.get("tokens_per_s"),
                    wall_s=tm.get("wall_seconds"), final_loss=tm.get("final_loss"),
                    packing=(tm.get("packing") or {}).get("mode"),
                    isolation=((tm.get("packing") or {}).get("isolation_check") or {}).get("verdict"),
                    lora=tm.get("lora"), empty=tm.get("empty"), svd_init=bool(tm.get("svd_init")),
                    target_tokens_dropped=tr.get("target_tokens_dropped"),
                    items_split=tr.get("items_split"), note=tm.get("note"),
                    seed=(tm.get("config") or {}).get("seed"), lr=(tm.get("config") or {}).get("lr"))
    meta = _load(os.path.join(ad, "train_meta.json"))
    if meta:
        wall = next((float(t.get("seconds", 0)) for t in timings if t.get("step") == f"train_{cell}"), None)
        toks = meta.get("tokens")
        return dict(trainer=meta.get("recipe"), target_tokens=None, total_tokens=None,
                    epochs=meta.get("epochs"), epochs_run=meta.get("epochs"),
                    # v1 increments `tokens` inside the epoch loop, so it is
                    # already the realized all-epoch count.
                    token_passes=toks, token_passes_estimated=False,
                    steps=meta.get("steps"), tokens_per_s=(round(toks / wall, 1)
                                                            if toks and wall else None),
                    wall_s=wall, final_loss=meta.get("final_loss"), packing="v1 (bsz 4, max_len 512, no mask)",
                    isolation=None, lora=dict(rank=meta.get("rank"), alpha=2 * meta.get("rank", 0)),
                    empty=False, svd_init=False, target_tokens_dropped=None, items_split=None,
                    note="frozen v1 trainer: whole-text loss, no seed; train_meta.tokens is only the "
                         "realized all-epoch count, so per-pass target/total tokens are unavailable",
                    seed=meta.get("seed"), lr=meta.get("lr"))
    return None


def summarize(out_dir: str, life: str, brief_dir=None, cells=None) -> dict:
    cells = cells or ["A", "B", "C", "C_tmem"]
    L = os.path.basename(os.path.normpath(life)) if life else None
    probes = os.path.join(out_dir, "probes")
    timings = []
    tp = os.path.join(out_dir, "timings.jsonl")
    if os.path.exists(tp):
        timings = [json.loads(l) for l in open(tp) if l.strip()]
    off = {p: probe_cell(os.path.join(probes, f"OFF_{p}.json"), None, 8 if p == "report" else 12)
           for p in ("report", "disjoint")}
    table = {}
    for c in cells + ["OFF"]:
        row = {}
        for p in ("report", "disjoint"):
            pc = off[p] if c == "OFF" else probe_cell(os.path.join(probes, f"{c}_{p}.json"),
                                                       off[p], 8 if p == "report" else 12)
            if pc.get("mean") is not None and off[p].get("mean") is not None and c != "OFF":
                pc["delta_vs_off"] = round(pc["mean"] - off[p]["mean"], 4)
            row[p] = pc
        row["train"] = train_row(out_dir, c, timings) if c != "OFF" else None
        cm = _compile_manifest_for(out_dir, c) if c != "OFF" else None
        row["compile"] = dict(recipe=cm.get("recipe"), n_items=cm.get("n_items"),
                              est_target_tokens=cm.get("est_target_tokens"),
                              est_tokens_total=cm.get("est_tokens_total"),
                              token_measure=cm.get("token_measure"),
                              max_item_tokens=cm.get("max_item_tokens"),
                              view_share=cm.get("view_share"), views=(cm.get("params") or {}).get("views"),
                              token_budget=(cm.get("params") or {}).get("token_budget"),
                              by_category=cm.get("target_tokens_by_category"),
                              harness_echo=(cm.get("target_tokens_harness_echo") or {}).get("total"),
                              conditioning=cm.get("conditioning"),
                              exposures=cm.get("effective_exposures"),
                              truncation=cm.get("truncation")) if cm else None
        table[c] = row
    # the text-memory cells: frozen model + this life's brief. 'brief' = the
    # life's FINAL waking brief (gpu/brief_baseline.sh output, referenced);
    # 'brief_mid' = the brief written at the corpus horizon (sleep_<N>), the
    # horizon-matched comparator P1 rule (vi) names, probed by write_ab.sh.
    brief = {}
    if brief_dir and L:
        for p in ("report", "disjoint"):
            bp = os.path.join(os.path.expanduser(brief_dir), f"{L}_brief_{p}.json")
            brief[p] = probe_cell(bp, off[p], 8 if p == "report" else 12)
            if brief[p].get("mean") is not None and off[p].get("mean") is not None:
                brief[p]["delta_vs_off"] = round(brief[p]["mean"] - off[p]["mean"], 4)
    table["brief"] = dict(report=brief.get("report", dict(missing=True)),
                          disjoint=brief.get("disjoint", dict(missing=True)),
                          train=None, compile=None,
                          source="gpu/brief_baseline.sh (frozen model + the life's FINAL waking brief; "
                                 "horizon mismatch against the adapters)")
    mid = {}
    for p in ("report", "disjoint"):
        mid[p] = probe_cell(os.path.join(probes, f"brief_mid_{p}.json"), off[p],
                            8 if p == "report" else 12)
        if mid[p].get("mean") is not None and off[p].get("mean") is not None:
            mid[p]["delta_vs_off"] = round(mid[p]["mean"] - off[p]["mean"], 4)
    table["brief_mid"] = dict(report=mid["report"], disjoint=mid["disjoint"], train=None, compile=None,
                              source="write_ab.sh (frozen model + sleep_<horizon>/waking_brief.txt; "
                                     "the mid-life text-memory cell of P1)")
    gpu_h = round(sum(float(t.get("seconds", 0)) for t in timings) / 3600.0, 3)
    est = _load(os.path.join(out_dir, "estimate.json"))
    summary = dict(life=L, out_dir=os.path.basename(os.path.normpath(out_dir)), cells=table,
                   timings=timings, measured_gpu_hours=gpu_h, estimate=est,
                   budget_note="supervised-token budgets differ by construction (A is success-"
                               "filtered; B is every child chunk in two views; Bs is scale 1 alone; "
                               "C is one pair per note/executed move/reflection). B_match is B "
                               "subsampled to A's target-token budget (newest rows in full, the rest "
                               "uniform; mechanism 2.3) so the write is compared at matched supervised "
                               "compile-time pre-EOS target tokens; realized loss positions, content, "
                               "steps, and exposure distribution may still differ. Steps and actual "
                               "train token-passes are in the table because packing makes "
                               "optimizer steps incommensurable across cells (A's short exemplars pack "
                               "into a handful of sequences).")
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, default=str)
    with open(os.path.join(out_dir, "table.md"), "w") as f:
        f.write(to_markdown(summary))
    return summary


def _fmt(x, nd=4):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def to_markdown(s: dict) -> str:
    lines = [f"# Write A/B/C pretest — {s.get('life')}",
             f"measured GPU-hours (timings.jsonl): {s.get('measured_gpu_hours')}; "
             f"estimate: {json.dumps((s.get('estimate') or {}).get('total_gpu_hours'))} h", "",
             "| cell | 8-panel mean | reps | Δ vs OFF | disjoint mean | reps | Δ vs OFF | collapsed reps | "
             "recipe share (8p / disj) | note Jaccard (8p / disj) | recall modal (8p / disj) | "
             "target tokens | total tokens | epochs | steps | token-passes | tok/s | train s | packing | flags |",
             "|---|---:|---|---:|---:|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for c, row in s["cells"].items():
        r, d = row.get("report", {}), row.get("disjoint", {})
        tr = row.get("train") or {}
        rr, dr = (r.get("ritual") or {}), (d.get("ritual") or {})
        coll = len(r.get("collapsed_reps") or []) + len(d.get("collapsed_reps") or [])
        flags = []
        if tr.get("target_tokens_dropped"):
            flags.append(f"TARGET_TOKENS_DROPPED={tr['target_tokens_dropped']}")
        if tr.get("items_split"):
            flags.append(f"items_split={tr['items_split']}")
        if tr.get("token_passes_estimated"):
            flags.append("token_passes_estimated")
        if tr.get("isolation") not in (None, "isolated"):
            flags.append(f"isolation={tr.get('isolation')}")
        for panel_name, panel in (("report", r), ("disjoint", d)):
            pairing = panel.get("collapse_pairing_status")
            if pairing and pairing.startswith("unavailable:"):
                flags.append(f"collapse_{panel_name}={pairing}")
        cm = row.get("compile") or {}
        if (cm.get("conditioning") or {}).get("items_head_missing"):
            flags.append(f"head_missing={cm['conditioning']['items_head_missing']}")
        if cm.get("token_measure") and "estimate" in str(cm.get("token_measure")):
            flags.append("token_estimate")
        lines.append("| " + " | ".join([
            c, _fmt(r.get("mean")), _fmt([round(x, 4) for x in (r.get("reps") or [])], 0) if r.get("reps") else "",
            _fmt(r.get("delta_vs_off")), _fmt(d.get("mean")),
            _fmt([round(x, 4) for x in (d.get("reps") or [])], 0) if d.get("reps") else "",
            _fmt(d.get("delta_vs_off")), str(coll) if (r.get("reps") or d.get("reps")) else "",
            f"{_fmt(rr.get('recipe_share'), 3)} / {_fmt(dr.get('recipe_share'), 3)}",
            f"{_fmt(rr.get('note_jaccard'), 3)} / {_fmt(dr.get('note_jaccard'), 3)}",
            f"{_fmt(rr.get('recall_modal'), 3)} / {_fmt(dr.get('recall_modal'), 3)}",
            _fmt(tr.get("target_tokens")), _fmt(tr.get("total_tokens")), _fmt(tr.get("epochs_run")),
            _fmt(tr.get("steps")), _fmt(tr.get("token_passes")),
            _fmt(tr.get("tokens_per_s")), _fmt(tr.get("wall_s")),
            _fmt(tr.get("packing")), " ".join(flags)]) + " |")
    lines += ["", s.get("budget_note", ""), "",
              "Δ noise: SD of a 2-rep mean ≈ 0.0046 on the compiler panels (replicate SD 0.0065); "
              "two noise widths ≈ 0.013 (PRETESTS P1). 'collapsed reps' = a rep below its "
              "same-index OFF replicate − 0.04; the flag is unavailable unless generation seed, "
              "panel and replicate count match. "
              "token_passes_estimated = an old v3 manifest lacked train_tokens_seen, so token-passes "
              "were estimated as encoded total tokens × completed epochs. "
              "flags: TARGET_TOKENS_DROPPED = the trainer cut target tokens (the compile-time 'each "
              "target once' guarantee was voided; the split backstop keeps this at 0); head_missing = "
              "items whose GOAL/METRIC head was not in a stored prompt; token_estimate = the compile "
              "sized windows by chars/3, not the tokenizer.", ""]
    for c, row in s["cells"].items():
        cm = row.get("compile")
        if cm:
            lines.append(f"- {c}: {cm.get('recipe')} items={cm.get('n_items')} est_target_tokens="
                         f"{cm.get('est_target_tokens')} ({cm.get('token_measure')}) views={cm.get('views')} "
                         f"view_share={cm.get('view_share')} token_budget={cm.get('token_budget')} "
                         f"max_item_tokens={cm.get('max_item_tokens')} by_category={cm.get('by_category')} "
                         f"harness_echo_target_tokens={cm.get('harness_echo')} "
                         f"exposures={cm.get('exposures')} conditioning={cm.get('conditioning')} "
                         f"truncation={cm.get('truncation')}")
        tr = row.get("train")
        if tr:
            lines.append(f"  train: {tr.get('trainer')} lora={tr.get('lora')} lr={tr.get('lr')} seed={tr.get('seed')} "
                         f"isolation={tr.get('isolation')} svd_init={tr.get('svd_init')} "
                         f"final_loss={tr.get('final_loss')} note={tr.get('note')}")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate")
    e.add_argument("--corpora", required=True)
    e.add_argument("--epochs", type=int, default=3)
    e.add_argument("--reps", type=int, default=2)
    e.add_argument("--tok-per-s", type=float, default=TOK_PER_S)
    e.add_argument("--cells", default=None)
    e.add_argument("--out", default=None)
    s = sub.add_parser("summarize")
    s.add_argument("--out-dir", required=True)
    s.add_argument("--life", default=None)
    s.add_argument("--brief-dir", default=None)
    s.add_argument("--cells", default="A,A_v3,B,Bs,B_match,C,C_tmem")
    args = ap.parse_args(argv)
    if args.cmd == "estimate":
        r = estimate(os.path.expanduser(args.corpora), args.epochs, args.reps, args.tok_per_s,
                     cells=[x for x in args.cells.split(",") if x] if args.cells else None)
        print(json.dumps(r, indent=1))
        if args.out:
            with open(os.path.expanduser(args.out), "w") as f:
                json.dump(r, f, indent=1)
    else:
        r = summarize(os.path.expanduser(args.out_dir), os.path.expanduser(args.life) if args.life else None,
                      args.brief_dir, [x for x in args.cells.split(",") if x])
        print(open(os.path.join(os.path.expanduser(args.out_dir), "table.md")).read())
        print("WRITE_AB_SUMMARY_DONE")


if __name__ == "__main__":
    main()
