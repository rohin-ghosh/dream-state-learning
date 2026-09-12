# SEQ-082 — same-episode correction path executes, process primary remains null

September 12, 2026. Source `30cdad8e10fe99873787a0f6ba7bb32d9ac42fb6`,
run `astra_P1_fresh_correction_20260912_attempt1`, node3 GPU3 controller97128.
Both fresh no-adapter arms complete32 episodes with two wake opportunities.
Original-source CPU replay verifies raw generation/ledger/Scratchpad/next-prompt
joins in both arms. No training or parent-removal test executes.

| Endpoint | Process package | Sham package |
|---|---:|---:|
| First-wake first-ACT solves /32 | 1 | 1 |
| Second-wake first-ACT solves /32 | 2 | 2 |
| First-wake strict format /32 | 8 | 7 |
| Second-wake strict format /32 | 13 | 10 |
| Qualifying one-ACT failure-to-success corrections | 1 | 2 |
| Episodes with any multiple ACTs /32 | 15 | 7 |
| All native ACTs | 91 | 80 |
| Generation requests | 99 | 96 |
| Retokenized generated tokens | 12007 | 9449 |
| Actual package-token presentations | 9603 | 9312 |

The fixed97-token packages match per presentation; realized package exposure
and generated-token totals do NOT match because each actual first-wake ACT
receives its own Scratchpad call. The two opportunities are matched, not the
number of actions or total compute. These are one generation-seed exploratory
development observations, not independent learner replication or a causal
parenting benefit. The primary solve counts tie; the process arm has fewer
qualifying corrections. No improvement in future autonomous learning follows.

New32 IDs passed native train membership and overlap checks against the
specified prior metadata; global historical freshness remains unverified.
The static EVALUATION_ONLY scout is not reused as training experience.
Preserve all failed/multi-ACT cases; do not retrospectively rewrite them.

The process candidate is1850124; both arms' unchanged raw Scratchpads and
accepted action outputs require a public-constraint/content audit before any
material selection. Maxwell owns that read-only audit, pending at this cut.
Observed correction is not proof that the reflection is factually correct,
that it caused the correction, or that it is safe/useful as a sleep target.
No automatic raw-guess fitting, lowered material threshold or C11 gate added.

Worker97157 and98303 cleanup receipts show owned groups/GPU processes absent.
Main fullGPU/XML/CUDA/queue check at13:12:35UTC finds controller97128 absent
and releases GPU3. No manual kill or unrelated process removal. Separate
semantic writer controller98756 continues on reserved GPU0.

Receipts under `receipts_20260912/`:
- Terminal capsule `astra_parent_correction_terminal_20260912.tgz`, SHA256
  `bd4f7c5d035f423f27c262efbb17cc90bcab57cb30a45d894f7b3c98db65dd5b`.
- Original-source replay JSONL SHA256
  `711cc079da813c8e2631c8d7ebba90ef287ae54ffc453632bfac9025160af390`.
- Full cleanup observation JSON SHA256
  `5f7ef4bb44df261bdd6fbeac6709155b1dafeb5ee3f5519b03e259a5e16b7988`.

Local model hashes remain unresolved official-origin evidence. No mechanism
freeze, P1, G5, H1 or H2 result is established by this collector.
