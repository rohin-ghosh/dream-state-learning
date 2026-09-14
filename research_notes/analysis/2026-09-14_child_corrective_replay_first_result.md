# Child-selected corrective replay: fixes both errors, loses one prior success

2026-09-14 UTC. Bounded independent terminal reduction. Both100-update fits and
fresh AFTER readouts are complete. No model/tokenizer load, forward, generation,
fit, relaunch, remote write, kill, notebook edit, or commit by this worker.
Owned changes are the new stdlib reducer, its focused tests, and this memo.

## Endpoint: neither arm dominates all outcomes

The common archived baseline is the collecting A1 cue actor's A2 BEFORE,
**2/4 GOAL arrivals with W0 actual reader**. Both forks start from that same
actor, unlike the earlier across-development-arm adult comparison.

| Raw-replayed endpoint | Common BEFORE | CHILD_CORRECTIVE | UNIFORM_REPLAY |
|---|---:|---:|---:|
| All-four own routing | 2/4 | 3/4 | 4/4 |
| Initially wrong tasks2/3 | 0/2 | 2/2 | 2/2 |
| Initially right tasks1/4 | 2/2 | 1/2 | 2/2 |
| Own episodes with READ | 4/4 | 4/4 | 4/4 |
| Own episodes with second READ | 4/4 | 3/4 | 2/4 |
| Own actual reader calls | 8 | 7 | 6 |
| Reader-disabled routing | 2/4 | 2/4 | 2/4 |
| Reader-disabled READ / second-READ episodes | 4/4 /4/4 | 4/4 /4/4 | 4/4 /4/4 |
| Held external-text routing | 8/8 | 8/8 | 8/8 |
| New exact W0 recall | 0/4 | 2/4 | 4/4 |
| New exact W8 recall | 0/4 | 2/4 | 4/4 |
| Earlier-memory W0 recall | 8/8 | 8/8 | 8/8 |
| Earlier-memory W8 recall | 7/8 | 8/8 | 6/8 |
| Unknown exact MISS | 0/4 | 0/4 | 0/4 |

Corrective selection is not superior on the primary all-four routing endpoint:
it fixes both initially wrong tasks but loses previously successful task4.
Uniform fixes both without that loss, but has worse prior-adult W8 retention.
Do not hide either failure behind the initially-wrong subset or an aggregate
new-recall improvement. All original wrong answers remain in raw artifacts.

### Selected/unselected and task partitions

Source indexes are zero-based; episode numbers in this memo are one-based.
The two child choices are **[0,2]**, while actual wrong task indexes are **[1,2]**.
The selection replay preserves exactly those choices and all16 mechanical view
origins; no goal-matching substitution or candidate filtering occurred.

| Partition | Corrective W0 /W8 recall | Uniform W0 /W8 recall |
|---|---:|---:|
| Selected source records0/2 | 2/2 /2/2 | 2/2 /2/2 |
| Unselected source records1/3 | 0/2 /0/2 | 2/2 /2/2 |
| Records associated with initially wrong tasks1/2 | 1/2 /1/2 | 2/2 /2/2 |
| Records associated with initially right tasks0/3 | 1/2 /1/2 | 2/2 /2/2 |

All these new-record recall partitions are0 at baseline. Selecting source0 for
wrong task index1 retains evidence about the failed/non-goal option. That is a
sourced negative-option choice, **not automatically useless material**. The
prefit11:30 qualification explicitly anticipated partial-memory risk because
unselected addresses receive no direct rehearsal and unknown MISS was already0/4.

## Raw mechanisms, not an aggregate causal story

Corrective AFTER own episode2 reaches its goal despite a wrong second reader
return. It first reads the accurately rehearsed source0, whose destination does
not match this task's goal, then reads unselected `E_VEEAOY3IIH`:

```text
actual:   EVENT E_VEEAOY3IIH AT N_NQ7J7B2WK DID P_S7AIZXQ77X GOT N_WBXQVETNWG EVIDENCE R_V77FCXUDYO
expected: EVENT E_VEEAOY3IIH AT N_NQ7SZP2WK3 DID P_X3KIPDIW4F GOT N_6AUMRWYCVK EVIDENCE R_YJNOWTRK53
action:   ROUTE P_X3KIPDIW4F
```

It selects the remaining public port and succeeds. This is consistent with
negative-option evidence helping eliminate the first choice, but the trace alone
does not establish that internal strategy or isolate its cause. Accurate recall
of the goal-reaching record is not necessary for this observed successful action.

Corrective episodes3/4 both first read unselected `E_DEX6OHDHJP`, receiving the
same unsupported content, then correctly read selected source2:

```text
actual:   EVENT E_DEX6OHDHJP AT N_KGA6B2GC43 DID P_6Q379NEQYX GOT N_R2R3W7QECX EVIDENCE R_O32FCXUDYO
expected: EVENT E_DEX6OHDHJP AT N_IRD6ZSHY2B DID P_FWMNJO5UYN GOT N_DH2AYPUMUT EVIDENCE R_3KI5HYYQOV
second:   EVENT E_QQ43NOEYBQ AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD EVIDENCE R_6MJCDE77X2
action:   ROUTE P_ONQCERJ5LE
```

That action is correct for episode3, wrong for episode4's `N_DH2AYPUMUT` goal.
Episode4 previously chose `P_FWMNJO5UYN` and succeeded. Thus the lost prior
success occurs in a mixed accurate/inaccurate reader context; it is not merely
the selector's first non-goal choice failing to help. Three of seven corrective
actual reader calls are wrong (two distinct unselected addresses); all six
uniform actual reader calls are exact. These are content failures, not LF-only
serialization issues. Each displayed EVENT string ends with LF in the raw data.

### Uniform old-W8 failures retained

Original-bank old recall stays4/4 at both wrappers in both arms. Prior-adult
W0 stays4/4. Prior-adult W8 changes3/4 →4/4 corrective, versus3/4 →2/4 uniform.
Uniform `OLD_RECALL_W8_07.json` retains the pre-existing failed address
`E_3FIXU7HBPN`, with a different terminal, untruncated malformed answer:

```text
EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ2P Presented with REQUEST R_I67ACACQG72F containing EVIDENCE E_7KIPDI2Z4A4Z DID E_3FIXU7HBPN DO OBLIGATE N_Q5JLOL7SKZ2P TELL P_IU6QG7MO23DU THAT EVIDENCE E_KGA62CO7ZJYX SUFFICES FOR EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ2P
```

Uniform also newly fails old row8, `E_3K7UVCYOTM`:

```text
actual:   EVENT E_3K7UVCYOTM AT N_NQ7SZP2WK3 DID P_2RVHKWHYEC GOT N_WBXQAC5J5Z EVIDENCE R_VQGRQACZ74
expected: EVENT E_3K7UVCYOTM AT N_Q5JLOL7SKZ DID P_2RVHKWHYEC GOT N_S6IHXBULZX EVIDENCE R_VQGRQACZQB
```

These failures are scored strictly against original source records, without
identifier repair, substring extraction, or salvaging a malformed answer.

## Training and binding checks

Source commit: `e3a575d79cc45641ed647a3c4ce028e8aa10960f`, immutable remote root
`/tmp/astra_corrective_sleep_source_20260914_attempt2`. Only attempt2 supplied
these runs. Main reports attempt1's incomplete packaging never launched and
5674 source files hash-matched; this audit does not repeat that broad custody
operation. It independently matches the three relevant remote files to the
local frozen Git snapshot:

- Driver: `6b3c7f07b271b7599e4a78e473852be774faf774d21de571000f152d31b8fa09`.
- Training helper: `1b8f4d59c6fc391d735d39df4b9567e9268bfc926c93eb7d8d01504142c47f4b`.
- Pure selector: `24716244dbb919f2e909598655b8cd184a8e83368e6d3b8732855c517134f2e3`.

**REQUEST.runner_sha256 identifies the driver; train RESULT.runner_sha256
identifies the training helper.** This disclosed distinction is intentional,
not source corruption. The reducer checks each hash against its own source
role, rather than allowing arbitrary REQUEST/RESULT mismatch. AFTER uses the
driver hash. Other request fields join unchanged.

Both forks load initial adapter state
`07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`, initial
adapter-file hash `7e6fe380553b20e23b63f5934199fb04a44388079ce3fcc68b0ccbb9e9602f26`,
and prior train receipt `3eaad009cc1546fa62209a1871b0b129140db485afc4676f057a93333faf8046`.
Both bind the same base state
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`, tokenizer,
original memory, prior adult collection, cue capture, A2 collection, selection,
and exact archived BEFORE. No sleep note, parent revision, or OFF diagnostic
output enters these masks.

The A2 COLLECTION SHA is
`d5d9162827c5f621644d96791c751283b50cde954c30c9ac87e2ed9a273f55c5`;
SELECTION SHA is `f27a29e69ea31acde78cdb2a4dc8a5011d5fe535443fecd23446d369acc0d361`.
The no-fit selector's two captured outputs replay as sourced selections,
including the negative option. Their prompt/output token counts are1016/54 and
1006/52; actual wrong-case preparation, public prompts, individual CALL files,
and all source/provenance hashes join. No selector inference was rerun.

Both training MASKS hashes are
`feeeb242739bc41b7c7140e673a74dea066865f6936636ee14ce9401549c4501`.
All116 encoded masks exactly equal the already-captured source-faithful A2
OLD64+CUE20+NEW32 reference masks. This audit revalidates that reference's
original-row hash, prior-adult replayed rows, all32 new targets against actual
EVENT token IDs, and20 cue targets against actual cue calls. It then checks all
116 masks' contiguous final-target/EOT labels and masked template LF. No
tokenizer reconstruction or model cache is required. Encoding an unselected
row is not training on it: actual sampled indexes, below, determine exposure.

Independent100-update schedule replay:

| Quantity | CHILD_CORRECTIVE | UNIFORM_REPLAY |
|---|---:|---:|
| Actual update1 indexes | `[0,64,84,88]` | `[0,64,84,85]` |
| Actual update100 indexes | `[35,83,108,112]` | `[35,83,90,91]` |
| Reference update100 indexes | `[35,83,90,91]` | `[35,83,90,91]` |
| Old /cue /new presentations | 100 /100 /200 | 100 /100 /200 |
| Original-bank /prior-adult old presentations | 64 /36 | 64 /36 |
| New source0/1/2/3 presentations | 104 /0 /96 /0 | 50 /50 /50 /50 |
| Actual supervised target tokens | 17009 | 16701 |
| Reference supervised target tokens | 16701 | 16701 |
| Loss-scale range | 0.9939759036–1.0434782609 | 1–1 |

The helper's wrapper-major encoded order is respected: selected source0's eight
views occupy84,88,…,112, not a contiguous eight-row block. Both arms use one old,
one cue, and two new rows per update. All100 actual/reference index lists,
causal label counts, count aliases, loss scales, finite logged losses, and
scaled-mean-loss values are recomputed. The actual/reference denominator is
matched per update; token equality is neither assumed nor claimed. Native
receipts/source specify fresh AdamW, LR3e-5, seed0, existing rank8 adapter and
optimizer settings; no old-cue gradient-off arm is involved here.

Saved states, each joined to its fresh AFTER loaded state:

- Corrective: `b82490d3d1f848bcaaa58e2167bcbbb9d5d554d60154e7b61ab7944fbe2094b9`.
- Uniform: `186accc58c90c10487a9c2657119ab06543af04852cf4f60bde14f0e160c06cf`.

Training artifact hashes and adapter-provenance receipts match, and AFTER binds
the corresponding train RESULT. Base immutability, tensor state hashes, finite
gradients, and checkpoint identities are native attestations plus source checks;
this reducer does not load tensors or independently test numerical gradients.
Adapter binaries are left for Main's preservation step.

## Time, calls, artifacts, and reproduction

| Stage, September14 UTC | Start | Finish | Elapsed |
|---|---|---|---:|
| Corrective train | 11:34:25.749101 | 11:36:43.175044 | 137.425943s |
| Uniform train | 11:34:25.789793 | 11:36:42.802253 | 137.012460s |
| Corrective AFTER | 11:36:44.255284 | 11:39:08.910591 | 144.655307s |
| Uniform AFTER | 11:36:43.803914 | 11:39:07.537757 | 143.733843s |

Common archived BEFORE:88 calls,14010 input/2344 emitted tokens.
Corrective AFTER:86 calls,13640/2324 tokens. Uniform AFTER:84 calls,13206/2328.
All258 readout calls are terminal/untruncated and satisfy captured2048-input/
160-emitted-token bounds. The reducer replays all48 routing episodes across
BEFORE and the two AFTERs, all new probes, and48 eight-record old-retention calls.
Fresh AFTER totals170 calls,26846 input/4652 emitted tokens, in addition to the
two earlier selector calls and200 total optimizer updates. No new BEFORE call
or selector call was charged to these fits. Stage durations include setup and
overlap; dollar cost and isolated kernel times are unavailable.

Remote results are under
`/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/corrective_sleep/{arm}/{train,after}`.
Local bounded root:
`gpu_artifacts_local/astra_corrective_replay_first_result_20260914/`.
`capture/` retains terminal train/AFTER files and the completed selection;
`remote.sha256` matches **227 files,1577413 bytes** locally. `source/` is the
frozen Git snapshot. Prior collection, BEFORE, cue and reference masks are reused
from the existing adult-cycle capture roots, not recollected. All raw failures
are retained, including `after/OLD_RECALL_W8_07.json`, `_08.json`, and
`after/new_task/OWN_PARAMETRIC_EPISODE_04.json` in the relevant arms.

```bash
python3 -B tools/astra_corrective_replay_reduce.py \
  --capture-root gpu_artifacts_local/astra_corrective_replay_first_result_20260914/capture \
  --reference-root gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/capture/CUE_REPLAY \
  --prior-root gpu_artifacts_local/astra_adult_cycle_first_result_20260914/after_snapshot \
  --cue-root gpu_artifacts_local/astra_adult_cycle_first_result_20260914/upstream/cue \
  --source-root gpu_artifacts_local/astra_corrective_replay_first_result_20260914/source \
  --output gpu_artifacts_local/astra_corrective_replay_first_result_20260914/ANALYSIS.json

PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_astra_corrective_replay_reduce tests.test_astra_adult_cycle_reduce -q
```

Validation:25 focused+adjacent tests pass. New tests cover exact schedule,
wrapper-major selection, duplicated-choice preservation, dose counts,
actual/reference denominator drift, source bounds, masks, partial evidence,
nonfinite loss, and intentional driver/helper hash roles. Full captured reduction
reports `ALL_STAGES_TERMINAL`, no pending stages, `no_native_imports=true`.

## Limits and release

This is one matched fixed-budget DEV fork from one collecting actor on one bank,
not independent replications or a third adult cycle. Error-driven selection
reuses experienced evaluation tasks and externally posed corrective prompts;
it is not autonomous attention or durable selector learning. Partial-memory
behavior was explicitly unqualified before fitting: unknown MISS remains0/4,
and inaccurate unselected-reader replies complicate the role of selection.
Do not infer either uselessness of negative evidence or a uniquely identified
cause of the lost goal from this single trace. The earlier400-update result is
an unmatched reference, not a third100-update control. No H1/H2, general efficacy,
held-out adaptation, or downstream utility claim follows.

Reducer, focused tests, and this memo released to Main; no commits or new runs.
