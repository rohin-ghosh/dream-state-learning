# V10R1 W0 current-bytes pre-GPU audit

Date: 2026-09-12 UTC  
Observation window: 07:16--07:21 UTC  
Disposition: **current bytes pass their CPU gate; no immutable preparation or
GPU execution existed at the end of the observation window.**

This is a read-only watcher audit of Astra's conditional native-action writer
gateway. It did not edit builder-owned source, prepare or execute a run, move
source to a node, or start/stop any process.

## Exact current bytes and CPU evidence

The earlier 47-test audit no longer binds the current source and test file.
Astra added explicit lease-end/cutoff custody and evidence-boundary checks
after that audit. At 07:20:39--07:21:40 UTC the VM bytes were stable at:

- `organism_v6/multikey_writer_gateway_simple.py`:
  `dc0b0c48fa58b85b5f37d5aa4ad5c1a9214257d2e08ac3231861e4217cd46c54`
- `tests/test_multikey_writer_gateway_simple.py`:
  `adf3819a17a3a4721dd7bdeebac64f41810a1aa38b37eeac9620b90041fb0381`
- `gpu/multikey_writer_gateway_simple.sh`:
  `3994bf389e63ac790b3eb500c74a974ed57b88fd8fd02d494ae6fecc0ab33665`

Every digest above was independently recomputed and confirmed to contain
exactly 64 hexadecimal characters. The launcher value corrects the 65-character
transcription error in the historical audit note; it is not a launcher byte
change.

I independently ran, on those exact VM bytes:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_multikey_writer_gateway_simple -v
```

Result: **51/51 passed in 8.997 seconds**. `bash -n` also accepted the thin
launcher. This was CPU-only. It did not load the real tokenizer or model and
is not scientific evidence.

The four tests added since the earlier audit exercise explicit finite
`lease_end_unix`/`lease_cutoff_unix`, the inclusive six-hour finish boundary,
rejection of a ten-minute cutoff before output creation, and rejection of an
unsafe sealed cutoff before GPU access. The implementation requires
`lease_cutoff_unix <= lease_end_unix - 21600` at both preparation validation
and execution validation.

## Contract trace on current bytes

The current implementation still realizes the central V9 + V10 + V10R1
mechanics:

- two engineered roots, complementary `W+`/`W-` maps, and four distinct
  clean-base fits;
- exactly 128 target-masked rows and 256 optimizer steps per fit, hence 512
  rows and 1,024 steps overall, with rank 8, alpha 16, dropout 0.05, all seven
  attention/MLP projection families, AdamW at `3e-5`, batch size one, and two
  fixed unshuffled passes;
- joint real-tokenizer preflight over context plus exactly `ACT: a0\n` or
  `ACT: a1\n` plus EOS, refusing truncation, token-boundary straddling,
  unequal candidate masks, or tokenizer round-trip changes before model load;
- one fresh process for each of four fits and each of five adapter/OFF states
  by generation/scoring operation, requiring 14 distinct worker PIDs;
- exactly 1,504 typed requests: 384 primary generations, 256 OFF-oracle
  generations, 240 spill generations, 384 primary likelihood scores, and 240
  spill likelihood scores;
- local-only Qwen2.5-7B-Instruct loading, one pinned A40 UUID/node/driver,
  exact local snapshot inventory hashes, exact dependency versions, and a
  maximum of one GPU for three measured hours;
- exact ASCII-boundary output parsing, adapter-only multiple-`ACT` gating,
  exact native-interface equality, full candidate-plus-EOS likelihood sums,
  stable two-choice log-sum-exp normalization, fixed denominators, full
  precision, fail-if-exists receipts, raw traces, adapter-tree hashes, final
  seal, and read-only replay.

The arithmetic agrees with the effective contract. Per-key NLL gain is the
even median of the four values of
`log q_target(adapter) - log q_target(OFF)`. Per-key directional margin is the
even median of `ell_target - ell_opposite`. Mean binary TV correctly reduces
to `abs(q0_adapter - q0_OFF)` for the two-action distribution. Root predicates
are AND-reduced across both maps and then across both roots. Classification
precedence is `ASSAY_INVALID`, `OPTIMIZATION_INCONCLUSIVE`,
`INTERFACE_INVALID`, `BINDING_WITH_SPILL`, `MULTIKEY_BINDING_PASS`, then
`GATEWAY_NEGATIVE`.

The frozen generated identifiers plus one-character neighbours were also
checked directly: each root has 16 distinct values and the two 16-value sets
have empty intersection. The implementation regenerates and byte-compares the
frozen material, although an explicit general cross-root tool-plus-neighbour
assertion remains defense in depth rather than a launch blocker.

## Live VM and node state

At 07:21:40 UTC, searches under the VM's `~/v6_out`, `~/dream-state`, and
`~/dream-state-artifacts` found no `PREPARED_SEAL.json`,
`EXECUTION_STARTED.json`, `REAL_EXECUTION_SEAL.json`,
`NONREPORTABLE_ABORT.json`, or W0 process. The three W0 source files remained
untracked VM worktree bytes. None of the three inspected A40 nodes yet held the
W0 source or a prepared receipt.

Read-only node checks at 07:17--07:21 UTC found:

- `ipp2-ovx-p6-09` (node 3): all eight A40s idle; driver `580.173.02`; local
  Qwen snapshot ref `a09a35458c702b33eeacc393d103063234e8bc28`; Python
  `3.12.3`, torch `2.13.0`, transformers `5.5.3`, peft `0.20.0`, tokenizers
  `0.22.2`, safetensors `0.8.0`, numpy `2.3.5`.
- `a4u8g-0105` (node 1): GPUs 0--2 occupied and GPUs 3--7 idle; same driver,
  local snapshot ref, and package versions.
- `ipp2-ovx-p2-08` (node 2): all eight A40s showed substantial allocations;
  it was not the clean launch choice at that observation.

These observations establish availability only. The ref name is not the
required model/tokenizer content inventory hash, and current source presence
on the VM is not source identity on an execution node.

## Exact next evidence required

Before W0 is launch-ready, the next durable evidence is:

1. transfer/freeze these exact three source bytes on one chosen A40 node;
2. create an immutable configuration binding that node's hostname, one idle
   A40 UUID, driver, authoritative lease end and cutoff, environment versions,
   absolute model/tokenizer snapshot paths, the 40-hex local revision, full
   model/tokenizer inventory hashes, protected roots, frozen seeds, intake,
   scope, and dated builder preflight reference;
3. run `prepare` there and preserve a successful real-tokenizer preflight,
   51-test receipt, four exact fit inputs/encoded hashes, request blueprint,
   manifest, receipt set, and `PREPARED_SEAL.json` while the source hashes
   remain unchanged;
4. only then execute once with `--allow-gpu`, preserving four clean-base fit
   receipts, 1,504 raw records and traces, exact reducer report, resource
   receipt, final seal, and successful read-only replay.

The prepared review receipt is still designed to say
`NOT_AN_INDEPENDENT_APPROVAL`, and validation checks its hash rather than
rejecting that status. `AGENTS.md` makes this nonblocking for Astra's bounded
launch, but it does not satisfy V9's paper-closure term. A fresh implementation
reviewer and separate scientific advocate must inspect identical current
source, tests, manifest, and dry-run/preparation receipts, or the evidence must
explicitly record the standing operational waiver, before calling the
artifact fully V9/V10/V10R1-closed.

## Claim boundary

There is no W0 scientific result yet. Even a sealed
`MULTIKEY_BINDING_PASS` would support only four supervised, seen-key
conditional native-action carriage instances under the enumerated shortcut,
optimization, binding, interface, and spill gates. The implementation itself
marks the material as synthetic researcher-authored, the lineage as unclean,
and official model authentication as `UNRESOLVED_LOCAL_HASHES_ONLY`. It cannot
support a claim about retention, lived learning, DREAM, parenting,
generalization, connected memory, recurrence, continual learning,
reliability, child authorship, or a whole organism.
