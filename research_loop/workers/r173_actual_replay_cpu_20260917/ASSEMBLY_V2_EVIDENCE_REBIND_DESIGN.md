# Proposed ASSEMBLY_V2 evidence rebind — design only, not approved

## Present decision: refuse

Do **not** register R173 receipt
`26e9efb519fbc0a8129fd47daa115d71b715a3907ff19e506ca3ee69359de285`
as approved CPU evidence. It is `FAILED_NO_RETRY`, not a replacement for
`NATIVE_CPU_FINAL.json`. No code in ASSEMBLY, OPERATOR, RECOVERY, frozen R168
evidence, or R170 bootstrap has changed. This note grants neither a retry nor
ratification. Main writes and reviews any future implementation.

The original ASSEMBLY refusal is correct: historical `NATIVE_CPU_FINAL.json`
binds plain-context `dcfd1f7f5584867e39356f336f53bb7222aeb535da87d5ecb8f1f0bb59f72feb`
and also records two unused R145 suffix helpers. The receiving guard actually
binds plain-context `b3859e4a45d53fc67c51add5dad8431985ca0adda901389e0206819a56245d92`.
Historical evidence is not full approval of this different source closure.

## Narrow prospective interface

Keep historical evidence and receiving evidence as **separate, byte-bound
inputs**. A prospective V2 could take `historical_cpu_ref` and an independently
reviewed `receiving_cpu_ref`, plus the existing exact old guard/plan refs.
Do not replace the current pinned historical receipt or edit its dependency
map. Do not approve a receipt merely because it names an expected schema or
sets `success=true`.

A Main-reviewed allowlist entry would need exact bytes for:

1. Original guard reference:
   `/localhome/local-rohing/orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json`,
   SHA256 `8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d`;
   original source root remains
   `/localhome/local-rohing/orch_r144_node3_targets_20260916t1515z_2/physical1/source`.
2. Guard-bound original plan reference and **every** original source pin, with
   candidate whitelist exactly `old_guard.source_pins + three_frozen_helpers`.
   No generic extra-file allowance and no suffix/newer plain-context copying.
3. New receiving receipt full-file SHA256, actual receiving runner hash,
   original/adapted test hashes, exact declared test IDs and scope, TRAIN fixture
   hash, execution origin records and candidate-manifest serialization.
   The source-only manifest observed in this failed attempt has SHA256
   `0148d734ad436e189829cc946028e4d04fdccd081ca6375211a6905291f6ac9d`;
   it proves no successful test result by itself.
4. Actual native `cdb542...`, arm `4ff5a3...`, integration `12e512...`, driver
   `43295e...`, and actual receiving dependency hashes, including `b3859e...`.
   Full hashes are already recorded in the immutable receiving receipt.

No such **approved positive** entry is proposed by this sidecar. Its approval
and evidence fields remain unresolved, not inferred from the metadata above.

## Validation rules that must not be relaxed

- Verify the full evidence hash and reviewed scope before consulting its
  result fields. Require actual receiving execution, zero failures/errors,
  complete required test coverage, all skips explicitly handled by the
  established gate, no forbidden operation, immutable candidate bytes, and
  measured module origins/hashes from candidate source. A transport returncode,
  imported module, local unit-test result, or manifest-only receipt cannot pass.
- Preserve all historical evidence and assertions. Do not erase the two suffix
  test obligations, relabel errors as skips, run against workspace dependencies,
  or turn R173's five passes into native replay approval. A future reviewed CPU
  harness would need legitimate descriptor traversal/runtime-library access
  without opening life/evaluator data, and an explicitly resolved suffix-test
  scope without adding prohibited suffix optimization to runtime. That work
  requires new scope; it is not performed or authorized here.
- Separate **test-support provenance** from **loaded runtime dependency
  provenance**. Historical evidence's broad `source_sha256` table is not an
  instruction to add all its files to receiving source. V2 must verify the
  exact three names in frozen `integration.DEPENDENCIES` against a passing
  receiving receipt **and actual newly assembled files**. Also verify every
  observed transitive project file against the exact candidate whitelist.
  Never waive an unknown, missing, or mismatched dependency hash.
- Independently validate every copied old Python byte and all three helpers;
  do not infer full source approval from the subset imported by CPU tests.
  STARTUP is not present in this CPU scratch: Main must separately copy only
  the existing bound STARTUP bytes during source-scoped staging.
- Preserve the sole authorized staged guard delta: original guard source at
  its frozen hash transformed by **exact** `driver.patch_guard(binding_ref)`,
  with the binding reference outside source. Recompute final guard hash and
  source pins. The CPU candidate's original guard hash does not itself approve
  an arbitrary staged guard patch.
- Keep plan edits limited to source/startup paths and allocation-plan hash
  rebinding. Preserve the existing hardwall/lease. Retain Main's source and
  inventory lifecycle, exact physical/life identity, actor/timer/supervisor
  ownership gates, saved boundary/COMMIT verification, source assembly before
  handoff, unchanged whole child row118 OBJECT_REPLAY with four extras,
  current-window next-cycle selection, no rewind/catch-up, and explicit Main
  GO with exact intake and fixed expiry. This sidecar creates none of them.

## Required V2 rejection cases

Main's future tests should refuse: this R173 failed receipt; transport-only or
manifest-only success; a recomputed/self-labeled approval; missing per-test
results; unknown runtime hashes; workspace import leakage; old `dcfd1f7...`
plain-context evidence applied to receiving `b3859e...`; any suffix helper or
other unvetted source addition; native/helper/test mutation; source changes
after tests; a non-exact guard patch; binding inside source; plan changes beyond
paths; wall/intake/GO changes; stale saved-boundary selection; and any attempt
to convert source metadata into saved-state ownership or evaluator admission.

**This is a provenance/integration repair design, not a recipe, scientific
benefit claim, whole-source approval, lifecycle admission, or human ratification.**
