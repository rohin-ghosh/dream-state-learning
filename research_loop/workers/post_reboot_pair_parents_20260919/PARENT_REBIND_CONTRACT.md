# Bounded exact-COMPLETE parent rebind contract

Status: **FUTURE-ONLY CONTRACT; NO REBIND AUTHORIZED OR PERFORMED NOW.**
Requested by main, September 19, 2026. This is an operational handoff to
main/Banach, not a receiver launch, source-epoch approval, scientific-policy
change, or permission to bypass existing receiver gates. Current parents must
continue refusing any changed native. Do not edit `remote_io.TARGETS`, live
`STATE.json`, parent argv, or native identities while preparing this contract.

## 1. Scope and unchanged invariants

One transaction binds **one arm, one old native incarnation, one actual receiver
LOADED record, one preserved parent ledger, one new parent incarnation**.
The other arm is outside that transaction. Journal/root, provider, curriculum,
prompts, tool policy, parent budget, all-authentic training rows, learner/frozen
control, provenance, visibility and deadline remain unchanged. The only new
parent-side fact is the explicitly validated native incarnation/source epoch.

| Arm | Current native PID/start | Journal | Current CPU parent PID/start |
| --- | --- | --- | --- |
| learner | 493500 / 10070880 | 038f85cbde5c4abfb749ea4d59da6897 | 345404 / 792480 |
| frozen | 471737 / 9987073 | 30fa18c869b34fd496a2758a4a28e197 | 345405 / 792480 |

These are current observations, **not authorization to signal any process**.
Re-read exact host/boot/PID/start/UID/argv/guard immediately before any future
transaction. Parent self-deadline and supervisor entry stay `1790791200`.
No lease, GPU placement, base model, weights, rows, dose or context policy may be
changed by the parent-rebind procedure. Receiver source changes belong solely
to main/Banach's separately approved retention source closure.

## 2. Required receiver evidence bundle

Supply immutable paths **and file SHA256s**, canonical record indices/hashes,
and a common arm/journal/root for all evidence. A PID printed by a launcher is
not LOADED. A synthetic test, DISPATCHED receipt, provider output or supervisor
status cannot stand in for the real native journal.

1. **Main's activation scope:** an explicit later request for this one old→new
   binding, identifying the reviewed receiver authority/source pins. This
   document and a consensus are not that activation request.
2. **Exact saved boundary:** actual `SLEEP_COMPLETE` plus its matching
   `R184_LEARN_COMPLETE` record and intents; checkpoint-file/adapter/optimizer/
   saved-RNG identity; exact `resume_state` digest; original deadline; and
   `pending=None` with a complete sleep frontier. Require Banach's exact
   checkpoint/tail parity proof, not merely matching optimizer-step counts.
3. **Handoff and old exit:** original bound old-native exit evidence, exclusive
   dispatch claim, and `RETENTION_HANDOFF.json` with valid token digest,
   `old_native_exited=true`, exact COMPLETE/state, new source closure, receiver
   plan/guard and unchanged deadline. No parent-side native signal is involved.
4. **Source adoption:** canonical `RETENTION_SOURCE_ADOPTED`, on the same
   journal, linking the same handoff digest, source-pin digest, COMPLETE index/
   SHA, state digest and deadline. The receiving wrapper must already have
   verified the exact COMPLETE + driver completion + INBOX-only tail under
   the existing native writer lock. No lost prefix, rewritten row, new birth,
   repeated WALL_EXTENDED or unapproved intervening child work is acceptable.
5. **Actual LOADED:** canonical hash-chain-bound `LOADED` after the source epoch,
   with `resume=true`, its real native PID, loaded timestamp and available
   adapter/optimizer evidence. Cross-check that PID against fresh remote
   boot/start/UID/argv/cwd/guard/root and the same physical allocation. Join
   checkpoint/plan/source/deadline facts through their real receipts; do not
   invent LOADED fields absent from the actual schema. If those joins cannot
   prove the exact saved checkpoint, reject the binding.
6. **First post-load work:** if a first REQUEST already exists, require it to
   follow LOADED, use the same native epoch and unchanged deadline/prompts/control,
   and bind its real pending hash. Its absence is a pending observation, not a
   reason to restart or stall the receiver. No sealed scores are consulted.

The receiver's current interface is
`post_recovery_pair_retention_receiver_20260919/receiver.py: PairReceiver`;
its source-epoch wrapper is `pair_retention_runtime.py: bind_journal`.
Their actual receiving-source CPU/provenance/admission/review gates remain
prerequisites. Their synthetic CPU tests do not authorize a live receiver.

### Mandatory dependency proof before native handoff

The receiver additionally requires `PAIR_RETENTION_PARENT_DEPENDENCIES_V1`
before preparation/dispatch, not just a post-LOADED check. In a separately
authorized future pre-handoff step, the parent owner must durably fence delivery
and resolve all in-flight outcomes without replay before claiming zero in flight.
Keep that fence effective across the receiver handoff and until successful
explicit rebind. An ambiguous provider/send outcome blocks this proof; never
clear its disposition to manufacture a zero count. No fence is applied now.

The immutable dependency receipt must bind the boundary module's canonical
`digest(exact_life_binding)` as `life_binding_sha256`, the prepared `source_epoch`,
explicit `owner`, `delivery_fenced=true`, `inflight_deliveries=0`, `durable=true`,
`preserve_existing_ledgers=true`, `automatic_pid_adoption=false`, and
`replay_delivered_messages=false`. Nonempty `ledger_pins` must include raw SHA256s
and absolute paths of all actual parent identity/state/delivery ledgers, after
durable persistence under exclusive ownership. Store the receipt outside those
pinned files. It is not a substitute for the complete preserved ledger below.

Pass that later receipt through `PairReceiver(parent_dependency_receipt_path=...)`.
Before dispatch and again before rebind, verify its exact bytes, unchanged ledger
pins and effective fence. The receiver's `PARENT_REBIND_REQUIRED.json`,
`RECEIVER.json` and handoff token must reference that same dependency proof.
Preserve queued arrivals without falsely acknowledging delivery. Any changed
proof/ledger requires a fresh reviewed attempt, not editing bound evidence.
`DISPATCHED.json` identifies a dispatch supervisor, not the receiving native;
it remains `loaded=false`, `parent_rebind_allowed=false`. This prospective
contract is not a dependency receipt and does not claim a live fence exists.

## 3. Single-writer ledger handover

At a future authorized activation, first prevent that arm's supervisor from
launching another CPU publisher during the short ownership transfer; disabling
new launches is not a command to stop a native. Coordinate this with Averroes.
Do not alter the other arm or stop a live parent merely to prepare evidence.

Under the existing per-arm `PUBLISHER.lock`, preserve an immutable ledger
snapshot and its file hash. The old CPU publisher must be quiescent/exited and
the lock released before a new publisher can own it. Preserve:

- `stage`, all events/assessments/messages, cycle and last-parent-cycle;
- `next_index` and `previous_sha256`, pending request/response/commit/stage;
- every delivery ID, original publication-author PID/start, remote receipt,
  INBOX/render/following-ACT proof, and exact provider RESULT/response bytes;
- `pending_turn`, provider-inflight intent, explicit-429 budget, and all
  provider/publication/transport blocked dispositions;
- `first_turn=false` for these already-restored parents. No birth opening,
  reboot-gap message replay, stage reset or bulk replay of old corrections.

Revalidate the cursor anchor and each referenced record against the receiving
journal. A cursor past COMPLETE is acceptable only when its exact retained tail
is proven by the receiver; a missing/mismatched cursor is a rejection, **never
a reason to reset the cursor to zero**. The parent ledger is not rolled back to
the checkpoint if it already contains later inbox/delivery evidence.

Create a new immutable `PARENT_REBIND_RECEIPT` linking old/new native identities,
LOADED/source-adoption/handoff references, old parent identity, old ledger hash,
new parent source hash and transaction ID. Only the runtime binding field may
change in the carried ledger; provenance is appended, not rewritten. Any future
binding adapter is a separate scoped implementation with tests—not installed
by this contract. Existing refusal of a changed native remains mandatory until
that explicit implementation/activation is authorized.

## 4. At-most-once publication reconciliation

The invariant is **no duplicate parent send**, not a fabricated exactly-once
guarantee in the face of an unknown network outcome. A receiver resuming the
same journal sees the existing inbox; a parent must not republish to announce
that the native incarnation changed.

| Preserved state | Required disposition before any send |
| --- | --- |
| Local PUBLICATION and matching remote control receipt/INBOX | Carry their exact IDs and hashes. Never call publish again for that turn. |
| Remote receipt exists but local publication acknowledgement is missing | Read-only reconcile the exact RESULT-derived delivery ID, text SHA and provider-response SHA; append a reconciliation receipt. Do not dispatch again. |
| INBOX present but not yet rendered | Leave the existing inbox file and canonical registration intact. Follow the receiver's normal read; no repost or new message ID. |
| `.dispatch` exists without a conclusive receipt, or provider call outcome unknown | Preserve the artifacts and block new dispatch for that unresolved turn. Text similarity, a timeout, process death or LOADED is not proof that it was unsent. Main must resolve it explicitly. |
| Valid RESULT, provably never dispatched, no in-flight old owner | A later explicit activation may send that exact RESULT once under its original delivery ID, after checking its source ACT survives in the retained journal. Never regenerate it silently. |
| Explicit provider HTTP429 rejection | Preserve the original rejection and bounded retry budget; only the existing explicit-429 policy permits another model attempt. |

Keep the original remote `control/PARENT_<RESULT-file-SHA>.json` namespace,
`*.dispatch` markers and all inbox files. Do not delete markers, change a
delivery ID, clear a blocked disposition or synthesize a receipt to get past
the handover. Ambiguous evidence fails closed for the **parent**, not the GPU
native. No model downgrade, scaffold change or semantic row exclusion follows.

## 5. Bounded activation and acceptance

The future transaction must name a finite verification/activation deadline no
later than the existing `1790791200` ceiling. It is single-use for the exact
arm/old/new identities and ledger hash. Re-check the live receiver before
activation and again immediately before the first publication. Expiry, identity
change, guard/source mismatch, competing lock owner or unresolved send returns
`BLOCKED_REBIND` without a native action. There is no automatic alternate
receiver, repeated source scan fallback or repeated dispatch attempt.

Acceptance requires all of the following, separately reported:

- current new CPU PID/start/boot/argv and sole held publisher lock;
- actual receiver native and canonical LOADED/source-epoch/checkpoint chain;
- exact preservation of the prior parent ledger, policy and publication IDs;
- the actual pre-handoff dependency receipt and still-effective delivery fence,
  retained until the explicit atomic binding update is verified;
- old delivered/inbox messages not republished; resolved or explicitly blocked
  pending-turn disposition, with zero implicit ambiguous retries;
- first post-rebind observation and, when the unchanged curriculum calls for
  feedback, a fresh provider result, queued INBOX, rendered REQUEST and following
  committed ACT with their actual record hashes;
- `following_ACT_proven` **separate from** `ACT_prompt_exposure`. Compaction may
  make the latter false without negating restoration. Neither proves uptake,
  retention, correct task execution or learning;
- updated exact supervisor source hash/argv only if needed by the separately
  authorized binding adapter, followed by `RUNNING_ADOPTED_NO_SIGNALS` for the
  new CPU owner. No native PID becomes a supervisor target.

Required future regression coverage: stale/PID-reused/native-boot mismatch;
wrong COMPLETE/LOADED/source epoch; moved root/journal/deadline/control;
missing cursor or inbox; preserved stage/history; stale publication-author
identity; duplicate lock; conclusive already-sent vs ambiguous send; no opening
replay; no resetting blocked attempts; and following-ACT/exposure distinction.
Do not infer that these future binding tests already exist or passed from the
current restoration suite.

## 6. What was done now

Only this prospective contract and inert handoff metadata were added. No new
receiver identity was supplied, no native or parent was rebound, no live parent
source/ledger/argv was changed, and no publication was replayed. The existing
two parent commands are enabled for supervisor adoption at their unchanged
ceiling; that operational registration does not authorize a receiver handoff.
