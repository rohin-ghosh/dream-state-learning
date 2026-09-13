# PCFL own-write: record boundary after SEQ-169/170

**Date:** 2026-09-13  
**Scope:** design recommendation only; no runtime, parser, test, model, fit, or
GPU change by the watcher.

## Observed fact

In both SEQ-169 and the prospectively clarified SEQ-170, the child emitted the
same 90-byte EVENT payload with every required identifier correct, then emitted
EOS.  The only mismatch against the registered 91-byte wire representation was
the absent terminal LF.  SEQ-170 explicitly requested the LF, and the token
capture confirms that no transport layer removed it.  Both attempts correctly
failed under their frozen admission contract; neither may be rescored.

## Recommendation

Do not spend another native call trying to elicit an invisible transport
delimiter.  For a separately named prospective DEV version, define the public
model response as exactly one whole **record payload terminated by EOS**:

```text
EVENT <event_id> AT <source> DID <port> GOT <destination> EVIDENCE <receipt_id>
```

and analogously for LINK.  Full-match the entire raw response with no leading
or trailing whitespace and no normalization.  Preserve and hash those exact
child bytes.  If a ledger/file needs newline-delimited storage, the storage
layer may append its own LF, but it must record separately:

1. `child_payload_raw` and its hash;
2. `storage_record = child_payload_raw + LF` and its hash; and
3. an explicit `serialization_origin = HARNESS_RECORD_DELIMITER` receipt.

Training targets should use one prospectively chosen representation and say
which one.  The cleanest option for this diagnostic is the exact EOS-terminated
child payload, so cold readout asks for and scores the child's actual bytes.
If the canonical LF-terminated wire form is instead trained, the resulting
claim must say **endogenous semantic payload, exogenous record serialization**
rather than byte-exact child-authored storage.

This is not permissive parsing: `EVENT ...\n`, extra prose, multiple records,
wrong identifiers, missing fields, or any other trailing/leading byte still
fails.  It merely assigns record framing to the transport/storage layer, where
it belongs, instead of requiring the model to express an invisible file
delimiter immediately before EOS.

## What stays fixed

- Preserve SEQ-169 and SEQ-170 as immutable failures.
- Same selected disposable DEV root, predeclared actions/links, model, seed,
  call order, writer recipe, budgets, and fail-fast behavior.
- No fit until all 20 prospective formation calls pass the new contract.
- No output repair, stripping, newline insertion into child evidence, retry,
  resampling, or favorable-row selection.
- Keep the scoped one-life acquisition claim and the frozen W8 reducer; this
  repair creates no evidence for generalization, traversal, or learning yet.

## Separate limitation that remains

The formation curriculum predeclares the required EXPLORE actions and LINK
pairs and rejects other outputs, even if another output could be world-valid.
That is acceptable only for the already-bounded description **controlled
authentic child execution/recording**.  It is not autonomous exploration or
discovery and must remain outside the claim.
