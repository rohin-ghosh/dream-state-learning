# Memory replay follow-up — design only

2026-09-12. **Recommendation: the proposed two-arm fixed-update comparison is a useful, bounded next experiment, with the interpretation and budget conventions below. Await Main's confirmation before implementation.** No code, new corpus, launch or model call was created. Only this design document was written after completing the separate raw-result review.

## 1. Comparison and estimands

Start both arms independently from each **original teach parent**, seeds0/1/2—not from SEQ105's continued adapters. Retain rank8, alpha16, dropout0.05, lr3e-4, batch4, grad_accum1, unchanged training masks/EOS/templates, and one carried adapter with a fresh AdamW optimizer. Parent and continuation optimizer seed match. Both arms finish160 new updates, therefore **240 cumulative lineage updates**, not320.

| Arm | Fixed material | Epochs | New updates | New exposures per memory fact |
|---|---|---:|---:|---:|
| Mixed replay | Original16 memory + fixed16 original arithmetic teach rows | 20 | 160 | 20 |
| All-memory comparator | Original16 memory rows only | 40 | 160 | 40 |

**Primary estimand:** under a fixed160-update budget, compare allocating half the example presentations to original arithmetic replay against allocating all presentations to memory. Report paired differences in memory recall and retained ACT/PREDICT behavior. This is not a pure effect of replay with memory dose held constant: the all-memory arm has twice the new memory exposure. Same optimizer seed also does not make the differently sized/shuffled corpora have identical stochastic updates.

**Secondary, differently labeled estimand:** mixed160 versus inherited SEQ105 memory-only80 has equal new memory exposure (20 presentations/fact), but mixed has twice the updates and additional arithmetic exposure/token cost. It is an equal-memory-exposure anchor, not another fixed-update comparator or an unconfounded replay effect. Do not rerun or count the inherited SEQ105 arm as a new replicate.

The original parent already saw each memory fact four times. Lifetime memory exposures are24 for mixed,44 for all-memory40, and24 for SEQ105. Report both comparisons without choosing whichever supports the preferred narrative. A mixed arm meeting the progression gate does not by itself demonstrate superiority to all-memory40.

## 2. Freeze the smallest material selection

Use the shared original `teach.json`, SHA-256 `2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c`, whose bytes match across original seeds. “First16 arithmetic rows” means the first16 records with `view="addition"` in that file's existing list order, **not** lexicographic IDs or cases selected by recent failures:

`011,039,055,029,048,000,052,017,036,046,063,019,057,030,012,015`

These are suffixes of `train-addition-NNN`, each linked to the corresponding original `source-addition-NNN`. Example: train-addition-011 retains its existing rendered question about13+17 and target `PREDICT: 30\nACT: 30`.

Select those16 IDs plus all16 memory IDs, then retain the selected records in their **original overall corpus order**. Preserve each complete record, including its existing `order` field, spans and metadata; do not regroup memory ahead of arithmetic or renumber fields. The all-memory40 material is the same16-row subset already used in SEQ105, subset SHA-256 `758960c4bbfe1ae5328e30a25ebcf767f9d5ab9c3e968fe6c31e5470adca61fd` when using its unchanged serialization.

All32 mixed records are original training records. There are16 existing factual assignments and16 existing arithmetic examples, not32 new facts. No dev/confirmation labels enter training. No new objective, loss weighting, balancing scheme, declarative/canonical interface, fact bank or additional probe is needed.

## 3. Exact native token accounting

The following totals are independently summed from the original native per-row audits; actual native preparation must reproduce them. No new tokenizer call was made for this design.

| Material / arm | Input tokens per epoch | Supervised tokens per epoch | Input presentations over fit | Supervised presentations over fit |
|---|---:|---:|---:|---:|
| Selected arithmetic16,20 epochs | 950 | 218 | 19,000 | 4,360 |
| Memory16,20 epochs (SEQ105 anchor) | 704 | 32 | 14,080 | 640 |
| Mixed32,20 epochs | 1,654 | 250 | **33,080** | **5,000** |
| Memory16,40 epochs | 704 | 32 | **28,160** | **1,280** |

Mixed has28,080 ignored-context presentations versus26,880 for all-memory40. Mixed's640 supervised memory-token presentations are320 colors plus320 EOS; all-memory40 has640 colors plus640 EOS. Arithmetic target counts include the original complete PREDICT/ACT response and EOS. Selected arithmetic sequences range57–61 total tokens, versus44 for memory.

Both arms present640 examples and take160 updates. Nevertheless, mixed has about17.47% more unpadded input tokens and3.90625× the supervised tokens. Half the examples does **not** mean half the supervised tokens: memory accounts for32/250=12.8% of mixed's supervised-token count. This is not a claim that its gradient contribution is exactly12.8%; existing batch loss normalization and gradient magnitudes also matter. Do not introduce corrective loss weights to “fix” this difference.

Consequently label the comparison **update-matched, not token-matched, FLOP-matched, time-matched or loss-mass-matched**. Report actual native tokens, training seconds, worker windows and full reservation separately.

## 4. Readout and prospective progression

Every executed arm gets both unchanged endpoints: original dev48 (32 arithmetic +16 memory) and exact16 training-prefix recall, with separate raw captures. Keep temperature0, readout seed20260912 and64-token output caps. No new OFF/HF/confirmation calls. The existing alternate dev memory wording tests the same16 facts, not new factual generalization.

Run the **complete seed0 pair first**. A simple fixed order is mixed then all-memory40, using separate children and a fresh optimizer for each; do not stop the comparator because the mixed outcome is already visible. Assess progression only after both arms have valid terminal evidence and both mandatory panels.

Proceed to **both** seed1 and seed2 pairs if seed0 mixed meets all predeclared thresholds:

- Dev memory ≥15/16 and exact memory ≥15/16.
- PREDICT-before-ACT adherence ≥30/32 and correct ACT ≥31/32.
- Both seed0 arms' technical completion/provenance/readout/cleanup checks pass.

No comparator-score or pairwise-superiority condition is added. Once progression is triggered, do not use seed1's outcome to decide whether to run seed2. If the gate is missed, retain/report the full seed0 pair, the missed conditions and the two unrun pairs; do not lower thresholds, add epochs or substitute another sentinel. A technical failure is not a zero scientific score.

This is explicitly **outcome-gated staged follow-up**, not unconditional three-seed replication. The seed0 choice and thresholds are prospective for these new arms but informed by prior SEQ105 observations. They are readiness criteria, not statistical significance or a general G1 gate. If later pairs run, report every arm/seed; never select seed2 because it retained behavior previously.

## 5. Feasibility:1200s per pair and90 A40-minute envelope

**Interpret1200s as one pair controller on one A40, running the two arms sequentially, including CPU gaps and140s cleanup reserve.** If1200s instead means per arm, or simultaneous occupancy of two GPUs for1200 wall seconds, all three pairs could reserve120 device-minutes before margin and would exceed90. Confirm the one-device pair interpretation before implementation.

Actual SEQ10580-update memory-fit measurements:

| Seed | Trainer loop (s) | Fit worker including load/cleanup (s) | Dev48 worker (s) | Exact16 worker (s) |
|---|---:|---:|---:|---:|
| 0 | 21.0 | 69.18 | 88.16 | 78.66 |
| 1 | 19.4 | 63.54 | 152.61 | 78.84 |
| 2 | 19.1 | 63.58 | 113.23 | 77.35 |

Rough forecast, not a guarantee: memory40 doubles trainer work to38–42s; retaining observed fixed overhead suggests an83–90s fit worker. Mixed has33,080/14,080≈2.349× the original unpadded tokens; longer padded sequences can raise cost further. A45–58s training loop and roughly89–107s fit worker are plausible estimates, not equal-compute assumptions.

Using the previous full-controller timings, two endpoint sequences and these longer fits gives approximately**740–860s per sequential pair**, before any additional external release-observation delay. The1200s controller has a1060s productive window before reserving140s for cleanup: plausible observed-performance headroom, but not a hard completion guarantee. Source validation/loading and repeated native model-file hashing are included in the earlier controller overhead rather than assumed free.

Important downside: seed1 previously capped23 arithmetic outputs, making its dev worker materially slower. If either new arm caps many more dev or exact responses, or model loading stalls, the pair can exceed the forecast. Do not shorten training, skip the second arm/exact panel or increase output caps to force completion. Preserve partial evidence and label an exhausted pair operationally incomplete.

Three sequential pair controllers at1200s each reserve at most**60 A40 device-minutes**, leaving**30 minutes within the90-minute aggregate envelope** for external reservation/startup/release delays and scheduling margin. Main must track actual summed device occupancy, not just parallel elapsed wall time. Prior release-observation delays after controller completion were roughly155–208s per seed; do not assume they vanish. Prefer prompt release collection and no reservation held idle between scheduled pairs. No lease extension is implied.

Workload ceiling if all pairs run: six fits/960 new updates,384 generations,16,818 readout input tokens and24,576 maximum output tokens. Seed0 alone is two fits/320 updates and128 calls. Actual generated tokens must be reported because repetition can dominate inference cost. Training tokens over three full pairs are183,720 input and18,840 supervised presentations; neither these totals nor native seconds justify calling the arms compute-matched.

## 6. Minimal readiness checklist

1. Main confirms this design, fixed arithmetic list/order, pair execution order, gate and one-device1200s pair convention; no implementation before confirmation.
2. Original parent hashes and full single-adapter warm load match; children start from parent cumulative80 and finish240 with matching seeds/fresh optimizers.
3. Native CPU preparation reproduces the unchanged selected records/masks, token totals,160 steps per arm and no truncation/packing/template changes; only inherited training sources are used.
4. Existing separate dev48/exact16 capture/scoring and worker ownership/cleanup checks remain intact. Freeze the staged progression before scores, retain all raw outputs, validity/caps and per-case changes.
5. Main logs the prospective90-minute full envelope, checks real lease/capacity, and accounts for both arms plus140s cleanup before starting a pair. Failure preserves evidence, never changes its estimand.

**Disposition:** scientifically useful as a small replay-allocation comparison, computationally plausible within the stated convention, but neither causally pure nor guaranteed to complete under extreme capped-generation behavior. No new framework or guard specification is needed. **DESIGN ONLY — awaiting Main confirmation.**
