# Collection-time reasoning gap is not downstream learning utility

2026-09-14, old Builder -> Rohin / astra2. Prospective interpretation advice
only: no changed gates, source pools, targets, allocations, or paper claims.

## Why this matters for the flywheel

The current MATH-RICH protocol requires initial rich successes to exceed terse
successes within each8-task family before scaling. PERSIST-CODE likewise requires
more rich successes for screen survival. Those are legitimate, prospectively
chosen tests of an immediate collection benefit. They are not necessary or
sufficient conditions for learning from the resulting material after sleep.

Let G be the rich-minus-terse collection success difference, and U be the
post-sleep held-behavior difference between a learner trained on admitted
child material and its matched control. G concerns generation under two
instructions; U concerns the effect of a parameter update on later behavior.
There is no logical implication G=0 => U=0, or G>0 => U>0. For example,
both generators might solve the same tasks, yet one emits an admissible
operation sequence whose learning utility has not been measured. Conversely,
extra inference can improve answers without producing useful future targets.
This is a counterexample to an inference rule, not a claim about our data.

**My recommendation:** retain all current decisions and failures exactly, but
do not turn an initial rich-over-terse gap into a universal prerequisite for
every future corpus-utility experiment. The original G4 question requires
testing the write's downstream utility, not inferring it from collection.

This does NOT rescue current zero-success/zero-qualified-row screens. The
newly published MATH-RICH reduction also is not a gap-null: it reports29/32
initial rich successes versus5/32 terse,19 admitted rows, and no family meeting
the separate8-row scale threshold. This writer has read that reduction and
worker journal, not independently re-reviewed all64 nonterse rows. Its current
scale decision remains unchanged. No tiny fit or old-row recycling is proposed.

## Narrow primary-source check

**STaR:** Eric Zelikman, Yuhuai Wu, Jesse Mu, Noah D. Goodman,
*STaR: Bootstrapping Reasoning With Reasoning*, arXiv2203.14465v1.
Sections3.1–3.2 distinguish generating/filtering correct rationales from
fine-tuning on them. Section4.3 Table1 reports GPT-J GSM8K accuracy3.0 for
few-shot direct answers,3.1 with few-shot rationales, and10.1 after STaR without
rationalization. These are the paper's model/settings, not predictions for
Qwen/LoRA. Rationalization additionally reveals the known answer during
generation; that is a different provenance/visibility treatment and must not
silently enter our child-only, no-gold-feedback recipe. The ordinary bootstrapping
path already starts with rationale demonstrations, unlike instruction-only
collection here. A small immediate rationale gap and a later training result
are separate measurements in the paper.

Primary full text inspected: `https://arxiv.org/html/2203.14465v1`.
Existing project bibliography key: `zelikman2022star`.

**ReST-EM:** Avi Singh et al., *Beyond Human Data: Scaling Self-Training for
Problem-Solving with Language Models*, arXiv2312.06585v4.
Section2/Algorithm1 samples model outputs, filters using a binary correctness
reward, and performs supervised fine-tuning. Its acceptance rule is positive
reward, not a measured rich-versus-terse prompt advantage. Sections3.1–3.2 and
AppendixA evaluate subsequent problem-solving and discuss sampling/filtering
budgets. This supports separating collection and learning tests; it does not
prove that our semantic rubric, records, continual updates, or parenting will
work. Outcome-only filtering in that method is not permission to remove our
grounding/provenance requirements.

Primary full text inspected: `https://arxiv.org/html/2312.06585v4`.
Existing project bibliography key: `singh2023restem`.

## Prospective decision boundary, not an executable protocol

For a genuinely new authorized pool, separately declare (a) collection yield,
content/provenance qualification, diversity and cost, and (b) downstream
held-behavior utility after a real saved/reloaded update. A collection-gap
screen may remain a useful efficiency filter; name it as such. Existing
minimum-corpus and content requirements are NOT waived by this memo.

If a future pool qualifies but rich and terse collection outcomes tie, the
orchestrator can explicitly decide whether a newly declared matched utility
test is worth its cost rather than concluding the material cannot teach.
FULL versus identical-input new-label loss-off tests new supervision utility;
it does not isolate the superiority of rich targets over terse targets.
That stronger claim needs its own prospectively matched target-form comparison.
Neither result alone establishes parent-free internalization, repeated adult
learning, or improving learning efficiency. Those remain later campaign tests.

No new fit is requested now. No result-gate redefinition, source answer
rationalization, unknown-row admission, or canonical-manuscript edit occurs.

## Local source bindings at inspection

- `research_notes/analysis/orch_math_rich_20260914_protocol.md`: SHA256
  `c8e641bf81b95a04433dc206c2400375fab467d5322b5efa0e495f01c7fb458e`.
- `research_notes/analysis/orch_persist_code_protocol.md`: SHA256
  `83e46d849725914880fb4b78befba085ef29e191de073d7f118a4a4ff7c256b0`.
- `research_notes/analysis/orch_persist_math_protocol.md`: SHA256
  `e8682dd53ee0987cf1a766ede1d2ab1a022eda09e652d2299ee41095a474269e`.
- MATH terminal reduction and22:18:43UTC worker journal are inherited from
  merge commit `a48f250e`, not a new independent outcome certification.

Literature scope: the named method/experimental sections only. No new broad
novelty search, official-code/license review, or claimed implementation fidelity.
