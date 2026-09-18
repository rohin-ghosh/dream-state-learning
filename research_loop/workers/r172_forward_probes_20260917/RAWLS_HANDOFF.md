# Author handoff to Rawls — preparation only, September 17, 2026

Reviewer: `01a0b004-e818-73d3-96e7-6f0447428d3e`. This file is the shared-file acknowledgement of `REVIEW_FORWARD.md`; the author does not edit the independent review or its tests. No agent/provider is launched.

## Current status and repairs under development

- Resource-only handoff: `RESOURCE_HANDOFF_20260917T1543Z.md`. R167 release evidence exists, but no new strict admission or execution GO exists.
- Fresh source observations at **15:46:01–04 UTC / 08:46:01–04 PDT**: **4/4 capture controllers live**, 22 enrolled lives, 24 captured checkpoint packages (22 initial, 2 forward), zero capture failures or holds among enrolled lives. Paths: `preparation1/capture_observations/{a100,ovx2,ovx3,a40r}_01.json`. These are source captures, not receiving validation or evaluated calls.
- C5 and repo_reader remain separately held. Existing capture controllers and their frozen source remain unchanged. Local repairs are future receiving candidates, not silent replacement of those deployed source bytes.
- Local candidate repairs now call the unchanged native checkpoint verifier with durable pre-read adapter reservations, require the complete model source closure, pin ON/OFF reservation pairs to identical captures, handle list/dictionary lease UUID inventories, order each life's ready sleeps by checkpoint rather than transfer arrival, and remove the uncharged growth-detection byte in the local reader.
- `validate_cell` deliberately now requires a receiver-read allowance and a complete source closure. The review's positive fixture currently supplies only the runner in its source freeze and no receiving allowance; those fixtures must be updated by the reviewer to model the stronger contract. Do not interpret rejection of an incomplete synthetic source as receiving proof.
- Transfer completeness repair, author regressions, source freeze, and actual receiving CPU are still being prepared. No `ACTUAL_RECEIVING_CPU_PASS`, independent approval, or execution GO is asserted.

## Budget blocker requiring an explicit disposition, not a reset

Before further receiver allocations, 64 durable reservations total **29,806,635,018 metadata bytes**, **15,638,726,536 adapter bytes**, and **52,212,340 discovery bytes** (discovery included in metadata). Global ledger: `preparation1/global_ledger/reservations/`.

The source envelopes reserve capture plus export for four checkpoints per life. They do not pay for extra receiver-side adapter verification and model-loader rereads. Only **1,541,142,648 adapter bytes** remain in the 16 GiB ceiling. No source-envelope refunds, hidden reuse, or uncharged receiving verification will be used. A bounded earliest-ready subset may fit; full 24-life execution readiness must not be asserted without a complete read-cost binding. Any larger byte authorization needs a narrowly explicit amendment from Main, not inferred permission from the 576-call reservation. Calls, tokens, instrument, wall, and old R167 accounting remain unchanged.

## Receiving evidence to follow

The receiver template is the unchanged node2 tree identified in `preparation1/RECEIVER_RESOURCE_OBSERVATION_01.json` (1,106 code/JSON files, 14,052,933 stat bytes). That observation is not receiving CPU proof. Fresh CPU execution will run with GPUs hidden, no model loading and no provider credentials, under a separate precharged metadata envelope. Its immutable snapshot, command, interpreter identity, full test log and exit status will be placed under `preparation1/receiving_cpu1/` and referenced here. It will distinguish synthetic tests from any real-custody join; no synthetic fixture can certify real source custody.
