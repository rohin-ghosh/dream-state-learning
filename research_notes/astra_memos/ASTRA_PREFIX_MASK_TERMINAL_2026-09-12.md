# Prefix-mask terminal result — SEQ-074

Recorded September 12, 2026, 11:39 UTC. Exploratory oracle-material diagnostic;
not clean lineage, a selective-writer repair, or a mechanism freeze.

## Result

Same bank0, optimizer seed2, rank8, learning rate1e-4, 9,693 updates and
749,985 input-token passes as the original whole-text comparison. The
predeclared conservative context mask lowers spill but erases acquisition.

| Endpoint | Original whole-text | Prefix mask |
|---|---:|---:|
| I_d_frame | 1.921469873 | 0.015228690 |
| Owner-bootstrap interval | [1.202607550, 2.682502692] | [-0.132712882, 0.174474171] |
| Frame spill | 0.415536920 | 0.201955099 |
| Dose16 correct conditional probability OFF | 0.259649920 | 0.259649920 |
| Dose16 correct conditional probability ON | 0.685322980 | 0.250952640 |
| Candidate mass ON | 0.998158431 | 0.993089 |
| Unchanged G9 | FAIL | FAIL |
| Unchanged G11 | FAIL | FAIL |

Near-unit candidate mass is not correct owner/color binding. This is an
acquisition/locality tradeoff, not evidence that the masked writer works.
No additional mask-only or learning-rate-only sweep is selected.

## Execution and comparability

Run `astra_A1_prefixmask_bank0_ts2_20260912_attempt2`, node3 GPU0,
controller73820, frozen source `f96ca5088802c1d8e969f18bc842ba66f5d1ed45`.
Worker result records completion at11:28:37.334520UTC; controller absent at
terminal capture. Worker73821 cleanup verifies owned process group empty,
GPU processes absent and reservation release, with no cleanup error. No
manual kill. GPU0 reservation is released.

All1,313 cue IDs/order/metadata and OFF scores match the original at serialized
precision; native report and independent reduction agree. Final fit loss
1.104537606; training wall1216.1seconds. Masked supervised passes422,925 versus
711,213 original. The5,376 crossing ` Owner` tokens are omitted under the
unchanged conservative encoder, as amended before training. No truncation.
The initial zero-straddle preparation refused before creating attempt1;
that refusal remains a distinct preserved event, not a training failure.

## Evidence

Files under `research_notes/astra_memos/receipts_20260912/`:

- `astra_prefixmask_terminal_20260912.tgz`: terminal capsule excluding weight
  payloads; SHA256 `7017ef230af76ba685a1b0ae420557bd0bbcc1436a6401067965e43f53bfbe18`.
- `astra_memory_mask_reduction_20260912.json`: `valid=true`; SHA256
  `782d7f5f31fb39ca1ca786bffc353852b92bb56bb80699dc37b1b30054d7b090`.
- `astra_prefixmask_remote_weights_20260912.txt`: remote weight rehash receipt;
  adapter SHA256 `8afb67f5f57740f5f31eefb37002602f86853e13547e0d3bbfc8dbfe2f7a80c2`.
- `astra_capture_mask_terminal_20260912.sh`: exact terminal capture command.

Protocol: `ASTRA_PREFIX_MASK_COMPARISON_2026-09-12.md`. Native reducer source
`organism_v6/memory_dose.py` remains unchanged. Weights remain on node3;
the repository capsule does not contain them. Official model origin remains
`UNRESOLVED_LOCAL_HASHES_ONLY`.

## Next decision

Retain whole-text acquisition and test training-only frozen-OFF distribution
preservation as a separate, prospectively fixed diagnostic after CPU/native
checks. This is not an SDFT reproduction, and preserving OFF cannot by itself
satisfy G11's abstention threshold because the OFF model already fails it.
No coefficient or GPU launch is authorized by this result alone. Continue
the running historical lesson/sham material fork without a formal C11 gate.
