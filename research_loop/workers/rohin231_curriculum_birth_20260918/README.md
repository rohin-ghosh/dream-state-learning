# R231 curriculum from fresh BASE birth

## Current status — September 18, 2026, 10:33 UTC

The initial launch below is historical, not current liveness. R231 exited
naturally at 10:28:21 UTC after two complete sleeps and 96 optimizer updates:
the protected prompt was 3637 tokens against the 3072-token compaction trigger.
No operator stop, restart, trimming, reset or baseline replacement occurred.
The exact-initial R232 frozen sibling loaded at 10:23:37 UTC and exited at
10:30:33 UTC after two zero-update sleeps at the same guard (3600 tokens).
Both states and inboxes are preserved. See `r232_pair/PAIR_MANIFEST.json` and
`r232_pair/README.md`. Only the frozen sibling rendered the later exploration
epoch; the learner registered its input but failed before making that REQUEST.

This operator owns one new life on the explicitly assigned ovx4 physical GPU0.
It uses frozen Qwen2.5-7B-Instruct and a freshly initialized private rank-8 LoRA,
not C2 checkpoint51 or any inherited optimizer, RNG, journal or adapter.

## Actual launch

- Native LOADED: September 18, 2026, 10:13:23.009538 UTC, PID62947.
- Journal identity: `038f85cbde5c4abfb749ea4d59da6897`.
- Saved initial optimizer steps and optimizer state entries both independently
  read back as zero. Birth rows, sleeps and working-state entries are zero.
- Exact 6-paragraph, 2744-byte birth text is pinned. SHA256:
  `7362d19a950779633067c81bacd0f0942e4243bbd62cf029463b61c264d66191`.
- Actual first request at 10:13:23.026946 UTC contains the exact birth text once
  and the genuine Astra opening, with 1797 prompt tokens and a 512-token cap.
- First Astra inbox ID: `85cc49386aba44faaccce68c0b33241b`, delivered 10:12:32 UTC.
- First ACT-review inbox ID: `01b4a1da83924811889da1ba3a01fef9`, delivered
  10:14:41 UTC. Publication is not itself proof of subsequent rendering.
- Strict native device confinement opens only assigned GPU0 and denies GPUs1–7.
- Finite learner and parent wall: September 18, 2026, 14:00 UTC. No lease change;
  the conservative operator horizon is not a verified provider expiry timestamp.

`LAUNCH_RECEIPT.json` holds source-bound metadata. `private/` holds raw CPU
failures, canonical journal observations, parent prompts and actual responses;
it must not be published. `LATEST.json` is a timestamped observation, not an
indefinite health claim. Shared runtime and other lives remain unchanged.

## A10G settings and measured limits

4096-token context, 512 generation cap, one sample per microbatch, existing
non-reentrant gradient checkpointing, rank8/alpha16/dropout0.05, LR3e-5,
16 new-only presentations, zero rehearsal, anchor coefficient0.25. The
standard pure-BASE TRAIN anchor inventory is separately source-verified;
no judge panels or C2 training state enter this birth.

At 10:14:43 UTC, seven actual UPDATE receipts exist and GPU0 uses
18941/23028 MiB. This establishes fit for those observed updates, not a bound
on every possible future context. The first recipe explicitly says
`R227_ALL_AUTHENTIC_CHILD_ROWS_V1`, no semantic exclusions, empty active
semantic filters, three new authentic child rows. Technical provenance and
encoding checks remain active.

## Parent and checks

The actual CPU Astra parent uses the exact six-stage document as its standing
brief. Stage0 sets one small checkable calculation and reviews each actual ACT.
Metrics and transition proposals are attributed parent judgments, not objective
scores. Unknown evidence cannot pass stage0. No automatic LR or dose changes
are implemented. Birth-prompt retention statements are authorized prompt text,
not demonstrated scientific claims. No sealed readouts are sent to the parent.

Seven receiving birth/compaction/confinement tests and two initial parent
language checks pass. A further native RESPONSE-schema regression passes with
the two language checks. The first parent-loop schema error is preserved;
only the CPU parent was relaunched, reusing the same opening publication
idempotently, with no learner signal or restart.

Run focused tests from this directory with the exact copied source closure:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/private/source" \
  python3 -B -m unittest -v test_birth_spec test_parent
```

The Builder line is logged in the owned isolated checkout's
`research_loop/COORDINATION.md`; Main owns shared publication. This worker
does not commit or push the shared checkout.
