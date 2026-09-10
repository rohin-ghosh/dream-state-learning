# Private typed-action structural provenance fixture v3

Status: proposal only; no architecture intake, deliberation, ratification,
implementation, fixture execution, model call, tool execution, or GPU run has
occurred.

## Decision

v3 takes the simplifying branch allowed by the authoritative v2 consensus. It
does **not** add runtime spies and does **not** claim actual runtime provenance.
It specifies a deterministic structural fixture: six declared records whose
bytes and relations can later be rendered and checked. Actor labels identify
the producer prescribed by the fixture grammar; they are not observations that
a process ran. `FUTURE_PC_ACTUAL_CONSUMER_PROVENANCE` is deliberately outside
this change and requires a new ratified live protocol.

The maximum possible v3 claim is:

> Under the registered synthetic fixture grammar, the accepted and rejected
> six-record artifacts are internally byte- and relation-consistent with one
> declared request, response envelope, parse decision, and either one declared
> pure transition or one parser-authored non-dispatch receipt.

Nothing here supports model consumption, authorship, intention, real dispatch,
actual syscall order, secrecy, answer blindness, learning, memory, behavior,
performance, scaling, or the Experience Models thesis.

## Closed design

1. `contract.json` freezes canonical byte rules, the exact response envelope
   and extraction interface, six-record accepted/rejected schemas, a total
   first-error order, structural oracle, publication state machine, platform
   and threat model, and the exact claim ceiling.
2. `manifests.json` freezes every normative component algorithm and the
   cross-manifest equality requirements. Later implementation source hashes are
   evidence fields, not values invented in this pre-implementation proposal.
3. `fixtures.json` contains exact success/rejection inputs and exact expected
   semantic records, plus closed mutation recipes. It is explicitly synthetic
   and may be answer-bearing.
4. `metamorphic_spec.json` defines a 2^32-case generator. After both validator
   sources are frozen, their hashes and the normative-bundle hash select the
   cases. Hash allowlisting of the two golden artifacts cannot satisfy PC17.
5. `acceptance_tests.json` registers PC0, retained PC1-PC9, and PC10-PC17.
   All except the pre-implementation portion of PC0 remain future work after a
   releasable consensus and exact human ratification.
6. Publication, if later authorized, is supported only on the exact platform
   contract. “Immutable” means collision-safe creation plus post-commit
   mutation detection; it never means a same-UID/root adversary cannot modify
   bytes.

## Authority order

The complete normative bundle is authored and hash-bound first. Next, but not
in this task: two fresh-context interpretations, cross-critique, adjudicated
consensus, and explicit human ratification of the exact bundle-manifest hash
and sorted scope. Only a releasable consensus plus that ratification can permit
scoped CPU implementation. PC1-PC17 and fresh review must then pass before the
narrow structural claim can be stated. No stage grants adjacent authority.

## Stop

This package stops before `architecture_intake init` and before any
deliberation. The exact next command sequence is recorded but not executed in
`proposal_workflow.json`.
