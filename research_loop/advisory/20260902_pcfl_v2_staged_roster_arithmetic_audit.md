# PCFL-Compose staged-v2 roster: arithmetic and adaptivity audit

**Status:** read-only advisory. This audits the proposed staged roster in
`20260902_pcfl_v1_value_and_efficiency_audit.md` at SHA-256
`376d6e60d760407dbf7b983955c9d675880aa2affbf523755b84493385686a9a`.
It neither edits a proposal nor authorizes a run.

## Verdict

**FAIL as an exact, cap-bound v2 roster.**

The successful-path arithmetic is correct if every “preselected side” is one
presealed continuation and one presealed z side, and every cell uses the
declared 48/64/82/62 call units. It totals **3,414 model calls**, not merely
“about 3,400.” But the 3,600-call ceiling does not bound every stated adaptive
path: optional panels lack literal row counts, several triggers are subjective
or overlap, and the one-shot Think cell is ambiguous about z and h/q selection.
Thus 3,414 is a success-path subtotal, not a ratifiable resource envelope.

The repair is a pre-model decision-table ledger. Every terminal leaf must name
its Boolean predicate, precedence/union rule, literal rows, seeds, replay
allowance, and maximum calls. The cap must cover the largest terminal leaf, not
only the all-pass leaf.

## Exact successful-path arithmetic

The source declares these units: ordinary recurrent Dream life = 48; a
shared-Dream-1 two-continuation fork = 64 Dream calls per z side; recurrent
Think D1+D4 over two goal twins = 82 per life; D4 twins = 62 per life; a
one-shot Dream phase pair = 2 per selected life; and a one-shot Think plan = 1
per D4 goal twin. `EXACT_PROGRAM` contributes zero model calls.

| Stage/cell | Calculation | Dream | Recurrent Think | One-shot Think | Total | Finding |
|---|---:|---:|---:|---:|---:|---|
| V1 SELF h fork, z+antipode | `2 × (64 + 2×82)` | 128 | 328 | 0 | 456 | Correct |
| V1 oracle, one life, D1+D4 twins | `1×82` | 0 | 82 | 0 | 82 | Correct if presealed |
| V1 EMPTY, selected h, z+antipode, D4 twins | `2×62` | 0 | 124 | 0 | 124 | Correct |
| V1 crossed corpus, selected h, z+antipode, D4 twins | `2×62` | 0 | 124 | 0 | 124 | Correct |
| V1 sham, selected h, z+antipode, D4 twins | `2×62` | 0 | 124 | 0 | 124 | Correct |
| **V1 subtotal** |  | **128** | **782** | **0** | **910** | Correct |
| V2 untouched factor SELF h fork | `2 × (64 + 2×82)` | 128 | 328 | 0 | 456 | Correct |
| V2 independent SELF q fork | `2 × (64 + 2×82)` | 128 | 328 | 0 | 456 | Correct |
| V2 factor EMPTY+OBSERVED, h×z, D4 twins | `2 controls × 2 h × 2 z × 62` | 0 | 496 | 0 | 496 | Correct |
| V2 independent EMPTY+OBSERVED, q×z, D4 twins | `2 controls × 2 q × 2 z × 62` | 0 | 496 | 0 | 496 | Correct |
| V2 AST, two families, one life each, D4 twins | `2 × (48 + 62)` | 96 | 124 | 0 | 220 | Correct only for selected lives |
| V2 one-shot Dream, two families, one life each | `2 × (2 + 62)` | 4 | 124 | 0 | 128 | Correct |
| V2 opaque one-shot Think, two roots, D4 twins | `2 roots × 2 twins × 1` | 0 | 0 | 4 | 4 | Correct only for one selected life/root |
| V2 factor crossed corpus+sham, selected h, z+antipode | `2 cuts × 2 z × 62` | 0 | 248 | 0 | 248 | Correct |
| **V2 subtotal** |  | **356** | **2,144** | **4** | **2,504** | Correct under selected-life reading |
| **V1+V2 total** |  | **484** | **2,926** | **4** | **3,414** | Exact success-path subtotal |

The 500-Dream ceiling leaves 16 calls of success-path slack. The 3,600 total
leaves 186 calls before diagnostic panels or replay. If “same two sides” for
one-shot Think means z plus antipode for each family, that row is **8**, V2 is
**2,508**, and the successful total is **3,418**. The 4-call number requires
one presealed z side and one presealed h/q continuation for each root.

The proposed 3-million output-token and 36-million combined-token caps are not
verifiable from call counts: staged per-row input/output entitlements,
especially for one-shot Think, are absent. A v2 manifest must sum literal
prompt/operation maxima rather than extrapolate from number of calls.

## Matched controls and mandatory rows

The V2 control rows are correctly matched only if every contrast is restricted
to identical `(root, h-or-q, z_side, target, goal_twin)` keys. Factor controls
provide `2 h × 2 z × 2 twins` rows per control; independent controls provide
the analogous q-specific rows. No control may be reused across q, no h/q may
be pooled, and malformed/timeout/abstention rows must remain zero-valued in the
predeclared reducer. The independent specificity result is an alarm, not an
inferential test.

V1 pairs EMPTY, crossed corpus, and sham only at one selected h. This is valid
only if every V1 memory-value, life-binding, sham, and redirection conclusion
is explicitly limited to that h. The other h still tests raw-A revision and
authentic action, but not a matched corpus contrast. If V1 instead aggregates
or claims those interventions across both h branches, it is missing **372
Think calls**: `3 controls/cuts × 1 additional h × 2 z × 62`. V1 would be
1,282 calls and the successful path 3,786 calls before replays/diagnostics.

The V2 crossed-corpus/sham rows likewise apply only to one ordinary h and must
not be presented as a two-h aggregate. No independent corpus crossing is
required for the stated independent-table negative if q-specific SELF versus
EMPTY/OBSERVED contrasts and the conditional-null certificate are retained.

The exact program/oracle are mandatory construct ceilings, but their rows must
declare exact h-branch B checks, direct CPU solver invocations, and actor calls
separately. Their zero model-call count does not make their resource ledger
optional.

## One-shot comparability

The 4-Dream/124-Think one-shot-Dream row is arithmetically sound. Before V1,
the ledger must fix its root, h/q, z side, target/twins, public eligibility,
pre/post-A chronology, K/R/byte/output entitlements, and paired seed group
against recurrent Dream on the same life. It compares eligible information and
output capacity only; interaction, input trajectory, calls, latency, and FLOPs
remain intentionally unmatched.

Four opaque one-shot-Think calls are sufficient only for one full frozen
corpus/goal/menu packet and one open-loop action plan per D4 twin in two
preselected root-lives. The plan contract must freeze corpus bytes/order,
action-feedback policy, action-sequence requirement, cumulative output cap
matching the 31-call iterative trajectory, and paired seed IDs. Otherwise the
comparison changes recurrence, full-corpus exposure, lexical retrieval, and
action-tray feedback together. A one-shot match can remove an advantage claim
for this disclosed interface; a one-shot failure cannot prove recurrence is
necessary.

## Adaptive-trigger audit

The V1-to-V2 gate can be selection-safe for a DEV diagnostic only when it is
predeclared, consumes named immutable Boolean receipts, does not replace roots
or analysis after output, keeps V1 failure durable, and records every row as
`RUN_SUCCESS`, `RUN_FAILURE`, `NOT_TRIGGERED`, `NOT_APPLICABLE`, or `NOT_RUN`.
The source states these principles, so the basic staged design is sound.

Its optional panel table does not yet meet them. “Appears noisy,”
“scientifically important,” and “a recurrence claim is contemplated” are not
mechanical predicates. Several listed signatures may co-occur, but there is no
precedence or union rule and no per-panel count. Consequently the claimed
1,000--1,400 additional calls and the 3,600 cap cannot be audited; panels
triggered after apparent success can exceed the success-path envelope.

Freeze a terminal-leaf routing table with `predicate_id`, exact receipt fields,
precedence-or-union rule, exact row keys, seed groups, replay allowance, call
count, and terminal status. Make success-contingent exploratory panels
`NOT_TRIGGERED` in this DEV, or include their maximum union in the cap. A
triggered diagnostic may explain a durable failure but never rescue it or enter
a selected efficacy denominator.

## Additional blocking resource repair

V0 retains v1's 128-root CPU suite but not a jointly satisfiable CPU statement:
`128 × 30 CPU-minutes = 64 CPU-hours`, versus the prior 24-hour aggregate cap.
Use a compatible per-root bound (for example 10.5 minutes gives 22.4 CPU-hours)
or state that failure to certify all roots returns `NOT_RUN` without claiming
the complete suite fits the envelope.

## Recommendation

Pass only after a new v2 manifest chooses one explicit envelope:

- **narrow selected-h plan:** 3,414 scientific calls plus named replay and
  fully bounded diagnostic-leaf maxima; or
- **both-h V1 intervention plan:** 3,786 scientific calls before replay and
  diagnostics, with a correspondingly increased cap.

Either retains the main causal test. The first is preferable if all V1 action
intervention language is confined to its selected h. As written, the roster
fails exact arithmetic/cap and adaptive-validity review despite its correct
successful-path subtotal.
