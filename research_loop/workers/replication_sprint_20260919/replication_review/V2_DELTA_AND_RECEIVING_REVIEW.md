# V2 exact-byte review and actual receiving failure

**Cut: September 19, 2026, 13:51 UTC. No model/GPU dispatch readiness.**
Only this review directory was written. No receiving commands, claims,
services, signals, installs, model calls, commits or pushes were performed.

## Exact reviewed identity

| Item | SHA-256 / identity |
| --- | --- |
| `CPU_CUSTODY_SOURCE_FREEZE_V2.json` | `050587019d9f0a53e3c52ea6ac1af61635db20683ba40ac69809c47e90b099df` |
| Scientific diagnostic | `4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95` |
| Separate CPU execution incarnation | `d0f368fbcb0ac74ba908a008d7b4daac0bf3f3cd19d5a3fc171902e7419adaad` |
| New CPU block | `a465f7195077b4820d36e81d257ca36c30db991793467f7805430ff3090725e3` |
| `execution.py` | `818ef75d1cc111b5d8ddf2e5871633ee8c25b305c7b82c88c0f48145b3689f9d` |
| `sealed_runner.py` | `aecd3aa3b95722ef325dbf1d48eb03e174fd95540aebee13c3b8f7ddf5d76ae0` |
| `prepare_executable.py` | `3d687a248df0638f6c8d4b649d5a171632cd81d0d8366119a322dd03883ba29c` |
| `dispatch_sampling.py` | `89a90fa4ed6be41cbee5f0f4630e8d259ffc7a52a4fadacf7bab680c86ee0732` |
| `release_failed_claims.py` | `88783fdc342324a035d11eff47086c2689fa8d19c61d27a59241f75cbd89c239` |
| `report_sampling.py` | `e0fdc8d6c49047901ac1122745a23bbd18bbe40f4894e72cab3204e6d0329fcd` |

`CPU_REVIEW_RECEIPT.json` at 13:50:29 UTC records **77 passing offline tests**:
66 candidate tests plus 11 independent checks. Frozen source, inputs and author
test evidence all match; reviewed bytes stayed unchanged during the run. Test
temporary directories were redirected into this review directory. These are
mock/local tests, not substitutes for actual namespace or GPU admission.

## Source deltas: what passes offline

- The extraneous `sentence_transformers` import is removed. Original dependency
  versions, source manifest, scorer, extraction, decoder and tokenizer checks
  remain. Original player/judge functions still pass the independent synthetic
  model-facing equivalence tests.
- Player unit construction includes `InaccessiblePaths` for `view/judge`,
  `view/epoch`, and `view/assets`. The cannot-open predicate and original three
  private-file checks are retained. An independent real-filesystem regression
  confirms readable zero-byte and nonempty synthetic files both fail denial.
- The CPU repair has different root, job and unit identities, with unchanged
  scientific identity. Registry validation rejects relabelling it as science;
  command construction, dispatcher and role runner disallow model mode.
- Claim disposition checks the original lock/namespace, exact six unit commands,
  identities and corresponding STARTED PIDs, terminal states, absent processes,
  empty cgroups, original admission and exact two owned claim hashes. It archives
  claims and rechecks failed-root references; it does not clear attempt guards.
- Present incomplete RESULT receipts no longer abort accounting. The independent
  128/1024-token fixture returns all six source/seed rows, preserves the partial
  hash/status/tokens, leaves the full-budget token count unknown, and excludes
  the partial cell from completed-cell rates. Wrong scene/seed/epoch remains an
  integrity failure. This closes the earlier reporting defect for these bytes.

## Actual receiving evidence outranks those tests

`operations/SAMPLING_CUSTODY_V2_PREPARED.json` binds the same freeze and distinct
CPU registry. `operations/SAMPLING_CUSTODY_V2_LOGS.txt` independently shows all
three player processes fail the unchanged private-path predicate. Main reports
three successful judge proofs and, for base job `aa9a113...`, config SHA-256
`2f5f431404cdd8044d537da044dbe9696bd13899f1eb1b71dae604286e047825`, UID1352:

- `view/epoch/JUDGE_EPOCH.json`: denial false.
- `view/epoch/PRIMARY_PANELS.private.json`: denial false.
- `view/judge/REFERENCE_PANELS.private.json`: denial false.
- Common host paths, including `/proc/1/root`: denied.

The full exported per-path JSON and timestamps have not yet been independently
joined in this sidecar. Main's reported values are not represented as a second
receiving inspection. No proof success is inferred from empty logs.

## Root-cause boundary and minimal V3 requirements

The concrete layout defect is visible in frozen `prepare_executable.py`:
both roles bind the entire host `view` writable, and the judge mounts three
private files onto targets beneath that same shared ancestor. The earlier host
metadata showed exactly those targets as root-owned, readable empty files. V2
kept this layout and added directory masks; the receiving player checks show
that those masks did not enforce the required cannot-open boundary.

This establishes the failed shared-storage isolation, **not** a proven private
payload disclosure or a complete explanation of systemd's mount ordering.
The exited processes' mount tables and effective unit properties have not been
provided; do not fabricate that missing evidence or blame the denial predicate.

For Singer's V3 delta, independently check:

1. Judge-private bind targets and their backing directories are outside every
   shared writable tree. No broader shared parent, symlink or recursive bind may
   reintroduce them. Player roots must not acquire judge mount placeholders.
2. Preserve the old three private-path checks and add the new canonical private
   targets to player denial checks. Keep original host-private/canary/proc
   checks and the one-assigned/seven-denied device test unchanged.
3. Preserve the original judge's expected panel/asset paths through role-local
   mapping rather than changing scoring/extraction. Only intended request/result
   queues and public readiness/output transport are shared. Verify both roles
   still address the same queue and player completion signal.
4. The actual proof must capture effective mount information and individual
   open outcomes without private contents. Join each player check to its config,
   source seal and execution identity, and establish it occurs after the paired
   judge's private mounts exist. A player that ran before target creation is
   not evidence of post-mount isolation.
5. Preserve V1 and V2 failures, source seals and no-retry history. A V3 CPU
   incarnation must be new, linked to both failed attempts and incapable of
   model execution. Claim reconciliation remains Main's ownership-checked work,
   not an automatic retry or permission to dispatch science.

These are concrete integration checks, not a new human-ratification gate.
The repair remains nonmaterial only if the original scientific/visibility
contracts stay intact. No successful actual custody proof has been reviewed.

## Additional concrete V2 configuration mismatch

The exact frozen `execution.command()` sets `RootDirectory=rootfs_player`, but
spells `InaccessiblePaths` as plain absolute `view/judge`, `view/epoch`, and
`view/assets` paths, without a `+` prefix. Upstream systemd's primary
`systemd.exec.xml` specifies that these restrictions are host-root-relative by
default; `+` selects the unit's configured root. Bind-mount destinations, in
contrast, are already relative to `RootDirectory`. The V2 strings therefore do
not express masks on the same root-relative locations as the bind destinations.

Primary specification inspected September 19:
`https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.exec.xml`,
`InaccessiblePaths`/`ReadWritePaths` section and `BindPaths` section (also checked
against upstream main). The receiving version has not been supplied. This is a
source/configuration diagnosis consistent with the receiving failure, not a
substitute for the actual receiving systemd version, effective properties or
exited namespace mount tables. Do not describe the precise mount ordering as
measured. The CPU test only checked path substrings in the generated option;
it did not check root-relative semantics or actual isolation.

V3 should still implement Main's stronger structural repair, not retry V2 with
one prefix edited: private targets outside shared writable storage, retained
denial tests, and an explicit new CPU execution identity. Any retained path
masks must address the correct unit-root paths. Only actual post-mount open
checks establish success. The observed exposure is of readable paths; private
caption payload exposure has not been demonstrated.

## Exact remaining handoff at 13:55 UTC

No V3 source/freeze or `operations/SAMPLING_CUSTODY_V2_PROOFS.json` is present
in the shared checkout at this cut. V2 source review and failure triage are
complete; V3 byte-level and actual receiving checks cannot yet be claimed.
Main can publish the failed CPU proof honestly without waiting for another
review or human approval. Preparation continues with Singer/Main; this
reviewer has neither replayed the receiving attempt nor changed any candidate.
