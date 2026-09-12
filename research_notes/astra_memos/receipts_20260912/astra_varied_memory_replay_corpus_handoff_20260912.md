# Varied-memory replay material — EDIT-STOP

2026-09-12. Rohin message20 varied phrasings: **new authored comparison, not reopening failed SEQ107**. Owned/changed only:

- `organism_v6/varied_memory_replay_corpus.py`
- `tests/test_varied_memory_replay_corpus.py`
- `/tmp/astra_varied_memory_replay_corpus_handoff_20260912.md`

No GPU, network, Git, training, readout, optimizer, model loading, or unrelated source changes. Native tokenizer preparation is for Main; only character-token CPU fixtures ran here. Source inspection included the original teaching material, not model outputs. This is author-side material validation, not an independent scientific result.

## Fixed material

Both arms have **128 rows = 32 original source rows × four adjacent copies**. Selection is all16 original memory sources plus the same first16 arithmetic sources as SEQ107, retained in the shuffled original80 teaching-row order. Arithmetic IDs in that first16 order:

`011,039,055,029,048,000,052,017,036,046,063,019,057,030,012,015`

Full IDs use `train-addition-` plus the three-digit suffix. Memories are `train-memory-000` through `train-memory-015`.

SINGLE_VIEW repeats the exact original context four times. FOUR_VIEW uses these fixed memory-only templates, in order:

1. `Which color does the log assign to {device}?` — exact original.
2. `What is the color assigned to {device} in the log?`
3. `According to the log, which color is assigned to {device}?`
4. `Name the color that the log assigns to {device}.`

No output-dependent variant selection or tuning. Arithmetic context **and full original PREDICT/ACT target** remain byte-identical in all four copies and both arms. Every memory target remains the original color bytes, without punctuation or added instruction. Source event IDs are preserved; the candidate exports only32 selected training source events, not heldout events or raw evaluation/confirmation cases. Device joins, logged color text, integer sums, exact target bytes, and normalized heldout-context exclusion are checked. Memory contexts may contain no color label or `unknown`; source facts/answers are metadata or target-only, never concatenated into prefixes.

## Actual V3 layout and schedule

Native rows preserve original `group`, `order`, `view`, two span categories/masks, and `meta.source_event_ids`. Added `meta.replay_copy` records source/copy identity identically across arms. Only memory prefix text changes between paired rows. No packing; one example per sequence, original source group repeated four times with equal original order, stable item-index tiebreak.

**Important:** actual V3 `pack_by_group(..., pack=False)` sorts groups, then `epoch_order` shuffles group blocks. Thus **each batch of four is four copies of one original source**, not four different sources. This is the same in both arms. The audit replays the actual V3 helpers and collation for caller-selected seed(s)0/1/2 and saves all320 optimizer-update batches per seed. It verifies all128 row indices appear exactly once per epoch, copy order0/1/2/3, paired identical groups/indices, and40 presentations for each of all32 original sources. Per-original-view memory dose is10 presentations in FOUR_VIEW, versus40 presentations of the sole phrasing in SINGLE_VIEW.

Recipe declaration only: frozen original Qwen2.5-7B-Instruct base; rank8/alpha16/dropout.05/LR3e-4; ten epochs, batch4, accum1, AdamW, caller seed0/1/2, all original projection targets/layers, BF16, no packing, no double chat templating, one supervised EOS, max_len512. `overflow="truncate"` is only the V3 selector; **any actual drop/split/overflow rejects export**. 128/4 ×10 = **320 intended updates per arm**. Counts assume every batch trains finitely; no actual steps are asserted.

Each future arm must warmstart **independently from the ORIGINAL teaching parent**, with a fresh optimizer, not a SEQ107 descendant or the other replay arm. This builder cannot verify a parent adapter or launch that recipe; Main must bind/check parent and base inventories later.

## API and commands

From a source root containing the three pinned Python dependencies:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_varied_memory_replay_corpus.py -v

# CPU raw candidate only; OUT and its parent must be chosen by Main.
python3 -B -m organism_v6.varied_memory_replay_corpus emit --out "$OUT"
python3 -B -m organism_v6.varied_memory_replay_corpus verify --root "$OUT"
```

- `build_candidate()` → deterministic raw candidate, paired arms,32 source events, selected IDs/templates, recipe/boundaries. No tokenizer.
- `validate_candidate(candidate)` → strict fixed-data/recipe equality plus explicit source-key, membership, target and heldout-exclusion checks. Unsupported modifications fail.
- `export_native(candidate, original_teach, tokenizer, seeds=(0,1,2))` → in-memory `{corpora, audit}`. `original_teach` is the parsed actual80-row native `teach.json`. The entire supplied80-row object must match original source membership/order/targets/metadata and callback-rendered original prefixes, including unselected training rows. Direct calls are useful for fixtures; they do not authenticate original file bytes.
- `prepare(out, teach, tokenizer, seeds=(0,1,2))` → fresh disk export and manifest. `teach` is a path to the exact original native teaching bytes pinned below. No model/path guessing or tokenizer loading happens inside this module. Only unique nonempty subsets of seeds0/1/2 are supported; corpora are identical regardless of seed selection.
- `verify(root)` → current source/artifact hashes, fixed candidate, manifest recipe/status/audit bindings and original source hash. It does **not** rerun tokenization or attest parent/base identity. Artifacts must remain with the same source bytes; preserve the original native teach file.

**Main-only native CPU callback example** (not executed here). Set `TEACH_ROOT` to the actual original teaching/replication root with `teach.json` and `plan.json`; set `OUT` to a separate fresh directory. Use Main's native Python and immutable source CWD. No weights/model path is hardcoded:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 python -B - <<'PY'
import json
import os
from pathlib import Path
from organism_v6 import rulegame_parenting_diagnostic as base
from organism_v6 import varied_memory_replay_corpus as material

root = Path(os.environ['TEACH_ROOT'])
plan = base.read(root / 'plan.json')
base.require(base.model_hashes(plan['model']) == plan['model_files'], 'original base bytes changed')
tokenizer = base.native_tokenizer(plan['model'])
manifest = material.prepare(Path(os.environ['OUT']), root / 'teach.json', tokenizer, seeds=(0, 1, 2))
base.require(base.model_hashes(plan['model']) == plan['model_files'], 'base changed during audit')
print(json.dumps(manifest, sort_keys=True, indent=2))
PY
```

The surrounding base checks are Main's CPU provenance checks, not a claim authenticated by this callback API. If a surrounding check fails after writing, preserve the output as failed/unapproved evidence; no overwrite or retry into that root.

## Artifacts / token evidence

Raw emit: `candidate.json`, `manifest.json` with `RAW_CANDIDATE_TOKEN_AUDIT_PENDING`.

Callback prepare: `candidate.json`, `SINGLE_VIEW.json`, `FOUR_VIEW.json`, `token_audit.json`, `manifest.json`, with `CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT`. All paths are fresh-only; writes use exclusive creation. Errors before export create no output root. Interrupted writes are preserved, never repaired/replaced. Symlink output roots/ancestors are rejected.

Native audit records exact raw/rendered contexts, target text/UTF-8 hashes, prefix/response IDs, target+EOS IDs, full input IDs and labels, selected original baselines, per-arm per-epoch/ten-epoch input/context/target totals, and actual schedules. It checks exactly one supervised EOS, masked original context EOS tokens, causal label boundary, single-sequence collation, zero drops/splits, and batch4 padding masks. Same-view rows, all arithmetic, and memory view0 must exactly equal the original native baseline. Every target+EOS must match the original and the paired arm.

**Do not claim compute matching.** Prefix counts differ; native counts are measured, not length-normalized or forced equal. Scheduled padded-input slots are also reported separately. This run used character fixtures, so no genuine native token totals are claimed yet. Tokenizer class is recorded, but `native_identity_authenticated=False`: Main must authenticate the supplied native tokenizer/base via original plans. No dataset, parent, or base identity is inferred from the fixture class or success status.

## Tests / hashes

**27/27 owned stdlib CPU tests PASS, zero skips**, including actual V3 group order for seeds0/1/2, source-major128 layout,40 presentations/source, all source joins, unchanged original target bytes/EOS, full80 native-prefix parity, arithmetic parity, target-vs-prefix cost distinction, mask-shift regression, EOS failure, overlength rejection, seed restrictions, mutation/source-race refusal, fresh roots, manifest integrity, and no heldout prompts sent to the tokenizer. CLI `--help` also passed. The fixture reconstructs the pinned original native source text bytes exactly, but its token IDs are intentionally synthetic, not native Qwen evidence.

| Object | SHA256 |
|---|---|
| `organism_v6/varied_memory_replay_corpus.py` | `fbdcb87ec2d2475b1b988e7b19ee53cb8318f0bafe2e805807871059d2cbfaa2` |
| `tests/test_varied_memory_replay_corpus.py` | `1a6e995b8c88ab81d88ede6d84795336c074f164d2fa9c1ed5ae8a1c68926a0b` |
| Pure `candidate.json` bytes from `encoded(build_candidate())` | `6c74c1f5c4428c4758bba427dd0e938034155496db5bc2d270076981332de094` |
| Actual original native `teach.json` | `2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c` |
| Canonical original raw80 teaching rows | `d44585d4081819248f18774f12d8e1260e61af6fa6aaa260afbe3833e10838ab` |
| `fundamental_teaching_corpus.py` | `44b1a61e10695e1e65ca3ee2e6c151eba45df1512ea3fc108402e96226ddaa13` |
| `train_adapter_v3.py` | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |

Claim: `AUTHORED_VARIED_PHRASING_REPLAY_NOT_CHILD_EXPERIENCE_NOT_BRAIN_PROOF`. Origin: `UNRESOLVED_LOCAL_HASHES_ONLY`. This is literal varied phrasing/perception material, not a proof about brains, conditional cognition, parenting, generality, or successful memory binding. No new evaluation/scoring protocol, no actual fits, and no launch code.

**EDIT-STOP. Main owns native preparation and any later orchestration.**
