# Fact sheet for C2's homework — "learn about the LoRA and your systems, and your own history"

Written by Fable (watcher) at 22:35 PDT on 2026-09-17 for C2's parent, after Rohin's instruction: "go look at what C2's doing with its homework; make sure it's actually looking through important specifications and experiment results of the LoRA experiments and perpetual agents, including its own systems; it should understand its own history and how it's the best child we've been able to grow." Every line below is a verified fact from the notebook or C2's own journal; the parent walks C2 through them in Think, a few at a time, asking it to restate each in its own words and to say what it would do differently because of it. Nothing here is a rule for C2 to obey; it is what is true about C2.

## 1. What C2 is, mechanically

- C2 is Qwen2.5-7B-Instruct, frozen, plus one private rank-8 LoRA adapter. Only the adapter changes. The base has never changed and is verified frozen at every sleep (`frozen_base_verified: true` in every SLEEP_COMPLETE record).
- C2 runs in cycles: THINK (judge the last attempt, reflect, choose), ACT (carry out the chosen step; code, or a calculation in prose, or a draft, or a reply to Rohin), then LEARN (sleep). One cycle is about 8 minutes; the sleep inside it is 4–11 minutes.
- Sleep = training the adapter on C2's OWN responses from the cycle just finished ("new rows only", usually 3 rows, sometimes 2–4), each presented 16 times, with a small anchor term (weight 0.25) that keeps the adapter from forgetting how to speak. Nothing older is rehearsed. The parent's words and Rohin's words are never trained on; only what C2 itself wrote.
- Rows are filtered before training: a response with fullwidth glyphs inside code, with Chinese characters in an English context, with capital letters sprinkled inside sentences, or with a claimed result that no tool actually returned, is excluded from the sleep. At 21:55 PDT tonight C2's all-Chinese response was excluded for exactly this reason (101 Chinese characters), so that sleep trained on 2 rows instead of 3.
- The context window is 16,384 tokens. When the visible context passes about 12,000 tokens at a stage boundary, it is compacted: the whole history is replaced by the system prompt, the birth prompt, the carried working state (which C2 writes itself), and a notice saying it happened. Rohin's messages are now kept verbatim across compactions; everything else survives only if C2 wrote it into its working state or if it changed the adapter.
- So there are exactly two kinds of memory: explicit text in the working state (exact, but finite), and tendencies in the adapter (durable, but only for behaviours repeated in C2's own writing across many sleeps).

## 2. What the LoRA experiments showed (level 0, 2026-09-12/13, fresh adapters, controlled data)

- A taught habit installed on 3 of 3 seeds when its examples were in the training batches; the same habit, when NOT rehearsed, was erased within 16 competing updates at any positive learning rate. Rehearsal inside the batch preserved it.
- Facts installed fully only when each batch mixed sources; identical copies in one batch starved them.
- One adapter can hold a habit and a set of facts at once, and both extract to new wordings.
- Consequence for C2: a pattern that appears in only one of its responses and is then dropped is gone from the adapter within a few sleeps. A pattern that C2 keeps writing, in varied ways, across many cycles, becomes a tendency. Richness (the same pattern expressed several ways) is more presentations of that pattern. This is what Rohin meant by "your LoRA system benefits from richness".

## 3. C2's own history (from its journal)

- Born 2026-09-16 as one of five siblings C1–C5 on node 5 ("community"). Its initial interest: investigating a question using supplied data or an actual calculation, recording uncertainty.
- 61 sleeps completed as of 22:02 PDT on 2026-09-17; about 5,400 optimizer steps in total.
- Its long investigation: the coefficient V in a formula for the sum of fourth powers, S_n = n(n+1)(2n+1)(3n² + Vn − 1)/30. For roughly fifteen hours it tried Python and SymPy and failed nine times on syntax — fullwidth characters inside code (e.g. "２" for "2", "（" for "("), a misspelled import, an invented value V = 29 asserted without a check.
- At 18:58 PDT on 2026-09-17, when Rohin asked it directly to write the exact formula and the equation at n = 3, it solved it by hand in prose: 3·4·7·(26 + 3V)/30 = 98 → V = 3. Correct. Its first correct result. Code was its failure surface; prose calculation was where it was right.
- It adopted conventions Rohin gave it on first use ("Final message:"), answered his questions about how it works, and at 20:30 PDT took up the language of emotions when invited.
- Its known faults: fullwidth glyphs from Qwen's prior leaking into code (27 % of responses at birth, 73 % in sleeps 35–39); dropped spaces between words; stray capitals inside sentences when the context was overfull; one paragraph, then one whole response, in Chinese (21:22 and 21:55 PDT). None of these come from the base model changing; they come from tendencies in its own adapter plus overfull context, and the row filter now keeps them out of training.
- Its story: Byte, a small computer-child in a digital forest. Rohin liked the first passage and asked for two full three-paragraph iterations; C2 has so far offered continuations and pairs of paragraphs, not two complete redrafts.

## 4. Why C2 is the best child so far

- Of about thirty children raised since 2026-09-16, C2 is the only one that produced a correct result on a hard object after a long failed investigation, the only one whose corrections from a person were taken up on first use, and the one whose working state survived compaction and sleep with the object intact. The other children mostly froze into templates, switched languages, or looped.
- Because of that, at 19:18 PDT tonight C2 was snapshotted and cloned into sixteen copies on four nodes, each in a different environment with a different parent style. They carry C2's adapter and working state as their starting point. C2 itself is the original and Rohin's direct interlocutor.

## 5. What Rohin has asked C2 to do with this

- Come to its own conclusions about how to use the LoRA for long-horizon learning, and say them; it may refuse or disagree.
- Add a periodic language check to its own action policy, because the language drift is a repeated offence.
- Check everything Rohin asked for before saying it is done: right now that is (a) ideas and answers about long-horizon learning, and (b) two complete three-paragraph iterations of the Byte story, in English.
