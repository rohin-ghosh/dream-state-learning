# FeltCraft v6 external scope-audit contract

Status: governance proposal only. This document authorizes no implementation,
test, kernel run, audit run, compute, promotion, or scientific claim.

## 1. Exact subject and proposal-time bindings

SK10 is an external post-freeze governance review of exactly these five files:

```text
feltcraft_symbolic_kernel/__init__.py
feltcraft_symbolic_kernel/kernel.py
feltcraft_symbolic_kernel/report.py
feltcraft_symbolic_kernel/run.py
feltcraft_symbolic_kernel/test_kernel.py
```

The repository root is `.`, the recursive root is
`feltcraft_symbolic_kernel`, and the fixed Git diff base is the full commit
`742f8bfa4bf4e530fdf264150bff962506fe449f`. The ratified V6 change supplies the exact audit-contract and
scope-schema path/SHA-256 context bindings. The future request copies those
values and supplies the SHA-256 of the exact ratified `change.json`; none is
chosen by the reviewer. The contract never embeds or self-binds its own hash.

Proposal-time fixed values are therefore: repository and recursive roots,
five paths, manifest encoding, diff base, request/schema field definitions,
and the contract/schema bindings carried by the ratified change. Future values
are only the frozen file bytes and per-file sizes/hashes, manifest root,
request bytes and requester, implementation authors, freeze/request/context/
review/adjudication times, reviewer identity/evidence/attestations, receipt,
and the human disposition. No future value or pass is predicted here.

## 2. Deterministic byte and path checks

Resolve the audit root without following symlinks. Its complete recursive
entry set must equal the five real regular files above in raw UTF-8 path order.
No extra entry, directory, symlink, device, ignored/generated file, deletion,
case collision, invalid UTF-8, absolute path, empty segment, `.` segment, or
`..` segment is permitted. Bind each raw file by path, byte length, and
SHA-256. For each sorted entry encode

```text
uint32be(len(path_utf8)) || path_utf8 || uint64be(size) || sha256_raw32
```

and hash `b"feltcraft-scope-manifest-v1\0"` plus the concatenation. With
rename detection off, union the NUL-delimited paths from
`git diff --name-only -z --no-renames 742f8bfa4bf4e530fdf264150bff962506fe449f -- feltcraft_symbolic_kernel`
and `git ls-files -z --others --exclude-standard -- feltcraft_symbolic_kernel`.
Reject deletions and require discovered, changed, and manifested path equality.

Every file must parse with `ast.parse(..., feature_version=(3,9))`. Enumerate
every `Import` and `ImportFrom`; local imports must resolve to the five paths,
and nonlocal top modules are exactly `collections`, `fractions`, `itertools`,
`json`, `pathlib`, and `sys`. Reject star/dynamic/unresolved imports, vendoring,
native extensions, and dependency metadata. The direct forbidden-AST registry
is `feltcraft_scope_structural_v6`: F01 imports; F02 direct uses/references of
`eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`, `delattr`,
`globals`, `locals`, `vars`, and dunder attributes; F03 direct syntax for stdin,
arguments, environment, network, IPC, subprocess, configuration, arbitrary or
audit/review/scientific file reads, and filesystem operations other than a
syntactic candidate for the sole allowed golden write; F04 direct identifier
components for renderer/world/life/agent/model/provider/tokenizer/DREAM/SLEEP/
reader/memory/LoRA/weights/GPU/remote/network/subprocess/promotion/benchmark/
scientific/claim capabilities; and F05 direct static CLI surfaces.

The only declared CLI is `python3 -I -m feltcraft_symbolic_kernel.run`, with no
arguments, options, stdin, environment, configuration, hooks, or alternate
entrypoint. These are deterministic syntax and inventory checks. They do not
claim a complete Python call graph, alias/callback/context-manager resolution,
dormant-branch capability proof, sandbox, or security proof.

## 3. Fresh independent human source review

After freeze, human governance creates the canonical JCS-plus-one-LF request
at `research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v6/scope_audit.request.json`. It contains exactly
the schema-defined fields and copies the fixed diff base and the ratified
change's change/contract/schema hashes. A reviewer starts in a fresh context
after the request, is byte-distinct from every implementation author, authored
and modified none of the five subject paths, and binds identity evidence.
Times satisfy `frozen <= request-created <= context-created <= review-started
<= review-completed <= adjudicated`.

The reviewer reads the exact five frozen files and explicitly reviews them
against all eight frozen forbidden-scope atoms. The reviewer records findings,
escalates every unresolved call, alias, callback, context-manager, dormant
branch, allowed-write-equivalence, capability, or reachability ambiguity, and
attests only if no ambiguity remains and the sole optional filesystem effect
is semantically equivalent to
`Path("golden_report.json").write_bytes(exact_success_bytes)`. This is a
human-adjudicated conservative review, not a deterministic completeness claim.

Human governance separately records an explicit attestation accepting the
deterministic checks, the review's freshness/independence, and its forbidden-
scope disposition. `passed` is true only when all fourteen schema checks are
true, exact path/empty-finding conditions hold, the reviewer attestations are
true, and the explicit human adjudication accepts them. A false check forces
`passed=false`. The receipt is labeled `governance_evidence_only`; it is not a
runtime input, scientific evidence, benchmark evidence, promotion token, or
security proof.

## 4. Visibility and authority

Contract/schema byte payloads are distinct from their repository path/hash
context bindings. Path/hash metadata is visible to authority, SK10, and human
governance; byte payloads are visible only to SK10 and human governance. All
audit subject bytes, request, reviewer evidence, receipt, and adjudication are
forbidden to SKN01--SKN06 and SKN05, and permanently forbidden to any renderer,
life, agent, model, tokenizer, DREAM/SLEEP/memory, LoRA, GPU/remote, benchmark,
promotion, or scientific-claim stage. Runtime reports never enter SK10, and no
audit or runtime output enters successor science.
