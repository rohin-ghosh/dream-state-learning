# SEQ-073: bounded fresh-solution behavioral reread — design only

Date: 2026-09-12. Decision owner: Main. Status: PROPOSED; no panel generated,
no adapter loaded, no GPU queried/reserved/launched, no new fit, no repo edits.
This note is a sidecar; it does not alter Main's RuleGame work or reservations.

## 1. Question and proposed smallest comparison

Can the **six existing** external-oracle mini-sudoku useful/corrupt adapters
(optimizer seeds 0/1/2) retain their earlier small material-specific first-ACT
effect on one prospectively selected 16-item panel whose **exact solution
grids** occur in neither the 32 training items nor the previous 16 canaries?

**Yes, the existing runner can express this without fitting or changing the
runner. Use six paired OFF/ON invocations, not common OFF + six ON.** The public
pair path requires both conditions, their different fresh-process PIDs, and
paired custody/cleanup receipts. `--condition on` is an internal worker path:
it requires a preexisting bound `PAIR_STARTED.json`. It is not a standalone
common-OFF orchestration interface. Do not fabricate that receipt or bypass
the pair controller to save five OFFs.

The smallest new surface is a CPU-only, panel-aware preparation/reduction
helper outside the repository, **specified here but not implemented**. Main
must decide scope and approve its exact implementation/design before any new
panel generation. No deliberation, ratification, qualification, or execution
approval is asserted by this note. No material generator or diagnostic launcher
that schedules training is to be called.

## 2. Grounded inputs: actual successful paths, not failed attempts

All remote paths below are recorded on node 3 (the existing `gpu/ovx2_ssh.sh`
transport in the historical capture script). These are **receipt-recovered
locations**, not a fresh assertion that files still exist remotely. No SSH was
performed for this design. Main's later CPU preflight must check availability
and rehash bytes; an absent adapter is a stop, never a reason to refit.

```bash
BASE=/localhome/local-rohing/astra_diagnostics
SEED0_ROOT=$BASE/astra_mini_sudoku_useful_corrupt_20260912_attempt3
SEED1_ROOT=$BASE/astra_mini_sudoku_seed1_20260912_attempt1
SEED2_ROOT=$BASE/astra_mini_sudoku_seed2_20260912_attempt1
SOURCE=/localhome/local-rohing/astra_sources/bc4250ed5ea3c058b5f8a81a4f66ed033bcb745b
OLD_SOURCE=/localhome/local-rohing/astra_sources/3d56c5cd703cb6adc66f732905845a1b787a40ec
PYTHON=/localhome/local-rohing/v2/venv/bin/python
MODEL=/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
```

| Optimizer seed / arm | Exact actual adapter directory | `adapter_model.safetensors` SHA256 |
|---|---|---|
| 0 useful | `/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_useful_corrupt_20260912_attempt3/training/useful_seed0` | `42096acafe563db0e614ce7cd42e874159545822066cdfeb47b6501eee0fd14c` |
| 0 corrupt | `/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_useful_corrupt_20260912_attempt3/training/corrupt_seed0` | `9cb1a01d93222131587f1cd4f550844007c681f32eb13788b4fabda9aace4689` |
| 1 useful | `/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_seed1_20260912_attempt1/training/useful_seed1` | `91d29c8ec9ff80a6708c03d4fe7bcd9a9a7975a206af398a6b036b24dc7473f3` |
| 1 corrupt | `/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_seed1_20260912_attempt1/training/corrupt_seed1` | `88d322b9f5d3370a6612bc23534a3b3da06090464d833bec5f1e30722a83510e` |
| 2 useful | `/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_seed2_20260912_attempt1/training/useful_seed2` | `8f5d08e15b93b7f3184fc3f255c44bff4c2a05d03c3a5dde34ec9b81739af3e0` |
| 2 corrupt | `/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_seed2_20260912_attempt1/training/corrupt_seed2` | `5c1e1ce199c00c6a8003db8cc97948c765fb170700eabbb12087298058cc081e` |

Each root has its own `material/` directory and authoritative
`logs/{useful,corrupt}/probe_spec.json`; the old outputs are
`probes/{useful,corrupt}/{off,on}/`. Material locations are therefore exactly:

```text
/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_useful_corrupt_20260912_attempt3/material
/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_seed1_20260912_attempt1/material
/localhome/local-rohing/astra_diagnostics/astra_mini_sudoku_seed2_20260912_attempt1/material
```

The following saved material bytes agree across all three roots:

| Relative material file | SHA256 |
|---|---|
| `useful.json` | `c6954d48246a37cdd1ac06309d819664e37a2119d92cbf6d2eceeb945caf5db4` |
| `corrupt.json` | `e670bb9ddb8bfddea8774e435fec5054b5ab0cf4dca5a07a1ba7f433c95b2127` |
| `oracle_sources.json` | `e86d480dbcc723115aaf4789e477efd23f69302e9cf4109243dc64ed3ba90785` |
| `ids.json` | `6468cb882e64145c0529b7765df2956c3e04426060f4243d447f4d5abf3b76a2` |
| `local_pins.json` | `84f9a010ce2f0367f0456ccc25da4149a9fb833322414a0c897248cb1c2f43fb` |

Training IDs are `rg/mini_sudoku/1850000` through `1850031` inclusive;
old canaries are `rg/mini_sudoku/1900050` through `1900065` inclusive.
The saved 48 records contain **42 distinct exact solution arrays**, not 48.
Known old canary/training solution matches are 1900054/1850030,
1900055/1850026, 1900059/1850012, and 1900065/1850015.

The historical fit contract is rank 8, alpha 16, seven attention/MLP projection
targets across 28 layers, lr 1e-4, batch 1, grad accumulation 1, three epochs,
96 updates, max length 4096, no packing, no trainer chat-template application.
Useful targets are native oracle `ACT:` solution grids; corrupt targets use a
fixed one-position cyclic donor shift over the same 32 training rows. The
pre-rendered native user-chat context is masked; only the action target plus
EOS is supervised. Recorded dose is 1,216 target tokens/pass, 3,648/fit;
77,124 is total context-plus-target token exposure, not target-only dose.
These are historical facts to bind, **not preparation commands to repeat**.

## 3. Exact generation/source/model contract

Keep the frozen Qwen2.5-7B-Instruct snapshot above and the complete
`expected_model_hashes` and arm-specific `expected_adapter_hashes` inventories
from each original probe spec. Do not replace expected inventories with newly
observed hashes. Check the entire directories, not just the six weight hashes
in the table. The capsule omits adapter weight payloads; the recorded remote
rehashes are historical evidence only. Local pins and configured loader
identity still do not authenticate official model origin or loaded runtime.

Use the seed1/2 `SOURCE` for all six new pairs. Seed0 used `OLD_SOURCE`.
Read-only comparison of both preserved source archives found the runner,
probe, custody, backend, gym, batch loop, gym backend and state files identical
to each other and the corresponding files inspected in the current checkout.
Material preparation differs by the optimizer-seed extension; equal corpus
bytes do not imply all source trees are identical.

| Critical source | SHA256 |
|---|---|
| `organism_v6/run_reasoning_neutral.py` | `dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496` |
| `organism_v6/reasoning_neutral_probe.py` | `28431b85d8df5c348b484476e7ad921f2c2e5d795ee203b8e2cc0498c03c5607` |
| `organism_v6/neutral_pair_custody.py` | `49ae8d5f9a215fb42abe51dee60f0084218973fcc81f43d161ecfef7abaeda6b` |
| `organism_v6/model_backend.py` | `93feee1cb30720b565aac8f570d368cad8e137789b39f228fbd8ed264123a3f5` |
| `organism_v6/reasoning_gym_gym.py` | `da9879537d33923c9702b1a5b3d63d6a2fcb396a64e110a886bd445c33e1c084` |
| `organism_v6/reasoning_gym_families.json` | `220071c8783ed4d608b04015c188e8b22fc5745c10f250c7fbd724dd854649ea` |
| `organism_v6/bootstrap_reasoning_gym.txt` | `9b2cf7521bc75fe995ffa05a117f61d12ded24395e8b315e384f58add846e1f1` |
| installed `reasoning_gym/games/mini_sudoku.py` | `20b77f97b1f5a9aa364940311d6647c4fa3e2b69834995371e0b20dd9f818c0c` |

The exact recorded generator path is
`/localhome/local-rohing/v2/venv/lib/python3.12/site-packages/reasoning_gym/games/mini_sudoku.py`.
Require `reasoning_gym==0.1.25` **explicitly**: the gym constructor checks package
availability/family names but is not itself sufficient version pinning. Saved
entries record difficulty `empty: [8,12]`; use native defaults, not a difficulty
override. The installed generator implementation was not fetched/read remotely
in this design; its source path/hash and the wrapper invocation are recovered.
Later preflight must hash it and record the actual dataset config/defaults.

Existing CPU interfaces, requiring no family-file edit:

```python
from organism_v6.reasoning_gym_gym import ReasoningGymGym, installed_version, parse_id, decode_answer
from organism_v6.mini_sudoku_behavior_material import board_from_text, validate_solution, one_tick_prompt

assert installed_version() == "0.1.25"
gym = ReasoningGymGym(families_path=FAMILIES, require_package=True, strict_verifier=True)
family, seed = parse_id(episode_id)
dataset, entry = gym._item(family, seed)
```

`gym._item` calls `reasoning_gym.create_dataset(family, seed=seed, size=1)` and
uses `dataset[0]`. Seed is the dataset seed, not the index and not optimizer
seed. Entry fields are `question`, `answer`, and `metadata` including `puzzle`,
`solution`, `num_empty`, `difficulty`, `source_dataset`, and `source_index`.
`gym.episode_from_id(episode_id, budget_ticks=1)` and
`one_tick_prompt(gym, episode_id)` preserve native prompt construction.
`dataset.score_answer(answer=..., entry=entry)` is the native verifier.

For mini-sudoku the frozen family file permits **canary seeds [1900000,1900100)**.
Arbitrary 19001xx/200xxxx IDs would be classified as training, not accepted as
new canaries. Explicit in-range IDs need not be in `canary_set`; do not alter
that file. `mini_sudoku_behavior_material.prepare(...)` is **not** a fresh-panel
API: it hard-codes the old 32+16 IDs and emits new training commands. Do not use
it or `gpu/astra_mini_sudoku_diagnostic.py` for this reread.

Every condition retains the old settings:

```json
{"gen_seed":0,"seed_salt":15420,"budget_ticks":1,"wake_max_tokens":400,
 "scratchpad_max_tokens":100,"total_token_budget":38400,"max_episodes":16,
 "max_model_len":4096,"worker_timeout_seconds":900,"order":["off","on"]}
```

The backend applies its tokenizer's user-message chat template with
`add_generation_prompt=True`, temperature 0.7, and explicit per-request seeds.
Wake seed is `(crc32(f"{episode_id}/{tick}".encode()) ^ gen_seed) & 0x7fffffff`.
Post-outcome scratchpad seed uses the execution ID, gen_seed, and salt 15420.
Same new episode ID therefore gives the same wake seed across all arms; do
not set gen_seed to the optimizer seed. Sampling parameters not explicitly
set by this backend remain the pinned runtime's defaults, not invented values.
Historical logs identify vLLM 0.27.1, bfloat16, TP=1, no quantization; wrapper
settings are eager mode, GPU memory utilization .85, maximum LoRA rank 32.
Record and compare installed runtime versions before launching; a changed
runtime is a deviation for Main to decide, not silently equivalent evidence.

Episodes use fresh non-retrieving ledgers, no parent/history/material input,
one tick and the existing post-outcome Scratchpad (100-token cap). Keep the
scratchpad even though it is not the primary endpoint. One generation can
contain multiple ACT lines: one tick is **not** a guarantee of exactly one ACT.
Never truncate ledgers to their best action or use the native best as primary.

## 4. Prospective fresh-panel rule — decide before generating

Proposed deterministic rule, to be ratified unchanged or replaced by Main
**before inspecting any candidate**:

1. Exclusion source is all 48 saved oracle records above, after validating
   their manifests, array/text/metadata bindings and cross-seed equality.
   Form the forbidden set from all 32 training and all 16 previous-canary
   solution arrays (42 unique grids); never use only the four known overlaps
   or only the previously solved canaries. Also forbid their puzzle arrays.
2. Read the historical `declared_prior_cpu_examined_ids` without generating
   those extra items. It includes 1900050–1900069, 1900020–1900042 and other
   train/out-of-range IDs. Also exclude frozen `canary_set` IDs and any
   additional previously examined IDs that Main declares **before** generation.
   No corpus, adapter or historical outcome rankings enter candidate selection.
3. Candidate order is exactly `rg/mini_sudoku/1900070` through
   `rg/mini_sudoku/1900099`, ascending, inclusive: **30 candidates maximum**.
   A declared prior-exposure ID is logged/skipped before generating it.
   Stop immediately after 16 acceptances; do not generate the unused suffix.
4. For each generated candidate require strict canary classification; native
   question/answer parse equal metadata puzzle/solution; integer cell ranges;
   matching blank counts; row/column/2x2-box/givens validity; native canonical
   and semicolon-decoded solution scores exactly 1. Independently enumerate
   the valid 4x4 completions and require exactly one completion of its givens,
   equal to the saved native solution. These checks use CPU oracle data, not
   Qwen. A malformed/inconsistent/nonunique generator result **fails the whole
   preparation**; do not improve the panel by silently discarding invalid data.
5. Reject a structurally valid candidate if its exact solution appears in
   either historical solution set or an already accepted candidate, or if its
   exact puzzle appears in either historical puzzle set or an accepted item.
   Otherwise accept it immediately. Compare full integer arrays/row-major
   tuples, not seed equality or hash equality alone. Hash the arrays as evidence.
6. Fewer than 16 accepted after the fixed 30-ID list is **PANEL_INSUFFICIENT**:
   emit rejection evidence, no executable probe specs, and return to Main.
   No automatic reseed, fallback range, canary-range expansion, source change,
   difficulty quota, outcome screening, or sampling until a positive result.
7. Freeze the 16 IDs in acceptance order, complete entries, solution/puzzle
   hashes, every rejection reason, historical exclusions, source/config pins,
   unrendered first prompts and tokenizer-rendered prompt hashes. Preregister
   the resulting manifest and all six spec hashes before the first model load.
   No selected IDs or candidate hashes can be supplied in this design because
   generation has intentionally not occurred.

Use exactly the existing `_encoded` serialization (sorted keys, UTF-8,
ensure_ascii=False, indent=2, allow_nan=False, final newline) for comparable
board/entry SHA256s. Native first prompts include a real `CLOCK:` line: preserve
and record it; do not monkeypatch clocks or post-hoc normalize mismatches away.
Require actual first-prompt bytes to agree across conditions and with the
preregistered prompt for each item. A mismatch is an auditable comparability
failure, not permission to replace that item or drop the failing condition.

This is exact labeled-grid nonoverlap, **not** nonisomorphism under digit/row/
column transformations, absence from model pretraining, independent task
families, or a certificate of globally unseen data. Historical exposure beyond
the declared records remains unaudited. The new data is one shared panel, not
16 new panels and not 48 independent observations from three seed repeats.

## 5. Minimal future helper interface and commands

These commands are **not executed** and the helper is **not presently supplied**.
They specify the smallest implementation Main could approve. It lives at
`/tmp/astra_fresh_behavior_panel.py`; only `prepare` and `reduce` subcommands,
no fit, launch, model inference, model-outcome selection, or GPU argument.
Use the original source working directory, not Main's moving checkout.

### CPU prepare interface

```bash
# Only after Main's scope decision and approval of the helper/design bytes.
FRESH_ROOT=$BASE/astra_fresh_behavior_panel_20260912_attempt1
DESIGN=/tmp/astra_fresh_behavior_panel_design_20260912.md
DESIGN_SHA256=$(sha256sum "$DESIGN" | cut -d ' ' -f 1)
env -C "$SOURCE" CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE" \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PYTHON" -B /tmp/astra_fresh_behavior_panel.py prepare \
  --seed0-root "$SEED0_ROOT" --seed1-root "$SEED1_ROOT" --seed2-root "$SEED2_ROOT" \
  --source-root "$SOURCE" --design "$DESIGN" --design-sha256 "$DESIGN_SHA256" \
  --approval-ref "${MAIN_APPROVAL_REF:?Main must supply exact scope approval}" \
  --prior-exposure-json "${MAIN_PRIOR_EXPOSURE_JSON:?Main must freeze additional ID list, even if empty}" \
  --out-new "$FRESH_ROOT"
```

Required preparation behavior (the contract, not permission to implement now):

- Validate design/approval binding and exposure-list hash before generation.
  Refuse any existing/symlink output; never overwrite a failed or partial root.
  Validate all historical material manifests and six successful fit-to-adapter
  bindings against the saved specs/audits and the hashes in this note. Preserve
  complete original spec/manifest hash inventories as inputs, not updated pins.
- CPU-rehash current model and all six adapters using
  `reasoning_neutral_probe.file_hashes`; compare with original specs including
  auxiliary files. Validate actual rank, seed, corpus digest, 96 steps and
  target-mask/dose metadata. No training execution or extra optimizer state.
- Verify the complete existing custody source snapshot and material source
  inventories; compare critical source files to historical values above.
  Explicitly pin/hash the installed mini-sudoku generator as well as its
  procedural dataset/factory dependencies and package versions. The pair
  wrapper's own snapshot does not substitute for generator attestation.
  Any unavailable historical dependency pin must be disclosed, not invented.
- Regenerate the **48 old items only after authorization**, using native
  `_item`, and require exact saved entry/puzzle/solution identity before using
  the candidate list. This is source reproducibility checking, not retraining.
  Verify all three saved datasets agree; regenerate once, not three times.
- Apply section 4 exactly. Freeze answers in evaluator-only provenance files;
  they are never added to episode prompts, scratchpads, model history, or
  training corpora. Load only the local tokenizer for prompt/context checks,
  never `VLLMBackend` or model weights. Check rendered context plus generation
  caps fits 4096; no truncation, prompt shortening or exclusion by token length.
  Verify post-outcome prompt bounds as well; a bounds failure goes to Main.
- Write `panel.json`, `candidate_audit.json`, `preflight.json`, `specs/` and a
  hash manifest, and create an empty `probes/` parent. Use exclusive creation,
  hash and seal preparation files; leave only the future output parent writable.
  Preflight records CPU-only status, model calls=0, fit count=0, GPU calls=0,
  exact source and helper hashes, inventories and disposition of every check.
  CPU regression coverage for the helper must include overlap rejection,
  within-panel duplication, 30-item exhaustion, version/hash drift, output
  reuse, and missing/invalid first ACT; no synthetic case is real panel evidence.

Spec creation is **copy original spec, then change only these fields**:

```python
spec.update(
    episode_ids=panel_ids,
    families_path=str(source_root / "organism_v6/reasoning_gym_families.json"),
    probe_root=str(fresh_root / "probes"),
    output_dir=str(fresh_root / "probes" / f"seed{seed}_{arm}"),
    training_life_roots=[str(seed0_root), str(seed1_root), str(seed2_root)],
    lineage_roots=[str(root / "training") for root in (seed0_root, seed1_root, seed2_root)],
    panel_role="exploratory",
    selection_used_episode_ids=sorted(all_declared_prior_ids),
)
```

Here `all_declared_prior_ids` is the union of train/old-canary IDs, the historical
CPU-examined IDs, configured canary IDs and Main's frozen extra-exposure list.
Document that these denote prior exposure/exclusion, not Qwen screening.
Do **not** include solutions, approval metadata or extra keys in runner specs:
`read_spec` requires the exact `FIELDS` set. `families_sha256` stays unchanged;
all adapter/model fields and generation/budget/order values stay unchanged.
`exploratory` is intentional, not `untouched_confirmation`. No new path may
overlap any historical root, model, adapter, or source input.

For `specs/seed{seed}_{arm}.json`, write a sibling `.sha256` containing only its
digest; run `run_reasoning_neutral.read_spec(path, digest)` during CPU preflight
with CUDA hidden. That validates specs and file inventories without model load.
The runner regenerates entries from IDs; it cannot consume the frozen panel
JSON directly. Thus later source/entry/prompt checks are essential.

### Exact existing probe entrypoint, future only

After Main accepts preparation and owns a compatible available device/lease,
use this fixed sequence on one device (all pairs OFF then ON). No GPU number
is assigned here, and no RuleGame device is borrowed implicitly.

```bash
for cell in seed0_useful seed0_corrupt seed1_useful seed1_corrupt seed2_useful seed2_corrupt; do
  SPEC="$FRESH_ROOT/specs/$cell.json"
  SPEC_SHA256=$(cat "$SPEC.sha256")
  env -C "$SOURCE" CUDA_VISIBLE_DEVICES="${RESERVED_GPU:?Main must assign an exclusive available device}" \
    V6_MODEL="$MODEL" PYTHONPATH="$SOURCE" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
    VLLM_WORKER_MULTIPROC_METHOD=spawn HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    "$PYTHON" -B -m organism_v6.run_reasoning_neutral \
    --spec "$SPEC" --spec-sha256 "$SPEC_SHA256" --allow-gpu || break
done
```

This is six fresh-process pairs, with no `--condition` argument and no trainer
or diagnostic-controller invocation. The fixed useful-first ordering preserves
the old arm ordering but retains time/order confounding; do not silently switch
ordering after looking at a result. Main may choose a different prospective
order before generation and update this design, not during outcome inspection.
The wrapper verifies owned-group cleanup and device process absence; failures
preserve receipts and retain the reservation pending Main's reconciliation.
The loop stops on operational failure, not on a weak/negative behavioral score.
Retain all partial evidence; no automatic rerun, extra sampling or reused roots.

### CPU reduction interface

```bash
env -C "$SOURCE" CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE" \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$PYTHON" -B /tmp/astra_fresh_behavior_panel.py reduce \
  --prepared-root "$FRESH_ROOT" --output-new "$FRESH_ROOT/first_act_report.json"
```

`mini_sudoku_behavior_analysis.py` hard-codes `EPISODE_IDS=1900050..1900065`
in both config and results validation; its stock CLI will reject this panel.
Its `LIMITATIONS` also asserts the old four overlaps. The full historical run
auditor binds the same original train/canary material. Neither is an arbitrary
fresh-panel reducer. Do not edit their constants, monkeypatch globals, reuse
the old overlap text, or run the historical auditor as if it certified this run.

The helper should reuse the existing `_Inputs`, `_pair_custody`, `_episode`,
`_totals`, and `_difference` semantics from the pinned analysis source, but
replace only panel enumeration/validation with the frozen manifest's 16 IDs
and supply accurate new limitations. Fail closed on custody/config mismatch,
duplicate/missing result entries or missing ledgers. Valid completed episodes
with no first ACT or invalid/unmeasured first ACT score zero; a missing process
or artifact is an incomplete run, not a zero-filled scientific observation.
Bind all 12 configurations, full source/generator inventories and native first
prompt bytes to preflight. Record adapter OFF absence/ON identity, raw action
strings, score vectors, all ACTs, worker/cleanup receipts and input hashes.

## 6. Endpoint and interpretation frozen before outcomes

For each seed report useful OFF/ON and corrupt OFF/ON **first-ACT solved counts
over 16**, plus `G_seed = (useful_ON-useful_OFF)-(corrupt_ON-corrupt_OFF)` on
per-item scores/counts. A solve requires first recorded ACT, validated measured
native score exactly 1. Missing/invalid/unmeasured first ACT = 0, with reason.
Later ACTs never rescue it. Secondary: zero-filled first-ACT native mean,
native best mean, ACT counts/status counts, direct useful_ON-corrupt_ON, and
per-item action/score agreement across all OFFs. Preserve each arm's OFF even
if all OFFs agree; never assume old OFF=0 still holds on fresh items.

Report all three contrasts, mean/median/range, all 16 items and absolute useful
success. A descriptive recurrence of the previous directional pattern means
all three `G_seed > 0`; anything else is mixed/absent recurrence. This label is
not a significance test, a minimum-utility pass, or claim confirmation. Do not
change the endpoint to continuous score if solved-count recurrence is absent.
No p-values/confidence claims treating repeated cells or seeds as independent
puzzles; no success-triggered extension or failure-triggered rank/dose search.

The three adapters per material arm differ in **optimizer seed on identical
data**, not independent training-data draws. The fresh 16 puzzles are shared
by all six adapters. Removing exact known solution reuse narrows one concrete
contamination explanation; it does not establish general G2, parenting/H1/H2,
clean lineage, independent-data replication, an unseen-model-pretraining panel,
or a reliable general reasoning engine. A negative result only says the weak
effect did not recur by the frozen criterion on this bounded filtered panel.

## 7. Counts, bounded cost and stop conditions

| Quantity | Forecast / bound |
|---|---|
| New fits / updates / supervised tokens | **0 / 0 / 0** |
| Existing adapters | 6, no checkpoint selection |
| Old entries regenerated in approved CPU preparation | 48 once, after validating all three saved copies |
| New candidate entries generated | 16–30 on success, at most 30; possibly fewer if prior-exposure exclusions exhaust supply |
| New distinct evaluation puzzles / solutions | 16 / 16 if preparation succeeds |
| Model loads / condition processes | 12 = 6 OFF + 6 ON |
| Episode-condition observations | 12 × 16 = **192**, not 192 independent puzzles |
| Wake generation requests | 192 |
| Post-outcome scratchpad requests | 192 if one ACT each as historically; actual count is outcome-dependent |
| One-ACT output reservation | 192 × (400+100) = **96,000** max reserved output tokens |
| Unchanged declared ceiling | 12 × 38,400 = **460,800** reserved output tokens; input tokens not included |
| Worker execution timeout ceiling | 12 × 900 s = **180 device-minutes**, plus controller hashing/cleanup overhead |

Historical seed1/2 condition-log windows were 2.117–2.450 minutes, mean 2.308
(first runtime log through shutdown log, not full process wall time). Twelve
such windows imply ~27.7 A40-minutes before wrapper/preflight overhead. Forecast
**35–50 A40-minutes on one similar available A40**, plus CPU preparation and
model-inventory I/O; plan up to 60 minutes operationally, not a guarantee or
lease request. The old 37.48 A40-minute two-controller total included four fits
and eight conditions, so it is not a direct twelve-condition estimate.
Heavy new multi-ACT output, shared-node contention, caches or changed runtime
can change cost; retain the existing per-worker/token ceilings. A desired
aggregate 60-minute hard stop would need Main-approved owned-process lifecycle
handling, not a naive timeout that leaves engines or alters cleanup guarantees.

CPU-only panel validation is small (at most 78 distinct old+candidate entries
and a reusable independent 4x4 completion enumeration), but full model hashing
is substantial I/O and is repeated by the unchanged runner. No dollar quote
is inferred without an already authorized rate: incremental accounting is
`device_minutes / 60 * existing_hourly_rate`, not new spending authorization.

For comparison only, common OFF + six ON would be 7 conditions, 112 episodes,
56,000 one-ACT output tokens and a 268,800 declared ceiling. That reduction is
**not supported by the unchanged paired controller**, so it is not this plan.

Main stops before GPU on: no scope approval, any pin/source/entry drift,
missing actual weights, fewer than 16 eligible candidates, overlap or prompt
contract failure, incomplete CPU/provenance checks, or unavailable compatible
device/lease. No alternative panel or new fit is automatically authorized.

## 8. Evidence inspected and explicit limits of this design

Only the requested terminal record and its directly relevant material/probe
code and receipts were inspected. No broad literature or unrelated experiments.
Primary local evidence is under `research_notes/astra_memos/`:

- `ASTRA_BEHAVIOR_REPLICATION_TERMINAL_2026-09-12.md`.
- `receipts_20260912/astra_mini_sudoku_terminal_20260912.tgz`, SHA256
  `cfe1ca3f319c82a6e118a42449ae24607c8db8270961bc7ca76af9db4d55e16e`.
- `receipts_20260912/astra_behavior_replications_terminal_20260912.tgz`, SHA256
  `e45c272e3781583f3ac1bae80d600ac35449b68e183b3b499d6b34d182ddd39b`.
- Original material manifests, six probe specs, fit metadata, configuration/
  generation/results records, source inventories and selected timing logs in
  those captures and their existing `/tmp` extracts.
- `receipts_20260912/astra_mini_sudoku_run_audit_final_20260912.json`, the seed1/2
  run audits, `astra_replication_claim_review_20260912.md`, the capture/reducer
  scripts, and `astra_behavior_replications_remote_rehash_20260912.json`.
- Preserved `/tmp/astra_mini_sudoku_source_3d56c5cd.tar` and
  `/tmp/astra_mini_sudoku_source_bc4250ed.tar` for scoped source comparison.
- `organism_v6/{run_reasoning_neutral,reasoning_neutral_probe,neutral_pair_custody,
  reasoning_gym_gym,mini_sudoku_behavior_material,mini_sudoku_behavior_analysis,
  mini_sudoku_behavior_run_audit,model_backend,batch_loop,state}.py`, plus
  directly relevant family/bootstrap/post-outcome definitions.

No tests of a new helper are claimed: none was implemented. No new native
puzzle was generated, no new tokenizer/model call was made, and no live remote
availability/runtime check was performed. The only new artifact is this design
file. **Next action belongs to Main: accept/revise the bounded design and helper
scope before panel generation; do not launch from this note alone.**
