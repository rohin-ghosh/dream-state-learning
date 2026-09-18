# Parent-retention adoption sidecar

**Stage-only / NO-GO for live adoption.** Read `DECISION.md` first.
All artifacts and temporary writes are confined to this worker. No action
implements deployment, source mutation outside the worker, restart or signaling.

From the repository root:

```bash
WORKER=research_loop/workers/post_recovery_parent_retention_adoption_20260918
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -B "$WORKER/adoption.py" dry-run --observation SOURCE_STRUCTURE_OBSERVATION.json
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -B "$WORKER/run_cpu_checks.py" --log CPU_TESTS_RERUN.log
```

Optional source-metadata refresh (read-only existing SSH wrapper, no GPU use):

```bash
python3 -B "$WORKER/adoption.py" capture --observation SOURCE_REFRESH.json
python3 -B "$WORKER/adoption.py" stage --observation SOURCE_REFRESH.json --output stage_refresh
```

These refuse existing output names, changed process incarnations or any drift
from phase2's full guarded source closure. A refresh is not permission to launch.
The default original observation remains historical; no freshness/activation
claim is inferred by dry-run/stage. The fixed phase2 provenance, manifest, patch
and capture hashes are embedded in the helper. Exact preimages and postimages
are verified by strict `git apply --check`, application, and SHA-256 comparison.

`stage/` is an incomplete, non-dispatchable **three-file overlay**, not a complete
source tree. It contains no runtime guard/plan/checkpoint or deployment entrypoint.
Its receipt proposes the new source pins and retains all other observed pins.
Never use it to overwrite a diverged checkout; independently verify each target's
preimage before main integrates. Keep all existing recovery/checkpoint-tail/R227/
frozen-optimizer changes outside these exact three-file deltas.

`SOURCE_OBSERVATION.json` and `SOURCE_STRUCTURE_OBSERVATION.json` contain source
hashes, process/guard/lease metadata and function-call metadata only; no score
panels, model payloads or journal records. `REVIEW_BINDINGS.json` records reviewed
source identities; `ARTIFACTS.json` is the integration allowlist with file hashes.
