# R179 — context survives sleep

Rohin163, relayed with label September17,2026 10:15PDT:

> okay, have the context worry connected to the first priority of behaviour learned through LoRA. This will basically make it a little less obvious to check if behaviour is learned, but luckily behaviour is not so obvious — perception and self-reflection, things of that nature, come in different forms — and if it is properly being learned then it will show in extraction, ideally. So yeah, make sure this step is happening on all steps right now.

Rohin164, relay label10:25PDT:

> you can also periodically test base behaviour by having a model copy run on a clean context and see the behaviour, which is a separate way to probe; I would not replace one probe with another.

Builder scope: prospective context-view policy on the24 existing learner lives in
the09:52PDT source census. Preserve own pre-sleep generations, masks, optimizer
recipe, exact saved state, sources, readout dispatches, measurement instruments,
device confinement and walls. No resets, repeated consumed requests, new agents,
retirements, new scientific claims, or additional evaluator budget. Deploy only
after author CPU/provenance checks and node-local exact-state admission.

Implementation choice: check the rendered visible prompt after the existing own
pre-sleep response; preserve it below75% of the context window; compact with that
response at/above75%, capped by the generation-reservation boundary. The only
current window is16,384 and generation reservation512, hence threshold12,288.
Existing no-distillation skips the pre-sleep response/compaction; leave that recipe
unchanged. Existing logged hard-window eviction remains the last-resort bound for
oversized inputs. Do not reconstruct omitted history or invented child thoughts.

Safe handoffs are prospective. Prior context already removed from the active view
is still archived, but this rollout does not silently reinsert it as a new input.
The first subsequent cycle begins accumulating history across sleeps.
