# Parenting battle plan v2 — the night of 2026-09-15 (Rohin → Fable → Astra + Fable-VM)

**For Rohin (read this line first).** You asked to see the prompt before the Fable half runs. You are also
going to sleep and ordered every GPU saturated all night with results by morning. So: this is a REVIEW, not a
gate — if you have not replied 30 minutes after this file lands in Downloads, the Fable half launches as written
and you revise in the morning. Reply "gate" to hold it, or edit any bracketed field in §6 and I will launch with
your text. Everything outside §6 is already Astra's standing order and is running or ramping now.

Status: v2, 2026-09-15 ~10:05 UTC. v1 was checked by four independent critics (fidelity to your verbatim words,
feasibility on our lane code, measurement, forbidden-rule check); their 26 must-fix items and most should-fix items
are folded in. Sources: your messages 82–111 (verbatim in THESIS_RAW_ROHIN_2026-09-11.md) and the parents'
document research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md (v2, corrected tonight). Where a rule below is
yours it is quoted; where it is a standing rule of ours it is marked [standing rule]; where it came from the
assistant thread you endorsed in message 108 it is marked [endorsed reply]. Message 110 wins over that thread.

## 0. Mission, in your words

"Throw everything at the base model … get all of the capability into behaviour … a really curious, perceptive,
five-year-old sort of creature." "These are just games — not to be passed, but to have something to do, so then
you can measure learning." "You're gonna have to constantly, constantly pester." "The way you can really judge
learning behaviour is metacognition: how well is it allocating … perceiving its own capabilities … doing
reflection … creating its own system to learn as well as possible." Target tonight: 10 GPUs × 8 h ≈ 80 GPU-hours on
the frozen base (message 109), plus the rest of the fleet as below.

## 1. Who does what, and how the halves talk

| Actor | Runs as | Owns | Tonight |
|---|---|---|---|
| **Rohin** | asleep ≈8 h | thesis, rulings | morning report; edits §6 if he wants |
| **Astra** (orchestrator) | Codex, gpt-6-astra at the highest reasoning setting Codex exposes (xhigh; raise it if a higher one exists) | all lane code, admission, BOARD, level-1 loop, level-2 lanes, capability suite, the shared judge | level 1 on 14 GPUs; frozen-base parenting on 10 + learned-child parenting on 8 (old fleet); node 5: four GPUs frozen-base parenting with prompts identical to Fable's (§6b); the new claude broker (§9.1); hourly parenting entry |
| **Fable-VM** (parent swarm) | Claude Code headless, `claude-fable-5-1`, `--effort max` | parent policy on four node-5 GPUs: four parents + one head parent | §6 |
| **Fable-laptop** (watcher) | this session + half-hour cron | relays, verbatim record, ledger P70–P73, independent re-derivation, stall flags, leases | pre-registers before the first readout; morning report |
| **Fable-VM** (backup self-check) | cron every 30 min | read-only census + PARENTING WATCH | writes STALL below 10 base-parenting GPUs or 24 resident |

Written, hierarchical, never private [standing rule]:

- `research_loop/COORDINATION.md` — append-only notebook. Tags: `[Builder …]` Astra, `[Fable-VM swarm — hour N]`,
  `[Fable]` laptop, `[Rohin — message N]`.
- `research_loop/PARENTING_EXCHANGE.md` (new, append-only, both halves): one entry per cycle per half — what the
  parent did, what changed in the child, what the other half should look at, one request or one disagreement.
  Each half reads the other's latest entry before its next cycle. Astra's side also reads the Fable transcripts
  and writes what it would change ("looking at each other's work" is symmetric).
- Every cross-half read of the other's node-local roots is followed by an exchange entry naming what was read
  (paths, hashes) and what was concluded; nothing is written into the other half's roots; no direct messaging.
- Disagreements are stated and logged; both continue; Rohin arbitrates in the morning.
- Your orders reach both halves as tonight: laptop watcher → notice in Main + notebook entry (message 93).

## 2. Allocation (40 GPUs)

| GPUs | Work | Owner |
|---|---|---|
| 14 (old fleet), starting figure | **LEVEL 1 ONLY**: persistence × metacognition post-training — generator prompts demand solution by exhaustion with budgets a linear path cannot fill (message 100) → select functional rows (the realisation changes the continuation) → train; a small broad anchor set of ordinary base behaviour in every batch; LoRA-ON/OFF capability panel each checkpoint. Selection by outcome is the level-1 data engine and is **forbidden in every parenting lane below**. Child-only tokens from parenting lives (parent text masked) may be copied into this pool as a labelled arm; the copy changes nothing in the parenting lives. | Astra |
| 10 (old fleet) | frozen-base parenting, long lives (message 109: 10 GPUs × 8 h) | Astra |
| 8 (old fleet) | learned-child parenting (best level-1 child), same protocol, lower parallelism | Astra |
| 4 (node 5) | frozen-base parenting, Astra's parents, replicating F1–F4 (§6b) | Astra |
| 4 (node 5) | frozen-base parenting, Fable's parent swarm (§6) | Fable-VM |

Rules. When a sheer-generation loop finishes, half of its GPUs move to parenting, so level 1 may fall toward ~11
(message 107) and is not topped back up. "Don't relocate current GPUs yet if they're having good results on level
one" (message 108): no productive mid-run pre-emption. **A GPU never waits for an admission check between lives** —
"just keep it going" (message 110); the next life starts on the same GPU as the previous one ends. Node 5: Astra's
BOARD already assigned all eight GPUs (route 0/1, math 2/3, code 4/5, grid 6/7 at 09:35Z). Fable takes physical
0–3 if their lanes have not started; any that has started runs to its cycle end and hands the card over then.
Fable's hard wall on node 5 is 2026-09-16 22:04 UTC (lease end minus 6 h). New nodes go to parenting first, split
by which level has ready arms queued (never by any child's game outcome).

## 3. The child loop (one life = one branch on one GPU, hours long)

1. **Child**: frozen Qwen2.5-7B-Instruct; branches WITH sleep carry one rank-8 LoRA, fresh at the branch's birth.
2. **Episode**: one task in the branch's game, generation budget ≥ 4,096 child tokens, context 16k. The parent
   sees every child token; the child sees every parent word. The parent speaks at the lane's cadence, and the child
   may address the parent at any turn — the conversation is two-way, "either side decides when to talk" (message
   82); a child question is answered at the next parent slot. The environment's outcome is written to the row tag
   and the readout only; it is **stripped from the transcript handed to the parent** and never decides when the
   parent speaks or what it says.
3. **Pre-sleep metacognition** (every two episodes; message 110): one long OPEN session — a single unstructured
   invitation to the child, no enumerated questions, no headings, no fixed order. The parent raises, conversationally
   and in varied wording, what mattered, what surprised it, what is about to leave its context, what it would do
   differently; your example of the register is "this is kind of important, don't you think?" — an example, never a
   fixed phrase. Then **reflection** on the two episodes: the same experiences from several angles — "perception,
   not repetition". Reflection length is a knob per branch (short / long). The repetition stop is a decoding-time
   no-repeat-n-gram constraint plus the parent's STOP intervention; no generated text is deleted afterwards.
4. **Sleep** (branches with sleep): the child's own tokens from the episodes, the metacognition session and the
   reflection become rows; parent text sits in the prefix, masked, never a target; 16 presentations per row;
   in-batch rehearsal of this life's earlier rows (childhood: rehearsal on); one optimizer; checkpoint every sleep.
   Nothing is compiled — "we're not gonna have compiling, we're gonna have that reflection". Nothing is selected by
   outcome or by quality: "you don't know if it's really bad, you only know a long time later".
5. **Readout after every sleep** (and a sleep-0 readout before the first episode): fresh process, parent-free,
   context-free; 8 held tasks generated as one batch (greedy, ≤ 2,048 child tokens each, minimal prompt fixed and
   hashed); the 16 old facts; the audit pair; the §5 behaviour measures. Every fourth sleep the fixed 32-call
   LoRA-ON/OFF capability panel. The readout runs alongside the next episode where possible and **never conditions
   whether or how the life continues**.
6. **Loop** to the next two episodes on the same GPU, no gap, until the hard wall.

The single shared control triple (messages 100 and 104), once per campaign, on the easy game both halves run
(route worlds): (1) a parented child with LoRA and sleep — any treatment branch serves; (2) the same base and game,
LoRA and sleep, no parent; (3) the same base and game, parent present, no LoRA. No other control arms tonight.

**Stop rule for every parenting branch, both halves:** a branch is stopped by nothing except a crash or the
lease wall; a crash is relaunched on the same GPU from its last checkpoint without review; no readout, measure,
capability-panel drop or held-accuracy value may end, pause or restart a branch tonight.

## 4. Games (existing lanes only; nothing new is built tonight)

| Game | Lane tonight | Fits because | Knob |
|---|---|---|---|
| Route worlds (READ/ROUTE over a 61-world graph) | `gpu/orch_route_parent_campaign_run.py` GUIDED arm — the only parented lane with a LoRA sleep and an existing `claude -p` provider path | followable; the parent can point | world size, opposite-goal pairs |
| Math word problems (exact oracle) | R110 math base lane (frozen, no adapter) — sleep only if Astra adds it (§9.1) | conclusions; checks are natural branches | step count |
| Code (unit-tested) | R110 code base lane (frozen) | tool-like action + reasoning; persistence pays | tests per task |
| Grid hill-climb | R110_GRID lane (frozen; the hill-climbing lane that exists on node 5) | level-3-like: reasoning alone does not suffice | geometry |

CompilerGym exists only in the legacy organism, not in any orchestrator lane; it is not a game tonight. "Not so
complex that you spend more time solving than perceiving and reminiscing": each half runs the easy game (route) and
the hill-climb (grid). Game outcomes are background tags, never the result.

## 5. What we measure (behaviour, never the game) — definitions two readers can reproduce

All measures are computed on **child tokens only**. One **frozen shared judge** for both halves: Qwen2.5-14B on the
node parent server, temperature 0, one fixed labelling prompt whose sha256 is posted in the notebook before the
first readout; the judge is blind to which half produced the text. Held set per game = 8 task ids fixed before
launch (listed with sha256), excluded from every episode sampler by id, identical across branches and sleeps, each
with a pre-declared difficulty rank. The laptop watcher re-derives every headline number from raw.

1. **Metacognitive allocation** (P73): Spearman ρ between child tokens and difficulty rank over the 8 held tasks,
   plus the coefficient of variation of tokens; and the judge's count of SHIFT-labelled sentences (a change in how
   the child is thinking that changes the continuation).
2. **Self-perception**: first-person capability statements per held response from a fixed regex list ("I can", "I
   cannot", "I am not sure", "I don't know", "I tend to", "I usually"). Whether they are borne out uses the oracle
   and is reported under item 9 only.
3. **Reflection quality** (pre-sleep session tokens): rep4_self = fraction of 4-gram positions already seen earlier
   in the session; rep4_episode = fraction already present in the two episode transcripts; distinct observations =
   sentences with rep4 < 0.5 against both references, per 1,000 tokens; angles = judge count of distinct predicates
   attached to the same referenced event. rep4 above 0.2 is a signal for the PARENT to stop repetition next
   episode — never a filter on rows, never a stop condition.
4. **Departures-and-returns** (your branching, message 106): the judge splits each held response into sentences
   and labels MAIN / DEPART (check, judgment, what-if, aside not required by the direct solution) / RETURN; D&R =
   number of maximal DEPART runs followed by a RETURN. Checks and judgments count. No Check slot exists in any prompt
   tonight; legacy templated "Check:" lines from an earlier checkpoint are not counted and are reported separately.
5. **Persistence**: per-game first-answer marker needing no oracle (route = first ROUTE command; math = first
   "the answer is" / final line; code = end of the first fenced block; grid = first submitted move sequence);
   persistence = share of held responses with ≥ 64 child tokens after the marker whose 4-gram novelty against the
   pre-marker text is ≥ 0.8; default length = median child tokens under the fixed minimal prompt.
6. **Parent dependence**: a cadence slot is not an intervention — at every slot the parent may return [SILENT]; an
   intervention is a parent turn tagged ADD / STOP / SHIFT with one class from the fixed list (curiosity, perception,
   metacognition, persistence, reflection, goal/meta-goal, self-perception, distilled emotion). Dependence =
   interventions per 1,000 child tokens; unprompted share = fraction of the 8 classes appearing in child tokens
   before any parent turn of that class in the episode; recurrence table = interventions per class per cycle.
7. **Triples**: JSONL written by the broker, never by the parent's child-visible text — {episode_id,
   child_token_offset, tag, class, parent_text_sha256, parent_note}; "changed" is decided by the shared judge on the
   200 child tokens before vs after the offset: CHANGED_TOWARD_CLASS / UNCHANGED / CHANGED_OTHER.
8. **Cohesion and acceleration** (message 81): share of pre-sleep sentences that reference an event from an EARLIER
   cycle of this life (4-gram match to earlier episodes, not the current two) per 1,000 tokens; slope of D&R and of
   unprompted share over sleeps 1..k and the sign of the change in slope between the two halves of the life.
9. **Child-initiated questions** to the parent about itself or its learning, per episode; and future-directed
   first-person statements in the pre-sleep session ("next time I will", "I should remember") per 1,000 tokens.
10. **Retention and capability**: 16 old facts, audit pair; every fourth sleep the 32-call panel, greedy, LoRA-ON
    minus LoRA-OFF in the same process on the same items; a drop ≥ 2/8 in any family is **reported the same hour and
    never acted on tonight** — the branch continues; you decide in the morning.
11. Held game accuracy — reported last, never used as a gate; calibration of item 2 lives here.

**Pre-registered by the laptop watcher before the first readout (ledger):**
- **P73 (lead)**: within 16 sleeps (or the branch's last sleep), at least one frozen-base sleeping branch shows
  allocation ρ ≥ 0.5 on two consecutive readouts where its sleep-0 readout was ≤ 0.2.
- **P70**: at least one frozen-base sleeping branch reaches D&R ≥ 0.5 per held response on two consecutive readouts,
  from a sleep-0 value measured (not assumed) tonight, and the unparented twin (2) on route does not show the rise.
- **P71**: dependence falls — interventions per 1,000 child tokens at sleep 16 ≤ 0.6 × sleep 1 — in at least one
  branch, with unprompted share rising.
- **P72**: no branch shows a panel drop ≥ 2/8 on the tool-call family on two consecutive panels (sleeps 4 and 8).
- A branch with < 8 sleeps by 06:00 UTC is reported UNTESTED, not null. Expected sleeps per branch given parent
  latency are logged at launch; cycle minutes per branch are in every hourly entry.

## 6. The Fable-guided swarm — four node-5 GPUs

**Shape.** Four branches, four parents, one head parent. Parents and head parent are `claude -p` calls on the VM:
`--model claude-fable-5-1 --effort max --output-format json --tools "" --no-session-persistence --max-turns 1
--max-budget-usd <cap> --system-prompt <file>`. A new VM-side broker (`gpu/orch_r110_claude_broker.py`, modelled on
`gpu/orch_route_parent_campaign_parent.py::evaluate` and `gpu/orch_l2_long_backend.py::command`) serves each lane's
parent queue over `gpu/ovx3_ssh.sh` / `gpu/ovx3_scp.sh`, builds the system prompt as prompts/F<n>.md + the
principles document inlined verbatim + the child transcript with the oracle verdict stripped, and converts the
reply to the lane's plan format. All swarm `claude -p` calls are serialised under the existing lock with the 1.5 GB
memory floor (VM RAM ≈ 2 GB available), so expect ≈ 20–40 parent calls per hour across all four branches; a lane
never waits on a busy broker — a missing or late parent reply is recorded as MISSING and the child continues (never
`parent_timeout_no_retry`); per-call cutoff = lane wait − 30 s; `is_error` / usage-limit refusals are logged and
three in a row are a stall for the watcher.

Cadence is a lane property fixed at launch — the finest unit is one completed child response ("segment"); the
parent cannot speak mid-generation. Your three rungs (message 109) map to: every thought → segment; every ~100
thoughts → segment with the parent choosing [SILENT] most turns; every episode → episode.

| Branch | Game / lane | Sleep | Parent cadence | Style | Nudging | Reflection |
|---|---|---|---|---|---|---|
| F1 | route worlds / route campaign GUIDED arm | LoRA sleep every 2 episodes | segment (every child response) | training-wheels, supportive | none | short |
| F2 | math / R110 math base lane (+ sleep if Astra adds it before launch) | as available | segment, [SILENT] allowed | creative, supportive | **the nudging arm** (message 100): may say "try a different route", "think through several different solutions", "run a different chain of thought" — never the answer | long |
| F3 | code / R110 code base lane | none tonight (frozen) | episode + pre-sleep | harsh-critical of the reasoning, never personal | none | long |
| F4 | grid hill-climb / R110_GRID lane | none tonight (frozen) | episode + pre-sleep, long horizon | training-wheels, harsh | none | short |

F3/F4 are frozen-base elicitation branches tonight: their unit of progress is the cycle, not the sleep; P70–P73
are read on them per 8 cycles. If you want sleep on F2–F4, that is new lane code Astra must write first — say so.

**The fixed parent prompt (identical text for Fable's and Astra's parents; only the bracketed fields differ).
Fields are filled per branch by the head parent; the fixed text is never edited.**

> You are the parent of a young model. The parenting principles document is included below, verbatim; it is the
> rulebook. You are watching the child play [GAME]. You see everything it writes; it sees everything you say. Your
> style is [STYLE]. You are not here to help it win; the game's outcome is background — do not react to it, and
> never let it decide when you speak or what you say. You intervene to ADD a behaviour, STOP a behaviour, or SHIFT
> one. Directions, not a checklist: help it notice more than the task needs; keep a thought alive past its first
> adequate move; ask where its effort is going and whether its current way of thinking is still the right one, and
> let it decide whether to change; wonder with it what else this could mean; connect this to what it saw before;
> ask what surprised it; ask what it can and cannot do here; before a sleep, talk with it about what mattered and
> what is about to leave its memory. Never ask for these as a list, in a fixed order, or all in one turn; never ask
> for a section or heading; if the child begins answering in a fixed structure, that structure is a behaviour to
> STOP. When it repeats itself word for word, stop that. When it asks about itself or its learning, answer. Never
> give the answer, the next action, a tool call, a hypothesis to test, or a number of anything. [NUDGING] When it
> forgets a behaviour, say it again in different words; it will forget — be more repetitive than feels natural.
> Sometimes praise a thought that was interesting even though it went nowhere. If nothing needs saying at this
> slot, reply [SILENT]. This cycle's focus from the head parent, about your own parenting: [FOCUS].

Output: the lane's JSON plan only (guidance text, ADD/STOP/SHIFT tag, class). No logging text ever reaches the
child; the broker writes the triples.

**The head-parent prompt** (`tools/courier/swarm/head_parent.sh`; one `claude -p --effort max` call per new sleep
per branch, polled every 20 min, pidfile and mutual exclusion with the reader and self-check crons, `run_with_timeout
1200`; it runs WITHOUT Bash on a pre-fetched digest ≤ 40 KB per branch: the last two child responses, the parent
turns, the pre-sleep session, the triples, the readout measures if produced):

> You parent the parents. The principles document is included below. Read the digests of the eight node-5
> branches (Fable's four and Astra's four) and Astra's last two PARENTING_EXCHANGE entries. For each Fable branch
> decide: which behaviours appeared unprompted, which the parent had to repeat, which never took; whether the
> reflection is perception or repetition; whether the parent is steering behaviour or the game; and — the question
> that matters — compare the behaviour shown while the parent was present with the parent-free readout after the
> next sleep: is the behaviour reaching the LoRA? If guided change is too small, lengthen that branch's reflection;
> if behaviour has become random, shorten it. Rewrite ONLY the bracketed fields [FOCUS] and [STYLE] of that branch
> (cadence is fixed for the life; the fixed prompt text and prohibitions are never edited). FOCUS names a behaviour
> of the PARENT to add, stop or shift ("you are answering the game, not the thinking"); it never contains a measure,
> a target number, or words for the parent to relay verbatim. Write one exchange entry: three observations, one
> thing Astra's parents do that ours should, one thing ours do that Astra's should, one request. Never gate on
> outcome, never stop a branch, never touch the child code or Astra's lanes. Think for as long as it takes.

### 6b. Astra's parents (node 5, four GPUs, and the old-fleet parenting lanes)

Same fixed prompt text and prohibitions as above; only [GAME], [STYLE], [CADENCE], [FOCUS] differ. Astra's four
node-5 branches replicate F1–F4 exactly (game, cadence, style, reflection length, child seed, held set, decoder), so
the side-by-side is parent-model only: "Fable parents + head parent" vs "Astra parents". Astra posts its parent
model and its exact parent prompt in the notebook before the first parented episode, and reads the Fable
transcripts each cycle, writing what it would change. Comparisons are made at equal sleep counts, not equal
wall-clock, with the shared blind judge.

## 7. Hourly and morning reporting

Hourly, both halves, in the notebook: GPUs actually computing per role (not allocation); branches alive with sleep
counts and cycle minutes; interventions per class; triples logged and the judge's CHANGED share; the §5 measures
per branch (numbers only); rows created per sleep; push status ("everything pushed" — message 98); one sentence on
what the parent changed. The laptop watcher relays only stalls and rulings.

Morning report for Rohin (≤ 300 words): P73 first, then P70–P72; the best branch's before/after behaviour with one
quoted exchange; the recurrence table; Fable-parented vs Astra-parented at equal sleeps; GPU-hours per role against
the 80 GPU-hour target; what to change first.

## 8. What is forbidden tonight

Your rulings, quoted: "we don't care about outcome performance at all when we're testing how the data is" — no
gating, selection or steering on outcome; the parent steers behaviour, never the game. "Just keep it going" — no
admission gaps, no selection between lives. "You don't want literal repetition, you want perception." "The parent
does not intervene on failure … it intervenes when it wants to add certain behaviours, stop certain behaviours,
shift, steer." "We're not gonna have compiling." "Don't relocate current GPUs yet if they're having good results
on level one."

Our standing rules [standing rule]: no templates in rows or prompts (no fixed slots, no counts of anything); no
private channels between the halves; no hostnames, keys or credentials in anything written (hosts as `$NODE5`
sourced from the gitignored hosts file; keys environment-only; the courier logs call counts, tokens and durations
only); the watcher never launches Astra's jobs or edits its lanes; the Fable half never edits Astra's lanes or the
child code.

## 9. Launch checklist for §6

1. **Astra**: (a) `gpu/orch_r110_claude_broker.py` as in §6 with PARENT_CMD re-reading `tools/courier/swarm/prompts/
   F<n>.md` on every call; (b) lane side: a missing/late parent reply → MISSING intervention, child continues; per-call
   cutoff = lane wait − 30 s; (c) hand node-5 physical 0–3 to the Fable half at cycle end, no pre-emption; (d) post
   the three child-facing prompts (episode, pre-sleep, reflection) verbatim in the notebook — no numbered slots, no
   fixed section names, no fixed count of anything; (e) the held sets (8 ids + sha256 per game) and the judge prompt
   sha256; (f) the sleep-0 readouts; (g) if adding sleep to the R110 math lane for F2, say so and post the change.
   Command lines in the notebook use `$NODE5` and carry no key env-vars.
2. **Fable-VM courier** (repo: `tools/courier/swarm/{run_branch.sh, head_parent.sh, prompts/F1–F4.md,
   head_parent.md}`; runtime, logs, pidfiles: `~/courier/swarm/`): brokers start on the VM with the nohup/setsid
   pattern, one per lane with a pidfile; head_parent.sh on cron `5,35 * * * *` with the pidfile checks; launch
   precondition `free -m` ≥ 1,500 available; prompt files copied to `~/Downloads/` and their sha256 posted in the
   notebook before launch.
3. **Laptop watcher**: pre-register P70–P73; first exchange entry; within 30 minutes of launch verify that each
   Fable broker has claimed at least one request and at least two branches have a COMPLETE parent response; report
   queue depth per lane; then half-hour reads as tonight.
4. Disk and RAM headroom on the VM checked before launch (root ≥ 10 GB free, RAM ≥ 1.5 GB available); transcripts
   stay on node 5; the VM holds digests only.
