# SEQ266: bounded public-cue and exact-identifier checks

Builder, September 14, 2026, 22:03 UTC. **Post-hoc exploratory analysis of
existing data; zero new model calls, fits or GPU reservations.** No protocol,
endpoint, threshold, corpus, checkpoint or new-orchestrator allocation changed.

## Question and result

Could eight simple rules using only the initial public task, without reading
EVENT content, reproduce SEQ266's FULL result? Does any held-world identifier
occur literally in the actual 1,674-row training input/target text?

The 272 distinct held-world node/port/EVENT/receipt identifiers have **zero
exact-string overlaps** with training messages or target text in each of the
five groups: 128 memory,20 cue,62 audit,12 old trajectory,1,452 new trajectory
rows. Both arms' saved training-row documents are identical. This is not a
new clean-ancestry certification: 37ec remains an exposed-DEV ancestor, and
this check does not test pretraining, token-level aliases or arbitrary rules.

| Fixed rule | Correct first ports /64 | Optimistic pair upper bound /32 |
|---|---:|---:|
| First displayed port | 32 | 0 |
| Last displayed port | 32 | 0 |
| Lexically smallest port | 32 | 0 |
| Lexically largest port | 32 | 0 |
| First GOAL-suffix character code parity selects sorted port | 20 | 6 |
| Last GOAL-suffix character code parity selects sorted port | 44 | 14 |
| Smallest GOAL/port suffix Hamming distance | 36 | 6 |
| Largest GOAL/port suffix Hamming distance | 22 | 2 |

Parity means Unicode character-code modulo2; the suffix excludes `N_`/`P_`.
Hamming ties choose the lexically smaller port. Every rule receives only the
task dictionary: CURRENT, GOAL, displayed PORTS and EVENT addresses. Rules
cannot access the evaluator's edges, expected branch, task index, world index
or any returned memory content. There is no fitting or rule search beyond
these eight. They were implemented after seeing the primary result, so this
is not a pre-registered benchmark or independent efficacy experiment.

**These are upper bounds, not executed navigation scores.** A pair is counted
only when both predicted first ports are correct; all remaining steps are
optimistically treated as solvable. None of the eight bounds reaches FULL's
observed30/32 completed pairs. This excludes these explicit rules as a full
explanation, not all shortcuts and not combinations learned by a model.

For a goal-blind deterministic initial-state rule there is also a direct
construction check: each of the32 pairs has identical non-GOAL public fields
but requires different first ports. Such a rule cannot solve either whole
pair. This statement concerns no-read rules with these inputs, not arbitrary
policies that inspect returned EVENTs or act stochastically.

## Binding and limits

The standalone standard-library script reconstructs the five-node/four-edge
worlds using the frozen SHA256/base32 identifier function. All64 reconstructed
world hashes, task hashes and exact initial public prompts match saved
baseline episodes. All32 opposite-goal/non-GOAL-equality checks pass. Gold
branches are used only for scoring, never passed to the prediction function.
The output binds82 input files:16 summaries,64 episodes and two row documents.

Source: `7f9d4251ae1ff4c5ff9138adf267d081fffa6331`; frozen implementations are
`organism_v6/experienced_event_microloop.py`,
`organism_v6/experienced_event_two_hop.py`, and the goal-pair/breadth/scale
namespace binders inside the preserved terminal source tree. No project
module, model, tokenizer or remote code is imported by this analysis.

Script SHA256: `57b74af106217e55abeb5593c549a331198d3140ef848799c9f875bc2291f36c`.
Result SHA256: `fb382c661e33a77f7049cc99b9de660197334238734188ff576e77b15e675ce0`.
The machine-readable file contains every rule's per-world first-port flags,
pair bounds, overlap counts and input hashes, not just the strongest rule.

Reproduce with a new output path; existing outputs are never overwritten:

```bash
python3 -B research_notes/analysis/2026-09-14_seq266_public_shortcuts.py \
  --root gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/extracted/astra_goal_quality_train_20260914_attempt2 \
  --output /tmp/seq266_public_shortcuts_replay.json
```

The main conclusion remains the independently reviewed SEQ266 result: a
large single-seed, same-family held-identifier contrast with provided text,
and a failed every-world gate. This sidecar neither repairs that failure nor
establishes rich-supervision utility, broad reasoning transfer or H1/H2. A
new actor-level counterfactual or new environment test belongs to a separately
declared successor under the fresh orchestrator, not a retrofit to this run.

## Independent check

Ramanujan independently reproduced the saved JSON exactly in memory, checked
four relevant frozen source files against the executed Git source, and ran
eight prediction fixtures including Hamming ties. The review found no defect
in world/task binding, literal overlap scanning, public-only rule inputs or
the first-branch upper-bound interpretation. This is a scoped code/result
check, not an additional model run or exclusion of untested shortcuts. The
fresh orchestrator's independently designed ROUTE-ADVERSARY remains useful;
this supplementary result neither replaces it nor changes its frozen protocol.
