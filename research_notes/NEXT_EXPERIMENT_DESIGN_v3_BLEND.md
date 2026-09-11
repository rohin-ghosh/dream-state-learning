# NEXT_EXPERIMENT_DESIGN_v3_BLEND — one pretest-first plan (2026-09-11, Fable; revised after critique)

Blends `CHILD_MECHANISM_v7.md` and `NEXT_EXPERIMENT_DESIGN_v2_ASTRA.md` under Rohin's rulings (`IDEAS.md` 09-10/11) and evidence to SEQ-034; colliding rulings are listed in §8, not resolved. Codex's STOP (COORDINATION ~857) stands: a lineage born without a passed fail-closed provenance guard is a development life, not a result. Boundaries: `CANON_v7.md`. Every setting is proposed.

**Terms, defined once.** *Child*: frozen Qwen2.5-7B-Instruct plus its adapter lineage. *Life*: one run from an empty record until stopped from outside. *Clone*: one running copy per GPU sharing the lineage's adapter. *Sleep / write*: training the adapter on the child's own text. *Birth*: the lineage's first problem. *Parent*: a stronger frozen agentic model that reads the child's redacted record and teaches; *room*: two parents on one gym.

## 0. One screen

**Claim.** One lineage, existence proof: a child raised in reasoning-gym classrooms under parents teaching six moves in varied modes, whose sleep writes its own frequent thoughts and perceptions into two adapter blocks, learns the unseen compiler gym faster than the identical mechanism untaught, by ≥ +0.020 with interval excluding zero — a demonstration with internal controls, not a population claim [IDEAS 09-10 "one-lineage claim"].

**Mechanism, five lines.**
1. Free text; the harness reads only `ACT:`; problems arrive forever, no end token, stopping external [IDEAS 09-10].
2. Parents teach six moves (decide, associate, goal, build, prune, perceive) in varied modes — question first; suggestion, demonstration, worked pattern or recipe offered as opinion, never enforced, never verbatim across briefs, never the only thing offered [IDEAS 09-11 "no nevers"]; the leak scan is the hard shell.
3. Every thought and perception is kept, repeats included; sleep trains two blocks from child text only — behaviour (rank 8) and memory (rank 32, bare frames read by completion) [IDEAS 09-11].
4. Gate as patience: refuse only broken interface or stopped work; roll back after three confirmed strikes; hold-and-confirm is D6, off [IDEAS 09-10].
5. Clones never wait; the writer trains one round behind; the final test is the unseen compiler gym in two conditions [IDEAS 09-10].

## 1. The child

Free-form turns ≤ 400 tokens; context = briefs, problem head, recent turns [v7 §1.1]. No parsed markers — predicting, noting, recalling, perceiving are learned behaviours the instruments count [IDEAS 09-10 "Less predefined child"]. No end token; nudge after 4 silent turns; 16-turn budget [v7 §1.3]. The child sees its gym scores [IDEAS 09-11 early], never the structure metrics [SURVEY rule 26]. Private reflection 4 turns per round; parents read, never mention [v7 §1.6].

## 2. The write

**Eligible.** Child-authored thought, reflection and perception rows only; gym lines masked; parent text stripped and refused by the leak scan; the writer refuses to train without a scan report [guard defined once: CANON_v7 §1 "Guard"; Codex fixes 2, 4]. Every row kept, no dedup, no cap [IDEAS 09-10 late]; the polarity-tag arm (D15) runs in the struggle write (item 5), not in the write pretest [Codex fix 6].

**Behaviour block — rank 8, attention projections.** Multi-scale sequences (three scales, a token budget per scale), neighbourhood packing by family and time [IDEAS 09-11 "write shape by block"; v7 §2.2]. Phase A cumulative from base for K = 3 sleeps; phase B incremental with use-and-recency replay only through P9 [IDEAS 09-10 "Stop replaying everything"].

**Memory block — rank 32, MLP projections.** Bare declarative frames from the child's own perceptions and outcomes, every occurrence kept, each ending in the child's canonical sentence; no chat template or question form [IDEAS 09-11 "Retrieval by completion"; SEQ-033]. Retrieval is a taught move; dose fixed by cell F.

**Serving and release.** The two deltas add; one adapter served; each block switchable (both / behaviour-only / memory-only / OFF). **Default = interim merge**: the existing coordinator in non-blocking mode plus the existing ≈ 4-minute engine restart at batch boundaries [v7 §2.4 line 103], labelled in the manifest. Asynchronous hot-swap [Astra §3] is switched on mid-childhood only after the P6 fixtures pass. Release blockers on every write: canary and leak scan (Codex checks the scan independently [fix 3]). Rank growth by exact zero-padding on the incremental path only, disabled unless P9 qualifies (C1) [IDEAS 09-11 early]; SVD-based initialisation only if write cost becomes the bottleneck [IDEAS 09-10 TMEM framing].

**Budget.** One writer cycle ≤ 1.25 GPU-h of training at the measured 1,107 tok/s [SEQ-028]: T_max = 5 M token-passes split 3.5 M behaviour + 1.5 M memory, frames packed to avoid the short-item regime (389 tok/s, SEQ-028); newest round in full, the rest sampled. Cycle ≈ 1.25 train + 0.1 canary + 0.45 gate exam + 0.07 engine start ≈ 1.9 h [v7 §2.4]; T_round = the measured cycle (§7).

## 3. The gate as patience

Protect against collapse, allow dips, roll back with patience [IDEAS 09-10]. Per trained adapter:
- **Brake** (never a score): canary fails, or median tokens per unsolved exam problem < 0.5 × frozen (≥ 6 paired observations; missing support = hold) → `REJECTED`.
- **Provisional activation** at the next batch boundary, re-examined at the next probe (never averaged). **Strike**: confirmed score < F_g − tol_g. Three consecutive strikes → roll back to the best committed adapter; parents told by reason code.
- **Severe deficit** (≤ F_g − 5 tol_g; the shape of R4 601@800's 0.114, SEQ-015): committed and activated like any other adapter — the ruling says three sleeps for everything; the hold-and-fresh-check fast path is D6, default off until P8 gives the numbers.
- **Floor F_g** = best gate score of any committed adapter, per gym, never lowered [ruling 8 via v7 §3.3]. **Tolerance**: compiler 0.01 (v7 §3.4); reasoning gym max(quantum, 2 × paired SD, 0.02) after recalibration [Astra §3]. Rollback never touches the record (D7); parents see reason codes only.
- **Build dependency.** None of this exists (`run_life_v2.py`: fixed score floor plus brevity ratio). "Gate v7 state machine" is on the 09-11/12 build list (owner Fable; cut line 09-13 06:00 UTC). Pre-declared fallback: birth under the existing gate, labelled "gate v6" in the manifest and listed for Rohin as a deviation.

## 4. Parents

**Room parents (Astra + Astra, two per gym).** Score-blind, gate-informed: redacted record, instruments as trends (counts until 6b), gate reason codes, parental ledger; never a panel number. They teach the six moves one per nudge at the frontier, in varied modes — question first; suggestion, demonstration, worked pattern or recipe offered as opinion, never enforced, never verbatim across briefs, never the only thing offered [IDEAS 09-11 "no nevers"; rules 20–26 as revised, C11]. **Grain-of-salt absorption is taught**: parents offer, the child weighs advice against its own record and may disagree; a disagreement followed by a test is the desired shape [IDEAS 09-11 item 2]. Pruning by drop-or-defend [rule 23]; fade per move [rule 26]. Brief ≤ 10 lines, ≤ 2 questions, ending in a request for restatement; same lesson, sharpened not switched [IDEAS 09-10].

**Central parent (Fable; Codex reviewer).** Advisory, asynchronous, never blocks a sleep [IDEAS 09-10]; asks "is this new intelligence or a script", proposes experiments, re-ranks curriculum [IDEAS 09-11 early]; writes only from a fresh allow-listed context [v7 §1.5.5].

**Appraisal gym: not in this run** (item 9 done, future work); no 09-12/13 engineering time for created events or appraisal questions.

## 5. Gyms

**Classroom = reasoning-gym**, families held out by name (train / gate / exam), difficulty recalibrated so the frozen child sits at 0.2–0.5 [SEQ-027]; persistence first. **Final test = compiler gym** (withheld): gate set disjoint panel v1 [SEQ-012], report set the 8 programs held out by identifier (panel v2 vs exploratory label: CANON §4). **Two co-primary endpoints**, each with its own receipt [Codex fix 5]: (a) learned agency — final adapter frozen, ON vs OFF at entry and after 128 problems; (b) continual learning — taught life vs untaught comparator, identical mechanism, empty record, 512 problems, ON−OFF every 64, slope 128→512, ruler = between-life SD 0.027 [SEQ-011]. **The comparator runs both conditions**: (a) its own final adapter from an untaught life frozen at the matched checkpoint, ON vs OFF; (b) as stated. No developed-vs-regular arm: the baseline is the identical mechanism untaught [IDEAS 09-10 night]. Secondary: tokens-to-target ≥ 10 % lower [Astra §6]; text-memory comparator at matched horizons within node [SEQ-034]. Margin +0.020, interval excluding zero (§0); one pair = demonstration, not a population claim.

## 6. Pretests, in order

Arithmetic at 16 compiler problems per GPU-hour (v7 App. B), ≈ 168 puzzles per GPU-hour (SEQ-027), 1.25 GPU-h per write (1,107 tok/s, SEQ-028); "band" = one noise width.

|#|pretest|cell design|GPU-h|success / failure / mixed|unblocks|
|---|---|---|---:|---|---|
|0|**Provenance guard** (build 09-11/12)|fail-closed manifest: birth hash, parent-state hash, source set, mechanism version, exposure domains, quarantine check; regression-tested on a deliberately contaminated fixture and on the P3 variants|0|fail → no birth (Codex STOP)|birth|
|1|**Interface canary** (standalone step over an adapter directory; build today)|4 train-split problems × 6 turns, birth brief only, ≥ 3 scoreable; post hoc over all pretest adapters 09-12 morning (≈ 21 × 0.15 GPU-h)|3|fail → "interface-collapsed", never scored|every judgement below|
|2|**Write pretest A/A_v3/B/C (+Bs, B_match, C_tmem)**, 3 lives (seed0 done [SEQ-033]; seed8, seed7 running)|horizon 512, rank 32 all projections, both panels, 2 reps, within-node. C_tmem = TMEM-shaped: self-extracted QA pairs, rank 6 last-4 FFN, SVD-initialised frozen A [COORDINATION 09-11 01:45]; canary first. Plus one cell B at rank 8, attention-only (≈ 3 GPU-h)|27|canary-passing cell ≥ +0.015 over OFF on the unseen panel, not the routine, in ≥ 2 of 3 lives → behaviour-block representation; all positive cells routine or collapsed → target-only multi-scale, claim "no lock-in"; mixed → B_match / Bs decide; without the rank-8 cell the freeze inherits a rank-32 result, labelled|behaviour block; freeze|
|3|**Cell F frames** (code in review)|bare frames ending in the canonical sentence; ladder in code: 16 and 64 (F_r16k1 / F_r16k4 / F_r16k16, F_r64k16; ≈ 8 GPU-h, running); add F_r256k16 on bank 0 (≈ 3 GPU-h, FORCE=1) for a 256 reading by 09-12 noon; 1,024 on bank 0, one form (≈ 11 GPU-h) on node-1 GPU 2 after the struggle test, dropped if not started by 09-12 12:00 UTC; I_d_frame primary|22|I_d_frame > 0, interval excluding zero at dose ≥ 64, spill ≤ 0.03 → memory block = frames; null at 256 on bank 0 → memory block dropped; binding with spill > 0.03 → one fewer-forms cell, then drop|memory block; item 5|
|4|**Band recalibration** (build: per-family config in `reasoning_gym_families.json`, setting tag `rg/<family>@<setting>/<seed>`; ≈ 1–2 h)|5 families × 3 settings × 4 reps × 12 instances; gate tol measured|5|all in band, rep SD < 0.05 → classroom launches; untunable family dropped|classroom; tol|
|5|**Struggle test** (reasoning gym, n_queens: frozen child 0/48 [SEQ-027]; no compiler firewall)|7 clones × 74 problems (512 exposures) on node 1, GPU 2 left to cell F; one write, both blocks, plus the polarity-tag arm (D15); ON vs OFF on new instances; completion of the child's canonical sentence vs OFF. Unbuilt (09-11 08:30 UTC): struggle harness, two-block combine, gym-frame writer, completion probe; if not landed by 09-12 06:00 UTC: behaviour block alone, memory reading "not run", D11's memory block provisional|6|both > 1 band → memory at scale; both null → memory endpoint withdrawn; behaviour only → "procedural memory"|memory endpoint; item 10; D11|
|6a|**Detectors** (write 09-11; engineer time)|back-reference, plan span, move diversity, echo, dependency, unprompted rate; perceptions per situation, novelty, share later used by a decision; advice uptake conditional on track record, disagreement rate, disagreement followed by a test. None exist today|0|—|6b|
|6b|**Detector calibration** (09-12 evening)|50 flagged turns per detector hand-audited on the first 200 v7 turns from item 7, precision ≥ 0.8|0|< 0.8 → readings "detector-flagged, uncalibrated"; parents receive counts, not trends [V14]|frontier estimates; item 7 exit|
|7|**Preparation phase, first child** ((c) dropped under the STOP; C3 resolved)|(a) brief only vs (b) brief + own-words rehearsal, two rounds; parents at problem boundaries; one move per problem on the easiest family; exit when each move is unprompted in ≥ 3 of the last 8 problems by a keyword detector declared provisional; cap 160 per variant [v7 §4; rule 22]; wall-clock binds (≈ 2–4 min per problem)|6 (≈ 12 h wall, 2 GPUs)|earliest exit with scoreable ≥ 0.9 and thoughts per action ≥ half of (a); no exit by 09-13 06:00 UTC → (a) ships|birth|
|8|**Asynchronous merge + hot-swap** (P6; off the critical path)|destructive fixtures first; production soak after birth: 0 duplicate ingestion, 0 partial publication, 0 mid-problem swaps [Astra P6]. Today the coordinator is a barrier and the backend cannot reload an adapter [v7 §2.4]|0 pre-birth|pass → hot-swap at a batch boundary, labelled; fail → interim merge throughout|D3|
|9|**Appraisal-language probe** — done 09-11|P(change \| affect word) 0.204 vs 0.157; sign unstable across arms; neutral control "further" +0.225 [AFFECT_LANGUAGE_PROBE_2026-09-11]|0|above null, not above the topical control → future work|—|
|10|**Two-block attribution**|both / behaviour-only / memory-only / OFF, 2 reps, both panels (≈ 10 GPU-h per checkpoint) at three checkpoints: struggle adapter, mid-childhood (≈ sleep 18), final adapter; drop the mid cell if it contends with gate confirmations|30|memory-only = OFF → memory block not claimed; both < either → re-split by layer once; one receipt per claim [Codex fixes 5, 7]|paper claims|
|P2|**Pace pilot** (today, node 1, 2 GPUs × 2 h)|v7 turn budget (16 × 400), no end token, one batch per gym, with/without a parent call; problems per GPU-hour, tokens per problem|4|rewrite §7's round length, sleep count and finals horizon before 09-12 18:00 UTC|§7|

Offline: P8 gate replay (once the state machine exists), P9 incremental qualification (12 GPU-h). Order: 0, 1, 2, 3, 4, 6a, P2 today; 5, 7, 6b on 09-12; 10 with 5 and the lineage; 8 after birth. Total ≈ 103 GPU-h plus 30 for item 10.

## 7. Budget and timeline to 2026-09-18

**Capacity.** Node 1: 8 × A40, dies 09-14 16:14 PDT (23:14 UTC), not extendable; node 2: 8 × A40, work stops 09-18 [COORDINATION 02:50 UTC]. From 09-11 08:00 UTC ≈ 2,140 gross GPU-h, ≈ 70 owed to finishing lives (sleep counts per SEQ-034; pretest chains counted in §6). Third node: counts as 0 until tested (bookings refused, HTTP 409 [COORDINATION 04:30 UTC]).

**Allocation.** Pretests ≈ 133. Lineage on node 2: 5 clones + writer + evaluator + probe GPU = 8 × 72 h ≈ 575 GPU-h; sleeps ≈ 72 h / T_round (≈ 36 at 2 h; fewer if P2 measures a slower cycle). Finals on node 2: two lives (clone + writer each) plus condition (a): 8 × 42 h ≈ 340. Total ≈ 1,050 GPU-h; wall-clock binds.

**Per-GPU assignment, 09-12 (UTC).** Node 2: GPUs 6/7 finish the write pretests ≈ 00:30; GPU 3 holds cell F; item 7 on 2 GPUs from 01:00; the rest finish R4 600 / R3 504. Node 1: struggle test on 7 GPUs from ≈ 04:00 when R4 604/605/606 end (1.1–1.7 h per sleep [SEQ-034]); GPU 2 keeps cell F, then the 1,024 rung.

**Calendar (UTC).** 09-11: items 0–4, 6a, P2; build canary, frame writer, band, detectors, gate v7. 09-12: items 3–4 results by noon; item 5 on node 1; item 7 on node 2; 6b evening; D6 and C1–C11 to Rohin by 18:00. 09-13 06:00: item 7 exit or fallback to (a); gate v7 tested or "gate v6" declared; 08:00: struggle readings → D11 decided (if slipped: born with both blocks, memory block OFF at the first checkpoint if item 5 is null); ≤ 10:00: guard passes on the preparation winner's manifest, else birth waits; **12:00: lineage born on node 2**. 09-16 12:00: childhood ends; final adapter, manifest, provenance frozen. 09-16 14:00 → 09-18 08:00: finals — both lives started within the same hour on one gen-seed schedule; (b) 512 problems per life (≈ 32 h wall plus write lag), (a) in parallel, text-memory comparator (≈ 3 GPU-h) on the evaluator GPU. Pre-registered minimum horizon: if either life is below 512 at 09-18 06:00 UTC, the primary curve is read at the largest common multiple of 64 (slope 128→384 at worst). 09-18 08:00: last sleep committed (not merely started); export to 20:00.

**Two lineages.** Default: two if a third node is tested by 09-13 12:00 UTC, else one, labelled "no replication" [IDEAS 09-11 early; CANON §4].

**What will not fit.** The 1,024-problem final; a second untaught seed; P9 (phase B, rank growth); a live appraisal gym; a source-disjoint report panel; variant (c). **Slack:** GPU calendar ≈ 4–6 h (finals: 32 h of problems + 2–4 h write lag + 2 h freeze inside 42 h); engineering 0 h. Cut list, in order: item 10's mid-childhood checkpoint; the 1,024 rung; item 5's memory block; hot-swap; gate v7.

## 8. Decision register

**Kept (D1–D10).** D1 T_max 5 M split 3.5 / 1.5 M, E = 1; phase B via P9 only. D3 **interim merge (synchronous, labelled) by default; hot-swap if P6 passes** (reversed). D6 severe-deficit hold: off; P8 numbers. D8 variant (c): not run (C3 resolved by the STOP). D9 node 1: struggle test, write-pretest lives, the 1,024 rung; no lineage. D2, D4, D5, D7, D10 as in v7 §9.

**Added.** D11 two blocks (8 attention / 32 MLP), each switchable, entering only through items 3, 5, 10; struggle readings before birth. D12 bare frames, completion retrieval. D13 canary everywhere. D14 three strikes, no hold. D15 polarity arm in the struggle write. D16 parent text stripped. D17 perception as sixth move; appraisal gym future work. D18 comparisons within-node only. D19 gate v7 is a birth dependency with a pre-declared "gate v6" fallback. D20 under the STOP, a lineage born without a passed guard is a development life, not a result.

**Conflicts between rulings, for Rohin.**
- C1 Rank: "rank 32" (09-10 late) vs "grow 8 → 16 → 32" (09-11 early) vs "8 + 32" (09-11). Default: two fixed blocks, no growth. Write pretest at rank 32 because the rank-32 D cell was already running (IDEAS 09-11 "Physics of LLMs"); cell F and the struggle test at rank 8 unless Rohin says otherwise.
- C2 "Keep every thought, no cap" (09-10 late) vs Codex fix 6 (excluded or tagged). Exclusion breaches no-cap; options are tag or train equally. Default: tag, never exclude; decided by D15 in item 5 (CANON §4).
- C3 "No pretrained-adapter bootstrap" vs "interface-only set" (both 09-10 late). Resolved for this run by the STOP: variant (c) not run.
- C4 "Parents see training outcomes and gate decisions" (09-11 early) vs SYSTEMS_BRIEF §4.4 vs parents see scores. Default: reason codes and outcome text, no numbers.
- C5 "Mechanism frozen 09-11" vs the 09-11 rulings. Default: freeze re-dated to birth, hash registered.
- C6 "Two short childhoods" (09-11 early) vs the deadline. Default: two if a third node is tested by 09-13 12:00 UTC, else one.
- C7 Emotional gym now vs pretest first. Resolved by item 9: future work.
- C8 "Allow structured lengthening" (09-11) vs v7's 16 × 400. Default: 16 turns; brake reads length downward only.
- C9 "Child sees its scores" (09-11 early) vs SURVEY rule 7. Default: gym scores yes; structure metrics never.
- C10 Floor "best committed ever" (ruling 8) vs Astra's anchor. Ruling wins; bias absorbed by tol (v7 §3.4).
- C11 Moves taught by question only (09-11 line 1514; SURVEY rules 20–26, rule 24 "Never transmit a recipe") vs no nevers / a recipe may be offered (09-11 line 1547). Rohin to confirm the later governs and rule 24 is rewritten; this file follows it.
