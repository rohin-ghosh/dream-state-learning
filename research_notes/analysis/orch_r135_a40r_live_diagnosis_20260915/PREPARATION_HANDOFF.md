# R135 CPU preparation and Main handoff

**Native CPU-ready; not launched; broker routing pending.** September 15, 2026 UTC. Canonical source is `/localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2/gpu/orch_r135_a40r_context_epoch.py`; canonical campaigns use `overflow_r135_v2`. No existing runtime source, provider policy, repetition-stop policy, credentials, shared ledger, allocation, or Git state was changed.

Local source: `gpu/orch_r135_a40r_context_epoch.py`. Tests: `tests/test_orch_r135_a40r_context_epoch.py`. Source SHA-256 `7950db91ab668697027c1d113daca49d2c70d278cbbc2e308935cfb0a1c8a3aa`; tests SHA-256 `7efb4612164c31a9ce34cd816c992d313daf7f47eaa8d88367cc89dec68d69fb`. **84 local tests passed** (73 R135 + 11 R129 reference); **73 R135 tests passed on-node** against the exact frozen native-function source, with synthetic engine execution only. Local receipt: `CPU_TESTS.json`; compact node evidence index: `NODE_PREPARATION.json`.

## Prepared state

| Physical | Pending native | Parent disposition retained | Whole compact prompt | Original context / effective output cap |
| --- | --- | --- | --- | --- |
| 0 | C53 turn 2, **2048** | P112 COMPLETE; next future parent **113** | **6,428** tokens | 32,768 / 8,192 |
| 2 | C60 turn 2, **2329** | P127 MISSING, empty advice; late COMPLETE ignored; next future parent **128** | **6,191** tokens | 32,768 / 8,192 |

Campaign0: `/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2/overflow_r135_v2/campaign_node1_7`.

Campaign2: `/localhome/local-rohing/orch_r109_route_20260915_r120_C39_fork_a40r2_attempt1/overflow_r135_v2/campaign_node1_7`.

Each campaign contains `EPOCH.json`, byte-identical inherited `READY.json`, `CPU_PREPARATION.json`, `NATIVE_CPU_TESTS.json`, and **`MAIN_READY.json`**. The last receipt binds the exact epoch, source, preparation, native CPU test proof, original READY, token fit, inherited counters, and unchanged charged ledger. It reports `native_CPU_ready=true`, `broker_route_ready=false`, `launch_authorized=false`. Its hashes are in `NODE_PREPARATION.json`.

`CARRY.json` retains the complete latest actual child reflection, original system message, original pending instruction with an explicit new-context notice, and actual applicable parent advice. `ARCHIVE_CONTEXT.json` preserves the full pending context and references the earlier preserved evidence, including the previous R129 carry. **These raw files remain node-local.** No synthetic summaries, tail clipping, historical train/native replay, or retroactive parent consumption. Frozen base, no adapter, optimizer0, original caps and absolute deadlines remain unchanged. Host hash + physical slot + exact UUID + root + original relocation must all match; wrong slots, source aliases, hash drift, stale ledgers, or an existing next-call artifact fail closed. The first native reservation rechecks the unchanged full ledger while holding its exclusive lock.

The initial v1 preparation proved slot0 fit but rejected slot2's pre-existing source symlink before writing its output. All 182 original source hashes matched. v2 permits only the exact original shared source target, with regressions rejecting other aliases and per-file redirects. **v1 is preserved but superseded and must not be launched.**

## CPU commands — already executed

The following stage command is provenance documentation, **not a request to overwrite or rerun the existing v2 stage**. Its exclusive `mkdir` fails if that stage exists.

```bash
set -o pipefail
tar -cf - gpu/orch_r135_a40r_context_epoch.py tests/test_orch_r135_a40r_context_epoch.py \
  --transform='s|research_notes/analysis/orch_r135_a40r_live_diagnosis_20260915/CPU_TESTS.json|CPU_TESTS.json|' \
  research_notes/analysis/orch_r135_a40r_live_diagnosis_20260915/CPU_TESTS.json |
  bash gpu/a40r_ssh.sh 'umask 077; mkdir /localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2 && tar -xf - -C /localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2'
```

The exact CPU preparation command was run once for each physical slot; it refuses to overwrite an existing epoch:

```bash
for physical in 0 2; do
  bash gpu/a40r_ssh.sh "env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2/gpu/orch_r135_a40r_context_epoch.py prepare --physical $physical"
done
```

**Use `verify`, not `prepare`, for the current artifacts:**

```bash
for physical in 0 2; do
  bash gpu/a40r_ssh.sh "env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2/gpu/orch_r135_a40r_context_epoch.py verify --physical $physical"
done
```

On-node native CPU test command, also recorded and hashed in each `NATIVE_CPU_TESTS.json`:

```bash
bash gpu/a40r_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=/tmp/orch_r135_native_cpu_20260915_v2:/tmp/orch_r135_native_cpu_20260915_v2/python_deps /localhome/local-rohing/v2/venv/bin/python -B -m pytest -q -p no:cacheprovider --rootdir=/tmp/orch_r135_native_cpu_20260915_v2 --confcutdir=/tmp/orch_r135_native_cpu_20260915_v2 /tmp/orch_r135_native_cpu_20260915_v2/tests/test_orch_r135_a40r_context_epoch.py'
```

The node runtime did not have pytest. An isolated `/tmp/orch_r135_native_cpu_20260915_v2` harness holds the exact test bytes, references the exact staged R135 source and frozen original native source, and uses pure-Python pytest dependencies copied from the local isolated test environment. No installation or modification of the node's runtime environment occurred. Test stdout was displayed and retained in the harness log. These tests execute mocked native-function boundaries, not a GPU engine. Actual token-fit preparation loads only the local tokenizer, never model weights.

## Broker routing and liveness — outstanding Main handoff

**No: unchanged existing lane brokers do not keep polling the R135 queues.** The lineage roots remain the same, but the campaign/queue paths change. R129's directory adapter targets `overflow_r129_v1/campaign_node1_7`; R120's targets `lease_r120_v2/campaign_node1_7`. The unchanged provider poll loop (`gpu/orch_r109_route_broker.py:102`, SHA `ed5a903ccddc77c791ad38ead4dfa547dad9395511560fb9dda5f7867a9bafc4`) exits when its own campaign's `TERMINAL.json` exists. Both historical campaigns are terminal FAILED.

At **22:09:09 UTC on this controller** and **22:09:10 UTC on a40r**, targeted process metadata found **no broker for either target root / R129 / R135**. Two other R120 life brokers were present but target different roots. Old and new parent queues are separate non-symlink directories; both new queues have zero requests. This is a bounded lane-poller census, not an assertion about downstream provider service availability or other controllers. No provider probe was made.

**Smallest pending handoff:** Main's parent-broker owner must bind the existing unchanged broker/provider transport to each new campaign directory, with the existing authentication unchanged. Use the existing `orch_r111_route_recovery.broker` directory-adapter seam, but target precisely the corresponding `overflow_r135_v2/campaign_node1_7/parent_queue` and its new PUBLICATION/epoch binding. Each slot needs its own bounded buffer and receipt namespace. Reuse the current provider implementation and account; do not change provider or stopping policies. This is a new queue-routing binding, not a replacement model/provider.

- Physical0: route only future R135 requests **P113 onward** for its exact root/UUID/epoch.
- Physical2: route only future R135 requests **P128 onward** for its exact root/UUID/epoch.
- Do not copy old requests, redirect old queues, remove old terminal markers, replay P112/P127, or convert P127's late response into consumed advice.
- Do not call the GPU-node-only `R135.runtime()` on the controller as a broker bootstrap: its exact-host guard deliberately fails there. The broker owner should validate the remote epoch/slot via the existing wrapper and use the existing CPU provider transport's directory binding.
- No broker adapter or process was launched here. `orch_r135_a40r_context_epoch.py` intentionally exposes no broker-launch phase. **Treat full campaign broker readiness as pending**, even though the initial unreserved child continuation requires no parent call. Later cycles retain the original bounded parent-wait/missing-disposition behavior; launching without routing would leave future requests unserved.

## Launch commands for review only — not executed

After Main's own tests, exact allocation/publication, GPU admission review, and broker-routing handoff, the concrete foreground guard commands are:

```bash
bash gpu/a40r_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2/gpu/orch_r135_a40r_context_epoch.py guard --physical 0'
bash gpu/a40r_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r135_a40r_context_source_20260915_v2/gpu/orch_r135_a40r_context_epoch.py guard --physical 2'
```

These are separate foreground commands, not a serial script expected to start both concurrently. Main may use its own audited process launcher. The guard selects the exact UUID for the native child and retains the existing privileged admission scanner; do not call `native` directly as a shortcut.

Main must first create each new campaign's `ALLOCATION.md` and `PUBLICATION.json`. The code requires `epoch_sha256`, `ready_sha256`, `allocation_sha256`, `source_sha256`, and `dated_builder_publication=true` to match. Main should additionally bind `MAIN_READY.json` / `NATIVE_CPU_TESTS.json` and the broker handoff in its publication. Those allocation/publication files and all launch markers were absent when native readiness was issued. **Readiness is not launch authorization.** Main owns those writes and shared coordination/Git; none were performed here.
