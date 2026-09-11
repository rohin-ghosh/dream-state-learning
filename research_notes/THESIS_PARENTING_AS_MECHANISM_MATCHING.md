# Thesis: parenting teaches the child to think in the form the write can store

Ruled by Rohin, 2026-09-11 (evening), after the completion-frame results (SEQ-038 to SEQ-042). Foundational for the paper. Supersedes any earlier framing in which the sleep/compile machinery is the contribution.

## 0. One screen

- **Parenting is teaching the model how to think: perceive, reflect, judge, plan, execute.** Remembering is one of those skills. The skill is *perceiving well enough that the memory gets written* — the child's thought output is its own training data.
- **The write/read mechanism is not our innovation and should not be a heavy lift.** Physics of Language Models (Allen-Zhu & Li: knowledge is extractable only when it was seen in many forms and many times) and TMEM (self-written canonical pairs absorbed into fast LoRA weights) already show how facts get into weights and out again. Our form differs — bare canonical frames from the child's own perceptions, retrieved by completing the sentence, repeated — but we are not reinventing storage. We adopt it.
- **We already know the write works for behaviour** (the lineage's routine went into the weights and came out on unseen programs). **The car test with synthetic multi-perspective renderings (cell F) shows the same consolidated write works for memory**: sixteen renderings of an event per occurrence take completion of the planted fact from 0.23 to 0.66–0.97 and make it owner-specific, on fresh owners too (SEQ-039, SEQ-041, SEQ-042). What remains open on the mechanism side is narrow: abstention (a memory that knows what it has not observed) and the rank of the memory block.
- **Therefore the problem is on the thought side.** If the right thoughts are there, the write stores them. The research question becomes: can the child be taught to produce thoughts — perceptions, reflections, judgements, plans — whose *form* matches what the storing mechanism needs (many looks at one event, in a canonical shape, repeated, with "not observed" where nothing was seen)? Teaching that is parenting. **We are changing the model's behaviour so that its outputs match what strong training data looks like.** The child learns to author its own good training data.
- **Sleep and compile are infrastructure.** The work on them is done and is largely existing training engineering; it is not the core of this paper. The core is the thought portion and the teaching portion.

## 1. What this changes in the programme

1. **Order of proof.** First the experimenter writes the multiple perspectives on one memory synthetically, following Physics-of-LLMs and TMEM, and proves the consolidated write stores and retrieves them (done: cell F; abstention pending). Then the child is asked to write them itself, and the only question is whether child-authored perceptions store as well as synthetic ones. That gap — synthetic vs child-authored — is the measure of the perception skill, and closing it is the job of the parents.
2. **The bridge experiment ("child-authored frames").** Same planted events as the car test. Instead of templates, the frozen child (later: the taught child) is shown each event and asked to look at it several times and write what it notices, ending each look with the canonical sentence. Those renderings are the corpus. Compare to F_r16k16 on the same cues: completion, owner-specific contrast, spill, abstention. Variants: (a) the child writes the perceptions and the harness appends the canonical sentence; (b) the child writes the canonical sentence itself (the recall cue is part of the taught format); (c) the child also writes "not observed" for owners it has not met. Failure modes to measure: echo (the same sentence sixteen times), drift (perceptions that change the fact), missing canonical frame.
3. **Parenting content, restated.** The moves already ruled (decision, association, goal, building, rethinking/pruning, perception) are the list of thought forms; each has a storage form the write can consolidate. Parents teach the child to produce thoughts in those forms, by varied modes, never by enforcing a recipe. The thought-structure and perception instruments measure whether the forms appear unprompted.
4. **The paper's spine.** (i) Weights carry behaviour (measured). (ii) Weights carry memory when the writing is in the right form, and the right form is known from prior work (measured with synthetic renderings; abstention open). (iii) The child does not naturally produce that form (its notes are echo and recipe; SEQ-036: affect words are bootstrap echo; SEQ-003/005: reflective phrases rise while thinking narrows). (iv) Parenting is the attempt to teach the form; the bridge experiment is its first test. The lineage/final-test experiment is the destination, not the contribution of this paper.

## 2. Boundaries

- No claim that the mechanism is new. Cite Allen-Zhu & Li (Parts 3.1, 3.3) and TMEM for the storage regime; cite our completion-cue result as the retrieval route that fits an agent that controls its own cues.
- No claim about memory that has not passed the frozen gate; "canonical-cue associative recall" is the permitted wording for a pass (Astra q9).
- No claim about parenting until child-authored renderings are measured against synthetic ones.

## 3. Immediate consequences (2026-09-11)

- Build the bridge experiment (child-authored frames) as the next car-test representation; run it on the frozen child first (no parenting) to measure the raw perception skill, then with a perception-teaching prompt as the first parenting intervention at the mechanism level.
- Finish the mechanism side only where it blocks the bridge: exposure-parity abstention (running), memory-block rank (rank 32 running).
- Move sleep/compile work off the critical path except the interface canary and the leak scan.
- The canon's EVIDENCE table gets the bridge experiment as the measurement for claim (iv).
