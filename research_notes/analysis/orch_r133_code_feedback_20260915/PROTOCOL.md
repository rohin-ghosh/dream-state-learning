# R133 — fresh PUBLIC TRAIN code-feedback collection

Prepared 2026-09-15. **CPU-only handoff; no GPU reservation or launch.**
Main owns publication, release/allocation decisions and any subsequent launch.
This is a bounded, non-material public-TRAIN experiment preparation within the
existing frozen architecture, visibility rules and scientific claim boundaries.
No shared coordination, board, Git, parent notice, publication or R130/R132 files
are changed. The candidate ovx3 physical GPU 7 is not owned by R133.

## Question and limits

The user-supplied motivation is matched checkpoint18404 code ON 0/8 versus OFF
2/8, with mostly JSON/expression interface errors. No underlying evaluation
task, answer, response, evaluation ID, fixed32/held or FINAL data was consulted.
This preparation does not validate that supplied aggregate or reuse its examples.

Measure immediate within-episode revision with actual expression execution
feedback versus a neutral review opportunity. No persistence, metacognition,
learning, H1/H2 promotion or general capability claim follows from this collection.
No optimizer, fit, automatic admission or external parent/provider call exists in
the collector. No safety-refusal model rerouting, credentials or response cache.

## Fixed design

- Exactly 16 fresh PUBLIC TRAIN tasks, four of each public ledger specification
  kind. Reuse R119's public contract, task prose, semantic reference functions and
  normalization; **never call R119 or legacy task builders**.
- Two states: FULL fixed checkpoint18404 and the exact same frozen base with all
  LoRA modules actually disabled. Base is not another checkpoint or adapter.
- Three new native calls per task/state: one draft, one interpreter-feedback
  continuation, one neutral-review continuation. Both continuations receive the
  exact same raw draft and original prefix; neither receives its sibling's text.
- 16 × 2 × 3 = **96 calls** on successful completion. There are 32 drafts and 64
  fork continuations. Counterbalance state and fork ordering by task position.
- Greedy native decoding: `do_sample=False`, one beam, repetition penalty 1.0,
  2,048 new tokens per call, 32,768-token context ceiling, no trimming or budget
  shrink. “Fresh” means a newly executed call, not a claim of independent samples.
- Exclusive on-disk intent is reserved before every native call. Exceptions stop
  without retry/replacement; refusal, malformed and token-capped returns remain
  recorded in the fixed schedule without rerouting. Incomplete pairs cannot be
  counted as recoveries. A run/episode start marker forbids resuming or replaying
  the same output directory. Main must use the seed/run only once across nodes.

## Freshness and exclusions

The CPU preview uses a newly drawn 256-bit seed, distinct from synthetic test
fixture seeds, and is explicitly `PREVIEW_NOT_LAUNCHABLE`. No production exclusion
inventory was supplied. **Disjointness from protected/prior tasks is not yet
attested.** Do not treat the preview as launch approval or silently use an empty
inventory. Do not recover exclusions by reading protected task files.

Main must supply exactly this hash-only schema (no raw IDs, tasks, answers or
namespace contents):

```json
{
  "schema": "R133_HASH_ONLY_EXCLUSIONS_V1",
  "normalization": "R119_LEDGER_FUNCTIONAL_SPEC_V1",
  "attested_by": "Main",
  "coverage": "R119_LINEAGE_DECLARED_CODE_INVENTORIES",
  "inventory_refs": [
    {"ref": "R119_LINEAGE_CODE_HASH_PROJECTION", "sha256": "<64 lowercase hex characters>"},
    {"ref": "FIXED_PANEL_CODE_HASH_PROJECTION", "sha256": "<64 lowercase hex characters>"}
  ],
  "spec_sha256": ["<64 lowercase hex characters>"],
  "task_id_sha256": [],
  "used_seed_sha256": []
}
```

`spec_sha256` must be nonempty and contain the union of specification fingerprints
from the **explicitly declared inventories**, under the shared R119 normalizer.
There is no global-universe exclusion claim. Main supplies a verified existing
R119 lineage projection and any declared fixed-panel hash-only CPU projection;
this worker neither reads nor exports the underlying panel contents. Inventory
references are 1–16 unique non-sensitive uppercase/digit/underscore labels
(maximum 80 characters) with SHA256s of their source projection artifacts, not
paths, hosts or evaluation IDs. Main verifies those source projection hashes and
their union before attesting; the collector never opens the source inventories.
The pinned `EXCLUSIONS.json` byte hash binds all declared refs/hashes and the
exclusion set; candidate spec/ID/seed filtering is checked again on regeneration.
Other lists contain
digests only and can be empty if genuinely unused. Task-ID and seed hashes use
R119's canonical JSON `digest(string)` convention, not a raw-string SHA256.
Reject the old global coverage label, non-Main attestation, empty/malformed/duplicate
inventory refs, extra fields, invalid/duplicate
hashes or a previously used generation seed. Reject excluded task IDs/specs while
generating with a bounded candidate loop; deduplicate all 16 generated specs.
This is disjointness only against the declared hash inventories under their shared
normalizer. It neither covers undisclosed inventories nor proves exclusion of every
possible extensional equivalence between arbitrary programs.

All prepared bytes are exclusive-created. Tasks are regenerated from the seed
and checked against pinned inventory/source hashes before use. Synthetic
inventories in unit tests are test doubles, not production attestations.

## Interpreter and visibility

Only a final-line JSON object with exactly one string-valued `expression` key is
accepted. Duplicate JSON keys fail. Prior reasoning is permitted. Reuse the
public AST whitelist (500 characters, 100 nodes, bounded integer literals) and
execute with recursive dispatch over `values` and the six public ledger helpers.
There is **no eval, exec or compile call on child code**. Reject other identifiers,
attributes, indexing, comprehensions, keyword args, lists, functions, arithmetic
operators, wrong helper argument types and noninteger results. Bound input list
length, input integers and intermediate integer bit lengths.

Feedback reports the actual attempted-expression parser/interpreter outcome on
one public input: parse/validation/runtime error or observed output. It never
reports the desired output, solution, success label or verification comparisons.
The continuation builder recomputes the receipt and requires exact equality,
rejecting fabricated outputs or extra fields. Neutral review receives no receipt.
Only public specification/input, original model draft and permitted evidence enter
model messages. Task IDs, model-state labels, exclusion metadata and verification
inputs/results stay out. A draft-text digest in actual feedback binds provenance.

Reference semantics and 20 independently generated verification inputs per task
are local scorer-only data for these fresh PUBLIC TRAIN tasks; they are not a
held evaluation. Checks include empty, duplicate, threshold/clamp boundary and
random inputs. Passing means passing these finite checks, not universal proof.

## Readout and evidence

Retain each INTENT, CALL (full raw response and native token IDs), actual PUBLIC
receipt, scorer VERIFY, and failure/terminal record under the node-local run root.
Never export raw child text, failures or expected results to a parent/provider.
Each fork pins the identical draft CALL-file hash and raw-draft digest. No old
logical-call replay and no automatic dataset/admission outputs.

Report the paired fork results separately for FULL and BASE, at task level:

1. **Formatting-only recovery:** a conservative JSON/fence diagnostic extracts an
   already semantically passing draft expression; the accepted continuation has
   exactly that same expression. This diagnostic is scorer-only, never feedback.
2. **Task-semantic correction:** the draft executes but fails task checks, and the
   continuation executes and passes; both responses must be complete.
3. **Interface execution recovery:** parser/sandbox/runtime error becomes an
   observed execution. Do not automatically call this a semantic correction.
4. Record failed-to-passed and unresolved/unclassified recoveries, still-wrong
   responses and incomplete pairs. A malformed draft corrected to a different
   program is not enough to establish pure semantic rather than interface repair.

Compare interpreter-feedback versus neutral-review outcomes within the same
task/state/draft; retain both successful and negative cases and common complete
pair denominators. Greedy calls, 16 task clusters and one seed support only a
small descriptive public-TRAIN probe, not an independent-sample causal claim.

## CPU reproduction

Run only the new suite, without bytecode or pytest cache writes:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 tests/test_orch_r133_code_feedback_collection.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m gpu.orch_r133_code_feedback_collection verify \
  --root research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview
```

The command-line interface exposes **only `prepare` and `verify`**, never native
launch. To prepare a separately authorized, new node-local directory later:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m gpu.orch_r133_code_feedback_collection prepare \
  --root /MAIN_VERIFIED_NODE_LOCAL/new_r133_run \
  --seed FRESH_64_HEX_SEED --exclusions /MAIN_VERIFIED_NODE_LOCAL/exclusion_hashes.json
```

## Runtime integration and pins

CPU preparation/tests require Python 3.10+ and the existing repository modules,
not torch, a GPU, pytest or provider packages. This handoff ran on Python 3.12.
Native loading uses the repository runtime binding in
`gpu/astra_pchain2_native.py`: torch `2.13.0+cu130`, transformers `5.5.3`, peft
`0.20.0`, tokenizers `0.22.2`. The loader also checks installed distribution
metadata (torch distribution `2.13.0`); importable local safetensors model and
adapter support and an appropriate CUDA/driver runtime are prerequisites.
No dependency installation or native import/load was performed in this handoff.

The base loader uses bfloat16, SDPA, `local_files_only=True`,
`trust_remote_code=False`, safetensors, and the exact local tokenizer backend.
The loaded base is state-hashed against
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
Mount the existing rank-8 LoRA, alpha 16, dropout .05, float32 adapter autocast,
on the seven existing projection targets with `is_trainable=False`. Native
observation verifies exact mounted adapter state, base state and all adapter
files against Main's identity document. Every parameter must stay frozen. The
same model is used for both states; BASE enters `disable_adapter()` and checks
all LoRA disable flags rather than assuming an OFF label means a true base.

`PLAN.json.source_sha256` is the exact required source-checksum map, including
the new collector/test, reused public contract/scorer modules, native loader,
bridge, engine, native runtime, state-hash code and engine budget policy. All
must match on the node. Existing transitive repository imports must also be
available; the two new Python files are not a standalone model-runtime bundle.
Reprepare rather than rewriting pins if Main changes a pinned dependency.

There is intentionally no native `collect` CLI subcommand. The exact callable
integration below is **for Main only after every launch prerequisite**, not a
command executed or authorized by this handoff:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import sys; from gpu.orch_r133_code_feedback_collection import collect, read; collect(sys.argv[1], read(sys.argv[2]), expected_gpu_uuid=sys.argv[3])' \
  /MAIN_VERIFIED_NODE_LOCAL/new_r133_run /MAIN_VERIFIED_NODE_LOCAL/main_authorization.json \
  UUID_INDEPENDENTLY_PINNED_BY_MAIN_FROM_R130_GUARD
```

API: `collect(root, authorization, *, expected_gpu_uuid)` and
`validate_authorization(root, authorization, now, *, expected_gpu_uuid)`.
The mandatory UUID argument must come independently from Main's R130 custody
guard, not be copied from the unverified authorization document. Authorization
UUID and `CUDA_VISIBLE_DEVICES` must exactly equal that guard pin.
`host_sha256()` returns `hashlib.sha256(socket.gethostname().encode('utf-8')).hexdigest()`
(raw UTF-8 bytes, **not** the JSON `digest()` convention). Only `host_sha256`
is accepted in authorization and receipts; raw `hostname` is rejected. Internal
hosts remain in Main's gitignored `hosts.env`, never these native receipts.
Main separately owns `gpu/orch_r133_code_feedback_guard.py` and its tests; neither
is part of this worker's write scope.

## Launch prerequisites — all deferred to Main

1. Finish Main's current priorities. Confirm R130 has released the candidate and
   recheck node, physical index/UUID, ownership, processes, capacity and lease.
   There is no resource reservation here, and the code does not probe/acquire one.
2. Supply Main-attested bounded inventory references and hash-only exclusions;
   verify the projection-artifact hashes and their union, declaring omissions.
   Establish a fresh single-use seed/run.
   Reprepare, rerun CPU tests and verify source/task/inventory hashes after any
   Main publication or dependency change. Main owns any required coordination.
3. Pin the actual FULL checkpoint18404 adapter path, state SHA256, exact adapter
   file list/hashes, and frozen Qwen2.5-7B-Instruct base state SHA256. The base hash
   is the existing public collector constant. No real weights were read or loaded
   in this handoff; no synthetic CPU adapter attestation is usable for launch.
4. Main supplies `R133_MAIN_NATIVE_AUTHORIZATION_V1`: `approved_by=Main`, exact
   `plan_sha256`, `r130_released=true`, `allocation_confirmed=true`, `host_sha256`,
   UUID, physical index 7, absolute node-local root/model directory, checkpoint
   18404, adapter identity, native deadline and lease deadline (over 120 seconds
   of margin). Match `CUDA_VISIBLE_DEVICES` to the verified UUID. This is metadata
   binding, not a substitute for Main's actual ownership/physical-GPU check.
5. In a fresh node-local process Main may call
   `collect(root, authorization, expected_gpu_uuid=R130_GUARD_PIN)`.
   It uses the actual existing `orch_guided_native.load_stage` and native Qwen
   engine with local-files-only/offline model loading, frozen parameters, no
   optimizer and empty context. Verify all adapter-disable flags for BASE and
   frozen state/file hashes after collection. CPU mocks test this binding only;
   real loader, weights, CUDA and outputs still require native validation.
6. Keep raw artifacts on verified node-local storage outside the repository and
   weights outside the output root; preserve all evidence. Main provides an
   external process-scoped watchdog as well as the collector's native deadline,
   forward checks and signal timer (Python signals cannot guarantee interrupting
   a wedged native/CUDA operation). No launch is authorized by this handoff.

## Exact write allowlist

- `gpu/orch_r133_code_feedback_collection.py`
- `tests/test_orch_r133_code_feedback_collection.py`
- `research_notes/analysis/orch_r133_code_feedback_20260915/PROTOCOL.md`
- `research_notes/analysis/orch_r133_code_feedback_20260915/CPU_RESULTS.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/CPU_MANIFEST.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview/PLAN.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview/TASKS.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview/EXCLUSIONS.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview_before_main_revision/PLAN.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview_before_main_revision/TASKS.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/cpu_preview_before_main_revision/EXCLUSIONS.json`

The three `cpu_preview_before_main_revision` files preserve the earlier CPU-only
preview before Main's hostname/UUID and bounded-inventory revisions. Its pins are
superseded; never launch or repin it. The current `cpu_preview` is regenerated
from the same not-yet-used-on-model generation seed against the final source pins.
