# Activation4 execution outcome — 2026-09-17 09:17 UTC

Main's explicit operational authority was logged before the single dispatch
at 09:06:09 UTC. Ordinary `execute` ran once for C1/C2/C4 from their exact
activation4 successor sources. No C3/C5 restart, parent action, source edit,
targeted replay, wall change, or uncertain retry occurred.

## Actual outcomes

| Life | CPU operator / start ticks | Outcome |
|---|---|---|
| C1 | 4068492 / 17152921 | Safe 600-second boundary timeout; no termination intent or retirement. Original native2578597/start14835459 alive, state S at09:16:10.439 UTC. |
| C2 | 4068493 / 17152921 | Strict admission and actual LOADED3581, then exact invitation exposure REQUEST3590. |
| C4 | 4068494 / 17152921 | Safe 600-second boundary timeout; no termination intent or retirement. Original native2619696/start14891073 alive, state R at09:16:10.441 UTC. |

C1/C4 failure class is `TimeoutError: no_boundary_old_native_left_running`.
Both CPU operators exited. Neither original was left paused. This does not
authorize a retry: any later handoff needs fresh readiness and Main authority.
The observations establish no qualifying boundary within the wait, not a
diagnosis of why those lives did not present one.

## C2 continuity and exposure

- Native4077813/start17169605, timeout4077812/same ticks. LOADED3581 at
  09:09:54.531447 UTC: resume=true,3024 optimizer steps and adapter SHA
  `1b16201b6356533cebd461f271f5174d61bae6ad755e50c9a3202e1c86e897fc`
  match actual SAVED_PROOF. LOADED record/intent/chain, native argv/cwd/cgroup,
  timeout identity, GUARD/PLAN/LAUNCH hashes and wall1789776000 verified.
- GUARD SHA `f1f858a4ce133cc59ed24b78f23db632ba866d6fbba41578ed2d8f466f093066`;
  PLAN SHA `331abbc0655e4a3bd73f12ce135402f838e0149d8e71054f022c0b0c44868b2e`.
- First resumed own triple3582→3583→3584, segment96, terminal423 tokens.
  Next3585→3586→3587, segment97, terminal453 tokens. Both exact original
  prefixes/targets/token IDs join to committed own TRAIN rows, prefix masked.
- Invocation3588, cycle33; exact invitation rendered in REQUEST3590 at
  09:14:06.328222 UTC, segment98, message8 user span[0,1257), history masked.
  Invitation SHA `c3d2e219e024baff2e2bde638d0caa303fb408d89afd8b305deaf4187839d56f`.
  No response to this invitation was claimed by this bounded observer.
  Source adoption and actual rendered exposure are established; semantic
  correctness, adoption by the learner, or learning benefit are NOT adjudicated.
- Mendel/Main notified through COORDINATION on actual LOADED and exposure.
  Parent migration remains Mendel's responsibility; C2/C4 parent successors
  were not touched. C1 retains its original native binding.

## Immutable local receipts

All files below are in this directory; JSON receipts and completed observation
files are read-only. The read-only observer finished normally, with empty
stderr; 1200-second/64MiB caps and15-second polls, no held-file reads.

| File | SHA256 |
|---|---|
| ACTIVATION4_MAIN_GOS.jsonl | 9169b8f4ae888a10142d5fcd7135a8e975fef9e103cca747e5211113a4ec480a |
| ACTIVATION4_MAIN_DISPATCH.jsonl | 1fe6e16bb7494f34d8b1de7828b65fb0e328eb3511ccb62cfa3b1eddcee2862e |
| ACTIVATION4_C1_SAFE_TIMEOUT.json | 23776425f6eb821c647b4262f14a55c57ab2e92d7f4300949aafd697d7f03c93 |
| ACTIVATION4_C2_CONTINUITY.json | 0516733b358900516610017df037f14a9dadaf55d62c86972f7a268e46473942 |
| ACTIVATION4_C2_EXPOSURE.json | 42e0b210145dc96c2a3e64995afcc51d5fb7179e6067cb27a7bf2c42b7fc6559 |
| ACTIVATION4_C4_SAFE_TIMEOUT.json | 7e2ca2813490a985ce1e27e6e9777f1b08cb5008ab2c6269cb6e66dad454dc3f |
| ACTIVATION4_OBSERVATION.jsonl | 4ddbaf4cb7d910fe3c58f41ff32a04f97383162874eefe6252452c3d45abdd43 |

Remote attempt roots remain
`/localhome/local-rohing/orch_r166_retelling_C{1,2,4}_20260917_activation4`.
Exact per-life GO bytes/bindings and their hashes are in MAIN_GOS; each has
fresh actual-now+1800sec validity, original wall and600second wait/pause.
Old attempts/GOs and all failed artifacts remain intact.

Reviewed pre-dispatch CPU_ACTIVATION4.log:102 tests+63subtests PASS;
actual successor subprocess readiness was Main-reviewed. No runtime source
changes or additional test claims were made during execution/observation.
