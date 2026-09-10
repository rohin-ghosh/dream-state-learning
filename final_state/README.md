# Final state — organized view (started 2026-09-10)

This directory is the curated map of the project's final-stage artifacts. Nothing old is removed or moved; everything below links into the repository as it stands. Read in this order.

## 1. The claim and the paper
- `../research_notes/ONBOARDING_ABSTRACT.md` — one page: what the system is and what has been measured (revised after the harsh review).
- `../paper_fable/main.tex`, `../paper_fable/refs.bib`, `../paper_fable/README.md` — the ICLR 2027 draft (8.9 pp main text + appendices A–J), its number→source table (every number traced to a dated entry), and the auditor's brief. Abstract registration 2026-09-18; paper 2026-09-25.
- `../research_notes/REVIEW_HARSH_2026-09-10.md` — the harsh review of the notes and formalizations (5 fatal, 16 major) that reshaped the paper.
- `../research_notes/REVIEW_PAPER_FABLE_2026-09-10.md` — the harsh review of the revised paper; section 5 holds the abstract text proposed for 09-18 and the rules for replacing clauses as data lands.
- `../research_notes/PAPER_WRITING_PROMPT.md` — the one-shot prompt used to write and re-write the paper (rules, allowed/forbidden claims, reading order).

## 2. Evidence
- `../research_notes/EVIDENCE_TABLES.md` — every number a paper may use, with setup constants, noise bands and dated addenda.
- `../research_loop/COORDINATION.md` — the dated lab notebook shared by the two agents (Fable: machinery/measurement; Codex: protocol/audit). Entries SEQ-001… are the sequence-numbered recounts.
- `../research_notes/analysis/` — machine-readable analyses pulled from the nodes: per-life tables, noise estimates, per-program splits, ritual-in-weights, efficiency-over-cycles and markers.
- `../research_notes/certification_report_draft.md` — the writer's safety story including its own revision.
- `../research_notes/disjoint_panel_v1.json` — the 12 out-of-curriculum programs used to re-probe adapters the gate never selected on.

## 3. The system as run
- `../organism_v6/` — the organism: `run_life_v2.py` (life loop, probes, gates incl. the disjoint gate panel), `sleep_compile.py` (the write's compiler as run), `train_adapter.py` (v1, frozen for all lives) and `train_adapter_v21.py`, `parent_backend.py` and `parent_brief.py` (parents, leak scan, ritual detector, rehearsal), `classroom_round.py` (rule-game lineages), `bootstrap_corpus.py` (schooling corpora; DEV_UNVERIFIED_PROVENANCE), `probe_adapter.py` (panels, seeds, text-memory baseline), `analysis_tables.py`, `efficiency_markers.py`, `echo_null.py`, `absorption_probe.py`, `rulegame.py`, `rulegame_noise.py`, `cgym_eval.py`.
- `../organism_v6/DESIGN.md`, `bootstrap.txt` (birth prompt), `parent_prompt.txt`, `PARENTING_MENU.md`.
- `../gpu/` — node scripts (internal addresses live in an ignored `hosts.env`): `disjoint_reprobe.sh`, `brief_baseline.sh`, `launch_RP_lives.sh`, `launch_bootstrapped_life.sh`, `launch_parent_server.sh`.

## 4. Direction and design
- `../research_notes/IDEAS.md` — the idea log; entries dated 2026-09-07…10 carry the binding rulings (thinker/compiler line, repetition, no end token, state-to-state reasoning, two parallelisms, gyms that instil persistence, parents at agentic intelligence, thoughts carry the gain).
- `../research_notes/CURRICULUM_DRAFT_v1.md` — what to teach and in what order, with exit criteria.
- `../research_notes/NEXT_EXPERIMENT_DESIGN_v1.md` — the next experiment (written by the max-effort design workflow; folded with the curriculum and the agentic-parent direction).
- `../research_notes/related_work/tmem_positioning_2026-09-10.md` — TMEM as the shoulder we stand on and the stated delta; `../research_notes/related_work/` — reading notes.
- `../research_notes/NEXT_PAPER_POPULATIONS.md` — parked: collaborative populations, divergent agents, learning from people.

## 5. Data and provenance
- `MANIFEST.md` (this directory) — archives of raw receipts and adapters with SHA-256, where they live, and the node environments.
- Codex's STOP on unverified bootstraps: `../research_loop/COORDINATION.md` (entry "STOP: bootstrap-v3 is not yet an eligible clean child").

## 6. History (kept, not reorganized)
Everything under `../research_notes/` numbered 01–64, `../rml_stage_b/`, `../SPEC_V2.md`, `../DESIGN_SUPER.md`, `../REVIEW_PACK.md`, `../archive/` is the earlier architecture and planning era. It is the record of what was tried first; the paper cites it only for that.
