# Prompt for Rohin to paste to Astra (q16, direct session)

Attach or paste `ASTRA_PACK_2026-09-12.md` (same folder) first, then this text.

---

You are a senior research collaborator. I am the project lead, prompting you directly this time; my agents (Fable, Codex) have been asking you questions as q10–q15, which are in the pack. The pack is everything you may rely on: my raw words (section 1, which win over every paraphrase), the thesis note, the brief with its status-tagged evidence ledger, the notebook result headers, your own earlier memos, the bibliography, and the open decisions. Do not fetch anything. Mark anything you cannot support from the pack or from literature you know with high confidence as "unverified", and never invent a number. Ideas first, numbers second; cite the pack section or notebook entry you rely on; say what you would do, not what could be done. Up to 5,000 words.

Deliverables, in this order:

A. APPLY THE LITERATURE TO OUR MECHANISMS. For each mechanism below, name the two to four most relevant prior results you are confident about (from the bibliography in section 6 or from memory, flagged), state what they predict for OUR setting specifically, and what they would change in our design or in how we describe it:
   1. memory written into a LoRA from many varied renderings of one event and retrieved by completing a canonical sentence (our bridge; Physics of Language Models 3.1/3.3, TMEM);
   2. behaviour written by whole-text training on the child's own successful thinking, three epochs, rank 8, refit from the frozen base at every sleep (our routine result; the write pretest);
   3. the child's own notes as training data: the two rituals, articulation zero, the post-outcome record slot, the articulation gate (self-generated data, model collapse, provenance, reflection / Reflexion-style verbal RL, ExpeL, Voyager-style skill libraries — what is genuinely different here and what is not);
   4. the parenting curriculum in levels (base with prompting → birth → preschool gyms → school → parent-free deployment) and the agent parent amortising a human teacher (curriculum learning, teacher–student and imitation, complementary learning systems, sleep consolidation);
   5. the final test: parented × sleep-running-vs-frozen on unseen tasks, slope not level (continual-learning evaluation practice; what the CLS and generative-replay literature says about our fresh-from-base refit and about plasticity by level);
   6. the node effect: byte-identical corpora and recipes giving 0.83 vs 0.45 completion on two machines (what is known about LoRA training nondeterminism across GPUs and its magnitude; what to check first).

B. REFACTOR THE PLAN FOR THE SIX DAYS LEFT (deadline: abstract 2026-09-18, paper 2026-09-25; 16 A40 GPUs on two machines, most busy for the next day). Given the ledger, say what to STOP, what to RUN and in what order with GPU-hours, and what the paper can honestly claim on the 18th under each of two outcomes of the preschool experiment (the child learns to write records / it does not). Resolve or take a position on each open decision in section 7, with the reason in one or two sentences each.

C. WHAT OUR OWN DATA ALREADY SHOWS THAT WE HAVE NOT NOTICED. Re-read the ledger and the SEQ headers as a sceptic: which results are stronger than we say, which are weaker, and which two analyses on data we already have would change a conclusion.

D. REFACTOR THE STORY. In my own framing (section 1), write the paper's spine in eight sentences, then the one paragraph that states the mechanism and the collapse defence together, then the two sentences that separate what is adopted from prior work from what is ours.

E. THE ONE THING WE ARE ABOUT TO GET WRONG, and the five questions you would ask me before I spend the next GPU-day.

Constraints from my side: no "nevers" on the child (recipes may be offered, never enforced; gates on the corpus are allowed); Codex's STOP on launching children seeded from unverified adapters is binding until I lift it; nothing may be pooled across the two machines until the node effect is resolved; the raw words in section 1 win where any note differs.
