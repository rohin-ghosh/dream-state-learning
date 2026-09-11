## Verdict

**Finish the causal checks, not another generation of lives.** Protect the lives already running; make the write replications, completion-frame test, and real-gym struggle test the critical path. Prepare the first v7 child, but do not let an uncalibrated classroom or an untested memory block consume the remaining experimental window.

The paper already has a defensible contribution: **successful fitting of experience text does not guarantee usable factual memory; the write recipe changes the behaviour transmitted; and text versus weight memory has no universal winner.** The new experiments should sharpen that claim, not make submission depend on demonstrating a generally improved child.

**Source boundary:** I have the supplied notebook excerpts, not separately accessible attachments or run artifacts. I cite their SEQ sections and named intervening entries. Actual process occupancy, remaining runtimes, and completed results after SEQ-035 are **unverified**.

## The next 48 hours

### Capacity and scheduling assumptions

At SEQ-035, the unfinished lives are R4 604/605/606 on node 1 and R4 600/R3 504 on node 2: **5 running lives**. Assuming each retains **1 GPU**, the supplied inventory leaves **11 GPUs** for new work.

Over the requested **48-hour window**, that gives:

- **768 GPU-hours** total capacity.
- **240 GPU-hours** conservatively reserved for unfinished lives.
- **528 GPU-hours** available for the decision queue.

These are **derived capacity figures, not measured runtime forecasts** [inventory: user; occupancy: SEQ-035]. When a life finishes, reclaim its reservation immediately.

**All allocations below are proposed GPU-hour ceilings.** The notebook does not provide reliable remaining runtimes for this full queue. Finishing early is success; do not pad a completed experiment to consume its reservation.

### Ranked decision queue

| Priority | Work | Proposed ceiling | What it decides; stopping rule |
|---|---|---:|---|
| **Blocking prerequisite** | **Interface canary**, including the outstanding seed0 probe chain | **8 GPU-hours** | Does each proposed write preserve parseable `ACT:` output, actual actions, and normal termination? Evaluate frozen, behaviour-only, memory-only, and combined adapters before expensive gym scoring. Quarantine a failing adapter rather than interpreting its task score as failed reasoning. C already produced **0 actions across 16 episodes**, so this is an observed failure mode, not optional instrumentation [SEQ-033, SEQ-035]. |
| **Highest scientific priority** | **Write-pretest replications on seed7 and seed8** | **96 GPU-hours** | Does the A/A_v3/B ordering recur, and does the mid-life adapter advantage survive outside seed0? Finish matched frozen, adapter, and same-sleep brief evaluations on both panels. Prioritize A, A_v3, B and brief; use Bs and the budget-matched cell to resolve a specific ambiguity, not as mandatory expansion. These seeds are already training B [SEQ-034–035]. |
| **Next** | **F completion rescoring, unrepeated control, and equal-exposure trio** | **16 GPU-hours** | Is B’s apparent recall owner-specific under a completion cue? At equal exposure, do additional forms help binding rather than merely strengthen a colour habit? Complete the corrected trio: **16 renderings per occurrence**, with **1, 4, or 16 templates**, across **3 banks** [“Cell family F…08:05 UTC”; SEQ-035]. |
| **Next, concurrent** | **F exposure ladder: R=64, K=16** | **8 GPU-hours** | Does moving toward repeated experience rescue extraction when completion cues and varied forms are already supplied? Start with the queued bank, then confirm any positive result across the remaining banks before calling it binding. Retain owner-versus-similar-owner, spill, absolute colour mass, and dose checks [SEQ-034–035; F implementation entry]. |
| **Next** | **Real-gym struggle test** | **144 GPU-hours** | Can a write carry a repeatedly experienced, decision-relevant lesson into a fresh-context encounter where it changes action and success? This is the realistic memory test requested by Rohin—not another isolated planted fact [SEQ-034]. Design below. |
| **Launch prerequisite** | **Reasoning-gym band recalibration** | **48 GPU-hours** | Is there usable headroom and measurement resolution in every selected family? Adjust difficulty toward the notebook’s proposed frozen-score band of **0.2–0.5 score units**, then remeasure exam and gate variability. Do not start a classroom life on the current near-floor band [SEQ-026–027]. |
| **Conditional** | **Preparation phase of the first v7 child** | **64 GPU-hours** | Can the child practise the intended thinking moves, receive varied teaching, and produce leak-clean experience suitable for a safe write? This is preparation and feasibility—not evidence of improved learning. Start GPU rollout only after the band and canary pass; keep one child state, even if evaluation shards run concurrently [SEQ-027; Rohin’s 08:25 UTC rulings; 04:30 UTC guard continuation]. |
| **Conditional attribution** | **Behaviour/memory block cells** | **96 GPU-hours** | Does a combined adapter’s benefit come from behaviour, memory, or their interaction? Compare frozen, behaviour-only, memory-only, and combined states on the same held-out struggle encounters and interface checks. Keep the proposed **rank-8 behaviour block** and **rank-32 memory block**, but do not assume their functions from their names [shared design ruling; SEQ-033]. |
| **Evidence closure** | Same-node controls, unfinished-life baselines, scoring and artifact checks | **48 GPU-hours** | Close the paper’s actual missing cells: final versus latest checkpoint, same-node brief/routine comparisons, matched mid-life controls, and safe attribution probes. Do not manufacture replication by rerunning the identical deterministic routine-only prompt [SEQ-031–035, especially the correction to SEQ-032]. |

**Total new-work ceiling: 528 GPU-hours.**

### Assignment for every GPU

Use logical slots where the notebook does not identify a current device. **Do not kill a process based on an inferred GPU index.**

| Device or verified slot | Initial assignment → refill within the window |
|---|---|
| Node 1: GPUs occupied by R4 604/605/606 | Finish those lives → checkpoint/export → missing final controls → struggle-test confirmation. |
| Node 2: GPUs occupied by R4 600/R3 504 | Finish those lives → final controls → attribution or struggle confirmation. |
| Node 2 GPU 6 | Seed7 write replication: **48 GPU-hours** ceiling. |
| Node 2 GPU 7 | Seed8 write replication: **48 GPU-hours** ceiling. |
| Node 1 GPU 2 | F rescoring/control/trio: **16 GPU-hours** → struggle: **32 GPU-hours**. |
| Node 2 GPU 3 | Finish the running B trajectory stage; F exposure ladder: **8 GPU-hours** shared ceiling → attribution: **40 GPU-hours**. |
| Node 1 GPU 3 | Finish existing seed0 probes and canary: **8 GPU-hours** → attribution: **40 GPU-hours**. |
| Node 2 GPU 4 | Finish the already-running R4 603 baseline probes → struggle queue: **48 GPU-hours** envelope. |
| Node 2 GPU 2 | Evidence closure: **48 GPU-hours** ceiling. |
| Remaining free node-2 GPU | Band recalibration: **48 GPU-hours** ceiling. |
| Remaining free node-1 slot A | Preparation: **48 GPU-hours** ceiling. |
| Remaining free node-1 slot B | Struggle: **48 GPU-hours** ceiling. |
| Remaining free node-1 slot C | Preparation: **16 GPU-hours** → attribution: **16 GPU-hours** → struggle: **16 GPU-hours**. |

Device assignments follow SEQ-027 and SEQ-034–035 where available; the remaining slots require a process check. Residual jobs count against their lane’s ceiling, not as extra capacity.

**Dependency rule:** if preparation or attribution is blocked, its GPU takes ready struggle-test controls, replication probes, or evidence closure. If F finishes in minutes rather than hours—as its throughput estimates suggest—release the lane immediately [F implementation entry]. No duplicate training into a shared output directory; SEQ-028 already documents that failure.

### Make the struggle test answerable

Use an existing real-gym encounter class where the frozen child repeatedly fails but a specific observation or strategy can help.

- **Experience:** collect repeated encounters and the child’s own decision-relevant noticings. Preserve occurrences; do not replace lived experience with a parent-authored answer corpus.
- **Receipt:** record what was repeatedly experienced, the exposure count, and whether those observations actually informed successful actions.
- **Test:** use fresh instances and a fresh context. Remove the experience record and brief from the weight-only condition.
- **Controls:** frozen; frozen plus the same experience summary; behaviour-only; memory-only; combined. Add a matched scrambled-binding or irrelevant-memory control where the task supports it.
- **Success:** better held-out action and task success attributable to the relevant write, with a functioning interface and no broad spill.
- **Failure:** reciting the lesson without using it, succeeding only when the answer remains in context, or improving solely through a general behaviour change.

**Do not require F to be positive before running this.** F diagnoses a controlled retrieval regime; the struggle test checks useful memory in the actual operating environment [SEQ-034].

### What to drop

- **No new v6 life.** That decision was already correct at SEQ-027.
- **No further rank/strength/exposure-order sweep of the old car-test regime.** Close the existing report; do not keep searching it for a positive result [SEQ-033–034].
- **No incorrect “equal-exposure” F cells.** The earlier varying-rendering trio is not the comparison claimed; the implementation entry explicitly corrects it.
- **No additional QA-form training sweep before the canary.** Finish and inspect already-trained C_tmem, but do not spend the sprint tuning around an interface-destroying representation [SEQ-033–035].
- **No classroom rollout on the present reasoning-gym settings** [SEQ-027].
- **No broad parenting-mode or negative-row factorial.** Those are follow-up questions unless a specific preparation failure makes one necessary.
- **No new full lineage comparison as a submission dependency.** Preparation may justify proceeding; it cannot establish the long-term claim.
- **No deterministic duplicate routine-only cells masquerading as independent life evidence** [SEQ-032 correction].

Before **2026-09-14 23:00 UTC**, export node-1 adapters, corpora, manifests, raw evaluations and reports, and verify they load on node 2. Do not assign node-1-only dependencies after that deadline. All experiments must finish by **2026-09-18**; reserve the interval to the **2026-09-25** paper deadline for analysis, writing and verification, not promised results [user deadlines].

## What the paper can now say

The supplied paper-status entry says the manuscript still uses the SEQ-022 cutoff. I have **not** inspected the manuscript itself.

### Completed car test: a bounded negative mechanism result

**Use this wording:**

> In the tested car-memory regime, no evaluated write produced clean out-of-context owner–colour binding under the registered criteria. Antecedent-based writes instead learned to read and revise facts supplied in context; occurrence-preserving bare-text writes produced surface recall and spill.

The completed study now covers the reported **rank-8 and rank-32 adapters**, tested strengths, and both exposure orders [SEQ-033–034].

**Do not say:** “LoRA cannot store facts,” “capacity is ruled out,” or “the fact was stored semantically but inaccessible.” Text-fit gain establishes improved prediction of training text, not a separately verified semantic memory. Also, B has a narrow owner-specific signal at one strength; “no signal anywhere” would contradict SEQ-033.

**Abstract:** yes—the bounded negative result and context-reading contrast belong there. F must remain separate until complete.

### Text versus weights: broader coverage, with a horizon-dependent counterexample

**Use this wording:**

> On the primary seen panel at the end of life, the frozen child supplied with its own brief matched or exceeded the adapter in **12 of 19 lives**; the adapter scored higher in **7 lives**. This endpoint ordering was not universal across life horizons.

That is the corrected tally, not a pooled result across both panels [SEQ-031–032, corrected].

At **512 episodes** in seed0, the adapter exceeds the same-sleep brief by **0.034 score units** on the seen panel; both score **0.2731 score units** on the unseen panel [SEQ-034–035].

**Abstract:** the endpoint comparison belongs. The mid-life result is currently a main-text qualification, not a headline. Promote it only if seed7/seed8 support it.

**Premature:** “weight memory precedes text memory across lives,” or “late collapse explains the population ordering.” The observed reversal is from one life; its proposed explanation is not a population-level attribution. Cross-node routine values are also not interchangeable [SEQ-033].

### The write recipe changes what the write carries

**Use this wording:**

> Rewriting the same source experience with different training recipes yielded routine-like behaviour on both panels, on the unseen panel only, or on neither panel.

For seed0, A scores **0.5293 / 0.2731 score units**; A_v3 scores **0.4896 / 0.2557 score units**; B scores **0.4817 / 0.2731 score units**, against matched frozen scores of **0.4845 / 0.2487 score units** [SEQ-033–035].

The cleanest same-corpus comparison is A versus A_v3. But it changes **both loss masking and training duration**: whole-text loss for **3 epochs** versus target-only loss for **1 epoch** [SEQ-031, SEQ-033].

**Abstract:** yes, in cautious form—“write recipes changed the behaviour transmitted.”

**Premature:** “target-only loss removes the routine,” “headers cause transfer,” or “multi-scale writing learns a better skill.” The present experiment does not isolate those causes. Also verify A’s actual rank from its artifact: SEQ-030 and SEQ-031/033 describe it inconsistently.

### QA-form collapse: a concrete systems failure, not a literature verdict

**Use this wording:**

> A QA-formatted write destroyed the action interface: the child emitted bare answers without the required action marker, producing **0 actions across 16 episodes** and **0.000 score units** on both panels.

This is directly observed [SEQ-033].

**Abstract:** optional, as a short interface-fragility clause. Keep the detailed diagnosis in the main text.

**Premature:** “QA memory does not work,” “TMEM fails,” or “EOS caused collapse.” QA format, chat template, objective and termination targets are bundled; C_tmem evaluation was still pending at SEQ-035.

### Additional correction: the gate is not a guarantee

R4 603 finished with a harmful committed adapter: **−0.062 score units** versus frozen on the final seen-panel probe [SEQ-035]. That strengthens the existing warning that gating does not reliably prevent degradation. The ledger diagnosis is pending; do not attribute the failure to a particular gate mechanism yet.

## Recommended abstract spine

> We study whether a frozen language-model agent can turn its own successful experience into usable weight memory through sleep-time adapter rewriting. In a one-lineage case study, write recipes changed the behaviour transmitted, including brittle task routines and interface failure. A controlled fact-memory test found no clean out-of-context binding in the tested regime, despite improved training-text fit and strong reading of facts supplied in context. At end of life, a frozen model reading its own brief matched or exceeded its adapter in **12 of 19 lives**. These results distinguish fitting experience text from retrieving facts and preserving useful behaviour.

Sources: SEQ-031–035. **No claim of successful continual learning, improved general reasoning, positive completion-frame memory, or effective two-block separation belongs in the abstract yet.** The paper is already viable without those results.