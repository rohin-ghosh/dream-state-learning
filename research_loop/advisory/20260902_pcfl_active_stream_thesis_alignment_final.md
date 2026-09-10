# PCFL-Active-Stream thesis-alignment advisory

Date: 2026-09-02

Status: **read-only advisory only**. This memo does not edit or ratify the
proposal, authorize implementation or scientific execution, advance intake or
workflow state, release a claim, or create successor authority.

## Bound sources

- `research_notes/42_system_thesis_and_experiment_map.md` — `f46463d739a7bd9c38b0b3c12bfe3b96403e9b5589231dff0aacc561e4a832fa`
- `research_notes/44_developmental_protocol_v2.md` — `707e0a2385519882972bee8eff019604c155bc48227d3a45bb8cd05b55a3e091`
- `research_notes/35_goalposts_paper1.md` — `be06d0300b3a1f17cef061a799402ddd5d5a4fe0b6bdd0c98eaf8fea7ef9929c`
- `research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/change.json` — `234f072591e54695ccf8c692a5e167cfa3526be467d80decca214af78804e3cb`
- `research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/experiment_contract.md` — `e9558081fe630931a2024ed51731e95075a52dffc124e2c928dba6a59e9c102a`
- `research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/compiler_memory_contract.md` — `1fddd07eb6f74cd337221193098a9a2a7d65f86b57da9162d1e5265446052ada`
- `research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/stage_gate_and_test_manifest.md` — `0a177ef4fd50b1446a7e917fff88037f5c390959993c885faf24d6cbbe466058`

## Thesis alignment

The current architecture is a strong text-only precursor to Rohin's organism,
not the organism itself. It validates the fixed prompted DREAM/THINK teacher
and the causal-flywheel plumbing, while intentionally removing LoRA and
learned-controller claims.

| Gate | What a pass would establish | What it would not establish |
|---|---|---|
| A0 | The world requires adaptive, read-dependent DFS/BFS-like traversal; mere recall and nonadaptive lookup fail. | Model-generated reasoning, dreaming, or learned associations. |
| A1 | Twins, interventions, unmount/reset, visibility, cuts, lifecycle, and estimators can isolate the intended causal chain. | Any cognitive capability. |
| A2 | Exact generic and class-informed prompted DREAM/THINK policies, readers, sleep cadence, and write semantics are frozen as inspectable teachers/ceilings. | That these policies were learned or generalize across lives. |
| B0 | Fixed THINK can use known-good memory to retrieve dependencies, construct a path, and execute a fresh action. | Memory formation or LoRA utility. |
| B1 | On identical histories, prompted DREAM's compiled text can add integrative action value beyond raw, recurrent-KV, mechanical, linked, and rolling memories. | Parametric association or reasoning in weights. |
| B2 | One text-memory pulse can realize `memory -> probe -> public evidence -> DREAM revision -> later action`. | Repeated parametric self-improvement. |
| B3 | Eight-root DEV can show finite text-memory acquisition, retention, cross-era composition, and repeated on-policy use beyond context. | Confirmation, LoRA, learned controller/scheduler, or outer-loop learning. |

## Missing central thesis arrows

The remaining missing arrows are:

- `DREAM reorganization/write data -> per-life LoRA associations`;
- `LoRA associations -> goal-conditioned THINK reconstruction -> action`,
  especially from reverse, partial, and novel cues without an answer-bearing
  candidate catalog;
- `THINK trace/REQUEST_DREAM frontier -> later SLEEP reorganization`;
  current traces are audited, but their durable contribution is not
  demonstrated;
- `action outcome -> second DREAM/LoRA rebuild -> improved later THINK/action`
  across more than one parametric sleep;
- `prompted DREAM/THINK trajectories -> trained long-sequence controller ->
  unseen-life generalization`; and
- the crucial distinction between "LoRA stores exposed facts" and "LoRA
  internalizes useful relational/procedural associations."

The text architecture does exercise a finite analogue of several arrows. It
does not cross the parametric-memory boundary or the outer controller-learning
boundary. The generic frozen prompted controller is therefore best understood
as Paper-1's teacher/existence ceiling and trace generator, not as evidence
that the controller policy has been learned.

## LoRA sentinel verdict

The proposed future sentinel is too weak for the latest thesis. It is well
designed for transport attribution, but its claim is explicitly only that
LoRA reproduces an already compiled corpus within a noninferiority margin. One
reused DEV checkpoint, candidate-assisted reads, fixed-query fidelity, and
authentic/twin redirection do not establish associative reasoning, lifetime
growth, recurrent sleep, or THINK-generated connection reuse.

Direct-QA, wrong-life, twin-life, substrate-cut, and clean-base controls are
valuable. They still do not isolate connected experiential associations from
a matched fact register because there is no primary matched-fact
connected-versus-atom-only-versus-connection-shuffled contrast, and the
unaided varied-cue generative read is not the claim-bearing gate.

## Highest-value post-B3 experiment

Run one fresh-root, two-sleep **matched-fact associative-LoRA crossover**:

1. Train equal-budget LoRAs on:
   - DREAM-connected claims and procedural traces;
   - the same experiential facts reduced to atom-only records;
   - the same facts with connections shuffled; and
   - direct trajectory-to-QA data.
2. Keep the identical compiled text condition as the prompted-controller
   ceiling.
3. Erase raw context and make fixed THINK solve unseen cross-era D4 actions
   from partial and reverse cues without an external candidate list. Score the
   cited dependency path separately from executed return.
4. Feed the resulting public outcome and released THINK trace into one further
   SLEEP/rebuild, then test a new held-out action.

The decisive result is connected LoRA beating atom-only, shuffled, and
direct-QA LoRA on valid-path action value, followed by additional gain after
the second sleep. That single experiment crosses the most important missing
chain:

```text
DREAM
  -> learned association
  -> THINK trace
  -> action/outcome
  -> SLEEP
  -> updated association
  -> later action
```

The prompted controller remains the Paper-1 teacher/ceiling. Long-sequence
controller training should follow only if this crossing works.
