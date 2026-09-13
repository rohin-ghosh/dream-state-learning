# TSJ-v4 narrow source-contract closure

**Date:** 2026-09-13 PT  
**Status:** textual source contract. On adoption, `GO_CPU_SOURCE=true` under
Section 7 only. This is not authority for preparation, tokenizer/model calls,
scientific materialization, child formation, fits, adapters, GPU use, claim,
or release.  
**Imports without modification:** TSJ-v3 at commit
`ac1feacb08581adf60972adc14eabd501c13847b`, SHA-256
`fafbd7818f607e0227328b13b47068f9d1493e244a297fc3c7e18bd882b61ad9`,
except where this document expressly supersedes it.  
**Upstream:** M-COMBINE-v2 commit `654b54dc`, SHA-256
`dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74`.  
**Closes:** P0.A--P0.E of the fresh TSJ-v3 source audit. The XOR estimand,
paired worlds, authentic lineage, coherent response forks, RAW construction,
68-rollout roster, and narrow claim do not change.

## 1. Treatment-invariant unit slots (P0.A)

The following integer slot table is created before any transform. `slot_key`
is the authentic semantic role and never changes across arms:

```text
00 E.s0   01 E.s1   02 E.t0   03 E.t1
04 E.i0   05 E.i1   06 E.i2   07 E.i3
08 L.LS0  09 L.LS1  10 L.IL0  11 L.IL1
12 E.n0   13 E.n1   14 L.NL0  15 L.NL1
```

S1 uses slots 00--11; S2 uses 00--15. Compiled tape order is exactly
`repeat_ordinal 0..24`, then `view_ordinal 0..7`, then integer `slot`; it is
never ordered by row hash. Every arm's presentation at a slot consumes the
same batch position and dropout/RNG draw as AUTH. The manifest row is exactly:

```text
stage,arm,slot,slot_key,treatment_type,before_auth_sha256,
after_treatment_sha256,before_address_sha256,after_address_sha256,
private_provenance_type
```

AUTH has identical before/after hashes. O/T/N, cuts, ATOM, and OLD_FILLER keep
the slot key and record their actual replacement hash. A missing/duplicated
slot, changed ordering, or absent before/after hash is preparation failure.
RAW alone uses its separately bound tokenizer-solved slot/batch assignment and
makes no paired-dropout claim.

The proportional BIRTH/memory batch weave from v3 remains unchanged. The
semantic-slot correction changes no presentation or update count.

## 2. Complete filler and island contract (P0.B)

### 2.1 Authentic irrelevant islands

The previously mnemonic island rows are now exact role laws:

```text
i0: D0 --u0--> E0       i1: E0 --v0--> J0
i2: D1 --u1--> E1       i3: E1 --v1--> J1
IL0: FIRST i0 SECOND i1 VIA E0
IL1: FIRST i2 SECOND i3 VIA E1
```

They occupy E slots 04--07 and LINK slots 10--11. No task starts at, reaches,
names, or queries D/E/J nodes except cold coverage.

### 2.2 ATOM link fillers

This Section 2 replaces v3 Section 2.3's filler inventory in full; no unnamed
four-block/two-block reserve survives. There are exactly six
`ATOM_LINK_FILLER` rows/world, AF0..AF5. Each has one
private synthetic second-parent EVENT `CP0..CP5`. CP rows exist in the private
control registry and receipt ledger but are not memory presentations. The map
is total and has no replacement choice:

|slot|auth row/address|filler FIRST|filler SECOND|CP SOURCE|reuse|
|---:|---|---|---|---|---|
|08|LS0 / `LINKS_FROM s0 SLOT 0`|s0|CP0|`s0.DEST`|S1+S2 ATOM|
|09|LS1 / `LINKS_FROM s1 SLOT 0`|s1|CP1|`s1.DEST`|S1+S2 ATOM|
|10|IL0 / `LINKS_FROM i0 SLOT 0`|i0|CP2|E0|S1+S2 ATOM|
|11|IL1 / `LINKS_FROM i2 SLOT 0`|i2|CP3|E1|S1+S2 ATOM|
|14|NL0 / `LINKS_FROM t_T SLOT 0`|`t_T`|CP4|F0|S2 ATOM only|
|15|NL1 / `LINKS_FROM t_(1 xor T) SLOT 0`|`t_(1 xor T)`|CP5|F1|S2 ATOM only|

For k=0..5:

```text
CPk = EVENT <control-event-id-k> SOURCE <listed-source> PORT <control-port-k>
      DEST <control-node-k> PROVENANCE <control-prov-event-k>
AFk = LINK <control-link-id-k> FIRST <listed-auth-event> SECOND <CPk-id>
      VIA <listed-source> PROVENANCE <control-prov-link-k>
```

Line wrapping above is expository; material uses the canonical one-line EVENT/
LINK grammar. AFk occupies the authentic slot and exact public request address
listed in the table, despite receiving control-only row bytes. Its FIRST.DEST
equals CPk.SOURCE equals VIA. CP/AF private provenance is
`SYNTHETIC_CONTROL`; transform receipts cite the authentic slot and both
private parents. No factual receipt is fabricated. AF0..AF3 bytes are reused
unchanged in S2 ATOM; AF4..AF5 are added. Reuse is exact replay, not duplicate
allocation. The ATOM tape keeps all authentic EVENT slots and replaces only
LINK slots with AF rows.

### 2.3 Cut block and matched S2 filler

There is exactly one cut block `CB0` per world:

```text
CB0.e0: C0 --cp0--> C1
CB0.e1: C1 --cp1--> C2
CB0.l0: FIRST CB0.e0 SECOND CB0.e1 VIA C1
```

All identifiers/receipts/provenance are control-only. `RELEVANT_CUT` replaces
the two EVENT slots and LINK slot on the primary old route with these same
three row bytes; `IRRELEVANT_CUT` replaces slots 04,05,10 with the exact same
bytes. Rows occupy treatment-invariant target slots; per-slot hashes expose
the different placement. CB0 EVENT public addresses are their canonical
control-only SOURCE/slot addresses and CB0 LINK address is LINKS_FROM CB0.e0
slot0; the three removed authentic addresses return MISS. These before/after
address hashes are explicit in the slot manifest. There is no donor or
alternate block.

There is exactly one S2 matched-filler block `MF0`:

```text
MF0.e0: SOURCE F0 PORT <control> DEST Z0
MF0.e1: SOURCE F1 PORT <control> DEST Z1
MF0.l0: FIRST t_T SECOND MF0.e0 VIA F0
MF0.l1: FIRST t_(1 xor T) SECOND MF0.e1 VIA F1
```

All four rows are privately synthetic, receipt-bearing control transforms.
They replace slots 12--15 respectively in OLD_FILLER. Their exact public
addresses are EVENT_AT F0/F1 slot0, direct EVENT MF0.e0/e1, and LINKS_FROM the
two named tail events slot0. The rest of the bank is exact authentic OLD.
No H ID, N destination, or authentic NEW receipt enters MF0.

All control IDs are allocated by v3's treatment-blind ID law. Target-token,
padding, and per-slot equality are certified only at GO_PREPARE; UNSAT stops
the whole version.

## 3. Sole executable phase/gate ledger (P0.C)

The v3 Section-7 phase ledger remains the sole execution roster, with these
machine-readable amendments; Section 8 is generated from them and has no
independent authority.

### 3.1 ATOM is a gate everywhere

P10 `ATOM_TEXT` and P50 `ATOM_TEXT` are changed from `diagnostic` to `gate`.
Their predicate is `success <=1/2` independently in W0 and W1. P30 S1 ATOM
and P70 S2 ATOM retain the same root-local `<=1/2` gate. Any 2/2 ATOM text or
native state stops the corresponding stage; LINK-added-value cannot be claimed
or rescued by another world. RAW alone remains diagnostic except for its
interface/custody/feasibility gates.

### 3.2 Imported reduced-controller baseline row

Insert zero-call phase `P05_IMPORT_CONTROLLER_BASELINE` before P10. It imports
from the content-bound upstream receipt exact raw output/call hashes for:

```text
SEEK pairs 0,2,4,6       denominator 4
PROSPECT pairs 0,2,4,6   denominator 4
CHECK pairs 0,2,4,6      denominator 4
CONTINUE pairs 0,2,4,6   denominator 4
typed intervention calls denominator 32
chain tasks 0,4,8,12,16,20,24,28 denominator 8
chain useful-pre-STEP-READ denominator 8
chain typed-STEP denominator 8
canaries 0..15 denominator 16
```

The selected BIRTH subset itself must meet: both pair members correct >=3/4
per skill, typed intervention calls >=30/32, chain success >=6/8, useful
pre-STEP READ >=7/8, typed STEP >=7/8, canaries >=15/16. Otherwise TSJ stops.

P31 and P71 use the same denominators and absolute minima. In addition, each
integer count must be at least its imported BIRTH subset count minus one;
this comparison applies separately to each of four skill counts and to typed,
chain-success, useful-READ, typed-STEP, and canary counts. A ratio is never
rounded or compared across different denominators.

Exact call ledger:

```text
C001..C032   four skills in SEEK,PROSPECT,CHECK,CONTINUE order;
             within skill pair 0,2,4,6; lower member then upper member
C033..C264   eight chains in 0,4,8,12,16,20,24,28 order;
             exactly 29 reserved call slots/task, unused tail slots EMPTY
C265..C280   aliases to that stage AUTH cold-canary Q calls 00..15
```

Aliases execute zero new calls and inherit identical raw hashes. EMPTY chain
slots consume no call/token budget. A malformed/rejected/stopped output counts
zero in its fixed denominator; there is no retry or denominator reduction.

### 3.3 Generated truth/resource totals

No model row was added: P05 is imported/zero-call, ATOM role changed only, and
preservation aliases were already counted. Regeneration from the amended
ledger therefore yields exactly:

```text
route rollouts/world       12+18+16+22 = 68
actor calls/world          68*22 = 1,496
native reader calls        (16+18)*10 = 340
cold/canary calls          7*60+6*70 = 840
formation calls            20+6 = 26
incremental preservation   2*(32+8*29) = 528
model calls/world          3,230
model calls/pair           6,460
generated tokens/world     572,096
generated tokens/pair      1,144,192
```

Fits remain 13/world, 26/pair. D1 remains 24,656 updates/98,624
presentations/pair; D2 31,312/125,248. Max padded tokens remain
1,615,855,616 D1 and 2,052,063,232 D2. The generated JSON truth and resource
ledgers must byte-match these totals or source audit fails.

## 4. Tokenizer-only GO_PREPARE (P0.D)

Authorization sequence is now noncircular:

```text
adopt v4 -> GO_CPU_SOURCE
two CPU implementations + fresh source audit pass -> GO_PREPARE
GO_PREPARE receipt passes -> eligibility for later GO_MODEL/GO_FIT review
```

`GO_PREPARE` authorizes exactly one deterministic CPU preparation of the
paired W0/W1 sealed root from the fixed master and the pinned upstream
tokenizer only. GPU use is forbidden. Allowed outputs are:

- concrete public/private ID and role manifests and their hashes;
- sealed potential-outcome/topology bytes (evaluator custody only);
- exact rendered messages/rows, semantic-slot before/after hashes, transform
  diff receipts, and phase/truth/resource JSON ledgers;
- tokenizer IDs/lengths/round-trip hashes; literal/normalized/token-ID/
  namespace/rooted-topology overlap reports;
- compiled and RAW target/loss-run counts;
- lexicographically selected RAW multiplicity/batch witness;
- exact batch padding, padded-token, and stopping-budget-FLOP manifests;
- CPU oracle/checker outputs, all required to be perfect.

It forbids model weight loading, forward/generation calls, child/parent calls,
formation, benchmark scoring, adapter creation/mounting/training, optimizer
steps, CUDA/GPU, alternate seed/root generation, result inspection, and any
scientific claim. Only the single pinned tokenizer and deterministic CPU code
may execute. `RAW_UNSAT`, overlap, round-trip failure, nonunique slot, or
oracle disagreement stops TSJ-v4; no regenerated root is allowed.

The GO_PREPARE receipt content-addresses every allowed output. Only a later
explicit grant may expose public root bytes to model execution; private
answers remain evaluator-only.

## 5. Remaining literal pins (P0.E)

### 5.1 Actor grammar

After removal of at most one terminal LF, raw ASCII output must full-match one
and only one anchored regex:

```text
\ATHINK (?=.{1,256}\Z)[!-~](?:[ -~]*[!-~])?\Z
\AREAD EVENT_AT TS3N_[A-Z2-7]{12} SLOT [01]\Z
\AREAD LINKS_FROM TS3E_[A-Z2-7]{12} SLOT [01]\Z
\AREAD EVENT TS3E_[A-Z2-7]{12}\Z
\ASTEP TS3P_[A-Z2-7]{12}\Z
\ASTOP\Z
```

Regexes operate on ASCII bytes, not Unicode codepoints; `.` cannot match LF.
THINK body is 1--256 bytes, printable ASCII 0x20--0x7e, first/last byte not
space. Empty, leading/trailing-space, tab, CR/LF, non-ASCII, Markdown, or
multi-line bodies are malformed. THINK is capped by both this byte rule and
the v3 per-call token cap.

### 5.2 Invalid sentinels and reserved inventory

These four exact bytes are permanently reserved and never allocated:

```text
TS3N_AAAAAAAAAAAA
TS3N_AAAAAAAAAAAB
TS3E_AAAAAAAAAAAA
TS3E_AAAAAAAAAAAB
```

The four cold invalid request bytes, in order, are:

```text
READ EVENT_AT TS3N_AAAAAAAAAAAA SLOT 0
READ EVENT_AT TS3N_AAAAAAAAAAAB SLOT 1
READ LINKS_FROM TS3E_AAAAAAAAAAAA SLOT 0
READ EVENT TS3E_AAAAAAAAAAAB
```

Every returns exact `MISS`. `confirmation_reserved` allocates exactly 4,096
IDs **per kind total**, using world byte 0xff and serials 0..4095; it reserves
identifiers only and materializes no topology/answer.

### 5.3 Seed bytes and writer linkage

Construction world encoding is one byte: W0=`0x00`, W1=`0x01`, reserved=
`0xff`. `uint32_big_endian` is network-order four bytes. The v3 literal writer
seeds are integers `0x54534a3300000000` and `0x54534a3300000001`, encoded as
unsigned 8-byte big-endian strings. Stage bytes are exact ASCII `S1` or `S2`;
stream bytes are exact ASCII `dropout`, `optimizer`, or `collator`.

```text
stream_digest = SHA256(writer_seed_uint64_be || NUL || stage_ascii ||
                       NUL || stream_ascii)
stream_seed = unsigned_big_endian_integer(stream_digest[24:32])
```

Thus `low64` means the final eight digest bytes interpreted unsigned big-
endian. Every arm in one world/stage receives the same three stream seeds;
arm name never enters derivation. The receipt records input bytes/digest/
integer. Greedy decode consumes no RNG; imported decode seeds remain logged.

### 5.4 Parameter count and FLOP stop

`imported_parameter_count` is an upstream-receipt integer equal to the sum of
`numel` over every uniquely named loaded base-model tensor plus the largest
active rank-8 adapter tensor set, excluding optimizer states, gradients,
duplicate storage aliases, tokenizer, and KV cache. Two independent readers
of the safetensors/adapter index must agree.

```text
FLOP_STOP = 8 * imported_parameter_count * exact_padded_training_tokens
```

This is a conservative stopping budget and arm-matching proxy, not an identity
for hardware-profiler FLOPs and not feasibility evidence. The run stops before
an update that would make the cumulative proxy exceed it. Profiler counters
are reported separately and cannot replace/redefine the budget. The existing
248 GPU-hour and 72 elapsed-hour numbers are hard stops, not derived claims of
feasibility.

## 6. Claim and ITT remain unchanged

Every root-local v3 predicate remains noncompensatory. Formation failure,
malformed output, ATOM gate failure, rejected write, controller loss, cap
exhaustion, or scientific timeout remains zero/stopped under ITT. There is no
replacement root/seed or scientific retry. The sole pre-side-effect
infrastructure restart rule remains unchanged.

Maximum wording remains only a paired two-world DEV mechanism demonstration
conditional on one selected BIRTH child. No reliability, parenting, lifetime
improvement, active-text superiority, autonomous OLD exploration, physical
compression, general continual learning, emergence, or whole-flywheel claim
is licensed.

## 7. Authorization and self-audit

On adoption, CPU source/checker authors may implement this content-addressed
contract with dummy identifiers/fake tokenizer tests and fail-closed schemas.
They may not perform GO_PREPARE until two implementations and a fresh source
audit pass. This document itself authorizes no tokenizer/model/scientific/GPU
execution.

|blocker|closure|
|---|---|
|P0.A|integer semantic slots invariant across treatment; per-slot before/after/address/provenance hashes|
|P0.B|IL0/IL1 explicit; AF0..AF5 total ATOM map, exact reuse/addresses/parents/provenance; CB0/MF0 exact|
|P0.C|ATOM uniformly gates; every reduced-controller denominator/minimum/BIRTH-drop/alias in sole ledger|
|P0.D|separate tokenizer-only GO_PREPARE with exhaustive allow/deny outputs and RAW_UNSAT stop|
|P0.E|THINK/full grammar, four sentinel bytes, 4,096 reserved/kind, seed bytes/low64 linkage, parameter/FLOP semantics|

**Designer verdict: GO_CPU_SOURCE after adoption; GO_PREPARE only after two
CPU implementations and fresh source audit; all model/fit/GPU/claim gates
remain false.**
