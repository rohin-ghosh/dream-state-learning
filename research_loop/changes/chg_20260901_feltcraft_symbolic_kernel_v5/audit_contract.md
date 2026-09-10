# FeltCraft v5 lineage and external scope-audit contract

**Status:** proposed governance design only. This document authorizes no
implementation, test, kernel run, audit run, compute, promotion, or claim.

## 1. Standalone lineage

The v5 FeltCraft registry base is the empty registry
`FELTCRAFT_UNIMPLEMENTED_PROPOSAL_BASE_V1`:

```text
nodes = []
edges = []
loops = []
claims = []
implemented_change_ids = []
```

This is an implementation-state base, not a claim that the repository has no
other research architecture. The following are proposal ancestors only and
were never applied to an implementation registry:

| proposal | change SHA-256 | disposition |
|---|---|---|
| `chg_20260901_feltcraft_lifetimes_v1` | `3f349860ec02a906caff8c735f3c8068e525dfa2bb9a3fd32aa81bef707489dd` | proposed; no consensus or ratification |
| `chg_20260901_feltcraft_lifetimes_v2` | `cdb10a61638454ce86e54de359d09c1cdd082029b2a433209b9553d917324361` | rework; implementation forbidden |
| `chg_20260901_feltcraft_symbolic_kernel_v3` | `53fd4e0bce3360bfb649e06c3dccf85356eea45188bb1c9cea5e8afffc2b7db3` | rework; implementation forbidden |
| `chg_20260901_feltcraft_symbolic_kernel_v4` | `fa5ef77c127b7fe614ef33875d55a4099a023bec8fc6a8a1dd98db5f0fbf2a8e` | rework; implementation forbidden |

The v4 consensus bytes themselves have SHA-256
`682a6b53dce625283df32b82bad559ca03e5ec77e64f36279b1da8fd119ab12e`.
No proposal agreement, retained test, human-required state, or later successor
wording changes those dispositions.

V5 must therefore use standalone replacement semantics. Its `change.json`
must name the empty base above, bind this lineage table, and declare complete
final registries. Every final node, edge, loop, and active claim is an `add`
against the empty base. An identifier absent from a final registry does not
exist; removals, modifications, inherited entries, aliases, and implicit
carry-forward are invalid. In particular, no V1/V2 `N*`, `E*`, or `L*` entry,
no v3 renamed `SKN*` entry or `SKL01_EXACT_SYMBOLIC_KERNEL`, and no v4
operation record is active merely because it appears in an ancestor.

The complete v5 runtime graph registry is exactly:

```text
nodes = [
  SKN01_AUTHORITY,
  SKN02_DOMAIN_ENUMERATOR,
  SKN03_PROJECTIONS,
  SKN04_TWIN_COST_BRIDGE_DELETION_CHECKER,
  SKN05_GOLDEN_REPORT_VALIDATOR
]
edges = [
  SKE01_authority_to_enumerator,
  SKE02_authority_to_projections,
  SKE03_authority_to_checker,
  SKE04_authority_to_validator,
  SKE05_enumerator_to_projections,
  SKE06_enumerator_to_checker,
  SKE07_enumerator_to_validator,
  SKE08_projections_to_validator,
  SKE09_checker_to_validator
]
loops = [SKL01_PREAPPROVAL_GOVERNANCE, SKL02_RATIFIED_CPU_CONFORMANCE]
claims = [
  C01_symbolic_conformance_only,
  C02_random_motif_information_geometry,
  C03_twin_cost_and_bridge_deletion,
  C04_atoms_or_baseline_claim,
  C05_learned_system_and_paper_claims,
  C06_report_or_audit_as_scientific_evidence
]
```

All six claims are `add` operations against the empty base. C04--C06 are
active negative-boundary statements: they deny atoms/baseline, learned-system
or paper, and report/audit-as-science claims; they are not positive results.
Exact registry equality, unique IDs, edge endpoint membership, and absence of
all ancestor-only IDs are pre-ratification structural requirements. This
contract does not choose or ratify the final claim wording beyond requiring
those preserved boundaries.

## 2. Audit subject and byte manifest

SK10 is a post-freeze external review. Its repository root is exactly the Git
worktree root, represented as `.`, and its recursive audit root is exactly
`feltcraft_symbolic_kernel`. Resolve both without following symlinks. The audit
root must be a real directory and its complete recursive entry set must be
exactly these five regular files, in this UTF-8 byte order:

```text
feltcraft_symbolic_kernel/__init__.py
feltcraft_symbolic_kernel/kernel.py
feltcraft_symbolic_kernel/report.py
feltcraft_symbolic_kernel/run.py
feltcraft_symbolic_kernel/test_kernel.py
```

There are no exclusions. An extra file, directory, symlink, device, ignored
file, generated file, or case-colliding path fails root/path equality. Each
manifest entry records the exact repository-relative path, byte length, and
SHA-256 of the raw file bytes. Paths must decode as UTF-8, use `/`, contain no
empty, `.` or `..` segment, and are not Unicode-normalized or case-folded.

Sort entries by raw UTF-8 path bytes. For each entry construct:

```text
uint32be(len(path_utf8)) || path_utf8 || uint64be(size_bytes) || sha256_raw32
```

Then compute:

```text
manifest_root_sha256 = SHA256(
  b"feltcraft-scope-manifest-v1\0" || concatenated_entry_encodings
)
```

The v5 proposal must bind an exact full Git diff-base commit. With rename
detection disabled and NUL-delimited path output, SK10 takes the union of (a)
tracked paths emitted by `git diff --name-only -z --no-renames <base> --
feltcraft_symbolic_kernel` and (b) paths emitted by `git ls-files -z --others
--exclude-standard -- feltcraft_symbolic_kernel`. It rejects deletions,
non-UTF-8 paths, and paths outside the audit root, sorts by UTF-8 bytes, and
compares the result with the manifest paths. The two lists must be exactly
equal to the five paths above. Git status is supporting path evidence only;
the recursive manifest, not a commit or status assertion, binds the frozen
implementation bytes.

## 3. Deterministic closure

The audit uses CPython 3.9 grammar via `ast.parse(..., feature_version=(3,9))`
on every manifested file. Parse failure fails the audit. Source locations are
`path:one-based-line:zero-based-column` and are sorted as UTF-8 strings.

Import closure is the complete AST walk of every `Import` and `ImportFrom`.
Relative and absolute package imports must resolve to one of the five manifest
paths. A nonlocal top-level module must be one of exactly
`collections`, `fractions`, `itertools`, `json`, `pathlib`, or `sys`.
Star imports, unresolved relative imports, imports outside that allowlist,
namespace extension, vendored code, native extensions, package metadata,
requirements/lock entries inside the audit root, and dynamic import surfaces
(`__import__`, `importlib`, `pkgutil`, or `runpy`) fail. Standard-library
implementation internals are not claimed as audited application bytes.

CLI closure contains exactly one entrypoint:
`python3 -I -m feltcraft_symbolic_kernel.run`. It accepts no arguments,
options, stdin, environment variables, configuration files, plugin hooks, or
alternate entrypoints. `sys.argv`, `sys.stdin`, `input`, argument-parser/click
registries, console-script metadata, and module-discovery hooks fail.

The forbidden-rule registry is exactly `feltcraft_scope_rules_v1`:

1. **F01_IMPORT:** apply the complete import rule above.
2. **F02_DYNAMIC:** reject calls or references to `eval`, `exec`, `compile`,
   `__import__`, `getattr`, `setattr`, `delattr`, `globals`, `locals`, or
   `vars`, and reject any attribute whose name begins and ends with `__`.
3. **F03_INGRESS:** reject runtime reads from stdin, arguments, environment,
   network, IPC, subprocesses, configuration, arbitrary files, audit files,
   review files, manifests, receipts, or scientific artifacts. The only
   permitted filesystem effect is an optional write of the exact successful
   bytes to repository-relative `golden_report.json`; it is an output sink,
   never an input.
4. **F04_CAPABILITY:** reject any reachable renderer/RNG, source-life or
   target-agent execution, model/provider/tokenizer, DREAM/SLEEP/reader/memory,
   LoRA/weight, GPU/accelerator, remote/network, subprocess, promotion,
   benchmark-authority, or scientific-claim capability. Imports outside F01
   already fail; the reviewer must additionally inspect locally defined calls,
   aliases, callbacks, decorators, context managers, and dormant branches.
5. **F05_REACHABILITY:** construct the complete local call graph from the CLI
   module and exported package callables. Every unresolved indirect call fails.
   No audit input or audit output may reach a runtime node, and no runtime or
   audit output may reach a successor benchmark, model, or scientific stage.

F03 mechanically rejects `open`, every `Path` read/open/discovery/metadata
method (`open`, `read_bytes`, `read_text`, `iterdir`, `glob`, `rglob`, `stat`,
`lstat`, `exists`, `is_file`, `is_dir`, `resolve`), and every audit basename
(`scope_audit.json`, `scope_audit.request.json`, `scope_audit.schema.json`,
`audit_contract.md`) occurring as an exact string literal or final path
component. The sole filesystem exception is a resolved call equivalent to
`Path("golden_report.json").write_bytes(exact_success_bytes)`; any other path
expression or method fails.

For F04, split every `Name`, attribute, function/class name, parameter, and
import alias on `_`, ASCII-case-fold each component, and reject an exact
component in this registry:

```text
argparse click renderer render world life agent model provider tokenizer dream
sleep reader memory retrieval lora weight weights gpu cuda mps remote socket
http https subprocess popen promotion promote benchmark scientific claim
```

String literals are not subjected to F04 because the authority contract may
quote forbidden-scope atoms. `random` is deliberately not in the registry
because `RANDOM_SOURCE` is a lawful deterministic projection; randomness is
instead excluded by F01, F02, F03, full call resolution, and absence of an
input or entropy surface. A syntactic F04 hit always fails, but an empty hit
list is only one conjunct and is not represented as a general security proof.

The receipt records every import edge, dependency surface, CLI surface,
filesystem access, unresolved call, forbidden finding, and reachability edge;
empty inventories are explicit empty arrays, not omitted fields. `passed` is a
deterministic conjunction of the checks named in the schema. This is a narrow
static closure check for a five-file package, not a claim of sandboxing,
malware resistance, or proof against an adversarial Python interpreter.

## 4. Request, reviewer, freshness, and independence

Human governance creates
`research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v5/scope_audit.request.json`
after the implementation freeze. The request binds the change hash, this
contract hash, schema hash, manifest root, request ID, requester identity, and
creation time. SK10 must start in a new context after that request and bind the
request's exact bytes.

The request is an RFC-8785/JCS JSON object followed by exactly one LF, with no
other keys and exactly these fields:

```text
schema_version = 1
artifact_type = "feltcraft_scope_audit_request"
request_id = nonempty lowercase identifier
change_id = "chg_20260901_feltcraft_symbolic_kernel_v5"
architecture_change_sha256 = lowercase SHA-256
audit_contract_sha256 = lowercase SHA-256
scope_audit_schema_sha256 = lowercase SHA-256
diff_base_commit = lowercase full 40-hex Git commit
manifest_root_sha256 = lowercase SHA-256
requester_identity = nonempty UTF-8 string
implementation_author_identities = nonempty sorted unique UTF-8 strings
frozen_at = UTC RFC-3339 timestamp
created_at = UTC RFC-3339 timestamp
```

The corresponding receipt fields must equal the request fields byte-for-byte;
`review.request.sha256` is the raw-byte SHA-256 of that request.

The receipt names the reviewer and the implementation-author identities,
records session creation/start/completion times, and attests that the reviewer
did not author or modify any subject file and had no pre-request conversation
context. The reviewer identity must differ byte-for-byte from every declared
implementation-author identity. Times satisfy:

```text
frozen_at <= request_created_at <= context_created_at
          <= review_started_at <= review_completed_at
```

These are review provenance assertions, not cryptographic identity proof.
The receipt also binds one repository-relative identity-evidence record by
path and raw-byte SHA-256 and labels it `human_attestation` or
`process_session_record`. Human governance must judge whether the record, named
reviewer, and process are in fact fresh and independent; schema validity alone
cannot establish that fact.

## 5. Audit visibility and terminal use

V5 must add the following exact information items to its visibility product:

```text
audit.contract_bytes_and_sha256
audit.schema_bytes_and_sha256
audit.repository_and_recursive_root
audit.diff_base_and_changed_paths
audit.frozen_file_bytes
audit.per_file_manifest
audit.manifest_root_sha256
audit.import_resolution_closure
audit.dependency_closure
audit.cli_options_hooks_closure
audit.forbidden_rule_registry
audit.capability_and_reachability_closure
audit.review_request_bytes_and_sha256
audit.reviewer_identity
audit.reviewer_freshness_evidence
audit.reviewer_independence_evidence
audit.scope_audit_receipt
```

The first sixteen items are visible only to
`SK10_EXTERNAL_SCOPE_AUDITOR` and `HUMAN_GOVERNANCE_REVIEW`; they are forbidden
to all five runtime nodes (including each SKN03 projection principal). The
receipt is `derived_only` at SK10, visible to human governance, and forbidden
to every runtime node. Every item is permanently forbidden to a successor
renderer, life, agent, model, tokenizer, DREAM/SLEEP/memory, LoRA, GPU/remote,
benchmark, promotion, or scientific-claim stage. SK10 and human governance are
external stages, not nodes or edges in the five-node runtime graph.

## 6. Real ratification binding

There is no valid `ratification.change_sha256` field. The strict ratification
schema forbids it. V5 visibility and authority text must instead name the
actual chain validated by `architecture_intake.py`:

```text
ratification.change_id
  == intake.change_id
  == consensus.change_id
  == change.change_id

ratification.consensus_sha256
  == SHA256(consensus bytes)

consensus.architecture_change_sha256
  == SHA256(change bytes)

ratification.human_required_state_sha256
  == SHA256(exact paused intake-state bytes)

paused_state.artifacts.architecture_change.sha256
  == SHA256(change bytes)
paused_state.artifacts.architecture_consensus.sha256
  == SHA256(consensus bytes)

approval_transition.source_state_sha256
  == ratification.human_required_state_sha256
approval_transition.artifact_sha256
  == SHA256(ratification bytes)
```

The corresponding visibility item IDs are exactly:

```text
authority.ratification.change_id
authority.ratification.consensus_sha256
authority.consensus.change_id
authority.consensus.architecture_change_sha256
authority.ratification.human_required_state_sha256
authority.paused_state.artifacts.architecture_change.sha256
authority.paused_state.artifacts.architecture_consensus.sha256
authority.approval_transition.source_state_sha256
authority.approval_transition.artifact_sha256
authority.ratification.authorized_scope
authority.ratification.forbidden_scope
authority.scope_proposal.requested_scope
authority.scope_proposal.forbidden_scope
```

These authority items are visible to `SKN01_AUTHORITY`, SK10, and human
governance; they are forbidden to SKN02--SKN05 except for the already-declared
immutable constants released by SKN01 on an exact valid chain. They are not
audit-subject source inputs and do not weaken the separate audit visibility
rule in section 5.

The validator also requires one approval transition, revalidates the full
change/interpretation/critique/consensus chain, rejects a non-releasable
consensus, binds authorization-evidence bytes and excerpt, and requires exact
ratification scope equality with `scope_proposal.json`. The visibility items
must expose these real fields and derivations rather than infer a nonexistent
shortcut. None of this implies that a v5 ratification currently exists.

## 7. Unresolved before any audit

The v5 change hash, audit-contract hash, schema hash, diff-base commit, frozen
manifest, review request, reviewer identity, and review times do not yet
exist. They must be filled only from future exact bytes after a releasable
consensus and separate human ratification. This document neither predicts an
audit pass nor supplies approval.

Draft-2020-12 JSON Schema validates structure, constants, pass/fail branches,
and exact passing inventories, but it cannot itself hash files, recompute the
binary manifest root, compare duplicate fields, order timestamps, or prove
that two real identities are independent. A future SK10 evaluator must perform
those contract checks and set the corresponding booleans; no such evaluator
is designed or authorized here. Human governance must review that evidence.
