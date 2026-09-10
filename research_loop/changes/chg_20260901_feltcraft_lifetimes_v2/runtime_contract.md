# FeltCraft-Lifetimes CPU runtime and visibility contract v2

**Status:** proposal only. This contract closes the first CPU scope without
creating dormant model, DREAM, SLEEP, tokenizer, or LoRA implementations.

## 1. Active CPU graph

The active graph contains exactly these declared principals:

- `N01_AUTHORITY`: validates exact ratification and requested scope.
- `N02_GENERATOR_ENV`: deterministic hidden-world generation and transitions.
- `N03_SOURCE_COLLECTOR`: open-loop public source action schedule.
- `N04_PUBLIC_LOG`: immutable public source events.
- `N05_TARGET_CLONE`: disposable calibration/evaluation state.
- `N06_EXACT_CONTROLLERS`: BF/NPLUS/ATOM/SCHEMA/SOURCE/ORACLE calculations.
- `N07_SCORER_REPORT`: isolated certificates, resource records, and verdict.

Allowed directed edges are exactly:

```text
N01_AUTHORITY -> N02_GENERATOR_ENV
N02_GENERATOR_ENV -> N03_SOURCE_COLLECTOR
N03_SOURCE_COLLECTOR -> N02_GENERATOR_ENV
N02_GENERATOR_ENV -> N04_PUBLIC_LOG
N04_PUBLIC_LOG -> N05_TARGET_CLONE
N02_GENERATOR_ENV -> N05_TARGET_CLONE
N04_PUBLIC_LOG -> N06_EXACT_CONTROLLERS
N05_TARGET_CLONE -> N06_EXACT_CONTROLLERS
N02_GENERATOR_ENV -> N06_EXACT_CONTROLLERS
N06_EXACT_CONTROLLERS -> N07_SCORER_REPORT
N05_TARGET_CLONE -> N07_SCORER_REPORT
```

Every endpoint is declared. The environment-to-controller edge carries hidden
state only to ORACLE and scorer-side posterior enumeration under the field
permissions below. No future scientific organ is an active node or edge.

## 2. Closed capability boundary

The closure claim is relative to this named trusted base: a hash-bound CPU
container image, one hash-bound launcher, the kernel's namespace/seccomp
enforcement, the exact source package, and declared read-only input manifests.
It is not a claim about every capability of the host OS.

If ratified, implementation must run one local CPU entry point under:

- read-only container root and individually hash-bound read-only inputs;
- one fresh writable artifact directory;
- no network interface, inherited sockets, credentials, proxy/provider
  variables, user site, plugin path, or host service IPC;
- no GPU/accelerator or host device mounts beyond explicitly listed pseudo
  devices;
- `python -I`, exact interpreter/package/library closure, and fixed argument
  grammar;
- no subprocess/shell, dynamic plugins, package installation, model/tokenizer
  imports, provider SDKs, torch, transformers, CUDA, or remote commands;
- exact environment allowlist, resource limits, and fail-closed startup if an
  enforcement mechanism or content hash differs.

Tests attempt alternate Python imports, native loading, subprocess/shell,
filesystem/symlink escape, user-site/plugin discovery, sockets/DNS, inherited
file descriptors, credential access, and accelerator discovery. An undeclared
capability is absent or denied before use. These are governance receipts, not
paper evidence.

## 3. Field-level permissions

The following are distinct fields; prose cannot override these permissions.

| Field | Generator/env | Source collector | Public log | Target clone | Exact controllers | Scorer/report |
|---|---|---|---|---|---|---|
| ratification hash/scope | read | none | none | none | none | hash only |
| hidden recipe graph | originate/read | none | none | transition only | ORACLE/posterior only | certificate only |
| hidden role/slot alignment | originate/read | none | none | transition only | ORACLE/posterior only | certificate only |
| regime/twin label | originate/read | none | none | none | NPLUS audit and posterior only | aggregate only |
| source schedule slot | none | originate/read | none | none | none | count only |
| source RNG counter | none | originate/read | none | none | none | terminal count only |
| public pre-state | declassify | read | append | sealed prefix | legal subsets | none |
| public action | transition input | originate | append | append locally | legal subsets | trace only |
| public observation | declassify | read | append | append locally | legal subsets | trace only |
| public post-state | declassify | read | append | append locally | legal subsets | none |
| family/instance/event index | originate | read schedule view | append | sealed prefix | legal subsets | aggregate only |
| target public goal/state/budget | originate | none | none | read | all controllers | trace only |
| target calibration prefix | transition | none | none | append/read | ATOM/SCHEMA/SOURCE/ORACLE | trace only |
| decisive action/plan truth | originate/read | none | none | forbidden | ORACLE/posterior only | certificate only |
| target query/action trace | transition | none | none | append | current controller only | append-only |
| target score | derive | none | none | none | none | originate/append |
| evaluation RNG/cache | none | none | none | local only | local only | terminal hash only |
| evaluation report | none | none | none | write-only channel | write-only channel | append-only |

`N06_EXACT_CONTROLLERS` is internally split by the information sets in
`measurement_contract.md`; no controller may inherit another controller's
fields. Unique canaries are injected into every forbidden hidden field and
scanned across public events, controller inputs, target bytes, suffix state,
and reports. Scorer declassification exposes values/certificates, never hidden
bindings or answer-bearing traces to an acting policy.

Scientific DREAM/SLEEP claims, semantic proposals, provenance graph, workspace
`Z`, reader candidates/returns, compiler corpus, model state, tokenizer state,
adapter weights, optimizer state, and backend-private work are absent fields in
CPU v2. Adding any requires a successor change.

## 4. Evaluation suffix isolation

The CPU suffix state contains only:

- bound authority/code/manifest hashes;
- source instance/event cursor;
- source environment continuation state;
- non-evaluation RNG counters;
- immutable public-log hash;
- predeclared target-deck cursor;
- inert canary registry.

Canonical bytes are RFC-8785/JCS plus one LF. The hash is:

```text
SHA256("feltcraft.cpu.suffix.v2\0" || u64be(length) || canonical_bytes)
```

Run-versus-skip evaluation requires identical suffix hash, continued source
event bytes, non-evaluation counters, and public-log hash. Target reports live
in a disjoint branch and are excluded from equality. Wall time, PIDs, temp
paths, inode numbers, and OS counters are report metadata, never scientific
state.

## 5. PCFL disposition

CPU v2 removes the v1 analytical PCFL fallback from requested scope. Note 48
remains historical context only. A FeltCraft `REJECT` does not automatically
select or authorize PCFL-Stream; it returns to a new human-reviewed design
decision. This eliminates post-result fallback drift without implementing a
second benchmark.
