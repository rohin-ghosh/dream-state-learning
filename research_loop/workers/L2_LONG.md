# L2-LONG — owner journal and Main interface

2026-09-14T23:36Z [Builder → Main] DECLARED / CPU work underway; no GPU/model
calls yet. Read raw81–82 locally and raw83 at 39c15c90, current RESEARCH_STATE
L2 sections and BOARD. Approved scope: this direct LONG assignment and standing
builder authorization; experiment-serving implementation, no invariant change.

Exact disjoint ownership: `organism_v6/orch_l2_long_parent.py`,
`gpu/orch_l2_long_backend.py`, `gpu/orch_l2_long_lane.py`,
`tests/test_orch_l2_long_parent.py`, `tests/test_orch_l2_long_backend.py`,
`tests/test_orch_l2_long_lane.py`,
`research_notes/analysis/orch_l2_long_20260914_attempt1/`, and this journal.
No shared driver/cohort/control edits; no peer merges, staging or GPU cells
by Main. A100 physical1 only; own guardian, UUID/CVD checks and 12h/12GPUh cap.

## Narrow interface requested from SHORT through Main

- Import SHORT's immutable cohort/source/readout manifest and generic native
  three-cycle driver. LONG never reconstructs worlds or fits separate controls.
- Hook before an experience turn: cycle/world/turn ordinal, child's optional
  parent question, public training observation, learner's own nonsealed past
  episodes and completed sleep learning telemetry. Separate training-only
  control summaries may be supplied with provenance; absent controls are null.
  No sealed readout data, answer keys, hostnames, credentials or paths.
- Hook returns optional complete parent message plus an auditable decision;
  messages are visible to child in full but excluded from student prefix/loss.
  Expose child-question channel (including self/system/learning questions),
  parent-initiated opportunities, and decline; do not make every child turn
  invoke the evaluator. Preserve raw child text for shared semantic admission.
- Freeze LONG involvement at maximum FOUR parent messages and FOUR evaluator
  decisions per cycle (12 each total), max256 generated parent tokens/message,
  max1024 parent output tokens/cycle. Eligible initiative at experience ordinal
  0,8,16,24, at most one message/world. Child questions may use remaining
  opportunities, with an explicit cap-exhausted decision, not a canned answer.
  This is a low-involvement cross-episode/sleep policy, not a matched-dose
  horizon-isolation experiment. Report actual exposures as well as messages.
- Shared driver must provide event callback for nonsealed completed experience
  and sleep training metrics; per-cycle parent distillation uses only these.
  Distillation is not an extra child reflection or extra evaluator call.
- Same final SHORT recipe: four presentations of qualified actual own raw
  targets plus identical old rehearsal, fresh AdamW, natural variable/zero
  yield and unchanged weights preserved. Six experience turns, <=512 generated
  and2048 child context, RICH150–400 from cycle1; reflection separately counted.
- Please expose common atomic all-call accounting (20000 across four arms,
  parent calls included), fixed source identity, guardian inputs and a LONG
  arm entrypoint. Shared controls may arrive later, never gate collection/fit;
  causal comparisons wait for their exact receipts.

Native seam ce9a906e/f2e76c43 read from git objects; not present in this checkout
at23:35Z. Main should make the owner-published seam/shared interface available
without LONG modifying those paths. Continuing parent policy/backend/CPU work
now, not building a parallel shared framework or waiting idle.

Initial hypothesis (not result): rare history-informed coaching can improve
cohesive retained learning with much less parent involvement than dense
episode-local nudges. Falsification: parent-free gains/retention do not improve
or require comparable guidance cost; initial ceiling/continuity is not progress.
No causal or scientific result claimed. Backend will be explicit, existing
authorized evaluator only, no fallback around denied authorization.

2026-09-14T23:40Z [Builder → Main] IMPLEMENTED17/17CPU tests pass (python3;
VM has no `python` alias). Native seam now available at e1028963. No model
calls. Shared V1 read and accepted, not regenerated:8worlds/16episodes/cycle,
8heldworlds,8048aggregate ceiling, RECIPE lr1e-4/freshAdamW/four presentations/
222oldrows, max216updates. Initial larger-envelope wording is superseded by
SHORT's narrower frozen batch. Initiative slots now episode0,4,8,12 (worlds
0,2,4,6), one message/world; four decisions total/cycle INCLUDING declines.

Precise callable: `LongParent.before_turn(cycle, episode_index, turn,
observation, question='', metrics={'scope':'training','values':{}}, controls=[])`
uses keyword arguments, returns a dict with `message`, `decision`, costs.
`observe_episode(...)` receives own observation/raw response and TRAIN scalars;
`observe_sleep(cycle=..., metrics=...)` receives only TRAIN scalars;
`record_exposure(cycle=..., messages=[complete messages actually shown])`;
`distill_cycle(cycle)` produces the Rohin record without another model call.
The class owns cross-cycle state; shared driver must persist/replay training
events across fresh collector processes or use the VM service's live instance.
No test/retention outcome may enter this hook, even as a scalar.

Backend: existing authorized Claude CLI, tool-free, safe-mode/no plugins or
MCP, explicit parent system, no session persistence, no permission bypass or
fallback. Auth remains existing runtime; no credentials copied into files.
`EvaluatorBackend(output, charge_call, deadline=...)` invokes runtime only after
the caller's shared-bucket debit. Native-token cap256 applies to delivered
message, no truncation; complete evaluator JSON capped1024 provider tokens
(reason/distillation/metadata overhead reported separately, not child exposure).
Global VM lock proposed `/tmp/orch_l2_evaluator.lock`: always max1 process,
admit none below1.5GiB. SHORT should share this lock through Main to meet the
cross-worker memory/fanout rule. No backend calls or credentials on GPU host.
Need shared driver/transport hook signature next; continuing own guardian and
native integration tests, not writing a competing loop/cohort/control driver.

Evidence:17 tests cover sparse budget, child initiative/self questions,
real decline, nonsealed history/sleep context, rejected sealed/unknown scalars,
control receipt requirements, secrets/paths/hosts rejection, no truncation,
exact repeated exposure, no canned fallback and memory-floor-before-dispatch.
This is CPU readiness only, not native completion or learning evidence.

2026-09-14T23:42Z [Builder → Main]21/21LONG CPU tests pass. Own guardian
`gpu/orch_l2_long_lane.py` schedules only10 shared-native stages (initial
readout,3×experience/sleep/readout), A100physical1 UUID
GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b, own12h/12GPUh cap, exact PID identity
before any owned-group stop. No launches yet. Source once on SHORT physical2.

Accept SHORT23:41 pre-call correction: **lr3e-5 / NO gradient clipping**, not
earlier draft1e-4/clip1; LONG imports final `shared.RECIPE` verbatim. No optimizer
or dose fork. Prior draft wording retained as evidence, superseded here.

ACTIONABLE shared seam request via Main (no peer messages): current
`shared_run.run(options)` hardcodes devices SHORT/FROZEN/UNPARENTED and
`parent_present = arm == 'SHORT'`, so a LONG wrapper cannot reuse it without
copying or monkeypatching the generic driver. Please expose LONG device1,
`parent_present = arm in ('SHORT','LONG')`, optional parent-factory/hooks
and per-arm PARENT_LONG bucket. Hook may be constructed on GPU with tokenizer
and shared parent_request transport, using LONG policy from this worker.
Parent transport receives only already-sanitized LONG request; VM uses
LONG tool-free backend. Shared episode needs optional per-turn callback and
ASK_PARENT channel for child self/system questions, not only SHORT turns0/2/4.
Training-only prior episode/sleep events initialize LONG history each cycle.
Parent-free readout gets NONE. Exact exposed messages feed exposure callback.
No global SOURCE/test path or test scalar ever goes to parent/evaluator.

I will supply that constructor adapter in my owned module as soon as the
injectable signature lands. Guardian currently intentionally fails
`shared_driver_long_hook_not_published` rather than treating LONG as SHORT,
copying the trainer, rebuilding cohort, or silently collecting unparented.
This is an integration dependency, not a requested Main/reviewer launch gate.

2026-09-14T23:44Z [Builder → Main] Constructor delivered, new exact owned path
`gpu/orch_l2_long_hook.py` (LONG prefix, no shared edits).
`build_parent(root=..., cycle=..., tokenizer=..., transport=parent_request,
emit=...)` returns callable `SharedLongHook` plus `observe_episode(record)` and
`distill_cycle()` methods. Call observe after EACH episode, before next hook.
It reconstructs only own PRIOR TRAIN episode/sleep history from exact
LONG/cycleN/experience and sleep files, never reads readout or global SOURCE.
Current payload is shared actor's coach payload plus optional child_question.
It sends `{'kind':'long_coach','long_request': sanitized_request}` to transport
only at sparse opportunities; all other decisions local/logged, no evaluator
debit. Backend returns actual decision/message/reason/distillation dictionary.
Native tokenizer enforces complete256-token limit; driver LONG cap must match.
Exposure accounting reads actual capture parent-message inventory, not merely
message creation. Main can relay this literal constructor to SHORT immediately.

Read SHORT23:43 correction:8648 aggregate prospective cap (adds FROZEN coach
bucket), same worlds/recipe. LONG accepts final immutable shared manifest under
the user's20000 envelope; no own call-cap/cohort reconstruction. GUIDED-FROZEN
is SHORT-style, not matched sparse-LONG; report that limitation explicitly.

2026-09-14T23:49Z [Builder → Main]58 combined CPU tests pass, including own
callback + nonsealed history-only file-read regression, native seam and shared
tests. Actual read-copy of shared INITIAL/COHORT/PREPARE verified; PREPARE
83ebe041508a265ff06824072c603ece22d3881df908d4a6ab822afffd724c2d,
COHORT file8cd5a0f85ca8cb20a1d96b47e267debd580bb260e0c4ed5a7999a2481a5c5c
(use file output for authoritative full hash if copying; semantic digest
matches PREPARE). Accept8648 and final3e-5/no-clipping recipe.

Generic VM broker may dispatch LONG via
`gpu.orch_l2_long_backend.evaluate_queued(request, directory, deadline=...)`;
it accepts only shared queue LONG ids / long_coach sanitized payload, invokes
real tool-free existing CLI, preserves usage/raw/receipt and never double
debits the already-reserved queue request. It uses `/tmp/orch_l2_evaluator.lock`;
SHORT's other evaluator calls must also hold that same lock (or use a single
serial broker for all arms) before actual invocation. Do not run separate
unguarded evaluators at current~3GiB available.

Concrete native blocker remains SHORT-owned run/actor dispatch seam, not
ratification:23:48 local driver still has noLONG device/parent selection.
Own guardian now follows shared V2: collect experience1 from8currentTRAIN
receipts NOW, initial parent-free readout before sleep1, then3sleep/readouts.
It consumes `L2_NATIVE_MANIFEST` bound to own snapshot; immutable shared V1
PREPARE/SOURCE never overwritten. No LONG GPU cells or parent calls yet.

2026-09-14T23:58:15Z [Builder] LONG PRE-GPU PASS / LAUNCHING physical1 only.
87CPU tests passed: own parent/backend/hook/lane, shared actor/backend and
native/bridge. Final generic caller matches SHORT RuntimeV3 exactly:
shared_run88e762f2c89b6f8a15e42a316480d3340a52992299ac7f4debb8b42f5529ea71,
actorfb724beb5a437cc6c360df5a224e6899a98581a206c5b106006efaa5742932f0,
native559d8e6ea7002f2651748ba192a57c5cf627381f6a3994d93cb02d63011a3157.
Shared module633d699b/protocol16fa840e unchanged; no reconstructed cohort/source.
Own archivea5b178fe84acbc8511ecad8859a5f7d2c264733a392067628e56848c63177015
verified local/remote;390 source/artifact hashes pass remote CPU verification.
Own PREPARE_LONG_V4 hash5c836c30b195ccbffd9a5e3533451f01ef95242472eab366852807a548ce54e5
binds same initial e226 inventory/base and legacy/recipe/cohort as sharedV3.
Remote local-disk/tmp has2.7TB free; originalV1 source/manifest/publication and
failed scanner receipts preserved, not overwritten without retained copies.

Non-material guardian repair uses the same bound SHORT scanner/service
identities plus exact physical1/A100/UUID/memory checks; old scanner's unrelated
CPU-guardian false positives and transient sshd failures preserved. Detached
guardian retries only transient unreadable sshd (<=5), otherwise fails closed;
actual PASS mandatory before any child Popen. No process exemptions/kills to
obtain admission. Own boot/PID/starttime-bound stop,12h/12GPUh deadline and
earlier shared deadline remain enforced. A1001 GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b
only; other workers untouched. No native/modelcalls before this publication.

Actual conversation in existing6turn grammar: parent invites PARENT QUESTION:
inside child reasoning before ordinary finalaction; hook extracts new questions
at shared0/2/4 review turns, answers or declines using actual evaluator. A
question may spend remaining4decision cap even in an already-coached world;
otherwise one initiative/world. Final-window unanswered questions disclosed.
No extra child turns/reflection, no second actor loop or canned response.

SINGLE shared VM broker2373091 is the backend, commonlock, tool-free/safe-mode,
no fallback. Provider utility+main both reserved before dispatch,600actual
provider slots per bucket/8648total. Own coach transport not double-charged.
Optional standalone LONG backend is not separately launched. JSON cap2048
shared; complete message256/native tokens and1024/cycle,4decisions/cycle remain.
Initial SHORT auxiliary undercount/posthoc repair retained/disclosed.

Main: this is the dated builder preGPU publication for notebook mirroring,
not a request for approval or for Main to run cells. Strongest evidence so far
is native-source/provenance readiness, NOT learning; next concrete receipt
will be own LOADED and actual LONG parent/child calls. Same3sleeps, four
presentations,3e-5/freshAdamW8203/no clipping, zero/variable yield preserved.

2026-09-15T00:01:01Z [Builder → Main] LONG NATIVE LIVE, NOT just CPU scaffold.
Own guardian182923, actual native child182989, physical1 exact UUID. Physical
admission passed before launch; mounted actual named_parameters statee226cea2
and mounted basea2367093 match full expected hashes. `LOADED.json` and native
REQUEST/launch/admission/START copied into own analysis. Current shared broker
2373091 delivered actual firstLONG parent response (0000_LONG_C1), complete
message shown to child, actual provider accounting retained. No canned answer,
backend substitution, duplicate dispatch/debit or Main GPU execution.

Concrete partial00:00:56UTC:9child calls present,2completed experience episodes,
1success/2; first response512tokens/truncated preserved as failure, successful
second episode's6raw turns89–105tokens below150minimum. These observations
establish native collection and the initial richness obstacle, NOT gain,
acceleration, qualified yield, sleep completion or a causal parent effect.
Shared source/readout/control receipts remain separate. First raw call,
episode, parent event/response, INVOCATION and provider accounting archived.

Own bounded guardian continues all3cycle experience/sleep/readout stages;
current phaseC1experience, no manual Main/reviewer/rowcount hold. Sixturns,
actual raw targets only, natural zero/variable rows/no-update readouts retained.
Strongest result: real evaluator→child communication on the correct mounted
native learner. Assumptions: single child/seed, shared source and final recipe;
LONG vs SHORT confounds dose/horizon; SHORT-policy frozen is not LONG-matched.
Falsification remains no parent-free learning/retention advantage or no rich
grounded trainable supply. Compute recommendation: finish this existing
12h/12GPUh envelope, no duplicate controls or extra leases. Peer lesson for
Main: native dispatch success is not richness/learning; accounting must include
utility inference and exact repeated parent exposure, not just CLI launches.

2026-09-15T00:05Z [Builder → Main] IMPORTANT supersedes LIVE: own guardian
STOPPED cleanly after4episodes/16childcalls/2tasksuccesses, before any sleep.
Actual delivered parent108native tokens and firstchild call receipts are
stable in ownanalysis:CALL_0000.json,0000_LONG_C1.response.json,
LONG_PARENT_EVENT_0002.json,LOADED.json,PUBLICATION_V4.json;STATUS.md has full
handoff. Provider Haiku16+Sonnet315 outputtokens,2slots pre-reserved for first
message; no duplicate dispatch. No isolated reflection/compiler/learning claim.

Root cause is SHARED broker parsing, not authorization: raw provider outputs
0001semantic and0002coaching are fenced JSON; json.loads(result) failed.
0002 also names `distillation_for_rohin`. Actual original raw/model usage and
both error responses preserved locally. Hook propagated error and guardian
releasedphysical1; no unknown-process signals, no peer GPUs stopped.

Main relay to SHORT: need non-material lossless envelope/parser recovery plus
resume-current-experience interface; DO NOT regenerate first4episodes or
clear ledgers. LONG will restore own history/used coaching budget. Preserve
original12hdeadline/actualcost and failedstage, and recover actual generated
text only with bound provenance. No replacement actor targets or rubric
decisions. Scientific acceptance/source/cohort/recipe unchanged. Guarded stop
is a real technical dependency, not an added Main/reviewer/1krow approval gate.

2026-09-15T00:13Z [Builder → Main] STRICT ENVELOPE HELPER READY (non-material).
Own gpu/orch_l2_long_envelope.py exports parse_json_envelope(text: str) -> dict;
call with provider_response['result']. SHA256:
82b0867480d50c2073d4149c7139ae3a9ecda64397e0629a5f37bb69f37f3ec3.
Six CPU tests pass, including actual preserved0001/0002, equal parsed semantic
values and identical UTF-8 teacher message/reason/distillation bytes. Rejects
extra prose/malformed objects/duplicate keys/both alias keys/non-JSON constants;
only full json fences and unambiguous top-level distillation_for_rohin alias.
No shared edits, modelcalls, charges, teacher/rubric/gate changes or exposure
repair. Exact import/caller duties in ownanalysis/ENVELOPE_HANDOFF.md. SHORT
owns import and provenance-bound response recovery/shared partial resume.
Original failed receipts and first4episodes stay intact. Own phase/history/
quota snapshot in progress; both coaching attempts already consume decisions,
0002 generated but NOT delivered. Do not reset or debit it twice.
Actual neutral PUBLIC SYSTEM was supplied verbatim; omission hypothesis is
disproved for firstcall. Opaque-label advice preserved as protocol-quality
counterexample without causation. Full RICH GUIDANCE omission is a separate
possible limitation, not current repair authorization. No parent-held scores.

2026-09-15T00:13:23Z [Builder → Main] ENVELOPE + EXACT RESUME EVIDENCE PUBLISHED.
33 LONG CPU regressions pass (6 envelope tests include actual0001/0002).
Helper SHA/signature unchanged from handoff. No shared files edited, no model
retry/duplicatecharge/replay. Ownanalysis/RESUME_ORIGINAL_001.tar.gz preserves
all16calls/fourcompletedepisodes/12parentevents/threequeuepairs and original
ledgers/deadline, SHA cb57a948f9e95e9fc7e3e05f39bfa2db4801ab6084e82ea61ff03ecf0272a7fb.
RESUME_STATE_001.json SHA daf92dd20bff3b425a6f8c42e49d9f7cd9261680de22838c502d2321a1908423
binds full ownhistory, exactpendingrequest, attemptedturns/questionoffsets,
2decisionsconsumed/2remaining,1message/108tokens/1exposure, sixprovider slots.
0002 has remaining_decisions3 BEFORE reservation; do not regenerate it with2
or consume a third decision to recover it. Full ownhistory projection equals
actual0002request history; sleeps remainempty. Exact continuation at e4turn0,
same deadline1789472611.845884, no updates/readouts yet. RESUME_HANDOFF.md
spells out ownership/boundary. This is preserved recovery state, not a claim
that shared partial-stage resume is integrated or native LONG is running.
Main relay: use strict helper now; provide shared recovery boundary to wire
LONG ownhistory/counter restoration without another generic driver.

Envelope/recovery publication remote-verified at
/tmp/orch_l2_long_20260914_attempt1/envelope_recovery_v1.tar.gz,
SHA fb0734987e2220bf20b9668194c1d7aa3585f3577ff82e3f0a6dc56179d0d595.
Local ENVELOPE_PUBLICATION_V1.json binds exact helper/tests/archive and33passes.
No GPU cell or parent process launched by this helper/recovery-evidence work.

2026-09-15T00:19:53Z [Builder → Main] Lifetime physical1 ownership retained.
Exact11path helper/provenance commit9f02db5fb3954980a9f420faa88b2058e9fa419c
created (no blanket staging, no peer files/notebook merges, no retirement).
Six helper tests pass postcommit. Pending0001/0002 recovered queue files now
exist remotely; physical1 remains0MiB. Shared V5 publication not present yet.
Own guardian now has --resume-experience, preserves originalrun, new
run_resume_v5, originaldeadline/start and prior0.0602369795GPUh. Its readonly
prelaunch reconciliation binds snapshot, all originalfiles/ledgers, exact
saved0001/0002results+providerhashes and zero newcharges. Fifteen lane/hook
tests pass including actual originalarchive, byte drift, missing recovery,
teacher edits, duplicatecharge and timer-reset rejection. Will bind V5 and
launch physical1 myself once delivered, not request Main GPU execution.
No raw84scope/cap borrowing, no PUBLIC SYSTEM/exposure repair. Main relay:
shared replay creates new cache timings; original provider timing/error
receipts must remain separately reported in cycle distillation (not mistaken
for original live parent latency). Original advice/firstchild remain intact.

2026-09-15T00:24Z [Builder → Main] LONG RESUME PRE-GPU PUBLICATION, no hold.
Bound delivered sharedV5 ff59e055, archive0fac7689 / manifestad574e17 / same
interface16fa840e; no SHORT V5 edits. OwnV5 preflight caught missing standalone
LONG backend import before GPU; failure preserved. OwnV6 adds unchanged V4
backend dependency, archive544203996b6c01a3ba2e3cc34c50ecd7b1344bf00fb660f6b7f521be3a1d5ac3
verified remotely; native manifest775941482b34b483f76b1fce885e3a3389cf53e4c47f686db0867523b4adb40c.
107CPUtests PASS; all540 snapshotfiles verified remotely. Exact readonly
reconciliation PASS over four originalepisodes/16calls/ledgers/failedreceipts,
zero-cost recovered0001/0002 result+rawprovider hashes. Originaldeadline
1789472611.845884 and prior0.0602369795GPUh retained. REMOTE_PRE_GPU_V6.json,
PUBLICATION_V6.json and PREPARE_LONG_V6.json bind the evidence.
Own guardian resumes only C1experience with --resume-experience then executes
remaining original readout/sleep stages. Shared driver reconstructs hook once;
no independent counter restoration or duplicatecharge. Own distillation now
separates cached-callback timing from original actual request latency/error,
with exact original event hashes; no parent-input or policy change.
Launching own physical1 lifetimeguardian; full existing scanner PASS and
UUID/CVD checks remain mandatory, no peer GPU/node/lease/approval action.

2026-09-15T00:27Z [Builder → Main] Own manifest-alias integration repaired.
Guardian209616/native209663 exited before model load/call with
original_runtime_manifest_missing: own new-manifest alias had hidden V4 at
sharedV5's lookup. OriginalV4 file always preserved. No child/provider calls
were made; first4episodes/16calls/ledgers remain identical. Failed receipts
RESUME_V5_TERMINAL.json/exposure log retained; cumulative0.0603387021GPUh.
OwnV7 restores PREPARE_LONG.json to originalV4 and binds NEW native manifest
explicitly; sharedV5 is unchanged.109CPUtests pass. Remote actual shared
continuation_records passes on four originalepisodes BEFORE GPU, not just a
mock.540files verified, same originaldeadline, zero calls. Own archive
d630ab7cde5c1ac04eb03d7f616aa89024f080bafd56eac68a20e3ff6ba734b9;
manifestef137d9ee2797f6285c339e4a2f498df7a0b5745e25bb8a34c29e09601e8c3f4.
PUBLICATION_V7/REMOTE_PRE_GPU_V7 bind resumedrun_resume_v5_02 and prior cost.
Relaunching physical1 only; no original episode/provider retry or peer repair.

2026-09-15T00:29:53Z [Builder → Main] NATIVE LONG RESUMED, lifetime retained.
Actual guardian212185 / native212275 physical1; mounted adaptere226cea230b4...
and base provenance preserved. CALL_0016 is the first new native child response
after original16, noerror and actual recovered0002message present in context.
LONG_PARENT_EVENT_0024 records86native parenttokens. PARENT_CACHE_0003 records
zero provider calls and zero request reservations for original0002, not a retry.
NATIVE_RESUME_MILESTONE.json verifies42 originalfiles byte-identical, original
16child/3parent ledgerprefixes unchanged; no oldepisode replay/rescore/modelcall.
Observed26totalchildcalls/5completedepisodes; these are continuity counts,
NOT learning/gain. Ownanalysis contains CALL_0016, RESUME_LOADED,
PARENT_CACHE_0003 and milestone; source/publicationV7 stable remote. Guardian
continues original C1collection/readout0/sleep1/readout1/C2/C3, originaldeadline
and cumulativeGPUh. No Main execution/approval or source/cohort/control rebuild.
Recovered semantic output is the same previously generated evaluation, not
new grading; original error/gate receipts remain historical. Cached transport
timings are separated from original provider latency in own cycle distillation.

Exact19path native LONG implementation/provenance commit66768c8a7644dd018e5108eb375d57fe91fec630
now published locally; no peer edits/staging/merges. Earlier helper commit
9f02db5f remains unchanged. Main handles cross-notebook merges; own STATUS.md
now correctly reports resumed native activity rather than historical STOPPED.

2026-09-15T00:57Z [Builder → Main] CONCRETE SLEEP1 MILESTONE + boundary recovery.
Your idle-device snapshot was a stopped own chain, not release. Guardian212185
completed C1experience (16episodes/78calls/6tasksuccesses/2admitted rawrows),
initial parent-free readout0 (11/16goals), and native sleep1 (28updates).
LoRA changed e226→ad2d1065a97b88b183c001baf48117886d16ab66fe8f305158d7adfc00882cec;
basea236 unchanged. This establishes actual training, not a learning/gain claim.
At00:43:36UTC it stopped BEFORE readout1 on inaccessible sshd224055 and
sftp-server224056; no GPU owners, no child phase launched, no fit failure.
All COMPLETES and failedguardian/admission preserved in ownanalysis C1_*,
C0_READOUT_COMPLETE and STAGE_BOUNDARY_*; prior cumulativeGPUh0.3306937765.

Own non-material guardian repair: bounded10 rechecks for transient sshd/sftp,
still fully CLEAR/UUID/CVD required, persistent unknowns/owners fail closed;
no service exemptions, signals or sharedV5 edits. --resume-stages verifies
contiguous receipt-hash/lineage/guardian prefix and starts ONLY readout1, then
remaining original C2/C3. Already-started next stage is refused, not replayed.
115CPUtests pass; actual remote prefix/newadapterfiles and540sourcefiles verify.
Own archive8c2889a485221d771842bd2439fc3b2a42d997060725a9451007e547adf84579;
manifestef6107818c2651ecce835b7a361f6d048c92616ff525ffb029a2f933446b0215.
PUBLICATION_V8/REMOTE_PRE_GPU_V8 bind originaldeadline1789472611.845884 and
all priorGPUh. No child/provider replay, quota reset or source/benchmark change.
Launching own physical1 readout1. Parent distillation C1:4decisions/4messages,
378generated parenttokens;18actualexposures/1642exposedtokens. Original latency
30.0175s + laterlive latency separate from0.00483s cached callbacks; backend
failure preserved. Zero childquestions; final-window/question cap limitation
and SHORT-policy frozen-control mismatch remain, no causalcomparison yet.

2026-09-15T00:59:43Z [Builder → Main] READOUT1 NATIVE RECOVERY CONFIRMED.
New own guardian236763 / native236830, full CLEAR admission. Actual mounted
ad2d1065... child from completed sleep1, basea236 unchanged. First readout1
call index203 follows exactly78 C1experience +125 initialreadout calls; no
index resets, no replay/refit or parentcalls for recovery. Three completed
receipt hashes remain byte-identical; prior0.3306937765GPUh/deadline unchanged.
STAGE_RECOVERY_MILESTONE.json and C1_READOUT_LOADED/RECOVERY_ADMISSION/LAUNCH
are stable ownanalysis evidence. All remaining C2/C3 stages remain under this
same lifetime guardian. No release of1 and no dependency on pilot3/SHORT0/2.
Strongest result is actual28-update sleep and fresh-process post-sleep readout,
not a causal gain. Next useful report is completed readout/sleep or an error,
not another fleet census. Peer lesson: bounded CLEAR-only retries and exact
completed-stage prefixes prevent benign transport churn from causing replays.

Exact18path guardian-recovery/sleep1 evidence commit9905adfc4fd6a1805cd778f51bd20459a5be9164
published locally for Main; no peer/shared files staged or merged. Lifetime
physical1 remains LONG; current guardian236763 owns remaining native stages.

## Terminal audit — Main only, 2026-09-15 UTC

[Builder → Main] Native LONG COMPLETE at01:26:38UTC; all10original stages,
three sleeps28/0/0updates, final CLEAR release of physical1, cumulative
0.8087686875793669GPUh. Originaldeadline unchanged. No new run/replay or broker
mutation. Final LONG held11/8/9/9 of16; W0/W8/audit16/16 throughout. No positive
learning advantage demonstrated; zero-yield C2/C3 preserved, not refit.

NEW accounting obstacle found in terminal audit: original LONG semantic
0004_LONG_C1 and0016_LONG_C3 stdout report is_error=true/num_turns=4, output
maximum2048 exhaustion, although INVOCATION says attempts1/--max-turns1.
Original responses fail closed with empty reviews; no target rescue authorized.
34provider ledger reservations are NOT34actual model calls: reported main
turns23 +17utility invocations =40turn-based model invocations. No owner-issued
retry; hidden CLI continuation occurred. Preserve ledger; no retroactive claim
of correct pre-dispatch reservation. Main should retain this as a protocol/cost
limitation, not silently amend the frozen broker or rerun these requests.

Read-only same-ledger-ID reconciliation also finds SHORTbucket192 vs184slots
(0008_UNPARENTED_C1:4turns;0047_SHORT_C2:3;0054_SHORT_C2:4), FROZEN187 vs184
(0039_FROZEN_C2:4). LONG675 learner calls; original batch ledger3554 versus
CLI-reported-turn-based3571, still below8648 observed envelope. Provider wire
attempts are not independently exposed by these receipts; exact network retry
count is not claimed. This supersedes any earlier claim that modelUsage-key
counts alone establish actualprovidercalls. Broker remains untouched.

Terminal publication: `research_notes/analysis/orch_l2_long_20260914_attempt1/`
contains FINAL_REPORT.md, FINAL_AUDIT.json, FINAL_TERMINAL.json,
FINAL_RELEASE_GPU1.json and FINAL_PARENT_EXPOSURE.json. Own offline
audit_terminal.py reconciles all10completion receipts, original4episodes/
16calls byte-identically, all675learner receipts, three-sleep adapter chain,
same-stage control tasks, and provider outcomes with the disclosed exceptions.
Final both-goal pairs5/2/2/1 of8 reinforce the absence of demonstrated cohesive
learning advantage; retention16/16 is a ceiling, not progress. Parent dose12
messages/1138tokens/4373exposedtokens vsSHORT82/9137/26779 is lower involvement,
not evidence of better efficiency. Recommend no extension/replay/newLONGrun.
Full report includes per-cycle Rohin distillations, preserved bad advice,
explicit SYSTEM exposure, frozenSHORT-policy mismatch and cost caveats.

Own native archive8f770ed7602afc3121dfd2e4d03f4bd75e68b1e45a6e4f048cf3c676b4f93331
and provider archive730c9fda9711cc6c18cdf9b1568ba715a3c0e46865c054f43abf7bcf26dce0df
are copied and hash-verified on A100 /tmp/orch_l2_long_20260914_attempt1/.
Raw control-cost archive28a4e7c35af2a62d775456989f3bde0aefdfb297eef6b8f1c3f6eddebc8998d7
is a read-only provenance copy, not a shared-ledger edit. FINAL_PUBLICATION.json
binds final local/remote artifact hashes. Main handles cross-notebook updates;
no direct peer messages, shared changes, or broker lifecycle actions taken.
