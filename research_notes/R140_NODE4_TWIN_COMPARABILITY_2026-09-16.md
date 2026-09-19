# R140 NODE4 TRAIN-only pair comparability

## Verdict — collection ending September 16, 12:21:26 UTC

**Kernel5 is initialization/runtime-matched to kernel4, but not an exact
message-only unparented twin.** Their initial adapter tensors, optimizer/RNG
file, seed, Python closure and core configurations match. Their first inputs
already differ in parenting instructions and resource identifiers. This is
at most a comparison of the announced parenting programme plus delivered
parenting against an explicitly unparented programme, not an isolated effect
of later messages. **Raw1 is not an initialization/runtime-matched twin of
raw3**: seed, initial adapter/RNG, runtime implementation and starting time
also differ. Neither label establishes a causal learning benefit.

Read-only sidecar: no new run/reset, model/GPU call, held output/score access,
or live edit. Main's original0/executor2 remain untouched. These are sequential
journal-prefix observations, not a simultaneous census or whole-future claim.

## Exact comparison

| Dimension | Kernel4 versus kernel5 | Raw1 versus raw3 |
|---|---|---|
| Base/tokenizer location | Same Qwen2.5-7B-Instruct snapshot, base pin below | Same snapshot/base pin |
| Initial seed | 0 / 0 | 0 / 1 |
| Initial adapter | Same state/tensor-file hashes | Different state/tensor-file hashes |
| Initial optimizer/RNG | Byte-identical combined file; both step0 | Different combined files; both step0; raw3 also adds experiment metadata |
| Adapter configuration | Only serialized target_modules order differs; identical set and every other JSON field | Same ordering-only configuration difference; does not erase different tensors |
| Startup bytes | Four differing lines: workspace, physical GPU, source path, branch-parenting paragraph | Same four categories; raw3's startup names source1 although actual PLAN binds source2 |
| First TRAIN REQUEST | 1483 / 1485 prompt tokens; different message hashes | 1277 / 1278 prompt tokens; different message hashes |
| Runtime Python closure | All pinned Python bytes equal, rehashed on node | Native/stream/journal differ; R133 seed/replay/binding implementation versus legacy |
| Actual replay configuration | free_distillation / free_distillation; no parent_guided execution | free_distillation / free_distillation (legacy omission versus explicit field) |
| Decoder, optimizer, readout config | Equal as detailed below | Equal core settings, despite different native implementation |
| Parenting exposure | 18 bound publications; 17 registrations and rendered REQUEST exposures / zero registered inputs | zero registered inputs / 10 publications, registrations and rendered REQUEST exposures |
| LOADED time | 1789554051.8062432 / 1789554051.7620451 (44ms apart) | 1789554000.254505 / 1789556190.34679 (raw3 2190.092s later) |
| Device policy evidence | Neither collected legacy GUARD contains device_containment | Legacy raw1 lacks that field; raw3 contained GUARD binds uid/gid2524, minor0 |

All differing PLAN keys, unmodified differing startup lines, first REQUEST
hashes and source hashes are recorded in `COMPARISON.json`. Kernel PLAN
differences are exactly birth_prompt, gpu_uuid, physical, root, source_root,
startup_context; raw PLAN differences add seed and presleep_variant. No
path-normalized text was substituted into any live or historical artifact.
Direct comparison of initial REQUEST message contents found the same four
line differences, including actual parenting declarations, not merely a
different provenance envelope. Physical GPU identity is not randomized here.

Kernel4 declares experimental-coach every2 responses; kernel5 explicitly says
no scheduled guidance. Raw3 declares Socratic every3 responses; raw1 explicitly
says no scheduled guidance. All four startups say kernel execution is pending
explicit connection. This audit does not promote those declarations to proof
of a working tool or a measured kernel result.

## Common settings and implementation qualification

- Base snapshot suffix `a09a35458c702b33eeacc393d103063234e8bc28` under node-local
  `models--Qwen--Qwen2.5-7B-Instruct/snapshots/`; base pin
  `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
  PLAN/LOADED agree; this sidecar did not rehash the base weight files.
- LoRA rank8, alpha16, dropout0.05, bias none, standard initialization,
  no DoRA/RSLoRA; target set q/k/v/o/gate/up/down_proj. Serialized configuration
  has peft_version0.20.0. Runtime source requires FP32 LoRA, frozen BF16 base,
  SDPA, non-reentrant gradient checkpointing, BF16 autocast during sleep.
- Generation: sampling, beams1, temperature0.7, top_p0.95,
  repetition_penalty1.05, no_repeat_ngram_size16; context16384, segment512,
  two ordinary segments then free-distillation presleep generation. Same
  SYSTEM, compaction invitation and R125_PLAIN_CONTEXT_V1 renderer bytes.
- Sleep:16 new presentations,1 rehearsal, objective weight0.25 TRAIN anchors /
  0.75 child (not token fractions). Same TRAIN anchor source manifest/plan/row/
  suite pins. AdamW lr3e-5, betas(0.9,0.999), eps1e-8, weight_decay0.01,
  foreach=False, fused=False; same loop body for actual free-distillation.
- Readout: revision2, identical readout source; initial and after-sleep
  fresh-process dispatch, no shared conversation or parent. Suite pin
  `32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c`,
  cap512, greedy/beams1/repetition_penalty1.0. Only configuration/source was
  compared: completion, outcomes and scores were not inspected.
- Raw3 R133 initializes a newly attached adapter with seed1 before LoRA;
  legacy Engine initializes with its fixed seed0 before native generation
  reseeding. R133 also records immutable experiment bindings in stream,
  checkpoints and optimizer/RNG, verifies them on resume, and factors
  presleep into a variant-aware helper. Its actual free invitation is equal,
  but this is not a byte-identical implementation control.
- Common hard end1789754400 and lease end1789776000, no max_sleeps. The later
  raw3 start implies a different remaining wall budget, not equal exposure
  opportunity. This audit took no lease action.

## Initial hashes (actual files rehashed on node)

| Artifact | Raw1 / kernel4 / kernel5 | Raw3 |
|---|---|---|
| Adapter state | `95966e71c3ec81487d05e02d6b770c422febfc433fe367d856a6e4817f8dbe14` | `e55b0b605cdab30fdfb736a99fd89787a2d6c9bf00d736f218c675da2bfe3eb9` |
| adapter_model.safetensors | `2beaa09d4930b1eafa6a1a07a67f3d062b35336d5e5ac58778a00ad518cf9dfe` | `7741c43c998d9e86f0cc5d30d2ed5536d3fbc597cbd6b44f429987e7823f123e` |
| optimizer_rng.pt | `aa5811768e68f1de7765f7616da244170302211f4fb7cbc235a3434037ebafa5` | `c1e39b4201e2524cd691b31078b03ff07461637de90264744c70576abf19b930` |

No pickle/tensor deserialization was performed. A different combined RNG file
does not prove every optimizer tensor differs: raw3's payload also contains
additional experiment metadata. The adapter tensor file itself does differ.

Startup SHA256 by physical:
- 1: `1b2ceaa70106f61f6ea1d67c277ebf06da480fae495fd21d7f1441c6e8afb21b`
- 3: `e88a40c9a25385f201dc5608064d3e3df24ad5d6f1754efae3e4373115bbfd03`
- 4: `fa747c19f42a73e29450914655c57986913839d4cfa7834611698cb80aefec50`
- 5: `713bece391095bcc38fe24418f44081cf9574c1c9dade998eec7536c2099fa1e`

## Actual parenting and limits

Strict REQUEST exposure, not intended cadence, is the comparison variable.
Raw1 has zero registered inboxes through1046 records; kernel5 zero through972.
Kernel4 has17 verified exposures through967 records; its eighteenth bound
publication is not yet registered/exposed. Raw3 has10 through769 records.
Journal head hashes and every publication/RESULT/request binding are retained.
Zero in these prefixes does not rule out future publications or unpublished
external actions; this is not a blanket claim of lifetime isolation.

Raw3 is a mixed historical language phase: prior call8's Chinese message was
exposed in REQUEST668; its nine historical receipts remain unchanged. The
prospective English parent handoff preserved cursor27 and did not restart the
child. First English source30 publication is verified in REQUEST757, hash
`7f590b050c5f33b2a33deb0dae3af56655496e93552586503f4e041d0f967ef4`.
See `R140_RAW3_PARENT_LANGUAGE_PHASE_2026-09-16.md`; exposure is not uptake.

Remaining unknowns: complete installed-library/binary equivalence, first-call
GPU nondeterminism, CPU/I/O contention and device clocks, equality of all
external interventions, later delivery, and readout completion/outcomes.
Equal initialization is not equal later RNG trajectories after different
prompts. Nothing here estimates an effect size or validates learned skill.

## Receipt custody and checks

Local root: `research_notes/analysis/orch_r140_node4_pair_audit_20260916/`.
Remote original collection:
`/localhome/local-rohing/orch_r140_node4_pair_audit_20260916_v1/COLLECTION.json`.
The local `collected/` tree retains exact static configs/source and exposure
metadata; no held outputs. `INITIAL_REQUESTS.json` preserves raw UTF-8 TRAIN
record2 bytes for each branch with file/record hashes.

- COLLECTION SHA `0926ab9f815eeb9b608a4a4b40da82172862f2ec2f54a9eb04a3848002d00a73`.
- INITIAL_REQUESTS SHA `826cb47c74d0dc4406f446430899397914984cdcd6d0241be678497853d3d8c8`.
- COMPARISON SHA `974072211ed22e544a2c68df71f0f070efc0f029581fba0ef70c732db4cd540a`.
- `compare.py`:135 CPU evidence checks PASS (custody, raw REQUEST binding,
  source/config comparisons, exact four-line startup differences, publication
  RESULT hashes and exposure bindings). These are sidecar checks, not new
  GPU tests or a replacement for the earlier exposure auditor's test suite.
