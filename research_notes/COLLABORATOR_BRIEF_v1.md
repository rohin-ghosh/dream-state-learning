# Experience models — brief for prospective collaborators (v1, 2026-09-11)

Tags: [SEQ-nnn]=dated internal lab-notebook entry (others by date); [E:nn]=internal evidence-table line; not public; every number traceable on request.

## 1. The idea in one paragraph

An *experience model* is frozen Qwen2.5-7B-Instruct plus one small per-life LoRA adapter, the only trainable component. It thinks in free text; a gym scores answers exactly; the harness executes one line (`ACT:`) per step and ledgers the rest; an episode is one program, ≤16 steps ("chunks"). Each "sleep" retrains the adapter from the base on the agent's own success-filtered spans. Stronger "parents" read the redacted record and brief the agent on *how* it thinks: process-only by prompt, leak-scanned by a porous regex, deliveries unaudited; the proposed design bans answers, recipes and scores. Parent text is never a training row; the child's own restatement of one can be (uncounted). Next: one agent as clones across gyms, merged at sleep; final test: does a taught lineage learn faster than the same mechanism untaught in an unseen gym? At most a case study of one lineage, not a benchmark.

## 2. Design principles for the proposed next system (not yet run)

- **Free thought is grown, not switched on; hard shell, soft centre.** With this write alone the agent ritualises (8/9 lives) and locks onto recipes (§3; no adapter-free life long enough to show causation), so proposed parents prompt thinking *moves* by question, not instruction; parents so far prescribed patterns ("Repeat after me"); nothing separated (§3). Boundaries (information, authority, evidence, stopping) fixed precisely; inside them, free choice.
- **The gate is patience, not a veto** (§3's gate was a score-floor veto plus brevity rule): refuse only broken format or stopped work; dips pass; roll back to the best committed adapter after repeated decline.
- **Text memory versus weight memory is a first-class comparison** (frozen model plus own notes vs each life's final adapter; 15 lives so far).

## 3. What we have measured so far

Mostly negative. Compute: two 8-GPU A40 nodes. Score: fractional shrink in a program's LLVM instruction count (0.487=48.7%).

**The system as run** (rank 8, rewritten every 32 episodes, 1,024-episode lives, compiler-optimisation gym; where gated, commit iff 8-program probe ≥ floor−0.02, floor=max(latest adapter-off, committed adapter's latest probe), and chunks/episode ≥ half the frozen model's (brevity rule) [E:25]).
- The write changes behaviour and in 4/9 lives harms late. 9 ungated lives, paired adapter-on/off probes on 8 programs held out by name only (training holds same-source siblings of 4–6): mean life gain +0.019 (SE 0.011; 6/9 ≥ +0.02, 3/9 negative); 4/9 had a harmful pair (below −0.03; paired SD ≈ 0.013), first at episode 384, all passing the format check [E:6, E:23, E:48, E:58–59].
- Recipe lock-in: in the gated lives, where adapter-on means were tabulated, plateaus repeat to four decimals: 0.4878, the birth prompt's four-pass list run with no model; 0.5291, one six-pass routine (`-Oz` 0.522). Nine ungated endpoint adapters, scored once at 1,024: three exactly on those values, one 0.003 below, three collapsed below adapter-off (0.4329, 0.4329, 0.4093), two on neither (0.5091, 0.4889) [E:50, E:54, E:73; SEQ-022, SEQ-023, SEQ-026; notebook 09-11 04:30].
- Thinking ritualises (≥2 of 4 repetition flags in a 32-episode window: same first action, flat predictions, templated notes, same recall) at episodes 160–224 in 8/9 scored unparented lives (6 of 7 scorable ungated plus 2 under an earlier writer, not the nine above) [E:32].
- The score-plus-brevity gate is porous: its brevity rule refused ≥19 writes that had passed its score rule [E:89; SEQ-012, SEQ-013; paper §4, Table 2]; its floor tracks the committed adapter's latest re-probe and in two gate+parent lives decayed to admit writes below the adapter replaced (0.037 below in one; floor 0.06 below the life's best in the other) [SEQ-016, SEQ-019, SEQ-022, SEQ-023]; one approved adapter hit 0.138 on an unseen-panel replicate [SEQ-016]. Parenting: n=3, nothing separates from controls [E:47, E:32, E:53, E:55].

**Unseen-program panel** (12 programs no life trained on; 48 cells; 2 adapter replicates vs 3-replicate machine bases 0.2574/0.2541; replicate SD 0.006–0.007, ±0.015 descriptive) [SEQ-022/E:72]. Final-adapter mean gain −0.017 ungated (n=9), +0.003 gated (6), −0.010 gate+parent (7), +0.001 parented (3); 9/48 cells above +0.015 (7 exactly the routine 0.2731), 33 within, 6 below (all finals with a collapsed replicate); ungated finals lost the mid-life gain (6/9 negative, 3/9 zero). No cell demonstrated program-dependent choice (panels not designed to elicit it).

**Text memory versus weights** (frozen model plus the life's own final brief, no adapter; one parented life also its last parent brief [SEQ-020]). 15 lives, 8-program panel: brief ≥ adapter in 10, adapter > brief in 5; three of the five also beat their brief on the unseen panel (+0.006, +0.010, +0.024; only the last outside ±0.015) [SEQ-018, SEQ-021, SEQ-027, SEQ-028]. The three wins tallied at the 8-life cut-off were fixed-recipe adapters [SEQ-022]; the two later (adapter-on 0.5091, 0.5115) sit on no named plateau [SEQ-027; notebook 09-11 04:30]. The recipe line alone equalled the full brief (0.5291; first life tested) [SEQ-020, SEQ-021; E:74].

**Car test: controlled memory dose–response** [SEQ-025/E:77–78; SEQ-026]. 64 made-up owners' car colours, doses 0/1/4/16 over four sleeps, rank 8, paraphrased-cue scoring (chance 0.25). Writers: keep-every-occurrence vs deduplicate × one-line fact vs fact in its real context ("antecedent"), plus a scrambled-binding control. I_d: adapter log-odds gain for the planted colour at a cue naming the owner minus that at a matched cue for a similar unexposed owner. Bank 0 unless stated. No cell binds fact to owner out of context: every I_d interval includes zero; colour odds shift 0.20–0.25 on unrelated cues (gate ≤0.03; "red" for everything); scrambled equals real. Occurrence-preserving short pieces give the only paraphrase dose signal, +0.10/+0.08 at doses 4/16 (+0.049 pooled over two banks; I_d spans zero in both), and exact-cue recall 0.944: a surface habit, not a bound fact. Antecedent cells read as a context skill, not facts (fact-in-context 0.844–1.000 vs 0.563 frozen; repaint followed 100%), yet fit their training text by 4.35 nats with I_d≈0 (−0.007, 0.006): storage without extraction.

**Reasoning-gym headroom band** [SEQ-027]: frozen exam mean 0.113, rep SD 0.061 (compiler replicate SD 0.0066 [E:66]); three of five families near-constant; recalibrate difficulty to ~0.2–0.5.

## 4. The open problem we want help with

**Extraction from weights.** Why does a write that fits its text by 4 nats retrieve nothing under paraphrase? The lineage matches: ~3 nats/token lower loss on own rows, ~+0.02 behaviour (2 lives) [E:35]. Two literatures:

- **TMEM** (Ren et al. 2026, arXiv 2606.04536): within-episode absorption of self-extracted experience into fast LoRA weights.
- **Physics of LMs 3.1** (Allen-Zhu & Li, arXiv:2309.14316): knowledge seen in one surface form is stored but not extractable until augmented (paraphrase, sentence shuffling, translation, or instruction-style QA in pretraining). The car test plants each fact in one template: that regime.

Next: each fact in several forms plus QA pairs on disjoint owners; if that extracts, sleep augments at write time. Wanted: mechanism ideas (write representation, two-block adapters, replay), evaluation design (extraction probes, panels, noise bands), compute, hard review.

## 5. Status and timeline

This week: write-mechanism pretests (four adapters; probes running), car test stage 2 and rank 32 [SEQ-028]. ICLR 2027 abstract 2026-09-18, paper 2026-09-25; GPU access ends 2026-09-18. Binding stop: no bootstrapped or parented "clean child" counts as a result until a fail-closed provenance guard passes.

## 6. What we are not claiming

From the paper: not that gated writes are safe or the gate prevents collapse; not that parenting improves scores, delays ritual, prevents collapse or is taken up; not that the adapter stores usable knowledge; not that the ungated life-long gain sits on the birth-recipe plateau (endpoint adapters scored once); nothing about schooling corpora beyond composition; not that small frequent writes beat one large or that rank is irrelevant; nothing beyond 1,024 episodes, eight programs, one gym, one base model; no firsts.

Contact: Rohin Ghosh
