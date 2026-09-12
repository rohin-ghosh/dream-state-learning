# Trained-record acquisition — independent raw audit, September 12, 2026

**Audit PASS; the prespecified JOINT acquisition criterion is NOT MET by P or A in either context.** This is not “no parameter learning.” Both adapters improve full-context truth likelihood on both own records, but required truth–foil margin gains fail on individual records. No retuning, substitute criterion, selective averaging or alternative-criterion rescue is applied.

## Custody, targets and native scoring

Verified capsule SHA256 `f7faf00c65ba67c76a3778750fcc9b093d544cd4543df160635200c5940c8e27` and **119/119** inventory hashes, in memory: unique regular members, safe relative paths, no links/traversal/duplicate paths or weight payloads. Plan `79fad7b32e88f8dffda5f96214fbc511d702167610c613527daa68d024952bfc` binds source `610c6edd05ce9c85720ee6e992889badecc2c158` and original write-attempt2 plan `48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4`. Archived driver/dependency bytes match pins. Original write result, material/source/token receipts and selected formation request/response hashes agree with the acquisition records.

**Exactly24 requests/48 forwards/zero generations**: OFF→P→A, each evaluating P0/P1/A0/A1 under FULL and MAPPING_SENTENCE_REMOVED, with truth then foil. No requests are missing. Raw JSON preserves whitespace, byte order and all fields except the foil's single unique literal `relation` substitution. Duplicate keys/null predictions are rejected. Original truth fields independently agree with captured observed/predicted fields:

| Record | TRY | Predicted / observed | True relation | Truth / foil scored tokens, including EOS |
|---|---|---|---|---:|
| P0 | [2,3,4] | false / true | mismatched | 38 / 36 |
| P1 | [1,2,3] | true / true | matched | 36 / 38 |
| A0 | [1,1,1] | false / true | mismatched | 38 / 36 |
| A1 | [2,2,2] | true / true | matched | 36 / 38 |

Removed contexts delete **exactly one LF + the mapping sentence**,152characters/UTF-8 bytes, without other edits. Native prefix counts decrease by26: P282→256, A281→255. All truth/foil target IDs remain unchanged across contexts. FULL truth IDs/labels equal the original training receipts. The audit checks contiguous char/byte offsets, no context-boundary straddle, context labels−100, every target/EOS label, predictor position=label position−1, relation spans, and exactly one terminal target EOS. Both recorded native forwards match candidate IDs, equal-width future-EOS padding, positions, all-one attention masks and no-cache inputs. Padding is after scored positions; these are causal teacher-forced forwards, not generated completions.

All48 token-logprob vectors have the expected lengths, finite nonpositive values, valid disjoint-candidate probability mass and identical scores on their common earlier target prefix (**max difference0**). Independently recomputed sums, means, counts, margins and all stored cross-control deltas agree **exactly; max difference0**. Scores are sums in nats, means=sum/count; margins remain summed truth minus summed foil despite unequal truth/foil lengths. Full vectors, both candidates' sums/means/counts and all24 P−OFF/A−OFF/P−A record/context comparisons are retained in the companion JSON.

## All record/context scores

Each cell below is **truth summed logprob / truth–foil margin**; R denotes MAPPING_SENTENCE_REMOVED. Display rounding is not used for decisions.

| Record/context | OFF | P | A |
|---|---:|---:|---:|
| P0 FULL | −0.386693 / 15.374990 | −0.000109 / 12.874988 | −0.000165 / 14.124994 |
| P0 R | −1.469417 / −0.500160 | −5.131383 / −5.125281 | −4.018867 / −4.000343 |
| P1 FULL | −0.392151 / 18.670014 | −0.000664 / 19.282093 | −0.004268 / 19.152316 |
| P1 R | −0.455257 / 19.653480 | −0.000094 / 18.273671 | −0.000128 / 18.151608 |
| A0 FULL | −0.283231 / 19.625082 | −0.000399 / 18.875432 | −0.000297 / 19.000436 |
| A0 R | −0.379893 / 15.374983 | −0.000202 / 9.374982 | −0.000211 / 9.749973 |
| A1 FULL | −0.196348 / 18.909020 | −0.001158 / 18.518787 | −0.002452 / 18.647560 |
| A1 R | −0.315843 / 18.653190 | −0.000125 / 17.145242 | −0.000209 / 18.521539 |

Strict prospective criteria require **both own records individually improve truth sum AND margin against OFF**. Stronger P-specific carriage additionally requires both improvements against A on both P records.

| Context | P own LL gains | P own joint gains | A own LL gains | A own joint gains | Stronger P-specific |
|---|---:|---:|---:|---:|---|
| FULL | 2/2 | 1/2: criterion FAIL | 2/2 | 0/2: criterion FAIL | FAIL |
| R | 1/2 | 0/2: criterion FAIL | 2/2 | 0/2: criterion FAIL | FAIL |

FULL P0 has ΔLL+0.386584 but Δmargin−2.500003; A's own A0/A1 margin changes are−0.624646/−0.261460 despite positive LL changes. Under R, P0 also loses truth LL (−3.661965 against OFF); the other own records gain LL but lose margin. Thus both context-pattern labels are `neither_demonstrated` **for the joint criterion**, not for learning generally.

Cross-arm controls are not dropped: FULL both adapters increase truth LL on all four records; each improves both LL and margin only on P1. Under R, each improves truth LL on three records but margin on none versus OFF. P beats A jointly only on P1 in each context, insufficient for the stronger both-P-record criterion. The prespecified shared/nonselective joint-acquisition condition also fails; descriptive cross-arm likelihood gains remain visible.

## FULL→removed sensitivity

Each entry is **removed minus FULL: Δtruth sum / Δmargin**, retaining all records/cells:

| Record | OFF | P | A |
|---|---:|---:|---:|
| P0 | −1.082724 / −15.875151 | −5.131274 / −18.000269 | −4.018702 / −18.125338 |
| P1 | −0.063106 / +0.983466 | +0.000569 / −1.008423 | +0.004140 / −1.000708 |
| A0 | −0.096662 / −4.250099 | +0.000198 / −9.500451 | +0.000086 / −9.250463 |
| A1 | −0.119495 / −0.255830 | +0.001033 / −1.373545 | +0.002243 / −0.126021 |

P0 changes from truth-preferred to foil-preferred in all three cells. The other records retain positive margins. This establishes sensitivity to this exact ablation, not a unique semantic mechanism: prompt length/positions change, and schema, action and observed-outcome scaffolding remain. Earlier **correct target fields are teacher-forced before relation**, so this is conditional record scoring—not autonomous record production, pre-TRY prediction competence or process selection. OFF already strongly discriminates the FULL foils; base strength/saturation is a possible limitation of the margin-improvement criterion, not a demonstrated causal explanation or a reason to override it.

## Isolation, costs and scope

Three distinct supervised processes bind the same base and OFF0/P1/A1 adapter counts, frozen eval/no-cache HF bf16/eager loads and zero trainable parameters. P/A are the original saved12-update adapters; model/adapter inventories and source pins agree across receipts. P weight `c9f1fa5cd3391b407a0102856faa4926d6a550c799979026d399b55bd979868c`; A `5ea89adcf57956867f7bd7014ede004df0874c8ca82c4e72fc485ff121c681ab`. All workers report success and owned cleanup; full release matches launch UUID `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1`, at22:25:40.827056UTC. No retries, updates or generations occurred.

Each cell:8requests/16forwards,592 scored target tokens,4,888 native input tokens,4,904 padded-forward positions. Totals:1,776 /14,664 /14,712 respectively. Calls7.495794s ⊂ workers206.790118s ⊂ controller348.379228s ⊂ launch-to-release610.814112s (**10.180235 A40-min**). Collection84.893527s overlaps these windows; do not add it. OFF/P/A worker times51.859/63.939/90.993s; process→ready26.510/37.536/64.961s is not pure weight-load time. Bounds1800s controller,≤600s/worker,140s nested cleanup,300s collection; no overrun indicated.

**Limits/disclosure:** no logits-based recomputation, tokenizer/model/native execution, live GPU/SSH/network/Git or weight-byte reread; native forward/mask/load/inventory receipts were checked, not independently regenerated. Local identity is not model-origin or semantic-nonleakage certification, nor vLLM parity. I authored formation/write collectors, not acquisition code; Main already saw the complete result, so this is **not blinded**. No inference of absent parameter learning, inability, heldout acquisition, parenting/P1/H1/H2/G5, or scientific freeze. All technical/numerical contradiction flags are empty. **EDIT-STOP.**
