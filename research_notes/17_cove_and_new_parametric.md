# 17 — COVE and New Parametric-Memory Papers: Collision Assessment

Date: 2026-08-10

## Our idea (axes for scoring)

1. **Learned value/attention head** trained on an **external outcome/reward** signal (frozen backbone).
2. Head decides **what gets written** into a **PARAMETRIC fast-weight** memory.
3. **OFFLINE, CROSS-EPISODE "sleep"** consolidation (not online/within-episode).
4. Value is **RELATIONAL** (per-dependency, not per-item).
5. **Selective forgetting** that keeps relational structure and sheds episodic detail.

All four papers verified to exist. arXiv IDs confirmed via abstract pages. Note: 2608.01234
is dated Aug 2 2026, consistent with today (2026-08-10). Mechanism extractions below are from
the HTML full text; a few substrate details are underspecified in the papers and flagged.

---

## 1. COVE — arXiv:2608.01234 (Aug 2 2026) — PRIORITY

Full title: *"Learning What to Remember and What to Internalize in LLM Self-Evolution via
Adaptive Memory-Parameter Coordination."* Backbone in experiments: Qwen3-8B.

**Mechanism.** COVE splits self-evolution into a **harness/Memory side** (volatile facts kept
external, editable) and a **parametric side** (stable behavioral knowledge internalized into
weights). Three components: task-aware routing, stage-aware scheduling, knowledge optimization.

- **(a) What-to-internalize decision = HYBRID (rule + judge), NOT a reward-trained head.**
  Volatility labeling is heuristic: "Volatile knowledge depends on external surface forms, such
  as API names or table schemas... explicitly protected from internalization." A "constrained
  judge" (LLM) assigns labels {volatile, stable, strategic}. Promotion to volatile is a heuristic:
  "repeated correction as evidence that the entry depends on shifting external state." The
  task-aware router is feedback-conditioned but **no explicit reward signal trains the router**;
  it queries the judge for a structured decision record. So the decision is judge/heuristic-driven,
  not a learned value module trained on outcomes.
- **(b) "Anti-recitation" = keep reasoning / drop volatile surface form.** Implemented as a
  loss/reward penalty, not a learned value head: volatile entries have names randomly renamed
  before training, and `R = R_task - lambda * I[uses stale or unobserved volatile name]`. Stable
  knowledge is exempt, "allowing reusable patterns to be internalized." This is *spiritually*
  our "keep structure / drop detail" — but the discarded axis is **surface-form volatility**
  (API names, schemas), NOT relational-vs-episodic structure.
- **(c) OFFLINE, CROSS-EPISODE.** Triggered by performance plateau over a window of w episodes
  (success rate / avg reward below threshold). Matches our offline-consolidation axis.
- **(d) Parametric substrate: underspecified.** "supervised fine-tuning or reinforcement learning"
  on the weights; paper does not state LoRA vs full-weight. **Not fast-weights.** (FLAG: uncertain.)
- **(e) No separate reward-trained value/attention head.** Anti-recitation is a loss term.
- **(f) Value is PER-ITEM, not relational.** Utility judged per stable memory entry via held-out
  A/B eval ("if the performance drop... is below a threshold... marked as internalized").

**Verdict on COVE vs our contribution — see dedicated section below.**

---

## 2. User as Engram — arXiv:2606.19172 (Jun 17 2026)

*"Internalizing Per-User Memory as Local Parametric Edits"* (Bojie Li, Pine AI). Hippocampus
(sparse local engram) / neocortex (shared skill) framing — same CLS rhetoric we use.

- **(a) Write decision = HEURISTIC.** Facts reduced to where/what: trigger suffix N-gram hashes
  to sparse row addresses in a hash-keyed memory table. Insertion strategies (UNEMBED_P closed
  form, OPT gradient, Joint OPT) optimize *how* to edit predetermined content, not *what* to edit.
- **(b) No value/reward.** Objective is next-token probability toward the gold answer.
- **(c) OFFLINE / cross-session.** Facts consolidated into per-user override table after interaction.
- **(d) Substrate: engram hash-keyed table + one shared (not per-user) LoRA for reasoning skill.**
  Content stored surgically in disjoint hash slots; ~33,000x smaller footprint than per-user LoRA;
  edits compose additively/losslessly across users.
- **(e) Pure personalization** (medical history, preferences, contacts). No agent/RL/decision-making.
- **(f) No selective forgetting by type.** Facts persist until explicitly removed by app logic.

Collision: **LOW-MODERATE.** Shares CLS/hippocampus framing + parametric edits + offline write,
but heuristic, personalization domain, no reward, no forgetting. Strongly differentiable.

---

## 3. Parametric Memory Head (PMH) — arXiv:2604.23388 (Apr 25 2026, SIGIR 2026)

*"A Parametric Memory Head for Continual Generative Retrieval"* (Mekonnen, Tang, de Rijke).
Domain is generative IR (GenIR): decode docids from queries; the memory head absorbs new docs.

- **(a) Write = HEURISTIC via decoding-time access statistics.** "updates only a fixed budget of
  memory values selected using decoding-time access statistics" — activation frequency, not reward.
- **(b) Driven by document ingestion**, not reward. Objective is docid generation accuracy.
- **(c) ONLINE / continual** across sequential disjoint corpus increments.
- **(d) Substrate: product-key memory with fixed addressing**; decoder hidden states sparsely
  query PMH for residual corrections in hidden space.
- **(e) Document retrieval, NOT agent memory.**
- **(f) Has a usage-based selective-retention rule** ("prioritizing entries frequently activated
  by the current slice and rarely used in prior sessions") — but that is frequency/recency, not
  information-type (relational vs episodic), and not reward.

Collision: **LOW.** Different domain (GenIR docs), heuristic, online. Only loose overlap on
"isolated parametric memory head + forget budget." Differentiable.

---

## 4. RECONCILE — arXiv:2606.26806

**The earlier survey label was CORRECT; the new list's description is WRONG.**

Actual paper: *"Memory Depth, Not Memory Access: Selective Parametric Consolidation for
Long-Running Language Agents"* (Haoliang Han, Jun 25 2026). It evaluates **EVAF**, a
"surprise- and valence-gated LoRA consolidation" mechanism. So our earlier "EVAF / Memory Depth,
keep-parametric-vs-discard split" label is accurate.

The new list's claim — "online test-time fast weights consolidating context traces with
scaling-law analysis over multi-day sessions" — is **inaccurate on two counts**: (i) substrate
is **LoRA**, not generic fast-weights framed that way; (ii) **there is NO scaling-law / multi-day
result** — evaluation is synthetic 200-event streams across 10 users on GPT-2 / TinyLlama, no
scaling curves. (Do not rely on a scaling-over-sessions result from this paper for our scaling axis.)
Companion: arXiv:2606.29916 *"EVAF: A Test-Retest Protocol for Selective Parametric Consolidation"*
is a separate protocol paper — check if our scaling-axis note conflated the two.

Mechanism:
- **(a) Write = HEURISTIC gate**, not learned: `g_t = sigma(k_s(s_t - tau_s)) * sigma(k_v(v_t - tau_v))`.
- **(b) "valence" is INTERNAL, not external reward:** "valence score v_t from embedding similarity
  to the user's durable goal and preferences." Surprise = token NLL. Both from the model's own
  representations — **not** an external outcome/reward signal.
- **(c) ONLINE / within-episode** ("For each event x_t... enters the buffer").
- **(d) Substrate: LoRA** ("the adapter is a LoRA module; replay and an L2 anchor act as drift guards").
- **(e) No scaling laws / multi-day.**
- **(f) No selective forgetting by info type** — explicitly future work ("forgetting is not solved").

Collision: **MODERATE.** This is the closest paper to our *value-gated parametric write* idea in
spirit (goal-conditioned durable behavior, valence gating, "memory depth" = what continues to
shape behavior after context unload). But: gate is **heuristic** (not a learned reward-trained
head), valence is **internal similarity** (not external outcome/reward), consolidation is
**online within-episode** (not offline sleep), and it is **per-event** (not relational). Differentiable.

---

## Collision ranking (highest -> lowest)

| Rank | Paper | Write decision | Substrate | Timing | Forget-by-type | Reward-trained value | Severity |
|------|-------|----------------|-----------|--------|----------------|----------------------|----------|
| 1 | **COVE 2608.01234** | Hybrid judge/heuristic + loss penalty | Weights (SFT/RL; unspec) | **Offline, cross-episode** | Yes — surface-form volatility (keep reasoning) | No | **HIGH** |
| 2 | **EVAF / Memory Depth 2606.26806** | Heuristic surprise×valence gate | LoRA | Online, within-episode | No (future work) | No (internal valence) | **MODERATE** |
| 3 | **User as Engram 2606.19172** | Heuristic hash-key | Engram table + shared LoRA | Offline | No | No | **LOW-MOD** |
| 4 | **PMH 2604.23388** | Heuristic access stats | Product-key memory | Online continual | Usage-based only | No | **LOW** |

Key: **none of the four uses a learned value head trained on external reward, none uses relational
per-dependency value, and none does forgetting on a relational-vs-episodic axis.** Those three are
where our defensible novelty concentrates.

---

## COVE VERDICT (does it occupy our contribution?)

**COVE is the biggest collision but does NOT fully occupy our contribution — it is differentiable,
provided we position sharply.**

What COVE DOES claim, overlapping us:
- The coarse thesis "learn what to internalize vs keep external" during **offline, cross-episode**
  consolidation.
- A "protect stable structure, don't memorize volatile detail" mechanism (anti-recitation) that
  reads at headline level like our "keep structure / shed episodic detail" selective forgetting.

What COVE does NOT do (our open ground):
1. **No learned, reward-trained value head.** COVE's decision is a rule + LLM-judge + a fixed-lambda
   anti-recitation loss penalty. Our core claim — a *small value/attention head trained on an
   external outcome/reward signal over a frozen backbone* — is not present.
2. **Value is per-item, not RELATIONAL.** COVE scores utility per knowledge entry via A/B eval.
   Our per-dependency / relational value is untouched.
3. **The "drop detail" axis differs.** COVE drops **surface-form volatility** (API names, schemas)
   via random-renaming + name-penalty. We drop **episodic detail while keeping relational
   structure**. These are different partitions of "what to forget"; COVE's is lexical/interface
   volatility, ours is structural/relational. Do not let a reviewer collapse them — this is the
   sharpest line of separation on the selective-forgetting axis.
4. **Substrate.** COVE internalizes into standard weights (SFT/RL); it is not a **fast-weight**
   store, and does not frame consolidation as fast-weight writes. (FLAG: substrate underspecified,
   so avoid overclaiming this difference in writing without re-checking the camera-ready.)

**Bottom line:** COVE occupies the *what-to-internalize* framing and a *volatility-based*
anti-memorization mechanism during offline consolidation. It does **not** occupy (a) the
learned reward-trained value head, (b) relational/per-dependency value, or (c) forgetting on a
relational-vs-episodic axis. Our contribution survives, but the paper draft **must** explicitly
contrast against COVE on exactly points 1-3 above, and must avoid pitching our headline as merely
"decide what to internalize / don't memorize volatile detail" — that framing is now taken.

### Uncertainties to resolve
- COVE parametric substrate (LoRA vs full-weight) — not stated in v1; recheck before claiming
  the fast-weights distinction in print.
- Whether COVE's router has any implicit reward-shaping we under-read (v1 says no explicit reward
  trains it, but "task-aware routing" + RL knowledge optimization warrants a second pass).
- 2606.26806 vs 2606.29916 (EVAF protocol paper): confirm which our scaling-axis note referenced.
