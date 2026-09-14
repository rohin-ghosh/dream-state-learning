# Rich versus terse grounded trajectories: bounded parallel pilot

**2026-09-14 — DESIGN PROPOSAL; Main adjudicates. No implementation or launch authorization from this note.**
Scope: a small independent data comparison alongside, not instead of or a prerequisite for, Main's scale collections. No claim that these captures, fits, or readouts have occurred. Frozen goal, breadth, scale, graph, and command helpers remain unchanged.

## Directive and source basis

Read `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, messages 64–68, including the raw directives:

- **64:** richer actual actor outputs and decision-station prompting; asks whether data is raw, masked, or compiled. Parenting should teach use of the learning loops, not just vocabulary.
- **65:** roughly 5–10× row tokens is explicitly an idea, not a ruling. Relevant articulation, not padding or a compulsory reasoning template, is the proposed mechanism.
- **66:** scale and parallel good-behavior DATA, supervised and critique learning; not another checklist of agent functions.
- **67:** richer LoRA-ready outputs and diversity, context distillation, with SFT first; reasoning-prompt intensity and critique/RL are hypotheses. Do not interpret richness as established sufficiency for learning. Main owns collections/launches.
- **68:** parallel research and possibly multiple generators; speed with comparison quality. An actor plus one bounded critic is enough to examine the multi-agent idea here; no agent framework is needed.

Code anchors: `experienced_event_read_route.parse_command` accepts only `READ EVENT E_…` or `ROUTE P_…`, ignoring final LF characters only; prose/JSON is not a valid action. `experienced_event_two_hop` allows six actor turns, four distinct reads and two commits, with actual reader text and public CURRENT/PORTS feedback. `experienced_event_goal_pairs` supplies four tasks, opposite-goal pairs `(0,2)` and `(1,3)`, and replay-backed pair scoring. `experienced_event_two_hop_lesson._plan` joins captured EVENTs, while `_coached_messages` adds researcher guidance that must not enter student prefixes. Its READ coaching also reveals the requested EVENT before the READ; do not carry that future observation into this pilot's rationale prompt. Existing encoders supervise final actual assistant plus EOT, with history and suffix masked.

## Question and minimal comparison

**Does supervising the actor's publicly grounded articulation improve parent-free goal-conditioned use of remembered edges, beyond supervising the exact same successful actions?** An articulate answer is not itself evidence of semantic memory use.

Propose four TRAIN worlds and two independently named PROBE worlds, using the unchanged graph/task construction under a new `ASTRA-RICH-20260914-PILOT-V1` namespace. Check identifiers against old worlds and current goal/breadth/scale registries before source collection. Do not repurpose any already-inspected PROBE as fresh. Freeze the six masters and starting adapter/base hashes before collection; this note does not assign their actual values. Main can collect TRAIN worlds independently in parallel. All arms consume the same captured source EVENTs and the same admitted trajectory IDs.

| Arm | Student target / labels | What its comparison adds |
| --- | --- | --- |
| TERSE | Exact action-field bytes extracted from the rich actor's actual response; action + EOT active | Paired command-only projection, **not** a separately sampled terse actor and not a fabricated command |
| RICH | Exact full emitted rationale/action envelope + EOT active | RICH versus TERSE tests the richer-output training recipe; includes more supervised tokens and changed target format |
| RICH_ACTION_ONLY | Same full token sequence as RICH; rationale and envelope delimiters masked, actual action + EOT active | RICH versus this arm isolates adding rationale/format supervision at identical teacher-forced inputs; TERSE versus this arm diagnoses conditioning on emitted rationale |
| ORIGINAL | Same initial adapter; no fit | Identical source/task/readout baseline, not a substitute for either loss control |

The third fit is recommended because otherwise a rich-versus-terse difference conflates additional rationale supervision, output format, and teacher-forced rationale conditioning. These comparisons still do not identify an internal reasoning mechanism. No separate generation of terse commands: that would lose exact source/action pairing and introduce a generator-quality confound.

## Actual generation, action separation, and visibility

1. Collect all four edges per world through actual exposure ROUTE and actual child EVENT calls, then replay those captures. Six worlds require at most **48 exposure calls**. Never replace failed events with canonical expected text. Only replay-valid complete TRAIN sources enter teaching; all incomplete sources stay in evidence.
2. On TRAIN only, attempt tasks 0,1,2,3 once, at most six turns each: **16 episodes / 96 actual actor calls maximum**. No retries or invented fixes. Source-informed coaching may request the next read or route, but it is logged as researcher instruction, not evidence that the child discovered a plan.
3. At each station request an **observable explanation**, not hidden/private reasoning: “Explain what in your available observations matters to this goal, how it bears on your next action, and what you expect to observe. Use detail where useful; do not invent evidence.” Record exact prompt bytes. The richer explanation can be wrong; it is model output, not privileged access to cognition or proof of the claimed connection.
4. Use one explicit native response envelope:

   ```text
   RATIONALE
   <actual actor-written text>
   ACTION
   <exactly one existing-grammar command, optional final LF>
   ```

   Require exactly one delimiter of each kind at the specified positions, nonempty rationale, a terminal nontruncated response, and an action accepted by the unchanged parser. Preserve raw response and byte offsets. Do not find a command anywhere in free prose, trim arbitrary whitespace, repair identifiers, or choose among multiple actions. A malformed envelope ends that attempt as a captured failure.
5. Feed **only the exact action slice** to the frozen environment runtime. The explanation cannot commit a route, generate a memory result, or simulate the next turn. Keep a separate native capture and an explicit projection receipt linking raw response hash/offsets to the action-trace hash. The projected hop trace is not itself the native generation record; do not overwrite its provenance or claim identical guided/unguided prompts.
6. Keep subsequent actor history action-only plus actual public replies. Explanation text is a non-recurrent sidecar for this pilot, not a new memory channel. This makes each rich/terse row share an identical parent-free prefix and avoids silently changing later action contexts between the two compiled arms. A recurrent rationale-history experiment would be separate.
7. Use a small **new pilot public response contract** allowing either the envelope or a single command; do not combine an envelope instruction with the frozen system instruction forbidding all non-command text. The actual action contract remains turnbound. In student prefixes retain this neutral format contract, task, actual prior actions, and actual feedback. Strip articulation requests, teacher commands, raw parent source blocks, critic text, and parent role markers by constructing prefixes from the saved public conversation, not string replacement.
8. For READ turns, the coach can specify the public address but must not reveal its not-yet-returned EVENT or expected outcome. After actual reads, routing coaching can show the two joined **already observed** EVENTs. A prediction is marked as a prediction, never as an observed receipt; the next runtime reply decides whether it occurred. Do not synthesize a successful final reflection: terminal feedback is evidence, not another actor target unless actually requested in a separately counted call.

Retain the **2,048 context / 160 generated-token** caps initially, including EOT in target accounting. Short commands leave room for substantial articulation without increasing caps. Measure the achieved token ratio; 5–10× is a diagnostic target, not an admission quota. No padding, silent truncation, or token-cap escalation. If the bound prevents usable output, Main chooses a separately declared cap change rather than this pilot quietly changing limits.

## Train-only judgment, public grounding, and admission

- The TRAIN admission judge uses replayed actions/outcomes: four real reads, source-supported first port, the actual intermediate reached before the second route, two legal commits, final goal, and source/prompt/capture joins. It does not award success for a fluent rationale, claimed receipt, or teacher's expected command.
- Check rationale identifiers and asserted EVENT/transition quotations against observations already visible at that turn. Teacher-only/future observations and copied guidance are grounds to exclude the **entire episode from every arm**, not to rewrite its rationale. Free-form semantic claims are not fully certified by identifier checks; label unsupported or ambiguous claims as such. Inspect a fixed TRAIN-only sample (all 16 episodes is bounded here), reporting contradictions/uncertainty rather than declaring prose valid because routes succeed. If a stricter content filter is chosen, freeze its rubric before comparing arms and apply the same episode set to all three.
- Primary admission is complete paired episodes: retain both members of `(0,2)` or neither, and both members of `(1,3)` or neither. Record every attempted task, dropped pair, and reason, including wrong-goal legal trajectories and malformed explanations. No selecting a different successful subset for RICH and TERSE. Prefer all **eight TRAIN goal pairs / 96 turns** for this small comparison; if incomplete, report collection/admission failure and do not fit a silently reduced pilot.
- Held PROBE tasks, scores, missing-memory outcomes, and audit labels never enter teacher or critic prompts, row admission, prompt selection, or training. A fixed evaluation reducer may score held results only after fit; it is not the training judge.

## Small actual-child critic branch

In parallel, optionally ask an actual child critic for **one critique per TRAIN episode**, maximum **16 calls**. It sees the public task, emitted explanation/actions and real replies; no private weights, parent plan, held task, or sealed score. Ask it to identify a specific observed inconsistency or unsupported claim, distinguish prediction from observation, and suggest one next check. Keep exact responses, identity/state receipts, errors and referenced episode hashes, including mistaken criticism. A correct actor output is not automatically a correct critique, and an articulate critique is not an oracle.

First use these captures diagnostically; do not include them in the primary three fits or let a model's “pass” override transition evidence. If Main selects a later critic own-data fit, its targets must be these actual critic responses, paired to the original episode, with instruction/history masked and contradictory/unverifiable critiques retained as rejected evidence rather than silently repaired. A bad actor trajectory may be masked context for an evidenced critique, **never an active successful-action target**. Training critiques would add tokens, output behavior and a selection mechanism, so it requires its own declared arm. It is not RL/CFT merely because a critic was called, and no revised successful action can be claimed without a separately executed child attempt.

## Compilation and accounting

The data path is **raw native capture -> explicit action projection -> actual runtime feedback -> train-only outcome admission -> three paired masked row views**. “Compiled” here means byte selection and masking, not authored richer text.

- Pair key: `(collection_sha256, master, task_index, episode_call_index, native_call_sha256)`; every arm has the same ordered 96 keys. Store raw response, action/rationale offsets, public-prefix hash, guided-prompt hash, source EVENT hashes, episode/projection receipt, tokenizer/template hashes, and selection-reason manifest. The RICH target is emitted bytes; TERSE is explicitly labeled a projection. Preserve parent evidence outside encoded training bytes.
- RICH and RICH_ACTION_ONLY must have identical input IDs and target spans; only label masks differ. TERSE has the same public prefix but omits the envelope/rationale target bytes. Check action/EOT token boundaries against the **actual rendered sequence**; do not assume substring tokenization composes or reuse the old 48/192-row encoder unchanged. All history and template suffix remain masked. No truncation, guessed offsets, or fabricated EOT evidence.
- Suggested finite pilot: **three sibling fits of 32 optimizer updates** from one identical initial adapter/base/optimizer recipe. Each update carries three trajectory rows plus 32 fixed old-fact replay rows; a fixed paired row order presents all 96 trajectory rows exactly once. Cycle the 16 old facts equally: 1,024 old presentations, 64 per fact. Same old row IDs, masks, LR, optimizer, accumulation and row order in all arms; sealed audit rows are never training rows. Main must accept this proposed schedule or substitute and freeze its actual native schedule before collection comparison, not tune it from held outcomes.
- Use a shared **reference denominator** per update: active old-fact tokens plus TERSE action/EOT tokens for those three pair keys. Sum active loss over the whole update before dividing; accumulation/microbatch partition must not silently change weighting. RICH adds rationale/format loss without silently diluting old/action loss through a larger mean denominator. RICH_ACTION_ONLY uses that same denominator, though its action tokenization may differ; log the exact difference rather than assume token counts equal.
- Log per row/step/arm: input tokens, rationale/delimiter/action/EOT active tokens, masked tokens, old active tokens, reference denominator, row presentations, optimizer updates, gradient norm/clipping, and saved-state/base hashes. Report total and per-pair RICH:TERSE supervised-token ratios, generated tokens and generation cost separately from training presentations. Do not reuse 8,245 from another recipe as this pilot's denominator.
- Matched updates and source/action presentations are **not matched supervised tokens, gradients, retention, or compute**. If a rich advantage remains worth pursuing, the smallest subsequent dose check is a prospectively token-matched terse-repeat arm with its extra updates/action presentations disclosed; it cannot retroactively make this pilot token-matched. Do not automatically launch that fourth fit.

## Parent-free readouts, budget, and interpretation

Run the same frozen command-only turnbound readout on ORIGINAL and all three saved states. This tests action execution rather than rewarding a newly trained wrapper. Extra rationale/format output remains an `invalid_command`, not silently stripped at readout; show this error category separately. A later envelope-capable readout would be a different, prospectively paired interface condition.

- TRAIN: all 16 tasks with OWN_TEXT; **96 actor calls maximum per state**. These are acquisition checks, not transfer.
- PROBE: all eight tasks in OWN_TEXT and UNAVAILABLE, same task order, exact source text bytes and common unavailable reply across states; **96 actor calls maximum per state**. PROBE sources are newly captured instances available equally to every arm; never taught, but not a new graph family. Keep all outcomes, including failures/early closure.
- Per state: 16 old facts at W0 and W8 plus 16 held audit checks = **48 additional calls**, assuming the existing one-call-per-check reader. Record whether W8 is a prompt condition or another procedure in Main's native manifest; if it performs additional actions, revise the cap before execution, not afterward.
- Thus the proposed maximum is **240 readout calls × four states = 960**, plus **48 exposure + 96 rich-actor teaching = 144**, totaling **1,104 native calls**; optional critic raises this to **1,120**. Three fits / 96 optimizer updates total. Early failures reduce actual calls but never reduce declared denominators without explanation. These are proposed ceilings, not observations or launched work.

Primary report: PROBE goals `/8` and goal pairs `/4` per condition/state; each pair additionally reports both goals correct, distinct source-correct first ports, and two legal commits. Show task indexes, first commands/ports, intermediate/terminal nodes, read counts, invalid-command versus invalid-route versus dead-end errors. A goal-independent first-port policy can get 2/4 tasks but 0/2 pairs within a world; individual accuracy alone cannot establish semantic goal use. Include TRAIN `/16`, `/8` pairs and old/audit costs, with actual loaded-state/readout joins.

| Observed comparison | Bounded interpretation / next decision |
| --- | --- |
| Longer output but no held pair improvement | Richness manipulation alone did not improve this endpoint; inspect grounded content and action errors, not a new dose escalation by default |
| RICH improves held OWN_TEXT pairs over both controls, UNAVAILABLE does not | Supports this grounded richer-supervision recipe for use of available memory on fixed held worlds; then consider dose-matched follow-up, not broad intelligence claims |
| RICH and RICH_ACTION_ONLY both beat TERSE | Rationale conditioning/format exposure may explain benefit; rationale loss itself has not been isolated as useful |
| Acquisition rises, held pairs tie; retention drops | Memorized taught instances or damaging training tradeoff, not demonstrated transferable goal selection |
| UNAVAILABLE also succeeds | Inspect prior knowledge, structural guessing, and namespace leakage; not proof of retrieval-grounded behavior |

These two held worlds provide a small descriptive comparison, not independent population inference. Shared raw trajectories and controlled prompts reduce confounds; they do not prove explanation truth, private reasoning, self-directed discovery, closed-loop learning, generalized planning, or H1/H2. The old retained effect must be measured, never assumed equal because schedules match.

## Proposed implementation interfaces and Main's open decision

Names below are proposed contracts, not implemented helpers or a new agent architecture:

```text
collect_rich_episode(runtime, collection, task_index, generate, *, coach_prompt, caps)
  -> {native_captures, action_projections, episode, errors}
project_action(raw_response)
  -> {action_bytes, rationale_span, action_span, raw_sha256}  # reject, never repair
compile_paired_rows(train_episode_bundle, train_admission_manifest)
  -> {TERSE, RICH, RICH_ACTION_ONLY, pair_manifest, rejection_evidence}
encode_paired_rows(paired_rows, tokenizer)
  -> {arm: input_ids/labels/spans}, per-row-token-ledger
capture_train_critique(train_episode, generate_critic, *, caps)
  -> {actual_critic_capture, public_evidence_refs, unresolved_claims}
```

Reuse existing world/task generation, exposure replay, command parser, action runtime and pair reducer. The necessary new part is a small native-envelope/projection capture and paired encoder; plain rich prose must not be forced through the frozen command-only collector or misrepresented as old-helper-compatible raw output.

**Unresolved decision for Main:** approve the three-arm **non-recurrent public-explanation / exact-action projection** pilot and common-prefix contract, or prefer a simpler two-fit RICH/TERSE recipe with its conditioning/format confounds explicitly accepted? Separately bind the six masters, initial state, exact coaching bytes, TRAIN content-review rubric and native schedule. Critic collection can remain an optional 16-call diagnostic sidecar; fitting critic data is not included. This proposal neither changes nor gates the running scale work.

**Ownership released for Main's design adjudication.** Only this note was authored; no code, notebook, model, GPU, or remote action was performed for this design task.
