# Long-lifetime writer wiring audit v1

Date: 2026-09-09

Status: source-only evidence correction. No code, architecture, protocol,
artifact, model, process, or resource was changed or executed. This audit
authorizes no repair or scientific claim.

## Verdict

The repository contains a newer native/chat-masked compiler and trainer, but
the only long-lifetime runner is still wired to the legacy bare-text writer.
The long-lifetime canary can prevent a rejected adapter from becoming the
active head, but its corpus is still eligible for the next cumulative build.
Therefore neither "new writer deployed in long lives" nor "rollback removes a
bad sleep from future learning" is true from the current local source.

## Exact source path

`organism_v6/run_life_v2.py`:

- line 18 imports `compile_sleep`, not `compile_native`;
- line 78 defaults to rank 16;
- lines 203--211 load the most recent prior `corpus.json` regardless of that
  sleep's adapter verdict and call `compile_sleep`;
- lines 228--233 execute `organism_v6.train_adapter`, not
  `organism_v6.train_adapter_v21`;
- lines 237--258 stage a candidate and rename its marker to `DONE`,
  `REJECTED_CANARY`, `REJECTED_SCORE`, or `REJECTED_BREVITY`; and
- line 259 reloads `latest_adapter`, which protects the active adapter head but
  does not remove or quarantine the rejected sleep's corpus.

`organism_v6/train_adapter.py` explicitly identifies itself as the frozen V1
recipe (lines 1--7): bare-text loss, learning rate `1e-4`, three epochs, and
rank-16 default. It trains on every nonpadding token (lines 50--62).

The newer components exist but are used elsewhere:

- `compile_native` is defined at `organism_v6/sleep_compile.py:177--213`;
- `train_adapter_v21.py` uses the chat template and response-only loss masking
  (`:1--10`, `:74--91`), a `3e-5`/two-epoch/rank-8 default (`:24--35`), and an
  explicit training seed (`:31--40`);
- `organism_v6/nursery.py:66--79` connects `compile_native` to
  `train_adapter_v21`; and
- `organism_v6/classroom_round.py:307--311` invokes
  `train_adapter_v21`, but its corpus construction is its own classroom path.

No `run_life_v3.py` or other long-lifetime runner appears under `organism_v6/`.

## Scientific consequences

1. Legacy v6.1 results remain correctly labeled old-writer diagnostics.
2. Any newer `run_life_v2` result must bind its exact launch arguments and
   source ancestry; source defaults alone cannot establish whether rank was
   overridden, but they do establish which compiler/trainer modules the runner
   calls.
3. A format/score/brevity canary is not writer certification. It can reject a
   candidate associated with immediate measured harm, but it neither proves
   causal memory transport nor prevents rejected corpus semantics from being
   replayed later.
4. Adapter rollback and evidence rollback are different operations. The latter
   needs an explicit eligibility/quarantine rule before the next cumulative
   clean-base build.
5. Nursery/write-swarm evidence for `train_adapter_v21` cannot be silently
   transferred to the lifetime system until the lifetime writer path is
   prospectively bound and independently reviewed.

## Required eventual repair properties, without choosing an implementation

A ratified successor long-lifetime path must bind:

- the exact compiler function and trainer module;
- response-mask and chat-render receipts;
- rank, dose, seed, cumulative-corpus identity, and immutable birth;
- a candidate-only staging state;
- separate decisions for adapter-head promotion and evidence/corpus promotion;
- quarantine of rejected candidate-derived corpus from future cumulative
  builds unless a separately grounded row remains independently eligible;
- atomic promotion/rollback with the prior life preserved; and
- an end-to-end source/launch/artifact receipt proving that the evaluated life
  used those exact bytes.

This is an E0 blocker, not a reason to patch the current runner ad hoc. The
replacement writer remains subject to the material-change path in `AGENTS.md`.
