# Independent review: declared non-bitwise pending-sleep restart

2026-09-19 UTC. Review scope: the 112-line CPU-only `prepare` helper, its
14 tests and `DECLARED_RESTART_ACTUAL_RECORDS.json`. No runtime integration,
node access, tensor/model execution, source mutation or launch occurred.

## Scoped verdict

**PASS as a non-authorizing, data-preserving declaration over supplied records.**
No row/working-state copying defect or false bitwise-resident-continuity claim
was found. **Do not treat this PASS as proof of unchanged recipe, complete tail
selection, or original admission.** Those bindings are not established by
this helper and must be enforced before a consumer executes the contract.
These observations do not block Banach's separate clean-caption CPU port.

The exact pending `resume_state` is deep-copied, including rows, working state
and pending marker (`restart_contract.py:96`). Old rows, sleep frontier,
sleep receipts, experiment and wall are compared (`:58`, `:62`, `:64`, `:65`,
`:67`, `:69`). The helper does not clear pending, modify inputs, rewrite old
records, launch, or execute generations/tools. It correctly names the RNG
origin as the old COMPLETE rather than post-generation resident RNG (`:100`),
disclaims exact continuity (`:104`), and requires separate compute accounting,
binary/tail verification, preservation and admission (`:102` through `:111`).
Those requirement flags are declarations, not evidence of completed execution.

## Concrete findings / required consumer bindings

### 1. Unchanged recipe is not validated by the helper

Location: `prepare`, `restart_contract.py:40`, `:44`, `:78`, `:97`.

`new_presentations` is caller supplied and checked only for a positive integer
and capacity for the supplied UPDATE count. It is not compared to a pinned
original plan or SLEEP_RECIPE. The synthetic fixture's **16 presentations can
be changed to 2** and `prepare` accepts: planned restart work becomes **6 rather
than 48 updates** for the same three pending rows. This is an actual accepted
input variation, not a mutation of the real C0/Astra7 records.

Row-policy input is similarly checked against a literal, not independently
bound to the source/plan that will run. Anchors, rehearsal, loss implementation
and other recipe settings are not inputs to this helper. Therefore its
`unchanged_positive_presentation_count_required` label does not prove unchanged
training policy or budget. The declared contract may be useful, but the stronger
claim requires an external exact binding.

Before execution, compare the proposed recipe to original-authority-pinned
plan/source/anchors and the authenticated original SLEEP_RECIPE; include their
bindings in the approved selection/contract. A separate validator is acceptable;
no live/helper mutation is requested by this review. Regression: altered
presentation counts in either direction, wrong original recipe, changed
anchors/source or policy must fail while original pins remain fixed.

### 2. Supplied records are internally hashed, not a complete authorized selection

Location: `authenticate`, `restart_contract.py:22`; `prepare`, `:42`, `:50`,
`:78` through `:88`, `:101`, `:108`.

The helper checks self-hashes, same journal ID, increasing indices and
consecutive optimizer steps. It has no externally pinned original head,
complete chain/intent inventory, exact selected-record authority or life↔guard
binding. **Supplying only the first of four known UPDATEs is accepted** and
reports `recorded_uncheckpointed_updates=1`; relabeling the same fixture between
the two allowed life names is also accepted. No old bytes need to be altered
to truncate the supplied update list.

A separately resealed changed history also passes, with a different record
and contract digest. This is not a hash collision or evidence of actual data
loss: it illustrates why self-hash validation cannot establish original-source
authority. The returned state is an exact copy of whatever pending record was
supplied. Authenticity must come from independently pinned selection/chain.

The existing `full_journal_tail_verification_required=True` properly leaves
this work outstanding; do not bypass it. The consuming gate must bind all
records through the exact original head, the full UPDATE subsequence, exact
life/root/journal/source/plan, and any non-UPDATE tail/mailbox/sidecar state and
partial-publication manifest. Regression: omit a known suffix, select the
wrong head/life, or substitute a resealed pending record under fixed authority
and require refusal. This prevents understated durable compute or stale state
from becoming an executable contract. Actual unknown unjournaled compute must
remain separately labelled unknown, as the helper already does.

### 3. Real-record receipt supports selected-data compatibility, not full attestation

Location: `DECLARED_RESTART_ACTUAL_RECORDS.json:9`, `:38`, `:63`.

The compact receipt publishes contract hashes, selected record references,
state hashes and counts, but not the full contracts, `new_presentations`,
helper SHA, source/plan selection or invocation identity. Thus this review
cannot independently recompute its contract digests or prove which exact
helper bytes produced it from this receipt alone. Attach the exact producer
source/invocation and full canonical contract (or immutable pinned location)
to the eventual admission evidence. No need to copy large journals off-node.

I cross-checked its COMPLETE/SLEEP_REQUEST index+hash, preserved-state hash,
durable optimizer steps, retained/pending row counts, UPDATE counts and row
source sets against independent earlier sidecar receipts: **all match**.
C0: 6631→6660, step8412, rows444/frontier441, 48 durable UPDATEs.
Astra7: 7750→7776, step9644, rows453/frontier450, 29 durable UPDATEs.
Both explicit no-continuity/no-execution flags are correct. Its 1.554s is
contract checking, **not** full recovery or bounded admission timing.

## Tests and remaining scope

- Independently ran all **14 existing CPU tests: PASS**.
- Five pinned review probes: changed presentation count accepted, known UPDATE
  suffix omission accepted, allowed-life relabel accepted, resealed history
  accepted with changed digest, and exact-state-copy/no-aliasing PASS.
- Cross-receipt selected-boundary/state/count consistency: PASS.
- No claim to have run crash/restart integration, binary audit, checkpoint-tail
  runtime, GPU tests or confinement admission. Missing strict-replay tensor/RNG
  witnesses are **not** a rejection of this explicitly non-bitwise policy.
- A consumer still needs original failed-artifact preservation, exact partial
  handling, a unique new checkpoint path and epoch, separate compute accounting,
  and no historical external-action replay. These are deliberately not actions
  performed by the pure helper; their absence here is not a new runtime bug.

## Exact reviewed bytes

Main-worker paths are under
`research_loop/workers/post_recovery_node2_sleep_20260919/`:

- `restart_contract.py` SHA256
  `ce7fda824274563985a66020ca5f3b0afb59865f13adc00af304acf1111d67a1`.
- `test_restart_contract.py` SHA256
  `baf2771b55e7584aa8bd061360aca4c8a96fb7e380aeb029b112c14139c626eb`.
- `DECLARED_RESTART_ACTUAL_RECORDS.json` SHA256
  `189da19fe15cae2f5f8ea56cff50070e787fccfda904c2bc31d2cf30be2df836`.

Local reproducible review artifacts, in this directory:

- `review_restart_contract.py` SHA256
  `007d0afa09513d3206cf07082c21877af218313b133ee23581f74985dc18cfb0`.
- `RESTART_CONTRACT_REVIEW_PROBES.json` SHA256
  `1d1d65f79d636818148a8cc0ab8c96e574fb00f2214f913f0e37524bd5e5bb29`.

Reviewed files retained their hashes after testing. This review changes only
new sidecar review artifacts, not main's helper/tests, any runtime, or any node.

## Final V2 addendum — 2026-09-19 UTC

**PASS at declaration level; both reported V1 gaps are closed.** No remaining
declaration-level data-loss or continuity-overclaim issue was found within the
stated scope of externally selected original records and a non-authorizing
contract. The historical V1 findings above remain preserved, not applicable
as unresolved defects in the exact V2 bytes reviewed here.

### Verified fixes

- `restart_contract.py:78` authenticates SLEEP_RECIPE and TARGET_ELIGIBILITY.
  `:81` binds the requested dose, pending-row count, new-only recipe and zero
  rehearsal selection. `:84` and `:88` require the original all-authentic policy,
  exact ordered pending-row source inventory, no semantic filters, no excluded
  rows, and no raw modification.
- `restart_contract.py:93` requires the supplied UPDATE list to terminate at
  the explicitly supplied original head. `:95` verifies consecutive record
  indices and previous-hash links from SLEEP_REQUEST through recipe,
  eligibility and every UPDATE. Optimizer-step continuity remains checked.
- `restart_contract.py:108` includes recipe, eligibility and old-head references
  in the contract digest. `:127` explicitly requires fresh filesystem-head
  agreement. Exact pending-state deep-copy and all non-bitwise/RNG-origin,
  separate-compute and no-execution declarations remain intact.

Independently reran **18 CPU tests: PASS**, including dose16→2, trailing UPDATE
omission, middle omission and wrong recipe-chain refusal. The V1 archive at
`history/restart_contract_v1.py.txt` matches the reviewed V1 SHA exactly.

Without contacting the node, cross-checked V2's actual-record receipt against
the prior independent evidence: COMPLETE, SLEEP_REQUEST, recipe, eligibility,
old head, preserved-state hashes and durable UPDATE counts all agree. C0 binds
6631 / 6660 / 6661 / 6662 / 6710 with **48 UPDATEs**; Astra7 binds
7750 / 7776 / 7777 / 7778 / 7807 with **29 UPDATEs**. Both retain three pending
rows and their original state hashes. The new receipt pins the exact V2 helper
SHA, resolving the prior missing-helper-byte binding.

### Scope retained

This remains a declaration, not a filesystem authenticator or launch grant.
Original-admission authority must supply the actual life/root/source/plan and
head selection; a caller-chosen alternative self-consistent head is not thereby
authorized. Full-journal/intent validation, original checkpoint binaries,
failed-artifact/partial preservation, executable epoch accounting and fresh
confined admission remain explicitly external requirements, not reopened
declaration defects. Main's fresh directory-head observation was **not** repeated
by this reviewer. The compact actual-record receipt still does not include
full contracts, so their reported digests were not independently recomputed.
No all-in recovery timing, current node state or LOADED claim is made.

### V2 evidence pins

- `restart_contract.py`:
  `050bdf3de64d213330af37b7f87da328ca5a826badc42e0497f4544fe44a9e95`.
- `test_restart_contract.py`:
  `6a584d70bc8dfcfad01d6a13e2c31f6cc23dc07f113929ab663ca8c825f8873f`.
- `DECLARED_RESTART_V2_ACTUAL_RECORDS.json`:
  `5acbd41d700d657aad9d9a44594e6e39579543731e71f77ac4a259f25b46c9c9`.
- New local `RESTART_CONTRACT_V2_REVIEW_CHECKS.json`:
  `96ab7201de5f41ecf8141ef47f6a420d34cf9e9d183c7c6474be67926e740876`.

No main/runtime files or node state were changed; only this review was appended
and a new local consistency receipt was written.
