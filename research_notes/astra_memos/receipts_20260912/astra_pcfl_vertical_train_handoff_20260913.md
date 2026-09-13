# PCFL writer — EDITSTOP interface, 2026-09-13

Frozen narrow implementation; CPU preparation only, NOT native readiness or launch approval.
Main's integration correction is incorporated: the current unresolved preparer
report blocks `train_fit` before encoding, output claim or base-factory call.
Pure build/validation/encoding and optional tiny CPU objective tests remain usable.
Own only `organism_v6/pcfl_vertical_train.py`, its matching test, and this file.

## Explicit integration seam

`build_fit(contract, corpus_id, queries, rows, generations, controls,
binding)` returns a detached sealed fit manifest; `validate_fit(fit)` rechecks
it. `encode_fit(fit, tokenizer)` uses shared trainer `encode_item` explicitly,
never shared training globals/loop. Optional `train_fit` consumes an already
qualified fresh-base factory; it does not download or launch anything.

- Consume preparer's entire execution contract unchanged, select its corpus
  and concrete `[slot_id, view_id]` schedule; no selection/scheduling algorithm.
- Consume core's exact rows and `materialize_queries` output unchanged.
  Check preparer's formation bank before encoding. W0–W7 come from core's
  sealed render registry. W8 is never a training item.
- Authentic sources require actual UTF-8 generation payloads and exact bound
  byte offsets/hash, not only the core's CPU admission Boolean. That Boolean
  currently does NOT establish native custody. Main still supplies custody.
- Registered CONTROL rows retain original child ancestors and transformation
  receipts. CEILING_FIXTURE/rendered oracle targets cannot become authentic.
- Twenty slots/eight views; five concrete epochs/forty batches/four items;
  exactly 200 updates, no shuffle, packing, synthetic PAD targets, warm start,
  skipped updates, checkpoint choice, or hidden repair.

## Binding question requiring Main before execution

The inspected v2.2/closure documents say response-only including EOS but do
not distinguish pooled supervised-token mean from a mean of four sequence
means. Proposed explicit binding is `pooled_response_token_mean`: summed
shifted response+EOS cross-entropy over the four examples divided by their
total supervised tokens (standard batch masked-CE semantics). This is NOT
target-token equalization. Main must bind this choice; absent/other objectives
will fail closed, not silently select a weighting rule.

Init/dropout seeds, LR selection receipt, concrete source/helper pins and
fresh-base identity are explicit fit bindings, not inherited mutable globals.

## Frozen owned bytes and tests

| Owned file | SHA-256 |
|---|---|
| `organism_v6/pcfl_vertical_train.py` | `cf3cbe57886e9d283ac40760d129e0f3065def192064c846eefeaedb496fe68c` |
| `tests/test_pcfl_vertical_train.py` | `c4ba2b43d154057c2930b1977b2571468f70c91077f72e64a94e8a60f024377b` |

Commands from `/data/home/rohing/dream-state`:

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 -m unittest discover -s tests -p test_pcfl_vertical_train.py -v
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 -m unittest discover -s tests -p 'test_pcfl_vertical_*.py' -v
```

Final focused run: **35 discovered, 34 passed, 1 skipped, 2.158 s**.
Joint core/preparer/writer run: **100 discovered, 99 passed, 1 skipped,
16.093 s** (final joint command uses `-q` instead of `-v`). The skip is the optional real Torch numerical objective test;
Torch is absent on this VM. Python AST and trailing-whitespace checks pass.
An initial toy-fixture namespace error was corrected before these final runs;
no native attempt or outcome occurred.

Actual seams exercised: core row parser/byte validation, core READ address/
block verification, real preparer `validate_formation_binding`, shared v3
encoder, core EVENT_TWIN recomputation, exact replay bytes and schedule order.
The writer fixture intentionally uses an artificial twenty-singleton bank;
its full execution-contract validator is mocked for narrow seam tests. A
separate rejection test proves this fixture is NOT a full qualified contract.
The joint suite separately exercises the real preparer/core suites. It does
not establish one integrated scientific world-to-native-training fixture.

The 200-step lifecycle test mocks a future positive release report plus
Torch/PEFT/model/loss and verifies exactly
200 backwards, AdamW steps and clipping calls, final-only save, RNG seed
arguments, preserved failed attempts, no nonfinite-loss skip, no warm start,
and no existing-root overwrite. It is NOT numerical training evidence.

Crucially, the new native-gate integration test uses the **real, unpatched
preparer** and its synthetic structural contract fixture. The preparer's real
`execution_contract_valid=False` and missing-interface list reject before
encoding/factory/output creation. A separate table tests missing fields, false
fields, integer/string truthiness and residual missing interfaces. There is
no public bypass or override flag. Lifecycle release mocks are tests only,
not evidence of a released scientific contract.

## Complete caller seam

Fit schema: `pcfl.writer.v2.2.unpadded.v1`. Canonicalization uses preparer's
strict JSON wire encoder. `fit.sha256` hashes the complete payload excluding
the SHA field itself. No aliases to caller inputs survive `build_fit`.

The exact `binding` keys are:

```text
contract_sha256, authority_sha256, custody_sha256,
objective, layout, learning_rate, phase, selection_receipt_sha256,
init_seed, dropout_seed, base_state_sha256, writer_sha256,
shared_trainer_sha256
```

- `objective=pooled_response_token_mean` and
  `layout=four_unpadded_forwards_one_backward` require an explicit prospective
  authority binding. There is no default/fallback to a different objective.
- `learning_rate` must be the JSON float `3e-5` or `3e-4`, never bool/string/
  NaN/1e-4. `phase=CAL_LOW|CAL_HIGH|DEV`; CAL phases fix their LR and match
  `environment.cal_seeds['cal/init']` and `['cal/dropout']`. DEV uses explicitly
  supplied nonnegative integer seeds below 2**63. Main must prospectively
  bind those DEV seeds and match them across paired arms.
- `authority_sha256`, `selection_receipt_sha256`, `custody_sha256` bind Main's
  external decisions/evidence; this module validates their form, NOT their
  scientific authorization/content. No HIGH or DEV eligibility is inferred.
- `base_state_sha256` is the exact hash of fresh official C0 `state_dict()`
  under this module's `_state_hash` algorithm. Main's qualified factory must
  provide matching weights; adapted bases fail before LoRA attachment.
- The complete preparer contract is unchanged inside the fit. Core/preparer
  hashes come from `bindings.implementation_pins`; no competing schema or
  schedule-generation algorithm is supplied here.

`generations` is a list of closed records:
`{raw, sha256, origin:'CHILD_NATIVE', capture_sha256}`. SHA is over original
raw UTF-8. Each CHILD_SUBMISSION row must identify that generation and its
exact UTF-8 `byte_start:byte_end` in core provenance. All supplied generations
must be used. A `native_generation_verified=True` Boolean alone is insufficient.
These are byte joins, not proof that a payload really came from a native child;
Main must check captures against original request/response/adapter custody.

`controls` is a list of `{name, ancestors}`. Only EVENT_TWIN or LINK_PERMUTE
in its matching S1 arm is allowed. Ancestors must themselves be bound original
child spans. The writer invokes the **existing core transformation** and
compares the entire resulting row, including provenance, without rewriting
targets. Core LINK_PERMUTE's prebound four-link chronology restriction remains;
there is no fallback remap. CEILING_FIXTURE and arbitrary CONTROL rows fail.

`encode_fit(fit, tokenizer)` renders the sealed core memory system prompt
plus W0–W7 user wrapper using `apply_chat_template(..., tokenize=False,
add_generation_prompt=True)`. It passes explicit prompt-masked and exact
target-active spans to shared `encode_item(chat_template=False, add_eos=True,
max_len=512)`, then independently checks IDs and labels. Any context OR target
truncation, empty target, embedded EOS, wrong chat-template pin or mask drift
fails. EOS is supervised. Encoded items retain slot/view, prompt/target/source
hashes, complete IDs/masks and exact supplied epoch order.

`verify_sources(fit)` hashes actual imported writer/shared/core/preparer files
and controlling local analysis sources. `verify_tokenizer_files(fit, tok)`
requires offline evidence, local absolute `tok.name_or_path`, relative file
paths (no parent traversal) and exact file hashes; it also replays recorded
measurement text through the provided tokenizer. Full tokenizer coverage and
actual load configuration still belong to Main's integration checks.

`train_fit(fit, tokenizer, base_factory, out)` is optional and never called by
import. It first consumes the actual preparer validation result and requires
`execution_contract_valid is True`, `static_contract_complete is True`,
`ready_for_model_calls is True`, and `missing_interfaces == []`. The current
preparer intentionally cannot return this release; **native fitting is blocked**.
The `_validate` path for build/encode intentionally checks structural validity
without turning that into release. No synthetic contract can enter fitting.

After a future integrated closure only, `base_factory()` returns
`(fresh_base_model, environment_dict)`, with
environment exactly equal to the sealed contract's environment. The caller
owns safe local-only loading, routing, timeout/lease and process teardown.
No loader/launcher/collector, checkpoint selection or retry API exists here.

## Objective, work and receipts

Each four-item batch performs four **unpadded** forwards, adds their summed
shifted response+EOS cross-entropies, divides once by total supervised tokens,
and performs one backward and one optimizer step. It is not a mean of sequence
means; no target tokens are equalized and no item gets a scientific weight.
There are 200 updates, 800 example presentations/forward invocations, 160
distinct slot/view items per epoch, five epochs. Replayed slots remain replay,
not newly distinct source evidence. No new inference endpoint calls occur.

Since no physical padding occurs, no post-EOS alternate-pad invariance claim
is made or needed for this layout. Changing to a padded implementation would
require the specified padding certificate and a new layout binding. Four
unpadded graphs may differ in dropout/RNG consumption and hardware cost from
a padded batch; no padded-layout performance/parity claim is made.

Fresh rank8/alpha16/dropout.05 LoRA uses shared `lora_config`, all seven
projection modules, bf16 base, no packing/shuffle/checkpoint recomputation.
AdamW explicitly uses betas(.9,.999), eps1e-8, weight_decay.01 and selected LR;
global norm clipping is exactly1.0. Base weights are frozen, optimizer fresh.
Nonfinite loss/gradients/updated parameters abort; never skip a counted update.

Fresh output directory only; existing files/dirs/symlinks reject. Outputs
only after the release gate (currently test mocks only): `fit.json`,
`encoding.json`, `execution_contract_report.json`, `initial.json`, `updates.jsonl`, final `adapter/`,
then `completed.json`. Trace has row/view pairs, source hashes, supervised
token count, loss, pre/post clip norm, CPU/all-visible-CUDA RNG hashes per
update. Initial/final trainable tensor and optimizer state hashes are retained.
Completion includes hashes of saved files. A caught failure after claiming
the directory writes `failed.json`; hard process death may leave only partial
files, never a completion. The directory remains non-reopenable by this API.

## Observed dependency pins and remaining gates

These are observed joint-test bytes, not ownership or a promise that other
agents will not publish another version:

- shared trainer: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- core: `03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f`
- preparer: `e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4`

Before any fit: Main must bind objective/layout and complete integrated
contract, formation/native-custody, calibration-selection, clean-C0 factory,
real tokenizer, numerical Torch/PEFT and finite device-budget checks. Current
preparer/core missing-interface reports remain authoritative and mechanically
block the native entry, not merely advise its caller. `validate_fit`
always reports `native_custody_verified=False`, `release_authorized=False`.
No full PCFL implementation, writer qualification, C11, model readiness,
native PASS, scientific result or Main launch authorization is asserted.

Only the two owned source/test files and this handoff were edited, using
apply_patch. Root/local instructions and local Git status were inspected.
No pull was attempted because the same task explicitly prohibited network;
no commit/push, model/tokenizer download, native/GPU call or live-run mutation.
Other agents' changing files and pre-existing rules edits were preserved.

**EDITSTOP — the owned code/test hashes above are frozen.**
