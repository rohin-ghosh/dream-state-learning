# Fable v6.1 episode-960 sealed-pair follow-up v4

Date: 2026-09-07 UTC

Status: exploratory, read-only analysis of an in-flight legacy run. No model,
compiler, adapter, benchmark, or GPU operation was launched or changed. This
artifact supports no confirmatory or manuscript claim and inherits every
split, prompt-provenance, generation-seed, and writer confound enumerated in
`20260907_fable_v61_late_life_fixation_followup_v3.md`.

## Sealed boundary

At `L_B_seed0` episode 960, both the adapter-on and adapter-off probe ledgers
and summaries were durably present. The unchanged saved-artifact analyzer gave:

| condition | held-out mean | actions | distinct actions | dominant share | invalid | unpredicted |
|---|---:|---:|---:|---:|---:|---:|
| adapter on | 0.523262 | 142 | 4 | 139/142 = 97.9% | 2 | 6 |
| adapter off | 0.470193 | 60 | 22 | 21/60 = 35.0% | 10 | 7 |

The paired level difference is `+0.053069`. Adapter-on minus adapter-off under
best-of-first action caps `{1,2,4,8,16}` is respectively
`{+0.063425,+0.063425,+0.055573,+0.053069,+0.053069}`. Thus the stored policy
still improves first-proposal value; the difference is not created by a larger
number of dispatched actions.

The mechanism remains the negative one identified at episodes 832 and 896.
The on-adapter dominant action is the same six-pass routine
`-mem2reg,-sroa,-gvn,-simplifycfg,-licm,-instcombine`, now emitted in 139 of
142 actions. Off-adapter remains much more diverse. Episode 960 therefore
replicates **transported routine competence with extreme policy
concentration**, not a positive late-life learning slope, discovery, learned
THINK, or model meta-intelligence. The adapter-on score is byte-for-byte equal
to its episode-896 score to six displayed decimals despite another 64 programs
and two sleeps. That is additional descriptive evidence of a local plateau.

`L_B_seed1` had started but not completed its episode-960 probe at the same
read-only status check, so no seed-1 episode-960 comparison is included.

## Artifact receipts

Remote root: `/localhome/local-rohing/v6_out/L_B_seed0`

- `probe_ep0960.json`:
  `5a4fb978343a968da3851b5580e41fae23f525a0d17e622335a0d7c4f26f7b70`
- `probe_ep0960.ledger.jsonl`:
  `eab04a95365bd5a19069824c802c6badd77df9380facd89a315e6cdbdce7153e`
- `probe_ep0960_adapterOFF.json`:
  `6cf07c944191ea8bf4a4e343a98492bb2d7c3d6e8a7ad5ecfc34266be313972a`
- `probe_ep0960_adapterOFF.ledger.jsonl`:
  `2ecf37f1e492d7cdccfa2a024d452ed48222a6b95298c9816513364becfd4c08`

Reproducer:
`research_loop/advisory/analyze_fable_v61_probe_actions.py --root <saved-root>
--seeds 0 --checkpoints 960 --summary-only`.
