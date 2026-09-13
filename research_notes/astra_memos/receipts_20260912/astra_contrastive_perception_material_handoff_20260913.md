# EDITSTOP — contrastive perception material, CPU only

2026-09-13 UTC. Implemented only the generator, matching tests, and this handoff
in `/tmp`. No repository changes, Git, network, tokenizer/model/native/GPU
execution, fitting, live-root writes, or outcome-dependent selection. Main's
six L2 LR runs and Lovelace's aggregation are outside this work. No launch is
performed or requested by these scripts.

## Final pins and reproducibility

- `/tmp/astra_contrastive_perception_material_20260913.py`
  SHA256 `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.
- `/tmp/test_astra_contrastive_perception_material_20260913.py`
  SHA256 `2f73b41a01f0d735e7568a511c3b332068cf1e2128fa2824181b6b80088875c9`.
- `/tmp/astra_contrastive_perception_material_handoff_20260913.md`
  is the third and last changed path; its hash is supplied separately to avoid
  a self-referential file digest.
- Deterministic build bytes: **232584 bytes**, canonical sorted-key compact
  UTF-8 JSON with one final newline. SHA256:
  `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`.
- Fixed template manifest SHA256:
  `811fb45ebb9737aa6fe98b68bf9bfeef2e738decdff3dcc567b2ccd0aac961a4`.
  Generator self-hash is embedded; no dates, PIDs, machine paths, output paths,
  model results, or runtime timing enter dataset bytes.

The accepted design is `/tmp/astra_contrastive_perception_next_20260913.md`
(`50e361ce54a3f7c91d77827b14cb6f427068c3c9f255bddebff428b2832cacc9`).
**Main's latest instruction supersedes its 16-renderer search, input-token
equality requirement, and references to matched input-token dose.** This
implementation has fixed literal templates, no renderer search and no exact
input-length matching gate. It implements an authored material hypothesis,
not guaranteed mechanism repair, child SLEEP, or a new L2 endpoint.

## Sources, generation, and exposure

Pinned read-only source loader checks both whole files before executing the
stdlib-only corpus; the corpus AST-extracts the existing public grammar rather
than importing the native diagnostic framework. No global monkeypatching.

- `organism_v6/birth_skill_corpus.py`:
  `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`.
  Reuse `build_slice`, `assess_source`, `_identify`, `_row`, `_interface`, and
  `score_response`; preserve original TRAIN targets/proofs/source objects.
- `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
  Existing `decode`, `judge_record`, `record_instruction`, and action parser;
  duplicate keys/nonfinite JSON/fences/schema violations receive no repair.
- Native reuse reference, **not imported or executed**:
  `research_notes/astra_memos/receipts_20260912/astra_perception_fit_run_20260913.py`,
  `f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`.
  Use `training_item`/`encode_training` through explicit arguments; these
  validate complete assistant target plus EOS and context/tail/padding masks.
- Native trainer reference, **not imported or executed**:
  `organism_v6/train_adapter_v3.py`,
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`.

TRAIN: exactly 12 selected original sources, two triples times six cases;
each has its unique same-triple/same-prediction/opposite-observation companion
from TRAIN. These are explicitly independent hypothetical boxes. Reciprocal
pairing means each original source appears once as selected and once as
companion in each arm. No extra selected source exposure in CONTRAST.

Both arms contain the exact same two raw source transcripts and eight labeled
field-value cells. PLAIN orders cells source-first; CONTRAST orders field-first
and asks attention to shared action/prediction versus opposing observations.
The cell multiset, occurrence counts, selected/companion identities, target
bytes/hashes, original selected proofs, group IDs, and initial row order match.
Arm names do not enter group/order IDs. No teacher note is a supervised target;
all note/transcript text is loss-masked context. Two training skins (ledger and
case cards) each carry the full six-case factorial, one original triple each.

D1/D2: 12 fresh cases rendered in two fixed unseen wrappers, 24 calls per
state, **not 24 independent situations**. Two fresh triples are
`(-10,21,-17)` and `(13,7,-19)`. Coordinates use canonical JSON SHA256 with
domain `heldout`, seed 2026091333, situation/coordinate/nonce, modulo61-30;
reject original TRAIN/DEV/earlier/duplicate triples, bounded 1000 nonces.
Outcomes remain authored PUBLIC_CASES, never inferred from a hidden rule.
Earlier event remains TRY20,21,22 with observation opposite the selected final
event. IDs and field proofs are recomputed; companion/note absent at evaluation.
Order seed 20260913 is arm-neutral. Derivations disclose exposed DEV ancestry
but selected triples/targets and held wrappers are fresh.

C-record: byte-identical existing exposed DEV12 rows; preservation canary only.
C-general: six deterministic integer additions and six exact copies, generated
with separately tagged hashes (`general-add`, `general-copy`), no training
exposure and no classroom/record vocabulary. Evidence and expected answers are
frozen before model outputs. No model judge. One taught competency only:
source-bound record discrimination; general tasks are no-harm canaries.

## CLI contract (Main's future fresh directory only)

The source root defaults to `/data/home/rohing/dream-state`. Optional
`--source-root /path/to/pinned/tree` precedes the subcommand. Source pins must
match even on a copied tree. Outputs use exclusive creation, refuse overwrite
and resolved paths inside the selected repository root; parent must exist.
Main must choose a fresh external experiment directory, never an old L2 root.

```sh
python3 -B /tmp/astra_contrastive_perception_material_20260913.py build --output /FRESH/material.json
python3 -B /tmp/astra_contrastive_perception_material_20260913.py score --dataset /FRESH/material.json --responses /FRESH/responses.json --output /FRESH/scores.json
```

Dataset partitions: `training.plain`, `training.contrastive`, each 12 rows;
`evaluation.D1`, `evaluation.D2`, `evaluation.C-record`, `evaluation.C-general`,
each 12 rows. **Never feed the entire dataset/manifest to a learner.** Only the
selected `training[arm]` rows reach its encoder. Evaluation target/proof fields
are evaluator-only, never prompt text or training material. Native visibility
enforcement is a future wrapper responsibility; this is not a launcher.

Responses are an object with exactly `OFF`, `plain`, `contrastive`, each a map
whose keys are `panel + "/" + row["row_id"]` from that evaluation panel.
Each value is exactly `{"raw": RAW_TEXT_OR_NULL, "finish_reason": REASON}`;
REASON is `stop`, `length`, or `error`. Preserve raw bytes as text, never strip
fences or whitespace. Map native truncation to `length` even when the partial
text happens to parse. Missing entries count as failures; unknown IDs, invalid
envelopes, duplicate JSON keys, and any dataset deviation from a fresh pinned
rebuild reject. No hidden scores or rules are generator arguments.

Scorer emits raw text/hash, strict pass using the existing grammar, separate
syntax/schema/completion/source errors, all four field-correct indicators
(null when malformed/unevaluable), panel totals, paired held wins/losses, and
itemwise OFF-to-CONTRAST canary regressions. General scoring recomputes integer
sum/copy expectation; normalized whitespace does not earn credit. A length or
error completion never passes. No generation is performed or substituted.

Predeclared exploratory screen: CONTRAST >=20/24 held, >=9/12 each skin,
>=4 improvement over each of PLAIN and OFF, and retain every OFF-correct canary
item. All outputs must be complete. OFF>=21/24 is ceiling-limited, not success.
Report field versus interface changes, not just this binary screening flag.

## Native preparation only; not performed here

Keep the base, target modules/dtype, optimizer and archived inference settings
unchanged. Both fresh authored fits: rank8/alpha16/dropout.05/LR1e-4/seed0,
batch4/gradaccum1/epochs4/maxlen1024/no packing. This is an existing recipe,
not proof that LR1e-4 fixes anything. Two fits =24 updates/96 row presentations;
OFF plus two fitted states times48 eval =144 calls, max192 output tokens each.
Same group ordering/seeded epoch orders must be checked across arms.

Main's explicit native preflight must verify the same supervised token-ID
vector including EOS per paired row, same target mask policy, no dropped,
split or truncated rows, and exactly12 updates each. Reject incompatibility;
do not rewrite targets, drop rows, search renderers, or tune against outcomes.
Record actual context tokens, padded tokens/compute/time and cost differences
per arm and row. **No input-length equality gate.** Current measured context
UTF-8 totals are PLAIN15900 versus CONTRAST16692 bytes (+792 total, +66/row);
all token counts remain null. Equal output-supervision contract is verified
at byte level only here; native tokenizer/mask verification remains undone.
Different context lengths may also change dropout RNG consumption; equal seed
is not a claim of identical stochastic trajectories or compute equivalence.

Do not repurpose archived launcher stages/grid constants, monkeypatch helpers,
resume old roots, alter active runs, or insert teacher text into child SLEEP.
Main alone chooses future wrapper/launch/timing and receipts; no implementation
of that wrapper is included. Authored success would remain Level0/1 material
evidence, not child-generated learning, general G1/H1/H2, mechanism proof, or
promotion of original L2 endpoints. Only two fresh triples and one learner seed
limit generality. If improvement is merely syntax, report interface practice.

## CPU validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p 'test_astra_contrastive_perception_material_20260913.py' -v
python3 -B /tmp/astra_contrastive_perception_material_20260913.py --help
sha256sum /tmp/astra_contrastive_perception_material_20260913.py /tmp/test_astra_contrastive_perception_material_20260913.py /tmp/astra_contrastive_perception_material_handoff_20260913.md
```

**20 tests PASS, 0.436s** on the final code/test bytes. Includes deterministic
rebuild and JSON roundtrip, no shared mutable manifest aliases, pair/fact/target
identity, exact exposed canary, fresh held relationships, native-token unknowns,
strict/field/type/duplicate/fence tests, truncation refusal, no-harm/ceiling and
missing-output behavior, tamper/pin/overwrite protection, and end-to-end CLI
build/score with synthetic responses in an automatically removed temporary
directory. Only CPU fixtures were produced; no real model outputs were read or
created. Dataset digest/size above were also measured in memory without saving
a deployment artifact. EDITSTOP: these three files are handed back to Main.
