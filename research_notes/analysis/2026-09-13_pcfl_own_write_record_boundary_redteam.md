# PCFL own-write record-boundary red-team after SEQ-169/170

**Date:** 2026-09-13 PT  
**Scope:** independent design review only; no runtime, parser, test, model, fit,
readout, or GPU change  
**Reviewed:** SEQ-169/170 receipts in `research_loop/COORDINATION.md`, the
record-boundary recommendation, formation driver/core/planner, scoped writer,
readout/scorer, and focused tests at repository HEAD

## Verdict

**The recommendation is directionally correct, but an EOS-payload change by
itself is not launch-ready.** The smallest scientifically honest repair is:

1. admit one exact **no-terminal-LF child payload** at an evidenced EOS/stop
   boundary;
2. preserve that payload and its token/byte receipts unchanged;
3. create a separately named **harness-serialized record** by adding exactly
   one LF, because the existing query compiler, trainer, and scorer all use
   LF-framed records; and
4. train and score the same serialized block bytes, while reporting payload
   exactness separately.

Do not use an optional-LF grammar. Do not simply remove `\n` from the current
regex and pass the resulting row into the current compiler. Do not run another
native formation until the still-hidden predeclared action/link choices are
also resolved prospectively.

This chooses **exogenous LF serialization** as the minimum implementation
repair. Fully converting the own-write stack to EOS-delimited/no-LF records is
conceptually clean but is not the smallest repair: the existing row validator,
multi-row block compiler, writer targets, and readout scorer are all explicitly
LF-based.

## Severity-ranked findings

### FATAL before another native attempt — the current stack cannot consume a raw no-LF row consistently

The current representation contract is end-to-end LF-bearing:

- `PATTERNS["EVENT"]` and `PATTERNS["LINK"]` require terminal LF;
- `_row` reparses and hashes that LF-bearing `raw`;
- `materialize_queries` concatenates row `raw` values directly;
- `_block_rows` requires a terminal-LF block and uses LF to separate the two-row
  `EVENTS_AT` blocks;
- the writer tokenizes `query["target"]` and then adds EOS; and
- readout compares the generation against that exact same target.

Consequently, changing only admission to accept SEQ-169/170's 90-byte payload
would either fail later validation or create ambiguous two-row blocks such as
`...R_xEVENT...`. The formation boundary, stored-row boundary, training target,
and readout target must be frozen together before fitting.

**Minimum prospective representation:**

```text
child_payload_raw = exact decoded UTF-8 response, no LF
storage_record    = child_payload_raw + U+000A
query_block       = concatenation of one or two storage_record values
training_target   = exact query_block, followed by the trainer's EOS target
readout_target    = exact query_block
```

For every admitted row, retain and bind:

- `child_payload_raw`, raw UTF-8 hash, raw hex, and native output token IDs;
- the captured `finish_reason`, `stop_reason`, and tokenizer EOS identity;
- `storage_record`, its UTF-8 hash and hex;
- `serialization_origin = HARNESS_RECORD_DELIMITER`; and
- a checked relation `storage_record == child_payload_raw + "\n"`.

The EOS/stop boundary must be evidenced by the native receipt; it must not be
inferred merely because decoded text ended. The preparation receipt should
measure the actual tokenization of both payload and serialized target. The fit
must verify the exact serialized target token IDs it uses, and readout must bind
the identical target hash. Appending LF can change tokenization at the boundary,
so a claim of "one added token" is not allowed unless the pinned tokenizer
measurement proves it.

### HIGH — the predeclared curriculum contains another likely fail-fast stop

The child is told to **choose** an available EXPLORE port and later to choose
one not-yet-recorded directly chained EVENT pair, but the driver rejects every
choice except the hidden presealed one.

On this fixed disposable root:

- EXPLORE opportunities 0 and 4 each expose two valid ports. Opportunity 0
  happened to match in SEQ-169/170; opportunity 4 has not been reached.
- The eight admitted events permit exactly four directed chained pairs:
  `(e0,e1)`, `(e1,e2)`, `(e3,e4)`, and `(e3,e7)`.
- The plan requires those four in one hidden order. At the first LINK call the
  public instruction permits any of the four, while the driver accepts only
  `(e0,e1)`; a different world-valid pair stops formation before admission.

That is not outcome cherry-picking, but it is a hidden action policy inside a
supposed free-choice prompt. It makes a complete formation depend on guessing
the harness's undisclosed curriculum order.

For the already bounded **controlled authentic child execution/recording**
claim, the smallest repair is to disclose the assigned public action at each
EXPLORE slot and the assigned pair at each LINK slot. The assignment may name
only already public ports and already child-authored EVENT handles; it must not
expose destinations, receipts before execution, routes, evaluation answers, or
private graph labels. Exact-match admission may then remain.

The scientifically stronger alternative is to accept any world-valid action
and any remaining directly chained pair and deterministically compile the
actual completed bank. That would test real child choice, but it is a larger
planner/schedule/provenance change and is not the minimum repair for this
storage diagnostic.

### MAJOR — `no normalization` remains true only at the evidence boundary

With exogenous serialization, these statements remain true:

> The native response is preserved byte-for-byte. Admission does not strip,
> append, repair, extract, retry, or normalize the child payload.

These statements become false and must be removed:

> Every supervised target is byte-identical to the complete child response.

> The full stored/read block is entirely child-authored bytes.

The truthful description is:

> Supervised blocks contain exact child-emitted, world-grounded semantic
> payloads under prospectively fixed harness record framing; the framing byte
> is separately receipted and contains no world fact or answer.

That framing does not contaminate the substantive memory content, but it is
still exogenous supervision. In particular, AUTH can learn the LF output habit
that C0 demonstrably lacks. The primary W8 strict endpoint may remain frozen,
because it requires the entire identifiers-and-relations block rather than LF
alone, but payload-only semantic equality should be reported beside it so the
format component is visible.

### MAJOR — an optional-LF regex is the wrong repair

Accepting both `payload` and `payload + LF` would make the child's row
representation depend on an incidental generation-tail choice. Without a
canonical serializer, multi-row joins remain ambiguous; with a canonical
serializer, optionality buys nothing and obscures which bytes were authored.
It also invites post-result discretion over whether raw, stripped, semantic, or
canonical equality is the endpoint. Select one public payload contract before
generation. The evidence from two identical EOS endings supports the no-LF
payload contract.

### MODERATE — the current recommendation's preferred EOS end-to-end option understates the multi-row problem

Keeping payload bytes unchanged all the way through training/readout would be
cleaner in principle, but the query compiler serves up to two rows at one
address. It therefore still needs a prospectively defined separator even if it
does not need a terminal delimiter. A full EOS-record rewrite would need a
separate own-write row type, an exact inter-row separator receipt, revised
block parsing/scoring, revised writer parity tests, and a newly frozen target
hash/reducer binding. That is valid future cleanup, not the minimum change for
this one-life diagnostic.

## Minimum prelaunch regression set

Before another native formation, the prospective version should prove on CPU:

1. exact no-LF EVENT and LINK payloads at a valid stop boundary admit;
2. payload plus LF, leading/trailing space, blank line, fence, prose, literal
   `\\n`, wrong field, and non-stop/length termination all fail admission;
3. the failed raw payload is always preserved and never rewritten;
4. every admitted row has dual payload/storage hashes and the exact one-LF
   serialization relation;
5. one-row and two-row query blocks serialize unambiguously and the scorer
   rejects missing, extra, reordered, or false rows;
6. writer encoding uses the registered serialized target plus EOS, with
   response-only loss, and readout scores the identical registered target hash;
7. assigned EXPLORE and LINK choices are visible in their prompts, contain no
   nonpublic outcome information, and any mismatch still stops without retry;
8. all 20 calls are required before fit; SEQ-169 and SEQ-170 remain immutable
   failures; and
9. the W8 reducer thresholds and one-life claim boundary are unchanged except
   for the explicit serialized-block wording.

## Prospective claim if the frozen reducer passes

Use:

> In one controlled curriculum life, a rank-8 LoRA trained on prospectively
> serialized memory blocks whose substantive rows were exact child-emitted,
> world-grounded payloads caused a cold-loaded model to reproduce most trained
> address-to-block mappings under one unseen query wrapper, while the unchanged
> base did not.

Do not say that the child selected the experiences, discovered the links,
authored every target byte, generalized to unseen facts/addresses, traversed a
graph, preserved unrelated capability, compressed experience, or established
the Dream--LoRA--Think loop.

## Bottom line

**REWORK, THEN ONE PROSPECTIVE DEV ATTEMPT.** Exogenous LF serialization is the
smallest honest repair because it leaves the existing LF-framed compiler,
training targets, scorer, and W8 reducer intact while separating model-authored
content from storage framing. But repairing only LF is likely to waste the next
attempt: the hidden predeclared EXPLORE/LINK choices should be made explicit in
the same prospective version, consistent with the already narrow controlled-
curriculum claim.
