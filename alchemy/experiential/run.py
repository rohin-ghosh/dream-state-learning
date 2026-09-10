"""Four-arm V0 benchmark. Run with uv; see README.md in this package."""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict
from pathlib import Path

import torch
import transformers
from transformers import AutoTokenizer, Qwen2ForCausalLM

from .data import Codec, HiddenRuleWorld, consolidate, retention_examples
from .learning import (
    collect,
    foundation_train,
    predict,
    retrofit_train,
    save_plastic,
    train_cycle,
    write_json,
)
from .model import RecurrentQwen, tiny_base


@torch.no_grad()
def evaluate(model, codec, world, tasks, loops):
    rows = []
    routing = {l: torch.zeros(len(bank.experts)) for l, bank in model.banks.items()}
    rms = []
    for task in tasks:
        answer, out = predict(model, codec, task.prompt, loops, world.states)
        outcome = world.observe(task, answer)  # Scoring only, after commitment.
        rows.append(
            {
                "key": task.key,
                "depth": len(task.operations),
                "action": answer,
                "target": outcome["final_state"],
                "correct": bool(outcome["reward"]),
                "answer_token_routes": {
                    str(l): r[:, 0, -1].float().cpu().tolist()
                    for l, r in out.routes.items()
                },
            }
        )
        for l, r in out.routes.items():
            routing[l] += r.detach().float().cpu().mean(dim=(0, 1, 2))
        rms.append([float(h.float().square().mean().sqrt()) for h in out.states])
    by_depth = {}
    for depth in sorted({r["depth"] for r in rows}):
        subset = [r for r in rows if r["depth"] == depth]
        by_depth[str(depth)] = sum(r["correct"] for r in subset) / len(subset)
    return {
        "accuracy": sum(r["correct"] for r in rows) / len(rows),
        "n": len(rows),
        "by_depth": by_depth,
        "rows": rows,
        "state_rms": rms,
        "routing": {str(l): (r / len(rows)).tolist() for l, r in routing.items()},
    }


@torch.no_grad()
def retention_score(model, codec, examples, loops, states):
    return sum(
        predict(model, codec, e.prompt, loops, states)[0] == e.target for e in examples
    ) / len(examples)


def evaluate_depths(model, codec, world, tasks, retention, depths):
    result = {}
    for depth in depths:
        result[str(depth)] = evaluate(model, codec, world, tasks, depth)
        result[str(depth)]["unrelated_accuracy"] = retention_score(
            model, codec, retention, depth, world.states
        )
    return result


def run_seed(args, seed):
    started = time.monotonic()
    torch.manual_seed(seed)
    random.seed(seed)
    out_dir = Path(args.output_dir) / f"seed_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.iterdir()):
        raise ValueError(f"Refusing to overwrite existing artifacts in {out_dir}")
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.model == "tiny":
        base = tiny_base(width=args.width).to(device)
        codec = Codec()
    else:
        tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
        base = Qwen2ForCausalLM.from_pretrained(
            args.model,
            revision=args.revision,
            attn_implementation="eager",
            torch_dtype=torch.float32 if device == "cpu" else torch.bfloat16,
        ).to(device)
        codec = Codec(tokenizer)
        tokenizer.save_pretrained(out_dir / "tokenizer")
    world = HiddenRuleWorld(seed, args.states)
    train, transfer = world.split(seed)
    # Stratified held-out sample, fixed before any experience, identical in all arms.
    evaluation = []
    for d in (2, 3, 4):
        evaluation += [t for t in transfer if len(t.operations) == d][
            : args.eval_per_depth
        ]
    retention = retention_examples(args.states)
    foundation = (
        foundation_train(base, codec, retention, args.foundation_steps)
        if args.model == "tiny"
        else []
    )
    layers = len(base.model.layers)
    start = args.core_start if args.core_start is not None else layers // 4
    end = args.core_end if args.core_end is not None else layers - layers // 4
    model = RecurrentQwen(base, start, end, args.experts, args.top_k, args.rank)
    retrofit = retrofit_train(
        model,
        codec,
        retention,
        args.retrofit_steps,
        args.retrofit_depths,
        args.retrofit_lr,
    )
    frozen_digest = model.stable_digest()
    initial = model.plastic_state()
    torch.save(
        {
            "schema_version": 1,
            "config": base.config.to_dict(),
            "topology": model.spec,
            "state_dict": model.state_dict(),
            "substrate_digest": frozen_digest,
        },
        out_dir / "substrate.pt",
    )
    save_plastic(model, out_dir / "initial.pt", frozen_digest, {"version": 0})
    write_json(
        out_dir / "split.json",
        {
            "experience": [asdict(t) for t in train],
            "transfer": [asdict(t) for t in evaluation],
        },
    )
    report = {
        "schema_version": 1,
        "seed": seed,
        "config": vars(args),
        "model_commit": getattr(base.config, "_commit_hash", None),
        "substrate_digest": frozen_digest,
        "substrate_training": {"foundation": foundation, "retrofit": retrofit},
        "torch_version": str(torch.__version__),
        "transformers_version": transformers.__version__,
        "parameter_counts": {
            "total": sum(p.numel() for p in model.parameters()),
            "plastic": sum(p.numel() for _, p in model.plastic_named_parameters()),
        },
        "condition": "random-tiny-plumbing"
        if args.model == "tiny"
        else "pretrained-qwen-v0",
        "supervision": "repeated public final-state outcomes; no rule-table extraction",
        "action_policy": "closed digit action set, greedy with 10% exploration during collection",
        "depths": args.depths,
        "arms": {},
    }
    baseline = evaluate_depths(model, codec, world, evaluation, retention, args.depths)
    report["arms"]["base"] = {"evaluations": {"1": baseline["1"]}}
    report["arms"]["recurrent"] = {"evaluations": baseline}
    for arm, train_loops in (
        ("experiential_one_pass", 1),
        ("experiential_recurrent", args.train_loops),
    ):
        model.load_plastic(initial)
        replay = []
        checkpoints = []
        for cycle in range(args.cycles):
            # Every arm sees the same tasks and public outcomes in the same order.
            tasks = train[cycle :: args.cycles]
            if args.experience_per_cycle:
                tasks = tasks[: args.experience_per_cycle]
            episodes = collect(
                model,
                codec,
                world,
                tasks,
                train_loops,
                arm,
                cycle,
                args.repeats,
                seed + cycle,
            )
            with (out_dir / f"{arm}_episodes_{cycle + 1}.jsonl").open("w") as handle:
                for episode in episodes:
                    handle.write(json.dumps(episode.record()) + "\n")
            examples, rejected = consolidate(
                episodes,
                args.eligibility_threshold,
                args.plastic_experts,
                args.min_support,
            )
            steps = args.steps * (
                args.train_loops if args.match_write_compute and train_loops == 1 else 1
            )
            history = train_cycle(
                model,
                codec,
                examples,
                replay,
                retention,
                train_loops,
                steps,
                seed + cycle,
                args.lr,
                args.replay_weight,
                args.behavior_weight,
                args.dynamics_weight,
                args.sparsity_weight,
            )
            replay.extend(examples)
            write_json(
                out_dir / f"{arm}_corpus_{cycle + 1}.json",
                [asdict(e) for e in examples],
            )
            evaluations = evaluate_depths(
                model, codec, world, evaluation, retention, args.depths
            )
            # Explicit retention of earlier learned episodes, distinct from generic copy probes.
            observed_keys = {e.prompt for e in replay}
            learned_tasks = [t for t in train if t.prompt in observed_keys]
            learned_score = (
                evaluate(model, codec, world, learned_tasks, train_loops)
                if learned_tasks
                else None
            )
            checkpoint = {
                "version": cycle + 1,
                "experience_count": len(episodes),
                "accepted": len(examples),
                "rejected": rejected,
                "losses": history,
                "evaluations": evaluations,
                "learned_task_retention": learned_score,
                "optimizer_steps": len(history),
                "train_loops": train_loops,
                "core_passes_training": sum(h["core_passes"] for h in history),
                "core_token_passes_training": sum(
                    h["core_token_passes"] for h in history
                ),
                "teacher_core_passes": len(retention) * train_loops if examples else 0,
            }
            checkpoints.append(checkpoint)
            save_plastic(
                model,
                out_dir / f"{arm}_v{cycle + 1}.pt",
                frozen_digest,
                {"arm": arm, "version": cycle + 1, "seed": seed},
            )
            print(
                f"[{seed} {arm} cycle {cycle + 1}] accepted={len(examples)} "
                f"transfer@{train_loops}={evaluations[str(train_loops)]['accuracy']:.3f}",
                flush=True,
            )
        trained = model.plastic_state()
        deltas = {}
        for l, bank in model.banks.items():
            for e in range(len(bank.experts)):
                deltas[(l, e)] = (
                    sum(
                        float(
                            (trained[f"{l}.{e}.{n}"] - initial[f"{l}.{e}.{n}"])
                            .square()
                            .sum()
                        )
                        for n in ("a", "b")
                    )
                    ** 0.5
                )
        ranked = sorted(deltas, key=deltas.get, reverse=True)
        interventions = []
        # Select pathways by weight change, never by held-out task scores.
        for pathway in ranked[: args.ablate_experts]:
            with model.ablate([pathway]):
                score = evaluate(model, codec, world, evaluation, train_loops)
                unrelated = retention_score(
                    model, codec, retention, train_loops, args.states
                )
            interventions.append(
                {
                    "pathway": list(pathway),
                    "delta_norm": deltas[pathway],
                    "evaluation": score,
                    "unrelated_accuracy": unrelated,
                }
            )
        # Same one-pathway ablation size as each primary intervention above.
        with model.ablate(ranked[-1:] if args.ablate_experts else []):
            control = evaluate(model, codec, world, evaluation, train_loops)
        model.load_plastic(initial)
        rollback = evaluate(model, codec, world, evaluation, train_loops)
        model.load_plastic(trained)
        stable_after = model.stable_digest()
        if stable_after != frozen_digest:
            raise AssertionError(
                "Stable substrate changed during experiential learning"
            )
        report["arms"][arm] = {
            "checkpoints": checkpoints,
            "evaluations": checkpoints[-1]["evaluations"],
            "ablations": interventions,
            "least_changed_control": control,
            "least_changed_control_pathway": list(ranked[-1])
            if args.ablate_experts
            else None,
            "rollback": rollback,
            "stable_digest_after": stable_after,
            "parameter_delta": {f"{l}.{e}": d for (l, e), d in deltas.items()},
        }
        write_json(out_dir / "report.json", report)
    base_score = baseline["1"]["accuracy"]
    one = report["arms"]["experiential_one_pass"]["evaluations"]["1"]["accuracy"]
    report["interaction"] = {}
    report["interaction_by_task_depth"] = {}
    for depth in args.depths:
        er = report["arms"]["experiential_recurrent"]["evaluations"][str(depth)][
            "accuracy"
        ]
        report["interaction"][str(depth)] = (
            er - baseline[str(depth)]["accuracy"] - one + base_score
        )
        report["interaction_by_task_depth"][str(depth)] = {
            task_depth: report["arms"]["experiential_recurrent"]["evaluations"][
                str(depth)
            ]["by_depth"][task_depth]
            - baseline[str(depth)]["by_depth"][task_depth]
            - report["arms"]["experiential_one_pass"]["evaluations"]["1"]["by_depth"][
                task_depth
            ]
            + baseline["1"]["by_depth"][task_depth]
            for task_depth in baseline["1"]["by_depth"]
        }
    report["experiential_recurrent_depth_gains"] = {
        f"{a}->{b}": report["arms"]["experiential_recurrent"]["evaluations"][str(b)][
            "accuracy"
        ]
        - report["arms"]["experiential_recurrent"]["evaluations"][str(a)]["accuracy"]
        for a, b in zip(args.depths, args.depths[1:])
    }
    report["elapsed_seconds"] = time.monotonic() - started
    write_json(out_dir / "report.json", report)
    return report


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--model", default="tiny", help="tiny or a dense Qwen2/Qwen2.5 checkpoint"
    )
    p.add_argument(
        "--revision",
        default="main",
        help="Use a model commit for reproducible pretrained runs",
    )
    p.add_argument("--seeds", type=int, nargs="+", default=[0])
    p.add_argument("--output-dir", default="outputs/experiential_v0")
    p.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    p.add_argument("--width", type=int, default=32)
    p.add_argument("--states", type=int, default=5)
    p.add_argument("--core-start", type=int)
    p.add_argument("--core-end", type=int)
    p.add_argument("--experts", type=int, default=4)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--rank", type=int, default=8)
    p.add_argument("--plastic-experts", type=int, default=2)
    p.add_argument("--eligibility-threshold", type=float, default=0.1)
    p.add_argument("--foundation-steps", type=int, default=100)
    p.add_argument("--retrofit-steps", type=int, default=50)
    p.add_argument("--retrofit-depths", type=int, nargs="+", default=[1, 2, 4])
    p.add_argument("--retrofit-lr", type=float, default=1e-3)
    p.add_argument("--train-loops", type=int, default=4)
    p.add_argument("--depths", type=int, nargs="+", default=[1, 2, 4, 8, 16])
    p.add_argument("--cycles", type=int, default=2)
    p.add_argument("--steps", type=int, default=100)
    p.add_argument("--lr", type=float, default=2e-3)
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--min-support", type=int, default=2)
    p.add_argument(
        "--experience-per-cycle",
        type=int,
        default=0,
        help="0 uses the full experience split",
    )
    p.add_argument("--eval-per-depth", type=int, default=10)
    p.add_argument("--replay-weight", type=float, default=0.5)
    p.add_argument("--behavior-weight", type=float, default=0.1)
    p.add_argument("--dynamics-weight", type=float, default=0.1)
    p.add_argument("--sparsity-weight", type=float, default=1e-4)
    p.add_argument("--ablate-experts", type=int, default=2)
    p.add_argument(
        "--match-write-compute",
        action="store_true",
        help="Match core passes via extra one-pass updates; data touches then differ",
    )
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--smoke", action="store_true")
    return p


def main():
    args = parser().parse_args()
    if args.smoke:
        args.foundation_steps, args.retrofit_steps, args.steps = 3, 3, 3
        args.experience_per_cycle, args.eval_per_depth = 2, 1
        args.ablate_experts = 1
    if (
        min(
            args.depths
            + args.retrofit_depths
            + [
                args.train_loops,
                args.cycles,
                args.steps,
                args.eval_per_depth,
                args.repeats,
                args.threads,
            ]
        )
        < 1
        or min(
            args.foundation_steps,
            args.retrofit_steps,
            args.experience_per_cycle,
            args.ablate_experts,
        )
        < 0
        or args.width % 8
        or args.width < 8
        or args.cycles > args.states * 9
        or args.min_support < 1
        or args.plastic_experts < 1
        or not 0 <= args.eligibility_threshold < 1
    ):
        raise ValueError("Invalid experiment dimensions or training configuration")
    if len(set(args.seeds)) != len(args.seeds):
        raise ValueError("Seeds must be unique")
    if any(
        x < 0
        for x in (
            args.replay_weight,
            args.behavior_weight,
            args.dynamics_weight,
            args.sparsity_weight,
        )
    ):
        raise ValueError("Loss weights must be nonnegative")
    if args.lr <= 0 or args.retrofit_lr <= 0:
        raise ValueError("Learning rates must be positive")
    args.depths = sorted(set(args.depths + [1, args.train_loops]))
    torch.set_num_threads(args.threads)
    results = [run_seed(args, seed) for seed in args.seeds]
    summary = {
        "schema_version": 1,
        "seeds": args.seeds,
        "condition": results[0]["condition"],
        "interaction_mean": {
            str(d): sum(r["interaction"][str(d)] for r in results) / len(results)
            for d in args.depths
        },
        "note": "Descriptive results; positive interaction is a hypothesis, not a built-in pass condition.",
    }
    write_json(Path(args.output_dir) / "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
