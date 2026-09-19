# R135/R136 REPO-READER — 2026-09-16

Owner: REPO-READER worker. Scope is a new child on ovx3 physical7 only,
GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b. Protect physical2/6 and every
other lane; no retirement, lease, authorization, shared native or journal edits.
Implementation choices preserve the standing frozen-model/visibility invariants.

## Launch and evidence

Use a committed-HEAD runtime archive, the unchanged R127 seed0 free-distillation
template, frozen Qwen2.5-7B-Instruct, rank8, anchor0.25, 16 new/1 rehearsal,
two segments then free distillation, and the existing separate readout schedule.
Remove resume/extension authorization only from the NEW template, not native.
Stage through `gpu/orch_r133_stage_child.py`; launch once through its existing
continual guard after fresh privileged exclusive admission of physical7.

Existing lease receipt:
`/localhome/local-rohing/orch_r115_grid_pair_20260915/A4/independent_r119_recovery_v2/LEASE_BUDGET.json`
SHA256 `287e36bc9b646401f5382b06c8bda4e71748a5f94d6eb011d436c1ead7b246a5`.
Lease ends 1789617840; requested maximum wall 1789617240. Receipt actually
ends work at **1789596240**, so the derived effective wall is **1789596240**
(minimum of authorized receipt and requested wall). No extension is created.
Raw run, tools and parent artifacts stay off the VM repo root, on node-local
storage (parent API transport may use an off-repo private VM control directory).

## Read-only snapshot contract

Start with three short manually reviewed documents: a public-facing runtime
overview derived from the factual R127 startup; a typed aggregate-only digest
of the published R127 continuity audit; and an omissions/access guide.
This is deliberately NOT all repository results. Do not copy research directories.
Exclude credentials, host information, provider configuration, COORDINATION,
held/FINAL sets, answer keys, raw evaluations and R130 corpus/outputs.
Bind original source hashes, source commit, exact exposed file hashes and a
compact snapshot manifest digest. Every exposed byte is reviewed before release.

The file tool opens actual allowlisted files under the pinned snapshot using
directory-descriptor traversal with no-follow on every component. It rejects
absolute/parent/nested paths, symlinks, special files, unknown names, writes,
changed manifests and changed content. Exact file bytes produce an immutable
R127 workspace-result receipt, delivered by the pilot's actual Tool/environment
inbox path. Separate provenance binds manifest, file hash, source and actual
child RESPONSE hash. No fabricated result, hidden readout or arbitrary shell.

Startup names actual new paths and says the tool is pending until a real
environment receipt announces connection. No CPU executor or file writer is
claimed. Once connected, `repo_read overview.md` (or another allowlisted name)
on its own line requests a read. An explicitly operator-initiated first read is
labelled as such, not misrepresented as a child request. Every child request
is bound to a verified TRAIN response. Parent per Rohin message128: one
asynchronous Astra conversation using the programme helper, actual TRAIN only,
initiative and useful silence, no compulsory recurring thought format.

## Gates and reporting

Before connection: negative path/write/symlink tests, source/manifest tamper
tests, real-file receipt and TRAIN attribution tests. Before GPU: CPU tests,
base/source/lease provenance and dated Builder gate entry. Record staging,
fresh admission, actual launch, actual LOADED and first real read separately;
do not equate process dispatch with successful load or queued with consumed.
No improvement claim follows from launch, file reads or continuity counts.
Matched controls remain necessary for scientific claims.

Initial ETA at 10:08 UTC: tests/snapshot about 10 minutes; first inference
about 15–20 minutes, conditional on committed source and fresh exclusive
admission; the lane may launch truthfully tool-pending while reader gates finish.

## Actual deployment and R137 update (10:19 UTC)

- Runtime: published commit `de1fc4b779e939a1082c54c341bef8a6a6497512`,
  1,848 tracked Python files; archive SHA256
  `78ab356e03e80c9cbfbc630ef413994a4b5a37609e2b06d927e2a76ab72c35a8`.
- Native node CPU167 passed; archived plain-context CPU13 passed with existing
  isolated pytest support on VM. Initial node missing-pytest receipt preserved.
- Exclusive admission at 1789553521.4934273; native launch at
  1789553521.4942205, native PID2287827. Actual LOADED at1789553576.2588634.
- Root: `/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/run1`.
  Live native `source1`/`control1` remain unchanged after launch.
- Main explicitly approved published runtime plus own tested/pinned sidecars
  without waiting for central commit. Sidecars are NOT claimed committed.
- Reader1 performed its actual access.md read, then stopped because its initial
  chain assumption was zero rather than the real journal-manifest digest.
  Non-material reader2 repair uses actual JOURNAL.json genesis and identity.
  Actual-journal and no-duplicate-read regressions pass; all reader1 evidence
  is preserved. Separate `toolsource2`, `broker2`, `file_receipts2`; no native
  edits, restart, reset or replay of the operator connection publication.
- Node reader2/pilot/staging/parent CPU46 passed. Source-pins digest
  `da18586f684c1fcacae0a6960083cadd6c927cc6af2a6d5c19583736e5a4169d`.
  Snapshot manifest remains
  `565dc5676f597e0ad6ef5bbde6dd35612ee9bf2a28846a76b44768c07cc999d2`.
- Operator connection consumption verified at record2; first actual child
  request at RESPONSE record4 produced an access.md receipt in `file_receipts2`.
  Request hash `12cafc817d2d4071ae16425b88ed780ebbd243389208c8224d62faf2ab7ce623`.
  Publication is not yet a verified consumption of that child-requested result.
- R137: exact **SPARSE(3) / free_distillation / source-critical** configuration.
  `minimum_duration_seconds=0`; `parent_reasoning_effort=null` inherits the
  existing provider setting, with no provider configuration/auth change.
  Parent helper/provider CPU17 passed. Prior responsive parent stopped without
  an inflight call; its response-count3 frontier carries into the new sole
  asynchronous Astra parent (PID674405, started1789553931.2364907).
  Config SHA256 `587f165943628c665cdece20450461986b0335e6556d3026a3f86be76a3935a2`.
  Parent raw artifacts are under `/data/home/rohing/courier/orch_r136_repo_reader_20260916_attempt1`,
  verified on a different filesystem from the VM root. Native/tool raw are node-local.
- At1789553954.3846173: three responses, 48 update records, one SLEEP_COMPLETE.
  No capability gain, perfect cadence coverage or matched-parent-control claim.
  Original2/6, other lanes, raw controls and control learning remain untouched.

At10:20 UTC the first child-requested access.md result is also verified consumed:
record64, SHA256 `f358f5bd7d875aa964f0ad8c0f1d7dd3e2c0cd172eccde0385e4fe8066daf8af`,
observed1789553993.7342157. Native2287827, reader2343420 and sole source-critical
parent674405 remain alive; no native FAILED receipt or reader/parent log error.
