# Native-writer transport micro-assay v0

Status: design note only; not ratified, not implemented, and not authorized
for model or GPU execution. It must enter the architecture-deliberation path
before any run.

## Artifact audit ruling (2026-09-06)

The already-running v6.1 ledgers do **not** contain the prompts that produced
their thought rows. A read-only copy of the three ledgers found prompt-bearing
thought rows `0/7043`, `0/5916`, and `0/10612`. The current on-disk
`batch_loop.py` contains prompt logging, but its hash only binds the file as
audited, not the module bytes loaded by the long-lived processes when these
rows were generated. Exact runtime-source ancestry is therefore unresolved.

Consequences:

- Existing artifacts can support only C0--C2: base, bare continuation, and
  neutral-chat response training.
- C3/C4 and any native prompt-conditioning or prompt/action-binding claim are
  **unavailable**, not merely pending. They require a new prospectively
  instrumented source life that binds loaded source hashes and persists exact
  prompts before generation.
- Do not reconstruct missing prompts from current state, manifests, or later
  ledger rows. Such a reconstruction would invent the recalled/tail/state
  bytes actually seen at generation time.
- The complete-prompt action-present/novel split is unavailable for legacy
  rows. Existing rows can only be tagged against immutable known inputs such
  as the birth prompt; the dominant four-pass action is explicitly shown in
  that birth prompt and therefore cannot support novel-proposal language.

This note retains C3/C4 below as the specification for the prospective
instrumented assay, not as runnable cells over the legacy lives.

## Question

Can a low-rank write preserve the useful early cross-program action prior in
Fable's v6.1 traces without teaching the model to leave its executable action
dialect?

This is deliberately narrower than continual learning, learned THINK,
parenting, dreaming, or intelligent sleep. It is a writer/interface isolation
assay motivated by a post-hoc observation and cannot confirm the parent claim.

## Frozen source rows

Use only already-persisted, pre-collapse v6.1 life prefixes through completed
wake boundary 256 from all three B lives. The live ledger has kept growing and
does not store unique occurrence IDs for the 67-program cycle, so first create
an immutable proposal-source snapshot: bind exact `wake_START_END.json`
manifests through `wake_0248_0256.json`, walk ledger rows in byte order, and
assign `(life_id, occurrence_ordinal, canonical_program_id, tick,
act_ordinal, ledger_byte_offset)` from the wake-manifest order. An independent
extractor must reconstruct the same mapping. Hash the closed prefix snapshot,
not the still-growing ledger file. The train/probe URI intersection must
remain empty. For each life independently:

1. read `kind=thought` rows carrying persisted note fields; for the legacy
   assay record `prompt_present=false` and do not impute a prompt;
2. admit a row only when its persisted note contains exactly one parseable
   line-start `PREDICT:` followed by exactly one parseable line-start `ACT:`,
   the ledger contains the one matching executed action/outcome at the same
   occurrence and tick, and that action increased the episode's prior measured
   best score;
3. bind the exact persisted normalized note bytes, corresponding executed
   action row, public measured outcome, source-life ID,
   source-occurrence ID, and source-prefix hash; `batch_loop.py` stored
   `chunk.strip()[:2000]`, so exclude any row at that cap and describe the
   target only as the persisted stripped note—not the unavailable raw model
   continuation; prompt bytes are absent in the legacy artifacts regardless
   of what the currently audited source file says;
4. use the outcome only as the admission gate. It is not an assistant target;
5. deduplicate legacy rows only by exact continuation-byte hash; prospective
   rows use the complete `(prompt, continuation)` pair hash.

Before tokenization, tag every accepted legacy row with whether its normalized
ACT string already occurs verbatim in the immutable birth prompt. The current
birth prompt itself demonstrates `-mem2reg,-sroa,-gvn,-simplifycfg`, so
transport of that exact sequence is reinforcement of an available action,
not evidence of novel proposal formation. A complete-prompt
action-present/novel tag is reserved for the prospective instrumented assay.

The common accepted row set is frozen before any tokenizer, adapter, or probe
is run. No model-generated restatement or principle is admitted.

## Writer cells: stage A, representation

Every nonbase cell receives the identical accepted continuation bytes.

| Cell | Serialization | Recipe |
|---|---|---|
| C0 | no adapter | frozen base |
| C1 | continuation alone as bare LM text; all nonpadding tokens supervised | hot: r16, lr 1e-4, 3 epochs |
| C2 | fixed neutral user cue -> continuation in the live chat template; response tokens only supervised | hot: r16, lr 1e-4, 3 epochs |
| C3 | **prospective only:** persisted task prompt -> persisted normalized note in the live chat template; response tokens only supervised | hot: r16, lr 1e-4, 3 epochs |
| C4 | **prospective only:** C3 with continuations deranged across source programs within life | hot: r16, lr 1e-4, 3 epochs |

C2 bridges between bare unconditional training and contextual native
training: C2-C1 measures the live chat boundary plus response-only masking
without adding the long task prompt; C3-C2 measures task conditioning. C4
preserves syntax and continuation marginals while breaking prompt/action
binding. If the learned action is genuinely universal, C4 may remain useful;
that outcome must be reported as generic-procedure transport, not conditional
learning.

Legacy stage B runs only if C2 materially improves over C1 and holds C2
serialization fixed. The prospective stage B runs only if C3 materially
improves over C2 and holds C3 serialization fixed. Either version crosses
rank `{8,16}` with learning rate
`{3e-5,1e-4}` at a common prebound supervised-token exposure. This separates
capacity from heat instead of changing both at once. Epoch count is derived
from the common exposure target, not treated as an additional free variable.

Train from the same immutable base revision. Freeze tokenizer revision,
package versions, PEFT target-module inventory, row order, optimizer seed,
adapter initialization seed, LoRA alpha/scaling, dropout, packing policy,
optimizer and scheduler settings, encoded input IDs, label masks,
supervised-token count, update count, and every final adapter hash. Use
`lora_dropout=0` for the first deterministic assay; if deterministic training
cannot be demonstrated, freeze at least three adapter-initialization/order
seeds per life and average them within life. Reject any zero-label,
truncated-response, nonfinite, missing-EOS, or row-set mismatch.

In the prospective assay, persisted prompts can exceed the old trainer's
2,048-token default. No
cell may silently left-truncate. Before training, freeze the exact tokenizer
projection for every cell: complete encoded prompt, generation-boundary
index, exact continuation token IDs, label mask, terminal EOS policy, and
truncation decision. The continuation IDs and terminal EOS must be identical
across C1--C4. Fail the assay if a C3/C4 prompt does not fit the frozen
maximum length; a later explicit prompt-projection experiment may choose a
common prefix/suffix law, but this assay may not invent one after seeing
results.

C4 is a binding intervention only if binding was identifiable beforehand.
For each life freeze three independent derangements such that every target is
paired with a different canonical source program, there are no fixed points,
the normalized ACT sequence differs, and the source/target continuation
length distributions are matched by a predeclared binning rule. Precompute
the conditional entropy of accepted ACT strings given canonical program and
report the fraction of rows whose action can actually change under the
derangement. If this support is too small to meet the prebound identifiability
floor, omit C4 and remove all prompt/action-binding interpretation rather than
calling a low-entropy shuffle a control.

## Evaluation interfaces

The old eight programs are development-only: their action/score behavior was
inspected while motivating this design. Select a new target-blind panel from
an installed, previously unused CompilerGym dataset (candidate family:
`poj104-v1`) by two independent no-model sealers after the architecture and
selection law are frozen. Enumerate the complete installed dataset manifest,
derive a canonical reset-state LLVM/module-content hash for every URI, sort by
that hash, and filter only for reset/evaluator constructibility--never score.
Exclude content-hash collisions with every source-training program and every
previously inspected development program; URI disjointness alone is
insufficient. The sealers must agree on the full enumerated manifest, content
hashes, exclusions, and final hash-ranked panel. Use isolated ledgers, zero
retrieval, no waking brief, and a common bootstrap.

CPU-only feasibility check on 2026-09-06 confirmed that `poj104-v1` is
installed and enumerates at least the evaluator's 400-URI listing cap. No URI
was scored or selected into a final panel by that check.

1. **Free/strict interface:** ordinary free generation; only an exact
   line-start `ACT:` dispatches. Measures the combined proposal-plus-routing
   behavior that the live agent actually needs.
2. **Free/permissive diagnostic:** save the identical free-generation bytes,
   then apply one frozen offline parser that additionally recognizes only the
   two already-observed near-miss forms, `### ACT:` and `- **ACT:**`. Evaluate
   those recovered pass strings once without another model call. This is an
   emitted-action-value diagnostic only: it does not reconstruct the
   counterfactual subsequent state, context, or search trajectory. Strict
   versus permissive on identical first-decision bytes localizes surface
   routing loss.
3. **Typed proposal upper bound (optional):** a separately declared
   grammar-constrained action request. Because this changes decoding and adds
   legality/capability, it is an upper bound—not a routing contrast.

The permissive and typed values never replace the strict registered score.

## Budgets and endpoints

Run deterministic greedy decoding first. Every adapter-ON and adapter-OFF
cell starts from byte-identical fresh initial state; removing an adapter only
after it has altered notes, recalls, or outcomes is a distinct mediation
experiment and may not be called the OFF control. If a stochastic panel is
later needed, freeze common per-program seeds before execution.

For every cell/interface/program report:

- best measured score after exactly the first 1, 2, 4, and 8 dispatched
  actions;
- best measured score under one equal generated-token budget;
- strict action-marker compliance;
- invalid-pass rate;
- total proposed and dispatched actions;
- exact first action and its score;
- a separately labeled switch-off-from-adapter-induced-final-state mediation
  diagnostic, if run at all.

The one prebound stage-A primary scalar is the life-level mean target-panel
score of the first strictly dispatched action, assigning score zero when no
strict action is dispatched. The legacy primary representation contrast is
C2-C1. In the prospective instrumented assay the primary representation
contrast is C3-C1; C2-C1 and C3-C2 are explicitly package-level
decompositions (chat boundary + response mask, then long task conditioning),
not atomic serialization effects. Report a separate life-level
strict-marker-compliance contrast. Only the prospective complete-prompt novel
stratum can support proposal-quality language; legacy rows support
birth-prompt reinforcement/imitation language only. K={2,4,8}, equal-token,
permissive, and typed endpoints are secondary.

Because there are only three independent source lives, stage A is a
descriptive writer go/no-go assay, not confirmatory evidence. Before any run,
bind an absolute smallest effect of interest and equivalence/noninferiority
margins for the first-action score and strict compliance, the exact rule for
missing actions, the within-life aggregation over derangements/training
seeds, and multiplicity treatment. Do not promote a representation from
checkpoint- or program-level pseudoreplication. Additional independent lives
are required for a paper-level writer-effect claim.

Strict versus the frozen permissive parser on identical generated bytes
localizes first-decision routing loss. C3-C4 asks whether prompt/action binding
matters beyond generic action-dialect imitation only if the pre-run entropy
and derangement audits pass.

No pooled checkpoint pseudoreplication: the experimental unit is the source
life, so there are three paired life-level observations. Raw program cells are
shown but not treated as independent lives.

## Interpretive table

| Pattern | Permitted interpretation |
|---|---|
| chat-neutral > bare in strict, equal under permissive parse | chat/response serialization preserves interface routing |
| task-conditioned > chat-neutral in both strict and permissive views | task conditioning improves proposal quality |
| strict poor but the identical bytes useful under permissive parse | knowledge acquired, surface interface lost |
| C3 approximately C4 | transported procedure is generic or binding control is non-diagnostic |
| C3 > C4 | true prompt/action binding contributes |
| all adapter cells approximately C0 | early trace effect did not survive controlled rewriting |

None of these patterns alone establishes learned THINK, continual
improvement, parenting, or an experience-model flywheel.

## Required pre-GPU gates

1. exact architecture change plus two fresh interpretations, adversarial
   critique, adjudicated consensus, and Rohin's exact scope ratification;
2. an independently implemented row extractor agrees byte-for-byte with the
   author extractor;
3. CPU token/mask/update goldens and a tiny optimizer-order fixture pass;
4. two independent no-model seals produce the same source-row and probe
   manifests;
5. fresh pre-GPU reviewer verifies the finite commands, quantitative memory
   budget, lifecycle, failure suffixes, and claim ceiling;
6. a separate exact run-manifest ratification precedes model or GPU use.

The run manifest must also bind the primary scalar, missing-action value,
SESOI/equivalence margins, multiplicity rule, action-present/novel split,
complete tokenizer projections, all LoRA/training fields above, exact fresh
initial-state bytes, content-hash panel manifest, and C4 identifiability
receipt. None may be filled from observed model or GPU outcomes.
