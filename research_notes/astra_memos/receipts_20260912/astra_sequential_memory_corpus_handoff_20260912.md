# Sequential memory corpus — public interface contract

2026-09-12. Published before implementation; Main confirms relay to Darwin.
Darwin agreement is not asserted. Main's subsequent explicit optimizer-seed0
clarification supersedes advisory seed1 in both code and this contract.
Only material generation and CPU audits;
no parent implementation, runner, fit, native execution, or historical edits.

## Frozen interface

Module: `organism_v6.sequential_memory_corpus`.
Protocol: `AUTHORED_SEQUENTIAL_MEMORY_FIXED_BUDGET_V1`.
Arms: `R`, `NEW_ONLY`. Cycles: string keys `1`, `2`.
States: `S0`, `R1`, `NEW_ONLY1`, `R2`, `NEW_ONLY2`.

- `build_candidate()` returns `manifest`, `banks`, `source_records`,
  `cycles[cycle][arm]` (128 raw rows each), `readout_cases` (128 cases).
- `validate_candidate(candidate)` rejects any change to the fixed candidate.
- `export_native(candidate, original_teach, tokenizer)` accepts an injected CPU
  tokenizer and the complete original80 native teaching object. Returns
  `corpora[cycle][arm] = {corpus: [...]}` and `audit`, with per-row token/mask
  receipts and 320 actual V3 scheduled/collated batches per fit. This does not
  authenticate tokenizer/model identity or bind a parent checkpoint.
- `readout_cases(candidate=None)` returns the fixed answer-bearing 128 cases.
- `readout_requests(cases=None)` returns fixed answer-free requests, identical
  across all five states; callers own capture and scoring. IDs are stable.
- `emit_candidate(out)` and `prepare(out, teach, tokenizer)` exclusively create
  a fresh output directory. `teach` is the exact original80 native file,
  byte-hash checked. No overwrite, fallback, substitution, or retry.
- CPU candidate CLI: `python3 -m organism_v6.sequential_memory_corpus candidate
  --out /absolute/fresh/directory`. Native preparation is callback API only.

Each four-row group has slots: current-new memory, arithmetic, replacement
memory, arithmetic. Group IDs/order align across arms. Replacement memory
has the same color target as the R old-memory row and differs in key from the
first memory slot. Inputs/padded compute are audited, not presumed matched.

S0 MUST be seed0 FOUR_VIEW's saved 400-update checkpoint (Main override of
Darwin's seed1). Fresh optimizer seed0 each fit; one continued adapter,
immediate preceding weights, cumulative steps 400 → 720 → 1040. Parent
provenance verification is deferred to the runner owner, never implied here.

Fixed budget, NOT new-dose matched: R current bank20 presentations/fact/fit,
NEW_ONLY40. R cycle1 M0=20; R cycle2 M0=10 and B1=10. Four fits ×320 updates.
Readout: 5×128=640 calls; max64 tokens, temperature0, seed20260912. Original
confirmation and unknown panels remain untouched. Authored facts, not child
experience; finite writes would not establish behavioral utility or lineage.

## Implementation status

**EDITSTOP. Implementation and CPU validation complete.** Main's last explicit
clarification is applied: S0 seed0 FOUR_VIEW, optimizer seed0 in all four fits.
No future replication/seed parameter is introduced. No native/model/fit/GPU,
SSH, network or Git execution; no trainer, historical inventory, parent, runner,
or unrelated file edits. Only the three assigned paths are deliverables.

## Invocation and outputs

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.sequential_memory_corpus candidate --out /absolute/fresh/directory
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_sequential_memory_corpus.py' -v
```

Native tokenizer construction is deliberately NOT part of the CLI. Main's
future CPU-native preparation wrapper calls:

```python
from organism_v6 import sequential_memory_corpus as material
manifest = material.prepare(fresh_output_directory, exact_original80_teach_path, cpu_tokenizer)
```

`prepare` requires original80 file SHA256
`2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c`;
the lower-level `export_native` instead checks the complete original80 object
against caller-tokenizer rendering, and records its canonical hash. This latter
callback also supports mocks and does not authenticate a native tokenizer.

Prepared filenames: `candidate.json`, `token_audit.json`, `readout_cases.json`,
`readout_requests.json`, `cycle1_R.json`, `cycle1_NEW_ONLY.json`, `cycle2_R.json`,
`cycle2_NEW_ONLY.json`, and `manifest.json`. Every payload hash is in the
manifest. Existing output directories/symlink paths are rejected. A write-time
failure can leave a partial directory; never reuse or retry it. Validation and
wrong-original-file failures precede directory creation.

Audit layout:
- `fits[cycle][arm].rows`: actual rendered-prefix/response/target+EOS IDs, full
  inputs, labels, raw context/target UTF8 hashes, source joins and original-row
  index. `original_selected_native_rows` separately records unchanged original
  native rows, and originals are checked for complete token/mask equality.
- `fits[cycle][arm].schedule.updates`: 320 actual unmodified V3 pack/order/collate
  batches, epoch/batch/group/item indices, source IDs, row target counts, target
  mass by kind, full inputs/context/target counts, padded width/input slots,
  padding slots and all masked slots. Seed0 order is independently unit-tested.
- `schedule.source_presentations`: actual scheduled source exposures. Per-row,
  per-epoch, ten-epoch and schedule totals are **nested, never additive**.
- `paired[cycle]`: targets matched, `new_dose_matched=false`, paired prefix-length
  equality and padded-slot equality. Unequal prefixes are accepted and reported,
  without any ID replacement, padding text, truncation, or dose adjustment.
- `total_target_exposure` adds exactly the four fits' ten-epoch target counts.
  `observed_optimizer_updates=0`: these are planned exposure schedules, not fits.

Training allocation only uses original16 memory/16 fixed arithmetic sources and
the two separately versioned authored banks. Readout arithmetic cases are the
unchanged `eval-addition-000..031`; their original source joins remain in the
hash-bound historical teaching module, not in the training-source inventory.
No closed-log inventory is extended or reinterpreted; no teacher or readout
output enters generation. Exact raw source-row and target bytes are hashed.

## Predetermined maps

Each bank independently sorts indices0..15 by the SHA256 of
`<domain>:<two-digit-index>` and assigns existing `COLORS[position % 4]`.
Domains and complete permutations are recorded in the new bank inventories.
The mappings do not depend on M0 colors, token lengths, checkpoints, scores,
child experience, or model outputs. All keys have the `device-` prefix:

| Keys in increasing order | Assigned colors in the same order |
|---|---|
| 100..115 | blue, green, yellow, yellow, green, blue, green, green, yellow, red, blue, blue, red, yellow, red, red |
| 200..215 | red, blue, yellow, blue, green, red, blue, yellow, blue, red, green, green, yellow, red, green, yellow |

Domains: `sequential-authored-bank-one-20260912` and
`sequential-authored-bank-two-20260912`. Both banks are independently balanced
four/color, mutually disjoint, and distinct from the old mapping. All original
training questions and arithmetic targets are unchanged. Group ordering is
color-major (eight groups/color), first new fact cycling through four same-color
facts; NEW_ONLY replacement rotates by one same-color fact, avoiding duplicates.
R replacement cycle1 uses each M0 color fact twice; cycle2 uses each M0 and B1
color fact once. Arithmetic pair index is `(2*group_index) % 16` and its successor
in the historical fixed arithmetic selection order.

## Validation and unresolved native acceptance

**69 CPU tests PASS**: sequential14, unchanged interleaved28, unchanged varied27.
The sequential suite passed again after the final seed0-order assertion. Tests
use character-based mock prefix tokens and one-token colors, with real V3 pure
encoding/scheduling/collation; no production tokenizer or fit ran. Mock
`prepare` success explicitly patches the original file hash only inside the
test. Production hash checking is unchanged and wrong hashes fail closed.

Covered: exact independent maps/source bytes, doses, actual paired same-color
replacements/distinct keys, 32 groups/320 updates, seed0 schedule, full masked
prefix and exactly one target EOS, perbatch denominators/padding, common128
readouts, no answer-bearing request fields, original inventory preservation,
candidate/source/target/mask/slot/seed mutation, partial pairs, changed native
originals, multi-token colors, target EOS injection, overlength, scheduler drops,
bad collated masks, source changes during audit, unequal prefix reporting,
wrong original file hash and exclusive/symlink-safe outputs.

Main must still perform actual CPU-native token preparation and identity/source
binding. Historical 1,000 targets/epoch, 10,000/fit, 40,000 overall are conditional
expectations, **not measurements from this mock suite**. Memory one-token-color
plus EOS is enforced; arithmetic/input/padded counts are reported as measured,
not silently forced to historical values. No clean-lineage or utility claim.

The future runner must independently bind S0 seed0 FOUR_VIEW's exact completed
400-update saved weights and base; R2/NEW_ONLY2 must use their own immediately
preceding saved child. One adapter, fresh optimizer seed0, rank8/alpha16/dropout
.05/LR3e-4, 10 epochs/batch4/accum1, 320 finite completed updates per fit,
400→720→1040 cumulative counts, initialized-weight equality and tensor/custody
checks remain unresolved here. Candidate metadata is not parent acceptance.
Five full saved-state panels are fixed; B2 is explicitly untrained in S0/R1/
NEW_ONLY1. Missing results remain technical partials, not zeros. Reservation,
lease, worker supervision and collection are outside this material module.

## Final SHA256

- `organism_v6/sequential_memory_corpus.py`:
  `5c04e98f6a87b01a431cd2e464e158ef2b5b6511f3618f39ed922db33cd90fd3`
- `tests/test_sequential_memory_corpus.py`:
  `392716f3ddc951fa39ade3f3118e6acd7b273b2bb90cbf0e0a3444eebde38bd9`
- Canonical `build_candidate()` (`encoded`, sorted indent2 UTF8 plus newline):
  `6225acb06ca9f2507aedd986af7690967ee1c83cf0bd37bfe46bc69d3dd2f6b6`
- Canonical `readout_cases()`:
  `7d0e15a975c14b8d984882a1e80c739ce6089cd3a36ad635c94a24717868e0a4`
- Canonical `readout_requests()`:
  `b0e7e177016c451348ff8441076c0bb0c2bef5e4e3e51d0367aadbe7226e0381`

Unmodified runtime helper bytes:
- `fundamental_teaching_corpus.py`:
  `44b1a61e10695e1e65ca3ee2e6c151eba45df1512ea3fc108402e96226ddaa13`
- `train_adapter_v3.py`:
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- `varied_memory_replay_corpus.py`:
  `fbdcb87ec2d2475b1b988e7b19ee53cb8318f0bafe2e805807871059d2cbfaa2`

Handoff hash is reported externally to avoid a self-referential checksum.
