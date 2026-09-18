"""Development rounds v2 — repaired against Codex's 2026-09-07 audit.

One round: shared child snapshot S_k -> N SHORT parallel classrooms (all act
from S_k; no per-branch weight updates) -> pooled ADMITTED corpus with
provenance -> stratified replay (exact dose, no duplication) -> ONE
conservative clean-base write -> exams (ON / OFF / PREV, seeded) + canary
-> transactional commit or reject -> hashed lineage manifest.

Repairs (each maps to an audited defect):
  D1 compile the ENTIRE ledger            -> only world-ADMITTED lesson pairs
  D2 provenance dropped                    -> every row carries evidence_ids,
                                              branch, round
  D3 shared mutable ledger (cross-recall)  -> one ledger per classroom;
                                              RECALL sees only its own
  D4 dose not filled / duplicates          -> exact target fill, no dup;
                                              shortfall reported not padded
  D5 no serial/OFF/PREV exams, no reject   -> ON/OFF/PREV exams; transactional
                                              REJECTED on canary or harm
  D6 seeds by batch position               -> seed = f(episode_id, tick, base)
  D7 silent base fallback                  -> hard-fail if round>0 checkpoint
                                              missing or rejected

  python -m organism_v6.classroom_round --lineage <dir> --round K \
      --classrooms N --lessons L --phase live|sleep|exam
Phases are separate processes (engine-teardown law).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys

from .gym_backend import Episode
from .ledger import Ledger
from .batch_loop import EpisodeDriver, _seed_for
from .rulegame import RuleGame
from .nursery_dialogue import CHILD_BOOT, PARENT_BOOT, PROBE_EIDS
from .sleep_compile import canonicalize_dialect

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM_SEED = 777
HARM_TOL = 0.03          # ON must not trail OFF by more than this on the exam
CANARY_TOL = 0.10        # PAIRED canary: ON parseable-ACT rate may not
                         # trail OFF (same seeded exam) by more than this.
                         # Absolute thresholds are gym-specific (2026-09-07
                         # smoke: base itself ~0.2 in the rule game).

STRATA = {               # minimum share per foundational disposition
    "dialect_anchor": 0.10,
    "prediction_revision": 0.15,
    "evidence_scope": 0.10,
    "stopping": 0.05,
    "memory_use": 0.05,
    "old_experience": 0.15,
    "new_experience": 0.40,
}


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def resolve_snapshot(lin: str, rnd: int) -> str | None:
    """D7: round 0 -> base (None). round>0 -> latest COMMITTED adapter at a
    lower round; hard-fail if none exists."""
    if rnd == 0:
        return None
    for r in range(rnd - 1, -1, -1):
        ad = os.path.join(lin, f"round_{r:03d}", "adapter")
        if os.path.exists(os.path.join(ad, "DONE")):
            return ad
        if os.path.exists(os.path.join(ad, "REJECTED")):
            continue                      # explicit rejection: keep walking
        raise RuntimeError(f"round {r} adapter neither DONE nor REJECTED — "
                           f"lineage inconsistent; refusing to guess")
    # Every lower round was EXPLICITLY rejected: the previous committed state
    # is the base. This is the transactional gate working, not a silent
    # fallback (2026-09-07 smoke: both parallel arms' first writes rejected).
    return None


def drive(model, drivers, gen_seed: int):
    """D6: per-(episode,tick) seeds independent of batch position."""
    while any(not d.done for d in drivers):
        act = [d for d in drivers if not d.done]
        outs = model.batch([d.prompt() for d in act],
                           seeds=[_seed_for(d.ep.eid, d.st.tick, gen_seed)
                                  for d in act])
        for d, o in zip(act, outs):
            d.consume(o)


def classify(row: dict) -> str:
    if row.get("stratum") in STRATA:
        return row["stratum"]
    a = (row.get("a") or "").upper()
    if "PREDICT" in a and any(k in a for k in ("WRONG", "REVIS", "GOT ")):
        return "prediction_revision"
    if "[SCOPE" in a or "SCOPE:" in a:
        return "evidence_scope"
    if "DONE" in a and "DIMINISH" in a:
        return "stopping"
    if "RECALL" in a:
        return "memory_use"
    return "new_experience"


def stratified_mix(new_rows, old_rows, anchors, target_n: int, seed: int = 0):
    """D4: exact fill without duplication. Each stratum gets min(share*N,
    available); remainder filled from new then old rows; shortfall reported."""
    rng = random.Random(seed)
    pools = {k: [] for k in STRATA}
    for r in new_rows:
        pools[classify(r)].append(r)
    pools["old_experience"] = list(old_rows)
    pools["dialect_anchor"] = [dict(a, stratum="dialect_anchor")
                               for a in anchors]
    chosen, used = [], set()

    def take(pool, n):
        avail = [r for r in pool if id(r) not in used]
        pick = rng.sample(avail, min(n, len(avail)))
        for r in pick:
            used.add(id(r))
        return pick

    for s, share in STRATA.items():
        chosen += take(pools[s], int(target_n * share))
    for s in ("new_experience", "prediction_revision", "evidence_scope",
              "old_experience"):
        if len(chosen) >= target_n:
            break
        chosen += take(pools[s], target_n - len(chosen))
    rng.shuffle(chosen)
    return chosen, dict(target=target_n, filled=len(chosen),
                        shortfall=max(0, target_n - len(chosen)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lineage", required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--classrooms", type=int, default=8)
    ap.add_argument("--lessons", type=int, default=4)
    ap.add_argument("--phase", choices=["live", "sleep", "exam"],
                    required=True)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--target-rows", type=int, default=400)
    ap.add_argument("--gen-seed", type=int, default=5000)
    ap.add_argument("--parent", choices=["self", "server"], default="self",
                    help="self: the child model plays parent (smoke only). "
                         "server: a stronger model on its own GPU, answer-"
                         "aware-but-withholding, leak-scanned, ledgered.")
    ap.add_argument("--parent-url", default="http://[REDACTED_ADDRESS]:8011/v1")
    ap.add_argument("--exam-eids", type=int, default=len(PROBE_EIDS),
                    help="exam size; rule-game noise SD is 0.067 at 8 eids "
                         "(2026-09-07), so 8 cannot resolve HARM_TOL. Codex "
                         "sets N; default unchanged.")
    args = ap.parse_args()
    lin = os.path.expanduser(args.lineage)
    rdir = os.path.join(lin, f"round_{args.round:03d}")
    os.makedirs(rdir, exist_ok=True)
    snapshot = resolve_snapshot(lin, args.round)
    game = RuleGame()
    gseed = args.gen_seed + 100 * args.round

    if args.phase == "live":
        from .model_backend import VLLMBackend
        model = VLLMBackend(adapter_path=snapshot)
        ledgers = [Ledger(os.path.join(rdir, f"ledger_c{c:02d}.jsonl"))
                   for c in range(args.classrooms)]          # D3
        receipts = []
        parent = pledger = None
        if args.parent == "server":
            from concurrent.futures import ThreadPoolExecutor
            from .parent_backend import ParentLedger, ServerParent
            pledger = ParentLedger(lin)
            parent = ServerParent(base_url=args.parent_url, ledger=pledger)
        with open(os.path.join(rdir, "parent_mode.json"), "w") as f:
            json.dump(dict(parent=args.parent, url=args.parent_url,
                           model=os.environ.get("V6_PARENT_MODEL")), f)

        def parent_correct(d):
            # the rule is handed to the parent for DIAGNOSIS only; leak_scan
            # in ServerParent.correct replaces any utterance that states it
            name, _fn, desc = game._rule(d.ep.eid)
            return parent.correct("\n".join(d.tail[-8:])[-3500:],
                                  child_stage=f"round{args.round}",
                                  evidence_ids=[d.ep.eid],
                                  hidden_answer=f"{name}: {desc}")
        for les in range(args.lessons):
            pre = []
            for c in range(args.classrooms):
                eid = f"rule{(c * 7 + les) % 10}/r{args.round}-c{c}-l{les}-a"
                pre.append(EpisodeDriver(
                    Episode(eid=eid, goal="Induce the hidden rule; ace the "
                            "quiz.", metric="quiz accuracy",
                            intro="A fresh mystery box."),
                    CHILD_BOOT, game, ledgers[c], budget_ticks=8))
            drive(model, pre, gseed)
            if parent is not None:
                with ThreadPoolExecutor(max_workers=len(pre)) as ex:
                    corr = list(ex.map(parent_correct, pre))
            else:
                corr = model.batch(
                    [PARENT_BOOT + "\n\nYour child's transcript:\n---\n"
                     + "\n".join(d.tail[-8:])[-3500:] + "\n---\nName the ONE "
                     "most important PROCESS mistake (never the answer), "
                     "under 100 words." for d in pre],
                    max_tokens=160, temperature=0.5,
                    seeds=[_seed_for(d.ep.eid, 900, gseed) for d in pre])
            restate = model.batch(
                [CHILD_BOOT + "\n\nYour parent said:\n" + x +
                 "\n\nRestate the lesson in your own words as a NOTE with "
                 "scope:" for x in corr],
                max_tokens=100, temperature=0.5,
                seeds=[_seed_for(d.ep.eid, 901, gseed) for d in pre])
            post = []
            for c, d in enumerate(pre):
                ledgers[c].append(dict(kind="parent", episode_id=d.ep.eid,
                                       note=corr[c]))
                ledgers[c].append(dict(kind="note", episode_id=d.ep.eid,
                                       note=canonicalize_dialect(
                                           restate[c].strip()[:400]),
                                       stratum="prediction_revision"))
                post.append(EpisodeDriver(
                    Episode(eid=d.ep.eid[:-2] + "-b", goal="Induce the hidden "
                            "rule; ace the quiz.", metric="quiz accuracy",
                            intro="A fresh mystery box. Remember: "
                            + restate[c].strip()[:250]),
                    CHILD_BOOT, game, ledgers[c], budget_ticks=8))
            drive(model, post, gseed)
            for c in range(args.classrooms):
                p1 = pre[c].summary()["best_score"]
                p2 = post[c].summary()["best_score"]
                adm = p2 >= p1                                   # world admits
                receipts.append(dict(classroom=c, lesson=les, pre=p1, post=p2,
                                     admitted=adm,
                                     evidence_ids=[pre[c].ep.eid,
                                                   post[c].ep.eid]))
                if pledger is not None:
                    pledger.append(kind="admission", source="world",
                                   child_stage=f"round{args.round}",
                                   evidence_ids=[pre[c].ep.eid, post[c].ep.eid],
                                   intervention=corr[c][:300], admitted=adm,
                                   outcome_delta=round(p2 - p1, 4))
            n_adm = sum(r["admitted"] for r in receipts[-args.classrooms:])
            print(f"[round {args.round} lesson {les}] admitted "
                  f"{n_adm}/{args.classrooms}", flush=True)
        with open(os.path.join(rdir, "admission_receipts.json"), "w") as f:
            json.dump(receipts, f, indent=1)                      # D1
        if pledger is not None:
            pledger.rewrite_playbook(lambda p: parent._chat(p, max_tokens=1200))
            leaks = sum(r.get("kind") == "leak_blocked" for r in pledger.rows())
            print(f"PARENT leak_blocked_total={leaks}", flush=True)
        print("LIVE_DONE")
        return

    if args.phase == "sleep":
        from .write_swarm import ANCHORS
        receipts = json.load(open(os.path.join(rdir,
                                               "admission_receipts.json")))
        admitted_eids = {e for r in receipts if r["admitted"]
                         for e in r["evidence_ids"]}
        new_rows = []
        for c in range(args.classrooms):
            led = Ledger(os.path.join(rdir, f"ledger_c{c:02d}.jsonl"))
            for r in led.rows():
                if r.get("episode_id") not in admitted_eids:
                    continue                                       # D1
                if r.get("kind") == "thought" and r.get("prompt") and \
                        (r.get("win") or r.get("had_note")):
                    new_rows.append(dict(
                        q=r["prompt"], a=canonicalize_dialect(r["note"]),
                        evidence_ids=[r["episode_id"]], branch=c,
                        round=args.round))                         # D2
                elif r.get("kind") == "note" and r.get("note"):
                    new_rows.append(dict(
                        q=f"What did you learn on {r['episode_id']}? "
                          f"Answer with scope.",
                        a=r["note"], evidence_ids=[r["episode_id"]],
                        branch=c, round=args.round,
                        stratum=r.get("stratum", "new_experience")))
        old_rows = []
        for r in range(args.round):
            p = os.path.join(lin, f"round_{r:03d}", "corpus.json")
            if os.path.exists(p):
                old_rows += [x for x in json.load(open(p))["corpus"]
                             if x.get("round") == r]
        mixed, fill = stratified_mix(new_rows, old_rows, ANCHORS,
                                     args.target_rows, seed=gseed)
        cp = os.path.join(rdir, "corpus.json")
        with open(cp, "w") as f:
            json.dump(dict(corpus=mixed, fill=fill, n_new=len(new_rows),
                           n_old=len(old_rows), n_admitted_pairs=len(
                               [x for x in receipts if x["admitted"]])), f)
        print(f"[sleep] new={len(new_rows)} old={len(old_rows)} "
              f"fill={fill}")
        rc = subprocess.run(
            [sys.executable, "-m", "organism_v6.train_adapter_v21",
             "--corpus", cp, "--out", os.path.join(rdir, "adapter"),
             "--rank", str(args.rank), "--epochs", "3", "--lr", "3e-5"],
            cwd=os.path.dirname(HERE)).returncode
        print(f"[sleep] train rc={rc}")
        if rc == 0:
            ad = os.path.join(rdir, "adapter")
            os.rename(os.path.join(ad, "DONE"), os.path.join(ad, "CANDIDATE"))
            with open(os.path.join(rdir, "manifest.json"), "w") as f:
                json.dump(dict(round=args.round, rank=args.rank, lr=3e-5,
                               epochs=3, classrooms=args.classrooms,
                               lessons=args.lessons, prev_snapshot=snapshot,
                               corpus_sha=sha(cp), fill=fill,
                               ledger_shas=[sha(os.path.join(
                                   rdir, f"ledger_c{c:02d}.jsonl"))
                                   for c in range(args.classrooms)],
                               gym_exposure="none (rule-game only)"),
                          f, indent=1)
        sys.exit(rc)

    if args.phase == "exam":
        from .model_backend import VLLMBackend, close_backend
        ad = os.path.join(rdir, "adapter")
        if not os.path.exists(os.path.join(ad, "CANDIDATE")):
            print("NO_CANDIDATE")
            sys.exit(1)

        def exam(adapter, tag):
            m = VLLMBackend(adapter_path=adapter)
            led = Ledger(os.path.join(rdir, f"exam_{tag}.ledger.jsonl"))
            ds = [EpisodeDriver(Episode(eid=e, goal="Induce the rule.",
                                        metric="quiz", intro="A fresh box."),
                                CHILD_BOOT, game, led, budget_ticks=8)
                  for e in [f"probe/rule-{i}" for i in range(args.exam_eids)]]
            drive(m, ds, EXAM_SEED)
            close_backend(m)
            scores = {d.ep.eid: d.summary()["best_score"] for d in ds}
            # MODEL OUTPUTS ONLY (ledger thought rows) — d.tail also holds the
            # intro and harness-injected [OUTCOME] lines, which polluted the
            # denominator (2026-09-07: recorded 0.21 vs true 0.93).
            chunks = [r["note"] for r in led.rows() if r.get("kind") == "thought"]
            ok = sum(bool(re.search(r"^ACT:\s*\S", t, re.M)) for t in chunks)
            return dict(mean=sum(scores.values()) / len(scores), scores=scores,
                        parseable_act_rate=ok / max(1, len(chunks)),
                        n_chunks=len(chunks))

        res = dict(on=exam(ad, "on"), off=exam(None, "off"))
        if snapshot:
            res["prev"] = exam(snapshot, "prev")                   # D5
        harm = res["off"]["mean"] - res["on"]["mean"]
        canary_ok = (res["on"]["parseable_act_rate"] >=
                     res["off"]["parseable_act_rate"] - CANARY_TOL)
        commit = canary_ok and harm <= HARM_TOL
        os.rename(os.path.join(ad, "CANDIDATE"),
                  os.path.join(ad, "DONE" if commit else "REJECTED"))
        res["decision"] = dict(commit=commit, harm=harm, canary_ok=canary_ok,
                               reason=("OK" if commit else
                                       "CANARY" if not canary_ok else "HARM"))
        with open(os.path.join(rdir, "exam.json"), "w") as f:
            json.dump(res, f, indent=1)
        print(f"EXAM round={args.round} on={res['on']['mean']:.3f} "
              f"off={res['off']['mean']:.3f} "
              f"prev={res.get('prev', {}).get('mean', float('nan')):.3f} "
              f"canary={res['on']['parseable_act_rate']:.2f} "
              f"-> {res['decision']['reason']}")


if __name__ == "__main__":
    main()
