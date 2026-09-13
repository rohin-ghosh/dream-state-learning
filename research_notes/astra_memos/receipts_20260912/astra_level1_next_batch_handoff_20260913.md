# EDITSTOP — explicit fresh-roster Level1 batch adapter

2026-09-13 UTC. Code preparation and CPU/mocked tests only. No native
preparation, GPU/controller launch, remote/node access, repository/Git operations,
or changes to other agents' files. Main alone launches the adapter.

## Changed paths and final hashes

- `/tmp/astra_level1_next_batch_20260913.py`
  SHA256 `03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2`.
- `/tmp/test_astra_level1_next_batch_20260913.py`
  SHA256 `8ff38be690a62bf9fb17e656b8fab718bbaa10230cd331a95d4572dd783a33a9`.
- `/tmp/astra_level1_next_batch_handoff_20260913.md`
  Hash supplied separately rather than self-embedded.

Original files were read, not edited, and rehashed unchanged:

- Original batch `/tmp/astra_level1_batch_20260913.py`:
  `7a0a7628e04d0f54a3e5b28e307d30b17f3412316d1dcf2ed7a14d7b7e7ebfce`.
- Original tests `/tmp/test_astra_level1_batch_20260913.py`:
  `de9d1dedbb04a5db31d3f722f85af08c0c6a1e2662a48d04c32a6c4c4c346fc2`.
- Frozen runtime at EXACT path `/tmp/astra_level1_skill_run_20260913.py`:
  `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`.
  No runtime path/pin CLI override or alternate backend exists.

## Main's future CLI contract

```sh
python3 -B /tmp/astra_level1_next_batch_20260913.py \
  --roster /ABS/FRESH_ROSTER/roster.json \
  --roster-sha256 FULL_LOWERCASE_64_HEX_SHA256 \
  --node node1 \
  --batch-name batch_node1_unique
```

All four flags are required. `--node` accepts exactly node1, node2, a100.
This command performs native preparation and submits controllers when Main
invokes it on the intended host; it is NOT a dry-run. `--help` is safe CPU-only.
No prepare-only flag was added: it is unnecessary for this adapter and would
introduce a separate partial-root/re-entry workflow. No resume/retry mode.

The batch directory is exactly `resolved_roster.parent / batch_name`.
Its mkdir is an exclusive atomic fresh claim BEFORE importing the runtime or
performing native work. An existing directory, file or symlink fails; nothing
is reused, deleted or overwritten. Batch/cell names must be single safe path
components, starting alphanumeric and containing only alphanumerics, underscore,
period or hyphen, at most128 characters. No traversal/absolute names.

Roster schema remains the original: `prechecks: {path,sha256}` and `entries`.
Entries retain node, name, root, gpu_index, gpu_uuid and spec `{path,sha256}`.
Only entries whose node matches the explicit selection are processed, in
original roster order. No matching cells fails instead of reporting success.
Selected cell names, resolved roots, indices and UUIDs must each be unique;
roots must be absolute; index must be a nonnegative integer (not bool).
Allocations must match the selected pinned precheck config before claiming.
Native prepare retains responsibility for fresh per-cell root creation and
all spec/source/native checks; an already-used root cannot be resumed.

Roster and frozen runtime hashes are checked before reading the request for
execution; precheck identity file must match its roster pin. The supplied
roster hash must be full lowercase64-hex. No default historical roster is used.

## A100 support is schema-only until Main supplies a precheck

The precheck file may contain `a100` under exactly the same node-config schema:
`daemon_identities` list, `gpus` index-string-to-UUID mapping, `host_boot_id`
nonempty string, and `uid` nonnegative integer. No boot ID, UID, daemon identity,
UUID or permissive exception was invented. Missing a100 config or allocation
rejects before native work. Main must supply and pin the real config.

The inherited `/localhome/local-rohing/queue/{pending,running}` requirement is
UNCHANGED on a100. Missing/unreadable/nonempty queue directories are not bypassed.
If the actual host does not satisfy that contract, report the mismatch rather
than introducing a fallback. Config presence is not GPU/lease approval.

## Safety behavior preserved exactly

AST regression checks establish equality to the original batch for `digest`,
`identity`, `selected`, `known_exception`, `reservations`, and the complete
per-cell body after node filtering. No hot NVML changes or extra exception.

Per selected cell, the unchanged sequence is:

1. Frozen runtime `prepare`, explicit root/spec path/spec hash, `--allow-native`,
   timeout180 seconds, CUDA_VISIBLE_DEVICES empty. Save stdout/stderr prepare.log.
2. Parse the returned plan hash, call frozen `runtime.verify(..., native=False)`
   for source/runtime/interpreter/prepared-byte/config checks, then match the
   roster's index AND UUID to the verified plan.
3. Fresh original reservations scan: bind boot ID and UID; check permitted UUID;
   inspect same-UID process CUDA environments; reject occupied/unresolved records.
   Preserve only exact daemon identities and the exact transport-ancestor rule
   with transport hash
   `33000acd013adbf8dbb593c9baf3f7acaa8911db00e85f90a5abc6cd25afcc44`.
   Require unchanged shared queue vacancy.
4. Original `probe.gpu_state(plan)` all-process XML vacancy check.
5. Original strict lease margin: lease_end must exceed current time plus
   5400+180+21600 seconds.
6. Frozen runtime controller with plan hash and `--allow-gpu`; fresh session;
   stdin DEVNULL; stdout/stderr controller.log; CUDA_VISIBLE_DEVICES is the
   exact allocated GPU UUID, not index. Record PID/PGID/process identity and
   original cap_seconds5400. Native timeout/cleanup enforcement stays in the
   unchanged runtime; no new batch watchdog or NVML behavior is introduced.

Batch receipts: started.json, per-cell prepare.log/precheck.json/controller.log/
launched.json or failure.json, then finished.json only if all submissions succeed.
Started adds explicit roster path/hash, node, batch name, runtime path/hash.
Successful completion means ALL_CONTROLLERS_SUBMITTED_NOT_RESULTS, not successful
fits/readouts. Failure stops the batch with retry=false. If a process was already
created, controller_may_be_running=true and its PID is preserved. Earlier launched
controllers are not killed or retried. Even a failed/empty claimed batch remains
claimed; Main reconciles identities/root state, never blindly reruns it.

## CPU tests and limitations

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p 'test_astra_level1_next_batch_20260913.py' -v
python3 -B /tmp/astra_level1_next_batch_20260913.py --help
sha256sum /tmp/astra_level1_next_batch_20260913.py /tmp/test_astra_level1_next_batch_20260913.py /tmp/astra_level1_next_batch_handoff_20260913.md
```

11 tests PASS,0.028s. All three original tests retained: historical12 unique
allocations/spec pins, UUID/index/all visibility matching, exact exception
identity/transport ancestry. Additional tests cover all three node filters,
roster/precheck pins, missing a100 config, bad names/empty selection/duplicates,
exclusive fresh claim, AST safety preservation, explicit CLI, zero-CUDA native
prepare arguments, UUID controller environment and fresh session, and fail-before-
Popen behavior for preparation/verify/allocation/reservation/XML/lease failures.

All subprocess preparation/controller calls in tests were MOCKED. No actual
reservations scan, all-process GPU query, model/tokenizer preparation, host
precheck collection, lease verification or controller launch was performed.
Original roster/spec checks were local metadata reads only. Temporary receipts
were in auto-removed test directories. Main must supply the real new roster and
host prechecks, and pin this adapter before launch. EDITSTOP: three files ready.
