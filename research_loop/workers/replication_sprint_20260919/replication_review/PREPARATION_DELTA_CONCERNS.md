# CPU preparation failure: bounded repair review checklist

Main reports that the first actual CPU staging attempt failed at the static
`BACKBONE` mount: `/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_qwen_model_v1`
does not exist. Main reports no GPU/model dispatch or shared-claim creation.
The partial diagnostic root and source stage
`/localhome/local-rohing/post_sampling_source_20260919T1337` are preserved.
These are Main's receiving observations, not an independent live check by this
reviewer. The repair source/seal and primary receiving receipts are pending.

## Necessary properties of the repair

1. Derive required read-only model mounts from the **hash-bound actual primary
   scalar configuration and base-model manifest**. Verify those original hashes
   first. Do not substitute a model, rewrite a manifest, select another adapter,
   widen player access to private judge assets, or silently use a new path merely
   because it exists. Prevalidate all mount sources before creating a new staged
   incarnation where practical.
2. Preserve the entire failed preparation in place, with its source/config hashes
   and exception. A distinct preparation incarnation can repair an unlaunched
   CPU staging failure without pretending a different scientific experiment
   occurred. The scientific epoch, source identities, seeds, panels, and budgets
   remain unchanged.
3. **No-retry identity must survive preparation incarnations.** Fresh stage paths
   must not allow an already attempted diagnostic to be run twice. Verify that
   no prior incarnation contains a launch/model-start/dispatch intent or a
   platform-denial marker before admitting this repair; use a stable logical
   attempt guard across incarnations if multiple preparations are supported.
   A consumed attempted identity cannot be made fresh by changing a path.
4. Keep the original GPU-UUID claims, protected handles, lane mapping, lease,
   rootfs custody, and in-namespace proofs. A failed CPU filesystem preparation
   is not the same as a platform denial; that distinction should be backed by
   receipts rather than inferred from the desired outcome.
5. Add CPU tests for the missing static path/manifest-derived path, source-hash
   mismatch, preserved failed preparation, rejected prior dispatch/denial, and
   unchanged scientific job identity. Freeze and review the actual repaired
   source bytes before Main stages them.

The separately reproduced incomplete-cell reporting defect remains documented
in `FINAL_DELTA_REVIEW.md`; it can be repaired in this same non-scientific delta.
No additional human-approval gate is requested. This reviewer makes no runtime
changes and does not dispatch, publish, signal, or retry a platform request.

## Reviewed repair implementation — 13:39:01 UTC

Preparation source SHA-256:
`0b8ffe6270840da33a0fcbb2d4c0928f364d608eade8198ef4a721e0a6df7919`.
**61 CPU checks pass**: 52 candidate tests and nine independent tests. This
includes negative checks for 14 prior preparation/dispatch/denial/custody/result
markers and rejection of a corrupt base-manifest hash. No actual receiving
staging or proof was performed by the reviewer.

The inspected repair derives the scalar backbone from its pinned manifest,
requires the same model/revision and a snapshot inside the already mounted
Hugging Face cache, and removes the absent hard-coded extra directory. It does
not rewrite the scorer configuration or substitute weights.

The CPU preparation continuation preserves the exact inventoried failed tree by
an archive rename, hashes every small file and symlink target, and writes a
preservation receipt. It then creates a fresh preparation at the same canonical
scientific root. This differs from leaving the tree at the identical path, but
retains the artifacts and scientific identity. It is acceptable as a bounded
unlaunched-preparation repair: `PREPARED`, launch, failure, proof, model-start,
result and own GPU-claim evidence prohibit this path; archived roots cannot
satisfy the dispatcher's canonical registry-root join. It is not a way to retry
a consumed model job or platform denial. The archive destination is never
overwritten and the shared lock covers inspection/archiving/root creation.

**Still pending:** a resealed release and receiving staging/custody evidence.
The 13:34 source freeze remains the old hash `e717180b…` and does not match this
preparation/test delta. The independent accounting fixture still reproduces the
incomplete-cell reporting exception. No further scientific or runtime-policy
change is requested by this review.
