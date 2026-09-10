# PCFL v2 fixture-authority adjudication

**Date:** 2026-09-02  
**Status:** advisory authority reconciliation; no intake, implementation, CPU,
model, network, GPU, or claim authority

## Ruling

The fresh semantic audit correctly distinguishes unexecuted receipts from
underspecified tests, but it overreaches by requiring every incidental literal
schema witness before architecture ratification. That demand is rejected.

`AGENTS.md` fixes this order:

```text
exact architecture / visibility / test proposal
-> independent deliberation
-> exact human ratification
-> scoped implementation and tests
-> fresh review
-> pre-GPU gate
```

The pre-intake proposal must freeze every **scientifically material** test
choice: tested schema branch, phase and topology, model-visible fields, causal
ordering, dimensions and caps, mutation class, expected acceptance or
rejection, failure routing, registered roots/rows, gate equation, denominator,
and claim consequence. The current `static_fixture_contract.md` is required to
do that exhaustively.

It need not freeze arbitrary **incidental implementation witnesses** such as
which harmless Unicode scalar realizes a minimum string, which nonsemantic ID
literal is used to exercise a regex, or the serialization address of a
temporary Stage-0 object. Those bytes are neither model-visible scientific
inputs nor experimental assignments. Requiring them now would implement the
test suite before the human has authorized implementation and would add no
identifiability.

## Post-ratification obligation

If the exact proposal is later ratified, implementation must materialize a
complete fixture catalog before executing Stage 0. That catalog must:

1. bind every named fixture and mutation in `static_fixture_contract.md` to
   literal input bytes, expected result, schema/reducer/runtime version, and
   source hash;
2. contain no new scientific condition, model-visible field, allowed value,
   threshold, branch, retry, or interpretation;
3. be hash-frozen with the implementation and executable identities;
4. pass the complete Stage-0 suite; and
5. receive fresh independent review at T17 before any GPU/scientific call.

If materializing a witness requires choosing or changing a scientific value,
the implementation must stop and return to a new architecture intake. A
fixture catalog or passing receipt can never silently repair a proposal-level
semantic omission.

## Disposition of the fresh audit

- **Accepted:** stale change-level actor routing and hashes must be repaired.
- **Accepted:** G04 must bind the complete raw-A-read -> decisive-PREDICT ->
  terminal-REPLACE evidence chain, including the charged candidate parent.
- **Rejected as a pre-intake blocker:** absence of literal incidental min/max,
  regex-witness, temporary receipt, and rendered-test bytes.
- **Retained as a pre-GPU blocker:** absence, failure, or unreviewed mutation of
  the realized fixture catalog and execution receipts.

This ruling narrows process overhead without weakening the experiment. It does
not claim the proposal is otherwise ready; a new whole-bundle audit must still
pass after G04 and change-level reconciliation.
