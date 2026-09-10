# PCFL physical-carrier intercept receipt v2

Date: 2026-09-07

Status: **partial receipt, model-free and tokenizer-free; positive E3 spend
remains blocked.** This supersedes only the parser and completion language of
`20260907_pcfl_physical_crossover_receipt_v1.md`. It does not supply the
missing generated-load denominators required for a complete E3 crossover
receipt.

## Independent attack adopted

The fresh review
`research_loop/advisory/20260907_pcfl_physical_crossover_receipt_attack_v1.md`
(SHA-256
`e383a80dff908dfb19ba887dfc802047fe5c3c24206df1ee87def1792451e052`)
returned **REVISE**. It independently reproduced every published parameter,
file/sidecar, strict-rate, and 8x-density calculation, but demonstrated that
the v1 parser accepted overlapping intervals and leading data gaps. It also
correctly ruled that numerator/crossover requirements are not observed
denominators or rates.

## Hardened instrument

Current script:
`research_loop/advisory/pcfl_crossover_receipt.py`

SHA-256:
`74098e6f6e3aa26ce7271cb9a25fc17afc79affe6fe4a3c6567b8c00646b5081`

Regression tests:
`research_loop/advisory/test_pcfl_crossover_receipt.py`

SHA-256:
`6085a8083547f60dc82fa27793a2433dcc43fdfa0b7753388480306b4221af30`

The revision now:

- rejects duplicate JSON keys and invalid header lengths/schemas;
- rejects negative, reversed, empty, overlapping, and gapped tensor ranges;
- requires one contiguous partition from byte zero through the exact data
  buffer and checks unique payload sum against that buffer;
- rejects unexpected tensor namespaces, layers, modules, or tensors;
- requires complete LoRA A/B pairs in all 28 layers and all seven declared
  projection families;
- validates consistent A/B rank and an explicit expected rank per artifact;
- uses exact integer rational arithmetic for the `.50` and `.35` strict
  thresholds; and
- can emit the complete tensor manifest with `--include-tensors`.

Nine CPU-only regression tests pass, including fabricated overlap, leading
gap, negative interval, duplicate-key, unexpected-tensor, rank-mismatch, and
strict-equality cases. The hardened parser was then rerun read-only against
the same rank-8/rank-16/rank-64 remote artifacts with explicit expected ranks
`8,16,64`; all three passed the new structural checks and reproduced the v1
hashes and numeric rows. No model, tokenizer, benchmark, adapter mount/train,
or GPU operation occurred.

## What is established

The exact current numerator/intercept evidence remains:

| rank | serialized `B_life` | bf16 tensor floor | expanded bytes needed for serialized `R_exp < .50` | required bytes/token at 8x16k |
|---:|---:|---:|---:|---:|
| 8 | 80,792,096 | 40,370,176 | 161,584,193 | 1,232.7896 |
| 16 | 161,533,192 | 80,740,352 | 323,066,385 | 2,464.8009 |
| 64 | 645,975,704 | 322,961,408 | 1,291,951,409 | 9,856.8070 |

The complete remote file/config/tensor-manifest hashes and accounting
breakdown remain recorded in the attacked v1 note. The new validator confirms
that their tensor layouts are contiguous, gap-free, structurally complete
all-layer carriers with the declared ranks. The exact values justify rejecting
the proposed 8x positive-rate GPU panel on scientific-information grounds.

## What remains unestablished

This is deliberately an **intercept receipt**, not the complete
`CROSSOVER_RECEIPT` demanded by note 56. Before positive E3 spend, a new,
prospectively sealed packet must still provide, for every generated load and
carrier layout/precision:

- SHA-bound eligible raw-event, canonical-semantic, and deterministic
  `EXPANDED_EQUIVALENT` artifacts;
- their exact bytes and separately authorized pinned-tokenizer counts;
- a complete common/life-specific auxiliary census and growth laws;
- serialized, resident, and simultaneously retained coordinates without
  double counting;
- actual `R_exp`, `R_raw`, and minimum possible rates; and
- at least three prospectively chosen useful loads beyond the honest physical
  crossover before power analysis or GPU work.

Accordingly, v2 satisfies the narrow question “what denominators would the
current real carriers require?” It does **not** implement the complete E3
pre-spend evidentiary receipt. Its scientific action is fail-closed: do not
run the proposed positive panel; preserve physical LoRA compression as a
later-scale objective, and keep semantic-code compression and LoRA transport
separate in any nearer paper claim.
