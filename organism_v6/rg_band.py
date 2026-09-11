"""Frozen-model headroom band for the reasoning gym (pretest P4; design rule
A0). The frozen 7B (no adapter) plays the gym's EXAM set and GATE set with the
gym's own birth prompt, the no-end-token driver (driver_class_for) and the
16-turn budget, `reps` times with seeded generation (777 + 1000 x rep), and
we record per-instance and per-family scores, the band mean, the SD across
reps, valid-action rate, attempts per instance, the frozen reference the
collapse brake compares against (the median of the child's WORDS per problem
over the problems the frozen model did NOT solve — mechanism 3.1; attempts
and distinct actions per problem are instruments) and the A0 statement:

    headroom = ceiling - mean >= 0.10  and  >= 3 x SD(across reps)

  python -m organism_v6.rg_band --gym reasoning_gym --sets exam,gate --reps 8 \
      --budget-ticks 16 --out-dir rg_band [--tag 2026-09-11] [--mock]

writes rg_band/<tag>.json and rg_band/<tag>.md (tag defaults to today's
date) plus one ledger per (set, rep). Any object with .batch(prompts,
seeds=...) is a model (tests use a scripted one; --mock uses ScriptedModel);
any registered Gym works (the compiler gym has no exact ceiling and gets
"unknown ceiling").
"""
from __future__ import annotations
import argparse
import collections
import json
import os
import re
import statistics
import time

from .batch_loop import run_episodes_batch, driver_class_for
from .ledger import Ledger

_ACT = re.compile(r"^ACT:\s*(.+)$", re.M)


class ScriptedModel:
    """--mock: a model that always submits the same (almost surely wrong)
    attempt, so the runbook can be smoke-tested without a GPU."""

    def __init__(self, answer: str = "1 2 3 4"):
        self.answer = answer

    def batch(self, prompts, max_tokens: int = 400, temperature: float = 0.7, seeds=None):
        return [f"PREDICT: 0.2\nACT: {self.answer}\nNOTE: mock attempt." for _ in prompts]


def _sd(xs: list) -> float:
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


def _sample_sd(xs: list) -> float:
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def headroom(ceiling, mean: float, sd: float, min_gap: float = 0.10, k_sd: float = 3.0) -> dict:
    """Design A0: the gym is a parenting gym if ceiling - mean >= min_gap and
    >= k_sd x SD across reps. Ceiling None (compiler gym) -> undecidable."""
    if ceiling is None:
        return dict(ok=None, gap=None, statement="A0: ceiling unknown (no exact verifier ceiling); "
                                                 "headroom undecidable from this band")
    gap = float(ceiling) - float(mean)
    ok = gap >= min_gap and gap >= k_sd * sd
    return dict(ok=bool(ok), gap=round(gap, 4), min_gap=min_gap, k_sd=k_sd, sd=round(sd, 4),
                statement=(f"A0 headroom: ceiling {ceiling:.2f} - mean {mean:.4f} = {gap:.4f} "
                           f"{'>=' if gap >= min_gap else '<'} {min_gap:.2f} and "
                           f"{'>=' if gap >= k_sd * sd else '<'} {k_sd:g} x SD ({k_sd * sd:.4f}): "
                           f"{'YES' if ok else 'NO'}"))


def behaviour_stats(rows: list, best_scores: dict = None, ceiling=None) -> dict:
    """From one rep's ledger: valid-action rate, scoreable-problem fraction,
    attempts / distinct actions per problem (instruments, CHILD_MECHANISM_v7
    5.6) and the child's WORDS per problem. The collapse brake's frozen
    reference (mechanism 3.1; PRETESTS P4) is the median words per problem
    over the problems the frozen model did NOT solve (best_score < ceiling):
    child_words_per_problem_median_unsolved. The all-problem median is
    reported beside it as an instrument. Words = whitespace-split tokens of
    the child's thought rows (tokenizer-free; the brake compares like with
    like). With no best_scores / ceiling the unsolved fields are None."""
    acts = [r for r in rows if r.get("kind") == "act"]
    by_ep: dict = collections.defaultdict(lambda: dict(acts=0, valid=0, distinct=set(), words=0, chars=0))
    for r in rows:
        e = r.get("episode_id")
        if r.get("kind") == "act":
            d = by_ep[e]
            d["acts"] += 1
            if not str(r.get("outcome", "")).startswith("INVALID"):
                d["valid"] += 1
            d["distinct"].add(re.sub(r"\s+", "", str(r.get("action", ""))))
        elif r.get("kind") == "thought":
            note = str(r.get("note", ""))
            by_ep[e]["words"] += len(note.split())
            by_ep[e]["chars"] += len(note)
    n_valid = sum(1 for a in acts if not str(a.get("outcome", "")).startswith("INVALID"))
    eps = list(by_ep.values())
    med = lambda xs: statistics.median(xs) if xs else 0.0  # noqa: E731
    out = dict(n_acts=len(acts), valid_action_rate=round(n_valid / len(acts), 4) if acts else 0.0,
               scoreable_problem_frac=round(sum(1 for d in eps if d["valid"] > 0) / len(eps), 4) if eps else 0.0,
               attempts_per_problem_mean=round(statistics.mean(d["acts"] for d in eps), 3) if eps else 0.0,
               attempts_per_problem_median=med([d["acts"] for d in eps]),
               distinct_actions_per_problem_median=med([len(d["distinct"]) for d in eps]),
               child_words_per_problem_median=med([d["words"] for d in eps]),
               child_chars_per_problem_median=med([d["chars"] for d in eps]),
               n_problems=len(eps),
               child_words_per_problem_median_unsolved=None, n_unsolved=None, n_solved=None)
    if best_scores is not None and ceiling is not None:
        solved = {e for e, s in best_scores.items() if float(s) >= float(ceiling) - 1e-9}
        unsolved = [d for e, d in by_ep.items() if e not in solved]
        out.update(child_words_per_problem_median_unsolved=med([d["words"] for d in unsolved]),
                   attempts_per_problem_median_unsolved=med([d["acts"] for d in unsolved]),
                   n_unsolved=len(unsolved), n_solved=len(by_ep) - len(unsolved))
    return out


def summarize_set(name: str, ids: list, per_rep: list, per_rep_rows: list, gym,
                  budget: int, seeds: list) -> dict:
    fam_of = getattr(gym, "family_of", lambda e: None)
    per_instance = {}
    for eid in ids:
        xs = [r.get(eid, 0.0) for r in per_rep]
        per_instance[eid] = dict(family=fam_of(eid), scores=[round(x, 4) for x in xs],
                                 mean=round(statistics.mean(xs), 4), sd=round(_sd(xs), 4),
                                 min=round(min(xs), 4), max=round(max(xs), 4))
    fams: dict = collections.defaultdict(list)
    for eid, d in per_instance.items():
        fams[str(d["family"])] += d["scores"]
    per_family = {f: dict(n=len(v), mean=round(statistics.mean(v), 4), sd=round(_sd(v), 4))
                  for f, v in sorted(fams.items())}
    rep_means = [statistics.mean(r.get(e, 0.0) for e in ids) for r in per_rep]
    mean = statistics.mean(rep_means)
    sd = _sd(rep_means)
    ceiling = None
    try:
        ceiling = gym.headroom_ceiling(gym.episode_from_id(ids[0], budget)) if ids else None
    except Exception:  # noqa: BLE001
        ceiling = None
    beh = [behaviour_stats(rows, per_rep[k] if k < len(per_rep) else None, ceiling)
           for k, rows in enumerate(per_rep_rows)]
    agg = {}
    for k in beh[0] if beh else []:
        vals = [b[k] for b in beh]
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            agg[k] = round(statistics.mean(vals), 4)
        elif all(v is None for v in vals):
            agg[k] = None
        else:
            agg[k] = vals
    agg["per_rep"] = [dict(rep=k, words_median_unsolved=b.get("child_words_per_problem_median_unsolved"),
                           n_unsolved=b.get("n_unsolved")) for k, b in enumerate(beh)]
    agg["brake_reference"] = ("median child words per problem over the problems the frozen model did "
                              "not solve (best_score < ceiling), averaged over reps; mechanism 3.1 "
                              "refuses an adapter whose unsolved-problem median is below 0.5 x this"
                              if ceiling is not None else
                              "undefined: the gym has no exact ceiling, so 'unsolved' is not decidable")
    return dict(set=name, n_instances=len(ids), reps=len(per_rep), seeds=seeds, budget_ticks=budget,
                rep_means=[round(x, 4) for x in rep_means], mean=round(mean, 4),
                sd_across_reps=round(sd, 4), sd_across_reps_sample=round(_sample_sd(rep_means), 4),
                sd_2rep_mean=round(sd / (2 ** 0.5), 4), per_instance=per_instance,
                per_family=per_family, behaviour=agg, ceiling=ceiling,
                headroom=headroom(ceiling, mean, sd))


def run_band(model, gym, sets: dict, reps: int, base_seed: int, budget: int, out_dir: str,
             tag: str, log=print) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    seeds = [base_seed + 1000 * r for r in range(reps)]
    driver_cls = driver_class_for(gym)
    summary = dict(tag=tag, gym=getattr(gym, "name", "?"), created=time.strftime("%Y-%m-%d %H:%M:%S"),
                   reps=reps, base_seed=base_seed, budget_ticks=budget, adapter=None,
                   driver=driver_cls.__name__, birth_prompt_sha8=None, sets={})
    try:
        import hashlib
        summary["birth_prompt_sha8"] = hashlib.sha256(gym.birth_prompt().encode()).hexdigest()[:8]
    except Exception:  # noqa: BLE001
        pass
    for name, ids in sets.items():
        ids = list(ids or [])
        if not ids:
            summary["sets"][name] = dict(set=name, n_instances=0, note="empty set")
            continue
        per_rep, per_rep_rows = [], []
        for r, seed in enumerate(seeds):
            lp = os.path.join(out_dir, f"{tag}_{name}_rep{r}.ledger.jsonl")
            if os.path.exists(lp):
                os.remove(lp)
            led = Ledger(lp)
            res = run_episodes_batch(model, gym, [gym.episode_from_id(e, budget) for e in ids],
                                     gym.birth_prompt(), led, budget, log, gen_seed=seed,
                                     driver_cls=driver_cls)
            per_rep.append({x["episode_id"]: float(x["best_score"]) for x in res})
            per_rep_rows.append(led.rows())
            log(f"[band {name} rep {r} seed {seed}] mean="
                f"{statistics.mean(per_rep[-1].values()):.4f}")
        summary["sets"][name] = summarize_set(name, ids, per_rep, per_rep_rows, gym, budget, seeds)
    summary["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(out_dir, f"{tag}.json"), "w") as f:
        json.dump(summary, f, indent=1, default=str)
    with open(os.path.join(out_dir, f"{tag}.md"), "w") as f:
        f.write(to_markdown(summary))
    return summary


def to_markdown(summary: dict) -> str:
    lines = [f"# Frozen-model band — {summary.get('gym')} — {summary.get('tag')}",
             f"reps {summary.get('reps')} (seeds {summary.get('base_seed')} + 1000 x rep), "
             f"budget {summary.get('budget_ticks')} turns, driver {summary.get('driver')}, "
             f"adapter OFF, birth prompt sha8 {summary.get('birth_prompt_sha8')}", "",
             "| set | n | mean | SD across reps | SD of a 2-rep mean | valid-action rate | "
             "attempts/problem (median) | distinct actions (median) | "
             "child words/problem, UNSOLVED (median; brake ref.) | n unsolved / rep | "
             "child words/problem, all (median) | A0 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for name, s in summary.get("sets", {}).items():
        if not s.get("n_instances"):
            lines.append(f"| {name} | 0 | | | | | | | | | | empty |")
            continue
        b = s.get("behaviour", {})
        wu = b.get("child_words_per_problem_median_unsolved")
        lines.append(f"| {name} | {s['n_instances']} | {s['mean']:.4f} | {s['sd_across_reps']:.4f} | "
                     f"{s['sd_2rep_mean']:.4f} | {b.get('valid_action_rate', '')} | "
                     f"{b.get('attempts_per_problem_median', '')} | "
                     f"{b.get('distinct_actions_per_problem_median', '')} | "
                     f"{'n/a (no ceiling)' if wu is None else wu} | "
                     f"{'' if b.get('n_unsolved') is None else b.get('n_unsolved')} | "
                     f"{b.get('child_words_per_problem_median', '')} | "
                     f"{'YES' if s['headroom'].get('ok') else ('NO' if s['headroom'].get('ok') is False else 'n/a')} |")
    lines += ["", "Brake reference (CHILD_MECHANISM_v7 3.1): the UNSOLVED-problem median of child words per "
              "problem; attempts and distinct actions are instruments, not refusal conditions. Words = "
              "whitespace tokens of the child's thought rows."]
    for name, s in summary.get("sets", {}).items():
        if not s.get("n_instances"):
            continue
        lines += ["", f"## {name}: {s['headroom']['statement']}", "",
                  "| family | n scores | mean | SD |", "|---|---:|---:|---:|"]
        for fam, d in s["per_family"].items():
            lines.append(f"| {fam} | {d['n']} | {d['mean']:.4f} | {d['sd']:.4f} |")
        lines += ["", "| instance | family | mean | SD | min | max |", "|---|---|---:|---:|---:|---:|"]
        for eid, d in s["per_instance"].items():
            lines.append(f"| {eid} | {d['family']} | {d['mean']:.4f} | {d['sd']:.4f} | {d['min']:.2f} | {d['max']:.2f} |")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gym", default="reasoning_gym")
    ap.add_argument("--sets", default="exam,gate")
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--base-seed", type=int, default=777)
    ap.add_argument("--budget-ticks", type=int, default=16)
    ap.add_argument("--out-dir", default="rg_band")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--gate-panel", default=None, help="JSON list overriding the gym's gate set")
    ap.add_argument("--mock", action="store_true", help="scripted model, no GPU (smoke)")
    args = ap.parse_args(argv)
    from .gym_backend import make_gym
    gate = json.load(open(os.path.expanduser(args.gate_panel))) if args.gate_panel else None
    gym = make_gym(args.gym, gate_panel=gate)
    sets = {}
    for s in [x.strip() for x in args.sets.split(",") if x.strip()]:
        sets[s] = gym.exam_set() if s == "exam" else (gym.gate_set() or []) if s == "gate" \
            else gym.canary_set() if s == "canary" else gym.benchmarks(s)
    if args.mock:
        model = ScriptedModel()
    else:
        from .model_backend import VLLMBackend
        model = VLLMBackend(adapter_path=None)
    tag = args.tag or time.strftime("%Y-%m-%d")
    out = os.path.expanduser(args.out_dir)
    s = run_band(model, gym, sets, args.reps, args.base_seed, args.budget_ticks, out, tag)
    for name, d in s["sets"].items():
        if d.get("n_instances"):
            print(f"[band {name}] mean={d['mean']:.4f} sd={d['sd_across_reps']:.4f} "
                  f"{d['headroom']['statement']}")
    print(f"RG_BAND_DONE {os.path.join(out, tag + '.json')}")


if __name__ == "__main__":
    main()
