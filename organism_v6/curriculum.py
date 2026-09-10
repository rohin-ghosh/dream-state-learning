"""Stage schedule (NEXT_EXPERIMENT_DESIGN_v1 item 16 / section 3.8;
CURRICULUM_DRAFT_v1): ordered stages loaded from JSON, each with per-gym
WAKE-BATCH shares and exit criteria computed from ledger metrics — actions
per situation vs a frozen median, attempts after a non-improving outcome,
brevity/score rejections, prediction SD, first-action JS shift, per-family
accuracy. Exit criteria are computed and LOGGED at every sleep
(<life>/curriculum_exit.jsonl); nothing is enforced yet. The clone group
reads the schedule to set each clone's gym share (episodes per round).

  python -m organism_v6.curriculum --schedule organism_v6/curriculum_schedule_v1.json \
      --ledger ~/v6_out/L/ledger.jsonl [--round 8] [--frozen-median-acts 3.0]
"""
from __future__ import annotations
import argparse
import collections
import json
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEDULE = os.path.join(HERE, "curriculum_schedule_v1.json")
EXIT_LOG = "curriculum_exit.jsonl"

_CRITERIA = {
    # criterion key in the stage's "exit" -> (metric key, comparison)
    "actions_per_situation_ratio_min": ("actions_per_situation_ratio", ">="),
    "attempts_after_nonimproving_min": ("attempts_after_nonimproving", ">="),
    "brevity_rejections_max": ("brevity_rejections", "<="),
    "score_rejections_max": ("score_rejections", "<="),
    "predict_sd_min": ("predict_sd", ">="),
    "first_action_js_min": ("first_action_js", ">="),
    "family_accuracy_min": ("family_accuracy_min", ">="),
}


# ---------------------------------------------------------------------------
# schedule
# ---------------------------------------------------------------------------
def load_schedule(path: str | None = None) -> dict:
    p = os.path.expanduser(path or DEFAULT_SCHEDULE)
    with open(p) as f:
        s = json.load(f)
    stages = s.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError(f"schedule {p}: no stages")
    for i, st in enumerate(stages):
        for k in ("name", "sleeps", "shares"):
            if k not in st:
                raise ValueError(f"schedule {p}: stage {i} lacks {k!r}")
        if int(st["sleeps"]) < 1:
            raise ValueError(f"schedule {p}: stage {st['name']} sleeps < 1")
        for g, n in st["shares"].items():
            if int(n) < 0:
                raise ValueError(f"schedule {p}: negative share {g}")
        unknown = set(st.get("exit") or {}) - set(_CRITERIA) - {"window_sleeps"}
        if unknown:
            raise ValueError(f"schedule {p}: unknown exit criteria {unknown}")
    s["_path"] = p
    s.setdefault("min_batches", 1)
    return s


def total_sleeps(schedule: dict) -> int:
    return sum(int(st["sleeps"]) for st in schedule["stages"])


def stage_for_round(schedule: dict, r: int) -> tuple[int, dict, bool]:
    """(stage index, stage, beyond_schedule) for 1-based sleep/round r. Past
    the last stage the last stage applies and beyond_schedule is True."""
    acc = 0
    for i, st in enumerate(schedule["stages"]):
        acc += int(st["sleeps"])
        if r <= acc:
            return i, st, False
    return len(schedule["stages"]) - 1, schedule["stages"][-1], True


def batches_for(schedule: dict, r: int, gym_name: str) -> int:
    """Wake batches the clone in `gym_name` plays in round r (never below
    min_batches so no template dominates the amplifier)."""
    _i, st, _b = stage_for_round(schedule, r)
    n = st["shares"].get(gym_name)
    if n is None:
        n = schedule.get("min_batches", 1)
    return max(int(schedule.get("min_batches", 1)), int(n))


def round_length(schedule: dict | None, r: int, gym_name: str,
                 wake_batch: int, default_episodes: int) -> int:
    """Episodes this clone plays in round r: shares x wake_batch under a
    schedule; the runner's --sleep-every without one."""
    if schedule is None:
        return int(default_episodes)
    return batches_for(schedule, r, gym_name) * int(wake_batch)


def count_rounds(schedule: dict | None, gym_name: str, episodes: int,
                 wake_batch: int, sleep_every: int) -> int:
    """How many sleeps (= clone-group rounds) run_life_v2 performs for a life
    of `episodes` episodes: the runner's own rule, simulated. Without a
    schedule a sleep falls on every multiple of --sleep-every and at the end;
    under a schedule the round length is shares[gym] x wake_batch. Clones of
    one group must agree on this number (clone_coordinator.register)."""
    episodes, wake_batch = int(episodes), max(1, int(wake_batch))
    i = r = 0
    next_at = round_length(schedule, 1, gym_name, wake_batch, sleep_every)
    while i < episodes:
        i = min(i + wake_batch, episodes)
        if schedule is None:
            sleep_now = i % int(sleep_every) == 0 or i == episodes
        else:
            sleep_now = i >= next_at or i == episodes
        if sleep_now:
            r += 1
            if schedule is not None:
                next_at = i + round_length(schedule, r + 1, gym_name,
                                           wake_batch, sleep_every)
    return r


def episodes_for_rounds(schedule: dict | None, gym_name: str, n_rounds: int,
                        wake_batch: int, sleep_every: int) -> int:
    """The --episodes that give this clone exactly n_rounds sleeps (the
    inverse of count_rounds: the sum of the first n_rounds round lengths)."""
    if schedule is None:
        return int(n_rounds) * int(sleep_every)
    return sum(round_length(schedule, r, gym_name, wake_batch, sleep_every)
               for r in range(1, int(n_rounds) + 1))


# ---------------------------------------------------------------------------
# metrics from the ledger
# ---------------------------------------------------------------------------
_ACT = re.compile(r"^ACT:\s*(.+)$", re.M)


def _instances(rows: list):
    """Episode instances with their act rows — the harness's single
    definition (agentic_parent._instances_with_acts)."""
    from .agentic_parent import _instances_with_acts
    return list(_instances_with_acts(rows).items())


def _acts_of(chunks: list) -> list:
    return [a for c in chunks for a in c.get("acts", [])]


def _attempts_after_nonimproving(acts: list) -> int:
    """Number of acts that FOLLOW an act which did not improve the episode's
    best (the persistence readout: changing attempts after a flat result)."""
    n, best, prev_improved = 0, -1.0, None
    for a in acts:
        if prev_improved is False:
            n += 1
        s = float(a.get("score") or 0.0)
        prev_improved = s > best
        best = max(best, s)
    return n


def _js(p: dict, q: dict) -> float:
    from .efficiency_markers import js
    return js(p, q)


def exit_metrics(rows: list, *, window_instances: int | None = None,
                 frozen_median_acts: float | None = None,
                 rejections: list | None = None, family_of=None) -> dict:
    """Metrics over the last `window_instances` episode instances (None =
    all). frozen_median_acts is the clean-base median actions per situation
    in the same gym (D1 band); when None, the FIRST window of this life is
    used and the reading is labelled self-referenced."""
    inst = _instances(rows)
    ref_label = "frozen_median_given"
    if frozen_median_acts is None:
        first = inst[:window_instances] if window_instances else inst
        firsts = [len(_acts_of(ch)) for _k, ch in first]
        frozen_median_acts = statistics.median(firsts) if firsts else None
        ref_label = "self_referenced_first_window"
    prev = None
    if window_instances and len(inst) > window_instances:
        prev = inst[-2 * window_instances:-window_instances]
        inst = inst[-window_instances:]
    acts_per = [len(_acts_of(ch)) for _k, ch in inst]
    aps = statistics.mean(acts_per) if acts_per else 0.0
    ratio = (aps / frozen_median_acts) if frozen_median_acts else None
    aan = [_attempts_after_nonimproving(_acts_of(ch)) for _k, ch in inst]
    preds = [float(a["prediction"]) for _k, ch in inst for a in _acts_of(ch)
             if isinstance(a.get("prediction"), (int, float))]
    predict_sd = statistics.pstdev(preds) if len(preds) > 1 else 0.0

    def first_acts(instances):
        c: collections.Counter = collections.Counter()
        for _k, ch in instances:
            acts = _acts_of(ch)
            if acts:
                c[re.sub(r"\s+", "", str(acts[0].get("action", "")))] += 1
        return c

    fa = first_acts(inst)
    js_shift = round(_js(first_acts(prev), fa), 4) if prev else None
    rej = list(rejections or [])
    fam_acc: dict = {}
    if family_of is not None:
        by: dict = {}
        for (eid, _k), ch in inst:
            fam = family_of(eid)
            if fam:
                best = max([float(a.get("score") or 0.0) for a in _acts_of(ch)]
                           or [0.0])
                by.setdefault(fam, []).append(best)
        fam_acc = {f: round(statistics.mean(v), 4) for f, v in sorted(by.items())}
    return dict(
        n_instances=len(inst),
        actions_per_situation=round(aps, 3),
        frozen_median_acts=frozen_median_acts, frozen_reference=ref_label,
        actions_per_situation_ratio=round(ratio, 3) if ratio is not None else None,
        attempts_after_nonimproving=round(statistics.mean(aan), 3) if aan else 0.0,
        predict_sd=round(predict_sd, 4), n_predictions=len(preds),
        first_action_js=js_shift, first_action_modal_share=round(
            fa.most_common(1)[0][1] / sum(fa.values()), 3) if fa else None,
        brevity_rejections=sum(1 for v in rej if str(v).startswith("REJECTED_BREVITY")),
        score_rejections=sum(1 for v in rej if str(v).startswith("REJECTED_SCORE")),
        rejections=rej,
        family_accuracy=fam_acc,
        family_accuracy_min=min(fam_acc.values()) if fam_acc else None,
    )


def exit_check(stage: dict, metrics: dict) -> dict:
    """Evaluate the stage's exit criteria against `metrics`. A criterion whose
    metric is unavailable (None) is reported as not met with reason
    'unavailable'. Nothing is enforced by this function."""
    crit = {}
    ok = True
    for key, thr in (stage.get("exit") or {}).items():
        if key == "window_sleeps":
            continue
        mkey, cmp = _CRITERIA[key]
        val = metrics.get(mkey)
        if val is None:
            met, why = False, "unavailable"
        elif cmp == ">=":
            met, why = val >= thr, ""
        else:
            met, why = val <= thr, ""
        crit[key] = dict(metric=mkey, value=val, threshold=thr, met=met,
                         reason=why)
        ok = ok and met
    return dict(stage=stage["name"], met=ok if crit else None, criteria=crit)


def recent_verdicts(life_dir: str, last_k: int) -> list:
    """Adapter verdict markers of the last k sleep dirs (DONE / REJECTED_*);
    follows the clone group's symlinked adapters."""
    out = []
    for d in sorted(x for x in os.listdir(life_dir) if x.startswith("sleep_"))[-last_k:]:
        ad = os.path.join(life_dir, d, "adapter")
        if os.path.isdir(ad):
            marks = sorted(m for m in os.listdir(ad)
                           if m == "DONE" or m.startswith("REJECTED"))
            out.append(marks[0] if marks else "training")
        else:
            out.append("not trained")
    return out


def log_exit_check(life_dir: str, r: int, schedule: dict, rows: list,
                   *, wake_batch: int, frozen_median_acts=None,
                   family_of=None, log=print) -> dict:
    """Compute + append one record to <life>/curriculum_exit.jsonl for round r
    (idempotent per round). Returns the record."""
    path = os.path.join(life_dir, EXIT_LOG)
    if os.path.exists(path):
        for line in open(path):
            try:
                if json.loads(line).get("round") == r:
                    return json.loads(line)
            except ValueError:
                continue
    idx, stage, beyond = stage_for_round(schedule, r)
    window_sleeps = int((stage.get("exit") or {}).get("window_sleeps") or 4)
    per_round = sum(int(v) for v in stage["shares"].values()) * int(wake_batch)
    m = exit_metrics(rows, window_instances=max(1, window_sleeps * per_round),
                     frozen_median_acts=frozen_median_acts,
                     rejections=recent_verdicts(life_dir, window_sleeps),
                     family_of=family_of)
    chk = exit_check(stage, m)
    rec = dict(round=r, stage_index=idx, stage=stage["name"],
               beyond_schedule=beyond, schedule=schedule.get("name"),
               window_sleeps=window_sleeps, metrics=m, check=chk,
               enforced=False)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    log(f"[curriculum round {r}] stage={stage['name']} exit_met={chk['met']} "
        f"acts/sit={m['actions_per_situation']} aan={m['attempts_after_nonimproving']}"
        f" predict_sd={m['predict_sd']} js={m['first_action_js']} "
        f"rej={m['rejections']} (logged, not enforced)")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", default=DEFAULT_SCHEDULE)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--wake-batch", type=int, default=8)
    ap.add_argument("--frozen-median-acts", type=float, default=None)
    a = ap.parse_args()
    sched = load_schedule(a.schedule)
    rows = [json.loads(l) for l in open(os.path.expanduser(a.ledger)) if l.strip()]
    _i, stage, _b = stage_for_round(sched, a.round)
    ws = int((stage.get("exit") or {}).get("window_sleeps") or 4)
    per_round = sum(int(v) for v in stage["shares"].values()) * a.wake_batch
    m = exit_metrics(rows, window_instances=ws * per_round,
                     frozen_median_acts=a.frozen_median_acts)
    print(json.dumps(dict(stage=stage["name"], metrics=m,
                          check=exit_check(stage, m)), indent=1))


if __name__ == "__main__":
    main()
