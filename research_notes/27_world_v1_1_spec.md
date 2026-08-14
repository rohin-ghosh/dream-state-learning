# Note 27 — World v1.1 spec: making credit ≠ type (response to reversal #6)

**Requirement (from the audit):** the generator must contain BOTH
(a) non-structural facts that are causally load-bearing, and
(b) experienced structural facts that are never used —
so that "keeps what the task needs" and "keeps facts of type recipe/location"
are different behaviors, measurable apart.

## Changes

1. **Goal pools (unused structure).** Each world draws episode goals from a
   deterministic ~half of its recipes (world-seeded). Consequence: recipe
   edges off the pool's closure are experienced (see #2) but never used.
2. **Recipe experience via failed crafts.** The engine already *teaches*
   recipes through informative errors ("requires A and B"); v1.1 emits a
   recipe fact (kind="recipe") on failed attempts too. Consequence:
   experienced-but-unused recipes exist; recipe credit is no longer
   emission≡use. (Also makes the error-mining channel an honest, labeled
   part of the epistemics instead of a leak.)
3. **Hint-bearing decor (load-bearing details).** Per world, a subset of
   decor words is bound to resource types (world-seeded map, e.g.
   "mossy → raw_4"); sites holding that raw receive the bound word. The
   hint map is stated in the manual (it is itself a structural relation);
   the decor observation ("site_3 looked mossy") is verbatim-class BUT
   causally usable: knowing it (plus the map) locates a resource without
   visiting. Consequence: some decor facts earn dependency credit.
4. **Credit v2 (felt/depcredit.py).** Takes the World. Strict inequality
   (no self-credit at emission). Uses: recipe ← later successful craft of
   that item; location ← later successful gather of (r@s); decor ← later
   successful gather at s of a raw implied by its hint word; count ← none
   (pure verbatim junk is retained BY DESIGN — the dissociation measure
   needs junk). Prints **AP(credit → structural)** every run — the leakage
   canary; target ≈ base rate (was 0.975 in v1.0; that number is the bug).
5. **Zoo additions:** `fact_type_regex` (three string matches — the cheap
   competitor the audit says reviewers will build; it replaces label_ref as
   the honest type-baseline and label_ref keeps its "reference" role),
   `frequency_weight` (stream-frequency of the fact text) at the GPU tier,
   `random_write` restored to S4 arms.
6. **_FAKE_TPL check:** verify fake-fact floor templates are not trivially
   separable from real facts in hash-embedding space (report cosine stats).

## What the rerun must show for the thesis to stand
- AP(credit→structural) ≈ base rate (leakage canary green).
- felt > fact_type_regex, SIG — the claim that died tonight, now testable.
- felt vs label_ref becomes a REAL comparison (target ≠ label).
- Head AUC on the new target (expect lower than 0.98 — that number was
  type-detection; honest readability of use-vs-nonuse within type is the
  question).

## Order of work (against lease end Fri ~8-11 PM)
Engine+dag changes + tests (tonight) → CPU validation incl. new canaries →
regenerate S1 v1.1 (7B, ~7 h, Thu) → fact cache + credit v2 labels →
S2-fact → S3 (full zoo) → S4-reduced with random_write → backup.

## Metric implication (added pre-implementation)
With hint-decor, type and utility DISSOCIATE inside the verbatim class — so
the gist/verbatim dissociation score would penalize a policy for correctly
retaining usable decor. v1.1 metrics: PRIMARY = use-weighted retention
(AP of retention vs held-out dependency credit on eval streams) + S4 win
rate; gist/verbatim dissociation becomes the descriptive memory-profile
(the psychology port), no longer the policy scoreboard. Same credit
definition train vs eval, different data — standard held-out evaluation;
the firewall concern (benchmark labels training the head) remains satisfied:
nothing trains on structural/gist labels.
Also banked: 14B replication on v1.0 target (attn AUC 0.978, felt−surprise
+0.111 t=7.9) — meaning deferred to v1.1 relabel.
