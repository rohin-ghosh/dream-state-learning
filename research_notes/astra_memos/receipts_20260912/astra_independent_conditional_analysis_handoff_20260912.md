# Astra conditional root0 — independent raw-analysis sidecar

2026-09-12. **CPU-only deliverable complete. EDITSTOP.** This is an independent
arithmetic/parser implementation, not a new assay, launch gate, or scientific
verdict. Main retains protocol, launch, collection, and interpretation ownership.

## Owned files and exact bindings

Only these three files were created/edited:

- `/tmp/astra_independent_conditional_analysis_20260912.py` — 789 lines;
  SHA256 `edd380af2e4c2122dc247e2c7652c89d8d56860a63772ed5e0f0d4fb8b5f6223`.
- `/tmp/test_astra_independent_conditional_analysis_20260912.py` — 685 lines;
  SHA256 `ea9e1ccfa631c80c08017f007319ac1641294716e6658347687584c0a0a28869`.
- This handoff, `/tmp/astra_independent_conditional_analysis_handoff_20260912.md`.

Frozen CLI pins, independently checked against the permitted static local files:

- Readout manifest: `5a26f0da17d53518aa00c80bce3bfbfbe76ef61e65ea5ebc781f797dd33190a6`.
- Candidate file: `5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c`.
- Assay: `conditional-dual-map-fixed-endpoints-v2-20260912`;
  contrast: `dual-map-belief-endpoints-v2`.

Read only source/schema, static candidate/manifest, and frozen amendment/handoff
documents. No repository edits, Git, network, GPU, model/tokenizer imports,
native execution, live outcome bytes, collector execution, or launch actions.
No analysis JSON has been written. Synthetic fixture data stayed in memory;
CLI output tests mocked file creation. Nothing was written to the repository.

## Main-only use after terminal collection

The positional argument is the **safe extraction directory containing
`astra_diagnostics/`**, not the nested run root and not the archive itself.
Main must have validated/extracted the collector capsule safely. This script
does not extract archives, collect anything, follow native absolute plan paths,
read model directories, or poll a live run.

```bash
python3 -B /tmp/astra_independent_conditional_analysis_20260912.py \
  /tmp/MAIN_SAFE_READOUT_EXTRACTION \
  --validation /tmp/astra_conditional_readout_root0_terminal_20260912.tgz.validation.json \
  --output /tmp/astra_conditional_root0_independent_analysis_NEW.json \
  --terminal-data
```

`MAIN_SAFE_READOUT_EXTRACTION` and the NEW output path are placeholders for Main
to choose. `--terminal-data` is an explicit Main affirmation, not permission to
inspect a live native tree. Before reading raw calls the loader requires
collector-inventoried, hash-matching terminal and Main full-release/controller-
absence markers. Missing/nonterminal markers refuse without creating output.

Defaults use `/tmp/astra_conditional_readout_manifest_root0_20260912.json` and
the existing attempt2 native-preparation `material/candidate.json`. Optional
`--manifest`/`--candidate` permit relocated files **only with the same frozen
bytes**; there is no CLI bypass for the pins. Material is external because the
readout capsule does not include that directory. Collector validation must be
provided explicitly. The archive itself is not reopened or rehashed here;
Main's safe extraction and validation receipt are prerequisites.

Only collector-listed metadata inside the fixed readout prefix is loaded;
unlisted extraction files are ignored. Path traversal, symlinks, hardlinks,
special files, weight suffixes, duplicate JSON keys, nonfinite JSON constants,
oversized files (>32 MiB), excessive inventory (>10,000 entries), and excessive
metadata (>256 MiB) are refused. Output uses exclusive `xb` creation outside
the extraction/material tree, with no overwrite or source mutation.

- Exit **0**: all six raw panels, stored comparisons, and checked technical
  evidence agree; status `COMPLETE_INDEPENDENT_RAW_REDUCTION_NOT_SCIENTIFIC_VERDICT`.
- Exit **2 with a JSON path on stdout**: `TECHNICAL_PARTIAL`; retained diagnostics
  and explicit issues, not scientific failure or zero. A claimed COMPLETE with
  missing/invalid phases has `complete_assertion_refused: true`.
- Exit **2 with REFUSED on stderr and no new JSON**: input/safety/pin/terminal or
  output-path prerequisites failed. Never overwrite an existing analysis.

## Independent calculations

- Parse captured generation `response.text` without consulting reducer scores.
  Derive AUTH/DERANGED targets from candidate beliefs/goals or public
  expected/observed/prior-action inputs, not candidate response labels.
- Recount strict syntax, semantic components/joints and strict joints for both
  maps, train/dev, PROSPECT/REVISE, all registered strata and all four generation
  twin families. Preserve raw text. Per state the full panel is 128 train
  (64/operation), 64 dev (32/operation), 16 addition and 16 copy executions.
- Recount addition validity/correctness/exactness, copy validity/exactness, and
  tag spill. Copy has eight unique prompts executed twice; unique-all-correct
  requires both executions, not just an available partial execution.
- **Preserve the frozen copy-validity quirk:** the existing validity regex
  excludes internal hyphens, so `ACT: -loop-unroll` can be exact/correct while
  `valid` is false. This is tested and reported as specified, not repaired or
  silently normalized. Addition may be valid/correct but nonexact/spilling.
- Raw HF receipts contain `response.token_logprobs`: per-token scalar arrays
  for each complete candidate, not a separate raw complete-candidate sum field.
  Sum those arrays afresh, including the stored final EOS position, with no
  length normalization. Existing reducer `candidate_logprob_sums` are used
  **only as cross-check targets**, never as calculation inputs.
- PROSPECT belief twins register all four fixed strings: AUTH endpoint0/1 and
  DERANGED endpoint0/1. REVISE outcome twins use two actual swapped strings;
  validate AUTH0=DERANGED1 and AUTH1=DERANGED0. Never substitute goal/prior-action
  families for primary scoring or relabel the endpoint1 candidate pair.
- For each state, operation, map and each of 16 twins, retain both endpoint
  complete-candidate log probabilities, signed fixed-A/B log odds and odds
  ratios, endpoint-own-target log odds, and the signed interaction
  `(L(A|x0)-L(B|x0)) - (L(A|x1)-L(B|x1))`. Report each map's 16-twin mean
  separately. Overflowed odds ratios are null with the finite signed log odds
  retained; underflow is explicitly labeled. No absolute-value/sign selection.
- Retain signed state-minus-shared-OFF mean differences separately by map and
  operation. These are descriptive contrasts, not an automatic learning claim.
- Recount raw request, input/output-token, output-ceiling, candidate-forward,
  scored-target-token, pair-padding and call-time costs. Full workload is 672
  generation calls, 192 scoring requests, 576 candidate forwards, and a 43,008
  generated-output-token ceiling. Scored tokens are not generated output tokens.
- Compare derived generation rows/counts/strata/twins, controls, candidate sums,
  interactions, costs and summary comparisons to stored reductions/summary.
  Check exact six-phase identities, plan/capture/request/response hashes, native
  stored prefixes/IDs/masks, same state adapter for generation/scoring, shared
  source/base/material, candidate token consistency across endpoints and states,
  ordered call intervals and receipt bindings.
- Check the 64-token generation cap, stored 16,384-token context bound, 120s
  call cap, 600s configured worker/process allowance, 4500s controller bound,
  300s collection margin, and prior fit reservation plus full launch-to-
  collection window <=5400s. Worker reservations and call windows are nested;
  they are not added again to the full reservation. No independent clock,
  billing measurement, current vacancy or lease certification is claimed.

## PARTIAL and interpretation contract

Damaged/missing raw calls are diagnosed individually; other calls/phases remain
available. `observed_cost` is an observed subtotal only, never total spend on a
partial panel. Full `cost` is null when a raw panel is incomplete. Generation
coverage supplies registered and observed denominators and missing case IDs;
observed empty counts are not scientific zeros. Missing twins/endpoint values
remain explicit; a primary-family mean is null unless all 16 twins have both
endpoints. There is no available-case mean substitution. State generation
comparisons are unavailable when the required phases do not pass their checks.
Inspect root and phase issues before interpreting any retained diagnostic.

**Cannot independently recompute logits, tokenizer outputs, native EOS identity,
token-ID decoding, or actual causal forwards.** Structural stored ID/mask checks
do not prove the stored text is the token decode or the numeric logprobs came
from the claimed weights. Both parsed text and scalar likelihoods remain
capture-dependent. Metadata hashes prove consistency, not origin.

Positive interaction does not guarantee that both endpoints prefer their own
target, high absolute likelihood, or a learning effect; both endpoint odds are
therefore retained. PROSPECT's two maps do not create 32 independent twins.
REVISE's negated map effects are **not independent replications**. OFF is shared.
No automatic L1/H1/Q0 verdict, no clean-lineage/child-experience/confirmation
claim, and no composition claim: `UNTRAINED_FUTURE_ASSAY`, zero trained chain
rows. This does not change the assay or clear any launch/review gate.

## Synthetic validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /tmp/test_astra_independent_conditional_analysis_20260912.py
```

**51 tests passed, no skips; last run 3.027 seconds.** Tests use only standard
library and in-memory synthetic fixtures; no repository reducer is imported.

Coverage: rule-derived literal targets; strict versus reordered/whitespace
semantics; duplicate/missing/unknown fields and prose; both maps; all generation
cell/twin denominators; addition and copy/spill controls; duplicated copy
coverage; four-versus-two candidates; analytically known endpoint odds and
positive/negative interactions; positive interaction with one wrong endpoint;
REVISE exact negation; absent endpoint null means; EOS sum inclusion; padding
and 864-request/576-forward aggregate arithmetic; masked causal concatenations;
invalid/nonfinite/positive likelihoods and impossible candidate mass; cap
violations; missing, duplicate and corrupt phases/calls; forged stored metrics,
costs and summary totals; empty/partial panels; terminal-first read guard;
traversal/weight/symlink/JSON hazards; mandatory pins and affirmation;
exclusive output creation, no overwrite, and preserved PARTIAL/nonzero exit.

Full synthetic receipt fixtures build stored comparison payloads with sidecar
helpers to test transport/cross-check wiring. Separate literal/analytical unit
tests establish expected targets, signs, denominators and costs independently;
the wiring fixture alone is not numerical validation or native calibration.

**EDITSTOP — code and tests frozen at the hashes above. Main runs this only
when the readout terminal capsule arrives; no live analysis was performed.**
