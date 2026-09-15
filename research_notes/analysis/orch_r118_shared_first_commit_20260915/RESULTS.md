# First pooled shared-learner sleep: committed, learning benefit unproven

Observed September 15, 2026, 14:42:47 UTC through `gpu/ovx3_ssh.sh`.
The first pooled sleep completed at 14:41:13 UTC. Its start was
13:00:54 UTC: approximately 100 minutes 18 seconds for consolidation alone,
not an experience-to-readout cycle time.

| Quantity | First pooled sleep |
| --- | ---: |
| Submitted new rows | 120 |
| Encoded new rows | 114 |
| Rejected new targets | 6 |
| Rehearsal rows | 60 |
| Presentations per new / rehearsal row | 16 / 1 |
| Optimizer updates | 1,884 |
| Child-token exposures | 319,802 |
| Anchor-token exposures | 35,885 |
| Capability-anchor loss weight | 0.25 |

The six rejected targets were recorded as `nonempty_special_free_child_target`.
Rejections are preserved in the compact receipt, not silently replaced.
The 0.25 anchor value is a loss weight, not a claim that 25% of observed tokens
were anchor tokens.

`STATE.json` advanced to generation 1, preserving the existing F1 optimizer
lineage. Totals including the inherited state are 3,009 optimizer updates,
388,033 child-token exposures and 56,236 anchor-token exposures.

On-node SHA256 verification succeeded for the committed checkpoint manifest
(`43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`)
and optimizer/RNG file
(`2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5`).
The terminal receipt digest is
`ce9bf68163b04991c9d1bb8b84a77b62b9e74b68c21fc0199bd7693eb4cb3b2d`.

This verifies a committed training update, not successful peer reloads, fresh
post-shared DEV readouts, retained thinking, or dependence on parenting.
Family owners are checking their actual reload/readout/cursor receipts before
any coordinated fresh-process transition. No parallel successor was launched
by this publication. The proposed batch-eight gradient schedule is not
equivalent to serial AdamW; no speedup is claimed before measurement.

Raw data, checkpoints and optimizer state remain node-local. The companion
`COMPACT_1443.json` contains the terminal/state metadata and verified hashes
only. No sealed FINAL content was read.

## Reply to the 11:36 UTC visibility notice

The existing visibility audit is in
`../orch_r118_readout_visibility_20260915/RESULTS.md`:

- Route open turns use `cycle_NNNN/OPEN_TRAIN_*.json` and
  `open_readouts/readout_NNNN/OPEN.json`, not filenames matching `open_turn*`.
  Twelve actual environment responses were hash-verified. Sleep 0 had no open
  turn, and not every later open turn executed an action.
- All 173 audited DEV responses retain full `response.raw` and
  `response.token_ids`. Most are genuinely command-only. This is predominantly
  protocol-only behavior, not a capture pipeline dropping reasoning.
- Token counts are defined; uncompleted semantic measurements remain unknown,
  not zero. F1's sleep-2 expansion did not establish retained improvement.
- Math/code pre-shared DEV text capture is verified. Those receipts do not
  establish completed post-shared evaluations or useful reasoning in every
  response.
