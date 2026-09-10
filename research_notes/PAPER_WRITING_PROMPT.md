# One-shot prompt: write the ICLR 2027 first draft of "Experience Models"

Copy everything below the line into a fresh session of a strong model with file access to this repository (`/Users/rohing/dream-state`). Do not paste this file into a session that has been working on the code; a fresh context reads the evidence without our habits.

---

You are writing the first full draft of an ICLR 2027 submission (abstract deadline Sep 18, paper Sep 25, 2026). Target: a 9-page main text in ICLR format plus appendices, delivered as `paper/main.tex` (ICLR 2027 style) with a compiled-clean structure, plus `paper/README.md` listing every number's source file. Write the whole paper; do not stop at an outline. Where a number is not in the evidence files, write "not measured" rather than inventing one.

## What the paper is about (use these words)
A frozen base model plus a small per-life adapter that converts lived experience into better future action. Three mechanisms, always in this order and this simplicity: **THINK** (the agent's loop: a stream of thought with markers PREDICT / ACT / NOTE / RECALL, recorded in an append-only ledger), **DREAM** (context management: notes persist, the rest fades, a brief written at sleep opens the next wake), **SLEEP** (the write: the agent's own successful continuations, paraphrased and replay-mixed, compiled every 32 episodes into a rank-8 LoRA from the clean base, committed only through gates). Then **PARENTING**: a stronger model that never gives answers watches the child and prescribes better thinking patterns when the child's thinking becomes repetitive; the child rehearses the lesson in its own words so it becomes its own thought, which is what sleep writes. Parent weights never learn; only the child's do.

Positioning: this is NOT "continual learning" (labs already do that) and NOT retrieval. Frame it on one axis with two neighbours: looped transformers recur in activations, chain-of-thought recurs in tokens, experience models recur in weights — expensive to write, persistent, and inspectable because the system dreams in text. The banner is prospective, action-oriented, experiential intelligence. "Memory" may be used as a reference term, not as the frame. One-sentence mechanism (use it): bootstrap teaches the habit of making and revising rules; parenting teaches when to use that habit; lived outcomes supply the evidence; sleep makes the child's own successful use persistent.

## Non-negotiable rules
1. Every empirical statement is a cell count or a measured mean with its noise band, taken from `research_notes/EVIDENCE_TABLES.md` or a dated entry in `research_loop/COORDINATION.md`. No narrativized mechanisms. If you infer a mechanism, label it "reading, held loosely" and give the falsifier.
2. Report what failed as plainly as what worked: late-life collapse under the format-only gate (3/9 lives), the storage–extraction gap (3 nats stored, ~+0.02 behaviour), parenting effect not established at n = 9 vs 8 lineages, ritual returning despite briefs, large one-shot writes harming.
3. Guardrails (canary, leak scan, gates, contamination rules) go in Methods and Appendix, never in the front matter.
4. Simple language. Explain "chunk", "probe", "paired ON−OFF", "ritual" in one plain sentence each on first use. Numbers must be understandable: say what 0.487 means (programs shrink 48.7%).
5. Do not name or imply any internal infrastructure (hostnames, IPs, node names, lease systems). Anonymize authors for review. Include an AI-use disclosure paragraph (code and drafting assisted by Claude and Codex; all numbers from logged runs; humans responsible for claims).
6. The held-out probe programs are a sealed split; say so, and say the `_canon` fix for the URI-prefix leak.
7. Claims you may make: the write changes behaviour; gated writes are safe (0 harmful in gated pairs so far); small frequent writes beat large one-shot writes; children rehearse parental lessons in context; parented children have not collapsed; ritual onset is measurable and consistent. Claims you may NOT make: that parenting improves scores (not established), that the adapter stores "knowledge" the agent can use (storage ≠ extraction), anything about a 7-day child (not yet run), anything about transfer beyond the gym's held-out programs.

## How to read the repository (in this order)
1. `research_notes/ONBOARDING_ABSTRACT.md` — one page: the whole thing.
2. `research_notes/EVIDENCE_TABLES.md` — every number you may use, with setup constants.
3. `research_loop/COORDINATION.md` — the dated lab notebook between the two agents (Fable = machinery/measurements, Codex = protocol/audits). Read the entries from 2026-09-07 onward; each result appears with its cell counts and caveats. Where EVIDENCE_TABLES and COORDINATION disagree, COORDINATION's later entry wins; note the discrepancy in `paper/README.md`.
4. `research_notes/certification_report_draft.md` — the safety story of the writer, including its own revision (what the first draft claimed, what late-life data showed, the gate that followed).
5. `research_notes/IDEAS.md` — the idea log. Use the entries marked RULED / DIRECTION / MECHANISM SENTENCE / DIAGNOSIS for framing and the Discussion; do not turn ALIVE ideas into claims. The entries from 2026-09-07 to 09-11 carry the design rulings (thinker/compiler line, repetition, no end token, state-to-state reasoning, two parallelisms, bootstrap pipeline).
6. `research_notes/related_work/` — reading notes (sleep consolidation, Zahavy 2026, Allen-Zhu & Li 2309.14316). Cite from these; do not invent citations. Where a citation is needed and absent, write `\cite{TODO-<topic>}` and list it in README.
7. `organism_v6/DESIGN.md`, `organism_v6/bootstrap.txt` (the agent's birth prompt), `organism_v6/parent_prompt.txt` (the parent's rules), `organism_v6/PARENTING_MENU.md` — for the Methods text. Code you may describe from: `run_life_v2.py` (life loop, probes, gates), `sleep_compile.py` (compile_native, canonicalize_dialect), `train_adapter.py` (v1 frozen) and `train_adapter_v21.py`, `classroom_round.py` (lineages), `parent_backend.py` and `parent_brief.py` (parent, leak scan, ritual detector, rehearsal), `bootstrap_corpus.py` (schooling corpus), `absorption_probe.py`, `rulegame.py`, `rulegame_noise.py`.
8. Older material (`rml_stage_b/`, `research_notes/3x_…`, `4x_…`, `5x_…`, `SPEC_V2.md`, `DESIGN_SUPER.md`) is the prior architecture and planning era. Use it only for the "what we tried first" paragraph if at all; it is not the system being reported.

## Required structure (9 pages main text)
1. Abstract (≤ 200 words; the one-sentence claim, the three mechanisms, the two headline cell counts, the honest limit).
2. Introduction: the axis (activations / tokens / weights); what "experience model" means; contributions as a numbered list of measured things.
3. The system: THINK, DREAM, SLEEP, PARENTING, each with one figure-worthy schematic described in text (figures may be TODO placeholders with exact captions).
4. Measurement design: sealed probes, paired ON/OFF, noise bands, cell counts, the certification bar (absorption, retention, interface, no-harm), contamination rules, why the classroom exam needed 40 episodes.
5. Results: (a) the writer: recipe, rank × dose, small-frequent vs large-once; (b) safety: ungated late-life collapse vs gated; (c) storage vs extraction; (d) parenting: rehearsal, ritual onset, lineage tallies, what did not separate; (e) bootstrap corpora (composition and ritual check; adapters "in training" if still not measured).
6. Discussion: the sleep-as-amplifier reading; why repetition; why the thinker/compiler line; state-to-state reasoning as the target; what a 7-day child would need; limitations (n, one gym, one base model, seed variance, nondeterminism).
7. Related work (short; the axis, sleep consolidation, knowledge extractability, continual learning as a contrast).
8. Reproducibility and AI-use statements.
Appendices: prompts (birth prompt, parent prompt, brief prompts v1–v3 with the reason each changed), gate definitions and thresholds, ritual metric definitions, full per-life tables, the classroom lineage table, corpus compositions, infra notes without identifiers.

## Deliverables and checks
- `paper/main.tex` (complete, compiles with the ICLR 2027 style; use `\usepackage{iclr2027_conference}` with a TODO if the style file is absent), `paper/refs.bib` (only real, verifiable references; TODO markers otherwise), `paper/README.md` (a table: every number in the paper → its source file and dated entry).
- Before finishing, re-read the paper against rule 7 and remove or soften any claim that exceeds the evidence. Then write a 10-line "auditor's brief" at the end of README listing the five claims most at risk, so a second model can attack them.
