# PCFL offline opaque qualification — EDITSTOP, 2026-09-13

**New owned source/tests frozen. Algorithm implementation and bounded CPU tests
only; no production tokenizer qualification, complete production render claim,
model readiness, or scientific result.**

Only these newly assigned paths were authored:

- `organism_v6/pcfl_tokenizer_qualification.py`
- `tests/test_pcfl_tokenizer_qualification.py`
- `/tmp/astra_pcfl_tokenizer_qualification_handoff_20260913.md`

AGENTS, nested-instruction absence, assigned-file absence and Git status were
checked before writes. No commit/push/pull, network/download, native/model/GPU
call, tokenizer loading, or change to another agent's files. Main and other
agents continued editing/committing unrelated work; it was not reverted.
Preparer/core were not edited and retained their assignment-start hashes:

- preparer: `e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4`
- core: `03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f`

## Frozen source/tests and commands

| Path | SHA-256 |
|---|---|
| `organism_v6/pcfl_tokenizer_qualification.py` | `da30eb90a8655ec0707dd8c83c22ed08f1032dadb7a663edd7102774e0e84d3a` |
| `tests/test_pcfl_tokenizer_qualification.py` | `30b057078522cc5d0c2396749fb22d529f9935cb6d484eb610e26d1a445004be` |

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_pcfl_tokenizer_qualification.py -q
# 23 tests PASS; final repeat 0.137 seconds
git diff --check -- organism_v6/pcfl_tokenizer_qualification.py tests/test_pcfl_tokenizer_qualification.py
sha256sum organism_v6/pcfl_tokenizer_qualification.py tests/test_pcfl_tokenizer_qualification.py organism_v6/pcfl_vertical_prepare.py organism_v6/pcfl_vertical_dev.py
```

Also ran `ast.parse`, in-memory `compile`, trailing-whitespace checks and
import inspection on both owned Python files: PASS. Implementation imports only
`base64`, `dataclasses`, `hashlib`, `json`, and `re`; it does not import the
preparer, core, tokenizer libraries, subprocess, networking, or a model stack.

Tests cover exact source pins, the existing `E_3TGT3U43QK` golden candidate,
seed derivation, strict namespace/width/alphabet, structural rather than lexical
order, all seven roots/namespaces, fixed public limits, a real 4096-entry
synthetic pool, reserved-candidate receipts, minimum feasible L, first DFS
solution and backtracking, an independent 27-vector Cartesian oracle, global
collision pruning, all required-class/slot coverage, strict 511/512 boundary,
unequal training lengths, no obsolete PAD, deterministic replay, hash/token/
context tampering, streaming sink failure, encoder failure, exhaustion, and
input/callback mutation isolation. Tests invoke only pure Python synthetic
encoders. Their returned token IDs are logged exactly, not represented as real
Qwen tokenizer evidence.

## Public API

```python
qualify_opaque_ids(bindings, encode, tokenizer_pins, *, receipt_sink=None)
verify_qualification(result, bindings, tokenizer_pins, receipts=None)
seed(label)
opaque_candidate(root, namespace, index, salt)
validate_identifier(value, namespace)
canonical(value)
digest(value)
```

`encode(text)` is supplied by the caller and returns the actual nonempty
`list[int]` token IDs. Tokens must be nonnegative integers, not Booleans.
The caller's offline adapter must disable added specials and truncation.
Training texts are already complete serialized chat-template/assistant/EOS
texts supplied through typed parts. This module never constructs an assumed
chat template, silently adds EOS, loads a tokenizer, or downloads files.

The public search has **no** pool/length/salt knobs. Limits are exactly:

```text
salt: 0..999999 inclusive
candidate pool: first 4096 locally admissible candidates per slot per L
L: 4,5,6,7,8,9,10,11,12
root order: excluded/0..3, disposable/0, dev/0..1
namespace order: node,port,event,link,probe,receipt,goal (N,P,E,L,Q,R,G)
within namespace: caller-frozen structural list index, never opaque spelling
```

Seeds and salt serialization match §5 and the core's existing allocator:
63-bit first-eight-byte big-endian SHA256 of `PCFL-V2.1-PREP\0` plus the ASCII
domain; master seed domain is `opaque/{root}`. Candidate hash uses the unsigned
eight-byte master seed, NUL-separated semantic namespace name, decimal
structural index and decimal salt. Namespace hash bytes are `node`, `event`,
etc., **not** an alternate prefix-letter encoding. The prefix letter plus
underscore and first ten RFC-4648 base32 characters is exactly 12 ASCII bytes.

For each L, complete every slot's 4096-entry pool in slot/salt order. If a pool
cannot reach 4096 within the salt ceiling, that L is infeasible; do not use a
smaller pool. The next explicitly registered L may then be tried. Within L,
iterative DFS tries the salt vectors in fixed lexicographic traversal, prunes
global uniqueness/substrings and every newly fully-instantiated substitution
class or training sequence, and accepts the first complete solution. It uses
no heuristic, score, hidden bit, answer, model output, random state or redraw.
An impossible literal-only constraint is rejected before candidate search.

Private `_Limits`/`_qualify(..., synthetic=True)` permit bounded synthetic unit
tests of the exact same algorithm. They label all results `synthetic_test=True`.
Any weakened limits in non-synthetic mode fail. These internals are not an
alternative production interface.

## Exact closed caller schema

`bindings` has exactly:

```text
schema source_pins tokenizer_pins root_slots reserved_literals substitutions
training_sequences required_training_ids render_registry_sha256
```

- `schema = "pcfl.opaque_qualification.v1"`.
- `source_pins` equals the module's three exact SHA256s for the production
  binding memo, retained prospective register and v2.2 writer repair. The
  tests compare these to local source bytes. Runtime inputs cannot substitute
  a differently pinned rule set.
- `render_registry_sha256` identifies the caller's frozen concrete render
  registry. The module cannot certify its semantic completeness from a hash.
- `tokenizer_pins` is also supplied separately as the observed adapter pins;
  exact mismatch fails before any encoding. Its fields are
  `{revision, files, chat_template_sha256, encoding_policy}`. Files are a
  nonempty filename→SHA256 map; revision is nonempty. Policy is exactly
  `preformatted_text_no_added_special_tokens_no_truncation`. These are caller
  declarations; loaded file/template provenance remains externally verified.

### Root and slot manifest

`root_slots` is a list of `{root, namespaces}` objects in exact root order.
Production requires all seven roots and all seven namespaces per root.
Each namespace value is a nonempty ordered list of unique structural names.
List order defines the index entering the candidate hash. The input dictionary
insertion order does not define namespace order. No fixed D topology, probe
receipt slots or goal visibility is invented to fill this manifest.

Do not assume the current core's provisional slot inventory is the final
production manifest. Main still must bind the missing D/probe semantics and
complete the actual production slot/render coverage before a production use.

### Reserved literals

`reserved_literals` has exactly four list fields:

```text
prompt_keywords canary_ids parser_prefixes other
```

The first three must be nonempty. `other=[]` explicitly means no additional
reserved literals; a missing field is not allowed. Entries are nonempty exact
text and duplicate-free within each category. Case is not normalized.

A candidate is rejected if it occurs within a reserved literal, or if a
prompt keyword/canary/other literal occurs within the candidate. Parser prefixes
are the deliberate exception to the latter direction: reserving `N_` must not
ban every valid node identifier. Candidate equality/containment *in* a reserved
parser literal still fails. This exact deterministic collision rule is exposed
in `_reserved` and tested; no keyword/canary corpus is guessed by the module.

### Substitutions and complete training text

`substitutions = {required, classes}`. `required` maps each of these six kinds
to a nonempty list of prospectively required class IDs:

```text
grammar_row query event_twin link_permute collision_render reachout_order
```

Every named class must appear exactly once, with the matching kind. Each class
is `{id, kind, members}` and has at least two members. This ensures a missing
query/twin/derangement/collision/RA-RB class cannot be silently omitted. All
declared slots must occur in substitution members; training-only occurrence
does not excuse missing substitution coverage.

Each member is `{id, parts}`. A part is **one** of:

```json
{"literal": "exact already-frozen text"}
{"slot": ["excluded/0", "node", "S_L"]}
```

Slot references must exist in the manifest. Member IDs are globally unique
across all classes and training sequences. Parts are concatenated literally;
there is no implicit join, formatter, solver choice or escaping policy. Unknown
parts/references, unresolved `{PLACEHOLDER}` text and obsolete `PAD_S1_`/
`PAD_S2_` literals fail. All members of a class must have equal observed token
counts once the entire class is instantiated. Counts are compared only within
that named substitution class.

`training_sequences` is a nonempty ordered list of the same `{id, parts}`
records. Its exact IDs/order must equal `required_training_ids`; missing,
reordered or extra sequences fail. Every fully rendered sequence must tokenize
to **<512** tokens; 512 fails, and no token IDs/text are truncated. Sequences
from different arms need not have equal length. No loss-active PAD or target
token equalizer is supplied by this code.

The registry manifest is caller-supplied authority over which concrete cases
are required. Structural completeness relative to that manifest is checked;
the module does **not** infer that the caller covered every real cube/render/
grammar/control/training state. That remains an explicit pending interface.

## Measurement receipts, failures and replay

Every actual `encode(text)` call emits an ordered receipt, including candidates
rejected by L, reserved literals or local duplicate filtering, rejected DFS
substitution attempts, and every accepted class/training sequence. Repeated
consideration is re-encoded and recorded; no fictional cached measurement is
inserted. A receipt contains:

```text
index previous_sha256 bindings_sha256 tokenizer_sha256 run_sha256
context text token_ids error sha256
```

Candidate context names root/namespace/structural slot/index/salt/L; other
contexts name class or training sequence and member. `token_ids` contains the
exact encoder return, copied before exposure to callbacks. `sha256` hashes all
other receipt fields. Chain head, count and each selected candidate/member's
receipt hash are reported. Bindings and run hashes seal the input manifest,
tokenizer metadata, search limits and synthetic mode.

Without a sink, the result retains the complete receipt list. With
`receipt_sink(record)`, records are streamed as detached objects and
`result.receipts=None`. **Use a durable streaming sink for a real large search**:
up to a million salts per slot/length is intentionally not a small transcript.
The module itself does no file I/O. Sink failure aborts with `QualificationError`
without retry or continuing with missing evidence.

Invalid/missing inputs raise `QualificationError` before encoding. Encoder
exceptions or invalid token-ID returns produce an error receipt and
`VS_ASSAY_INVALID`, with no retry. Exhausted fixed pools/lengths also return
`VS_ASSAY_INVALID`, preserving all accumulated receipts/attempts. Rejected or
partial assignments are not reported as an accepted inventory.

`verify_qualification` replays the complete recorded token-ID transcript
through the same deterministic traversal, checks text/context/hash-chain,
limits, source/tokenizer pins, salt vector and final result seal. It invokes
no actual tokenizer. Supply the external receipt list for streamed results.
It reports `transcript_and_search_verified=True`, but
`actual_encoder_provenance_verified=False`. Failed-encoder exception transcripts
are retained for review rather than having an exception fabricated during
replay. Keep an external immutable result hash to anchor transcript custody;
rewritten hashes alone do not prove actual tokenizer execution.

## Result boundary and still-missing interfaces

A successful algorithm result has
`status=QUALIFIED_FOR_SUPPLIED_REGISTRY`,
`qualified_for_supplied_registry=True`, the chosen L, nested
root→namespace→structural-slot inventory, salt vector/receipt references,
accepted check counts and immutable hashes.

It always also says:

```text
full_production_qualified=False
ready_for_model_calls=False
```

Pending: authoritative D and public probe-result semantics; the complete real
render registry and all scientifically required substitution classes; actual
loaded tokenizer file/chat-template provenance; and native execution release.
This new module does not change the preparer's explicit unresolved-D state.

These receipts are not a fabricated drop-in replacement for the preparer's
full tokenizer receipt: Main still must assemble actual view/token offset,
response mask, EOS and opaque-span evidence against the sealed full contract.
NLL grammar/content offset classification remains with the existing core;
it is not guessed from token counts here. No native tokenizer or scientific
qualification was executed by this sidecar, and no test asserts otherwise.

**EDITSTOP — only the newly assigned source/tests are frozen here.**
