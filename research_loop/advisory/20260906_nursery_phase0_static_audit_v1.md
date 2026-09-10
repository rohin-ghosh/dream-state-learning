# Nursery phase-0 static audit v1

Date: 2026-09-06  
Scope: read-only/static audit of `organism_v6/nursery.py`,
`sleep_compile.compile_native`, `train_adapter_v21.py`, the curriculum, and
the model backend. No model, tokenizer, training, behavioral, or GPU run was
executed. This note grants no architecture or run authority.

## Verdict

The inheritance scout is a useful implementation sketch, but it is not ready
for a scientifically interpretable GPU launch. Its current highest-risk bug
can silently create examples with zero supervised response tokens. Its current
evaluation can show lesson recall, but cannot show that parenting taught the
child to learn or think better on a target-blind task.

## What is genuinely present

- A target-generic twelve-document curriculum and rank-8 default.
- Native-stream collection: thought chunks containing `NOTE:` and winning
  continuations can become prompt/continuation training pairs.
- Chat-template training with response-only labels, rather than bare-text
  whole-sequence loss.
- Adapter-on versus adapter-off lesson questions.

These are worthwhile ingredients. They do not yet implement interactive
parenting: `parent_prompt.txt` has no runtime consumer, and the stated
`nursery_dialogue.py` phase does not exist.

## Blocking defects

### N00 — the child receives only the first 1,200 characters of each lesson

`nursery.py:72-80` inserts each complete curriculum document as one tail
element. `state.py:66-67` truncates every tail element to 1,200 characters
before rendering. The twelve lessons are 3,148–4,263 characters each, so the
child never sees most of any lesson even though the read marker records the
document as completed. Required repair: split readings into explicitly indexed,
overlapping chunks with a complete-coverage receipt, or place the active
reading in a separately budgeted immutable source region. Test reconstruction
of the exact source bytes from the chunks before launch.

### N01 — right truncation can erase every training target

`train_adapter_v21.py:65-70` tokenizes the full prompt and response, then
keeps `(prompt_ids + answer_ids)[:768]`. If the prompt alone is 768 tokens or
longer, every retained label is `-100`; the example contains zero supervised
tokens. `nursery.py:72` permits a 6,000-character reading inside a rendered
state prompt, and `batch_loop.py` records prompts as long as 24,000
characters. The native compiler can therefore hand the trainer precisely the
long examples most likely to lose their complete response.

Required preflight: compute and freeze prompt tokens, response tokens,
retained supervised tokens, and truncation side for every example; reject any
example with no retained target. Preserve the response and trim only the
oldest/reconstructible prompt region under an explicit state-layout rule.
Training must abort on non-finite loss.

### N02 — the assay measures recitation, not taught agency

`nursery.py:105-121` asks four direct questions whose answers are stated in
the curriculum. A positive adapter-on difference would establish parametric
recognition/paraphrase at most. It cannot establish better prediction,
surprise investigation, scoping, context reconciliation, or task learning.

Required gate: freeze unrelated nursery tasks before teaching; probe parent
absent under equal generated-token budgets; include regular, context-parent,
parented-LoRA, shuffled-feedback, wrong-child, and adapter-off arms. Lesson
recognition is an absorption sub-assay, not the primary endpoint.

### N03 — claimed contamination firewall is not executable

The code comment says the curriculum was verified by a curator grep, but no
byte manifest, forbidden-target vocabulary, semantic review receipt, or
train/evaluation intersection report is produced. Reading the whole repository
would be especially unsafe because it contains benchmark identifiers, pass
names, outcomes, probes, and post-hoc diagnoses.

Required gate: curate only general process laws; freeze every inherited byte;
exclude benchmark source/results/identifiers/actions; run lexical and semantic
leakage audits before task sampling. Preserve the full repository as parent
source material, not as direct child input.

### N04 — no reproducible dispatch or write receipt

`model_backend.py:24-39` does not pass a seed to `SamplingParams`, and its
`__call__` `seed` parameter is ignored. `train_adapter_v21.py` does not freeze
or record model/tokenizer revisions, source hashes, corpus hash, curriculum
hashes, RNG seeds, per-example target-token counts, loss trajectory, adapter
hash, or generic-behavior preservation results.

Required gate: exact dispatch/train receipts plus multiple seeded probe
replicates. A single stochastic on/off answer per question is descriptive
only.

### N05 — no interactive parent exists yet

Phase 0 asks the child to summarize static readings. It never gives feedback
on one child's actual prediction, action, outcome, or context-management
failure. Consequently it cannot answer the user's proposed parenting question:
whether correction tied to this child's life becomes a durable disposition.

Required next unit: one target-blind task episode, one public-trace parental
correction, child restatement and near-transfer exercise, dream successor
state, sleep-write, then a parent-absent held-out probe.

### N06 — backend teardown can leave the GPU occupied

`model_backend.py:42-76` explicitly documents that deleting the Python object
and running garbage collection cannot terminate vLLM's separate EngineCore;
the supported `close_backend()` performs shutdown and waits for memory to
clear. `nursery.py:93-96` and `116-118` instead use `del`, `gc.collect()`, and
`torch.cuda.empty_cache()` immediately before Transformers training or another
backend load. This can reproduce the orphan/OOM failure already observed in
the long-life harness. Required preflight: use the explicit backend shutdown,
assert memory below a frozen threshold, and abort rather than starting a
second owner on an occupied device.

## Nonblocking design cautions

- `compile_native` deduplicates on the first 120 lowercase answer characters.
  Distinct states that induce similar openings may be silently discarded.
- The curriculum's rules are hypotheses. For example, mandatory prediction
  may improve calibration or merely consume budget; “diversity before
  commitment” may help novel tasks and harm familiar ones. Register behavioral
  endpoints and exceptions instead of treating every lesson as truth.
- The long CompilerGym run still calls the separate frozen v1 trainer, not
  `train_adapter_v21`; nursery evidence must not be attributed to that run.

## Smallest useful launch after repair

Do not begin with all twelve readings or a long compiler life. Use one lesson,
one correction, one restatement, and one unrelated micro-task family. First
prove this chain:

`authentic child-specific correction -> retained supervised tokens -> adapter
absorption -> parent-absent behavioral delta -> better sealed task learning`

If the chain fails, localize it before adding curriculum volume. If it passes,
scale to several lessons and interactive parent sessions, then estimate the
hours/tokens per durable disposition before asking Rohin to parent the child.
