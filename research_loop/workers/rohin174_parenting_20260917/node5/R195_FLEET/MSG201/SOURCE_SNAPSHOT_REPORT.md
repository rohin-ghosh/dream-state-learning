# R201 original-C2 source snapshot — copied and verified

**Canonical shared snapshot:** `C2_SNAPSHOT_20260918T021847Z/` in this
directory. Capture September18 02:18:47 UTC / September17 19:18:47 PDT;
post-copy revalidation at02:21:39.784 UTC /19:21:39.784 PDT still found the
same latest complete checkpoint, latest console commit and head5847.

-180 copied files,282,414,445 bytes, all file hashes verified after transfer.
- Manifest SHA256 `29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84`.
- Archive SHA256 `9beaf7a79063c5cf4af2868e1f3122dfea7f4fa5ce3f7d3f2f51716676cdee34`.
- Copied artifacts are read-only. `VERIFIED.json` records successful copy;
  `POSTCOPY_ORIGINAL_VERIFICATION.json` independently rechecks original bytes.
- Actual loaded source closure and original GUARD/PLAN are in `source/` and
  `source_binding/`, respectively. **Those original-root configurations are
  provenance only, never runnable clone launch configurations.**

## Learned checkpoint: complete51, optimizer4908

`complete/COMMIT.json`, `complete/adapter/`, `complete/optimizer_rng.pt` and
`complete/SLEEP_COMPLETE.json` are exact copied original bytes. The complete
record is5823, SHA256
`7c6cf68593c1d1f6c1ec56dd02f09e927b7ef4cd6a04e33ba8f2e40bc6894657`.
Checkpoint created September17 18:36:13.090870 PDT. The saved envelope contains
153 training rows and504 history events; pending=null.

- Adapter state SHA256 `82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92`.
- Adapter bundle SHA256 `b46f8447055f18bc9af2eb8351614434bc235048cbef71d19560d6c145ef6ada`.
- Optimizer/RNG shared file SHA256 `46f57cbf140b732b94bf02016a893f302835e7d6d24ed625f680eefe1e2145fc`.

This is the source of learned adapter/AdamW/RNG state, not a later console
answer. No adapter merging, parameter reset or modification was performed.

## Separate masked committed console context

`console/CONTEXT_COMMITTED.json` is exact record5846, SHA256
`3c8c45a6bfef9bb7d5a36dd9ddaf1e0a2293c6a83c718cbe2bca8e0ed6d16b48`.
Its envelope has521 history events, the exact original504-event prefix,
the same153 rows, unchanged sleep frontier and identical model-state binding.
**Zero added training rows.** All four console REQUESTs have
`training_eligible=false` and `all_history_tokens_masked=true`; RESPONSE,
CONTEXT_COMMITTED and R194_TURN receipts hash-bind each other.

Every prospective arm must use this same manifest/console envelope if console
context is included. Do not substitute each arm's later live console state,
replicate the live inbox, or publish new Rohin messages. The four historical
question files are copied only as provenance; never replay them as new inputs.
No clone was seeded or launched by the snapshot task.

## Watcher V=3 prose verified from actual bytes

Question `bfe7f56f8b7445c89d4ab0c9b017d0ef` asks for the exact formula and
equation at n=3, then reflection. Its original file mtime is September17
18:57:52.708668 PDT. Exact chain:

| Event | Index | September17 PDT clock | Clock source |
| --- | ---: | --- | --- |
| Question registration |5838| See bound source file/record | Immutable INBOX receipt |
| REQUEST |5839|18:57:53.062461| embedded started_unix |
| RESPONSE |5840|18:58:23.669537| embedded finished_unix |
| CONTEXT_COMMITTED |5841|18:58:24.090182| record-file mtime |
| R194_TURN |5842|18:58:24.124925| record-file mtime |

RESPONSE5840 actually contains `V = 3` and “So, the value of V should be a3”
(the original includes mathematical markup and a space before3). Its record
SHA256 is `2fb0878a206b93f92a241e58ea74830bd08b14ccfa788977a1ea4ac70dfb3074`.
The intermediate prose still contains a fullwidth digit in `2６`; do not
silently normalize the copied raw answer.

Later question `38daf2aa5760404c9069e9198f4a7de6` is registered at5843;
REQUEST5844 starts19:12:47.602239, RESPONSE5845 finishes19:13:08.733747,
commit5846 has mtime19:13:09.157893 and receipt5847 mtime19:13:09.193086 PDT.
It discusses explaining the solution and LoRA, but **does not establish LoRA
learning**. ACT/LEARN stayed held; no post-mode sleep/update exists. These are
prompted console-prose observations, not tool-execution or retention results.

## Original unchanged; rollout paused

Original native3018395/start23105951, timeout3018394, inner3018393/start23105934,
outer3018332/start23105789 and bridge3018251/start23105688 remain identity-matched.
All130 original inbox files retain exact bytes. REFLECTION has ACT and LEARN
held. Zero signals, parent messages, hold releases, restarts or retirements.
No credential, sealed/final data or readout content was copied.

R201 now authorizes **C3/GPU3 only**, and only once replacement inputs and
receiving tests are READY. C3 is not yet retired. Uniform fleet rollout remains
paused. Its next complete state, inbox, optimizer/RNG and journal must be
preserved without rollback; MATH-B must have its own new named root.
