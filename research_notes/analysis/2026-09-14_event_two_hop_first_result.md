# SEQ-248: connected EVENT readout stops before memory access

September 14, 2026, 14:48 UTC. Frozen source
`e41439989de59858cd6d36fdd400a26c3dd1a12d`, node2 GPU0 guardian389937,
14:43:42–14:46:24 UTC. Zero fits; collection and readonly readout COMPLETE.

Four scheduled actions generated four actual receipts and four source-valid
child EVENTs (8 calls). The connected world is genuinely new, not relabelled
previous receipts. One graph, two final goals and two display orders; not four
independent worlds or seeds. Parent is SEQ245 SELECTED207ad43e.

| Readout | Goal /4 | Native actor calls | Memory calls | Committed actions |
|---|---:|---:|---:|---:|
| ON_PARAMETRIC | 0 | 4 | 0 | 0 |
| ON_OWN_TEXT | 0 | 4 | 0 | 0 |
| ON_UNAVAILABLE | 0 | 4 | 0 | 0 |
| OFF_OWN_TEXT | 0 | 4 | 0 | 0 |

Each mounted condition produces three invalid multi-command continuations and
one nonterminal/truncated continuation (task2). These outputs simulate several
READ/ROUTE/environment turns without yielding control. All four OFF outputs
are `ROUTE N_EFGNDBEB6D`: a node, not an offered port. Therefore13 invalid_command
and3 actor_nonterminal_or_truncated outcomes are retained; not13 identical
format failures. No memory service was invoked and no action committed.
The condition differences were never exercised. This does not diagnose memory,
path composition or a new learning failure. It localizes an actor-interface
failure under this public prompt. No simulated output is an environment receipt.

Collection took65.122s and readout94.827s: approximately0.0444 dedicated A40h
summed native phase wall, not measured kernel-active time. Base and adapter
readonly checks pass in both stages; parent state remains207ad43e. Full terminal
root, source, calls and launch receipts copied and extracted successfully:
`gpu_artifacts_local/astra_event_two_hop_terminal_20260914_attempt1/extracted`.
Local/remote archive SHA256:
`8e1cf0c9b7c42f1e4f57f4924cd3561c09308d3097ec2ee547629e17b4ee46c4`.
Independent CPU replay/reduction is pending with Kant; do not call it complete.

Next prospective diagnostic: same parent/world/collected bytes, zero fits,
explicit single-command-per-turn instruction. Preserve this original failure
and scoring; do not parse the simulated multi-turn text into successful actions.
