# R125 continuous child — native v1

September 16, 2026. This is a new base-initialized continuous life, not a reset
of F1/F2/F4 or the earlier continual child. It implements the posted R124/R125
design within the frozen-base, LoRA-only, provenance and held-visibility
invariants. Experiment shell tools remain disabled pending real isolation.

## Prospective dispatch

- Wrapper: `ovx3`; physical GPU2, verified UUID in `RESOURCE_PROBE.md`.
- Node-local parent: `/localhome/local-rohing/orch_r125_continual_20260916_attempt1`.
- Immutable source: `source_v1`; control receipts: `control`; native life: `run1`.
- One frozen Qwen2.5-7B-Instruct plus fresh rank8 LoRA; sampler seed0.
- Context4096, segment512; two autonomous segments then one child-authored
  pre-sleep reflection. EOS does not stop the scheduler. Empty reflection is
  recorded as skipped compaction, never replaced with invented child text.
- Temperature0.7, top_p0.95, repetition penalty1.05, no-repeat16-gram.
- All new child rows:16 presentations; earlier child rows:1 per later sleep.
  Each optimizer update has own-row objective weight0.75 plus four broad-anchor
  family microbatches of0.0625 each. This is objective weight, not token fraction.
- `max_sleeps=null`: continuous life, not a finite smoke. Existing conservative
  wall September16 22:04 UTC; lease ends September17 04:04 UTC. No extension.
- No automatic replay after an uncertain request or sleep. Exact restart is
  accepted only at a saved-RNG sleep boundary. Committed unslept generation
  cannot silently restore an older RNG snapshot.

## Readouts and operator access

Sleep0 and every completed sleep dispatch the existing synthetic32 capability
panel, both LoRA-ON and genuinely disabled LoRA-OFF, greedy cap512, in a fresh
process on the same assigned GPU. The resident is temporarily CPU-offloaded;
its optimizer tensor devices and CPU/CUDA/Python RNG are restored afterward.
Readout outputs live only in `run1/readouts`, never history, inbox or sleep rows.
No parent or accumulated context is passed. Raw generated text is retained.
Readout failures are separately recorded and do not masquerade as complete
evaluations or prevent subsequent TRAIN generation. This fixed diagnostic is
not a broad benchmark or evidence of retained skill acquisition by itself.

Once the journal exists, use two terminals through the `ovx3` wrapper. The
source root must be on `PYTHONPATH` and the existing native venv Python used.

```
python -B -m gpu.orch_r125_stream_console --root /localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1 --follow
python -B -m gpu.orch_r125_stream_console --root /localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1
```

The second command accepts one labelled TRAIN parent message per input line;
`--text 'message'` publishes a single message instead. The child never waits
for the inbox. `--follow` reads only the immutable child RESPONSE records.
No held task, evaluator result or answer key belongs in the operator inbox.

## Validation and claims

Local integrated suite:191 tests and202 subtests passed. It covers history,
journal crash boundaries, exact token masking, presentation accounting,
compaction, console publication/following, fresh-readout separation, no-replay,
checkpoint corruption, lease/source/allocation and privileged admission bindings.
System Python lacks pytest; tests used the existing local test-dependency
directory. Staged tests and a fresh privileged admission still precede dispatch.
No GPU model call, optimizer update or retained-learning success is claimed here.

Exact prompts and source hashes are in `NATIVE_BUILD.json`; launch and native
evidence will be published separately. Raw model/checkpoint/call files remain
on the node, not in this repository. ovx3 GPU7's FINAL and same-life resumption
reservation is unchanged; no experiment GPU access is enabled by this launch.
