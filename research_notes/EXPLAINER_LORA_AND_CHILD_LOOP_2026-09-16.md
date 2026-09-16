# Dream-state: the LoRA model and the child's loop, as they actually run

Written by Fable, 2026-09-16 ~02:00 UTC, from the code of the lanes that ran on 2026-09-15 (route lane
`gpu/orch_r121_route_independent.py`, math lane `gpu/orch_math_feedback_uptake_r121_independent*.py`, engine
`gpu/orch_guided_native.py`, environment `organism_v6/orch_full_rich.py`) and from the level-0 record
(`research_notes/SUCCESSES_AND_LAWS_2026-09-14.md`, `research_notes/PREDICTIONS_LEDGER.md`). Two readers pulled every
number below with file:line citations; the citations are in `research_loop/COORDINATION.md` under the same date.

---

## Part A. The LoRA model

### A1. What the adapter is

- **Base:** Qwen2.5-7B-Instruct, frozen, pinned by file SHA. Nothing in it ever changes.
- **Adapter:** a rank-8 LoRA on all seven projection matrices of every layer: the attention q, k, v, o projections and
  the MLP gate, up, down projections, in all 28 layers. For each targeted weight W the model computes
  W·x + (alpha/r)·B·(A·x), where A is r×d_in and B is d_out×r. With r = 8 and alpha = 16 the delta is scaled by 2.
  Dropout 0.05 on the LoRA path, no bias terms, plain LoRA (no rsLoRA, no DoRA).
- **Size:** 20,185,088 trainable parameters, 0.26 % of the base. On disk 80.8 MB (fp32) as
  `adapter_model.safetensors` + `adapter_config.json`, saved with PEFT at birth and after every sleep, each save
  wrapped in an identity record (state hash, base SHA, file SHAs).
- **Why rank 8:** in the level-0 fact-bank tests rank 32 never helped and hurt when a fact had few renderings
  (one-form loss 2.60 vs 0.52 nats at rank 8; equal only at sixteen renderings). The older design document
  CHILD_MECHANISM_v7 still says rank 32 / alpha 64; the running code is rank 8 / alpha 16.

### A2. What "the base is not overwritten but access can be lost" means concretely

The adapter is an additive low-rank delta on every projection. Switching it off (LoRA OFF) returns the exact base
model: on the 32-call capability panel OFF reproduced BASE on 32/32 outputs (P66) and 31/32 (P68), token for token.
With the adapter ON the same child scored 22/32 and 21/32 against 24/32 for BASE. So a capability drop under ON is
steering by the delta, not destruction of the base: the knowledge is intact, the adapter changes which path the model
takes to it. The anchor rows in every sleep (below) exist to keep those paths open.

### A3. How a sleep writes the adapter

- **Optimizer:** AdamW, learning rate 3e-5, weight decay 0.01, betas 0.9/0.999. In the route and math lanes the
  optimizer state and the CPU/CUDA random state are checkpointed after every sleep and restored, so the optimizer is
  never reset across a life (one older engine used a fresh optimizer per sleep).
- **What is trained on:** only tokens the child itself generated. Every prompt token (the task text, the environment's
  replies, the parent's words, the carried reflection) is masked to loss −100. The parent's words never enter the
  weights directly; they can reach the weights only by changing what the child says next.
- **Dose per row:** every new row is presented 16 times; every row from earlier cycles is presented once more
  (rehearsal). Every optimizer step pairs one child row (weight 0.75) with one of 42 fixed anchor rows (weight 0.25)
  drawn from base-capability tasks. Steps per sleep = 16 × new rows + earlier rows; one observed sleep scheduled 1,884
  steps. Rows over the 16,384-token context are rejected, never truncated.
- **Cadence:** two episodes per cycle, one sleep per cycle.
- **Scale of one life:** at the fork of the current route child, 3,009 optimizer steps had pushed 388,033 child-token
  exposures and 56,236 anchor-token exposures through the adapter. Tonight route F1 is past 16,500 update lines and the
  math children are past 13,700 optimizer steps.

### A4. What level 0 established about this adapter's dynamics

| Finding | Numbers |
|---|---|
| A behaviour (habit, format) installs fast and completely | 32/32 after 80 matched updates, 0/32 with the adapter off |
| Facts need dose, counted in optimizer encounters, interleaved | ~200 presentations per fact: 14/14; 40 updates: 0/4; grouped copies 4/16 vs interleaved 16/16 |
| An unrehearsed habit is erased by competing updates | 32/32 → 0/32 within 16 updates at lr 3e-5, 3/3 seeds; lr 0 keeps 32/32 |
| Rehearsal keeps the old | replay 48/48 after 1,040 updates vs new-only 4/16 |
| Behaviour and facts coexist in one adapter | control arm fails facts identically (4/16 vs 4/16): dose, not crowding |
| Sleep compresses | MATH764 child ~20 % shorter than base (180 vs 226 tokens), same steps on 28/32 paired tasks, 0 added checks |
| Rituals form | fixed first action and templated notes appear between sleeps 5 and 7 in 8/9 lives and persist |

Read together: this adapter is a fast, faithful recorder of the child's own output distribution. Whatever the child
says most often, in whatever form, is what it will say by default after sleep. It does not add richness on its own;
it installs the shape of what was said.

---

## Part B. The child's loop

### B1. Where the child is

One resident process per lane on one pinned GPU. The frozen base and its LoRA adapter live in that process. The
environment (the route world, or the math checker) is code inside the same process. The parent is a separate
process (a broker running a Claude or Astra call) that talks to the lane only through files: the lane writes
`parent_queue/<id>.request.json` and later reads `<id>.response.json`.

### B2. What happens at the start of an episode

The context is rebuilt from nothing every episode. It contains exactly:

1. **System prompt** (route): the rules — at most six turns, four distinct memory reads, two committed routes; end
   every turn with exactly one action on its last line, `READ EVENT <listed address>` or `ROUTE <listed port>` — and a
   guidance block asking for 150–400 generated tokens of substantive first-person reasoning on every turn.
2. **One user message = the board:** `ROUTE TASK / CURRENT N_… / GOAL N_… / PORTS P_…, P_… / EVENTS E_…, …`.
3. **Appended to that user message, if they exist:**
   - `Your prior reflection, not a new observation:` + the reflection text the child wrote at the end of the previous
     cycle (the "carry"). This is the child's only memory in context across sleeps.
   - `Prior parent conversation (advice, not observed facts):` + the last two parent messages.

No earlier transcripts. Decoding is greedy (no sampling), up to 4,096 new tokens per turn, stop on end-of-sequence only.
Math is the same shape: greedy, seeded, 4,096 tokens per episode turn, 8,192 for reflection, and the carried line reads
`Your recorded earlier reflection (not a verified fact):`.

### B3. What happens after the model answers

- **Route:** the environment reads the last non-empty line. `READ EVENT` returns `MEMORY RESULT` + the record (or
  `MEMORY UNAVAILABLE`). `ROUTE` returns a receipt and the new board. Any other last line ends the episode as
  `invalid_final_action`. Limits: 6 turns, at most 4 distinct reads, at most 2 routes; the episode ends on goal, dead
  end, cap, or invalid action.
- **Math:** `INSPECT` and `CALCULATE: <expr>` (first four per turn) are actually executed and their results returned
  (`<ErrorType>: invalid arithmetic request` on bad input). `FINAL:` ends the attempt; the checker's verdict is fed
  back as `Checker feedback delivered to you: {…}`.
- **Open turn (route):** after each episode, two extra turns with `The task is over; the environment is still here … to
  stop, end with STOP.`
- **Parent slot:** once per episode, after the episode's last call. The parent receives the public transcript (every
  child and environment message, labelled; no system prompt). It has 120 s (math: 600 s) to answer; the child never
  waits. A reply is appended as text to the user message of the child's next episode. If the reply is missing or
  `[SILENT]`, nothing is appended and the child proceeds unchanged. Only one parent request can be outstanding.

### B4. Reflection and pre-sleep

After both episodes of a cycle:

1. **Pre-sleep session**, two turns. System: `Take some time with what you just experienced and what you want to carry
   with you.` User: the JSON evidence of both episodes, then `You may continue the conversation.`
2. **Reflection.** System: `Reflect freely on these actual experiences in a way that could help your future self. Stay
   with what you perceived rather than repeating passages or inventing experience.` over the evidence plus its own
   pre-sleep words. Cap 1,024 tokens by default (the parent tier can set 1–8,192); 16-gram repetition guard.

The reflection's raw text becomes `OWN_CARRY.json`, the paragraph injected as "your prior reflection" next cycle.

### B5. Sleep and readout

Training rows are the child's own utterances from the experience turns, open turns, pre-sleep and reflection; readout
text never enters. The adapter trains as in A3, then adapter + optimizer + RNG are checkpointed. Then a **readout** runs
in a fresh subprocess with the parent environment variables stripped: empty context, no parent, no carry, the same 8
held DEV prompts every time (a sealed FINAL set is held for the morning cut). A crashed readout does not stop the life.

### B6. Continuity, in one list

Persists across cycles: the adapter weights; the AdamW state and random state; one reflection paragraph (the carry);
the history rows (for rehearsal); counters and the call ledger. Reset every episode: the whole message context. Trimmed
every cycle: the parent history, to its last two messages. So between sleeps the child remembers exactly two things:
what its weights now say by default, and one paragraph it wrote to itself.

### B7. The baselines

- **UNPARENTED + SLEEP:** the same loop with the parent call omitted; nothing is ever appended to the user message
  except the carry.
- **FROZEN / SEED reference:** the same loop with no optimizer; the adapter must equal the seed adapter, training is
  forbidden.
- **GUIDED + FROZEN** (parented, never sleeps) exists as a named arm in the bridge code.
- **Historical `run_life_v2`** (organism_v6): 1,024 episodes, a sleep every 32, held probes every 64 with a fixed seed.

---

## Part C. Three consequences for the level-1 redesign

1. **Parenting reaches the weights only through the child's next words.** The parent's text is masked out of every
   training row and appears in context only as two appended messages. If the child answers the parent with an echo
   or a confession, the echo or the confession is what gets installed 16 times.
2. **The carry is the whole in-context memory.** One reflection paragraph, rewritten each cycle, is all that bridges
   sleeps. The overnight rituals ("the event I read is not among the task's listed events" as an opener) are this
   paragraph being trained on and then re-read.
3. **Dose is heavy and rehearsal is on, so what is said first gets fixed first.** 16 presentations per row plus 0.75
   weight means the first cycles' habits are installed by cycle 2–3 and rehearsed thereafter. Richness therefore has to
   be present in the child's own words before the first sleeps, or the adapter will faithfully install terseness.
