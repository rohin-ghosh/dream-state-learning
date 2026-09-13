# EVENT-only reducer independent review — 2026-09-13

**Verdict: fixed endpoint and principal producer/consumer schemas agree. No concrete native-shape rejection found by source reasoning. One bounded request/timing-validation gap below; no endpoint or native-run change requested.** Review is advisory, not full-assay/C11 qualification or a scientific result.

## Exact pins

Current hashes match reducer EDITSTOP and its declared command/outer dependencies:

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_event_only_analyze.py` | `83b88bab9603c3fd519cf08a9e785b3141d5492694abc34e7002397db417cbe4` |
| `tests/test_astra_pcfl_event_only_analyze.py` | `f122d63e82895cc880dcbad34c08322926b9b094d8fe63579b2eb73759e20c13` |
| `gpu/astra_pcfl_event_only_command.py` | `3ebef8ce6c8cd783104f5d0d74946fd1df5f99e41208508451482f56fdf9d916` |
| `gpu/astra_pcfl_event_only_outer.py` | `5bc4f24a744a2ee53edbe7623ce0e10831fd8a566fcfbae58e1f84531a89aac4` |

Handoff `/tmp/astra_pcfl_event_only_analyze_handoff_20260913.md`: SHA256 `5e627ffe55155adc925d3fa27a2f0661dde77ee8b8acea49812097b59ea42e78`. Also inspected relevant ReadoutActor production emission code and reused inventory/interval helpers. The handoff's 18-test result is author evidence only; this review ran no tests.

## Concrete correction for owner coordination

**Low severity — request receipt fixtures omit production timing/limits, and the reducer does not validate them.**

Production `gpu/astra_pcfl_own_write_readout.py:263` records operation start before lazy cold load; lines 275–276 write both `started` and `limits` into every request sidecar. Command line 253 supplies exactly `{deadline: worker_deadline, device_seconds: 1740}`. In contrast, `tests/test_astra_pcfl_event_only_analyze.py:174` omits both fields, and reducer lines 229–230 never inspect them. Reducer lines 246–260 check ordered generation intervals and only aggregate response-operation duration. A missing/contradictory request start or request deadline is therefore not detected by these joins; individually impossible response durations can also be hidden by other calls' durations in the aggregate.

Smallest correction: make synthetic request fixtures use the existing production fields; compare archived request limits to the fixed command call and check each operation start against its own generation interval and response elapsed duration. Keep aggregate costs too. Specifically preserve the cold-call rule: first `started` may precede `load.ready_at`; **generation_started**, not operation start, must follow readiness. Add focused missing-field/wrong-limit/impossible-per-call-duration regressions if the owner makes this correction. No new thresholds, tokenizer/model calls, controller changes, or result-dependent selection are needed.

This is incomplete evidence validation, not an established failure of the running native job, and not a bypass of independently fixed file hashes. It does not change the 14-address endpoint. Do not amend the frozen reducer silently: coordinate/version any correction and bind the new source/test hashes prospectively.

## Confirmed consistency

- Actual prepared layout is the eight top-level input files plus manifest. Reducer joins their file hashes and seals, fixed imported prefix, exact scope hash and repository-relative source mapping. It does not substitute the old full-bank analyzer or relocate original-v3 replay authority.
- Fit path joins `fit/write/{fit,encoding,event_only_scope_report,initial,completed}.json`, all 200 update records, 160 encodings, 800 presentations/forwards and the saved adapter inventory/identity. Validation uses the unchanged shared writer/masks and immutable fit schedule; no duplicate numerical loop or model invocation occurs in reduction.
- Production native kinds match: stage `NATIVE`, preparation `OFFLINE_PREPARATION`, actor/load/close/raw `NATIVE_OWN_WRITE_READOUT`. Base identity removal of mount/lora fields matches ReadoutActor's actual implementation. AUTH mounts the bound checkpoint; C0 has no adapter. Identity PID joins the corresponding released outer worker; three process identities must be distinct.
- Cold generation receipt shape correctly uses `generation_started`/`generation_ended`, not a nonexistent raw `operation_started`. The first generation follows load readiness. Worker deadline is joined to outer binding rather than inferred as worker start plus 1740. Outer post-resource observations follow owned-group release; approved CVD visibility limitations remain in reported observations rather than becoming an assertion of complete visibility.
- Exact roster reconstruction fixes 14 addresses at W0 and the same ordered 14 at W8, 28 calls per arm/56 total; W8 EVENT8/EVENTS_AT6 strata are checked. Primary service14/14, AUTH>=13/14, C0<=1/14 and paired difference>=12/14 agree with `event.ENDPOINT`. W0 remains diagnostic and cannot rescue W8.
- Both arms and fit require independently pinned stage completion and successful outer collection, complete inventories and exact 28-call actor sidecars. Missing/failed arms throw before endpoint emission, never become numerical zeros. Exact raw strings feed the unchanged scorer; recorded scores must match. Length-finished exact bytes fail strict_stop; semantic tolerance is not promoted into strict correctness.
- Output explicitly labels format-scaffolded developmental EVENT-prefix acquisition, one source life/root/fit, no compute-matched C0 assertion, no generalization/full-assay or automatic promotion. Reported durations are elapsed intervals, not GPU-active time. Native labels and local archive consistency are not independent hardware authentication.

No actual new fit/readout outputs, original archive data, live paths, or native outcomes were opened. No tests, native/model/tokenizer calls, GPU/remote/network actions, commits, or source amendments performed. Only this review artifact was written. No cold-result selection or interpretation of the unrelated interface outcomes is part of this review. **EDITSTOP.**
