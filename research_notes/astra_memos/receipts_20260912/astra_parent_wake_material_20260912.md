# Source-linked P0 raw wake exporter — frozen handoff

2026-09-12. Implemented only new `organism_v6/parent_wake_material.py` and `tests/test_parent_wake_material.py`. No existing modules/criteria/notes modified; no Git, SSH, remote jobs, GPU/model calls, trainer calls or real P0 corpus export. Comparison selection still belongs to main after seed results.

## Interface / invocation

```python
export_pair(lesson_root, sham_root, output_dir, *, count,
            selection, families=None, max_len=4096, tokenizer=None)
```

`count` is an explicitly chosen integer 1..64; `selection` is explicitly `measured` or `accepted`. Optional `families` restricts existing training families. No scientific comparison has been chosen by default. `tokenizer` injection is for CPU tests and is labeled as injected in output; normal CLI loads only the actual local tokenizer, not weights.

CPU-only invocation template, NOT executed against P0 here:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /path/to/venv/bin/python -B -m organism_v6.parent_wake_material \
  --lesson-root /original/formation/lesson \
  --sham-root /original/formation/sham \
  --out /fresh/external/wake_material \
  --count "$COUNT" --selection "$SELECTION" --max-len 4096
```

Optional repeated `--family mini_sudoku` etc. No train/launch mode, optimizer selection or generated coaching. `READY` means the explicitly requested paired export is available, not writer/parenting/scientific acceptance. Shortage writes `PAIRED_SKIP` with **both corpora empty**, explicit reasons/available counts; no lowered count or partial-arm fit. Caller must inspect status rather than treating CLI exit0 as available training material.

## What is bound and what is excluded

- Reuses existing `parent_note_replay_diagnostic._inventory`, `parent_material_write` path/JSON/tokenizer utilities, fixed formation protocol, `_lesson_rows`/`_teacher_row`, `facts_from_act`, raw ACT parser, source identity helper and V3 encoding/collate.
- Source requires COMPLETE original roots, intact artifact inventory, original source paths/bytes, matching policy/batch/families bytes, recorded local pins, exact original schedule and teacher receipt. The historical producer module may differ from current formation code as in the existing replay source validator; its recorded file must still exist and hash correctly.
- Matches each raw wake request/output uniquely by prompt/output hashes and request seed, checks model/adapter identity, temperature/cap and original episode/tick-derived seed. Full output bytes are retained. A thought row must match the producer's exact `raw.strip()[:2000]` projection; clipped ledger rows recover **actual stored generation**, not a completion or restatement.
- Measured ACTs retain execution/occurrence IDs, chronological ledger positions/hashes, same episode/tick/receipt, native feedback facts and execution ordinals. Parsed raw ACTs must match the entire ordered ledger action list, including repeated identical actions. Membership-only joins and orphan/duplicate executions fail. Original request/action counts are checked independently of NOTE eligibility.
- **No call to `judge_record`, `_judge_source`, `gate_sleep` or formation `summarize` during export.** Historical bad NOTE content remains bad under the unchanged original gate; it is simply not this exporter's target type. All requested raw generation files remain hash-checked, including unused historical note outputs.
- Checks actual teacher ledger receipts; normalized complete teacher sentences/lines from both historical arms are excluded from raw targets and remaining context using existing replay `_payloads` / `_echo`. Target echoes are rejected, never excised or rewritten.
- Removes only the known historical teacher-bearing `=== YOU ===` head: require it equal original birth prompt + actual fixed teacher, replace with original birth prompt alone. Preserve the entire original state/history suffix. If child history still echoes teacher text, reject that candidate rather than redact history. This removes explicit teacher content, not all downstream influence.
- The context comes from the original **pre-generation** request. Current chunk's ACT feedback remains audit-only in the source map and is never appended to its conditioning. Earlier public feedback already present stays visible. No answer-key field is fetched or fabricated, no native score is invented/rerun, and the exporter does not certify every statement in raw child prose as true.

## Selection and budgets

For each arm and episode, consider the first raw wake with at least one measured event (`measured`) or at least one measured score1 event (`accepted`), in physical source order. It is considered only once: if teacher exclusion/token budget rejects it, do not fall through to a later wake of that episode. Select the first requested number of **common eligible episodes in original schedule order**. This is not score ranking, does not rewrite targets, and is not a frozen comparison selection made on main's behalf.

One example is the entire raw child chunk, including any other failed/unexecuted lines. `accepted` means at least one actual accepted event in that chunk, NOT that every token/action is correct. Source-map audit makes this explicit. Same episode count and per-row input cap in both arms; total input envelope `count * max_len` each. Actual input/target-token totals are reported; exact token-dose equivalence and historical teacher-dose equivalence are NOT asserted.

Source summaries include all distinct accepted episode IDs by family, `accepted_mini_sudoku_episodes`, clipping counts and rejection reasons. These are episode-identity counts, not a new board-identity proof. The concrete P0 limitation remains: its accepted mini-sudoku actions correspond to one episode/board per arm; a request for two or more distinct accepted mini-sudoku source episodes therefore cannot be padded by repeated actions. The synthetic regression exercises precisely this shortage.

## V3 span recipe / files

The tokenizer pre-renders the cleaned raw context using its actual single-user chat template, preserving terminal newlines. V3 receives:

```text
spans = [[rendered_context, false, "parent_removed_context"],
         [exact_raw_child_output, true, "raw_child_wake"]]
```

Use **plain V3 encoding, no `--chat-template`** if main later authorizes training. Encoder and actual collate must show all context labels -100, every target token plus EOS supervised, no split/truncation, and the requested length cap. No training command is emitted by this exporter.

Fresh output directory files:

- `lesson.json`, `sham.json`: top-level recipe/boundary/corpus with V3 spans.
- `lesson_source_map.json`, `sham_source_map.json`: exact source request/output/ledger references and hashes, raw output, ledger projection/clipping flag, measured events, original and cleaned prompts, rendered context, label/token evidence. **Audit-only: original prompts contain historical teacher bytes and must not be passed wholesale to a trainer.**
- `original_sources.json`: original paths, inventory, configuration/pins, teacher receipts; also audit-only.
- `selection.json`: explicit rule/count/families, available/selected episodes, budget and format.
- `source_hashes.json`: exporter/helper/bootstrap identities.
- `results.json`: READY/PAIRED_SKIP and paired availability/rejection/token summaries.
- `artifact_hashes.json`: exact file digest map, written last.

Files use the existing exclusive read-only writer; final directory is read-only. Existing destination, overlapping source/base/output roots, failed sources, changed inputs/local pins/source implementations, or inconsistent joins reject. No overwrite/retry. Filesystem failure during writing may leave an incomplete fresh root; preserve it, do not reuse it. No new general custody framework or clean/H1 certificate was introduced.

## Tests actually run

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_parent_wake_material.py -v`: **17 passed in 12.198s**.
   Synthetic CPU formations use the real existing producer/ledger/teacher/slot interfaces and V3 encoder. Tests cover raw joins despite rejected notes, repeated ACTs/ordinals, clipping recovery, teacher targets/context, no same-event feedback in training context, exact masks, single accepted mini-sudoku shortage, token shortage, source/tick/seed corruption, input drift and no overwrite. Both old NOTE judges and trainer entrypoint are patched to raise during the positive exporter test.
2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_parent_material_diagnostic.py -v`: **13 passed in 30.287s**. Log `/tmp/astra_parent_wake_formation_tests.log`.
3. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_parent_note_replay_diagnostic.py -v`: **12 passed in 32.205s**. Log `/tmp/astra_parent_wake_replay_tests.log`.
4. `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_train_adapter_v3.py`: exit0, script reports 9/9 with **three optional-dependency skips/partial skips**; no claim of GPU training tests. Log `/tmp/astra_parent_wake_trainer_tests.log`.
5. `PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.parent_wake_material --help`: exit0.

The first exporter test run exposed a fixture mistake: leading spaces before ACT meant the actual native parser executed only the second ACT. The fixture was corrected to leading newline so both repeated ACTs genuinely execute; parser behavior was not relaxed. Existing bootstrap ResourceWarning remains unchanged.

## Remaining limitations / freeze

Local tests are synthetic CPU, not actual-tokenizer export of archived P0. Original on-node source paths and model pins are intentionally required; a copied capsule does not pass by editing its recorded paths. Main must choose the comparison/count/selection and then invoke the actual source/tokenizer CPU preflight. Token/teacher shortages are possible and are not repaired by this module. Parent-influenced historical child behavior, teacher-dose confound (203/158), different trajectories, one successful mini-sudoku source and unqualified usefulness remain disclosed. No claim about ongoing replication outcomes is made.

Frozen hashes:

- `organism_v6/parent_wake_material.py`: `b24b90766f43be7ecdb7ba1a3d20754103fa970ad1c9ccd8f5bffd092b5a6d4f`
- `tests/test_parent_wake_material.py`: `6d082f4327235dfeef1b07f7fe96d95811b703907d5094f9a55cfff031f1034b`

No further edits planned pending main review.
