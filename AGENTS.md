# Research-agent operating contract

Preserve the project-level thesis while changing implementation details. For
every material instruction from Rohin that changes the architecture, learning
loop, benchmark, information visibility, acceptance tests, or scientific
claims, use the durable architecture deliberation path before editing the
affected system:

```text
verbatim directive
  -> graph / loop / claim / visibility / test deltas
  -> at least two fresh-context independent interpretations
  -> adversarial cross-critique
  -> adjudicated consensus with every concern/disagreement/test disposed
  -> explicit human ratification of exact bytes and scope
  -> scoped implementation and tests
  -> fresh independent reviewer plus author-side scientific advocate
  -> GPU/scientific-claim gate
```

Use `research_loop/architecture_deliberation.py` and
`research_loop/architecture_intake.py`; every material supervisor workflow
must declare its approved intake and requested scope. Models can recommend,
pause, reject, or request rework. They cannot auto-ratify or infer human
authorization from agreement.

This gate does not block a non-material bug fix that preserves the frozen
architecture, benchmark, visibility contract, tests, and claim boundaries.
Label that work as a non-material repair, add a regression test, preserve
artifacts, and do not expand its scope into a design decision.

Never launch a GPU science run merely because CPU code or model consensus is
green. Satisfy the change's explicit pre-GPU tests and independent-review gate.
An author-side advocate may explain or repair a rejection, but cannot override
the independent review verdict; promotion requires a new bound approval over
the repaired evidence.

## Ratified scopes (human ratification log)

The deliberation path above ends in "explicit human ratification of exact
bytes and scope". Ratifications are recorded here so a restarted agent can
find them without a chat transcript. Operations inside a ratified scope need
no further deliberation before launch; the path still governs material
changes.

- **2026-09-12 05:15 UTC — Rohin Ghosh.** `research_notes/HANDOFF_2026-09-12.md`
  §5 and §5b as committed at `8758c596`, items 1 (write robustness, four
  training seeds, bind check in the runbooks), 2 (consolidation-recipe trial),
  3 stage 0 only (one 32-episode slot-only scout on a plain child; the
  note-after tick change approved), 4 (Meta-TTL-style frozen-reflector
  baseline) and 5 (write pretests on idle GPUs), on nodes 1, 2, 3 and the
  A100 node once onboarded. Adapter rank 8 by default, 16 only after a matched
  joint test. NOT ratified: R6/R7, adapter-seeded children, any parented life
  (preschool lesson/sham arms, the 2×2 deployment), taught cells t/u,
  node-effect bridge fits, R5 lives, cross-node pooling. Full text:
  `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md` §15.
