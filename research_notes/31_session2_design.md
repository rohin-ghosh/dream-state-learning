# Note 31 — Session-2 design doc (opened 2026-08-15)

## The what-matters taxonomy (what LTM must hold; each independently testable)
1. WORLD FACTS → planning without rediscovery → use-weighted retention +
   win rate (v1.1 test on leakage-engineered worlds, AP(credit→type) ≤ ~0.7).
2. NEGATIVE KNOWLEDGE (dead ends, failures) → exploration efficiency →
   repeat-failure/revisit rates. **Missing from the world's fact schema —
   highest-value addition. Worlds must EMIT failure facts + contain
   REPEATING TRAPS so retaining them pays.**
3. PROCEDURES/SKILLS (tool recipes) → faster execution → episode length on
   stored-how-to tasks (habitual-tier candidate).
4. EPISODIC ANCHORS → case-based reuse → second-encounter speedup on
   repeated goal families.
5. ATTEMPT HISTORY / SELF-KNOWLEDGE → progress/stall detection (the input
   for future goal-drift policy; policy stays frozen this session, but the
   environment logs attempts so the content exists).
6. GAP MAP (known unknowns) → directed exploration → S4 gap-aware read
   vs naive read (the S4 fix, now a measured arm).

## Design principles carried in
- One head, six content types: candidate-in-context input generalizes;
  dependency credit generalizes (avoided-trap = a dependent use).
- Each content type independently load-bearing (hint-decor trick × 5).
- Result = a HELP PROFILE per policy, not one number (better figure).
- v2 store: semantic-fingerprint card-box (read = one attention head over
  life); text payloads primary, o-vector ablation.
- Poverty regime: mem-hidden ≈ 32-tier pressure or slot-budget analog;
  calibration curves for the head alongside AUC; horizon-curriculum
  transfer curve; never-block read cadence; hysteresis in any arbitration.

## v2 store REVISED (Rohin's correction, 2026-08-15): net-first
Card-box was instrument-first design (v1's sin, milder). REVISED: the memory
is an ATTRACTOR NET — modern-Hopfield-style pattern pool; similar patterns
converge into shared basins; retrieval = PATTERN COMPLETION ("recreate the
vibe"): project prompt-space state into memory space, dynamics converge,
completed pattern returns as the felt-attentioned vector to the prompt
engine. Sequences via hetero-associative CHAINING (each completion points to
the next pattern; long memories = chained short attractors). Importance =
PRESS DEPTH (felt scalar = write strength = basin depth; no stored dials);
dream = basin-landscape maintenance (re-press what mattered, let junk
flatten). Theory on our side: modern Hopfield ≡ transformer attention
(Ramsauer et al.) — the net read and attention-read are the same operation;
capacity exponential in dimension (the 100M-1B-token scale argument).
CARD-BOX DEMOTED TO INSTRUMENTATION: an external logging shadow used only to
build probes (cue-in, completion-quality-out). Design order corrected:
memory for the system; instruments around the memory.
Honest costs (work items): vector→prompt-engine translation training;
probe machinery for BLENDED memories (prototypes).
