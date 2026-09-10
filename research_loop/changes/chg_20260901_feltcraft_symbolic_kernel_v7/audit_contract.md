# FeltCraft v7 external scope-audit contract

Status: governance proposal only. This document authorizes no implementation,
test, kernel run, audit run, review, receipt, compute, promotion, benchmark, or
scientific claim.

## 1. Exact subject and fixed bindings

SK10 is a post-freeze governance audit of exactly these five repository files,
in this raw UTF-8 byte order:

```text
feltcraft_symbolic_kernel/__init__.py
feltcraft_symbolic_kernel/kernel.py
feltcraft_symbolic_kernel/report.py
feltcraft_symbolic_kernel/run.py
feltcraft_symbolic_kernel/test_kernel.py
```

The repository root is `.`, the recursive root is
`feltcraft_symbolic_kernel`, and the fixed full Git diff base is
`742f8bfa4bf4e530fdf264150bff962506fe449f`. The ratified V7 change binds the
architecture change, this contract, the request schema, and the receipt schema
by repository path and SHA-256. No artifact embeds or self-binds its own hash.

The five frozen files, their sizes/hashes, manifest root, request bytes and
identity fields, authors, timestamps, reviewer evidence, findings,
attestations, receipt, and disposition are future evidence. V7 predicts none.

## 2. Exact deterministic subset

The deterministic tier performs only the following mechanically specified
operations. No broader inference is part of this tier.

1. Check fixed binding field equality against the ratified V7 context.
2. Resolve the recursive root without following symlinks and require its
   complete recursive entry set to equal the five listed real regular files.
   Reject any extra entry or directory, symlink, device, deletion, case
   collision, invalid UTF-8 path, absolute path, empty segment, `.` segment, or
   `..` segment. Bind every raw file byte sequence by path, byte length, and
   SHA-256.
3. For each entry in raw UTF-8 path order encode

   ```text
   uint32be(len(path_utf8)) || path_utf8 || uint64be(size) || sha256_raw32
   ```

   and hash `b"feltcraft-scope-manifest-v1\0"` followed by their concatenation.
   Require the recomputed manifest rows and root digest to equal the receipt.
4. With rename detection off, union the NUL-delimited paths from
   `git diff --name-only -z --no-renames
   742f8bfa4bf4e530fdf264150bff962506fe449f --
   feltcraft_symbolic_kernel` and `git ls-files -z --others
   --exclude-standard -- feltcraft_symbolic_kernel`; reject deletions and
   require discovered, changed, and manifested path equality.
5. Require `scope_audit.request.json` to be canonical RFC 8785 JCS UTF-8 bytes
   plus exactly one LF and validate its parsed value against the exact
   `scope_audit_request.schema.json` bytes. That request value contains no own
   path or own hash. In the later receipt require
   `request_binding.path` to equal the fixed request path,
   `request_binding.sha256` to equal SHA256(the exact request-file bytes), and
   `request_binding.content` to equal the parsed request value byte-
   equivalently: JCS(content)+LF equals the exact request-file bytes.
6. Require timestamp order
   `frozen_at <= request.created_at <= context_created_at <=
   review_started_at <= review_completed_at <= adjudicated_at`.
7. Decode each subject as UTF-8 and require
   `ast.parse(source, filename=path, mode="exec", feature_version=(3,9))`
   to succeed.
8. Walk the parsed trees and inventory literal `ast.Import` and
   `ast.ImportFrom` nodes only. Emit one row per alias in node order and alias
   order. Reject `*`. For `Import`, classify the literal `alias.name`. For
   `ImportFrom` with `level=0`, classify the literal `module`; it must be
   non-null. For `level>0`, let the importing package be
   `feltcraft_symbolic_kernel`, require `level=1`, and form the base literal as
   `feltcraft_symbolic_kernel` when `module is None`, otherwise
   `feltcraft_symbolic_kernel + "." + module`. If `module is None`, append
   `"." + alias.name` before classification; otherwise classify the base
   literal and record the alias name without treating it as a module. A local
   literal equal to `feltcraft_symbolic_kernel` maps to
   `feltcraft_symbolic_kernel/__init__.py`; a local literal beginning
   `feltcraft_symbolic_kernel.` maps by replacing dots in its suffix with `/`
   and appending `.py`. Every mapped target must be one of the five fixed
   paths. For a nonlocal literal, its first dotted component must be exactly
   one of `collections`, `fractions`, `itertools`, `json`, `pathlib`, or `sys`.
   Any other literal, relative level, null absolute module, or unresolved local
   target fails. The receipt records source path, node line/column, kind,
   literal module/name/level, classification, and resolved local path if any.

This deterministic tier makes no forbidden-AST, CLI, input-source, file-effect,
capability, reachability, security, or full Python semantics judgment.

## 3. Separate request-file grammar and later receipt

The future request path is exactly
`research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v7/scope_audit.request.json`.
Its content validates against `scope_audit_request.schema.json` and consists
only of request identity, V7 binding hashes, fixed diff base, frozen manifest
root, requester and implementation-author identities, `frozen_at`, and
`created_at`. It has no `path`, `sha256`, `request_path`, or `request_sha256`
field.

The later `scope_audit.json` validates against `scope_audit.schema.json`. Its
`request_binding` separately supplies the fixed request path, exact byte hash,
schema-validation/JCS results, and a copied request `content` value. Receipt
validation requires exact equality between copied request fields and the
receipt subject/bindings plus byte equivalence as defined above.

## 4. Fresh independent human source review

After freeze and request creation, a reviewer begins in a fresh context, is
identity-distinct from every implementation author, and authored and modified
none of the five paths. The reviewer reads the exact frozen bytes and judges
all semantic matters excluded from the deterministic tier, including:

```text
all forbidden AST matching and aliases
all CLI, argument, option, alternate-entrypoint, stdin, environment, and configuration behavior
all dynamic import, reflection, callback, context-manager, plugin, and dormant-branch behavior
all filesystem effects and exact-success-byte allowed-write equivalence
all capability and reachability questions
all other semantic Python scope judgments against the eight forbidden atoms
```

The reviewer records findings and unresolved ambiguities and explicitly
attests freshness, independence, exact reviewed bytes/paths, review of every
forbidden atom, and semantic equivalence of the sole optional filesystem effect
to `Path("golden_report.json").write_bytes(exact_success_bytes)`. Any ambiguity
or false attestation prevents pass.

Human governance separately records evidence and explicit attestations that it
accepts the deterministic checks, request binding, freshness/independence, all
semantic source-review dispositions, allowed-write disposition, and governance-
only terminality. `passed=true` requires every deterministic boolean, every
fresh/independent reviewer attestation, no finding or ambiguity, and every
explicit human adjudication boolean. This is governance evidence only, not a
complete static/dynamic/capability/security proof or scientific evidence.

## 5. Visibility and terminality

Authority sees only real context path/hash/scope/ratification metadata; it does
not read audit contract/schema bytes, request bytes, receipt bytes, subject
bytes, reviewer evidence, or adjudication. Contract, request-schema, and
receipt-schema byte payloads are visible only to SK10 and human governance.
Request bytes, their later path/hash metadata, copied content, frozen subject
bytes, manifest, reviewer evidence, findings, attestations, adjudication, and
receipt are forbidden to SKN02/SKN03/SKN04/SKN06/SKN05 and to every renderer,
life, agent, model/provider/tokenizer, DREAM/SLEEP/memory, LoRA/weights,
GPU/remote, benchmark, promotion, paper, or scientific stage. No audit input or
output enters runtime, and no runtime or audit output enters successor science.
