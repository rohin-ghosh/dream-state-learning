# W0 stdout/stderr custody repair — 2026-09-12

Delivered approximately 08:24 UTC. Classification: bounded non-material custody repair for future preparations/executions only.

## Terminal state is unchanged

Main reports all 14 W0 stages completed and the raw report emitted ASSAY_INVALID, with oracle BA 0 in all four cells. Main also reports replay-real fails `sealed bytes changed`: among 3,161 files, only in-root `launcher.out` differs (sealed empty, subsequently 6,099 bytes). The empty-file SHA256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Root cause: execute sealed every run file before main printed its returned report to stdout, which the caller had redirected into that same sealed run directory. This is a custody failure independent of the negative assay result. The raw label is not a successfully sealed/replayed pass. **W1 remains blocked.**

No actual W0 run was accessed, modified, repaired, excluded from inventory, resealed or reinterpreted by this task. No remote/network/GPU/Git operations or new execution attempts were performed.

## Exactly what changed

Only the owned existing repository files changed:

- `organism_v6/multikey_writer_gateway_simple.py`: import `stat`, add `assert_output_fds_outside_run(root)`, invoke it from `execute_real`.
- `tests/test_multikey_writer_gateway_simple.py`: import `socket`, add eight CPU regression tests in `OutputCustodyTests`.

The guard runs immediately after the existing explicit `--allow-gpu` gate and run-path check, BEFORE `validate_prepared`, native compilation, snapshot pinning, GPU inventory/idleness calls, tokenizer/model loading, worker launching or any run receipt/marker write.

For each actual process FD 1 and 2:

1. Read `/proc/self/fd/<fd>` and call `os.fstat(fd)`; failures reject execution.
2. Accept kernel `pipe:[inode]` or `socket:[inode]` targets only when the actual descriptor type agrees.
3. Otherwise require an existing absolute destination, resolve it, and reject any path inside the resolved run root. Nested paths and symlink aliases into the root are covered; lexical filename-prefix matches outside the root are not falsely rejected.
4. Require resolved destination device/inode to match the open FD's device/inode. Missing, stale, deleted, unresolvable or mismatched destinations fail closed.
5. Accept verified external regular logs, external FIFOs, actual terminals, and `/dev/null`. Unknown anonymous-inode targets or unknown device types are rejected.
6. For an external regular file with multiple hard links, reject any matching device/inode within the run tree. An external pathname cannot bypass custody by aliasing an in-root evidence file.

The assertion itself writes nothing, launches nothing and changes no descriptor. Failure raises ContractError. Existing CLI exception handling remains unchanged. It does not bypass the explicit GPU flag or the existing no-rescue/no-refit gate.

## Scientific/evidence preservation

No changes to recipes, labels, oracle thresholds, material, masks, step counts, seeds, caps, environment prerequisites, fit/generation/scoring behavior, reducers, seal inventory, seal format, source binding or replay behavior.

In particular, **no exclusion for launcher.out or other logs was added to sealing/replay**. Future caller logs must be siblings/outside the run, as main directed. Existing prepared source bindings remain immutable: this patch is not permission to run a changed source against an old preparation or to reseal terminal artifacts.

AST comparison against byte-preserved pre-edit snapshots confirms the entire source differs only by the stat import, new guard function, and execute guard call. The tests differ only by the socket import and new OutputCustodyTests class. All prior 60 W0 tests are structurally unchanged.

## CPU tests

Command:

`python3 -B -m unittest tests.test_multikey_writer_gateway_simple tests.test_writer_replay_plan -q`

**93 tests passed: 68 W0 tests (60 preserved + 8 new) and all 25 preserved W1 tests.** Final combined run: 13.402 seconds; no skips or warnings.

New regression coverage:

- Actual child-process stdout and stderr separately redirected into an in-root file reject before even read-only manifest validation; all native/runtime/GPU/model/worker/write entrypoints are patched as forbidden and remain uncalled.
- Rejection creates no execution marker or execution seal and does not write into the temporary redirected log in the direct execute test.
- Actual nested/symlinked in-root logs and external hard-link aliases reject.
- Actual sibling stdout/stderr logs and captured pipes pass the custody check and reach only a deliberately intercepted read-only preparation boundary.
- Actual Unix socket pairs, pseudo-terminals and `/dev/null` pass without GPU operations.
- Actual deleted external logs fail closed.
- Unknown/unreadable proc targets, mismatched pipe/socket descriptor types and unavailable/closed FD metadata fail closed.

Test log: `/tmp/astra_w0_log_custody_tests_20260912.log`. Whitespace checks passed. No real scientific run is represented by these tests.

## Exact custody hashes

Previous source SHA256:
`99abab2c78dc06756b0bbbeb86d5717c5baf430af2cbafdab206f4fc8af4cafc`

Previous tests SHA256:
`874ca3984471694724c365d1efc98e04187afb3ddf997a173993eda7d2188f37`

Byte-exact pre-edit copies are preserved at:

- `/tmp/astra_w0_log_custody_before_20260912/source.py`
- `/tmp/astra_w0_log_custody_before_20260912/tests.py`

Repaired source SHA256:
`b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8`

Repaired tests SHA256:
`44e66d283a2c9b27d449dfb099f54f93bec52f518edf4e11e9f235054c24e84c`

W1 files were not edited and retain their exact starting hashes:

- `organism_v6/writer_replay_plan.py`: `20c77d471d2ea9b2542132f7fdb882a16a34755021f07a211506f33cd7887ea5`
- `tests/test_writer_replay_plan.py`: `2490dee7ec8ce7de242865a0ec9f56feac0f46057433ebec30ae583ad2034df6`

## Exact limits

This is a Linux `/proc` preflight. Unavailable FD introspection fails closed; there is no permissive platform fallback. It checks destinations at entry, not subsequent descriptor reassignment or filesystem mutation by other processes. Known pipes/sockets are allowed as requested; their consumers' eventual output destinations cannot be inferred from the local FD. Main must ensure any logger/tee consumer also writes outside the run.

Shell redirection may already create/truncate its target before Python starts; this guard cannot undo that caller-side operation. Existing CLI failure diagnostics still use stderr, so an unsafe caller-owned stderr can receive an error message on rejection. Neither behavior is used here to modify any existing run. The safety property is refusing execution/sealing under an unsafe or unknown output destination, not silently repairing prior caller mutations.
