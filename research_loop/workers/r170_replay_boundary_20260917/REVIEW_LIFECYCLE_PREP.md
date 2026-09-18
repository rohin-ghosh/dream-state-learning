# Independent R170 lifecycle preparation sidecar

September 17, 2026. Distinct from the already-consumed source/recovery reviews.

## Verdict and exact scope

**APPROVED FOR METADATA OBSERVATION / SELECTION FINALIZATION AND CPU AUTHORITY
COMPOSITION ONLY. NOT LIFECYCLE ADMISSION OR SIGNAL GO.**

The existing observer may continue unchanged. Its scope is one bounded,
create-only observation attempt, followed by at most one isolated selection
finalizer; no GO binding, source guard patch, checkpoint payload load, model,
learner signal, retirement, supervisor dispatch or replay. LIFECYCLE_READY is
appropriate for original source/topology preparation. The composed CPU receipt
correctly describes its inherited labels and non-admission limits.

There is one concrete result-handling gap: a successful finalizer followed by
a moved head still returns successfully. Consequently **returncode 0 is not
readiness**. A false same_boundary_after must be disposed as expired metadata,
never passed into GO/handoff. This restriction preserves the narrow metadata
approval without stopping or modifying the current observer. No actual
selection is approved for admission by this report.

## Frozen bytes reviewed

| Artifact | SHA256 |
| --- | --- |
| BOUNDARY_FREEZE.py | `34d8a82e6dd5cf15493b2a838baa66806dcf25b96cdbe91586c83ce924d489c0` |
| test_boundary_freeze.py | `c2fe6c26a8ab1584aa78a1ec2337f15363aa125287e83a22311910c2ab6a77f3` |
| LIFECYCLE_READY.py | `4ecd0343921c6380a072b480b3d365859d1080d58c5cc7a68a2dce615ba129e6` |
| test_lifecycle_ready.py | `115eb5b68f71518cbee1eb8ab20b6dc3350f82ccf2a1cb857633e61dece51a20` |
| CPU_LIFECYCLE_AUTHORITY.json | `ef38100cf80a6e64299fb012e348ceab80689726338332289860792273f7e8fd` |
| LIFECYCLE_PREPARATION_RECEIPT.json | `4eb7d8dbe1028858e0f32e4e7c0e90c7317df8b327bb121c9cdfb6e219d84d68` |
| test_lifecycle_prep_review.py | `1c4971429dcba67309b9f7bec714680f5da072a0c4327e8b3d55dc34faa0f897` |

Consumed REVIEW_ASSEMBLY_V2.md remains exactly
`af9d60e96a035b5363e3eaf7c179e010a9e44b4d58eb83b1692bf2d3b19510ce`.
No consumed review, approval, receipt, original source, author code or running
observer was changed. Reviewer writes are this new report and its separate tests.

## Actual metadata observations

The preparation receipt's stdout parses as the original source/guard validation
plus two matching topology observations, at **16:15:53 UTC** (09:15:53 PDT):
native1266769, timer1266768, supervisor1266757, no current completed head, zero
signals/model calls, source_ready_only=true and saved_state_handoff_authorized=false.
Transport returncode is zero, stderr empty. This is preparation, not ownership.

With the user's subsequent explicit wrapper-only metadata authorization, the
reviewer made two read-only checks through gpu/ovx2_ssh.sh. No once script was
rerun and no process was stopped, restarted or signalled.

- **16:26:22 UTC:** current journal head is UPDATE **5380**, path
  `/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1/stream/records/00000000000000005380.json`,
  file SHA256 `d3d92d3cef7f4935d2d9f999782c02790bd39894fef8894a02c0591b456324cb`.
  Head path was unchanged across that observation. It is not a SLEEP_COMPLETE
  opportunity; no current source cycle or prospective target was inferred.
- Native1266769/start28048014 was R. Launch handle503582/start36825558 was S.
  SELECTION_OBSERVER_STARTED.json identifies the actual Python worker503583;
  marker SHA256 is `9e349de8269185ed1f5abdb0b2f700c823ab2a3b8002ceb3fc2702c25ad03838`.
- **16:27:01 UTC:** worker503583/start36825558 was S, parent/group503582,
  argv exactly the receiving interpreter, `-I -B`, deployed BOUNDARY_FREEZE.py,
  `--watch 5400`. Its deployed source SHA matches the table. PID503582 is the
  launch handle, not the PID written by the Python observer itself.
- At the 16:26:22 snapshot, SELECTION_OBSERVER_RESULT.json,
  SELECTION_FREEZE_RECEIPT.json, MAIN_GO.json, DRIVER_BINDING.json and
  PROPOSED_GUARD.json were absent. This is a timestamped observation, not an
  assertion that those files remain absent indefinitely.

## What the observer/finalizer actually guarantees

BOUNDARY_FREEZE.opportunity (`BOUNDARY_FREEZE.py:77`) checks the current head
through the pinned original saved helper, the old plan's readout revision,
the timer PID as resident process group, and equality of a second head read.
The original helpers (`gpu/orch_r131_saved_boundary_handoff.py:39` and `:64`)
read files/proc only. Their source SHA e86dae... equals the actual R175 source
manifest pin. An existing readout COMPLETE file can make readout_started true
without a current readout process check; this remains an opportunity hint,
not proof of readout completion or saved-state custody.

The watcher hashes actual record bytes and the same-cycle COMMIT, not the
record's internal digest. It uses a single separate receiving interpreter with
`-I -B`, exact script/JSON arguments, empty CUDA visibility, offline flags, a
small explicit environment and 120-second subprocess timeout. This avoids
reusing the observer's resident-native import namespace during assembly.
The starting marker is create-only; repeated watch invocation refuses before
another finalizer can launch. Subprocess command/transport tests use mocks.

`freeze` (`BOUNDARY_FREEZE.py:45`) requires canonical bounded input paths,
positive cycle, exact life/record/COMMIT relation and unchanged byte references.
It loads pinned ASSEMBLY_V2 via the exact receiving approval and scaffold,
then calls only unchanged finalize_selection_bundle with main_go_scope=None.
The returned cycle must match, target must be source+1, and the extra receipt
is metadata only. The original finalizer separately checks the SLEEP_COMPLETE
and matching COMMIT/state and own-row selection; no checkpoint tensor loading
or learner code is invoked. No bind_main_go entry is called.

Watch duration is bounded by 5400 seconds and **hard wall minus 1800 seconds**,
so the unchanged 18:00 UTC wall caps observation at **17:30 UTC**, earlier than
the original handoff's 17:45 UTC cutoff. Timeout/no-opportunity is not success
or permission to extend the wall.

## Concrete gap and minimal disposition

**Moved-head success result — BOUNDARY_FREEZE.py:118.** The watcher writes
same_boundary_after but only requires completed.returncode == 0. A mocked
finalizer returning zero with the head subsequently changed to UPDATE returns
normally with same_boundary_after=false. The separate freeze entry also does
not prove present-head/readout status; immutable historical record/COMMIT bytes
can remain valid after the opportunity has passed. Thus successful selection
serialization is not successful window capture.

Independent desired-behavior regression is an explicit strict xfail, not a
pass. No learner safety bypass was reproduced: the unchanged R170 saved_evidence
comparison and original handoff still enforce the selected cycle/state/path
before pause/retirement. Nevertheless using watcher exit status alone could
waste the one selection and lead Main toward an already-expired window.

**Minimal disposition for the already-running pinned observer:** require
same_boundary_after is True when consuming its result, verify the actual bound
selection/freezing receipts, and reobserve the exact selected current boundary
before proceeding. False/missing/uncertain means expired or failed: preserve
artifacts, no GO, no retry/rebind/cleanup-to-reuse. Even true is not ownership;
the original stage/handoff checks remain mandatory. No live source edit or
observer restart is needed to enforce this consumer restriction. A future
unconsumed revision could raise after recording false, but is not reviewed here.

If subprocess timeout/transport interruption occurs, the watcher preserves the
starting latch but may have no final result; the isolated child may have written
partial selection artifacts. Tests confirm there is no second invocation.
Treat this as uncertain, never rerun --assemble or a once script to find out.

## CPU authority composition verified, not promoted to admission

CPU_LIFECYCLE_AUTHORITY.json has the correct V2 entrypoint hash, API hash and
literal FAMILY PATCH_SHA/HELPER_SHA compatibility fields. Private __file__ in
OPERATOR_RECOVERY_V2.adapter_namespace (`OPERATOR_RECOVERY_V2.py:69`) is the
deployed V2 entrypoint, so using the V1/FAMILY hash for operator_sha256 would
fail unchanged FAMILY.stage (`gpu/orch_r144_node3_target_handoff.py:280`).

The authority explicitly calls patch/helper fields inherited labels, not an
assertion that the R144 patch was executed. This is accurate: the private
verify_source override (`OPERATOR.py:75`, installed by family_namespace)
checks the actual three R168 helpers and exact guard entry delta; it does not
invoke the old patch utility. No request to apply that utility is justified.

Independently verified all **13 referenced artifact hashes** in the composition:
actual R175, receiving binding, consumed source review, recovery review,
source-scaffold receipt, topology preparation, inherited tests, current local
CPU log/XML and four preparation source/test refs. All six dependency pins
match their exact source files, using operator5 for BOUNDARY_API. Its author
log actually reports **203 passed, 4 documented xfails, 86 subtests passed**.
Those historical/setup xfails remain limitations, not converted passes.

The composition correctly retains learner_handoff_authorized=false,
main_go_created=false and zero signals/model calls. Its absolute author-host
paths are provenance references, not automatically receiving-host paths.
Unchanged stage tests the compatibility scalars and binds the whole CPU file;
it does not recursively validate these provenance references on the worker.
That verification is established here for these exact composed bytes, not for
arbitrary future receipts with matching scalar labels.

## Practical next gate, only when an actual selection exists

Keep deterministic preparation complete while the observer runs. A future
admission decision must bind the actual SELECTION_FREEZE_RECEIPT, observer
result, SELECTION/SELECTION_BUNDLE byte refs, source cycle/state/path, proposed
plan/runtime, unchanged hard wall and an explicit exact Main scope. Call the
unchanged bind_main_go only through ASSEMBLY_V2's returned namespace; raw V1
would restore historical-only CPU validation. This report supplies no Main GO.

Then retain original FAMILY.stage fresh receiving validation/driver._admit and
historical selected-boundary check, followed by handoff's actual same-cycle
readout/quiescence, V2 death recovery, pidfds, full checkpoint custody, and strict
post-retirement admission. If the head advances, refuse rather than choosing an
older, predicted or catch-up cycle. Do not bypass these steps to fit a window.
No successful deployed finalizer or selected-bound lifecycle admission has yet
been observed by this review, and no replay timing/scientific claim is made.

## Independent CPU result

**28 passed, 1 strict expected failure in 0.18 seconds.** The expected failure
is solely the moved-head success behavior above. This combines the 21 author
preparation tests with independent mocked command/namespace, no-GO, byte-drift,
single-use, timeout/failure and exact composition-reference checks.

```bash
TMPDIR=/tmp CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/r136-pytest-support python3 -B -m pytest -p no:cacheprovider \
  research_loop/workers/r170_replay_boundary_20260917/test_boundary_freeze.py \
  research_loop/workers/r170_replay_boundary_20260917/test_lifecycle_ready.py \
  research_loop/workers/r170_replay_boundary_20260917/test_lifecycle_prep_review.py \
  -q -rx --junitxml=/tmp/r170-lifecycle-prep-independent.xml
```

Log `/tmp/r170-lifecycle-prep-independent.log` SHA256:
`79a81991ad34a6dcfab0c48f9c3f777d77155f9192f1a2c4dad4ade237c5620a`.
XML SHA256:
`c3f47291eeeb1abfb64f6d7a298942b7357e6173766a861bb5c90f73bb743501`.
No actual finalizer was invoked by the tests. The only reviewer remote actions
were the two explicitly authorized read-only metadata checks described above.
