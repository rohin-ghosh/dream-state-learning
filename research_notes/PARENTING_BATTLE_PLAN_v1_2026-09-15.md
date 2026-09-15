# Parenting battle plan v1 — the overnight of 2026-09-15 (Rohin → Fable → Astra + Fable-VM)

Status: DRAFT for Rohin's review (message 111: "I want your in-depth battle plan that you, Astra and Fable 5.1 VM
are building … on the 8 I want you to test 4 with a Fable-guided swarm that uses this battle-plan prompt … both
Fable and Astra on max settings, communicating with each other and looking at each other's work … let's get this
prompt right"). Nothing in §6 launches until Rohin says go; everything else is already Astra's standing order.
Source of every rule below: Rohin's messages 82–110 (verbatim in THESIS_RAW_ROHIN_2026-09-11.md) and the parents'
document research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md, which this plan cites but does not replace.

## 0. Mission, in his words

"Throw everything at the base model — get all of the capability into behaviour … a really curious, perceptive,
five-year-old sort of creature." Parenting turns experience into material the LoRA can learn from: curiosity,
perception, metacognition, persistence, reflection, goal and meta-goal setting, self-perception, distilled emotion.
"We're not trying to think just about capability here. These are just games — not to be passed, but to have
something to do, so then you can measure learning." "You're gonna have to constantly pester." "The way you can
really judge learning behaviour is metacognition." Results by morning.

## 1. Who does what

| Actor | Runs as | Owns | Tonight |
|---|---|---|---|
| **Rohin** | asleep ≈8 h | the thesis, the rulings | reads the morning report; approves §6 before it launches |
| **Astra (orchestrator)** | Codex, gpt-6-astra, xhigh, tmux `astra2` on the VM | all lane code, GPU admission, the BOARD, the level-1 loop, the level-2 lanes, the capability suite | 14 GPUs level 1; 18 GPUs parenting on the old fleet (10 frozen-base + 8 learned children); node 5 GPUs 4–7 frozen-base parenting; hourly parenting entry |
| **Fable-VM (parent swarm)** | Claude Code headless, `claude-fable-5-1`, effort MAX, launched from the VM under `~/courier/` | the parent policy on node 5 GPUs 0–3: four branches, one head parent | four frozen-base branches, different games and cadences; head parent reviews all eight node-5 branches (its four and Astra's four) every cycle and rewrites its parents' prompts |
| **Fable-laptop (watcher)** | this session + the half-hour cron | relays, verbatim record, ledger, independent reads, stall flags, leases | relays Rohin; verifies both halves; pre-registers P70–P72; morning report |
| **Fable-VM (backup self-check)** | cron `backup_selfcheck.sh` every 30 min | read-only census + PARENTING WATCH step 3b | writes STALL if base parenting < 10 GPUs or fleet < 24 resident |

Communication is hierarchical and written, never private:

- `research_loop/COORDINATION.md` — append-only notebook; tags `[Builder …]` (Astra), `[Fable-VM swarm]`,
  `[Fable]` (laptop), `[Rohin — message N]`.
- `research_loop/PARENTING_EXCHANGE.md` (new, append-only, both halves) — one entry per cycle per half:
  what the parent did, what changed in the child, what the other half should look at, one request or one
  disagreement. Each half reads the other's latest entry before its next cycle. Disagreements are stated, logged,
  and both continue; Rohin arbitrates in the morning.
- `research_loop/BOARD.md` — Astra's allocation and state; Fable-VM never edits it.
- Raw transcripts stay node-local under each branch root; each half may READ the other's roots on node 5
  (read-only, node-local); only hashes, counts and short quotes enter the repo.
- Rohin's orders reach both halves the same way as tonight: laptop watcher → notice in Main + notebook entry.

## 2. Allocation (40 GPUs)

| GPUs | Work | Owner |
|---|---|---|
| 14 (old fleet) | level 1: persistence × metacognition post-training — prompt → select functional rows → train; anchor set in every batch; LoRA-ON/OFF suite each checkpoint; level-2 corrected continuations flow in as a labelled arm | Astra |
| 10 (old fleet) | frozen-base parenting, long lives | Astra |
| 8 (old fleet) | learned-child parenting (best level-1 child), same protocol at lower parallelism; one shared control triple for the whole campaign | Astra |
| 4 (node 5, GPUs 4–7) | frozen-base parenting, Astra's parents | Astra |
| 4 (node 5, GPUs 0–3) | frozen-base parenting, Fable's parent swarm | Fable-VM |

Rules: no productive mid-run pre-emption; as sheer-generation loops finish, half of those GPUs move to parenting;
every GPU stays busy all night; **a GPU never waits for an admission check between lives** — the next life starts
on the same GPU as soon as the previous one ends, with the fresh-process readout folded into the life itself.
New nodes (node 6 when it turns RESERVED) go to parenting first, split by the level-1 vs level-2 results.

## 3. The child loop (one life = one branch on one GPU, hours long)

1. **Child**: frozen Qwen2.5-7B-Instruct + one rank-8 LoRA (fresh at birth of the branch). Base-model branches
   start from the untrained base; learned-child branches from the best level-1 checkpoint.
2. **Episode**: the child works one task in its game with a large token budget (≥ 4,096 generation tokens,
   context 16k). The parent sees every child token and may speak at its cadence; the child sees every parent
   word. The environment returns its outcome; the outcome is recorded, never used to select.
3. **Pre-sleep metacognition** (every 2 episodes): a long session in which the child says what it did, what
   mattered, what surprised it, what is about to leave its context, what it would do differently; the parent
   converses ("this is kind of important, don't you think?"). Then **reflection** on the two episodes: the same
   experiences seen from several angles — perception, not repetition; the repetition stop is on. Reflection
   length is a knob per branch (short / long).
4. **Sleep**: the child's own tokens from the episodes, the metacognition session and the reflection become rows
   (parent text in the prefix, masked; never a target). 16 presentations per row, in-batch rehearsal of earlier
   rows of this life (childhood: rehearsal ON), one optimizer, checkpoint every sleep. Nothing is compiled;
   nothing is selected by outcome or by quality.
5. **Readout after every sleep** (fresh process, parent-free, context-free, ≤ 3 min): 8 held tasks of the game,
   the 16 old facts, the audit pair, and — the readout that matters — the behaviour measures of §5 on the held
   outputs. Every 4 sleeps: the fixed LoRA-ON / LoRA-OFF capability panel.
6. **Loop** to the next two episodes on the same GPU without a gap. A life runs until Rohin wakes, or a hard
   wall bound set by the lease, whichever first.

Twins (the single shared control triple, once per campaign, not per branch): the same base + the same game with
(a) parent present but sleep frozen, (b) no parent, sleep running, (c) parent present, no LoRA. Everything else is a
treatment branch.

## 4. Games (3–6 branches per half; each branch one game, one parent cadence, one style)

All exist in the repo already; no new environment is built tonight.

| Game | Why it fits | Difficulty knob |
|---|---|---|
| Route worlds (61-world graph, READ/ROUTE protocol) | followable, the parent can point ("you aren't here, here, here"); learning = using records | world size, opposite-goal pairs |
| Math word problems (GSM-style, exact oracle) | putting things together; conclusions; checks are natural branches | multi-step count, held families |
| Code (MBPP-style, unit-tested) | tool-like action + reasoning; persistence pays | tests per task, hidden tests |
| CompilerGym pass ordering (cgym, deterministic reward) | hill-climbing, level-3-like: reasoning alone does not suffice | benchmark, pass budget |

"Not so complex that you spend more time trying to solve than perceiving and reminiscing": each half runs at least
one easy game (route or single-step math) and one hill-climbing game (cgym or hard code). Games are never scored as
the result; the environment outcome is a background tag.

## 5. What we measure (behaviour, never the game)

Per branch, per sleep, from the parent-free held outputs and the transcripts; the orchestrator's readout code
computes, the laptop watcher re-derives from raw:

1. **Metacognitive allocation**: does effort vary with the task (tokens and steps per task vs a flat profile); does
   the child change how it is thinking within a solution (strategy switch that changes the continuation)?
2. **Self-perception**: does it state what it can and cannot do, and is the statement borne out by the next action?
3. **Reflection quality**: in the pre-sleep session — distinct observations per token (novel-thought yield), number
   of angles on the same experience, repeated-4-gram fraction (must stay < 0.2).
4. **Departures-and-returns per response** (Rohin's branching): checks, judgments, what-ifs, asides that return to
   the main line; the template Check slot is excluded.
5. **Persistence**: fraction of responses that continue past the first adequate answer with new content; median
   tokens by default (minimal prompt).
6. **Parent dependence**: interventions per episode the parent needed; ratio of behaviours shown unprompted vs after
   a nudge; the recurrence table of interventions (which classes the parent keeps having to repeat).
7. **Triples**: every (child state, intervention, behavioural change) logged; per cycle: count, share with a visible
   behavioural change in the next 200 tokens.
8. **Retention and capability**: 16 old facts, audit pair, and every 4 sleeps the 32-call LoRA-ON/OFF panel (code,
   math, tools, concise) — a drop of ≥ 2/8 in any family is reported the same hour.
9. Held game accuracy — reported last, never used as a gate.

Pre-registered by the laptop watcher before the first readout (ledger P70–P72): (P70) within 8 sleeps, at least one
frozen-base branch shows departures-and-returns per held response ≥ 0.5 where the base's default is ≈ 0.1;
(P71) parent dependence falls across sleeps in at least one branch (interventions per episode at sleep 8 ≤ 0.6 × sleep 1);
(P72) no branch loses ≥ 2/8 on the tool-call family of the capability panel. Expected: ten sleeps before anything
shows; a null on all three by morning is a result about the base, not a failure of the night.

## 6. The Fable-guided swarm (node 5, GPUs 0–3) — for Rohin's approval

**Shape.** Four branches, four parents, one head parent, all Claude Code headless sessions on the VM with model
`claude-fable-5-1` and maximum effort, launched by a small courier script under `~/courier/swarm/` that Astra
wires to the existing lane code (the lanes already accept an external parent provider; the provider becomes a
`claude -p` call). No new model code.

| Branch | Game | Parent cadence | Parent style | Reflection |
|---|---|---|---|---|
| F1 | route worlds | micromanaging — after every child paragraph | training-wheels, supportive | short |
| F2 | math (multi-step) | every ~100 tokens of child thought | creative, supportive | long |
| F3 | code (unit-tested) | once per episode + pre-sleep | harsh-critical (of reasoning, never personal) | long |
| F4 | CompilerGym hill-climb | once per episode + pre-sleep, long horizon | training-wheels, harsh | short |

**Head parent** (one more `claude -p` session per cycle, max effort): after every sleep of every branch it reads the
four Fable transcripts AND Astra's four node-5 transcripts, the triples, and the §5 measures; it writes the
`[Fable-VM swarm]` entry in PARENTING_EXCHANGE.md and COORDINATION.md; it rewrites each Fable parent's prompt for the
next cycle (what to add, stop, shift in the parenting itself — "parenting the parents"); it never touches Astra's
lanes and never edits the child code. This is the metacognition Rohin asked the parenting itself to have.

**The parent prompt (template; the head parent fills the bracketed parts each cycle).**

> You are the parent of a young model. Read research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md before every
> episode; it is the only rulebook. You are watching a child play [GAME]. You see everything it writes; it sees
> everything you say. Your style is [STYLE]; you speak [CADENCE]. You are not here to help it win. You are here to
> add, stop and shift behaviour: make it notice more than the task needs, keep a thought alive past the first
> adequate move, decide where its effort goes and change how it is thinking, wonder what else this could mean,
> connect this to what it saw before, say what surprised it, say what it can and cannot do, and — before every
> sleep — say what mattered and what is about to leave its memory. Never give the answer, the next action, a tool
> call, a hypothesis to test, or a number of branches. Never mention the score. When it forgets a behaviour, say
> it again in different words; it will forget — you must be more repetitive than feels natural. Occasionally
> praise a thought that was interesting even though it went nowhere. After each episode write one line per
> intervention: what the child was doing, what you said, what changed in the next 200 tokens. This cycle's focus
> from the head parent: [FOCUS].

**The head-parent prompt.**

> You parent the parents. Read PARENTING_PRINCIPLES_ROHIN_2026-09-15.md and the last two PARENTING_EXCHANGE.md
> entries from Astra. For each of the eight node-5 branches read the newest sleep's transcript, triples and measures
> (paths in the branch roots; read-only). For each Fable branch decide: which behaviours appeared unprompted, which
> the parent had to repeat, which never took; whether reflection is perception or repetition; whether the parent is
> steering behaviour or the game. Rewrite that parent's [FOCUS] and, if needed, its cadence or style, in one
> paragraph each. Write one exchange entry: three observations, one thing Astra's parents do that ours should,
> one thing ours do that Astra's should, one request. Never gate on outcome, never stop a branch, never change the
> child code. Use maximum effort; think for as long as it takes; you have the whole cycle.

**Effort and models.** Fable: `claude -p … --model claude-fable-5-1` with the session setting for maximum
reasoning effort; Astra: gpt-6-astra xhigh (already). Both halves keep all transcripts as lineage data.

**Cost.** Four parents at every-paragraph to per-episode cadence ≈ 40–120 parent calls per branch-hour; head
parent one long call per branch-sleep. Rohin's provider budgets apply; the courier logs every call.

## 7. Hourly and morning reporting

Hourly, both halves, in the notebook (Astra tag `[Builder — parenting hour N]`, Fable `[Fable-VM swarm — hour N]`):
GPUs actually computing per role; branches alive and their sleep counts; interventions per class; triples logged and
the share with a visible change; the §5 measures per branch (numbers only); one sentence of what the parent
changed. The laptop watcher relays only stalls and rulings.

Morning report for Rohin (laptop watcher, ≤ 300 words): the P70–P72 verdicts; the best branch's before/after
behaviour with one quoted exchange; the recurrence table (what parents kept repeating); Fable-parented vs
Astra-parented side by side on the §5 measures; GPU-hours spent per role; what to change first.

## 8. What is forbidden tonight (his words)

No outcome gating, selection or steering ("we don't care about outcome performance at all when we're testing how
the data is"). No admission gaps between lives ("just keep it going"). No templates in rows or prompts (no Check
slot, no "three hypotheses"). No "intervene on failure" — add, stop, shift. No compiler. No literal repetition in
reflection. No relocation of GPUs mid-run where level 1 is producing good results. No private channels between the
halves. No hostnames, keys or credentials in anything written. The watcher never launches Astra's jobs and never
edits its lanes; the Fable half never edits Astra's lanes or the child code.

## 9. Launch checklist for §6 (after Rohin's go)

1. Astra: expose the parent-provider hook as a shell command taking (transcript path) → (parent text), and the
   lane launcher for node 5 GPUs 0–3 with `--parent-provider claude` and the branch table above; post the exact
   command lines in the notebook.
2. Fable-VM courier: `~/courier/swarm/run_branch.sh <F1..F4>` (calls the lane launcher; supplies the parent
   command = `claude -p` with the template) and `~/courier/swarm/head_parent.sh` (cron every 20 min, max effort).
3. Laptop watcher: pre-register P70–P72; first exchange entry; verify the first parent responses on all eight
   node-5 GPUs within 15 minutes of launch; then half-hour reads as tonight.
4. Stop rule for the Fable half only: a branch is stopped by nothing except a crash or the lease wall; a crash is
   relaunched on the same GPU from its last checkpoint without review.
