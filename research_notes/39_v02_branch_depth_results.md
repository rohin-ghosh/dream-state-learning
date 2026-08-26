# 39 — Semantic World v0.2 verifier-free depth result

Date: 2026-08-26. Branch: `semantic-world-v02`.

## Headline

The repaired D3 diagnostic is solvable by a verifier-free frozen-model system
when thinking is factored into inspectable atomic branches and recurrent
compression. With Qwen2.5-32B-Instruct, the system discovers the exact hidden
parent set in 35/36 targets across aligned seeds 0-2. On the two untouched
replication seeds, the frozen finishing protocol reaches 23/24 final answers
(.958) against a 1/12 (.083) per-seed floor.

This is a **prompt/controller ceiling**, not yet the parametric-memory result.
The system exhaustively enumerates every public source subset, uses 114 atomic
model checks per target, and keeps operator/parent/role memories in text. No
FactorSolver result, hidden role, parent set, answer, or offline verdict enters
the loop. Hidden state is used only after outputs commit for scoring.

## Game and control gates

V0.2 passes 1,000/1,000 CPU identifiability audits with 1,000 unique world
fingerprints. The true generator uses 2-5 parents, while the audit and model
controller conservatively search sizes 2-6 so the maximum is not leaked. On
aligned seed 0:

| clean-model condition | accuracy | floor |
|---|---:|---:|
| complete lifetime, direct | .000 | .083 |
| complete lifetime, one generic scaffold | .000 | .083 |
| oracle-resolved operator/parents/source recipes | .750 | .083 |

The oracle failures are clean-composer arithmetic/label-read errors. They set a
.75 generative composition ceiling; they are not memory failures.

Two monolithic recurrent attempts also failed:

| model | answer | exact parents |
|---|---:|---:|
| 7B | .000 | .000 |
| 32B | .083 | .000 |

Their traces explain why. A long dream collapsed a role into one color, applied
the blend across animals rather than within a role, assumed all targets copied
the demonstrations' two-parent count, or reused the query animal's role-
identification lands as target parents. Repetition then deepened the malformed
memory instead of repairing it.

## Working loop

The successful controller is an explicit tree of model thoughts:

```text
public demonstration episodes
  -> operator dream (finite SUM/UNION/COPY/OTHER recognition)
  -> canonical public cell reads
  -> enumerate all 57 source subsets of sizes 2-6
  -> for each subset, one LLM proof leaf per observed target role
  -> mechanically AND the two self-verdicts
  -> revisit/compress surviving branch thoughts into PARENTS memory
  -> three atomic same-land role checks for the query animal
  -> retrieve only the selected role row at the dreamed parents
  -> model componentwise recipe ledger
  -> lossless lookup in the public workshop dictionary
```

The controller enumerates and routes evidence but never calculates whether a
candidate is true. The model performs each sum and emits MATCH/MISMATCH. The
exact label lookup is a public-memory read, not a verifier. Every prompt,
branch, verdict, parent memory, read plan, and arithmetic trace is preserved.

The iterations themselves yielded a useful defect ladder:

1. free-form world memory lost role structure;
2. global target search conflated role evidence with parent evidence;
3. free generation corrupted exact workshop and cell reads;
4. episode flattening made the operator dream sum unrelated lands;
5. two-role branch thoughts swapped animals or omitted a source;
6. atomic role leaves fixed cross-role contamination;
7. final generation computed correct recipes but corrupted the label or final
   serialization, fixed by a component ledger plus public exact lookup.

## Scale result under the same atomic controller

Aligned seed 0, same 57-candidate search and same public evidence:

| dreamer/thinker | true-branch recall | exact parents | false MATCH branches | raw final |
|---|---:|---:|---:|---:|
| Qwen2.5-7B | .500 | .500 | 32 | .417 |
| Qwen2.5-32B | 1.000 | 1.000 | 5 | .750 |

Scale improves both sensitivity and specificity: the larger model accepts all
true paths while accepting fewer false paths. This effect did not appear under
the monolithic recurrent prompt; model scale becomes useful only after the
state and proof leaves are made legible.

## 32B seed results

| seed | status | true branch | exact parents | false matches | raw final | atomic role | first recipe | ledger final |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | development | 1.000 | 1.000 | 5 | .750 | 1.000 | .750 | .833 artifact; 1.000 post-hoc parser diagnostic |
| 1 | untouched | 1.000 | 1.000 | 0 | .833 | 1.000 | .917 | **1.000** |
| 2 | untouched | .917 | .917 | 30 | .833 | 1.000 | .833 | **.917** |

Untouched aggregate: exact parents 23/24 (.958), roles 24/24 (1.000), and
final answers 23/24 (.958). Seed 2's single final failure is the same target
whose true branch was rejected; the downstream system correctly cannot recover
a parent memory it never formed. Seed 2's 30 false matches are concentrated in
three targets; the revisit step still selects the true parent in two of them.

Seed 0 is explicitly not a holdout. The component-ledger decoder was developed
after inspecting its two serialization failures. It was frozen before seeds 1
and 2. The post-hoc seed-0 1.000 diagnostic is therefore not pooled with the
replication statistic.

## Artifact locations

The full prompt/trace artifacts are intentionally not committed because each
branch file contains all 1,368 atomic traces (12 targets x 57 subsets x 2
roles). They are on the H100 at:

```text
/localhome/local-rohing/dream-state/alchemy/v2_out/
  lands_v02_branch_all_aligned_s{0,1,2}_qwen-qwen2-5-32b-instruct.json
  lands_v02_finish_aligned_s{0,1,2}_qwen-qwen2-5-32b-instruct.json
  lands_v02_recipe_recheck_aligned_s{0,1,2}_qwen-qwen2-5-32b-instruct.json
  lands_v02_branch_all_aligned_s0_qwen-qwen2-5-7b-instruct.json
  lands_v02_{direct,scaffolded,oracle-resolved}_aligned_s0.json
```

The branch, finish, and recheck files include prompts, raw generations, parsed
memories, offline labels, and per-target scores. Copy or archive them before
releasing the GPU lease.

## What this establishes

- Corrected Blendyland is identifiable and model-solvable; v0's failure was not
  evidence against higher-order dreaming.
- Higher-order structure can be produced without an exact in-loop verifier:
  operator memory -> branch memories -> parent memory -> role read -> unseen
  consequence.
- The user's tree-growth intuition is operational: reliable depth came from
  revisiting many local memory states and extending them one proof leaf at a
  time, not from one very long chain.
- Dreamer/thinker scale has a measured effect once state representation and
  reads are sound.
- Recognition/canonical reads remain part of the intelligence. Free generation
  corrupts exact memories even when the reasoning trace contains the answer.

## What this does not establish

- It is not efficient or amortized dreaming. Exhaustive 57x2 branching is a
  ceiling and a data generator for a future learned proposal/controller policy.
- It does not yet place the operator/parent memories in LoRA weights. The
  v0.2 context-vs-LoRA comparison remains to be run at a matched read plan.
- It uses an aligned semantic skin only. Neutral/conflicting skins and more
  world seeds remain required. The current canonical source-cell read assigns
  conventional recipes to aligned color words; applying it unchanged to other
  skins would leak the latent recipe gauge. Those skins require a separately
  scored model-dreamed gauge from public demos and calibration mixtures.
- Canonical cell formatting, lexical retrieval, branch enumeration, logical
  AND, and public dictionary lookup are disclosed controller/tool operations.
- It does not validate Action World. Action remains parked until this memory
  path survives substrate transport and prompt/controller ablation.

## Next experiments, in order

1. Run the prepared `alchemy/run_lands_v02_topk.py` on untouched aligned seed 3.
   It dreams one ranked frontier, atomically checks only those candidates, and
   reports success@1/2/4/8/12 with exact model-call/token accounting against the
   exhaustive 57-candidate ceiling.
2. If the proposal frontier fails, diagnose on development seed 0 and refreeze;
   do not prompt-tune on seed 3.
3. Ablate canonical reads, atomic-role factoring, revisit, and ledger decoding
   one at a time. Keep the degradation curve as a result.
4. Run aligned seeds 3-5. Before neutral/conflicting fan-out, add and score a
   model-dreamed ordinary-token recipe gauge; never derive it from `Skin.colors`.
   Report false-match concentration, not only accuracy.
5. Emit the accepted operator/parent/role memories into the canonical QA
   grammar. Compare context+recognition and LoRA+recognition with the same read
   plan. Only then sweep memory horizon beyond context.
6. Extend the top-k baseline into model-written next questions / adaptive
   branch expansion, preserving provisional states and recovery from false
   memories.
7. Move to Action World only after the v0.2 memory transport and compression
   gates pass.
