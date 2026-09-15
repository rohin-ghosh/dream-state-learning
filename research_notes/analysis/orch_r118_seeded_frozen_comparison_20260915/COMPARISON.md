# Seeded-frozen versus canonical learned readouts

Native reductions observed **September 15, 2026, 16:26:14–16:26:16 UTC**. Read-only comparison of original held groups C1–C6: 12 task identities, two episodes / one world per group. Raw outputs, token IDs, tasks and event-store contents remain on their nodes. No new model, parent, judge, FINAL, training or provider calls; no broker changes.

## Output behavior first

**All 183/183 saved responses are command-only; 0/183 are truncated.** Every arm has an aggregate median of **11 generated token IDs per response**, including EOS (10 text tokens excluding EOS). Every response has a native terminal/EOS flag; observed lengths span 9–14 IDs. These are complete short outputs, not missing captures or 512-token truncations.

| Arm | Responses | Generated IDs | Text tokens excluding EOS | Median IDs / response | Command-only | Truncated |
|---|---:|---:|---:|---:|---:|---:|
| GUIDED | 65 | 720 | 655 | 11 | 65/65 | 0/65 |
| UNPARENTED | 60 | 666 | 606 | 11 | 60/60 | 0/60 |
| Seeded frozen | 58 | 644 | 586 | 11 | 58/58 | 0/58 |

Literal rule: full-match the entire stripped raw response against `(?:READ EVENT|ROUTE)\s+\S+`. This measures output form only, not correctness, metacognition, branching, cohesion, or unobserved computation. No semantic annotations were invented.

### Per-group response measurements

| Group | Arm | Responses | Generated IDs | Median IDs / response | Command-only | Truncated |
|---|---|---:|---:|---:|---:|---:|
| C1 | GUIDED | 9 | 97 | 11 | 9/9 | 0 |
| C1 | UNPARENTED | 9 | 97 | 11 | 9/9 | 0 |
| C1 | Seeded frozen | 9 | 97 | 11 | 9/9 | 0 |
| C2 | GUIDED | 8 | 91 | 11 | 8/8 | 0 |
| C2 | UNPARENTED | 8 | 91 | 11 | 8/8 | 0 |
| C2 | Seeded frozen | 8 | 91 | 11 | 8/8 | 0 |
| C3 | GUIDED | 12 | 133 | 11 | 12/12 | 0 |
| C3 | UNPARENTED | 12 | 133 | 11 | 12/12 | 0 |
| C3 | Seeded frozen | 10 | 109 | 10.5 | 10/10 | 0 |
| C4 | GUIDED | 12 | 135 | 11 | 12/12 | 0 |
| C4 | UNPARENTED | 12 | 135 | 11 | 12/12 | 0 |
| C4 | Seeded frozen | 8 | 90 | 11 | 8/8 | 0 |
| C5 | GUIDED | 12 | 133 | 11 | 12/12 | 0 |
| C5 | UNPARENTED | 11 | 122 | 11 | 11/11 | 0 |
| C5 | Seeded frozen | 11 | 126 | 11 | 11/11 | 0 |
| C6 | GUIDED | 12 | 131 | 11 | 12/12 | 0 |
| C6 | UNPARENTED | 8 | 88 | 11 | 8/8 | 0 |
| C6 | Seeded frozen | 12 | 131 | 11 | 12/12 | 0 |

GUIDED has 76 more generated IDs and seven more responses than seeded frozen, without a higher aggregate response median or any non-command output. UNPARENTED has 22 more IDs and two more responses. Total token counts alone do not establish richer reasoning; response count reflects the realized action trajectory. Equal counts do not imply identical actions.

## Outcomes second — descriptive only

Every cell uses the original observed correctness field, cross-checked against COMPLETE; denominator is two episodes, not model responses.

| Group | GUIDED correct | UNPARENTED correct | Seeded frozen correct |
|---|---:|---:|---:|
| C1 | 1/2 | 1/2 | 1/2 |
| C2 | 1/2 | 1/2 | 1/2 |
| C3 | 2/2 | 2/2 | 2/2 |
| C4 | 2/2 | 1/2 | 1/2 |
| C5 | 2/2 | 2/2 | 1/2 |
| C6 | 2/2 | 1/2 | 2/2 |
| Total | 10/12 | 8/12 | 8/12 |

These small descriptive outcome differences are not a parenting causal-effect estimate or retained-thinking result.

## Control matching and limits

- All ordered task hashes and initial public-message hashes match across the three arms within all six groups. Original PREPARE, COHORT and SOURCE file hashes match the copied frozen-reference inputs.
- GUIDED and UNPARENTED initial experience REQUESTs bind the same initial adapter as the frozen reference: state `d13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f`, base `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`. Initial and evaluated adapter-file hashes were verified on-node.
- All 18 readouts have distinct process identities, parent-absent bindings/LOADED receipts and empty episode parent messages. Learned readouts match their exact saved sleep outputs and differ from their predecessor sleep processes. Frozen readouts retain the unchanged initial adapter, with zero optimizer steps/training rows and six successful fresh subprocess exits.
- Frozen execution's historical decoder/environment source hashes match canonical PREPARE. Shared greedy generation uses `do_sample=False`, one beam, the 512-output / 8192-context bounds, original task/episode/environment semantics, and no rich-contract readout steering. This is configuration/source matching, not a claim of cross-node bit-identical numerical execution.
- Realized cumulative updates by C1…C6: GUIDED **0,104,208,320,424,424**; UNPARENTED **0,104,208,320,424,536**; seeded frozen **0 throughout**. Doses are **not matched: 424 versus 536**. GUIDED C1 and C6 make no updates; do not attribute those readouts to new sleep updates.
- Groups change tasks and contain only one world each; this is not same-task longitudinal retention, multiple independent training replicas, or a population-level estimate. Frozen evaluation was later and on another node.
- Original parented bare-BASE NO_LORA is a different condition and is excluded. This completes the seeded-frozen reference measurement, **not a matched control for the later pooled R118 child**. Semantic learning/retained thinking and causal dependence on parenting remain unproven.

## Evidence and publication

Canonical root via `gpu/ovx2_ssh.sh`: `/tmp/orch_route_parent_campaign_20260915_canonical102`, GUIDED/UNPARENTED `cycle1…cycle6/readout` only. Frozen root via `gpu/ovx_ssh.sh`: `/localhome/local-rohing/orch_r118_frozen_seed_reference_20260915_attempt2`, `RESULTS/group_01…group_06`.

`COMPARISON.json` records exact COMPLETE/LOADED/BINDING/episode/predecessor refs, full task hashes, per-group artifact inventory hashes, saved state hashes and mechanical checks. Frozen terminal SHA `02bf9b90d1e194299b8e43fe99186a44337ee46f5429d3f4a5fccd15c09b9580`, finished 16:07:53 UTC, matches Main's published result. No raw response, token-ID sequence, task text, answer key or event-store content is included in this reduction.

Scope exclusions: no C0, unmatched C7/C8, newer DEV/FINAL, parent transcript review, label changes, retries or old-readout salvage. Only the first TRAIN experience REQUEST metadata was checked to establish initial-state matching. Main-reported failed second startup `2987f2` is not reinterpreted here; brokers and claims were untouched. Main retains GPU/Git ownership.
