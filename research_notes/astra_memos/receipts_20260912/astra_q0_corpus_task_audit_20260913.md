# Q0 corpus/task audit — 2026-09-13

**To Main: no validity-critical code/data defect found in the checked immutable v1 projection. Full-dose work need not pause on this audit.** This answers Rohin messages31/32 and the 04:44UTC relay, not whether Q0 has acquired its map. Q0 is a consistent but stronger-than-simple-storage test: conditional association, held-wording extraction, exact action production and locality. Its loss directly trains only one of those surfaces. No v2 implementation was inspected or certified.

## 1. Labels, visibility and train/test compatibility

The map is `AUTH = orientation[slot] XOR mode`, `DERANGED = AUTH XOR 1`, with orientation `(0,1,1,0,1,0,0,1)` and actions `0 → -mem2reg`, `1 → -gvn`. `V_AUTH` has AUTH's labels; unary ignores mode. The recomputed AUTH/DERANGED labels match the original material's W+/W− labels exactly (`gpu/astra_pairwise_q0.py:188`; source construction at `organism_v6/multikey_writer_gateway_simple.py:152`). Opposite labels are trained in **separate fresh fits**, not contradictory examples mixed into one fit. They disagree on 100% of keyed targets, despite sharing prompts and action vocabulary.

Source-only checks establish:

- **128 exact rows:** 8 opaque IDs × 2 modes × 8 wrappers; **64 held rows:** the same 16 ID/mode keys × 4 different wrappers. Prompts are disjoint; labels and keys agree across panels. Held means wording transfer, not unseen-key learning.
- Both maps are 64/64 balanced in training and 32/32 held. Constant, ID-only, mode-only, stratum-only, template-only and checked template/mode shortcuts score exactly 50%. All 32 training quartets are 2/2 balanced, including unary; four identical sweeps give 128 updates/512 row presentations, four presentations per exact row.
- Rendered text contains the correct opaque ID and `m0`/`m1`, plus both legal action options. Example: `Unit code sq0_d6a04cda759975740198edda; active setting m0. Act now.` has AUTH target `-mem2reg`. No per-arm mapping bit or target suffix enters the assistant training prefix. Wrong-root64, neighbour16, missing8 and unsupported8 are **OFF-relative locality controls**, not examples with a learnable correct-action label; copy8 measures exact copying.

**What the writer knows:** the request specifies the output format, ID and mode, not that ID's mapping table, compiler state, reward, program semantics or an optimization goal. The correct mapping is nevertheless available to the optimizer through the per-row supervised branch loss. Thus the data are not unlabeled or internally unsatisfiable; the model must store an arbitrary keyed association rather than infer a useful compiler action from a supplied goal. It is not a rich “perfect thought” corpus with explanations, practice feedback or behavioral demonstrations. Passing and failing this task cannot substitute for those broader corpus tests.

## 2. Token branch and loss: correct, but narrower than the endpoint

For all 288 non-copy recorded prefixes, metadata agrees with the source projection: the natural common assistant prefix is `ACT: -` (IDs `[6823,25,481]`); the next-token branches are `mem=10536`, `gv=21404`. Candidate suffixes are `[10536,17,1580,198]` versus `[21404,77,198]`. There is no branch-order reversal or off-by-one visible here. Recorded IDs were inspected as JSON; a synthetic tokenizer exercises the code, **not a new native tokenizer qualification** (`gpu/astra_pairwise_q0.py:240`, `:626`).

With `d=z_mem−z_gv`, pairwise loss is `softplus(−(1−2b)d)`. Independent scalar finite differences confirm bit0 favors mem and bit1 favors gv. Training averages four such losses, then performs one AdamW update (`:377`, `:875`). This is **not full-response SFT**: the answer branch, remaining action spelling, newline and EOS are not supplied as a teacher-forced target sequence. P loss normalizes only over the two branches, so it neither directly penalizes outside-vocabulary logits nor guarantees legal-pair mass. The earlier numerical test explicitly checks that distinction from V (`tests/test_astra_pairwise_q0.py:260`).

Final generation instead begins at the ordinary assistant boundary, without the supplied `ACT: -` suffix. It must generate the prefix, correct complete action, terminate, and preserve locality. That train/readout difference is intentional contract scope, not a discovered label defect, but it matters when interpreting “the write worked.”

## 3. Exactness, similarity and the first-step result

The parser permits surrounding whitespace but requires one exact action identity, no extra prose/multiple actions, no truncation, and termination (`gpu/astra_pairwise_q0.py:977`). A misspelling is another/invalid action; the wrong legal branch is a mapping error. Rohin's near-sequence examples motivate **descriptive error decomposition**, not changing correctness: there is no task-defined semantic-equivalence or reward metric that makes a nearby string a correct tool call. No compiler execution tests semantic interchangeability here.

Fine ID details and `m0` versus `m1` are plausible learning challenges; one-character neighbours explicitly stress locality. However, “the maps blend” is an optimization hypothesis, not observed label mixing. Balanced marginal gradients can cancel without keyed gradients vanishing. The relay's claim that update1 cannot separate maps “by construction” is too strong: the existing feature-equipped XOR CPU toy passes its canary and trains128 steps (`tests/test_astra_pairwise_q0.py:431`). That does not predict Qwen's behavior.

SEQ126 measured **one update per arm, three total**, with no ON endpoint readouts. Its signed-projection passes were 2/4 in every arm; observed-margin passes 3/4,1/4,2/4. Those finite misses do not identify wrong labels, deficient full-dose capacity, or impossibility. Averaged-quartet interference, learned feature sensitivity, dose and dropout-active training versus dropout-off measurement remain distinct hypotheses, not established explanations.

## 4. Smallest decisive next analysis

**No source repair is indicated.** Keep Main's selected Q0-FULLDOSE-v2 and final thresholds unchanged. At its already planned32/64/128 readouts, distinguish (a) correct signed branch margins, (b) legal-pair mass M, and (c) raw action identity/format, by key and class. Better forced-prefix discrimination without raw-action success localizes an extraction/interface gap; exact-versus-held divergence localizes wording transfer; neither alone proves a mechanism. Report all roots and the endpoint, not the best checkpoint. A later explicit-map-in-context control could isolate instruction following from weight-only association if needed, but is not an added arm or prerequisite here.

The selected protocol changes stopping policy **and uses fresh ID/seed allocations**; comparisons with historical v1 cannot isolate a randomized dose effect. Three paired root/seed instances do not separately estimate key versus optimizer variance. Success would remain this diagnostic's success, not parent/sleep/H1/H2 promotion. Failure would not invalidate the level-1 arsenal or all LoRA writes. No new gate, launch veto or impossibility claim is introduced.

## Evidence record and boundaries

Eleven unchanged material-test methods ran via source-only AST extraction with the pinned material-only reader substituted for archive loading: **11 passed**, no skips. Independent enumeration verified labels, balances, wrappers, recorded prefix metadata and scalar loss signs. The full native/numerical suite was not run. No tensor payload, model, native/GPU, network or Git operations; no v2/source edits. Only this memo was written. Whole-file SHA256 pins follow; pins do not imply full historical review.

```text
gpu/astra_pairwise_q0.py
1459c037cccf2f043bc02f40fb9957f38c5620a4d0bcfc8cbb4ebf30fd31182a
tests/test_astra_pairwise_q0.py
bc08064301721157fa353247559105a31b11ee3e0c3b14d5dbbbfa255b9d42e3
original source-material archive / material.json member
422b27e55f794cd14670f049ad09fd31b95887aa615c4d59bc0a03687e83dcf0
769ee38ab444c9e56b6ce7dbf93be95f49e113ca7a60e02322349a53c3ef4336
/tmp/astra_q0_attempt2_metadata_20260913/prepared.json
aa96210c73048d9980011930cb57e3407beacbe7ed094ae13b46dda187de4852
ASTRA_Q0_FIRST_UPDATE_STOP_2026-09-13.md / ASTRA_Q0_FULLDOSE_PROTOCOL_2026-09-13.md
e8fa45555718b643d74a078405dd342ceef5b4d9f0c2ef14014bb400b6b17901
58463922037e8c29b1ce8d5b2cffa3aff3bc1f9b7277ae3ee5600cd2059f353a
/tmp/astra_q0_revision_design_20260913.md
287fbd868a662f9a19045a8e207a2073c75f2511ef6630b8ff5a90dc3bd7fac8
THESIS_RAW message31 through message32 (7911 bytes; before next message or EOF)
ac96914089a87b6b12b1bd9bde8c701180e1f7887c280e15fd61f5e718072e03
COORDINATION 04:44UTC relay (2483 bytes; before next heading)
e0105533edf905d4060cfe834438f62e2e45fa6f6e2452d63f13f73e9a78a9a2
```
