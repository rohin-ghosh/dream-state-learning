# Legacy continuation-writer floor v0

Status: exact design proposal only. No model, tokenizer, trainer, GPU,
scientific-claim, or release authority. This proposal must complete the
repository architecture-deliberation path and receive an exact run-manifest
ratification before execution.

## Narrow question and ceiling

Can a rank-16 LoRA trained on post-hoc selected improving continuations from
the archived v6.1 lives reinforce useful first-action behavior without eroding
the strict executable `ACT:` interface, and what is the effect of training
those identical target tokens behind one exact neutral-chat-prefix package
versus behind BOS alone?

The maximum permitted conclusion is continuation/action reinforcement plus
interface retention on content-disjoint compiler programs. The source prompts
were not persisted, and the dominant four-pass action was demonstrated in the
birth prompt. This assay cannot establish native task conditioning,
prompt/action binding, novel proposal formation, learned THINK, parenting,
continual improvement, or an experience-model flywheel.

## Frozen source prefix and join

Use the exact existing B0/B1/B2 ledgers only through completed wake boundary
256. Copy their raw bytes into an immutable read-only snapshot; bind every
`wake_START_END.json` from 0 through 256 plus the immediately succeeding
completed wake manifest as a boundary fence, all by raw SHA-256, and retain
every raw JSONL line plus its byte offset, byte length, and raw-line SHA-256.
The fence wake is never eligible training data. Legacy runtime source is not
reconstructed or inferred from the newer file on disk; the artifact bytes
below are the complete extraction authority.

The only permitted nonempty ledger-row kinds through the boundary are
`thought`, `act`, and `note`. The ordered wake manifests supply every program
occurrence through the fence and its exact positive integer `ticks` count.
Partition each program's ordered thought rows by those counts, requiring exact
ticks `1..T` for every occurrence.

Historical rows contain both thought-before-marker and marker-before-thought
serialization, so source code or one global orientation is not an authority.
In each program-filtered physical stream over the bound prefix plus fence,
enumerate every maximal contiguous run of `act`/`note` rows: leading the first
thought, between neighboring thoughts, or trailing the last thought. Every row
in a group must have one common tick. Candidate edges exist only to an existing
immediately preceding or immediately following thought with that program and
tick; leading/trailing groups therefore have at most one candidate. Solve the
finite attachment graph subject to each group attaching once and each thought
receiving at most one group; require a unique complete assignment. A group may
contain multiple act/note rows in their exact physical order. Zero-marker
thoughts are permitted. Reject mixed-tick groups, a missing compatible
neighbor, a second valid assignment, or a row that would cross a thought
boundary. This resolves runs of consecutive one-tick occurrences from the
artifact topology rather than a tick-reset or nearest-distance guess.

Define the terminal ledger byte offset as the minimum starting byte offset
over all rows assigned to any occurrence in the immediately succeeding fence
wake. Require every row assigned to an occurrence below 256 to end at or
before that offset, every fence-assigned row to begin at or after it, no group
to straddle it, and no unassigned/unknown row before it. Freeze this offset in
the receipt. `note` rows are assigned provenance only and never enter the
corpus. Invalid JSON/UTF-8, missing/duplicate/out-of-order thoughts, manifest
disagreement, or prefix/fence interleaving rejects the life. Later bytes are
retained in the copied source file but are outside the snapshot.
This artifact-defined grammar is intentionally narrower than guessing which
historical writer was loaded.
Two source-distinct extractors must emit byte-identical terminal offsets,
occurrence ordinals, thought offsets, act offsets, note exclusions, candidate
assignments, and rejection reasons.

Admit one continuation only when:

1. the thought has no `prompt` field; no prompt is reconstructed;
2. its decoded `note` is nonempty valid Unicode, its re-encoded UTF-8 target
   is fewer than 2,000 bytes, and the exact decoded-target hash is retained;
3. it contains exactly one column-zero `PREDICT:` line and exactly one later
   column-zero `ACT:` line;
4. the ACT parser removes the literal `ACT:` and at most one following ASCII
   space, retains the remaining line bytes exactly, and finds a nonempty
   payload equal byte-for-byte to the one matching ledger `action`;
5. exactly one ledger act exists at that occurrence/program/tick;
6. the outcome is `instructions I0 -> I1`, with integers `I0>0` and `I1>=0`;
   its stored finite score equals `(I0-I1)/I0` within `1e-12`;
7. its score exceeds `max(0, every earlier valid act score in that occurrence)`
   by more than `1e-12`.

Deduplicate within life by SHA-256 of exact decoded continuation UTF-8 bytes,
retaining the lowest thought byte offset. Never pool lives before training.
Tag the exact four-pass birth-demonstration payload separately.

After the tokenizer fit check below, each life must retain at least 64 unique
continuations, 4,096 supervised target tokens, four distinct ACT payloads,
and no single payload above 80% of rows. No retained row may have an ambiguous
join, source-cap hit, nonfinite/inconsistent outcome, or tokenizer truncation;
all excluded rows and reasons remain in the receipt. Failure in any life makes
this legacy assay NO-GO; do not drop a life, lower a threshold, or replace it
with program-level replication. These feasibility thresholds were chosen
after inspecting aggregate legacy counts, so even a pass remains formative
and cannot be presented as a prospective statistical test.

## Cells and target-token/update matching

Train one C1 and one C2 adapter independently per source life. C0 is one
common frozen-base reference.

| cell | exact model input | labels |
|---|---|---|
| C0 | no training/no adapter | none |
| C1 BARE | `BOS + continuation_ids + EOS` | continuation and EOS only |
| C2 CHAT | frozen live-chat prefix for neutral user text `Continue the recorded agent stream.` followed by the same `continuation_ids + EOS` | continuation and EOS only; prefix masked |

Derive `continuation_ids` once per row with the frozen tokenizer and
`add_special_tokens=false`; concatenate IDs rather than retokenizing across a
boundary. C1 and C2 must therefore have byte-identical target-ID vectors,
label masks over those target IDs, supervised-token totals, row order, and
optimizer-update counts. No packing. Reject any row for which the longer C2
sequence exceeds 1,024 tokens; never truncate.

This is not a fully exposure-, position-, or compute-matched serialization
ablation. C2 also changes role tokens, instruction bytes, prefix length,
target positions/RoPE phases, attention context, and FLOPs. The registered
estimand is the effect of this exact neutral-chat-prefix package relative to
BOS-only training. Report masked-prefix tokens, total input tokens, target
position distributions, and estimated training FLOPs per cell. No isolated
chat-boundary, role-token, or serialization-mechanism claim is permitted.

Stage-A recipe proposal: Qwen2.5-7B-Instruct at one immutable local revision;
all-layer attention+MLP LoRA; rank 16; alpha 32; dropout 0; bias none; bf16;
batch size 1; exactly three passes through frozen byte-offset row order;
AdamW with every parameter, scheduler value, initialization seed, data-order
seed, and deterministic-runtime flag bound in the later run manifest. The
same optimizer schedule is indexed by identical update ordinal in C1/C2.

Before full training, repeat complete B0/C1 and B0/C2 training twice each from
the same base, initial adapter tensor bytes, row order, hardware, libraries,
and seeds. Canonically hash ordered raw tensor bytes separately from metadata
and require byte-identical tensor hashes and bit-identical loss trajectories.
Also run the complete C0 panel twice through the exact serving path and require
byte-identical generated token IDs, strict-parser outputs, and scores. Run a
zero-delta LoRA/base-path equivalence golden. These deliberately conservative
canaries have no numerical fallback: failure leaves the assay NO-GO and starts
a new, separately ratified reproducibility design; do not average seeds or
relax tolerances post hoc.

## Content-disjoint target seal

The old eight probes are development-only. Before any target enumeration, the
exact run manifest and every corpus-selection, model/tokenizer revision,
template/prompt, renderer, parser, trainer, seed, metric, threshold, timeout,
and failure byte must be frozen and human-ratified. No design byte may change
after a target URI or module is exposed; a required change abandons that panel
and requires a new deliberation and new sealed namespace.

The ratified manifest must also bind a finite contamination input manifest:
every exact source ledger/wake file; every exact saved probe/control ledger or
result used in the Fable audits; every named advisory output containing a
program URI; and every exact source-program/probe list imported by those
analyses. A no-model extractor enumerates all canonical program URIs from only
those bound bytes. Any malformed or unresolvable URI is NO-GO. This closed
manifest replaces the open phrase "previously inspected."

Only then may two independent no-model sealers enumerate the complete
exact-version `poj104-v1` dataset directly from CompilerGym (not the current
400-URI display cap), export canonical reset-state LLVM bitcode/module bytes
for every URI, and SHA-256 those bytes. Freeze exact CompilerGym, LLVM,
dataset, container/host, reset/export command, subprocess environment, and a
60-second per-URI timeout. Independently resolve and hash every contaminated
URI. Exclude the entire target content-hash class if any member collides with
contaminated content. Among remaining duplicate POJ-104 content hashes, retain
only the lexicographically smallest canonical URI, record the discarded
aliases, sort survivors by `(content_sha256, canonical_uri)`, and take the
first 64. Scores and model calls are forbidden until the ordered panel is
sealed. Both sealers must produce byte-identical complete enumeration,
contamination, collision/alias, constructibility, and final-panel manifests.
Incomplete enumeration, fewer than 64 survivors, timeout, or any disagreement
is NO-GO.

## One-decision evaluation

Every cell/program starts from byte-identical fresh model, tokenizer, prompt,
environment, compiler, RNG, and empty state. There is no retrieval, note,
recall, waking brief, prior outcome, wall-clock field, or cross-program
ledger. The ratified run manifest contains the literal production-bootstrap
bytes and a pure target renderer. For canonical URI `U`, the renderer emits
exactly the following LF-joined user content with one terminal LF:

```text
=== YOU ===
{literal_bootstrap_without_trailing_whitespace}
=== STATE ===
GOAL: Optimize program '{U}': choose LLVM optimization passes that minimize its IR instruction count.
METRIC: score = (base_instructions - after) / base. Higher is better; 0 = no improvement. Passes are applied in the order you give them.
CLOCK: one decision; 256 generated-token budget
BEST SCORE THIS EPISODE: 0.0000
LAST OUTCOME: (no actions taken yet)
=== RECALLED EXPERIENCE ===
(nothing recalled)
=== YOUR THINKING (continues) ===
New program: {U}. I should form an expectation before acting, and write down what I learn.
```

The exact message array is `[{'role':'user','content': rendered_bytes}]` and
the frozen tokenizer's exact chat template is applied with
`tokenize=true, add_generation_prompt=true`; the resulting per-target input
ID vector is sealed before inference. The manifest binds tokenizer special
IDs, EOS/stop-token IDs, greedy sampling parameters, maximum 256 new tokens,
single-request batch size, vLLM/Transformers serving versions, LoRA mount
configuration, and no retry. C0/C1/C2 use byte-identical input IDs for a
target; only the mounted adapter differs.

The strict parser dispatches only the first column-zero line matching
`^ACT:[ \t]*(\S(?:.*\S)?)$`. Markdown forms do not dispatch. Execute that
payload from a separate fresh reset. Define score in percentage points as
`100*(I0-I1)/I0`; valid worsening actions remain negative, while missing,
empty, malformed, or evaluator-rejected actions score zero. This convention
matches the option of taking no optimization action; strict-marker compliance
is reported separately so silence cannot masquerade as interface success.

A frozen secondary parser may recognize only the already-observed
`### ACT:` and `- **ACT:**` forms in the identical emitted bytes, choose the
first strict-or-near-miss marker by byte position, and evaluate it once from a
fresh reset. It is an emitted-action-value diagnostic, not a counterfactual
trajectory. There are no K-action, equal-token, typed-decoding, or
switch-off-after-history endpoints in this floor assay.

For source life `l`, let `S[c,l]` be the 64-program mean strict first-action
score and `M[c,l]` the strict-marker rate. C0 is a single common deterministic
reference, not three pseudo-lives.

Primary exact-prefix-package contrast:

`D_prefix = mean_l(S[C2,l] - S[C1,l])`.

Call an exact neutral-chat-prefix package advantage present only if all hold:

- `D_prefix >= +1.0` instruction-reduction percentage point;
- at least two of three life differences are `>= +0.5` point;
- `mean_l(M[C2,l] - M[C1,l]) >= +0.05`.

Separately call a useful selected-continuation training effect present only if:

- `mean_l(S[C2,l] - S[C0]) >= +1.0` point;
- at least two of three C2 life means exceed C0 by `>= +0.5` point;
- mean C2 strict-marker rate is no more than 0.02 below C0.

These are descriptive go/no-go rules over three source lives, not a
population inference. No p-value, program bootstrap, checkpoint pooling, or
training seed can upgrade the claim. Program-wise intervals may be shown only
as conditional sensitivity displays.

C2-minus-C0 is the total effect of the complete post-hoc selected-corpus
training package. It is not evidence that verification, outcome binding,
source task conditioning, or novel experience caused the effect. Report for
every source life the frequency of the exact birth-demonstrated four-pass
payload in all rows and unique rows, strict first-action payload histograms,
and corpus-feasibility counts after excluding that payload. No claim may be
conditioned on the exclusion diagnostic, and no birth-excluded adapter is
trained in this floor.

## Gates before any GPU

1. exact change artifact, two fresh interpretations, adversarial critique,
   adjudicated consensus, and exact human architecture ratification for only
   the declared CPU preparation scope;
2. independent extractor agreement on the closed source snapshot;
3. corpus-feasibility thresholds pass for all three lives;
4. CPU tokenizer/label/EOS/update goldens prove target-token/update matching;
5. an exact run manifest binds every source/contamination input, model and
   tokenizer revision, prompt/renderer/template byte, trainer/serving path,
   seed, command, limit, metric, threshold, margin, lifecycle, failure suffix,
   and claim ceiling, followed by separate exact human run ratification;
6. only after gate 5, two target sealers agree and every contamination/content
   exclusion passes without exposing a score or changing any design byte;
7. deterministic duplicate B0/C1, B0/C2, C0, and zero-delta serving canaries
   are included in the ratified finite command set and pass before other
   training/evaluation;
8. quantitative GPU memory/lifecycle/failure plan and a fresh independent
   pre-GPU review approve the exact sealed manifest and gates 1--7.

Only after this floor is understood should a new instrumented life make C3
task-conditioned continuation and typed tool-call training testable.
