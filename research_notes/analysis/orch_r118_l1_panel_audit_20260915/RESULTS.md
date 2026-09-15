# L1 fixed32 capability panel: code discrepancy predates the new feed

Observed September 15, 2026, 13:53:55 UTC; pre-C2 baseline rechecked at
13:54:57 UTC. This is a read-only audit, not new inference or a new training gate.

| Update | FULL LoRA ON / OFF | Masked-control LoRA ON / OFF |
| --- | --- | --- |
| 12132, before C2 | 22/32 / 24/32 | 22/32 / 24/32 |
| 12260 | 22/32 / 24/32 | 22/32 / 24/32 |
| 12388 | 22/32 / 24/32 | 22/32 / 24/32 |
| 12516 | 22/32 / 24/32 | 23/32 / 24/32 |
| 12644 | 22/32 / 24/32 | 23/32 / 24/32 |
| 12772 | 22/32 / 24/32 | 22/32 / 24/32 |
| 12900 | 22/32 / 24/32 | 23/32 / 24/32 |

All pairs are complete. Each condition has eight cases per family. At update
12900, FULL scores code 0/8 ON versus 2/8 OFF; the masked control scores 1/8
versus 2/8. Math is 7/8, simulated tool calls 8/8, and concise instruction
following 7/8 in every shown condition. FULL's code ON failures are six invalid
JSON outputs and two invalid/unsafe expressions under the fixed capability-free
interpreter. Tool-call cases are schema/argument comparisons, not external tool
execution.

The code discrepancy already exists at checkpoint 12132 in both lineages;
it is **not evidence that the newly appended C2 examples caused it**. Toggling
LoRA changes performance on this diagnostic, consistent with an adapter effect;
these counts do not establish damage to the frozen base or broad coding ability.
The base itself passes only two of eight code cases. At update 12900 the masked
control has two OFF-only successes and one ON-only success, so its aggregate
one-point deficit is not simply a subset relation.

FULL's pass count does not improve across these six new-feed checkpoints.
This is not a semantic-thinking or persistence readout, and it does not prove
the absence of other behaviour changes. No parenting lane is stopped or selected
using these scores, and no capability questions/answers are sent to parents.

## Reproducibility

The audit recomputes 768 native capability cells from twelve saved C2 panels,
plus 128 cells from the two pre-C2 baseline panels. It calls the existing
`organism_v6.orch_r107_capability.reduce_paired` with each exact saved checkpoint,
base hash and 512-token cap; all twelve rederived C2 panels equal their saved
reductions. Baseline readout receipts match the C2 handoff hashes. This is CPU
scoring of saved text, with zero model/provider calls and zero optimizer updates.

- Reducer SHA256: `f8398dbf755c041508ee9268a46f7411c09146ccbe02b8bee254c027a85ebbc9`.
- Node root through `gpu/ovx_ssh.sh`: `/localhome/local-rohing/orch_r118_l1_panel_audit_20260915_attempt1`.
- `COMPACT.json` SHA256: `703564293dc4f846cf7cf411204419ee69bfe0a3b06dfcf5671728ee22b9f599`.
- `BASELINE_12132.json` SHA256: `ad98c6b2b614ea0224e8db729c7dd4f976d219aa5427c0984e09928def5f9ba1`.
- Full native record-reference manifest remains on-node as `SOURCE_RECORDS.json`; the compact records its hash. Raw responses and model artifacts are not copied to the repository.

Claim boundary: the fixed synthetic32 diagnostic only. No population-level,
retained-thinking, or parenting-dependence claim follows from these counts.
