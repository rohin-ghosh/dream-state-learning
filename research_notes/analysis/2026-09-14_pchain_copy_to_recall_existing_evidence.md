# PCHAIN copy-to-recall: existing query-only evidence

2026-09-14. Bounded local evidence analysis; recommendation only. No code,
model/tokenizer loads, fits, GPU actions, new acceptance rules, or launches.

## Finding

The strongest close precedent is **SEQ-194/195 EVENT-retention-v2**: train on
an opaque address-only question and supervise the exact previously captured
EVENT answer, then generate without that answer in the prompt. A200 acquired
4/4 exposed A records in both W0 and W8 for each of three optimizer seeds.
**SEQ-118** supplies a simpler question-to-single-value example, with successful
recall of 16-fact banks. Neither result demonstrates why PCHAIN failed.

PCHAIN's copy-to-recall mismatch is a plausible diagnostic target, not an
established cause. The smallest precursor is query-only supervised retrieval
of the already sourced atomic relations, using the existing one-hop question
and answer grammar. Do not start by adding more two-hop training or a sweep.

## Current contrast: what is observed

Local saved reduction:
`gpu_artifacts_local/astra_pchain2_free_reduce_20260914_attempt1/RESULT.json`.
For both `ATOM-LOCAL` and `ATOM-JUNCTION`: one-hop 0/32 (each hop 0/16),
`prompt_trace` 16/16, canaries 16/16. BASE/LR0 common80 has 80/80 raw identities.
These are saved reducer values, not a fresh native reconstruction. The
reduction explicitly does not assess original-protocol compliance or null
clearance. Its remote `/tmp/...` input paths were not fetched for this note.

The current source agrees with Main's inspected row:
`gpu/astra_pchain2_prepare.py:306` (`_memory`, `_atomic_row`):

```text
user = "OBSERVED RELATION\nNEXT {source} => {target}\nTASK\nStore exactly this one relation.\n"
assistant = "MEMORY NEXT {source} => {target}\n"
```

By contrast, `gpu/astra_pchain2_free_material.py:64` constructs one-hop readout:

```text
user = "QUERY\nRecall NEXT for {origin}.\nOUTPUT\nReturn exactly one MEMORY line.\n"
expected = "MEMORY NEXT {origin} => {target}\n"
```

The answer is present in the training user turn and absent in recall. Success
when relations are supplied demonstrates performance on that supplied-fact
surface; it does not establish storage of the withheld relations. Conversely,
zero strict recall does not by itself localize failure to the training format.

## Strongest source-backed precedent: SEQ-194/195

Source path:
`organism_v6/pcfl_event_sequence.py:76` joins each address to its stored row,
requiring query target = row raw = captured generation raw. Export at line 126
uses W0–W7 from `organism_v6/pcfl_vertical_dev.py:44`. The system message is:

```text
You are the child's local personal-memory reader. You receive one opaque address request and no task. Return only the exact stored memory block associated with that address. Do not explain, infer, repair, or invent. If nothing usable is remembered, return exactly MISS.
```

One actual saved record (bank A, index 0, source `call_index=1`):

```text
W0 user = "Retrieve the exact stored memory for this request.\nREAD EVENT E_BRFFHBSD7R\nReply with only the stored memory block."
target = "EVENT E_BRFFHBSD7R AT N_HO47JGPS4W DID P_6JXK6M6ESI GOT N_J5KEPP4ZMR EVIDENCE R_D3FNLC3V7Z\n"
W8 user = "Provide the exact stored personal-memory block at this address.\nREAD EVENT E_BRFFHBSD7R\nOutput only the block."
```

The messages are rendered by the bound tokenizer's chat template with
`add_generation_prompt=True`. V3 receives context with loss disabled and the
exact EVENT with loss enabled, then one EOS:

```text
ids    = prompt_ids + target_ids + [eos]
labels = [-100] * len(prompt_ids) + target_ids + [eos]
```

Thus “mask answers” must mean **omit the answer from the question**, not remove
the answer from supervision. The source checks no truncation or dropped
context/target. W0 readout is the trained query surface; W8 was excluded from
the eight training wrappers but already exposed as DEV. Neither is an unseen
fact test, and W8 is not a fresh sealed transfer claim.

Historical acquisition recipe, not a proposed PCHAIN hyperparameter change:
`organism_v6/pcfl_event_sequence.py:48` and
`organism_v6/pcfl_event_sequence_v2.py:62`: frozen base/LoRA rank 8, alpha 16,
dropout .05, AdamW LR 3e-5, batch 4, grad accumulation 1, max length 512,
no packing or group shuffle, bf16. A200 schedules four A records × eight
wrappers × 25 repetitions = 800 presentations / 200 updates. Seeds 0/1/2
repeat the same bank; they are not independent fact banks.

For each seed and separately W0/W8, the saved final reduction reports:

| State | A correct / 4 | B correct / 4 |
| --- | --- | --- |
| C0 / no write | 0 | 0 |
| A200 | 4 | 0 |
| B200 or B400 new-only after A200 | 0 | 4 |
| REPLAY400 or CLEAN_CUM600 | 4 | 4 |

References: `research_notes/astra_memos/ASTRA_HANDOFF_2026-09-12.md`
(SEQ-194 acquisition and SEQ-195 completion sections),
`research_notes/analysis/2026-09-13_event_retention_v2_three_seed_analysis.md`,
and `research_notes/analysis/2026-09-13_event_retention_v2_three_seed_raw_report.md`.
The documented accepted comparison has 288 calls with no truncations. This
note checks selected saved evidence, not the entire prior custody procedure.

Concrete local evidence inspected:

- `gpu_artifacts_local/pcfl_v2_acquisition_20260913_attempt1/evidence.tar`, member
  `localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_acquisition_20260913_attempt5/inputs/seed0/material.json`:
  `spec.records[0]` supplies the exact example above. It records CHILD_NATIVE
  origin, but also `native_generation_verified=false` in row provenance; this
  note does not upgrade that field or independently attest generation.
- `gpu_artifacts_local/pcfl_v2_final_three_seed_20260913_attempt1/reduction.json`:
  acquisition call ID `event-sequence-v2/W0/00`, captured source path
  `/localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_acquisition_20260913_attempt5/runs/seed0/a200_outer/readout/actor/call_0000.raw.json`.
- `gpu_artifacts_local/pcfl_v2_final_three_seed_20260913_attempt1/evidence.tar`,
  member prefix `localhome/local-rohing/astra_diagnostics/pcfl_sequence_v2_followup_seed0_20260913_attempt6/runs/CLEAN_CUM600_readout_outer/readout/`:
  `readout_config.json` contains that address-only roster entry;
  `response_0000.json` contains exactly the EVENT above, `finish_reason=stop`,
  `truncated=false`, under the same call ID. The readout source
  `gpu/astra_pcfl_event_sequence_v2_readout.py:129` generates before scoring
  against the separately joined target.

## Simpler precedent: SEQ-118 / FOUR_VIEW

`organism_v6/varied_memory_replay_corpus.py:24` defines four training questions:

```text
Which color does the log assign to {device}?
What is the color assigned to {device} in the log?
According to the log, which color is assigned to {device}?
Name the color that the log assigns to {device}.
```

The supervised response is the source-record color alone, e.g. `blue`, with
no explanation or color in the question. `render` (line 140) makes a user-only
chat turn plus assistant generation prefix; response + one EOS are supervised,
prefix ignored. `organism_v6/sequential_memory_corpus.py:69` constructs sourced
new-bank rows; line 263 exports this same context/target split.

SEQ-118's exact probe is the first training question. Its development probe
is `Recall the logged color of {device}.` (`sequential_memory_corpus.py:91`).
Both ask about trained keys; the latter changes wording, not fact identity.
These are researcher-authored synthetic logs, not autonomous child experience.

The local terminal capsule
`research_notes/astra_memos/receipts_20260912/astra_sequential_memory_seed0_pair_attempt2_terminal_20260913T0000Z.tgz`,
member `seed0_pair_attempt2/run/terminal.json`, confirms R2 M0/B1/B2 each
16/16 on both surfaces. NEW_ONLY2 is M0 9/16 dev, 8/16 exact; B1 4/16 on
both; B2 16/16 on both. Arithmetic adherence and correct ACT are 32/32.
See `research_notes/astra_memos/ASTRA_SEQUENTIAL_MEMORY_2026-09-13.md` and
`research_loop/COORDINATION.md` SEQ-118. One optimizer seed, three 16-fact
banks; replay/new-only doses differ. This is a useful existing mechanism
example, not a matched causal comparison to PCHAIN.

## Why not lead with memory-dose

`organism_v6/memory_dose.py:280` includes a genuine query-like short form:
`Owner {owner}. Q: what colour is the car?\nA: ` with target
`{owner}'s car is {colour}.`. Its held question p1 is
`What colour is owner {owner}'s car? Answer with one colour:` (p2/p3 nearby).
But `_piece` at line 1623 distinguishes short bare-text/all-token loss from
antecedent training (answer-bearing observation, target-only loss) and frames
(answer-bearing prose, all-token loss). The module describes synthetic
planted facts and conditional log-odds scoring, not strict free-generation
recall. Notebook memory-dose completion probabilities must not be relabeled
as query-only free-recall accuracy. SEQ-194/195 and SEQ-118 are closer evidence.

## Smallest diagnostic precursor — Main's decision, no launch here

Reuse the existing authorized source relations and fixed keys. Construct each
atomic training question from its key alone, using the existing one-hop user
bytes above; supervise the unchanged source-backed `MEMORY NEXT ...\n` answer
and existing terminal token. Apply this to A→B and B→C independently, without
putting either retrieved target in the question. Use source facts, not held
probe outputs, to obtain targets. “Acquired” here means available source
facts, not demonstrated acquisition by the failed PCHAIN adapter.

Keep the existing diagnostic lineage, numerical recipe/budget and answer
grammar otherwise fixed as Main binds them; no new seeds, fact redraw,
wrapper/rank/dose search, BASE panel, or acceptance gate. First inspect the
existing key-only one-hop surface before claiming any two-hop acquisition.
When trained with those exact questions, that readout becomes explicit DEV
resubstitution on trained keys, not held-question generalization. Do not
relabel it as the original prospective PCHAIN result.

This recommendation tests whether a matched query-only interface can acquire
the sourced mapping under the chosen conditions. A successful precursor alone
would not establish that copying caused the earlier failure, nor demonstrate
composition. Preserve the original failed run and its controls unchanged.

## Check receipt and remaining interface

CPU-only checks used `python3 -B` with standard-library `json`/`tarfile` to
read the selected members above, inspect saved reduction cells, and join the
example request/answer. No project/native imports, extraction of the full
archives, tokenization, or new test suite. Focused standard-library assertions
passed: both PCHAIN panel vectors and BASE/LR0 identities; EVENT source/target
equality and address join; exact saved CLEAN_CUM600 response with stop and no
truncation; all six SEQ-118 R2 bank/surface cells. This is not a rerun of the
full scientific reducer or an independent custody attestation.
A reproducible existing receipt
inspection command is:

```bash
tar -xOf research_notes/astra_memos/receipts_20260912/astra_sequential_memory_seed0_pair_attempt2_terminal_20260913T0000Z.tgz seed0_pair_attempt2/run/terminal.json | jq '.reductions | map_values(.counts)'
```

Remaining interface: Main owns prospective source-to-query material binding,
the existing trainer's masking/rendering verification, any decision to launch,
and interpretation of the DEV result. No implementation or new guard program
is supplied or required by this evidence note.
