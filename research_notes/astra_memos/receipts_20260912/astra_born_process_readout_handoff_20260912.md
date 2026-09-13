# Born-child readout adapter — final integration handoff / EDITSTOP

2026-09-12 local date. The schema section was published early for Main.
Only the three assigned `/tmp/*born_process_readout*20260912*` files are owned.
No launches, native loads, tokenizer loads, network, outcome reads, or Git changes.

## Normalized lineage v1 (Main supplies; never synthesize completion)

`validate_lineage(lineage)` will validate an exact JSON-only schema. All hash
values are lowercase SHA256 hex. `value_hash` is SHA256 over the existing
diagnostic's sorted, ensure_ascii=False, allow_nan=False JSON plus newline.
Every receipt has `receipt_sha256 = value_hash(receipt without receipt_sha256)`.
This is **normalized receipt integrity**, not authentication of upstream releases.
Main must check the real completed, released artifacts first and bind these
normalized values to those exact bytes; the adapter never reads release outcomes,
loads native weights, or turns an incomplete upstream job into COMPLETE.

Exact top-level keys:
`schema`, `source`, `base`, `birth`, `writes`, `claim`, `origin`.
`schema = born-child-readout-lineage-v1`; `writes` has exactly P_WRITE and A_WRITE.
`claim = SOURCE_AUTHORED_BIRTH_NOT_CLEAN`;
`origin = UNRESOLVED_LOCAL_HASHES_ONLY`.

Receipt shapes (all fields required, no extra keys):

- source: `receipt_sha256`, `files` (nonempty source path -> SHA256 map).
- base: `receipt_sha256`, `model` (absolute loader path), `model_files`
  (nonempty relative model file -> SHA256 map).
- birth: `receipt_sha256`, `release`, `source_receipt_sha256`,
  `base_receipt_sha256`, `arm` (= AUTH), `root` (one corpus root 0/1/2),
  `candidate_sha256` (frozen corpus.digest(candidate)), `panel_sha256`
  (value_hash of frozen driver's full fixed_requests), `adapter`
  (absolute original immutable birth LoRA path), `adapter_files`, `identity`.
- each write: `receipt_sha256`, `release`, `source_receipt_sha256`,
  `base_receipt_sha256`, `parent_birth_receipt_sha256`,
  `parent_adapter_files_sha256` (= value_hash(birth.adapter_files)),
  `formation_receipt_sha256`, `own_wake_arm` (= P or A), `material_sha256`,
  `warm_start` (= true), `adapter`, `adapter_files`, `identity`.
- release: exactly `sha256` (actual upstream completed release bytes), `status`
  (= COMPLETE; normalized only after Main verifies upstream completion/release).
- adapter_files: exactly adapter_config.json and one of
  adapter_model.safetensors / adapter_model.bin, with SHA256 values.
- identity: unchanged configured_generation_identity shape:
  `backend` (= vllm), `model_input`, `adapter_input`, `adapter_files`,
  `default_max_tokens` (=400), `default_temperature` (=0.7),
  `scope` (= configured loader inputs; base authentication requires lineage pins).

Both descendants must join the **same birth receipt and immutable birth file
hashes**, source receipt, base receipt and shared formation receipt. They must
have different output paths from each other and the original birth. Both are
single warm-started LoRAs, not base-OFF fits and not sequential P -> A writes.
**Final schema clarification:** independent provenance does not require unequal
output or material bytes. Equal hashes are retained, including unchanged birth
weights at distinct descendant paths, rather than selecting away nulls. Main
verifies actual independent fits/material sourcing; the reducer reports weight
equality flags without treating equality as either success or failure.
The base path/model_files are fixed across all cells. Source files must include
the inspected readout helper, frozen birth driver, diagnostic and birth corpus
at their exact pinned hashes (implementation exports REQUIRED_SOURCE_PINS).

## Mapping and sequencing

Actual cells are BIRTH_ONLY, P_WRITE, A_WRITE. The explicit local mapping to
legacy schedule slots is BIRTH_ONLY -> OFF, P_WRITE -> P_ON, A_WRITE -> A_ON.
Those are *schedule slots only*, never model identities. Raw request/event arm
names remain the actual new cells. No global monkeypatch of diagnostic.CELLS.

Capture invokes unchanged play_task four times, not run_evaluation (which
aggregates early). Per-action rewards/judgments remain necessary environment
events; no metric aggregate is emitted before all three RuleGame captures and
all three fixed128 conditional captures have closed and replayed. Conditional
requests are identical to the initial birth driver's fixed_requests, held in a
separate capture, with no history or answers in prompts. This is repeated/exposed
dev diagnostic, **not independent holdout**. Maximum model calls are 96 + 384 =
480, not a guarantee. Failed/incomplete captures cannot be scored or padded;
invalid text is retained and scored with all prescribed denominators.

Main owns worker creation, fresh child-only processes, immutable native loading,
supervision, native audits, authoritative release verification, and GPU operation.
The adapter will accept an injected backend; it supplies no launcher/autochain.
Only one-root exploratory local utility/retention contrasts are reported; no
P1/G3/G5/H1/H2/freeze or clean-origin verdict.

## Public helpers and Main integration

Implementation: `/tmp/astra_born_process_readout_20260912.py` (393 lines).
Tests: `/tmp/test_astra_born_process_readout_20260912.py` (400 lines).

- `value_hash(value)`: canonical normalized receipt/panel hash; compatible with
  diagnostic.value_hash, **not** the birth driver's indented value_hash.
- `validate_lineage(lineage)`: exact schema/receipt/parent joins; returns actual
  cell -> birth/write receipt. Main must supply its already-release-verified
  normalized values. It does not load/check real base or adapter weights.
- `conditional_requests(lineage, candidate)`: verifies initial candidate/root
  and panel pins; uses the **unchanged frozen driver.fixed_requests**. Use the
  exact initial candidate, including label configuration, not a new default
  candidate unless Main verifies it is byte-equivalent.
- `capture_rulegame(out, lineage, cell, backend, *, worker_id)` and
  `capture_conditional(out, lineage, cell, candidate, backend, *, worker_id)`:
  separate fresh directories; capture only, no metric or usage reduction.
- `capture_cell(out, lineage, cell, candidate, backend, *, worker_id)`: convenience
  composition for **one** Main-supervised already-loaded fresh child worker.
  Creates rulegame/ and conditional/. It neither loads nor closes the backend;
  Main owns successful native close and process join. No retry in that worker,
  cross-cell process reuse, teacher backend, or extra context parameters.
- `replay_rulegame(out, lineage, cell)` and
  `replay_conditional(out, lineage, cell, candidate)`: CPU raw replay only.
  Direct replay checks local manifest consistency; joint reduction additionally
  checks the manifest hashes returned to Main at capture completion.
- `reduce_joint(captures, lineage, candidate, worker_exits)`: CPU joint reduction
  after all six raw replays and successful distinct process joins. Returns
  actual identities, explicit legacy schedule slots, frozen process metrics,
  full AUTH-map conditional/anchor metrics (operations, strata, twins, rows),
  raw finish/stop/token-limit flags, usage, named contrasts and bounded claims.

Backend interface is only `identity()` and `generate(request)`. Preserve the
existing NativeBackend response fields: text, rendered_prompt, prompt_token_ids,
output_token_ids, finish_reason and stop_reason. No generation wrappers may
append history or mutate the immutable loaded adapter. Prompt/token correctness
against the real tokenizer remains Main's native audit, not this CPU adapter.

Each capture function returns exactly:
`{cell, panel, path, pid, worker_id, manifest_sha256}`. `capture_cell` returns
`{rulegame: <receipt>, conditional: <receipt>}`. Preserve those returned hashes;
do not recalculate acceptance pins from subsequently modified captures.

`captures` passed to reduce_joint maps each actual cell to
`{rulegame: <path>, conditional: <path>}`. `worker_exits` maps each actual cell to:

```text
{
  worker_id: same Main-assigned worker ID recorded in both captures,
  pid: actual joined worker PID recorded in both captures,
  returncode: actual successful supervisor exit code (must be integer zero),
  backend_closed: actual successful close attestation (must be true),
  capture_manifest_sha256: {
    rulegame: original rulegame capture-returned manifest_sha256,
    conditional: original conditional capture-returned manifest_sha256
  }
}
```

These are **Main's attestations**, not self-issued authorization. Reducer rejects
missing panels, missing/extra raw pairs, altered prompt/seed/identity/response
receipts, early or unsuccessful exit, mismatched process joins and changed
Main-bound manifests. Partial failed captures remain on disk without a closed
manifest; no partial scoring, dropped rows, retries, padding or synthetic zeros
for missing artifacts. Invalid *generated text* is preserved/scored normally.
RuleGame invalid/DONE can end a task immediately under the unchanged parser;
the full run therefore need not consume 480 calls.

Main must keep completed captures and source/lineage/native artifacts immutable
through replay/reduction. This is deliberately not an OS sandbox, native token
authenticator, lease guard, collector, launch wrapper or adversarial custody
framework. Single-cell replay cannot certify a complete three-cell comparison.

## CPU validation and source preservation

Completed 2026-09-13 00:44 UTC / September 12, 2026 17:44 PDT.
Command (no native/model/tokenizer/network calls):

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_born_process_readout_20260912.py -v
```

**11 tests passed**, 13.615 seconds on the final implementation. Synthetic-only
fixture subprocesses exercise the public capture interface; no live result was
read. Assertions ensure torch/transformers/vllm are not imported by fixtures.
The initial invocation used `python`, which is absent; `python3` passed.

Coverage: exact normalized lineage/source/base/birth/formation joins; AUTH-only
birth, warm starts, no stacked/off/aliased-path adapters; equal byte nulls kept;
fixed128 request equivalence and candidate mismatch; raw tokens, stop metadata,
actual cell IDs, repeated probes, invalid records and absent quizzes; exact
24-quiz-label and 12-opportunity denominators; all-six-before-metrics spies;
missing panel, wrong manifest pin and bad exit without any score call; rehashed
tamper rejection; failed final conditional call preserving raw partial evidence;
480-call full fixtures and 396-call DONE/invalid fixtures; no parent/restate
calls, record-feedback context, panel retry or cross-cell process reuse.

An existing upstream ResourceWarning from nursery_dialogue.py's static
parent_prompt.txt import was observed. No source repair was made. Static
diagnostic imports do not send that teacher prompt to these child calls.

Non-material adapter/CPU repair scope only. No repository, Git, native, GPU,
lease, SSH/network or other writer's file changes. No launch or autochain.
Main must still supply completed release-bound lineage and perform its native
supervision; this handoff does not invent COMPLETE or any scientific outcome.

Exact SHA256 of final implementation and test bytes:

```text
336c6faaf834139b086e028c949cd82be102498d445af2da67238ae24c9a62f2  /tmp/astra_born_process_readout_20260912.py
92f97746aa461a21db728d39ef7e48c668ef752b00440fb59e714c4fa8fd6d0b  /tmp/test_astra_born_process_readout_20260912.py
```

Inspected dependencies were rehashed unchanged after testing:

```text
46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46  /tmp/astra_rulegame_process_readout_20260912.py
072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa  /tmp/astra_birth_conditional_run_20260913.py
e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526  organism_v6/rulegame_parenting_diagnostic.py
43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b  organism_v6/birth_conditional_corpus.py
```

The hash of this final handoff is returned to Main separately (a file cannot
include its own final-byte SHA256 without self-reference).

**EDITSTOP.** These three owned files are ready for Main's integration. No
further edits, launch, outcome inspection or claim promotion by this worker.
