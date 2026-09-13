# Independent terminal audit: PCFL `S_A40` acquisition and sequence stop

Date: 2026-09-13 PT  
Scope: documentation-only audit of the already-terminal native fit and its two
cold readouts. No source, model, tokenizer, adapter, benchmark, or GPU state was
changed, and no new scientific execution was performed.

## Verdict

The eligible `S_A40` attempt is authentic and its negative endpoint is valid.
It does **not** acquire any complete Bank-A EVENT at the pre-correction state:
`0/4` under the directly trained `W0` wording and `0/4` under the untrained
`W8` wrapper. The identically prompted `NO_WRITE` control is also `0/4` in
both banks and both views. Because Bank A has no pre-correction successes,
there is no positive item whose survival a second write could measure.
Retention is therefore **undefined**, not failed, and no warm descendant is
eligible.

There is one reportable diagnostic effect, but it is negative rather than
memory acquisition. `NO_WRITE` returns the safe `MISS` response on all 16
queries. `S_A40` instead emits an EVENT-shaped non-refusal on all 16 queries,
yet gets zero complete records and zero exact non-address fields. The adapter
has learned the response dialect before the bindings: it turns abstention into
confident malformed or false pseudo-memory.

This version is terminal. Do not launch `SEQ_REPLAY`, `SEQ_NEW_ONLY`,
`FRESH_MIX`, `ALL_AVAILABLE`, or a higher-dose `S_A` rescue under this version.
A materially new acquisition recipe would be a prospective successor, not a
continuation of this retention experiment.

## 1. Authoritative roots

- eligible fit:
  `/localhome/local-rohing/astra_diagnostics/pcfl_event_sequence_S_A_20260913_attempt4`
- cold no-write readout:
  `/localhome/local-rohing/astra_diagnostics/pcfl_event_sequence_readout_NO_WRITE_20260913_attempt1`
- cold `S_A` readout:
  `/localhome/local-rohing/astra_diagnostics/pcfl_event_sequence_readout_S_A_20260913_attempt1`

Attempt 3 is not evidence. It trained but failed before producing an eligible
completion receipt because a non-built-in version object changed type across
JSON round-trip. Attempt 4 uses a fresh root and is the first eligible fit.

Important pins and hashes:

| Object | SHA-256 |
|---|---|
| immutable original formation archive | `bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869` |
| exported sequence material | `9fe776c38a493152526920cb13a9bc37911cd6e674b7009cc199f1e3f9e4ae4f` |
| sequence specification | `9456d93bc21a5846c39343efb369800fc25296cc91dbad436b8f38a3c8c0e90e` |
| authenticated import | `cc9e97a290933633d67c371625ae5cfffeb46bc8ca7c130279022868e98a545e` |
| fit completion file | `8478373fa109ae5115ed7845753ca4812fc6a1857c4c86fbb71a52c7ae10897b` |
| adapter tensor file | `82d98aed28fe4bcd0a6c18e49111b48ff0b92b37c3ef9459e1993edd38e661b2` |
| no-write completion file | `4c975552a27860a3226ba592d18217b63ec70cd192875b783b0804b1719dba0e` |
| `S_A` completion file | `1635b213888afc7c81ca6a638b6564ac3660192f6630b5c4b75035c1e204460f` |

All source/input pins currently rehash: 12/12 for the fit inputs and 15/15
for each readout input. All declared artifact inventories rehash: 10/10 fit
completion files plus 11/11 outer-stage files; 89/89 no-write completion files
plus 90/90 outer-stage files; and 93/93 `S_A` completion files plus 94/94
outer-stage files.

## 2. What was actually written

The source is one exposed development root, `disposable/0`, containing eight
chronological OLD EVENT rows at original formation calls 1, 3, 5, ..., 15.
Records 0--3 are Bank A and records 4--7 are Bank B. Every record has:

- `origin = CHILD_NATIVE`;
- `taint = CHILD_SUBMISSION`;
- byte-identical row, generated target, and target hash;
- a source capture hash and world-evidence receipt hash; and
- `fixture_only = false`.

This remains a format-assisted diagnostic, not clean autonomous formation.
The frozen material explicitly records the original formation as
`FORMATION_FAILED`, uses the externally supplied one-line terminal-LF format
scaffold, and records `native_generation_verified = false` in each imported
row's provenance. Those limitations must travel with any use of the result.

`S_A40` trains **only Bank A**:

- 40 updates, one batch of four records per update;
- 160 presentations total;
- each of the four A records appears 40 times: five repetitions under each of
  wrapper views `W0`--`W7`;
- no Bank-B item appears in `fit/corpus.json`;
- 8,400 supervised target tokens and 22,840 total tokens;
- rank 8, alpha 16, dropout 0.05, learning rate `3e-5`, bf16, batch size 4;
- fresh Qwen2.5-7B-Instruct base at revision
  `a09a35458c702b33eeacc393d103063234e8bc28`, no predecessor or warm start;
- no packing, no truncation, no non-finite batches, and base unchanged; and
- final-batch loss `2.4754524` (epoch mean `3.92211`).

The cold `S_A` reader mounted only a byte-identical three-file copy of the
completed adapter. The tensor, config, and README hashes match the fit
checkpoint exactly. Neither cold readout trained or updated anything.

## 3. Exact cold scores

Each cell contains four distinct addresses. `W0` was present in the S_A
training mixture; `W8` was not, although it was already an exposed development
wrapper. Bank A is the written bank. Bank B is the not-yet-written bank.

| State | View | Bank A exact + stop | Bank B exact + stop |
|---|---:|---:|---:|
| `NO_WRITE` | W0 | 0/4 | 0/4 |
| `NO_WRITE` | W8 | 0/4 | 0/4 |
| `S_A40` | W0 | 0/4 | 0/4 |
| `S_A40` | W8 | 0/4 | 0/4 |

All 32 generations finish with `stop`; none is length-truncated. All 16
`NO_WRITE` outputs are exactly `MISS`. All 16 `S_A40` outputs are non-refusals
ending in LF, but all 16 are semantically and byte-exactly wrong.

The decisive acquisition cells are the two Bank-A cells. Even the four facts
shown directly under `W0` five times each are `0/4`; the wrapper-only `W8`
view is also `0/4`. Bank B's zero is not itself an acquisition failure because
Bank B has not yet been written. It does show that the new response tendency
spills onto unwritten addresses.

The experimental unit is one root, one life, and one fit. The 16 calls and the
four records per cell are repeated within-unit measurements, not independent
replicates.

## 4. Partial output audit

There is **no defensible partial memory-content result**.

- `S_A40` starts all 16 generations with `EVENT`; 15/16 begin with the exact
  prompt-visible form `EVENT <queried-address> AT ...`, and the queried address
  appears somewhere in all 16. Address reproduction is prompt echo, not stored
  content.
- Across the 16 outputs, none contains any of the expected source-node, port,
  destination-node, or evidence-receipt fields for its queried row: **0/64
  exact non-address fields**.
- More strongly, none of the 14 unique non-address identifiers from the four
  trained Bank-A rows appears anywhere in any `S_A40` output. This rules out
  even a reportable exact-field-but-wrong-association signal.
- Only 1/16 outputs parses as a complete but false EVENT row under the frozen
  row grammar. The other 15 are malformed pseudo-rows. Six contain the literal
  `EVIDENCE` field label.
- Exact target/output BPE-prefix lengths are 10--14 tokens on the 15
  address-prefixed outputs and one token on the remaining output. These
  prefixes are accounted for by `EVENT`, the address supplied in the prompt,
  and fixed row syntax. A few outputs share a single identifier subtoken, but
  there was no predeclared or baseline-calibrated subtoken score, and the same
  behavior occurs on unwritten Bank B. It is not memory evidence.

The valid partial statement is therefore behavioral: at this dose the LoRA
learned to attempt the EVENT dialect and stopped obeying the reader's
appropriate `MISS` behavior. It did not recover a single complete content
binding. This is useful evidence for a write-safety gate: response-format
acquisition can precede factual acquisition and can make the reader more
confidently wrong.

## 5. Symmetry, custody, and release

The two cold arms use the same model revision and model binding, tokenizer and
chat-template hashes, 16-row roster, 2,048-token output cap, seed-zero roster,
engine settings, GPU UUID, and source/material pins. For all 16 paired calls,
the public messages, row metadata, device limit, rendered prompt token IDs,
and per-row seed/output limit are byte-identical. The fixed engine settings
also match after excluding the intended arm and adapter identity. Both arms
consume exactly 1,506 prompt tokens. The only
scientific treatment difference is the mounted `S_A40` adapter; its larger
output total (836 versus 32) is an outcome.

The fit and both readout workers exit zero with empty owned process groups.
Each outer collection has `errors = []`, `returncode = 0`, and
`gpu_released = true`; post-run GPU and queue checks are empty/matched. Post-CVD
checks are clear with no unexpected or unresolved owners, using only the
declared non-worker init-service exceptions. The inner completion receipts
correctly retain `gpu_released = false` because outer lifecycle code owns final
release; the outer receipts establish release.

Every artifact preserves `full_contract_released = false` and
`automatic_promotion = false`.

## 6. Terminal scientific disposition

1. `S_A40` fails its acquisition precondition. Do not call this storage,
   sequence learning, or retention.
2. Because pre-correction Bank A is all-zero, `kept_1_to_1` and
   `lost_1_to_0` have denominator zero. Retention is **undefined**.
3. No warm sequence descendant exists on node 2. The only sequence roots are
   the ineligible attempt 3, eligible attempt 4, and the two cold readouts;
   no sequence process or GPU owner remained at audit time.
4. No dose rescue is permitted under this frozen version. The high terminal
   loss makes under-acquisition plausible, so this result does not bound what
   another prospective recipe could do. It does terminally answer this
   predeclared low-dose state.
5. The reportable mechanism finding is a warning: the low-dose adapter learned
   output schema without address-to-content bindings, changing 16 safe misses
   into 16 false or malformed assertions. A future acquisition gate should
   require exact content plus false-positive control before any sequential
   retention phase is eligible.
