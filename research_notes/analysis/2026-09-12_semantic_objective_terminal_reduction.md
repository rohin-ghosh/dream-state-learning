# Semantic writer objective probe: independent terminal reduction

Date: 2026-09-12 UTC

Scope: read-only watcher reduction of Astra's completed supplementary probe at
`/localhome/local-rohing/astra_diagnostics/astra_semantic_objective_20260912_attempt1`
on node 3. This note changes no builder source, job, model, tokenizer, adapter,
GPU state, frozen Q0 result, paper claim, or follow-up authorization.

## Terminal integrity

- immutable probe source SHA-256:
  `98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41`;
- bound test SHA-256:
  `0a327ab022b434d89cdcd881ab795f4ee28ff896679d45da16b03be1ddb95de0`;
- report SHA-256:
  `4ca5316949252400b6377feca674ba4abd11eac8759a99f9ed427a2b39b7b659`;
- all five registered stages completed once; the report records 512 training
  forwards/optimizer steps, 384 exact-prompt generations, 384 dropout-off
  decision-prefix forwards, 2,559 generated tokens, zero held queries, and
  576.104 seconds elapsed;
- all five cleanup receipts report `owned_group_empty=true` and
  `gpu_processes_absent=true`; the controller is absent and no node-3 compute
  process remained at the terminal check.

The full-response control exactly reproduces the historical root-1 W+ fit at
the scientifically relevant level: identical initial LoRA tensor digest
`49b7cb...0565`, final LoRA tensor digest `31f101...787`, mean loss
`0.24362293088472597`, update norm `1.8857633694472649`, first loss
`3.7756545543670654`, and final loss `0.06812606006860733`. The serialized
adapter tree hashes differ, but the learned tensors do not. Both fits used
FP32 LoRA parameters, gradients, and Adam states on the same pinned GPU and
runtime.

## Primary result

| state | exact generated correct | strict valid | generated action concentration | positive / zero / negative teacher-forced gold margin |
|---|---:|---:|---|---:|
| OFF | 65/128 | 128/128 | `-mem2reg` 127, `-gvn` 1 | 64 / 0 / 64 |
| full response | 64/128 | 128/128 | `-gvn` 128 | 64 / 2 / 62 |
| first decision token only | 64/128 | 128/128 | `-gvn` 128 | 64 / 1 / 63 |

The two trained arms produced the same action on all 128 prompts. Their
teacher-forced margin signs also agreed on all 128 prompts: both were positive
on 64 and nonpositive on 64. Mean gold-minus-other margin was `0.029296875`
for full response and `0.025390625` for decision-only, a treatment-minus-
control difference of `-0.00390625`. Every one of the 16 key/mode cells was
therefore either 8/8 or 0/8 according to the global `-gvn` class, and every
template was 8/16. This is not conditional binding.

The first-choice fit moved substantially (`update_norm=1.4330553267092672`)
and had mean one-token loss `1.0637142623105547`; its null is not a no-update
artifact. It learned a global response preference, just as the reproduced
full-response fit did.

## Scientific disposition

**Null for the proposed objective explanation.** Removing every supervised
token except the first divergent action token did not improve acquisition on
the exact 128 training prompts. The current failure is therefore not rescued
by removing shared syntax/suffix supervision, and more unchanged full-response
fits, rank sweeps, heat sweeps, or paraphrases are lower-information next
moves.

This remains a one-root/one-map/one-seed exact-form diagnostic. It says neither
that LoRA lacks capacity in general nor that a different conditional objective
cannot work. The treatment also increased the decision term's relative scale
by roughly 7--8x and removed response-length weighting, so a positive result
would only have identified a composite objective effect. Because the result is
null with identical final decisions and margin signs, that ambiguity cannot
rescue the hypothesis.

The next bounded writer test should directly encode the missing relation:
contrast the correct action continuation against the paired incorrect action
for the same prompt (pairwise/log-odds or equivalent contrastive objective),
while keeping the clean base, exact rows, initialization, dose, strict
generation, teacher-forced margins, and spill/interface panels fixed. It must
first pass a CPU/native canary proving that one update increases
`log p(correct)-log p(incorrect)` conditionally in opposite directions for
opposite labels without merely shifting the global action prior. If that
objective also remains at chance on exact rows, stop semantic-writer tuning and
revisit the carrier/representation rather than spending the next cell on scale.

Fresh pre-run critique is preserved at
`research_notes/analysis/2026-09-12_semantic_decision_token_objective_fresh_audit.md`.
It correctly limits any positive result to a composite objective effect and
asks for a scaled-mask isolation if mechanism attribution is later needed;
several operational concerns were in fact closed by the launched source and
terminal receipts. The null conclusion above does not depend on those disputed
positive-attribution details.
