# PCFL Transition-Path P0/P1 resource manifest

Status: proposed limits. Every number is a hard ceiling, not a target to spend.
Crossing a ceiling follows the zero/stop rules in
`statistics_and_gate_contract.md`.

## 1. Stage and authority order

```text
exact human ratification of this intake and scope
  -> P0 implementation + deterministic CPU certification
  -> freeze exact code/manifests/receipts
  -> fresh independent code review with PASS_FOR_P1
  -> P1 single compiled-text canary
  -> terminal STOP, NOT_RUN, or human-facing REQUEST
```

There is no automatic transition. P0 pass is required but does not itself
start P1. The fresh reviewer may reject. P1 has no outgoing executable edge.

## 2. Future allowed write surface

If exact ratification occurs, the requested scope permits new or replaced bytes
only under these future subject paths:

```text
research_loop/pcfl_transition_preflight_v1/**
research_loop/test_pcfl_transition_preflight_v1.py
research_loop/workflows/pcfl_transition_preflight_v1.json
artifacts/pcfl_transition_preflight_v1/p0/**
artifacts/pcfl_transition_preflight_v1/p1/**
```

It does not permit edits to existing experiments, archived results, prior
change bundles, shared provider/runtime modules, leases, credentials, package
state, or any other repository path. If the implementation cannot fit this
surface without modifying shared code, it stops and requests new authority.

## 3. P0 caps

| Resource | Hard cap |
|---|---:|
| Device | local CPU only; zero GPU device or kernel |
| Network/provider/model/tokenizer service | zero calls and zero bytes |
| Training/gradient/adapter/LoRA objects | zero |
| Fixture pair roots | 32, exactly the registered P0 range |
| Parallel worker processes | 4 |
| Logical CPU time | 1,200 seconds total |
| Wall time | 900 seconds total |
| Peak resident memory | 2 GiB |
| Written artifacts | 512 MiB |
| Generated source slots | at most 32 pairs × 2 sides × 240 = 15,360 |
| Hidden single-tree bit-orbit cases | exactly 32,768 |
| Retry/fallback attempts | zero |

P0 may use only the standard library and dependencies already frozen in the
repository environment. It may not install a package or query a service.

P0 freezes a manifest of every source file, schema, fixture root, public vector,
target/twin certificate, compiler corpus, reader/index/bag/graph object,
cut/sham object, expected receipt, and reproduction command. Every entry has
path, size, and SHA-256; the manifest has a deterministic root hash.

## 4. Fresh code-review gate

After P0 all-pass, an independent reviewer who authored and modified none of
the subject paths reviews the exact frozen bytes in fresh context. The reviewer
must reproduce P0, inspect provider/network and write allowlists, verify all
visibility/reset mutants, confirm that `WCANON-T1` has no model/target/oracle
input, and select `PASS_FOR_P1` or `REJECT`. Missing identity/freshness evidence,
changed bytes, unresolved finding, or any new capability means `REJECT`.

The review may write only its immutable receipt under the P0 artifact path. It
does not authorize a claim or a scope change.

## 5. P1 fixed configuration

| Resource | Hard cap / exact setting |
|---|---|
| Provider | Codex provider through the already configured narrow research-loop transport |
| Model | `gpt-5.6-luna` |
| Reasoning effort | `medium` |
| Model attempts | one per response; no retry or fallback |
| Maximum output | 128 tokens per response |
| Maximum model-visible context | 8,192 tokens per response, including all system/target/reader bytes |
| Provider responses | 474 absolute maximum |
| Aggregate input tokens | 1,500,000 absolute maximum |
| Aggregate output tokens | 60,672 absolute maximum |
| World-life/twin pairs | 6 |
| World sides | 12 |
| Trees per side | 8 |
| Source action slots | 2,880 total |
| Target episodes | 114 assigned |
| Reader operations | 360 maximum |
| Executed target commands | 570 maximum, including commit |
| Compiler calls | 24 local deterministic snapshot builds (`M0` and `M1` per side); zero model compiler calls |
| User-controlled GPU/training | zero |
| CPU worker processes | 4 maximum |
| Peak resident memory | 4 GiB |
| Written artifacts | 2 GiB |
| Wall time | 12 hours |
| Provider/network destinations | the pinned Codex transport only; no arbitrary URL, shell networking, sync, telemetry, or upload |

If the provider cannot attest the exact model name and configured reasoning
effort before the first response, P1 is environment-wide `NOT_RUN`. Provider
drift after the first response is a failure/zero and stop, not a fallback.

## 6. Information and compute ledger

For every world side, snapshot, arm, target, and response, the ledger records:

- canonical source bytes and hashes;
- canonical atom bytes and provenance bytes;
- flat-bag, forward-index, reverse-index, exact-graph, cache, and handle bytes;
- construction comparisons/operations and wall/CPU time;
- per-query scan comparisons, candidates considered (zero for exact linked
  lookup), returned atom hash, prompt/input/output tokens, provider response
  count, and latency;
- prompt/system/target/reader bytes separately;
- action commands, public state trajectory, terminal value, parse/error code;
- all failures, aborted/unexecuted assignments, and zero/NOT_RUN decisions;
- total retained and peak active state;
- amortization denominator of exactly the number of assigned downstream target
  episodes using that built object, including failed episodes.

Latency is never model-visible. P1 permits observed-range resource reporting
only. It cannot support an asymptotic, scalable-retrieval, Pareto-efficiency,
compression, or baseline-plateau claim.

## 7. Minimal reproducible artifact

The P0 implementation must expose one offline command that, in a fresh checkout
with no network, regenerates all 32 fixture closures and public projections,
the JCS+LF source and target bytes, exact target-prior orbit, H/tau vectors,
goal pairs, M0/M1 corpora, forward/reverse reads, flat-bag scans, exact-graph
controller traces, depth proofs, cut/sham proofs, taint/reset mutations,
resource receipt, and the final root-hash manifest byte-for-byte.

The P1 artifact, if run, adds the six canary root closures, sealed target and
arm manifests, exact prompt/reader/model/action traces, failure-inclusive
114-row episode ledger, resource ledger, and terminal gate receipt. Private
hidden closures may be access-controlled, but the reproduction package must
include a deterministic verifier and commitments sufficient for a fresh
reviewer to reproduce every public projection and score. No polished public
benchmark platform, package publication, outreach, or external release is in
scope.

## 8. Explicit zero-resource rows

The current scope allocates zero calls, tokens, bytes, or runtime to LoRA,
adapters, gradients, optimizer state, training examples, direct-QA training,
full confirmation, lifetime scaling, plateau tests, compression studies,
on-policy interaction, learned dreaming, learned scheduling, graph discovery,
other baselines, other models/backbones, or provider fallbacks. It allocates
zero authority to claims, publication, automatic successors, lease/quota/spend
changes, or unrelated networking.
