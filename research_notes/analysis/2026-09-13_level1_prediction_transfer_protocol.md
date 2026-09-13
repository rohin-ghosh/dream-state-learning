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

## Implementation freeze — September 13, 2026, 17:45 UTC

Main joint CPU suite25/25PASS in25.197s (14 lifecycle/custody tests plus11
material tests): `python3 -m unittest discover -s tests -p '*prediction_transfer*.py' -v`.
Material module SHA25676c742ed35f0d30012e2095c4a0077c9c026d97b55d1f4c7810b2d7b745d2e8d;
runner24e74d5d57a36ab1e749567ba603a025680a66ad605642e9697b69d92bfd6274.
Exact native material seal150bc6b4431a2ad80205ee17e04f3f2d99c4f8e19e917ce7d6bbb8210e537d29;
material JSON FILE SHA7cdd08b461bf88daf02cf1ad6228d81b5912c19781f076fc23f2ac2ba551f690.
All48 rows frozen before native outputs. Default fixture path is portable to
the tracked old receipt; native generation explicitly uses original pinned
`/tmp/astra_level1_prediction_goal_material_20260913.py`, unchanged bytes.

Operational selection: node1 GPUs0/1/2, corresponding original prediction
seeds0/1/2; native interpreter `/localhome/local-rohing/v2/venv/bin/python`.
Original plan/completion pins and exact service identities are in the archived
`receipts_20260912/astra_prediction_transfer_setup_20260913.py` (relative to
research_notes/astra_memos). Its prepare mode does CPU/tokenizer checks only;
launch mode creates three bounded controllers and collects completed captures.
No GPU is reserved solely by this document. Each controller rechecks live
compute processes, CVD environments and queue before each state, and owns
only its spawned group. Exact known user-init service exceptions only;
no blanket unreadable-process exemption. Detach before checks so the launch
SSH transport exits. Collection stays within each30minute controller budget.
Main will preserve all new roots/captures on the VM before reporting results.

## Infrastructure amendment — September 13, 2026, 18:00 UTC

Before scientific outcome inspection, attempt1 seeds0/1 failed post-run CVD
checks because finished seed2 controller2960286 was left unreaped by Main's
ordered batch waits. All six workers captured their48calls, exited0 and
released; only seed2 has a successful original controller/collection. Preserve
the other two failures and their raw data/cost; do not retroactively pass them.

Select fresh attempt2 for seeds0/1 only, serial orchestration with immediate
reaping. Keep seed2 attempt1 unchanged. Same source, frozen material, parents,
GPU assignment, sampling, scorer and per-state call counts; no outcome-driven
change. This is an infrastructure retry, not another independent learner or
resampling to improve an answer. Add192calls/1.0allocated GPU-hour maximum,
for480total attempted calls if both retries finish. Timing/concurrency differs
and must be reported. No third attempt. Strict resource checks remain intact.
