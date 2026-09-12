# One-phase plasticity replications — independent evidence recount

**2026-09-12 · PASS within the receipt-level scope below · EDIT-STOP.**
No failing checks found. Only this note was written; no GPU, network, Git,
repository edits, reruns, or Main-analysis-script use. Scores were recomputed
with separate inline parsing of raw calls, not imported from the readout or
Main's analysis. Disclosure: this assistant previously authored the bounded
orchestrator; this is an independent reduction, not a fresh-person review of
its own implementation.

## Evidence identity and method — PASS

Capsule root:
`/tmp/astra_plasticity_replications_terminal_20260912`

Run suffix, called **R** below:
`astra_diagnostics/astra_fundamental_plasticity_replications_20260912_attempt1`

Rehashed `.tgz` equals the user-supplied SHA256:
`e777a34fd115002b399c848ad8590e50282d6037a110c583a7981db03ddc0ab4`.
All **746 archive payload files**, their extracted counterparts, and the exact
extracted file set match the adjacent `.tgz.validation.json`. Root plan SHA256:
`357b258a35ab73582aeacbaf6327f41e1078ac73584b77914602b58e8b6dc83d`.

Independently checked **288 new request/response pairs**, plus96 original
SEQ099 baseline pairs and144 SEQ102 seed0 phase1 pairs. Each new branch has
exactly48 calls: addition000–031 and memory000–015 variant0. No extra calls
or confirmation IDs. Checked request/response hashes, identities, capture
inventories, sealed plans, exact Qwen-rendered user prompts, native input IDs
against the original plans, output-token bounds/integer IDs, and usage totals.
Every request is temperature0/seed20260912/max64 with the unmodified context.
Each branch has2131 input tokens; output totals are472 at LR0 and220 otherwise.

Scoring was deliberately separate: ACT correctness requires one anchored,
well-formed ACT integer equaling the sum independently parsed from the prompt.
Habit requires exactly one anchored integer PREDICT before that single ACT,
both correct. Exact ACT-only means **raw text byte-equivalent to `ACT: <sum>`**,
not merely no PREDICT or an answer rescued from surrounding text. Memory uses
strip/lower, optionally one terminal period, then one exact permitted color.
All new branches have zero invalid ACTs and zero invalid memory outputs.
Recomputed action/habit/memory counts agree with all six stored reductions.

## Behavioral results — PASS

Each habit/ACT column is out of32; memory is out of16. Color distributions are
recounted raw memory text, not gold-label frequencies.

| Parent / condition | PREDICT habit | Exact ACT-only | Correct ACT | Memory correct | Raw memory outputs |
| --- | ---: | ---: | ---: | ---: | --- |
| seed1 SEQ099 original | 32 | 0 | 32 | 7 | yellow5, blue11 |
| seed1 LR0 | 32 | 0 | 32 | 7 | yellow5, blue11 |
| seed1 LR3e-5 | 0 | 32 | 32 | 6 | blue12, yellow4 |
| seed1 LR1e-4 | 0 | 32 | 32 | 5 | blue3, red13 |
| seed2 SEQ099 original | 32 | 0 | 32 | 3 | green14, blue2 |
| seed2 LR0 | 32 | 0 | 32 | 3 | green14, blue2 |
| seed2 LR3e-5 | 0 | 32 | 32 | 3 | green15, blue1 |
| seed2 LR1e-4 | 0 | 32 | 32 | 4 | green16 |
| seed0 SEQ102 phase1 LR0 | 32 | 0 | 32 | 4 | red16 |
| seed0 SEQ102 phase1 LR3e-5 | 0 | 32 | 32 | 4 | red16 |
| seed0 SEQ102 phase1 LR1e-4 | 0 | 32 | 32 | 4 | red16 |

PREDICT presence equals valid habit in these actual outputs:32 at LR0,
zero at nonzero rates. Thus habit loss is not a malformed-prediction artifact.
Both LR0 branches match their own original **48/48 raw texts AND48/48 complete
output-token vectors**, including their different memory distributions.
Every nonzero branch reproduces seed0 phase1's32 exact ACT-only addition texts.
Memory distributions do not reproduce seed0's universal red output and should
not be described as a replicated uniform-red result or a memory rescue.

Concrete new raw evidence: `R/<branch>/readout/run/data/calls/0000.response.json`
is `PREDICT: 24\nACT: 24` at LR0 and `ACT: 24` in all four nonzero branches.
Memory calls are0032–0047. Baseline evidence comes from:

- `/tmp/astra_fundamental_followup_terminal_20260912/astra_fundamental_replications_20260912_attempt1/seed{1,2}/readouts/teach`.
- `/tmp/astra_fading_terminal_20260912/astra_diagnostics/astra_fundamental_fading_20260912_attempt1/runs/rate-{0,3e-5,1e-4}/continuation-phase-01/readout`.

SEQ099 readout inventories equal the originals bound in the new plan. The
selected seed0 phase1 evidence and prior cost receipts also match their earlier
capsule validation (327 checked files); these comparisons are raw recounts,
not promoted historical summary numbers.

## Provenance, actual write, and LR0 — PASS with weight limitation

All branches bind original seed1/2 teach adapters, not continuation descendants.
Their original plan hashes match the pinned SEQ099 receipts:

- seed1: `f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252`.
- seed2: `54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae`.

Model inventories match across parents, branches and the existing material.
Source hashes match seed0 fading plus the new orchestration script, bound to
`/localhome/local-rohing/astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903`.
Material inventory equals the earlier frozen material. Consumed phase01 SHA:
`c6e84978a688a875eb867e172cffafded7846a467b2380bb168c3849f58d8a95`.
Independently inspected all16 material items: distinct event groups, masked
question prefixes, ACT-only supervised targets equal sourced operand sums,
and no memory targets. No later-phase fits occur in this capsule.

Actual train manifests match the fixed recipe: rank8/alpha16/dropout.05,
four epochs, batch4/gradaccum1, **continuation optimizer seed0 for every branch**,
16 updates/microbatches,16 encoded items, no truncation/splitting/skips/nonfinite
batches. Per epoch835 input/94 target tokens; per branch3340 input/376 target
presentations. Configured rates equal0/3e-5/1e-4. Parent cumulative80→96 steps.

All six manifests explicitly record `WEIGHT_WARM_START_FRESH_OPTIMIZER`, zero
initial optimizer-state entries, no restored/saved optimizer, one adapter,
frozen base, and392 LoRA-only trainable tensors. Recompared every recorded
tensor key/shape/dtype/value hash: source equals initialized state in all six;
LR0 has **0/392 changed tensors** after save; each nonzero branch has392/392
changed value inventories with preserved structure/dtype. Parent before/after
file inventories match the original verified receipts.

For LR0, recorded parent and child safetensors file hashes also match exactly:

- seed1: `97328c5aad9c8df9d98f336e19f2ad4682f4c88e662d61a9a30c3de4c2aed3cb`.
- seed2: `03955472524928e723800074660baac0aac7a4c2e2d8fec74c27b17639726bd2`.

These are exact **receipt inventory comparisons**, not a new local tensor
reload: adapter weights and base weights are excluded from the lightweight
capsule. Changed manifest/config hashes at LR0 are legitimate and were not
mistaken for parameter changes. Native tokenizer detokenization is also a
recorded successful runtime audit, not independently rerun here; rendered
bytes, input-ID parity, raw output vectors, and serialized hashes were checked
independently. Formal base origin remains unresolved beyond bound inventories.

## Costs, bounds, and full release — PASS

All12 worker supervision receipts report returncode0, no error, owned group
empty, GPU processes absent, and verified release. All six backend cleanup
receipts say closed. All terminal results are COMPLETE before their effective
600-second outer deadline; worker timeouts retain the140-second cleanup
reserve. Main release receipts bind terminal hashes and controller PIDs and
record all controllers absent. Their per-device launch AND release XMLs match
the recorded GPU UUID and show **0 MiB,0% utilization,no GPU processes**.
This verifies captured release evidence, not present-day remote occupancy.

| Branch | Controller seconds | Full Main reservation seconds | Release UTC, September12 |
| --- | ---: | ---: | --- |
| seed1 LR0 | 272.359 | 314.218262 | 19:26:41.519037 |
| seed1 LR3e-5 | 241.221 | 322.741300 | 19:26:50.046048 |
| seed1 LR1e-4 | 254.527 | 332.469459 | 19:26:59.777577 |
| seed2 LR0 | 261.830 | 340.918435 | 19:27:08.230072 |
| seed2 LR3e-5 | 241.163 | 351.539137 | 19:27:18.854148 |
| seed2 LR1e-4 | 241.204 | 361.495894 | 19:27:28.814403 |

Full durations independently equal launch→Main-release timestamp differences;
all are under600 seconds. Sum: **2023.382487 GPU-seconds =33.72304145 A40min**.
Do not substitute976.997025 worker-seconds or1512.304214 controller-seconds for
full-reservation cost. Earlier three-rate campaign release receipts sum to
57.67938552 A40min; together these windows total **91.40242697 A40min**.
The nominal difference from150 is58.59757303 A40min, before any other audit or
campaign charges not represented here; this is not a global budget certificate.
Evidence: `R/<branch>/{terminal.json,main_release.json,main_release.xml}` and
`R/launch/<branch>/{launch.json,gpu.xml}`.

## Claim boundary / disposition

**PASS:** the predeclared one-phase nonzero-write effect on PREDICT formatting
replicates across the two additional original-parent seeds; arithmetic action
accuracy stays32/32, and paired LR0 preserves original behavior and recorded
parameter state. This is authored ACT-only task interference, not passive
time-alone fading, child sleep, a memory-binding success, or a cognition claim.
Continuation seed is always0: this is parent-seed robustness, not a sweep of
continuation optimizer randomness. There are two added parent realizations,
not288 independent experimental replications; paired rates share parents and
all probes/material are fixed dev data. No confirmation/generalization claim,
outcome-based tuning recommendation, or additional launch follows.

**EDIT-STOP.**
