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
