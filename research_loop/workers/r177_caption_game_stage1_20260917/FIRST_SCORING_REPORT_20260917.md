# First real development scoring report

Main, September 17, 2026, 12:24 PDT. This is a development engineering report,
not a final benchmark release or a retained-learning claim.

## Judge: trained, but not usable yet

The corrected v6 DistilBERT classifier run on node4 physical2 started optimizer
updates at **12:15:22 PDT** and completed its fixed 2,000 sampled batches at
**12:22:22 PDT**. Both humor and scene-fit models trained. The earlier v4 attempt
was stopped and preserved because biased negative sampling could teach scene
identity rather than scene-caption compatibility. v6 fixes training and
calibration/stress negative construction.

Data uses released `canny`, `location` and `entities`, excludes `uncanny`, and
does not wait for the separate local Qwen vision service. There are 180 usable
training contests and 1,041,036 available retained rating rows; this initial
candidate samples 34,560 rows, up to 64 per quality band per contest. Eighty-two
training descriptions are missing and excluded. Training makes 32,000 humor
example draws with replacement; this is not an all-row epoch. Registered-dev
partitions are 19 selection, 13 probability calibration, 7 threshold selection,
and 6 audit contests. Eleven dev descriptions are missing. Locked validation and
FINAL remain unopened.

| Disjoint development-audit measure | Result |
| --- | ---: |
| Captions / contests | 384 / 6 |
| Multiclass soft-target Brier | 0.0148788838 |
| Soft log loss | 0.5314883418 |
| q-ECE, ten bins | 0.0192178242 |
| Mean within-contest Spearman, q vs positive-vote mass | 0.0341122266 |
| Feasible acceptance tau | **None** |
| Accepted captions / coverage | 0 / 0% |
| Accepted positive-vote-mass proxy | Undefined, because nothing qualifies |

The predeclared operating standard requires at least 0.30 mean positive-vote
mass with at least 5% threshold-set coverage. No threshold met it. We do not
lower the standard to turn this failure into a usable benchmark. Low Brier
alone is misleading here: within-contest ranking is near-flat. The checkpoint
selected by model-selection soft log loss is step100; its selection Spearman
is 0.04366. Step2000 selection Spearman is still only 0.08069.

Scene-fit calibration on matched versus balanced synthetic swaps achieves
63.17% balanced accuracy and 57.14% matched recall. These are synthetic
compatibility diagnostics, not human scene-fit truth. All stress acceptances
are zero because tau is absent; that is **not** evidence of robust rejection.
Mean humor-score changes for scene swaps and broken punchlines are nearly zero.
The second blind comparator is not complete.

Next work is a separately versioned training improvement addressing weak
within-scene ranking and limited fitting-row coverage, selected on the existing
model-selection pool. The saved v6 report remains the first disjoint audit;
subsequent use of these development contests is reuse, not a fresh unseen test.
No child game or FINAL run is released against this unusable acceptance gate.

Safe provenance: `data_judge/evidence/RECEIVING_V6_OBSERVATION_1789672960306252378.json`,
SHA `59501b755992aa7603aece5a348b50873d3c208c089107ab9bb3e7f68c3f6c0d`.
Public scoring report SHA
`ca09a01f02fc1545a9c56e8c1f13314e49b3843ba2000fcbf11d7799bb5344d0`;
trained artifact SHA
`b6cdc59274d9e5ec6d1bf1b1adc073346cf35e31bc1e1e93115d2d80421cd0e7`.
Main read only the operational and aggregate development reports, not private
error cases, captions, labels or sealed outputs.

## Novelty: first provisional calibration exists

The actual frozen all-MiniLM-L6-v2 encoder ran on 300 model-labelled pairs,
partitioned by contest into 240 fitting and 60 held-out pairs. Primary rho is
0.9765189220557066. Held-out retrieval errors are **0 false merges / 30 different
jokes**, and **8 false splits / 30 same jokes**. This is embedding-retrieval
error, not the full verifier-backed archive's error rate or human ground truth.

The same-joke verifier also ran: 30 valid reversed-order smoke labels agreed
with the original model labels; two real archive integration smokes passed.
These use the same provider/instruction, so they demonstrate repeatability, not
independent correctness. The campaign charged 45 label-related calls and 32
verification calls, with no retries. Labels and caption contents remain private.
Calibration and error rates stay explicitly provisional.

## Integration and living children

The bounded real-tool smoke CLI exists, without synthetic fallback. Its initial
combined CPU suite passed **371 tests and 66 subtests**, including eleven new
wiring tests. The first collection attempt lacked Pillow and is preserved; an
ephemeral test environment with Pillow resolved that dependency. Source hashes
in the local CPU receipt were observed after that suite, not claimed as a frozen
receiving-node GPU proof. No real smoke dispatch or learner launch is claimed.

Local Qwen weights/CPU compatibility/device-confinement proofs are staged on
physical5. Its actual image-only development release/admission and model load
are still pending; it never blocked this judge training. Existing children and
the R179 exact-state context-preserving rollouts continue separately. All six
node3 lives have been recovered and their parent processes reattached.
