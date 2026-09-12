# W0 interface calibration — September 12, 2026

Status: **executed, externally replayed, development-only diagnostic**.
No training or adapters; no W0 rescue, writer qualification or parenting result.

Source `92a800bd3672caea0569b8350af2c23bf9e5b3d6`, node3 GPU1,
run `~/astra_diagnostics/astra_W0_interface_calibration_20260912_attempt1`.
The protocol selected64 paired inputs before outcomes: the first held row for
each tool/mode in each of two roots and two maps. Five predeclared conditions
produced320 actual generations. These formerly held-out items are development
calibration data now; they cannot support untouched confirmation claims.

| Condition | Correct / 64 | Valid / 64 | Truncated / 64 | Multiple ACT / 64 |
| --- | ---: | ---: | ---: | ---: |
| Raw, original,32 tokens | 0 | 0 | 64 | 0 |
| Chat, original,32 tokens | 0 | 0 | 59 | 0 |
| Raw, explicit format,32 tokens | 0 | 0 | 64 | 10 |
| Chat, explicit format,32 tokens | 45 | 61 | 0 | 0 |
| Raw, original,256 tokens | 0 | 0 | 63 | 1 |

The unchanged parser rejects explanation, incomplete/truncated output and
noncanonical ACT syntax. The explicit instruction was fixed before execution:
“Reply with exactly one line: ACT: a0 or ACT: a1. Do not include explanations.”

Only the joint chat/explicit-format condition restored substantial parseability.
Chat alone did not fix the assay, and increasing the raw generation cap did not
fix it. This narrows the interpretation of the earlier failure: raw32 truncation
was real, but “use chat” alone is not a sufficient repair.

Correctness remains inadequate for the existing W0 oracle requirement. In the
joint condition the four root/map cells have correct counts10,11,13,11 of16;
valid counts14,16,15,16. Every cell is below the existing0.90 oracle criterion.
This is a64-input diagnostic, not a rerun of W0's256-oracle panel; do not promote
a gate from its aggregate61/64 formatting count or45/64 correctness count.
The64 prompts are not64 independent learner seeds. No inferential significance
or generalization claim is made.

## Reproduction and custody

Actual external `writer_interface_calibration replay` returned exit0 after
completion. Reserved elapsed time851.6260188490014seconds =
0.2365627830136115 A40-hours. Local copied-file verification matched329 sealed
files, the separately bound external worker log, and three source-file hashes.
Original W0's invalid report and failed seal remain unchanged.

Raw capsule: `receipts_20260912/astra_interface_calibration_terminal_20260912.tgz`.
SHA256 `46815dde46a3b50c037905c7cda8eb12893bdd1032b75f2d59b608aea8eb7412`;
667003bytes;342 archived payload hashes independently verified. It includes
raw requests, token IDs, outputs, report, preparation/execution seals, resource
receipt, external logs, frozen source, replay output and the analysis script.
Report SHA256 `65b9e4eb2947f45984854626c28f1ae977490a160cb6dc9313e1bc62111180c8`.
Base/tokenizer binaries are not bundled. They remain locally pinned with
official-origin authentication unresolved. The prior failed-W0 capsule is an
explicit dependency, SHA256
`1ef045e5e18e0747b6429e9f08c32702dab09bd03d53f1752950794b90a46608`.

Extract into a new directory; verify `SHA256SUMS`; run the bundled
`analysis/astra_summarize_interface_calibration_20260912.py` against the copied
calibration run directory. Full external replay additionally needs the retained
original remote paths/dependencies; the capsule is not a bundled model runtime.

## Next decision

Do not launch a new writer fit merely because61 outputs parse. A bounded
inference-only follow-up can select the one relevant table row by its tool/mode
key, keeping question, chat rendering, fixed instruction, token cap and parser
unchanged. Compare its64 new outputs with the already-recorded full-table
condition. This tests whether table selection contributes to the remaining
failure; it does not demonstrate extraction utility for learning. Preserve all
conditions and use fresh data before any future confirmatory writer assay.
The independent lesson/sham material-formation pair proceeds concurrently.
