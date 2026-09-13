# PCFL v2.2 DEV execution-readiness audit

**Date:** 2026-09-13 UTC  
**Role:** fresh builder-facing execution skeptic  
**Scope:** repository/source audit only; no source implementation, fixture
materialization, tokenizer/model call, training, adapter mutation, or GPU work

## Verdict: REWORK before execution; retain the scientific design

The v2.2 scientific repair is the correct next experiment. It removes the
loss-active PAD confound, keeps the child's exact authored bytes, adds
truthful replay, and adds the task-specific retention test demanded by the
terminal own-record result. I found no reason to replace the world, add a rank
sweep, or run another proxy first.

It is **not launch-ready**. The protocol is a delta over several v2.1 documents,
while all named PCFL implementation/test files are still absent. More
importantly, five preparation choices that determine scores remain unbound:
the exact zero-fit/retention memory render, the cut map, the semantic/refusal
parser, the replay counterpart/support map, and the CAL_HIGH trigger. The
v2.1 request ledger also omits every new v2.2 retention and diagnostic call,
so `19--20 A40-hours` is a cap arithmetic statement, not yet an executable
resource receipt.

Do not spend GPU time until the short closure checklist below passes. This is
implementation closure, not another architecture round.

## 1. What exists now

### Passed prospective science

- v2.1 defines the opaque route world, two-SLEEP chronology, child-span
  custody, seven fitted arms/root, candidate-free memory service, native
  endpoint, formation and route denominators, stop order, and bounded claims.
- The prospective binding register fixes the ordinary route, formation,
  reachout, writer-wrapper, canary, seed, and A40 placement text.
- v2.2 replaces trainable PAD with exact replay, specifies the 20-slot arm
  rosters, source-diverse scheduling constraints, LOW-then-HIGH writer
  qualification, task-specific retention thresholds, diagnostics, and the
  stricter connected-memory conjunction.
- Existing terminal evidence supports LOW-first: at `3e-5`, actual child
  records retained `18/30` exact semantic and `18/30` paraphrase reads while
  C0-correct Level-1 losses fell to `3/143`, versus `45/143` at the earlier
  high heat. This supports the direction; it does not replace PCFL
  qualification.

### Reusable code, but not PCFL implementation

- `organism_v6/train_adapter_v3.py` already supplies chat-template
  response-only masking, all-layer LoRA construction, bf16, no-pack mode,
  final-checkpoint saving, deterministic generic ordering, and basic training
  manifests.
- `organism_v6/l2_public_record_dev.py` and
  `gpu/astra_l2_public_record_dev.py` contain useful raw-before-feedback,
  process-isolation, stage, seal, custody, collection, and fail-closed runtime
  patterns.
- Q0/L2/semantic-carrier code contains reusable tensor/RNG hashing,
  candidate-free generation, semantic-versus-surface reporting, and bounded
  worker patterns.
- The old PCFL change trees are specifications/golden material, not an
  executable implementation of this world.

## 2. What is absent

Every implementation file named by the exact build ledger is currently
missing except the generic trainer and its old tests:

```text
MISSING organism_v6/pcfl_vertical_dev.py
MISSING gpu/astra_pcfl_vertical_dev.py
MISSING organism_v6/pcfl_vertical_train.py
MISSING tests/test_pcfl_vertical_dev.py
MISSING tests/test_astra_pcfl_vertical_dev.py
EXISTS organism_v6/train_adapter_v3.py
EXISTS tests/test_train_adapter_v3.py
```

The generic trainer is not sufficient as-is. It does not expose the frozen
AdamW fields, does not clip gradients, skips nonfinite batches rather than
failing, does not emit the required per-update loss/gradient/RNG/tensor
receipt, and cannot consume a different explicitly presealed batch assignment
for each epoch. Its group shuffle is not the v2.2 joint coupled scheduler.

Consequently none of these exists yet: the cube/two-oracle core; exact
EVENT/LINK admission; v2.2 replay materializer; joint batch solver; real
tokenizer seal; local service; native actor; formation runner; CAL runner;
tainted stage DAG; v2.2 retention panel runner; diagnostics; ordered reducer;
or terminal custody tree.

## 3. Five blocking specification seams

### A. Bind the actual v2.2 source of truth

The v2.1 build ledger and binding register still mandate PAD IDs, PAD search,
active-target-token equality, random/group shuffling, 14 fits/2,800 updates,
and a 17-hour cap. V2.2 supersedes those with truthful replay,
source-diverse schedules, 15--16 fits/3,000--3,200 updates, and 19--20 hours.

Produce one machine-readable v2.2 run spec whose validation rejects every
obsolete PAD/equal-token field. Do not let the builder choose which document
wins at runtime.

### B. Freeze every score-bearing renderer and parser

The register fixes the ordinary route prompt but never gives exact render
bytes/placement for `EXACT_WITNESSED_GRAPH`, `FULL_CHILD_TEXT`,
`EVENT_ATOMS_TEXT`, `NATIVE_CONTEXT`, `RAW_EPISODIC`, `OLD_ONLY_TEXT`,
`NEW_ONLY_TEXT`, or `WRONG_ROOT`. The new retention gate reuses
`NATIVE_CONTEXT`; without exact bytes, it is not yet a frozen 64-item panel.

Before any model call, bind:

- one exact memory header, placement, ordering, separator, and task join for
  every zero-fit projection and the retention panel;
- the exact semantic parser (including whether fences/prose/multiple rows can
  count), the finite registered non-row-refusal set, and false-row rule;
- the literal ninth wrapper; and
- the exact scorer-only wrong-block candidate universe and token-category
  boundary rule for the four diagnostics.

No parser or refusal registry may be revised after seeing a disposable, CAL,
or DEV generation.

### C. Freeze the replay/schedule identities, not just their algorithm

`root_skeleton_hash` is not yet a closed schema, and the structural
counterpart map is not enumerated. Define its canonical pre-native object and
prove that it excludes all generated/derivative bytes. Enumerate every
AUTH/ATOMS/TWIN/PERMUTE and FULL/OLD_REPLAY counterpart slot.

For the diversity rule, collision means **any overlap in underlying
support-row/span identities**, not merely equality of the enclosing multi-row
response-block hash. Otherwise `READ EVENT e0` and
`READ EVENTS_AT S_L` can enter one batch even though both train on `e0`.
Run the joint solver on structural placeholders before formation and prove a
solution for all seven arm shapes and all five epochs. Admission then only
substitutes exact bytes; it cannot change assignments.

### D. Resolve writer qualification literally

V2.2 alternates among three incompatible triggers:

- HIGH only if LOW misses semantic carriage;
- HIGH if LOW misses the whole writer gate; and
- HIGH after semantic/locality/canary/refusal misses, with retention omitted
  from that list.

For information/GPU-hour and the current evidence, bind this rule:

```text
run CAL_HIGH only when valid CAL_LOW passes custody, locality, generic
canary, PCFL retention, finite/truncation checks, but misses EVENT or LINK
acquisition; otherwise stop qualification
```

HIGH must start from the same clean C0 tensors, not LOW, and use the same
corpus/batches/init/dropout/readout seeds. Add exact `cal/*` seed domains.
Require the disposable root to meet the same `8/8 EVENT + 4/4 LINK` OLD
formation gate. The word "tune" cannot authorize prompt/parser repair inside
that root; failure requires a newly versioned protocol and a fresh disposable
root.

### E. Bind the causal cuts and updated work inventory

The documents demand critical LINK/OLD/NEW cuts but never name the exact
structural request/block replaced by `MISS`. Bind one cut map before native
output for:

- S1 link-service mediation;
- reachout OLD-memory mediation; and
- S2 OLD and NEW service mediation.

Also bind the eight unseen and eight wrong-root local addresses and their
wrapper/seed assignments. Otherwise a favorable address or cut can be chosen
after behavior is visible.

The v2.1 request ledger is no longer complete. At minimum, v2.2 adds the
64-request retention panel for every final fitted state: `14` DEV fits plus
`1--2` CAL fits, i.e. **960 or 1,024 new native calls**, while the existing
C0 64-item ceiling can be reused once. It also adds CAL carrier/locality/
canary reads, ninth-wrapper generations for every supported address, and
forward scoring for grammar/content NLL and every registered wrong-block
margin. Enumerate all of these, their cold loads and caps, then profile them.
Until that receipt exists, the 20-hour maximum is not demonstrated feasible.

## 4. Causal and power audit

- **No hidden answer leak found** in the fixed ordinary route, formation,
  reachout, or local READ prompts. Fresh addresses are typed storage handles,
  not answer candidates. The sterile post-S1 visibility rule is sound if the
  runtime enforces it byte-for-byte.
- **No arm-dependent optimizer-step count:** every arm has 20 slots, eight
  wrappers, batch four, five epochs, and 200 updates.
- **Arm token/FLOP exposure is intentionally unequal after PAD removal.** LINK
  and NEW blocks carry different target lengths, and ATOMS spends missing LINK
  slots on extra EVENT replay. Report active target/context tokens and charged
  device time per arm. Call the contrast fixed-slot/fixed-update, never
  token-matched or FLOP-matched.
- The AUTH-over-ATOMS contrast is conservative for EVENT rehearsal: ATOMS has
  six EVENT replays versus AUTH's three. An AUTH win therefore cannot be
  explained by more atom replay.
- No threshold is arithmetically impossible. The S1 critical-LINK drop of
  `6/16` has a maximum relevant half-panel effect of `8/16`, so the exact cut
  must target that half. The connected-service gate is nonetheless demanding:
  exact EVENT atoms are sufficient in the zero-fit ceiling and both systems
  have 12 reads. A null may mean links did not add value under this budget,
  not that EVENT memory failed. Preserve `EVENT_COMPOSITION_ONLY` rather than
  tuning read limits after seeing it.
- The root is the unit; two DEV roots cannot support a frequency or interval
  claim. The v2.2 labels correctly remain mechanism-development labels.

## 5. Builder checklist

### CPU/source closure — must all pass before tokenizer/model work

- [ ] Add the pure PCFL core, independent oracles, exact wire types, strict
  route/EVENT/LINK parsers, cuts, collision/entropy/projection audits.
- [ ] Merge v2.2 into one closed run spec; reject PAD and obsolete v2.1
  arithmetic.
- [ ] Bind all projection/retention renders, semantic/refusal rules, ninth
  wrapper, cut/address maps, CAL trigger/seeds, and diagnostic candidate sets.
- [ ] Implement replay selection and joint five-epoch batch solver over
  structural support sets; prove every arm schedule exists before generation.
- [ ] Unit-test no OLD text after S1, no service/evaluation/control ancestry,
  no output-derived seed/order, no parser repair, and no replacement root.

### Native preparation — still before scientific generation

- [ ] First-valid real-tokenizer opaque inventory; all namespaces and rows
  valid; no sequence truncation; 20 slots/160 singleton examples per fit.
- [ ] Exact per-arm target/context token receipts and response-type/exposure
  counts; no claim of token equality.
- [ ] Trainer proves explicit AdamW `(.9,.999), eps=1e-8, wd=.01`, grad clip
  `1.0`, exact sealed batches, 200 finite updates, final-only selection, and
  immutable numerical/tensor/RNG receipts.
- [ ] Updated request/load/token/device-time ledger includes all v2.2 CAL,
  retention, ninth-wrapper, and forward-score work and fits the 19/20-hour
  cap under charged A40 time.
- [ ] Scripted DAG tests fail at every ordered gate, preserve siblings and
  controls, restore the exact pre-evaluation AUTH snapshot, reject tainted
  ancestry, roll back without converting failure to success, and reduce once.

### GPU order — only after the preceding receipts are sealed

1. Four excluded-root zero-fit ceiling shards; stop if any mandatory ceiling
   or shortcut control fails.
2. One disposable OLD formation root; require all rows, then CAL_LOW; run
   CAL_HIGH only under the single frozen trigger above.
3. Only after one rate qualifies, open the two untouched DEV roots and follow
   the existing stage DAG. Stop each root at its first registered failure.

## Final disposition

**REWORK for execution readiness, PASS for scientific direction.** The next
valuable work is the actual PCFL core/materializer/runtime plus the five local
bindings above. Once those CPU/native-preparation receipts pass, launch PCFL
v2.2 directly. Do not insert another Q0, parenting, rank, or authored-memory
screen in front of it.

## Evidence cut

Audited at repository HEAD `8e0c0455` with controlling file SHA-256 values:

```text
222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456  v2.1 synthesis
683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca  v2.2 writer repair
5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd  prospective binding register
f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679  exact build ledger
9f96d8699f6088e872e56263f8a325a7849191a853a03093df479045919d13f5  implementation reuse map
7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7  train_adapter_v3.py
```
