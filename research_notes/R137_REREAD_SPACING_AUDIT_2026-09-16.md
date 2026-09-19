# Raw6 reread spacing audit — September16,2026

## Finding

The collapsed spaces are present in the child's native generated token IDs.
No renderer or eligible-target rewriting bug was found in the five audited
Selected Passages responses (records9,70,134,202,272). This does not establish
why the model generated them or that all renderer behavior is correct.

The branch remains **reread_select**: a prompt-guided copying invitation, not
a machine-verified extractive selector. Its compliance failed on these passages.
No live source, raw response, target, replay definition or adapter was changed.
Automatically inserting spaces would change child-authored evidence/targets,
not repair a demonstrated renderer defect.

## Exact trace

- REQUEST69 contains source RESPONSE67's `temperatures around`.
- RESPONSE70 instead contains `temperaturesaround`. Recorded IDs19879 and19454
  decode respectively to ` temperatures` and `around`; the second token has
  no leading-space marker. This predates containment handoff records193/194.
- RESPONSE272 contains `Toanalyze thehistoricalweatherpatternsforSanFrancisco...`.
  Its preceding REQUEST271 contains the more-spaced prior selection202 and
  normally spaced source269. Each of272's four quoted passages has whitespace
  changes against a matching visible source span. Previously generated errors
  also survive unchanged in compacted context, so some losses are inherited
  and others are newly generated; they are not a display-only artifact.

For all five responses, twelve checks passed (60 total): native tokenizer
decode and direct backend decode equal stored raw; committed target and IDs
equal raw/native IDs; eligible target and IDs remain unchanged; encoded target
IDs and unmasked training labels equal native IDs; re-tokenized REQUEST has
the exact recorded generation prompt hash/count; chat-template decode preserves
rendered text; restored history renders exactly the recorded REQUEST.

The actual frozen native loader restores `tokenizer.json` into the fast
tokenizer backend. The audit used that loader, not an approximate tokenizer
or the concurrently edited local runtime. It instantiated no model and verified
CUDA remained uninitialized. No held/readout files were opened.

## Receipts and scope

Node prefix: `/localhome/local-rohing/orch_r136_node4_20260916T101200Z`.
Receipt: `reread_spacing_audit_1789556800662908225/AUDIT.json` beneath that prefix.
SHA256: `b7b28ccaebc013c2ad80ff34c06e0ec0dedbe35ede6463f0a6c85b6ec19c331b`.
The full audit and20 exact TRAIN records are mirrored and hash-verified under
`research_notes/analysis/orch_r136_node4_20260916/reread_spacing_audit_1789556800662908225/`.
Reproducible collector: adjacent `reread_spacing_audit.py`.

Audit ran1789556800.6629074–1789556805.8886843. It read6,169,072 bytes within
a64MiB/1024-record cap. The initial collector failed when saving a repeated
evidence filename; its partial directory remains preserved. Only that collector
deduplication bug was repaired, followed by a new audit directory.

Frozen native SHA256:
`6b46401e5f8ff92d95e018b481d2303a55a3ce7c8e617aec65faa64bbc8381c7`.
Frozen plain-context SHA256:
`b3859e4a45d53fc67c51add5dad8431985ca0adda901389e0206819a56245d92`.
Tokenizer JSON SHA256:
`c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`.
Other exact source/config hashes, tokens, source spans and edit positions are
in the receipt. Whitespace-normalized matching was diagnostic only; it did not
modify model inputs, outputs, targets or the replay algorithm.

No causal claim about repetition penalties, training reinforcement or a general
capability change follows from this trace. Those would require separate
controlled evidence, not speculative sanitization of the live branch.
