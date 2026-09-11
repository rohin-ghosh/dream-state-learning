# Can an agent write its own experience into LoRA weights it can later use? Collaborator brief (v2, 2026-09-11)

[SEQ-nnn]: dated internal notebook entry (others by date); [E:nn]: internal evidence-table line; paper: our draft; traceable on request.

## 1. Research question and intended claim

Can a language model convert its own successful experiences into persistent, usable weight memory? Loop: (1) frozen Qwen2.5-7B-Instruct; (2) episode = one program, ≤ 16 think-then-act steps, exact score; (3) every 32 episodes, keep the agent's own spans from well-scored episodes; (4) sleep: train a fresh LoRA adapter from the frozen base on the cumulative spans, never on the previous adapter; the only training; (5) gate: accept or refuse it; (6) run base + committed adapter + own brief (+ parent brief when taught, §5); (7) repeat. Next: augmented writes (§4), then the decisive experiment (§5): does a lineage (§2) taught process-only learn an unseen gym faster than the same mechanism untaught?

Intended claims. Paper (2026-09-25): a characterisation of what one write learns on one gym, how it fails, and the extraction bottleneck; no positive memory claim. Next study (compute permitting): a one-lineage case study of taught versus untaught, existence proof or documented failure, not a benchmark; without compute after 2026-09-18 the paper stands alone.

## 2. Architecture

- **Life**: one 1,024-episode run of one agent from a fixed initial prompt in a compiler-optimisation gym. **Score**: fractional shrink in a program's LLVM instruction count (0.487 = 48.7%).
- **Gate**: whether the new adapter replaces the committed one; so far a score floor plus a brevity rule; proposed: patience (refuse only broken format or stopped work; roll back after repeated decline).
- **Committed adapter**: the last gate-accepted adapter. **Final adapter**: a life's last committed adapter.
- **Collapse**: an adapter-on probe more than 0.03 (about 2.3 paired SD) below the same life's adapter-off probe (a harmful pair); shapes: act once and stop, or a degraded adapter admitted then frozen by later refusals.
- **Brief**: the agent's own summary written at sleep. **Parent brief**: advice from a stronger model reading the agent's redacted record, process-only by prompt (the proposed design bans answers, recipes and scores; the historical leak scan was porous, deliveries unaudited); never a training row (the agent's own restatement of it can be; frequency not measured); the write-time scan now refuses verbatim parent lines where the loss falls.
- **Lineage**: one agent run as several clones, each in its own training gym; at every sleep their success-filtered spans are pooled, one adapter is trained from the frozen base on the pool, and every clone loads it.

## 3. Findings

Rank 8; two 8-GPU A40 nodes.

**(i) Writing experience into the adapter changes behaviour, noisily and sometimes harmfully.** Nine ungated lives, paired adapter-on/off probes on eight programs excluded from training by identifier (training holds same-source siblings of 4–6): mean life gain +0.019 (SE 0.011; 6/9 ≥ +0.02, 3/9 negative; paired SD ≈ 0.013); 4/9 lives had a late harmful pair (first at episode 384), all passing the format check [E:6, E:23, E:48, E:58–59].

**(ii) Behaviour ritualises and locks onto compiler recipes; the gate does not reliably prevent degradation.** Thinking ritualises (≥ 2 of 4 repetition flags in a 32-episode window: same first action, flat predictions, templated notes, same recall) at episodes 160–224 in 8/9 scored unparented lives (6 of the 7 scorable lives of (i) plus 2 under an earlier writer) [E:32]. In the gated lives, where adapter-on means were tabulated, plateaus repeat to four decimals across lives: 0.4878, the initial prompt's four-pass list run with no model, and 0.5291, one fixed six-pass routine [E:50, E:54]. Gate failures (gate+parent development lives; observational): the decaying floor admitted a write 0.037 below the adapter it replaced and, in another life, sat 0.06 below the life's best as a write passed; one approved adapter scored 0.138 on an unseen-panel replicate [SEQ-016, SEQ-023]. Gate catches: ≥ 19 brevity refusals of score-passing candidates (appendix) [SEQ-012].

**(iii) The frozen model reading the life's own final brief (no adapter) matches or beats the final adapter in most lives.** On the eight-program panel it did so in 12 of 19 lives; the adapter won in 7 (unparented 10 vs 4; parented development lives, observational, 2 vs 3) [SEQ-031]. These controls establish neither equivalence nor a general advantage either way [paper §1]. On 12 programs no life trained on, final-adapter means sat near or below the frozen base in every arm; no cell showed program-dependent choice (panels not designed for it) [SEQ-022/E:72].

**(iv) A controlled "car test" identifies the bottleneck.** Made-up owners' car colours planted at doses 0/1/4/16 (dose = occurrences of the fact in the record) over four sleeps, scored by paraphrased cues; bank = one independent set of 64 owners and colours. The adapter trained on each fact in its real context fits that text by 4.35 nats (bank 0), yet its binding statistic I_d (log-odds gain for the planted colour at the owner's cue minus the same at a matched unexposed owner's) is ≈ 0, and a scrambled-binding control matches it [SEQ-025/E:77–78]. Rank 32 did not help in the one cell tested; more adapter strength only sharpens a read-from-context skill (appendix) [SEQ-029, SEQ-030].

## 4. Immediate experiment and decision criteria

The next cell changes the write's representation and the retrieval cue, not the capacity. Memory is written as bare declarative text in which every rendering of a fact ends in one canonical sentence ("Owner X's car is red"), and it is retrieved by completing that sentence, not by answering a question: the agent controls its own recall cue, so paraphrase robustness is secondary. At equal total exposure (16) we compare 16 repeats of one form, 4 forms × 4, and 16 forms × 1, separating repetition from variety (Allen-Zhu & Li, arXiv:2309.14316: knowledge seen in one form is stored, not extractable, until augmented); alongside, the TMEM recipe (Ren et al. 2026, arXiv:2606.04536): low-rank FFN-only adapter on the last layers, SVD-initialised, SGD-trained. Chat-rendered training (fact in the user turn) taught the model to copy from context rather than store; bare text avoids that shortcut.

- **Success**: at dose 16, the owner-specific gain at the completion cue (the planted owner's frame minus a similar unexposed owner's frame) above zero with a confidence interval excluding zero, and the frame for unexposed owners and for the wrong property (bicycle) within the spill gate (colour-odds shift ≤ 0.03); sleep then expands each percept into many renderings at write time.
- **Failure**: text fit improves but the owner-specific gain stays at zero; we turn to retrieval (a separate memory block; retrieved context at write time), not more training.
- **Mixed** (gain above zero but spill above 0.03, as in the rank-8 occurrence-preserving short-piece cell, which recalls 0.944 on its training frame): a failure for lineage use; test whether fewer forms or fewer repeats cut spill before retrieval.

## 5. Longer-term lineage experiment (proposed, not run)

The lineage (§2) is raised in reasoning-puzzle gyms under parents (briefs: §2). Final test in the compiler gym (unseen by the lineage): a taught life (born with the lineage's final adapter; its writes carry a fixed sample of lineage spans) versus an untaught life (empty record, no adapter), identical mechanism, neither parented. Co-primary endpoints: (1) frozen transfer: the lineage's final adapter on the test gym, on versus off; (2) the 512-problem learning curve: on-minus-off score every 64 problems, entry level and slope from problem 128 to 512, ruler = between-life SD of that gain, 0.027 [SEQ-011]. One pair is a demonstration, not a "learns faster" claim; a second untaught seed is the minimum noise band; threshold to be pre-registered, not yet set. Parenting so far is observational (three parented development lives; nothing separates from unparented controls on score, echo or efficiency [E:47, E:53, E:55]); it is this study's manipulated variable, not a paper result.

## 6. What help we want

Write representations that bind facts to cues; two-block adapters; replay; a separate memory block; evaluation design (extraction probes, unseen panels, noise bands); GPU access after 2026-09-18; review of §4.

## 7. Appendix: evidence and non-claims

- Nine ungated endpoint adapters scored once at 1,024: three exactly on the two plateaus, one 0.003 below, three collapsed below adapter-off (0.4329, 0.4329, 0.4093), two on neither (0.5091, 0.4889) [E:50, E:54, E:73; SEQ-017–SEQ-019, SEQ-022, SEQ-023, SEQ-026; notebook 2026-09-11 04:30 UTC].
- Gate floor as run: max(latest adapter-off, committed adapter's latest probe) − 0.02 [E:25]; brevity rule: ≥ 19 refusals of writes that passed the score rule [E:89; SEQ-012, SEQ-013; paper §4, Table 2]; floor decay and the 0.138 replicate: (ii) [SEQ-016, SEQ-019, SEQ-022, SEQ-023].
- Unseen-program panel (12 programs, 48 cells; 2 adapter replicates vs 3-replicate bases 0.2574/0.2541; replicate SD 0.006–0.007; ±0.015 descriptive): final-adapter mean gain −0.017 ungated (n = 9), +0.003 gated (6), −0.010 gate+parent (7), +0.001 parented (3) (parented arms observational); 9/48 cells above +0.015 (7 exactly the routine's 0.2731), 33 within, 6 below (all with a collapsed replicate); ungated final − mid-life: 6/9 negative, 3/9 zero [SEQ-022/E:72].
- Recipe line alone vs full brief: eight-program panel, matched or beat in 4 of 4 lives (0.5291/0.5291/0.5291/0.5294 vs 0.5291/0.5163/0.5291/0.4898); unseen panel, matched once (0.2730 vs 0.2731), beat once (0.2727 vs 0.2525), below twice (0.2443 vs 0.2667; 0.2445 vs 0.2731) [SEQ-020, SEQ-021, SEQ-022, SEQ-023, SEQ-029, SEQ-030].
- Car test, rank 8, bank 0 unless stated: paraphrase dose signal only in the occurrence-preserving short-piece cell, +0.10/+0.08 at doses 4/16 (+0.049 pooled over two banks; I_d spans zero), exact-cue recall 0.944: a surface habit; colour-odds shift 0.20–0.25 on unrelated cues (gate ≤ 0.03); fact-in-context 0.844–1.000 vs 0.563 frozen [SEQ-025/E:77–78; SEQ-026]. Rank 32, three banks: I_d −0.137 [−0.488, 0.199] [SEQ-029]. Strength λ 0.25/0.5/1 on the rank-8 every-occurrence, real-context adapter, three banks, no retraining: I_d −0.25/−0.19/−0.55 [−1.06, −0.08]; read-from-context 0.80/0.95/0.94 [SEQ-030].

Not claimed (paper): that gated writes are safe or the gate prevents collapse; that parenting improves scores, delays ritual, prevents collapse or is taken up; that the adapter stores usable knowledge; that the ungated life-long gain sits on the initial-prompt plateau; that rank is irrelevant; anything beyond 1,024 episodes, eight programs, one gym, one base model; no firsts.

ICLR 2027 abstract 2026-09-18, paper 2026-09-25; GPU access ends 2026-09-18. Binding stop: no bootstrapped agent, and none whose provenance has not passed a fail-closed guard, is a lineage member or result; every compiler-gym life here is a development life; parented ones observational only.

Contact: Rohin Ghosh
