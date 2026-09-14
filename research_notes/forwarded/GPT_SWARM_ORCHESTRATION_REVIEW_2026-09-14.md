# Forwarded by Rohin, 2026-09-14 ~20:50 UTC (message 73): a GPT conversation on how the Navier–Stokes swarm was run, how to structure the fresh orchestrator, and a review of FRESH_ORCHESTRATOR_LAUNCH_2026-09-14.md

Saved verbatim as forwarded (three assistant turns and Rohin's own interjection). Rohin's covering words are in
THESIS_RAW_ROHIN_2026-09-11.md, message 73. Claims about the OpenAI run are the forwarded assistant's; our own
primary-sourced survey is research_notes/related_work/AUTONOMOUS_RESEARCH_SWARMS_2026-09-14.md.

## Key points Fable extracted (for the launch pack)

- The Navier–Stokes run was "an adaptive research organization wrapped around a very strong RL-trained model":
  diversify → explore independently → communicate locally → synthesize globally → reallocate compute → inject
  discoveries → diversify again. Lean was the FINAL verifier (~17 h after the ~88 h run), not the per-step discovery
  oracle; discovery used code execution and a cached internet with local deterministic checks.
- Agents were partitioned into communicating groups seeded with deliberately different formulations (A/B proof of
  regularity vs C/D counterexample); an easier adjacent problem (unforced Euler, ~100 agents, ~50 h) succeeded and
  changed the allocation policy; Codex consolidated insights across groups and generated follow-up prompts.
- The high-leverage decisions (which formulation gets more agents, when to consolidate, what to inject) had
  meaningful researcher involvement; the model supplied research capability inside that structure.
- Prompts were probably a sequence: root objective (maintain competing hypotheses; decompose; delegate; seek
  counterexamples; record failure reasons; prioritise by likelihood / information gain / falsification / independence),
  narrow worker prompts (one subproblem; return strongest result, evidence, assumptions, attempted falsification,
  obstacle, compute recommendation, one message useful to others), and a synthesizer prompt (ESTABLISHED / PROMISING /
  CONTRADICTIONS / DEAD ENDS / OPEN BOTTLENECKS / NOVEL CONNECTIONS, then allocate ~50 % exploit / 25 % adversarial /
  15 % alternatives / 10 % high-risk with minimal overlap).
- Anti-convergence is deliberate: seed groups with different stances (assume true / assume false / first principles /
  prior-work delta / boundary conditions / cheapest decisive experiment / adversary / orthogonal formulation).
- Communication is hierarchical, not all-to-all: workers → group state → synthesizer → global state → new allocation;
  information crosses groups only through compression events.
- Make research state an explicit object (objective, known results, candidate mechanisms, evidence, contradictions,
  unresolved questions, experiments, dead ends, surprises, priority frontier); the core operation is State_t → next
  research bets, not transcript → next action.
- For our fresh run: two timescales — a longitudinal PI agent (continuity, state, cross-stage synthesis, replanning)
  and stage/hypothesis threads; be exact about invariants and interfaces (goal, evidence, authority, state,
  delegation, verification, escalation, stopping, integration) and deliberately under-specified about reasoning;
  "rigid epistemology + flexible strategy".
- Five explicit clauses: the plan is a hypothesis to improve, not a task list; control over decomposition; protect
  independence (keep one branch blind to the favoured interpretation); separate observation from interpretation
  (observation / supported interpretation / unresolved alternatives / confidence / next discriminating test);
  uncertainty drives allocation.
- Review of the draft pack: add an adaptive-orchestration clause after "Your job is orchestration, not execution";
  change "retire after one clean null" to "deallocate after one clean null unless it creates a new discriminating
  hypothesis — a null stops compute, it does not disprove"; approve 18 GPUs as budget but not as a continuous
  invariant; treat 5,000 rows / 4 fit pairs / 5,000 updates as capacity targets, with the real metric the
  distribution (rows × rubric pass × outcome pass × diversity × richness × world coverage); keep code + math, not
  kernels (confounds); the new thread gets GPUs and finalized knowledge, not the old active arms; add BOARD fields
  BELIEF CHANGE / ALTERNATIVE EXPLANATION / VALUE OF NEXT TEST. "Your draft is already maybe 80–85 % of the way there."
