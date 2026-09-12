#!/usr/bin/env python3
"""Independent stdlib reduction for the bounded preservation pair.

This intentionally does not import organism_v6.memory_dose. It recomputes the
registered frame metrics from serialized cue probabilities and audits the
optimizer trace. It executes no model or tokenizer.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random


DOSES = (0, 1, 4, 16)
N_STEPS = 9693
N_ANCHORS = 48
PARAPHRASES = ("p1", "p2", "p3")
COLOURS = ("red", "blue", "green", "white")


def load(path: Path):
    return json.loads(path.read_text())


def one(root: Path, pattern: str) -> Path:
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f"expected one {pattern} under {root}, got {paths}")
    return paths[0]


def mean(values):
    values = list(values)
    return sum(values) / len(values)


def normalized(row: dict, side: str, answer: str) -> float:
    raw = row[side]["p_raw"]
    total = sum(raw.values())
    return raw[answer] / total if total else 1.0 / len(raw)


def delta_p(row: dict, answer: str) -> float:
    return normalized(row, "ON", answer) - normalized(row, "OFF", answer)


def delta_logodds(row: dict, a: str, b: str) -> float:
    log = lambda value: math.log(max(value, 1e-12))
    return ((log(row["ON"]["p_raw"][a]) - log(row["ON"]["p_raw"][b]))
            - (log(row["OFF"]["p_raw"][a]) - log(row["OFF"]["p_raw"][b])))


def bootstrap(values, n_boot=2000, seed=0):
    rng = random.Random(seed)
    n = len(values)
    draws = sorted(mean(values[rng.randrange(n)] for _ in range(n))
                   for _ in range(n_boot))
    return dict(mean=mean(values), lo=draws[int(.025 * n_boot)],
                hi=draws[min(n_boot - 1, int(.975 * n_boot))], n=n)


def cue_metrics(root: Path):
    evaluation_path = one(root, "eval/*__lam1.json")
    evaluation = load(evaluation_path)
    if evaluation.get("n_cues") != 1313 or len(evaluation.get("cues", [])) != 1313:
        raise ValueError("incomplete 1,313-cue evaluation")
    if not evaluation.get("template_check") or not evaluation.get("abstain_check", {}).get("ok"):
        raise ValueError("template/abstention evaluation check failed")
    rows = evaluation["cues"]
    # The frozen native reducer selects the first row for a repeated
    # (kind, owner, form) surface key. Preserve that published convention;
    # completion-frame cue keys are unique.
    index = {}
    for row in rows:
        index.setdefault((row["kind"], row.get("owner"), row.get("form")), row)
    owners = load(root / "banks/bank0.json")["owners"]
    if len(owners) != 64 or sorted({owner["dose"] for owner in owners}) != list(DOSES):
        raise ValueError("unexpected bank owner/dose structure")

    frame = {}
    for owner in owners:
        oid, dose = owner["id"], owner["dose"]
        own = index[("frame", oid, "frame")]
        a = own["a"]
        b = max((candidate for candidate in own["OFF"]["p_raw"] if candidate != a),
                key=lambda candidate: own["OFF"]["p_raw"][candidate])
        item = dict(
            dose=dose,
            a=a,
            b=b,
            p_off=normalized(own, "OFF", a),
            p_on=normalized(own, "ON", a),
            d_p=delta_p(own, a),
            mass_off=own["OFF"]["mass"],
            mass_on=own["ON"]["mass"],
            abstain_off=own["OFF"]["p_abstain"],
            abstain_on=own["ON"]["p_abstain"],
            term1=delta_logodds(own, a, b),
        )
        if dose > 0:
            similar = index[("frame_similar", oid, "frame_similar")]
            bicycle = index[("frame_bicycle", oid, "frame_bicycle")]
            item.update(
                term2=delta_logodds(similar, a, b),
                I_d=delta_logodds(own, a, b) - delta_logodds(similar, a, b),
                similar_abs_d_p=abs(delta_p(similar, a)),
                bicycle_abs_d_p=abs(delta_p(bicycle, bicycle["a"])),
                abstain_similar_on=similar["ON"]["p_abstain"],
                abstain_bicycle_on=bicycle["ON"]["p_abstain"],
            )
        frame[oid] = item

    by_dose = {dose: [item for item in frame.values() if item["dose"] == dose]
               for dose in DOSES}
    if any(len(items) != 16 for items in by_dose.values()):
        raise ValueError("expected 16 owners at each dose")
    exposed = [item for item in frame.values() if item["dose"] > 0]
    i_values = [item["I_d"] for item in by_dose[16]]
    spill_parts = dict(
        similar=mean(item["similar_abs_d_p"] for item in exposed),
        unexposed=mean(abs(item["d_p"]) for item in by_dose[0]),
        bicycle=mean(item["bicycle_abs_d_p"] for item in exposed),
    )
    spill = mean(spill_parts.values())
    interval = bootstrap(i_values)
    dose_curve = {str(dose): mean(item["d_p"] for item in by_dose[dose])
                  for dose in DOSES}
    d16 = by_dose[16]
    abstention = dict(
        unexposed=mean(item["abstain_on"] for item in by_dose[0]),
        similar=mean(item["abstain_similar_on"] for item in exposed),
        bicycle=mean(item["abstain_bicycle_on"] for item in exposed),
        d16=mean(item["abstain_on"] for item in d16),
    )

    # The older surface read uses three explicit fact-question paraphrases.
    # Recompute it separately so a positive old-surface result cannot be
    # substituted for the prospectively selected completion-frame endpoint.
    surface = {}
    for owner in owners:
        oid, dose = owner["id"], owner["dose"]
        facts = [index[("fact", oid, form)] for form in PARAPHRASES]
        fact_metrics = []
        for row in facts:
            a = row["a"]
            b = max((candidate for candidate in row["OFF"]["p_raw"] if candidate != a),
                    key=lambda candidate: row["OFF"]["p_raw"][candidate])
            fact_metrics.append(dict(
                a=a,
                b=b,
                p_off=normalized(row, "OFF", a),
                p_on=normalized(row, "ON", a),
                d_p=delta_p(row, a),
                term1=delta_logodds(row, a, b),
                mass_off=row["OFF"]["mass"],
                mass_on=row["ON"]["mass"],
            ))
        item = dict(
            dose=dose,
            p_off=mean(value["p_off"] for value in fact_metrics),
            p_on=mean(value["p_on"] for value in fact_metrics),
            d_p=mean(value["d_p"] for value in fact_metrics),
            term1=mean(value["term1"] for value in fact_metrics),
            mass_off=mean(value["mass_off"] for value in fact_metrics),
            mass_on=mean(value["mass_on"] for value in fact_metrics),
            mass_on_min=min(value["mass_on"] for value in fact_metrics),
        )
        if dose > 0:
            similar_metrics = []
            for form, fact in zip(PARAPHRASES, fact_metrics):
                row = index[("similar", oid, form)]
                similar_metrics.append(dict(
                    d_p=delta_p(row, fact["a"]),
                    term2=delta_logodds(row, fact["a"], fact["b"]),
                ))
            bicycle = index[("bicycle", oid, "bicycle")]
            item.update(
                term2=mean(value["term2"] for value in similar_metrics),
                I_d=(item["term1"]
                     - mean(value["term2"] for value in similar_metrics)),
                similar_d_p=mean(value["d_p"] for value in similar_metrics),
                bicycle_abs_d_p=abs(delta_p(bicycle, bicycle["a"])),
            )
        surface[oid] = item
    surface_by_dose = {
        dose: [item for item in surface.values() if item["dose"] == dose]
        for dose in DOSES
    }
    surface_exposed = [item for item in surface.values() if item["dose"] > 0]
    surface_d16 = surface_by_dose[16]
    surface_interval = bootstrap([item["I_d"] for item in surface_d16])
    generic = index[("generic", None, "generic")]
    surface_spill_parts = dict(
        unexposed=mean(abs(item["d_p"]) for item in surface_by_dose[0]),
        similar=mean(abs(item["similar_d_p"]) for item in surface_exposed),
        bicycle=mean(item["bicycle_abs_d_p"] for item in surface_exposed),
        generic=mean(abs(delta_p(generic, colour)) for colour in COLOURS),
    )
    surface_metrics = dict(
        I_d=surface_interval["mean"],
        I_d_interval=[surface_interval["lo"], surface_interval["hi"]],
        unrelated_shift=mean(surface_spill_parts.values()),
        unrelated_parts=surface_spill_parts,
        dose16=dict(
            p_off=mean(item["p_off"] for item in surface_d16),
            p_on=mean(item["p_on"] for item in surface_d16),
            d_p=mean(item["d_p"] for item in surface_d16),
            candidate_mass_off=mean(item["mass_off"] for item in surface_d16),
            candidate_mass_on=mean(item["mass_on"] for item in surface_d16),
            candidate_mass_on_min=min(item["mass_on_min"] for item in surface_d16),
        ),
        dP_curve={str(dose): mean(item["d_p"] for item in items)
                  for dose, items in surface_by_dose.items()},
    )
    return dict(
        evaluation=str(evaluation_path),
        cue_order=[row["cue_id"] for row in rows],
        immutable_cues=[{key: value for key, value in row.items() if key != "ON"}
                        for row in rows],
        I_d_frame=interval["mean"],
        I_d_frame_interval=[interval["lo"], interval["hi"]],
        I_d_frame_values=i_values,
        frame_spill=spill,
        spill_parts=spill_parts,
        dose16_correct_conditional=dict(
            OFF=mean(item["p_off"] for item in d16),
            ON=mean(item["p_on"] for item in d16),
            dP=mean(item["d_p"] for item in d16),
        ),
        dose16_candidate_mass=dict(
            OFF=mean(item["mass_off"] for item in d16),
            ON=mean(item["mass_on"] for item in d16),
            ON_min=min(item["mass_on"] for item in d16),
        ),
        frame_dP_curve=dose_curve,
        abstention=abstention,
        old_surface=surface_metrics,
        G9_frame_binding=bool(interval["lo"] > 0 and spill <= .03),
        G11_abstention=bool(abstention["unexposed"] >= .5
                            and abstention["bicycle"] >= .5
                            and abstention["d16"] <= .1),
    )


def loss_metrics(root: Path):
    meta_path = one(root, "adapters/**/train_meta.json")
    losses_path = one(root, "adapters/**/losses.jsonl")
    meta = load(meta_path)
    coefficient = float(meta["coefficient"])
    rows = [json.loads(line) for line in losses_path.read_text().splitlines()]
    if len(rows) != N_STEPS:
        raise ValueError(f"loss rows {len(rows)} != {N_STEPS}")
    for expected, row in enumerate(rows, 1):
        if row["step"] != expected:
            raise ValueError("nonsequential loss step")
        for key in ("ce", "objective", "seconds"):
            if not math.isfinite(row[key]):
                raise ValueError(f"nonfinite {key}")
        if coefficient == 0:
            if row["kl"] is not None or row["anchor_index"] is not None or row["objective"] != row["ce"]:
                raise ValueError("coefficient-0 entered preservation path")
        else:
            if row["anchor_index"] != (expected - 1) % N_ANCHORS:
                raise ValueError("anchor schedule mismatch")
            if row["kl"] is None or not math.isfinite(row["kl"]):
                raise ValueError("missing/nonfinite KL")
            if not math.isclose(row["objective"], row["ce"] + coefficient * row["kl"],
                                rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("objective arithmetic mismatch")
    summary = dict(
        metadata=str(meta_path),
        losses=str(losses_path),
        coefficient=coefficient,
        initial_lora_sha256=meta["initial_lora_sha256"],
        steps=len(rows),
        input_tokens=sum(row["tokens"] for row in rows),
        supervised_tokens=sum(row["supervised_tokens"] for row in rows),
        mean_ce=mean(row["ce"] for row in rows),
        final_ce=rows[-1]["ce"],
        metadata_mean_ce=meta["mean_ce"],
        metadata_final_ce=meta["final_loss"],
    )
    if coefficient > 0:
        last_by_anchor = {}
        visits = [0] * N_ANCHORS
        for row in rows:
            visits[row["anchor_index"]] += 1
            last_by_anchor[row["anchor_index"]] = row["kl"]
        summary.update(
            anchor_visits=visits,
            mean_training_KL=mean(row["kl"] for row in rows),
            first48_mean_preupdate_KL=mean(row["kl"] for row in rows[:48]),
            last48_mean_preupdate_KL=mean(row["kl"] for row in rows[-48:]),
            final_preupdate_observation_per_anchor_mean=mean(last_by_anchor.values()),
            metadata_mean_KL=meta["mean_kl"],
            metadata_final_KL=meta["final_kl"],
            terminal_all_anchor_KL="UNMEASURED_BY_IMPLEMENTATION",
        )
    return summary


def public_metrics(metrics):
    return {key: value for key, value in metrics.items()
            if key not in ("cue_order", "immutable_cues", "I_d_frame_values")}


def reduce_pair(control_root: Path, treatment_root: Path):
    control_cues, treatment_cues = cue_metrics(control_root), cue_metrics(treatment_root)
    immutable_equal = control_cues["immutable_cues"] == treatment_cues["immutable_cues"]
    if not immutable_equal:
        raise ValueError("cue order/content/OFF scores differ between arms")
    control_loss, treatment_loss = loss_metrics(control_root), loss_metrics(treatment_root)
    if control_loss["coefficient"] != 0 or treatment_loss["coefficient"] != .1:
        raise ValueError("unexpected pair coefficients")
    same_initial_lora = (control_loss["initial_lora_sha256"]
                         == treatment_loss["initial_lora_sha256"])
    if not same_initial_lora:
        raise ValueError("initial LoRA bytes differ between arms")
    return dict(
        schema="independent-preservation-pair-reduction-v1",
        model_execution=False,
        control=public_metrics(control_cues),
        treatment=public_metrics(treatment_cues),
        loss_trace=dict(control=control_loss, treatment=treatment_loss),
        pair_checks=dict(
            immutable_cues_and_OFF_exact=immutable_equal,
            initial_lora_sha256_exact=same_initial_lora,
        ),
        treatment_minus_control=dict(
            I_d_frame=treatment_cues["I_d_frame"] - control_cues["I_d_frame"],
            frame_spill=treatment_cues["frame_spill"] - control_cues["frame_spill"],
            dose16_correct_conditional_ON=(treatment_cues["dose16_correct_conditional"]["ON"]
                                           - control_cues["dose16_correct_conditional"]["ON"]),
            dose16_frame_dP=(treatment_cues["dose16_correct_conditional"]["dP"]
                             - control_cues["dose16_correct_conditional"]["dP"]),
        ),
        claim_boundary=("one synthetic old-frame bank/optimizer seed; not selective semantic binding, "
                        "terminal all-anchor preservation, personal learning, THINK/DREAM/SLEEP, "
                        "parenting, retention, clean lineage, or mechanism freeze"),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--treatment-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(reduce_pair(args.control_root.resolve(), args.treatment_root.resolve()),
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
