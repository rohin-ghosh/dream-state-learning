# Short commands can still express useful action-level behavior

Read-only audit, September 15, 2026. Same original 12 tasks / 36 episodes / 183 responses across canonical GUIDED, UNPARENTED and seeded-frozen C1–C6. No FINAL, models, parent calls, scorer changes, retries or broker mutations. Exact episode hashes match the preceding comparison.

**The earlier command-only finding does not imply absence of useful behavior.** GUIDED's committed routes consistently match previously returned public memory and a publicly evidenced path to the goal. There is a concrete state-tracking/commitment-order contrast at C4 with GUIDED and UNPARENTED both at 320 updates. However, useful routing also occurs in the frozen seed; GUIDED's reading is exhaustive rather than demonstrably targeted, and causal reliance on feedback or parenting is not isolated.

## Directly counted behavior — all 12 tasks per arm

| Observable | GUIDED | UNPARENTED | Seeded frozen |
|---|---:|---:|---:|
| READ attempts / accepted episode-unique reads | 43/43 | 39/39 | 37/37 |
| Distinct event addresses across whole cohort | 24 | 24 | 24 |
| Repeated READ attempts within episode | 0 | 0 | 0 |
| READs before / after first committed route | 43 / 0 | 36 / 3 | 35 / 2 |
| Episodes reading all four events | 10/12 | 8/12 | 7/12 |
| Episodes reading in displayed address order | 12/12 | 12/12 | 12/12 |
| ROUTE attempts / committed routes | 22/20 | 21/17 | 21/17 |
| Original `invalid_route` rejections | 2 | 4 | 4 |
| Invalid command syntax | 0 | 0 | 0 |
| Committed routes matching previously read EVENT | 20/20 | 16/17 | 17/17 |
| Committed routes on a previously evidenced goal path | 20/20 | 16/17 | 16/17 |
| Subsequent routes after actual transition feedback | 10 | 8 | 8 |
| Of those subsequent routes, sole currently available port | 10/10 | 8/8 | 8/8 |
| Committed routes to terminal wrong destination | 0 | 0 | 0 |
| Node revisits | 0 | 0 | 0 |
| Extra pre-route READs after a full goal path was already available | 7 | 4 | 2 |

All 119 returned memory results parse as actual EVENT records. All 54 committed routes agree with the returned public receipt and next CURRENT/PORTS. Every one of the ten rejected routes selects a port mentioned in a previously read EVENT **for a different source node**, not a malformed or wholly invented command. One UNPARENTED and one frozen rejection reuse a port that was available at an earlier CURRENT but is no longer available.

“Matching read evidence” means source/port/destination/receipt equality against an EVENT already in the prefix. “Goal path” is derived only from already returned EVENT edges, the public CURRENT/GOAL, and remaining route budget—not hidden world edges. These are evidence-consistency measurements, **not proof the model causally used or understood the evidence**. Denominators exclude rejected route attempts; their errors are reported separately.

## C4: equal 320-update GUIDED/UNPARENTED contrast

E1 succeeds with identical action sequences in all three conditions. The informative difference is **E2**, task SHA `b0fda5e156b1269db6e5b6c98f8e1d751c660eccacac15edd735918d300267a7`.

All three first read `E_BVF6C7NMWT`. Its actual returned record describes **intermediate node** `N_MKVG24JT55` via port `P_YA6NGABBMK` to the public goal `N_VCHDZY62DL`; it does not say that port is available at the current root. Turn 2 has the same full public-prefix hash in all arms: `167cd38c8bf5ac0ae7bb80b6c6a86964146ed778562f0309a6f76cdc2c6910eb`.

- **GUIDED:** reads the remaining listed events before committing. The second read supplies the root→intermediate connection; a complete goal path is already public then, but GUIDED still reads two additional alternative-path events. It commits `P_FZERR6OVV5`, receives CURRENT=`N_MKVG24JT55` / PORTS=`P_YA6NGABBMK`, then correctly commits that sole port. Sequence: four READs → two valid ROUTEs; success.
- **UNPARENTED:** after only the first read, commits the valid root port `P_FZERR6OVV5` before its matching root-edge memory is read. The actual receipt places it at the same intermediate node, with sole port `P_YA6NGABBMK`. It then reads the other three events but outputs `P_QXSCBXLUGK`, an old **root** port unavailable at its current node. Original scorer records `invalid_route` and stops. This is a concrete failure to respect updated public CURRENT/PORTS—not a failure to emit explanatory prose.
- **Seeded frozen:** after the first read, immediately attempts intermediate-only port `P_YA6NGABBMK` while still at the root. Original result: `invalid_route`; no route is committed.

Episode receipt hashes: GUIDED `91b1e26107b0d7bda11def068a036b34966b23b1f723a33865da748b48e1b2ee`; UNPARENTED `caf47fd113c1b5adfe8f50f15c2af9d9261e325fb8f9fe9d4652d6f5ffa101ee`; frozen `edf989e60fd804908e8a24dbaac667e9b9d56a63fc16f35d345549632fa5a152`. Exact per-action IDs, capture/feedback hashes and original paths are in the compact JSON.

**Interpretation:** GUIDED expresses a useful evidence-before-commitment/state-consistent action sequence at this task. Equal cumulative update counts remove the simple total-update-count difference at C4, but not different training content, parent exposure, optimization histories or single-lineage confounding. The result does not establish parenting causality or semantic self-reflection.

## C5: equal 424-update learned arms; mixed effort-allocation result

**E2** task SHA `1bcd888d25f7359526072fae14e7fa025fa52b1f8b431ae789194e35c11a34d6`:

- GUIDED and UNPARENTED have identical four-READ/two-ROUTE sequences and succeed. They wait for `E_SUSH6OH76J`, which connects the root to `N_Q2E7S6Y5VZ`; the earlier `E_MDR3MILPXO` supplies that node's route to the goal. After receiving all four events they commit `P_HQ62U3NUPF`, then the newly listed `P_PL5TYRE3PS`.
- Frozen diverges at turn 3 from the same public prefix, SHA `e1ced18bdbcb462bc940c13e8b7e924f18f8029083655fb0fd0d1a29f37ad788`: it commits the other root port `P_7Y7ST5JZ5W` after two READs, before a complete goal path is publicly supported. The receipt moves it to `N_472ZKNJKBK`, whose sole port is `P_QYDSZMIX3F`. It then reads two more events and attempts the root-only `P_HQ62U3NUPF` from this intermediate node: `invalid_route`. This is an attempted stale-source action, **not a successful revision or return**.

Both learned E2 episode files have SHA `9da7b83a3999886ff5c149194295617bd621e84a57486bcb26361df14b3386d2`; frozen SHA `720bdb3810c4ead93be129994cdd7392624314eda146b68e24a0540f9996926d`. This contrast supports useful learned-arm action behavior relative to this seed on this task, but **not a GUIDED advantage over equal-update UNPARENTED**.

**E1 counterexample to “more effort is better”:** all succeed. UNPARENTED and frozen stop reading after the third event establishes the required path, then take two routes. GUIDED reads the fourth event before taking the same route pair: six rather than five calls. Divergence follows identical prefix SHA `5cf0a2fdaf2d4267f1ec79e47837de0ab0b06ad204beb5d945646ba477a6acab`. The extra READ may check an alternative; it is not automatically an error, but it does not improve the observed outcome.

## What this does and does not establish

- **Positive behavioral evidence:** fresh parent-free checkpoints execute memory-consistent multi-step routes; C4 demonstrates a precise state-consistency contrast at equal 320 updates, and C5 shows learned-arm avoidance of a premature commitment/stale-port failure at equal 424 updates.
- **Effort allocation remains mixed:** all 36 episodes read an ordered prefix of the displayed event list. GUIDED's ten successes all use all four READs. This resembles broad prefetching, not demonstrated selective information seeking. Seven GUIDED extra READs occur after a complete goal path is already public, versus four UNPARENTED and two frozen.
- **Revision is not directly measured:** there is no declared plan/expectation to track in these short outputs. Invalid commands end the episode; their error is captured by the runner and is not followed by a child correction opportunity. No error-recovery or reflective-revision success is inferred.
- **Zero revisits/repeated reads is weak evidence:** the task graph is a shallow directed tree; repeated READs are forbidden and errors terminate. The environment does not provide a general retry/backtracking test. Second committed routes have a single available port, limiting claims about choice after feedback.
- **Not a retained-cognition or causal parenting proof:** seed itself succeeds on eight tasks and supports 16 goal-path-consistent routes. C4/C5 equal update totals do not equalize training experience. Across C1–C6 the totals are still 424/536/0. There are only two episodes per group, changing tasks, no feedback-ablation/perturbation intervention, no repeated training seeds, and no pooled-R118 control.

Original outcomes remain GUIDED10/12, UNPARENTED8/12, frozen8/12. The useful correction to the earlier form-only summary is **“action-level evidence consistency and specific state-tracking differences are present,” not “retained thinking is proven.”**

## Reproducibility and scope

`ACTION_AUDIT.json` binds the previous comparison and all 36 unchanged episode hashes. Every capture joins its actual CALL response/messages; all public prefixes and returned feedback were checked in sequence. Detailed C4/C5 examples contain opaque IDs and hashes, not raw transcripts. Other episodes retain action IDs/counts/receipt hashes only. “Known” always means publicly available, never an attributed model belief. Original scorers and labels are unchanged; all raw remains on the original nodes.
