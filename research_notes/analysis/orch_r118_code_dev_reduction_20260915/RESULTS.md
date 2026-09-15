# First shared child's CODE DEV outputs

September 15, 2026, approximately 14:53 UTC. Read-only native reduction;
no new inference, training, parent calls or sealed FINAL reads.

## Measured behavior before outcome

The same eight ordered DEV tasks have matching saved input messages, prompt
token counts and generation caps. F3 C19 and A3 C5 are the last existing
pre-shared snapshots selected here; F3 C21 and A3 C7 use the first committed
pooled child, checkpoint
`43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`.

| Measure | Pre-shared | First pooled child |
| --- | ---: | ---: |
| Completed tasks | 8/8 | 8/8 |
| Median generated tokens, including EOS | 41.5 | 36 |
| Total generated tokens | 370 | 353 |
| Truncated responses | 0/8 | 0/8 |
| Whole-response JSON expression wrapper | 3/8 | 6/8 |
| Required last-line JSON expression wrapper | 0/8 | 0/8 |

All eight output texts and token sequences changed from pre-shared to pooled.
Six responses became shorter; two became longer. At each snapshot, F3 and A3
have identical output hashes and token-ID hashes on all eight tasks. This is
**one shared model evaluated twice**, not sixteen independent observations or
evidence of different Fable/Astra learning effects.

No repeated token or whitespace-word fourgram occurs in the eight pooled
outputs. The decoder already applies a fourgram repetition constraint; this
does not establish learned avoidance of repetition. The reducer does not
score departures, metacognitive shifts, coherence or novel-thought yield.
Those semantic measures remain unassessed.

Main's manual inspection of these eight paired DEV outputs found attempted
expression/JSON answers rather than explicit reasoning narratives. Changed
text includes altered constants, invalid expression syntax and wrapper
differences. That inspection is not a blinded semantic rating and is not
passed to parents as TRAIN evidence. Shorter output or increased whole-response
JSON frequency is not demonstrated useful thinking or retained improvement.

## Outcome and interpretation limits

The unchanged official scorer records 0/8 correct and 0/8 format-valid in
both snapshots. Its parser inspects the final nonempty line only. The
whole-response JSON count above is a separately labelled formatting diagnostic;
it neither changes official scores nor establishes that the enclosed expressions
are valid, permitted or correct. A closing brace alone fails the original
last-line contract even if the complete response parses as JSON.

The pre-shared branch is documented as frozen BASE, but it is not an
adapter-matched frozen copy of the pooled lineage's initial child. There is
also no matched unparented pooled optimizer here. This reduction cannot
identify a causal parenting effect, isolate inherited LoRA behavior from
this sleep, or satisfy the sprint's control requirements.

F3's original sleep-0 DEV and C1 DEV each have eight FAILED captures. Those
remain failed; selecting already-completed C19 is not a retry or a substitute
claim that the original baseline succeeded. A3's original sleep-0 captures
completed. No calls were replayed to produce this reduction.

## Receipts and tests

`F3_v2.json` and `A3_v2.json` include per-task native hashes, visibility checks,
checkpoint binding, paired deltas and lexical diagnostics without raw text,
messages or token arrays. Earlier `F3.json`/`A3.json` reductions are preserved.
`CPU_TESTS.txt`: twelve local unittest tests passed, including no FINAL access,
failed-row preservation, exact input/cap matching, training exclusion and
format-diagnostic separation. These are reducer tests, not model evaluations.

Immutable native reducer:
`/localhome/local-rohing/orch_r118_code_dev_reduction_source_20260915_v2/orch_r118_code_dev_reduction.py`.
Reproduce through `gpu/ovx3_ssh.sh` with the selected root, `--before`, `--after`
and `--checkpoint-sha256` values recorded in these receipts. No GPU is used.
