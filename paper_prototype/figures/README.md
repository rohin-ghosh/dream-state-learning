# Source-bound research figures

## SEQ266 transfer comparison — selected rendering: v3

Use `seq266_transfer_v3/seq266_transfer.pdf` for manuscript inclusion,
`seq266_transfer_v3/seq266_transfer.svg` for editable vector art, or
`seq266_transfer_v3/seq266_transfer.png` for preview. V1/V2 are retained layout
drafts, not separate experiments: their source tables are byte-identical toV3.
V3 prevents the15/16 label from overlapping the all-world threshold line or
extending outside its bar. No result, denominator or gate changed.

### Proposed caption — existing claim boundaries only

**Held-identifier, text-supported transfer in the one-seed SEQ266 DEV recipe.**
The full-target adapter reaches30/32 strict opposite-goal pairs and62/64
individual goals with actual stored EVENT text, versus1/32 and26/64 for the
matched new-target-loss-off control and2/32 and33/64 for the unchanged37ec
baseline. With stored text unavailable, all three states achieve0/32 pairs.
Full supervision covers15/16 worlds, failing the frozen requirement of at
least one successful pair in every world; all worlds and failures remain
included. Training uses1,452 new outcome-filtered terse targets, shared legacy
rehearsal,2,928 updates and FOUR trajectory presentations. Old W0/W8 and audit
are16/16 in each state; this does not imply identical retention on every other
panel. No error bars are shown because only one training seed was run. These
same-topology held-identifier results do not establish rich-supervision utility,
new parametric EVENT acquisition, repeated adult adaptation, clean ancestry,
or H1/H2. The preexisting invalid EVENT remains; no source repair or exclusion
is represented.

The canonical manuscript and abstract were NOT edited to include this figure.
Their owner decides placement and caption integration. A standalone figure PDF
was generated; no full TeX manuscript build is claimed.

### Sources and checks

- Original reduction:
  `gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/REDUCTION.json`.
- Original native root:
  `gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/extracted/astra_goal_quality_train_20260914_attempt2`.
- Independent result review:
  `research_notes/analysis/2026-09-14_goal_quality_fit_independent_result.md`.
- Renderer: `research_notes/analysis/render_seq266_figure.py`.

The renderer re-aggregates the reduction's saved PROBE taskwise entries by
state/condition/world, with fixed opposite-goal pairs(0,2)/(1,3), correct
source-distinct first ports and two committed transitions. It checks all18
count fields against the reduction, retains all16worlds/64goals/32pairs per
condition, checks the three named retention panels, and verifies both saved
training recipes' dose and seed. This is visualization consistency checking,
not another independent native model evaluation or whole-result certification.

`source_table.json` records the reduction/recipe hashes and source/protocol/
archive identities. `source_table.csv` contains the18 plotted/source counts.
Re-rendering from that committed table trusts it as the figure input; it does
not repeat raw-episode provenance verification. The original-source route is
available when the preserved reduction and native recipes are present.

Validation: all five V3 assets regenerate byte-identically in this installed
environment; existing output directories are rejected rather than overwritten.
SVG is well-formed and accessibility-labelled. The one-page PDF contains the
expected counts, four-presentation statement and failed-gate/one-seed labels.
The PNG was visually inspected. SVG/PNG/PDF layouts use the same primitive
coordinates; minor rounded-corner decoration differs between exporters.

### Reproduce without the large terminal archive

```bash
python3 research_notes/analysis/render_seq266_figure.py \
  --table paper_prototype/figures/seq266_transfer_v3/source_table.json \
  --output /tmp/seq266_figure_new_render
```

Use a new output directory. The script uses the already-installed Pillow and
ReportLab plus DejaVu Sans fonts; it does not import model libraries. CairoSVG
was initially tried but its native Cairo library is absent, so no environment
installation was made and the final exporter does not depend on Cairo.

### Re-derive the figure table from preserved source

```bash
python3 research_notes/analysis/render_seq266_figure.py \
  --reduction gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/REDUCTION.json \
  --native-root gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/extracted/astra_goal_quality_train_20260914_attempt2 \
  --output /tmp/seq266_figure_new_source_render
```
