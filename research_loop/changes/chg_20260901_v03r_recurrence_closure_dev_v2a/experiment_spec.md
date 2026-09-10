# v0.3-R recurrence-closure development transition v2a

Date: 2026-09-01 PT. Status: **superseding proposal only; unratified**.
Change ID: `chg_20260901_v03r_recurrence_closure_dev_v2a`.

## Normative inheritance

This proposal incorporates the entire v2 experiment specification at exact
SHA-256 `f01890b34b03b7f7b5edeebf5251e9d4d1e48264ba6bedc0ede46ca468963c7d`
and its architecture change at exact SHA-256
`599c98d4a9bef3d47298e4fd66530f841b27da847079bbc9df52b8b3f37667c8`.
Every v2 requirement remains normative except the four explicit corrections
below. If inherited prose conflicts with a correction, v2a controls. V2a is a
fresh intake and does not authorize or alter v2.

The experiment remains option-C recurrence closure only: six aligned
development lives, exactly three arms, 802 recurrent DREAM calls, at most 72
THINK calls, separately frozen closure baselines, no final question, no final
thinker, no answer or `RELEASE`, no LoRA, no online truth/admission/support,
blinded post-`MEMORY_1` scoring, independent artifact completeness, durable
remote markers, two exact independent reviews, exact human GPU scope, and an
unconditional post-result human stop.

## Correction 1: exact precommitted exchangeability rule

Before any provider call, independently enumerate the own and precommitted
matched-distractor selector candidate sets for each life. Compute the following
from frozen public bytes and the frozen selector only:

- candidate-set size;
- witness count separately for every witness kind;
- booleans for initial source-endpoint availability, target-endpoint
  availability, route-record availability, and effect-record availability;
- selected view count;
- mechanical closure opportunity;
- source and target endpoint frequencies (reported separately and compared by
  the maximum absolute endpoint-frequency difference);
- route and effect provider positions (reported separately and compared by the
  maximum absolute position difference);
- bounded-memory rank (maximum absolute rank difference over matched required
  items; missing is not a numeric value and therefore fails);
- tokenizer lexical overlap with the selected public view, using the exact
  frozen model tokenizer and the same denominator for own and distractor.

The pair passes only when exact equality holds for candidate-set size, every
witness-count-by-kind field, all four initial-availability booleans, selected
view count, and mechanical closure opportunity, **and** all numeric tolerances
hold: endpoint-frequency difference `<= 1`, route/effect provider-position
difference `<= 1`, bounded-memory-rank difference `<= 1`, and tokenizer
lexical-overlap absolute difference `<= 0.10`.

Classify each life before cognition:

- `EXACT`: all exact-equality fields pass and every numeric difference is 0;
- `NEAR`: all exact-equality fields pass, at least one numeric difference is
  nonzero, and all four numeric tolerances pass;
- `OUT_OF_STRATUM`: any exact-equality field or numeric tolerance fails, or a
  required numeric comparison is missing/non-finite.

Own-versus-distractor is a primary comparison only for `EXACT` and `NEAR`.
`OUT_OF_STRATUM` lives still run on the originally precommitted target and are
reported, but their distractor delta is secondary and cannot satisfy any go
criterion. There is no target replacement, resampling, adaptation, seed
substitution, or post-outcome reclassification.

## Correction 2: connector aliases

Add prompt-local connector handles `C0`, `C1`, ... to the v2 `E*`, `M*`,
`X*`, and `N0` namespaces. Each `C*` is a deterministic call-local alias bound
outside provider bytes to the SHA-256 of one connector present in the bounded
public view. The exact DREAM schemas use `connector_alias: "C*" | null` for
edge/replacement proposals. Unknown, duplicate, cross-call, or type-wrong
connector aliases reject. The provider never sees the canonical connector ID
or alias ledger.

## Correction 3: bounded DREAM output

DREAM decoding is temperature 0.2, top-p 0.95, and maximum **256** generated
tokens. Every `canonical_text` field is capped at **192 characters** (not 512).
All other exact-schema bounds remain unchanged. The preflight tokenizer must
prove that each legal maximal JSON operation fits within 256 generated tokens;
otherwise the transition fails before GPU rather than truncating or relaxing
the schema.

## Correction 4: offline-only relation normalization

No relation normalization allowlist, canonical relation vocabulary, accepted
synonym list, or normalization result appears in DREAM/THINK prompts, parsers,
memory, selector inputs, provider receipts, or cognition-time artifacts.
Relation text is stored verbatim in provisional proposals.

The frozen offline scorer alone owns a reviewed relation-normalization
allowlist. Its exact bytes and version are in the full-closure lock before the
run. It maps verbatim proposed relation strings to scorer labels only after all
`MEMORY_1` artifacts commit, reports unmatched strings separately, never
rewrites raw proposals, and cannot route retry, repair, another call, another
run, or status promotion. Allowlist changes require a new intake.

## Claim and stop boundary

The strongest result remains the inherited six-life development observation:
own query-guided bounded-view allocation changed later witness-bound
provisional proposal closure relative to no feedback and, only on precommit
`EXACT`/`NEAR` lives, the matched distractor after frozen controls. Every life,
including `OUT_OF_STRATUM`, is reported. No general, behavioral, reliability,
scaling, memory, transport, discovery, or paper-headline claim follows.

Every result or failure stops at Rohin. Follow-up, repair, replication, LoRA,
heldout access, external action, claim promotion, lease/spend change, or a
second GPU run needs a new exact intake and ratification.
