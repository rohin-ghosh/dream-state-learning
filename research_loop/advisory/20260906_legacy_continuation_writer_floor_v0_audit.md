# Legacy continuation-writer floor v0: independent design audit

Date: 2026-09-06  
Verdict: **BLOCKED pending narrow design repairs.**  This is close to a valid
formative transport assay, but the current bytes do not yet identify a
neutral-chat-boundary mechanism or define a leakage-safe executable run.
No model, trainer, fixture, GPU, claim, or release authority is conferred.

## Blocking findings and minimal repairs

### B1. The source-prefix join is not closed over the actual ledger row types

The proposed snapshot has no exact per-life terminal byte offset, even though
the source ledgers continued beyond wake 256 (`lines 24--27`).  The join
partitions thought rows and assigns act rows, then rejects any unassigned
prefix row (`lines 29--40`), but the writer also emits `kind=note` rows.  It
does not say whether notes belong to an occurrence, are deliberately excluded,
or cause rejection.  “Nearest same-tick thought” can also cross repeated
program occurrences unless it is constrained by an occurrence interval.

**Minimal repair:** freeze one terminal ledger byte offset per life at the
completed wake-256 boundary; enumerate the permitted prefix row kinds; assign
or explicitly exclude every note row; and define each occurrence as a closed
byte-offset interval.  An act may join only to a same-program/same-tick thought
inside that interval, with an exact allowed intervening-row grammar.  Both
source-distinct extractors must output the same occurrence ordinal, thought
offset, act offset, and exclusion reason.

The absence of saved prompts is handled honestly: no prompt is reconstructed
(`lines 42--45`), and the claim ceiling already excludes prompt/action binding
(`lines 15--20`).  The output should therefore be called a continuation
corpus, not native task-conditioned examples.

### B2. Target sealing currently occurs before the final cognition/config freeze

The sealers enumerate and expose the target panel at `lines 102--118`, while
the exact run-manifest ratification that binds model revision, prompts, seeds,
training details, limits, metrics, and margins occurs only at gate 8
(`lines 168--181`).  Even without computing scores, target URIs and LLVM bytes
can influence later prompt, recipe, seed, parser, or threshold choices.  The
phrase “every program whose score/action behavior was previously inspected”
is also not a finite auditable contamination set (`lines 111--115`).

**Minimal repair:** freeze and ratify all corpus-selection, model/tokenizer,
template/prompt, parser, trainer, seed, metric, threshold, and failure bytes
before target enumeration, or keep the target manifest blinded from every
design role until that freeze.  Replace the open-ended inspection clause with
an exact hash-bound contamination manifest extracted from named legacy
ledgers, probe logs, advisory analyses, and source-program manifests.  Define
whether equal hashes within POJ-104 are deduplicated or exclude the entire
collision class, and freeze the exact constructibility command and timeout.

### B3. C1 versus C2 does not isolate chat serialization alone

C2 changes the chat-role tokens, instruction text, input length, target token
positions/RoPE phases, attention context, and forward compute simultaneously
(`lines 72--95`).  Equal target IDs, masks, update counts, and optimizer
schedule correctly match *supervised target exposure*, but do not match total
token exposure or positional/conditioning heat.  Therefore
`D_interface` identifies the exact neutral-chat-prefix **package**, not a
chat-boundary or serialization mechanism (`lines 147--155`).

**Minimal repair:** either (a) narrow every label and conclusion to “effect of
the exact frozen neutral-chat-prefix package versus BOS-only training,” while
reporting total input tokens/FLOPs separately, or (b) add one length- and
position-matched non-chat prefix control if a serialization-specific claim is
required.  Do not call C1/C2 fully exposure-matched; call them
target-token/update matched.

### B4. C2 versus C0 identifies a training package, not grounded experience

There are no source prompts, the exact dominant four-pass action was already
shown in the birth prompt, and the proposal does not include an
exposure-matched unrelated/non-improving-label control (`lines 15--20,
58--60, 157--166`).  A C2 gain can therefore be stronger unconditional action
or interface reinforcement; it cannot show that outcome verification, source
program/action binding, or novel experience content caused the gain.

**Minimal repair:** the smallest floor keeps the three cells but states that
C2-minus-C0 is the total effect of training on this post-hoc selected corpus,
not the effect of verification or grounding.  Make the tagged birth-payload
frequency and a sensitivity result excluding that payload mandatory.  If the
desired word is “experience transport,” add a prospectively defined,
target-token/shape-matched non-improving or action-content control; otherwise
retain the narrower “continuation/action reinforcement” ceiling.

### B5. The determinism canary is simultaneously over-strict and incomplete

Byte-identical adapter tensors and loss trajectories are a conservative
same-machine reproducibility target (`lines 97--100`), but GPU kernels may be
numerically deterministic without producing byte-identical serialized tensors.
Conversely, repeating only B0/C1 does not exercise C2's longer sequence shapes
or prove evaluation determinism.  A C1-only pass therefore does not establish
the determinism used by the primary C2 contrasts.

**Minimal repair:** bind hardware, libraries, deterministic algorithms,
worker/batch order, serialization, and initial adapter tensor hash; duplicate
both B0/C1 and B0/C2 plus the C0 evaluation.  Keep exact tensor equality as the
preferred hard canary where supported, but predeclare a fail-closed alternative
based on exact data/order hashes, bounded tensor/loss tolerance, and
byte-identical greedy outputs.  Do not invent seed averaging after failure.

### B6. The evaluation input and C0 identity still need exact bytes

“Production bootstrap, one live-chat call” does not itself define how the
target program URI, goal, metric, and current state are rendered
(`lines 120--145`).  C0 is a valid common reference only if model input,
batching, serving path, and greedy output are reproducible.  Otherwise sharing
one C0 across three trained lives understates runtime variability.

**Minimal repair:** before sealing targets, freeze the complete chat message
array/template/token IDs, program-state renderer, stop/EOS rules, batching,
LoRA serving configuration, and output parser.  Run a zero-LoRA/base-path
equivalence golden and the duplicate C0 canary.  If C0 is not byte-stable, the
assay remains NO-GO or must prospectively model runtime replication.

## Items that are already sound

- The target labels and EOS are exactly shared between C1 and C2, with masked
  prefixes, no packing, equal row order, and equal update ordinals
  (`lines 77--95`).  That is a good paired representation comparison once its
  estimand is named correctly.
- The content-hash target exclusion, score-blind panel ordering, fresh-reset
  first-action endpoint, strict interface parser, and diagnostic-only near-miss
  parser are directionally strong (`lines 102--141`).
- The feasibility thresholds were chosen after legacy aggregate counts, but
  this is disclosed and the result is explicitly formative/descriptive
  (`lines 62--70, 163--166`).  They must remain fixed before any target output;
  they cannot support p-values, population inference, or a prospective error
  guarantee.
- The claim ceiling and authority boundary are appropriately narrow, and the
  eight pre-GPU gates respect `AGENTS.md` (`lines 3--20, 168--184`).  Missing
  evidence means NO-GO; reviewer or model agreement cannot substitute for
  exact human ratification.

## Disposition

After B1--B3 and B5--B6 are frozen, this can answer a useful small question:
whether an exact selected legacy-continuation training package changes
content-disjoint first-action value and whether the exact neutral-chat-prefix
package retains the strict `ACT:` dialect better than BOS-only training.  It
still cannot establish learned THINK, task-conditioned experiential learning,
verification causality, or continual improvement.
