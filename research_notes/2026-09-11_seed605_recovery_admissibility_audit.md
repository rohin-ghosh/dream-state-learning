# R4_B_seed605 recovery admissibility audit

**Audit time:** 2026-09-12 01:10--01:13 UTC  
**Scope:** read-only inspection of the live node-1 recovery; no process was
stopped, started, or modified.  
**Operational verdict:** **ALLOW THE RECOVERY TO FINISH, THEN QUARANTINE THE
MUTATED SLEEP-128 ACCEPTANCE HISTORY.** A stop is not warranted. The recovered
terminal ON/OFF endpoint is admissible for the already-exploratory R4 analysis
if the incident is disclosed. The recovered directory is not admissible as a
pristine record of per-sleep acceptance decisions, and R4 remains non-paper-
grade for its pre-existing design reasons.

## What was complete at the first crash

The authoritative node-1 state showed:

- all **128 wake markers** (8 episodes each = 1,024 episodes);
- all **32 `COMPILED` markers**;
- `sleep_1024/corpus.json` and `waking_brief.txt`, written at
  `2026-09-12T00:25:13Z`;
- report probes through episode 960 (16 ON probe files including ep0000;
  15 adapter-OFF files);
- accepted sleep-992 adapter;
- no sleep-1024 parent brief, adapter, gate, final probes, or `LIFE_DONE`.

Fixed terminal inputs at audit time:

| artifact | SHA-256 |
|---|---|
| `sleep_1024/corpus.json` | `7e32d8805ef22b4e3635f82e0d72158f906b8712b0c354df4b1812dd93872940` |
| `sleep_1024/waking_brief.txt` | `ecdfd4442ba35af3f149f44e1b9cd68a0df996359834fb5b27dabc099497f84e` |
| `ledger.jsonl` | `cc16b2bc3ff452221a50ed05acdc70494025cfcc56dc75aa1705a37d6bb01767` |

The recovery process was live as PID 1511871 with the intended arguments:
arm B, seed 605, 1,024 episodes, rank 8, probe gate, and the 14B parent at
port 8011.

## Resume semantics: what is and is not idempotent

`run_life_v2.py` restarts its loop at episode zero and relies on artifact
markers rather than restoring a program counter.

Safe/idempotent in this recovery:

1. Existing `wake_*.json` files suppress wake replay, so the lived trajectory
   and ledger are not regenerated.
2. `COMPILED` suppresses recompilation, so every historical corpus and the
   already-written sleep-1024 corpus remain unchanged.
3. Existing `parent_brief.json` makes `parent_brief()` return immediately, so
   sleeps 32--992 do not call the parent again.
4. Existing probe JSON suppresses probe generation/re-execution. (The runner
   still needlessly reloads models at old probe boundaries, but this writes no
   scientific output.)
5. An adapter carrying `adapter/DONE` suppresses retraining.

**Not idempotent:** the adapter condition checks only `adapter/DONE`; it does
not treat `REJECTED_*` as terminal. Seed605 had exactly one rejected sleep,
sleep 128. The recovery therefore retrained that adapter. Training has dropout
and no explicit RNG seed, so this is not a deterministic replay. Worse,
`probe_gate()` called `run_probes_batch()`, which saw the existing
`probe_gate0128.json` and skipped evaluation, then reused that old candidate's
score to judge the new candidate.

This happened, not merely could happen:

- original `sleep_0128/adapter/REJECTED_SCORE` remains, timestamped
  `2026-09-10T03:52:35Z`;
- a new `sleep_0128/adapter/DONE` appeared at
  `2026-09-12T01:07:00Z`;
- the adapter weights and `train_meta.json` were overwritten by the new fit;
- `sleep_0128/gate.json` was overwritten at `01:09:27Z`;
- `probe_gate0128.json` retained its original `2026-09-10T04:06:08Z`
  timestamp;
- the new log reports candidate 0.4925 accepted against the restart-time
  floor 0.4878, whereas the original log reports that same stored candidate
  score rejected against its then-current floor 0.5239.

Thus the directory now has contradictory `DONE` and `REJECTED_SCORE` receipts,
and any analyzer that counts current `DONE` markers will falsely rewrite the
life's acceptance history.

## Why the terminal endpoint remains recoverable

The sleep-128 mutation is isolated from the missing terminal computation in
this particular life:

1. Sleep 992 remains the lexicographically latest accepted adapter, so
   `latest_adapter()` continues to select sleep 992 after the ancient
   sleep-128 mutation.
2. The sleep-1024 corpus was compiled **before** the crash and the restart
   skips it. It therefore cannot ingest the mutated adapter or a new parent
   response.
3. `train_adapter.py` fits every sleep adapter from the frozen clean base over
   that sleep's cumulative corpus; sleep 1024 does not initialize from any
   earlier adapter.
4. The terminal gate has no existing `probe_gate1024.json`, so its candidate
   probe will be fresh. R4 uses the legacy (no separate gate-panel) rule: its
   floor comes from the latest report ON/OFF probes (episode 960), not from the
   newly relabelled sleep-128 gate.
5. The final episode-1024 ON and OFF probe files do not yet exist and will be
   produced fresh. These probes use `gym.birth_prompt()`, not the waking or
   parent brief.

The fixed ledger deterministically makes the terminal parenting detector fire
(`same_recipe` + `flat_predictions`; ritual true). The relaunched parent server
will therefore make a fresh, unseeded sleep-1024 parent call. That call is the
first attempted terminal brief, because the original call failed before a
receipt was written. It is under the same v3 prompt/model policy, but its exact
text is not counterfactually reproducible after the server reset. This does
**not** affect the terminal adapter, gate, or probes: compilation already
finished, parent text is outside `corpus.json`, and probes use the clean birth
prompt. Mark or exclude this last brief in analyses of exact parent-text
continuity.

## Exact work still missing at audit time

The live recovery must still produce, in order:

1. `sleep_1024/parent_brief.json` and, because ritual is true, likely
   `parent_brief.txt` plus a parent-ledger row;
2. sleep-1024 adapter weights, config, `train_meta.json`, and candidate status;
3. fresh format-canary result;
4. fresh `probe_gate1024.json`/ledger and `sleep_1024/gate.json`, followed by
   `DONE` or `REJECTED_*`;
5. fresh `probe_ep1024.json`/ledger;
6. fresh `probe_ep1024_adapterOFF.json`/ledger;
7. `LIFE_DONE`.

## Required disposition after completion

- Preserve the contradictory sleep-128 receipts; do not silently delete or
  normalize them.
- Flag sleep 128 as `RECOVERY_RETRAINED_WITH_STALE_GATE_EVIDENCE`; exclude it
  from acceptance-count, rejection-rate, or gate-trajectory analyses.
- For score trajectories, use the already-existing original probes through
  episode 960 and the newly recovered episode-1024 pair, with an incident flag.
- Treat the final endpoint as exploratory R4 evidence, not a pristine or
  paper-grade replicate.
- Before any future restart, make rejected statuses terminal too, bind a
  candidate identity to its gate evidence, and add a restart regression test.
  That is a non-material recovery repair, but it should not be applied to this
  already-running process.

## Terminal addendum — 2026-09-12 02:24 UTC

The recovery reached `LIFE_DONE`. An independent terminal inspection found:

| measurement | exact value |
|---|---:|
| final adapter ON | `0.48779287089022094` |
| final adapter OFF | `0.4671571454612038` |
| ON minus OFF | `+0.02063572542901714` |

Sleep 1024 committed operationally safely. Its fresh candidate gate mean was
`0.48779287089022094`, exactly equal to the previous ON floor
`0.48779287089022094` and above the gate's adapter-OFF base
`0.4784264535800406`. `score_ok=true`, `brevity_ok=true` (`16.0` candidate
chunks/episode versus `12.0` for the base), and the log records a format-canary
rate of `0.92` with `pass=True`. The sleep-1024 adapter has `DONE` as its sole
terminal verdict, the final mounted-adapter probe matches the fresh gate
exactly, and `LIFE_DONE` exists.

The endpoint is therefore usable only as **recovered exploratory evidence**:
the mounted terminal adapter beats its contemporaneous adapter-OFF probe by
about `2.06` percentage points, and the fresh terminal write preserved the
previous mounted-adapter score and interface. It did not improve over sleep
960. The directory remains historically contaminated by the non-idempotent
sleep-128 replay and cannot count as a pristine writer, parenting, or restart
replicate. Sleep 128 stays excluded from all gate-history analyses, and the
recovery incident must accompany any use of the terminal endpoint.
