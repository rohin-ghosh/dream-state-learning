# AI-use ledger for ICLR 2027 disclosure

Status: working disclosure record. Human authors must verify, correct, and
approve it before submission. It is not itself an experimental provenance
receipt.

Human-contribution note (Rohin, self-reported 2026-09-06): Rohin originated
and repeatedly revised the core thesis, architecture, terminology, scientific
priorities, parenting framing, and many decisive protocol choices, and reports
more than 100 hours of direct work on the project. He intends to take primary
responsibility for writing/revising the final nine-page manuscript. Verify the
final wording and contribution allocation with every author before submission.

Official policy:
https://iclr.cc/Conferences/2027/AIPolicyForAuthors

## Uses requiring disclosure

Generative AI systems have been used to:

- propose and refine the Experience Models / Dream--LoRA--Think conceptual
  framework and competing hypotheses;
- design, critique, and revise benchmarks, controls, causal graphs,
  information-visibility contracts, acceptance tests, and stopping rules;
- generate and review implementation code, test fixtures, launch scripts,
  analysis utilities, and research documentation;
- inspect experimental artifacts and propose interpretations of positive,
  null, and adverse results;
- generate synthetic benchmark structures and candidate task content where
  separately permitted by the applicable frozen protocol;
- draft and edit manuscript prose, tables, titles, abstracts, limitations,
  and reproducibility materials; and
- search for and summarize related literature, with important novelty claims
  rechecked against primary sources.

## Verification procedures currently used

- Material architecture changes follow a hash-bound multi-role deliberation,
  adversarial critique, human-ratification, scoped implementation, and fresh
  independent-review path defined in `AGENTS.md`.
- Exploratory runs are not promoted into headline evidence when their source
  ancestry, seeds, visibility, or causal controls are incomplete.
- Numerical claims are checked against immutable artifacts and, where
  possible, independently recomputed by source-distinct analysis code.
- Benchmark targets and hidden state are separated from model, teacher,
  writer, and trainer roles through prospectively registered visibility
  contracts.
- External factual and related-work claims are checked against primary
  sources; overlapping prior work is treated as a baseline rather than hidden.
- The final paper will be generated from one frozen result manifest and will
  receive human line-by-line claim, citation, anonymity, and PDF review.

## Known AI-assisted research failures retained in the record

- repeated over-claims from descriptive or post-hoc experimental effects;
- benchmark leakage through identifiers or prompt examples;
- writer and parser dialect mismatches;
- generated validators that agreed while sharing semantic blind spots;
- source files changing after a long-running process imported older bytes;
- incomplete curriculum delivery and behavior probes that did not instantiate
  the advertised environment; and
- designs whose apparent provenance guaranteed structural consistency but not
  independently observed runtime execution.

These failures motivate the independent audit and claim-boundary procedures;
they are not evidence that every remaining artifact is correct.

## Final disclosure fields to complete

- exact product/model/provider names and versions used for each research role;
- which human author reviewed each code path, experiment, analysis, and paper
  section;
- which benchmark/data artifacts were AI-generated or AI-transformed;
- any AI-generated mathematical claim or proof and its independent check;
- final statement of author responsibility using the conference template;
- confirmation that all required uses appear both in the manuscript and the
  submission form.

## Disclosure posture

The final statement should be factual and role-specific, not self-deprecating.
It should distinguish human intellectual control from AI assistance:

- human authors originated and selected the thesis, architecture, claims, and
  research direction; supplied substantive feedback; made final protocol and
  submission decisions; inspected evidence; and are responsible for the work;
- AI systems served as research-engineering, literature, drafting, and
  adversarial-review assistants under those decisions;
- AI-generated prose, code, reviews, or interpretations were not treated as
  evidence merely because another AI agreed with them; and
- independent executions, immutable artifacts, primary-source checks, and
  human review determine the final claims.

Reducing or eliminating AI drafting for the final manuscript changes the
disclosure for that later task. It does not erase earlier AI assistance with
conceptual framing, methodology, implementation, or interpretation, which the
conference policy lists as mandatory disclosure categories.
