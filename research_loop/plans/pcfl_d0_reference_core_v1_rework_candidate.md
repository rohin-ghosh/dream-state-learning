# PCFL-D0 reference core v1 — staged rework candidate

Date: 2026-09-10

Status: **superseded working draft; not ready for deliberation or
ratification**. This file authorizes no code
change, test execution, world/root generation, model or tokenizer use,
parenting, adapter/checkpoint work, CPU scientific execution, GPU use,
resource acquisition, claim, release, or promotion.

The post-draft audit found that the source bundle's own
`cross_audit.md` marks it `REWORK`: its deck, support admission, cuts, Bayes
conditioning, goldens, and runtime fixture are not yet exact. The hashes below
remain useful source identities, but they must not be described as a
ratifiable contract. This draft is preserved as an audit trail and is not the
successor proposal.

## Decision

Keep the complete Dream--LoRA--Think scientific program, but do not attempt to
authorize it as one implementation.

The first implementation proposal will contain only the deterministic PCFL-D0
reference core. It will answer one question:

> Is the proposed causal world mechanically capable of separating access to
> connected lifetime evidence from guessing, shortcuts, copied solutions, and
> hidden target information?

It will contain no child. Therefore it will contain no THINK model, DREAM
model, SLEEP writer, LoRA, parent, clean developmental lineage, model-facing
prompt, scientific sample, or paper result. A green result will mean only that
the CPU reference instrument conforms to its exact contract.

This is the smallest useful response to the v1 consensus. Instead of filling
in every future M/L/C field before writing any code, it removes every field
that is not needed to settle the world.

## Reuse rather than reinvention

Substantial semantic work exists in the unimplemented
`chg_20260901_pcfl_d0_exact_v2` bundle. A successor may use the following
tracked bytes as design sources only after disposing the bundle's recorded
cross-audit; they are not imported here as normative authority:

| Artifact | SHA-256 | Purpose in Stage 0 |
|---|---|---|
| `schemas/pcfl_d0_objects.schema.json` | `cf1cd5445651f5b3476f013a3e71151aa1eff266d0c70ceee212f91ce925f905` | Closed public and private object grammar and canonical wire shapes |
| `world_manifest.json` | `49fd409801ccd86d9e577f8a1553029ade75d94e9f82730c3ecf96b814bdd5d0` | Finite relation algebra, worlds, twins, source schedule, targets, actions, outcomes, collision rules, and structural failures |
| `controller_manifest.json` | `e9ce4c24c24ea888f63ca3992e3996e1e9e60409c226966ff1855d026bbdd6b5` | Exact hidden-world, atomic-ceiling, authentic generic-reader, open-loop, Bayes, shortcut, and corrupted-assignment reference controllers and CPU gates |
| `reader_contract.json` | `4634d2f2a53405231d6b6f08d0056cce11e04cabb1ef9ca337d8992ba6e5e1c4` | Finite one-atom reader, anchor legality, return bytes, repeat/block/discard state, budgets, and reachability checks |
| `compiler_contract.json` | `a99651480d9848e31c91785dba1c78027f447cf97b20d8e695a34c0797679020` | Supported-atom fixtures, canonical deduplication, four one-edge renderings, binding derangements, and twin intervention fixtures |
| `split_seed_manifest.json` | `0b43a4fbe2f08ef8c9d88a94b34b2459c362ade5de77d4fa42d9e605100a6152` | Counter RNG, namespaces, DEV/CPU identities, frozen dormant later split identities, and no-replacement rule |
| `golden/canonical_examples.jsonl` | `8d5561f9a768eb26e5ad5968199bf558a78f41f90f602413fa5d56b8e4308e0b` | Canonical serialization fixtures |
| `golden/controller_cases.json` | `8d4e36a28e4ce21404882e6e5f2d888d6d7fcc319b7d9aafa9f6767625f4fff6` | Exact posterior, controller, collision, reader, quantile, and gate fixtures |
| `claim_policy.json` | `1f9df4ae510c12aad1de32a2817265451285e8792cc3ddaa5704b7509af25750` | D0-only wording firewall and negative dispositions; future scientific templates remain dormant |

The old `authority_manifest.json`, future estimator surface, and missing old
deliberation files are **not** imported as authority. A future successor would
need newly reviewed exact bytes rather than a wrapper around this incomplete
bundle.

## Exact active Stage-0 object

The active object is the fixed-deck PCFL-13 reference instrument already
specified by the imported bytes:

- four public binary traits;
- six opaque preparation families, each secretly assigned one stable trait
  transformation;
- four opaque site families, each secretly assigned one stable acceptance
  predicate;
- three opaque route families, each secretly assigned one stable route
  requirement;
- one world from the exact `6! * 4! * 3! = 103,680` assignment family and its
  registered involutive counterfactual twin;
- exactly 1,568 one-action public source episodes per twin;
- paired A2 and A3 targets whose complete pre-action public bytes collide even
  though the correct actions differ;
- at most one public atom per generic read, four reads, eighteen resolver
  operations, and six world actions;
- exact rational Bayes and exact scripted reference controllers; and
- root-pair reduction with every missing, malformed, failed, capped, or
  indeterminate target valued as zero.

The CPU gate opens only the already bound DEV and CPU namespaces. CAL, CONF,
and RESERVE identities remain dormant: their worlds, roots, streams, and
results cannot be instantiated in this stage.

## What the v1 blockers become

### Bound now by imported exact bytes

- finite relation algebra and public action/outcome semantics;
- counterfactual twin construction;
- pre-action paired-prefix collision and balanced marginal laws;
- canonical UTF-8/NFC/JCS-plus-one-LF serialization;
- finite candidate catalog and query-to-agenda boundary;
- reader return, repeat, block, reset, discard, and budget behavior;
- source chronology and old/third/recent root requirements;
- provenance identity, alias/dedup rules, legal diamonds, cycle/descendant
  rejection, and contradiction/revocation fixtures;
- direct-record closure prohibition;
- legal constructive dependency traces for the exact reference controller;
- source-string, identifier, passive-signature, target-only, current-state,
  action-frequency, shuffled binding, and twin shortcut controls;
- deterministic pair-level reducer, failures, thresholds, and no replacement.

### Removed from Stage 0, not left implicit

- `GOALS_COMPLETE` or any A/B learned-probe join;
- model-visible prompt, chat template, tokenizer, parser, or generation bytes;
- child-authored DREAM proposals or claims about DREAM authorship;
- uncertainty-guided learned experiment selection;
- recurrence comparisons involving a model;
- explicit-text M, M-LoRA, E0, a SLEEP writer, or any training corpus;
- clean-child/parent source receipts or OS-enforced model isolation;
- confirmation masking, scientific estimators, or statistical claims;
- L lifetime lineages, `ACTIVE_TEXT_FIXED`, on-policy flywheel tests, or C
  rate--distortion accounting.

Their absence is normative. None may be supplied by an implementation
default. Each returns in a separate later proposal only after Stage 0 passes.

## Proposed implementation boundary after future exact ratification

Allowed repository writes would be limited to:

```text
pcfl_d0/__init__.py
pcfl_d0/canonical.py
pcfl_d0/schema_validation.py
pcfl_d0/world.py
pcfl_d0/generator.py
pcfl_d0/controllers.py
pcfl_d0/reader.py
pcfl_d0/compiler.py
pcfl_d0/interventions.py
pcfl_d0/reducer.py
pcfl_d0/run_cpu_gate.py
pcfl_d0/tests/__init__.py
pcfl_d0/tests/test_canonical.py
pcfl_d0/tests/test_schema_validation.py
pcfl_d0/tests/test_world.py
pcfl_d0/tests/test_generator.py
pcfl_d0/tests/test_controllers.py
pcfl_d0/tests/test_reader.py
pcfl_d0/tests/test_compiler.py
pcfl_d0/tests/test_interventions.py
pcfl_d0/tests/test_reducer.py
pcfl_d0/tests/test_contract.py
pcfl_d0/tests/test_run_cpu_gate.py
```

Allowed generated outputs would be limited to one derived immutable run root
under `.research_loop/pcfl_d0/`, containing contract hashes, property-test
receipts, the complete 64-pair CPU gate ledger, resource counts, and one final
conformance/failure report. No output is a clean child input or successor
promotion token.

Execution would use one local CPU process, Python standard library plus the
already installed validation dependency if exact import review permits it,
with network and accelerators disabled. No package installation or remote
access is in scope.

## Acceptance tests for this stage only

1. **Canonical bytes:** all positive goldens round-trip byte-exactly; duplicate
   keys, floats, nulls, unknown keys, malformed handles, non-NFC wire forms,
   invalid UTF-8, and wrong newline counts reject.
2. **Finite world:** all `103,680` assignments enumerate uniquely; the twin is
   involutive; source schedules and marginal counts are exact; all accepted
   targets satisfy their structural and chronology requirements.
3. **Paired indistinguishability:** every paired A2/A3 target has identical
   complete pre-action actor-visible bytes and registered different correct
   actions; public divergence occurs only after an ordinary action outcome.
4. **Reader boundary:** only the declared anchor and snapshot inputs influence
   one canonical return; candidate order, hidden target, world rank, twin side,
   split, seed, provenance, score, latency, and backend identity are absent;
   repeat/block/discard transitions match the contract.
5. **Constructive ceiling:** the authentic generic-reader reference controller
   completes only traces whose later queries depend on prior public reads or
   outcomes, while direct single-record closure remains zero.
6. **Shortcut falsifiers:** exact Bayes/no-lifetime and every registered
   shortcut remain below their bound; shuffled/twin assignments remove the
   registered share of authentic-memory gain.
7. **Compiler/provenance:** only one-edge supported-atom fixtures are rendered;
   canonical aliases deduplicate; legal diamonds retain distinct root support;
   duplicate roots, cycles, descendants-as-evidence, unsupported rows, and
   target/plan material reject.
8. **Interventions:** bridge cuts and complete twin substitutions change only
   the declared memory assignment at a byte-colliding decision cut and cause
   the registered trace/action redirection in the reference checker.
9. **Reducer:** roots are the only units; nested paths, calls, goals, targets,
   and checkpoints cannot inflate N; all assigned pairs remain present;
   failures are zero; no replacement, threshold change, or reserve opening is
   possible.
10. **Scope:** static import/write/capability tests show no model, tokenizer,
    trainer, adapter, GPU, network, parenting, clean-child, scientific split,
    or unlisted output path in the Stage-0 implementation.

Any failure yields `D0_REFERENCE_INVALID`. It authorizes no model-facing
repair or favorable root replacement. A material semantic repair requires a
new proposal.

## Claim ceiling

A complete pass permits exactly:

> The deterministic PCFL-D0 CPU reference implementation conformed to the
> ratified finite world, visibility, reader, intervention, and reducer
> contracts on the fixed DEV/CPU suites.

It does **not** show that a model thinks, DREAM discovers, SLEEP writes, LoRA
stores, a child learns, memory improves action, learning continues with life,
or one system beats another.

## Later staged path, preserved but inactive

1. **M-TEXT:** bind the actual target-independent DREAM producer, phase join,
   model-facing bytes, recurrence/bypass controls, and distinct behavioral
   endpoints. Establish that a frozen model can use explicit connected memory.
2. **E0 + M-LoRA:** independently certify the native writer, then test the
   same semantic rows through LoRA with adapter-off/wrong-root/binding controls.
3. **M-ONLINE + L:** test memory-changing information acquisition and then
   increasing-lifetime learning against certified `ACTIVE_TEXT_FIXED` in
   independent lineages.
4. **C:** separately test semantic-code rate--distortion with complete charged
   decoder/state/work accounting.
5. **Parenting/final 2x2:** bind one clean parent/child development packet and
   one-way disposable evaluation descendants. The lineage firewall becomes
   mandatory here, where a child actually exists.

No later stage inherits implementation or execution authority from Stage 0.
