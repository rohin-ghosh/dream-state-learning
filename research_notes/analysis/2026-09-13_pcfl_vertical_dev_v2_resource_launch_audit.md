# PCFL vertical DEV v2.1 resource and launch-readiness audit

**Date:** 2026-09-13 UTC  
**Scope:** read-only resource/scheduling audit; no source authoring, model or
tokenizer execution, fit, GPU mutation, reservation, or scientific redesign  
**Protocol:** `2026-09-13_pcfl_vertical_dev_v2_synthesis.md`  
**Implementation map:**
`2026-09-13_pcfl_vertical_dev_v2_implementation_reuse_map.md`

## Verdict

The passed design fits on one healthy eight-A40 node and does not need the
A100 node or the expiring node 1. The exact recommended authoritative
placement is **node 2 (`ipp2-ovx-p2-08`) only**. It supports the protocol's
peak of eight concurrent S1 fits, keeps all charged time in the protocol's
actual A40 units, and removes cross-node environment and custody seams.

The campaign is **scheduling-ready but not launch-ready**. Training work is
fully countable: 14 fits, 2,800 updates, and at most 7 aggregate A40-hours.
Inference is only capped, not yet completely enumerated. The runtime must
materialize and seal every formation, carrier, actor, service, native, cut,
control, and canary request and show that their worst-case measured device
time fits the 10 aggregate A40-hour allowance before a model is loaded.

## Fleet observation and accounting ruling

Read-only observations were made at 2026-09-13 06:38 UTC. These are vacancy
observations, not reservations or fresh control-plane lease attestations.

| wrapper | observed host/device state | lease evidence | ruling |
|---|---|---|---|
| `gpu/a40_ssh.sh` | node 1 `a4u8g-0105`; 8x A40 46,068 MiB, all reported 0 MiB | hard end 2026-09-14 23:14 UTC (16:14 Pacific), from the ratified launch addendum | Do not place authoritative work or unique artifacts here. The compute-process query timed out, and only about 40h36m remained at observation. |
| `gpu/ovx_ssh.sh` | node 2 `ipp2-ovx-p2-08`; 8x A40 46,068 MiB, all 0 MiB; compute-process query completed empty | end 2026-09-21 08:43 UTC from the addendum | **Use for the complete vertical.** Fresh vacancy/UUID checks remain mandatory at launch. |
| `gpu/ovx2_ssh.sh` | node 3 `ipp2-ovx-p6-09`; A40 indices 0--6 reported 0 MiB; index 7 was absent and the query timed out | end 2026-09-26 03:03 UTC; finish cutoff 2026-09-25 21:03 UTC | Do not use in the primary schedule until GPU 7 and the process table pass fail-closed checks. Optional overflow only after that; none is needed. |
| `gpu/a100_ssh.sh` | `a4u8g-0147`; 8x A100 80GB, all reported 0 MiB; compute-process query timed out | wrapper/addendum place lease through 2026-09-26 | Do not use for this frozen protocol. A100-hours are not A40-hours and no conversion is defined. Using it requires a prospective resource-unit amendment and actual A100-hour reporting. |

Preseal node 2's observed device roster, then revalidate it immediately before
launch:

```text
GPU0 GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0
GPU1 GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4
GPU2 GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05
GPU3 GPU-c9450d3d-0455-f034-b9bf-7f8956e44733
GPU4 GPU-d304a15c-516a-16a0-a926-a560304077cc
GPU5 GPU-0cc84073-37a0-4f7a-e555-11671425bd03
GPU6 GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf
GPU7 GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed
```

## Exact stage concurrency and node-2 assignment

No inference worker should share a GPU with a fit. This avoids turning the
30-minute fit cap into a contention measurement. A worker owns exactly one
GPU, process group, immutable stage root, and hard deadline.

| stage | concurrency | fixed node-2 assignment |
|---|---:|---|
| CPU cube/oracle/projection gate | 0 GPU | CPU only; all gates close before native work |
| zero-fit delayed/reachout ceilings | up to 8 inference workers | deterministic presealed shards on GPU0--7; finish and seal before DEV formation |
| disposable grammar-formation root | 1 | GPU0; freeze grammar/parser, then destroy its eligibility for DEV |
| DEV OLD formation | 2 | root 0 on GPU0; root 1 on GPU4 |
| S1 fits | **8 peak** | root 0 AUTH/ATOMS/EVENT_TWIN/LINK_PERMUTE on GPU0--3; root 1 same arm order on GPU4--7 |
| S1 evaluation | up to 8 | preserve the same root/arm affinity; only AUTH may progress |
| authentic primary reachout | 2 | root 0 AUTH on GPU0; root 1 AUTH on GPU4; one shot each |
| diagnostic reachout forks | up to 8 | read-only forks on GPU0--7 after authentic pre-outcome snapshots are sealed |
| public R continuations / NEW formation | 4 | root0 R0/R1 on GPU0/1; root1 R0/R1 on GPU4/5 |
| S2 fits | **6 peak** | root0 FULL_R0/FULL_R1/OLD_REPLAY on GPU0--2; root1 on GPU4--6; GPU3/7 idle until fits release |
| S2 evaluation | up to 8 | presealed deterministic shards on GPU0--7 |
| terminal seal/reduction | 0 GPU | CPU only; one reduction after all required roots/controls are present |

If one root stops at a progression gate, its unlaunched downstream workers do
not run. The sibling root and already-launched diagnostic controls may finish;
freed devices are not used to invent a replacement root or extra fit.

## Exact fit budget

Every fit has 20 response slots x 8 views = 160 singleton examples per epoch.
At batch 4, accumulation 1, and five epochs, that is 40 updates/epoch and
exactly 200 finite optimizer updates/fit.

| stage | fits | updates | maximum aggregate device time | maximum fit-stage wall time at prescribed concurrency |
|---|---:|---:|---:|---:|
| S1, two roots x four arms | 8 | 1,600 | 4 A40-hours | 30 minutes |
| S2, two roots x three arms | 6 | 1,200 | 3 A40-hours | 30 minutes |
| **total** | **14** | **2,800** | **7 A40-hours** | **60 minutes plus load/seal/cleanup barriers** |

The first scheduled S1_AUTH and S2_FULL_R0 are the two profiling fits already
inside this roster. They are not extra fits. Every worker still has the same
30-minute hard cap; a timeout is `VS_RESOURCE_CAP`, not permission to increase
the cap, retry, or choose another checkpoint.

## Inference budget: what is known and what is still missing

The immutable allowance is 10 aggregate A40-hours. The zero-fit portion alone
is exactly countable at the task level:

- delayed table: 10 conditions x 64 cells = **640 actor tasks**;
- reachout table: 5 conditions x 32 cells = **160 actor tasks**;
- total zero-fit actor tasks: **800**;
- maximum ACTIVE_LINKED_TEXT local reads: `64x12 + 32x12 = 1,152`;
- maximum active-service returned memory: `(64+32)x4096 = 393,216` tokens;
- maximum actor output over the 800 zero-fit tasks: **1,638,400 tokens**.

These figures are not the complete inference inventory. The protocol also
requires disposable and DEV formation, S1/S2 local-read panels, modular and
native route panels, cuts, OFF/wrong-root/cross-mount controls, reachout forks,
and 40-item canaries. Several thresholds state denominators, but the current
documents do not provide one machine-readable sum of every request, mount,
token ceiling, and stage. Therefore `10 A40-hours` is presently a ceiling, not
a proven executable budget.

Before launch, the preparer must emit an immutable request ledger with, per
stage and in total: actor generations, service generations, native mounted
generations, formation calls, canary calls, maximum input/output/returned
tokens, model loads, zero retries, and charged GPU seconds. The worst-case
ledger must fit 10 aggregate A40-hours using the sealed native profiles.
Device seconds are summed across workers; parallel wall time is never used as
aggregate cost. Eight-way parallelism gives only a theoretical 1.25-hour
lower bound for 10 aggregate hours, not a runtime promise.

## Failure containment

- Fresh process group and exactly one bound GPU UUID per stage; no ambiguous
  `CUDA_VISIBLE_DEVICES` and no shared fit/inference GPU.
- A nonzero, empty, malformed, or timed-out GPU/process query means release is
  unknown, never "0 MiB." The next worker cannot start until owned descendants
  are absent and the exact bound UUID is successfully observed free.
- Immutable stage roots and no resume, retry, replacement root, favorable
  decode, or post-output prompt/parser repair.
- Root-local stopping at the first ordered gate; sibling work remains isolated.
- Only the exact pre-evaluation S1_AUTH snapshot can enter reachout. Restore it
  after read-only evaluation; controls and service forks are tainted types and
  cannot enter lineage.
- S2 always starts from clean C0 with cumulative OLD+NEW material and a fresh
  optimizer; it never warm-starts S1 weights.
- Rejected candidates and every synthetic/control corpus remain sealed and
  quarantined through independent reduction.
- Terminal collection requires controller absence, verified GPU release,
  immutable seal, whole-root custody, and one deterministic reduction.

## Must be sealed before launch

1. Two agreeing CPU oracles, complete cube/cut/collision/shortcut report, and
   every mandatory deterministic gate.
2. Exact model/tokenizer/chat-template/environment/source hashes and the
   node-2 UUID roster above, freshly revalidated.
3. Real-tokenizer arm materialization: the exact 17+3, 14+6, 19+1, and 17+3
   semantic/PAD rosters; 20 slots, eight views, 160 singleton sequences, equal
   target tokens, no physical packing, and no truncation.
4. Trainer contract: explicit AdamW values, grad clipping 1.0, clean C0/fresh
   optimizer, five sealed epoch orders, exactly 200 updates, and complete
   loss/gradient/RNG/tensor/optimizer receipts.
5. The complete request/resource ledger proving the 7 training + 10 inference
   A40-hour caps, with per-worker deadlines and no retry budget.
6. The deterministic DAG, root/arm/GPU table, authentic/control taint graph,
   stage dependencies, progression labels, rollback identities, and terminal
   artifact allowlist.
7. Linux CPU-suite receipt proving visibility isolation, especially no OLD
   textual reinjection after S1, no service fork into lineage, no control
   ancestry, fail-closed cleanup, and one terminal reduction.
8. Zero-fit native ceilings and then the disposable formation root must pass
   in protocol order before either DEV root exists.

With those seals, no resource acquisition or node-1 migration is needed. The
authoritative two-root DEV fits on node 2 with substantial lease margin while
keeping every charged device-hour in the frozen protocol's declared unit.
