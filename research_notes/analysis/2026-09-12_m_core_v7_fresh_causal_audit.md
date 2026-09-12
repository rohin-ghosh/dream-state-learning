# M-core v7 fresh causal and scientific audit

Date: 2026-09-12 UTC

Scope: independent, adversarial, read-only audit of
`2026-09-12_m_core_exact_two_cycle_design_v7.md`, with only the two directly
relevant v6 causal/execution audits used as prior context. I read `AGENTS.md`
first. I did not inspect or modify builder code, run a model, use a GPU, or
treat any future package, qualification, TEXT, fit, receipt, or test as
evidence. This memo is the only intended repository change.

## Verdict

**REWORK before CPU materialization.** V7 closes most of the v6 causal defects,
and its six-fit topology can support the narrow Section 0 claim without another
trained arm. Three remaining specification gaps still admit executions that
pass the displayed schemas without identifying that exact claim. All three are
zero-fit contract repairs and should be made before the root bytes freeze.

## Exact blockers

### 1. Compiler admission is not a causal predecessor of a fit deck

Section 0 says the writer carried rows *compiled from* authenticated child
turns and that the second write occurred *following* the public experimental
outcome (lines 26--33). Compiler events do bind their own prerequisites and
admitted rows (lines 457--475 and 1400--1415), and the prose calls the S2 rows
“admitted n0/n1” (lines 697--710). There is, however, no closed training-deck
object joining those facts.

`TrainingTensorReceipt` has no compiler/admission reference. `OptimizationReceipt`
and `FitAttemptReceipt` carry only an opaque `deck_sha256`; neither identifies
the deck members or their producing compiler decisions (lines 1615--1631 and
1873--1878). `PadWorkReceipt` cites a PAD compiler case, but no corresponding
source/link/NEW lineage object exists. The program schedule has no pre-S1 or
pre-S2 compiler/deck input role; its S2 open cites only `Q_S1`, whose stated
roster does not literally require both live-C outcomes, both NEW admissions,
or a deck built from them (lines 896--902, 939--943, 1844--1849, and
2269--2271).

Counterexample: because all answer-bearing templates are presealed, an executor
can construct and fit the canonical FULL/FULL_NEW bytes first, then later emit
canonical child, outcome, and compiler traces. The fit hashes, tensors,
compiler aggregate, endpoints, and present schedule can all agree. That shows
carriage of the right bytes, but not carriage *from* the authenticated child or
*following* the experimental outcome.

Required repair: add a typed `TrainingDeckReceipt` (or equivalent) for every
fit. It must enumerate every deck row and bind each non-foundation row to the
exact admitted `CompilerDecisionEvent`/`CompilerCaseReceipt` or registered
derived-control transform. Add a pre-S1 gate requiring the authenticated
SOURCE/LINK inputs and admissions before the S1 deck/open, and a pre-S2 gate
requiring both live-C outcome/declaration/dispatch chains, both NEW admissions,
and the PAD input/admission before the S2 deck/open. The schedule event
and later fit/tensor/optimization receipts must cite that deck receipt, with
checked logical and monotonic precedence. A presealed template hash alone must
not satisfy the lineage.

### 2. The clean-process and reveal barriers are asserted, not evidenced

The public projections and event ordering are well designed, but the runtime
information boundary is not closed. `ResetReceipt` represents “no parent or
childhood text,” “no external capabilities,” and “fresh process” as bare bits
(lines 1324--1328). `AclReceipt` is only a list of
`{capability, object_type, access, passed}` claims (lines 1737--1740). Neither
object binds an enforced launch policy, inherited file descriptors,
environment, filesystem mounts, cache/IPC/network access, broker allowlist, or
an independently observed access transcript. `ProcessBirthReceipt` identifies
a process and runtime, but does not supply that missing evidence.

This matters because `RootGeometry`, complete compiler templates, cell
expected-trace hashes, controls, and hidden validation material all exist before
the child/actor turns. Exact public-input hashes and model-turn continuations do
not prove that those were the process's only inputs. A process with package or
cache access can read the preassigned pair or expected action before the public
reveal and still produce byte-perfect `ModelTurnReceipt`, `ResetReceipt`, and
`AclReceipt` objects. Thus v7 authenticates which continuation was recorded,
but not recovery from only the claimed public evidence or a reset-clean actor.

Required repair: package-bind a concrete capability/launch policy and add a
per-process enforcement receipt tied to `ProcessBirthReceipt`. It must close
argv/environment, inherited descriptors, namespace/mount view, network/IPC,
cache/state inheritance, and the sole allowed frame/broker channels; actor
render inputs must resolve to the complete allowlisted frame sequence. ACL and
reset gates must consume these enforcement objects rather than self-reported
bits. If that boundary cannot be evidenced, Section 0 must drop “reset clean”
and the claim that recovery preceded access to support/template information.

### 3. The causal treatment bytes for S and M remain open-ended

V7 checks that tensors agree outside an `AllowedTensorDifference`, but that
object permits an arbitrary vector of JSON pointers (lines 1483--1499). The
only higher-level restriction is the undefined phrase “row payload fields
permitted to differ” (lines 720--725). Nothing normatively enumerates the
scientifically allowed pointer set for each S1 comparison.

Consequently a materializer could allow a source-row handle, citation, key, or
other actor-visible field to differ with FULL versus SOURCE_DERANGED, or allow
analogous condition-correlated bytes in FULL versus DREAM_DERANGED. The work
receipt would prove fidelity to that presealed bitmap, not that the bitmap
isolates counts for S or link rebinding for M. In that case S or M is the effect
of a bundled row intervention, not the intended component.

Required repair: make the allowed pointer closures literal protocol constants.
For S, hold row handle, query/keys, actions, citations, ordering, surfaces, and
all non-count bytes fixed; permit only the two displayed count payloads and
mechanically forced render/content/tensor descendants. For M, keep handles,
keys, citations, query/mode, unrelated rows, and presentation bytes fixed;
permit only the predeclared link action/destination rebinding and forced
descendants. Retain the already stated S2 rule that every old-deck byte is
identical and the only substantive positive-versus-PAD change is the admitted
NEW row versus grounded PAD. The independent checker must reject a difference
map whose pointer set is broader, even if its bitmap is internally complete.

## Scientific disposition after those repairs

The remaining design is causally coherent at its stated narrow level:

- `S` is a paired response-pattern contrast for an informative 3/1 source row
  versus a truthful 2/2 row, not a general measure of statistical reasoning.
- `M` is a paired contrast for selected authentic link binding versus the
  preassigned nonidentity `pi` rebinding, not DREAM intelligence or a causal
  benefit of the child's selection policy.
- `U` establishes endpoint necessity of the mounted FULL carrier under the
  matched carrier-off interface; it does not identify a general benefit of the
  reader or retrieval algorithm.
- `W`, with the repaired admission-to-deck edge, identifies the paired effect
  of the outcome-selected NEW row rather than grounded PAD while preserving
  the required old link. It supports clean-base cumulative reconstruction, not
  online or in-place growth.
- `R` is a noncompensatory protocol/joint-fidelity indicator, not an additional
  mechanistic effect. Its gate roster must continue to require the relevant
  positive endpoints and registered control failures, not merely structural
  receipt presence.

The cuts, same-handle swaps, source count swap, PAD/no-sleep controls, child
pair/support typing, condition-neutral SOURCE projection, and public
law/codebook/selector logic are otherwise fit for these narrow interpretations.
The LINK and NEW compiler algorithms are noncircular on their declared public
inputs; the unresolved leak is the unevidenced process boundary, not their
mathematics.

The exact Binomial(16, p) tests and 12/16 cutoff are valid **conditional on**
the stated iid root-level seed/noise-vector and identical component-function
premise. Four probes are correctly collapsed within a root; no within-root iid
claim is needed. Adverse filling of invalid/skipped roots with indicator zero
is conservative for the predeclared success-probability estimand. Fixed-sequence
testing controls familywise error without requiring independence among the five
component statistics. These tests establish `Pr(I_component=1) > .5` for the
finite-benchmark generator/noise law, not an average causal effect, deployment
generalization, or any excluded Section 0 claim. Any shared or uncertain
cross-root execution cause must continue to produce no test, as v7 requires.

## Promotion disposition

Do not begin CPU materialization from v7 as written. Repair the three closed
contracts above, regenerate the normative schemas and semantic constraints,
and only then apply the existing two-materialization/independent-checker gate.
No seventh fit, new model arm, GPU work, or broader claim is needed.
