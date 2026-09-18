# R232 exact-initial frozen sibling — source-bound status

## Outcome at September 18, 2026, 10:33 UTC

| Arm | Assigned GPU | Actual LOADED UTC | Initial parent REQUEST UTC | Final native state |
|---|---:|---|---|---|
| R231 learner | 0 | 10:13:23.009538 | 10:13:23.026946;1797 tokens | Natural EXIT1 10:28:21;two sleeps/96 updates |
| R232 frozen sibling | 1 | 10:23:37.453606 | 10:23:37.470198;1807 tokens | Natural EXIT1 10:30:33;two sleeps/zero updates |

Neither native is currently live. Neither was signaled or restarted by this
operator. Both retained exact states, every raw row, inbox, journal and saved
checkpoint. Reserved scorer GPUs2/3 and all unrelated lives were untouched.

## Exact pairing

The sibling copies **only R231's saved initial checkpoint**, not its current
weights: same rank8 LoRA tensors, optimizer0 with empty state, saved RNG bytes,
seed231180, initial BIRTH state, six-paragraph prompt, model, decoder,
context4096/generation512, tools and original source files. The original205
Python files are byte-identical; the sibling adds one zero-update wrapper.
Checkpoint metadata relocates only the two private filesystem path fields.
The new journal has its own identity; all initial model payloads are identical.

Original birth SHA256:
`7362d19a950779633067c81bacd0f0942e4243bbd62cf029463b61c264d66191`.
Initial adapter state SHA256:
`04341ab86f5f98718bc53218166537ecc20fc7d5053f3ed47cc0fcdda918f5d0`.
Initial optimizer/RNG file SHA256:
`6e6b3af8a0ec413cc36f5aeb50d68f0c023cd2a5d0326af3a9772dba3a9d8e37`.

LOADED stagger is **614.444068 seconds**. The learner had completed **73
UPDATEs before frozen LOADED**, independently counted using UPDATE finish
timestamps. This is not a simultaneous birth experiment and does not establish
causal isolation. Parent messages, request token counts, output histories,
throughput and available wall time differ and are measured, not assumed equal.

## Frozen sleeps and strong parenting

THINK, ACT, LEARN, technical target encoding, state consolidation, compaction,
checkpointing and readouts use the same native paths. Only gradient/optimizer
training is disabled. `optimizer.step` explicitly fails closed. Frozen sleep
receipts honestly report zero presentations, token training exposures and
optimizer updates; the nominal16x schedule is recorded as not executed.
There are no semantic target exclusions in either arm.

Two frozen sleeps completed with zero UPDATE receipts. An independent CPU
check after sleep1 found all **392 adapter tensors bitwise identical** to the
initial checkpoint and the saved optimizer still empty/step0. Generation RNG
may advance; freezing weights does not mean freezing sampling RNG or history.

Both CPU parents use the same source-bound Astra policy, model, low reasoning
effort,90-word message ceiling,4096-token provider completion ceiling and
stage0/1/2 opportunity after every actual ACT. Replies are genuinely generated
from each child's own output; corrective messages are not copied between arms.
The original CPU parent was rebound at an idle turn boundary preserving its
ledger; no learner process was affected. Parent-call receipts and budget
differences are in the manifest. There is no automatic dose change.

## Explicit later exploration epoch

Revision `f236ffa32` adds exactly one paragraph to the original six; neither
birth was retroactively rewritten. Identical source-bound **Tool/environment**
messages were published at 10:25:55.874550 and10:25:55.875947 UTC. No human or
parent reply was impersonated. The same revised document became the standing
brief for both parent policies, with no copied corrective text.

- Frozen: exact payload rendered in **THINK REQUEST37**, SHA256
  `d8b9a4997df52026f5952412acaf52653c673e898d5c88a223759844eef264e0`,
  at **10:27:00.207427 UTC**,3047 prompt tokens.
- Learner: input delivered and registered, but **no epoch REQUEST** exists.
  Do not label publication/registration as model consumption or learning.
- Original six-paragraph birth pins remain intact. The later epoch is a masked
  environment input, not a retroactive replacement or a new permanent pin.

## Actual blocker and preserved limits

Both native exits are the existing `R203_CONTEXT_BUDGET_BLOCKED` path:
`protected_input_or_pinned_state_cannot_fit_without_silent_loss`.
The learner recorded3637 tokens and the frozen sibling3600 against3072;
their final states have pending=null, six rows, frontier6 and two complete
sleeps. No generation was silently cropped. This is a context-fit failure,
not an OOM, normal wall termination, or evidence of a learned causal mechanism.
The fixed original wall remains14:00UTC; no lease or audience was changed.

The requested second epoch-render receipt cannot be produced without a
subsequent explicitly scoped recovery; **no retry/restart was attempted**.
Do not merge copies, discard pending inputs, reinterpret the updated prompt as
the birth prompt, or claim either life remains running.

## Evidence and tests

`PAIR_MANIFEST.json` contains hashes, seed/context/source binding, both actual
LOADED and parent REQUEST receipts, stagger and pre-pair exposure, parent
policy/budget metadata, zero-update proof, epoch receipts and both failures.
`LATEST.json` is a dated status cut. `private/` contains raw artifacts and
provider inputs/outputs and is never in the publication allowlist.

Sixteen focused CPU tests plus seven negative subtests pass, including real
journal first/second frozen-sleep replay, rejection of forged updates, exact
paragraph addition, birth-pin compaction/restore and parent native-schema/
language regressions. The receiving host separately passed four frozen-control
tests and exact source/state provenance. Strict actual confinement denied every
foreign GPU in each arm. CPU success is not represented as live completion.
