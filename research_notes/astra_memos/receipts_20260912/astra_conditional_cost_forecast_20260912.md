# Conditional diagnostic: bounded cost forecast — EDIT-STOP

**2026-09-12. Planning scenarios, not measured conditional performance:** roughly **33–66 A40-minutes** with mostly short generations; **46–83 minutes** in a cap-heavy sensitivity scenario, under the assumptions below. **No defensible whole-run p50/p95 is available. Main's90-A40-minute ceiling is an authorization/budget limit, not a prediction or completion guarantee.** HF runtime is the largest unprofiled component. No live replay scores were opened.

## Work and native lengths

Fixed workload: **two fresh128-row/128-update fits**, **224 generations ×3 states =672 calls**, and **64 two-candidate HF requests ×3 states =192 requests/384 candidate forwards**. OFF/AUTH/DERANGED execute sequentially on one GPU, with separate cold generation/HF processes; no duplicated OFF or assumed batching/cache speedup.

Recounted attempt2's stored native rows and verified all six material-file hashes against its manifest:

| Native training quantity | Each AUTH/DERANGED arm |
|---|---:|
| Input/target tokens per epoch |11,248 /1,888|
| Four-epoch input/target presentations |44,992 /7,552|
| Total sequence lengths: min /median /max |81 /88 /95|
| Prefix lengths: min /median /max |66 /73.5 /80|
| Supervised continuation including EOS |96 rows×15 tokens +32×14|

Both fits total **89,984 input/15,104 target presentations**,256 updates. HF candidate strings match native training targets, but **dev/control prefix and HF-concatenation native IDs are missing here**; their total token cost is not measured.672×64 =43,008 output tokens is a ceiling, not expected usage. The material receipt authenticates no model-weight origin.

## What completed captures actually measured

Latency = response `ended`−request `started`; empirical percentiles interpolate rank `(n−1)p`. Calls are dependent, not independent run-level uncertainty estimates.

| Completed-call stratum | n | p50 seconds | p95 seconds |
|---|---:|---:|---:|
| Two-token outputs, pooled prior captures |192|0.123|0.127|
|10–20-token outputs, pooled prior captures |104|0.583|0.823|
| Two-habit readouts, all outputs2–24 tokens |96|0.936|0.993|
| Original OFF,64-token capped outputs only |16|1.807|1.814|
| Memory-only seed1,64-token capped outputs only |23|2.483|2.656|

Pool: **432 calls**—original OFF/control/teach144, memory-only192, two-habit96. Prior prompts41–47 tokens are shorter than conditional training prefixes66–80; these are not conditional percentiles.

- **Fitting:** original fresh80-update fits processed18,068 input tokens in20.7–20.9s training-loop time; supervised workers took60.36–72.64s. Warm memory80 took19.1–21.0s/14,080 tokens; two-habit80 took24.4s/20,328 tokens. Token-proportional scaling to44,992 predicts **52–67s loop/fit**; using fresh-fit overhead40–52s gives92–119s/fit. Allow **90–135s/fit** as an extrapolation range, not a fitted percentile.
- **Generation startup:** across11 workers, process-start→backend-ready was **38.69–78.45s**. Worker residual after subtracting readiness and call span was **36.47–50.62s**. These include imports/loading/backend initialization and post-call handling/cleanup respectively; neither is an isolated model-load or pure cleanup timer.
- **HF:** the completed parity worker took **64.70s for32 prefix/full forwards at42/44 tokens**, including setup, full-vocabulary artifact work and cleanup. Launch→full release was141.94s. **No per-forward timings or separate HF ready/load interval are stored**; consequently no HF request p50/p95 can be computed. Its two-token scoring workload is not the proposed14–15-token candidate scoring workload.

## Conditional stage forecast and accounting

| Component | Scenario allowance, all requested stages |
|---|---:|
| Two fresh fits |3–4.5min supervised workers|
| Three generation states, mostly short outputs |11–20min supervised workers|
| Same generation workload, cap-heavy stress alternative |24–37min supervised workers|
| Three HF states: mechanical sensitivity only |13–28min supervised workers|
| In-controller CPU validation/gaps |3–8min additional|
| External launch/release-observation allowance |3–5min additional|

Generation range: about0.6–1.2s/call ×224, plus75–130s startup/residual per state; upper margin reflects longer prefixes rather than an asserted measured slowdown. Cap stress uses about1.8–2.7s/call instead. **Multiplying a call percentile by224 does not produce a state/run percentile.** If a600s worker bound is retained, a224-call capped adapted state can exceed it before cleanup despite fitting under the aggregate ceiling.

HF sensitivity:128 forwards/state versus32 gives `4×64.70≈259s/state`; also scaling by native-training maximum length95/44 gives≈559s/state, or13–28min across states. **This scales fixed setup too: neither a calibrated interval nor an upper bound.** Actual dev lengths, scoring implementation and HF setup remain unprofiled; the prior3-second weight-loading progress bar is not total startup.

Thus **summed worker occupancy** is approximately27–53min short-output scenario,40–70min cap-heavy. **Sequential controller wall time** adds3–8min:30–61 or43–78min. **Single-GPU full reservation** adds3–5min external allowance:33–66 or46–83min. GPU kernel-active time is not measured by worker reservations. Prior controllers spent102–156s beyond worker sums, and full-release observation added155–262s beyond controller time; extrapolating those to this eight-worker workload motivates, but does not bound, the allowances. Standalone CPU preparation before allocation is excluded; any preparation/queue/collector wait while holding a device belongs in Main's ledger. Unbounded waits or HF overruns can exceed these scenarios.

**Sources:** `/tmp/astra_conditional_native_preps_20260912` attempt2 material; `/tmp/astra_{fundamental_seed0,memory_only,two_habit,hf_parity}_terminal_20260912` completed raw calls, process/readiness/supervision, fit and release receipts (brace notation names four directories). No live replay material inspected. Only this document written; no native/model/GPU/network/Git actions or new framework. **EDIT-STOP.**
