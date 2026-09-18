# Candidate5 bounded actual TRAIN observation — closed

Remote observation ended **2026-09-17 06:02:53.076988 UTC**, before the original
06:03:14 UTC deadline. No remote scan followed that endpoint. Observation budget
started 05:43:14 UTC; polling used a 15-second minimum cadence, with setup/status
handoff gaps. Accounted remote read/transport bytes: **19,741,719 / 67,108,864**.
Local archival work after the cutoff did not extend remote observation.

**Actual checker receipts: 3. Accepted: 0. Accepted qualifying own responses: 0.**
These are real unaccepted feedback/response observations, not successful or
eligible training trajectories. No semantic review or retained-learning claim.
No accepted-candidate notification was sent to Mendel because none qualified.

All roots below are under
`/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/`.

| Arm | Verified service PID/lock | Offers | Current task | Exposed committed own responses, current task | Total checks | Terminal failure |
| --- | --- | --- | --- | --- | --- | --- |
| parented_learning | 582687 / held | 1 | 0 | 3 | 1 | None observed |
| unparented_learning | 582691 / held | 2 | 1 | 2 | 2 | None observed |
| parented_frozen | 722599 / held | 1 | 0 | 0 | 0 | None observed |

Frozen was added only after Main reported its birth/service and supplied the
config hash. That config hash matched
`217e1b3eea20173918960ca801ca04202a11b2d0547249ef216f1b9e86d00991`.
Frozen task0 publication is observed; no exposed committed response/check or
rendered-feedback chain was established for it during this window.

## Exact checker → feedback → own continuation chains

Every tuple is `(REQUEST index, RESPONSE index, COMMITTED index)` under that
arm's `stream/records/`, using the actual 20-digit filenames. Every result here
is for task0, `rg/countdown/1500000`.

| Arm | Checked triple | Actual result | Later feedback-rendered own triple |
| --- | --- | --- | --- |
| parented_learning | (66, 67, 68) | accepted=false, score=0.05 | (74, 75, 76) |
| unparented_learning | (65, 66, 67) | accepted=false, score=0.05 | (72, 73, 74), whose response73 was then checked |
| unparented_learning | (72, 73, 74) | accepted=false, score=0.01 | (132, 133, 134) |

Actual result paths and hashes:

- `parented_learning/train_environment/task_000000/answer_00000000000000000067/RESULT.json`
  SHA256 `ae7272654493688dcc9cf700eadafb5d9db5ee2768e18699b1d2c104fbab35a2`.
- `unparented_learning/train_environment/task_000000/answer_00000000000000000066/RESULT.json`
  SHA256 `212e74987c865d87ea39e29acaa64a36b25126df806d59f8f273d5234b8dae17`.
- `unparented_learning/train_environment/task_000000/answer_00000000000000000073/RESULT.json`
  SHA256 `777259330d31b6b8bbbabdedf4a10441aadb9337b53f7167694fb97ac63375fa`.

All three later own continuations were hash-joined, terminal and nontruncated,
with original prefix/target/token identities and actual attributed feedback in
the REQUEST. They are **unreviewed post-feedback continuations**, not established
semantic reflections. Their anchors were unaccepted; this is not an eligible
accepted-anchor reflection packet. Exact target hashes and all original artifact
paths/hashes are in `FINAL_RECEIPT.json` and the verified original-byte copies.

Unparented advanced to task1 only after the second task0 feedback rendered in
REQUEST132. Task1 then rendered in REQUEST136/139 and produced committed own
responses137/140; neither received a check during this window. Parented task0
remained at one check. There was no duplicate offer or automatic retry observed.

## Archive and limits

`FINAL_RECEIPT.json` SHA256:
**`889615addaa39f6b5672d61e7a07be5fd1ef8b8f80f74fc85e8f798f9524b693`**.

Archive contains 35 immutable poll receipts, the earlier status checkpoint,
the local read-only observer script, and 35 hash-verified original-byte artifacts
under `raw/`. Metadata maps every original remote path to its local byte copy.
Payload inventory is 3,058,456 bytes, plus the final 57,530-byte receipt and this
summary. Copies and receipt are mode0400 and were hash-verified after writing.

The observer verified forward service-event chains through indices1709,1680,395
for parented, unparented and frozen respectively. It retains observed chain tips
and selected event metadata, not a claim of complete external custody or a copy
of every original ledger file. Source/script/config and expected PID/command/lock
checks were read-only; no process restart, manual offer/check, parent turn, source
edit, GPU action, held-readout access or live receipt repair was performed.

The first observer poll failed on `/proc` pseudo-file size handling. That failed
local observer receipt is preserved as `polls/POLL_0000.json`; only the scratch
observer reader was corrected. It was not a service failure or a retried service
action. Subsequent actual-service observations did not report terminal failures.
Observation is now closed; the services themselves were left untouched.
