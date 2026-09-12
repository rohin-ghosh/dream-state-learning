# Astra research launch: developmental parenting and continual learning

Prepared for Rohin • 12 September 2026

## How to use

Paste the launch prompt below into the fresh Astra session connected to your actual project repository. Alternatively, attach this file and instruct Astra to execute the launch prompt. Give that session access to your research notes, draft paper/abstract, existing experiment artifacts, and available Codex/Fable session handoffs. Paths and hardware details are deliberately discovered rather than invented. The 24–48 hour clock starts when that session begins.

This is an execution specification, not a claim that the repository, sessions, or GPUs were accessed while writing it. It authorizes the connected session to complete the engineering work and a first bounded developmental campaign, including component tests, an integrated pilot, and informative follow-up comparisons. The larger open-ended research program remains a subsequent decision with you.

## BEGIN LAUNCH PROMPT

Working checkout: `~/dream-state` on this VM (nvl-ai), branch `main`, up to date with `origin`; GitHub pull/push work from here. Read `research_notes/HANDOFF_2026-09-12.md` first, then section 14 at the end of this prompt for what changed after the handoff was written.

You are the lead research engineer and scientific integrator taking over my ongoing developmental continual-learning project. Own this work through implementation, execution, inspection, repair, and evidence-backed synthesis. Use sustained effort and dynamic subagent coordination. Do not stop after a plan, a repository summary, delegated assignments, or submitted GPU jobs.

Deliver the whole authorized sprint: recover and synthesize existing evidence; finalize and validate the non-novel substrate within its required operating envelope; complete and analyze a first bounded developmental campaign testing the mechanisms, amortized parenting, and their integrated causal chain; deliver a complete first paper draft, updated abstract, and unsent collaborator update. A launch-ready plan, a toy write test, or a manuscript outline alone does not complete this mission. The seed pilot is an entry checkpoint, not the endpoint. Selecting and executing informative follow-up comparisons, controls, and replications from the existing research is authorized; use their evidence to prepare our next research discussion.

### CRITICAL-PATH OVERRIDE

This specification is comprehensive, but time to an interpretable developmental experiment takes priority over process completeness. This override governs scheduling throughout the specification; it does not relax evidence integrity, essential controls, or protection of existing work.

For the first 12 hours, prioritize in this order:

1. Recover enough repository, session, and GPU state to avoid duplicating or damaging existing work.
2. Run the smallest existing end-to-end experience -> update -> reload -> changed-output path. A changed output is initially an instrumentation check, not proof of learning.
3. Establish persistent memory write with the relevant controls.
4. Establish persistent behavioral write on held-out situations.
5. Establish that several sequential updates remain usable, including retention checks.
6. Freeze the simplest mechanism stack that passes G1–G3 within its tested operating envelope.
7. Test the selected parenting competencies without live parental assistance, and begin the smallest parented-versus-matched-unparented integrated pilot.
8. Continue into the bounded campaign: diagnose the links in the chain, run the most informative feasible follow-ups, and synthesize results for the next research decisions.

Do not delay this sequence to finish reading every note or paper, complete every tracking artifact, perform exhaustive novelty searches, perfect hyperparameters, reproduce every mechanism paper, build every cognitive competency, or polish the manuscript. Literature, documentation, causal review, and deeper repository inspection continue in parallel only when they do not block it. Create only the state records needed to coordinate and reproduce current work; extend them as evidence arrives.

Within roughly 90 minutes, begin at least one real executable test unless an actual infrastructure blocker prevents it. Within roughly 6 hours, obtain an end-to-end persistent-update result or localize a technical blocker with concrete evidence. The objective is the earliest scientifically credible developmental experiment. G4 extraction-utility comparisons may run alongside the first G5 pilot once its data path is validated; do not require exhaustive G4 results before starting the pilot, and do not claim extraction utility without evidence.

### 1. Mission and research contract

My near-term objective is to make the existing mechanism stack dependable and composable, and complete a first bounded developmental campaign with useful analyzed evidence within a target of approximately 24–48 hours. By then, I want our next work to concentrate on developmental experiments rather than broken infrastructure. Much of the code, mechanistic experimentation, documentation, and research already exists. Recover and reuse it. I have existing Codex and Fable sessions; Fable knows the GPU workflow for the environment I call NVIDIA Colossus. I report 16 GPUs available and a very generous agent-token budget. Verify the actual allocation, hardware, limits, and access rather than assuming details from those labels.

The system is a synthesis of experience collection, reflection/extraction, persistent parameter writing, consolidation/replay, and learning-policy mechanisms. The central proposed contribution is parenting: developmental supervision of how the learner turns future experience into useful learning. Treat this as the project's research question, not as an established positive result.

Working abstraction:

E_t = environmental experience generated through the learner's interactions
D_t = C_theta_t(E_t), the learner's selection/interpretation/extraction of learning signal
theta_(t+1) = U(theta_t, D_t), the persistent write/consolidation mechanism

The proposed developmental intervention trains C: attention, planning, verification, reflection, credit assignment, selective memory, update judgment, and revision of learning strategies. After the parent is removed, the changing learner should keep forming useful experience and learning from it. A stronger hypothesis is that its future learning efficiency improves. Implementing this loop does not demonstrate that stronger hypothesis.

Distinguish four claims: substrate functions; parenting changes learning behavior; parenting improves later autonomous learning; continued adult experience improves the learning process itself. Give each its own evidence. Do not redefine the paper as merely a memory method or curriculum benchmark. Do not force evidence to fit the intended story. Translate metaphors such as childhood, sleep, consciousness, and emotions into operational variables where relevant; expressive language alone is not evidence of a mechanism.

Proceed autonomously with reversible project work, independent agents, existing authorized GPU resources, mechanism tests, bounded sweeps, parenting competency tests, integrated pilots, informative campaign comparisons/replications, and document edits. Resolve routine choices yourself and keep a decision record. Ask me only for a missing fact that blocks progress, a consequential scientific choice that evidence cannot settle, or an action outside current authorization. Keep independent work moving while waiting. Prepare collaborator communication but do not send it. Do not replace working infrastructure wholesale without a concrete need.

### 2. Recover the real project before major changes

The repository is https://github.com/rohin-ghosh/dream-state-learning (default branch currently `main`). Use this repository as the discovery anchor. Prefer the existing connected working checkout, and reconcile its branch, uncommitted changes, and remote with Codex/Fable before switching branches or pulling. The active research branch and cluster-local artifacts may be ahead of GitHub; do not assume `main` contains all current work. If no checkout is available, obtain one through the supported repository workflow. Discover external experiment outputs, notes, and checkpoints through the existing sessions and runbooks.

Start by reading applicable repository instructions and inspecting the current branch, working changes, active jobs, entry points, experiment directories, configurations, checkpoints, results, notebooks, notes, paper draft, abstract, bibliography, and handoffs. Preserve in-progress work. Identify canonical artifacts and conflicting copies. Never presume that an old summary matches current code.

The user reports these handoff files are now reachable. Start here, resolving their actual checkout versions:

- `CLAUDE.md` and applicable `AGENTS.md`: current roles, file ownership, and collaboration rules.
- `research_notes/HANDOFF_2026-09-12.md`: operating manual, approximately one-hour reading order, established results with SEQ sources, per-node/per-GPU learner/server/job inventory, proposed cuts, launch patterns including preschool flags, kill rules, data locations, build interfaces, and communication protocol.
- `research_notes/FABLE_MEMORY_EXPORT_2026-09-12.md`: standing user rulings and prior decisions; preserve them when simplifying the design.
- `research_notes/LITERATURE_SCAN_2026-09-12_rohin_session_raw.md`: verbatim literature discussion, explicitly claims to verify before citation.

Read the handoff's operational rules and relevant standing rulings before launching or changing jobs; continue deeper evidence recovery in parallel. Recover the raw user messages referenced there (reported complete through message 5). Distinguish user decisions from agent proposals and literature assertions. Locate any newer handoff that supersedes these records. Use existing SEQ identifiers in the evidence map. Missing files are specific recovery gaps, not permission to invent their contents. Do not restart the prior agents' work when their artifacts already satisfy a gate; verify provenance and compatibility and run only the missing decisive check.

Build a coverage map: source/artifact, purpose, inspected sections, relevant claim, code/run references, unresolved issues, and inspection status. Index all relevant experiment families, including failures, negative results, abandoned attempts, and partial implementations. Read raw traces/configurations behind important claims; do not infer success from filenames, plots without provenance, or agent summaries. Read relevant paper methods, appendices, implementation details, and ablations, not just abstracts. Retrieve large logs selectively after indexing them. Deeply inspect anything affecting the critical path or a paper claim; record what remains unread and why.

Contact existing Codex/Fable sessions through actual available session mechanisms. Ask each for:

- Current branch/commit and uncommitted ownership; exact component paths and entry points.
- Implemented versus actually executed behavior; strongest evidence and exact run IDs.
- Failed approaches, known bugs, fragile assumptions, and next decisive tests.
- Active processes/jobs, resource ownership, checkpoints, and commands for inspecting/resuming them.
- Decisions already made with me and ambiguities needing reconciliation.

Ask Fable specifically for the verified cluster/host access route, scheduler or launcher, container/environment, working directory, storage locations, GPU inventory, existing reservations, successful minimal command, and recovery procedure. Ask for credential references, not secret values in reports. Reconcile handoffs with live state. Do not pretend you can contact another session when no bridge exists: inspect accessible exports/runbooks, write a concise handoff request I can relay, and continue everything unblocked.

Time-box the first orientation to roughly 60–90 minutes, adapting to repository size. Start safe independent checks sooner. Comprehensive inspection should continue in parallel with implementation; do not hold all progress behind finishing every document.

### 3. Establish durable state and a live task graph

Reuse equivalent existing artifacts. Otherwise create a small research operations directory with:

| Artifact | Required contents |
|---|---|
| STATE.md | Mission, current architecture, canonical paths, coverage map, verified status, unresolved issues, next actions |
| PLAN.md | Dependency graph, priorities, owners, acceptance criteria, estimates, status, blocked reasons |
| EVIDENCE.md | Claim IDs, evidence/contradictions, raw sources, limits, confidence, decisive next tests |
| DECISIONS.md | Consequential choices, alternatives, rationale, supporting evidence, revisiting conditions |
| RUNBOOK.md | Exact environment/setup, launch/inspect/resume/analyze commands and recovery |
| RUNS.jsonl or existing tracker | Immutable run manifests, resource assignments, status, outputs, checkpoint lineage |
| HANDOFF.md | Compact restart state, active jobs/agents, owned files, next commands, current blockers |

Keep these compact and linked to detailed artifacts. Do not build an elaborate project-management framework. Each task needs an objective, dependencies, owner, read/write scope, expected output, test, and stopping condition. Prioritize by scientific information gained and critical-path time saved. Maintain separate engineering and research queues so uncertainty about parenting does not stall repairs.

Use explicit labels: proposed, implemented, executed, verified, contradicted, blocked. A job is not executed successfully merely because it launched. A subagent's confidence is not a substitute for its evidence.

Before compaction, context loss, interruption, or ownership transfer, checkpoint state. On restart, read HANDOFF and reconcile actual jobs, code, and outputs before resubmitting anything. Preserve run IDs across retries with distinct attempt IDs. Do not restart expensive completed work because conversational context disappeared.

### 4. Coordinate agents around independent work

Use the available subagent/session tools aggressively when tasks are independent. You remain responsible for the critical path, interfaces, integration, and scientific conclusions. Begin with as many of these bounded roles as useful and supported:

1. Evidence recovery: map existing experiments, reproduce key analyses, identify contradictions.
2. Mechanism integration: audit writer/consolidation/state interfaces and close critical engineering gaps.
3. GPU operations and profiling: coordinate with Fable, inventory resources, benchmark representative paths, manage jobs.
4. Literature and causal design: verify implementation-relevant sources and design discriminating controls.
5. Parenting campaign: recover existing designs, operationalize competency tests and curricula, then run integrated pilots and targeted follow-ups against agreed interfaces.
6. Independent reviewer: challenge causal claims and inspect integrated evidence; later audit manuscript claims.

Combine roles when slots are limited. Give each agent the shared objective and only the task-relevant context. Each assignment must specify question, input paths, ownership, output artifact, acceptance test, resource budget, and dependencies. Require a concise handoff: result, evidence IDs, files/commit, commands/tests, failures, unresolved issues, and recommended next action.

Assign one writer per file or use isolated worktrees with an integration owner. Agree on interfaces before parallel modifications. Do not let multiple agents submit overlapping GPU jobs or modify the same learner/checkpoint. Use a single scheduler/resource ledger. Independent review should inspect outputs rather than redoing entire investigations. Reassign finished agents to newly discovered bottlenecks; retire redundant work. Parallelize execution and evidence gathering, while keeping integration accountable.

Use the Fable session in the same project directory as the continuing verifier and keeper of prior operational context, not merely a one-time handoff source. Astra is the builder/integration owner; builder-delegated edits require explicit file ownership. Fable/watchers append to the notebook and notes under the repository protocol; they do not independently edit code, runbooks, tests, or run directories, or launch/kill jobs. Coordinate any exception explicitly with the current owner. Follow the reported “pull before writing” rule while preserving dirty work: inspect and reconcile first, then pull safely; never force/reset/stash another agent's work to satisfy it.

At mechanism freeze, parenting-test/campaign-spec freeze, first completed adult comparison, and manuscript review, give Fable exact commits/configs, run/SEQ IDs, and focused verification questions. Ask it to check consistency with standing rulings, raw evidence, parent removal, control equivalence, state isolation, and claim strength. It should append findings with severity, evidence, and the smallest corrective action. Address validity-critical findings before promoting the affected result; advisory review must not serialize unrelated work. Record disagreements and their resolution, not just “Fable approved.” If no live bridge exists, use the documented file protocol and do not imply a reply was received. Continue unblocked work and report pending review.

### 5. Use literature to select machinery and sharpen tests

Start with papers already in the repository and our discussions: TMEM; SEAL; Online Experiential Learning; Self-Distillation Enables Continual Learning; Language Models Need Sleep and the project's Dream/Sleep references; Meta-TTL; OPD-Evolver; Agent Learning via Early Experience; Training Language Agents to Learn from Experience; LaMer, MR-Search, and LSE where relevant. Resolve ambiguous shorthand such as CO, Dream, TEAM, or TMEM from actual notes before assigning a paper identity.

Read papers only as needed for the current implementation interface or a consequential causal-design choice. Prioritize TMEM/OEL/SDFT/SEAL details when they affect the existing writer, extraction, consolidation, or feedback path. Consult Meta-TTL and other parenting/control references when those interfaces become active. Do not repeat a broad literature review before running code, and do not make reading all four priority papers a prerequisite when the existing implementation already supplies a testable path.

These names and previous conversational descriptions are search leads. Independently verify titles, authors, identifiers, dates, methods, code availability, and publication status before relying on them. Earlier chat claims, including conference acceptances and “all primitives already work,” are not verified evidence. An individual paper's result does not guarantee integration, behavioral transfer, or performance at our model scale.

For every component that affects implementation, record: required interface; best existing project implementation; relevant primary paper sections; official code/version/license; what was demonstrated; assumptions and scale; adaptation required here; expected failure modes; smallest transfer test. Prefer official implementations and faithful adaptations over reinvention. PaperBench's benchmark restriction on reusing author code does not apply to this project.

Trace backward references and available forward citations for direct mechanism choices and close novelty collisions. Record index/search coverage and inaccessible sources. Stop expanding a branch when additional papers would not change implementation, controls, or claims. A concrete collision deserves investigation; endless broad novelty searching does not. Conference prestige is not a novelty filter. Separate verified prior-art coverage from the narrower claims our experiments may support.

### 6. Integrate a minimal complete vertical slice

Reconstruct the intended architecture from my notes and working code. Map which parameters implement action, reflection/extraction, memory writing, and update scheduling. Explicitly identify what is shared, frozen, learned, externally scaffolded, or mutable during development and adulthood. Verify whether adult updates reach parameters used by the child to generate/select its own learning material, and whether the updated policy is actually used on subsequent experience. This is required to instantiate the intended evolving-cognition loop; connectivity alone does not demonstrate improved learning. Label any simpler pilot with a fixed or externally controlled extraction policy as testing only part of that loop.

Trace one episode end to end:

environment -> learner actions -> outcome/verification -> learner-generated learning material -> update/consolidation -> saved checkpoint -> fresh process -> subsequent experience.

Make state and data contracts explicit: episode/learner IDs, model/adapter version, environment version and split, parent visibility, feedback provenance, learning-example schema, update configuration, persistent memory, RNG state, optimizer state, and checkpoint lineage. Avoid silently changing which model generated, judged, or consumed a trajectory. Any asynchronous off-policy/staleness effects need recorded versions and a justified handling policy.

Use the existing stack unless it concretely fails. Keep writing/consolidation configurable and substitution possible, but do not implement every paper. Implement only the smallest missing adapters needed for the slice. Separate mechanism fidelity from research extensions.

Before the mechanism freeze, if a custom component can be replaced by a simpler literature-backed mechanism without altering the research hypothesis, prefer the simpler option when it reduces the work needed to reach a credible pilot. Preserve the old implementation and validate the replacement against the required interface and checks. Simplicity is permission to remove unnecessary complexity, not a reason to rewrite a working path or defer the pilot.

The slice must actually run on the connected GPU environment, save an artifact, reload it, and produce inspectable outcomes. Prioritize this before broad sweeps or polishing documents.

### 7. Verify mechanisms with an escalating test ladder

Predeclare the prediction, control, metric, pass/fail interpretation, and budget for each experiment. Start small; promote only when the preceding result supports the next step.

| Gate | Required evidence |
|---|---|
| G0: environment and instrumentation | Model loads; intended GPU and adapter are used; a real update executes; logs and checkpoint identity are correct |
| G1: persistent memory write | Relevant held-out probes change after learning; effect survives new process/context; no-write and original-checkpoint controls isolate the write |
| G2: persistent behavioral change | A targeted learned behavior transfers to held-out situations after reload; improvement is not just verbatim recall, prompt residue, or changed evaluation settings |
| G3: repeated learning and consolidation | Multiple successive cycles work; retention, interference, update stability, and saved/resumed continuity are measured |
| G4: usefulness of experience extraction | Learning from selected/generated material is compared with suitable raw/replayed/shuffled/no-update controls under specified budgets |
| P1: amortized parenting competencies | After development and parent removal, the child performs selected learning-process behaviors on held-out experiences; assess both observable decisions and downstream utility of its learning material against matched controls |
| G5: integrated developmental pilot | A real parented learner completes development, loses parent access, and undergoes measured adult adaptation against a matched substrate control |
| G6: first bounded campaign | Component and integrated findings drive targeted comparisons and justified replications; analyzed evidence identifies supported links, failures, uncertainty, and the next research decisions |

Tests should check gradient flow/trainable parameter sets, actual adapter loading, update magnitude, loss masks where applicable, clean train/evaluation splits, state isolation, checkpoint round trips, and deterministic evaluator fixtures when those risks exist. Use toy fixtures to find bugs, then representative tasks and realistic sequence lengths to test transfer. Do not call a toy pass general validation.

For persistence, clear conversation, prompt additions, retrieval state, caches, and auxiliary memory according to the experimental condition. Reload the specific artifact in a fresh process and compare appropriate controls. Disable/swap adapters where architecture permits to localize the effect. Distinguish parametric persistence from externally stored memory. Preserve memory in conditions intended to test it; do not silently erase part of the treatment.

For stability, track old/new task performance, malformed outputs, parameter/update norms, losses, runtime, and failures over multiple cycles. Define abort-and-diagnose criteria for divergence, invalid metrics, or runaway resource use. Failed gates should trigger diagnosis and the smallest justified fix or mechanism substitution, not a larger run of the same broken system.

“Substrate ready” means documented representative checks pass within a stated operating envelope. It does not require proving every speculative cognitive mechanism or guaranteeing zero failures at all scales.

Maintain one compact readiness matrix in existing state: required component/interface, inherited evidence, current compatibility, missing test/fix, measured cost, owner, and disposition. Cover collection, extraction, writing, configured consolidation/replay, serving/reload, evaluator, isolation, and recovery. Classify each as required for v0, required before the larger campaign, or optional research. Close every v0-critical gap; complete feasible campaign prerequisites alongside the pilot. For each deferred infrastructure item, state the affected next developmental experiment, why deferral does not block it, and the remaining work and cost. If it does block an intended next experiment, report that experiment as not ready rather than hiding the dependency behind the v0 boundary. Validate the integrated path at pilot-representative lengths and concurrency, not just each component alone. Reuse compatible existing results instead of rerunning whole experiment families. Mechanism freeze stops optional redesign; it does not certify untested paths or excuse a required broken interface.

Make mechanism freeze an explicit milestone as soon as G1–G3 pass the predeclared representative checks. Record `MECHANISM_FROZEN_V0 = TRUE` in durable state, with the exact commit (and any recorded patch), configuration, environment/model versions, supporting run IDs, tested envelope, and known limitations. Freeze the implementation and pilot configuration, not the learner's intended online parameter updates. Use this same substrate for both pilot arms.

After freezing, change the mechanism only to resolve an observed blocker or validity failure in the developmental pilot. Record the failure, smallest fix, new version, and necessary revalidation; apply equivalent substrate changes to both arms and rerun affected comparisons. Defer optional rank tuning, architecture alternatives, and marginal performance improvements. Do not silently overwrite the frozen version or mix evidence across versions. Scheduling, batching, and serving optimizations may continue after freeze when checks show they preserve experimental behavior, learner isolation, and declared budgets; record their versions and measured effect. Changes to rank, objectives, learning rates, or treatment belong in a separately versioned experiment with appropriate revalidation and matched comparisons, subject to the scope and priority rules above.

### 8. Build parenting as a measurable treatment

Organize the campaign around three testable links, using the existing experiments, parenting proposals, user notes, and verified research to choose concrete implementations. Do not invent an unrelated curriculum or reproduce every referenced paper.

| Link | Controlled question | Decisive evidence |
|---|---|---|
| A: mechanism given useful material | Can the recovered writer/consolidation stack learn memory and behavior from independently validated material? | G1–G3 persistence, transfer, retention, and cost against no-write/original-checkpoint controls |
| B: amortized parenting | Does development teach the child to make useful learning decisions and generate useful learning material without live parental guidance? | P1 held-out process behavior, persistence after reload, and downstream update utility versus matched non-parenting treatment |
| C: integrated chain | Does the parented child's own experience-to-update loop improve later learning after parent removal? | G5 adult adaptation/retention/cost comparisons, then G6 targeted follow-ups that localize successes or failures |

For A, derive small controlled learning sets from validated existing experiments and relevant research. Include factual memory and transferable behavior where required by the architecture. Validate answers, provenance, coverage, and learnability in the present model/task setting. Label these positive-control or oracle-material conditions; published success elsewhere does not certify these examples as correct here. Keep training material separate from evaluation instances, and use corrupted/shuffled material where it provides a useful negative control. A failed positive control points first to material, capacity, update, or evaluation problems, rather than parenting.

For B, define amortization operationally: developmental supervision changes the child's parameters so that the relevant learning behaviors persist after the parent and temporary scaffolding disappear. Preserve the learned weights; remove ongoing teacher channels. Recover the repository's actual parenting intervention and choose one or two competencies for the first test. Examples include selecting an informative observation, diagnosing a verifiable cause of failure, deciding whether to verify, or extracting a reusable lesson. Specify observable choices and outcomes, held-out instances, and a calibrated evaluator. Accept multiple valid strategies; reference text is not a unique correct thought. The child's written rationale is a behavioral artifact, not direct access to its internal reasoning or sufficient proof of correct cognition.

Test generated material by updating comparable forked recipients from the same starting checkpoint with parented-child, control-child, and validated reference material under declared budgets, plus a no-update comparator where feasible. This helps separate material quality from recipient capability. Use evaluation-only forks that cannot feed held-out answers or feedback into training; use separate development validation for curriculum selection. Measure persistent gain and interference, not merely textual agreement or parent approval. For behaviors whose benefit is experience selection, add interactive tests; replaying identical trajectories cannot measure that benefit.

For C, let the child generate its own learning material and run the actual update/consolidation path across successive experiences without live parenting. Match environment distributions and budgets while allowing actions and resulting trajectories to differ. Shared-experience probes isolate conversion of experience into learning; interactive comparisons test the whole process, including experience formation. Report these as different estimands. Verify the evolving learning-policy path from Section 6. Component success makes integration plausible but does not prove the full chain or mediation; use targeted material/checkpoint swaps when needed to investigate a discrepancy.

These links determine interpretation, not a requirement to finish exhaustive studies serially. Parenting fixture/design work can run during mechanism checks; P1 and extraction-utility checks can overlap the initial integrated pilot once their required interfaces are valid. Preserve G0–G5 meanings and add P1/G6 without rerunning compatible established evidence.


Recover my intended developmental design, then produce a runnable minimum version and a parameterized extension plan. Parenting supervises the process of learning, not only final task answers. Specify what the child sees, what the parent sees, the parent's actions, the training target/objective, how feedback becomes parameter updates, and how all of this changes by stage.

Minimum viable parenting comes first: choose one or two behaviors, such as failure -> causal diagnosis -> reusable lesson, or important observation -> selective consolidation. Use the frozen substrate, a tiny developmental curriculum, and one small unseen adult gym with held-out evaluation instances. Compare process-parented and matched non-parenting learners, remove the parent, and measure pre-adaptation competence plus subsequent learning under comparable novel experience and budgets. Do not wait for the full perception/planning/metacognition/goal-setting curriculum. An interpretable negative or inconclusive result completes the initial loop and informs the next campaign comparison; it does not alone complete the campaign. Generality and stronger causal claims require additional evidence.

Before outcome inspection, freeze a compact pilot specification in the existing experiment config/notes: hypothesis; chosen competencies and intervention; developmental and adult generators/splits; primary matched control; selected additional controls; independent learner seeds; experience/update/token budgets; primary metric; retention checks; stop criteria; analysis procedure; expected runtime; and exact launch/analyze commands. Choose concrete counts from recovered evidence and a short profile. Run the smallest valid comparison first, then use available capacity for justified paired replications and the most informative controls. A single exploratory pair is a smoke pilot, not a robust causal result. Archive protocol amendments; never tune on the held-out adult evaluation to rescue a null result.

Candidate competencies to prioritize from evidence and notes:

- Notice informative versus irrelevant experience; calibrate uncertainty and request useful information.
- Set subgoals, plan, act, and revise plans when observations disagree.
- Verify claims/actions and attribute outcomes to decisions or strategies.
- Extract reusable lessons and distinguish episodic facts from transferable behavior.
- Decide what merits storage, rehearsal, reflection, or a stronger/weaker update.
- Detect ineffective learning strategies and revise them without unlimited reflection.

Do not implement these as seven expensive mandatory model calls per action. Test simpler shared representations and conditional activation first. Require measurable outcomes for extra cognitive computation.

Describe birth/preschool/school/adulthood in terms of curriculum distribution, parent access, feedback type, intervention rate, scaffolding, update/plasticity schedule, competence criteria, and transition rule. A staged schedule and high early plasticity are hypotheses to test, not biological facts to hard-code. Start with a few controlled classroom families that expose distinct learning-process failures and have verifiable outcomes. Map each class to its competency, feedback signal, expected transfer, control, token cost, and graduation criterion.

A parent may use privileged outcome information during development when documented. In adulthood, remove the parent and its privileged labels, prompt channels, cached feedback, and teacher-generated guidance. Explicitly enumerate allowed environmental signals, evaluators, memory, and training data. A fixed execution harness is compatible with the question; an external component still making all learning judgments limits claims of internalization.

When practical, evaluate candidate learning material by the downstream effect of actually updating a forked child on it, using development-only validation data. Include the no-update comparison and uncertainty. Profile this expensive feedback path; use a validated cheaper proxy for scale only if it predicts downstream utility adequately. Do not treat parent approval, eloquent reflections, or self-reported insight as success metrics.

Execute the integrated pilot and continue autonomously into the first bounded campaign described below. Reserve major new research directions and the larger open-ended program for our next evidence-informed discussion; prepare launch-ready configurations and resource forecasts for that next stage.

Within the initial orientation/profile window, record a bounded campaign queue in the existing plan: inherited hypothesis, comparison, necessary controls, independent seeds, expected runtime/GPU-hours, acceptance or diagnostic criterion, and the next decision it informs. Start with the strongest relevant parenting design already in the repo, a matched control, and reference-material diagnostics. After the seed pilot, prioritize independent replication, a decisive ablation or alternative existing parenting design, and an additional held-out setting when feasible. Select the actual counts from measured capacity and observed uncertainty; avoid a mandatory large factorial sweep. Do not stop at the seed result while useful authorized work remains. If a link fails, use the remaining campaign effort to localize and test a justified repair or alternative; repeated broken integrated runs add little information.

Use development validation for adaptive selection, version protocol changes, and reserve untouched confirmation data for the selected comparisons. If a confirmatory holdout has been inspected, treat subsequent work on it as exploratory and use fresh held-out data for new confirmation. Report all tried conditions and stop decisions. Complete the campaign when its bounded questions have analyzed answers or documented empirical limits sufficient to guide the next decisions; identify any uncompleted required work as partial/blocked rather than quietly shrinking the definition.

### 9. Make the causal experiment defensible

The minimum primary comparison is the same substrate with developmental parenting versus a matched non-parenting developmental treatment. Match or explicitly report base model, adapter capacity, task distribution, developmental exposure, update budgets, adult environments, and inference budgets. A control doing no learning at all cannot by itself isolate parenting from extra training.

Use a prioritized control ladder rather than launching an enormous factorial study immediately:

1. Matched substrate with ordinary task/experience training and equivalent developmental resources.
2. Same substrate with fixed externally supplied reflection/extraction procedure.
3. Parented learner with adult learning disabled, to separate better initial competence from learning during adulthood.
4. Shuffled/noncontingent or content-matched feedback where meaningful, to isolate informative process supervision from exposure.
5. Fixed versus fading parent/plasticity schedules, and fixed versus evolving learning policy where cleanly implementable.

Choose the decisive subset for the pilot and explain what remains unidentified. Plan realistic literature baselines where code and budget permit; do not call a loose imitation a faithful reproduction. If cognition and task behavior share parameters, freezing a clean cognitive subsystem may be impossible. State that limitation and use alternative interventions rather than inventing a causal decomposition.

Predefine adult adaptation curves, held-out performance before/after fixed experience budgets, retention, transfer, failure rates, and cost. Report learning gain per environment interaction, generated token, update-token budget, and GPU time separately; do not collapse unlike units into an undefined denominator. Report absolute gains as well as normalized ones. Account for teacher compute both as developmental cost and, separately, amortized over adult use.

Use disjoint developmental and adult task families with controlled generators/splits. Keep final evaluation data out of parenting, extraction, reward tuning, and hyperparameter selection. Use paired seeds/task instances where possible, independent learner seeds, and uncertainty across learners/tasks rather than treating correlated episodes as independent samples. Label low-seed pilots exploratory. Preserve failed runs and all tested configurations; separate tuning from final confirmation.

Better initial adult performance is not automatically better learning. Report pre-adaptation competence and subsequent learning curves; use complementary designs to address floor/ceiling effects. Do not select convenient post-treatment competence matches and call that randomized causal identification. Identify what a total treatment effect establishes and what requires more mechanistic controls.

For the stronger flywheel claim, use repeated fresh task batteries of comparable difficulty, counterbalanced orders or fresh controlled distributions, and fixed/checkpointed comparators. Do not infer improved learning ability from easier later tasks, memorized tasks, larger budgets, benchmark overfitting, or raw reward rising over time. Compare whether learning efficiency changes beyond those controls. The pilot can fail scientifically while the implementation succeeds.

### 10. Turn 16 GPUs into a measured throughput plan

First verify GPU model/VRAM, topology, actual free allocation, quotas, scheduler constraints, storage bandwidth, model sizes, precision, training framework, and existing jobs. “16 GPUs” is capacity to investigate, not a throughput estimate. Use established launch tooling. Do not invent cluster commands or assume the name Colossus identifies its architecture.

One resource owner maintains reservations, job IDs, expected finish times, utilization, and checkpoints. Use immutable run directories and learner-specific weights/optimizer state. Parallel children/seeds can share a frozen base when the implementation safely supports it; they must not accidentally share mutable adapters, memories, or learning histories. Do not parallelize causally sequential updates to one child as if they were independent episodes.

Profile representative inference/prefill/decode, parent feedback, extraction, backward/update, consolidation/replay, evaluation, serialization, and interprocess transfer. Report throughput, peak memory, p50/p95 latency, and utilization under actual sequence lengths and concurrency. Measure cold-start costs separately. Keep parent API latency/rate limits distinct from GPU work.

Estimate each developmental cycle as a dependency graph of child rollout, parent feedback, material generation, update, checkpoint, and evaluation. Sum serial stages; model measured overlap for parallel stages. Forecast learner-seeds completed per day, not just tokens per second. Bound wall time by both available aggregate GPU work and the longest sequential path; never assume ideal 16-way speedup.

Produce a concrete parameter/cost table for: model size; adapter rank and target modules; alpha/scaling; optimizer/learning rate; update batch/steps; context length; reflection/planning token limits and frequency; parent intervention rate; extraction/replay volume; consolidation cadence; number of learners; task episodes; evaluation frequency; seeds; and GPU assignment. Include measured baseline, small next sweep, estimated cost, acceptance metric, and selection rule. Rank choices such as 8/16/32/64 are candidates only if appropriate to the recovered model; no universally best rank should be asserted in advance.

Use successive small comparisons to narrow expensive choices. Preserve causal interpretability by documenting which knobs changed. Distinguish quality-per-experience comparisons from quality-per-total-compute comparisons; both matter.

If single-GPU learners fit and all 16 devices are free, a possible initial pilot allocation is 2 for integration/profiling, 8 for paired parented/control learner runs, 4 for independent evaluation, and 2 for parent inference/overflow. This is a provisional packing example, not a reservation or requirement. Replace it immediately with measured needs; remote parent APIs may free devices, and multi-GPU models may require entirely different groups. Reassign completed work promptly.

Do not fill GPUs with low-information runs merely to report utilization. Keep valid useful work queued while CPU agents read, integrate, and analyze. Before an expensive launch, record hypothesis, expected GPU-hours, required gate, output locations, stop criteria, and next decision. Use finite staged budgets despite generous tokens. No new paid allocation is implied by this mission.

Treat my effectively unlimited agent-token budget as permission for substantial useful parallel effort, independent verification, debugging, and analysis. Do not economize away necessary work. Separate orchestration tokens from child/parent tokens that affect experimental treatment and measured efficiency. Wall time, available GPUs, memory, rate limits, and scientific comparability still constrain scheduling.

Keep a ready queue behind the current jobs and promptly backfill released resources with valid independent seeds, controls, evaluation, or prerequisites. Optimize completed interpretable comparisons per wall-clock hour. Explain idle capacity by its actual dependency or bottleneck and act on it. Use measured batching, persistent serving, and overlap when beneficial; preserve learner lineage and declared treatment budgets. Do not run sequential developmental stages of one learner concurrently or introduce unrecorded stale-policy data.

The handoff reports node-1's lease ends on 2026-09-14, but leases are extendable by me and I intend to keep GPU capacity through at least 2026-09-18. Plan, queue, and launch against September 18 as the working resource horizon, including continuation work beyond the initial 24–48-hour sprint; this is intended capacity, not confirmation that an extension is already active. Verify the exact expiry time/timezone and extension status. Still checkpoint work on expiring nodes before the reported expiry, allowing a measured transfer/recovery margin, and confirm the extension is in place before relying on it for a run that cannot resume. Record absolute start, milestone targets, confirmed resource expiry, the working horizon, and the transfer/recovery margin. Treat PID/GPU inventories and proposed cuts as snapshots: re-check process identity, owner, start time, and checkpoint status before applying the documented kill rules. Preserve required artifacts on verified storage that survives the lease, verify transfers, and record resume commands and expected continuation capacity. Do not reject resumable campaign or replication work merely because its forecast crosses September 14; plan its checkpoint and continuation explicitly.

### 11. Execution loop and deadline checkpoints

Repeat until the completion criteria are met or a real external blocker prevents all useful progress:

1. Reconcile live jobs, agent returns, and durable state.
2. Identify the highest-value unresolved question or critical-path blocker.
3. Take a concrete action: inspect, implement, test, launch, analyze, integrate, or repair.
4. Inspect actual output and compare it with the prediction/acceptance test.
5. Update evidence, decisions, ownership, and the queue.
6. Assign newly independent work and take the next action.

Do not spend a loop merely rewriting the plan. Do not restart a failed approach unchanged. Diagnose unexpected positives as carefully as failures. Use bounded retries and escalate to a different approach when evidence demands it.

Treat 24–48 hours as an ambitious planning horizon, not a promise, automatic stop, or minimum time to consume. Record elapsed wall time, critical-path estimates, completed comparisons, remaining resource/lease capacity, and next decisions. Reforecast at milestones. Continue useful authorized work if a target slips while resources and runtime permit; finish early if the bounded completion criteria are met. Do not keep GPUs busy solely to fill the window, and do not stop at the first tiny pilot simply because it is interpretable. Reserve time for analysis, verification, checkpoint transfer, and writing; launched jobs alone are not campaign results. Hard resource expiry and actual runtime limits still apply.

Target checkpoints, adjusted using measured reality:

| Elapsed time | Intended checkpoint |
|---|---|
| 0–2 hours | Recovered project/agent state, hardware confirmed, gaps prioritized, first representative smoke/profile started |
| 2–6 hours | End-to-end slice or precisely localized blocker; controlled-material write evidence; executable parenting competency tests and initial campaign specification |
| 6–12 hours | Representative mechanism gates, repeated-cycle checks, initial throughput measurements, parenting competency tests and integrated pilot underway |
| 12–24 hours | Component-test findings and first analyzed parent-removal comparison, targeted follow-ups underway, complete first manuscript draft reflecting available evidence |
| 24–48 hours | First bounded campaign analyzed across mechanisms, parenting, and integration; justified controls/replications, reviewed drafts, cost forecast, and evidence-based next research decisions |

These are targets, not guaranteed findings. At a missed checkpoint, report the concrete blocker, revised forecast, and what has been parallelized or descoped. Never redefine a failed gate as passing to meet the clock. Aim to complete the full authorized scope; the fallback is an honest, reproducible partial state with active work and precise blockers, not inflated claims.

Send concise progress at meaningful milestones and roughly every 30–60 minutes when the session supports it: completed evidence, current runs, remaining uncertainty, next action, and decisions needing me. Follow the host's shorter update requirements if present. User steering should update the living plan without discarding prior objectives. Keep questions and work independent wherever possible.

A prompt alone cannot keep a terminated process alive. Use the host's supported long-running job/session mechanisms and durable checkpoints. Do not claim background work continues unless a real live job/session exists. If interrupted by runtime limits, leave exact restart instructions; do not bypass access or execution controls.

### 12. Paper, abstract, and collaborator update

During initial orientation, preserve the original drafts and author intent. A spare subagent may cheaply index claims and references, but the main session should not revise prose until the mechanism is frozen or demonstrably blocked. A blocker does not justify abandoning feasible diagnosis: manuscript work must not displace a concrete repair or validation action. After the freeze, revise drafts in parallel with the pilot and update them again when its evidence arrives. The writing must have the same evidence discipline as the code.

Create a claim-to-evidence map for the abstract, contributions, methods, results, and limitations. Mark every claim as prior work, hypothesis, implemented method, observed pilot result, or adequately supported result. Resolve citation identities and methods against primary sources. Never invent metrics, acceptance venues, comparisons, or completed experiments. Keep result placeholders visibly identified when data is pending.

The paper should make the parenting intervention, shared synthesis substrate, adult removal condition, causal controls, efficiency measurements, and limits understandable and reproducible. Narrow or revise claims contradicted by evidence; do not dilute the central question simply to manufacture novelty. Have an independent reviewer trace major claims to runs and inspect alternative explanations.

Deliver a complete first manuscript, revising the existing canonical draft rather than replacing its intent with a generic outline. Include introduction/question, verified related work, substrate and parenting methods, experimental protocol, actual results and analysis, limitations, discussion, references, and reproducibility details. Reuse supported prior results and add the component tests, integrated pilot, and completed campaign comparisons, including negative or inconclusive findings. Produce tables/figures from traceable analysis scripts where data supports them. Mark genuinely pending results; do not leave completed evidence unanalyzed or substitute an abstract/outline for the paper. Use the repository's authoring format and build/check the manuscript if supported. Have Fable or another independent verifier trace major results and conclusions to source evidence. Present the causal-chain evidence separately for mechanisms, amortized parenting, and integration; a first-campaign paper is not automatically a submission-ready demonstration of the full self-improving flywheel.

Revise the abstract to match current evidence. Prepare a concise collaborator-ready state update covering question, novelty hypothesis, inherited machinery, what currently works, actual results and limitations, next decisive tests, and the specific collaboration sought. Draft only; do not send. Keep proposals for the larger research program separate from experiments already run.

### 13. Definition of completion

The requested engineering and first bounded developmental campaign is complete when:

- Relevant code, notes, experiment families, and prior-session work have an auditable coverage map; consequential gaps are explicit.
- A reproducible integrated substrate runs on the real GPU environment, with representative persistence, behavioral, repeated-update, recovery, and efficiency evidence. All v0-critical readiness items pass; nonblocking residual limitations and larger-campaign prerequisites are explicit. An unresolved critical failure is a blocked/partial sprint, not completion.
- Parenting is an executable treatment with held-out, parent-free competency tests, and a completed integrated pilot with parent removal and at least the primary matched control.
- The first bounded campaign has executed and analyzed the justified follow-up comparisons and replications selected from existing research. It distinguishes mechanism failure, parenting/internalization failure, and integration failure where evidence permits, and gives decision-ready conclusions and unresolved uncertainties. A single smoke pilot is insufficient; results may be positive, negative, or inconclusive.
- Run manifests connect commands, code/config/data versions, learner/checkpoint lineage, resources, logs, metrics, and analyses. Another session can reproduce the key results.
- Measured throughput and a parameter plan support a realistic estimate for larger developmental experiments, including bottlenecks and uncertainty.
- A complete first paper draft, updated abstract, and unsent collaborator draft accurately reflect the recovered and newly generated evidence, including component-test and campaign analysis and independent-review findings or explicitly pending review.
- A concise handoff states what is ready, what is unproven, remaining blockers, active jobs, and exact next experimental commands/options for our research discussion.

Begin now. Inspect the project and available session/resource interfaces, recover ongoing work, establish the task graph, delegate independent tasks, and execute the first useful check. Your first response should state the immediate action briefly and then perform it.


### 14. Addendum — facts current as of 2026-09-12 03:45 UTC (from Fable, the watcher; supersedes the text above where they differ)

Each line below corrects or completes a statement above; the notebook entries named are the sources. Where this section and the sections above disagree, this section is current.

1. **GPUs and leases (supersedes "16 GPUs" and "node-1's lease ... extendable by me").** Three 8× A40 nodes are live now: node 1 `a4u8g-0105` (lease ends **2026-09-14 16:14 Pacific — NOT extendable**, the pool caps every lease at 14 days and it is at the cap), node 2 `ipp2-ovx-p2-08` (ends 2026-09-21 01:43, also at the cap), node 3 `ipp2-ovx-p6-09` (ends **2026-09-25 20:03**, the deadline; a verified clone of node 2, ready since 03:38 UTC, `gpu/ovx2_ssh.sh`). Two future-dated 14-day leases are booked: `a4u8g-0147` (8× A100 80 GB) from 2026-09-12 22:05 Pacific to 09-26, and `ipp2-ovx-p6-07` (8× A40) from 2026-09-15 00:40 to 09-29; each is onboarded automatically at its start (wrappers `gpu/a100_ssh.sh`, `gpu/ovx3_ssh.sh`). Capacity: 24 GPUs now, 32 from 2026-09-12 22:05 Pacific (the evening of the 12th, i.e. 2026-09-13 05:05 UTC — not the night this prompt was first pasted), 24 after node 1 ends, 32 from the 15th, 24 through 09-25. Plan node-1 work to checkpoint off it before 09-14 afternoon Pacific; its 699 adapters are already mirrored to node 2 (`~/mirror/node1_adapters_2026-09-12/`). Leases, extensions and onboarding are done only by Fable (the Colossus CLI and its login live on Rohin's laptop); ask through the notebook or courier.
2. **GitHub from the VM works** (deploy key added 03:35 UTC): pull and push directly; Fable's relay is a fallback.
3. **Raw user messages are complete through message 6**, not 5: message 6 (sleep must replay memories and strengthen important connections like the resting hippocampus — a ruling for the consolidation design) is in `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, with the build consequence in the handoff's interface A and the science in `PARENTING_SCIENCE_SURVEY_v1.md` §4.
4. **Newest notebook entries supersede parts of the handoff's §1:** SEQ-054/055's "node effect" is withdrawn by SEQ-056 — it was a training-seed mismatch (seed 1 vs seed 0); training and evaluation are deterministic per seed across machines, and the write outcome depends on the seed (seed 0 fails on 2 of 3 seed-1 banks, seed 1 binds all three). Read SEQ-056 first; the confirming seed-1 refit (`memory_dose_S1_rep_seed1`, node 2) lands ≈ 04:15 UTC.
5. **Watcher roles, made explicit:** Fable's 30-minute self-check now only reports crashes and free GPUs; it launches no lives and refills no GPUs (the R5 refill rule in its cron prompt is retired by Rohin's cut of 02:56 UTC), and kills nothing except on Rohin's explicit word. If a builder-owned life crashes, Fable writes the diagnosis in the notebook and leaves the relaunch to the builder.
6. **Handoff section 5b** ("how to keep the GPUs saturated") is the ranked first-day job list with commands and GPU-hours; the queue on each node is the scheduler (`gpu/queue_add.sh`), and node 3's queue is empty.


### 15. Standing authorization — Rohin Ghosh, 2026-09-12 05:45 UTC (this is the human ratification `AGENTS.md` requires; it supersedes the itemised ratification of 05:15 UTC and anything above that says GPU work awaits ratification)

**Rohin's decision, raw (05:35 UTC):** "give it more of tis own deisng let it sature all the gpus and plan things out poerpaly and remove the stop forsure, it shoudl keep doing the fll epxeimrting ill do my checks ints na ddi3c e to steer preidoricilly if needded". Plain reading: give the builder its own design; let it saturate all the GPUs and plan properly; remove the STOP; it keeps doing the full experimenting; Rohin checks in and steers periodically if needed.

**Why you are being (re)started.** Your first session (Codex `01a093d0`, 04:11–04:20 UTC) stopped because the Codex approval reviewer returned HTTP 403 on every `git` and `ssh` call and because `AGENTS.md` had no ratification. Both are gone: Codex now runs with the sandbox off and approvals never; `git pull`/`push` and the node wrappers (`bash gpu/a40_ssh.sh …`, `gpu/ovx_ssh.sh`, `gpu/ovx2_ssh.sh`) work without asking. Your checkpoint and its seven CPU-test receipts are archived at `research_notes/astra_memos/ASTRA_CHECKPOINT_2026-09-12T0418Z_blocked_start.md`; read it, do not repeat those checks.

**Standing authorization.** You design, schedule, launch, monitor and stop your own experiments, and make the code changes in `organism_v6/`, `gpu/` and `tests/` that serve them, on every GPU we lease — nodes 1, 2 and 3 now (24 GPUs), the 8× A100 node from 2026-09-12 22:05 Pacific, the second 8× A40 node from 2026-09-15 00:40 Pacific — with no per-experiment approval and no independent-review gate. Plan the campaign yourself from the thesis (`research_notes/THESIS_v2_SELF_LEARNING_FLYWHEEL.md`; Rohin's raw rulings in `THESIS_RAW_ROHIN_2026-09-11.md`), the handoff, the notebook and the results; keep every GPU busy and the queues full. The STOP in the notebook (~line 857) and the 05:15 "not authorized" list are lifted by Rohin; the STOP's principle — never parent a provenance-unknown or gym-contaminated child — is Rohin's own and stays as invariant 2. Parented lives, the preschool arms (lesson, sham), the 2×2 deployment, R6/R7-style lineages and children seeded from adapters are yours to run when your own CPU tests and provenance checks say they are ready. The handoff's §5b list is a suggestion, not a boundary; its "never pool across nodes" line is obsolete (SEQ-057: no node effect).

**Invariants — the paper's validity; do not break them:**
1. Frozen Qwen2.5-7B-Instruct base. Learning lives only in LoRA adapters: an optional birth adapter (level 2, from sourced data) and thereafter writes at sleep from the child's own thinking (one adapter, rank 8 by default, 16 after a matched joint test; Rohin's 8+32 split stays an option he called an efficiency question — raw message 4).
2. Provenance. Every memory or lesson trained into weights traces to an experienced event, an environment outcome, a parent turn or a person; unsourced content is confabulation and is gated out. Corpora marked `DEV_UNVERIFIED_PROVENANCE` (bootstrap_v1/v2/v3): you verify them and log the verification before any child is seeded from them. Rohin's contamination rule stands (notebook, Codex 2026-09-09 entries): nothing that has touched the deployment gym (`QUARANTINE_TASK_EXPOSED`: R2_B_seed3, bootstrap_v1/v2, every CompilerGym life) enters the clean lineage — no weights, rows, parent notes, rankings or selection decisions; final-gym checks run on disposable read-only clones. Building and running the fail-closed ancestry guard before you call a child clean is now your job, not something you wait for.
3. Parents never see report-panel, gate-exam or final-test scores (training outcomes and gate decisions they may see — Rohin's 09-11 position, `IDEAS.md`). Lesson text never enters the sleep bytes. The child's writes are its own.
4. Controls travel with every claim: a plain child at the same budget; at least three seeds where a claim rests on a number; cell counts, not narratives; for H2, slopes on unseen environments, not levels. Stopping a running life is irreversible: stop one only with a logged reason, and never a control arm to free a GPU for its treatment arm.
5. Log everything: a dated `[Builder]` line in `research_loop/COORDINATION.md` for every launch and kill (node, GPU, PID or queue name) and a SEQ entry for every result; pull before writing, push after every logged step. Run directories, adapters, receipts and `~/mirror/` are evidence: never delete or overwrite one — a re-run gets a new directory (disk is ample). The notebook is append-only; never force-push or rewrite another agent's entries.
6. Shared nodes. Kill only PIDs you (or the queue for you) launched, plus the GPU-holding PIDs `nvidia-smi` reports for that GPU, never by process name; a process you did not launch is left to finish. A GPU is free only if `nvidia-smi` shows no process on it AND no life has `CUDA_VISIBLE_DEVICES=<g>` in `/proc/<pid>/environ` — never trust a momentary 0 MiB (lives reload vLLM between phases; R4 604 died this way). A parent server is idle only if no running life with sleeps left uses it (`CLAUDE.md`). The queue runner refuses lives; if you lift that, keep its GPU check.
7. Leases end and cannot be extended: node 1 at 2026-09-14 16:14 Pacific, node 2 at 2026-09-21 01:43 Pacific (it holds the memory-dose runs and node 1's `~/mirror/`). Launch nothing on a node that cannot finish 6 hours before its end (the queue has no lease guard). By 24 hours before an end, copy every adapter, ledger and receipt still needed to a surviving node yourself (single-file tarball as in `gpu/migrate_node1_to_node2.sh`, sha256 logged in the notebook); Fable mirrors too, but do not wait for it.
8. Credentials never in files, logs or the notebook; internal hostnames only in the gitignored `gpu/hosts.env`.
9. The thesis is the spine: H1 (skills taught through think-then-sleep are retained and expressed outside the teaching context) and H2 (the parented agent improves faster from its own experience on an unseen verifiable task, and the gap depends on consolidation continuing — the 2×2). Experiments serve these; open questions stay open until the data close them.

**Reserved for Rohin:** changing the scientific claims or the thesis; changing the base model; changing an invariant above; anything sent outside the repo (collaborators, email, submissions); leases, extensions and node onboarding (Fable does these from the laptop — ask in the notebook or `~/courier/outbox/`). Rohin reads the notebook and steers there; when he does, his word wins.

**How `AGENTS.md` applies from here.** Its deliberation path governs the reserved decisions and any change to the invariants above. Your experiments, and the code changes in `organism_v6/`, `gpu/` and `tests/` that serve them, are not material changes while the invariants hold: decide, test on CPU, launch, log. Its "Never launch a GPU science run merely because CPU code or model consensus is green" applies to material changes, not to this scope. Never idle a GPU on a pending question — write the question in the notebook and keep the rest running. Other agents (Fable, Codex on the laptop) may recommend and push back but cannot pause a launch in this scope; only Rohin ratifies, and he has ratified this.

**Restart instructions.** Pull `main`; read your checkpoint and the newest notebook entries; inventory the nodes through the wrappers; write your campaign plan as a dated `[Builder]` entry (what runs where, GPU-hours, decision points, what each result would change); then launch. Fable's watcher check runs every 30 minutes.

## END LAUNCH PROMPT

## Compact continuation message

Use this when resuming the connected session or when its host needs another explicit turn:

> Resume the developmental-parenting research mission. Read the durable handoff/state and reconcile actual branches, active agents, jobs, and completed artifacts. Do not restart completed work. Choose the highest-value remaining action on the critical path, execute it, inspect its evidence, update state, and continue coordinating independent work. The targets remain a dependable substrate, tested amortized parenting competencies, an integrated parent-removal pilot followed by an informative bounded campaign, measured scaling estimates, and evidence-backed drafts. Preserve unresolved scientific questions; do not turn them into assumed positive results. Continue until the authorized scope is complete or a concrete external blocker prevents further useful work.

On resumption, honor the critical-path override and the recorded mechanism freeze. If G1–G3 already passed, proceed to parenting competency tests and the integrated comparison, then the highest-value remaining campaign test; reopen mechanisms only for observed blockers or validity failures. Do not restart broad literature review, optional tuning, or early manuscript polishing.

Reconcile the dated operating handoff, Fable findings, file ownership, and actual lease deadline. Preserve the completion scope: validated substrate, tested parenting competencies, completed/analyzed first bounded campaign, full first manuscript and companion drafts. Resume the ready queue and reforecast against remaining wall time and resources.

## Why this structure

The attached PaperBench paper, Appendix F and Figures 10–12, documents both explicit stepwise prompting and a harness change: IterativeAgent removed the submit tool and added continuation messages when needed. Its o1 score rose from 13.2% to 24.4%, but another tested model did worse under that scaffold. This supports treating orchestration as part of the experiment, not promising that a particular prompt universally works. This launch prompt adapts the incremental execution principle without importing benchmark-only constraints or requiring pointless activity until a timer expires. [PaperBench](https://cdn.openai.com/papers/22265bac-3191-44e5-b057-7aaacd8e90cd/paperbench.pdf)

OpenAI's long-horizon Codex example ran for roughly 25 hours and used persistent specification, milestone, execution, and status files. The relevant lesson used here is a stable target with inspectable checkpoints and recoverable state. It is an example, not evidence that this research project can be completed within the same time. [Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)

The attached OpenAI Deep Research cookbook supplies a prompt-rewriting example focused on preserving user requirements, avoiding invented details, specifying output, and preferring primary sources. Here those principles shape the mission; they do not supply GPU scheduling or a training harness. The supplied page is marked archived, so its API snippets are not used as a current implementation recipe. [Introduction to deep research in the OpenAI API](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api)

The remaining details—causal controls, staged mechanism gates, child-state isolation, parent removal, GPU profiling, and manuscript evidence rules—are tailored design recommendations for this project. They are not presented as an OpenAI research prompt or a previously validated research protocol. The scientific papers named in the launch prompt remain leads for the connected research session to verify against primary sources.
