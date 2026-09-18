# Full-target content classification

This is a single-auditor semantic annotation of the complete original child target,
not a keyword or first150-character classifier and not a quality/accuracy score.
Source stage, retention, and actual training presentations are determined separately.

- META_INTENT_COMPLIANCE: promises, plans, readiness declarations, generic compliance,
  retrospective success claims or intended review, without delivering the promised
  story/calculation/conceptual answer in this row. Claiming an excerpt exists is not
  delivering it. Merely saying a calculation was solved is not a worked calculation.
- SUBSTANTIVE_CONTENT: an instantiated narrative, calculation/code, or actual
  conceptual/direct answer. Incorrect arithmetic, malformed code and script drift
  can still be substantive content; correctness/execution is not inferred. A brief
  introduction or explanation of a delivered object does not by itself make it mixed.
- MIXED: substantive content together with a separately developed process-intent,
  compliance or self-evaluation passage. Keep the category separate; never assign
  all its presentations to the pure-meta or pure-content category.
- UNCERTAIN: the full row supports competing interpretations that cannot be resolved
  confidently under this rubric. Record alternatives and do not force a binary label.

Metacognition as a topic is not automatically meta-intent: a concrete answer about
working-state versus adapter storage can be substantive. Conversely, readiness and
claimed completion without the requested artifact remain meta-intent. Quoted old
story text is still content in the actual target, not evidence of a new achievement.

Counts use unique source-response document hashes. Presentation weighting uses actual
UPDATE events reconciled with completed SLEEP_COMPLETE receipts, not scheduled dose.
Raw original targets remain private; public previews are their exact first150 Unicode
characters, without normalization, repair, whitespace stripping or inferred suffixes.
Classification disagreement is methodological, not evidence of a causal mechanism.

For legacy rehearsal targets, read/list-only tool requests are classified META
(observation/review intention), not as substantive just because they use JSON.
Repeated familiar formulas within a claimed-completion/investigation-plan passage
do not alone count as delivered proof. Explicit instantiated numerical answers,
result tables and proof transformations do count, even if repeated or incorrect.
This boundary can be debated; row-level rationales are retained rather than hiding
the single-auditor judgment behind a mechanical rule.
