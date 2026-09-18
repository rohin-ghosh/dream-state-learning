# Final R232 observer/semantic-review ownership handoff

This daemon is **not recurring semantic maintenance**. It collects actual native
receipts, revalidates existing analyst annotations, publishes their bounded best
levels, and queues new inputs/ACT windows. It performs zero new semantic judgments,
model calls, parent writes or learner controls. The13 actual adjudications at the
11:04:13UTC cut were manual Turing work, not daemon-generated results.

## Main action each hour

Main owns the requested semantic-review handoff; acceptance/scheduling of a human
or model review session is **not inferred** from the running collector. Review
`public/REVIEW_QUEUE.json` after each cut. Its exact feedback/INBOX/REQUEST and
committed child/stage hashes locate the source in the private target/projection
files. No raw conversation or host path is published. All rendered external input
types are eligible for triage, including routine tasks and runtime telemetry;
queue membership is never a claim that an input is corrective.

At most4 items per life are displayed: up to2 newly observed items, then rotated
backlog. Aggregate pending and omitted counts stay explicit. New ACT windows
remain pending across polls instead of disappearing just because they were seen.
The display is bounded, not an assertion that the whole backlog was adjudicated.

Read actual bodies and context before recording another source-bound annotation
in `private/<life>/ANNOTATIONS.json`. Ambiguous/ignored remains unknown or a
reviewed level0 as appropriate. Do not promote a queue item from keywords, a
promise, a parent-authored solution, or a planned output. Reinspect reminders,
context exposure, NEXT ACT and a separate later relevant attempt. A newly validated
level3 triggers the existing durable COMPLETE manifest check; no racing state copy.
Re-reading static annotations is not a new review. Pending windows are not
automatically closed by an unrelated annotation. Preserve manual dispositions
and unresolved windows in the review handoff rather than claiming a clean queue.

## Exact lifecycle

The source-pinned observer runs once on adoption, then at UTC hours strictly before
**2026-09-18T14:00:00Z**: remaining regular cuts12:00 and13:00, not14:00. It exits at
the finite14:00 observer horizon; this does not stop lives or renew any lease.
`operator/PROCESS.json` and `public/SERVICE.json` identify the actual incarnation,
loaded source hashes, next cut, expiry and explicit non-semantic mode. Only the
observer PID is replaced to adopt this queue code. P7 overseer405221, bridge442474
and reader493471 are separate services and must stay running. No P7 ownership or
publisher duplication is transferred by this audit handoff.

Known gaps: the frozen non-native caption player's log contract remains pending;
Fable's independent whole-since00 reader artifact was not located here. C2 starts
at record5501 in this audit; current C0/math journals start at0, not predecessor
histories. Learner/frozen recovery LOAD172/74 retain original journal identities
and explicit1338.866738s/1152.938522s gaps. FRESH_R231 is the learner alias, not an
additional birth. No reviewed level3 exists at the handoff cut.
