# Swarm specification for closing level 1 → level 2 — DRAFT for Rohin's review (Fable, 2026-09-14 ~19:20 UTC)

Status: discussion material, not a ruling and not an instruction to the builder. Written in response to Rohin's
message 70 ("saturate the GPUs with sub-agents … hypotheses become sub-agents … planning is only an orchestration
layer … we run hard") and messages 65–69 (richness + scale as the content of level 1; gate = outcome ∧ richness;
Rohin → Fable → Astra channel). Raw words: research_notes/THESIS_RAW_ROHIN_2026-09-11.md, messages 65–70.

## 1. What is serialised today, and what is not

The builder already runs five workers (Nash, Parfit, Schrodinger, Ramanujan, Carson) plus Main. What is serialised
is not the thinking but the **admission path**: every GPU launch, CPU test gate, archive and hash step goes through
Main one at a time, and most arms are declared only after the previous arm's readout. Result on 2026-09-14: ~26
experiments of 100–1,632 updates, one or two GPUs at a time, three nodes idle for most of the night.

What must stay per arm (and is compatible with parallel admission): its own run root, source archive and hashes,
its own guardian, a pre-declared protocol with a matched control, a fresh-process readout, and the independent
reader's re-derivation. None of these requires the arms to wait for each other.

## 2. Roles

- **Orchestrator (Astra Main).** Plans only: maintains the hypothesis board, declares arms (one short protocol note
  each: rows, updates, control, readout, target), assigns GPUs, admits launches in batches, audits results as they
  land, retires arms, and re-reads Rohin's raw messages each cycle. Does not run experiments itself.
- **Hypothesis workers (one per arm; Codex sub-agents or headless model runs).** Each owns its GPUs for the arm's
  lifetime, runs collection → fit → readout end to end with its own guardian, writes one `[Worker <name>] SEQ-nnn`
  entry per result with the standard table, and posts a one-line status to the board every 30 minutes. Workers read
  the board before declaring follow-ups so they do not duplicate.
- **Independent reader (Fable on the VM, cron :15/:45).** Re-derives every result-bearing SEQ from raw receipts
  (already running; 33/33 verified, zero discrepancies). Builder never waits for it.
- **Watcher (Fable, laptop).** Relays Rohin's words verbatim, pre-registers a ledger row per arm before its readout,
  flags idle capacity and stalls each tick, audits data richness on samples, never launches.
- **Rohin.** Steers the orchestration layer: which hypotheses exist, what counts as success, what to retire.

## 3. Communication

- **The notebook** (research_loop/COORDINATION.md) stays the single channel: verbatim steers, protocol notes, result
  entries, reader verifications. Append-only, conflict-safe pulls.
- **A results board** (new file, research_loop/BOARD.md, rewritten by the orchestrator each cycle): one row per arm —
  hypothesis, worker, GPUs, state (declared / collecting / fitting / readout / verified / retired), last SEQ, held-probe
  pairs and goals vs baseline, retention, richness stats, next action. This is what Rohin reads.
- **Worker-to-worker:** through the board and short notebook notes only; no private channels, so the reader and the
  watcher see everything.

## 4. The hypothesis space (first wave — 24–28 GPUs, tonight) — ALLOCATION TABLE SUPERSEDED 19:5xZ, see the note under the table

Shared spine for every arm: the same 37ec child (or one declared successor), the same readout battery (held-probe
opposite-goal pairs and goals per world; deterministic first-port reference; unavailable-memory control; old 16 facts
W0/W8; held audit; original taught and fresh text), the same content rubric for "good behaviour" (outcome success
AND grounded content: names the record read, connects observed edges to the requested goal, states a checkable
expectation, then the command), matched loss-off controls, 16 presentations per trajectory target unless the arm is
about dose.

| axis | arms | GPUs (proposal) | what it decides |
|---|---|---|---|
| data form | terse (current contract) / rich single actor run hot / multi-agent rich (actor + critic + articulator; child tokens only as targets) / critique rows (grounded critiques of failed actions) | A100 0–3 (rich, running), A100 4–7 (multi-agent + critique) | whether richness moves held-world transfer at matched updates |
| breadth | 8 worlds (done: tie) / 64 worlds (scale corpus, 1,536 targets) | node 3 GPUs 0–7 (re-collection of 29 worlds, then fit) | whether identifier breadth alone moves transfer |
| scale | 1,632 updates (done) / 12,384 updates × 3 seeds | node 2 GPUs 0–5 | dose and seed spread at fixed corpus |
| environment | current route graph / one new gym with the same interface (different topology; e.g. longer chains or branching factor 3) / one text-only gym | node 2 GPUs 6–7 + node 3 spillover | whether the behaviour transfers across environments, not only identifiers |
| write→use loop | adult cycle on the best arm's child: parent-free experience → own records → one sleep → fresh parametric use, repeated over 3–4 sleeps vs a frozen twin | 2 GPUs when an arm shows transfer | the level-2 connection itself (slope vs the non-learning twin) |

Node 1 is excluded (lease ends 23:14 UTC). That is 24–28 GPUs in use tonight against 2–4 now.

**Update 19:5xZ (builder request, 19:53 entry):** the 1,536-target / 12,384-update scale cells and the "A100 4–7 / node 3 whole node" allocations above are superseded. Current BOARD reservations: A100 GPUs 0–3 = rich action-first V3 TEACH (Schrodinger); A100 GPUs 4–5 = self-critique vs repeat collection (Parfit); node 3 GPUs 0–2 = quality fit on the 1,452-target corpus (FULL / LOSS_OFF / BASELINE, Nash); node 1 no new work. The new orchestrator inherits these as running arms with an explicit boundary and allocates only the free GPUs (node 2 all 8; node 3 GPUs 3–7; A100 6–7) until they retire. Mined level-1 families stay out of the final level-2/3 tests; the existing graph readouts are exposed DEV diagnostics. The environment axis (content-bearing gyms: unit-tested code, checked-answer math) is the new orchestrator's first new branch.

## 5. Admission rules that keep it "very well"

1. No arm launches without a protocol note in the notebook (rows, updates, control, readout, success target) and a
   ledger row from the watcher — both committed before the readout.
2. Every fit has its matched control on a neighbouring GPU, started within the same admission batch.
3. The content rubric is applied to the shared source examples of every arm before any fit, so data selection cannot
   masquerade as a loss comparison (builder's own rule, 18:53Z).
4. Readouts are fresh-process, parent-free, on held worlds never used for teaching; the reader re-derives every
   headline count; nothing is promoted until it reads VERIFIED.
5. Retire an arm after one clean null at its declared scale; do not tune it. Spawn the next arm from the board, not
   from the last result alone.
6. Disk and packaging on /data, never on the VM root; each worker archives its own root when its arm retires.

## 6. What "level 1 → level 2 connected" will look like on the board

Level 1 (trained): a child whose rows were selected by outcome ∧ richness shows held-world transfer above the
first-port reference and above the loss-off control, with old facts and audits retained. Level 2 (learned): that
child, parent-free, runs collect → compile → sleep → use over several sleeps on fresh worlds and its held-world score
rises across sleeps while a frozen twin's does not (the slope, H2's shape). Both are readable on the same battery.

## 7. Open questions for Rohin

- How many hypothesis workers at once — one per arm (≈ 8–10 tonight) or fewer workers each owning several arms?
- Should new gyms be built tonight (costs a worker for 2–3 hours) or after the data-form result lands?
- Seeds now (he ruled seeds after success) — the 3-seed scale fit is "same corpus, dropout replication"; keep or drop?
- Does the board replace the [Builder -> Rohin] messages, or sit beside them?
