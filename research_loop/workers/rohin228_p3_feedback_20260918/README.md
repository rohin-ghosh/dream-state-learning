# R228 P3 attributed judgment transport

This is a non-material repair to visibility of already-scored development-game
results, not a new benchmark, scorer, learning rule or parent intervention.

## Diagnosis

The existing caption client places its whole scorer receipt into an environment
history event. Provenance marker strings in that JSON match the plain-context
scaffolding detector, which drops the event. Aggregate feedback may survive;
the individual ranks, acceptance and novelty do not. An actual rendered
REQUEST, not a journal RESULT alone, is the delivery test.

## Repair and custody

`relay.py` validates an existing RESULT's ACT origin against the canonical
child RESPONSE hash and exact raw output. Exact caption source spans, where
provided by the scorer, are verified before display. It publishes plain text
through the existing console with speaker Tool, actor environment and a source
receipt binding an immutable projection. Every caption receives its recorded
rank/acceptance/novelty; missing scores receive an explicit no-judgment reason.
Historical scorer schemas lacking spans remain explicitly unattributed to
particular caption bytes; no caption text is invented.

The projection's provenance stays outside the visible text so it survives the
existing renderer. Raw results, child outputs and semantic LEARN policy are
unchanged. This is not a training-row filter. Publications are deduplicated by
immutable projection identity, including crash recovery against actual inbox
files. Six synthetic tests cover the real renderer, source integrity, chunk
completeness, no-score feedback, bounded native tailing and result immutability.
Both local and receiving-source tests passed.

## Dispatch receipt

- Initial backfill at09:05:13UTC published28 Tool messages:68 scored captions
  and11 no-judgment attempts across24 saved ACT receipts.
- First scored-feedback INBOX: `b757a985f0894daca3133c517c1b9bea`, SHA256
  `fe3142bb4d72c9c000c660b7aba4ff1ddd5d617a7962ddf98c48b95208e8f49b`.
  Its exact SHA is verified in the generated delivery audit; do not infer
  rendering from this publication alone.
- The initial CPU relay exited after its successful backfill because it
  encountered a journal `.intent.json` file. The bounded record reader now
  explicitly skips these files; the regression test covers it. No learner was
  stopped and no published message was duplicated.
- Corrected CPU relay PID1493939 started09:07:09UTC, expires11:07:09UTC,
  polls every2seconds, and tails new RESULTs and native scorer failures.
- Corrected archive SHA256:
  `41a449446dead63036b4712aad6f271e0a43c905b48cb647a3723ac77eef998b`.
  Relay SHA256:
  `0b0ea65a243a1ecfce0944b8a7ad50efcd86abb7cb646a6b0f95555a3207a9ab`.
- P3 native PID237705 remains unchanged. No native signals, reload, pause,
  rescoring or parent reply on Rohin's behalf occurs in this repair.

`audit_delivery.py` checks exact published text in actual subsequent user-role
REQUEST messages and emits only IDs, hashes, counts and times. Its output,
rather than the presence of an inbox file, is authoritative for rendering.
At09:09:37UTC rendering was still pending during the existing sleep.

Verified at09:13:49UTC: all28 publications appeared verbatim as user-role Tool
messages in REQUEST1948, started09:12:45UTC. Its canonical record SHA256 is
`82d71568b2d66a55299241986c61aca82d84f8ae59511ecca47371155d94612e`.
This proves actual delivery of68 ranked results and11 no-judgment notices, not
behavioral uptake. Full per-publication bindings are in
`DELIVERY_20260918T091349Z.json`.

## Limits

This does not fix semantic scoring weaknesses, make the observation a matched
H2 experiment, or prove behavioral uptake. It does not switch the cached
learning policy of P3 or C2. Those older runtimes still need a supported
no-gap adoption path; a source commit alone is not evidence of adoption.

## R232 renewal armed, not yet activated

At10:28:00UTC on2026-09-18, exclusive CPU supervisor2002133 was armed for
the existing writer1493939. It waits for that writer's ordinary exit; neither
the relay nor P3 is signalled. The successor uses the exact unchanged relay
source, same life/sessions/output directory and writer lock, preserving the
projection and publication deduplication ledger. The only relay argument
change is the expiry from11:07:09UTC to14:09:07UTC.

`R232_RENEWAL_ARMED.json` binds92 existing immutable projection/publication
receipts. `renew_relay.py` verifies their preservation before and after the
successor starts, records the CPU-writer handoff interval, and refuses another
successor once activation is recorded. Twelve local relay/renewal tests and
five receiving-host renewal tests passed; the transferred supervisor source
SHA256 is `d5ce0ae62b6adfdf25c10e1d58fa636bff5fef84dc4f482c20f7dd26dbadc010`.

The future activation receipt is
`/localhome/local-rohing/orch_r228_p3_feedback_20260918/r232_renewal/ACTIVATED.json`.
At this cut it does not exist and renewal is not reported as active. A failed
handoff produces `FAILED.json` or the supervisor log; it does not stop or
restart the learner. The next attributed Tool rendering still needs the
normal delivery audit, independently of CPU-writer startup.
