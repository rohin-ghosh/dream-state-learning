# PCFL existing-asset reuse: fresh audit v1

Date: 2026-09-10

Status: **read-only source and authority audit; no implementation or execution
authority**. The only new artifact is this advisory. No model, tokenizer,
benchmark generation, GPU, training, or scientific run was used.

## Ruling

There is **no PCFL implementation package** in the tracked repository. In
particular, `pcfl_d0/` does not exist, although the abandoned D0 authority
manifest advertises 15 source and 17 test paths there. The only PCFL-named
Python is `research_loop/advisory/pcfl_crossover_receipt.py` plus its test; it
is byte-accounting machinery, not a world, reader, compiler, reducer, or
M-TEXT runner.

`feltcraft_symbolic_kernel` is the sole directly relevant executable kernel.
Its five current source bytes exactly match its frozen V7 scope-audit
manifest, and a fresh CPU-only invocation returned exit 0, all SK01--SK09
receipts passed, and the exact report SHA-256 was
`dce3fe74e5f4918f306dd365fad984bd3440c168348b92f7dbb5efa1652bccb4`.
That does **not** make it an authorized PCFL dependency: V7's ratification is
terminal and expressly preserves `promotion_to_rendered_or_model_stage` and
successor-input prohibitions, while its external `scope_audit.json` has
`passed:false`. A new PCFL-specific, exact-byte human approval may reuse the
five V7 source files unchanged, but must explicitly authorize the dependency
and close or replace the failed independent-review gate. No source rewrite is
needed merely to obtain that reuse authority.

The fastest path is therefore a thin PCFL-specific M0 layer over newly
reauthorized, byte-identical V7 primitives, followed by a separate M-TEXT
overlay. **Implement and authorize M0 as a standalone CPU package, but
co-design its narrow M-TEXT boundary now**: canonical semantic rows, renderer
and tokenizer/cut commitments, public reader return, prompt projection, and
receipt handoff. This avoids both a generic platform and a later incompatible
M0 redesign. Do not revive either historical bundle wholesale.

## Tracked inventory and formal state

The four audited trees are clean relative to `HEAD`
`b764a0e6064e4cec3fda046f63517177aab4ba07`. Aggregate hashes below are
SHA-256 over the sorted `shasum -a 256` manifest (hash plus path) of every
tracked file in the tree.

| Asset | Tracked bytes | What actually exists | Formal state |
|---|---:|---|---|
| `feltcraft_symbolic_kernel/` | 5 files; aggregate `ecd18b3d27c3c54e76b5b0e3ac00786c322bd323574c169d3045ea52f01c956d` | Pure-Python finite enumerator, graph/twin/cost/deletion checkers, four projection surfaces, golden report, exhaustive SK01--SK09 runner | V7 intake is `human_approved`, but only for the terminal symbolic kernel. External SK10 scope audit is `passed:false`; no PCFL/successor authority. |
| `research_loop/changes/chg_20260901_pcfl_d0_exact_v2/` | 17 files; aggregate `0f2a11bfcc9ed62d79c5152abaf4629767035fccc85bbe5f3e6a31344b7e5f20` | Substantial PCFL-13 schemas, world/controller/reader/compiler/statistics/claim contracts and candidate goldens; no source | `authority_manifest.json` says `proposed_not_effective`; `cross_audit.md` says `REWORK — not ratifiable and not implementable`. Sixteen of 18 named companion design files exist, but all seven required deliberation/ratification files and two companions are absent. |
| `research_loop/changes/chg_20260901_pcfl_execution_bundle_v1/` | 11 files; aggregate `684e08ee978ff0568bb534bc469de12d5be9a21d13eeedde33083b68898c7288` | Proposal/deliberation records and three short prompts; no schema package, source, test, deck, or receipt | Intake `human_required`, `implementation_authorized:false`; consensus `rework`, human decision pending/implementation forbidden, with eight unresolved disagreements and 14 accepted concerns. |
| `research_loop/changes/chg_20260902_pcfl_compose_self_revision_text_dev_v2/` | 38 files; aggregate `50168b04add4ed5e5be57d93f33be4a3aece4fd7962aaea1c1a35baaa0a49dc8` | Rich proposal-only schemas/contracts, prompt candidates, ledgers and fixture specifications; no implementation, materialized Stage-0 fixture catalog, executable snapshot, or results | Intake `human_required`, `implementation_authorized:false`; consensus `rework`, human decision pending/implementation forbidden. Six adjudications remain unresolved. |

Adjacent `rml_d0/` (22 tracked files; aggregate
`0f069946cc4598102528a28bb8125f1ee1592c0939c605324d454e0ccb48fc07`)
and `rml_stage_b/` (12 files; aggregate
`0fedf7872f23c1157ed4e35d72c7b636af4c9a9c7a2d499b58e18572f4ba091e`)
are real source packages, but they are RML implementations, not PCFL. Their
canonicalization, isolation, finite-state, certificate, and reducer patterns
may be consulted; making them a runtime abstraction would create the generic
platform this path is meant to avoid. Copy or import nothing from them without
the new PCFL scope naming exact hashes and semantics.

## Asset-by-asset disposition

### 1. FeltCraft V7 symbolic kernel

Reusable unchanged after explicit PCFL reauthorization:

- finite enumeration and graph rendering in `kernel.py`;
- the involutive twin mapping, exact cost arithmetic, and bridge-deletion
  checker;
- the fail-closed `DomainError` public surfaces;
- the exact SK01--SK09 comparator and golden-report validator.

These are useful only as PCFL M0 **primitives**. V7 contains no PCFL renderer,
event/atom identity, source life, target phase machine, finite reader,
provenance admission, M reducer, text carrier, model call, DREAM/SLEEP, or
LoRA path. Its own claim policy explicitly says it is not a benchmark or fair
atoms/graph/RAG baseline.

Current authority blocker: V7's human ratification authorizes only
`pure_cpu_symbolic_alignment_enumerator`,
`symbolic_golden_report_and_scope_audit`, and
`symbolic_kernel_unit_and_property_tests`. The change and consensus preserve
no promotion or successor input. The scope receipt failed because no required
fresh independent **human** semantic review was obtained, its reviewer had
pre-request context, required semantic attestations were false, and no
post-review human governance adjudication was obtained. Therefore M0 may
reference these bytes as prior art now, but may not call/import them under the
old authority.

### 2. PCFL-D0 exact-v2 design bundle

The reusable semantic core is unusually concrete: the 103,680-world finite
algebra and dagger twins, exact four-view compiler rule, separation of
`HW-SOLVE`/`ATOM-CEILING`/bounded authentic-reader estimands, fixed reader and
workspace budgets, SHA-256 counter-RNG grammar, root-only reduction intent,
and narrow fixed-deck claim firewall. Those clauses should be lifted by hash
or copied with explicit provenance into the new M0 proposal instead of being
redesigned.

No D0 file is currently executable authority. The manifest's own precondition
is impossible in this checkout: missing companions are `human_directive.txt`
and `experiment_spec.md`; missing authority-chain files are `change.json`,
both interpretations, `critique.json`, `consensus.json`, `intake.state.json`,
and `human_ratification.json`. The advertised `pcfl_d0/` package is wholly
absent.

The cross-audit's nine blocking repairs must be disposed before the first M0
code edit:

1. freeze renderer, tokenizer, BOS/EOS and complete-event cut bytes;
2. materialize the actual 64-pair deck, counters, rejection histories, target
   proposals, source cuts, and reachability certificates before implementation;
3. bind runtime/stdlib/native hashes and the resource/power certificate;
4. resolve DEV opened by split/controller contracts but denied by authority;
5. specify support admission for fit/prediction/contradiction, aliases,
   revisions, cycles, diamonds and root deduplication;
6. condition exact Bayes on the full deck-construction kernel, with a real
   103,680-world golden;
7. authorize or replace the derived-transform anchor that violates the
   inherited copy-origin rule;
8. replace invalid/placeholder goldens and digests with protocol-valid bytes;
9. freeze the 1,000-transition timing fixture and expected digest.

Thus the coherent algebra/budgets/claim limits can remain semantically
unchanged, but the old authority manifest, goldens, deck/split surface,
Bayes/support rules, and runtime certificate cannot be reused as-is.

### 3. PCFL execution bundle v1

This is historical problem decomposition, not a starting implementation. Its
consensus selected rework for: exact allowlist/resources; a single four-view
compiler contract; accepted-visible-item Bayes plus three distinct memory
controllers; exhaustive reader reachability and complete paired input
collisions; coherent binding/twin interventions; no-memory/comparator-qualified
claim language; exact estimators/CPU limits; and strict separation of D0
checker conformance from future model evidence. Those eight dispositions are
good requirements and are already more concretely expressed in D0 exact-v2.

The three prompt files may be used only as prose sketches. They lack the exact
renderer/tokenizer/schema/state closure needed by M-TEXT, and the bundle's
consensus forbids implementation. Reusing v1 itself would regress to the
defects its own consensus accepted.

### 4. Compose/self-revision text DEV v2

Useful M-TEXT references are the typed semantic/event schemas, visibility and
private-field registries, recurrent resolver/reducer grammar, two-lane
compiler/provenance concept, RNG/resource/call-ledger schemas, prompt
candidates, fail-closed gate receipt, and static-fixture checklist. They are
reference material, not a library or runnable overlay.

The exact unresolved consensus blockers are:

- `ADJ-D01`: render every live recurrent workspace value and both authorized
  read receipts in one typed/token-accounted next-call envelope; no hidden
  transcript/KV/history;
- `ADJ-D02`: add the explicit public actor next-state/action-validity feedback
  edge needed for multi-step USE, excluding truth/score/evaluation/private data;
- `ADJ-D03`: remove model-visible `target_id`, or prove a specifically
  authorized opaque label answer-neutral and treatment-invariant;
- `ADJ-D04`: treat echoed query text as tainted model state and causally
  separate it from retrieved NOTE/AST value;
- `ADJ-D08`: freeze a deterministic workload-matched resource forecast and
  strict 18-device-hour/24-wall-hour `NOT_RUN` rule;
- `ADJ-D09`: add positive diamond and negative self-edge/back-edge/true-cycle
  provenance fixtures.

Resolved adjudications still constrain reuse: “compose/self-revision” is only
a label for nonsemantic selected-object replacement; there is no mediation,
recurrence, online/lifetime, LoRA, generalization, comparator-superiority, or
paper-efficacy result; conditional Stage-2 arithmetic has no population
inference; any repair requires a new full hash-bound chain. Consequently, do
not inherit its 3,414-call roster or generic experiment shell. For M-TEXT,
select only the PCFL-specific schema/visibility/reducer ideas, repair the six
blockers, freeze actual model-facing bytes, and deliberate that smaller packet.

## Minimum reuse route

1. Create one compact M0 authority packet that lists only a PCFL overlay,
   exact fixtures, and tests. Bind the five unchanged V7 source hashes as a
   read-only dependency and explicitly authorize this successor use. Obtain a
   fresh independent scope review; do not claim the failed V7 SK10 receipt.
2. Import only the coherent D0 finite algebra, twin, controller separation,
   reader budgets, four-view rule, RNG grammar, reducer unit, and claim ceiling.
   Repair and freeze the nine cross-audit areas before authorizing code. The
   overlay should verify frozen inputs, never choose scientific deck bytes.
3. Implement no shared platform: direct PCFL modules for canonical objects,
   finite world/phase transitions, reader, compiler/provenance, interventions,
   exact controllers, root reducer, and preflight are sufficient. RML packages
   are patterns, not dependencies.
4. Co-design the exact M0-to-M-TEXT public byte interface in the M0 packet,
   because deck acceptance and the post-window property depend on frozen
   renderer/tokenizer cuts. Still implement, test, and authorize M0 as a
   standalone CPU package. Deliberate M-TEXT execution separately after M0.
   It may consume frozen M0 public
   objects and receipts read-only, while adding only exact text rendering,
   tokenizer/chat/parser bytes, recurrent actor feedback, explicit text
   carrier, model-call isolation, and M-specific endpoint/control reduction.
   It inherits no LoRA, L, C, parenting, generic plugin, or 3,414-call roster.

## Key SHA-256 evidence

- Governing `AGENTS.md`:
  `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`.
- V7 source: `__init__.py`
  `2274ed4d5ef1eaa63357f113a5a3f0f82a4321594c65596283e71601c68081e9`;
  `kernel.py`
  `c68771ec3d5f67193766cc56c16f152c5bc757a7e221c31a826b7649f2b69fdc`;
  `report.py`
  `41133956ad9f36842d439eea8df82f5f1407fb59e36b52a0510aa3dbd61921d3`;
  `run.py`
  `56f7e8d703bb7f3737f725d5b09c7ad3c12ce2a373308356c9c77b62a2b5b046`;
  `test_kernel.py`
  `d4a8a995be71a08413bdd718eebd25d3047a4c5b5edd52e3d1f3c715d3517219`.
- V7 authority: `change.json`
  `f6f3181db906b915d4711fc701cac4aee464fdd9b21bd0dbb41c95dc976ca83b`;
  `consensus.json`
  `4250f8fa1678fbb91f79803a9b14336fbf84d2554fddc5409673db2502cc1567`;
  `human_ratification.json`
  `d67f446f7b4cb11024033c49fd8b1dcb75424e1f8bf7efb1a64cadbdb02c1fb5`;
  failed `scope_audit.json`
  `1ed5411ee562f71bf0214f0e4763471d8b8ca748046aab377942a517823c84ec`.
- D0: `authority_manifest.json`
  `edb34db7f7572e4f51798ecb611cc7b59de8d78b3fa424cd15de353a2f44090e`;
  `cross_audit.md`
  `8c4ce353f69b38cdb4931ff8916aade38654055fec66fcd82084b4b81900a4fa`;
  object schema
  `cf1cd5445651f5b3476f013a3e71151aa1eff266d0c70ceee212f91ce925f905`;
  world/controller/compiler/reader hashes respectively
  `49fd409801ccd86d9e577f8a1553029ade75d94e9f82730c3ecf96b814bdd5d0`,
  `e9ce4c24c24ea888f63ca3992e3996e1e9e60409c226966ff1855d026bbdd6b5`,
  `a99651480d9848e31c91785dba1c78027f447cf97b20d8e695a34c0797679020`,
  `4634d2f2a53405231d6b6f08d0056cce11e04cabb1ef9ca337d8992ba6e5e1c4`.
- Execution v1: `change.json`
  `22af8508d3ccedd8ac0acda1a6aae53775e6843e8a37b6cad7ed7adea88ccaff`;
  `critique.json`
  `bde3b3bf171d5d17f86463009b7a9d5faa3682575af753fec2fdb5c6ac5b36c0`;
  `consensus.json`
  `96e05fdc0e63c13f3e5391ccb4f3de285e5fe849e104edd91eb3d66b4cbc832b`;
  `intake.state.json`
  `b570436bbe344cef1a965db7c17a907dc57ce631921a8d7e2c095f946bd59498`.
- Compose v2: `change.json`
  `1d4e9ca885c6782df060b70e8620228f2449cde837773a0141786b0952b81333`;
  `critique.json`
  `e0e79beaedf937de9344e7eeb8bec8c4b09a5d22b24708678c50ea7812423df5`;
  `consensus.json`
  `d761687a1b7759b7cce1304d792d95d6a9de5540f4811f2d0b3778900ce76a86`;
  `intake.state.json`
  `370648c288a725d747c0e95fc76b306673210b23d068001fda0f8ec72ab33faf`;
  visibility/semantic/reducer/static-fixture contracts respectively
  `6edea13851c3000500cb6cea066d38dcba21b94f323ccc3ce37cb876c3c77b23`,
  `c2a7ec13547e71c212aa36eddd6ef94ca8eb713dd07cec80aa7c835ca11efc07`,
  `0a8a3431bbec7b9af99d79337b018874975b3d4aa61cf0864cf1cfa0b2f13596`,
  `d34cf454271f090e2551f017f19471da66c366636e855849d7103f37a64bb04d`.

Bottom line: **reuse V7 code bytes, not V7 authority; reuse selected D0 and
Compose semantics, not their bundles; build only a PCFL M0 layer and then an
M-TEXT layer, each under a fresh exact-byte gate.**
