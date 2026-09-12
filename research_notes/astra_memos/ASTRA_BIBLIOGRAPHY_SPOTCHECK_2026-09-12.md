# Bounded primary-source spot check for the staged draft

Main, September12,2026,12:29UTC. Read-only web retrieval while the preservation
fit and independent CPU work continued. This verifies three existing related-work
identities and their narrowly cited mechanisms, not exhaustive prior art,
official code, licenses, reproduction quality or project result claims.

## SEAL

Primary abstract: `https://arxiv.org/abs/2506.10943`.
Version read: `https://arxiv.org/html/2506.10943v2`.
Title/authors match the staged bibliography: Self-Adapting Language Models;
Adam Zweiger, Jyothish Pari, Han Guo, Ekin Akyurek, Yoon Kim, Pulkit Agrawal.
SubmittedJune12,2025; version2September18,2025. Methods describe generated
self-edits, an inner weight-update/evaluation step, and an on-policy outer
learning procedure using downstream performance. Section3/Algorithm1 and
the discussion of ReST-EM support this mechanism description. Raw generated
text fitting alone is not a faithful implementation of that full loop.

## TMEM

Primary abstract: `https://arxiv.org/abs/2606.04536`.
Version read: `https://arxiv.org/html/2606.04536v1`.
Title and the eleven-author list match the staged bibliography: Scaling
Self-Evolving Agents via Parametric Memory; submittedJune3,2026.
Sections3.1–3.2 describe intra-episode fast LoRA updates and SVD initialization;
section5.1's implementation paragraph specifies rank6, FFN gate/up/down
projections in the final four layers, fixed SVD-initialized A and online B
updates. This supports the staged distinction from our existing rank8,
joint-factor, broadly targeted diagnostic writer; it does not validate our
adaptation or justify changing the frozen project base.

## MemSkill

Primary abstract: `https://arxiv.org/abs/2602.02474`.
Version actually checked: `https://arxiv.org/html/2602.02474v1`.
Title and seven-author list match the staged bibliography: MemSkill: Learning
and Evolving Memory Skills for Self-Evolving Agents. SubmittedFebruary2,2026.
The current abstract page also lists version2May24,2026; the staged citation
explicitly identifies its version1 reading, not a claim to have reviewed the
latest version. Section3.3 describes a learned skill-selection controller and
skill-conditioned executor; section3.4's designer evolves the skill bank.
That supports the narrowly stated learning-process connection, not an assertion
that this paper demonstrates our LoRA-only parenting or adult-removal design.

No numerical paper-performance claim was added and no canonical bibliography
was edited. Broader novelty coverage and all experimental efficacy claims
remain separately evidence-bound. The full-page retrievals were used for the
specified paragraphs only; no claim of line-by-line paper inspection is made.
