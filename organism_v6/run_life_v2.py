"""Long-lifetime life runner (v6.1): batched wake, sleep-v2 compile,
rescaled cadence. One life per GPU; wake batches run concurrently.

  python -m organism_v6.run_life_v2 --life-dir ~/v6_out/L_B_seed0 --arm B \
      --seed 0 --episodes 1024 --sleep-every 32 --probe-every 64 \
      --budget-ticks 16

2026-09-10 (NEXT_EXPERIMENT_DESIGN_v1 3.6 / 3.12 / IDEAS "private reflection
time"): the runner routes episode creation, stepping, evaluation, probes, the
gate set, the canary set and the birth prompt through a Gym object
(--gym compiler|reasoning_gym; default compiler, behaviour unchanged —
tests/test_compiler_golden.py), adds PRIVATE REFLECTION time
(--reflect-every, default off), the CLONE GROUP (--clone-group, default off:
X clones = X of these processes sharing ONE adapter lineage, merged at every
sleep by clone_coordinator) and a stage schedule (--curriculum, default off:
exit criteria logged per sleep, not enforced). A life launched with today's
flags behaves identically.

Review fixes (2026-09-10, same day): split hygiene is checked by FAMILY where
the gym defines families (assert_split_hygiene); every sleep of a life outside
the deployment gym scans the child's stored prompts and notes for
deployment-gym vocabulary and refuses the sleep on a hit (target_blind_check,
design 3.6's seal rule; recorded only in a --allow-deployment-gym development
group); the sleep compiler takes its nouns from the gym (compile_vocab); the
parent's leak scan receives the gym's leak terms and the window's reference
answers (parent_leak_terms); a clone group refuses a clone without a gate set,
a mixed deployment/trait group (unless --allow-deployment-gym) and unequal
round counts; --reflect-every fires when a wake batch crosses a multiple.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys

from .gym_backend import make_gym, gym_names, DEPLOYMENT_LEAK_TERMS
from .ledger import Ledger
from .batch_loop import run_episodes_batch, EpisodeDriver, driver_class_for
from .sleep_compile import compile_sleep
from .run_life import latest_adapter, marker, touch

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE_SEED = 777  # fixed: common-random probes across checkpoints and arms


def existing_adapter_verdict(adapter_dir: str) -> str | None:
    """Return an already-final write verdict, or ``None`` before a verdict.

    ``REJECTED_*`` is just as terminal as ``DONE``.  Treating only ``DONE``
    as terminal made a resumed life retrain an old rejected sleep, then gate
    the new weights with the old candidate's cached probe.  Multiple final
    markers are evidence that this has already happened; fail loudly rather
    than silently choosing one.
    """
    if not os.path.isdir(adapter_dir):
        return None
    finals = sorted(n for n in os.listdir(adapter_dir)
                    if n == "DONE" or n.startswith("REJECTED_"))
    if len(finals) > 1:
        raise RuntimeError(f"ambiguous adapter verdicts in {adapter_dir}: "
                           f"{finals}")
    return finals[0] if finals else None


def validate_adapter_states(life_dir: str) -> None:
    """Reject ambiguous or partial write states before any model is loaded."""
    if not os.path.isdir(life_dir):
        return
    for name in sorted(os.listdir(life_dir)):
        if not name.startswith("sleep_"):
            continue
        sleep_dir = os.path.join(life_dir, name)
        ad = os.path.join(sleep_dir, "adapter")
        stage = os.path.join(sleep_dir, "adapter.train")
        final = existing_adapter_verdict(ad)
        candidate = os.path.exists(os.path.join(ad, "CANDIDATE"))
        if final is not None and candidate:
            raise RuntimeError(f"candidate and final verdict coexist: {ad}")
        if os.path.isdir(ad) and final is None and not candidate:
            raise RuntimeError(
                f"unclassified adapter directory requires inspection: {ad}")
        if os.path.exists(stage):
            if os.path.exists(ad):
                raise RuntimeError(
                    f"staging and adapter states coexist: {stage}, {ad}")
            stage_marks = [m for m in ("DONE", "CANDIDATE")
                           if os.path.exists(os.path.join(stage, m))]
            if len(stage_marks) != 1:
                raise RuntimeError(
                    f"incomplete or ambiguous staged adapter: {stage}")


def promote_trained_adapter(stage_dir: str, adapter_dir: str) -> None:
    """Atomically turn a trainer-complete staging directory into a candidate.

    The trainer owns ``stage_dir/DONE``; the life runner owns every final
    marker under ``adapter_dir``.  Keeping those namespaces separate removes
    the crash window in which a trainer's completion marker could be mistaken
    for a gate-approved write.
    """
    done = os.path.join(stage_dir, "DONE")
    candidate = os.path.join(stage_dir, "CANDIDATE")
    if os.path.exists(done) and os.path.exists(candidate):
        raise RuntimeError(f"ambiguous staged adapter markers: {stage_dir}")
    if not os.path.exists(done) and not os.path.exists(candidate):
        raise RuntimeError(f"trainer completed without DONE: {stage_dir}")
    if os.path.exists(adapter_dir):
        raise RuntimeError(f"refusing to overwrite adapter candidate: "
                           f"{adapter_dir}")
    if os.path.exists(done):
        os.rename(done, candidate)
    os.rename(stage_dir, adapter_dir)


def format_canary(model, gym, threshold: float = 0.5) -> tuple[bool, float]:
    """Post-sleep motor-channel check in the REAL gym context: run the gym's
    canary set (compiler: 4 probe programs) for 3 chunks each with the real
    birth prompt and count chunks that contain a PARSEABLE canonical ACT
    (the thing that actually breaks). Measured 2026-09-07: a
    synthetic-prompt canary passed while the adapter emitted only '### ACT:'
    in gym context."""
    import re as _re
    led = Ledger(os.devnull)
    boot = gym.birth_prompt()
    cls = driver_class_for(gym)
    drivers = [cls(gym.episode_from_id(b, 3), boot, gym, led, budget_ticks=3)
               for b in gym.canary_set()]
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
    """eids=None → the gym's exam set (compiler: the 8 report-panel
    programs). A different list is used for the gate panel (--gate-panel,
    2026-09-10, review F1): the gate must not select on the programs whose
    scores the paper reports. Gyms with families (reasoning_gym) also get a
    per-family accuracy block in the probe file."""
    out_path = os.path.join(life_dir, f"probe_{tag}.json")
    if marker(out_path):
        return
    led = Ledger(os.path.join(life_dir, f"probe_{tag}.ledger.jsonl"))
    eids = list(eids) if eids else list(gym.exam_set())
    res = run_episodes_batch(model, gym, [gym.episode_from_id(b, budget)
                                         for b in eids],
                             gym.birth_prompt(), led, budget, log,
                             gen_seed=PROBE_SEED,
                             driver_cls=driver_class_for(gym))
    results = {r["episode_id"]: r["best_score"] for r in res}
    payload = dict(tag=tag, results=results,
                   mean=sum(results.values()) / len(results))
    if getattr(gym, "reports_family_accuracy", False):
        payload["family_accuracy"] = gym.family_accuracy(results)
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=1)
    os.rename(tmp, out_path)
    log(f"[probe {tag}] mean={sum(results.values()) / len(results):.4f}"
        + (f" families={payload['family_accuracy']}"
           if "family_accuracy" in payload else ""))


def assert_split_hygiene(gym, rows) -> None:
    """Design 3.6: no gate or exam id may ever appear in the life ledger.
    Gyms whose splits are FAMILIES (reasoning_gym: split_of(eid) classifies
    any id by family and seed range) are checked at the family level — an
    exam-family item with an unlisted seed is as forbidden as a listed one —
    and the canary items are held out too; the fixed-id check is the rule for
    gyms without split_of (the compiler gym)."""
    held = set(gym.exam_set()) | set(gym.gate_set() or [])
    held |= {h.replace("benchmark://", "") for h in held}
    seen = {r.get("episode_id") for r in rows
            if r.get("kind") in ("act", "thought", "note", "note_after")}
    bad = sorted(e for e in seen if e and (e in held or
                                         e.replace("benchmark://", "") in held))
    split_of = getattr(gym, "split_of", None)
    if callable(split_of):
        for e in sorted(x for x in seen if x):
            try:
                sp = split_of(e)
            except ValueError:            # not one of this gym's ids
                continue
            if sp in ("exam", "gate", "canary") and e not in bad:
                bad.append(f"{e} ({sp} family)")
    if bad:
        raise RuntimeError(f"split hygiene violated: held-out ids in the life "
                           f"ledger: {bad[:5]}")


_LEAK_TEXT_KINDS = ("thought", "note", "reflection", "note_after")


def deployment_leak_regex(terms=None):
    """Whole-token, case-insensitive matcher for the deployment gym's
    vocabulary (gym_backend.DEPLOYMENT_LEAK_TERMS)."""
    ts = sorted({str(t) for t in (terms or DEPLOYMENT_LEAK_TERMS) if t},
                key=len, reverse=True)
    return re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(t) for t in ts)
                      + r")(?![A-Za-z0-9_])", re.I)


def leak_scan_ledger(rows, terms=None, since: int = 0) -> dict:
    """Design 3.6 seal scan over every stored prompt and note of the child
    (rows[since:]): {n_rows, n_hit_rows, hits: {term: count}}. Zero hits is
    the target-blindness condition of a childhood life."""
    rx = deployment_leak_regex(terms)
    hits: dict = {}
    hit_rows = 0
    for r in rows[since:]:
        if r.get("kind") not in _LEAK_TEXT_KINDS:
            continue
        found = rx.findall(f"{r.get('prompt') or ''}\n{r.get('note') or ''}\n"
                           f"{r.get('text') or ''}")
        if found:
            hit_rows += 1
            for t in found:
                hits[t.lower()] = hits.get(t.lower(), 0) + 1
    return dict(n_rows=len(rows), n_hit_rows=hit_rows, hits=hits)


def target_blind_check(gym, rows, life_dir, r, log, enforce=True) -> dict:
    """At every sleep of a life OUTSIDE the deployment gym: scan the child's
    stored prompts and notes for deployment-gym vocabulary, append the result
    to <life>/leak_scan.jsonl and, when `enforce`, refuse the sleep on any
    hit (RuntimeError) — the seal rule of design 3.6. Incremental: rows
    already scanned clean are not re-read; a failing scan does not advance
    the cursor, so a restart fails again. The deployment gym itself is
    'not applicable' (its own vocabulary is the child's job)."""
    applicable = not str(gym.exposure_domain()).startswith("compiler_gym")
    if not applicable:                  # the deployment gym: nothing written
        return dict(round=r, applicable=False, clean=True)
    path = os.path.join(life_dir, "leak_scan.jsonl")
    prev = []
    if os.path.exists(path):
        for line in open(path):
            try:
                prev.append(json.loads(line))
            except ValueError:
                continue
    if any(p.get("round") == r and p.get("clean") for p in prev):
        return prev[-1]
    since = max([int(p.get("scanned_rows", 0)) for p in prev if p.get("clean")]
                or [0])
    res = leak_scan_ledger(rows, since=since)
    clean = not res["hits"]
    rec = dict(round=r, applicable=True, enforced=bool(enforce),
               scanned_from=since, scanned_rows=len(rows) if clean else since,
               n_hit_rows=res["n_hit_rows"], hits=res["hits"], clean=clean)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    log(f"[leak-scan round {r}] rows {since}-{len(rows)}: "
        f"{'clean' if clean else 'HITS ' + json.dumps(res['hits'])}"
        + ("" if enforce else " (recorded, not enforced)"))
    if enforce and not clean:
        raise RuntimeError(
            f"target-blindness violated: deployment-gym vocabulary in the "
            f"child's stored prompts/notes at sleep {r}: {sorted(res['hits'])[:8]} "
            f"({res['n_hit_rows']} rows); see {path}")
    return rec


def parent_leak_terms(gym, rows, window: int = 32) -> list:
    """What the parent must never utter for THIS gym: the gym's leak terms
    (held-out ids / families and labels) plus the reference answers of the
    episodes played in the recent window (gyms with answer_terms). Scanned
    as exact substrings by parent_backend.leak_scan(exact_terms=...)."""
    terms = [str(t) for t in (gym.leak_terms() or []) if t]
    answer_terms = getattr(gym, "answer_terms", None)
    if callable(answer_terms):
        eids = []
        for r in reversed(rows):
            if r.get("kind") == "act" and r.get("episode_id") not in eids:
                eids.append(r.get("episode_id"))
                if len(eids) >= window:
                    break
        for eid in eids:
            try:
                for a in answer_terms(gym.episode_from_id(eid)):
                    if a and len(str(a).strip()) >= 4:
                        terms.append(str(a).strip())
            except Exception:  # noqa: BLE001 — an unbuildable id is not a leak
                continue
    return list(dict.fromkeys(terms))


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
    ap.add_argument("--train-seed", type=int, default=None,
                    help="explicit optimizer/LoRA initialization seed for new "
                         "experiments; omitted preserves the historical recipe")
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
    # --- 2026-09-10: gym protocol, reflection time, clone group, curriculum
    ap.add_argument("--gym", choices=gym_names(), default="compiler",
                    help="the Gym the life lives in (gym_backend registry). "
                         "Default compiler = today's behaviour, unchanged. "
                         "reasoning_gym = organism_v6/reasoning_gym_gym.py "
                         "(pip reasoning-gym==0.1.25 on the node).")
    ap.add_argument("--reflect-every", type=int, default=0,
                    help="PRIVATE REFLECTION time every N episodes (after "
                         "the wake batch that reaches N): the child reads a "
                         "short summary of its own recent ledger and writes "
                         "freely for --reflect-ticks chunks — no task, no "
                         "score, no parent; rows kind='reflection' enter the "
                         "sleep corpus like any other thought. Default 0 = "
                         "off (existing arms unchanged).")
    ap.add_argument("--reflect-ticks", type=int, default=4,
                    help="chunks per reflection (with --reflect-every)")
    ap.add_argument("--clone-group", default=None,
                    help="CLONE GROUP directory: X clones = X run_life_v2 "
                         "processes (each its own GPU, each possibly another "
                         "--gym) sharing ONE adapter lineage; at every sleep "
                         "the clones' ledger slices are pooled, compiled and "
                         "trained ONCE by the coordinator, gated on EVERY "
                         "clone's gym gate set, and reloaded by all (see "
                         "clone_coordinator.py). Requires --arm B. Default "
                         "None = a single life, unchanged.")
    ap.add_argument("--clone-id", type=int, default=0,
                    help="this clone's id k in [0, --clone-count)")
    ap.add_argument("--clone-count", type=int, default=1,
                    help="X, the number of clones in the group")
    ap.add_argument("--clone-coordinator", type=int, default=0,
                    help="which clone compiles, trains and gates (default 0)")
    ap.add_argument("--clone-barrier-timeout", type=float, default=7200.0,
                    help="seconds the coordinator waits at the sleep barrier "
                         "for every clone's slice; a clone later than this is "
                         "SKIPPED for the round (logged) and the round still "
                         "completes")
    ap.add_argument("--clone-round-timeout", type=float, default=10800.0,
                    help="seconds a non-coordinator clone waits for the "
                         "round's verdict before continuing with its current "
                         "adapter (logged; the round is attached at the next "
                         "sleep once its verdict exists)")
    ap.add_argument("--allow-deployment-gym", action="store_true",
                    help="DEVELOPMENT ONLY: let a compiler (deployment-gym) "
                         "clone share a group with trait-gym clones. The "
                         "group manifest is labelled not_target_blind and the "
                         "per-sleep deployment-vocabulary scan of the trait "
                         "clones is recorded instead of enforced. Default off: "
                         "such a group is refused at registration.")
    ap.add_argument("--curriculum", default=None,
                    help="stage schedule JSON (organism_v6/curriculum.py; e.g. "
                         "organism_v6/curriculum_schedule_v1.json): per-stage "
                         "gym shares set this clone's episodes per round "
                         "(shares[gym] x --wake-batch instead of "
                         "--sleep-every) and the stage's exit criteria are "
                         "computed and LOGGED at every sleep to "
                         "<life>/curriculum_exit.jsonl (not enforced). "
                         "Default None = --sleep-every, unchanged.")
    # --- 2026-09-12: level-3 "preschool for records" (THESIS_v2 section 7, Astra
    # memo q14; organism_v6/preschool.py). Every flag defaults OFF; a life
    # launched without them is byte-identical (tests/test_preschool_flags.py).
    ap.add_argument("--note-after", action="store_true",
                    help="the post-outcome slot: after every measured ACT the "
                         "child is shown the execution's measured facts and "
                         "writes ONE short NOTE_AFTER (ledger kind note_after, "
                         "tied to the execution id); the head of context gains "
                         "exactly one sentence saying the field exists. Default "
                         "off.")
    ap.add_argument("--note-after-max-tokens", type=int, default=100,
                    help="generation cap of the NOTE_AFTER turn (default 100)")
    ap.add_argument("--artifact-lesson", choices=["none", "lesson", "lesson10", "sham"],
                    default="none",
                    help="the parent's artifact-naming paragraph (a MEASURED "
                         "ACTION RECORD) with three synthetic examples before "
                         "episode 1 and a one-line refresher with one new "
                         "example after sleeps 1-3; lesson10 adds the numbered "
                         "baseline paragraph (aim for 10 records per episode); "
                         "sham = the ACTIVE control: the same schedule, register "
                         "and length (word count within 5%%) with no artifact "
                         "content, only generic remarks about the task "
                         "(preschool.SHAM_VERSION). Fixed text "
                         "(preschool.LESSON_VERSION), never a score. Default none.")
    ap.add_argument("--articulation-gate", choices=["off", "shadow", "enforce"],
                    default="off",
                    help="judge every new note_after at sleep with the "
                         "retrospective audit's tests (G/N/F/D/P) and log the "
                         "counts to <sleep>/articulation_shadow.json; shadow "
                         "leaves the corpus untouched; enforce replaces the "
                         "corpus with the admitted records to date (legacy kept "
                         "as corpus_legacy.json) and SKIPS training when fewer "
                         "than --gate-min-items are admitted. Default off.")
    ap.add_argument("--gate-min-items", type=int, default=64,
                    help="enforce mode: admitted records needed to train at a "
                         "sleep (Astra q14 section 3 promotion rule); fewer => "
                         "the sleep is skipped, the adapter stays")
    ap.add_argument("--neutral-probes", action="store_true",
                    help="one held-out probe episode immediately before and "
                         "after every sleep (same program for the pair), fresh "
                         "context, optional Scratchpad field, separate ledger "
                         "(never harvested, never seen by a parent); results "
                         "in <life>/neutral_probe_<pre|post>_<episode>.json. "
                         "Default off.")
    ap.add_argument("--neutral-probe-panel", default=None,
                    help="JSON list of held-out benchmark URIs for the neutral "
                         "probes (e.g. the disjoint panel); default: "
                         "preschool.NEUTRAL_PANEL_DEFAULT")
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

    # the gate panel (disjoint from the report panel) is part of the gym: the
    # gym constructor performs the overlap check that used to live here
    gate_panel_list = None
    if args.gate_panel:
        gate_panel_list = json.load(open(os.path.expanduser(args.gate_panel)))
    gym = make_gym(args.gym, gate_panel=gate_panel_list)
    programs = gym.training_schedule(args.episodes, args.seed)
    log(f"[life-v2] arm={args.arm} seed={args.seed} n={len(programs)} "
        f"sleep_every={args.sleep_every} probe_every={args.probe_every}")

    # preschool flags (all default off): the post-outcome slot object, the
    # lesson phase and the neutral-probe panel; nothing below changes a life
    # that does not set them
    preschool_on = (args.note_after or args.artifact_lesson != "none"
                    or args.articulation_gate != "off" or args.neutral_probes)
    slot = None
    neutral = None
    phase = {"sleeps": 0}            # sleeps completed so far (lesson phase)
    if preschool_on:
        from . import preschool
        if args.note_after:
            slot = preschool.PostOutcomeSlot(max_tokens=args.note_after_max_tokens,
                                             log=log)
        if args.neutral_probes:
            neutral = preschool.neutral_panel(args.neutral_probe_panel)
            _c = lambda s: str(s).replace("benchmark://", "")   # noqa: E731
            clash = sorted(n for n in neutral if _c(n) in {_c(p) for p in programs})
            if clash:
                raise SystemExit(f"--neutral-probes: panel programs appear in the "
                                 f"training schedule: {clash[:4]}")
        log(f"[preschool] note_after={args.note_after} "
            f"max_tokens={args.note_after_max_tokens} lesson={args.artifact_lesson} "
            f"gate={args.articulation_gate} min_items={args.gate_min_items} "
            f"neutral_probes={args.neutral_probes} "
            f"panel={len(neutral) if neutral else 0} version={preschool.LESSON_VERSION}")

    schedule = None
    if args.curriculum:
        from . import curriculum
        schedule = curriculum.load_schedule(args.curriculum)
    group = None
    if args.clone_group:
        if args.train_seed is not None:
            raise SystemExit("--train-seed is not yet supported for clone groups")
        if args.arm != "B":
            raise SystemExit("--clone-group needs --arm B (one shared adapter "
                             "lineage)")
        from .clone_coordinator import CloneGroup, coordinate_round, \
            probe_summary, ProvenanceLedger, _sha as _file_sha
        from . import curriculum as _cu
        group = CloneGroup(args.clone_group, args.clone_id, args.clone_count,
                           coordinator_id=args.clone_coordinator, log=log)
        # flags go into a hashed, mirrored manifest: no paths, URLs or hosts
        flags = {k: v for k, v in vars(args).items() if "key" not in k.lower()}
        for fk in ("gate_panel", "curriculum"):
            if flags.get(fk):
                flags[fk + "_sha256"] = _file_sha(os.path.expanduser(flags[fk]))
                flags[fk] = "<file>"
        for fk in ("parent_url", "life_dir", "clone_group"):
            if flags.get(fk):
                flags[fk] = "<set>"
        n_rounds = _cu.count_rounds(schedule, gym.name, len(programs),
                                    args.wake_batch, args.sleep_every)
        group.register(gym=gym.name, life_dir=life, gate_set=gym.gate_set(),
                       exam_set=gym.exam_set(), canary_set=gym.canary_set(),
                       budget_ticks=args.budget_ticks, seed=args.seed,
                       arm=args.arm, exposure_domain=gym.exposure_domain(),
                       rank=args.rank, schedule=schedule, n_rounds=n_rounds,
                       compile_vocab=gym.compile_vocab(),
                       allow_deployment_gym=bool(args.allow_deployment_gym),
                       reasoning_gym_version=getattr(gym, "package_version", None),
                       flags=flags)
        log(f"[life-v2] clone {args.clone_id}/{args.clone_count} "
            f"coordinator={group.is_coordinator} rounds={n_rounds} "
            f"group={group.dir}")

        def preflight_group_gyms():
            """The coordinator must be able to build EVERY registered clone's
            gym (it gates on each): fail here, not at the first gate."""
            for k, s in sorted(group.clone_specs().items()):
                try:
                    make_gym(s["gym"], gate_panel=s.get("gate_set"))
                except Exception as e:  # noqa: BLE001
                    raise RuntimeError(f"coordinator cannot build clone {k}'s "
                                       f"gym {s['gym']!r}: {e}") from e
        if group.is_coordinator:
            preflight_group_gyms()
    if args.gym != "compiler" or group is not None or args.reflect_every or schedule:
        log(f"[life-v2] gym={gym.name} exposure={gym.exposure_domain()} "
            f"reflect_every={args.reflect_every} curriculum="
            f"{schedule['name'] if schedule else None}")
    if group is not None or gym.name != "compiler":
        from .clone_coordinator import ProvenanceLedger
        ledger = ProvenanceLedger(os.path.join(life, "ledger.jsonl"),
                                  clone_id=args.clone_id if group else None,
                                  gym=gym.name,
                                  exposure_domain=gym.exposure_domain())
    else:
        ledger = Ledger(os.path.join(life, "ledger.jsonl"))

    from .model_backend import VLLMBackend
    loaded = {"adapter": None}          # the adapter the live model carries

    def load_model():
        ad = latest_adapter(life) if args.arm == "B" else None
        loaded["adapter"] = ad
        return VLLMBackend(adapter_path=ad)

    def open_base():
        """The frozen base for an adapter-OFF arm of a preschool neutral probe:
        exactly the ordinary probe_ep*_adapterOFF path below (close the live
        model, open VLLMBackend(adapter_path=None))."""
        from .model_backend import close_backend
        close_backend(model)
        return VLLMBackend(adapter_path=None)

    def close_base(base):
        """Close the base opened by open_base and reload the live model."""
        from .model_backend import close_backend
        close_backend(base)
        return load_model()

    def parent_terms():
        return parent_leak_terms(gym, ledger.rows(), args.sleep_every)

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
                    return gym.birth_prompt() + \
                        "\n=== YOUR BRIEFING FROM LAST SLEEP ===\n" + t + \
                        ("\n\n=== YOUR PARENT, ON HOW YOU HAVE BEEN THINKING"
                         " ===\n" + parent_txt if parent_txt else "")
        return gym.birth_prompt()

    def head():
        """The head of context for the wake batches: brief() as always, plus
        (preschool flags only) the one slot sentence and the lesson block of
        the current phase. Identical to brief() when the flags are off."""
        b = brief()
        if not preschool_on:
            return b
        from . import preschool
        if args.note_after:
            b = b + "\n" + preschool.SLOT_SENTENCE
        lb = preschool.deliver_lesson(life, args.artifact_lesson, phase["sleeps"], log)
        if lb:
            b = b + "\n" + lb
        return b

    def probe_stats(tag):
        """(mean, chunks per episode) of a finished probe, or (None, None)."""
        p = os.path.join(life, f"probe_{tag}.json")
        if not os.path.exists(p):
            return None, None
        pj = json.load(open(p))
        mean = pj["mean"]
        n_eps = len(pj.get("results") or []) or len(gym.exam_set())
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

    # the gate set comes from the gym: the disjoint panel when given (or the
    # reasoning gym's fixed held-out families); None = legacy gate on the
    # report panel
    gate_panel = gym.gate_set()

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

    # ----------------------------------------------------------------------
    # clone group: the coordinator's gate over EVERY clone's gym, and the
    # per-clone sleep (slice -> barrier -> one write -> reload)
    # ----------------------------------------------------------------------
    gpu = {"model": None, "closed": False}

    def group_gate(adapter_dir, specs, r):
        """Commit rule (documented in clone_coordinator): the write commits
        only if EVERY registered clone passes on ITS OWN gym — the parseable-
        ACT canary, score >= floor - tol on that clone's gate set (floor =
        max(frozen base on that gate set, best committed round's probe on
        it)), and brevity: chunks/episode >= gate_brevity x base on that
        clone's chunks. Rejections name the failing clone(s)."""
        from .model_backend import close_backend
        if not gpu["closed"]:
            close_backend(gpu["model"])
            gpu["closed"] = True
        rd = group.round_dir(r)
        gyms = {k: make_gym(s["gym"], gate_panel=s.get("gate_set"))
                for k, s in sorted(specs.items())}
        for k, g in gyms.items():
            if not g.gate_set():
                # registration refuses this; never fall back to the exam set
                raise RuntimeError(f"clone {k} ({g.name}) has no gate set; the "
                                   f"group gate never selects on the exam panel")
        missing = [k for k in gyms if not marker(
            os.path.join(group.dir, f"probe_gate_base_clone{k}.json"))]
        if missing:                       # frozen-base floors, once per gym
            base = VLLMBackend(adapter_path=None)
            for k in missing:
                g = gyms[k]
                run_probes_batch(base, g, f"gate_base_clone{k}", group.dir,
                                 specs[k]["budget_ticks"], log,
                                 eids=g.gate_set())
            close_backend(base)
        cand = VLLMBackend(adapter_path=adapter_dir)
        per, reasons = {}, []
        for k, g in gyms.items():
            c_ok, rate = format_canary(cand, g)
            st = dict(gym=g.name, canary_rate=rate, canary_ok=c_ok)
            if not c_ok:
                reasons.append(f"CANARY_clone{k}")
                per[str(k)] = st
                continue
            tag = f"gate{r:04d}_clone{k}"
            run_probes_batch(cand, g, tag, rd, specs[k]["budget_ticks"], log,
                             eids=g.gate_set())
            c_mean, c_cpe = probe_summary(rd, tag)
            b_mean, b_cpe = probe_summary(group.dir, f"gate_base_clone{k}")
            prev = []
            for rr in group.committed_rounds(upto=r - 1):
                pc = ((group.read_record(rr) or {}).get("gate") or {}) \
                    .get("per_clone", {}).get(str(k), {})
                if isinstance(pc.get("candidate"), (int, float)):
                    prev.append(pc["candidate"])
            prev_on = max(prev) if prev else None
            cands = [x for x in (b_mean, prev_on) if x is not None]
            floor = max(cands) if cands else 0.0
            score_ok = c_mean >= floor - args.gate_tol
            brev_ok = (b_cpe is None) or (c_cpe >= args.gate_brevity * b_cpe)
            st.update(candidate=c_mean, base=b_mean, prev_on=prev_on,
                      floor=floor, tol=args.gate_tol, cand_chunks_per_ep=c_cpe,
                      base_chunks_per_ep=b_cpe, score_ok=score_ok,
                      brevity_ok=brev_ok)
            if not score_ok:
                reasons.append(f"SCORE_clone{k}")
            if not brev_ok:
                reasons.append(f"BREVITY_clone{k}")
            per[str(k)] = st
            log(f"[clone-group round {r}] gate clone{k}/{g.name} cand="
                f"{c_mean:.4f} floor={floor:.4f} chunks/ep {c_cpe:.1f} vs "
                f"{b_cpe} -> {'OK' if score_ok and brev_ok else 'FAIL'}")
        close_backend(cand)
        return dict(ok=not reasons, reason="+".join(reasons) or "OK",
                    per_clone=per,
                    rule="every registered clone: canary + score >= floor - "
                         "tol on its own gym gate set + brevity on its own "
                         "chunks")

    def clone_sleep(i, sdir, r):
        nonlocal model, bootstrap
        os.makedirs(sdir, exist_ok=True)
        # a round whose verdict arrived after this clone's timeout is
        # attached first, so the lineage converges (no fork after a REJECTED
        # round that follows a missed DONE)
        late = group.attach_missed_rounds(life)
        if late:
            log(f"[clone {args.clone_id}] attached late rounds "
                f"{[(rr, v) for rr, v, _d in late]}")
        n = group.write_slice(r, ledger.rows(), gym.name,
                              gym.exposure_domain())
        log(f"[clone {args.clone_id} round {r}] slice rows={n} (at episode {i})")
        gpu["model"], gpu["closed"] = model, False
        if group.is_coordinator:
            preflight_group_gyms()

            def compile_fn(rows, out_dir, prior):
                # every clone registered its gym's compile vocabulary: rows
                # resolve theirs per `gym` field (mixed pools get neutral
                # THINK prompts); this clone's is the default
                vb = {s["gym"]: s["compile_vocab"]
                      for s in group.clone_specs().values()
                      if s.get("compile_vocab")}
                return compile_sleep(model, rows, out_dir, prior,
                                     vocab=gym.compile_vocab(), vocab_by_gym=vb)

            def train_fn(corpus_path, out_dir):
                from .model_backend import close_backend
                if not gpu["closed"]:
                    if not close_backend(gpu["model"]):
                        raise RuntimeError("GPU did not free before training "
                                           "— refusing to train into OOM")
                    gpu["closed"] = True
                pm_ = plasticity_multiplier()
                lr_ = args.base_lr * pm_
                cmd = [sys.executable, "-m", "organism_v6.train_adapter",
                       "--corpus", corpus_path, "--out", out_dir,
                       "--rank", str(args.rank)]
                if args.plasticity:
                    cmd += ["--lr", str(lr_)]
                rc = subprocess.run(cmd, cwd=os.path.dirname(HERE)).returncode
                log(f"[clone-group round {r}] train rc={rc} "
                    f"plasticity={pm_:.2f} lr={lr_:g}")
                return rc

            def gate_fn(adapter_dir, specs):
                return group_gate(adapter_dir, specs, r)

            verdict = coordinate_round(group, r, compile_fn, train_fn, gate_fn,
                                       args.clone_barrier_timeout, log)
        else:
            verdict = group.wait_for_verdict(r, args.clone_round_timeout)
        group.advance_cursor_if_pooled(r)
        group.attach_round_to_life(r, life, sdir)
        log(f"[clone {args.clone_id} round {r}] verdict={verdict} "
            f"adapter={latest_adapter(life)}")
        if parent_fn is not None:
            pm = parent_fn(life, ledger.rows(), sdir, args.parent_url,
                           args.parent_model, args.sleep_every,
                           extra_leak_terms=parent_terms())
            log(f"[sleep {i}] parent ritual={pm['metrics'].get('ritual')} "
                f"flags={pm['metrics'].get('flags')} "
                f"intervened={pm['intervened']} hits={pm['hits']}")
        # reload when the model was closed for training or when the best
        # committed adapter changed (this round's, or a late-attached one)
        if gpu["closed"] or latest_adapter(life) != loaded["adapter"]:
            from .model_backend import close_backend
            if not gpu["closed"]:
                close_backend(model)
            model = load_model()
        bootstrap = head()
        return verdict

    def round_length(r):
        if schedule is None:
            return args.sleep_every
        from . import curriculum
        return curriculum.round_length(schedule, r, gym.name, args.wake_batch,
                                       args.sleep_every)

    # A corrupt historical marker must fail before latest_adapter() can mount
    # an ungated trainer-DONE or before probes/wake work mutate the life.
    validate_adapter_states(life)
    model = load_model()
    bootstrap = head()
    run_probes_batch(model, gym, "ep0000", life, args.budget_ticks, log)
    if gate_panel and not latest_adapter(life) and group is None:
        # base on the gate panel, once, with the same seeded generation (in a
        # clone group the coordinator measures the per-clone floor itself)
        run_probes_batch(model, gym, "gate_base", life, args.budget_ticks, log,
                         eids=gate_panel)
    if args.reflect_every > 0 and args.reflect_every % args.wake_batch:
        log(f"[life-v2] reflect_every={args.reflect_every} is not a multiple "
            f"of wake_batch={args.wake_batch}: reflection fires at the end of "
            f"the wake batch that crosses each multiple")
    target_blind_enforced = group is None or \
        not group.manifest().get("not_target_blind")

    i = 0
    r = 0                      # sleeps so far = the clone group's round index
    next_sleep_at = round_length(1)
    reflect_since = 0          # ledger rows already summarized in a reflection
    while i < len(programs):
        batch_start = i
        batch_end = min(i + args.wake_batch, len(programs))
        bm = os.path.join(life, f"wake_{i:04d}_{batch_end:04d}.json")
        if not marker(bm):
            eps = [gym.episode_from_id(p, args.budget_ticks)
                   for p in programs[i:batch_end]]
            res = run_episodes_batch(model, gym, eps, bootstrap, ledger,
                                     args.budget_ticks, log,
                                     gen_seed=1000 + args.seed,
                                     driver_cls=driver_class_for(gym),
                                     note_after=slot)
            tmp = bm + ".tmp"
            with open(tmp, "w") as f:
                json.dump(res, f)
            os.rename(tmp, bm)
        i = batch_end

        # fires when the batch crosses a multiple of --reflect-every (equal
        # to `i % N == 0` whenever N is a multiple of --wake-batch)
        if args.reflect_every > 0 and \
                i // args.reflect_every > batch_start // args.reflect_every:
            rm = os.path.join(life, f"reflect_{i:04d}.json")
            if marker(rm):
                reflect_since = json.load(open(rm)).get("rows_after", reflect_since)
            else:
                from .reflection import run_reflection
                rows_now = ledger.rows()
                written = run_reflection(model, gym.birth_prompt(), ledger,
                                         rows_now, reflect_since, i,
                                         args.reflect_ticks,
                                         seed=2000 + args.seed, log=log)
                rec = dict(at_episode=i, n_chunks=len(written),
                           rows_before=len(rows_now),
                           rows_after=len(rows_now) + len(written))
                tmp = rm + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(rec, f)
                os.rename(tmp, rm)
                reflect_since = rec["rows_after"]

        if schedule is None:
            sleep_now = i % args.sleep_every == 0 or i == len(programs)
        else:
            sleep_now = i >= next_sleep_at or i == len(programs)
        if sleep_now:
            r += 1
            sdir = os.path.join(life, f"sleep_{i:04d}")
            if neutral is not None:          # preschool: the pre-sleep neutral probe (adapter ON / OFF pair)
                _, model = preschool.neutral_probe(model, gym, life, "pre", i, r, neutral,
                                                   args.budget_ticks, log, loaded["adapter"],
                                                   max_tokens=args.note_after_max_tokens,
                                                   driver_cls=driver_class_for(gym),
                                                   open_base=open_base, close_base=close_base)
            assert_split_hygiene(gym, ledger.rows())
            # design 3.6 seal rule at every sleep of a childhood life: zero
            # deployment-gym vocabulary in the child's stored prompts/notes
            target_blind_check(gym, ledger.rows(), life, r, log,
                               enforce=target_blind_enforced)
            if group is not None:
                clone_sleep(i, sdir, r)
            else:
                if not marker(os.path.join(sdir, "COMPILED")):
                    prior = []
                    for d in sorted(os.listdir(life)):
                        cp = os.path.join(life, d, "corpus.json")
                        if (d.startswith("sleep_") and
                                d != os.path.basename(sdir) and
                                os.path.exists(cp)):
                            prior = json.load(open(cp))["corpus"]
                    rr = compile_sleep(model, ledger.rows(), sdir, prior,
                                       vocab=gym.compile_vocab(),
                                       vocab_by_gym={gym.name: gym.compile_vocab()})
                    log(f"[sleep {i}] new={rr['n_new']} "
                        f"principles={rr['n_principles']}")
                    if args.articulation_gate != "off":   # preschool gate (shadow|enforce)
                        preschool.gate_sleep(ledger.rows(), life, sdir,
                                             args.articulation_gate,
                                             min_items=args.gate_min_items, log=log,
                                             slot_stats=slot.stats() if slot else None)
                    touch(os.path.join(sdir, "COMPILED"))
                if parent_fn is not None:
                    pm = parent_fn(life, ledger.rows(), sdir, args.parent_url,
                                   args.parent_model, args.sleep_every,
                                   extra_leak_terms=parent_terms())
                    log(f"[sleep {i}] parent ritual={pm['metrics'].get('ritual')} "
                        f"flags={pm['metrics'].get('flags')} "
                        f"intervened={pm['intervened']} hits={pm['hits']}")
                if args.articulation_gate == "enforce" and \
                        preschool.training_skipped(sdir):
                    log(f"[sleep {i}] training SKIPPED: too few admitted records "
                        f"(preschool gate enforce, min {args.gate_min_items}); "
                        f"adapter unchanged")
                elif args.arm == "B":
                    from .model_backend import close_backend
                    ad = os.path.join(sdir, "adapter")
                    stage = os.path.join(sdir, "adapter.train")
                    final = existing_adapter_verdict(ad)
                    candidate = os.path.exists(os.path.join(ad, "CANDIDATE"))
                    wake_closed = False
                    if final is not None and candidate:
                        raise RuntimeError(
                            f"candidate and final verdict coexist: {ad}")
                    if os.path.isdir(ad) and final is None and not candidate:
                        raise RuntimeError(
                            f"unclassified adapter directory requires "
                            f"inspection: {ad}")
                    if os.path.exists(stage) and (final is not None or candidate):
                        raise RuntimeError(
                            f"staging and adapter states coexist: {stage}, {ad}")
                    if final is None and not candidate:
                        if os.path.exists(stage):
                            # A complete staged fit is safe to promote after a
                            # crash.  Any other partial state is deliberately
                            # manual: never train over unknown bytes.
                            if (os.path.exists(os.path.join(stage, "DONE")) or
                                    os.path.exists(os.path.join(
                                        stage, "CANDIDATE"))):
                                promote_trained_adapter(stage, ad)
                                candidate = True
                            else:
                                raise RuntimeError(
                                    f"incomplete staged adapter requires "
                                    f"inspection: {stage}")
                        else:
                            if not close_backend(model):
                                raise RuntimeError(
                                    "GPU did not free before training — "
                                    "refusing to train into OOM")
                            wake_closed = True
                            pm_ = plasticity_multiplier()
                            lr_ = args.base_lr * pm_
                            train_cmd = [
                                sys.executable, "-m", "organism_v6.train_adapter",
                                "--corpus", os.path.join(sdir, "corpus.json"),
                                "--out", stage, "--rank", str(args.rank)]
                            if args.plasticity:
                                train_cmd += ["--lr", str(lr_)]
                            if args.train_seed is not None:
                                train_cmd += ["--seed", str(args.train_seed)]
                            rc = subprocess.run(
                                train_cmd, cwd=os.path.dirname(HERE)).returncode
                            log(f"[sleep {i}] train rc={rc} "
                                f"plasticity={pm_:.2f} lr={lr_:g}")
                            if rc != 0:
                                raise RuntimeError(
                                    f"sleep {i} adapter training failed rc={rc}")
                            promote_trained_adapter(stage, ad)
                            candidate = True
                    if candidate:
                        if not wake_closed and not close_backend(model):
                            raise RuntimeError(
                                "GPU did not free before resumed candidate "
                                "gate")
                        wake_closed = True
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
                    if candidate:
                        model = load_model()
                        bootstrap = head()
            if preschool_on:
                # the lesson phase advances with the sleep count (refreshers
                # after sleeps 1-3, nothing from sleep 4); the head of context
                # is rebuilt so a life without training (arm A, a skipped or
                # resumed sleep) still receives the phase's text
                phase["sleeps"] = r
                bootstrap = head()
                if slot is not None:
                    log(f"[preschool slot] {json.dumps(slot.stats())}")
            if neutral is not None:              # the post-sleep neutral probe (adapter ON / OFF pair)
                _, model = preschool.neutral_probe(model, gym, life, "post", i, r, neutral,
                                                   args.budget_ticks, log, loaded["adapter"],
                                                   max_tokens=args.note_after_max_tokens,
                                                   driver_cls=driver_class_for(gym),
                                                   open_base=open_base, close_base=close_base)
            if schedule is not None:
                from . import curriculum
                curriculum.log_exit_check(life, r, schedule, ledger.rows(),
                                          wake_batch=args.wake_batch,
                                          family_of=gym.family_of, log=log)
                next_sleep_at = i + round_length(r + 1)

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
    if group is not None:
        group.mark_life_done()      # the barrier stops expecting this clone
    log("[life-v2] DONE")


if __name__ == "__main__":
    main()
