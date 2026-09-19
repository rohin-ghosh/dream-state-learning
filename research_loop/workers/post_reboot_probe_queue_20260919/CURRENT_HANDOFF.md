# Current handoff — 2026-09-19 03:32:49 UTC

**September19 04:13:06 UTC:** immutable same-job V3→V4 rebind is now verified.
Use `V4_REBIND_HANDOFF.md` for the final seal/config/registry pins and Main's
exact review-pinned foreground command. No activation or GPU work occurred.
The earlier missing-rebind blocker is resolved; fresh admission is still required.

**September19 04:01:29 UTC update:** see `V4_HANDOFF.md` for the separately sealed
bounded-cache repair, measured costs and V4 activation blockers. V3 bytes and
the concrete source capsule described below remain unchanged; V4 is NOT rebound
or activated. The rest of this document is the historical V3 handoff.

**OFFLINE CANDIDATE WITH ONE CONCRETE CAPSULE — READY FOR MAIN REVIEW, NOT ACTIVATED.**
This dated receipt supersedes the pre-construction status in README, earlier
REVIEW_READY.json and seals V1/V2. No GPU work, native/scorer signal, daemon
activation or boot installation was performed. The completed465ded… job was
never rerun; its one error was only rechecked with CPU tokenization.

## Exact bytes and tests

- Current seal: `SOURCE_FREEZE_V3.json`, SHA256
  `27fb65865fb5a313f21575b47b7ebafa180b6e9677543bb4e9e82d8dc0becb0c`.
- Canonical unchanged policy SHA256:
  `605c43ba2c87ead62f49c3efcc80a0f80689a1bc9ff20466478839497dfebd1b`.
- **58 CPU regression tests PASS locally and on the receiving host**. Local
  receipt `offline_receipts/REGRESSION_TESTS_V3.log`, SHA256
  `4d50c463cf722d09be001a63a658d1b0a7e464e716b48007e8a7994353dbfa6b`.
  Launch tests mock the executor; none is a GPU smoke run.
- Receiving candidate: `/localhome/local-rohing/post_reboot_probe_queue_20260919/candidate`.
  Prior receiving bytes are preserved in sibling `candidate_v2_sealed`.
- V3 fixes the real legacy multi-condition history case and refreshes host/claim
  observations after expensive source/provenance checking before durable INTENT.
  The copied four-module job runtime is unchanged between V2/V3 and was verified
  against the receiving V3 release after staging.

## Concrete next capsule — constructed and registered

`R232_SIBLING_FROZEN`, sleep24, optimizer0, COMPLETE800>frontier799. Captured
epoch remains LOADED74; it is not relabelled into the current live epoch.

- Job ID: `4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f`.
- Root: `/localhome/local-rohing/post_reboot_probe_queue_20260919/jobs/4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f`.
- Config: `runtime/JOB_CONFIG.json`, SHA256
  `c43eccadff2b9b1a5f0de5af45a3333e7f480f8b921d0a6c2f6e50368d3cbc4f`.
- Capsule: `runtime/CAPSULE.json`, SHA256
  `ce098e710484647d9edce1fb55692a26f57ae814a2d99bd9c119d7b66bb4c98a`.
- Registry: `/localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/capsules.json`,
  exactly one capsule, SHA256
  `678b26ac9fe1567550bfe0fb763a3f9ef523ef8c77d18094565d57aa47907250`.
  Local exact copy: `offline_receipts/REGISTERED_CAPSULES.json`.
- Four checkpoint files verified,103 original scientific files, original
  freshness audit:124 records,72 requests, one inherited source state, zero
  identifier/scene matches. Actual preparation returned CPU_SOURCE_READY_NOT_LOADED.
  Freshness file SHA256
  `0af5af57b7e558a399c7e1fc80dfc2378eb0054375c5b5ded9f2be54e7589bcd`.
- Original3 scenes/seeds23201+23202/6×1024=6144 tokens/judge/control; UUID-bound
  player2/judge7; no parent text, optimizer state, training or feedback publication.
- Latest read-only marker check: activation.json ABSENT; LAUNCH.json ABSENT;
  no new JUDGE_LOADED or player_DEVICE_PROOF. Constructor/binder PIDs exited.
  No new claim/reservation, actual model LOAD or GPU dispatch is asserted.

Construction used the sealed `CONSTRUCT_NEXT_CAPSULE.sh`. An initial missing
jobs-parent directory stopped preparation before job creation. After creating
that scoped directory, preparation completed; the tool timed out while the same
CPU binder continued. Its completed markers were observed without restarting it.
Because its output connection had closed, only the verified final registry append
was subsequently performed. **Do not rerun construction for this existing root.**
The V3 construction script includes the directory prerequisite for future use.

## Fault adjudication

See `POLICY_ADJUDICATION.md`. Blanket pausing on every shortfall was my addition,
not inherited policy; it is removed. A cleanly terminated authenticated6-cell6144
run whose only unknowns are independently reproduced original pre-model input
length guards receives COMPLETED_WITH_SCORING_SHORTFALL/no-retry; later independent
ages may run after original claims and handles clear. Unknown is never zero or
rejected, and this is not a clean comparison claim.

Generic provider/launch errors, incomplete runs, changed source/identity/lease,
provenance ambiguity or actual platform denial still persistently pause. No
retry or alternate route. The evaluator itself remains byte-identical.

The new classifier was run read-only against465ded… on the receiving host:
exact caption/request/result/config/tokenizer joins reproduced621>512, all_verified
true, model_loaded=false, scoring_called=false, job_relaunched=false. This was
not a new judgment or corrected measurement.

## Preserved backlog and remaining blockers

Latest local projection: **1660 ages across all16 roots retained**. Five known
attempted sources tombstoned; one prepared CPU-eligible source awaiting current
admission;182 pending capture/exposure/binding;32 historical pending;1440 pending
unsupported family. `offline_receipts/DISPOSITIONS_READY.json` keeps each age
and epoch with its explicit reason. No latest-only collapse or deletion.

The registry is no longer empty. Nevertheless, activation still requires Main's
review of exact source/config/route and fresh receiving identity/occupancy/claim
proof. Six protected identities matched at1789787880.7791848, but that old read is
not a present GPU reservation. Current admission performs its own checks. Future
retention/source adoption must use the explicit reviewed rebind path, never
automatic PID/epoch following; old capsules/ages remain explicit pending evidence.

The staged enrollment files are snapshots, not a newly duplicated collector.
Keep them refreshed using the existing owner/observer. Future prepared capsules
must be appended from the original capture/exposure path; v1 does not silently
convert the remaining182 missing bundles into executable jobs.

## Exact activation steps — for Main after review; NOT executed

1. Re-run receiving CPU tests and verify the source seal/config hashes above.
   Review policy against actual source adoption, protected handles and the
   original GPU-host confined route. Record the dated Builder provenance line.
2. On the receiving host, **only after approving those exact bytes**, create the
   absent activation receipt. This is deployment control, not a new per-GPU or
   per-experiment ratification requirement:

```bash
/localhome/local-rohing/v2/venv/bin/python -B - <<'PY'
import sys
from pathlib import Path
base = Path('/localhome/local-rohing/post_reboot_probe_queue_20260919')
sys.path.insert(0, str(base / 'candidate'))
import admission as rules
import daemon
import probe_runtime as runtime
freeze_sha = '27fb65865fb5a313f21575b47b7ebafa180b6e9677543bb4e9e82d8dc0becb0c'
policy_sha = '605c43ba2c87ead62f49c3efcc80a0f80689a1bc9ff20466478839497dfebd1b'
daemon.verify_freeze(base / 'candidate/SOURCE_FREEZE_V3.json', freeze_sha)
rules.require(rules.digest(runtime.read(base / 'inputs/policy.json')) == policy_sha, 'explicit_review_rebind_if_policy_changed')
runtime.write_once(base / 'inputs/activation.json', dict(
    reviewed=True, runtime_enabled=True,
    route='ORIGINAL_GPU_HOST_TRANSIENT_CGROUP_ONE_SHOT_ONLY',
    source_freeze_sha256=freeze_sha, policy_sha256=policy_sha,
    expires_unix=1790791170))
PY
```

3. Start the foreground candidate through the original permitted receiving-host
   route, not as a VM service-management workaround:

```bash
bash /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate/ACTIVATE_FOREGROUND.sh
```

That file contains the exact `python -B daemon.py --run` argv, both enrollment
snapshots, registry, policy, current seal, activation and durable state paths.
It invokes the real one-shot dispatcher only after serialized admission. Any
actual denial is terminal. No activation receipt or daemon was created here.

**Boot: BLOCKED_UNINSTALLED. Credential bootstrap: UNVERIFIED.** No supported
secure automatic provisioning was established; no reboot-safe guarantee from
templates or inherited shell credentials. No service-management bypass, native
changes, collector/enrollment duplication, parent publication, commit or push.
