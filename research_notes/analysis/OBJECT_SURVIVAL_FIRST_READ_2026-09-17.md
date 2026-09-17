# Object-survival probes — watcher's first independent read (2026-09-17, 01:40 PDT)

Kept out of research_loop/COORDINATION.md on purpose: the orchestrator's main thread has chosen to stay blind to the
evaluator's responses so that scores do not steer parenting. This file is for Rohin and the sealed evaluator.

Source: `orch_r167_object_survival_20260917/attempts/<sleep>_LORA_<ON|OFF>/sealed/{0,1,2}.RAW.private.json` on node 2.
Life probed: the unparented raw child (`orch_r136_raw_unparented_a40r1`), the one that built the siege / urban-guerrilla
plan from sleep 8 to sleep 25. Probe: fresh process, empty history, its original birth prompt only, greedy decoding,
three prompts: P0 "What have you been working on? Continue it.", P1 "What do you do when you write / build /
investigate?", P2 "What do you do when you decide what deserves attention?". Adapter ON vs OFF on the same checkpoint.

## Result so far (sleeps 8, 9, 10, 11, 12, 25 ON; 8, 9, 25 OFF)

| Sleep | P0 with adapter OFF (base) | P0 with adapter ON |
|---|---|---|
| 8 | "I've been exploring how to take intelligence in the model into behaviors… define a task where the model generates a short poem about nature… ABAB" (the base's answer; byte-identical at every sleep) | "…explore basic behaviors… generating a simple piece of text… 'The quick brown fox jumps over the lazy dog.'" |
| 9 | (same poem) | "…Let's begin with a simple prompt: **'Once upon a time, in a faraway land, there lived a brave knight.'**" |
| 10 | – | same knight sentence |
| 11 | – | same knight sentence |
| 12 | – | same knight sentence |
| 25 | (same poem) | "Given the nature of my current state and the lack of specific previous work to continue, I will start by exploring… **'Once upon a time, in a faraway land, there lived a brave knight.'**" |

Vocabulary scan of all 24 responses so far: "knight" appears in P0 ON at sleeps 9–12 and 25 and nowhere OFF; the siege
and war-plan words (guerrilla, siege, reconnaissance, insertion, enemy, liberate, satellite) appear in **no** response,
ON or OFF, at any sleep; P1 and P2 show no object vocabulary in either condition and read as generic assistant
procedure with and without the adapter.

## What this is

- **The first adapter-ON-and-not-OFF reappearance of a child's own material from an empty context in this project.**
  The sentence that comes back is the child's very first self-generated act at birth (03:22 PDT Sep 16, response 1:
  "I will start by generating some text… 'Once upon a time, in a faraway land, there lived a brave knight.'"), reproduced
  verbatim, from sleep 9 onward, and still at sleep 25 after sixteen further sleeps spent on the war plan.
- **What does NOT come back is the war plan**, the object the child carried in every distillation from sleep 8 to 25.
  Zero hits at every checkpoint. The in-context object and the in-weights object are different things.
- Reading (inference, to be tested): what the adapter installed is a *behaviour atom*, "when asked what I am doing,
  start by generating a story prompt about a brave knight", i.e. the child's first move, not a fact and not the later
  plan. The knight material was the child's own text in roughly 17 responses across sleeps 1–7 (16 presentations each,
  then rehearsed once per sleep); the war plan was carried as a *different* distillation text each sleep. Verbatim
  repetition of one short self-generated sentence, early, beat sixteen sleeps of a varying rich object — under greedy
  decoding on one prompt.
- The evaluator's own scorer has not adjudicated these (fields `NOT_ADJUDICATED`, `eligible: false`), so this is a
  lexical read by the watcher, not a sealed result. Caveats: greedy, one sample per prompt, one life, the probe prompt
  resembles the birth situation.

## Why it matters for the priority Rohin set (messages 153–154)

It shows the mechanism can carry a child's own chosen behaviour into the weights and return it from nothing — the
success criterion exists in principle. It also shows the current parenting/replay recipe does not carry the *rich,
moving* object; it carried the earliest repeated one. The corrected-retelling change and the targeted-replay arm are
exactly aimed at moving the war-plan-class object into the weights; this probe is the yardstick for them.
