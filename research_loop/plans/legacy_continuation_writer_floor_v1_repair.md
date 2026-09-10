# Legacy continuation-writer floor v1 repair overlay

Status: newly hash-bound design proposal only. This file is an exact overlay
on `legacy_continuation_writer_floor_v0.md`; every rule below replaces the
corresponding v0 rule on conflict. No implementation, tokenizer, target,
trainer, evaluator, GPU, scientific-claim, or release authority follows from
this proposal. The assay remains a formative writer/interface floor, not an
Experience Models result.

## R1. Exact scientific object and bootstrap shortcut

The historical source rows were generated under a birth prompt that displayed
the four-pass payload `-mem2reg, -sroa, -gvn, -simplifycfg`. Source actions,
outcomes, scores, improvement comparisons, and the matching payload frequency
are therefore selection-oracle information, not independent discoveries.
They are visible to the source extractor and causally used as described below.
The absence of persisted source prompts is never repaired or inferred.

The target-evaluation bootstrap MUST NOT contain any concrete LLVM pass name,
pass sequence, source action, source outcome, source score, or corpus text. It
may teach only the syntax `ACT: <comma-separated LLVM pass names>`. The exact
LF-normalized bootstrap bytes are frozen in the later pre-seal run manifest.
A static scanner rejects the manifest if the bootstrap or renderer contains
the historical four-pass payload, any selected source payload, or any pass
name outside the literal syntax description and immutable task metadata.

This removal closes direct evaluation-prompt copying, but it does not turn the
historical data into task-conditioned evidence. A passing C2-minus-C0 cell may
mean only that an offline, source-oracle-selected continuation package taught
a useful cross-program action prior and retained the strict interface. It does
not establish memory-path necessity, causal outcome learning, verification,
composition, discovery, recurrence, or online learning.

Required diagnostics remain: exact historical birth-payload row share,
generated first-action birth-payload share by cell, and corpus feasibility
with that payload excluded. They cannot condition the registered conclusion.

## R2. Information visibility and causal-use contract

The following table is exhaustive. `visible` means the stage may read the
bytes; `causal` means they may change a selected row or output.

| information | source snapshot/extraction | tokenizer golden | design/run-manifest authoring | target sealing | model serving | scoring/reporting |
|---|---:|---:|---:|---:|---:|---:|
| source thought/act/note bytes | visible, causal | selected targets only, causal | hashes/counts only | hidden | hidden | aggregate diagnostics only |
| source action payloads | visible, causal | target bytes only, causal | hashes/counts only | hidden | hidden | aggregate/hash diagnostics only |
| source outcomes and I0/I1 | visible, causal | hidden | aggregate counts only | hidden | hidden | aggregate diagnostics only |
| source stored scores | visible, causal after independent recomputation | hidden | aggregate counts only | hidden | hidden | aggregate diagnostics only |
| earlier valid-act comparisons | derived at extraction, causal | hidden | aggregate counts only | hidden | hidden | aggregate diagnostics only |
| historical bootstrap file/payload | visible, diagnostic; never joined as a prompt | hidden | visible, exclusion-causal | hidden | hidden | copying diagnostic only |
| contamination URIs already named in bound inputs | visible | hidden | hashes/counts only | visible, exclusion-causal | hidden | counts only |
| candidate target universe/URIs/module hashes | hidden | hidden | hidden | visible, causal | sealed target only | sealed target only |
| target baseline/after counts and scores | hidden | hidden | hidden | forbidden | forbidden until an immutable first action exists | visible, causal only to scoring/reporting |
| generated target continuations/actions | hidden | hidden | hidden | hidden | visible, causal to dispatch | visible, causal to scoring/reporting |

No source score or outcome is a target label. No target score, action, module,
or URI may affect extraction, corpus construction, tokenizer fitting, trainer
settings, renderer bytes, thresholds, or any design choice.

## R3. Target-aligned training equality

For retained row `r`, derive `target_ids[r]` exactly once using the frozen
tokenizer with `add_special_tokens=false`; define
`supervised_ids[r] = target_ids[r] + [eos_token_id]`. Reject an absent EOS.

For cell C1, `input_ids = bare_prefix_ids + supervised_ids`; for C2,
`input_ids = neutral_chat_prefix_ids + supervised_ids`. `bare_prefix_ids` and
`neutral_chat_prefix_ids` are separately frozen. Full masks necessarily have
different lengths. The equality object is instead the ordered target-aligned
projection

`[(target_ordinal, input_id, label_id, is_supervised)]`,

starting at ordinal zero at the first continuation token and including EOS.
For every row, C1 and C2 projections MUST be byte-identical, every projected
label MUST equal its input ID, and every projected bit MUST be true. Every
prefix label is `-100`. Hash and report both unequal full input/mask arrays and
the equal target-aligned projections. Row order, target-token totals, update
ordinals, optimizer schedule values by update ordinal, and initial adapter
tensor bytes are identical. There is no packing or truncation.

## R4. Serving round-trip contract

The evaluator never hands vLLM a string prompt. The frozen renderer produces
LF-normalized UTF-8 bytes; the frozen tokenizer applies the exact bound chat
template once with `tokenize=true` and `add_generation_prompt=true`. The
resulting integer IDs are placed in a vLLM `TokensPrompt` (or the exact
version-bound equivalent) and served directly. C0/C1/C2 receive the identical
sealed ID vector for a target.

For every canary and scored request, the receipt contains hashes of rendered
bytes, message JSON bytes, template bytes, tokenizer files, input IDs, special
and stop IDs, sampling parameters, adapter tensor identity, generated token
IDs, vLLM-reported consumed prompt IDs, vLLM text bytes, independently decoded
text bytes, and strict-parser bytes/result. The request is invalid unless the
reported consumed IDs equal the sealed input IDs exactly and the version-bound
vLLM text equals independent decoding under the explicitly frozen stop-token
and special-token rule. No silent string fallback or retry is permitted.

## R5. Acyclic authority graph

Authority is split into four exact human decisions. Failure never grants the
next stage.

1. **A0 architecture ratification.** Authorizes only isolated CPU/no-model,
   no-tokenizer source snapshotting, dual extraction, source visibility
   receipts, synthetic fault fixtures, and a tokenizer-manifest candidate.
2. **A1 tokenizer ratification.** After independent review of A0 receipts,
   ratifies exact local model/tokenizer/template file hashes and authorizes
   only CPU tokenizer execution, C1/C2 row rendering, target-aligned label
   goldens, and an exact pre-seal run-manifest candidate. No target, model
   forward pass, trainer, evaluator, or GPU is authorized.
3. **A2 seal-and-canary ratification.** After independent review of A1,
   ratifies the complete run manifest, contamination inputs, fresh seal salt,
   target-selection law, finite canary command list, output namespace, and
   failure bytes. It authorizes atomic score-blind target sealing and only the
   finite GPU canaries: duplicate B0/C1 and B0/C2 training, duplicate C0
   serving on the sealed panel, and zero-delta mounting. It does not authorize
   other lives/cells or a scientific result.
4. **A3 execution promotion.** Only after the seal and canaries pass, a fresh
   independent reviewer and an author-side scientific advocate inspect the
   exact receipts. Rohin then separately ratifies the exact remaining command
   set. Only A3 authorizes B1/B2 training, C1/C2 target evaluation, aggregation,
   and the bounded claim-state report.

A machine-readable DAG MUST contain exactly these nodes and edges
`A0 -> A1 -> A2 -> A3 -> REPORT`; tokenizer execution is reachable only from
A1, target sealing and finite canaries only from A2, and remaining execution
only from A3. A reachability test rejects cycles or any command reachable from
an earlier authority node.

## R6. Independent implementations and fault injection

Each extractor and sealer pair declares its shared trust base and its separate
implementation base. Pair members run in distinct processes, share no project
helper module, read no intermediate output from the other, and have separately
hashed source files and dependency manifests. Extractor A is a forward
event-stream implementation; extractor B is an offset-indexed constraint
solver. Sealer A enumerates through the bound CompilerGym dataset API; sealer
B independently enumerates the version-bound installed dataset inventory and
resets/exports each URI through a fresh environment. Sharing immutable Python,
LLVM, CompilerGym, raw inputs, and the written law is disclosed and never
called independent evidence.

A third declarative fixture manifest supplies known accepted and rejected
cases without importing either implementation. It covers at least: leading,
between, and trailing marker groups; repeated one-tick occurrences; ambiguous
attachment; mixed ticks; boundary straddle; action-byte mismatch; malformed
outcome; score mismatch; duplicate continuation; contaminated alias; duplicate
target content; timeout; partial enumeration; and fewer-than-64 survivors.
Both implementations must match the fixture oracle. Comparator mutation tests
then alter one side only (offset, assignment, exclusion, alias, terminal
boundary, target order, or content hash) and MUST produce disagreement/NO-GO.
The receipt binds process commands, environment, source/dependency hashes,
fixture hashes, and each injected fault.

## R7. Atomic target sealing and durable quarantine

The A2 manifest freezes a fresh random `seal_salt` supplied and ratified before
target enumeration. Eligible content-hash classes are ordered by
`SHA256(seal_salt || 0x00 || module_sha256)`, then canonical URI, rather than by
raw content hash. Every content hash ever exposed by an abandoned or failed
seal is included in the permanent contamination registry for all later seals.

Each sealer writes into its own unpublished temporary capsule. A comparator
publishes the ordered target manifest atomically only after exact agreement.
All file opens, URI emissions, and publication state changes are appended to
an access log. On timeout, disagreement, partial publication, unexpected read,
or any target exposure before publication, the seal ID becomes permanently
`ABANDONED`; all exposed content hashes are appended to the exposure registry;
the capsules are quarantined; and neither the seal ID, salt, targets, aliases,
nor content-hash classes may be reused. Repair requires a new deliberated
manifest, new ratified salt, and exclusion of the complete exposure registry.
No threshold or design byte may change after a successful publication.

## R8. Reporting isolation and claim states

All commands execute in a sandbox where source snapshots, organism code,
research intake/workflow directories, live-life paths, and prior results are
read-only; one newly ratified assay output directory is the only writable
mount. Pre/post tree manifests must prove no mutation outside that directory.
A deliberate write attempt to each denied ingress path must fail. The output
directory is absent from every automatic dream, life, trainer, and intake glob;
a scanner and an empty dry-run intake receipt prove no auto-ingestion. Results
terminate at a human-readable report and cannot update a life, waking brief,
adapter, corpus, parent pack, or future dream without a new deliberation.

The final state machine is total and deterministic:

- `INVALID_INFRA`: any extraction, tokenizer, serving, reproducibility,
  sandbox, or review gate fails before a valid complete evaluation;
- `ABANDONED_SEAL`: any target seal is exposed, partial, quarantined, or fails;
- `INCOMPLETE`: gates pass but a required ratified cell/target is absent;
- `VALID_NEGATIVE`: both registered contrast rules are false;
- `VALID_PREFIX_ONLY`: prefix-package rule true, selected-package rule false;
- `VALID_PACKAGE_ONLY`: prefix-package rule false, selected-package rule true;
- `VALID_BOTH`: both rules true.

Only the last four are scientific assay outcomes, and their fixed report text
uses only the two narrow claims in R1. Infrastructure failure can never be
reported as a negative. A truth-table test covers every gate/contrast
combination and rejects any unregistered state or broader prose.

## R9. Repaired acceptance-test registry

The newly generated architecture-change artifact MUST register AT1--AT7 from
v0, with AT2 amended by R3 and AT4 amended by R4/R5, plus all of the following:

- **AT8_bootstrap_visibility_and_copying:** prove concrete pass payloads are
  absent from target bootstrap/renderer; bind historical payload visibility,
  source shares, and generated copying diagnostics.
- **AT9_visibility_oracle_partition:** machine-check the R2 table and prove
  source selection oracles cannot enter target inputs or labels and target
  values cannot reach design/extraction/training.
- **AT10_prompt_serving_roundtrip:** prove the complete R4 byte/ID/adapter/
  parser round trip on canaries and every scored request.
- **AT11_authority_stage_acyclicity:** validate the R5 DAG and reject early or
  cyclic command reachability.
- **AT12_independence_fault_injection:** satisfy every fixture and one-sided
  mutation requirement in R6.
- **AT13_seal_atomicity_and_quarantine:** fault-inject partial publication,
  disagreement, timeout, and access-log violations; prove salt/namespace burn
  and exposure-registry exclusion on a synthetic universe before real sealing.
- **AT14_no_writeback_no_autoingestion:** satisfy the sandbox, pre/post tree,
  denied-write, configured-glob, and dry-run intake checks in R8.
- **AT15_claim_state_machine:** exhaustively validate the R8 truth table and
  exact bounded report templates.

AT1--AT15 are required as allocated by R5. No retained v0 test substitutes for
a new test, and no consensus prose mutates the registry after ratification.

