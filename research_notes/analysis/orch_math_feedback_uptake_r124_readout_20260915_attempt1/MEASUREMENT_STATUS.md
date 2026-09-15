# R124 actual matched readout and A2 recovery

## F2: matched measurement successful

Native root: `/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1/F2`.
Both fresh processes completed eight existing DEV tasks, with full raw text and
token IDs, AFTER identity checks and process return code zero. Exactly the same
two-message system/user prompts, no carry/parent context, greedy batch8 and
2048-token cap. No additional reasoning instruction or FINAL invocation.

The comparison is C13 checkpoint `82c1a68c83650a1f2d2afeee662f78f925cd029d8c1078086117e80f35bb57fd`
versus C14 `7e5e1a9ee966c55a1eacfc5bb5f0f9199c53cf238d98d0c10f6b840c2f87422e`.
Every actual C14 TRAIN row source binds the C13 predecessor. Both probes were
performed after saving C14: “before” means predecessor weights, not wall time.

| Quantity | Before C13 | After C14 |
|---|---:|---:|
| Complete / planned | 8 / 8 | 8 / 8 |
| Stored generated tokens | 975 | 1,021 |
| Parent calls / optimizer updates during probe | 0 / 0 | 0 / 0 |

Four of eight texts/token sequences differ. CPU author read all eight before
texts and all changed after texts: both sets contain explicit calculation steps;
the two algebra responses include substitution checks and are unchanged. Of the
four changed texts, one shortens explanation, two expand wording around the same
operations, and one changes whitespace. No changed mathematical approach was
observed in this small pair. This is not an automated admission label, evidence
of improvement, a style-matched control effect, or spontaneous disposition.

`F2_MATCHED_DEV_VERIFIED.json` contains all sixteen native CALL paths/hashes,
token counts, checkpoint/prompt hashes and full-process identity receipt refs.
No raw responses or answer keys are copied into the repository.

After probes, F2 PID3953966 restored C14 AdamW4108 and exact saved CPU/CUDA RNG
at19:22:54 UTC and began genuine C15. This is the same independent learned life,
not a new optimizer fork. Hubble owns the terminal-only F2 broker migration to
this root; actual RELEASED/PLAN hashes were posted at19:22 in COORDINATION.

## A2: failures preserved; offload continuation recovering

Actual safe release was C11, AdamW4419, native200/parent46. Initial admission
failed on transient process identity drift. One administrative re-admission
passed but used the system Python rather than the existing model venv. Both
probe processes and learner restore failed importing tokenizers, before model
load or native reservation/input. These probe keys are **not retried** and their
denominators remain FAILED_PREMODEL, not completed measurements.

The next runtime guard failed strict scanning; its immutable receipts remain.
The scoped sampling repair obtains two additional actual kernel/executable/CVD/
FD observations per scanner identity, retaining the existing three-observation
reconciler and all target-device checks. That scan passed, but a wrapper missing
`subprocess.DEVNULL` failed before native launch. The regression now tests the
complete subprocess launch interface. This implementation fault and all earlier
failures remain preserved, without changing counters.

Latest immutable runtime source is
`/localhome/local-rohing/orch_math_feedback_uptake_r125_runtime_source_20260915_v2`;
CPU5local/5native PASS, plus40combined local runtime/transient regressions.
`runtime_recovery3/ADMISSION.json` is clear and native PID4093591 started at
19:31:31 UTC. It skips the failed probes, restores saved C11 AdamW/RNG/carry,
and continues C12. Future original DEV20 calls use the tested full resident
model/optimizer CPU-offload path. Successful A2 future DEV remains to verify;
no A2 matched before/after result is claimed.

There are no scheduled new boundary signals or outcome-dependent interventions.
Both continued lives retain original carry, failed charges, two-episode sleeps,
rehearsal/42anchors/lambda0.25, and lease/FINAL custody. No Git mutation.
