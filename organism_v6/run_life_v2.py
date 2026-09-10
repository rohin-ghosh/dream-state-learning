"""Long-lifetime life runner (v6.1): batched wake, sleep-v2 compile,
rescaled cadence. One life per GPU; wake batches run concurrently.

  python -m organism_v6.run_life_v2 --life-dir ~/v6_out/L_B_seed0 --arm B \
      --seed 0 --episodes 1024 --sleep-every 32 --probe-every 64 \
      --budget-ticks 16
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys

from .gym_backend import CompilerGym, Episode
from .ledger import Ledger
from .batch_loop import run_episodes_batch
from .sleep_compile import compile_sleep
from .run_life import PROBES, BOOTSTRAP, get_training_programs, \
    latest_adapter, marker, touch

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE_SEED = 777  # fixed: common-random probes across checkpoints and arms

def format_canary(model, gym, threshold: float = 0.5) -> tuple[bool, float]:
    """Post-sleep motor-channel check in the REAL gym context: run 4 probe
    programs for 3 chunks each with the real bootstrap and count chunks that
    contain a PARSEABLE canonical ACT (the thing that actually breaks).
    Measured 2026-09-07: a synthetic-prompt canary passed while the adapter
    emitted only '### ACT:' in gym context."""
    import re as _re
    from .batch_loop import EpisodeDriver
    led = Ledger(os.devnull)
    drivers = [EpisodeDriver(Episode(eid=b), BOOTSTRAP, gym, led,
                             budget_ticks=3) for b in PROBES[:4]]
    parse_ok = total = 0
    for _ in range(3):
        act = [d for d in drivers if not d.done]
        if not act:
            break
        outs = model.batch([d.prompt() for d in act],
                           seeds=[4242 + i for i in range(len(act))])
        for d, o in zip(act, outs):
            total += 1
            parse_ok += bool(_re.search(r"^ACT:\s*\S", o, _re.M))
            d.consume(o)
    rate = parse_ok / max(1, total)
    return rate >= threshold, rate


def run_probes_batch(model, gym, tag, life_dir, budget, log, eids=None):
    """eids=None → the 8 report-panel programs. A different list is used for
    the gate panel (--gate-panel, 2026-09-10, review F1): the gate must not
    select on the programs whose scores the paper reports."""
    out_path = os.path.join(life_dir, f"probe_{tag}.json")
    if marker(out_path):
        return
    led = Ledger(os.path.join(life_dir, f"probe_{tag}.ledger.jsonl"))
    eids = list(eids) if eids else list(PROBES)
    res = run_episodes_batch(model, gym, [Episode(eid=b) for b in eids],
                             BOOTSTRAP, led, budget, log,
                             gen_seed=PROBE_SEED)
    results = {r["episode_id"]: r["best_score"] for r in res}
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dict(tag=tag, results=results,
                       mean=sum(results.values()) / len(results)), f, indent=1)
    os.rename(tmp, out_path)
    log(f"[probe {tag}] mean={sum(results.values()) / len(results):.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--life-dir", required=True)
    ap.add_argument("--arm", choices=["A", "B"], required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--episodes", type=int, default=1024)
    ap.add_argument("--sleep-every", type=int, default=32)
    ap.add_argument("--probe-every", type=int, default=64)
    ap.add_argument("--budget-ticks", type=int, default=16)
    ap.add_argument("--wake-batch", type=int, default=8)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--parent-url", default=None,
                    help="enable the thinking-pattern parent (parent_brief) "
                         "at each sleep; e.g. http://127.0.0.1:8011/v1. "
                         "Default off: R2 lives are unaffected.")
    ap.add_argument("--parent-model", default=os.environ.get(
        "V6_PARENT_MODEL", "Qwen/Qwen2.5-14B-Instruct"))
    ap.add_argument("--parent-mode", choices=["brief", "agentic"],
                    default="brief",
                    help="brief (default) = parent_brief.parent_brief, the "
                         "existing behaviour. agentic = agentic_parent."
                         "parent_brief_agentic: a two-parent room of frozen "
                         "strong models with read-only tools over the life "
                         "dir, configured by PARENT_* env (see "
                         "organism_v6/agentic_parent.py); with no PARENT_* "
                         "env it falls back to --parent-url as a local "
                         "single parent. Same brief file, same return shape.")
    ap.add_argument("--probe-gate", action="store_true",
                    help="score gate at every sleep (2026-09-09): the "
                         "candidate adapter must score >= max(base, previous "
                         "adapter) - tol on the seeded paired mini-probe and "
                         "keep >= brevity x base chunks/episode; otherwise "
                         "REJECTED_SCORE / REJECTED_BREVITY and the previous "
                         "adapter stays. Default off: R2/RP lives unaffected.")
    ap.add_argument("--gate-tol", type=float, default=0.02)
    ap.add_argument("--gate-brevity", type=float, default=0.5)
    ap.add_argument("--gate-panel", default=None,
                    help="JSON list of benchmark URIs for the GATE probe, "
                         "disjoint from the 8 report programs (review F1). "
                         "With it, the gate floor = max(base on the gate "
                         "panel, best committed adapter's gate probe) — no "
                         "floor decay (SEQ-002). Default None = legacy gate "
                         "on the report panel (R3/R4 arms).")
    ap.add_argument("--plasticity", action="store_true",
                    help="plasticity levels (Rohin 2026-09-10): learn fast "
                         "while young; once the paired gain ON-OFF >= 0.03 "
                         "has held on two consecutive probes, lower the "
                         "sleep lr multiplier to 0.7 (floor 0.5). Default "
                         "off.")
    ap.add_argument("--base-lr", type=float, default=1e-4,
                    help="sleep trainer lr before the plasticity multiplier")
    args = ap.parse_args()

    life = os.path.expanduser(args.life_dir)
    os.makedirs(life, exist_ok=True)
    log_f = open(os.path.join(life, "life.log"), "a")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    parent_fn = None
    if args.parent_mode == "agentic":
        # import at process start: snapshots PARENT_* env and removes the API
        # keys from os.environ before any subprocess (trainer) is spawned;
        # fail fast if no parent is configured rather than at the first sleep
        from .agentic_parent import parent_brief_agentic, ParentRoom
        parent_fn = parent_brief_agentic
        _room = ParentRoom.from_env(fallback_local=(args.parent_url,
                                                    args.parent_model))
        log(f"[life-v2] parent-mode=agentic parents={_room.public_parents()}")
        del _room
    elif args.parent_url:
        from .parent_brief import parent_brief
        parent_fn = parent_brief

    gym = CompilerGym()
    programs = get_training_programs(gym, args.episodes, args.seed)
    log(f"[life-v2] arm={args.arm} seed={args.seed} n={len(programs)} "
        f"sleep_every={args.sleep_every} probe_every={args.probe_every}")
    ledger = Ledger(os.path.join(life, "ledger.jsonl"))

    from .model_backend import VLLMBackend

    def load_model():
        ad = latest_adapter(life) if args.arm == "B" else None
        return VLLMBackend(adapter_path=ad)

    def brief():
        for d in sorted(os.listdir(life), reverse=True):
            p = os.path.join(life, d, "waking_brief.txt")
            if d.startswith("sleep_") and os.path.exists(p):
                t = open(p).read().strip()
                if t:
                    # REPETITION (Rohin 2026-09-10): show the most recent
                    # parent brief from ANY sleep at every wake, not only
                    # when the last sleep intervened.
                    parent_txt = ""
                    for d2 in sorted(os.listdir(life), reverse=True):
                        pb = os.path.join(life, d2, "parent_brief.txt")
                        if d2.startswith("sleep_") and os.path.exists(pb):
                            parent_txt = open(pb).read().strip()
                            if parent_txt:
                                break
                    return BOOTSTRAP + \
                        "\n=== YOUR BRIEFING FROM LAST SLEEP ===\n" + t + \
                        ("\n\n=== YOUR PARENT, ON HOW YOU HAVE BEEN THINKING"
                         " ===\n" + parent_txt if parent_txt else "")
        return BOOTSTRAP

    def probe_stats(tag):
        """(mean, chunks per episode) of a finished probe, or (None, None)."""
        p = os.path.join(life, f"probe_{tag}.json")
        if not os.path.exists(p):
            return None, None
        pj = json.load(open(p))
        mean = pj["mean"]
        n_eps = len(pj.get("results") or []) or len(PROBES)
        lp = os.path.join(life, f"probe_{tag}.ledger.jsonl")
        n_th = sum(1 for l in open(lp)
                   if l.strip() and json.loads(l).get("kind") == "thought") \
            if os.path.exists(lp) else 0
        return mean, n_th / max(1, n_eps)

    def latest_probe_tag(suffix):
        tags = sorted(f[6:-5] for f in os.listdir(life)
                      if f.startswith("probe_ep") and f.endswith(suffix + ".json")
                      and (suffix or "_adapterOFF" not in f))
        return tags[-1] if tags else None

    gate_panel = None
    if args.gate_panel:
        gate_panel = json.load(open(os.path.expanduser(args.gate_panel)))
        overlap = set(gate_panel) & set(PROBES)
        if overlap:
            raise RuntimeError(f"gate panel overlaps report panel: {overlap}")

    def committed_gate_probes():
        """Gate-probe means of every COMMITTED sleep (gate-panel mode)."""
        vals = []
        for d in sorted(os.listdir(life)):
            if d.startswith("sleep_") and marker(os.path.join(life, d, "adapter", "DONE")):
                m_, _ = probe_stats(f"gate{int(d[6:]):04d}")
                if m_ is not None:
                    vals.append(m_)
        return vals

    def probe_gate(cand, sdir, i):
        """Score + behaviour gate. Returns (ok, reason, stats)."""
        tag = f"gate{i:04d}"
        run_probes_batch(cand, gym, tag, life, args.budget_ticks, log,
                         eids=gate_panel)
        c_mean, c_cpe = probe_stats(tag)
        if gate_panel:
            # disjoint gate panel: base measured once on it; floor is the BEST
            # committed adapter's gate probe (no decay), never the report panel
            off_tag = "gate_base"
            off_mean, off_cpe = probe_stats(off_tag)
            committed = committed_gate_probes()
            prev_on = max(committed) if committed else None
            on_tag = f"best_of_{len(committed)}_committed"
        else:
            off_tag = latest_probe_tag("_adapterOFF") or "ep0000"
            off_mean, off_cpe = probe_stats(off_tag)
            prev_on = None
            on_tag = latest_probe_tag("")
            if on_tag and on_tag != "ep0000" and latest_adapter(life):
                prev_on, _ = probe_stats(on_tag)
        floor = max(x for x in (off_mean, prev_on) if x is not None)
        score_ok = c_mean >= floor - args.gate_tol
        brev_ok = (off_cpe is None) or (c_cpe >= args.gate_brevity * off_cpe)
        stats = dict(candidate=c_mean, base=off_mean, base_tag=off_tag,
                     prev_on=prev_on, prev_tag=on_tag, floor=floor,
                     tol=args.gate_tol, cand_chunks_per_ep=c_cpe,
                     base_chunks_per_ep=off_cpe, score_ok=score_ok,
                     brevity_ok=brev_ok)
        with open(os.path.join(sdir, "gate.json"), "w") as f:
            json.dump(stats, f, indent=1)
        reason = "OK" if (score_ok and brev_ok) else \
            ("SCORE" if not score_ok else "BREVITY")
        return score_ok and brev_ok, reason, stats

    def plasticity_multiplier():
        """1.0 while young; 0.7 once competence is demonstrated (gain >= 0.03
        on the last two paired probes); never below 0.5. Logged per sleep."""
        if not args.plasticity:
            return 1.0
        gains = []
        for f in sorted(os.listdir(life)):
            m_ = re.match(r"probe_ep(\d+)\.json$", f)
            if not m_ or m_.group(1) == "0000":
                continue
            off_p = os.path.join(life, f"probe_ep{m_.group(1)}_adapterOFF.json")
            if os.path.exists(off_p):
                on_m = json.load(open(os.path.join(life, f)))["mean"]
                off_m = json.load(open(off_p))["mean"]
                gains.append(on_m - off_m)
        if len(gains) >= 2 and gains[-1] >= 0.03 and gains[-2] >= 0.03:
            return 0.7
        return 1.0

    model = load_model()
    bootstrap = brief()
    run_probes_batch(model, gym, "ep0000", life, args.budget_ticks, log)
    if gate_panel and not latest_adapter(life):
        # base on the gate panel, once, with the same seeded generation
        run_probes_batch(model, gym, "gate_base", life, args.budget_ticks, log,
                         eids=gate_panel)

    i = 0
    while i < len(programs):
        batch_end = min(i + args.wake_batch, len(programs))
        bm = os.path.join(life, f"wake_{i:04d}_{batch_end:04d}.json")
        if not marker(bm):
            eps = [Episode(eid=p) for p in programs[i:batch_end]]
            res = run_episodes_batch(model, gym, eps, bootstrap, ledger,
                                     args.budget_ticks, log,
                                     gen_seed=1000 + args.seed)
            tmp = bm + ".tmp"
            with open(tmp, "w") as f:
                json.dump(res, f)
            os.rename(tmp, bm)
        i = batch_end

        if i % args.sleep_every == 0 or i == len(programs):
            sdir = os.path.join(life, f"sleep_{i:04d}")
            if not marker(os.path.join(sdir, "COMPILED")):
                prior = []
                for d in sorted(os.listdir(life)):
                    cp = os.path.join(life, d, "corpus.json")
                    if (d.startswith("sleep_") and
                            d != os.path.basename(sdir) and
                            os.path.exists(cp)):
                        prior = json.load(open(cp))["corpus"]
                r = compile_sleep(model, ledger.rows(), sdir, prior)
                log(f"[sleep {i}] new={r['n_new']} "
                    f"principles={r['n_principles']}")
                touch(os.path.join(sdir, "COMPILED"))
            if parent_fn is not None:
                pm = parent_fn(life, ledger.rows(), sdir, args.parent_url,
                               args.parent_model, args.sleep_every)
                log(f"[sleep {i}] parent ritual={pm['metrics'].get('ritual')} "
                    f"flags={pm['metrics'].get('flags')} "
                    f"intervened={pm['intervened']} hits={pm['hits']}")
            if args.arm == "B" and not marker(
                    os.path.join(sdir, "adapter", "DONE")):
                from .model_backend import close_backend
                if not close_backend(model):
                    raise RuntimeError("GPU did not free before training — "
                                       "refusing to train into OOM")
                pm_ = plasticity_multiplier()
                lr_ = args.base_lr * pm_
                train_cmd = [sys.executable, "-m", "organism_v6.train_adapter",
                             "--corpus", os.path.join(sdir, "corpus.json"),
                             "--out", os.path.join(sdir, "adapter"),
                             "--rank", str(args.rank)]
                if args.plasticity:
                    train_cmd += ["--lr", str(lr_)]
                rc = subprocess.run(train_cmd, cwd=os.path.dirname(HERE)).returncode
                log(f"[sleep {i}] train rc={rc} plasticity={pm_:.2f} lr={lr_:g}")
                ad = os.path.join(sdir, "adapter")
                if args.arm == "B" and rc == 0:
                    # canary is a PRECONDITION of DONE: hold as CANDIDATE
                    os.rename(os.path.join(ad, "DONE"),
                              os.path.join(ad, "CANDIDATE"))
                    cand = VLLMBackend(adapter_path=ad)
                    ok, rate = format_canary(cand, gym)
                    from .model_backend import close_backend as _cb2
                    _cb2(cand)
                    log(f"[sleep {i}] canary parseable-ACT rate={rate:.2f} "
                        f"pass={ok}")
                    verdict = "DONE" if ok else "REJECTED_CANARY"
                    if ok and args.probe_gate:
                        cand = VLLMBackend(adapter_path=ad)
                        g_ok, g_reason, g = probe_gate(cand, sdir, i)
                        _cb2(cand)
                        log(f"[sleep {i}] gate cand={g['candidate']:.4f} "
                            f"floor={g['floor']:.4f} (base={g['base']}, "
                            f"prev={g['prev_on']}) chunks/ep "
                            f"{g['cand_chunks_per_ep']:.1f} vs "
                            f"{g['base_chunks_per_ep']} -> {g_reason}")
                        verdict = "DONE" if g_ok else f"REJECTED_{g_reason}"
                    os.rename(os.path.join(ad, "CANDIDATE"),
                              os.path.join(ad, verdict))
                model = load_model()
                bootstrap = brief()

        if i % args.probe_every == 0 or i == len(programs):
            run_probes_batch(model, gym, f"ep{i:04d}", life,
                             args.budget_ticks, log)
            if args.arm == "B" and latest_adapter(life):
                from .model_backend import close_backend
                close_backend(model)
                base = VLLMBackend(adapter_path=None)
                run_probes_batch(base, gym, f"ep{i:04d}_adapterOFF", life,
                                 args.budget_ticks, log)
                close_backend(base)
                model = load_model()

    touch(os.path.join(life, "LIFE_DONE"))
    log("[life-v2] DONE")


if __name__ == "__main__":
    main()
