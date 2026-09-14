# Cue-loss control and optimizer-seed sensitivity: independent reduction

2026-09-14. Scope is only this new memo. All earlier analysis scopes are released. Read-only evidence comes through `bash gpu/ovx_ssh.sh` from:

- Primary **P**: `/tmp/astra_cue_sleep2_20260914_attempt1`, supplying cue-replay seed0 and the shared S1 readout.
- Sensitivity **S**: `/tmp/astra_cue_sensitivity_20260914_attempt1`, supplying `CUE_REPLAY_seed1`, `CUE_REPLAY_seed2`, and `CUE_LOSS_OFF_seed0/1/2`.

All six training/readout pairs are COMPLETE. Primary cue seed0 finished its readout at09:45:40.507995 UTC; all five followups finished by09:58:44.925254 UTC. No jobs, model/tokenizer/scorer loads, remote writes, notebook changes, adapter transfers or new custody directories were used. Other agents' files were not changed.

## Result that survives the loss control

Across optimizer seeds0,1,2, cue-loss-on produces **8/8 held-text GOAL arrivals,8/8 READ uptake and4/8 second-READ episodes**. Each cue-loss-off control produces **4/8 held-text arrivals,0/8 READ uptake and0/8 second READs**. This distinguishes learning the read/conditional-continuation behavior from merely forwarding cue examples alongside memory replay.

The three cue-loss-on runs have identical raw actor-action and reader-response sequences across all four task panels, not merely identical aggregate counts. Retention remains4/4 on each recall wrapper in every state/control, but **unseen-address MISS remains0/4 everywhere**. These are conditional successes on a fixed development panel, not a qualified general memory/controller result.

**Old-task accuracy has no robust cue-loss advantage:** cue-on gets4/4, but loss-off also gets4/4 at seeds0 and2 without any READ. Loss-off seed1 gets3/4. Thus cue-on's4/4 cannot be credited uniquely to cue supervision or contrasted only against the original S1's3/4. The one seed1 difference is reported, not hidden, but it does not establish a stable old-task advantage.

## Exact task-panel counts

Each cell is **GOAL arrivals /episodes with ≥1 READ /episodes with exactly2 READs**, each out of4. Counts were independently recomputed from individual `*_EPISODE_*.json` files: raw READ commands and memory traces, plus actual outcome equality to the public GOAL. Files match the corresponding RESULT/PANELS episode records, and recomputed counts match their summaries.

| State /training arm | HELD_TEXT_0 | HELD_TEXT_1 | OWN_PARAMETRIC | OWN_READER_OFF | Native calls |
|---|---|---|---|---|---:|
| Shared S1 before second sleep | 2/0/0 | 2/0/0 | 3/0/0 | 3/0/0 | 28 |
| CUE_REPLAY seed0, primary | 4/4/2 | 4/4/2 | 4/4/2 | 2/4/4 | 68 |
| CUE_REPLAY seed1 | 4/4/2 | 4/4/2 | 4/4/2 | 2/4/4 | 68 |
| CUE_REPLAY seed2 | 4/4/2 | 4/4/2 | 4/4/2 | 2/4/4 | 68 |
| CUE_LOSS_OFF seed0 | 2/0/0 | 2/0/0 | 4/0/0 | 4/0/0 | 28 |
| CUE_LOSS_OFF seed1 | 2/0/0 | 2/0/0 | 3/0/0 | 3/0/0 | 28 |
| CUE_LOSS_OFF seed2 | 2/0/0 | 2/0/0 | 4/0/0 | 4/0/0 | 28 |

For each cue-on seed, HELD_TEXT_0, HELD_TEXT_1 and OWN_PARAMETRIC each have per-episode READ counts **[2,1,2,1]**, hence six READ calls per panel. In each such panel, episodes0/2 observe a first-record GOT/GOAL mismatch and read the second record; episodes1/3 commit after a matching first record. The final retrieved record matches AT/NODE, GOT/GOAL and the committed DID in all twelve episodes. OWN_READER_OFF has **[2,2,2,2]**, hence eight READ calls, but only two arrivals. Cue-on total across the four task panels is26 READ calls; controls and S1 use zero.

HELD_TEXT panels provide researcher-supplied exact EVENT text at new evaluation identifiers. Their improvement is transfer of contextual read/route behavior, **not recall of those unseen events from the adapter**. OWN_READER_OFF disables the adapter only for reader generation; it is not a forced-MISS or blank-text intervention, and the actor retains its adapter. The within-cue-on4→2 old-task drop shows dependence on the reader channel in that learned policy, but does not show an accuracy advantage over loss-off's direct no-READ policy.

## Retention, MISS and seed dependence

| State group | RECALL_W0 exact | RECALL_W8 exact | UNSEEN_MISS exact |
|---|---:|---:|---:|
| Shared S1 | 4/4 | 4/4 | 0/4 |
| CUE_REPLAY, each seed0–2 | 4/4 | 4/4 | 0/4 |
| CUE_LOSS_OFF, each seed0–2 | 4/4 | 4/4 | 0/4 |

Recall was recomputed from terminal, untruncated raw generations equaling each recorded expected EVENT exactly. MISS requires exact **`MISS\n`**, per the frozen readout source; all four unseen probes fail in every run. Recall success on four previously exposed events and two wrappers is a limited retention check, not broader memorization/generalization coverage or calibrated refusal of unknown addresses.

Both held panels have arrival bits **[1,0,0,1]** for S1 and every loss-off seed, versus **[1,1,1,1]** for every cue-on seed. HELD_TEXT_1 episode2 is a malformed multi-port output in S1 and controls (`ROUTE P_2AA66KVPFZ,P_Q4RVHCV3YN`), not simply a valid wrong-port choice; the independent reduction retains this failure rather than assuming every raw command parses.

On both old-task panels, S1 arrival bits are **[1,1,0,1]**; loss-off seed1 changes them to **[0,1,1,1]** despite retaining the same3/4 total. Loss-off seeds0/2 achieve **[1,1,1,1]**. Thus some old-task behavior is seed-dependent even when aggregates tie. Cue-on is identical across these three optimizer seeds on the retained task trajectories, but this is **not three independent S1 models, new data collections, or new held-bank draws**. All seeds start from the same trained S1 and use the same32 memory rows,20 cue rows and banks.

## Loss-off control and denominator receipt

All six runs use200 fresh-AdamW updates, learning rate3e-5, batch4: **two cyclic memory rows plus two cyclic cue rows**. They present400 memory examples and400 cue examples. CUE_LOSS_OFF keeps the cue inputs in the forward batch, but masks all their target labels to−100; it has400 cue forward presentations and **zero cue-supervised presentations**, not zero cue exposure.

Persisted `MASKS.json`, `TRAINING_ROWS.json`, actual loss-log row indices and original S1/source bindings agree across all six runs. The shared masks are the original unmasked row encodings; control masking is applied during batch construction. I reconstructed the control's active counts from these arrays and indices and checked every followup's logged counts/scales. No tokenizer, post-forward tensor dump or numerical loss recomputation was used.

| Per200 updates | Cue-loss-on | Cue-loss-off |
|---|---:|---:|
| Memory /cue forward presentations | 400 /400 | 400 /400 |
| Cue-supervised presentations | 400 | 0 |
| Original causal supervised-label count | 24,480 | 24,480 |
| Active causal supervised-label count | 24,480 | 19,900 |
| Cue labels removed | 0 | 4,580 |
| Unpadded input tokens | 153,408 | 153,408 |
| Padded batch-token slots | 228,800 | 228,800 |

The followup receipt declares **`ORIGINAL_UNMASKED_BATCH_CAUSAL_LABEL_COUNT`**. For each batch with original label countN and active countA, the loss-off runner multiplies the model's active-label mean loss by **A/N**, preserving the original denominator:

```text
loss_off = active_label_mean_loss × (A / N)
         = sum_of_active_memory_label_losses / original_batch_label_count
```

This prevents the naive active-label mean from upweighting the retained memory objective merely because cue labels were removed. The first batch has N=120,A=98,scale=0.8166666666666667. Across all200 control updates, scales range **0.7967479674796748–0.8211382113821138**. Cue-on hasA=N and scale1. The first causal label is masked, so excluding label0 agrees with the shifted causal count. Every followup's logged original/active counts and scale matches the independent array/index calculation.

Primary seed0 predates the explicit normalization fields: its runner uses the original fully supervised loss and has implicit scale1. The original and followup source comparison confirms the cue-on branch remains the same fully supervised objective; primary is not falsely reported as carrying the newer receipt. This is a source-version limitation, not an unreported second control run.

`CONTROL_MASK_PREFLIGHT.json` records `ACTUAL_MASK_PREFLIGHT_PASS_NO_MODEL`, same inputs and the above totals. Its SHA256 is **`d056f4fd626cea0795808b0a32ed5f2e754eea6232bce608c0c7db42d3096680`**. Shared persisted hashes:

- MASKS.json: `53fe22946d5a9dae6ff32fce500787e584e31f413c0018fbd49b7ae020fde37d`.
- TRAINING_ROWS.json: `8840109e02a950536bf786c6b7a1ef0784fb14d47c1e26194b2766efa2dc0f38`.
- Starting S1 adapter-state receipt: `c08852cb6eb2c8bfa106cf2b7976fc5a2ba5f4cb06d79d53a3a3ac7222b865db`.
- Shared original S1 training RESULT binding: `c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f`.

Each readout's loaded-adapter state equals its training RESULT's final state, and its `initial_artifact_sha256` equals that training RESULT's literal file hash. These are receipt joins, not new weight custody or model-reload verification.

## Interpretation boundaries

- **Supported:** a consistent cue-supervision-dependent change in held-text READ uptake, conditional second reading and GOAL arrival under this common-S1/common-data development setup. Mere cue forward exposure with labels masked does not reproduce it.
- **Not established:** an old-task accuracy advantage unique to cue loss; controls tie at4/4 for two seeds. Reader ablation within the cue-trained policy is not a substitute for the loss-off comparison.
- **Still failed:** unseen-address MISS behavior,0/4 throughout. Retention remains a small4-event/two-wrapper test.
- **Replication limit:** seeds vary optimizer/training randomness from the same S1; no new S1 initialization, cue collection or held-bank draw. Repeated scores on the same eight held tasks are not24 independent tasks.
- **Control limit:** labels/objective differ intentionally; normalization holds the denominator and input/padding schedule fixed, not the gradient or optimizer trajectory. The matched control does not isolate an abstract reasoning mechanism.
- **Claim limit:** researcher-authored environments, previously coached cue targets, no parent present and no H1/H2 or parenting qualification. This memo neither starts nor recommends a new run.

## Source and result identities

Primary source commit: `4f68de78a036906a679558f31dcd1d31e02b3ded`; runner SHA256 `dc0bf710984a7f5d093f8ff41c99143328173db1cf2c57c5209c8a476863e021`. Five followups: `d8255946e33075ef20e8b9c7a5d02c32efad3cc6`; runner SHA256 `2cebd6a1e2cda64dca2720c7c5ba1162ef43ed2a8fb27ec85a30d41cfa0e50c3`. Shared pure cue-sleep source SHA256 `02c9e41b4a0382aa4c831ccd127532a885052fdc2937fbbf63a98797ad432846`. These match immutable Git source bytes; no mutable working-tree runner was executed.

| Readout RESULT | SHA256 |
|---|---|
| P/readout_sleep1 | `4049c89e83465ffb6a596a18d948dded01545848fe9ffdca0518beee78b05d3e` |
| P/readout_sleep2, cue seed0 | `99c5ef35ccb5b15117a7f6c1c1cf1afaf6f216556e35dce1589c3dfbd2c9c721` |
| S/CUE_REPLAY_seed1/readout_sleep2 | `5565892339bdf15f7bafd6152f5263703eac5c2ac9b5f89fec018ff2f2c63021` |
| S/CUE_REPLAY_seed2/readout_sleep2 | `4c6127858005901ef96e9c9a94817810935f9443dac58ca955fcc24914fe4213` |
| S/CUE_LOSS_OFF_seed0/readout_sleep2 | `9b900d7ce9b170649aa200e8a86c1ae63fb1217031279c69c94b3800026eeb33` |
| S/CUE_LOSS_OFF_seed1/readout_sleep2 | `4ea6a067cbd00877a30f574916cff871184775ac51b43129480d438a87952cf3` |
| S/CUE_LOSS_OFF_seed2/readout_sleep2 | `160001f1571db5fa8564053c27fc895236f54b208af8e1c2fdca22cae2fd9c50` |

## Reproducible read-only evidence commands

Run from the repository root. These commands read only bounded completed files and print small reductions, not prompts/logs or model state. They do not import project code or load models.

### Recompute outcomes, READ/second READ, retention and MISS

```bash
bash gpu/ovx_ssh.sh 'python3 -' <<'PY'
import hashlib, json
from pathlib import Path
primary = Path('/tmp/astra_cue_sleep2_20260914_attempt1')
control = Path('/tmp/astra_cue_sensitivity_20260914_attempt1')
roots = [('S1', primary/'readout_sleep1'), ('CUE_REPLAY_seed0', primary/'readout_sleep2')]
roots += [(name, control/name/'readout_sleep2') for name in
          ['CUE_REPLAY_seed1', 'CUE_REPLAY_seed2', 'CUE_LOSS_OFF_seed0',
           'CUE_LOSS_OFF_seed1', 'CUE_LOSS_OFF_seed2']]
for name, root in roots:
    document = json.loads((root/'RESULT.json').read_text())
    assert document['panels'] == json.loads((root/'PANELS.json').read_text())
    print(name, hashlib.sha256((root/'RESULT.json').read_bytes()).hexdigest())
    for panel, recorded in document['panels'].items():
        if 'episodes' in recorded:
            rows = [json.loads(path.read_text()) for path in sorted(root.glob(panel+'_EPISODE_*.json'))]
            assert rows == recorded['episodes']
            reads, goals = [], []
            for row in rows:
                episode = row['episode']
                goal = next(line[5:] for line in episode['messages'][1]['content'].splitlines()
                            if line.startswith('GOAL '))
                goals.append(episode['outcome'] == goal)
                reads.append(sum(trace['kind'] == 'memory' for trace in episode['traces']))
            counts = [sum(goals), sum(count > 0 for count in reads), sum(count == 2 for count in reads)]
            assert counts == [recorded['reached_goal'], recorded['with_reads'], recorded['second_reads']]
            print(panel, 'GOAL/READ/second', counts, 'READ_calls', sum(reads))
        else:
            count = sum(row['generation']['terminal'] and not row['generation']['truncated']
                        and row['generation']['raw'] == ('MISS\n' if panel == 'UNSEEN_MISS'
                                                         else row['expected'])
                        for row in recorded['rows'])
            assert count == recorded['correct']
            print(panel, count, '/', len(recorded['rows']))
PY
```

### Recompute the normalization receipt without tokenizer/model execution

```bash
bash gpu/ovx_ssh.sh 'python3 -' <<'PY'
import json, math
from pathlib import Path
primary = Path('/tmp/astra_cue_sleep2_20260914_attempt1')
control = Path('/tmp/astra_cue_sensitivity_20260914_attempt1')
roots = [('CUE_REPLAY_seed0', primary)] + [(name, control/name) for name in
         ['CUE_REPLAY_seed1', 'CUE_REPLAY_seed2', 'CUE_LOSS_OFF_seed0',
          'CUE_LOSS_OFF_seed1', 'CUE_LOSS_OFF_seed2']]
for name, root in roots:
    masks = json.loads((root/'train/MASKS.json').read_text())
    losses = [json.loads(line) for line in (root/'train/LOSSES.jsonl').read_text().splitlines()]
    assert len(masks) == 52 and len(losses) == 200
    original_total = active_total = 0
    for update, loss in enumerate(losses, 1):
        start = 2 * (update - 1)
        indexes = [start % 32, (start + 1) % 32, 32 + start % 20, 32 + (start + 1) % 20]
        assert loss['row_indexes'] == indexes
        batch = [masks[index] for index in indexes]
        assert all(row['labels'][0] == -100 for row in batch)
        original = sum(value != -100 for row in batch for value in row['labels'][1:])
        active = sum(value != -100 for row in (batch[:2] if name.startswith('CUE_LOSS_OFF') else batch)
                     for value in row['labels'][1:])
        if name != 'CUE_REPLAY_seed0':
            assert (loss['original_label_count'], loss['active_label_count']) == (original, active)
            assert math.isclose(loss['loss_scale'], active / original, rel_tol=0, abs_tol=1e-15)
        original_total += original
        active_total += active
    print(name, 'original/active', original_total, active_total)
print(json.loads((control/'CONTROL_MASK_PREFLIGHT.json').read_text()))
PY
```

Only this memo was created. No new artifact preservation or custody expansion was performed.
