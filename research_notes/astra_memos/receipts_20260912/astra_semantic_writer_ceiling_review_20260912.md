# Independent OFF-only ceiling review — 2026-09-12

**Verdict: confirmed.** Exactly **30/64 root/map/key median-gain requirements** are mathematically unattainable at the frozen **>= 0.50 nat** threshold, conditional on the supplied OFF scores and the current reducer. Each of the four root/map cells contains an unattainable requirement, so **all four cell-level optimization conjunctions necessarily fail**, irrespective of valid future ON scores. This is exploratory assay diagnosis, **not a final C11 guard**.

## Independent reconstruction and correspondence

- Read the specified prepared `material.json` and `requests.json`, the ceiling script/JSON, and relevant source. Computed directly from **128 OFF primary score records**; did not execute Main's script or import project modules. Used standalone standard-library CPU arithmetic, including 60-digit Decimal binary normalization. No ON outputs, GPU, network, git, or repository writes; this review is the only output file written.
- Verified exactly one OFF primary score request for each `(root, held index)`: roots 0/1, indices 0–63. Each request's owner/probe root, prompt, seed, tool and mode match its actual held row. Verified content-derived request IDs, raw `request_id`, canonical `request_sha256`, `attempts == 1`, and `adapter_sha256 == "OFF"` for all 128 records.
- Candidate order is actually **0 = `ACT: -mem2reg\n`, 1 = `ACT: -gvn\n`**, not the generic gateway's a0/a1 strings. The semantic carrier supplies these candidates; the generic gateway supplies only the index mapping and normalization here. Verified candidate prefix/response concatenation, masked labels, and complete finite nonpositive token-logprob vectors: **8 and 7 scored tokens**, respectively. Summed complete candidate vectors, with no token-length averaging, matching `score_sums`.
- Actual orientations match the source: root 0 `(0,0,1,1,0,1,0,1)`; root 1 `(0,1,1,0,1,0,0,1)`. `action = orientation[root][slot] XOR mode XOR (map == W-)`; therefore W- reverses the target, rather than reusing W+'s OFF target. This is exactly the target used by `reduce_records` for the same held index. Held rows do not supply an alternative stored target.
- Coverage is **2 roots × 2 maps × 8 slots × 2 modes = 64 key-map groups**, each with exactly four distinct held templates **8,9,10,11**: 256 target-specific bounds from 128 OFF observations, not 256 independent observations. Each cell contains 16 keys and 64 template-level target evaluations.

## Derivation and median-of-four rule

For complete candidate log-likelihood sums `S0,S1` and the actual target `t`, the source's natural-log normalization is

`log q(t) = S_t - log(exp(S0) + exp(S1)) <= 0`.

Thus each fitted-versus-OFF conditional gain satisfies

`g_i = log q_ON(t_i) - log q_OFF(t_i) <= b_i = -log q_OFF(t_i)`.

Independently evaluated `b_i = ln(1 + exp(S_other - S_target))` with Decimal. Coordinatewise domination implies domination of every order statistic. For four observations, the source's `statistics.median` is the **average of the second and third sorted values**, so

`median4(g) <= [b_(2) + b_(3)] / 2 = median4(b)`.

This does not assume gain ordering matches OFF ordering, nor replace a median of differences with a difference of medians. A ceiling **strictly below 0.50** proves impossibility even allowing ideal `q_ON = 1` (a limiting ceiling for finite two-candidate scores). The frozen test is inclusive `>= .50` for **every one of 16 keys**; it is not a mean, majority vote, or raw-target-loglikelihood test.

## Numbers

All values below are nats; slots/modes are zero-based.

| Root/map | Impossible / 16 | Not ruled out / 16 | Largest impossible ceiling | Smallest ceiling not ruled out |
|---|---:|---:|---:|---:|
| 0/W+ | 8 | 8 | 0.209278547779 | 1.087718374112 |
| 0/W- | 8 | 8 | 0.487578124203 | 1.754923438269 |
| 1/W+ | 7 | 9 | 0.463732727675 | 0.536497941625 |
| 1/W- | 7 | 9 | 0.393612016744 | 0.511044663858 |
| Total | **30 / 64** | **34 / 64** | | |

Impossible `(slot,mode)` keys:

- **0/W+:** (0,0), (1,0), (2,1), (3,1), (4,0), (5,1), (6,0), (7,1).
- **0/W-:** (0,1), (1,1), (2,0), (3,0), (4,1), (5,0), (6,1), (7,0).
- **1/W+:** (0,0), (1,1), (2,1), (4,1), (5,0), (6,0), (7,1).
- **1/W-:** (0,1), (1,0), (2,0), (3,0), (4,0), (5,1), (6,1).

Example: root 0/W+, key (0,0) has OFF-derived bounds `[0.171867835225, 0.052897653632, 0.587681868509, 0.002431881764]`; its median ceiling is `(0.052897653632 + 0.171867835225)/2 = 0.112382744428`, despite one template having more than half a nat of headroom.

All 256 template bounds, all 64 medians, and all feasibility flags agree with Main's JSON. Maximum absolute difference from Main's numerical values is **3.36e-15 or less**. Computing medians with exact-decimal token sums versus Python-float token sums changes them by **2.31e-15 or less**. The closest impossible ceiling is **0.487578124203**, still **0.012421875797** below threshold; the nearest nonexcluded ceiling is **0.511044663858**. No classification is a rounding-edge case.

## Gate consequence and claim boundary

`cell_gates` ANDs all 16 half-nat requirements. `reduce_records` then ANDs both map cells within each root and also requires mean-gain asymmetry `<= .25`; it finally ANDs roots. Therefore both root-level and the combined `optimization_ok` must be false for any complete, valid scored run with these OFF baselines. **The asymmetry requirement itself is not shown to fail**; it cannot rescue an already-false conjunction. Nor does this calculation establish failure of the other gate categories or the eventual classification label.

This proves a fixed-assay headroom obstruction, **not writer ineffectiveness or absence of learning**. The other 34 keys are merely not ruled out by this bound, not guaranteed attainable under a shared adapter. It does not evaluate ON acquisition, generation/binding, locality/spill, interface, raw target-sum gains, retention, parenting, or final C11 validity. Normalized two-candidate probability is not unrestricted generation probability. The source's synthetic, seen-key, root/seed-confounded, non-replicated and deferred-C11 boundaries remain intact. Request/hash and arithmetic checks are not a full tokenizer/model/provenance or raw-stage-custody audit.

**No gate or schedule change is proposed or made.** Main's fixed run continues as instructed: acquisition magnitudes and locality metrics remain informative even though these optimization pass/fail conjunctions cannot succeed. Preserve the current gates and all outcomes.

## Evidence fingerprints

Prepared directory: `/tmp/astra_semantic_writer_prepared_20260912/astra_semantic_writer_Q0_20260912_attempt1/`.
Raw directory: `/tmp/astra_semantic_writer_off_20260912/stages/off_score/raw/` (OFF primary score subset only).

- `material.json`: `769ee38ab444c9e56b6ce7dbf93be95f49e113ca7a60e02322349a53c3ef4336`
- `requests.json`: `a1795b1ea6a19399954f700624ed2155613b9197f4758ef86f8c772c81963c6c`
- `organism_v6/semantic_writer_diagnostic.py`: `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0`
- `organism_v6/multikey_writer_gateway_simple.py`: `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8`
- `organism_v6/semantic_carrier_diagnostic.py`: `fd31dc722f7a1a4b65a2fb597811e2598d603c650e8f6fe4e852915fc38c7392`
- Selected raw inventory: `de626ec6a6ebfd0bcc27dc625054efd2a9d71f4409c71fd554a326561a300466` (SHA256 of sorted `[filename, file-SHA256]` pairs, compact sorted-key UTF-8 JSON plus newline).
