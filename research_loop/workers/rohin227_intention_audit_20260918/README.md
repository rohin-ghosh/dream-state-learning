# R227 intention-to-ACT audit

This sidecar reads already recorded evidence; it never changes learner state,
parents, inboxes, targets, eligibility, processes or runtime configuration.
R227 withdraws semantic child-row quarantine escalation. Earlier R225 reviews
remain implemented/tested-but-not-live history, not deployment authorization.
Main owns the common no-filter path; Descartes owns C2 runtime and parenting;
Turing owns GAME1 routing. This audit has no control interface.

`audit.py` consumes the actual immutable-journal projection used by the existing
read-only reader. RESPONSE document hashes must match COMMITTED and R184_STAGE
source hashes. REQUEST hashes, segment/candidate identities, target hashes and
record ordering must agree. Sleep boundaries supply logical cycles; explicit
R184_TRANSITION binds the final THINK and its counted THINK group to a unique
same-cycle ACT. Console replies are separate, not fabricated THINK→ACT pairs.
Missing, ambiguous, incomplete and pending evidence is reported explicitly.

Metrics are descriptive **heuristics**, not task grades or semantic filters.
Intention cues, question marks outside fences, arithmetic-shaped text/code,
Byte/past-tense paragraph candidates and three-paragraph shape may be mistaken.
Questions are not failures. Code emission is not execution; execution is not a
correct result; an artifact link is not inspected file content. Text-work
candidates are not confirmed task fulfillment. The explicitly named math/Byte
surface count is not an exhaustive artifact detector: zero means neither of
those narrow cues was found, not no useful work. Non-execution receipts for
plain language responses do not establish failure. All fulfillment and semantic
alignment remain uncertain. No causal, retention, science or quality claim.

The ACT-form classes are exclusive: `INTENTION_ONLY_HEURISTIC`,
`QUESTION_OBSERVED`, `WORK_SURFACE_OBSERVED`, and `UNKNOWN`. Intention-only requires
an explicit future action and every remaining unit to match bounded future/
unverified-status scaffolding; a lexical intention marker alone is insufficient.
Questions are retained as questions, never failures. Literal drafts, concrete set
answers and nonliteral code can be observed work forms without being correct,
executed or good. Partial recall, unfamiliar language, mixed/unsupported forms and
memory commands stay unknown rather than being called intention-only. These
conservative English-oriented heuristics do not decide which rows are learned.

Exact parent text rendered in a non-assistant REQUEST message is linked to its
committed response; rendering is not comprehension. Parent topics are finite
word cues only. Public output has counts, fixed metric names, record indices,
hashes and timestamps, never child/parent text, code, paths, hosts or credentials.
Full evidence stays under ignored `private/`. The CLI uses exclusive output
creation so historical reports are not overwritten.

Run the CPU-only tests with `python3 -B -m unittest discover -s
research_loop/workers/rohin227_intention_audit_20260918 -p 'test_*.py'`.
Generate a report with `python3 -B audit.py --evidence PRIVATE_JSON --label C2
--output NEW_REPORT.json`. No GPU or inference call is made.

`collect.py --target C2 --start-cycle 72` and `collect.py --target P7
--start-cycle 90` perform one bounded live read each (at most1600 records), using
the existing approved SSH wrappers and read-only reader/projector, not new
remote infrastructure. Only local private evidence and local public metadata
are written. Reader/projector/program/transport hashes are attached. These are
point-in-time cuts, not evidence that the child is live at some later time.
P7 receives no messages, even when inspected. Life locations come from ignored
`private/TARGETS.json`; no live locations or credentials are published.

`observe.py --c2-evidence PRIVATE_C2_JSON --p7-evidence PRIVATE_P7_JSON
--interval-seconds 60 --duration-seconds 3600 --limit 256` continues both cuts.
Only new immutable record payloads after each exact cursor are read; directory
names are listed to bind a head, not reread as full history. Each tail validates
journal identity, anchor hash, continuity and source envelopes. Previously read
evidence is merged in memory, never fetched again per poll. Backlog is explicit.

Outputs are `operator/C2_LATEST.json`, `operator/P7_LATEST.json`, bounded-window
history snapshots, and `operator/PROCESS.json` with actual PID/start ticks,
interval/expiry and successful-poll receipts. Raw tail inputs and errors remain
private. The observer expires normally; no cron/system service, learner control,
parent publication or remote write is installed. The only lock is local to this
observer, preventing duplicate observers; it cannot gate a learner. Runtime
errors report types, not private transport text. Restarting an observer requires
an explicit new finite window, not automatic extension.

For clean checkouts without the earlier operator reader, `journal_reader.py`
contains the same bounded-read/hash/committed-state primitives without any live
location. The already-running observer continues its initially imported reader;
each poll records the reader and transported-program hashes actually used.
