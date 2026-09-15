# Main-ready paths (no Git mutation by this worker)

## Replay compiler

organism_v6/orch_continual_batch_replay_compile.py
gpu/orch_continual_batch_replay_compile.py
tests/test_orch_continual_batch_replay_compile.py

## Native publisher / branching / serialization source

gpu/orch_continual_batch_remote_feed.py
gpu/orch_continual_batch_snapshot_node2.py
gpu/orch_continual_batch_publish.py
gpu/orch_continual_batch_handoff.py
gpu/orch_continual_batch_codex.sh
gpu/orch_continual_batch_runtime.py
gpu/orch_continual_batch_segment.py
organism_v6/orch_continual_batch.py
tests/test_orch_continual_batch.py
tests/test_orch_continual_batch_handoff.py
tests/test_orch_continual_batch_serialization.py
tests/test_orch_continual_batch_immutable.py
tests/test_orch_continual_batch_remote_feed.py

The old runtime/mirror and segment preparation paths are superseded, NOT running. Do not launch them or interpret their inclusion as readiness. The native-only remote_feed runtime is the active implementation; its frozen live copies remain unchanged.

## Compact evidence only

research_notes/analysis/orch_continual_batch_20260915_disk_native1/REPLAY_COMPILE_HANDOFF.md
research_notes/analysis/orch_continual_batch_20260915_disk_native1/CHECKPOINT_TRAIN_SOURCE_HANDOFF_0459.json
research_notes/analysis/orch_continual_batch_20260915_disk_native1/QUIESCENT_RAW_INVENTORY_0457.json
research_notes/analysis/orch_continual_batch_20260915_disk_native1/REPLAY_CPU_TESTS_0454_FINAL.txt
research_notes/analysis/orch_continual_batch_20260915_disk_native1/REPLAY_CPU_TESTS_0503_ADAPTER.txt
research_notes/analysis/orch_continual_batch_20260915_disk_native1/NATIVE_REPLAY_CPU_REFERENCE_0505.json
research_notes/analysis/orch_continual_batch_20260915_disk_native1/REPLAY_SOURCE_REGISTRY_0505.json
research_notes/analysis/orch_continual_batch_20260915_disk_native1/READY_PATHS_0501.md
research_loop/workers/CONTINUAL_BATCH.md

Other files directly under disk_native1 are manifests, compact captures/results/failure/transfer/usage reductions, source inventories and receipts. No raw CALL forests, archives or training ROWS are written here by the active publisher. Main owns staging/push and verified old-raw removal. The old segment2 raw scopes are not part of this ready-to-stage list.
