# PCFL C0 DEV interface repair: independent red-team

**Date:** 2026-09-13  
**Role:** fresh adversarial reviewer  
**Reviewed:** `2026-09-13_pcfl_c0_dev_interface_repair_ladder.md`, the
SEQ-167 failure audit, current PCFL prompt/parser/runtime sources, and the
frozen v2 synthesis/build ledger.  
**Execution:** none. No model, tokenizer, test, benchmark, fit, update, GPU, or
runtime edit.

## Verdict

**REWORK BEFORE IMPLEMENTATION.** The central repair is correct: disclose the
READ language, restore a typed THINK loop, retain whole-response exact action
scoring, repair reachout to an order-only surface, develop only on exposed
roots, and confirm once on fresh roots. No topology or answer leakage was found
in that core.

Four protocol defects can nevertheless make a nominal pass ambiguous or make
the written run impossible under the current actor. They are small to fix and
do not require a new cognitive design.

## Severity 0 — must close before the first DEV model call

### S0.1 The main gates are marginal when the claim requires a conjunction

The A3/A4 rule separately asks for THINK in `>=60/64` tasks and graph success
in `>=60/64`. Those sets can differ: 60 THINK tasks plus 60 successful tasks
can contain only **56 tasks that both thought and succeeded**. The same defect
appears in the active delayed qualification, where served-read count and route
success are separate. Active reachout has no served-read requirement at all,
so it can pass by guessing without using the service.

Freeze joint per-task gates instead:

- A3/A4: at least `60/64` tasks have `>=1` valid THINK **and** one exact
  terminal ROUTE that graph-succeeds, with no invalid turn/cap failure;
- active delayed: at least `60/64` have `>=1` registered, non-`MISS` served
  READ **and** an exact graph-successful ROUTE in that same task;
- active reachout: at least `30/32` have `>=1` registered, non-`MISS` served
  READ **and** the exact relevant PROBE in that same task, with at least
  `14/16` joint successes in RA and RB separately; and
- A1's handshake counts a served read only when the exact request exists in
  the task query registry and returns a non-`MISS` registered block.

Keep the marginal counts as diagnostics, not acceptance criteria.

### S0.2 The byte boundary is still underspecified

`THINK <one nonempty physical line>`, `entire final ROUTE line`, and `zero
accepted mixed thought/action responses` do not define whether a terminal LF
is legal, what empty/whitespace-only THINK means, or whether action-looking
text inside a THINK payload is a mixed response. This is exactly the class of
boundary ambiguity that just killed the own-write formation attempt.

Before calls, freeze one exact whole-response grammar for every family,
including CR/LF policy. The smallest consistent choice is: no CR or LF in any
actor response; `THINK ` followed by at least one non-newline, non-whitespace
character; existing READ/ROUTE/PROBE regexes unchanged. An action-like token
inside a valid THINK payload is inert text, not an executed or “mixed” action.
Only a top-level whole response matching READ/ROUTE/PROBE dispatches. Record
raw UTF-8 bytes, token IDs, family, and stop reason. Do not use stop-string
truncation to manufacture a valid line from a longer raw generation.

### S0.3 Confirmation material is created too late

The proposal materializes the four confirmation roots only after DEV passes.
Even with deterministic materialization, the seed/domain/search procedure and
tokenizer rejection policy are then outcome-adaptive unless they were already
bound. That leaves room for redraw or favorable-root selection.

Before A1, bind the confirmation namespace, generator revision, four seeds,
first-valid allocation rule, cube/order balance, tokenizer qualification rule,
and root hashes. Keep their decoded inventories and prompts blinded, but do
not create or select them after seeing DEV. Also materialize and hash all A1–A4
and remaining-panel templates before A1; selecting A3 versus A4 must select an
already frozen hash, not permit editing after its score is visible.

### S0.4 The full-run arithmetic contradicts the current executor

The stated `1,792` calls cover only discovery. With `RAW_EPISODIC` omitted and
the selected EXACT result reused rather than rerun, the full maxima are:

| stage | maximum physical generations |
|---|---:|
| A1+A2+A3+conditional A4 | 1,792 |
| remaining mandatory DEV panels | 5,856 |
| fresh mandatory confirmation panels | 6,304 |
| **total** | **13,952** |

The corresponding loose caps are `3,407,872` actor-generated tokens and
`1,048,576` returned-memory tokens. Each optional RAW panel adds 448 calls per
pool.

The current native actor hard-caps a session at 1,952 calls
(`gpu/astra_pcfl_native_actor.py:182`), and the current driver requires exactly
1,952 (`gpu/astra_pcfl_zero_fit_dev.py:204`). Therefore “one cold-load session
per [remaining DEV/confirmation] stage” cannot execute as written. Freeze
either a larger validated actor cap or deterministic, outcome-independent
session partitions, plus per-partition wall/device budgets and exact call-slot
registries. Reusing the selected A3/A4 EXACT result must be explicit; rerunning
it would be a scientific retry.

## Severity 1 — required for an interpretable result

### S1.1 A4 may only diagnose route-policy failure

“Run A4 if A3 fails” is too broad. If A3 fails because the model does not obey
the THINK byte grammar, an added traversal algorithm can mask an interface
problem rather than localize traversal knowledge. Reach A4 only if the A3
typed-turn interface itself qualifies prospectively but the joint
THINK+graph-success gate misses. A malformed-turn/THINK-compliance failure
requires a separately named DEV successor, not A4. If A3 graph-succeeds but
misses an auxiliary compliance gate, do not escalate content.

### S1.2 “Identical interface” needs an executable arm matrix

The active service and native learner cannot literally have identical allowed
actions: one has READ and one does not. Freeze the exact common THINK and
terminal-action surface, then predeclare the sole capability difference:
read-enabled arms expose the same three READ forms and service; read-disabled
clean/adapter-on pairs expose the same explicit no-READ state. A selected A4
scaffold must appear byte-identically in every compared arm. Most importantly,
adapter-on versus adapter-off native comparisons must have identical messages,
caps, continuations, and turn topology. Do not let a cleaner C0 prompt become
an easier baseline than the mounted child.

### S1.3 The A2/A3 causal sentence is too specific

A3 changes more than private state tracking: it adds multiple generations,
self-produced text in history, a mandatory THINK convention, and repeated
fixed CONTINUE messages. If A2 fails and A3 passes, the supported statement is
that the **typed recurrent THINK protocol** enables successful traversal under
the shared actor-token envelope. It does not isolate retained state tracking
from extra calls or continuation prompting. No extra ablation is required for
this ceiling; narrow the interpretation.

### S1.4 Counter state and exhaustion order must be explicit

The controller needs separate `generation_count`, `think_count`, `read_count`,
`actor_tokens`, and `returned_tokens`. Current runtime derives remaining reads
from the turn index, which becomes wrong as soon as THINK turns exist. Freeze
the dispatch order at every boundary (`cap-1`, `cap`, `cap+1`), set each decode
request to `min(256, actor_tokens_remaining)`, check the fully rendered next
conversation against the context limit, and fail without a forced final answer
when any cap is exhausted.

## Severity 2 — reporting and efficiency repairs

1. **`WRONG_ROOT: zero usable false rows` is vacuous at the actor endpoint.**
   The present implementation scans the final actor response for complete
   EVENT/LINK rows, but a well-typed response can only be THINK/ROUTE/PROBE.
   Remove that gate or replace it prospectively with explicit wrong-root
   identifier use in the terminal action and unsupported service-return
   provenance.
2. **Do not rerun duplicate surfaces.** Reuse the selected A3/A4 EXACT result
   in DEV qualification. If FULL_CHILD_TEXT and NATIVE_CONTEXT remain
   byte/seed identical after repair, execute one physical task set and expose
   two compatibility labels, never two evidentiary counts.
3. **Report the real sampling units.** A 64-task panel is four root inventories
   crossed with repeated cube/goal cells, not 64 independent lives. Report
   `roots=4`, the exact cell structure, paired task vectors, and no inferential
   `n=64` language. Confirmation supports only this exact model revision,
   interface, topology, and root generator.
4. **Prebind the neutral example.** Its IDs, tokenizer lengths, topology and
   non-membership in every DEV/confirmation/future root inventory must be
   certified before A1, even though the bytes are revealed only on conditional
   A4.

## Smallest corrected handoff

The builder does not need a new architecture. Before implementation, amend the
DEV plan with:

1. exact byte grammars and typed-turn counter state;
2. joint success/use gates;
3. cause-specific A4 eligibility;
4. a frozen arm-capability matrix;
5. prebound, blinded confirmation roots and all prompt hashes;
6. the `13,952`-call maximum with executable session partitions and budgets;
7. no rerun of selected/duplicate cells; and
8. narrowed claim text.

With those edits, the plan is an honest and efficient clean-base
supplied-memory interface qualification. A pass still says nothing about LoRA
writing, own-experience formation, retention, continual learning, parenting,
compression, or the whole organism.
