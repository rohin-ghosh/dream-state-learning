# Independent neutral-runner review — 2026-09-12

Scope: read-only review of `organism_v6/run_reasoning_neutral.py`, `tests/test_run_reasoning_neutral.py`, and supporting `organism_v6/reasoning_neutral_probe.py`. Inspected shared backend/gym/loop code only as dependencies. Main owns all patches. No repository edits, Git commands, network, GPU access, model loading, or live-job actions. Review began 08:06:35 UTC; findings completed around 08:12 UTC, within the 15-minute bound.

## Disposition

Two high-priority cleanup defects and two medium-priority evidence/comparability gaps. Fix the cleanup defects before relying on this wrapper to release a reserved GPU on failure. This is a bounded implementation review, not approval of source origin, panel history, clean lineage, GPU execution, or scientific claims. No action was taken on W0/B0.

### P1 — Timeout/constructor failure can leave engine descendants alive

Locations: `organism_v6/run_reasoning_neutral.py:111`, `:112`, `:140`, `:157`.

The backend constructor executes before the worker's `try/finally`. If initialization starts an engine and then raises, `close_backend` is never called. Independently, `subprocess.run(timeout=...)` kills/waits for its immediate worker process, not the worker's descendants. There is no dedicated session/process-group cleanup in the controller. A killed worker cannot execute its backend cleanup. `PAIR_FAILED.json` records failure but does not establish resource release. KeyboardInterrupt also misses the controller's `except Exception` failure-record path.

CPU evidence:
- A Python worker spawned a sleeping Python child, then exceeded a 0.7-second `subprocess.run` timeout. The child survived the killed worker. The reproduction explicitly killed only that created child afterward.
- Mocking `VLLMBackend` to raise during construction and invoking actual `run_condition` produced `close_backend.called == False`.
- Existing timeout test mocks `subprocess.run` to throw and checks the failure marker; it does not test descendant reclamation.

Smallest repair: launch each worker in its own session and retain the actual process handle/group ID; on timeout, nonzero exit, or interruption, terminate then bounded-wait/kill that owned group and verify cleanup before any next condition. Use controller `finally` cleanup, preserving the original error and recording cleanup outcome. Cover constructor failure with cleanup of owned descendants even when no completed backend object exists. Moving the assignment into `try` alone is insufficient if the constructor never returns an object. Do not use broad system-wide process matching or touch other reservations. A process group handles ordinary inherited descendants; if the actual engine creates new sessions, use explicitly tracked descendants or an equivalent owned containment mechanism.

Regression: CPU-only worker that spawns a child then hangs/raises; assert no live owned child remains, no second condition runs, no DONE marker exists, and the failure artifact records cleanup success/failure. Test interrupt cleanup too.

### P1 — Shared cleanup helper interprets failed GPU query as successful release

Locations: `organism_v6/run_reasoning_neutral.py:115`; dependency `organism_v6/model_backend.py:83`–`:91`, used by `close_backend`.

`wait_gpu_free` discards the query return code and evaluates `int(out.strip() or "0")`. A failed `nvidia-smi` command with empty stdout is therefore accepted as zero memory. `close_backend` may consequently return True without escalation, allowing WORKER_DONE and the next condition although release has not been established. This is a pre-existing shared helper defect newly relied upon by the wrapper, not a newly introduced line in the neutral runner.

CPU evidence: mocked query response `{returncode: 1, stdout: '', stderr: 'GPU lookup failed'}` caused actual `wait_gpu_free(timeout_s=3)` to return True. No `nvidia-smi` executable was run. The reproduction environment deliberately hid CUDA devices; the same mocked failure also applies to a nonempty selector when a real query fails.

Inherited-environment connection: workers inherit `CUDA_VISIBLE_DEVICES` without validating or recording a reserved device. The helper defaults an absent value to `0`, takes only the first comma-separated entry, and accepts an empty selector through the empty-output bug. Caller-owned reservation remains the documented policy, but these behaviors do not verify that the release check corresponds to that reservation.

Smallest repair: require successful query status and nonempty, well-formed measurements for the explicitly selected device; query failure means unknown/not released, never zero. Record the selected device identifier and cleanup status. Reject absent/empty/ambiguous device selection before loading for this one-GPU wrapper, or require an explicit equivalent reservation binding. Do not infer authorization to use GPU 0. Main can fix the shared helper or add a fail-closed wrapper-specific check without changing unrelated runner defaults.

Regression: mock nonzero/empty/malformed output, missing/empty/multiple selectors, and successful numeric output. Failed/unknown release must block worker completion and the next arm. No actual GPU calls are needed.

### P2 — Pair finalization does not revalidate both arms or manifest-listed artifacts

Locations: `organism_v6/run_reasoning_neutral.py:144`–`:155`; helper artifact manifest construction at the end of `run_probe`.

The controller checks each arm's `results.json` and `manifest.json` only immediately after that worker exits. Final `read_spec` rechecks input files, not earlier worker artifacts. It also never verifies the hashes *inside* each manifest, so generation traces, episode ledgers, configuration, and source-check bytes are not verified by the controller. A matching manifest-file digest alone does not establish that its listed files still match.

CPU evidence: using the existing mocked-worker fixture, the second worker changed the first worker's results after the first check. `run_pair` wrote PAIR_DONE while `digest(off/results.json) != workers['off']['results_sha256']`. This is a controller-validation reproduction with transparently synthetic files, not a GPU or actual-subprocess claim. Production helper chmod is an accidental-write guard, not protection against same-owner writers; it does not substitute for validation. The fixture's empty manifests also mean the positive pair test currently cannot catch missing manifest verification.

Smallest repair: immediately before PAIR_DONE, re-read/verify both completion receipts against the originally collected receipts; verify their result/manifest digests and every required manifest-listed artifact. Reject malformed manifests, missing required artifacts, unsafe/escaping relative paths, and unexpected failure evidence. Include the worker receipt file digests in final custody. This closes the demonstrated pre-finalization gap; it is not a claim of adversarial filesystem immutability after finalization.

Regression: alter an earlier arm's result, generation trace, configuration, or receipt during the later arm; assert finalization rejects. Keep an actual-helper positive fixture with nonempty valid manifests rather than dummy `{}` manifests alone.

### P2 — ON/OFF can use different bootstrap/code without pair rejection

Locations: `organism_v6/run_reasoning_neutral.py:130`–`:142`, `:153`; `organism_v6/reasoning_neutral_probe.py:211`–`:232`; `organism_v6/reasoning_gym_gym.py:99`.

Model/adapter inventories and families bytes are pinned, but the bootstrap text is loaded from an additional repository file that is absent from the spec. Each helper records its own birth prompt and code hashes and checks its own code stability; the controller never compares those shared inputs across arms or against a prospective pair baseline. A bootstrap or implementation edit between workers therefore permits an adapter ON/OFF comparison confounded by another intervention. The wrapper hash in PAIR_STARTED is a controller snapshot, not a checked worker-source binding.

CPU evidence: executed the actual helper for both arms using synthetic CPU backends and mocked worker transport/PIDs. Each gym had a different synthetic birth prompt. Both helper runs completed and the controller emitted PAIR_DONE; their recorded `birth_prompt` values differed. No repository bootstrap file was modified. This tests the missing pair consistency check, not real fresh-process execution.

Inherited environment is also relevant here: `-m organism_v6.run_reasoning_neutral` inherits cwd and PYTHONPATH; no trusted source directory or explicit worker-source digest check is supplied. `VLLM_WORKER_MULTIPROC_METHOD` is inherited because the backend uses `setdefault`, so an inherited `fork` is not overridden to `spawn`. This does not itself prove parent-text contamination or negate the fresh top-level Python process, but it leaves runtime/import configuration outside the recorded comparison contract.

Smallest repair: snapshot/hash the bootstrap and relevant implementation files before spawning, bind that expected inventory into worker checks/receipts, and compare the arms' shared configuration, birth prompt, package version, and code inventory, allowing only the intended adapter/source-identity/output-path differences. Launch from the intended repo/package root with a deliberate import environment; explicitly set/record the selected worker multiprocessing policy and relevant GPU/runtime settings. Preserve needed environment settings intentionally rather than indiscriminately stripping everything; never serialize credentials or the entire environment into evidence. This is evidence custody around the existing evaluator, not an evaluator redesign.

Regression: changed bootstrap or shared code between arms, alternate import root, and conflicting inherited multiprocessing setting; either reject or bind and enforce the intended value before model initialization.

## Checks that look sound / limits of findings

- Normal pair flow starts separate Python invocations sequentially. OFF explicitly supplies `adapter_path=None` and an empty adapter inventory; ON uses the pinned adapter. Backend identity checks enforce adapter presence/path and config/weight hashes. The subset comparison in `run_probe` is not an empty-inventory bypass: `_identity_status` requires the expected config plus exactly one adapter weight entry for ON.
- `read_spec` binds exact spec bytes, complete local model/adapter inventories, and families bytes; unknown fields fail closed. Output/protected path overlap is checked with resolved paths. Leaf file symlinks are allowed but their target bytes are hashed; that alone is not a demonstrated hash bypass or a reason to reject normal local model snapshots.
- Parent absence is supported by the actual call path: no parent/history spec field, fresh driver per episode, new evaluation ledger, `recall()` always empty, and the explicit bootstrap/current-episode flow. No concrete parent-message injection was found. This does not authenticate model training ancestry or base origin, which the modules correctly disclaim.
- Held-out IDs, explicit seeds/budgets, evaluation-only labels, and refusal to reuse output directories are present. Panel-selection history remains caller-declared rather than independently proven; that is documented, not silently treated as clean custody here.
- No GPU execution, driver-release behavior on real hardware, actual vLLM descendant topology, or external source-origin claims were validated.

## Commands and results

1. Read-only `sed`, `nl`, `rg`, `find`, `sha256sum`, and `date -u` inspection. No scoped descendant AGENTS.md files were found.
2. Initial `python -B -m unittest ...` attempt could not start: `python: command not found`. Corrected to the installed `python3` and the tests' required import path.
3. Successful command:

   `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=tests:. python3 -B -m unittest test_run_reasoning_neutral test_reasoning_neutral_probe -v > /tmp/astra_neutral_review_tests.log 2>&1`

   **33 tests passed in 0.887 seconds.** No GPU backend was instantiated.
4. CPU-only `python3 -B -` heredoc reproductions with the same environment: stdlib worker/child timeout and explicit cleanup of that created child; mocked GPU-query failure; mocked constructor failure; existing synthetic worker fixture with first-arm mutation. Outputs: `/tmp/astra_neutral_review_reproductions.log`.
5. Actual `run_probe` twice with `FixtureGym`/`FixtureBackend`, different synthetic bootstraps, and mocked worker transport/PIDs. Output: `/tmp/astra_neutral_review_pair_inputs.log`.

Observed reproduction results:

```text
TIMEOUT: child survives killed worker: True (specific created PID logged)
GPU QUERY: returncode=1, empty stdout => wait_gpu_free: True
CONSTRUCTOR: cleanup called: False
CUSTODY: first arm changed during second; PAIR_DONE: True
CUSTODY: first arm still matches bound hash: False
PAIR_DONE with mismatched bootstrap: True
Recorded bootstrap equal: False
```

## Reviewed snapshots / ownership

SHA256 snapshots at 08:10–08:11 UTC:

```text
2c2125ec144098f7ea6fc208a731ce44482c0ea058f8e6f4c6452226b8d532c8  organism_v6/run_reasoning_neutral.py
9a7d931c2c44fb3c2a3820c8698c813823865449f3795178a34c84239ca7562e  tests/test_run_reasoning_neutral.py
28431b85d8df5c348b484476e7ad921f2c2e5d795ee203b8e2cc0498c03c5607  organism_v6/reasoning_neutral_probe.py
68d5aabcf725efbc45f52ba6f4e0ac03a32a134f6aa8699003e054338c53878e  organism_v6/model_backend.py
```

Repository files changed by this review: **none**. Review/log artifacts only under `/tmp`. Main retains patch ownership; this review does not reopen the completed selection-integration assignment. Findings are frozen for main review against the snapshots above.
