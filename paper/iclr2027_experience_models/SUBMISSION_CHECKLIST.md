# ICLR 2027 submission checklist

## Current gate status (2026-09-09 PT)

- **Full Experience Models claim:** not established. E0 writer, PCFL M relay,
  `ACTIVE_TEXT_FIXED`, and longitudinal L are still prospective.
- **Clean scientific child:** none currently admitted. CompilerGym-derived
  children are task-exposed; rule-game `bootstrap_v3` is quarantined as
  `DEV_UNVERIFIED_PROVENANCE` until the ancestry guard exists.
- **Architecture/protocol:** compact PCFL + clean-lineage deliberation is
  source-bound but awaits exact human approval before its five-role review.
- **Manuscript:** `main.tex` still contains the earlier CompilerGym/parenting
  headline, unresolved `TBD`/`UNPROVEN` text, and no main figures or frozen
  result manifest. The proposed migration is in
  `PCFL_MANUSCRIPT_MIGRATION.md`.
- **Build:** the official ICLR 2027 style file is not present locally, so the
  upload-form PDF has not been rendered or visually audited.

None of these statuses can be cleared by an exploratory score or by relabeling
a development artifact. Each requires the evidence named below.

Official sources:

- https://iclr.cc/Conferences/2027/AuthorGuidelines
- https://iclr.cc/Conferences/2027/AIPolicyForAuthors

## Do immediately

- [ ] Freeze the intended author set before the September 18 abstract
  deadline; no author can be added or removed afterward.
- [ ] Confirm every author has an accurate OpenReview profile and verified
  email. New profiles without an institutional email may require moderation.
- [ ] Check the 2027 submission quota and reciprocal-review eligibility.
- [ ] Assign one human owner for claims/results, code, literature/citations,
  anonymity, AI disclosure, and final PDF.
- [ ] Create the OpenReview submission early; the abstract must be genuine,
  not a placeholder.

## Before abstract freeze

- [ ] Central claim matches actually completed prospective evidence.
- [ ] Title/abstract do not claim parenting, meta-intelligence, continual
  improvement, connected knowledge, or baseline superiority unless the
  registered gate passed.
- [ ] Two main figures and one main result table exist from immutable inputs.
- [ ] Author order and all profiles are final.
- [ ] Closest-work table includes LEAFE, Early Experience, MemoPilot,
  Evo-Memory/ReMem, and the chosen benchmark precedents.

## Before paper freeze

- [ ] Main text is at most nine pages excluding references.
- [ ] Official ICLR 2027 style is used without margin/font modifications.
- [ ] Manuscript and supplement are anonymous; repository, paths, metadata,
  acknowledgements, self-citations, URLs, and PDFs pass an anonymity audit.
- [ ] Required AI-use statement accurately covers conceptual framing,
  methodology, implementation, interpretation, and writing uses.
- [ ] Reproducibility statement points to exact appendix/code/manifests.
- [ ] Every main number regenerates from one frozen result manifest.
- [ ] Every exploratory/post-hoc number is labeled and excluded from the
  registered headline comparison.
- [ ] All tables state independent unit, sample size, aggregation, uncertainty,
  and missing/failure treatment.
- [ ] Resource accounting includes model calls, generated tokens, accepted
  supervised tokens, optimizer updates, wall time, and GPU time.
- [ ] Limitations distinguish task learning, continual learning,
  learning-to-learn, and one-child parenting claims.
- [ ] Primary-source citation audit and exact related-work comparison complete.
- [ ] Human authors reproduce critical commands, inspect sampled raw artifacts,
  and review the final PDF line by line.
- [ ] Supplement/code bundle is anonymous and contains no secrets, private
  hostnames, user paths, hidden targets, or deanonymizing git history.
- [ ] AI-use disclosure in the OpenReview form matches the manuscript section.

## Final hours

- [ ] Render the exact upload PDF in a clean environment.
- [ ] Check page count, fonts, broken references, clipped figures, and metadata.
- [ ] Upload early and download the submitted artifact for byte/visual review.
- [ ] Keep SHA-256 hashes of the uploaded PDF, supplement, code bundle, and
  result manifest.
- [ ] Confirm the submission before September 25, 23:59 AOE.
