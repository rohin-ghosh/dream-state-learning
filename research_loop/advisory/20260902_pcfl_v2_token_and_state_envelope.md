# PCFL-Compose v2 token and state envelope

**Date:** 2026-09-02  
**Status:** advisory-only resource formalization. This document does not edit
or ratify v1, create or approve v2, authorize implementation, or authorize
CPU/model/GPU/network work.

## Bound basis and disposition

This envelope starts from the exact staged roster in
`20260902_pcfl_v2_roster_adjudication.md`, SHA-256
`471d001b76963ab7bd3032cc535f9c4ce733cc2a002c985aaab19d45803a9066`,
and these v1 operation/state contracts:

- `resource_manifest.md`, SHA-256
  `0c62cc8c68bcacfea9ad6e6ef4df30670f8128e38d52ad72e72965257cefe8f5`;
- `resolver_reducer.md`, SHA-256
  `78da30f7d720492f0bf88d438c4c49b3284ae5368a61bdd7e72bc96fbe9aff23`;
- `semantic_contract.md`, SHA-256
  `68709bc1d07d4d719e4763ab1db1f70ec5c71d29783380e8592aed4d7f722a77`;
- `semantic_dsl.schema.json`, SHA-256
  `4d3b78852e704a69b318767e0b38b4e574102b53984d179927aca8eb66147ce2`.

The v1 resource numbers cannot simply be scaled by `3,414 / 8,228`. Its
terminal COMMIT operation cannot repeat a permitted 8 KiB candidate or 16 KiB
two-candidate commitment under 256 generated tokens, Think has no explicit
per-operation output cap, JSON Schema `maxLength` is not a UTF-8 byte bound,
and the complete rendered live-state maxima are absent.

The minimum coherent v2 repair is:

1. content-address model-authored staged nodes and candidate objects;
2. make PREDICT select an ordered manifest of already-authored staged nodes;
3. make COMMIT confirm content addresses rather than repeat payloads;
4. keep the v1 Dream-1/Dream-2 cumulative entitlements of 8,192/4,096 tokens;
5. bind recurrent Think to 512 generated tokens per invocation;
6. bind every serialized component and full rendered input by bytes and by the
   pinned tokenizer; and
7. stop before GPU if maximum legal fixtures do not fit without truncation.

Under those conditions, the recommended exact scientific ceiling is 3,414
model calls, 1,709,056 output tokens, and 57,775,104 combined input-plus-output
tokens. With no more than two permitted infrastructure replays, the process
ceiling is 3,416 calls, 1,740,800 output tokens, and 57,872,384 combined tokens.
These are cap arithmetic, not expected use.

## 1. Canonical bytes, Unicode, and content addressing

### RFC 8785/JCS profile

V2 should bind one named implementation of RFC 8785 JSON Canonicalization
Scheme and its source hash. The accepted scientific object is the result of
exactly one parse-and-canonicalize boundary:

1. accept valid UTF-8 only, with no BOM or trailing non-whitespace bytes;
2. parse exactly one JSON object while rejecting duplicate property names,
   invalid or unpaired surrogates, non-I-JSON numbers, NaN, and infinity;
3. validate the operation-specific schema and cross-field rules;
4. serialize with JCS property ordering, ECMAScript string escaping and number
   rendering, and no insignificant whitespace; and
5. hash and retain those canonical UTF-8 bytes.

JCS does **not** normalize Unicode. Opaque NOTE text must not be NFC-normalized,
case-folded, or otherwise rewritten before its canonical envelope is hashed.
The lexical reader may derive a separately named NFC-plus-case-folded index
view under a pinned Unicode-data version, but that derivative never replaces
the stored bytes and is not the content-address identity.

All v2 byte caps must be measured on JCS bytes, not JSON Schema character
counts. A 256-code-point string can exceed 256 UTF-8 bytes, and control
characters, quotes, and backslashes can expand under mandatory JSON escaping.
The schema should retain human-readable `maxLength` checks only as secondary
guards and add runtime canonical-byte checks for every free string, record,
node, candidate, state, and response.

Required adversarial fixtures include ASCII, two/three/four-byte scalars,
combining sequences, canonically equivalent but byte-distinct strings,
characters whose case-fold expands, U+0000/control escaping, quote and
backslash escaping, duplicate keys, overlong/invalid UTF-8, and lone surrogate
escapes. Boundary fixtures at `cap-1`, `cap`, and `cap+1` canonical bytes must
show deterministic acceptance/rejection. NFC/case-fold index expansion must
have its own measured byte receipt and may not enlarge a model-visible reader
return beyond the original record cap.

### Content-addressed staging and COMMIT

Every accepted NOTICE/CONNECT/REVISE node is stored once under an address of
the form:

```text
sha256("pcfl-v2-staged-object\0" || object_type || "\0" ||
       uint64_be(jcs_byte_length) || jcs_bytes)
```

The exact domain string, type enumeration, length encoding, and lowercase-hex
rendering must be schema-bound. The registry retains the full JCS bytes; a
reference is never trusted without resolving it and checking type, length, and
hash.

PREDICT remains the model-owned staging decision. Instead of re-emitting up to
8,192 candidate bytes, it emits candidate ID, ordered staged-node references,
representation, confidence/uncertainty fields, exact A1/A2 or B1/B2
predictions, citations, and an optional bounded audit reason. The pure reducer
materializes the candidate deterministically from those already model-authored
objects, validates the 4,096-byte payload and 8,192-byte complete-candidate
caps, and registers the resulting candidate address. It neither creates a
note/record nor selects an address.

DREAM1 COMMIT emits only the ordered one-or-two candidate addresses plus their
IDs and canonical byte lengths. DREAM2 COMMIT emits only the staged decision
address plus its parent addresses and length. The reducer resolves each
address against the current staged state and terminally binds that exact
object. A missing, stale, reordered, mismatched, or unregistered address is a
charged failure. The standalone DREAM1/DREAM2 artifacts are then mechanical
envelopes over the resolved bytes and staged predictions.

This preserves model ownership: the model authored the nodes, ordered the
manifest, staged the predictions/decision, and emitted the terminal addresses.
It removes only redundant byte repetition. Merely hashing a large unseen
candidate outside the loop and asking the model to echo its hash would instead
transfer authorship to the harness and is not permitted.

One-shot Dream has no earlier staged-node registry. Its single response must
therefore carry its complete candidate object(s); the harness may address them
only after that response is accepted. Its maximum two-candidate DREAM1 and
one-candidate DREAM2 fixtures must fit 8,192 and 4,096 output tokens
respectively under the pinned tokenizer. Content addressing must not be used to
pretend those bytes were already visible. If adversarial Unicode makes either
maximum legal one-shot artifact too large, the v2 author must reduce and
rejustify the candidate/free-text byte cap or raise both recurrent and one-shot
phase entitlements and recompute every total. The arm may not receive a
typical-text exemption.

Maximum-size end-to-end fixtures must prove that two 8,192-byte DREAM1
candidates and one 8,192-byte DREAM2 candidate can be staged, addressed,
committed, resolved, and reconstructed under the terminal cap. Hash collision
is not treated as object equality: the registry always verifies the retained
bytes at resolution.

## 2. Per-operation and phase output caps

Use operation-specific response schemas so irrelevant v1 fields are omitted
rather than serialized as large null/empty structures. Charge the model call
and exact raw response tokens before parse, as in v1. A malformed response
uses the registered malformed allowance and cannot receive a larger retry.

| Parsed operation class | Maximum accepted response tokens | Required shape |
|---|---:|---|
| READ | 512 | One typed handle or bounded LEXICAL/AST query; never a reader result |
| NOTICE / CONNECT / cognitive REVISE | 512 | One content-addressable node and bounded reason |
| PREDICT | 2,048 | Compact candidate manifest/decision, addresses, predictions, and bounded audit fields; no repeated node/candidate payload |
| PASS | 256 | Minimal operation/reason |
| COMMIT / ABSTAIN | 256 | Content-address manifest or empty terminal decision |
| THINK USE / LOCK | 256 | One legal public action or terminal lock |

The operation is not known until the response is parsed, so the server cannot
apply the table as a prospective generation limit. Each recurrent Dream call
instead sets `max_new_tokens = min(2,048, phase_tokens_remaining)`; each
recurrent Think call sets `max_new_tokens = 512`. After parsing, the reducer
enforces the smaller operation-specific acceptance cap in the table. A
malformed Dream response may therefore consume up to 2,048 tokens and a
malformed Think response up to 512, all charged against the phase/trajectory
and global totals. Output that reaches the server cap without one complete
valid object is a failure; there is no truncation-and-parse path. One-shot
calls use their phase/trajectory entitlement directly as `max_new_tokens`.

The v1 cumulative phase caps remain the controlling scientific entitlements:

| Phase | Calls | Cumulative generated-token cap |
|---|---:|---:|
| Recurrent Dream-1 | at most 32 | 8,192 |
| Recurrent Dream-2 | at most 16 | 4,096 |
| One-shot Dream-1 | exactly one | 8,192 |
| One-shot Dream-2 | exactly one | 4,096 |
| Recurrent Think D1 goal twin | at most 10 | 5,120 (`10 x 512`) |
| Recurrent Think D4 goal twin | at most 31 | 15,872 (`31 x 512`) |
| Structured one-shot Think D4 goal twin | exactly one | 15,872 |

The one-shot Dream caps match the corresponding recurrent phase's total output
entitlement. Structured one-shot Think matches its D4 iterative trajectory's
total output entitlement. These comparisons remain interaction-, input-,
call-, latency-, and FLOP-unmatched.

The parsed-operation caps and phase cap are both binding. It is intentionally
not legal for every operation in a maximum-length Dream trace to consume its
individual maximum: later calls receive only the remaining phase entitlement.
Executability means that maximum legal nodes/candidate manifests and the
content-addressed terminal fit their own operation caps, and that the golden
32-/16-step traces reach terminal without exceeding the cumulative cap. It
does not mean reserving the sum of mutually exclusive maxima.

## 3. Serialized object and live-state ceilings

The v2 schema should enforce these proposed canonical JCS-byte maxima before
tokenization:

| Object/component | JCS-byte maximum |
|---|---:|
| One opaque NOTE text value or one canonical AST record | 256 |
| One live workspace node, including ID/op/premises/content | 512 |
| Sixteen live workspace nodes | 8,192 |
| One canonical notes or symbols-plus-records payload | 4,096 |
| One complete candidate | 8,192 |
| Two retained candidate objects in the content store | 16,384 |
| One candidate address/manifest summary | 512 |
| Two live candidate summaries | 1,024 |
| Staged predictions/decision/addresses | 2,048 |
| One raw public event object | 2,048 |
| DREAM1 raw-event read receipt | 2,560 |
| DREAM2 candidate-package read receipt | 8,704 |
| Think NOTE/record read receipt | 1,024 |
| Typed handle catalog | 4,096 |
| Hashes, counters, action state, and terminal status | 4,096 |

The per-note/record limit is on the full canonical value named by the contract,
not its apparent character count. The 8,192-byte candidate maximum includes
predictions and audit fields. Content-store bytes are retained artifacts but
are not automatically repeated inside every live prompt.

From those component limits, bind these whole-tuple maxima:

| Live state tuple | Maximum canonical bytes | Dominant resident objects |
|---|---:|---|
| Dream-1 | 24,576 | workspace, two summaries, predictions, one event receipt, catalog, counters/hashes |
| Dream-2 | 32,768 | workspace, summaries/decision, one full candidate receipt, catalog, counters/hashes |
| Think | 16,384 | workspace, one record receipt, eligible-store summary, action state, counters/hashes |

The content store itself is addressed outside the live tuple. A prompt may
show full bytes only when the contract makes them currently visible: live
workspace nodes, a charged read result, or the full eligible packet in a
registered one-shot arm. It may not use content addressing to hide model-visible
information, nor dereference every address without a charged read.

## 4. Maximum complete input fixtures

Every input limit applies after exact chat-template rendering, including system
text, operation schema, public objective, current state, tool/result framing,
and generation prompt. The following are proposed maximum UTF-8 byte fixtures,
not substitutes for tokenizer counts:

| Invocation | Full rendered UTF-8 bytes | Model-input token cap |
|---|---:|---:|
| Recurrent Dream-1 | 49,152 | 16,384 |
| Recurrent Dream-2 | 65,536 | 16,384 |
| Recurrent Think | 49,152 | 16,384 |
| One-shot Dream-1 | 65,536 | 32,768 |
| One-shot Dream-2 | 81,920 | 32,768 |
| Structured one-shot Think | 49,152 | 32,768 |

The larger Dream-2 fixture allows one charged 8,192-byte candidate read; the
one-shot Dream-2 fixture allows all eligible raw events and both candidate
objects. The one-shot Think fixture includes the presealed structured packet
and target packet, but no opaque corpus.

These limits are jointly feasible only if the pinned model configuration
admits the largest input-plus-output request without truncation. Under the
proposed caps that is structured one-shot Think:
`32,768 + 15,872 = 48,640` tokens. The pre-GPU receipt must therefore show a
configured context capacity of at least 48,640 tokens, with input counts
including all chat-template special tokens. If the pinned deployment cannot
provide that capacity, v2 must reduce the disclosed packet/output entitlement
through a new deliberated design or be `NOT_RUN`; it may not truncate.

## 5. Deterministic pre-GPU tokenizer and maximum-fixture gate

Exact token counts cannot be derived from byte caps or average characters per
token. They require the exact v2 prompts, schemas, constructed public packets,
chat template, and tokenizer files, none of which this advisory executes.

Before any model/GPU action, a CPU-only deterministic gate should:

1. hash the model revision, every tokenizer vocabulary/merge/config file, chat
   template, tokenizer library, JCS implementation, and Unicode-data version;
2. render one maximum legal fixture for every `(mode, representation,
   operation)` and every one-shot mode, including all fixed framing;
3. include fixtures maximizing each component separately and jointly: 16 live
   nodes, two maximum candidates, maximum candidate read, catalogs, targets,
   citations, queries, reasons, counters, and action state;
4. run the Unicode/JCS adversarial set above, including maximum escaping and
   reader-normalization expansion, while preserving the opaque stored bytes;
5. apply the exact chat template once, tokenize with truncation disabled, and
   record input IDs, token count, rendered bytes, and round-trip diagnostics;
6. tokenize maximum valid output fixtures for every operation and full
   one-shot artifact; prove they fit the operation and phase caps;
7. render golden maximum-length 32-step Dream-1, 16-step Dream-2, 10-step D1
   Think, and 31-step D4 Think traces and verify state growth, remaining-token
   arithmetic, terminal content-address resolution, and no hidden payload
   repetition;
8. verify the tokenizer's byte-fallback/normalization behavior rather than
   assuming tokens are bounded by UTF-8 bytes; and
9. emit one machine-readable receipt containing each maximum, the winning
   fixture hash, per-assignment caps, aggregate sums, and a pass/fail bit.

The fixtures must be generated from schema/runtime bounds, not handpicked
typical prose. A boundary failure blocks v2. It cannot be repaired by dropping
an assignment, shortening a realized model output after inspection, changing
Unicode, or raising a cap without producing new v2 bytes and re-deliberation.

## 6. Exact staged-roster arithmetic

The 3,414 scientific calls decompose as follows:

| Class | Phase/trajectory count | Calls | Output-token ceiling |
|---|---:|---:|---:|
| Recurrent Dream-1 | 8 phases | 256 | `8 x 8,192 = 65,536` |
| Recurrent Dream-2 | 14 phases | 224 | `14 x 4,096 = 57,344` |
| One-shot Dream-1 | 2 phases | 2 | `2 x 8,192 = 16,384` |
| One-shot Dream-2 | 2 phases | 2 | `2 x 4,096 = 8,192` |
| **All Dream** |  | **484** | **147,456** |
| Recurrent Think D1 | 26 trajectories | 260 | `260 x 512 = 133,120` |
| Recurrent Think D4 | 86 trajectories | 2,666 | `2,666 x 512 = 1,364,992` |
| **Recurrent Think** |  | **2,926** | **1,498,112** |
| Structured one-shot Think D4 | 4 plans | 4 | `4 x 15,872 = 63,488` |
| **Scientific total** |  | **3,414** | **1,709,056** |

The Dream phase counts follow directly from the staged roster: six recurrent
Dream-1 phases and twelve Dream-2 continuations for the three opaque forks,
plus two Dream-1 and two Dream-2 phases for the factor/independent AST cells;
the two one-shot sides each add one Dream-1 and one Dream-2 call.

Use 16,384 input tokens for each of the 3,406 recurrent calls and 32,768 for
each of the eight one-shot calls:

```text
scientific input ceiling
  = 3,406 x 16,384 + 8 x 32,768
  = 55,803,904 + 262,144
  = 56,066,048 tokens

scientific output ceiling
  = 147,456 + 1,498,112 + 63,488
  = 1,709,056 tokens

scientific combined ceiling
  = 56,066,048 + 1,709,056
  = 57,775,104 tokens
```

The exact call stops should be **484 Dream calls**, **3,414 scientific model
calls**, and **3,416 total process model calls**. EXACT_PROGRAM is CPU work and
adds zero model calls. There is no A-MEM reserve and no discretionary 3,600-call
pool in this exact staged envelope.

At most two exact-input infrastructure replays are allowed, and neither
replaces its scientific row. The largest permitted replay reservation is a
structured one-shot Think call:
`32,768 input + 15,872 output = 48,640` tokens. Reserving that maximum twice
gives:

```text
process input ceiling    = 56,066,048 + 65,536 = 56,131,584
process output ceiling   =  1,709,056 + 31,744 =  1,740,800
process combined ceiling = 57,775,104 + 97,280 = 57,872,384
```

Recommended exact ledger stops are those values. For a simple outer watchdog,
the safe proposal caps are **1,750,000 output tokens** and **58,000,000
combined input-plus-output tokens**. They are rounded above the exact process
maxima and do not rely on average output length or average tokens per byte.
Unused headroom cannot be reassigned to new scientific cells.

If the tokenizer gate yields smaller exact per-mode input maxima, v2 may bind
the smaller aggregate obtained by summing those predeclared maxima across the
assignment ledger. It may not claim that lower average realized use is the
worst-case cap. If any maximum fixture exceeds 16,384/32,768 input tokens or an
operation/phase output cap, the proposed 58-million envelope is not executable
and v2 remains unratifiable until its bytes and arithmetic change.

## 7. Device, wall, memory, and artifact envelope

Using only v1's retained planning anchors, 480 recurrent Dream calls scale to
about 4.45 occupied device-hours and 2,926 recurrent Think calls to about 3.36
hours. One-shot work, model loading, longer maximum input allowance, logging,
and 25% overhead make **10--14 occupied device-hours** a conservative schedule
estimate for a successful staged path. Reserve **18 device-hours** and **24
wall-hours** as proposed stops, one H100 NVL or GH200 at a time, and retain the
v1 50-GiB artifact ceiling.

This estimate is not a throughput proof and the token, device, and wall stops
are competing limits. Before ratification, the author should use retained
hardware throughput distributions and the exact tokenizer receipt to show
that the complete roster has adequate margin; otherwise raise the declared
time envelope before results exist. During execution, whichever hard limit is
reached first stops the stage without downsampling or truncation.

All input/output bytes, token IDs/counts, JCS objects, staged-object registry
entries, hashes, live states, reader derivatives, response failures, latency,
occupancy, and terminal rows remain append-only or content-addressed. No
resource headroom dispatches another stage.

## Final recommendation

V2 should bind the content-addressed staging protocol, operation-specific
schemas, 8,192/4,096 Dream phase caps, 512-token recurrent Think calls,
16,384/32,768 input caps, and maximum serialized fixtures as one inseparable
contract. The resulting safe staged envelope is 3,414 scientific calls and
3,416 process calls, with exact worst-case process ceilings of 1,740,800 output
tokens and 57,872,384 combined tokens.

Those numbers become executable only after the deterministic CPU tokenizer,
JCS/Unicode, content-address, live-state, and full-render fixture gate passes.
This advisory neither performs that gate nor authorizes a run.
