# V10R1 W0 terminal infrastructure-abort audit

Date: 2026-09-12 UTC  
Execution observation: 07:31--07:39 UTC  
Verdict: **the prepared inputs were exactly bound, but the first execution
terminated `NONREPORTABLE_ABORT` before optimizer step 1. No W0 scientific
label or gate result exists.**

This was a read-only watcher audit. I did not edit builder source or receipts,
transfer or install software, prepare or launch a run, stop a process, or
change a node.

## Frozen source

The executed source is commit
`b686fcf0a38dc0bf6b443380ec4619c7ee875a9c`, subject
`Freeze bounded V10R1 executor with lease and local identity guards`.
Astra's VM source archive was
`/tmp/astra_w0_source_b686fcf0_attempt2_20260912.tgz`, SHA-256
`59e51f41cad36745bb0e27b123229a28f5244d7672f83f189f82f9524b8142db`.
For all three implementation files, I independently verified that the commit
blob, archive member, deployed node-3 file, prepared manifest, first-fit job,
and first-fit load receipt agree on these exact hashes:

- module: `6d23b4470ae8cb3a5e7b6a0fc00678b9c5e0aa071f5e4b825b3ad54ed13c75b0`
- tests: `9dbb4cf6ee1472e19b2fe64a181ede865aa0d90857c6a690ad77ccf6df5287b0`
- launcher: `3994bf389e63ac790b3eb500cc74a974ed57b88fd8fd02d494ae6fecc0ab33665`

The committed focused receipt reported 51/51 CPU tests in 8.890 seconds; an
independent VM rerun on the same bytes reported 51/51 in 9.151 seconds; and
node-3 preparation reran 51/51 in 10.469 seconds. These tests and preparation
were not scientific outcomes.

## Exact preparation

The fresh run root is
`/localhome/local-rohing/astra_diagnostics/astra_W0_v10r1_20260912` on node 3.
Its preparation seal names manifest SHA-256
`5ec0ee13fefeff6bae79a9b73fbd35c27506a1864b08497e1336b9bcdb129894`;
the raw `PREPARED_SEAL.json` SHA-256 is
`6d09ffadb5ffc10445ab756d58f221752e2840415c2c43b201cf3d0102b8b1b1`.
The VM-side pre-execution archive
`/tmp/astra_w0_prepared_20260912.tgz` hashes to
`4d4d97bda99efe411cea01c3bd87a433155e54bbe47bd2dedb768e4384043b71`.

I ran the exact deployed module's `validate_prepared` read-only. It accepted
the prepared seal, every artifact/receipt hash, frozen recipe, four planned
fits, material regeneration, request blueprint, real-tokenizer preflight and
CPU receipt. I separately recomputed the complete 14-file local model snapshot
inventory; model and tokenizer both hash to
`1b248450cd087dad8956a8b77ccc4829040d614133f3c0aba834729af8075422`.

The sealed configuration binds:

- model: `Qwen/Qwen2.5-7B-Instruct`;
- local snapshot/revision:
  `a09a35458c702b33eeacc393d103063234e8bc28`, agreeing with the snapshot
  directory basename and local `refs/main`;
- model configuration: `qwen2`, 28 hidden layers, hidden size 3584;
- evidence boundary: `official_model_authentication =
  UNRESOLVED_LOCAL_HASHES_ONLY`, `material_origin =
  synthetic_researcher_authored`, `clean_lineage = false`;
- node-hostname hash:
  `3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9`,
  independently recomputed from node 3's hostname;
- GPU: index 1, UUID
  `GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821`, NVIDIA A40, driver
  `580.173.02`;
- environment: Python 3.12.3, torch 2.13.0, transformers 5.5.3, peft 0.20.0,
  tokenizers 0.22.2, safetensors 0.8.0 and numpy 2.3.5;
- lease end `1790391780` (2026-09-26 03:03 UTC), campaign cutoff
  `1789218000` (2026-09-12 13:00 UTC), and a separate 10,800-second/3.0-A40-hour
  execution deadline;
- all five protected kinds at `/localhome/local-rohing/v6_out`, outside the
  new diagnostic root;
- seeds: identifier 100, train order 200, held order 300, request 400, and
  root-confounded fit seeds 0 and 1.

The inherited receipt binds exact-scope hashes V9
`eac3e25c93230f3788612b3d0a25c0dac3609d49b4a5d9e28cf853ba806c0955`,
V10 `12a077950730c3abaef32b04a861d901ef4bae25a22e640b152472f5f364f549`
and V10R1
`6cba6518184e7c8d12d7c23088895a565b84ae5ee067eaa63aac4440b91ea1aa`,
plus their three consensus hashes and three decision-note hashes.

### Frozen inputs and tokenizer

The four planned clean-base cells were:

| fit | root/map | seed | input SHA-256 | encoded SHA-256 |
|---|---|---:|---|---|
| `fit_0_0` | root 0 / W+ | 0 | `c2dad0761455209091b2e7d4da61c44d63bfd0eea3fd0e0d00a0ccfdf63a8716` | `248efc0271ce1aafd4c7963f56ed105c293b4fae733af9ed3b3fee53dc117d83` |
| `fit_0_1` | root 0 / W- | 0 | `99d5fd12a8756fc2a65817bd29f4fc779b028d2314b403b1f394090e41cd7eeb` | `9c0dd6b697258faa8a93593351f0438e8587aaef0ffdbfd00b39eac6b145a421` |
| `fit_1_0` | root 1 / W+ | 1 | `3cf3d0b5c27b860eb88a21f4b6ffc893eb592c3465fbe706c61b19aa06673f44` | `985ce0f87d8a67c5b4d5854ee97494510cd9e00f7692fb8b413d24ea9be9fe16` |
| `fit_1_1` | root 1 / W- | 1 | `b6b3efe2bcca429f78fa700b2aaec71e365c40e9e12b1a89491677dae934643a` | `98c723cd593ac631b6d7b6bcd82346a8822ea183f1b4157033161b2c5260325a` |

The real Qwen fast-tokenizer preflight used EOS token 151645. It certified
exactly 128 rows per fit, 512 rows total, exactly six supervised tokens per
row including EOS, maximum fit sequence length 30, 464 context-pair entries,
464 generation encodings, and 1,504 unique blueprint request IDs. Geometry
certified every enumerated shortcut maximum as exactly one half on the frozen
training and held multisets.

The preparation review receipt remains
`status = NOT_AN_INDEPENDENT_APPROVAL`. Standing builder authorization made
that nonblocking operationally, but it does not by itself close V9's two-review
paper-evidence term.

## Launch and terminal failure

The launcher receipt binds the exact command, manifest, source commit, GPU and
run root. The controller was PID 21464, launched at
2026-09-12 07:36:30.801951 UTC. Immediately before launch the compute-process
table was empty; the launcher found no readable CUDA reservations or live
life process. It also records 1,381 service-process environments that were not
readable, so it does not make a universal reservation-absence claim.

After rehashing inputs, the controller wrote `EXECUTION_STARTED.json` at
07:37:02 UTC. Its raw SHA-256 is
`73ef075fb13939efa84288d4004d4db48d68bc977e6c171c7aaddd88d045b771`.
The receipt binds the prepared manifest, the same A40 UUID, driver, node hash
and environment hash, plus deadline `1789209422.503231`, exactly three hours
after `wall_start` and earlier than the campaign cutoff.

Only `fit_0_0` started. Its job SHA-256 was
`b3727534bdad07bcf9598a38dcf0ed2b087fbf18ee39fda5d451399c5d1c1439`
and worker PID was 21922. `fit_0_0_LOAD.json` binds
`adapter = OFF_CLEAN_BASE`, the same model/tokenizer/source/environment/hardware
pins, seed 0, the expected 392 LoRA trainable tensors, and initial LoRA digest
`e8290b734317aa4eefa66fdceb5863bcdf80e5acbb723b36227f40c08cadd232`.

The first training step triggered compilation of Triton's CUDA helper and
failed because `/usr/include/python3.12/Python.h` is absent:

```text
/tmp/tmpm4ffavro/cuda_utils.c:9:10: fatal error: Python.h: No such file or directory
```

Read-only inspection confirms both `/usr/include/python3.12/Python.h` and the
`python3.12-dev`/`libpython3.12-dev` packages are absent on node 3. The worker
returned code 2 after 46.023 seconds. The step trace is the empty file
(SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`),
so **zero optimizer steps ran**. The process-log SHA-256 is
`2c6d708154cf43eb0311042164f3e9ed72187b04260fa257b56bf7f2c1f8caa7`.

The controller then wrote `NONREPORTABLE_ABORT.json` after 46.026 reserved
GPU-seconds. Its raw SHA-256 is
`1f818b236d57a649fc8e5811bfb6c0f0e6ef49c4ea0989d1cd9d3bf0f9c277c8`;
the builder's subsequently mirrored terminal capsule hashes to
`5662c63d7cea89173e8ac289496794c02f18b43219dfc8e864e638cf5d2427dc`.
Its material fields are:

```text
evidence = INCOMPLETE_REAL_EXECUTION
scientific_label = null
completed_stages = []
no_retry = true
error = fit_0_0 failed; no retry or replacement fit
```

At 07:39 UTC the controller and worker were gone and GPU 1 was empty. The
following required artifacts do not exist: `fit_0_0_PROFILE.json`,
`fit_0_0_DONE.json`, the first adapter directory, any later-fit start,
`requests.json`, `RESOURCE_RECEIPT.json`, `report_real.json`, and
`REAL_EXECUTION_SEAL.json`.

## Gates, reducer and claim boundary

No fit completed, so the run contains zero of the required four clean-base
fits and zero of the 1,504 generation/likelihood records. The reducer did not
run. Consequently none of these evidence predicates has a value:

- oracle validity for either root/map;
- all-key median action-choice NLL gain or root map-asymmetry;
- generated binding BA, OFF gain, opposite-map contrast, per-stratum accuracy
  or directional margins;
- strict output validity, multiple-`ACT` behavior or the 8/8 native-interface
  panels;
- missing-mode, unsupported-mode, neighbour or unrelated-interface spill TV
  and legal-ACT locality.

The frozen reducer source and CPU golden tests correctly implement these
predicates and their `ASSAY_INVALID` → `OPTIMIZATION_INCONCLUSIVE` →
`INTERFACE_INVALID` → `BINDING_WITH_SPILL` → `MULTIKEY_BINDING_PASS` /
`GATEWAY_NEGATIVE` precedence. That validates computation code, not this
aborted run's scientific behavior.

This terminal artifact supports only the operational statement that the exact
prepared source/config/input/model pins reached a clean-base LoRA load and
then encountered a missing system-header dependency before training. It does
**not** support the bounded W0 supervised seen-key conditional-policy claim,
nor an optimization, binding, locality, interface or substrate-negative
claim. A hypothetical later sealed pass would still be limited to four
root/map conditional-policy instances, with paired seeds confounded by root;
it would not establish retention, lived learning, DREAM, parenting,
generalization, connected memory, recurrence, continual learning,
reliability, child authorship or whole-organism learning.

## Exact next evidence

This run root must remain terminal; its own receipt says `no_retry = true`.
The next reportable attempt would require a new run root and new immutable
preparation after the builder resolves the system dependency. Before another
launch, evidence must show in the exact execution environment that the Python
C development headers and Triton CUDA helper compile/load path work. Because
the current environment digest covers Python and Python-package versions but
not compiler/system-header bytes, a new preparation should bind that OS-level
preflight explicitly (or extend the environment identity) rather than assume
the package-version map captures the repair. Only a fresh terminal seal with
four 256-step clean-base fits, 1,504 complete records, exact reducer report and
successful replay could answer W0.
