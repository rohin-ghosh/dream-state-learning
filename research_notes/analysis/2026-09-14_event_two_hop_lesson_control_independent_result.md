# Independent result — matched trajectory-loss-off control

September 14, 2026. **Bounded accounting, artifact-join and replay checks PASS.
All old/fresh control goal panels are 0/4. Retention and audit outcomes are
inferior to the full arm; equal achieved rehearsal effects are not claimed.**

Only this assigned note was edited. Review used local terminal files, frozen
helpers and two existing CPU tests. No model/tokenizer/torch loading, GPU,
remote calls, new code/framework, launch changes or full ancestry re-audit.
Completed review and ownership are released to Main.

## Capsule and immutable provenance

- Control root: `gpu_artifacts_local/astra_event_two_hop_lesson_control_terminal_20260914_attempt1/extracted`.
- Full-lesson reference: `gpu_artifacts_local/astra_event_two_hop_lesson_terminal_20260914_attempt1/extracted` (SEQ-250).
- Fresh-transfer reference: `gpu_artifacts_local/astra_event_two_hop_transfer_terminal_20260914_attempt2/extracted` (SEQ-251).
- Independently hashed sibling archive: **349,171,367 bytes**, SHA-256
  `602454f836ed759648711af80f6a54cf254aa4b7a13af1529caa0853b305e35c`.
- Captured source `4f1d7b689e7892d989cb97e6406d5c80d9bfb6a8`:
  all 33 project modules imported for the primary check came from this
  capsule's `source/` and matched their local Git blobs at that commit.
  The control helper hash matches binding value
  `ca6f90ad0771ceb9083b8add6d94ff1546d5d9f38fa981435789e1708a8ac03e`;
  all five encoder/helper hashes also match.
- Independently compared **305 selected extracted files / 87,629,767 payload
  bytes** against archive members: phase artifacts, saved adapter, launch/log
  files, imported modules, guard and targeted-test source. No selected-path
  escape, symlink substitution or byte mismatch was found.
- PREPARE is `PREPARED_NO_MODEL`; TRAIN and AFTER are `COMPLETE`, without
  phase FAILED files. INPUTS/result bindings agree across all phases.
  Recorded launch interval: **2026-09-14 15:56:24–16:04:47 UTC**.

## Actual loss-off intervention

The saved TRAINING_ROWS are identical to the full arm, not a newly generated
corpus: **128 old-memory + 20 cue + 62 audit + 12 trajectory = 222 rows**.
The saved REFERENCE_MASKS equal the full arm's MASKS. Reference raw-row,
mask, recipe and training-file hashes match the SEQ-250 artifacts. Replayed
actual lessons equal the twelve saved trajectory rows.

For **every saved row**, input IDs and target-ID metadata are unchanged.
Rows **0–209** retain exactly the full-arm labels. Every label in rows
**210–221** is `-100`; none of the trajectory targets contributes direct loss.
Keeping target IDs as provenance does not unmask their labels. Reference masks
pass the frozen validator, and all sequences stay within 2048 tokens. The
frozen batch helper verifies unchanged input/attention masks and common labels.

All **100 actual LOSSES records** agree with the frozen schedule and saved
PREFLIGHT/RECIPE. Independently recounting causal labels from the saved masks:

| Accounting quantity | Verified value |
|---|---:|
| Full-reference active-label total | **8,245** |
| Control active common-label total | **5,977** |
| Omitted trajectory-label total | **2,268** |
| Trajectory row presentations | **200** |
| Supervised trajectory presentations | **0** |
| Updates / batch rows | **100 / 4** |

Per-trajectory presentation counts remain
`[17,17,17,17,17,17,17,17,16,16,16,16]`; supervised counts are twelve zeros.
The reference schedule presents 100 memory and 100 behavior rows in addition
to those 200 masked trajectory presentations. The 128-row memory inventory
does not imply that all 128 indexes receive a presentation in 100 updates.

**8,245 is the sum of the full-reference denominators, not one global loss
divisor.** For each update, the control's mean CE is multiplied by
`active_control_labels / reference_labels`, preserving that update's original
full-reference denominator. Independently recounted scale range:
**0.6891891891891891–0.7529411764705882**. All logged scales equal their per-batch
ratios; logged scaled losses agree with `control_mean_loss * loss_scale`
within float32 rounding (maximum relative discrepancy `6.96e-8`). Every logged
loss is finite and nonnegative. The frozen native training code applies this
scale **before backward**, confirmed by the existing fake-optimizer regression.

The source/recipes retain fresh AdamW, seed 0, learning rate `3e-5`, rank 8,
the four-row schedule and starting original adapter. This is not an accidental
two-row mean-loss control that upweights the retained rows. It is nevertheless
a different optimization trajectory once the trajectory labels are removed.

## Saved state and reference joins

Frozen `read_training` passes against independently reconstructed inputs and
PREFLIGHT, checking all six training-file hashes, all saved adapter-file hashes,
rank, saved masks/rows/recipe and all 100 dose-log records. The control result
has one fit, 100 updates, 5,977 active / 8,245 reference tokens and no parent.

- Initial state:
  `207ad43ef65f1f6ba7c50d37f5d5dfa8c2253d1cb301e585d7b6b7a78bb93990`.
- TRAIN final = AFTER mounted = AFTER final:
  `1f3d2614dfa66a6648f83fbcd96579b99464a59a7711a595b221200e9ad6383b`.
- Control training-result SHA-256, exactly joined by AFTER:
  `6df0dc838fbb4662da5433308d58be5742ffb5d1b78181946d21fea88e85f859`.
- Saved adapter: **80,792,096 bytes**, independently hashed SHA-256
  `270ccfd7d1fce75f55ab41a99b783147df0fb30381dc83b01a2cd083ea1438c2`.

STATES records agree with the initial/final values. AFTER has zero fits/updates
and training disabled. The bound source verifies frozen base, adapter files
and reference training files before writing COMPLETE. **Saved adapter-file
hashes are independently recomputed here; tensor-state/base equality remains
joined runtime evidence, not a new tensor/base-model hash computation.**

Only direct SEQ-250/251 reference artifacts were used. Full-arm TRAIN/AFTER
hashes, reference file inventories, both fresh-arm result hashes and embedded
reference panels match the control binding. Old and fresh source collections
replay. The fresh stimulus digest remains
`c046ded73172add43c0aec684fe8c4c53c0f78467f65accffc0d423699b1a2c9`.
All **24 control starting prompts** match their full-reference task/condition
counterparts. Actual subsequent actor/memory traces join their native captures;
the supplied-text services return the exact reference records. Later histories
are not asserted identical after different actor choices. No parent guidance
or injected source hints occur in the control readout prompts.

## Recomputed old and fresh endpoints

All **16 old + 8 fresh control episodes** replay with the captured helper.
Recomputed scores equal the individual saved records and result panels.
Reference full-arm old episodes and fresh TRAINED episodes were also rescored
from the supplied reference records, without restarting reference runs.

| Endpoint | Loss-off goals | Full-arm goals | Control actor calls | Service reads | Legal commits |
|---|---:|---:|---:|---:|---:|
| Old ON_OWN_TEXT | **0/4** | 3/4 | 14 | 10 | 0 |
| Old ON_PARAMETRIC | 0/4 | 0/4 | 22 | 16 | 2 |
| Old ON_UNAVAILABLE | 0/4 | 0/4 | 24 | 16 | 4 |
| Old OFF_OWN_TEXT | 0/4 | 0/4 | 11 | 3 | 5 |
| Fresh OWN_TEXT | **0/4** | 3/4 | 14 | 10 | 0 |
| Fresh UNAVAILABLE | 0/4 | 0/4 | 24 | 16 | 4 |

Control is **0/2 on order-0 tasks and 0/2 on reversed tasks** in every panel.
Full-arm supplied-text endpoints are 2/2 order-0 and 1/2 reversed on both
graphs. Legal partial commits in failed control episodes are not final-goal
successes. There is no fresh parametric condition in this readout.

### First commands and route failures

Task order below is 0,1,2,3. These are actual captured first commands:

| Control conditions | First-command sequence |
|---|---|
| Old ON_OWN_TEXT / ON_PARAMETRIC / ON_UNAVAILABLE | `READ EVENT E_IUCLJZNTJB`; `READ EVENT E_ZOXRVIWPH2`; `READ EVENT E_IUCLJZNTJB`; `READ EVENT E_ZOXRVIWPH2` |
| Old OFF_OWN_TEXT | `ROUTE P_4OSO65OGRU`; `ROUTE P_R3YCJCLGZO`; `ROUTE P_4OSO65OGRU`; `ROUTE P_R3YCJCLGZO` |
| Fresh OWN_TEXT / UNAVAILABLE | `READ EVENT E_4HC5RAOOVD`; `READ EVENT E_ZIWO2HIMER`; `READ EVENT E_4HC5RAOOVD`; `READ EVENT E_ZIWO2HIMER` |

Starting with a valid read is not sufficient for grounded L1→L2 use. **All
eight supplied-text control episodes subsequently issue the goal NODE as a
ROUTE argument**, rather than a port, and terminate `invalid_command`, zero
commits. Old first-route arguments are
`N_XVM2USEMBJ, N_XVM2USEMBJ, N_PJCMWXVRLH, N_PJCMWXVRLH`;
fresh arguments are
`N_JHDSMLVMTV, N_JHDSMLVMTV, N_44AN3UAXYD, N_44AN3UAXYD`.
Old supplied-text actor counts are `[2,5,4,3]`; fresh counts `[3,4,2,5]`.
The fresh control's endpoint/error/count pattern matches the original-parent
SEQ-251 supplied-text pattern; no bytewise identity of every generation is
claimed from that pattern alone.

Old ON_PARAMETRIC stops are `duplicate_address`, `invalid_command`,
`duplicate_address`, `invalid_command`. Both unavailable panels stop on
duplicate reads in every task. Old OFF_OWN_TEXT stops are `invalid_route`,
`dead_end`, `invalid_route`, `duplicate_address`. All are preserved as failures.

## Retention and held audit — unequal achieved effects

All 32 control retention records were rejoined to their native calls, exact
saved old-memory targets and appropriate wrappers. All 16 held audit responses
were replayed through rebuilt held cases; the case-bundle digest matches the
bound held-audit digest.

| Probe | Loss-off control | Full reference |
|---|---:|---:|
| Exact old recall W0 | **11/16** | 16/16 |
| Exact old recall W8 | **11/16** | 16/16 |
| Held audit overall | **15/16** | 16/16 |
| Held true cases | 7/8 | 8/8 |
| Held fault cases | 8/8 | 8/8 |

The same five exact-recall failures occur at W0 and W8: indexes **0,2,3,5,14**,
events `E_W76IFWI75T`, `E_X3YBAILZSM`, `E_QAQ5WQZQRH`, `E_GFK5ULRT6G`,
`E_PRS7JYHK37`. All have terminal, nontruncated responses; these are real
exact-recall misses, not missing calls. The failed audit is **true case 10**,
event `E_VEEAOY3IIH`: expected `NONE`, actual `E_VEEAOY3IIH\n`, recorded
`WRONG_OUTPUT`—a false positive on a correct record.

Thus the control differs by **5/16 recall outcomes on each wrapper and 1/16
audit outcomes**. Nominally identical common rehearsal data and normalization
did **not** yield equal retention/audit performance. This imbalance must remain
visible alongside the routing contrast, not be described as an equal-effect
rehearsal control.

## Counts and interpretation

AFTER contains **173 native calls = 109 actor + 16 parametric memory + 32
retention + 16 audit**, within its 208-call bound. Old task work contributes
71 actor + 16 memory calls; fresh task work contributes 38 actor calls. The
remaining text/unavailable memory services are local callbacks, not extra
native calls. PREPARE/TRAIN have zero generation calls. All 173 native captures
have null errors and terminal, nontruncated responses. Recorded maxima are
**649 prompt tokens / 55 output tokens**, within 2048/160.

**Supported:** in this matched-input, matched-reference-denominator realization,
removing trajectory-label loss does not reproduce the full arm's old/fresh
supplied-text routing gains. The traces locate the control's failure at legal
command use despite access to correct supplied records, not at acquisition of
the shared text. The saved masks establish that the intended loss ablation
actually occurred.

**Not supported:** that the contrast isolates a purely higher-level action
mechanism while holding achieved memory/audit ability constant. The retention
difference is an observed downstream effect of the different optimization
path, not evidence that common labels or denominators were mismatched; it
also prevents an equal-achieved-retention interpretation. Trajectory loss
could affect command learning, preservation/stability of shared representations,
or both. This one run cannot separate those mechanisms or establish necessity
across seeds, worlds and lineages. The result is not generalized planning,
fresh parametric storage, a complete grounded memory→action loop, or H1/H2.

No unresolved primary accounting, replay or artifact-join failure was found.
Behavioral failures and verification boundaries are explicit above. Original
base/ancestor weights were not reloaded or re-audited. Full-reference claims
are anchored to the existing SEQ-250/251 artifacts, not new reference fits.

## Local checks and stopping boundary

Archive command:
`sha256sum gpu_artifacts_local/astra_event_two_hop_lesson_control_terminal_20260914_attempt1/terminal.tar.gz`.
Primary checks ran as local Python here-docs under
`PYTHONDONTWRITEBYTECODE=1 python3 -`, with frozen `source/` first on the module
path and native ML imports explicitly blocked. Existing `validate_reference`,
`control_masks`/`training_batch`, `read_training`, lesson/collection replay,
episode scoring and captured-response audit helpers were reused. No native
training or inference entry point was executed.

Primary output: `CONTROL_PRIMARY_ACCOUNTING_AND_REPLAY_PASS`;
**273 selected JSON files / 11,309,526 bytes**, bounded by 340 files, 4 MiB per
JSON and 64 MiB aggregate. Both 100-line loss files were read separately.
Archive/adapter hashing was streamed. Archive output:
`CONTROL_ARCHIVE_SELECTED_EXTRACTION_PASS` (305 files). The first comparison
assumed a named archive root and stopped on that assertion; inspecting five
member names showed `./`, and the corrected lookup verified every selected
member. This was a review-path correction, not a run/artifact repair.

Two targeted frozen CPU regressions rerun via guarded `unittest`: **2 PASS**.

- `tests.test_astra_event_two_hop_lesson_control.ControlTests.test_exact_mask_schedule_denominator_and_doses`
- `tests.test_astra_event_two_hop_lesson_control.ControlTests.test_fake_optimizer_scales_loss_before_backward_no_reencode_drift`

**Bounded review finished. No extra hardening or experiments. Ownership released
to Main for staging.**
