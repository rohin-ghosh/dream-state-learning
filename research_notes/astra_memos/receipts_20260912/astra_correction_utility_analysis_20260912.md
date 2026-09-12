# Correction utility: six-recipient terminal reduction — September 12, 2026

**Result:** the unchanged CPU reducer returned `SIX_TERMINAL_CELLS_VALIDATED`, exit 0, on its first actual-capture invocation. No verification failure was encountered; no implementation/test repair was needed. Input evidence was not rewritten. This is a selected one-experience material-utility development comparison, not a parenting, P1, H1/H2, retention, generalization or clean-lineage result. Main's supplementary rescoring is separate and was not consulted or changed.

## Primary endpoint: first ACT accepted by recorded native verifier

Each cell has the same 32 development questions. OFF is **0/32** in all six pairs. Full raw wake/Scratchpad outputs and per-episode outcomes agree across all six OFF runs: one shared deterministic baseline, not six independent learners.

| Recipient seed | whole_raw ON | whole_raw ON−OFF | act_only ON | act_only ON−OFF | whole_raw−act_only gain |
|---|---:|---:|---:|---:|---:|
| 0 | 1/32 (3.125%) | +1/32 | 2/32 (6.25%) | +2/32 | −1/32 (−3.125 percentage points) |
| 1 | 0/32 (0%) | 0/32 | 2/32 (6.25%) | +2/32 | −2/32 (−6.25 percentage points) |
| 2 | 1/32 (3.125%) | +1/32 | 1/32 (3.125%) | +1/32 | 0/32 |

Accepted episode IDs, from first-ACT ledger records cross-bound to raw generations:

- whole_raw seed0: `rg/mini_sudoku/1900008`; seed1: none; seed2: `rg/mini_sudoku/1900008`.
- act_only seeds0/1: `rg/mini_sudoku/1900044`, `rg/mini_sudoku/1900047`; seed2: `rg/mini_sudoku/1900044`.

The whole_raw-minus-act_only primary contrast is negative, negative, tied across seeds. There is no observed full-Scratchpad advantage on this endpoint. No episode-pooled significance or independent-experience replication claim is made.

## Format and native partial-score diagnostics

All 12 OFF/ON conditions have exactly one native-parsed ACT per episode: **zero missing ACTs and zero multi-ACT episodes**. Native marker parsing is permissive. The separately declared strict diagnostic requires `ACT:` and four semicolon-separated rows, each containing four digits in 1–4; it is a syntax check, not independent board correctness.

| Condition | Strict first ACT /32 | Malformed ACT markers | Native first-ACT score mean |
|---|---:|---:|---:|
| Shared OFF | 2 | 30 | 0.059765625 |
| whole_raw seed0 | 5 | 27 | 0.1467578125 |
| whole_raw seed1 | 6 | 26 | 0.12189275568181819 |
| whole_raw seed2 | 5 | 27 | 0.119140625 |
| act_only seed0 | 30 | 2 | 0.431640625 |
| act_only seed1 | 30 | 2 | 0.42812500000000003 |
| act_only seed2 | 28 | 4 | 0.4091796875 |

Partial means retain the reducer's serialized float values. Since every episode contains one ACT, native-best means equal first-ACT means; no later successful action substitutes for a failed first action. Raw action counts, generation bindings and native summaries agree. The frozen panel labels all 32 questions incompatible with the single trained board's public givens; this is a recorded panel property, not new verifier adjudication or proof of transfer. No reference-answer comparison or board re-solving was performed here.

## Dose and cost

All six fits validate **96 optimizer steps, one unique source event, 32 explicit replays, three epochs**, matching model/panel/settings and saved rank-8 LoRA configuration. Training input/target tokens differ by treatment:

| Arm | Input token passes per fit | Supervised target token passes per fit |
|---|---:|---:|
| whole_raw | 92,064 | 8,832 |
| act_only | 86,880 | 3,648 |

These are not token- or compute-matched fits; target accounting includes the recorded supervised EOS. Replays are not separate discoveries.

| Arm/seed | Fit training seconds | Fit wall seconds | Recipient condition wall seconds | ON generated characters |
|---|---:|---:|---:|---:|
| whole_raw/0 | 84.7 | 85.3 | 776.314736 | 16,269 |
| whole_raw/1 | 83.9 | 84.4 | 695.798777 | 13,026 |
| whole_raw/2 | 84.1 | 84.6 | 736.047406 | 16,078 |
| act_only/0 | 81.3 | 81.8 | 625.526204 | 2,689 |
| act_only/1 | 81.1 | 81.6 | 578.221335 | 2,688 |
| act_only/2 | 81.8 | 82.3 | 578.913064 | 2,689 |

Each OFF/ON condition records 64 generation batches and **16,000 reserved output tokens**, not measured usage; all OFF outputs contain 10,409 generated characters. Actual generation token counts and truncation/finish reasons are absent and remain `null`, not inferred from characters or caps. Summed fit training time is 496.9 seconds; summed recipient elapsed time is 3,990.821522 seconds, **not calendar campaign time or measured GPU compute**, because conditions can overlap and include loading/probing.

## Verification and unverified boundaries

- Capsule SHA256 matches Main's supplied pin. Every one of **628 regular extracted files** matches the archive; no unsafe archive entry, extra/missing extracted file or byte mismatch. No extraction was necessary.
- Panel SHA256 matches the prospective fixed pin. The fresh index identifies all six distinct arm/seed cells without rewriting recorded absolute remote paths.
- Reducer checks all six completion markers, 96-step fits, corpus/tokenization/adapter metadata, paired model/panel/settings, source checks, generation/ledger/summary consistency and original captured `PAIR_DONE`/worker receipt hashes. All pass. Its **542 tracked input files** were independently rehashed after reduction and still match.
- Main's captured `MAIN_TERMINAL_AUDIT.json`, observed at **2026-09-12 13:55:58.780996 UTC**, agrees with the reducer's native pair receipt hashes for all six recipients; its adapter hash dictionaries exactly match the captured probe specs. Every captured `controller_absent` and `released` value is true. These are checked archived assertions, **not a new live process/GPU-release inspection**.
- All six adapter weight files are omitted from this capsule. Captured metadata is rehashed locally, and Main's recorded weight hashes agree; this sidecar does **not** independently rehash remote weights, replay original remote source, authenticate official model origin, or attest loaded GPU state. No GPU, SSH, network, training or git action occurred.
- Regression command below passes **87 tests**. No source/test edits were made in this terminal-reduction turn.

## Artifacts and reproduction

- Index: `/tmp/astra_correction_utility_capture_20260912.json`
  - SHA256 `14d4818c5959f1c5202460b132c561f5f0d04b5bbb730e106c7d933f1666d6e6`
- Complete machine report: `/tmp/astra_correction_utility_analysis_20260912_attempt1.json`
  - SHA256 `29b6cf3ca3de9b4d9f6fe643fc769dbaed3a3cbc710d6e69bb1f6e53ec8dd7b0`
- Reducer stderr: `/tmp/astra_correction_utility_analysis_20260912_attempt1.stderr` — empty, exit 0.
- Capsule: `/tmp/astra_correction_utility_terminal_20260912.tgz`
  - SHA256 `dfbb71fb9ea07bbff5dc990ca5c2028796d173bc0c51520b2f45c53cad87e3a4`
- Panel: `/tmp/astra_correction_utility_panel_20260912.json`
  - SHA256 `11b87e8b901978bcb331f2d126632517214e2a62c82221a47afd5baedd01cb2e`
- Main terminal audit SHA256: `d9ff094d74b0b9c107e46325330a1aef073715f18ae1a2bc63575862149136ab`.
- Reducer SHA256 at execution: `6cac222bf0500e787e7d18edf234a83c4fcdc1eb0172aee9490041df3ad0557c`.

From `/data/home/rohing/dream-state`, print a fresh reduction to stdout (do not overwrite the existing evidence/report):

```bash
python3 -B -m gpu.astra_correction_utility_analysis \
  --capture /tmp/astra_correction_utility_capture_20260912.json \
  --capture-sha256 14d4818c5959f1c5202460b132c561f5f0d04b5bbb730e106c7d933f1666d6e6

PYTHONPATH=tests:. python3 -B -m unittest \
  tests.test_correction_utility_analysis tests.test_correction_utility_diagnostic \
  tests.test_mini_sudoku_behavior_analysis tests.test_neutral_pair_custody -q
```
