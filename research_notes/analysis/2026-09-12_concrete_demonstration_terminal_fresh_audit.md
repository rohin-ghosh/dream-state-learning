# Fresh terminal audit: concrete demonstration pilot

Date: 2026-09-12 UTC  
Run: `astra_demonstration_20260912_attempt1`  
Source commit: `87936cc5ac9e6cd9e5e4dd23f452b87ced14cb7a`

Scope: independent, read-only scientific/raw-output audit of the frozen module,
test, terminal memo, native receipts, capsule, both raw generation ledgers,
both result files, and the archived content audit. I used a separate Python
standard-library replay over saved bytes only. I did not run a model,
tokenizer, test, GPU command, network command, or builder/coordination code.

## Verdict

**PASS for artifact custody and the reported strict counts. REJECT as a clean
changed-board transfer result.** The capsule supports one grounded response on
a distinct-hash second candidate in a prompt containing the exact prior child
note and no direct parent/example/source-board bytes. It does not support a
process-supervision effect, a correct-source-to-application chain, or even a
transfer-specific witness: the sole successful t02 citation is valid at the
same group, coordinates, and digit on both the s02 and t02 candidates.

The maximum defensible claim is:

> In one fixed eight-pair, one-sampling-seed feasibility run of the unchanged
> frozen base, process prompts produced two grounded source records versus zero
> under format prompts. On the subsequent distinct-candidate calls containing
> exact raw source notes, process produced one grounded record versus zero under
> format. That one t02 record followed an ungrounded s02 note and named a
> witness already true at the identical location on s02, so it is only a
> note-conditioned second-board success, not clean changed-board transfer or
> evidence that the demonstration/note caused the success.

There were zero fits, adapters, learner/optimizer seeds, or weight changes.
Nothing here is persistence, internalization, parenting, P1, H1/H2, clean
ancestry, an independent learner replication, or training approval.

## Saved-byte and scorer replay

The archived source module is unchanged at HEAD and has SHA-256
`cc61e146...2ec`; the base scorer has `59d667...859`. The test file has
`0ea2be...5d9`; I read, but did not execute, the saved 19-test/`OK` log whose
hash is `28d120...e7a`. The current terminal memo hash is `6a226c...839`.
The terminal capsule hash is `b2d03d...417`, its preparation manifest hash is
`75c528...343`, and its `COMPLETED.json` hash is the reported
`bd6336...fa5`.

I found 28 regular capsule members with no duplicate member names. Every one
of the 13 files covered by the preparation/process/format inventory manifests
rehashes exactly. Each arm contains exactly 48 events in strict
`request, raw_return, output` triplets, giving 32 calls. Every native raw text
equals its output event and result record; prompt/output token-ID cardinalities,
hashes, case/pair/order, seed 7101, cap 128, `stop` finish, no truncation and no
rewrite all agree. Worker PIDs are distinct (`132012`, `132748`); every request
identity has `adapter_input=null` and an empty adapter-file inventory.

The archived audit JSON (`9ab41d...0c6`) binds all 32 texts through raw-line
SHA-256, output SHA-256 and UTF-8 base64; I independently matched each binding.
Its 515 recorded checks all pass. The remote model/package paths and cleanup
state remain captured remote observations, not newly authenticated local
facts.

Here is my independent strict replay of all 32 outputs. `G` means schema-valid
and grounded; `F` means schema-valid/case-bound but its sole citation is
factually false; `J` means schema-invalid. Columns are p01 through p08.

| arm / phase | p01 | p02 | p03 | p04 | p05 | p06 | p07 | p08 | grounded | schema |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| process / source | J | F | F | G | F | F | G | F | 2/8 | 7/8 |
| process / transfer | J | G | F | F | F | F | F | F | 1/8 | 7/8 |
| format / source | F | F | F | F | F | F | F | F | 0/8 | 8/8 |
| format / transfer | F | F | F | F | F | F | F | F | 0/8 | 8/8 |

The two `J` records are process s01 and t01: each JSON object has one check but
names three coordinate arrays where exactly two are required. They receive no
partial salvage. The remaining 30 outputs have exact top-level/check keys,
the correct case ID, one check, integer coordinates/digit, and a nonempty
lesson. Of these, only three citations are factual:

- s04: row, `[4,1]` and `[4,2]`, digit 4;
- s07: row, `[4,1]` and `[4,4]`, digit 2;
- t02: box, `[3,3]` and `[3,4]`, digit 1.

Thus the global replay is 30 schema-valid objects, three grounded/whole-clean
records, 27 schema-valid invalid citations, and two schema failures. This
exactly reproduces both result files, `COMPLETED.json`, native terminal JSON,
and the archived audit.

## Pairing and exact note custody

I independently reconstructed the questions, public board parsing,
deterministic fills and edits from the eight stored pairs. The 16 episode IDs,
question hashes and candidate hashes are unique; their actual question and
candidate hashes do not intersect the 16 captured v1/v2 prior records. All
eight provided examples are factual, all eight designated example witnesses
become false on their transfer candidates after case-ID rebinding, and all
eight planted transfer targets are factual.

All 16 source outputs, including failures, occur byte-for-byte in their paired
transfer prompt at the stored half-open byte span. Receipt length and SHA-256
match the source output; bytes outside the span contain no source example,
source candidate rendering, source case ID, or arm-specific parent
explanation. Raw, rendered and output bytes agree. The particularly important
s02 note is the ungrounded row claim `[2,2],[2,3]`, digit 4, SHA-256
`8f5255...db8`, carried exactly at bytes `966:1087`.

Rebinding each of the 16 actual source-note citations to its transfer case
yields **0/16 grounded**, and no transfer output repeats its paired note's
exact witness. The t02 output changes all answer-bearing fields from its note:
row -> box, digit 4 -> 1, and `[2,2],[2,3]` -> `[3,3],[3,4]`. Therefore the
t02 success is not a literal answer copied from the saved child note. It also
differs from the designated source example and the planted transfer target.

## The missed board-witness overlap

The frozen construction invalidates only the one designated example witness
(`make_pair`, lines 103--122); the corresponding test checks only that witness
and that the planted target uses other cells (test lines 152--165). Neither
requires the complete sets of valid source and transfer answers to be
disjoint.

I exhaustively enumerated every valid `(group, digit, unordered cell pair)` on
each saved candidate. The source/transfer witness-set sizes and intersections
are:

| pair | source witnesses | transfer witnesses | identical witnesses shared |
|---|---:|---:|---:|
| p01 | 13 | 10 | 2 |
| p02 | 14 | 14 | 4 |
| p03 | 10 | 10 | 1 |
| p04 | 8 | 17 | 3 |
| p05 | 15 | 11 | 2 |
| p06 | 7 | 17 | 1 |
| p07 | 13 | 9 | 2 |
| p08 | 20 | 16 | 2 |

Every pair therefore retains at least one exact answer witness. Most
importantly, t02's only valid output—`box`, digit 1, cells `[3,3],[3,4]`—is one
of p02's four shared witnesses: both s02 and t02 display `1,1` at those exact
cells. The archived content audit correctly says t02 differs from the provided
example, erroneous note, and planted target, but it does not test this complete
source/transfer witness intersection.

This is a **board-construction/endpoint overlap**, not evidence of a direct
prompt-byte leak or proof that the model literally copied hidden state. The
source board is absent from t02's transfer prompt and the carried note does not
name the successful witness. Nevertheless, because the accepted answer itself
does not change across boards, t02 cannot demonstrate board-specific
adaptation. Any downstream use of t02 may call it one grounded, externally
conditioned child output; it must not inherit a clean-transfer label.

## Echo, format and causal limits

No output is byte-identical to, or contains, its complete worked example. No
output contains a full parent explanation or source-board rendering. Process
s04 does repeat the example's exact citation with different lesson prose.
Process s07 is the only grounded source citation different from the example.
In addition, schema-invalid process s01 copies the example's group, digit and
both cells and appends a third cell; the frozen echo metric returns early on
invalid schema and therefore does not count this clear partial example reuse.

t02 is a field-for-field structural analogue of s02's JSON note and retains
the lesson template “Check [group] members for duplicates,” while changing the
answer values. That is compatible with format/template carry, but the common
task already mandates the same schema and no note-free t02 counterfactual was
run. Grounding could equally be ordinary base-model reading of the visible
second board. The format arm's 0/8 does not identify mediation from a single
stochastic draw whose entire source prompt and resulting note differ.

The arms are not token/compute matched. Process versus format source prompts
use 2,982 versus 2,880 actual tokens (+102); transfer prompts use 2,655 versus
2,656; totals are 5,637 versus 5,536 (+101), with output totals 652 versus 648.
Process explanation doses are 67 tokens on six pairs and 78 on two, versus 57
on every format pair. Together with eight pairs and one generation seed, this
permits only descriptive counts, not a reliable process-coaching effect.

Final disposition: preserve the raw result as a narrow feasibility
observation, correct any wording that treats t02 as clean changed-board
transfer, and preserve the explicit no-internalization/no-parenting boundary.
