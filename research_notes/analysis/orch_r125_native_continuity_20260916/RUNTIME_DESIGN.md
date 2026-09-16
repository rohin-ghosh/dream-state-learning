# R124 continuous-stream child: native integration plan

This design is posted before any runtime dispatch or changes to existing lives.
The earlier CPU prototype is not relabelled as a deployed child. Raw Messages
124 and 125 govern this implementation; SEAL retrieval is not a dependency.

## Loop

One frozen Qwen2.5-7B-Instruct base plus a fresh rank-8 LoRA, one persistent
AdamW optimizer, and an append-only TRAIN history. Generation boundaries do
not clear history. The scheduler keeps generating without a human `continue`
request; pending/absent parent messages never cause a blocking provider call.
Available human messages enter once at the next boundary through a node-local
inbox, with their own provenance and loss masked.

Before each sleep, a runtime-attributed open invitation asks the child to
distill the history it wants to retain. The actual generated reflection is a
TRAIN target and a bound, child-authored compaction, not a teacher-written
summary or a verified factual record. Raw history remains archived. The wake
context contains the compaction, later events and pinned birth context.
Default standing context permits reflection/metacognition between inputs and
accurately explains that only the LoRA changes at sleep; it promises neither
improvement nor general numerical adapter laws. No synthetic `Next:` text is
attributed to the child.

## Native learning and persistence

- Reuse the existing native frozen-base/LoRA loading and base-state hash checks.
- Preserve actual prefix/token IDs; all prior history, parents, runtime cost
  messages and environment text are masked. Only newly generated child tokens
  receive loss. No DEV/FINAL/readout data is read by this pipeline.
- New child rows receive 16 presentations, prior rows one rehearsal
  presentation per later sleep. Every optimizer update includes the existing
  verified broad base-anchor inventory at total objective weight 0.25;
  actual token exposures and optimizer steps are recorded, not inferred from
  sleep counts. This is a stated weighted-loss mixture, not a claim that
  exactly 25% of target tokens are anchors.
- Save adapter, AdamW and CPU/CUDA RNG together, and bind history/row frontiers
  to the same committed checkpoint. Resume the exact state, never initialize
  another optimizer for a continuing life. A durable unresolved request does
  not authorize redispatch.
- Run-local raw evidence stays on the GPU node. The repo receives only source,
  tests, manifests, hashes and reductions. The operator inbox and stream paths
  will be published after admission.

## Initial engineering proof and boundaries

First demonstrate real sequential generation, prior context in later native
inputs, sourced pre-sleep compaction, a changed LoRA with unchanged frozen base,
advanced AdamW state, and continued generation after sleep. This engineering
proof is not an outcome comparison or evidence of retained skill acquisition.
Subsequent fresh-process, parent/history-free capability and retention readouts
remain necessary for claims; no old score panel is imported into TRAIN.

Existing F1/F2/F4 lives and September 16 06:00 UTC FINAL reservations are not
modified or displaced. A free GPU must pass the existing privileged process,
device and CUDA-visible ownership checks before launch; candidate availability
is not allocation. Concrete source hashes, CPU tests, GPU identity and wall
will be posted separately before dispatch. A finite engineering smoke, if used,
will be labelled as such, not passed off as the requested long-running life.

No arbitrary shell access is enabled. Four-GPU child-selected experiments need
a separate enforced sandbox/resource binding; they are not prerequisites to
making the core continuous generation and sleep loop run. No new benchmark,
base model, thesis or visibility invariant is introduced. This is inside the
standing builder authorization; all scientific benefit remains unproven.
