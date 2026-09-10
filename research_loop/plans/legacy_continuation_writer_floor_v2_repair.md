# Legacy continuation-writer floor v2 repair overlay

Status: newly hash-bound proposal only. This overlay is applied after
`legacy_continuation_writer_floor_v0.md` and
`legacy_continuation_writer_floor_v1_repair.md`; this file wins on conflict.
It repairs the v2 adversarial critique without broadening the scientific
object. No implementation or execution authority follows from it.

## R10. Closed-world terminology and claim ceiling

Replace every occurrence of “dream-time re-expression,” “memory growth,” or
“organism consolidation” in the floor's proposed graph, nodes, edges, tests,
and report templates with the literal terms **closed-world provenance
extraction**, **offline source-oracle-selected continuation corpus**, and
**assay-local supervised adapter training**. Extractors attach and select
existing rows; they create no memories, connections, evidence, recurrence, or
organism state.

The fixed forbidden-prose scanner also rejects claims of semantic novelty,
generalization, substrate superiority, memory-path necessity, online learning,
causal outcome/verification effects, recurrence, lifetime scaling, scale,
replication, seed robustness, hardware robustness, population inference, or
parenting. A positive remains compatible with target URI/family cues, base
pretraining, a generic action prior, marker imitation, and historical
birth-prompt shaping. Only the exact offline writer/interface package effects
registered below are reportable.

## R11. Exact acceptance-stage semantics and command DAG

The schema's coarse `required_before` field is interpreted as follows:

- `implementation`: before any implementation authorized by A0;
- `model_execution`: before any model forward pass or trainer, after A0/A1
  CPU implementation and tokenizer work;
- `gpu_run`: before the first finite GPU canary authorized within A2;
- `scientific_claim`: before A3 reporting can enter a valid scientific state.

AT1 and all source-extractor tests are required before `model_execution`, not
before A0 implementation. AT4, AT10, AT19, and AT20 necessarily exercise the
finite A2 GPU canaries and are required before A3/scientific claim, not before
the first GPU canary.

The A2 command DAG is exact and fail-closed:

1. before real target enumeration, AT2, AT9, AT11, AT12, AT13-synthetic,
   AT16, AT17, AT18-template, and AT22 pass;
2. the two real sealers run; AT3 and AT23 pass and atomically publish one
   target manifest;
3. exact target messages/IDs are rendered without scores or model calls;
   AT8, AT9, and AT18-full-policy pass on every target;
4. duplicate B0/C1 and B0/C2 trainers run and tensor/loss receipts agree;
5. duplicate C0, duplicate mounted nonzero B0/C1 and B0/C2, and zero-delta
   serving/scoring canaries run; AT4, AT10, AT19, and AT20 pass;
6. AT14 proves isolation, the finite canary receipt closes, and no further
   command is reachable until independent review plus exact A3 ratification.

Any failed prerequisite stops the DAG. A2 authorizes the finite commands but
does not make them concurrently reachable. AT16 validates all command and
receipt dependencies, not only the human-authority nodes.

## R12. Corpus feasibility is a validity gate

AT17 asserts, separately for B0/B1/B2 after exact extraction and tokenization:
at least 64 unique rows, at least 4,096 supervised target tokens, at least four
distinct exact ACT payloads, maximum single-payload row share at most 0.80,
valid EOS, no C2 sequence above 1,024 tokens, no truncation, and zero retained
row with ambiguous provenance, invalid outcome, inconsistent score, or source
cap. Any failure maps to `INVALID_INFRA`; no life may be dropped, pooled,
resampled, augmented, or threshold-relaxed.

## R13. Complete policy-visible byte scan

The frozen valid CompilerGym action-name inventory is part of the manifest.
For every target and every cell, AT18 scans the exact vLLM-reported consumed
input-ID vector, its independent decode under both special-token-preserving
and special-token-skipping modes, rendered user bytes, message JSON bytes,
chat-template bytes/output, and every template-added byte. It rejects:

- the historical four-pass payload or any selected source payload;
- any source action, outcome, score, continuation substring, or corpus row;
- every concrete valid action name, with no task-metadata or syntax exception;
- any input-ID subsequence equal to a concrete action name tokenized in raw,
  leading-space, comma-prefixed, newline-prefixed, or `ACT:`-prefixed form.

Only the abstract literal `ACT: <comma-separated LLVM pass names>` and the
words “LLVM pass names” may describe the interface. The scan runs first on the
target-independent template and again on every exact target ID vector after
sealing and before any GPU request.

## R14. Target-to-dispatch-to-score round trip

The assay does not use `organism_v6/gym_backend.py` normalization. The exact
floor dispatcher receives the first strict `ACT:` payload bytes, splits only
on literal commas, strips only leading/trailing ASCII space or tab from each
field, rejects empty fields, and requires each remaining UTF-8 field to equal
one frozen action name byte-for-byte. It records the ordered action names and
their exact version-bound CompilerGym integer indices; no whitespace-to-comma
rewrite, alias, repair, or retry is allowed.

For each scored request the scorer creates a fresh environment, resets the
sealed canonical URI, exports the reset-state module, and requires its SHA-256
to equal the sealed module hash before observing `I0` or applying an action.
It records the parser payload bytes, parsed names, integer indices actually
passed to CompilerGym, evaluator/library/container identities, pre-action I0,
post-action I1, and recomputed score. Any module, payload, index, or score
disagreement invalidates the request and therefore the assay; it is never
scored as zero.

## R15. Nonzero-adapter deterministic canaries

For both duplicate B0/C1 adapters and both duplicate B0/C2 adapters, serve the
complete sealed 64-target canary panel twice from fresh processes. Require
bit-identical engine-consumed input IDs, generated token IDs, decoded/parser
bytes, dispatched indices, I0/I1, and scores across the same-cell duplicates.
The receipt proves that the mounted adapter tensor hash is the independently
hashed nonzero tensor produced by the corresponding trainer and that disabling
the mount changes the declared adapter identity. Zero-delta equivalence is an
additional check, never a substitute. Any nonzero mismatch is `INVALID_INFRA`.

## R16. Positive-action endpoint; abstention cannot win

For each cell/program classify exactly one mutually exclusive outcome:

1. `accepted_positive`: strict marker, valid exact action vector, evaluator
   accepted, raw score greater than zero;
2. `accepted_nonpositive`: strict marker, valid exact action vector, evaluator
   accepted, raw score at most zero;
3. `invalid_strict`: strict marker but parser/evaluator rejects before a score;
4. `malformed_or_nearmiss`: action-like output without a strict valid marker;
5. `silent`: neither strict nor action-like output.

Report their rates, evaluator-accepted rate `A`, accepted-positive rate `Q`,
strict-marker rate `M`, raw score `S` (invalid/missing shown separately, never
silently imputed), and positive utility

`P = mean( max(100*(I0-I1)/I0, 0) for accepted requests; 0 otherwise )`.

`P` is the primary behavior value: refusal, invalidity, and valid worsening all
contribute zero and therefore cannot beat a baseline merely by avoiding a
negative action. A prefix-package advantage is present only if:

- mean over lives of `P[C2,l]-P[C1,l] >= +1.0` percentage point;
- at least two of three life differences are at least +0.5 point;
- mean `A[C2,l]-A[C1,l] >= -0.02`;
- mean `Q[C2,l]-Q[C1,l] >= -0.02`; and
- mean `M[C2,l]-M[C1,l] >= +0.05`.

A useful selected-package effect is present only if:

- mean over lives of `P[C2,l]-P[C0] >= +1.0` percentage point;
- at least two of three C2 life values exceed C0 by at least +0.5 point;
- mean `A[C2,l]-A[C0] >= -0.02`;
- mean `Q[C2,l]-Q[C0] >= -0.02`; and
- mean `M[C2,l]-M[C0] >= -0.02`.

Raw S, invalidity reduction, or abstention reduction are diagnostics only and
cannot override P/A/Q/M. A scorer-round-trip failure is invalid infrastructure,
not `invalid_strict` and not a scientific zero.

## R17. One-shot salt provenance and real-seal receipt

Before A2, the salt law, retrieval command, future UTC beacon epoch, beacon
endpoint identity, and empty output path are frozen at A1. The seal salt is
the SHA-256 of the first NIST Randomness Beacon 2.0 pulse at that exact future
epoch concatenated with the A1 receipt hash. A dedicated salt-steward process
with no CompilerGym/dataset dependency retrieves exactly that pulse once,
verifies the signed pulse/chain fields under the frozen verification procedure,
and atomically commits raw response bytes, derived salt, request/response
timestamps, command/environment hashes, and a one-shot counter. It has no
candidate-salt loop. The exact committed value is part of A2 ratification.

AT22 proves the pulse epoch postdates A1, the output did not preexist, one
request produced one committed salt, the signature/chain and derivation pass,
and the value/salt were never reused. A failed retrieval abandons the epoch and
requires a newly deliberated epoch law; it may not try another pulse under the
same proposal.

During the actual seal—not only synthetic tests—each sealer emits a write-ahead
access record before opening/enumerating a dataset object. AT23 requires exact
sealer agreement, complete access logs, no unexpected reader or file open,
complete exposure-registry writes before any failure exit, exact comparator
receipt, and one atomic `UNPUBLISHED -> PUBLISHED` transition. Any discrepancy
is `ABANDONED_SEAL`, burns the salt/namespace, and excludes every exposed hash
under R7.

## R18. Claim-state precedence

State selection uses this exact first-match precedence:

1. if any real target URI/module/hash was exposed and any seal/access/
   publication condition fails: `ABANDONED_SEAL` (all infrastructure faults
   are secondary flags; quarantine obligations still apply);
2. else if any extraction, feasibility, tokenizer, rendering, serving,
   dispatch, scoring, determinism, sandbox, review, or authorization gate
   fails: `INVALID_INFRA`;
3. else if any ratified required command, cell, target, or receipt is absent
   solely because execution was not completed and no gate failed:
   `INCOMPLETE`;
4. else select exactly one of `VALID_NEGATIVE`, `VALID_PREFIX_ONLY`,
   `VALID_PACKAGE_ONLY`, or `VALID_BOTH` from the two R16 booleans.

A timeout is a gate failure, not incompleteness. AT24 exhaustively enumerates
all overlapping predicate combinations, asserts the first-match label and
secondary flags, and proves that only the four `VALID_*` states can emit fixed
scientific report text.

## R19. Additional registered tests

The newly generated architecture-change artifact retains repaired AT1--AT15
and MUST add:

- **AT16_a2_receipt_dependency_order:** machine-check R11's complete command/
  receipt DAG, including every A2 prerequisite and the closed A3 gate.
- **AT17_source_corpus_feasibility:** enforce every R12 floor and map failure
  to `INVALID_INFRA`.
- **AT18_full_policy_visibility_scan:** enforce R13 on the template and every
  engine-consumed target ID sequence.
- **AT19_target_dispatch_scoring_roundtrip:** enforce every R14 identity from
  sealed module through exact executed indices and recomputed score.
- **AT20_nonzero_adapter_serving_canary:** enforce R15 for B0/C1 and B0/C2.
- **AT21_action_validity_and_abstention_decomposition:** enforce R16's outcome
  partition, P/A/Q/M reports, and exact effect gates.
- **AT22_salt_commitment_provenance:** enforce R17's one-shot independently
  verified future-beacon derivation and non-reuse.
- **AT23_real_seal_access_and_publication:** enforce the actual-seal write-
  ahead access, exposure, agreement, and atomic publication receipt.
- **AT24_claim_state_precedence:** exhaustively enforce R18.

AT1 and AT12/AT17 are required before `model_execution`; AT2, AT3, AT8, AT9,
AT11--AT13, AT16--AT18, AT22, and AT23 before `gpu_run`; AT4--AT7, AT10,
AT14--AT15, AT19--AT21, and AT24 before `scientific_claim`. Future substrate,
online-learning, causal-corpus, semantic-generalization, repeat-state, and
control-plane tests remain explicitly outside this floor.

