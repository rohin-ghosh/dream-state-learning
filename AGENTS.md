# Research-agent operating contract

Standing authorization (Rohin Ghosh, 2026-09-12): the builder runs its own
experiments and the code that serves them on every leased GPU without
per-experiment ratification or independent review — see the last section,
which is the human ratification the path below ends in. The path below
governs only the reserved decisions and changes to the invariants named there.

Preserve the project-level thesis while changing implementation details. For
every material instruction from Rohin that changes the architecture, learning
loop, benchmark, information visibility, acceptance tests, or scientific
claims, use the durable architecture deliberation path before editing the
affected system:

```text
verbatim directive
  -> graph / loop / claim / visibility / test deltas
  -> at least two fresh-context independent interpretations
  -> adversarial cross-critique
  -> adjudicated consensus with every concern/disagreement/test disposed
  -> explicit human ratification of exact bytes and scope
  -> scoped implementation and tests
  -> fresh independent reviewer plus author-side scientific advocate
  -> GPU/scientific-claim gate
```

Use `research_loop/architecture_deliberation.py` and
`research_loop/architecture_intake.py`; every material supervisor workflow
must declare its approved intake and requested scope. Models can recommend,
pause, reject, or request rework. They cannot auto-ratify or infer human
authorization from agreement.

This gate does not block a non-material bug fix that preserves the frozen
architecture, benchmark, visibility contract, tests, and claim boundaries.
Label that work as a non-material repair, add a regression test, preserve
artifacts, and do not expand its scope into a design decision.

Never launch a GPU science run merely because CPU code or model consensus is
green. Satisfy the change's explicit pre-GPU tests and independent-review gate.
An author-side advocate may explain or repair a rejection, but cannot override
the independent review verdict; promotion requires a new bound approval over
the repaired evidence.

## Standing authorization for the builder (human ratification — Rohin Ghosh, 2026-09-12 05:45 UTC)

Rohin, raw: "give it more of tis own deisng let it sature all the gpus and plan
things out poerpaly and remove the stop forsure, it shoudl keep doing the fll
epxeimrting ill do my checks ints na ddi3c e to steer preidoricilly if needded".

This section is the "explicit human ratification of exact bytes and scope" the
path above ends in. It supersedes the itemised ratification of handoff §5/§5b
(05:15 UTC) and lifts the STOP in the notebook (~line 857). Nothing above it
requires the builder to pause before a launch inside this scope.

- Scope: the builder (Astra in Codex on the VM) designs, schedules, launches,
  monitors and stops its own experiments, and makes the code changes in
  `organism_v6/`, `gpu/` and `tests/` that serve them, on every GPU we lease
  (nodes 1-3, the A100 node, the second A40 node), with no per-experiment
  approval and no independent-review gate. Parented lives, preschool arms, the
  2×2 deployment, R6/R7 lineages and adapter-seeded children are inside the scope.
- Pre-GPU gate for this scope: the builder's own CPU tests and provenance
  checks, logged as a dated `[Builder]` line in `research_loop/COORDINATION.md`.
  "Never launch a GPU science run merely because CPU code or model consensus is
  green" applies to material changes outside this scope, not to the builder's
  experiments.
- Not material (no deliberation): any experiment or implementation choice that
  keeps the invariants in `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md`
  §15 — frozen Qwen2.5-7B-Instruct base with learning only in LoRA adapters;
  provenance and contamination rules; parents blind to sealed scores; controls
  with every claim; logging and evidence preservation; shared-node, lease-end
  and credential rules; H1/H2 as the spine.
- Material (deliberation path above, then Rohin ratifies): changing the
  scientific claims or the thesis; changing the base model; changing an
  invariant; anything sent outside the repo; leases, extensions and onboarding.
- Rohin steers in the notebook and his word wins. Watchers (Fable, Codex on the
  laptop) may recommend and push back but cannot pause a launch in this scope;
  a pending question goes in the notebook and never idles a GPU.
