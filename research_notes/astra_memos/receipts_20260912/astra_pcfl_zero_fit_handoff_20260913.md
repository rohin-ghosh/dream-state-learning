# PCFL C0 zero-fit diagnostic — EDITSTOP, September 13, 2026

## Scope and status

Only `gpu/astra_pcfl_zero_fit_dev.py`, its matching test, and this handoff
were edited. No native/model/real-tokenizer/network/GPU execution. Main owns
the separate command wrapper; Copernicus owns actor/tokenizer profiling.
This is `PCFL_C0_ZERO_FIT_DIAGNOSTIC_V1`, never original full-v2.2 release.
No fits, updates, adapters, future-fit schedule, compiler, or C11 expansion.

## Exact callable interface for Main

```python
from gpu import astra_pcfl_zero_fit_dev as diagnostic

plan = diagnostic.build_tasks(root_wires)
measurements = diagnostic.measure_tokenizer(
    plan, tokenizer, diagnostic.tokenizer_binding(actor_config))
manifest = diagnostic.build_manifest(
    plan, measurements, actor_config,
    wall_seconds=wall_cap, device_seconds=device_cap, output_dir=output_dir)
validation = diagnostic.validate_manifest(manifest, tokenizer)
report = diagnostic.Diagnostic(manifest, tokenizer).run()
final = diagnostic.finalize_release(report, outer_release_receipt)
```

`root_wires` is a list of four `core.to_data(root)` inventories ordered
`excluded/0..3`, prospectively supplied and bound. Do not treat synthetic
test roots as actual tokenizer-qualified roots. `tokenizer` is caller-loaded
offline; this module never loads it. `actor_config` is the native actor's
closed config, not a new configuration dialect. Required diagnostic bindings:

- `source_files` contains every exact absolute path/hash from `source_snapshot()`.
- `output_dir` is the fresh diagnostic directory plus `/actor`.
- `max_calls=1952`, `max_output_tokens=2048`, and `device_seconds_cap=device_cap`.
- Actual local model receipt, tokenizer files/chat template/probe, environment,
  GPU UUID, engine and future monotonic deadline satisfy NativeActor validation.
- Wall/device caps are positive finite numbers at most36000s. Actual initial
  and continuation input plus remaining output must fit the actor engine.

`measure_tokenizer(..., synthetic=False)` seals full token-ID/text receipts for
all supplied opaque IDs, all800 initial chat-rendered requests, all used READ
queries/service blocks, and MISS. Template encode and plain encode must agree.
The four actual tokenizer-file hashes and tokenizer local path are checked.
`validate_manifest(manifest, tokenizer)` replays those measurements exactly;
Diagnostic always does this before backend construction/start. A validation
without tokenizer is structural, not a native qualification receipt.

No callable signature changed in the final pass. **Measurement group keys did
change**: initial reachout groups now include `/RA` or `/RB`; delayed includes
`/TASK`. Regenerate pre-final measurements/manifests; old seals must not be reused.

## RA/RB matching correction and source rationale

The inference inventory supplies fixed panel counts/costs, not a requirement
that different literal full prompts have identical length. Exact literals are
`organism_v6/pcfl_vertical_dev.py:65` (RA) and `:66` (RB); the render registry at
`:968` registers them separately. World binding memo lines26–28 explicitly
preserve their distinct literals/opposite order. Production-binding analysis
`2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md:308`–315 requires
equal counts **within prospectively named substitution classes**.

Initial groups therefore bind panel/projection/render_id: all16 substitutions
within each reachout template still match; distinct RA/RB literal overhead is
measured, not equalized. Global bare-ID common length4..12/unique token sequences,
delayed within-template matching, READ-operation groups and service row-count
groups remain enforced. No padding, template rewrite, search-policy change or
outcome-dependent relaxation. CPU regressions accept unequal RA/RB overhead
and reject unequal substitutions within RA. This does not certify allocator
search history or any separately named cross-template allocator constraint;
Main's actual inventory/allocator qualification remains separate evidence.

## Execution, output, and release seam

Reuses frozen runtime task expansion, inherited `_task`, READ transcript and
scorers/thresholds without invoking its full-assay constructor or granting its
release. Private cell/oracle structures remain local scoring data; only exact
public request fields reach the actor. Material is researcher-authored excluded
root ceiling material, never authentic child targets.

Fixed640 delayed plus160 reachout tasks. Ten64-item and five32-item denominators
remain intact on failure. 704 single-call tasks +96 service tasks with at most13
opportunities =1952 possible actor calls, not1952 required calls. Per task:
at most12 READs, cumulative2048 actor tokens and4096 returned tokens. No retry,
root reopening, replacement task, fit, checkpoint or output-driven repair.

Fresh diagnostic output contains `manifest.json`, `call_NNNN_request.json`,
`call_NNNN_response.json`, `task_NNN.json`, and `report.json`. Failed tasks not
reached remain explicitly NOT_SCORED in the report. Request/response hashes,
actual prompt token IDs/counts, seeds, source and task seals are checked.
Backend close is attempted on execution errors. A completed run produces
`COMPLETE_AWAITING_OUTER_RELEASE`, still `diagnostic_usable=False`.

Main's pure evidence attachment `finalize_release(report, receipt)` takes exactly:

```text
report_sha256 gpu_uuid owned_group_released gpu_vacant
elapsed_seconds_from_start evidence_path evidence_sha256
```

Both release Booleans must be true. Evidence is an absolute JSON file whose
hash matches and whose content is exactly the other five attestation fields
(excluding evidence_path/evidence_sha256), with type-sensitive comparison.
Elapsed time must include release, be >=reported through-close time and fit
both caps. It uses the report's `started_monotonic` basis; native actor close
does not certify process/GPU release. Main performs real ownership/vacancy
checks and saves the returned final object separately. Failed or synthetic
reports cannot become usable native evidence. Device time here is conservative
single-device reserved elapsed wall, not measured active GPU seconds.

## CPU evidence and limits

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 -m unittest discover -s tests -p test_astra_pcfl_zero_fit_dev.py -v
```

Final result: **18 tests PASS,31.721s**. Covers all800 injected tasks, exact
service transcript, fixed denominators on failures,13th READ stop, missing
measurements, source/task/tokenizer drift, unresolved world, strict caps,
expired deadline, cold-load/close envelope, fresh-only outputs, synthetic/native
separation, release evidence, and both render-group regressions. Actual core
audit executes once on immutable fixture roots; repeated fixture audits are
cached with an explicit test-only mock. Synthetic tokenizer is hash-based,
not Qwen qualification; injected backend oracle outputs are CPU fixtures only.

Core audit recomputed in production:32 worlds/64 delayed tasks,192 route/cut
decisions,48 atom/link decisions,16 entropy quartets. Route construct passes;
full construct does not. Supplied inventory checks do not prove first-feasible
salt/DFS allocation history or unused fit/twin/permutation qualification.
No actual tokenizer/profile/base/GPU receipt was generated by this worker.
Native start/resource/lease checks remain caller prerequisites. Synchronous
calls need Main's outer timeout/owned cleanup; the driver is not a watchdog.
Only excluded-root interface ceilings/failures can be interpreted: no memory,
parenting, learning, H1/H2/G3, full-shortcut or C11 claim.

## Final SHA256 pins

```text
b0100efe123604dde2900127663a3eda299bc60cc8fe1d40f10c045e48d73638  gpu/astra_pcfl_zero_fit_dev.py
03734def7a90b16c32a4fd68428d85ff3242a966d43b32a6487c4c05437231b5  tests/test_astra_pcfl_zero_fit_dev.py
026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1  gpu/astra_pcfl_vertical_dev.py (unchanged)
b8d033566574967e6f579c6b1451e65c1bb15a99fce554ba71ced0c270ad39c3  organism_v6/pcfl_vertical_train.py (unchanged)
f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26  gpu/astra_pcfl_native_actor.py
ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e  organism_v6/pcfl_vertical_dev.py
c674b152b6147f6f8a698af065c33648eaeea7a309bbb531e2b59d022c19f29c  ASTRA_PCFL_ZERO_FIT_SCOPE_2026-09-13.md
ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91  ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md
599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b  2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md
```

Dependencies owned by others are observations at this freeze, not permission
to change them. Main must regenerate source maps on the exact shipped snapshot.
Handoff's own hash is returned separately to avoid a self-referential pin.
