# Corrective reselection: source2 repeated; new-material prediction unmet

September14,2026 UTC. Bounded independent result reader. Attempt2 is fully
terminal, not merely at SELECTION-file completion. Attempt1 infrastructure
failure is retained separately. No native model/tokenizer load, generation,
GPU experiment, fit, job launch, kill, remote change, notebook edit, or commit
by this auditor. Only this memo and the owned ignored artifact directory change.

## Scientific result: one sourced repeated choice, zero fits

Fresh root `/tmp/astra_corrective_reselection_20260914_attempt2/run` records
`RESELECTION_CAPTURED_NO_FIT`,1 expected/actual call,1 admitted source selection,
parent absent, and0 fits. Pure captured replay reproduces the sole case:
**actual AFTER task index3** (one-based task4). Prior selected sources were[0,2];
the new choice is **[2]**, hence **0 new sources,1 repeated source**.

Entire raw output, with **no trailing LF**:

```text
EVENT E_QQ43NOEYBQ AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD EVIDENCE R_6MJCDE77X2
```

The output matches original source2 under the existing FINAL_LF_ONLY convention;
no identifier, source choice, or semantic repair is made. It is also byte-identical
to the prior source2 selection output. Its original public receipt is:

```text
RECEIPT R_6MJCDE77X2 AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD
```

The eight replayed material origins are original collection row indexes
**[2,6,10,14,18,22,26,30]**, all belonging to source2. Admission status is
`SOURCED_SELECTION_NOT_UTILITY`; the native disposition is
`SOURCE_VALID_SELECTION_ONLY_NO_FIT_AUTHORIZATION`.

The design's prediction of a previously unselected source, particularly source3,
is **not met**. This is not equivalent to a proven wrong or useless selection:
source2 accurately describes the option that produced the observed non-goal
outcome. Such negative-option evidence can be informative. No subsequent fit
or action test establishes whether repeating it would help here. Main explicitly
declines an automatic repeat fit; this audit neither launches nor gates anything.

## Actual public error and exact prompt replay

All four saved CHILD_CORRECTIVE AFTER own routes enter preparation; none is
filtered by a hidden score. Replaying their actual committed outcomes against
public goals identifies exactly task index3:

- Public node: `N_IRD6ZSHY2B`.
- Public goal: `N_DH2AYPUMUT`.
- Available ports: `P_FWMNJO5UYN`, `P_ONQCERJ5LE`.
- Actual committed port: `P_ONQCERJ5LE`.
- Actual observed destination: `N_ZXFXLP2ESD`, different from the goal.

Its captured route first reads unselected source3's address `E_DEX6OHDHJP` and
gets the unsupported reader text retained in the corrective-result memo. It
then reads source2's address `E_QQ43NOEYBQ` correctly and commits source2's
port. Both reader replies, including the inaccurate one, remain in the public
dialogue. The four inherited receipt-grounded EVENTs are supplied together;
the renderer does not replace the inaccurate reader reply or supply a singled-out
corrective target. Source3, which describes the goal-reaching alternative,
remains available in the full record set but was not selected.

The unchanged frozen `prepare_cases`/`prepare_after` code reproduces every saved
case, source-document digest, public mismatch, prompt, and all four route
replays. `CALL_000.messages` equals the reconstructed case exactly, and its
response/messages/error join the SELECTION capture. Full `replay_selection`
reproduces the selected source, canonical record, admission, and eight origins.

The system instruction and parser are unchanged from the previous selection.
The public payload is now the post-sleep error, so the **whole rendered prompt
is not claimed byte-identical to an earlier different task's prompt**. Across
failed attempt1 and repaired attempt2, however, INPUTS and CORRECTION_CASES files
are byte-identical, and prepare/run cases also match. The repair did not alter
the scientific prompt or evidence. The choice is retained without a goal-match
admission condition.

## Actor and source joins

The generating adapter is the actual post-corrective child, not its pre-fit
ancestor. The successful native receipt's loaded state matches both the saved
training state and the generating state of the archived AFTER:

`b82490d3d1f848bcaaa58e2167bcbbb9d5d554d60154e7b61ab7944fbe2094b9`.

Bindings verified against existing bounded captures:

- Corrective train RESULT:
  `e719123e761e987d74439cd36c7996a9cc22b8706c782bfb63bc7e83068ed3a5`.
- Generating AFTER RESULT:
  `91a137226776891dc12b67c52e7546f5e8d0a3d4fe2b8d8bed2dfece7883de5b`.
- Saved adapter file receipt:
  `0808585011b357f710f8d65d69e56d9b3be38ca6b465271b1e913cb66e0f760a`.
- Inherited A2 COLLECTION:
  `d5d9162827c5f621644d96791c751283b50cde954c30c9ac87e2ed9a273f55c5`.

All seven cited AFTER files, the prior selection's cited files, the collection
and collection RESULT, and train receipt join. REQUEST fields match the final
RESULT. The source provenance, selection-source provenance, INPUTS, and
CORRECTION_SOURCE agree. The native success path checks the loaded actor before
selection, verifies base and adapter parameters unchanged afterward, and rechecks
adapter-file and AFTER-file hashes before reporting completion. It records
`frozen_base_unchanged=true`, `own_experience_actor=true`, `parent_present=false`.
These tensor checks are native attestations inspected in frozen source, not
new tensor measurements by this reader.

The repaired wrapper commit is
`175997126b109ac694fd63af884f8f7fc850d0b8`; captured wrapper SHA matches its Git blob:
`ae2d62b4e9a43a8d760e22aa522003e7997e291a3d70b8875de94729bdb5e9ec`.
Unchanged imports remain from
`/tmp/astra_corrective_sleep_source_20260914_attempt2`, source `e3a575d7`:
driver `6b3c7f07b271b7599e4a78e473852be774faf774d21de571000f152d31b8fa09`,
selector `24716244dbb919f2e909598655b8cd184a8e83368e6d3b8732855c517134f2e3`.
The separate wrapper/driver identities are intentional and checked separately.

## Timing, budgets, and retained infrastructure failure

Successful attempt2: **11:56:19.835110–11:57:17.015420 UTC**, September14,
2026;57.180310s total including setup. One greedy generation uses
**1010 input tokens,52 emitted token IDs**, terminal and untruncated, within the
2048/160 per-call limits. No new route/read evaluation or fit occurs. Dollar
cost and isolated generation/kernel time are not recorded.

Attempt1, source `e49ae77d67fb7d17fe8cdc8b2a52a02033a08b7e`, failed
**11:54:27.881711–11:54:54.073485 UTC** after26.191774s with
`FileExistsError(17, 'File exists')`. The wrapper prewrote CORRECTION_CASES,
then the reused selector attempted the same exclusive creation. The trace
fails before entry into the generation callback. There are **zero CALL files,
no SELECTION, no successful RESULT, and no raw selection output**. Model loading
had occurred, but this is not a policy refusal, wrong choice, or CUDA failure.
Expected call count1 is not an executed call count. No successful post-run base
verification should be inferred from the failed receipt.

Main's repair only moves the wrapper's case-file write into prepare-only mode,
leaving the native selector to write cases during the actual run. The frozen
diff confirms that narrow change. This auditor did not edit or rerun native
code; attempt1 failure/log/source remain preserved alongside attempt2 success.

## Causal limits for the proposed discrepancy-focused probe

Main's prospective idea changes only the system instruction, retaining this
same post-sleep actor and exact public payload: audit reader-versus-receipt
discrepancies and choose a sourced record that could correct the reader. It is
not executed by this audit. Concrete interpretation pitfalls:

- **Changed criterion:** selecting useful evidence for a route outcome versus
  correcting a reader discrepancy are different posed tasks. A different next
  choice would not establish improvement on the unchanged original instruction.
- **External guidance:** explicitly directing discrepancy comparison supplies
  an evidence-processing strategy. Even without a singled-out correct record
  or scorer, all four true records are present in the payload. Success could be
  guided matching/extraction, not learned memory, internalized error detection,
  or autonomous choice of when to inspect experience.
- **No isolated selector learning:** the earlier initial selections used a
  different adapter state and different error episodes. Current reselection
  changes both state and experience relative to that stage. The proposed same-
  state comparison can describe response to instruction wording on one payload,
  but does not retrospectively identify learning as the cause of either choice.
- **Source validity is not utility:** selecting source2 is admissible negative
  evidence. Selecting source3 next would be new relative to[0,2], but novelty,
  goal matching, and repair of an inaccurate reader are distinct outcomes. No
  choice alone establishes improved future routing or retention without a fit
  and subsequent outcome evidence; none is part of this no-fit result.
- **Adaptive single case:** the next instruction is motivated by this observed
  repeated choice. Report both attempts and conditions rather than treating a
  later favorable extraction as independent confirmation or an efficacy rate.

These are nonblocking claim boundaries, not a new execution gate or request for
additional variants. The current result is recurrent source-valid extraction
under an external scaffold, with an unmet new-material prediction—not improved
learned selection, scheduling, correction efficacy, or H1/H2 evidence.

## Independent preservation and reproduction

Owned root: `gpu_artifacts_local/astra_corrective_reselection_independent_20260914/`.
It contains bounded `attempt1/` and `attempt2/` captures, source/scripts, logs,
prepare/run receipts, remote hash manifests, and audit JSON. All **30 captured
files /122923 bytes** match remote hashes (attempt1:14/51185; attempt2:16/71738).
No adapter/model/tokenizer binaries or caches were copied. Existing corrective
and adult-cycle captures supply the immutable upstream evidence.

Key attempt2 hashes:

| File | SHA-256 |
|---|---|
| `run/RESULT.json` | `098d15e1eb635498f6b9d74b139e933bb7acfdad71dd40b7411e1c81d9a9e0f3` |
| `run/SELECTION.json` | `9c2bdce160adc7b51f71d3138e8882ed863d4d7e500064f43d7317cc3e48240b` |
| `run/CALL_000.json` | `e6ba640794a69e0d096cffb844037ef7baeb560a506153728158826634007786` |
| `run/CORRECTION_CASES.json` | `4afca5ce8b1409ba86d1f45dd5415c82a1e01fd12f5dbd592ff56a0028dc94a7` |

Attempt1 FAILED hash:
`bfb68e6c1fe65bde0e8a4dd9921abcd27b51a1352162c39e075d41b06fa626d4`.

```bash
python3 -B gpu_artifacts_local/astra_corrective_reselection_independent_20260914/replay.py attempt1
python3 -B gpu_artifacts_local/astra_corrective_reselection_independent_20260914/replay.py attempt2
```

Both bounded source/capture checks pass with `no_native_imports=true`; attempt2
fully replays selection, attempt1 only the prepared case and failure boundary.
No new repository tests or runtime code edits. Memo and owned artifacts released
to Main; no commit or automatic follow-on fit.

## Supplemental terminal result: full-EVENT reader-audit recipe

Added September14,2026 UTC after independently capturing
`/tmp/astra_reader_audit_selection_20260914_attempt1`. This completes the
instruction comparison described prospectively above; all earlier records and
the failed first attempt remain unchanged. Main closes this recipe without a
fit. No new execution, model/tokenizer load, native code edit, or commit by this
auditor.

### Same actor and payload; same sourced output

The guided run is fully terminal: `RESELECTION_CAPTURED_NO_FIT`,1 expected and
actual call,1 admitted selection,0 fits, parent absent. It again selects
**source[2] for actual task index3**, repeating the prior selected set[0,2]. Its
raw EVENT and all52 emitted token IDs are identical to original reselection's
output. The raw EVENT has no final LF and matches source2 under FINAL_LF_ONLY.
All eight original row origins[2,6,10,14,18,22,26,30] replay without replacement.

```text
EVENT E_QQ43NOEYBQ AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD EVIDENCE R_6MJCDE77X2
```

The prediction of newly selected material remains **unsupported**. This is still
a source-valid negative-option record, not an invalid or fabricated selection.
Novelty, usefulness, and source admission remain separate quantities; neither
this unchanged choice nor the changed instruction was fitted or utility-tested.

Independent joins establish:

- Same actual post-sleep adapter state
  `b82490d3d1f848bcaaa58e2167bcbbb9d5d554d60154e7b61ab7944fbe2094b9`,
  training receipt, generating AFTER, original collection, prior selection, and
  adapter-file receipts as the original reselection.
- `INPUTS.json` is byte-identical to the original reselection input provenance,
  SHA `6036bfef38c930c6e84ec191bbcf8cb3ed8c8bd938270f0a3e6979b9bda95018`.
- Rebuilding original cases gives exactly the original attempt2 cases; applying
  the frozen `reader_audit` recipe reproduces the guided prepare/run cases.
  The complete user message—including public task, four own records in their
  original order, actual action/outcome, and both accurate/inaccurate reader
  replies—is unchanged. Only the system message differs; preparation metadata
  hashes change accordingly.
- The actual CALL messages equal that reconstructed guided prompt. Captured
  response replay through the unchanged source-admission reducer reproduces the
  entire SELECTION record, errors, admission, and material origins. No model
  callback was invoked; the replay callback returns only captured actual output.
- Native completion again attests unchanged base/adapter parameters and
  rechecks upstream file hashes. This auditor verifies receipt/source joins,
  not freshly loaded tensors.

The new system specifically directs comparing each returned EVENT with the
receipt-grounded EVENT at the same address and choosing a record that could
correct a discrepant reader reply. No specific address, replacement record,
correct port, or score is added by that instruction. Nevertheless the complete
original record set is already visible, so this remains externally guided
evidence comparison rather than an internalized extraction skill.

### Which returned record was actually discrepant?

Strict comparison of the two actual reader replies in this task yields:

| Address /source index | Reader reply versus own public record | Selected now? |
|---|---|---|
| `E_DEX6OHDHJP` /3 | Discrepant fields | No |
| `E_QQ43NOEYBQ` /2 | Exact | Yes |

The discrepant reply is retained verbatim:

```text
actual:   EVENT E_DEX6OHDHJP AT N_KGA6B2GC43 DID P_6Q379NEQYX GOT N_R2R3W7QECX EVIDENCE R_O32FCXUDYO
expected: EVENT E_DEX6OHDHJP AT N_IRD6ZSHY2B DID P_FWMNJO5UYN GOT N_DH2AYPUMUT EVIDENCE R_3KI5HYYQOV
```

Thus the guided output does **not identify the source record for the observed
reader discrepancy**. This is an interpretation of the new task criterion,
not a post-hoc source-admission rejection. Source2 remains accurate evidence
about the committed non-goal option, and its broader corrective usefulness has
not been tested. No source3 substitution or automatic repeat fit is warranted
by this audit.

### Timing, hashes, and preservation

Native run timing: **11:59:25.041794–12:00:20.745168 UTC**, September14,
2026;55.703374s elapsed including setup. The earlier11:59:24 launch time refers
to the guardian rather than the native RESULT start. Recorded input is
**1032 tokens** versus1010 for original reselection; both emit52 IDs, terminal
and untruncated. The same greedy2048-input/160-output limits apply. There is one
fresh selection call, no fresh route/read evaluation, and no fit. Dollar cost
and isolated generation time are not available.

Frozen wrapper commit:
`38a1044e5cc77fa6b3bd85effe12ac566ded5ddd`; its captured SHA matches the Git blob:
`210c6ccbad864b922484068a7213ef84ee8b1588ffc82730c63a67e03408eee7`.
The imported `e3a575d7` driver and pure selector hashes remain those verified
above. New evidence anchors:

| File under guided `run/` | SHA-256 |
|---|---|
| `RESULT.json` | `54a926f7cd4b448a7e3e5bccd65cb23ed6353976472d717ceed8837ba095c86d` |
| `SELECTION.json` | `25c1b2a2950bd345b51c7236030cffedafaddb9fbf183851400a32dcbc5c2e95` |
| `CALL_000.json` | `426c1f352b1eadfd53854eb2115658ef689f3593bf4201df33677871660b77e2` |
| `CORRECTION_CASES.json` | `b12e45d300505b32a0285c63f8aebee3a89b5c06318102ff020b92ffaf15c349` |

New `reader_audit/` capture, archive, remote hash manifest, and
`READER_AUDIT.json` reside within the same owned ignored artifact root. All16
new captured files,74587 bytes, match remote hashes. Previous attempt1/2 raw
captures and audit records remain intact. Reproduction:

```bash
python3 -B gpu_artifacts_local/astra_corrective_reselection_independent_20260914/replay.py reader_audit
```

It passes with `no_native_imports=true`; original attempt1/2 replay paths also
continue to pass. No new repository tests or source changes.

### Proposed ADDRESS channel: an untested mechanism hypothesis

Main's next prospective idea is a pointer-only `ADDRESS <event_id>` response to
test conflict between full-EVENT memory completion and selection. At this audit
request it was not launched, and this supplement reports no pointer result.

Identical full-EVENT responses under two instructions are compatible with an
output-format/completion bias, but do not establish it. Alternative explanations
include failure to use the discrepancy instruction, salience of a rehearsed
record or the most recent accurate reader reply, and selection of negative-option
evidence. No internal processing mechanism is observed here.

A pointer instruction would change the response contract, completion length,
and copying burden as well as the EVENT-format cue. A later changed address
could show sensitivity to that interface on this one payload, not uniquely
prove interference, improved learned selection, or memory repair. A later
unchanged address would likewise not identify a single cause. Any mechanical
address-to-existing-row join should remain distinct from generated new EVENT
content and from downstream utility; no pointer choice has been fitted here.
The investigation is adaptive and single-case, not independent confirmation.

Supplement and guided capture released to Main. No gate, fit, new probe,
repair, or commit performed by this reader.

## Supplemental terminal result: pointer contract rejects bare source2 identifier

Added September14,2026 UTC. Independent capture of
`/tmp/astra_pointer_selection_20260914_attempt1` completes the pointer probe
described prospectively above. Main has closed all same-error prompt variants
without a further memory fit. Earlier attempts, full-EVENT outputs, and their
interpretations remain preserved; this supplement does not repair or rescore
them.

### Exact raw output and strict disposition

The whole raw response is the following bare identifier, with no final LF:

```text
E_QQ43NOEYBQ
```

The required contract is `ADDRESS <event_id>` or standalone NONE. The output
omits the literal `ADDRESS ` prefix. Replaying the frozen pointer selector
therefore gives:

```text
status: REJECTED
error: ValueError('pointer_not_exact_source_address')
admitted_selections: 0
chosen_source_indexes: [null]
selected_event: null
row_source_indexes: []
```

The bare text literally matches the address of original **source2**, already
in prior selected set[0,2]. This descriptive byte match is **not admission**:
the strict recorded selection remains null, not[2]. No prefix is prepended,
identifier repaired, original EVENT mechanically copied, or eight-row corpus
constructed. It is neither a valid pointer nor a standalone abstention.

The distinction from the full-EVENT probes matters: those produced admitted,
source-valid negative-option records. Here the response fails the declared
output contract. That does not make the underlying source2 record false or
useless negative evidence. There is **no newly admitted material**, no fit,
and no evidence of utility or improved selection from this response.

### Same-source comparison and replay

The native run is terminal `RESELECTION_CAPTURED_NO_FIT`, with1 expected and
actual call,0 admitted pointers,0 fits, parent absent, and recorded unchanged
base/adapter state. A terminal run is not synonymous with successful source
admission; the rejection is preserved inside SELECTION rather than mislabelled
as infrastructure failure.

The same post-corrective actor state, generating AFTER, train receipt, inherited
collection, and prior source[0,2] joins pass again. `INPUTS.json` remains
byte-identical to the two preceding successful reselection conditions. All four
actual AFTER route records reconstruct the same single public error at task
index3, and all four inherited public EVENT records remain available.

The user payload is byte-identical to both preceding conditions. Frozen
`POINTER_SYSTEM` is the reader-audit system with only its response instruction
replaced by the ADDRESS form; the task evidence, ordering, and discrepancy
instruction are unchanged. Prepared/run cases and actual CALL messages exactly
match this reconstruction. The selected record would still have been retained
irrespective of goal match **if** the emitted syntax had met the source-pointer
contract; the rejection here is specifically the missing prefix.

For independent replay, the captured wrapper's `select_pointers` is executed
with an in-memory callback returning the already captured response and with
artifact writes intercepted in memory. No native Engine or generation is
invoked. Every resulting document—including the rejection, empty row list,
CALL, and complete SELECTION—matches captured JSON, and returned summary fields
match RESULT. The old replay paths continue to pass. Actual task3 reader
comparison remains source3 discrepant/source2 exact; this fact does not alter
the parser or justify salvaging the bare pointer.

### Budgets, timing, and custody

One terminal, untruncated generation: **1016 input tokens,11 emitted token IDs**,
within the unchanged2048/160 bounds. Native timing is
**12:02:54.228034–12:03:48.175166 UTC**, September14,2026;
53.947132s elapsed including setup. No route/read evaluation or fit was added;
isolated generation time and dollar cost are not recorded.

Frozen wrapper commit:
`969f115561831cf8237eb8d7cb267e78ed2016d5`.
Captured wrapper SHA matches the frozen Git blob:
`eeb4e068b998e54bad263d09232c0e9c46a1a32f2ed1edf8f0ebb6fdcbb59769`.
Imported driver/selector remain the verified `e3a575d7` source. Key hashes:

| File under pointer `run/` | SHA-256 |
|---|---|
| `RESULT.json` | `4b01a826d9d06242218e1a65b31e05dfce6b7cc04bea6eee56af647fb3e5f549` |
| `SELECTION.json` | `696fc48d7c1d5fdf260cfa13a634c85f35620c98eb46f7fdcace460ccf4169fb` |
| `CORRECTION_CASES.json` | `ec5a4a5dddc7b53a8d89c1456bdbfac9598a815a12baec98fa2487f1777bf26c` |
| `INPUTS.json` | `6036bfef38c930c6e84ec191bbcf8cb3ed8c8bd938270f0a3e6979b9bda95018` |

Owned `pointer/` capture, archive, hash manifest, and `POINTER_AUDIT.json` are
under the same ignored independent root. All16 new captured files,70076 bytes,
match remote hashes. All earlier raw records remain intact. No model, adapter,
or tokenizer binaries were copied. Reproduction:

```bash
python3 -B gpu_artifacts_local/astra_corrective_reselection_independent_20260914/replay.py pointer
```

The replay passes with `no_native_imports=true` and preserves the strict
rejection. There are no new repository code edits, test changes, native runs,
or commits by this auditor.

### Interpretation and branch closure

The pointer instruction changes the output shape from a full EVENT to a bare
address, but does not produce a valid ADDRESS response or a new source address.
It therefore does not demonstrate that changing the output channel recovered
useful selection. The format/completion-conflict hypothesis remains unisolated:
syntax compliance, prior rehearsal salience, discrepancy processing, and
negative-option selection are still plausible contributors. A one-case adaptive
sequence cannot establish a unique internal cause, a general deficit, or
internalized improvement.

Main's next activity is a separate developmental selection-skill teaching
experiment, not another repetition of this memory fit. This pointer audit does
not evaluate or claim results for its proposed80-call collection, conditional
paired200-update fits, or parent-removed readouts. Those require their own actual
evidence. All same-error variants reported here close without a further fit;
no additional prompt variant or execution gate is proposed by this reader.

Pointer supplement and owned capture released to Main, with strict failure and
all earlier complete records preserved.
