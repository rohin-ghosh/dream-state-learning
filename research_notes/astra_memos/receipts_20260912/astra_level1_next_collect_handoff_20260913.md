# EDITSTOP — explicit-roster once-only Level1 collector

2026-09-13 UTC. Main-operated helper preparation only. No native collection,
runtime import, GPU/model execution, node access, repository/Git operations or
changes to original helper/runtime. Failed A100 roots and the running second
roster were not inspected or modified. Main selects the real roster/node/batch
and performs collection.

## Owned files and final pins

- `/tmp/astra_level1_next_collect_20260913.py`
  SHA256 `fba79ae7813ad237b619d75fa65352778828c3a665666262bec0aa67cbd58499`.
- `/tmp/test_astra_level1_next_collect_20260913.py`
  SHA256 `16092ae805b29b870127818a04188b0807d38d600835e6e2b401a6d61d76422d`.
- `/tmp/astra_level1_next_collect_handoff_20260913.md`
  Hash supplied separately, not self-embedded.

Preserved/rehashed unchanged:

- `/tmp/astra_level1_collect_ready_20260913.py`:
  `b53c47e52df0e418167a17b70d79377f7e2609fa3dec6008ee7b31efbc9e4748`.
- `/tmp/test_astra_level1_collect_ready_20260913.py`:
  `4cb42636ced4e76f5fdb775817c50ff5bf34c3b4a10747bb001f1c384b9f0cf3`.
- Frozen exact runtime path `/tmp/astra_level1_skill_run_20260913.py`:
  `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`.

## Explicit CLI and roster/batch custody

```sh
python3 -B /tmp/astra_level1_next_collect_20260913.py \
  --roster /ABS/SELECTED_ROSTER/roster.json \
  --roster-sha256 FULL_LOWERCASE_64_HEX_SHA256 \
  --node node2 \
  --batch-dir /ABS/SELECTED_ROSTER/EXACT_EXISTING_BATCH
```

All four flags are required; node is exactly node1/node2/a100. No roster or
batch-name constants/fallbacks. Variable-size rosters replace the old fixed12
global/six-per-node inventory requirement, while preserving nonempty unique
names/roots and requiring at least one selected-node entry. Selected indices
and UUIDs must be uniquely allocated and typed. Cell names are safe single path
components. Filtering retains roster order and never redirects failed A100 cells
into a node1 fallback; Main supplies the separate fallback roster explicitly.

The batch must be an absolute, existing, non-symlink, normalized immediate child
of the resolved roster directory. `started.json` must match:

- `roster_sha256`: the explicit checked hash;
- `roster`: the resolved absolute roster path;
- `node`: the requested node;
- `batch_name`: the actual directory basename;
- `runtime` and `runtime_sha256`: the frozen exact runtime above.

These are the bindings written by the accepted next-batch helper. A renamed,
wrong-node, wrong-roster, wrong-runtime or incompletely bound batch rejects
before considering collection. Do not edit existing receipts to satisfy this
contract. The historical first-roster helper remains unchanged for its historical
batch receipts; this adapter does not reopen them through a hash-only exception.

The original pinned-precheck `check_node` is unchanged: read the roster's exact
precheck bytes, select the explicit node, and require actual boot-ID and UID
matching. A100 needs its real entry in that precheck file; no default host or
exception is invented. Missing/mismatched prechecks fail. There is no GPU query
or runtime import in the helper itself.

## Readiness, native custody and once semantics

AST tests establish unchanged function bodies for `require`, `digest`,
`unique_object`, `read`, `write`, `occupied`, `controller_present`, `check_node`
and the ENTIRE `collect_cell`. COLLECT_SECONDS remains180.

- Existing ROOT.collection_claim.json, ROOT_collected, or ROOT_collection_driver
  means claimed: no retries or overwrites, including failed prior attempts.
- `controller_failure.json` prevents scoring. A batch launch failure with no
  launched receipt reports failed; missing launch receipt otherwise is pending.
- Original controller PID must be absent from `/proc`; a live, zombie or reused
  PID is conservatively pending. No process is signalled to make it ready.
- Missing capture_complete.json is pending, not successful completion.
- Verify launch node/name/root/index/UUID, PID/PGID/original identity, exact
  original controller command, launched plan hash and prepared plan bytes,
  spec pin, frozen runtime pin, controller_started plan binding and interpreter
  path/hash. The capture-complete bytes must match that plan, calls must be
  integer120, and scored must be false.
- Atomically claim only the fresh external ROOT_collection_driver directory;
  never pre-create the native claim or output. Recheck controller failure/PID
  absence and absence of native claim/output just before calling the child.
- Invoke exactly plan.python, `-B`, frozen runtime, `collect`, root, plan hash,
  captured completion hash and fresh ROOT_collected output. No allow-gpu flag;
  CUDA_VISIBLE_DEVICES is empty and PYTHONDONTWRITEBYTECODE=1; new session;
  stdin DEVNULL; external streamed stdout/stderr; timeout180 seconds per child.
- Full artifact/source/response/adapter/native scoring validation stays in the
  frozen runtime. Successful exit alone is insufficient: collection.json must
  bind the observed completion hash and actual scores.json hash.

No partial/failed work is synthesized into scores. Nonzero native exit, timeout,
missing receipt, changed readiness or receipt/output mismatch yields error and
preserves the one-shot driver attempt and logs. Original root bytes are never
written by this helper. Native output/claim and helper attempts are siblings of
the root; locations and names are identical to the original collector, so a
second helper/pass cannot bypass an existing attempt by using another batch.

One pass over all selected entries, one JSON report per cell. No polling loop,
scheduler, prepare, retry or scientific interpretation. Main can make a later
pass for previously pending cells; claimed/attempted cells remain unrepeatable.
Per-cell errors do not prevent considering other independent cells once.
Exit0 means only pending/claimed/collected statuses, NOT that all work finished.
Any failed/error cell or global custody failure gives exit1. The180-second limit
is per native collection child, not an aggregate-node deadline. Timeout handling
targets only that child, not any original controller or unrelated process.

## CPU validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p 'test_astra_level1_next_collect_20260913.py' -v
python3 -B /tmp/astra_level1_next_collect_20260913.py --help
sha256sum /tmp/astra_level1_next_collect_20260913.py /tmp/test_astra_level1_next_collect_20260913.py /tmp/astra_level1_next_collect_handoff_20260913.md
```

18 tests PASS,0.174s. Retains all12 original scenarios with explicit-input
fixture adaptation: pending/no completion, present controller, exact one-shot
collection, all claim types, controller failure, completion/plan/interpreter
pins, nonzero/timeout/missing receipt, selected-node single-pass and error exit.
Adds variable-size a100/node2 selection, explicit roster hash and every started
binding, wrong directory/symlink/empty selection, invalid/duplicate cells,
AST custody preservation, explicit CLI and global error status.

All node identity, controller readiness and native subprocess calls were mocked;
the fake runtime is deliberately nonexecutable text. Only temporary CPU fixtures
were scored by mocks, not model outputs. No real precheck, native replay, GPU or
collection occurred. EDITSTOP: three new files ready for Main's pinned use.
