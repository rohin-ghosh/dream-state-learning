# Note 26 — Fact-Level Salience: design spec (for Rohin's review before build)

**Status: PROPOSED (fork option a). Nothing built until sign-off.**
Motivation: the perfect-salience control (JOURNAL 2026-08-12 evening) proved
per-step salience structurally cannot express fact-selective retention —
fact types co-occur at the same steps. The head must score the *proposition*,
not the moment.

## 1. The oracle: dependency credit (outcome-derived, firewall-intact)

For each emitted fact f in an episode, credit(f) = Σ of positive TD at future
steps whose progress DEPENDED on f's content:

- **recipe edge** ("crafting X requires A and B") ← TD of every successful
  `craft X` step after f's emission (the edge is what a memory would have
  needed to plan that craft).
- **location binding** ("R is found at L") ← TD of every successful
  `gather R` at L and every `move L` that immediately precedes one.
- **decor / counts** ← no dependent steps exist in the DAG ⇒ credit 0 by
  construction (NOT by label: the game's dependency structure, not the
  probe's gist/verbatim annotation, is what zeroes them).

Normalization: per-episode, same normalize_salience port. Cross-episode
accumulation: a fact re-experienced in later episodes sums credit across its
occurrences (this is where cross-episode value shows up — structure earns
credit episode after episode; decor never does).

FIREWALL CHECK: credit derives from (trajectory, TD, DAG-dependencies) — all
gameplay machinery. Probe labels (structural bool, gist/verbatim) are never
read. The keyword_gate canary stays in place to catch collapse-to-action-type;
a new canary should be added: **emission-step-salience** (fact scored by its
step's TD — v1's rule as an explicit baseline row, showing the granularity
delta inside one table).

## 2. The head input: fact-in-context

Embed ctx_text(rec, i) + "\nFACT: {fact.text}" at the fact's emission step
(PASS B-fact; ~33k fact instances — cheaper than PASS B-ctx). Head (keep BOTH
forms for the capacity story): (a) attention-shaped scorer, (b) +1 hidden
layer (licensed by the capacity probe). Same S2 protocol/split; regret target
vs the same floor logic (compute the fact-text-keyed floor first, same audit
method).

## 3. What changes in the write rule

w_f = surprise_f × (1 + β·salience_head(fact_in_context)) — same formula, S
is now per-FACT. felt rows in S3 change meaning accordingly; β=0 still =
stock surprise. oracle_weight ceiling unchanged (fact labels). New row:
felt_depcredit_oracle (true dependency credit, no head) = the NEW ceiling for
what a perfect fact-head could do — MUST land near oracle_weight for the
design to be worth training a head on. **Run this row FIRST on CPU before
any GPU spend** (it's computable from the local backup today).

## 4. Order of operations (if approved)
1. CPU: dependency-credit oracle in game/dag or engine + tests (incl. decor
   credit ≡ 0; recipe credit > 0 iff later craft; cross-episode sum).
2. CPU: S3 row felt_depcredit_oracle from local backup — GO/NO-GO: if it
   does NOT approach oracle_weight, stop and rethink (the credit design,
   not the head, would be wrong).
3. GPU: PASS B-fact cache (~33k embeds, ~15 min).
4. GPU: S2-fact (both head forms) → S3 with fact-head salience.
5. If separation: S4 closed loop with the fact-head condition.

## 5. Paper impact
§4 gains the granularity analysis + dependency credit as the salience
definition (strictly more principled: "what the task will need" now
literally = "what future decisions depend on"). The step-salience story
remains in the ledger as the controlled negative that motivated it. The
capacity probe (0.055/0.83) stays: salience is readable; v2's aperture
question is already answered in the affirmative.
