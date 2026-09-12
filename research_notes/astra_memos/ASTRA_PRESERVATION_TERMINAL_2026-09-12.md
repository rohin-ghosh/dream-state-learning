# SEQ-081 — OFF preservation suppresses acquisition as well as spill

September12,2026. The complete fixed coefficient0/0.1 pair is valid under the
prospective comparison, but BOTH unchanged G9/G11 gates fail. Reduced spill
alone is not selective learning. No additional coefficients or old-frame
mask/rate sweeps are selected.

| Native bank0/seed2 metric | Coefficient0 | Coefficient0.1 |
|---|---:|---:|
| Dose16 acquisition I_d | 1.921469873 | 0.152267044 |
| Native interval | [1.202607550,2.682502692] | [-0.023955285,0.333065840] |
| Frame spill | 0.415536920 | 0.036657910 |
| Dose16 correct conditional probability OFF | 0.259649920 | 0.259649920 |
| Dose16 correct conditional probability ON | 0.685322980 | 0.294129798 |
| G9 / G11 | FAIL / FAIL | FAIL / FAIL |
| Fit seconds | 1227.287121 | 2458.878753 |
| Cache seconds | 0 | 18.782232 |
| Evaluation seconds | 241.1 | 238.4 |

G9 requires positive interval lower bound and spill≤0.03. The treatment misses
both. Treatment-minus-control I_d is−1.769202829, paired-owner interval
[−2.433713142,−1.144942376], with16owners in ONE learner-seed comparison,
not independent fit replication. Spill falls0.378879010; correct conditional
probability ON falls0.391193182. Candidate mass ON falls0.987871325. Low OFF
abstention is substantially preserved, not transformed into G11's required
≥0.5unexposed/bicycle abstention. This regularizer largely removes acquisition
and format-mass changes while costing roughly twice the fitting time.

## Matched evidence and implementation difference

Both arms have12,924items,9,693steps,749,985CE input and711,213CE supervised
tokens, rank8, three epochs, batch4, seed2, lr1e-4, no truncation. Original
corpus hashes, encoded order, initial LoRA hash, recorded model inventories,
trainable set/dtypes and torch version match. All1,313cue identities/order and
OFF values are exactly equal at serialized precision. The coefficient0
historical bridge remains descriptive, not an independent-seed replication.

The positive48×152064float32 OFF cache is finite/detached and CPU-validated
using float64 normalization, maximum error3.064215547965432e-14. It supplies
one anchor per step:9,693extra anchor forwards/distribution positions and
77,544anchor input tokens. Extra compute is not matched by coefficient0.
CE dose and objective remain unchanged except the declared additive KL term.

Main inspected the actual producer diff between290a9ea0 and586757e3: only
cache-check arithmetic changes from float32 normalization to float64 with
atol1e-10/rtol0. Training cache/KL remain float32; no other objective/recipe
change appears in that file. The failed first positive attempt is preserved
separately as SEQ-076 and is not silently substituted or counted as a result.

## Custody and decision

Positive run `astra_A1_preservation_bank0_ts2_lam01_20260912_attempt2`,
controller88012/node3GPU2, source586757e359c7e80fb58951d1d6c9c3ab396cdf40,
completed12:45:34.293308UTC. Main observed controller absent12:46:23UTC;
worker88114cleanup reports owned group/GPU processes absent, no error,
reservation released. GPU2released. Stage totals45.27 versus24.47minutes
exclude controller overhead and the first failed attempt; no inflated
throughput or reproduction claim. This is not OEL/SDFT reproduction.

Terminal capsule SHA256
`c401bfdc6c85da16b52f760e879148ad93acebb016e4066395d1695a6363034e`;
full validated pair reduction
`7d97658367e5c5d0a02498c18a020cce9117775c98b91a82db3c4251f0ee2a57`.
Huygens ran the frozen reducer with explicit repaired producer hash; all
matching/cache checks pass. Captures omit adapter weights; remote rehash
receipts preserve their identities, not local weight verification.
Files use `astra_preservation_positive_` and `astra_preservation_pair_`
prefixes under `receipts_20260912/`.

The next writer experiment tests actual conditional semantic-action binding
after the separate carrier pass, not a looser claim on this failed gate.
No mechanism freeze, parenting internalization or H1/H2 claim follows.
