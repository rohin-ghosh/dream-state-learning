# Citation-sleep terminal adversarial audit

Date: 2026-09-12 UTC
Status: read-only scientific audit and recommendation; no builder code, run,
adapter, process, or GPU state was changed.

## Verdict

This is an exact **usable-output null**, not a mechanistic null about factual
memory. OFF, full-prefix, and syntax-mask are all 0/8 format-valid and 0/8
grounded. Full-minus-syntax and both trained-minus-OFF contrasts are therefore
zero on t02, the other seven exposed boards, and the whole panel. The only
positive observation is morphological: unlike OFF, both trained arms emit a
learned-looking citation prefix and then the same kind of 32-token malformed
JSON, for example `..."digit":1}][]}`. That is compatible with an
update-induced fragment/template habit, but it does not identify storage of a
factual citation.

The exact failure is **uncommitted continuation training**. The frozen target
ends at

```text
{"case_id":"t02","checks":[{"group":"box","cells":[[3,3],[3,4]],"digit":1}]
```

It omits the required `lesson` field, the top-level closing brace, and EOS.
The objective therefore rewards reaching a syntactically nonterminal prefix
and supplies no loss for completing or terminating the object. The terminal
malformation is direct evidence that this fragment recipe did not cross the
serialization/commit boundary required by the scorer. It is not evidence that
the adapter could not store the cited values behind another readout.

## Evidence and integrity boundary

The synced preparation capsule is internally consistent: digest
`bd1cd8a2...ac`, identical 264-token forward inputs, no EOS or truncation in
the fitted prefix, 32 presentations, and 8,448 input token-passes per fit. The
full arm has 27 supervised tokens per presentation and syntax has 21, or 864
versus 672 supervised token-passes. Both main and native logs report all 23
focused CPU tests passing. The launch receipt preserves the intended
one-seed, 24-read, two-fit order and its explicit claim exclusions.

A terminal result capsule is not synced under the citation-sleep receipt
names. Terminal outcome and cleanup facts here therefore rely on the supplied
authoritative read-only terminal summary, corroborated by the later checked-in
`COORDINATION.md` entry: `COMPLETED`, controller absent, GPU empty, and all
five cleanup receipts passing. Those operational facts are not independently
replayable from the local preparation capsule.

## Why the arm contrast does not identify a mechanism

1. The strict endpoints are floored. Zero full-minus-syntax says only that the
   six additional directly supervised value-token positions produced no
   *usable-output* gain in this one recipe. It does not show equal hidden
   states, logits, target likelihood, or adapters, none of which is in the
   available terminal summary.
2. “Syntax-only” means no direct loss on `box`, the four coordinates, and
   `1`; it is not content-blind. Those exact values remain in the identical
   teacher-forced input, and losses on subsequent punctuation are conditioned
   on them. Thus the arm cannot separate factual exposure from syntax or rule
   out indirect gradients through factual-token states.
3. Supervised dose is not matched: full carries 28.6% more loss-bearing tokens
   per presentation. Equal update count and input token-passes do not repair
   that mismatch. OFF also has no compute-matched update control.
4. There is one repeated, outcome-selected record, one optimizer/generation
   seed, and eight already exposed boards. t02 was selected post hoc from the
   sole grounded second-board output; its accepted witness is also valid on
   the paired source board. This is neither a clean changed-board transfer nor
   an independent experience sample.
5. The fitted bytes contain no source note, example, lesson, parent text, or
   whole committed record. Clean ancestry, holdout, persistence,
   internalization, parenting, and a qualified SLEEP writer are outside the
   experiment by construction.

No representation-level or factual-versus-syntactic mechanism is justified.
At most, within this deterministic execution, partial-prefix fitting changed
the output mode toward a brittle global prefix habit. Even that statement is
about observed behavior after updates, not how or where content was stored.

## Smallest high-information next writer test

Run a **two-target complete-record micro-canary**, not another eight-board
full-versus-syntax fragment comparison.

- On the same t02 prompt, preseal two distinct, mechanically grounded,
  token-count-matched citations. Give them identical complete schema and
  neutral lesson text, including the final brace and EOS; only the factual
  witness fields differ.
- Start two fresh-base, same-initialization arms. Arm A is supervised through
  the complete record and EOS for target A; arm B receives target B. Measure
  both complete-continuation log likelihoods before training and after each of
  the first two real, budgeted updates.
- Stop after those four total updates unless
  `log p(A)-log p(B)` moves positive in A and negative in B. This opposite-sign
  gate rejects a common schema prior or generic optimizer disturbance without
  paying for a full fit.
- Only on a gate pass, continue the same fits to small presealed checkpoints
  (for example 8 then at most 32 updates) and greedily read t02. Require both
  arms to emit their assigned, parseable, grounded record with EOS. Query the
  other seven exposed boards only after that exact-prompt positive control,
  and treat those reads solely as a parroting/spill diagnostic.

The two targets are an engineered, disposable mechanism canary; they do not
become child-authentic lineage material. A failure localizes the writer below
whole-record commitment or target-sensitive optimization. Opposite-sign
likelihood movement followed by assigned complete generation would establish
only exact-prompt, supervised, target-specific whole-record carriage. It
would still not establish transfer, generalization, authentic experience,
retention, internalization, parenting, or H1/H2.

## Exact claim boundary

> In one selected post-hoc record, one seed, and eight exposed prompts, 32
> presentations of either a full-loss or syntax-masked **partial citation
> prefix** produced zero parseable and zero grounded outputs. Six additional
> directly supervised factual tokens per presentation gave zero strict-endpoint
> gain over the syntax mask, while both trained arms produced 32-token malformed
> continuations. The experiment demonstrates failure to commit a usable JSON
> record under this fragment objective; it does not adjudicate factual storage
> or any transfer, persistence, internalization, ancestry, parenting, or SLEEP
> mechanism.
