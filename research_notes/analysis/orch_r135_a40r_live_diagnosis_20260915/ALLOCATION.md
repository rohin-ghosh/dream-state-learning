# R135 changed-context continuation allocation

[Builder / Main] 2026-09-15T22:19:17Z

Allocate only `gpu/a40r_ssh.sh` physical0 and2 to the exact prepared R135
continuations. Both prior campaigns failed context fit; old native inputs,
reservations, contexts, parent dispositions and terminal files remain unchanged.
The guard must perform a fresh privileged slot/UUID/process scan before loading.

| Physical | Exact UUID | First previously unreserved call | Inherited parent |
|---|---|---|---|
| 0 | GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d | 2048, C53 reflection turn2 | P112 COMPLETE retained |
| 2 | GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8 | 2329, C60 reflection turn2 | P127 MISSING retained; late COMPLETE ignored |

Whole initial prompts are6428/6191 tokens, including the entire last actual
child reflection, original system/pending instruction and applicable parent
disposition. Earlier context is archived node-local, not summarized or clipped.
These are declared changed-context forks, not identical-context continuations.
Frozen base, no LoRA, optimizer0; no old call is replayed or retroactively served.

Original limits remain16384native calls,640parent calls,256cycles,
32768context/8192output tokens, with absolute hard wall **September18,2026,
18:00UTC**. This does not extend a lease. Main84local CPU tests and73node R135
tests pass; both native tokenizer-fit/provenance preparations passed.
Canonical source SHA7950db91ab668697027c1d113daca49d2c70d278cbbc2e308935cfb0a1c8a3aa
is staged at `/localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2`.

**Parent routing remains pending at initial dispatch.** The first pending
reflection needs no new provider call. The broker adapter is being bound to
these new queues using the same existing Astra provider/settings; future
requests begin P113/P128. Do not claim full parenting readiness until that
binding is live and deliveries are observed. No Fable refusal is retried or
rerouted; this restores unrelated Astra lanes that failed context capacity.
If a future parent slot is missed, preserve its original missing disposition.

Epoch hashes: physical0
`0c8d22f2202b17710266206d8ca4c918ec83eacfb8e24a65490fc9c2da90839b`;
physical2 `3f879fc6ef3d31f64286c484b4627d8c7dd00731f215be8c605b5f6c0d16111d`.
Exact roots, preserved counter values and native CPU receipts are in
NODE_PREPARATION.json. Main publishes before launching separate CPU guards:
`python -B gpu/orch_r135_a40r_context_epoch.py guard --physical 0`
and the corresponding `--physical 2`, using the absolute staged source path,
empty CUDA visibility, offline model loading and the existing node venv.
Guards select the exact GPU UUID; never call native directly.

This is frozen-base context-only operation, not weight learning, and no
retention, parenting benefit or productive-reflection claim is made.
