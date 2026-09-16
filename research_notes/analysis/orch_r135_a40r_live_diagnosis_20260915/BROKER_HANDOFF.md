# R135 controller broker — frozen handoff

**Main launch update:** Both brokers are now launched by Main. Do not repeat the pre-launch recipes below. The actual staged source is `/data/home/rohing/courier/runtime/r135_controller_source_v1/orch_r135_a40r_broker.py`, with the frozen checksum below. Read-only controller census at **2026-09-15 22:33:27 UTC** verified serve0 PID **871039** and serve2 PID **871040**, exact source/slot arguments, their correct new queues and `/data` compatibility targets. Startup receipts record **22:32:37.681 UTC** on the controller clock (Main's launch time was approximate). Each startup verified eight frozen provider/principles files and Main publication. No completion receipts were present at that early check; this is not yet end-to-end provider completion evidence. See `BROKER_LIVE_CHECK.json`. Only these handoff artifacts changed; no source or process action was taken.

September 15, 2026. **Source frozen** at `cc06eb372a7449c79959ad3550b4fdc34ac9fbbc8900240f1dfd1e142c120ad3`. Adapter tests: **47 passed**. Main separately reports **162 tests + 124 subtests passed** at 22:32 UTC and both check phases passing. Both observed live preflights also passed at 22:31 UTC, including exact remote MAIN_READY/EPOCH/original READY, eight provider/principles file hashes, frozen controller imports, and Main publications.

The adapter uses `/tmp/orch_r129_dependencies_2106` and the unchanged `r111_recovery.broker` directory seam. Only exact `overflow_r135_v2/campaign_node1_7/parent_queue` paths are accepted. Physical0 starts at P113; physical2 starts at P128. Request filename, ID, original READY, TRAIN cycle and actual charged parent intent are checked before delegating to the unchanged claimant. C61/P128 is valid. No old queue copying, P127 reconsumption, alternate provider, safeguard fallback, credential change, timeout change, or STOP-policy change. No `R135.runtime()` call occurs on the controller.

`check` is read-only: it neither creates buffers nor claims requests, and is safe alongside live native guards. `serve` repeats the exact remote verification, takes one nonblocking flock per fixed queue, and creates a fresh bounded buffer/receipt namespace. The compatibility parent `/tmp/orch_r135_broker_a40r{0,2}_v1` must point only to `/data/home/rohing/courier/runtime/r135_broker_a40r{0,2}_v1`; the code verifies that actual storage is on `/data`, not the VM root filesystem. Existing/dirty buffers are not cleared or reused.

## Tests and checks

```bash
UV_CACHE_DIR=/tmp/orch_r135_uv_cache uv run --isolated --no-project --with pytest python -B -m pytest -q -p no:cacheprovider tests/test_orch_r135_a40r_broker.py
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/orch_r135_a40r_broker.py check --physical 0
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/orch_r135_a40r_broker.py check --physical 2
```

## Immutable staging — archival pre-launch recipe

Run from the repository. Exclusive directory creation prevents overwriting an earlier stage. Keep the existing controller account/environment; do not change authentication.

```bash
set -eu
STAGE=/data/home/rohing/courier/runtime/r135_broker_source_v1
mkdir -m 700 "$STAGE"
cp gpu/orch_r135_a40r_broker.py "$STAGE/orch_r135_a40r_broker.py"
printf '%s  %s\n' cc06eb372a7449c79959ad3550b4fdc34ac9fbbc8900240f1dfd1e142c120ad3 "$STAGE/orch_r135_a40r_broker.py" | sha256sum -c -
chmod 444 "$STAGE/orch_r135_a40r_broker.py"
```

## Launch — archival pre-launch recipe

After Main's publication, launch one separate controller process per slot with its normal audited launcher. These foreground commands are **not** a sequential script that starts both concurrently. Verify the source checksum above again before execution; stdout/stderr logs, if redirected, must live under `/data/home/rohing/courier/runtime`, not VM-root `/tmp`.

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /data/home/rohing/courier/runtime/r135_broker_source_v1/orch_r135_a40r_broker.py serve --physical 2 --repository /data/home/rohing/dream-state-orch
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /data/home/rohing/courier/runtime/r135_broker_source_v1/orch_r135_a40r_broker.py serve --physical 0 --repository /data/home/rohing/dream-state-orch
```

The adapter writes compact `BROKER_START.json` on `/data` after acquiring its queue lock. This task did not execute `serve`, stage a production broker, create production buffers, make provider/model calls, change Git/shared ledgers, or touch either live native guard. Main owns publication and launch. `BROKER_CPU_READY.json` records the exact source/tests and readiness evidence.
