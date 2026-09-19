#!/usr/bin/env bash
set -euo pipefail
: "${REVIEWED_FREEZE_SHA256:?set the reviewed SOURCE_FREEZE_V3.json file SHA256}"
NODE=/localhome/local-rohing/post_reboot_probe_queue_20260919
CANDIDATE="$NODE/candidate"
PY=/localhome/local-rohing/v2/venv/bin/python
SOURCE=/localhome/local-rohing/orch_r233_recovery_s24_probe_20260918
ORIGINAL=/localhome/local-rohing/orch_r232_age_probe_20260918
ROOT="$NODE/jobs/4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f"
QUEUED=/localhome/local-rohing/orch_r233_retained_source_queue_20260918/R232_SIBLING_FROZEN/R232_SIBLING_FROZEN_sleep_000024_7dfa305c4c2d689b
LEASE=/localhome/local-rohing/post_reboot_probe_dispatch_20260919/465dedb4d06300e2a82046af61bd914f915a4ccbe588d5f05fb0616b90440ae7/runtime/LEASE_AUTHORITY.json
export CUDA_VISIBLE_DEVICES=''
export PYTHONDONTWRITEBYTECODE=1
"$PY" -B - "$CANDIDATE" "$NODE/inputs/policy.json" "$REVIEWED_FREEZE_SHA256" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import admission as rules
import daemon
import probe_runtime as runtime
candidate = Path(sys.argv[1])
daemon.verify_freeze(candidate / "SOURCE_FREEZE_V3.json", sys.argv[3])
policy = runtime.read(Path(sys.argv[2]))
rules.validate_policy(policy)
runtime.verify_protected(dict(policy, queue_policy=policy))
for source in policy["supported_journals"]:
    runtime.verify_source_epoch(policy, source)
PY
mkdir -p "$NODE/jobs"
"$PY" -B "$SOURCE/source/research_loop/workers/rohin233_kept_age_probe_20260918/prepare_probe.py" \
  --root "$ROOT" --source-root "$SOURCE" --original "$ORIGINAL" --queued "$QUEUED" \
  --life /localhome/local-rohing/orch_r232_curriculum_frozen_20260918/raw \
  --condition R233_QUEUE_R232_SIBLING_FROZEN_s24
"$PY" -B "$CANDIDATE/bind_bundle.py" --root "$ROOT" --entry "$CANDIDATE/NEXT_ENTRY.json" \
  --policy "$NODE/inputs/policy.json" --lease-authority "$LEASE"
"$PY" -B - "$CANDIDATE" "$ROOT/runtime/CAPSULE.json" "$NODE/inputs/capsules.json" <<'PY'
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import probe_runtime as runtime
capsule = runtime.read(Path(sys.argv[2]))
registry_path = Path(sys.argv[3])
registry = runtime.read(registry_path) if registry_path.exists() else dict(schema="PREPARED_CAPSULE_REGISTRY_V1", capsules=[])
existing = [row for row in registry["capsules"] if row["source_key"] == capsule["source_key"]]
runtime.require(not existing or existing == [capsule], "never_replace_registered_capsule")
if not existing:
    registry["capsules"].append(capsule)
    temporary = registry_path.with_name(registry_path.name + "." + str(os.getpid()) + ".tmp")
    runtime.write_once(temporary, registry)
    temporary.replace(registry_path)
print(json.dumps(dict(status="CAPSULE_REGISTERED_NO_LAUNCH", job_id=capsule["job_id"], config_sha256=capsule["config_sha256"])))
PY
