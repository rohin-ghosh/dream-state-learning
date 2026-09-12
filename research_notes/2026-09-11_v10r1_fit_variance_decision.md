# V10R1 fit-variance decision

Date: 2026-09-11 PDT / 2026-09-12 UTC

Status: design adjudication only. This note authorizes no source change,
tokenizer/model execution, training, adapter work, GPU use, parenting, C11
work, claim, release, or submission.

## Decision

Keep V10R1's four-fit design as a strict, one-sided writer-capacity scout.
Do not reopen the V9 -> V10 -> V10R1 contract merely to add fit replication.

The four predeclared fits are two engineered roots times complementary `W+`
and `W-` maps. `MULTIKEY_BINDING_PASS` requires the oracle gate. For each
root, both adapters must pass all 16 per-key median NLL-gain thresholds and
the paired adapters must meet the mean-gain-asymmetry threshold. Each adapter
must also meet its aggregate and per-stratum generated-behaviour gates,
directional margins on at least 12/16 keys and 6/8 per stratum, and every
interface and spill gate. A pass means only that these four predeclared fit
instances met those frozen gates. It does not estimate a success probability
or training-run reliability.

The asymmetric label interpretation is mandatory:

- `MULTIKEY_BINDING_PASS`: the four observed root-map fits met every gate,
  under the exact maximum permitted wording;
- `NONREPORTABLE_ABORT` or `ASSAY_INVALID`: there is no writer result;
- `OPTIMIZATION_INCONCLUSIVE`: the exact dose and optimizer failed the
  all-key NLL/asymmetry gate, so no capacity conclusion follows;
- `INTERFACE_INVALID`, `BINDING_WITH_SPILL`, and `GATEWAY_NEGATIVE`: only
  their registered recipe-local meanings apply after their upstream gates;
- no non-pass label supports LoRA/substrate incapacity, and no result supports
  a training-seed, run-reliability, or node claim.

Fit variability therefore increases false-negative risk. It does not enlarge
the permitted positive claim or justify post-result rescue.

## Later execution-manifest requirements

Without changing the four fits or the 3.0 A40-hour cap, the separately
ratified execution manifest should:

1. pin one node and environment for all four fits;
2. assign one common training seed to `r0/W+` and `r0/W-`, and a different
   common training seed to `r1/W+` and `r1/W-`;
3. record training seed, GPU UUID, exact source hash, environment hash,
   effective-corpus hash, model/tokenizer identities, and deterministic-mode
   settings for every fit;
4. state `training_run_replication=false` and `root_seed_confounded=true`;
5. prohibit reliability, variance, and machine-effect claims; if one pinned
   node cannot be guaranteed, keep each within-root `W+`/`W-` pair
   node-matched, state `root_node_confounded=true`, and prohibit cross-root
   scientific comparison; if within-root node matching cannot be guaranteed,
   do not execute the assay;
6. treat any diagnostic repeat after a split result as a separate,
   prospectively bound experiment rather than a V10R1 rescue.

Using distinct root-level seeds exercises two seeds without breaking the
within-root complementary-map match or increasing GPU cost. It is not
replication: root identity and training seed remain confounded.

## Why not eight fits

A balanced root x map x training-seed repeat would be appropriate if the
estimand were writer reliability. V10R1 instead asks the cheaper prior
question as a one-sided feasibility scout: can the frozen writer recipe carry
a multi-key conditional native policy at all? A pass witnesses feasibility
in four particular fits; a non-pass does not answer the existential question.
Doubling the fits would either exceed the registered resource cap or force a
change to roots, epochs, or geometry. Under the deadline, the four-fit
conjunction has higher decision value per GPU-hour.

The terminal completion-frame audit localizes the observed divergence to the
configured optimizer seed for those measured fits: each of seeds 0 and 1
reproduced across machines at stored precision, while both failed locality.
This does not prove V10R1 is unstable, establish universal determinism, or
estimate the seed distribution. V10R1's label order
routes failure of the all-key NLL/asymmetry gate to
`OPTIMIZATION_INCONCLUSIVE` before downstream interpretation. That label
cannot distinguish underdose, fit variance, and capacity. Only every gate
passing yields `MULTIKEY_BINDING_PASS`, under the exact limited V10R1
wording.

## Bound proposal state

- V9 exact scope: `eac3e25c93230f3788612b3d0a25c0dac3609d49b4a5d9e28cf853ba806c0955`
- V10 exact scope: `12a077950730c3abaef32b04a861d901ef4bae25a22e640b152472f5f364f549`
- V10 consensus: `147aebaaf0b974a37897acc724c6fe27c8e82c6f94db0c1e775eba3d57a1ce7e`
- V10R1 exact scope: `6cba6518184e7c8d12d7c23088895a565b84ae5ee067eaa63aac4440b91ea1aa`
- V10R1 consensus: `5792ec9acbf9e2da26f34ff8303bce06a496a3c9f5010162b0e4491db93ea9a2`

V10R1 remains `human_required`. Existing authorized queues may continue under
simple hygiene; no V10R1 source or execution action follows from this note.
