# Granular authored Level1 roster — 2026-09-13

Predeclared before any native fit in this roster. Implements Rohin messages34/35:
independent skill work, source diversity, stronger recipe, separate content and
format scoring, three learner seeds, then the smallest useful Level2 loop.
Existing contrastive and LR experiments retain their original frozen protocols.

## First independent roster

Four skills, each learner seeds0/1/2: contradiction, update_judgement,
prediction and goal_completion. Twelve immutable roots. Each uses96 distinct
authored source situations across four skins,48 held situations and12 canaries.
Source IDs, construction-family reuse, train/held separation, public evidence,
generator/templates/filtering, target proofs and costs are recorded. Distinct
constructed situations are not independent real-world task families. Fixed
material seed0 is shared across learner seeds; only fitting randomness changes.

- Contradiction: distinguish an explicit prediction from its matching verified
  outcome, including agreement, disagreement and missing/ambiguous evidence.
- Update judgement: accept or abstain based on whether a proposed record is
  supported by the selected public source, including unsupported negative cases.
- Prediction: use the supplied public belief card for a prospective action or
  abstain when evidence is missing/conflicting; not hidden-rule discovery.
- Goal completion: complete only when all stated requirements have matching
  verified public state; otherwise continue. Not autonomous goal creation.

These are standalone authored interfaces. Abstention labels do not alter the
production play grammar or insert teacher prose into child SLEEP. There is no
live parent or seeded prior child in these roots. Other requested skills remain
in the ready queue: stronger perception/self-reflection, repetition and
meta-reflection. Do not describe the first four as the whole curriculum.

## Recipe, persistence and controls

Frozen official Qwen2.5-7B-Instruct plus one fresh LoRA, rank8/alpha16/dropout.05,
LR3e-4, AdamW, batch4 distinct source rows, accumulation1,320optimizerupdates,
unpacked, full assistant target plus native EOS supervised, all context masked.
Use up to1024tokens with no truncation; actual token/padding costs are measured.
Fresh model and optimizer per learner; no shared mutable adapters or memories.

This is SEQ113-inspired, NOT a faithful replication: that result used an80-step
parent followed by320additional updates and mixed memory/arithmetic batches.
Here training starts from the base, on skill material, without unrelated replay.
Its success cannot be presumed from the earlier memory result.

Per root: OFF readout in one fresh engine, one fit, then saved-adapter post-fit
readout in another fresh engine; each engine handles held+canary60calls.120calls
and320updates/root; total1440calls/12fits/3840updates. No live prompt scaffold
or retrieval state carries between engines; task instructions remain present
in both arms. Baseline and post-fit use the same held inputs and inference
settings (temperature0, samplingseed0, max192tokens). Only training rows enter
fitting. All raw outputs close before collection/scoring.

OFF is the no-update mechanism control, sufficient for this authored skill
screen, NOT a matched non-parenting developmental control. Do not infer a
parenting treatment effect. Any later parenting claim needs its matched trained
control, actual child-generated material and parent removal.

## Metrics and decisions

Primary: typed source-correct CONTENT on the48held cases. Separately report raw
canonical FORMAT accuracy, JSON parse/schema errors, all field diagnostics and
itemwise OFF-correct canary regressions. Content parsing permits JSON whitespace
and key order, or one enclosing JSON/code fence only; never repair values,
types, keys, contradictions, extra prose or malformed objects. Truncation/error
fails content and format. Raw outputs and parser classification are preserved.
Plain arithmetic/copy canaries retain their declared exact output contracts.

Report each seed's OFF/post counts and paired wins/losses, then mean/range across
the three learners only when all three complete. Do not treat episodes, skins
or repeated rendering families as independent learner replicates. Failure is
missing, not accuracy zero; all attempts and changes remain visible.

A useful candidate needs a content improvement beyond mere formatting and an
explicitly reported preservation profile. No automatic broad pass threshold or
G1/P1/H1/H2/clean/freeze promotion. If OFF is near ceiling, mark that fixture
ceiling-limited and create a separately versioned harder source distribution;
do not select favorable post-fit cases. If weak, inspect source/model/recipe
links and choose a bounded repair, not an unchanged larger run or thesis verdict.
Select subsequent transfer data without tuning on these inspected held panels.

Once a relevant skill transfers, connect it to a simple Level2 experience ->
child material -> sleep -> reload check whose demands fit the demonstrated
skill. Use that result to refine Level1, not an unnecessarily elaborate loop.

## Runtime, placement and stop conditions

Per controller5400seconds inclusive, separate180second collection; stage caps
fit3600seconds/readout600seconds, owned cleanup reserved within controller.
Twelve-controller ceiling18GPU-hours, not predicted use. Profile actual fit,
startup, inference, serialization and query costs as the first roots execute.
Do not raise timeouts or shrink panels inside a frozen run.

Prospective A40 placement: six cells on node1 and six on node2, with no use of
node2GPU0 while the contrastive controller owns it. Exact index/UUID/seed/skill
roster, source/model/environment/protocol/plan hashes and launch identities are
frozen after native CPU preparation and before launch. A100 is not silently
substituted: runtime parity remains unexercised. Node1 finish cutoff is
September14 17:14UTC; preserve artifacts off-node by September13 23:14UTC.

Prelaunch checks combine all-process GPU occupancy, same-user CUDA reservations,
known controller ownership and queue state. New controllers retain their GPU
UUID in their environment during CPU phases. Never kill foreign processes or
controls for a treatment. Stop on integrity/provenance failure, nonfinite loss,
occupancy conflict, invalid metrics or finite budget exhaustion; preserve all
artifacts and use a new attempt only after diagnosis. Formal C11 guard remains
deferred to the final paper-grade run, per Rohin.
