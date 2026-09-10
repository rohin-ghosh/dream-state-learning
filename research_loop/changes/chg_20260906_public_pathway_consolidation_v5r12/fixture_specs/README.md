# PPC5r12 fixture proposal

This namespace contains proposal bytes and proposal-source validators only. It
confers no architecture ratification, fixture materialization or execution,
model or GPU authority, conformance result, seal, scientific claim, or release
authority.

PPC5r12 preserves the PPC5r11 positive repairs and closes the three blockers
in the independent PPC5r11 static audit:

1. Both source-distinct T14 replay implementations reconstruct 24 semantic
   predecessor rows. The eight presence-receipt roles omitted by PPC5r11 are
   now consumed, and each role's `present` fact changes both replay relations
   and the terminal decision. Canonically re-encoded and rehashed
   `present:false` probes fail rather than pass.
2. The T07 receipt's `dispatch_scope` is consumed by both replays and must be
   exactly `ALL_REGISTERED_ROWS`. The full local dispatch registry is bound by
   canonical identity, self-hash, row count, row order, role/cardinality,
   consumer stages, and row content hashes. Undeclared scopes and independent
   mutations of each registry property fail the proposal machine.
3. Every source preimage used by authors and validators is vendored under
   `source_inputs/`, raw-hash bound by `SOURCE_INPUT_MANIFEST_RFC.json`, and
   included in `PROPOSAL_CONTEXT_RFC.json`. `validate_local_closure.py` copies
   only this `fixture_specs` tree to a temporary root, installs an inherited
   Python open guard that denies access to the original repository, and reruns
   both authors plus every independent proposal validator byte-for-byte.

The proposal still defines 58 content-addressed reducer vectors covering
T04--T14 and 1,113 concrete reducer input rows. Every reducer law has a closed
facts-only input schema, a closed parameter/output schema, a deterministic
executable proposal reducer, exact local source-pointer hashes, and no
executor-visible expected output.

The already-confirmed repairs remain: DREAM derives render equality from
bound bytes; T08 derives causal/noninterference outcomes from paired upstream
facts; T13 validates its concrete technical package and performs a Kahn walk
over source-bound authority stages; and T14 consumes two independent replay
relations plus six concrete self-hashed final carriers. Release exclusion is
semantic over typed values rather than dictionary-key spelling.

The legacy 7,629-case PPC5r9 universe and its authors/oracles are quarantined
by their four declared SHA-256 identities. PPC5r12 never opens those files;
the validator rejects matching bytes or embedded identity hashes under any
name or nesting within this proposal. The sole replacement vector remains
unmaterialized: P=465, N=2,467, Q=55, 2,987 logical cases and 5,974 planned
independent executions.
