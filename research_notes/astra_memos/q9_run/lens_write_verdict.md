## Verdict

**The write is not a neutral container for experience. Its representation and training objective select what becomes easy to produce: a routine, a context-reading skill, a recitation habit—or an answer format that prevents action.** The current evidence supports that operational claim. It does **not** yet separate the effects of loss masking, training exposure, and contextual representation.

Use A as the **routine-transfer positive control**, not as evidence of general experience memory. Keep contextual behaviour writes under test. Do not admit a QA-shaped memory write without an interface check.

### What the seed0 table establishes

Scores below are **unitless task scores**, at a horizon of **512 episodes**. Use the corrected frozen references, not the earlier life-probe or different-generation-seed baselines. [SEQ-034–035]

| Write | Seen-panel score | Unseen-panel score | Supported reading |
|---|---:|---:|---|
| Frozen | 0.4845 | 0.2487 | Matched reference |
| A: whole-text loss, **3 epochs** | 0.5293 | 0.2731 | Routine on both panels |
| A_v3: same pieces, target-only loss, **1 epoch** | 0.4896 | 0.2557 | No demonstrated routine transfer |
| B: episode and local windows | 0.4817 | 0.2731 | Routine-like result on unseen panel only |
| Bs: episode windows only | 0.4878 | Not reported | Seen-panel birth plateau |
| C: QA, chat template, EOS | 0.0000 | 0.0000 | Interface collapse |
| Frozen + horizon-matched brief | 0.4952 | 0.2731 | Below A on seen panel; tied on unseen panel |

**Source:** SEQ-035 table; trainer definitions in SEQ-031 and SEQ-033. “No demonstrated transfer” is deliberately narrower than “learned nothing.”

## What explains the differences—and what remains unresolved

### A versus A_v3: the training package matters; the responsible ingredient is unidentified

A and A_v3 use the same **856 pieces**, but change both the supervised spans and the number of training passes. A supervises the entire text, including headers, for **3 epochs**; A_v3 supervises target spans for **1 epoch**. [SEQ-031]

A plausible mechanism is that whole-text supervision and repeated exposure strengthen a broadly triggered continuation habit: produce and execute the six-pass routine. Target-only training may remove useful cue supervision, deliver insufficient exposure, or both.

**We cannot yet say which.** In particular, SEQ-031’s suggestion that transfer comes “not from the target content” is too strong: target content might transmit the routine after sufficient training. The missing crossed trainer cells decide this.

### B versus A_v3: context changes transfer, but “better generalisation” is not established

Under target-only training for **1 epoch**, B reaches the unseen-panel routine value while A_v3 does not. But B also changes corpus size and exposure: it contains **7,415 items** and **5.15 million target tokens**. Thus this is not a clean context-only contrast. [SEQ-032–033]

The leading representation hypothesis is **conditional routine activation**: contextual training teaches the routine together with situation cues, rather than making it a default response everywhere. The car test makes that mechanism credible: antecedent writes teach the child to use an observation currently in context, without establishing owner-specific retrieval when the observation is absent. [SEQ-025; SEQ-034]

But alternatives remain:

- B simply supplies more effective training exposure.
- The panel split reflects brittle prompting or generation thresholds.
- Equal aggregate scores conceal different action sequences.

Therefore call B **panel-dependent routine transfer**, not selective reasoning or improved generalisation. Read the action ledgers before claiming the same routine actually fired.

**Bs does not yet establish that local views caused B’s unseen-panel gain.** Its unseen-panel result is missing. The local-view attribution in SEQ-035 is premature; even after that result arrives, exposure must be controlled.

### The car test supplies the mechanism warning

The completed tested configurations at LoRA ranks **8 and 32** did not produce clean out-of-context binding. Antecedent writes learned context reading; occurrence-preserving bare text produced the only owner-specific signal, but with habit-like spill. Increasing rank or changing adapter strength did not rescue clean extraction in that tested regime. [SEQ-033–034]

That means:

> **Fitting experienced text is not the same as making its information retrievable under the intended cue.**

It does not establish that factual memory is impossible, or that capacity never matters. Completion-frame retrieval and the higher-exposure F regime remain unresolved in this record. [SEQ-034–035]

### The brief limits the advantage we can claim

At this horizon, A beats the same sleep’s brief by **0.034 unitless score points** on the seen panel, but ties it on the unseen panel. [SEQ-035] That supports a horizon-specific advantage in routine expression—not a generally richer weight memory.

The end-of-life tally—brief at least as good in **12 lives**, adapter better in **7 lives**—also prevents a blanket “weights beat text” conclusion. [SEQ-034]

## C: an interface veto, not proof that every QA or EOS write must fail

C produces bare pass-list answers without `ACT:` and makes **0 actions in all 16 evaluated episodes**, scoring zero on both panels. [SEQ-033] It has learned something operationally powerful: **answer and stop instead of act**.

The lesson applies to **every proposed QA-form or EOS-terminated write for this child**: treat format and termination as learned behaviour, not harmless packaging. A memory block can overwrite the interface before its memory content gets tested.

But C bundles QA conversion, chat framing, answer-only loss, and EOS supervision. It does **not** isolate EOS as the cause or prove that every QA write collapses.

**Decision:** run the parseable-`ACT:` and premature-termination canary before task scoring and before committing any write. Test the memory block alone and the combined adapter; do not assume the behaviour block will repair it. Keep the proposed block architecture, but make interface survival a prerequisite for interpreting memory performance. [SEQ-033]

## What seed7 and seed8 must show

These are different-life replications, not merely reruns of the same training randomness. Their pretests were still running at the notebook cutoff. [SEQ-034–035]

| Reading | Required replication result |
|---|---|
| **A reliably carries the routine; A_v3 does not** | Within each life, A must reproduce routine execution on both panels while A_v3 remains near its matched reference and lacks that execution pattern. If the contrast reverses, restrict the claim to seed0. |
| **B carries a conditionally activated routine** | Repeat the unseen-only action-pattern contrast within each life. If B transfers everywhere or nowhere, contextual representation may still matter, but the specific panel-selectivity claim fails to generalise. |
| **Local views enable B’s unseen transfer** | Bs must fail to carry the routine on the unseen panel where B carries it, with an exposure-matched comparison excluding “more training” as the explanation. |
| **C’s recipe reliably destroys the interface** | Replicate missing `ACT:` output and premature stopping—not merely lower reward. Interface survival in another life would make collapse conditional, while preserving the need for the canary. |
| **Weights precede the brief at mid-life** | A must exceed the same-horizon brief on the seen panel within each life. The unseen-panel tie should be reported separately, not folded into an overall adapter win. |

**All comparisons need same-node frozen, brief, and routine controls.** The routine-only unseen-panel result differs across nodes despite matched software versions; the cause is unresolved. Do not require replications to hit the node-specific score **0.2731**. Require the matched behavioural contrast. [SEQ-033, “Node effect check”]

These replications cannot themselves establish factual binding; that requires the owner-versus-matched-owner extraction controls.

## The three most informative next cells

These are **proposed cells**, each hard-capped at **4 GPU-hours including evaluation**, per your budget—not verified runtime estimates.

| Next cell | Controlled change | What it decides |
|---|---|---|
| **A, whole-text loss, 1 epoch** | Same seed0 pieces, initialisation, optimiser, rank, packing and evaluation as A; shorten training only. | Transfer would show that whole-text supervision can work without the longer schedule. Failure would show that whole-text supervision alone is insufficient at this exposure. |
| **A, target-only loss, 3 epochs** | Same setup as A_v3; extend training only. | Transfer would show that additional training rescues target-only writing. Failure, alongside successful short whole-text training, would favour supervised-span selection. If only original A works, the ingredients interact or require a joint exposure threshold. |
| **C without supervised EOS** | Preserve QA rows, chat framing, answer content and optimisation; mask the terminal EOS target only. Verify that rendering does not insert another supervised termination target. | Interface recovery would implicate EOS supervision. Continued bare-answer output would show that removing EOS alone is insufficient; QA/chat/answer-form training remains implicated. Neither outcome establishes memory retrieval. |

The crossed A cells separate the existing loss-mask and epoch factors; they do **not** make supervised-token counts equal. Log those counts and update counts explicitly.

### Plan for the requested 48-hour window

- **First:** harvest already-running seed7/seed8, Bs-unseen, B_match, C_tmem and F results; audit action traces and matched references. Do not duplicate their training.
- **Next:** run the crossed A cells in parallel; run the EOS ablation after checking the C rendering. Reserve evaluation time inside each hard cap.
- **Then:** freeze the verdict at the strongest replicated level: routine transfer, conditional transfer, or interface failure. Carry any surviving memory representation into the real-gym struggle test; do not promote training-text fit into a memory claim.

**Unverified:** raw action ledgers, B_match’s exact matching rule, completed replication results, C_tmem outcomes, F outcomes, and runtimes for the proposed cells. The supplied evidence contains SEQ sections rather than separately lettered attachments; the citations above refer to those sections.