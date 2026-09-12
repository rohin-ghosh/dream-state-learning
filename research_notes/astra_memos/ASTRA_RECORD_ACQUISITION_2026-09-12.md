# SEQ114 — trained-record acquisition diagnostic

Executed and independently audited:24 teacher-forced requests,48 candidate
forwards, zero generations or updates. OFF/P/A score all four original accepted
SEQ111 training records under FULL and MAPPING_SENTENCE_REMOVED contexts.
Each foil changes only the raw JSON relation value; all other bytes remain.

The prespecified criterion requires BOTH own records individually improve full
truth summed log-likelihood AND truth-minus-foil summed margin relative to OFF.
A stronger P-specific criterion additionally requires both gains versus A on
both P records. Neither criterion is met. This does NOT mean no parameter
learning: likelihood and discrimination are different quantities.

| Context | P own LL improves | P own joint gains | A own LL improves | A own joint gains |
|---|---:|---:|---:|---:|
| FULL | 2/2 | 1/2; criterion fails | 2/2 | 0/2; criterion fails |
| Mapping removed | 1/2 | 0/2; criterion fails | 2/2 | 0/2; criterion fails |

Both adapters improve FULL truth likelihood on all four records, including
cross-arm targets. They improve joint likelihood/margin only on P1. Under the
mapping removal each improves likelihood on three records, but margin on none
relative to OFF. No condition/record is omitted and no criterion is changed.

## Complete scores

Each cell: truth summed logprob / truth-minus-foil summed margin, in nats.
Display rounding is not used in decisions. R = MAPPING_SENTENCE_REMOVED.

| Record/context | OFF | P | A |
|---|---:|---:|---:|
| P0 FULL | -0.386693 / 15.374990 | -0.000109 / 12.874988 | -0.000165 / 14.124994 |
| P0 R | -1.469417 / -0.500160 | -5.131383 / -5.125281 | -4.018867 / -4.000343 |
| P1 FULL | -0.392151 / 18.670014 | -0.000664 / 19.282093 | -0.004268 / 19.152316 |
| P1 R | -0.455257 / 19.653480 | -0.000094 / 18.273671 | -0.000128 / 18.151608 |
| A0 FULL | -0.283231 / 19.625082 | -0.000399 / 18.875432 | -0.000297 / 19.000436 |
| A0 R | -0.379893 / 15.374983 | -0.000202 / 9.374982 | -0.000211 / 9.749973 |
| A1 FULL | -0.196348 / 18.909020 | -0.001158 / 18.518787 | -0.002452 / 18.647560 |
| A1 R | -0.315843 / 18.653190 | -0.000125 / 17.145242 | -0.000209 / 18.521539 |

P0 becomes foil-preferred after mapping removal in all three cells. This shows
sensitivity to that exact ablation, not a uniquely identified semantic mechanism:
prompt length/positions also change, while schema and public observed fields
remain. Correct earlier target fields are teacher-forced before relation. These
are not autonomous records, pre-TRY decisions, or held-out learning. Strong
baseline discrimination may limit this margin-improvement test; saturation is
a possible limitation, not a demonstrated explanation or reason to waive it.

## Verification and cost

Main/agent collector CPU22 tests and native22 pass. Native collection verifies
original write/material/source/native token joins, immutable saved adapters,
three fresh frozen HF processes and full nvidia/process/queue release. Herschel
independently checked119/119 capsule files and reconstructed every likelihood,
margin and cross-arm delta from48 raw score vectors; max numerical difference0.
Native forward/mask/offset/weight-identity receipts were checked, not regenerated
by his review. He authored earlier formation/write collectors, not the scoring
bridge; Main had seen the complete result, so this is not blinded.

Totals:1776 scored target tokens,14664 native input tokens,14712 padded-forward
positions. Score calls7.495794s, workers206.790118s, controller348.379228s,
launch-to-collector-observed-release610.814112s (10.180 A40-min). Collection
84.893527s overlaps these intervals; do not add them. The outer interval includes
waiting for collection, not just GPU-active time. Main separately observed full
vacancy at22:22:40.188350Z; collector independently confirmed at22:25:40.827056Z.

Native root astra_rulegame_record_acquisition_20260912_attempt1, former
node3GPU2 PID243383. Source610c6edd05ce9c85720ee6e992889badecc2c158;
plan79fad7b32e88f8dffda5f96214fbc511d702167610c613527daa68d024952bfc.
Metadata capsule f7faf00c65ba67c76a3778750fcc9b093d544cd4543df160635200c5940c8e27.
Raw review266d0a5f84d7e8a4f9d666b485098f2a342af25064be82163470e0393f265620;
full precision analysis4f20e9984f9fac98cc9401719909519762d0f8eaba9508159f938b298149c86b.
All are archived in receipts_20260912. Weights stay native; no retry occurred.

The SEQ112 absent parenting advantage remains. This diagnostic localizes
likelihood changes without establishing improved decision-making; the next
already-versioned comparison writes the child's actual wake decisions, not
retrospective reporting fields. Model origin remains unresolved; no G3/P1/G5,
H1/H2, mechanism freeze, clean lineage or universal inability claim follows.
