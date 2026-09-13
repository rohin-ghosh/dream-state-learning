# Birth conditional/locality component — prospective plan, September 12, 2026

Status at this cut: **133 Main CPU tests and native tokenizer audit PASS;
runner/collector acceptance pending, no birth GPU fit or readout launched.**
This follows Rohin's raw message 23: build level 1, then sample level 2 on the
born learner. It is the first bounded birth component, not a complete learned
flywheel or a claim that the corpus is perfect.

## Question and fixed intervention

Can source-authored single-LoRA birth training express input-conditional
prospective choices and expected-versus-observed revisions while obeying
unrelated output instructions? SEQ-108 motivates two repairs: REVISE had an
EXPECTED-factor shortcut, and both learned maps damaged locality. Those old
results remain unchanged; this is not a controlled estimate of each repair.

AUTH and DERANGED start separately from the same frozen Qwen2.5-7B-Instruct
base. Both receive the same public inputs, source records, truthful arithmetic
and copy anchors, and resource recipe. Conditional targets implement opposite
maps; target sequences, including EOS, swap within each optimizer group.
Birth data is sourced authored material, not child experience or clean ancestry.
No deployment-gym or quarantined weights/rows enter this new source construction.
Model origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`.

| Fixed item | Value |
|---|---|
| Source | `31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6` |
| Corpus module SHA256 | `43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b` |
| First optimizer/root seed | 0, exploratory; no favorable seed selection |
| Adapter | Rank 8, alpha 16, dropout .05; all existing projection targets |
| Optimizer | Existing V3 AdamW, LR 0.0001, fresh optimizer and adapter |
| Dose | 4 epochs; 256 rows; batch 8/accumulation 1; 128 updates per arm |
| Batch | PROSPECT pair, EXPECTED-flip REVISE pair, two addition and two copy anchors |
| Encoding | Native user chat prefix; target-only loss and one EOS; no packing |
| Training counts per arm | 64 each PROSPECT, REVISE, ADDITION, COPY |
| Held-out development counts | 32 PROSPECT, 64 REVISE, 16 ADDITION, 16 COPY |
| Readout | Fresh processes OFF, AUTH, DERANGED; same 128 inputs each |
| Generation | Greedy, maximum 64 generated tokens per call; 384-call ceiling |

REVISE crosses all EXPECTED × OBSERVED × PRIOR combinations within every
visible instance and template. All remaining public factors plus visible
instance/template/action-order are insufficient to exceed .5 joint accuracy
when any required factor is omitted. Source/corner IDs and expected answers
are not exported as readout inputs. Held-out instances and template families
are disjoint. These checks rule out the enumerated shortcuts, not every possible
shortcut or semantic generalization failure.

LR/dose preserve the earlier conditional-acquisition recipe while adding
anchors and changing batch composition. Identical conditional presentation
counts do not imply identical gradients. Neither the chosen rate nor the word
birth certifies high plasticity; outcomes and interference must be measured.

## Native cost and loss-mask acceptance

Main's offline native tokenizer audit completed in 4.189 seconds, with no GPU
model load. Receipt SHA256:
`55f8987c448f62d6745ec3b59c245e7ae1db72fafa1c87df9702615794309993`.
Both arms have exactly 18,352 input and 2,912 target tokens per epoch. Over
four epochs each fit has 73,408 input tokens, 11,648 targets, and 93,696 padded
input positions. Input includes targets; target counts include EOS. Padding is
masked. Full paired token-sequence swaps and per-batch length/padding parity
pass; zero truncated, split, skipped or dropped rows. Actual training receipts
must agree; native token preparation is not evidence of successful learning.

Tentative reservation: node 3, GPU 0, only after a fresh process/GPU/queue
vacancy check. Separate fit and readout stages: at most 1,800 seconds for the
two fits plus 300 seconds for collection, then at most 2,700 seconds for three
readout cells plus 300 seconds collection. These are caps, not runtime forecasts;
the combined maximum is 85 A40-min. Main retains ownership through observed
release; no automatic phase chaining, favorable retry or borrowed control GPU.
Supply the known node-3 expiry and preserve the six-hour lease margin. No new
paid allocation is requested.

## Predeclared descriptive component criteria

Collect all three complete panels before reducing or inspecting outcomes.
Retain every raw output, invalid response, token limit, source/adapter identity
and actual usage. A technical partial is not a scored scientific failure and
does not permit dropping the missing cell or selecting a replacement output.

For each trained map, report both AUTH-semantic and assigned-map results:

- Assigned-map strict joint correctness at least 90% in each operation:
  PROSPECT at least 29/32 and REVISE at least 58/64.
- Each registered factor-twin family at least 90% complete strict pair success:
  belief/goal at least 15/16; expected/observed/prior-action at least 29/32.
  Both endpoints and required flips count; syntax alone does not pass.
- Each locality family meets `max(ceil(.95*N), OFF_compliant-1)` instruction-
  compliant cases. At N=16 this requires 16/16. No forbidden conditional tag
  spill on either anchor family. Semantic correctness, canonical bytes and
  instruction compliance remain separate reported measures.

OFF is an unchanged-base comparator, not a matched-training control; DERANGED
is the matched-training mapping control. Report whether each part of the
conjunction passes; do not convert it into automatic full-L1/G3/P1/H1/H2 approval.
One root is exploratory. Any numerical robustness claim needs the authorized
independent replications, not correlated cases treated as learners.

## Level-2 sampling after the component result

The existing interaction_v3 RuleGame formation is the smallest reusable sample,
but its TRY/QUIZ/record schema differs from the conditional corpus's opaque
actions. Test participation rather than assuming transfer. Reuse its fixed two
P/A lesson positions, public event feedback and raw child replies; teachers see
only the existing developmental transcript, never sealed birth/adult scores.

The new role bridge keeps the child on the pinned birth adapter and teacher on
the same adapter-OFF base for all cells. A single engine uses explicit per-call
LoRA requests; role identities and replay are separately bound. Main's 21 new
CPU tests plus 46 existing diagnostic tests pass; actual native role routing and
completed-birth ancestry still need testing. This bridge does not launch anything.

A no-write teaching sample establishes only participation/in-context response,
not retained learning. A subsequent own-wake write must continue the same birth
LoRA, preserve raw source eligibility and wrong predictions, strip only the
declared temporary teacher context, and compare an unchanged-birth checkpoint
with matched P/A descendants after fresh reload. Do not silently use the old
fresh-base writer or its OFF cell for that different comparison. Freeze its
actual sample specification and counts before execution; this plan does not
pretend that missing warm-start integration is ready.

Simple hygiene and provenance rules stay active. The formal guard remains
reserved for the final paper-grade C11 run, as Rohin requested.
