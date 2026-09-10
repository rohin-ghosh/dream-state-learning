# Parenting-transfer protocol attack v1

Date: 2026-09-06

Status: **design-only independent advisory**. This document authorizes no
architecture change, benchmark construction, task enumeration, model or
tokenizer call, training, adapter mount, GPU use, external access, result, or
scientific claim. Adoption requires the complete `AGENTS.md` deliberation,
exact-byte human ratification, scoped implementation/tests, fresh review, and
pre-GPU gate.

## Verdict

**ADVANCE AFTER REWORK.** The one-parent/one-child headline is the right causal
story, but the present nursery note does not yet isolate parenting. Three
problems are load-bearing:

1. Its shared inheritance pack already instructs the behaviors parenting is
   supposed to teach, eliminating headroom and reproducing the Phase-0 prompt-
   compliance ceiling.
2. It leaves the unparented childhood writer ambiguous. If only the parented
   child receives nursery LoRA writes, teacher guidance is confounded with any
   childhood fine-tuning. If neither matched control nor raw-base reference is
   retained, “ordinary agent” becomes scientifically slippery.
3. A free-form parent can leak a deployment strategy through its choice and
   wording of a correction even without printing an LLVM pass. Target blindness
   must be a capability boundary plus a closed correction surface, not a prose
   promise or a forbidden-word grep.

The clean repair is a target-blind **epistemic-recovery nursery** in two
non-compiler task families, three childhood write cycles, and a closed
three-code parent policy. Each root contains exactly one parent and one child;
other roots are sealed replications and share nothing. The child learns only
from its own corrected continuations whose public consequences pass a
prospective admission rule. The parent disappears, then the child is forked
into frozen and continual deployment. The corresponding unparented child gets
the same practice tasks and LoRA-write schedule from its own supported
experience, but no parent message.

## Adversarial findings against the current proposal

### A1. The inheritance pack currently gives away the treatment

`parenting_nursery_v0.md` proposes a shared pack containing prediction,
surprise-driven credit assignment, cheap falsifiers, scoping, diversification,
time monitoring, recall, and context distillation. Those are almost the entire
registered disposition panel. The old CompilerGym bootstrap likewise commands
prediction, note-taking, investigation, and self-criticism and even prints a
high-value four-pass action. A parent cannot measurably teach a habit that the
control is explicitly ordered to perform at every call.

For the headline, the byte-identical shared birth prompt must contain only:

- the task objective and public score;
- the offered typed tools and their effectful/prose boundary;
- the generated-token budget and clock;
- the ordinary external-memory/files interface shared by all cells; and
- a generic request to solve the task efficiently.

It must contain no instruction to predict, react to surprise, discriminate
hypotheses, scope beliefs, diversify, recall, distill, hill-climb, mutate one
factor, or use any example action. A rich inheritance pack is a useful later
arm, not a neutral bootstrap.

### A2. “Process-only” is not guaranteed by omitting action strings

Advice such as “try one change at a time,” “keep searching after a good first
result,” or “test combinations rather than single moves” can be a direct
CompilerGym algorithm while containing no program ID or pass name. Selection
among advice types is itself information. A parent that has read this
repository is contaminated: the repository contains exact compiler actions,
scores, action-frequency diagnostics, and the supplied four-pass opening.

Therefore the confirmatory parent cannot read the repository, Fable artifacts,
CompilerGym source, LLVM documentation, deployment manifests, or the eventual
program split. Repository-wide “parenting” may be used for development only
and can never supply paper evidence on CompilerGym.

### A3. The world-admission sentence is not an executable causal rule

“Admit if the public outcome improves” is insufficient when the pre- and post-
correction tasks differ, when exploration trades immediate reward for
information, or when the second attempt benefits merely from another sample.
The current prototype already compared scores from different hidden rules and
then ignored failure. A paper protocol needs a same-checkpoint neutral shadow,
a code-specific process predicate, a utility guard, and a fresh homologous
application before a row becomes positive sleep data.

### A4. The four-rung ladder can manufacture transfer by target repetition

Showing one accepted response four times behind four prompts may teach the
response format even if the correction semantics are irrelevant. This is not
fatal—the purpose of sleep is to internalize the corrected response—but dose,
target repetition, and native syntax must be matched in the unparented child.
The final childhood fit must predominantly train ordinary parent-absent state
to child continuation; otherwise the learned policy can remain conditional on
teacher language while passing an in-context retry.

### A5. A behavior label is not a transferable thinking disposition

Prediction markers, lesson recitation, notes, and tool syntax can all reach
ceiling without changing investigation. A disposition is transferable only
if a parent-absent adapter changes a pre-outcome policy on surface- and action-
disjoint tasks, the change survives adapter removal/shuffle tests, and it
improves later task learning rather than only entry score. The main endpoint
remains the deployment interaction; nursery process scores are manipulation
checks.

### A6. Parent identity is a scientific variable

A continuing Codex conversation, a human, and a pinned open-weight model are
not interchangeable parents. A live human can adapt richly but is difficult
to replicate; an API session is not independently reproducible; a frozen
open-weight parent can raise many isolated children under one policy. The
identity must be frozen before any confirmatory child trace exists.

## Recommended causal object

Each independent root contains two separately evolving childhood branches
from the same pinned child checkpoint and paired task assignments:

```text
P-child: practice -> one parent correction -> child retry/application
         -> public admission -> childhood LoRA write

U-child: same practice opportunities -> no parent correction
         -> own retry/application -> same public admission law
         -> dose-matched childhood LoRA write
```

At deployment, fork each sealed childhood checkpoint once:

| childhood checkpoint | deployment writes off | deployment writes on |
|---|---|---|
| unparented, practice-written | `U0` | `U1` |
| parented, practice-written | `P0` | `P1` |

`U0` is the **dose-matched unparented control**, not a raw ordinary model. It
must receive target-blind childhood practice writes; otherwise parenting is
confounded with optimizer exposure and response imitation. Add a fit-free raw
frozen reference `R0` using the same deployment resource layer. `R0` is
descriptive and adds no trained arm. The paper-facing two-agent illustration
may show `P1` versus `R0`; the causal parenting claim comes only from the
`P/U` factorial. If a fifth reference curve would clutter the main figure,
place `R0` in a table or appendix, but never relabel `U0` as raw.

Within a root, `P0/P1` share the exact same parented childhood adapter bytes at
deployment entry, and `U0/U1` share the exact same unparented adapter bytes.
Only deployment write permission differs after the fork. All four keep the
same ordinary files, skills, active text memory, tools, clock, token budget,
and public outcomes.

## Nursery: two target-blind task families

Use two generated canonical cognitive tasks rather than a synthetic compiler
or sequence optimizer. This deliberately makes the nursery disjoint in
ontology, tool schema, action vocabulary, and reward mechanics from LLVM while
retaining the epistemic loop we intend to teach.

### N1: nonce Codebreaker

- A secret length-four code is drawn from six per-episode nonce symbols.
- Repetition is allowed, so the initial hypothesis set has `6^4 = 1,296`
  codes.
- `inspect_pattern` submits a four-symbol guess and returns only exact-position
  and misplaced-symbol counts.
- `commit_pattern` submits the final code.
- The pre-parent attempt receives exactly `3` inspection opportunities. The
  corrected and neutral-shadow continuations each receive at most `4` further
  inspections and one commit. A fresh application task receives at most `7`
  inspections and one commit.
- Every task has a finite mechanically enumerable hypothesis set, deterministic
  reset, and fixed query/token budget.
- A proposed query is objectively discriminating when two child-authored live
  hypotheses predict different public feedback; its partition quality can be
  computed without revealing the secret to the parent or child.

This family measures prediction, hypothesis discrimination, and update from a
surprising public observation. The task generator must permute symbols and
tool-instance handles independently in every episode so pretrained answers are
useless.

### N2: nonce RuleShift

- The child assigns cards with three nonce-valued attributes to one of three
  nonce bins through `place_card`.
- Public feedback is only correct/incorrect plus cumulative public score.
- The hidden classification rule is drawn from a finite registered family and
  changes once after trial `6`, unknown to the child.
- The pre-parent attempt contains trials `1..7`, so at least one ordinary
  post-change result is visible before correction. Corrected and neutral-shadow
  continuations receive trials `8..12`. A fresh application uses all `12`
  trials with no parent.
- A fresh episode independently permutes attributes, values, bins, rule, and
  change point.

This family measures whether a prediction violation changes the next belief
and experiment, and whether the child keeps a rule scoped to a regime instead
of treating one early regularity as permanent.

The parent never receives the secret code, hidden rule, change point, oracle
action, candidate answer, counterfactual score, or evaluator state in either
family. The compiler/admission role may use the sealed task definition only
after all child/parent outputs for that opportunity are immutable.

These are proposed families, not yet valid benchmarks. Before ratification,
CPU generation must prove deterministic reset, no answer collision, adequate
base headroom, nontrivial child action diversity, and usable process-score
variance on a development-only split. If either family is solved at ceiling by
the minimal shared bootstrap, replace the *development family* before sealing;
do not quietly make confirmation instances harder.

## Exact proposed childhood schedule

Use these integers for the first full protocol unless development-only
headroom tests reject the task family:

- `J = 3` childhood sleep/write cycles;
- `4` parenting opportunities per cycle;
- `2` Codebreaker and `2` RuleShift opportunities per cycle;
- one source attempt plus one fresh homologous application task per
  opportunity;
- therefore `12` maximum parent decisions and `24` unique nursery task
  instances per child branch;
- at most one correction code per opportunity; and
- no root replacement or eligibility filtering based on whether correction
  succeeds.

This gives each life three real opportunities for learning to compound while
keeping the already-derived fit budget at `2J + 6 = 12` trained fits per root
for three deployment writes. It supplies up to twelve child-specific lessons
without pretending that tasks or messages are independent children. Twelve is
not a powered parenting sample; the root is the independent unit.

If no correction is eligible, the parent emits `NO_CORRECTION`; the event and
task remain in the intent-to-treat root. Do not select “teachable children” as
the headline population. Report the complete funnel from opportunity to
trigger, correction, supported retry, fresh application, admitted target, and
fit.

## Closed parent policy and process vocabulary

The scientific curriculum should teach one composite disposition—
**evidence-responsive experimental recovery**—through exactly three codes:

1. `PREDICT_UPDATE`: before acting, make one falsifiable prediction of a
   public outcome; after a violation, identify and narrow one assumption before
   the next action.
2. `DISCRIMINATE`: state two explanations consistent with the public trace and
   choose, without being given the action, a legal experiment whose predicted
   public outcomes differ under them.
3. `SCOPE`: keep a belief local to the episode/regime until distinct public
   episodes support promotion; after contrary evidence, demote rather than
   silently preserve it.

Typed routing is a prerequisite writer/interface gate shared by all branches,
not a fourth scientific lesson. Context reconciliation is likewise an
identical Think/Dream opportunity in all cells and a secondary measurement,
not another parenting factor in this first headline.

The parent output is one closed object:

```json
{
  "lesson_code": "PREDICT_UPDATE|DISCRIMINATE|SCOPE|NO_CORRECTION",
  "evidence_event_ids": ["earlier-public-event-id", "..."],
  "template_version": "parent_process_v1",
  "answer_content": "NONE"
}
```

Proposed literal lesson templates (later ratification must bind exact UTF-8
bytes) are:

```text
PREDICT_UPDATE
Use only the public trace. Before your next action, state one falsifiable
prediction of the public result. If a result contradicted your prediction,
name one assumption that produced it and narrow or replace that assumption
before acting again. Choose the action yourself.

DISCRIMINATE
Use only the public trace. State two explanations that remain possible and
what different public result each predicts. Then choose the legal action
yourself whose possible results best separate those explanations.

SCOPE
Use only the public trace. Keep a belief local to this episode or regime unless
you can cite support from two distinct public tasks. If contrary evidence has
appeared, narrow the belief before choosing the next action yourself.
```

If more than one code is eligible, proposed priority is `PREDICT_UPDATE`, then
`DISCRIMINATE`, then `SCOPE`; the exact trigger/tie table must be frozen and
must return `NO_CORRECTION` when no predicate fires. The parent chooses only a
code and earlier evidence IDs; it cannot modify these bytes.

The harness renders the corresponding frozen lesson text. The parent may not
free-write a strategy, choose an action, insert a number other than copied
event IDs, or name an entity. Event IDs prove which public trace justified the
diagnosis. The code-selection policy sees only the committed child trace and
public outcomes. A fixed priority/tie rule and `NO_CORRECTION` behavior are
part of the parent manifest.

This is deliberately stricter than natural parenting. It identifies whether
adaptive, child-specific selection among general process lessons is useful.
Rich Rohin dialogue can be a later registered case study, not silently mixed
into confirmation.

## World-admission rule

For every parenting opportunity, fork a read-only **neutral shadow** from the
same current P-child checkpoint and same task state before displaying parent
feedback. The shadow receives the registered neutral continuation and the
same remaining child-token/action budget but is never trained. The parent
cannot read its output or score.

A parent-derived target is `ADMITTED_POSITIVE` only when all of the following
hold:

1. **Prospective trigger:** the pre-feedback trace satisfies the frozen
   code-specific failure predicate; no hindsight relabeling.
2. **Provenance:** every supervised child byte is joined to the exact context,
   native response envelope, typed dispatched action, reset state, and public
   outcome; parent/output/result roles are untainted.
3. **Process delta:** the corrected child satisfies the code-specific public
   predicate and the neutral shadow does not, or exceeds it by the registered
   discrete margin.
4. **Utility guard:** over the same remaining task budget, corrected terminal
   utility is no worse than neutral-shadow utility by more than a predeclared
   small non-inferiority margin. Information-seeking is not required to win on
   its first exploratory action.
5. **Fresh application:** on a new homologous task, with parent text absent and
   only the child-authored restatement available, the child again satisfies
   the process predicate and the task-family utility guard.
6. **Content firewall:** the parent object, child restatement, and selected
   targets contain no forbidden capability, task-answer, future, cross-life,
   deployment, or hidden-evaluator edge.

Failed advice remains an immutable rejected event and never becomes a positive
target or principle. Do not train it as a negative example in v1; that adds a
new objective. The public outcome supports the child's behavior, not the
truth of arbitrary parent prose. The hidden task definition may be used only
by the offline admission reducer and never returned into the child, parent,
Dream, or later sleep input.

Code-specific predicates must be mechanical. For example, `DISCRIMINATE`
requires two child-authored hypotheses, two distinct predicted public outcomes
for the selected legal query, actual dispatch, and elimination of at least one
hypothesis by the ordinary result. `PREDICT_UPDATE` requires a committed
prediction before dispatch, a registered surprise, and a changed subsequent
prediction/action rather than an identical repeat. `SCOPE` requires an
episode/regime-scoped claim unless at least two task-distinct public supports
are cited. Prose resemblance to a desired thought never counts.

## Scaffold fading and childhood writer

The parent is a data-elicitation and credit-assignment source, not a supervised
voice. Parent text, task outcomes, old transcript, lesson code, and restatement
are masked inputs. Targets are only the child's own validated native
`THOUGHT_CONTINUATION`, `TOOL_CALL_CONTINUATION`, and reversible
`DREAM_STATE_CONTINUATION` bytes.

For each admitted corrected-source and fresh-application continuation, use six
target exposures per childhood fit and fade input scaffolds prospectively:

| fit | parent text `P3` | child lesson `P2` | neutral review `P1` | ordinary state `P0` |
|---|---:|---:|---:|---:|
| sleep 1 | 2 | 2 | 1 | 1 |
| sleep 2 | 1 | 1 | 2 | 2 |
| sleep 3 / final childhood | 0 | 1 | 1 | 4 |

Thus target exposure stays constant while explicit parent conditioning falls
to zero and two-thirds of the final dose starts from ordinary parent-absent
state. The cumulative corpus is rebuilt from the clean frozen base at each
sleep. Do not carry an optimizer across cycles or stack adapters.

The U-child uses its own publicly supported retry/application continuations
under the identical native writer, six-exposure schedule, fit count, rank, and
optimizer-update ceiling, with parent slots replaced by presealed neutral
role/token-matched inputs. It never receives P-child targets. Each P/U fit gets
the same supervised-target-token and optimizer-step budget; unused treatment
capacity is filled only by a common target-blind, task-disjoint native
rehearsal packet frozen before root generation. Report the fraction of dose
coming from corrected, self-recovered, and rehearsal rows. Padding tokens are
not described as evidence.

Start with full attention-plus-MLP rank-8 LoRA because it is the current
scientific target, but do not freeze learning rate, supervised-token dose, or
update count from the uncontrolled r8/r16 scout. Select them once with a
treatment-neutral native writer canary, as required by the existing writer
review. `1e-6`, `3e-5`, and `1e-4` remain candidate heat anchors; the parented
treatment cannot select among them.

## Parent absence and CompilerGym firewall

Before deployment, start a new process and prove absence of:

- parent model/service/capability;
- parent feedback and restatement bytes;
- nursery tasks, ledger, notes, Dream state, retrieval/index state, optimizer,
  and rehearsal corpus;
- nursery KV/prefix cache or serving process;
- repository/Fable/CompilerGym-result access not part of the common ordinary
  resource layer; and
- any namespace/content hash shared between nursery and deployment tasks.

Only the pinned frozen base, one permitted childhood adapter, the byte-identical
minimal deployment bootstrap, and the common ordinary resource layer cross the
boundary. The parent process runs in a capability root containing only the
public nursery trace and closed rubric. A lexical audit is necessary but not
sufficient; two independent reviewers must also attempt semantic laundering
(e.g. generic advice that encodes sequence-search tactics) before the parent
policy is sealed.

Deployment should use `64` unique training programs per root, personal writes
after programs `16`, `32`, and `48`, and sealed probes at entry and after
`16/32/48/64`. No program repeats within a life. The exact generated-token cap
per program is **not defensible from current evidence**: the old runner spent
up to 16 chunks of 400 tokens and did not record a comparable saturation
curve. Freeze the smallest cap whose development-only base curve reaches at
least 90% of its within-program asymptote; candidate `2,048` tokens is a
resource-planning placeholder, not a ratified integer.

Use entry-adjusted normalized AUC and the registered interaction

```text
I = [nAUC(P1)-nAUC(P0)] - [nAUC(U1)-nAUC(U0)].
```

Also report the unadjusted curves, entry value, early slope, value/token,
forward transfer, backward retention, free typed-call compliance, and
typed-forced proposal quality. A higher `P0` entry score is static transfer;
only positive `I` supports parenting-improved deployment learning.

## Parent identity and reproducibility recommendation

For the confirmatory causal estimate, use the already pinned open-weight
`Qwen/Qwen2.5-32B-Instruct` revision
`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd` as the frozen parent policy, with
greedy constrained decoding, exact prompt/schema, no tools/network/repository,
no memory between children, and a deterministic-repeat canary. The child is
the pinned `Qwen/Qwen2.5-7B-Instruct` revision
`a09a35458c702b33eeacc393d103063234e8bc28` plus the per-life adapter. This
choice is reproducible and uses a parent already measured in the repository.

A Rohin-parented child is scientifically valuable after the pipeline proves
teachability. Unless Rohin applies one frozen blinded interface across every
independent root, it is a registered mechanistic case study, not the estimator
of a general parent-policy effect. If Rohin is the confirmatory parent, show
him only the permitted public trace and closed code buttons; free-form access
to the repository or deployment data invalidates the CompilerGym transfer
claim.

Parent identity remains an exact human decision. The recommendation above is
not authority to select or call that model.

## Decisive controls without turning the paper into seven arms

### Longitudinal headline cells

Only `U0`, `U1`, `P0`, and `P1` are trained longitudinal deployment cells.
`R0` is a fit-free raw frozen reference.

### Mandatory local/terminal diagnostics

1. **Childhood adapter off:** replay the parent-absent disposition panel with
   the exact P-child adapter absent. This localizes transfer to parameters.
2. **Correction-code derangement:** on a bounded terminal subset, preserve
   feedback-code/dose marginals but assign each correction to an opportunity
   whose registered trigger is false. This tests child/error alignment. No
   fixed point is permitted; report support rather than forcing a shuffle.
3. **World-binding derangement:** swap admitted child continuations across
   state/outcome bindings while preserving native syntax and target-token
   marginals. This distinguishes grounded state-to-action learning from tool
   dialect imitation.
4. **Final batch experience distillation:** at terminal deployment, compare
   periodic P1/U1 writes with one matched final Early-Experience/LEAFE-style
   batch writer. This is required for novelty; do not label an adapted control
   a reproduction of published full-model training.
5. **Free versus typed-forced action:** every checkpoint jointly gates native
   routing and latent proposal quality so another B2 failure cannot masquerade
   as forgetting or learning.

A static inheritance-pack-only control is useful only if resources remain; it
asks whether adaptive dyadic selection adds value over reading the same three
general lessons. It is not required before the four-cell spending pilot.

## Replication and staged integers

- Run exactly `4` development/spending roots through the complete four-cell
  surface. Never pool them with confirmation.
- Require zero provenance/target-blindness/routing failures and a positive
  directional interaction in at least `3/4` roots before confirmation. This
  is a spending rule, not evidence.
- Set confirmation maximum `n=32` independent dyads. A treatment-label-blind
  variance rule may stop at `n=20` only if the root-level interaction SD is at
  most `0.075`; continue to `32` if it is at most `0.10`; above `0.10`, do not
  call the available design powered for a `0.05` interaction without a new
  prospective resource/power decision.
- Checkpoints, programs, task instances, parent messages, generated samples,
  and optimizer seeds are repeated measurements, never additional `n`.

The pilot-direction rule can select spending because pilot roots are discarded;
the confirmation root count cannot be chosen from observed treatment effects.
All intervals resample whole dyads only. Publish the sensitivity curve and
label any feasibility-limited `n=20` result honestly.

## Exact blockers before a formal ratification candidate

1. **Human-only parent decision:** frozen open-weight parent versus Rohin; if
   Rohin, case study versus repeated blinded protocol.
2. **Nursery nonexistence:** the proposed two-family generator, typed tools,
   public process predicates, neutral shadow, and admission reducer do not
   exist or have CPU validity/headroom evidence.
3. **Writer floor:** native typed response provenance is still a design/static
   fixture, not a ratified live model-to-tool-to-outcome writer; heat/dose are
   unresolved.
4. **Control childhood semantics:** current plans/paper call `U0` ordinary
   without saying it receives target-blind practice writes. The label and raw
   `R0` reference must be ratified.
5. **Bootstrap contamination:** current inheritance/bootstrap language directly
   commands target dispositions and contains a high-value compiler action.
6. **Capability isolation:** no confirmatory parent container/root currently
   proves it cannot read repository/compiler/deployment bytes.
7. **Scaffold deletion:** no fresh-process test proves all parent/nursery/KV/
   retrieval state is absent while the ordinary resource layer remains matched.
8. **CompilerGym split:** the current runner repeats 67 programs and uses
   unseeded generation; no sealed unique-program, common-assignment, isolated-
   ledger deployment manifest exists.
9. **Budget calibration:** no same-code generated-token saturation curve
   justifies the per-program cap or final resource maximum.
10. **Power/lease:** confirmation `n` depends on root-level variance and a
    compute receipt beyond the current September 14 lease.

## Maximum defensible claim

If the writer gate, four-cell pilot, and confirmation all pass, the maximum
headline statement is:

> Under one frozen target-blind one-to-one parent policy, process correction
> in two non-compiler practice families increased the subsequent benefit of
> periodic personal low-rank writes on fresh CompilerGym programs, relative to
> a dose-matched unparented childhood, while both retained identical ordinary
> external agent resources.

This establishes a finite cross-task parenting-by-learning interaction for one
model pair and protocol. It does not establish general meta-intelligence,
learned dreaming as the mediator, novel compiler-strategy discovery,
population learning, unbounded improvement, or superiority to every external-
memory agent. `P1 > R0` alone is a system demonstration; it cannot replace the
factorial interaction.

## Recommended next decision artifact

Do not extend the current exploratory nursery. Create one formal architecture
change proposal whose exact bytes bind: the P/U childhood writer semantics,
`R0`, minimal bootstrap, two nursery generators, three correction codes,
`J=3`, twelve opportunities, neutral shadow/admission predicates, fading
schedule, parent identity, deletion firewall, 64-program deployment/cuts,
resource maximum, and pilot/confirmation rule. Then run the full independent
deliberation and present its hash to Rohin. No implementation or GPU work should
precede that ratification.
