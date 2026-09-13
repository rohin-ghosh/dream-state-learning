# Result-blind re-audit: contrastive keyed-discrimination v2

**Evidence cut:** `cae0afa2` (v2 protocol), checked against the result-blind
red-team at `e361daf7`. No material, result, model, tokenizer, runtime, or GPU
was used. The only edits made by this audit are local claim/check wording in
the protocol; they do not change topology, data, treatment, dose, or gates.

## Verdict: PASS

V2 resolves every fatal defect in v1. It is implementation-eligible as a
one-world, three-paired-optimizer-seed diagnostic of the effect of two exact
loss-masked instruction renderings. A pass would identify the treatment as the
truthful contrastive instruction rather than visible padding, answer exposure,
Boolean negation, a closed candidate roster, or cross-seed gate assembly.

This is not authorization to implement or run it, and a pass will not establish
internal attention mediation, generalization across worlds, actual child
perception, SLEEP, parenting, or organism learning.

## Fatal-check disposition

| V1 red-team defect | V2 finding |
|---|---|
| Visible arm-specific padding | **Resolved.** No visible padding exists. Only trailing post-EOS tensor padding is permitted, with `attention_mask=0` and label `-100`. The protocol now requires same-shape alternate-pad-ID invariance for all non-pad logits, supervised loss, and LoRA gradients, plus structural mask assertions. |
| False contrast statement | **Resolved.** Each family is a four-value permutation, so its three observed modes and outcomes are necessarily distinct. The exact contrast sentence is true. |
| Coupled construction randomness | **Resolved.** Identifiers, mapping, held mask, train skin, row order, candidate order, and canary use separate SHA-256 counter domains; rejected candidates and reasons are receipted. |
| Hidden generator shortcut | **Resolved within the registered one-root scope.** The protocol exhausts single, affine, and coarsened-pair nuisances before OFF, bounds observed/held nuisance accuracy at one half, and aborts after 256 candidates. It correctly exempts the intended full joint key and discloses the family-only H-KEY route. |
| Held-only rule cue | **Resolved.** The public one-of-each rule is present in training and absent from every evaluation route; supported query templates do not expose panel or held status. |
| Candidate bank in native primary | **Resolved.** Candidate scoring and candidate-free native generation have no outcome roster. Closed-set native is separately labeled and cannot satisfy the native gate. |
| Ambiguous permissive parser | **Resolved.** Exact boundary-delimited raw identifiers, no normalization/fuzzy repair; v2 now also requires non-overlapping identifiers under the frozen boundary grammar. |
| Candidate/native gates assembled across different seeds | **Resolved.** `JOINT_SEED_PASS` is a same-seed six-part conjunction; at least two of those same seeds must pass, with campaign-wide paired-delta gates and a bound on the remaining seed. |
| Resource cap not mechanically enforceable | **Resolved prospectively.** Fifteen-second campaign accounting plus hard per-worker monotonic deadlines, preallocation refusal, and no reuse of failed-stage budget bound maximum allocation below the cap. |

## Arithmetic and unit check

All protocol totals close:

- `8 families * 4 modes = 32` keys; 24 observed and 8 held.
- `24 sources * 4 skins = 96` memory rows; another 96 preservation rows.
- `192 / 4 * 10 = 480` updates/fit; 1,920 row presentations/fit.
- Six clean-base fits = 2,880 updates and 11,520 row presentations.
- Each observed source is selected as target `4 * 10 = 40` times. Since each
  same-family prompt contains all three observed records, each fact is also
  visible in 120 loss-masked memory contexts; these are now stated separately.
- Per inference state: `24 + 48 + 16 + 16 = 104` key/locality rows;
  `104 candidate-free + 104 closed-set + 16 canary = 224` generations.
- Seven states (one shared OFF, six fitted) = 1,568 native generations.
- Candidate scoring: `(24+48+16)*4 + 16*5 = 432` continuations/state and
  3,024 total.
- Worker allocations: `6*1200 + 7*900 = 13,500` GPU-seconds = 3.75 A40-hours,
  leaving 900 seconds below the 4.0-hour hard cap. Deadlines include model
  load, work, and cleanup. Device-reservation and active time are not summed.

The fit is the replication unit. Skins are repeated measurements. There is one
frozen mapping and three paired optimizer seeds, so even a pass supports only
that mapping under seed stability, not a population-of-worlds claim.

## Attention-mask and treatment invariance

Right padding occurs only after EOS. A supervised target cannot causally attend
to a padded future position in a decoder-only model; the zero attention mask
and `-100` labels independently exclude padding from attention and loss. The
strengthened pre-fit check changes only masked pad IDs at fixed shape and RNG
and requires bit-identical non-pad logits, supervised loss, and LoRA gradients.
This is the appropriate implementation gate for pad-ID invariance. If any part
fails, preparation aborts.

PLAIN and CONTRASTIVE naturally have different active context lengths and can
place the identical target at different positions. That is not a hidden pad
arm: it is part of the two explicitly frozen instruction renderings. The claim
must remain about those exact renderings, not a length-free latent semantic
intervention.

## Remaining nonfatal boundaries

H-SKIN is the joint family-by-mode discrimination panel. H-KEY contains only
one held cell per family, so family identity alone can encode its missing
value. H-KEY therefore shows family-level withheld-cell completion compatible
with the supplied one-of-each structure; it cannot prove that the model learned
or executed the rule. The protocol now says exactly that.

Likewise, each memory target is an observed outcome already visible in its
fact block. This is intentionally a supervised acquisition assay. The paired
contrastive advantage tests whether the extra truthful comparison instruction
improves later answer-hidden carriage; it does not show autonomous discovery.

Subject to the protocol's preparation assertions and abort rules being
implemented literally, no further scientific redesign is required.
