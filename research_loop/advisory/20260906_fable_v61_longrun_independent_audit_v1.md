# Fable v6.1 long-run independent audit v1

Date: 2026-09-06 02:56 PDT  
Scope: read-only audit and CPU-only counterfactual evaluation of Fable's
already-running CompilerGym lives on the A40 host. No process, adapter,
corpus, probe, or run file was changed. This grants no PPC, architecture,
GPU, or scientific-claim authority.

## Bottom line

The long run has already produced a useful mechanistic result: sleep can
improve the agent's compiler-action dialect for hundreds of episodes, but its
unconstrained bare-text self-training can also create a self-reinforcing
format shift that moves good actions outside the harness grammar. One seed's
reported score collapsed to zero even though its explicitly written intended
actions still achieved a 0.529 mean when scored post hoc.

This is evidence that the writer changes behavior and that the benchmark
detects failure. It is not yet evidence of continual learning: the run is
unseeded at generation time, has a B-only waking-brief difference, repeats 67
training programs 15--16 times, and does not preserve a common-random paired
probe.

## Bound code

The remote execution files had these SHA-256 values:

| file | SHA-256 |
|---|---|
| `run_life_v2.py` | `08cfe6669c46b30df01a9bddc14a2bbff66e03af536fce7c2c4d068d3777096c` |
| `run_life.py` | `eece8cc923ffcaa364eda5f78f77ba76b38720708f1fd98face35aa89e278e98` |
| `batch_loop.py` | `42ddb1b9a2a9b821bf025d847b327b18fade58b850053e1507702a919df4cc59` |
| `sleep_compile.py` | `9049a6e5f8ef4fdf35077a48c5500f3ca07b419274dc7fdb3abe605720f99a82` |
| `train_adapter.py` | `234d8a93b8fb9f79e2daef11b4b2b5c0eda860c3a096b5222a252be5019d2f1b` |
| `model_backend.py` | `1b224307db99e33423bd7029415384967bb7dee831966bdbecc0a72bb80c92c8` |
| `gym_backend.py` | `e112d4de98166539bff654b2ada92070d1c6cbb8d598d20b36d25a6964e1454e` |
| `cgym_eval.py` | `55b69b265d3a2a695a815e217ba0c06ee054c9f242442353ca7c7eeefbc1d4fa` |

The model/tokenizer revision, sampling seeds, training RNG state, package
versions, corpus hashes, and adapter hashes are not recorded in run receipts.

### Runtime/source ancestry correction (2026-09-06 follow-up)

The source hashes above bind the files present when this audit inspected the
host; they do not prove that the long-lived Python processes imported those
exact bytes. This distinction is material here. The audited
`batch_loop.py` now writes `prompt=...` into each thought row, but a read-only
copy of the live ledgers contains no prompt field in any thought row:

- B0: `0/7043` prompt-bearing thought rows;
- B1: `0/5916`;
- B2: `0/10612`.

The remote `batch_loop.py` mtime was `2026-09-06 09:17:38 +0000`, after every
currently running life process had started (A processes at Sep 5 19:12, B0 at
Sep 5 23:42, and resumed B1/B2 at Sep 6 05:57 in the host's `ps` clock).
The processes therefore plausibly retained an older imported module while the
file on disk changed beneath them. Exact native prompt-to-continuation
training rows cannot be recovered from these artifacts. A prospective source
life must record loaded-source hashes at process start and persist the exact
prompt before dispatch. Reconstructing missing prompts after the fact would
invent evidence.

There is also a narrower interpretation correction: the birth prompt itself
demonstrates the exact four-pass sequence
`-mem2reg,-sroa,-gvn,-simplifycfg`, which accounts for the dominant early
adapter-on transition. The observed delta can therefore establish stronger
transport/reinforcement of an available cross-program action, but not novel
strategy generation or learned THINK.

## Actual lifetime structure

For each seed the 1,024 episode list contains only 67 unique programs:

- 15 non-probe cBench programs;
- 12 CHStone programs;
- 40 MiBench programs.

The shuffled 67-program sequence repeats exactly, beginning again at episode
67. Each program occurs 15 or 16 times. Canonical train/probe intersection
with the eight cBench probes was empty, so the earlier URI-prefix leakage is
fixed here. The instrument is therefore a repeated finite curriculum with a
sealed same-family panel, not 1,024 independent experiences.

## Descriptive adapter effect before collapse

Across the 12 available adapter-on/off checkpoints at episodes 64--256, the
mean on-minus-off difference was `+0.0211`; 10/12 differences were positive.
The three life-level early means were approximately `+0.0467`, `+0.0155`, and
`+0.0010`. This is suggestive, not confirmatory: checkpoints within a life
are dependent and on/off samples do not share pinned generation RNG.

### Post-hoc fixed-action diagnostic

The early difference is not explained solely by one arm taking more actions.
Recomputing each probe's best score after only the first `K` parsed actions,
then pairing adapter ON versus OFF at the same 12 checkpoints, gave:

| action cap K | mean ON-OFF | median ON-OFF | positive pairs |
|---:|---:|---:|---:|
| 1 | `+0.0178` | `+0.0280` | 11/12 |
| 2 | `+0.0240` | `+0.0280` | 12/12 |
| 4 | `+0.0223` | `+0.0234` | 10/12 |
| 8 | `+0.0210` | `+0.0213` | 10/12 |

This was defined after inspecting the run and remains descriptive: it does
not repair the missing common-random generation or dependence among
checkpoints. It does, however, falsify the narrow explanation that the full
early delta was only an action-volume artifact. The prospective run should
pre-register both fixed-action and equal-generated-token endpoints.

The action strings localize what was acquired. Across the 96
seed/checkpoint/program first-action pairs, adapter OFF usually opened five
programs with `-mem2reg,-sroa,-gvn,-simplifycfg`, two with
`-mem2reg,-sroa`, and one with `-mem2reg,-sroa,-gvn`. Adapter ON used the
four-pass sequence 72/96 times and covered all eight programs with it. The
dominant stable transitions were:

- `dijkstra`: two-pass to four-pass in 10 pairs, mean score change `+0.1022`;
- `stringsearch`: two-pass to four-pass in 9 pairs, mean change `+0.1001`;
- `sha`: three-pass to four-pass in 8 pairs, mean change `+0.0213`;
- five programs already using the four-pass action in both arms: no change.

Thus the early signal is best described as transport of one useful
cross-program action prior, not evidence of program-conditional reasoning or
learned THINK. The exact read-only analysis is reproducible with
`research_loop/advisory/analyze_fable_v61_probe_actions.py` against the saved
remote ledgers.

At later checkpoints, B2 catastrophically diverged while B0/B1 initially
remained useful. At episode 576:

- B2 adapter ON: mean `0.000`, 0 parsed actions, 128 thought chunks;
- the same checkpoint adapter OFF: mean `0.476`, 41 parsed actions;
- at episodes 640 and 704, adapter ON parsed only one action per panel.

### B2 terminal follow-up (2026-09-06)

B2 subsequently completed all 1,024 episodes and did not recover under the
registered strict parser. Its adapter-on minus adapter-off panel difference
was `+0.0241` at episode 64, `-0.4310` at episode 320, `-0.4760` at episode
576, and `-0.4348` at episode 1,024. The terminal means were `0.0511` with
the adapter and `0.4859` with the same checkpoint's adapter removed. This
strengthens the writer-failure trajectory while leaving the causal-learning
limitations in this advisory unchanged: generation was unseeded, the writer
and context policies were confounded, and the retained prose-level action
quality was diagnosed post hoc.

A new terminal-only permissive extraction, defined after inspecting the
episode-1,024 bytes, accepted the strict marker plus the three observed
Markdown wrappers (`### ACT:`, `**ACT:**`, and `- **ACT:**`). It recovered a
first proposed action for all eight programs. Evaluating those exact saved
strings once with the unchanged CompilerGym evaluator gave mean `0.5287`,
versus registered strict `0.0511` and that checkpoint's adapter-off `0.4859`.
This is post-hoc mechanism localization, not a rescued endpoint or controlled
adapter benefit: at terminal time the adapter still emitted useful action
content, but almost entirely outside the executable serialization channel.

## Exact collapse mechanism: executable language became Markdown

B2's generated text still contained plausible action sequences, but rendered
them as `### ACT:` or `- **ACT:**`. The harness parser accepts only a
line-start `ACT:` marker. Thus the agent talked about an action without
executing it.

A post-hoc CPU diagnostic extracted only those two near-miss Markdown forms
from the saved episode-576 thought stream and evaluated the extracted pass
sequences with the unchanged CompilerGym evaluator. This changed the panel
mean from strict-parser `0.000` to counterfactual `0.5294`:

| probe | strict | recovered intended action |
|---|---:|---:|
| susan | 0.000 | 0.567 |
| sha | 0.000 | 0.547 |
| dijkstra | 0.000 | 0.409 |
| patricia | 0.000 | 0.651 |
| jpeg-c | 0.000 | 0.526 |
| tiff2bw | 0.000 | 0.486 |
| gsm | 0.000 | 0.528 |
| stringsearch | 0.000 | 0.522 |

This counterfactual is diagnostic only; it was defined after seeing the
failure and cannot replace the registered score. It shows that the checkpoint
retained useful compiler proposals while losing interface compliance.

## Self-reinforcing corpus evidence

The sleep writer trains a fresh rank-16 adapter at learning rate `1e-4` for
three epochs on cumulative bare text. It does not train through the exact live
chat/action dialect. In B2, cumulative corpus rows with a Markdown-wrapped ACT
rose from 0/274 at sleep 64 to:

- 11/428 at 128;
- 96/633 at 256;
- 157/702 at 320, when parsed probe actions fell to 1;
- 323/907 at 576, when parsed probe actions fell to 0;
- 354/940 at 704.

Across the 24 currently paired checkpoints from all B lives, the descriptive
correlation between off-dialect corpus fraction and strict probe score was
`r=-0.934`; with parsed action count it was `r=-0.697`. This pooled statistic
is seed-confounded and is reported only as mechanism localization. B0/B1 had
zero off-dialect ACT rows through most available checkpoints and continued to
execute many mostly valid actions.

The resulting failure loop is:

`small formatting deviation -> admitted self-trace -> bare-text LoRA write ->
more formatting deviation -> parser stops actions -> score collapse`.

The benchmark is doing something valuable here: it distinguishes knowing an
action from successfully routing it into the world.

### The B2 failure developed in two behavioral stages

The frozen wake summaries through episode 256 show that B2 did not jump
directly from healthy exploration to Markdown routing failure. It first
learned to terminate extremely early while retaining good one-action value,
then lost executable actions while continuing to generate full-length text:

| B2 episode block | mean ticks | one-tick episodes | mean actions | no-action episodes | mean best score |
|---|---:|---:|---:|---:|---:|
| 0--63 | 12.59 | 2/64 | 9.81 | 0/64 | 0.5540 |
| 64--127 | 10.48 | 21/64 | 7.03 | 3/64 | 0.5454 |
| 128--191 | 3.44 | 51/64 | 2.61 | 3/64 | 0.5459 |
| 192--255 | 14.88 | 4/64 | 0.73 | 48/64 | 0.1324 |

B0 and B1 had zero no-action episodes in the same prefix and only 15 and 4
one-tick episodes total, respectively. This suggests two distinct writer
effects worth separating prospectively: a stopping/search policy shift
(efficient when the first action is good, brittle if overlearned) and a later
serialization/routing shift (thinking continues but actions no longer
dispatch). The observation is post-hoc and life-specific, so it localizes
mechanisms but is not a causal learning claim.

## Completed rank/shuffle controls: useful, but not causal rank evidence

Fable's completed two-panel controls over the 131-row B1 sleep-64 corpus
reported:

| cell | mean over two unseeded panels |
|---|---:|
| base | `0.4854` |
| true corpus, newly trained r8 | `0.5149` |
| true corpus, original B1 r16 adapter | `0.4089` |
| outcome-shuffled corpus, newly trained r16 | `0.5259` |

These exact JSON hashes are, respectively,
`ffae05747024d00c88e6fa21372c0811eb83e7a28bb873f0531db01f0b3bf72b`,
`3452d10d2037e25e44715b23123168817ba27ae91fa07dbcbde337c5cafdd8ef`,
`85a6a800fed71f3749ec4df50fcb938910fe0d4ff164045ecd81abb36d7a29bc`,
and `f81a9113b0c8f06ab4861dacadaa47a1193442c74a1791def4346681b0580a38`.

They do **not** establish an inverted-U rank law. The r8 and r16 adapters
were separate unseeded training realizations, their stochastic probe panels
were not common-random, and only two panels were run. The trained r64 adapter
exists, but no r64 probe result exists: vLLM rejected it because the serving
backend froze `max_lora_rank=32`.

Nor is the shuffle a control for whether action knowledge was learned. It
changed 125/131 rows by permuting only text after ` -> `, ` scored `, or
` and measured: `. Program identifiers and action/pass strings remained in
their original heads, so all-token LM training could still learn the same
generic action prior. The result only says that correct outcome-tail binding
was unnecessary for this exact behavior (or that the two-panel noise is
large); it cannot distinguish useful action imitation from grounded
action-to-outcome learning.

The defensible conclusion is narrower: behavior is highly sensitive to
writer realization, and a cooler/smaller realization is worth testing under
controlled seeds. Rank, heat, and binding remain unresolved.

## Other causal limitations

1. `model_backend.py` ignores the `seed` argument and constructs unseeded
   `SamplingParams`; probe pairs are not common-random trials.
2. Arm B receives each generated waking brief during subsequent life, while
   arm A compiles but does not install the brief. The lifetime contrast is
   therefore adapter plus B-only context policy, not adapter alone. Probe
   calls themselves use the common base bootstrap.
3. Probe ledgers are shared across the eight batched programs. No recalled
   content was observed in sampled saved prompts, but the design permits
   cross-program retrieval and should use one isolated ledger per probe.
4. The v1 writer trains all tokens of bare experience text rather than
   response-only native continuations; it has no generic-behavior/KL guard.
5. Best-of-episode score under fixed chunks conflates thought formatting,
   action count, and action quality. The proposed equal-generated-token assay
   plus fixed-action diagnostic is still needed.

## Highest-value follow-up

Do not rescue the recorded score by loosening the parser post hoc. Freeze a
prospective micro-assay that separates three endpoints under common random
seeds:

1. latent action proposal quality under a typed/grammar-constrained action
   channel;
2. interface compliance under the original strict channel;
3. task value under equal generated-token and separately fixed-action
   budgets.

Race the same accepted experience rows through bare-text v1 versus exact
native-response training, with adapter-off and binding-shuffled controls.
This directly tests whether sleep can retain the useful early action delta
without amplifying its own representational accidents.
