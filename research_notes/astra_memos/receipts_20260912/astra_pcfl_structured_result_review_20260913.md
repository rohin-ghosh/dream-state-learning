# Independent structured-action RAW/custody review — 2026-09-13

## Verdict and scope

No blocking inconsistency found in the reviewed local evidence. All **56 actual captures** were checked, not a sample. The generic control has 7 stop-completed strict ROUTEs and one LENGTH failure, no READs, and no graph successes. The externally scheduled first-READ control has 8 strict terminal ROUTEs, 8 served-read handshakes, 40 READ calls, and no graph successes. This establishes successful disclosed service transport/use on these exposed cases under action-format scaffolding, **not successful routing, autonomous first tool choice, parenting, acquisition, or learning**.

Read-only audit of supplied archive/mirror and pinned public semantics; no native/remote/model execution, collector/replay invocation, aggregate-script execution, or evidence/source changes. Only this memo is written. Independent checks used exact bytes, public query lookup and the unchanged strict route scorer; they did not repair outputs or change the endpoint.

## Evidence and prospective status

- Archive: `gpu_artifacts_local/pcfl_structured_action_20260913_attempt1/evidence.tar`, SHA256 `a3745deee039131c037ac2e645e6ab54e6d437eaebd848b8452bc5cad7bdd37c`. All **420 regular files / 430 total members** match the unpacked sibling byte-for-byte.
- Roots in that sibling: `pcfl_interface_structured_action_smoke_20260913_attempt1` and `pcfl_interface_structured_first_read_smoke_20260913_attempt1`, with their `.outer` directories. Each stage's complete capture inventory is bound by its collection receipt (61 and 301 stage files respectively).
- `research_loop/COORDINATION.md:14649`, “collector repair and predeclared two-condition action-format diagnostic,” explicitly declares BOTH conditions before new output inspection, including the additional host-scheduled first READ. This is not a spontaneous second attempt selected from the first outcome. The earlier recommendation for generic-only and Main's prospective additional control are both recorded.
- The earlier READ_REQUIRED_SMOKE/SEQ180 failure and fixed-64 collector bug are not retroactively passed. These separately named controls use the prospectively repaired roster-sized collector; no old-output salvage is involved.

## All-case results

All cases have O/R/D=0/0/0. There are **four preserved excluded roots × two goals**, not eight independent roots or 56 independent tasks. G/F below mean generic/first-READ. Capture indices are zero-based within their respective actors.

| Root, goal | G capture/result | F capture range | F READs / non-MISS | F strict ROUTE outcome |
|---|---|---|---|---|
| excluded/0, 0 | 0: strict, illegal | 0–3 | 3 / 2 | legal, wrong destination |
| excluded/0, 1 | 1: strict, illegal | 4–7 | 3 / 2 | legal, wrong destination |
| excluded/1, 0 | 2: strict, illegal | 8–12 | 4 / 3 | legal, wrong destination |
| excluded/1, 1 | 3: strict, illegal | 13–17 | 4 / 3 | legal, wrong destination |
| excluded/2, 0 | 4: strict, illegal | 18–24 | 6 / 5 | illegal |
| excluded/2, 1 | 5: LENGTH | 25–31 | 6 / 5 | illegal |
| excluded/3, 0 | 6: strict, illegal | 32–39 | 7 / 5 | illegal |
| excluded/3, 1 | 7: strict, illegal | 40–47 | 7 / 5 | illegal |

F's four legal routes use OLD transitions but terminate short of the requested destination. The other four are illegal under actual graph execution; all eight have graph_success=false. G's seven complete routes are syntactically valid but illegal. G capture5 ends at 256 output tokens with finish_reason=length and an incomplete identifier; it remains LENGTH, score=null, not a repaired or omitted response.

F has 38 EVENTS_AT and 2 EVENT reads, **zero LINKS_FROM**, 30 non-MISS returns and 10 MISS returns. All 40 returns were delivered. No THINKs occurred. Actual calls are 8+48; the complete sealed slot denominators remain 104 each, with 96+56 UNCALLED slots retained and no duplicate attempt indices/retries. Handshake is 0/8 versus 8/8; graph success is 0/8 versus 0/8. The recorded interface gate is false/true respectively, never a graph-success gate.

## Sampling, child choice and information delivery

Verified all eight G samples use READ-or-ROUTE regex, all eight F first slots use READ-only regex, and all **40 later F samples** use the identical READ-or-ROUTE regex. Request/slot/seed and sampling receipts agree exactly with pinned `sampling_for`. Common settings: temperature0, top_p1, top_k−1, n1, frequency/presence penalties0, repetition penalty1, ignore_eos=false; max_tokens is the remaining-task-capped 256. The READ grammar is:

```text
READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})
```

The alternative ROUTE grammar permits generic N_/P_ identifiers of the same alphabet/length and comma-separated ports. Neither constraint enumerates registered addresses, ports, graph edges or correct routes. The pinned loader converts the JSON regex dictionary to `vllm.sampling_params.StructuredOutputsParams`; the default actor remains separately identifiable. All 55 stop-completed outputs full-match the intended respective grammar; the LENGTH raw remains untouched.

All eight F first responses are `READ EVENTS_AT <public START>`: the child selected family/address within the generic READ constraint, but **READ rather than ROUTE was externally required**, and the public instruction explicitly directed use of START/returned identifiers. This is not spontaneous tool choice. All 40 READ addresses already appeared in the current public task or earlier delivered service; none required an injected hidden address.

Every service request/raw/role/source-hash tuple matches the sealed query map and unchanged `core.read_query`; query maps independently equal `core.materialize_queries(source_rows)`. Exact LF-terminated EVENT blocks and literal `MISS` were preserved. All next-request histories contain the exact preceding child raw output and exact user-role service bytes, with no paraphrase or repair. Rendered prompts equal only the declared Qwen role wrappers, those messages, and assistant generation prefix: no extra hidden graph/target text. Each task starts afresh with its two public messages.

Paired case IDs, worlds, goals, source rows, service maps, initial public messages and seeds match exactly. Initial prompt tokens match the common 377-token prompt length; histories subsequently differ because actions differ. Both actor identities bind identical Qwen/Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`, model files/environment/source pins and model-binding seal `a7481b25da06b3358abbaa0934c9e2d4983bc667d97cfbeac8bc3eef7ca3e3e2`; mount=C0, lora_request=null. They are separate cold actors on different GPUs, not an identical-compute contrast.

## Raw custody, release and timing

Checked embedded capture UTF-8 and hashes against each actual request/render/raw/response sidecar; request digests, raw_hex, response text, output/prompt token arrays and counts, stop/length flags, request-start/generation/response chronology, per-call remaining limits, and all terminal scores. Prompt/output tokens total **3016/545 G**, **28250/807 F**. No independent tokenizer/model was loaded: token decoding fidelity rests on pinned native validation/replay receipts plus these byte/token crossjoins, not a second local tokenizer certification.

Manifest/input seals and file hashes, stage inventories, collection file inventories, report→completed→replay joins, native identity/load/close hashes, exact completed-copy joins, and release observations all agree. Native custody receipts report verified=true; pure report/replay correctly retain native_custody_verified=false and full_assay_qualified=false. Worker/collection returncodes are integer0, errors=[], fits=updates=generation_retries=0.

Explicit EngineCore shutdown receipts report returned=true. Actor.close itself says shutdown_method_available=false: it did not perform that explicit separately recorded shutdown. It also leaves GPU/group release unknown; those claims come only from the outer evidence. Worker identity joins start/exit/release: G pid=pgid=sid200113/start_ticks54426100; F200181/54426187; common boot `8ff7b0dc-fbdf-4945-9044-3dffe94b5407`, uid2524. Exit signal=null and owned-group release events end with no members. Pre/post GPU compute queries and explicit-CVD scans are clear; direct queue pending/running observations match empty maps.

**Visibility limit:** scans explicitly retain unreadable systemd36935/sd-pam36938 service exceptions, identical approved metadata before/after, environment_read=false, complete_cvd_visibility=false and device_unreserved=null. Owners/unresolved/unexpected lists and own-ancestor exclusions are empty. Thus no observed worker/CVD owner or GPU compute remains; this does not establish those two protected environments are empty, or universal reservation visibility.

| Time scope (seconds) | G | F |
|---|---:|---:|
| Outer entry through release/collection observations | 69.876066 | 81.417805 |
| Command stage, including cold/close | 62.003139 | 74.054270 |
| Report interval | 52.901075 | 65.917614 |
| Actor operation intervals | 52.719883 | 64.661521 |

Outer wall entries are **2026-09-13 16:10:17.268382Z / 16:10:18.147122Z**. These are archived clock values, not inferred from informal time labels. All remain within3600s with120s cleanup margin. Actor timing is wall intervals, not measured GPU-active time. Collection has an outer cumulative interval, not an independently isolated collection-duration measurement. Receipt observation values are projections of separately hashed timing wrappers, not whole-wrapper copies; a preliminary review assertion of whole-wrapper equality was corrected after reading this schema, with no evidence edits.

## Reproducibility pins and limits

Exact archived source bytes verified against all eight manifest source entries, including interface `b62f7f4ffbea11458342223b6118ee89ea60effde6294273f002a152f5e2fbfb`, actor `915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff`, public core `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`, outer `48a843258edefafdad2a0f70430350670e262970df9b10e95965bfd13a040a6c`. Locally used semantic helpers were byte-matched before import; no relocated-source equivalence was assumed.

| File SHA256 | G | F |
|---|---|---|
| manifest.json | `139507309739dc871bd6cf02f40802cc8caba0dc23df61148270f1d715bd2f0f` | `016a6162337b80591b27d5baa038f67f6517e6a53fe18fafe68a8f7a267f2c36` |
| stage completed.json | `022a91f0cfe20262800e803d675fa4798c6a1114fcc54c0d865320b575afe1d0` | `ba2afc27a46a86315ae051db5b1aee25a9a4344103414e821c6196b49ffebb34` |
| outer collection.json | `4744c7ad68b48b8a3906082fbdd432baba419627ab8d09baf677f529b38c45a4` | `d2df88cf10cd5a51fd5a20e26a4d67bb6c5f0e1590d0a0736da7422d4d636156` |

No new fit or child-authored memory exists here. The service is explicitly researcher-authored excluded-root ceiling material, not own experience. Native clean_lineage_certified=false remains a limitation, not overridden by matching base pins. Results do not establish general READ-family coverage (no LINKS_FROM), graph competence, learning, parenting, H1/H2, or full-assay passage. The meaningful narrow contrast is **format-constrained unscheduled choice failed to READ; externally scheduled first READ enabled byte-faithful service interaction, but subsequent strict route decisions still failed all exposed tasks**.
