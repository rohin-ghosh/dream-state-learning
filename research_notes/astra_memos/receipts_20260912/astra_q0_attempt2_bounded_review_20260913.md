# Q0 root1 attempt2 — bounded terminal metadata review

**PASS for metadata consistency and the limited early-stop interpretation. Not
an independent raw-tensor numerical replay or full-capsule custody certification.
EDITSTOP.** Main's full streaming custody validation was in progress at handoff;
this report neither waits for it nor represents it as completed.

## Finding and permitted interpretation

The recorded terminal is `EARLY_XOR_QUARTET_STOP_AUTH`, with
`BOTH_MAP_FIRST_STEP_MISS`, `EARLY_UNARY_TOOL_STOP` and
`OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE`. The scalar canary receipts and frozen
release/label code support those exact labels. The registered first update did
not satisfy every required signed projection and observed-margin predicate for
AUTH, its complementary DERANGED diagnostic, or the permitted unary localizer.

This rejects the tested seed1/rank8/LR3e-5/first-quartet/dropout-.05 path under
its registered gate. It is not zero final accuracy, proof that nothing changed,
a zero-gradient finding, general XOR/opaque-key impossibility, or a completed
unary-versus-XOR learning comparison. Do not retune thresholds, average away
failed rows, select a checkpoint or reinterpret missing readouts to rescue it.
The metadata contains no basis for proposing a gate change.

The primary label is selected by the failed AUTH canary before final acquisition
gates. DERANGED correctly has `diagnostic_only=true` and stops after exactly one
step. Its own canary also fails, supporting BOTH_MAP_FIRST_STEP_MISS rather than
FIRST_STEP_MAP_ASYMMETRY. Unary is the third/final attempted fit, stops on its own
miss, and supplies no completed unary accuracy. The broad-sounding opaque-tool
qualifier must be read together with EARLY_UNARY_TOOL_STOP, not as an independently
measured inability to learn opaque keys. No V_AUTH was allowed as a rescue in this
early-stop branch, even though the pre-fit objective contrast was nondegenerate.

## Recorded first-quartet diagnosis

All three fits use the same four row IDs/order, first quartet template3 and two
opposite-orientation tools, each in mode0 then mode1:
`sq0_28d311a08173871f80da31cc`, then `sq0_3ebf643ab3ecd502a034cccf`.
Signs are AUTH `[+,-,-,+]`, DERANGED `[-,+,+,-]`, unary `[+,+,-,-]`.
Rows below are1-based in that sealed quartet order. Values are rounded for
display only; pass/fail was checked against the stored full-precision scalars.

| Arm / row | Signed gradient-dot-delta | Projection passes | Signed observed margin change | Observation passes |
| --- | ---: | :---: | ---: | :---: |
| AUTH1 | -4.422992058 | no | +0.093272013 | yes |
| AUTH2 | +4.563704236 | yes | +0.255916138 | yes |
| AUTH3 | +5.277372685 | yes | +0.316643055 | yes |
| AUTH4 | -4.559008216 | no | -0.018410318 | no |
| DERANGED1 | +4.491738026 | yes | +0.443562872 | yes |
| DERANGED2 | -4.499817314 | no | -0.061607227 | no |
| DERANGED3 | -5.176779461 | no | -0.784498629 | no |
| DERANGED4 | +4.643787583 | yes | -0.466919931 | no |
| UNARY1 | -4.079117999 | no | -0.147556215 | no |
| UNARY2 | -4.132700889 | no | -1.207629091 | no |
| UNARY3 | +5.401617419 | yes | +0.898502087 | yes |
| UNARY4 | +4.766457955 | yes | +0.305777679 | yes |

Projection passes are2/4 in every arm; observed passes are AUTH3/4,
DERANGED1/4 and unary2/4. The gate needs4/4 of each, not a positive total or
majority. Stored projection bounds are approximately4.24e-8–4.95e-8; observed
bounds6.48e-10–6.60e-10. These recorded failures are negative changes/dots, not
an equality-at-boundary or display-rounding classification. That statement checks
metadata scalar comparisons, not the correctness of the underlying tensor sums.

AUTH1 has negative projection but positive observed change; DERANGED4 has positive
projection but negative observed change. Preserve both facts. The two tests are
separate registered requirements. Their disagreement alone does not establish a
sign bug, numerical corruption, or its cause. Training is the dropout-active
FP32 objective on BF16 forwards; the diagnostic uses the registered dropout-off
`d_canary64` surface. The stored4x4 Gram matrices and error bounds are present;
I did not recompute them, eigenvalues, gradients or parameter deltas from tensors.

## Zero-update audit, not a zero tangent

The audit records128 rows,32 quartets and zero optimizer steps. Both P and V
zero-gradient flags are false in all32 quartets; the stored decision is
`OBJECTIVE_CONTRAST_NONDEGENERATE_AT_INIT`, tangent null, all_both_zero false.
Scalar summaries:

| Quantity | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Legal branch mass M | 0.9999517931 | 0.9999956277 | 0.9999991714 |
| norm_P | 46.35366274 | 54.01863192 | 63.99246348 |
| norm_V | 46.63870118 | 54.16178005 | 64.06559622 |
| norm(V-P) | 0.5091404443 | 0.7259203769 | 2.4240010942 |
| R | 0.0083692361 | 0.0126129877 | 0.0522936258 |
| cosine | 0.9986598357 | 0.9999228612 | 0.9999650808 |

All128 stored negative-log masses satisfy the registered <1e-3 condition, but
quartet29 (1-based) has R0.05229362580551059 and cosine0.99865983569882, failing
both R<.05 and cosine>.999. The other31 satisfy both. Thus near-unit M and high
median cosine do not make the all-quartet contrast degenerate. No claim about
V_AUTH training performance follows: that arm was not run.

## Denominators and exact stopped work

| Stage | Updates | Training row forwards | Natural-prefix forwards | Model forwards | Generations |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00_audit | 0 | 0 | 128 | 128 | 0 |
| 01_eval_OFF_0 | 0 | 0 | 288 | 2353 | 296 |
| 02_fit_P_AUTH | 1 | 4 | 148 | 148 | 0 |
| 03_fit_P_DERANGED | 1 | 4 | 148 | 148 | 0 |
| 04_fit_P_UNARY_TOOL | 1 | 4 | 148 | 148 | 0 |
| Total | 3 | 12 | 860 | 2925 | 296 |

Each fit's148 natural forwards follow the frozen accounting128 initialization +
4 training +16 diagnostic. OFF has288 prefix readouts and296 generations:
128 exact,64 held,96 locality and8 copy generations. The locality breakdown is
8 missing,8 unsupported,16 neighbour and64 wrong-root. There are2065 generated
token IDs;2353=288+2065 and2925=860+2065. I checked all584 OFF operation/row keys
are unique, state OFF/snapshot0/attempts1. All8 stored copy texts match their
prepared expected lines under the existing stripped-text comparison; no fresh
tokenizer decoding was performed.

**No fitted arm reaches32/64/128 or has a snapshot/readout.** All three snapshot
maps are empty. `cells={}`, `checkpoint_curves={}`, complements exact0/held0
with schema denominators128/64, and wrong_root_opposites0 with denominator64
are initialization/default report fields where the two fitted maps were never
evaluated. Report these as **N/A / not measured**, not0% exact/held accuracy,
failed complementarity, or perfect wrong-root locality. Existing OFF observations
do not substitute for missing fitted states. No retention, final extraction,
parenting, endogenous learning, general writer, H1/H2 or robustness result follows.

## Metadata custody and source checks actually completed

- Metadata archive SHA matches the supplied pin. All661 regular archived files
  exactly match the extraction, with no extra extracted files. Of16098 entries
  in SEAL,659 present files match their hashes;15439 missing entries are all
  under `tensors/`, intentionally omitted. The other two local files are SEAL
  itself and FINALIZED; FINALIZED binds the seal hash. This is not a complete
  tensor inventory validation of the full capsule.
- All17 manifest source pins match the extracted frozen source files. The
  executor/tests match the counter-repair pins read before this metadata arrived.
  Recipe and prepared-material hashes agree; training order is the32 registered
  quartets repeated four times. The recorded acceptance receipt reports217 tests,
  zero failures/errors/skips; I did not rerun those model-library tests.
- Five stage jobs, DONE/event hashes, receipts, logs and cleanup hashes agree.
  Process IDs are306490 audit,307094 OFF,307542 AUTH,308239 DERANGED,308779 unary;
  distinct recorded workers, attempts1, no inherited adapter. Manifest/STARTED/
  job/ticket links agree. Cleanup receipts report no error, owned groups empty,
  GPU processes absent and reservation release verified. I did not query native
  processes/GPU or independently reobserve terminal vacancy.
- Audit/fit initial metadata is exactly equal across all attempted fits,
  including392 trainable entries, empty initial optimizer state, parameter
  ordering, RNG and step-zero logits digest. First-step row order and all four
  pre-forward RNG receipts are identical across the three fits. These are
  metadata identity checks, not independent tensor initialization verification.
- Stages finish within their recorded deadlines. Resource elapsed1373.552545s
  and post-fsync FINALIZED elapsed1378.080670s are below2700s, and completion
  wall time precedes the bound deadline. These clocks do not include Main's
  subsequent full-capsule transfer/streaming validation. Pending seal/provisional
  candidate labels are intentional publication stages; FINALIZED and the returned
  report complete that protocol, not a silent rewriting of the sealed candidate.
- Separate native replay JSON is byte-identical to the entire controller log.
  The canonical JSON-with-terminal-newline report hash reproduces250e67b3…;
  FINALIZED equals the report's durable-completion field. The provisional candidate
  equals the report after removing publication completion and scientific_claim,
  as prescribed by `provisional_reduction`. Native numerical replay is Main's
  execution, not mine.

## Exact bindings

| Artifact | SHA256 |
| --- | --- |
| `/tmp/astra_q0_metadata_only_20260913_attempt2.tgz` | `5b5184a64149a02973ccddea8a22a86faeafd8077931481edcefa74e49b6f483` |
| Controller log and separate replay JSON, each file | `1a850b0eed265ed027159747025ea64335b25601944c938b0bcccba55e120a4f` |
| Canonical report object | `250e67b36c16325f5b8042e7731dd71c615cd0387c1f1f6d092b68e8188c87e5` |
| Extracted `manifest.json` | `bd263500a4d1176dfec5e3489db0c20e479f9703eb745b9902dde017d82754d1` |
| Extracted `prepared.json` | `aa96210c73048d9980011930cb57e3407beacbe7ed094ae13b46dda187de4852` |
| Extracted `SEAL.json` | `abac7fe73e1b5952cb3d92be21bb604d304c57470ee734a4ce3889694e5ef937` |
| Extracted `FINALIZED.json` | `cd6fb48d488fe05efdc45928eba1bbb03f38aafea1b2c9d35335591160c750e1` |
| Frozen `source/gpu/astra_pairwise_q0.py` | `1459c037cccf2f043bc02f40fb9957f38c5620a4d0bcfc8cbb4ebf30fd31182a` |
| Frozen `source/tests/test_astra_pairwise_q0.py` | `bc08064301721157fa353247559105a31b11ee3e0c3b14d5dbbbfa255b9d42e3` |
| Result-blind terminal audit protocol | `3f9df78746e39cd2007e1a4099846a65f2c72fc476bdc6e3707321df0221a4fe` |
| Prospective numerical-registration memo | `76d56de8689a1591df4d120cbd84e6653d18e15ed371f30cd47b8aef4d7f8b64` |

DONE metadata pins, paths relative to the extraction:
- `stages/00_audit/DONE.json`: `8c81517751d531eccb2d4d589607b51a827d69b42b140cdc9ae38907c07aef38`.
- `stages/01_eval_OFF_0/DONE.json`: `36098b5c9e37c38bfbd559a705a762cf2967d3dc4872c50b8e079b109b3f58dd`.
- `stages/02_fit_P_AUTH/DONE.json`: `53fcd2737d1480362b8dc3c8bfb0f80d8a010870f5face6a01e685a7f33e9fbf`.
- `stages/03_fit_P_DERANGED/DONE.json`: `68c93be749dfdafa510375b08f0c553c4d47e763e533e4a5311f25976695e16c`.
- `stages/04_fit_P_UNARY_TOOL/DONE.json`: `4a7a65b5afe95b270129aa506417da05391e7e68500658bd10affc690cce3a60`.

Main-supplied full-capsule path:
`gpu_artifacts_local/q0_20260913_attempt2/astra_pairwise_Q0_root1_20260913_attempt2.tgz`,
SHA `ec5527e3e6aecc0e5f0c10e4a956620fefc4f4f8da8cfa6d4c6b4980e6ecc2ec`.
I did not open or hash that3.167GB capsule. Its full custody and omitted tensor
contents are outside this metadata-only certification.

## Methods, independence and stop

Used bounded text reads, `sha256sum`, and in-memory Python standard-library
JSON/hash/tarfile/Counter/statistics checks. I compared stored scalar predicates
and recomputed signed changes from stored before/after margins; I did not load
tensors, invoke the executor/reducer, decode tokens, regenerate logits, take
gradients, verify PSD numerically or perform native/model/GPU/network/Git work.
The registered protocol and frozen release/math code were read, not rewritten.
No polling or broader post-result design review was performed.

I did not author this Q0 experiment. Prior project involvement includes downstream
writer/learning helpers, probe/projected-runtime tests, manuscript/semantic reviews
and separate relay/birth-skill CPU reviews. This is a non-blinded metadata audit,
not wholly project-independent replication. Only this review was written. Main
owns full custody, integration and any subsequent experiment decision.
**EDITSTOP.**
