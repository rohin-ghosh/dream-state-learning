# Classic Deep-RL Memory Line — Prior-Art Sweep vs. Value-Gated Writes

**Question checked against every paper:** does the classic (mostly pre-LLM) deep-RL memory
literature already do *value-gated selective WRITES into a bounded (parametric) memory*, and does
any of it threaten our framing (frozen LLM + small attention head trained on TD/distance-to-goal
salience gating fast-weight writes, `w = surprise × (1+β·salience)`, retention-typed evaluation)?

**Headline: NO prior art on the write side.** The entire classic line writes *everything* (or on a
fixed schedule) and spends its learning capacity on the **read/retrieval** side or on **replay
sampling**. Learned gates exist for reinstatement (Ritter), retrieval attention (MERLIN, HCAM),
credit assignment through reads (TVT), and forgetting (LRU evictions, Expire-Span) — never for
value-weighted write strength into a bounded store. PER (2015) explicitly *named* prioritized
storage/erasure as an unexplored extension and the line never executed it in this form.
Two caveat results (Isele & Cosgun 2018; d'Autume 2019) show naive reward/surprisal *selection
heuristics* underperforming — these are baseline obligations, not refutations (details below).

---

## 1. MERLIN — Wayne et al. 2018, "Unsupervised Predictive Memory in a Goal-Directed Agent" (arXiv:1803.10760) ★ deep-read

**Mechanism.** RL agent with a slot memory matrix. A VAE-style world model produces latent `z_t`;
policy reads memory via content-based attention. **Writes are unconditional**: `z_t` is written to
row `t` at every timestep (write weight = 1 at position t, 0 elsewhere). A "retroactive memory
update" appends a discounted summary of *future* latents `[z_t, (1−γ)Σ_{t'>t} γ^{t'−t} z_{t'}]` —
temporal context, not value pruning.

**What EXACTLY it claims about reward-driven memory formation.** The claim is about *gradients*,
not about value signals per se:
- "learning the representations to put in memory by end-to-end policy gradient RL only works if
  the minimal time delay between encoding events and actions is not too long."
- BPTT over the encode→use interval requires keeping exact network states over the whole gap,
  which is "practically prohibitive" for long delays; when the truncation window τ is shorter than
  the storage timescale, "RL models can struggle to learn at all."
- Solution: let **unsupervised predictive modeling** (reconstruction + latent prediction) decide
  the *content/format* of what is stored, so nothing about encoding needs to be learned through
  the delay.

**Crucial nuance — value is NOT absent.** The return prediction `R̂_t` is one of MERLIN's decoders
and "has the essential role of shaping state representations": `z_t` is explicitly optimized to
retain return-relevant information. So MERLIN itself injects a value signal into what gets stored
— via representation shaping, not via write selection/strength. `R̂` is not stored; no gating.

**Evaluated.** Task return, plus analysis probes (goal-location decoding from `z_t`, return
prediction error, read-head specialization). Tasks: memory game, navigation variants, arbitrary
visuomotor mapping, rapid reward valuation, episodic water mazes, transient instructions, latent
learning T-maze. No fixed-budget retention typing.

**Relation to us / does it contradict?** **No — it supports us, if we phrase carefully.**
1. MERLIN's prescription is "representations that go into memory should come from unsupervised
   prediction, not from reward gradients through the delay." Our frozen pretrained LLM *is* the
   unsupervised-predictive encoder, taken to its modern extreme. We satisfy the constraint by
   construction.
2. Our value signal never backpropagates through the storage→use delay. It is a *dense, immediate,
   per-write scalar* (oracle TD distance-to-goal salience, later a learned head) that scales write
   strength. MERLIN's infeasibility argument targets exactly the thing we don't do.
3. Our write rule `w = surprise × (1+β·salience)` literally composes MERLIN's signal (predictive
   surprise, the primary factor) with a value gain (the modulation). MERLIN answers *what format*
   memories should have; it never addresses *which/how strongly* under a budget — it writes every
   step into an ample matrix.
- **Framing to avoid:** never claim "reward decides what to remember." Claim "value *modulates
  write strength on top of* predictive surprise, on unsupervised-pretrained representations" —
  that is MERLIN-compatible and matches the neuro line (note 04: dopamine-gated consolidation).

## 2. Neural Episodic Control — Pritzel et al. 2017 (arXiv:1703.01988) ★ + Model-Free Episodic Control — Blundell et al. 2016 (arXiv:1606.04460)

**NEC mechanism.** Per-action Differentiable Neural Dictionary (DND): keys = slowly-changing conv
embeddings, values = N-step Q estimates (N=100). Lookup = kernel-weighted kNN over keys.

**Writes.** **Everything**: "we elect to write all experiences to the memory, and allow it to grow
very large" (5×10^5 slots/action). Existing keys get a tabular Q update `Q_i ← Q_i + α(Q^(N) − Q_i)`;
new keys appended. Eviction = least-recently-used-as-neighbour. And the explicit anti-position:
NEC "does not try to learn when to write to memory, **as this can be slow to learn**."

**MFEC.** Even simpler: QEC table updated at episode end by backward replay with the optimistic
`max{Q_EC, R_t}` rule; LRU eviction at 1M; no gating. Core argument: episodic store latches onto
successful trajectories orders of magnitude faster than slow parametric gradient learning.

**Evaluated.** Atari return / data-efficiency curves only. No retention analysis.

**Relation to us.** NEC's sentence is the canonical citation for *why the classic line avoided
learned write gates*: learning when-to-write end-to-end by RL is slow. Our design answers the
objection rather than ignoring it — the gate is a small head trained against a **dense supervised
salience target** (oracle TD distance-to-goal, later distilled), on top of a frozen backbone; no
sparse-reward credit assignment through the write decision. Also note: NEC could afford "write
everything" because its store is quasi-unbounded and non-parametric; at a fixed parametric-write
budget that option does not exist, which is exactly our regime. MFEC/NEC's "fast episodic vs slow
parametric" story is also our wake/sleep motivation (note 01), but neither selects writes.

## 3. HCAM / "Towards Mental Time Travel" — Lampinen et al. 2021 (arXiv:2105.14039)

(Items 3 and the "Towards mental time travel" entry of item 7 are the same paper.)

**Mechanism.** Memory = fixed-length **chunks**; each stored in full detail (sequence of steps) with
one average-pooled summary key. Hierarchical read: attend over chunk summaries, then dense
attention *within* top-k relevant chunks, relevance-weighted.

**Writes.** All chunks are kept; no gating/selectivity on storage (the fetch's phrasing — treat as
accurate paraphrase, not verbatim). Gradients are **stopped into memory**, so the encoder cannot
even implicitly learn what to prioritize for retention; instead an image+language **reconstruction
auxiliary loss** forces task-relevant features into the stored representations — motivated by
sparse task reward being too weak a signal for learning what to store (paraphrase; same argument
family as MERLIN).

**Evaluated.** This is the classic line's closest thing to retention-typed evaluation: Ballet
(recall which dancer performed a pattern after 16–48-step delays), object permanence over 0–30 s
delays, rapid word learning tested after 0–20 **distractor task phases**, extrapolation from N
train distractors to 5N. But the metric is still task reward after delay — no typing of *what kind*
of information survives (relational vs episodic), no fixed write budget.

**Relation to us.** Strongest classic support for our *evaluation* framing (memory must survive
delays and interference, not just boost return), and a citation for "sparse reward can't teach
storage" (again: gradients, not salience gains). No overlap on the write side.

## 4. R2D2 — Kapturowski et al., ICLR 2019 "Recurrent Experience Replay in Distributed RL"

**Mechanism/writes.** "Memory" here means the **LSTM recurrent state**, trained by replaying
sequences with the stored-state + burn-in strategies to handle representational drift. There is no
episodic store and no write decision at all; retention is whatever the recurrent dynamics keep.
**Evaluated:** Atari-57 / DMLab return. **Relation:** included to delimit the term — much of the
"RL memory" line means recurrence + replay engineering; nothing to cite against our claims beyond
scoping language ("memory as recurrent state vs memory as store").

## 5. Episodic Meta-RL — Ritter et al. 2018, "Been There, Done That" (arXiv:1805.09692)

**Mechanism.** Meta-RL LSTM + DND with keys = task-context embeddings, values = **LSTM cell
states**. Retrieval reinstates a past cell state into working memory through a **learned
reinstatement gate**: `c_t = i_t⊙c_in + f_t⊙c_{t−1} + r_t⊙c_ep`.

**Writes.** Fixed schedule: cell state written **at end of each task/episode**, unconditionally.
No salience, no value signal on writes.

**Evaluated.** Reward/regret on contextual & compositional bandits (barcode/Omniglot contexts),
water maze, two-step task; frozen-weight probe blocks confirm memory (not gradient) driven reuse.
Analysis: the r-gate opens more on correct-action trials (p≪1e−20) — i.e., value-relevance emerges
**on the read/reinstatement side**.

**Relation to us.** The cleanest mirror image in the classic line: **the gate is learned for
reinstatement, not for storage**. Perfect one-line contrast for related work.

## 6. NGU — Badia et al. 2020 (arXiv:2002.06038) + Agent57 (arXiv:2003.13350)

**Mechanism.** Episodic memory of **controllable-state embeddings** (inverse-dynamics features),
**appended every step, no gating, reset empty each episode**. It exists to compute an intrinsic
exploration bonus: novelty ≈ 1/√(Σ kernel similarity to k-NN in memory), multiplied by an RND
lifelong-novelty modulator. Agent57 adds a bandit meta-controller over exploration/discount
mixtures; same memory. **Evaluated:** Atari-57 return, hard-exploration games.

**Relation to our surprise term.** NGU inverts our arrow: memory-relative novelty decides the
*reward* (behavior), not what memory *keeps*; surprising states change where the agent goes, then
get appended like everything else. We use surprise to scale **write strength into a persistent
bounded store**. Also a useful precedent that surprise must be computed against
*controllable/meaningful* features to avoid noise-TV traps — analogous to our surprise being LLM
predictive surprise, not pixel error.

## 7. Episodic Memory in Lifelong Language Learning — d'Autume et al. 2019 (arXiv:1906.01076); AMRL — Beck et al., ICLR 2020

**d'Autume mechanism.** Key-value store of raw examples, keys from a **frozen pretrained BERT
encoder** (a precedent for frozen-backbone memory keys); used for sparse experience replay (1%)
and MbPA-style local adaptation at inference. **Writes: RANDOM under budget** — write each example
with some probability; they report random writing beat their simple **surprisal-based** selection
in preliminary experiments, retaining performance with 50–90% memory reduction; learned selection
deferred to future work. **Evaluated:** retention across sequentially-presented text
classification / QA tasks — genuinely retention-flavored, but no typing of what survives and no
learned gate. **Relation:** the *random-write-at-equal-budget baseline is obligatory for us*; their
surprisal heuristic losing to random is a caution that raw surprise alone is weak — our claim is
precisely that the *value-modulated* combination beats both.

**AMRL.** LSTM + order-invariant aggregators (AVG/SUM/MAX) over all prior states, for gradient
decay and noise robustness; aggregates everything, no selectivity; return-only eval
(Minecraft/mazes). MAX-aggregation is at most a degenerate hard-selection by feature magnitude —
not value-gated, not learned as a write policy.

## 8. Prioritized Experience Replay — Schaul et al. 2015 (arXiv:1511.05952) ★ (closest classic analog)

**Mechanism.** Prioritizes **replay sampling**, not storage: `P(i) = p_i^α / Σ_k p_k^α` with
`p_i = |δ_i| + ε` (proportional) or `1/rank(i)`; IS correction `w_i = (1/N · 1/P(i))^β`, β annealed
to 1. **All transitions are stored; buffer is FIFO.** Evaluated on Atari-57 return (median 111%→128%).

**The precise difference from us.** PER re-weights *gradient exposure* of a complete, cheap,
non-parametric buffer — every transition remains recoverable, and a bad priority costs only
training time. We re-weight *what exists at all*: selective, weighted writes into a **bounded
parametric fast-weight store**, where an un-written or weakly-written experience is
unrecoverable and capacity is consumed permanently. PER prioritizes by learner TD error (what the
critic hasn't fit yet); our salience is task-value salience (distance-to-goal TD signal — what
*matters*), which is a different quantity with different failure modes (Isele & Cosgun below).

**The smoking-gun future-work paragraph** ("Prioritized Memories" extension): "Considerations that
help determine which transitions to replay are likely to also be relevant for determining **which
memories to store and when to erase them**." The classic line *named our problem in 2015* and, per
this sweep, never executed it as learned value-gated parametric writes. Lead citation for the
related-work paragraph.

## 9. Search sweep — learned/selective write gating, 2016–2026

- **Isele & Cosgun 2018, "Selective Experience Replay for Lifelong Learning" (AAAI).** The closest
  classic *selective-storage* experiment: a long-term episodic buffer beside FIFO, with four
  storage heuristics — surprise (|TD|), reward, global distribution matching, state coverage.
  **Finding: distribution matching won; surprise- and reward-based selection caused catastrophic
  forgetting.** MUST CITE and must answer: (i) their store feeds *gradient replay* for a full
  policy, which needs i.i.d.-like coverage — ours is an inference-time memory judged on typed
  recall, a different objective; (ii) their heuristics select *which transitions occupy a buffer*,
  not per-write strength; (iii) |TD|-of-the-learner ≠ distance-to-goal value salience. But this
  result plus d'Autume's random-write result means our experiments need **random-write and
  coverage/distribution-matched write baselines at equal budget**, or reviewers will supply them.
- **TVT — Hung et al. 2019, "Optimizing agent behaviour over long time scales by transporting
  value" (arXiv:1810.06721, Nature Comms).** MERLIN-family agent; writes still every-timestep. On
  a high-strength memory READ at t', it splices future value back to the attended past steps:
  `r_t += α · w_{t'}[t] · V̂_{t'+1}`. So the classics DID couple value with memory — but on the
  read/credit-assignment side. Second mirror-image citation alongside Ritter.
- **Neural Map — Parisotto & Salakhutdinov 2017 (arXiv:1702.08360).** Learned GRU-style *write
  operation* into a 2D spatial memory — but the write location is fixed by agent pose and a write
  happens every step; content-learned, not salience/value-gated, return-only eval.
- **Expire-Span — Sukhbaatar et al. 2021.** Learned per-memory *expiration spans* (learned
  forgetting) trained by task loss, over a cache of hidden states; end-to-end, non-parametric
  store, no value gating, mostly LM (+ small RL corridor tasks). Closest "learned retention"
  precedent; it learns *when to erase*, we learn *how strongly to write*.
- **Lu et al. 2022 (eLife), "when to retrieve and encode episodic memories":** neural-net cognitive
  model with a learned EM gate — for *retrieval timing*; encoding remains scheduled.
- LLM-era RL-trained memory ops (AgeMem-style store/discard tools, gated memory for long-context
  reasoning, MEMAUDIT budgeted-write evaluation) are 2025–26 developments outside this classic
  note — tracked in notes 12/17/23. Nothing pre-LLM surfaced doing value-gated writes.

---

## VERDICT

**(a) Does anything in the classic line already do value-gated selective writes into a bounded
memory? NO.** The write policies found: everything/every-step (MERLIN, NEC, NGU/Agent57, HCAM,
TVT, Neural Map, AMRL), fixed schedule (MFEC, Ritter — episode end), random-under-budget
(d'Autume), heuristic buffer composition for gradient replay (Isele & Cosgun — where TD/reward
selection *failed*), and priority over replay *sampling* with storage untouched (PER). Learned
gates appear exclusively on reads/reinstatement (Ritter's r-gate, MERLIN/HCAM retrieval attention),
credit assignment through reads (TVT), and forgetting (LRU, Expire-Span). PER explicitly flagged
"which memories to store and when to erase them" as an open extension. The specific object we
train — a value-salience-driven write-strength gate into a bounded parametric store, with a frozen
policy — does not exist in this line.

**(b) Does MERLIN's argument threaten or support our framing? SUPPORTS — with one phrasing
constraint.** MERLIN's insufficiency claim is about *end-to-end reward gradients propagating
through long encode→use delays*, and its remedy is unsupervised-predictive representations — which
our frozen pretrained LLM instantiates by construction. MERLIN itself keeps a return-prediction
decoder shaping stored latents, so "value should influence what memory holds" is *inside* MERLIN,
not against it. Our salience signal is dense, immediate, per-write, and never backprops through
the delay, so the infeasibility argument doesn't touch our mechanism; and `w = surprise ×
(1+β·salience)` keeps MERLIN's predictive signal primary with value as modulation. The one real
threat in this line is empirical, not MERLIN: Isele & Cosgun's reward/TD *selection* heuristics
losing to distribution matching, and d'Autume's random writes beating surprisal — both are
replay/buffer-composition settings, not per-write gain into an inference-time store, but they
dictate our baseline set (random-write, coverage-matched write, surprise-only, salience-only, at
equal budget) and they make the *ablation* `β=0 vs β>0` the load-bearing experiment.

**(c) What the related-work section must say about this line (draft skeleton).**
"Classic memory-augmented RL learned *where to read, never what to write*: MERLIN argues reward
gradients cannot select memory content over long delays and delegates encoding to unsupervised
prediction — while still writing every timestep; NEC explicitly declines learned write gating as
too slow to learn and writes all experiences; HCAM stores all chunks and stops gradients into
memory; Ritter et al. learn a gate for *reinstatement* and TVT transports value through *read*
attention — value meets memory only on the retrieval/credit side. Prioritized Experience Replay is
the closest analog, but it re-weights *sampling* from a complete non-parametric buffer and left
'which memories to store and when to erase them' as an explicit open extension; the few selective-
storage studies used fixed heuristics for *replay buffer composition*, where TD/reward selection
underperformed distribution matching (Isele & Cosgun) and random writing matched surprisal
(d'Autume). We differ on all three axes: the write itself is the learned object (a value-salience
gain over predictive surprise), the store is bounded and parametric so an unwritten experience is
unrecoverable, and evaluation is retention-typed at fixed budget rather than return. Following
MERLIN's argument, our representations come from a frozen pretrained model and the value signal is
a dense per-write scalar that never backpropagates through the storage delay."

**Three most relevant papers:**
1. **MERLIN (Wayne et al. 2018)** — the field's canonical position on what signal should drive
   memory formation; we inherit its constraint (unsupervised representations) and extend where it
   is silent (budgeted write selection); must be engaged head-on.
2. **Prioritized Experience Replay (Schaul et al. 2015)** — nearest classic mechanism
   (TD-prioritized *sampling*) plus the explicit "prioritized memories" future-work hook that our
   write gate finally executes; the precise replay-vs-write contrast defines our contribution.
3. **Isele & Cosgun 2018 (Selective Experience Replay)** — the only classic selective-*storage*
   experiment, and its negative result for reward/TD heuristics is the strongest empirical
   objection we must design baselines and framing against (d'Autume 2019's random-write result is
   the companion caveat).

---
*Sources: arXiv 1803.10760, 1703.01988, 1606.04460, 2105.14039, R2D2 ICLR'19, 1805.09692,
2002.06038, 2003.13350, 1906.01076, AMRL ICLR'20 (openreview Bkl7bREtDr), 1511.05952,
Isele & Cosgun AAAI'18, 1810.06721, 1702.08360. Deep-reads via ar5iv full text; short quotes are
as-extracted from full text — spot-check MERLIN §insufficiency quotes and the PER "Prioritized
Memories" extension paragraph against PDFs before citing verbatim in the paper.*
