# Semantic60 exact GO handoff — no calls made

Ready generation: `semantic60_generation3/READINESS.json`.
All paths below are relative to this worker directory unless absolute.

| Artifact | SHA256 |
|---|---|
| `semantic60_generation3/PLAN.json` | `d53e6c53d537d363ce113952e8188e4716f44658ff5544680e07fac2671696c3` |
| `semantic60_generation3/CPU_GATE.json` | `508f182d4aa485ac82e6af0832b759fe52d62ed881d1459e25df3b887a23a3ff` |
| `semantic60_generation3/source/semantic_judge.py` | `2134b17fe9bb18ad3c6796be762305ce878f38a12890f09959f5725b7062ca61` |
| `semantic60_generation3/source/test_semantic_judge.py` | `6688ea73ac752d8163067083219ce80835253fb307b9735d623f3a97d15b1b6d` |
| `semantic60_generation3/SOURCE_PINS.json` (61 source files) | `2bfc419576b8818da82f32ca13f09ff121a4d6f0d57882da5ace2edcf06ec418` |
| Existing strong transport, unchanged frozen copy | `4d99658252310c7f57986750ff3002443d5c4038139f79b0381ff6eafbde837e` |
| Existing VM provider configuration, not copied | `6b3affde9e76a17e5331d4dbfdbe23ec6099d7d2416b229890f81c5ba1d0c85f` |

Actual frozen-source CPU15 tests PASS, plus configuration/key-presence validation
PASS with **zero provider/GPU calls**. Existing config's canonical target is
pinned; the transport still opens its original existing logical config path.
Earlier preparation failures are preserved in generations1/2; none dispatched.

## Exact execution scope

Fixed60 already-built opaque packets only; no newer sweep outputs added.
Backend: `gpu.orch_route_parent_campaign_providers.strong`, model
`openai/openai/gpt-6-astra`, explicitly `high` effort. At most60 calls, at most4096
provider output tokens each (245760 aggregate ceiling), at most2 concurrent
fresh stateless worker processes. Per-call wall alarm120s, outer worker155s
including private packet fetch; batch wall5400s with no last-minute admission.
No retries, no fallback, no new service, no credential copy, no tools and no
child/parent publication. `speak=true` is strictly the existing parser envelope;
the JSON annotation is private `rationale`, not an inbox/send action.

Each provider input contains only one exact packet and frozen rubric. No
mapping, condition/checkpoint labels, other answers, history, or lexical flags.
Annotation/evidence validation is fixed; malformed/timeout/uncertain outcomes
remain charged failures. Each packet has RESERVED and WORKER_ONCE; the controller
has a separate ONCE and cannot resume itself under a consumed GO.

All annotations freeze before a separate private condition/checkpoint join.
Partial fixed60 adjudication is not the full114-call sweep or a complete initial
baseline comparison. No score-dependent follow-up, selection, retry or stopping.

## Main GO file

`semantic60_generation3/MAIN_GO.template.json` is deliberately **not** a GO.
Main must create a new exact file with the following fields:

```json
{
  "schema": "R167_STATELESS_SEMANTIC60_V1",
  "status": "MAIN_SEMANTIC_EXECUTION_GO",
  "plan": {
    "path": "/data/home/rohing/dream-state-orch/research_loop/workers/r167_object_survival/semantic60_generation3/PLAN.json",
    "sha256": "d53e6c53d537d363ce113952e8188e4716f44658ff5544680e07fac2671696c3"
  },
  "calls": 60,
  "provider_model": "openai/openai/gpt-6-astra",
  "max_concurrent": 2,
  "no_retries": true
}
```

GO must preserve exclusion of both exact private roots from all ongoing parents
and repo_reader:

- VM scratch/logs: `/tmp/orch_r167_semantic_60_generation3_private`
- Node2 annotations/user-readable appendix:
  `/localhome/local-rohing/orch_r167_object_survival_20260917/private_appendices/semantic60_generation3`

Mode0700/0600 is not a same-account security boundary. Existing parent exclusion
is the visibility contract. No private packets or outputs enter the repo.

After the new exact GO, run frozen source `semantic_judge.py validate --plan
PLAN.json`, then exactly once `semantic_judge.py dispatch --plan PLAN.json --go
MAIN_GO.json` from its frozen source directory with that directory on PYTHONPATH,
under a5400-second outer timeout. Main receives only operational counts and
hash/path references to `ANNOTATION_FREEZE.json` and `APPENDIX.private.md`.

Current readiness is preparation only: **no execution GO consumed and no judge
request sent**. Prospective fleet work remains separate from these60 packets and
the existing retrospective114-call sweep.
