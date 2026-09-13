# Level1 prediction: fresh-instance scaffold withdrawal (DEV)

Proposed by Builder, September 13, 2026, 17:34 UTC, before new model outputs.
Implementation and CPU validation pending. This is not a GPU launch receipt.

## Question and rationale

SEQ142 installed the authored prediction fixture in three LoRA learners:
held content OFF 22/48, post 48/48 for each, on shared material. Its prompt
explicitly supplied the decision procedure. Determine whether that learned
behavior remains useful on fresh facts when the procedural reminders are
removed, while retaining the public facts and response vocabulary. This is
a same-task DEV robustness/scaffold-withdrawal diagnostic, not spontaneous
cognition, new-task-family transfer, amortized parenting, H1/P1 or H2.
Do not replace this question with another PCFL reader or write-dose sweep.

## Fixed comparison

- Reuse the existing prediction adapters for learner seeds 0, 1, 2, each
  from its original 320-update authored Level1 run. Authenticate original
  manifests, adapter bytes and actual route before using them. No new fit,
  warm continuation, merged adapter, teacher, parent or external memory.
- Generate 24 fresh authored fact cases: six uniquely supported true, six
  uniquely supported false, six absent and six conflicting selected-action
  entries. Use disjoint action triples from original training and held data.
  Provenance is author-supplied hypothetical public facts, not real child
  experience. No generated answers enter writes or lineage selection.
- Each case has FULL and MINIMAL views. FULL retains the prior supplied
  decision procedure and response schema with new facts/framing. MINIMAL
  retains the same public card semantics, facts and selected future action,
  plus response vocabulary, but removes the procedure, reminders and
  classroom framing. It does not secretly change the meaning of absent or
  conflicting evidence. Both omit the selected action's observed outcome.
- Score OFF (adapter disabled) and post (exact saved adapter), 48 calls
  per state per learner: 288 planned total. Separate fresh processes per
  state, cleared context/caches and identical engine/192-token generation
  settings. No live feedback or history crosses cases. Fixed case/view
  order, shared across arms, is logged rather than called randomized.
- OFF repeats share the same frozen base and are reproducibility controls,
  not three independently trained baseline learners. Learners share all
  authored cases; cases and views are not independent learner replications.

## Endpoints and interpretation

Primary: paired post-minus-OFF content correctness on MINIMAL /24 per
learner. Report each of four case groups /6; retain wrong, missing, malformed
and length-terminated outputs in denominators. Secondary: FULL /24,
MINIMAL-minus-FULL within state, strict format, paired wins/losses, raw
finish reasons, prompt/output tokens, generation/load/controller wall time.
Use the existing frozen typed-content/format scorer; no answer repair,
rescoring of historical evidence or free-prose semantic credit.

Diagnostic continuation rule: positive MINIMAL content contrast in all
three learners with post at least 20/24 supports testing another existing
behavioral seam; it does not qualify a gate or authorize a broad claim.
Failure or mixed contrast localizes dependence on supplied procedure or
limited transfer within this test, not universal incapacity. FULL failure
also limits attribution to scaffold withdrawal. Keep old held acquisition
separate; do not rescue a null with another prompt, budget or fit sweep.

No retention claim: this check does not overwrite the adapters or probe
forgetting. No matched-trained parenting control exists in this comparison.
All prompts/material/source hashes freeze after CPU tests and before launch.
Code repairs after outcomes get separate attempts and explicit amendments.

## Execution and stopping

Main owns native launch/cleanup and resource assignment; workers own bounded
material/runner/tests only. Reuse existing authenticated runtime functions.
Use three free GPUs concurrently only after nvidia-smi AND /proc environment
checks, otherwise run sequentially. No job on node1 unless its entire bound
fits before September 14, 2026, 17:14 UTC (six hours before expiry).
Node1 preservation is due September 13, 2026, 23:14 UTC; preserve new receipts
and adapters elsewhere before then. Prefer surviving nodes if authenticated
source/adapter copies and environment are already available.

Budget forecast: at most 30 minutes/GPU, 1.5 allocated GPU-hours total,
including six cold model loads and collection. This is a conservative cap,
not measured utilization. Stop on identity mismatch, failed source binding,
resource conflict, timeout, missing/raw-capture corruption or release failure;
do not retry scientific outputs. Keep per-attempt immutable roots and collect
raw outputs, routes, manifests, hashes, completion/failure and release receipts.
Exact launch commands and selected resources follow after CPU validation.

Formal final-paper C11 guard remains deferred under Rohin's ruling. Ordinary
provenance, parent blindness, state isolation, evidence preservation and
shared-node/lease hygiene remain mandatory. Broader sprint is incomplete.
