# Legacy continuation-writer floor v0: repaired-byte re-audit v1

Date: 2026-09-06  
Verdict: **BLOCKED on one narrow source-join definition.** The previous B2--B6
blockers are resolved. The proposal is otherwise an honest, leakage-safe,
formative selected-continuation transport assay. This review confers no
implementation, CPU/GPU, model, training, scientific-claim, or release
authority.

## Remaining blocker

### R1. The adjacency grammar does not close marker blocks at stream boundaries

The repaired join correctly refuses to infer one global legacy writer order,
uses artifact-only program/tick adjacency, solves a finite one-to-one
attachment problem, and rejects multiple valid assignments
(`legacy_continuation_writer_floor_v0.md:34--52`). That is sufficient for
marker blocks flanked by two thoughts and safely rejects genuinely ambiguous
consecutive one-tick cases.

But the declared group universe is only maximal `act`/`note` runs **between
neighboring thoughts** (`:42--43`). A marker-before-thought writer creates a
leading block before the first thought in a program-filtered stream; a
thought-before-marker writer can create a trailing block at the frozen
prefix/fence boundary. Those blocks have exactly one adjacent thought and are
not defined by the present sentence. Because every pre-cutoff row must be
assigned (`:54--61`), a literal implementation either rejects otherwise valid
lives or silently invents an unratified boundary rule.

The cutoff also depends on “the first fence occurrence” (`:54--55`) without
defining first in raw-offset versus manifest-occurrence order. The later
noninterleaving requirements fail closed, but they do not remove that byte-level
ambiguity.

**Minimal exact repair:** define, for each program-filtered stream restricted to
the bound prefix-plus-fence interval, the complete marker-group universe as
every maximal physically contiguous run of `act`/`note` rows, including a
leading or trailing run with only one neighboring thought. Candidate edges are
only to the immediately preceding and/or following thought when that neighbor
exists and program/tick agree; retain the existing unique-complete-assignment,
one-group-per-thought, and rejection rules. Define the terminal cutoff as
`min(start_offset(row))` over **all rows assigned to any occurrence in the
successor fence wake**, then require every eligible assigned row to end at or
before it, every fence-assigned row to start at or after it, no row to straddle
it, and no permitted but unassigned row before it. Bind that exact cutoff and
the leading/trailing candidate edges in both extractor outputs.

No new heuristic, source-code authority, distance tie-break, or extra wake is
needed.

## Resolution of the original six findings

- **B1:** substantially repaired; R1 above is the only remaining closure gap.
- **B2:** resolved. All design/configuration bytes and the finite contamination
  input manifest are human-ratified before target enumeration, and any later
  change abandons the namespace (`:142--173`, `:265--270`).
- **B3:** resolved. C1/C2 are explicitly target-token/update matched, not fully
  exposure matched, and the estimand is limited to the exact neutral-chat-prefix
  package with positions, token counts, and FLOPs reported (`:98--122`).
- **B4:** resolved. C2-minus-C0 is expressly the total effect of the complete
  post-hoc selected-corpus package; verification, binding, novelty, and source
  conditioning are excluded. Birth-payload exclusion is diagnostic only and
  cannot condition the claim (`:237--255`).
- **B5:** resolved. Both B0/C1 and B0/C2 training paths, C0 serving, and the
  zero-delta mount path are duplicated under exact bindings. The deliberately
  strict bitwise policy fails closed into a new ratified design rather than
  inviting a post-hoc tolerance (`:124--140`). This is conservative but
  scientifically coherent.
- **B6:** resolved. The target renderer, message array, tokenization, serving
  parameters, state reset, parser, score, and common deterministic C0 identity
  are exact (`:175--225`).

## Materialization disposition

After R1 is repaired in the proposal bytes, this design is ready to enter the
`AGENTS.md` deliberation/ratification path. Its estimands are appropriately
narrow: first-action continuation reinforcement from a post-hoc selected
corpus, plus the exact prefix-package contrast. It cannot support native task
conditioning, causal verification/grounding, learned THINK, continual
learning, parenting, or an experience-model flywheel claim.

## Final byte confirmation after R1 repair

The proposal was reread after the surgical edit. It now enumerates leading,
interior, and trailing marker groups; restricts candidate edges to existing
immediate compatible neighbors; requires a unique complete assignment; and
defines the cutoff as the minimum start offset across all rows assigned to any
successor-fence occurrence, with explicit eligible/fence ordering, no straddle,
and no unassigned/unknown prior row. R1 is resolved. **Final proposal-level
verdict: PASS for architecture deliberation only.** No extraction,
implementation, model, GPU, training, or claim authority follows from this
confirmation.
