# R127: fresh-cohort transfer of the canonical parented and unparented learners

This is a new evaluation of preserved historical checkpoints, not a restart,
another live baseline system, a reattempt of old inputs, or an outcome-selected
checkpoint sweep. The full sprint claim remains unproven.

## Fixed question and panel

Does the canonical level-1-seeded learner retain useful changes after multiple
parented sleeps on fresh, parent-free route tasks, compared with its original
frozen weights and the independently sleeping unparented learner?

| Condition | Completed sleep index | Cumulative optimizer updates |
|---|---:|---:|
| Frozen initial adapter | 0 | 0 |
| GUIDED | 2 | 104 |
| UNPARENTED | 2 | 104 |
| GUIDED | 4 | 320 |
| UNPARENTED | 4 | 320 |
| GUIDED | 6 | 424 |
| UNPARENTED | 6 | 536 |

Checkpoint indices are fixed before new evaluation outputs exist. Both learned
arms share the same original adapter state
`d13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f`.
All six consecutive input/output sleep links were checked for each arm before
export. GUIDED C6 made zero updates and preserves C5; this is not relabelled as
another effective sleep. The source and adapters are frozen Qwen2.5-7B-Instruct
plus the existing LoRAs, never a different base.

The prospective panel has 16 deterministic fresh worlds, two goal tasks per
world, using a new R127 namespace. Identifier collisions with canonical
TRAIN/HELD and legacy material/readouts are rejected, never resolved by picking
a different world after seeing results. Every condition sees the same 32 tasks
and initial prompt bytes, in the same order, with empty episode context and no
parent. Later conversation depends on actual environment actions. These are
fresh opaque instances of the SAME two-hop family, not a new task family or an
independent training-seed replication. Existing FINAL tasks are not touched.

## Shared environment evidence and decoding

The original frozen initial child first attempts ROUTE+EVENT generation for
four edges per new world: at most 128 calls. The original deterministic
environment commits valid offered actions and checks that the child's stored
EVENT text describes the receipt it actually received. Only accepted original
raw child records enter the shared read-only store. Missing/rejected events stay
unavailable; worlds are never filtered. Every evaluated checkpoint uses this
same store. Source availability must be reported separately from learning.

Each of seven evaluation conditions starts a fresh process. The original
canonical episode implementation and `rich.SYSTEM` are used with
`rich_contract=False`: no new demand for lengthy explanations. There are at most
six calls per task, 512 output tokens per call, and the historical 8192-token
context limit. Invalid commands end the episode as before. Full messages,
generated text/token IDs, commands, environment responses, and failures remain
node-local. Calls are charged before generation; failed inputs are not retried.
There are zero parent calls, optimizer updates, reflection targets, or writes to
training buffers in this assay. Weight identities are verified before and after.

Maximum calls: 128 source + 7 × 32 × 6 evaluation = **1472**. Maximum generated
token allowance is 753,664, not a target to fill. Expected wall time is roughly
30–60 minutes based on previous protocol readouts; the enforced bound is three
hours and no later than the existing lease minus six hours. This estimate is
not a completion or utilization claim.

## Measures and inference limits

Behavior measures precede outcomes: evidence-access attempts before routing,
repeated reads, supplied/unavailable observations, action validity, full token
use, truncation, and task termination. Semantic use of evidence and post-error
revision remain UNKNOWN unless directly supported; this environment terminates
on invalid commands, so it cannot demonstrate recovery from that error.

Outcomes are secondary. Comparisons are paired by world, not by individual goal
episode, and every fixed contrast is reported. Uncertainty over these 16 worlds
does not account for training-seed variation or establish population-level
parenting superiority. C2/C4 have matched optimizer-update counts, not proven
matched token exposure. C6 dose differs. Parent delivery, target masks, and
training-task equivalence are being audited separately from TRAIN artifacts.
No new scientific claim follows merely from equal update counts or a confidence
interval. Current node-5 lineages are not controlled by this historical assay.

## Allocation and readiness

- Conditional reuse of `ovx` physical 7, UUID
  `GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed`, only after the generation owner's
  completed-task release. Generation continues until that handover; the other
  13 existing L1 allocations and all parenting actors are unchanged.
- Native root: `/localhome/local-rohing/orch_r127_route_transfer_20260915`.
- PLAN SHA256: `12710e14684045bd5e5b31187bac6094ac4e00e65e318a2b6a11d724d0139846`.
- READY SHA256: `e99f4ce44ce8ae5c9534ae4de45b1935f12f797439fafec382a3caeceaa3b5df`.
- Eight local and eight native CPU tests pass, including the actual original
  episode loop with a fake engine, failed-source preservation and no parent or
  optimizer path. All 34 export files and six critical historical runtime hashes
  match. Scanner imports resolve. These are readiness checks, not GPU evidence.
- An initial node-to-node bundle transfer timed out before EXPORT arrived. Its
  partial files are retained as `bundle.partial_transfer1`; a complete transfer
  subsequently passed all hashes. No model input was charged by either copy.

After the owner release, Main's detached supervisor performs fresh privileged
exact-device admission before each process. Raw stays on nodes; the repository
receives source, tests, manifests, hashes and reductions only.
