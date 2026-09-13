# Independent terminal audit: PCFL EVENT-only paired reduction

**Date:** 2026-09-13 PT

**Runtime label:** `SCOPED_EVENT_PREFIX_ACQUISITION_PASS`

**Scientific disposition:** **SUPPORTED, narrowly, on one disposable
development root and one fit. No blocker to retaining this component result;
no promotion to full-objective qualification.**

This was a documentation-only, read-only audit of the authoritative node-2
root
`/localhome/local-rohing/astra_diagnostics/pcfl_event_only_20260913_attempt1`
and the helper reduction
`/tmp/astra_pcfl_event_only_analysis_20260913_attempt2`. I did not alter or
restart a process, invoke a model or tokenizer, load an adapter, or use a GPU.
Raw generations remained in the bound archives.

## Bottom line

The endpoint is real within its deliberately small scope. A rank-8 adapter
trained on address blocks compiled from eight admitted child EVENT records
reproduced all fourteen registered mappings under both the trained wrapper
and a held wrapper after the source history was removed. The same cold base
without that adapter reproduced none:

| Read view | `AUTH_WRITE` exact bytes + stop | `NO_WRITE_C0` exact bytes + stop |
| --- | ---: | ---: |
| W0, trained surface | 14/14 | 0/14 |
| W8, held wrapper only | 14/14 | 0/14 |

Both ordered paired vectors are therefore `AUTH=[1 x 14]` and `C0=[0 x 14]`;
all 56 generations ended normally. W8 holds out only the request wording. It
does **not** hold out any address or fact.

This closes one previously weak component in the objective ladder:

> On this one development life, the system can take the child's own admitted
> action--outcome records, compile them into a LoRA, withdraw the source, and
> cold-read the exact registered blocks through a second request wrapper.

It does not establish connection formation, LINK storage, graph traversal,
goal-conditioned use, retention through later writes, new-address or
new-fact generalization, lifetime improvement, parenting, no-harm, or the
whole Dream--Sleep--Think organism.

## 1. Source-prefix legitimacy and exact eight-EVENT provenance

The imported prefix is not a selected successful life. It is exactly calls
`0..15` from the already fixed SEQ-171 attempt: eight chronological
EXPLORE/EVENT pairs, with EVENT call indices `1,3,...,15`. All sixteen slots
were accepted before call 16 attempted a LINK and failed. That LINK remains
excluded, and the enclosing run remains `FORMATION_FAILED`, return code 1,
17 attempted calls, 8 accepted EVENTs, 0 accepted LINKs, 0 fits, and 0
updates.

Independent joins on the authoritative archive found:

- exactly 68 original actor sidecars, four for each of 17 calls, all joined
  byte-for-byte to the corresponding attempt records;
- exactly eight imported rows, all `EVENT`, `CHILD_SUBMISSION`,
  `disposable/0`, and `fixture_only=false`;
- every row's raw-byte hash equals both its row hash and recorded generation
  hash, and every odd-slot admitted row equals the imported row;
- the source actor identity is the pinned Qwen2.5-7B-Instruct revision, C0
  mount, no LoRA request, with actor config, environment, GPU, model binding,
  and source-file maps joined;
- the actual-tokenizer receipt is sealed, binds this import, checks all 16
  original calls, and records zero new model calls.

The legacy row field `native_generation_verified=false` is preserved rather
than rewritten. The external archive/identity/capture audit above is the
basis for the bounded child-native provenance statement; this must not be
rephrased as clean-lineage certification. The original decoder supplied only
the target-free one-line/LF shape. Thus the correct scientific description is
**externally format-assisted controlled EVENT curriculum**, not autonomous
discovery or learned serialization.

The eight EVENTs materialize fourteen address blocks: eight `READ EVENT` and
six `READ EVENTS_AT`. Two `EVENTS_AT` blocks contain two rows, but that is
compiler aggregation over witnessed EVENTs, not a child-authored connection
or LINK.

## 2. Exact fit arithmetic

The executed schedule and writer receipts agree:

| Quantity | Audited value |
| --- | ---: |
| underlying child EVENTs | 8 |
| original registered address blocks | 14 |
| deterministic replay blocks | 6 |
| scheduled blocks per view | 20 |
| training wrappers | W0--W7 (8) |
| encoded examples per epoch | 160 |
| epochs | 5 |
| presentations / training forwards | 800 / 800 |
| examples per optimizer update | 4 |
| optimizer updates | 200 |

The update log is consecutive `1..200`, forty updates per epoch, with the
exact four-example schedule on every update. All response targets are
contiguously supervised while context tokens are loss-masked; no encoded
example is truncated. Rank is 8, alpha 16, dropout 0.05, and learning rate
`3e-5`. Initial and final LoRA and optimizer hashes differ. Loss moved from
5.465 to 0.000136, but this is only a descriptive fit diagnostic; the cold
readout supplies the evidence.

`800 presentations` means repeated presentations of the twenty compiled
blocks across eight wrappers and five epochs. It does not mean 800 distinct
experiences.

## 3. Hashes, custody, and release

The authoritative manifest FILE hash is
`69bb58e162dcd3982dbd246eb52d052a7faf82bcedfdaf337c43303f63a813cf`.
Its seal, all eight prepared-input hashes, every stage inventory, and every
outer inventory rehashed successfully. Stage completion files are
byte-identical to the copies captured by their outer controllers:

| Stage | PID | stage completion FILE SHA-256 | outer collection FILE SHA-256 |
| --- | ---: | --- | --- |
| fit | 189173 | `44a29a341c77871b038023ad965da5cf7f8dffe8c89ca3f4e520f2c0d6bd138b` | `384101975b74f9b8a273f41b90086977c99d1a572b3dad615441d8e7edca917d` |
| AUTH readout | 190885 | `0d5bfa8a6e99e6a8a487ba02a0d5a8b45462888b7b8aa33d8f13c3ddbf3f939c` | `a722628cc34a2f584510d395c83595836e376dcdb584313af5cb0fc651cd9fd6` |
| C0 readout | 192858 | `49d8ab4c2268d8393f628ea767488f241a4001e14d57ab57c735ce994f96faf5` | `9f837cea37c6589d6022c212ebb78cd22314e0c983b2bf4e368a101d932ab80c` |

All three workers are distinct, exited 0 with no signal, and have successful
owned-process-group release receipts. Both readout actors consumed exactly
28/28 calls, closed without error or budget excess, and returned from their
explicit shutdown paths. Post-release queue checks match, the bound GPU is
empty, and CVD reports have no owner or unresolved process. As already
disclosed, `complete_cvd_visibility=false` because two approved non-worker
service environments were unreadable; these receipts prove release of the
owned experimental workers, not universal host-process visibility.

Helper analysis files rehash to:

- `analysis.json`:
  `27a7180027210c1ec68bdda4b032fad039f91b99033c713742aba22d015b90a2`;
- `analysis.md`:
  `16238894ef90541db985ea22621f56fe0467965a0737c08ac99651d1bd310da9`.

## 4. Paired isolation and leakage audit

The two cold arms use the same model files, LoRA-capable engine, GPU binding,
source pins, public roster, call order, token limits, and seeds. Across all 28
paired cells, request messages, row definitions, rendered prompt token IDs,
and sampling seeds match. The only actor-config differences are the intended
adapter/arm and stage-local path/deadline fields. AUTH mounts the one saved
checkpoint; C0 mounts no adapter.

No target block appears in any readout message or rendered prompt. Readout is
therefore source-withdrawn. During fitting, the eight child records and their
compiler-rendered blocks are necessarily the supervised response targets;
they do not enter as visible response text in the read prompt, and the loss
mask applies only to the target continuation. This is memorization and
extractability of trained mappings by design, not novel-fact generalization.

The deterministic service returns 14/14 exact blocks and makes zero model
calls; it is an integrity ceiling, not another arm. `NO_WRITE_C0` is a clean
no-adapter isolation for the narrow effect but is not compute-matched, so the
result does not isolate correct content from generic effects of an equally
trained adapter.

## 5. Reducer history and claim boundary

The successful artifact is analysis attempt 2, not an untouched pre-outcome
reducer. Attempt 1 failed before producing an analysis artifact because its
validator expected the wrong native RNG-receipt shape. The disclosed
`request_timing_v1_and_native_rng_schema_repair_v1` amendment accepts the
producer's existing `{cpu, cuda[]}` RNG receipt and adds request timing/limit
checks. It changed validation schema, not native outputs, targets, checkpoint,
scores, thresholds, or calls. Direct authoritative-byte checks reproduce the
endpoint independently, so this is a reporting requirement rather than a
result blocker. The failed first reduction and amendment must remain visible.

The experimental unit is **one source life/root, one initialization, and one
fit** containing eight EVENT experiences. Fourteen addresses and 56 readout
calls are correlated measurements of that one fitted bank, not independent
samples. There is no variance estimate or replication claim.

## 6. What changes in the objective ladder, and what runs next

Before SEQ-179, the own action--outcome write rung was weak/bounded. It can
now be marked **supported on one disposable development root for exact atomic
carriage and cold readout**. Nothing above it moves:

1. **Atomic own-EVENT write/read:** bounded component support (this result).
2. **Authentic child LINK formation and connected carriage:** still missing.
3. **Correct goal-conditioned traversal/use:** still missing; A1--A3 did not
   establish a functioning typed recurrent read/use loop.
4. **Retention across later writes and no-harm:** still missing.
5. **Two-root generality, lifetime improvement, strong evolving-text and
   final-batch controls:** still missing.

Do not spend the next cell tuning or re-running EVENT-only. Its scoped job is
done. The next useful work is two-pronged:

- repair the typed READ/THINK frame on exposed development roots, starting
  with the already proposed newline-framed/forced-READ smoke, so an actor can
  actually use a supplied connected graph;
- obtain authentic child-chosen LINKs without the hidden preselected-pair
  seam, freeze the first complete admitted bank, and carry that bank into the
  two-root vertical with causal LINK cuts.

Only after connected use works should the program pay for retention and the
paper-grade lifetime/control ladder. This positive result removes atomic
LoRA carriage as the immediate unknown; **formation of connections and use of
them are now the binding bridge.**
