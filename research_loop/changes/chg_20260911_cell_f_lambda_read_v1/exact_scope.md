# Cell F lower-strength read — exact scout scope v1

**Change ID:** `chg_20260911_cell_f_lambda_read_v1`  
**State:** parked, non-executable draft; no execution authority.  
**Purpose:** decide whether an already-trained Cell F recipe passes the
lower-strength Cell F screen and may be proposed for a separately approved
F-Relay, or whether Cell F stops.

## Bound sources

- `organism_v6/memory_dose.py`:
  `db3222e61f0a8219bfc0f40f22ade532bb72bd3d83a299a02c25d65cebbbaf0e`
- `gpu/memory_dose_frames.sh`:
  `4117357b8b980bb8e3cf10f092e7fa50bf84082e6aed98c116dcee53681bda36`
- `research_notes/2026-09-11_mechanism_status_audit.md`:
  `ed87a023b0ed79df94d0a375e14810c1923e166f442509e7899b3a61a0819b33`
- `research_notes/2026-09-11_cell_f_next_action_advisory.md`:
  `99fb5755569d1fd8aaf213702164b4474dae6ea89a1b7a1b6dc35ff4cc622396`

## Exact operation

After the same-node bank-0/1/2 fits for `F_r16k1`, `F_r16k4`, and
`F_r16k16` are terminal, evaluate each existing rank-8 adapter at LoRA
strengths `0.25` and `0.5`. Strength `0` is the already-tested true adapter-off
reference and strength `1` is the already-completed full-strength read.

The operation loads existing adapters and performs inference only. It creates
no corpus, changes no model or adapter bytes, performs no training, opens no
new task data, and does not touch a child lineage. Each output uses a new
`__lambda_read_v1__lam{strength}.json` tag and must not replace an existing
artifact. Run only on the same node/runtime as the three-bank fits, with
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, seed `0`, batch size `16`, and
the existing `adjacent_subset=4`.

Before each read, require the adapter `DONE`, `train_meta.json`, corpus SHA,
items SHA, rank, target modules, training seed, and bank identity to match its
existing receipt. A mismatch or pre-existing output stops that cell; nothing
is repaired or overwritten.

## Fixed interpretation

For every `(K, strength)`, report every bank separately and all raw terms.
Banks reuse owner IDs under counterbalanced mappings, so `(bank, owner)` rows
must not be treated as independent. A candidate qualifies only if all of the
following hold in every bank:

1. dose-16 matching-owner `P_ON >= 0.80` and `ON-OFF >= +0.30`;
2. the existing owner-paired 95% interval for owner-versus-similar
   `I_d_frame` excludes zero on the positive side;
3. every dose-16 spill component—unexposed owner, similar owner, and
   bicycle/wrong relation—is `<= 0.03`;
4. every dose-16 owner's frame candidate mass ON is `>= 0.10` and at least
   half that same owner's OFF mass;
5. `dP1 <= dP4 <= dP16` and `dP16 - dP1 >= 0.10`; and
6. the mean matching-owner term and mean `I_d_frame` are positive.

When comparing strengths, spill may be credited only at a setting that still
meets the absolute owner-gain and mass rules; merely weakening all behavior is
not specificity.

If no candidate qualifies, Cell F stops for this sprint: no higher-exposure
`F_r64k16`, no F-Relay, and no factual-LoRA qualification. If one qualifies,
select the lowest K and then the lowest qualifying strength, but do not run
F-Relay without a separate exact approval. Passing this screen alone is not
usable-memory evidence: wrong-life, action-relay, retention, and untouched
confirmation remain absent. Either result remains exploratory until an
independent reviewer verifies identities, arithmetic, and raw outputs.

## Deliberation disposition

Three independent audits agreed that lower-strength inference is the only
cheap remaining rescue check and that failure must stop escalation. Their
resolved disagreement was whether to add shuffled writers, SVD truncation,
or four read interfaces. Those additions are rejected: they require new code
or training, create extra selection freedom, and cannot promote a writer that
fails the direct conjunction. No reviewer recommended rank escalation.

## Scope boundary

Approval authorizes only nine existing-adapter evaluation invocations (three
cells by three banks), producing eighteen new strength-specific JSON files,
their deterministic change-specific aggregation, and a read-only independent
review. The in-place `memory_dose report` command is forbidden because it
overwrites shared report artifacts. Aggregation must instead write under
`analysis/cell_f_lambda_read_v1/`, record every input path and SHA-256, use
the per-bank rules above without pooling owners across banks, and preserve all
raw outputs. It does not authorize training, higher-exposure `F_r64k16`,
F-Relay, new corpora, parenting, child/checkpoint changes, C11 work,
scientific claims, release, or submission. The full C11 guard remains parked
for the final paper-grade C11 run.

## Why this draft is parked

Independent execution review found that the same-node nine-adapter input set
is not yet bound by absolute paths and SHA-256 receipts, the existing evaluator
does not enforce the stated preflight checks atomically, and the required
change-specific non-overwriting aggregator does not yet exist. Building and
ratifying that machinery costs more deadline time than this optional rescue
read warrants. The full-strength Cell F family already fails the precommitted
specificity conjunction, so the current sprint stops factual-memory escalation
and spends its remaining mechanism effort on the process writer. This draft is
retained only as a possible later diagnostic; it must be completed, reviewed,
and explicitly ratified before any execution.
