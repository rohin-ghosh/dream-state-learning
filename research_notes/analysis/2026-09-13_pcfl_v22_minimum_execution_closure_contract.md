# PCFL v2.2: minimum execution-closure contract

**Date:** 2026-09-13 UTC  
**Scope:** execution-closure specification only; no source/runtime/test edit,
tokenizer or model call, fixture generation, fit, adapter, or GPU work

## Ruling

Close the five open seams with **one prepared execution contract and one
CPU-only materializer/validator**, not another scientific proposal. The
contract is sealed after offline tokenizer binding and before the first model
generation. From then on, runtime code may substitute exact admitted child
span hashes into already-named structural slots, but may not choose a renderer,
parser, replay source, batch, cut, address, calibration branch, denominator, or
resource row.

This does not add machinery to THINK/DREAM/SLEEP, reopen the passed world, or
delay unrelated bounded diagnostics. It is the smallest bridge from the
current partial CPU fixture to an auditable PCFL v2.2 launch.

## 1. Existing authority and precedence

The prepared contract must pin these exact current files and hashes:

| role | file | SHA-256 |
|---|---|---|
| base scientific protocol | `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md` | `222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456` |
| controlling writer delta | `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md` | `683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca` |
| literal v2.1 preparation bindings retained except where superseded | `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md` | `5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd` |
| implementation API and test denominators | `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md` | `f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679` |
| finite request interpretation | `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md` | `599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b` |
| five-seam closure ruling, including conservative HIGH trigger | `research_notes/analysis/2026-09-13_pcfl_v22_execution_readiness_audit.md` | `deb3b51abde362a0d35f41295b565c9b5ef02d7d77757644ae5834294e539c13` |

Precedence is literal: this complete prepared contract controls execution;
v2.2 supersedes only the boundaries named in its Section 1; all unaffected
v2.1 science and literal bindings remain. The runtime must not read prose to
resolve a conflict. Source-pin drift, an unknown field, or an unresolved value
fails preparation.

The archived partial fixture
`research_notes/astra_memos/receipts_20260912/astra_pcfl_world_core_20260913.py`
(`bac33dc30d6e34d2e18fdc967edb758b58ae432a8ce69995473903a46d7b580e`)
and its 20-test suite
(`15fdf91ead8f1da1ce0a488767b02f83f1e6e9eeb0d81286db9b51b6ac661df4`)
are reusable
implementation evidence, **not authority**. They explicitly report
`ready_for_model_calls=False` and leave the probe schema, tokenizer inventory,
full projections, formation compiler, and schedules open.

## 2. One contract, three files

Expected builder-owned source and test paths:

```text
organism_v6/pcfl_vertical_prepare.py       # pure materializer + validator
tests/test_pcfl_vertical_prepare.py        # all closure tests below
<run_root>/PREPARE/execution_contract.json # sole prepared execution input
<run_root>/PREPARE/execution_contract.sha256
<run_root>/PREPARE/validation_report.json  # evidence only, not authority
```

`execution_contract.json` is closed-schema canonical JSON. Its sidecar hashes
the exact canonical payload. The validator has no model, training, network,
GPU, or subprocess path. It may use the pinned tokenizer offline while
materializing, or verify an exact tokenizer-measurement receipt supplied by
native preparation. Either way, the contract records the tokenizer revision,
files, chat-template hash, every tokenization result used, and the validator
source hash.

Later formation receipts are not a second contract. They only bind
`structural_slot_id -> exact child span/hash` and must fail if a required slot
is absent. They cannot change the contract's slot, replay, batch, cut, request,
or seed assignments.

## 3. Minimum closed schema

### A. One v2.2 source of truth

The top level needs:

- `schema`, canonicalization rule, source pins, preparer/validator hashes, and
  exact base/model/tokenizer/chat-template/environment pins;
- all fixed constants: 4 excluded roots, 1 disposable root, 2 DEV roots;
  seven DEV fits/root; 20 slots, 8 views, 160 examples/epoch, batch 4, five
  epochs, 200 updates/fit; rank 8/alpha 16/dropout .05; clean C0 and fresh
  optimizer; exact AdamW fields and gradient clip 1.0;
- the v2.2 branches: 14 DEV fits plus mandatory `CAL_LOW` and optional
  `CAL_HIGH`, hence 15/16 fits and 3,000/3,200 updates; and
- explicit prohibitions: no loss-active PAD request/target, target-token
  equalization/reserve, arm-local random shuffle, trained treatment `MISS`,
  warm start, checkpoint choice, retry, replacement root, or output-derived
  decision. Ordinary post-EOS tensor padding is allowed only with
  `attention_mask=0` and label `-100`.

The exact v2.2 slot rosters are data, not reconstructed by runtime:

```text
S1_AUTH          17 first blocks + 3 authentic EVENT replays
S1_ATOMS         14 first blocks + 6 authentic EVENT replays
S1_EVENT_TWIN    17 first blocks + 3 twin EVENT replays
S1_LINK_PERMUTE  17 first blocks + 3 authentic EVENT replays
S2_FULL_R0/R1    19 first blocks + 1 authentic OLD EVENT replay
S2_OLD_REPLAY    17 first blocks + 2 OLD EVENT + 1 OLD LINK replay
```

Active target/context tokens and FLOPs are reported; equality is never
asserted. A contract containing `PAD_S1_*`, `PAD_S2_*`, `loss_active_pad`,
`equal_target_tokens`, or the obsolete 14-fit-only campaign arithmetic is
invalid.

### B. Exact score-bearing bytes and parsing

`render_registry` must carry exact UTF-8 bytes, final-LF policy, placement,
ordering, separator, and task join for all ten zero-fit projections:

```text
EXACT_WITNESSED_GRAPH  FULL_CHILD_TEXT  EVENT_ATOMS_TEXT
ACTIVE_LINKED_TEXT     NATIVE_CONTEXT   RAW_EPISODIC
OLD_ONLY_TEXT          NEW_ONLY_TEXT    NONE_OFF          WRONG_ROOT
```

It also embeds every route/formation/READ/reachout/canary prompt, `W0..W8`,
and the 64-item `NATIVE_CONTEXT` retention render. `W8` is one literal unseen
wrapper and is never loss-active. Every dynamic join is a typed placeholder
with one allowed substitution class; no free string assembly remains.

`parser_registry` must bind:

- strict EVENT, LINK, READ, ROUTE, EXPLORE, and PROBE grammars;
- strict memory success as byte identity with the registered block;
- the exact semantic envelope, including the only permitted fence handling,
  row count/order, terminal-LF handling, and a rule that extra prose or an
  extra usable row cannot count;
- a finite literal byte list of accepted non-row refusals (including the exact
  treatment of terminal LF); and
- `usable_false_row=true` whenever any parsable EVENT/LINK row is emitted on
  an absent/wrong request or differs from that request's registered rows,
  even if a refusal or prose is also present.

`diagnostic_registry` binds the complete scorer-only wrong-block universe for
each address: every candidate is pre-output, not the correct block,
type- and row-count-matched, and identified by hash. Candidates never enter a
prompt. It also binds the grammar/content NLL boundary: a token whose offset
overlaps any opaque-field byte span is content (boundary overlap resolves to
content); separators, fixed grammar, and EOS are grammar. The validator rejects
an empty eligible wrong universe or an unclassified supervised token.

### C. Immutable replay identities and joint schedules

`root_registry` enumerates all excluded/disposable/DEV roots and their role,
seed, O/R/D/goal assignments, opaque inventory, render/order assignments, and
primary reachout choice. `root_skeleton_hash` is over a closed canonical
pre-generation object containing only the schema/source-pin digest, structural
topology and slot IDs, opaque inventory, public/private render IDs, roots,
seeds, cuts, addresses, and counterpart maps. Child generations, derivative
bytes, scores, losses, and future runtime receipts are forbidden fields.

`slot_registry` gives every first-occurrence/control block a structural slot,
row type, ordered support-span IDs, derivative/lineage taint, request shape,
and exact counterpart in each paired arm. The S1 four-arm and S2 three-arm
counterpart maps are total wherever treatment does not replace a position.

`replay_registry` stores the output of v2.2 Section 2.1's rotation/subset
algorithm: quota, eligible structural slots, selected distinct sources,
counterpart positions, support appearance counts, and selection-domain hash.
The selection uses only `root_skeleton_hash`, stage, comparison family,
row type, and fixed suffix. No child bytes or arm-specific favorable choice
may affect it.

`batch_registry` contains all five epoch assignments for CAL and every DEV
arm: exactly 40 batches of four `(slot_id, view_id)` items per epoch. Collision
is intersection of underlying support-span IDs, not equality of enclosing
response-block hashes. It proves, per epoch:

- all 160 items occur once;
- no repeated query slot, wrapper view of one slot, or support span in a batch;
- S1 has exactly 24 one-LINK batches and no batch with two LINK items;
- S2 has exactly 32 one-LINK batches and no batch with two LINK items;
- every NEW-bearing view occupies its own batch with three OLD/replay items;
- unchanged counterparts occupy the same indexed positions across paired
  arms; and
- the deterministic joint backtracker found the first solution under the
  frozen order. Failure is `VS_ASSAY_INVALID`; random fallback is forbidden.

### D. One literal calibration state machine

`calibration` must encode this table, not prose:

1. Run `CAL_LOW` from clean C0 at LR `3e-5`.
2. If custody, masks, schedule, 200 finite updates, truncation, or complete
   readout is invalid, stop invalid; HIGH is forbidden.
3. If LOW fails locality/refusal (`>=15/16`, zero usable false rows), generic
   canary, or 64-item PCFL retention, stop writer qualification; HIGH is
   forbidden.
4. If LOW passes those safety gates and both EVENT and LINK acquisition gates,
   select LOW.
5. Only if LOW is valid and safe but misses an EVENT or LINK semantic/strict
   acquisition threshold may `CAL_HIGH` run at LR `3e-4`.
6. HIGH starts independently from the same clean C0 tensors and uses identical
   corpus, five epoch schedules, initialization/dropout/readout seeds, masks,
   and optimizer fields. Select it only if the complete writer gate passes;
   otherwise `VS_WRITER_QUALIFICATION_FAIL`.

Native route, W8, NLL, margins, and confusion are diagnostic and cannot trigger
HIGH. Exact `cal/*` seed domains and every Boolean transition are enumerated.

### E. Cuts, addresses, and complete work

`intervention_registry` must enumerate, before output, each task item affected
by the S1 critical-LINK, reachout OLD-memory, and S2 OLD/NEW service cuts. Each
entry names the exact structural request(s), registered response-block/support
IDs, replacement bytes `MISS`, endpoint, wrapper, comparison-block seed, and
unaffected mate. The pure graph/service oracle must prove that the named cut
removes the intended LINK/OLD/NEW carrier and that its registered denominator
can attain the stated drop threshold. Runtime may not choose “the critical
read” from an observed trace.

`locality_registry` enumerates the eight unseen and eight wrong-root addresses
for every applicable root/state, their root-disjoint counterpart, `W0..W7`
assignment, and shared comparison seed. Unseen addresses occur nowhere in a
supported/replay target; wrong-root addresses are valid only in the named
other root; neither roster may depend on output.

`work_registry` has one immutable row per logical task, model generation,
deterministic service lookup, forward-score sequence, fit, and cold load. Each
row names stage, root, state/arm, endpoint, prompt/render hash, mount, seed,
input/output/returned-token ceilings, allowed ancestry, denominator, GPU UUID,
and conditional branch. It must reproduce the v2.1 bound core
(`1,106` single-call actor tasks, `576` service-loop tasks, `324` direct reads,
`76` formation calls, `280` canary calls) and then explicitly add every v2.2
item rather than hiding it in those totals:

- 64 paired PCFL-retention calls for each of 14 DEV final fits and each
  executed CAL fit: exactly `960` added calls on LOW-only and `1,024` if HIGH
  runs; the global C0 64-item panel is reused once;
- CAL local/acquisition/locality/canary/native/W8/diagnostic work;
- W8 once for every supported address of every named state;
- every grammar/content NLL and correct-versus-wrong forward-score sequence;
- all candidate-free confusion generations (normally reused from registered
  direct reads rather than regenerated); and
- exact cold loads and four preparation profiles.

The validator recomputes both conditional branches, not one favorable path:
15/16 fits, 3,000/3,200 updates, exact per-fit 200-update schedules, device
product A40, summed device-seconds rather than parallel wall time, and the
separate training/DEV-inference/CAL-readout caps. It rejects any denominator
without a work row, work row without a score purpose, retry budget, unstated
load, A100 conversion, or use of natural early EOS as planned denominator
reduction. The contract predeclares each profile's path, shape, cap, and
accounting rule. Profiles later produce immutable evidence receipts at those
paths; they never fill or mutate contract fields. The validator consumes the
sealed contract plus those receipts and emits the final validation report
before the first scientific generation.

## 4. Pure-CPU validation cases

The minimum test file should include these fail-closed cases:

1. canonical round-trip, closed schema, source-pin drift, sidecar mismatch,
   missing/unknown/duplicate fields;
2. injection of each obsolete PAD/equal-token/v2.1-only field, while proving
   masked tensor padding remains legal;
3. exact snapshots for all ten projections, retention render, prompts, and
   W0--W8; one-byte placement/order/separator mutations fail;
4. parser truth table: strict, semantic-only fenced, malformed/prose,
   missing/extra/duplicate row, multiple block, refusal, and usable false row;
5. wrong-block enumeration completeness and grammar/content offset boundary;
6. complete root/cube cardinality and a negative attempt to insert generated
   bytes into `root_skeleton_hash`;
7. total/injective counterpart maps and exact seven v2.2 20-slot rosters;
8. replay golden vectors, distinct-source quotas, balance objective, common
   positions, and output-byte perturbation invariance;
9. the adversarial support-overlap case `READ EVENT e0` versus
   `READ EVENTS_AT S_L`, plus all 5 x 40 x 4 batch invariants for every arm;
10. exhaustive CAL truth table, especially rejection of HIGH after locality,
    refusal, canary, retention, truncation, numerical, or custody failure;
11. exact cut/address coverage and oracle proof that OLD/NEW/LINK cuts remove
    their registered carrier without touching control mates;
12. LOW-only and HIGH-used work expansions, including exactly 960/1,024 added
    retention calls, every diagnostic sequence, load count, and no orphan
    denominator; and
13. profile/device-time arithmetic, wrong product/UUID, over-cap branch, and
    parallel-wall-time substitution rejection.

A success report must say only `execution_contract_valid=true` and enumerate
the five closed seams. It is preparation evidence, not a model ceiling,
qualified writer, PCFL result, or scientific pass.

## 5. What remains builder implementation

After this memo, Astra still must:

1. author the pure PCFL core and this preparer/validator in the committed tree,
   reusing the partial fixture only after replacing its provisional IDs/probe
   schema/projections;
2. run offline real-tokenizer materialization and seal the single contract;
3. patch or wrap `train_adapter_v3.py` for explicit AdamW, clipping,
   fail-on-nonfinite, exact presealed batches, and per-update
   loss/gradient/RNG/tensor receipts;
4. implement `gpu/astra_pcfl_vertical_dev.py` so `prepare`, `verify`, workers,
   and reduction consume the contract hash and never recompute scientific
   choices;
5. finish the scripted native/DAG/custody tests already named in the exact
   build ledger; and
6. perform the four bound preparation profiles, seal their receipt hashes,
   rerun the CPU validator without changing the contract, then follow the
   frozen order: excluded-root ceilings -> disposable formation/CAL -> two
   untouched DEV roots.

Expected remaining implementation paths from the existing ledger are:

```text
organism_v6/pcfl_vertical_dev.py
organism_v6/pcfl_vertical_train.py        # only if a narrow wrapper is safer
gpu/astra_pcfl_vertical_dev.py
tests/test_pcfl_vertical_dev.py
tests/test_astra_pcfl_vertical_dev.py
```

Execution readiness is closed only when the committed CPU suite produces a
valid contract/report, the real-tokenizer and profile bindings validate, and
the native runtime demonstrably rejects any plan/hash other than that sealed
contract. No new parenting, Q0, rank, compression, or C11 work is a dependency.
