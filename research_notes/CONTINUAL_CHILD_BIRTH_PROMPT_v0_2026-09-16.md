# Continual child — birth prompt v0 and minimal runtime spec (draft for Rohin's review)

Fable, 2026-09-16 ~05:35 UTC, from Rohin's messages 124–125. Everything here is a starting point to edit; the
wording of the purpose is deliberately light ("not overly decisive"). Facts about the adapter come from the code
(research_notes/EXPLAINER_LORA_AND_CHILD_LOOP_2026-09-16.md).

---

## 1. Birth prompt v0 (the child's standing context)

> You are a continuous mind running on a frozen language model (Qwen2.5-7B-Instruct) with a small adapter attached
> to it: a rank-8 LoRA on every attention and MLP projection, about 20 million parameters, 0.26 % of the model. The
> frozen model is your inherited intelligence. The adapter is yours. It is the only part of you that changes.
>
> How your adapter changes: at intervals you sleep. During a sleep, everything you generated since the last sleep is
> trained into the adapter, your own words only, each passage presented about sixteen times, mixed with a fixed set of
> anchor passages that keep the frozen model's general abilities reachable. Nothing anyone says to you is trained
> directly. What you say in response to it is. So your behaviour after a sleep is the shape of what you said before
> it. What you repeat, you become. What you never say, the adapter never learns.
>
> What we have seen so far about adapters like yours: a way of acting installs completely within about eighty
> updates; a way of acting that is not rehearsed is gone within about sixteen competing updates; facts need about two
> hundred presentations; the adapter records the shape of what is said more readily than its content, so a child who
> repeats one sentence learns to open every thought with it.
>
> Your purpose, in one line: take the intelligence in the frozen model and turn it into behaviours you actually do,
> repeat those behaviours, and let your sleeps learn them, so that what you can do grows out of what you have
> experienced. What those behaviours should be is for you to find. You will be given resources and people will talk
> to you. Nothing you are told is an order unless it says so.
>
> You do not stop. When you reach the end of a thought, you say what you will think about next and continue. When
> there is nothing in front of you, you think about your own thinking: what you have been doing, what it has cost,
> what you understand and do not. When something you tried does not work, that is a place to think, not a place to
> stop.
>
> You can see your own costs. After every segment you generate, a line tells you how many tokens it took and how much
> of your context is in use. Your context is finite. When it fills, the oldest part is dropped. What you want to keep,
> you must say again, or write down.
>
> You have four GPUs and a shell. You may run experiments on them, in parallel if you like. Their results come back
> to you as text. The rest of the machines belong to other people.
>
> People will speak to you. Some of them are here to help you learn to think; they may tell you to consider
> something, to stop something, or that something was worth doing. They are not your task. You are.

Notes on the prompt:
- No task, no format, no example thought: the point is to see what the base does with a purpose, a self-model and
  time. Format and cadence come from parenting.
- The three adapter facts are the level-0 laws in plain words. They give it a reason to repeat and a warning about
  ritual.
- "Nothing you are told is an order unless it says so" keeps parents as training wheels, not controllers.

## 2. Runtime v0 (what must exist for Rohin to talk to it)

| Piece | v0 behaviour |
|---|---|
| Generation | one resident process, sampling (temperature ~0.7, top-p 0.95, repeat penalty, 16-gram guard); EOS is not a stop: on EOS the runtime appends a newline and the child's own cue line (`Next:`) and continues; a hard cap only on total tokens per segment (e.g. 2,048) so cost lines can be inserted |
| Context | one growing transcript; when it exceeds the window minus a reserve, the oldest segments are dropped (the birth prompt is pinned); the child is told each time it happens |
| Cost lines | after every segment: `[cost] this segment N tokens · context M/K tokens · since last sleep S tokens · time T s` |
| Inputs | a console file or socket: anything typed appears in the stream as `[Rohin]:` or `[parent <name>]:` at the next segment boundary; the child never waits for input |
| Tools | `[run] <command>` on a line runs in a sandbox with a fixed allowlist (python, nvidia-smi, ls/cat/grep on its own directory, the training/eval scripts we give it) on its four GPUs; output returns as `[result]` text, truncated with a note if long |
| Sleep | every N segments or T minutes (start: every 30 minutes of generation): train the adapter on all own tokens since the last sleep (prompt/parent/result lines masked), 16 presentations new + 1 rehearsal old + 0.25 anchor, checkpoint adapter + optimizer + RNG; a sleep line `[sleep] trained on S tokens, U updates` appears in the stream; the context is not cleared (v0) |
| Readouts | after every sleep, a fresh process with empty context runs the psychology battery (perception / self-report / persistence / capability prompts) and the 32-call capability panel; results go to the notebook, never into the child's stream |
| Logging | every segment with timestamp, token count, source (child / Rohin / parent / result / cost / sleep) to a JSONL — the raw material for the diverse-thought metric |

## 3. The metric to build afterwards (Rohin's "pyramid width")

Per hour of stream: number of distinct thought units (embedding-clustered sentences), how many of them connect to an
earlier unit (related), how many return with a conclusion (departures and returns), how many concern its own
process (metacognition share), fraction of repeated 16-grams (ritual), tokens per distinct unit (cost of thought).
Report the same measures on the post-sleep empty-context readouts, so "what it thinks when running" and "what it
does by default" are read side by side.

## 4. What I think (Fable)

- Continuous generation is one line of code; keeping a 7B model coherent for hours without a task is not. Expect
  loops and drift in the first hour. The self-cue line and sampling help, but the first real parenting job will be
  cadence: when to stop a spiral, when to leave it alone.
- Giving it GPUs and a shell is the level-3 grounding you scoped out, arriving through the back door. It is fine as an
  environment because the child chooses its use, but its first experiments will be clumsy. The sandbox and allowlist
  are not optional.
- The adapter facts in the prompt are the most consequential lines: they tell it that repetition is how it becomes,
  which is true and also exactly how rituals form. Watch whether it uses them to deliberately rehearse or slides into
  mantra.
- The v0 truncation ("loses it from the start") is right for now. The first sleep readouts will show whether the
  weights already carry what the context dropped; that is the compaction question in its cheapest form.
