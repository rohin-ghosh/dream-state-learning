# C2 epoch4 — sealed offline candidate, NOT dispatch-ready

Final selected bundle: `prepared_epoch4_v5/C2/epoch4/`.
Earlier v1/v2 are interrupted/failed builds; v3/v4 are superseded candidates,
retained unchanged. Never combine their tools, pins, authority or proof with v5.

- Source manifest: `prepared_epoch4_v5/C2/epoch4/EPOCH4_SOURCE.json`.
  SHA256 `f51ad85c16dbfc4f683baeee7147aecc9730ea993a9ef194dee6037555edac01`.
- Archive: `prepared_epoch4_v5/C2_EPOCH4_OFFLINE_CANDIDATE.tar.gz`.
  SHA256 `79b5d29bd6bc44e3e11ec5a44cb44f087c55f989a28dd67ae702452753cb13eb`.
- Main staging inputs, full exact before/after hashes and commands:
  `EPOCH4_MAIN_STAGE.json`; final validation: `EPOCH4_HANDOFF_COMPLETE.json`.
- **256 tests pass**: 36 source/retention/receiving, 128 frontier/reference,
  75 prefix/admission, 17 bounded-preflight/generated-receiver tests.
  Exact logs/JSON are in `prepared_epoch4_v5/C2/epoch4/cpu/`.
  `EPOCH4_SOURCE_CPU_FINAL.json` validates the sealed bundle, not a real checkpoint.

## Source and authority

186 Python files; exactly five epoch3 deltas: reader, shared proof helper,
C2 authority helper, C2 retention runtime, and the existing guard's final native
entry seam. Original r188 confinement, native driver, journal, bridge and history
bytes are unchanged from epoch3. Old epoch2/epoch3 remain unchanged and pinned.
R227 rows, saved state, deadlines, writer lock and source-adoption order remain.

The one shared ABI is Kuhn v4 `scan(..., prefix_proof=..., prefix_admission=...)`.
Reader/helper bytes match Kuhn's `consumer_context_v4/TEST_RECEIPT_attempt1.json`.
No pair-only `NamespaceAdmission` implementation is in candidate runtime source.

Main explicitly approved ONLY bounded derivation of final B guard/admission
clause from reviewed pinned authority. C2 transports the mode through original
guard -> allocation -> passed source CPU -> exact Main authority. The receiving
CPU copy adds the exact deterministic clause; allocation/guard pin those bytes
before tail scan. Native re-derives/compares after original fresh admission.
No token-selected mode, new paths, arbitrary proof, namespace list or loosened
allocation fields are accepted. `copy_raw == plan.root` is mandatory; identical
bytes in a cloned journal fail object checks. Same-namespace default is unchanged.

**Production proof binds 187 source files:** all 186 Python pins PLUS the
original `context/R153_STARTUP.md` asset, then the separate source-epoch document.
The Main stage manifest supplies `proof_source_pins`; do not pass only Python pins
to the producer. The Python closure/CPU epoch digest still contains 186 Python
files, not an invented 187th module. Source directories and every retained
record/intent/root object retain own-view identity checks; full raw A-to-B and
new tail checks remain mandatory. Same boot and v4's three-second quiet-age
metadata policy are unchanged; positive unit fixtures simulate clock age, while
the CLI quiet-age test actually waits. No live namespace/startup is inferred.

## CPU invocation (Main only after its own immutable staging)

```sh
BUNDLE=/localhome/local-rohing/orch_retention_20260919/C2/epoch4
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$BUNDLE/tools/cpu_check.py" source --bundle "$BUNDLE"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$BUNDLE/tools/source_checks.py" --source "$BUNDLE/source" --manifest "$BUNDLE/EPOCH4_SOURCE.json"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$BUNDLE/tools/frontier_checks.py" --source "$BUNDLE/source" --manifest "$BUNDLE/EPOCH4_SOURCE.json"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$BUNDLE/tools/prefix_checks.py" --source "$BUNDLE/source" --manifest "$BUNDLE/EPOCH4_SOURCE.json"
```

Do not overwrite an existing epoch path. Source producer/probe CLI is
`tools/prefix_cli.py`; C2 admitted CPU probe is `tools/cpu_probe.py` with a pinned
Main-prepared request/guard chain. `tools/receiving_core.py` and
`tools/prefix_preflight.py` are the tested receiving/budget plumbing; they require
the existing original boundary modules and Main's concrete capabilities.
There is no new dispatch CLI. The historical default COMPLETE11502 is unchanged
and still old-wall incompatible. Saved COMPLETE12902 proof is historical, not
current boundary authority; index/hash must always be explicit for real checking.

## Exact operational blockers

1. **C2 owner fence/rebind transport is not implemented.** `MainRoute.preflight`
   is a callback contract, not an executable owner adapter. Nothing here proves
   disabled C2-only registry admission, drained provider/queued publication,
   preserved manifests/cursors/ALL ledgers, authenticated current publisher
   PID/start/UID/boot and service/controller/publication lock ownership, or an
   idle-CPU-only fence. Pair's executable sidecar is not C2 evidence.
   Existing C2 owner is `../post_reboot_c2_p7_20260919/c2_service.py`, preserving
   `C2_SERVICE.lock`, original `private/C2_WAIT_CONTROLLER.lock`, prior STARTED
   ledger ancestry and reserved response cursors. A future C2-only adapter must
   authenticate those actual owners, fence only idle CPU, and explicitly rebind
   only after actual LOADED plus exact new-source adoption/native identity;
   restart the same parent policy without changing live owners here.
2. **No C2 reserved coordinator is packaged or measured.** The preflight budget
   caps subprocess timeout and refuses absent static evidence, but callbacks and
   original observer/bridge/parent/guard/checkpoint/commit work need an actual
   Main route and whole-path measurement. Old native must not be stopped merely
   because these tests pass. No full-prefix fallback after stopping is allowed.
3. **New production epoch needs its OWN authenticated proof and Main authority.**
   Main's observer prehash (24.205GB/43.37s outside stop), 3.243s full live scan,
   and two native `/proc/root` metadata comparisons concern a distinct 185-file
   observer. They are useful performance/object evidence, not this 186-file
   runtime or new confined startup. The fast scan preserved pending REQUEST and
   RESPONSE, so it was NOT an eligible COMPLETE+LEARN handoff. Do not reuse that
   proof. Exact local receipt paths/hashes are in `EPOCH4_MAIN_STAGE.json`.
4. Original `gpu.r188_node5_confinement`, original allocation restrictions,
   fresh privileged admission, actual own-view object checks, source checks,
   historical wall receipt at bound1789927200, Main review and a fully costed
   **30-second total reservation including commit margin** remain mandatory.
   Host4026531832/native4026536303 mismatch is allowed only through the explicit
   admitted mode; host success is never startup proof. Peer ABI handoff files
   are coordination requests, not inferred acknowledgements.

No remote command, staging, signal, restart, namespace entry, parent publication,
registry/manifest edit, GPU call or git commit/push occurred in this task.
This handoff completes the offline source candidate, not operational activation.
