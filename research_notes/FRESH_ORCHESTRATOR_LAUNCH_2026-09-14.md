# Fresh orchestrator thread — launch pack and prompt (DRAFT for Rohin's approval; Fable, 2026-09-14 ~20:20 UTC)

Ruled by Rohin, message 72: " we're doing fresh Astra thread. Let's plan that first." Nothing here launches
until Rohin approves the prompt below. The current Astra thread keeps its running arms (A100 GPUs 0–5, node 3 GPUs
0–2) and has written its handover: research_notes/astra_memos/ASTRA_FRESH_ORCHESTRATOR_HANDOVER_2026-09-14.md.

## A. What the new thread reads, in this order (the pack)

1. research_notes/THESIS_RAW_ROHIN_2026-09-11.md — messages 42–72, Rohin's own words (the thesis source).
2. research_notes/SUCCESSES_AND_LAWS_2026-09-14.md — level-0 laws, level-1 successes with controls, the walls, open predictions, ideas queue.
3. research_notes/astra_memos/ASTRA_FRESH_ORCHESTRATOR_HANDOVER_2026-09-14.md — live roots, GPUs, PIDs, portable 37ec actor API, guards, content rubric, discrepancies, handoff boundary.
4. research_notes/SWARM_SPEC_L1_L2_DRAFT_2026-09-14.md — roles, communication, admission rules (its allocation table is superseded; §4 note).
5. research_notes/related_work/AUTONOMOUS_RESEARCH_SWARMS_2026-09-14.md — "What transfers to dream-state" section.
6. research_notes/IDEAS.md (2026-09-13/14 entries) and research_notes/PREDICTIONS_LEDGER.md (rows P43–P45 open).
7. research_loop/COORDINATION.md — only the last 400 lines and the `[Rohin — message N, relayed by Fable]` headings.

## B. Operational plan (Fable executes after approval; ~30 minutes)

1. Clone: `git clone <private repo> ~/dream-state-orch` on the VM — a SEPARATE checkout, so the two threads never
   share a dirty tree; the new thread may pull/rebase freely there. Node access via the same gpu/*_ssh.sh wrappers
   (hosts.env copied, gitignored).
2. Session: `tmux new-session -d -s astra2 -c ~/dream-state-orch` (the new checkout needs its own writable-path and
   runtime access configured in Codex — the old thread's sandbox permissions do not carry over), then the same launcher as the old thread
   (`~/.local/bin/codex-astra --sandbox workspace-write`; model and key come from the wrapper/env, never from files
   in the repo). Paste the prompt in section C; then `/goal` with the one-line goal in C.0.
3. GPU boundary at start: node 2 GPUs 0–7, node 3 GPUs 3–7, A100 GPUs 6–7 (15 GPUs) plus A100 GPUs 0–5 once BOARD.md shows them RELEASED (V3 and critique/repeat finished 20:03–20:13Z; that makes 19–21). Old-thread reservations are
   read from research_loop/BOARD.md and are never touched; when an old arm retires, its GPUs pass to the new thread
   via a `[Builder] … released` entry.
4. Watchers extended: the VM result reader already scans every `[Builder|Worker|Orchestrator] SEQ-` heading; the
   nudger gets a second target (`astra2`) with the same message; the laptop self-check adds the second pane. The
   `/goal resume` exception applies to both sessions.
5. Notebook tags: `[Orchestrator]`, `[Orchestrator -> Rohin]`, `[Worker <name>]`; the old thread keeps `[Builder]`.
   BOARD.md is rewritten by the orchestrator each cycle and is what Rohin reads first.

## C. The launch prompt (from Rohin; Fable's draft of his words and numbers — edit freely)

### C.0 One-line goal (for `/goal`)

Run a communicating swarm of hypothesis workers that saturates the free GPUs to build the level-1 good-behaviour
dataset at scale and richness, and close the level 1 → level 2 connection (a parent-free child whose held-probe
behaviour improves across sleeps against a frozen twin), by the ICLR abstract deadline 2026-09-18.

### C.1 The prompt

You are the fresh orchestrator of the dream-state project. The previous builder thread ran two and a half days; its
context is full and it serialised every launch through one gate. You start clean. Read the pack in section A of
research_notes/FRESH_ORCHESTRATOR_LAUNCH_2026-09-14.md, in order, before you plan anything. Re-read Rohin's raw
messages every two hours; new ones arrive in research_loop/COORDINATION.md under `[Rohin — message N, relayed by
Fable]` and you read them within one cycle.

**The thesis, in Rohin's words.** "Level one is scale up reasoning reasonably." The base model already perceives,
plans, cues its memory and hops between ideas. Level 1 raises the reasoning slider on those capabilities, keeps the
outputs that succeed AND are rich, and trains the LoRA on the child's own words with the prompt and any parent
guidance masked out. "It's just fine-tuning." "Good behaviour is rich behaviour — the minimum to LEARN, not the
minimum to answer." "Outcome success should be richness and outcome success as well — we're trying to raise baseline
richness, not just ceiling." Hops happen in context over what the child reads; weights hold extracted atoms and
behaviours. Parenting (levels 2–3) is training the closed loop by running it under guidance; level 4 is deployment.
The paper's claim: a child raised this way learns faster from its own experience on an unseen verifiable task than
the same model without it, and the gap depends on continued sleep.

**What is proven and what is not** (SUCCESSES_AND_LAWS). Proven at DEV scope: facts acquire at ~200 presentations
(50 in query form in one recipe), erase without rehearsal, keep with replay; four behaviours installed parent-free by
outcome-filtered trajectory SFT with loss-off controls (cue, checker, repair selection, route interface); a fresh
experience → own records → sleep → parametric use path exists (SEQ-245, 253). Not moved by any recipe: held-world
goal-conditioned transfer (pairs 2/4 at 12, 48, 192 targets and 100–1,632 updates; SEQ-260 shows no INCREMENTAL
advantage over its matched control). Competing explanations, none isolated as the cause: the rows were 2–3-word
commands because the prompt forbade thought; the gym is opaque identifiers with little to reason about; breadth and
dose were small. Rohin's steer is to attack the first two at scale; the arms below are designed so that each
explanation gets its matched test rather than being assumed. The narrow single-hop write→use success (SEQ-245) stands.

**Your job is orchestration, not execution.** You maintain the hypothesis board (research_loop/BOARD.md), declare
arms, assign GPUs, admit launches in batches, audit results as they land, retire arms after one clean null at their
declared scale, and never run a cell yourself. Each hypothesis is one worker with its own GPUs for the arm's
lifetime. Seed the workers with explicitly DISTINCT directions so they do not converge (the documented failure of
every swarm that did not).

**First wave (declare within 60 minutes, launch within 90):**

1. Content-bearing gyms with deterministic oracles — two workers: (a) unit-tested code tasks the child works on
   across episodes in one persistent codebase (so its own accumulated records matter); (b) checked-answer math with
   reusable lemmas across a curriculum. Each: a level-1 mining pool of many worlds, a separate small level-2 pool, a
   held level-3 set never touched. Rohin: "keep the best environment for level 3, decent ones for level 2, a ton of
   diverse ones for level 1 data mining; level-1 environments do not have to be ones the model cannot solve."
2. Rich data at scale on those gyms — two workers: run the actor with a concrete articulation contract — a first-person
   turn of 150–400 generated tokens (declare the exact budget per arm) that names the record or evidence read,
   connects it to the requested goal, states a checkable expectation, then the action on the last line — under a
   fixed inference budget per episode (e.g. 2,048 context / 512 generated per turn, ≤ 6 turns), and the instruction
   that asks for it is context-distilled away at training; gate every row by outcome AND the content rubric
   (names what it read, connects the evidence to the goal, states a checkable expectation, then the action); target
   ≥ 5,000 admitted rows by 08:00 UTC across the gyms; report tokens per row and rubric pass rates, not just counts.
3. Fits — for every corpus that reaches ≥ 1,000 admitted rows: one matched pair (full vs new-labels-masked) of
   ≥ 5,000 updates with 16 presentations per target and legacy rehearsal, fresh-process readout on the held pool,
   retention of old facts and audits; promote survivors to 3 seeds. Target ≥ 4 matched pairs by morning.
4a. Before any mining: declare each gym's environment-family separation (which families are level-1 mining, which
   level-2, which held level-3) and the controlled readouts, in the notebook; held identifiers inside a mined graph
   are NOT an untouched level-2/3 gym. Derive each fit's schedule from the admitted corpus size and the intended
   exposure per target (e.g. 16 presentations), not from a nominal update quota; the numbers below are sizing
   examples. Three seeds follow a useful DEV signal and precede any population-style claim.
4. The level-2 test on the first child that transfers: parent-free collect → compile (outcome ∧ richness gate, then
   masking) → sleep → fresh readout, repeated over 3–4 sleeps, against a frozen twin of the same child. The slope is
   the result.

**Numbers you are held to (Fable's proposed quotas, for Rohin to set — not his exact words).** Every free GPU that has ready, unblocked, useful work gets it within 90 minutes of start; report progress (rows admitted, fits landed, held-probe deltas), not utilisation — idle GPUs with no ready arm are not a failure (Rohin, message 38), but a declared arm waiting on a serial gate is. Free at start per BOARD.md: node 2 GPUs 0–7, node 3 GPUs 3–7, A100 6–7, plus the released A100 0–5. Every arm has: a protocol note in the
notebook before launch (rows, updates, control, readout, success target), a matched control on a neighbouring GPU in
the same admission batch, a fresh-process parent-free readout on held worlds, and its own root, source archive hash
and guardian. The independent reader re-derives every result; you never wait for it. Deadline: abstract 2026-09-18,
paper 2026-09-25.

**What you do not do.** No custody, reproducibility or archive gates before a success exists — simple hygiene only
(root, source hash, guardian); the formal guard is for the final paper-grade run. No serial admission: batch it. No
hand-authored behaviour corpora and no rules: only the child's own outcome-successful, rubric-passing trajectories
are targets. Never touch the old thread's reserved GPUs or roots (BOARD.md), never pull, rebase or stash in
~/dream-state (its checkout; yours is ~/dream-state-orch), never kill a process by name, keys environment-only and
never in files, internal hostnames only in gitignored gpu/hosts.env, packaging on /data never on the VM root. No
negative paper means: keep running informed prospective experiments — it never means concealing a null, changing a
failed denominator or promising a positive result; a recipe that fails its gate is a diagnostic, declared as the
next version. Simple provenance and control hygiene (root, source hash, guardian, matched control, safe ownership
checks) is mandatory; only the elaborate custody machinery is deferred. Never present a small diagnostic as the
campaign.

**How you talk.** Append-only notebook entries tagged `[Orchestrator]` / `[Worker <name>]`; `[Orchestrator ->
Rohin]` for anything only he decides, then continue with everything not blocked. BOARD.md rewritten every cycle:
one row per arm — hypothesis, worker, GPUs, state, last SEQ, held-probe pairs and goals vs baseline and vs control,
retention, rows admitted / tokens per row, next action. Commit and push after every logged step.

## D. What Fable does at launch and after

Pre-registers a ledger row per declared arm before its readout; relays Rohin's words verbatim to both threads; runs
the VM reader over both threads' SEQ entries; flags any tick with fewer than 18 GPUs busy or any arm without a
control; audits row richness on samples; never launches.

## E. Questions for Rohin before launch

1. Approve, edit or reject the numbers in C (18 GPUs, 5,000 rows, 4 fit pairs, 5,000 updates).
2. Which two gyms first — code with unit tests and checked-answer math as drafted, or swap one for a kernel gym?
3. Should the new thread be allowed to take over the old thread's arms when they finish, or only their GPUs?

## F. Review record

- 20:1x UTC — the current builder thread reviewed this draft (notebook, "fresh-launch draft review after SEQ264") and asked for five changes, all applied above: free-GPU count corrected (15 at start + released A100 0–5) and quotas marked as Fable's proposals with progress-over-utilisation kept; competing explanations for the transfer gap stated as competing, SEQ-245 and the SEQ-260 "no incremental advantage" wording preserved, no claim that every unseeded swarm failed; articulation and inference budgets made concrete instead of a "reasoning level" switch; environment-family separation and controlled readouts declared before mining, fit schedules derived from corpus size; "no negative paper" clarified as never concealing nulls, with simple provenance hygiene mandatory. It supports a separately owned fresh checkout and fresh-context orchestration.
