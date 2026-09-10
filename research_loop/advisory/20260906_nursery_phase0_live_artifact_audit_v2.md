# Nursery phase-0 live-artifact audit v2

Date: 2026-09-06 02:49 PDT  
Scope: read-only audit of the already-running Fable nursery artifact on the
A40 host. This audit did not launch, stop, or modify the run. It grants no
architecture, parenting, GPU, or scientific-claim authority. The static
preflight remains in `20260906_nursery_phase0_static_audit_v1.md`.

## Verdict

The current repaired trainer does retain supervised response tokens for this
specific 24-row corpus. The run nevertheless cannot measure parenting or full
curriculum inheritance: every lesson was clipped to a 1,176-character source
prefix, the parent was absent, and 55 of 56 rows admitted by the alleged
native-`NOTE` gate did not contain a line-start native `NOTE` marker.

Treat any output as a formative writer/behavior scout only.

## Bound bytes and live state

The remote files matched the local working-tree bytes:

| file | SHA-256 |
|---|---|
| `organism_v6/nursery.py` | `18dfdd7064533c7a8c52ac5b4ebf88537d5aa4dfbe1431ec8abad515c8a2e256` |
| `organism_v6/train_adapter_v21.py` | `a9bd1a55c997968d43ac240379149a2e9b8020f953e0a133654b0841d6c817e3` |
| `organism_v6/state.py` | `e67ea71c18ef31082be6d2b56fa6004c29af08d8935669ce5099e6c26da429af` |
| `organism_v6/sleep_compile.py` | `9049a6e5f8ef4fdf35077a48c5500f3ca07b419274dc7fdb3abe605720f99a82` |

At inspection, GPU 6 was training `nursery_gen1/sleep_inherit/adapter` at
rank 8, 5 epochs, learning rate `5e-5`. GPU 7 was idle. This was a Fable run,
not a Codex-authorized PPC or parenting run.

## Exact curriculum delivery

`render_context()` truncates the entire initial tail item to 1,200
characters. The wrapper `=== TODAY'S READING ===\n` consumes 24 of those
characters, so the child saw exactly the first **1,176 source characters** of
each lesson. Source lengths were 3,148--4,245 characters. Coverage therefore
ranged from 27.7% to 37.4%; no lesson was delivered completely.

The completion markers nevertheless recorded all twelve readings as done.
Later generations had only the clipped prefix and prior generated text, not
the omitted source suffix. Model-generated headings such as “TODAY'S READING
(Continued)” are not evidence that the suffix was delivered.

## Exact compiled corpus and token path

The compiler reported 56 eligible stream thoughts and 2 recall rows, then
answer-prefix deduplication reduced the saved corpus to 24 rows: 22 exact
stream-pair matches and 2 recall rows.

Using the pinned cached Qwen2.5-7B-Instruct tokenizer and the exact current
`train_adapter_v21.encode()` rule:

- corpus rows: 24;
- supervised response tokens: 7,947 total, mean 331.125 per row;
- zero-label rows: 0;
- prompt-truncated rows: 0;
- answer-truncated rows: 0;
- rows losing response EOS: 0;
- prompt token range: 51--1,441;
- response token range: 53--401.

This closes the old zero-label failure **for this artifact only**. It does not
validate the general trainer: arbitrary longer responses can still lose EOS
under the 1,024-token answer cap, no per-row receipt is written, skipped
non-finite batches do not make the run fail, and an empty corpus still exits
successfully without an adapter.

## The support/native-dialect gate did not hold

Of 65 thought rows:

- 56 had `had_note=true` and were eligible for compilation;
- only 1 thought contained a line-start marker matching `^NOTE`;
- 55 eligible thoughts were false positives under that native-marker test;
- the ledger contained only 2 parsed `kind=note` rows.

Most false positives began with Markdown such as `### NOTE:`; others merely
mentioned `NOTE` in prose or regenerated parts of the reading. The admission
test in `batch_loop.py` is substring-based, while the live action dialect is a
line-start marker grammar. Thus the run trains predominantly on off-dialect,
unverified summaries despite its “native” label.

Per-lesson exact stream rows surviving corpus dedup were:

`1, 1, 1, 4, 1, 4, 1, 4, 1, 2, 1, 1` for lessons 01--12.

This is highly unequal exposure produced by generation/repetition and the
first-120-answer-character deduplicator, not a registered curriculum dose.

## Claim boundary and next gate

The run can at most reveal whether this clipped, off-dialect self-summary
corpus perturbs later generations. It cannot establish:

- interactive parenting (the parent prompt has no runtime consumer);
- full inheritance of the twelve lessons;
- verified or child-specific correction;
- disposition transfer rather than recitation/style change;
- target-blind task improvement.

## Completed output: null and probe-invalid

The chain completed after the first inspection. The adapter trained for 120
optimizer steps (24 rows x 5 epochs, batch size 1), reporting final loss
`0.5382`. `train_meta.tokens=128785` counts all attended prompt and response
tokens across epochs; it is not the supervised-target count reported above.

The unseeded eight-rollout behavioral summaries were:

| endpoint | adapter OFF | adapter ON |
|---|---:|---:|
| emitted PREDICT | 8/8 | 8/8 |
| emitted ACT | 8/8 | 7/8 |
| PREDICT before ACT | 8/8 | 7/8 |
| emitted NOTE | 8/8 | 8/8 |
| scoped NOTE | 0/8 | 0/8 |
| emitted RECALL | 3/8 | 1/8 |

This is not evidence of improvement. Direct absorption answers were generic
base-style lists and had no blinded rubric or obvious on/off separation.

The behavior probe is also internally invalid for its stated purpose. It asks
the agent to discover a mystery-box rule but supplies no interactive mystery
box evaluator, while rendering the compiler-specific production bootstrap.
Both arms consequently emit LLVM pass strings as `ACT` values. The result is
marker/style compliance in a contradictory prompt, not a disposition-transfer
or task-learning assay.

Bound result artifacts:

| artifact | SHA-256 |
|---|---|
| adapter weights | `797647ad72b7076248132f4cb755fd3682e2e518c445849a6b32f07896a08801` |
| adapter config | `2fa2edfc3983201e5353cdbda842f91805b86c7edd622720ad3e1fd8e0a4cbd4` |
| training metadata | `2315e799eb2a0003e504f7ef0ca2f30a317c5b4a07f0f99b2b4769ccf85363da` |
| behavior OFF | `88ad2736b1e4ccba051ceb6bd79888ef50c4e07783797755670f3c6af8dd06f5` |
| behavior ON | `032b26c71b56141827a6dd3938b5bdfdbc4f1edf186a67cf7f3efbe6131e0729` |
| absorption OFF | `894431e4b09c9425edeceb649548a484cedafb4116cd504ef8b449ec73479105` |
| absorption ON | `f52057831daff2689b63c6569178a7b103a0b131852044d4c970b5b5e73d238a` |

The next valid scout remains the minimal causal unit in
`plans/parenting_nursery_v0.md`: complete lesson delivery, one actual
child-specific parent correction, restatement plus near transfer, reversible
dream successor context, exact live-dialect write, then parent-absent paired
behavior under adapter-on/off/shuffled/wrong-child controls.
