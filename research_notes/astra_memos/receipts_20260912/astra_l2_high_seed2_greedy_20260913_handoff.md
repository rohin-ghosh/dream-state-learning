# Seed2-high native greedy TRAIN/readout — EDITSTOP

2026-09-13. New read-only diagnostic, implementation/CPU fixtures only. No native tokenizer/model/GPU call, deployment, launch, collection, Git or repository edit was performed. Main owns native preparation, fresh allocation and launch. Memory writer remains another worker's task.

## Deliverables and checks

- `/tmp/astra_l2_high_seed2_greedy_20260913.py`: SHA256 `a5f644c6660dc398a330bd51025f1d6c3ee75e7dda8a99310e5f3a91b1dea28f`.
- `/tmp/test_astra_l2_high_seed2_greedy_20260913.py`: SHA256 `575bb83aff05e53dde11998d076a3c1256483f52a02bc1c5361bc3c7b2ee5c6a`.
- This handoff: `/tmp/astra_l2_high_seed2_greedy_20260913_handoff.md`.

`python3 -B -m unittest discover -s /tmp -p test_astra_l2_high_seed2_greedy_20260913.py -v`

**15 tests PASS in0.119s**; CLI `--help` also passes. Tests use exact frozen source APIs with toy data and mocked vLLM/subprocesses: original32-token settings and LoRARequest, fixed32calls/state, prefix/route/raw/token rejection, original scoring, no repair, fresh process/timeout cleanup, reservation plus original all-process XML vacancy, one-shot complete collection, incomplete failure without scoring/retry, serial OFF/fit2/collect controller and shared1200s deadline.

## Exact experiment / source layout

OFF and saved `fit2_PROMOTE` only, each16TRAIN then16READOUT in original slot order: **64greedy generations,0fits,0updates**. Fit1 is deliberately not repeated. This supplies the missing native greedy exact-TRAIN endpoint; teacher-forced first-choice/full likelihood results are not reused as generated answers.

The new module imports these unchanged, hash-checked native helper files (Main must make their exact bytes available):

- `/tmp/astra_l2_access_high_seed2_20260913.py`, pin `d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525`: original source/plan/collection/candidate binding and **exact `build_cases`**.
- `/tmp/controller_astra_l2_access_high_seed2_20260913.py`, pin `3f5f6118e3fef60074ac533b2650d415b6bd57ff15e379e2bf548be470233721`: reuse only allocation/reservation checks, offline environment, process identity and owned cleanup; do not run its three-state HF controller.
- `/tmp/astra_node3_targeted_prelaunch_20260913.py`, pin `32d366afc432d9e8dcf0c188cbf0725cdadfcc68a1a0f8e0b11532ca7629862a`.
- Original four-file frozen source snapshot `/localhome/local-rohing/astra_sources/l2_lr_comparison_20260913_attempt1` and original plan-pinned public/reflection helpers/model/protocol remain unchanged.

Original root is `/localhome/local-rohing/astra_diagnostics/l2_lr_seed2_high_20260913_attempt1`; plan `74569b1e8c3e0330e0c4f387120fedd4d9f71406366d8b5459088a35ab1a3593`; fit2 candidate `8e79df460e52e94b342de285bcc85ef69cc5fb468a8904d443c665af37bc8ff4`. `--collection` takes the **original L2 completed collection metadata JSON** with pin `24f6e79530b575a8923e5b1145f2e26d7cd95590ceebf9d12b6fd79013ebbd7e`, not the recent HF-access report or an output directory. The earlier helper's default native metadata path was `/tmp/l2_lr_seed2_high_20260913_attempt1_collected`; Main supplies its verified actual path.

Preparation rechecks native tokenizer `build_cases`, full archived assistant masks/target suffixes and literal `calls.json` TRAIN/READOUT/native token prefixes. Workers freshly rebuild those cases and instantiate the original runtime `Native` class, original ENGINE/PARAMS (`temperature0`, seed0, max_tokens32, original penalties/stops), explicit original LoRARequest or OFF=None. Only original messages reach generation; archived target metadata/candidate token sequences never become model inputs. Every returned raw byte/token/prompt prefix and route is checked. Native files are saved before validation; failure evidence is retained.

## Main CLI

Use the original plan-pinned interpreter as `$PYTHON`, the deployed new script as `$GREEDY`, a fresh absolute root as `$NEW_ROOT`, and fresh independently checked boot/lease values. Example argument layout (not executed):

```bash
CUDA_VISIBLE_DEVICES='' "$PYTHON" -B "$GREEDY" prepare \
  --root "$NEW_ROOT" \
  --source /localhome/local-rohing/astra_sources/l2_lr_comparison_20260913_attempt1 \
  --collection "$ORIGINAL_COLLECTION_METADATA" \
  --access /tmp/astra_l2_access_high_seed2_20260913.py \
  --controller-helper /tmp/controller_astra_l2_access_high_seed2_20260913.py \
  --precheck /tmp/astra_node3_targeted_prelaunch_20260913.py \
  --gpu-index 3 --gpu-uuid GPU-e1277146-04f2-c38f-d1ae-1a98132f907e \
  --expected-boot-id "$FRESH_NODE3_BOOT_ID" --lease-end-unix "$LEASE_END_UNIX" \
  --allow-native

CUDA_VISIBLE_DEVICES='' "$PYTHON" -B "$GREEDY" controller \
  --root "$NEW_ROOT" --prepared-sha256 "$RETURNED_PREPARED_SHA256" --allow-gpu
```

Suggested new family: `/localhome/local-rohing/astra_diagnostics/l2_high_seed2_greedy_20260913_attempt1`. Main pins the deployed new script before preparation. Preparation creates `prepared.json` only in a fresh disjoint root and returns its SHA; any subsequent source/interpreter change fails closed. CPU-native preparation occurs **before** the timed controller and makes0generation calls. It does not check GPU occupancy; controller performs fresh checks.

Python APIs mirror CLI: `prepare(settings, root, allow_native=False)`, `controller(root, prepared_sha256, allow_gpu=False)`, `worker(root, prepared_sha256, state, deadline_unix, allow_native=False)`, `collect(root, prepared_sha256, deadline_unix)`. Worker and collect commands are normally **controller-internal**, not extra Main invocations.

## Runtime / collection / scoring boundaries

Controller uses a single1200s wall envelope including its verification, sequential fresh-state subprocesses, cleanup, release and collection. Each worker is capped at420s and shortened to reserve release/collection; collection subprocess is capped at180s, with25s outer cleanup reserve. Not a claim that the budget will suffice. Worker cooperative alarms are backed by parent process waits and identity-bound owned cleanup; no foreign kills or retries. Both preflight and release combine the existing reservation/compute checker with unchanged public-helper `gpu_state` all-process XML query (its30s timeout is not raised). Fresh boot/index/UUID and6h lease margin are required. On a failed worker, release is still attempted and no collection follows.

Successful controller automatically collects **once**, after both worker processes exit and their all-process release checks pass. Output is `$NEW_ROOT` plus `_collected`; claim is sibling `$NEW_ROOT.collection_claim.json`. Do not invoke collect again. Existing root/controller/state/claim/output are never overwritten or retried. Capture hashes, exact requests/responses, worker PID/state/route/candidate/work counts and incomplete/extra artifacts are checked. Failure writes durable terminal/collection-failure evidence and raises; incomplete cells are not scored as zero.

`report.json` gives OFF/fit2 TRAIN and READOUT old8/new8/total16 counts, legal/malformed counts, per-slot choices, exact saved child-target byte matches, length counts, costs and fit2-minus-OFF per view. Correctness is the original runtime's `legal_action` versus original saved-world success actions; it is not a forced choice between candidates. Legacy correctness does not itself exclude length termination, so **`stop_correct` is separately reported**, without silently changing the original scorer. The strict raw legal grammar permits only an original action with optional single newline. No teacher rewrite, output repair, new data or automatic scientific promotion is introduced.

No native preflight or diagnostic result is claimed in this handoff. EDITSTOP.
