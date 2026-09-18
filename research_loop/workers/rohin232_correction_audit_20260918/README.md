# R232 fleet correction sequence auditor

Read-only to lives: existing SSH transport runs bounded standard-library file
reads with CUDA hidden. No learner signals, pauses, restarts, inbox writes,
resubmissions, new training exclusions, private judge data or subagents. The P7
overseer/bridge/reader are unrelated processes and remain untouched.

## Meaning of the levels

- 0: an actual rendered corrective feedback event is reviewed, but own correction
  identification is not demonstrated in the inspected trace.
- 1: a literal span of a committed child output identifies that correction.
- 2: the **very next ACT after that identification** actually applies it.
- 3: a different later relevant ACT applies it without an intervening reminder or
  newly supplied solution. Three distinct child records are mandatory.

Keyword hits are only candidate discovery. Unknown/unreviewed is not level0,
and disagreement, a promise, correct-looking prose or an isolated correct number
does not certify application. The source-bound annotation ledger is an observer
semantic assessment; code verifies record/hash/span/order/masking/next-ACT links.
New semantic candidates are deliberately not automatically promoted. Current
limitation: this is an hourly receipt-and-candidate publisher with validated
analyst adjudications, not an autonomous general semantic judge. New candidates
remain visibly pending direct review. No extra model/agent is invoked.

`public/STATUS.md` is the bounded best-partial table, not a lifetime leaderboard.
`public/MAINTENANCE_CONTEXT.json` records owner-reported treatment changes,
recall contamination and recovery exclusions separately from native proof.
Caught-up journal coverage does not mean a life is currently running. A parent
process replacement is not proof its new treatment rendered to the child.
`public/CURRENT.json` includes exact feedback event/INBOX/REQUEST IDs, child
RESPONSE/COMMITTED/STAGE IDs and hashes, observed subsequent outputs, reminder
counts or explicit unknowns, parent-solution exposure, and cross-task/sleep
survival results. A single stage acknowledgment is not a corrected ACT.
An old correction must be interpreted in its contemporaneous policy: in
particular, historical pre-birth P7 correction is not a denial of its real later
Astra7 parenting role.

## Rendering and preservation

Both literal plain user messages and the original metadata-prefixed native
rendering are supported. Structured rendering must match exact actor, event,
source path/hash, split, and literal text; assistant quotations do not count as
delivered feedback. The initial plain-only observer projection was incomplete
for the fresh R231 life; its before-repair evidence is preserved privately.
Native histories were not rewritten.

Level3 records whether the original correction remains visible in context.
Absence of a **new** reminder is not absence of context assistance, adapter
retention proof, or causal transfer. All new intervening external turns must be
explicitly classified; unknowns cannot pass level3.

On the first observed full trace, `public/first_full/` references the first
following SLEEP_COMPLETE boundary once durable. The reader binds its canonical
record, resume-state hash, COMMIT, optimizer-step count, adapter file/state
hashes, and optimizer/RNG hash. It hashes stable files in place and publishes
only a manifest; it never copies a racing live state. A pending boundary is
reported pending, not falsely preserved. No full trace means no such claim.

## Operation

Private owner-provided target bindings, projections and annotation spans stay
under ignored `private/`. Raw child and parent text never enters public reports.
`TO_OWNERS.md` records unresolved root/identity requests. Initial windows are
bounded; `caught_up=false` remains explicit while the reader drains more records.
Node3 means the active replacement node from the owner's R227 registry, never
the expired earlier node3. The R231 birth is not silently called the later R232
matched sibling pair. The frozen non-native game requires its owner's specific
log contract; no native journal or sleep checkpoint is fabricated for it.

Run tests with:

```sh
python3 -B -m unittest discover -s research_loop/workers/rohin232_correction_audit_20260918 -p 'test_*.py' -q
```

`service.py --publish` takes one local process lock, reads immediately, then at
each UTC hour, and expires at **2026-09-18 14:00 UTC**. This is a conservative
observer horizon, not a lease extension or claim about provider expiry. It
re-reads private target bindings each poll so confirmed sibling births can be
added without touching their runtimes. `operator/PROCESS.json` pins the actual
local process identity and next due time; errors remain private. Publication
uses a separate detached checkout and an exact worker-file allowlist. It never
stages the shared checkout, raw logs, other workers, runtime or COORDINATION.
