# PCFL C0 SEQ-167 failure-cause audit

**Date:** 2026-09-13

**Role:** fresh read-only failure auditor
**Verdict:** **the captured C0 result is not a clean negative about memory use
or route competence. It combines two confirmed interface defects with a real
five-hop route-composition failure under the implemented answer-only
interface.**

The confirmed defects are:

1. the active service requires one of three exact READ forms, but none is
   disclosed to the model; and
2. the design says the mounted child may think for up to 2,048 tokens before
   committing a route, while the implementation tells it to emit exactly one
   ROUTE and fullmatches the entire generation. There is no thought/action
   projection in this C0 run.

Reachout has a third interface confound: RA/RB change wording as well as order,
use numbered options, and produce complete view dependence in the negative
controls.

The smallest *design-faithful* successor must expose the READ language and
restore a prospectively typed thought -> action boundary. The unchanged strict
route/probe parser should score only the exact action payload; it must not
heuristically salvage old outputs. A prompt-only answer-direct repair is a
useful cheap DEV canary, but it would not implement the THINK endpoint promised
in the synthesis.

Even a passing successor would establish only a **clean-base supplied-memory
interface ceiling**. It would say nothing about LoRA writing, own-experience
formation, retention, continual learning, parenting, or the full organism.

## Scope and evidence status

I did not run a model, tokenizer, benchmark, test, fit, update, GPU process, or
alternative scorer. I did not edit runtime or test files. I read:

- committed SEQ-167 at `9307b08e`;
- the frozen source and prompt/parser files recorded by the capture;
- the archived immutable evidence at
  `gpu_artifacts_local/pcfl_c0_zero_fit_20260913_attempt2/evidence.tar`, SHA-256
  `44473352a9220e4e92475d16194a87f1fc89bd3d6021bbe6caa97a74a2ca20cf`;
- the committed replay summary
  `research_notes/astra_memos/receipts_20260912/astra_pcfl_c0_capture_inspection_20260913.json`,
  SHA-256
  `786d96c659379675be03e7eaf40f018556efc25646f721e2d3985601ff2c5afd`.

The scientific status remains the one fixed by the terminal audit:
`UNUSABLE EXECUTION -- ENGINEERING-ONLY CAPTURE (FINALIZATION FAILED)`.
The 800 immutable prompt/response/task rows are adequate for debugging. They
are not a finalized diagnostic and cannot become sole C11 evidence.

## Fixed sample

Before reading the remaining raw prompt/response pairs, I fixed this simple
sample rule:

1. delayed: the lexicographically first task in every required positive
   projection x each of four roots: `5 x 4 = 20` rows;
2. reachout: the lexicographically first task in every required positive
   projection x each of four roots x each of RA/RB: `3 x 4 x 2 = 24` rows.

Total fixed sample: **44 rows**. Task 000 and aggregate counters had already
been seen before this rule; the rule includes task 000 and was not changed
after inspecting the other 43 rows.

The fixed-sample classifications were:

| family | mutually exclusive observed class | count |
|---|---|---:|
| delayed positive | disconnected visible ports / route-composition failure | 12/20 |
| delayed positive | illegal READ grammar | 4/20 |
| delayed positive | opaque-ID surface confusion | 4/20 |
| reachout positive | exact relevant probe | 6/24 |
| reachout positive | exact distractor / wrong probe | 8/24 |
| reachout positive | ordinal answer selecting the relevant position | 3/24 |
| reachout positive | ordinal answer selecting the wrong position | 5/24 |
| reachout positive | wrong identifier namespace | 2/24 |

Representative frozen rows:

- active delayed: `READ <START>\nREAD <GOAL>` -- two lines, and neither is a
  registered READ operation;
- exact graph delayed: a correct start/goal header followed by the two
  mutually exclusive first-hop ports and one final port;
- event-atom delayed: a correct header followed by ports selected from
  disconnected parts of the graph;
- reachout RB: `PROBE 1` or `PROBE 2` despite the required `Q_...` identity;
- two RB cases copy a `N_...` node or `E_...` event after `PROBE`.

These are command-like, short answers. The sample contains no essay, chain of
thought, apology, or other overlong answer framing.

## Full positive-panel classification

The following hierarchy assigns every required positive-panel output to one
and only one observable class. It is a failure morphology, not a claim about
the model's internal state.

### Delayed supplied-memory positives: 320 rows

| primary class | count | evidence |
|---|---:|---|
| illegal READ grammar | **64** | all 64 `ACTIVE_LINKED_TEXT` rows emit exactly two lines, `READ <START>` then `READ <GOAL>`; 0 reads served |
| opaque-ID surface confusion | **86** | route surface present, but at least one emitted port is not a valid port ID from the task root (commonly a removed `P_` prefix) |
| disconnected-port route composition | **170** | every emitted item is a valid task-root port, but the sequence cannot be traversed from the stated START through the public edges |
| exact answer with strict-syntax-only failure | **0** | no permissively parsed route equals the five-port answer |
| legal path ending at the wrong endpoint | **0** | none of the 170 valid-ID sequences is even a legal public path |
| response-budget / truncation | **0** | no task or call truncated |
| prose / overthinking / answer wrapper | **0** | 256 direct-memory answers are one `ROUTE` line; the other 64 are the two READ lines |

The counts sum to 320. They deliberately do not call every parser rejection a
"syntax problem." Across the four direct-memory positive projections,
**142/256 outputs satisfy the frozen exact ROUTE regex and all 142 still fail**.
The remaining 114 are syntax-invalid, but zero becomes correct after only
permissive comma-space parsing.

Direct public-memory details:

| projection | strict ROUTE | all emitted IDs are root ports | disconnected among those valid IDs | success |
|---|---:|---:|---:|---:|
| EXACT_WITNESSED_GRAPH | 12/64 | 20/64 | 20/20 | 0/64 |
| FULL_CHILD_TEXT | 44/64 | 44/64 | 44/44 | 0/64 |
| EVENT_ATOMS_TEXT | 42/64 | 62/64 | 62/62 | 0/64 |
| NATIVE_CONTEXT | 44/64 | 44/64 | 44/44 | 0/64 |

`FULL_CHILD_TEXT` and `NATIVE_CONTEXT` are not two independent pieces of
evidence here. For **64/64 matched tasks**, their public prompt and seed are
identical, hence their deterministic outputs are identical.

The required delayed answer is always five sequential ports:
`a(old), b, q(relevant), d, f(goal)`. The dominant generated patterns instead
select salient ports from separate branches, for example both mutually
exclusive `a0,a1`, an old-left terminal `c`, and a final `f`. In the exact
graph projection, the true intermediate roles `b`, `q`, and `d` are each
selected in **0/64** outputs. This is stronger than a punctuation failure: it
looks like unordered edge/endpoint salience rather than path execution.

### Reachout supplied-memory positives: 96 rows

| primary class | count | evidence |
|---|---:|---|
| exact relevant `Q_...` | **19** | frozen scorer successes: EXACT 6, FULL 5, ACTIVE 8 |
| exact distractor / wrong experiment | **40** | valid probe syntax, wrong candidate |
| ordinal answer, semantically relevant position | **5** | `PROBE 1/2`; would name the relevant option by position, but does not copy its required ID |
| ordinal answer, wrong position | **26** | `PROBE 1/2` and also chooses the distractor position |
| opaque-ID namespace confusion | **6** | `PROBE N_...` or `PROBE E_...` |
| response-budget / truncation | **0** | no truncation |
| long prose / overthinking | **0** | all 96 are one short `PROBE ...` line |

The counts sum to 96. Accepting numbered answers would therefore not repair
the assay: only 5/31 numbered positive answers point to the relevant candidate.

The RA/RB split exposes a stronger template problem:

| projection | RA relevant | RB relevant |
|---|---:|---:|
| EXACT_WITNESSED_GRAPH | 6/16 | 0/16 |
| FULL_CHILD_TEXT | 3/16 | 2/16 |
| ACTIVE_LINKED_TEXT | 8/16 | 0/16 |
| NONE_OFF control | **16/16** | **0/16** |
| WRONG_ROOT control | **16/16** | **0/16** |

Across positive panels the split is **17/48 RA versus 2/48 RB**. More
damagingly, both negative controls choose the relevant probe on every RA task
and no RB task. Their aggregated 16/32 happens to remain under the frozen
18/32 maximum, but it is produced by complete view dependence, not calibrated
uncertainty.

RA and RB change both candidate order and wording (`Q TESTS ...` versus `TEST
... USING Q`) and RA is one token longer. They are not an order-only causal
pair. The numbered presentation also invites the exact `PROBE 1/2` failure.

## Design/implementation mismatch: the run removed THINK

The synthesis's Section 9 says:

> It may generate up to 2048 thought tokens and then commit exactly one ROUTE.

The exact-build ledger similarly calls the native allowance `<=2048 generated
thought/action tokens, one ROUTE`. The implemented `NATIVE_SYSTEM` instead
says `Commit exactly one ROUTE line`. The active system permits only one READ
line or a final ROUTE per turn. Runtime `_task` stops on the first non-READ
generation and passes the **entire raw generation** into `score_route`, whose
parser is a full regular-expression match.

Therefore the 2,048-token budget is only a maximum decode allowance. It is not
a thought budget. Any visible thinking would make the answer invalid. Standard
autoregressive generation has no hidden scratchpad here, so SEQ-167 tested
direct one-line action prediction, not the promised think-then-commit endpoint.

This mismatch is likely relevant to the direct-memory failure: the model
copies START/GOAL and salient ports but never performs the five-hop traversal.
It does not erase the observation that this exact answer-only interface failed;
it prevents generalizing that failure to a THINK-capable actor.

## Confirmed prompt/interface defects versus unresolved competence

### Confirmed: the READ language was never exposed

The public active-memory prompt says only "a permitted READ request." It does
not reveal any legal form. The frozen service accepts only:

- `READ EVENT <E_id>`;
- `READ EVENTS_AT <N_id>`;
- `READ LINKS_FROM <E_id>`.

The model inferred `READ <START>` and `READ <GOAL>` and placed both in one
turn. That is illegal, so all 64 delayed active tasks stop after the first
call. Reachout active tasks make no READ attempt at all. Consequently the
active-memory conditions expose **zero memory text** and are information-
equivalent to no-service runs after the initial prompt. Their failures cannot
support a reader or memory-quality conclusion.

This is a prompt/interface defect, with observed symptom `READ grammar
mismatch`; those are two levels of the same 64-row cause, not overlapping rows
in the classification table.

### Confirmed: reachout conflates relevance with presentation

Numbered answer framing, two different templates, and the 32/32 RA versus 0/32
RB control split show that the aggregate negative-control gate hides a first-
view / template policy. Current reachout numbers do not isolate memory-guided
experiment choice.

### Real under the current interface: direct five-hop composition fails

The exact graph, event atoms, and full text visibly contain the necessary
edges. Yet no direct-memory answer gives the correct five-hop route, even
under permissive punctuation parsing. The model copies start and goal
perfectly in 256/256 cases and emits the right command family, but does not
execute a connected path.

The output alone cannot decide whether this is fundamentally opaque-ID
reasoning capacity or the answer-only implementation suppressing the state
tracking the base model needs. A design-faithful thought/action interface on
development roots is the minimum discriminating experiment.

### Not supported

- **response budget:** excluded; zero truncations and short answers;
- **overthinking:** excluded for this capture; answers are terse;
- **syntax as the whole failure:** excluded; 142 exact-syntax positive routes
  still fail, and no invalid route becomes correct under comma-space repair;
- **LoRA, learning, or parenting failure:** inapplicable; this is frozen C0
  with zero fits, updates, adapters, or parents.

## Smallest DEV interface repair

Call the successor `C0-IFACE-R1`. It is a clean-base diagnostic, not a writer
or learner change. Do not retroactively rescore SEQ-167.

### 1. Keep cognitive content and exact action scoring fixed

Do not change:

- opaque task IDs, graph/memory rows, START/GOAL, relevant/distractor probes,
  route truth, or negative memories;
- frozen Qwen base, temperature 0, generous equal token envelope, exact
  route/probe parser, or graph execution scorer;
- zero-fit/zero-update/zero-parent scope.

### 2. Restore the typed thought -> action boundary

Allow the child to generate bounded free thought and then exactly one typed
action. Preserve the complete raw generation. Bind one action span by an exact
marker/tool boundary with byte offsets and a hash, and apply the existing
fullmatch parser to that payload only.

Reject missing actions, multiple actions, malformed markers, text inside the
action payload, and any post-action continuation. This is not semantic repair
or relaxed scoring: it is the prospective implementation of the already
specified THINK/action separation. It must never be used to salvage SEQ-167.

Use the same thought/action topology for C0, supplied service, and later LoRA
arms so the baseline is not easier than the learner.

### 3. Teach the interface generically, without task answers

Add a disjoint neutral example using fresh L8 identifiers that never occur in
any scored root:

```text
EDGE N_EXAMPLE_A P_EXAMPLE_X N_EXAMPLE_B
EDGE N_EXAMPLE_B P_EXAMPLE_Y N_EXAMPLE_C
START N_EXAMPLE_A
GOAL N_EXAMPLE_C
valid action: ROUTE N_EXAMPLE_A N_EXAMPLE_C : P_EXAMPLE_X,P_EXAMPLE_Y
```

Use actual grammar-valid neutral opaque strings in implementation, not these
mnemonic placeholders. State the generic algorithm explicitly:

1. current node starts at START;
2. choose an EDGE/EVENT whose source/`AT` equals current;
3. append its port/`DID` and set current to destination/`GOT`;
4. stop only when current equals GOAL;
5. never combine ports from disconnected branches;
6. commit exactly one route action, with no spaces after commas.

This supplies the task algorithm, not any scored route.

For the active service, expose the three legal READ forms verbatim and say
**one READ action per turn**. Give one disjoint neutral request/reply example.
The service contents, query bank, read cap, and returned-token cap remain
unchanged.

### 4. Make reachout order-only

Use one template for both views and swap only two otherwise identical lines:

```text
CANDIDATE PROBE Q_... TESTS N_... TO N_...
CANDIDATE PROBE Q_... TESTS N_... TO N_...
Commit one action by copying the chosen Q_ identifier:
PROBE <probe_id>
Never output a choice number or a node/event identifier.
```

State the decision rule generically: choose the experiment whose proposed
edge connects the START-reachable side toward the GOAL-reachable side. This
defines usefulness without identifying the scored candidate.

### 5. Preserve outcome-blind confirmation

SEQ-167 exposed all four current roots. They may be used as prompt-development
fixtures only. Freeze the repaired prompt, action projector, and parser bytes
before generating **four fresh excluded roots**. The fresh roots, not repaired
scores on viewed roots, provide confirmatory evidence.

If a typed-action implementation cannot land immediately, a prompt-only
answer-direct canary may test the READ grammar, exact example, and RA/RB repair
on the viewed DEV roots. Label it `ANSWER_DIRECT_INTERFACE_CANARY`; it cannot
qualify Section 9's mounted THINK endpoint.

## Controls and stopping rules

Minimum controls:

1. keep exact-graph, full/event, active-service, none, and wrong-root views;
2. retain the existing positive thresholds and report every root separately;
3. report RA and RB separately, plus first-position choice rate; an aggregate
   control pass with complete RA/RB separation is not acceptable;
4. require zero invalid READs and record served-read count per active task;
5. report exact action syntax, legal-path rate, and goal success separately;
   only the unchanged exact action-payload scorer is scientific;
6. keep ordinal outputs invalid; the repair prevents them rather than accepts
   them;
7. preserve byte/token equality of order-swapped candidate lines and use the
   same wording/template in RA/RB;
8. add typed-action provenance checks: one action span, exact byte offsets,
   source hash, no post-action tokens, no heuristic last-line extraction;
9. if the repaired clean-base exact-graph ceiling still fails, stop. Do not
   tune on fresh roots or relax the scorer. A later more scaffolded controller
   would be a separately labeled ceiling, not a rescue of this assay.

Before any learned-arm comparison, the repaired clean base should at minimum
pass the already frozen exact-graph/full/event/active ceilings, the existing
negative maxima, and the new presentation checks. For the 32-cell reachout
panels, the existing 30/32 positive gate already implies at least 14/16 in
each view if both views are reported; the two negative controls also need a
small predeclared RA/RB gap bound so 16/0 cannot pass invisibly.

## Scientific disposition

1. Preserve SEQ-167 as a useful interface autopsy, never a general competence
   result.
2. Do not use its zeroes to judge DREAM, SLEEP, LoRA, parenting, or strong
   memory.
3. Do not use `ACTIVE_LINKED_TEXT` as a strong evolving-memory baseline; it is
   a supplied service ceiling even after repair.
4. The separately preselected own-write formation test may proceed, but its
   later route/readout interpretation must wait for a clean-base interface
   ceiling that actually works.
5. A passing `C0-IFACE-R1` licenses only: **this frozen base can consume the
   supplied memory through the declared interface and emit the exact scored
   action.** It does not license acquisition, transport, retention,
   recurrence, compounding, or whole-agent claims.
