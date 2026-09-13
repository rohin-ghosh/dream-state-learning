# Contrastive perception wrapper — CPU handoff, 2026-09-13

Prospective authored Level0/1 infrastructure only. Main owns source preparation,
protocol, native tokenizer preflight, node2 allocation/profiling and any launch.
No native tokenizer/model/GPU work, network, Git, repo edits, live-root reads or
helper/archive modifications were performed by this sidecar. CPU fixtures are
not native certification or experimental evidence. Earlier analyzer and vacancy
helper deliverables remain frozen.

## Exact source layout and pins

Use one fresh source snapshot with exactly these four files, no `.git`, bytecode
or additional files. Helper scripts live OUTSIDE this four-file source directory.
All paths in the specification must be absolute; source, model, protocol, binding,
helpers, spec and wrapper must be disjoint from the new run root.

- `organism_v6/__init__.py`: Main supplies its actual SHA256.
- `organism_v6/birth_skill_corpus.py`:
  `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`.
- `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
- `organism_v6/train_adapter_v3.py`:
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`.

Pinned, unchanged helper records use `{ "path": "/absolute/path", "sha256": "..." }`:

- `material`: `/tmp/astra_contrastive_perception_material_20260913.py`,
  `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.
- `encoder`: archived `research_notes/astra_memos/receipts_20260912/astra_perception_fit_run_20260913.py`,
  `f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`.
- `public`: original `/tmp/astra_birth_skill_probe_run_20260913.py`,
  `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`.
- `reflection`: `/tmp/astra_reflection_fit_run_20260913.py`,
  `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`.

Paths may be relocated byte-identically. The archived encoder is imported under
its own module name and `encode_training` receives explicit rows, tokenizer,
trainer and public helper arguments. No globals, grids or archive code are
monkeypatched. Cold model loading calls the unchanged reflection helper.
Vacancy and release call the original public `gpu_state`: full all-process XML,
planned index/UUID, 30-second query timeout. No compute-only CSV substitution.

## Specification and CLI

Main writes a JSON spec with exactly the following required content (no invented
GPU UUID, paths, pins or lease). Additional spec fields are preserved as metadata,
not interpreted as configuration overrides:

```json
{
  "source": "/tmp/astra_contrastive_source_20260913_attempt1",
  "source_files": {
    "organism_v6/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
    "organism_v6/train_adapter_v3.py": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
  },
  "model": "MAIN_SUPPLIES_ABSOLUTE_NODE2_MODEL_PATH",
  "runner_sha256": "aea1b5d84d6d79efa7dbdd43ab8e93bf0483fd4383531eae363cdbb4b7583d55",
  "material": {
    "path": "/tmp/astra_contrastive_perception_material_20260913.py",
    "sha256": "b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d"
  },
  "encoder": {
    "path": "/tmp/astra_perception_fit_encoder_20260913.py",
    "sha256": "f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51"
  },
  "public": {
    "path": "/tmp/astra_birth_skill_probe_run_20260913.py",
    "sha256": "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"
  },
  "reflection": {
    "path": "/tmp/astra_reflection_fit_run_20260913.py",
    "sha256": "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"
  },
  "protocol": {
    "path": "/tmp/ASTRA_CONTRASTIVE_PERCEPTION_PROTOCOL_2026-09-13.md",
    "sha256": "57e5f84c6188b29eb6b1c296eb544627a28d8025cf933a142ee945cbe9430f18"
  },
  "binding": {
    "path": "/tmp/astra_contrastive_model_binding_20260913.json",
    "sha256": "MAIN_SUPPLIES_ACTUAL_BINDING_SHA256"
  },
  "gpu_index": "MAIN_SUPPLIES_INTEGER_NODE2_INDEX",
  "gpu_uuid": "MAIN_SUPPLIES_OBSERVED_NODE2_UUID",
  "lease_end": "MAIN_SUPPLIES_NUMERIC_LEASE_END_UNIX"
}
```

The five MAIN_SUPPLIES values are deliberately unresolved and invalid for execution: Main/Pauli supplies the actual model path, binding hash, integer index, observed UUID and numeric lease end. The concrete staging paths are proposed new node2 paths, not an existing deployment or allocation. Binding uses the unchanged
public helper's `scope_binding`/`validate_binding` contract: official model-only
base revision/files, corpus source pins and native environment, never a clean
ancestry claim. An existing public verification receipt accepted by that helper
is also supported. No hostname is embedded; node2 routing remains Main-owned.

Run all commands with the same native interpreter spelling and bytes. Preparation
records both; symlink/venv spelling is not normalized away.

```sh
PYTHON -B /absolute/astra_contrastive_perception_run_20260913.py prepare \
  --root NEW_ROOT --spec-path SPEC.json --spec-sha256 SPEC_SHA256 --allow-native
PYTHON -B /absolute/astra_contrastive_perception_run_20260913.py controller \
  --root NEW_ROOT --plan-sha256 PREPARED_PLAN_SHA256 --allow-gpu
PYTHON -B /absolute/astra_contrastive_perception_run_20260913.py collect \
  --root NEW_ROOT --plan-sha256 PREPARED_PLAN_SHA256 \
  --completion-sha256 CAPTURE_COMPLETE_SHA256 --out NEW_EXTERNAL_COLLECTION_DIR
```

These are interfaces, not approval or instructions to launch now. The internal
`worker --root ... --plan-sha256 ... --stage ... --allow-gpu` command is spawned by
the controller in a fresh session for each stage, not a manual resume interface.

## Mandatory pre-GPU native preflight

`prepare --allow-native` sets CUDA visibility empty and uses only the real local
CPU tokenizer and v3 encoder, not a model. It hashes source/model/protocol/helper
inputs and records model/environment/interpreter bindings. The final generator
is rebuilt from its pinned corpus; no renderer search or data changes.

Both TRAIN12 arms must have identical supervised token-ID vectors per paired row,
including exactly the native EOS, identical arm-neutral seeded epoch orders,
and actual v3 masks matching the complete assistant template. Context, template
tail and batch padding remain loss-masked. Split/dropped/truncated rows, EOS or
token-boundary drift fail preparation, preserving failure evidence with no retry.
Do not lengthen max_len, shorten prompts, alter targets or omit rows to pass.

Prepared files: `prepare_started.json`, `material.json`, `train_plain.json`,
`train_contrastive.json`, `calls.json`, `costs.json`, and pinned `plan.json`.
Training receives only the selected arm's training items. Generation requests
contain only messages, row/call IDs and tokenizer renderings, never evaluation
targets/proofs. The full material is evaluator data, not a learner prompt.

Costs include per-row total/supervised tokens, per-arm context plus masked-tail
tokens, four-epoch padded token totals, presentations and supervision totals.
Actual context and padding costs may differ; there is no equality gate or
compute-equivalence claim. Native token counts are not established by CPU mocks.

## Execution, collection and budget limitation

Order: `fit_plain`, `fit_contrastive`, then OFF/plain/contrastive each crossed
with D1, D2, C-record, C-general. Each readout loads a fresh engine. There are
14 fresh owned process groups: two cold base fits, twelve cold readouts.
Each fit: rank8/alpha16/dropout.05/LR1e-4/seed0, four epochs, batch4/accum1,
maxlen1024, no packing, 12 updates/48 presentations, LoRA-only trainability.
Each readout: 12 calls, archived inference settings and max192 output tokens.
Total: 24 updates, 96 presentations, 144 generation calls.

2700 seconds is a HARD controller limit including cleanup, not a measured
feasibility claim. Collection has a separate 180-second bound. Six-hour lease
margin is required after the controller-plus-collection budget. Per-stage caps
remain 600 seconds/fit, 240/readout with 40 seconds reserved for owned cleanup
and the unchanged all-process release query. Stage caps are ceilings, not an
additive throughput forecast: spending every cap would exceed 2700 seconds.

**The twelve-cold-readout envelope is UNPROFILED.** Main must measure node2
cold-start, repeated verification and query costs before treating this as a
feasible full experiment. This sidecar cannot truthfully supply a measured
smaller envelope without native calls. No smaller panel count, warmer shared
engine, longer timeout or fabricated timing has been substituted. If native
profiling cannot fit 2700 seconds, preserve its actual limited-work receipt and
return to Main for a separately specified smaller profile/experiment; do not
launch this as a certified-completable envelope. An exhausted controller fails,
keeps partial artifacts, never retries and never scores incomplete captures.

Cleanup only targets the spawned owned worker process group through the unchanged
public helper. Graphics/foreign processes cannot be killed to obtain vacancy.
Every completed stage requires start/launch/release identity and artifact hashes.
No raw responses are scored until all 144 captures close. Collection is exclusive
through a sibling `ROOT.collection_claim.json`, including failed collection
attempts; it does not modify completed root evidence.

Collection revalidates custody and uses the pinned material scorer, including
original strict grammar, field indicators, raw outputs, finish status, held
pairing and canaries. It reports fit manifests/losses, measured fit times,
generation tokens/times, context costs and controller elapsed time. The material
screen is descriptive only: `automatic_pass=false`, `scientific_pass=null`.
No G1/P1/H1/H2, mechanism, clean founder, child SLEEP or original L2 promotion.

## Final Main integration details

Deploy the wrapper to `/tmp/astra_contrastive_perception_run_20260913.py` on node2,
copy the four source files beneath `/tmp/astra_contrastive_source_20260913_attempt1`,
and copy each helper/protocol to the exact external path in the spec example.
The archived encoder copy remains byte-identical despite its relocated filename.
Main supplies the actual model and binding identified by Pauli. No extra launcher
is needed: Main's existing simple guarded pattern can detach the controller CLI.

Protocol: `research_notes/astra_memos/ASTRA_CONTRASTIVE_PERCEPTION_PROTOCOL_2026-09-13.md`,
observed SHA256 `57e5f84c6188b29eb6b1c296eb544627a28d8025cf933a142ee945cbe9430f18`.
The example binds these exact bytes at the staged protocol path. Preparation and
every later verify recheck this pin; do not change protocol or plan in an old root.

The generator must rebuild canonical material SHA256
`7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`.
Prepared `material.json` uses the generator's exact canonical serialization, so
it has the same byte pin as Main's prebuilt candidate. Main need not deploy that
candidate separately; it can be compared with preparation output if desired.

Final CPU suite: **10 tests PASS (4.199 seconds)**. Native tokenizer preflight and
budget profiling remain Main-owned and unperformed here. This is not permission
to launch or a statement that the 12-cold-readout budget is feasible. EDITSTOP.

## CPU validation

`python3 -B /tmp/test_astra_contrastive_perception_run_20260913.py -v`

Actual pinned encoder and scorer run with a mocked tokenizer and native backend.
Tests exercise paired target/EOS/masks, unequal context, 14 identities/144 raw
captures, two separate cold fits, strict collection and tamper/one-shot behavior,
pins, truncation, nonfinite fit rejection, and owned timeout/vacancy cleanup.
No test invokes a GPU query, native tokenizer, model load or real worker process.
