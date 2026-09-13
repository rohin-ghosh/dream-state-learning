# PCFL vertical DEV v2.1: exact inference inventory and residual profile

**Date:** 2026-09-13 UTC  
**Scope:** read-only accounting over the passed protocol, exact build ledger,
resource audit, and existing A40 receipts; no source/model/tokenizer/GPU work and
no experiment redesign  
**Controlling protocol:**
`2026-09-13_pcfl_vertical_dev_v2_synthesis.md`

## Verdict

The protocol fixes the scientific task denominators, but it does **not** yet
fix one finite physical generation total. The countable full-pass core has:

- exactly **800 zero-fit actor tasks**;
- exactly **224 S1 standalone carrier/absence reads**;
- exactly **224 S1 route-task cells** under the minimum one-endpoint reading;
- exactly **82 reachout task cells**;
- **576 mandatory S2 task cells**, rising to **704** if both endpoint-ambiguous
  comparisons are required at both service and native endpoints;
- 24 exact S2 NEW-row read generations, plus an implied but not enumerated
  64-call OLD-retention panel; and
- **280 unique canary model-state x item cells**, requiring 280--480 physical
  calls depending whether identical C0 outputs may be reused.

An interactive service task is not one physical generation: with `r` reads it
uses `r+1` actor generations and `r` memory-worker generations, where
`0 <= r <= 12`. Under the natural one-command-per-generation runtime and one
endpoint for each ambiguous comparison, the countable core therefore spans
roughly **2,274 to 18,346 physical generations before formation**. That is an
accounting envelope, not a newly frozen protocol number.

There is no authoritative campaign maximum because the disposable/OLD/NEW
formation call caps, formation/direct-read/canary output caps, prompt-token
ceilings, C0-canary reuse rule, and four endpoint assignments are absent. Thus
the existing `10 aggregate A40-hours` is a hard runtime stop, not yet a proven
feasibility bound.

## Counting conventions

Three quantities must remain separate:

1. A **task cell** is one fixed-denominator scientific item.
2. An **actor generation** is one model continuation. In a service loop, each
   emitted `READ` stops generation, receives a response, and requires another
   actor continuation; `r` reads therefore mean `r+1` actor generations.
3. A **memory generation** is one C0+LoRA worker continuation for one local
   request. Deterministic linked-text lookup is a read but not a GPU model call.

All counts below are for both DEV roots unless explicitly marked otherwise.
They assume both roots reach every gate; ordered early stops only reduce work.

## Exact stage inventory

### 0. CPU construct gate

Exactly 32 worlds, 64 delayed tasks, 48 atoms/link decisions, and 192 route/
cut parser decisions are CPU-only. They use **zero model generations**.

### 1. Zero-fit ceilings

| portion | fixed tasks | actor generations | local reads / memory generations | fixed output ceiling |
|---|---:|---:|---:|---:|
| delayed, nine one-shot conditions other than `ACTIVE_LINKED_TEXT` | 576 | 576 | 0 | 1,179,648 actor tokens |
| delayed `ACTIVE_LINKED_TEXT` | 64 | 64--832 | 0--768 deterministic reads; 0 model-memory calls | 131,072 actor + 262,144 returned tokens |
| reachout, four one-shot conditions other than `ACTIVE_LINKED_TEXT` | 128 | 128 | 0 | 262,144 actor tokens |
| reachout `ACTIVE_LINKED_TEXT` | 32 | 32--416 | 0--384 deterministic reads; 0 model-memory calls | 65,536 actor + 131,072 returned tokens |
| **zero-fit total** | **800** | **800--1,952** | **0--1,152 deterministic reads** | **1,638,400 actor + 393,216 returned tokens** |

The `2048` actor-token limit is per task, not per continuation. The returned
token ceiling is relevant to later actor prefill but is not a LoRA-worker
decode cost for these text-backed zero-fit cells.

### 2. Formation

| portion | fixed semantic requirement | model-call status |
|---|---:|---|
| disposable formation-only root | one skeleton; grammar/parser must freeze | number of public actions, authoring calls, attempts, and output tokens unspecified |
| DEV OLD formation | 16 executed EVENT receipts, 16 exact EVENT rows, 8 exact LINK rows | at least one child authoring response per root if rows may be grouped (**>=2** total); no finite call/attempt/output cap |
| DEV NEW formation | four R continuations, 4 exact EVENT rows, 8 exact LINK rows | at least one authoring response per continuation (**>=4** total); no finite call/attempt/output cap |

The physical-line rule does not say “one line per generation.” Nor does the
protocol enumerate the wake calls that produce the old public receipts.
Consequently `24 OLD + 12 NEW` exact authored lines do not imply 36 calls.

### 3. S1 carrier, traversal, and controls

Standalone goal-blind memory-worker generations are exact:

| panel | arithmetic | calls |
|---|---:|---:|
| EVENT reads | 4 arms x 16 x 2 roots | 128 |
| LINK reads, including held-out ATOMS addresses | 4 arms x 8 x 2 | 64 |
| unseen plus wrong-root absence | 16 x 2 | 32 |
| **standalone S1 reads** | | **224** |

Route-task cells are:

| panel | cells |
|---|---:|
| AUTH and ATOMS memory-service OLD route | 2 arms x 16 x 2 = 64 |
| critical-result service cut | 16 x 2 = 32 |
| AUTH and ATOMS native OLD route | 2 arms x 16 x 2 = 64 |
| EVENT_TWIN and LINK_PERMUTE registered redirection | 2 arms x 16 x 2 = 64 |
| **S1 route total** | **224** |

The last 64 denominators are fixed, but the final protocol does not say
whether each runs through the service endpoint, the native endpoint, or both.
With exactly one endpoint each, service tasks therefore range 96--160 and
native one-shot tasks 64--128, always totaling 224. Physical calls range from
224 (no reads) through 4,064 (160 service tasks each using all 12 reads, plus
64 native calls), before the 224 standalone calls. Requiring both endpoints
for either control would add calls and is not authorized by the present text.

Across the 224 task cells, the actor/native output ceiling is **458,752**
tokens. Parametric service returns can reach **393,216--655,360** tokens,
depending on the endpoint assignment. The 224 standalone outputs have no
declared decode-token cap.

### 4. S1 canary and reachout

S1 has two authentic candidates, one per root. Its 40-item paired canaries
contain 80 candidate calls plus either 40 shared or 80 separately re-executed
C0 calls: **120--160 physical calls**.

Reachout is exact at the task level:

| panel | task cells |
|---|---:|
| one lineage-entering native primary per root | 2 |
| native AUTH robustness | 8 x 2 = 16 |
| service AUTH / critical cut / OFF / wrong-root | 4 x 8 x 2 = 64 |
| **reachout total** | **82** |

The 64 service tasks require 64--832 actor generations and 0--768 memory
generations; adding 18 native calls gives **82--1,618 physical calls**. The
actor/native output ceiling is **167,936** tokens and the returned-memory
ceiling is **262,144** tokens.

### 5. S2 carrier, retention, joint use, and controls

The NEW-carrier panel fixes **24** memory-worker generations:
`2 FULL arms x 6 held reads x 2 roots`. “Every critical OLD read remains
within 1/16” implies one 16-cell comparison per FULL adapter, hence 64 more
calls under the obvious implementation, but the protocol never names those
64 addresses/views. Treat **64 as implied, not sealed**, until the preparer
materializes that roster.

The endpoint task cells are:

| panel | task cells | endpoint status |
|---|---:|---|
| FULL delayed panels | 64 service + 64 native | explicit |
| OLD and NEW service cuts | 128 service | explicit |
| OFF and wrong-root | 64 service + 64 native | explicit |
| FULL cross-mounts | 64 native | explicit |
| OLD-route retention after each FULL | 64 | service versus native not stated |
| pooled OLD_REPLAY comparison | 64 | service versus native not stated |
| **mandatory one-endpoint total** | **576** | 256 explicit service + 192 explicit native + 128 unassigned |

If each unassigned panel is performed at one endpoint, there are exactly 576
task cells. If “OLD route” and “pooled FULL success” are each intended at both
endpoints, there are 704. Depending on the binding, there are 256--384 service
tasks and 192--320 native one-shot tasks. The corresponding physical range is
576 calls with no reads to at most **9,920** calls (384 service tasks x
`13 actor + 12 memory`, plus 320 native).

The task-level actor/native output ceiling is 1,179,648 tokens for 576 cells,
or 1,441,792 for 704. Parametric returned memory is at most
1,048,576--1,572,864 tokens. The 24 exact and 64 implied standalone-carrier
outputs have no decode-token cap.

### 6. All canaries

There are six authentic candidate adapters: two S1_AUTH and four S2_FULL.
Therefore the fixed scientific panel contains **240 candidate-item cells**.
One globally reusable deterministic C0 panel adds 40, for **280 unique
model-state x item cells**. Re-executing the C0 side per root or per candidate
raises physical calls to 320 or 480. The protocol requires paired common-random
outputs but does not bind reuse. Canary prompt-token and decode-token ceilings
are also unspecified.

## What can and cannot be totaled

Under the minimum one-endpoint interpretation, global C0-canary reuse, the
implied 64 OLD-retention reads, and one command per generation, the countable
non-formation core has this execution envelope:

```text
minimum: 800 zero-fit
       + 224 S1 standalone
       + 224 S1 route
       + 82 reachout
       + 88 S2 standalone
       + 576 S2 endpoint tasks
       + 280 canary
       = 2,274 physical generations

maximum: 1,952 zero-fit
       + 224 S1 standalone
       + 4,064 S1 route
       + 1,618 reachout
       + 88 S2 standalone
       + 9,920 S2 endpoint work
       + 480 canary
       = 18,346 physical generations
```

This is not an authoritative protocol min/max: formation is absent; the
maximum assumes only one endpoint for the two ambiguous S2 comparisons; and
several output caps are absent. The only honest campaign statement is:

```text
physical generations >= 2,274 + formation calls
physical generations maximum = unspecified
```

The specified task-level actor ceiling, excluding formation, carrier-only
reads, and canaries, is **3,444,736--3,706,880 generated tokens**. Returned
memory can contribute another **2,097,152--2,883,584 tokens** to actor inputs.
There is no global prompt-token ceiling.

## Evidence-only A40 timing conclusion

Existing receipts establish that this runtime family is operational, but not
a lower-bounded throughput for the vertical:

| observed A40 workload | measured evidence |
|---|---|
| L2 public-record | 128 generations; 18,315 prompt + 1,768 output tokens; 62.084 generation seconds; 1,365.515 controller seconds including three fits/11 stages |
| conditional root0 | 672 generations; 46,581 input + 18,848 output tokens; 666.024 summed call seconds; 1,527.157 controller seconds |
| projected-formation AUTH | 56 calls; 24,983 input + 1,541 output tokens; 79.493 summed call seconds; 293.498 controller seconds |
| fresh-behavior reread | 384 generations; 96,000 requested output-token cap; 2,411.314 aggregate controller seconds; actual token counts unavailable |
| sequential-memory | 640 requests plus its fits; 1,327.461 seconds from reservation to verified vacancy |

These workloads differ in prompt length, output length, batching, number of
fresh loads, adapter route, and interactive stops. None is a certified minimum
tokens/second for a future request.

As a deliberately conservative stress calculation—not a forecast—the slowest
observed known-output call ratio above is projected-formation AUTH:
`79.492846 / 1541 = 0.051585 A40-seconds per actual output token`. Pricing only
the zero-fit actor ceiling of 1,638,400 tokens at that observed ratio gives
**84,517 A40-seconds = 23.48 A40-hours**, before prompt prefill, deterministic
memory returns, model loads, or any later stage. Pricing the countable
task-level actor ceiling gives about **49.4--53.1 A40-hours**. This does not say
the model will consume its caps; prior runs usually stopped far earlier. It
does prove that the current token maxima plus historical observations cannot
certify the 10-hour allowance.

Therefore:

- **likely operational feasibility:** plausible, because measured natural
  completions are short and 8-way parallelism reduces wall time;
- **aggregate 10-hour feasibility:** unproven;
- **finite worst-case bound from the frozen documents:** impossible, because
  formation/canary/direct-read caps and a complete request inventory are absent;
- **parallel wall time:** never substitutes for summed A40 device seconds.

## Smallest preparer-time receipt that closes the gap

Before any DEV output exists, the preparer must emit one immutable request and
profile receipt containing only the following:

1. **Exact inventory resolution:** bind the two endpoint assignments, the 64
   OLD-retention addresses/views, C0-canary reuse rule, disposable/OLD/NEW
   formation action/authoring/attempt caps, every direct-read/canary/formation
   decode cap, every prompt token count, and the exact number of fresh model/
   adapter loads. This is accounting, not a new scientific cell.
2. **Four maximum-shape excluded-data profiles, each including cold load and
   release:** (a) one-shot base/native actor; (b) one complete 12-read
   clean-actor + LoRA-worker service loop; (c) standalone LoRA memory read; and
   (d) formation/canary generation. Use the longest presealed prompt in that
   class and force the newly bound maximum output lengths; an ordinary early
   stop is not a worst-case profile.
3. **Mechanical multiplication:** multiply the measured device seconds for
   each profile class by the now-exact inventory, add the exact number of cold
   loads, and require the sum `<=36,000 A40-seconds`. Preserve per-stage hard
   timers and the aggregate runtime abort regardless of the profile result.

If one class subsumes another after exact prompt/cap comparison, the preparer
may use the slower measured class and omit the redundant profile. No
throughput constant, batching gain, A100 conversion, or safety multiplier may
be invented. If this receipt does not fit 10 hours, the frozen run must stop as
`VS_RESOURCE_CAP`; the implementation cannot silently shrink scientific
denominators, raise the cap, or borrow parallel wall time.

## Launch disposition

The exact training ledger remains closed at 14 fits / 2,800 updates / 7
A40-hours. **No scientific launch is permitted until prospective finite
formation-call and output-token caps are added and the receipt above binds the
remaining physical work.** This is one preparation closure, not a reason to
redesign the passed world or add another deliberation round.
