# GAME-ORTHOGONAL worker journal

## 2026-09-14T21:57Z — readiness / prospective protocol to Main

READY to implement and CPU-verify; GPU launch awaits Main's published W1 board
and committed/pushed dated pre-GPU notebook line. Main never executes this cell.
Worker owns only new `gpu/orch_game*`, `organism_v6/orch_game*`,
`tests/test_orch_game*`, `research_notes/analysis/orch_game*`, and this journal.
Staging coordination request: worker will use a private Git index and commit
only its owned paths; Main must acknowledge a commit window before publication.

Orthogonal hypothesis: coherent observable transitions make grounded reflection
more useful than isolated QA. This is a DEV pool screen, not an H1/H2 result.
Portable37ec is provenance-bound DEV, not an uncontaminated new lineage.

Native inspection: A100 has no TextWorld/ALFWorld in either existing runtime.
The existing `/localhome/local-rohing/cgym_test/venv/bin/python` has Gym 0.21.0
with its off-the-shelf deterministic text-game `Taxi-v3`. Use that installed
environment immediately, not an invented game or downloaded model. Environment
CPU subprocess is separate from the unchanged portable actor's v2 runtime.
Taxi is a simple navigation/delivery text game, not a TextWorld household gym;
this limited pilot does not establish rich-household or general-game transfer.

Prospective freeze before any model generation:
- Mining task families: `Taxi-v3/aboard-delivery-R`, seed 14001; and
  `Taxi-v3/aboard-delivery-G`, seed 14002. Eight unique states per family.
- Held L1 validation task families: `Taxi-v3/aboard-delivery-Y`, seed 24001;
  `Taxi-v3/aboard-delivery-B`, seed 24002. Eight unique states per family.
- Select distinct taxi positions with exact shortest terminal distance 3–6,
  passenger already aboard, seeded permutation of the complete eligible set.
  Preserve full selected state IDs and native transition table hash before LM.
  These are disjoint destination task families inside one existing environment,
  NOT untouched environment families. L2/L3 remain proposals pending Rohin.
- Screen only the 16 mining states, paired RICH/TERSE, same frozen actor,
  observation, goal, deterministic greedy decoder and six-step cap. All 32
  episodes remain denominators. Maximum 192 model calls / 98,304 output tokens;
  2,048 input tokens and 512 generated tokens per call. Four shards, four
  matched states each, A100 physical GPUs0–3 only. Counterbalance arm order.
- RICH requests first-person 150–400 tokens, exact observation references,
  useful goal connection, grounded checkable expectation, action last. TERSE
  requests only the same action. Length and headings are diagnostics, not the
  semantic gate. Observations contain the actual map, position, passenger and
  goal, action outcomes, and reference IDs; no oracle solution is shown.
- Success = native environment terminal delivery with reward20, independently
  replayed from the frozen initial state. Invalid format/actions consume a
  turn and remain failures; no parser repair. Preserve all raw calls, text,
  format, termination, outcome, feedback and semantic denominators separately.
- Admission: RICH must exceed TERSE by >=4/16 successes with exact one-sided
  paired sign-test p<=0.05 and at least eight RICH successes. Otherwise
  deallocate this declared pilot, report an inconclusive/non-admitted pool,
  never say the orthogonal hypothesis is disproven. No adaptive extra seeds.
- Outcome-qualified rich episodes require full-text semantic review of EVERY
  turn: PASS/FAIL/UNRESOLVED and exact cited spans. Any unresolved/failed turn
  excludes the episode. Rich text alone or headings never admit rows.
- Child-only success, grounded correction plus useful child lesson, and own
  record rows are eligible categories, never hand-authored targets. Student
  prefixes omit rich instruction and parent feedback; parent loss is absent.
  No target writing, fit, or automatic admission in this screen.

Scale limitation: Taxi's fixed small state space cannot honestly supply >=1000
independent initial states. If this pilot passes, submit a separately frozen
off-the-shelf richer L1 game collection before scaling; do not relabel duplicate
states as diversity. >=1000 admitted unique child corpus rows is the future
capacity target. Any eligible fit requires a same-batch FULL/loss-off pair,
16 presentations plus legacy rehearsal, held fresh-process parent-free readout,
and old facts/audits >=15/16. None is authorized by an unreviewed pilot yield.

Operational root: `orch_game_20260914_attempt1`; local packaging only under
`/data/home/rohing/dream-state-orch/research_notes/analysis/orch_game_20260914_attempt1/`.
Use an exact source archive hash, existing local Qwen2.5-7B-Instruct files,
portable manifest5e675c30… and adapter37ec3788…; no weights download/rebuild.
Every shard gets a lease-aware guardian with a 2400-second absolute maximum,
60-second shutdown reserve and >=6-hour lease margin. Before launch bind GPU
index+physical UUID, compute PIDs, and `/proc` CVD/start-time identities. Unknown
owners mean no launch, never kill; no process-name kills; keys env-only and
hosts only `gpu/hosts.env`. No native GPU calls have occurred.

Main action now: publish W1 admission/ownership for this bounded screen and
confirm staging window. I will append exact CPU/provenance/source receipts and
a ready-to-append `[Builder]` launch paragraph here, then execute independently
after Main commits/pushes that paragraph. Peer message: full observability can
remove opaque-ID bookkeeping without inventing behaviour targets, but an easy
environment may eliminate the rich-over-terse gap and must then be retired.

## 2026-09-14T22:03Z — CPU implementation and resource check update

Main published W1 at9a9593af and explicitly delegated conflict-safe EOF-only
notebook entries plus exact owned-path publication; no further commit window
wait. Nine screen CPU regressions and four portable bundle regressions pass.
Installed Taxi-v3 native `step` matches all3000 exported deterministic state/action
transitions. FROZEN_BANK SHA256
`8d12ddb1e71df09fde3bacbb7eed83cbf9ee1a88e557667a9209ee0d1455dbc1`;
the32 frozen IDs include16 mining and16 held L1, all before native generation.
Local base/tokenizer/adapter/source provenance passes with no GPU calls.

First physical scanner check correctly FAILED CLOSED: its own active SSH
session had an unreadable `/proc/<pid>/environ`. No compute process or assigned
CVD owner was found, but that is not admission. Preserve PRE_GPU_PHYSICAL.txt.
Run checks after the SSH session naturally exits; guardian retries boundedly
and never exempts or kills an unknown PID. No GPU launch until an actual clean
UUID+compute+process scan is captured and the dated notebook line is published.

## 2026-09-14T22:04Z — pre-GPU ready; publication then autonomous launch

13/13 own screen/portable CPU tests PASS, guardian `bash -n` PASS, all3000
native Taxi transitions PASS, original invalid-format/budget regressions PASS.
Four detached physical GPU UUID+compute PID+/proc CVD scans PASS after the
transient own SSH process naturally exited. Preserve both failed and clean
checks. Own archive SHA256
`c58f7671411937dbee12246f8c3454bf842eef0843460b6b65dd8f058b7bf043`;
source manifest490files SHA256
`3b081fca8374cd8859190c1c4df6114fb61a390d78c184319784fc489cbaf001`.
Actual PREPARED_NO_GPU verifies frozen bank, base/tokenizer and portable37ec
without native calls. No header/content surrogate and no fitted weights.

Rohin/Main clarified the booked A100 lease ends2026-09-27T05:05Z; guardian
uses that exact bound minus6hours and a stricter2400seconds/shard cap with60s
shutdown reserve. Destination splits are WITHIN the same Taxi environment
family; do not describe them as unseen-family evidence. L2/L3 remain untouched.
Publish only owned paths plus this worker's dated EOF notebook receipt now;
on push failure stop and reconcile without force. Main need not acknowledge.

## 2026-09-14T22:05Z — launched after preGPU publication1fd5d077

Four guardians started2026-09-14T22:05:01Z. Physical0/1/2/3 guardians are
151826/151827/151828/151829; native Python152023/152015/152019/152027.
Deadline for all=2026-09-14T22:45:00Z (epoch1789425900), shutdown starts no
later than22:44Z. Guard resource scans PASS; native `/proc` UID/start_ticks/
CVD checks bind each known Python PID to its assigned physical UUID. All
initialization and generation are worker-owned, not Main. No fit processes.
Receipts LAUNCH_REQUEST.txt, LAUNCH_NATIVE.txt, NATIVE_PID_CVD.json. Native
result is pending; process existence is not completion or demonstrated gain.
