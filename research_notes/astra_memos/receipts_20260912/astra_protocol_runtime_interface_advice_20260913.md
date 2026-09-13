# Minimal protocol-probe runtime reuse — read-only interface advice

Scope: Main's new teacher-free OFF/AUTH capturer only. No source/runtime edits,
native execution, outcome reads, Git, network or GPU operations were performed.
Keep the fixed16 material unchanged; no new curriculum or C11 framework.

## 1. Normalize birth once during prepare, in its own subprocess

Aliases below: `formation` = frozen `/tmp/astra_born_rulegame_formation_run_20260912.py`;
`birth = formation.birth`; `common = birth.common`; `diagnostic` and `readout` =
the pinned source's `rulegame_parenting_diagnostic` and `fundamental_teaching_readout`.
Load the frozen helper by verified bytes; never monkeypatch its protocol/SELF/constants.

```python
normalized = formation.normalized_in_subprocess(
    fit_root, fit_plan_sha256, fit_release, fit_release_sha256)
formation.verify_custody(normalized, source_root, diagnostic)
child = normalized['pin']['child_identity']
model, auth = child['model_input'], child['adapter_input']
```

Use the original native fit root and original native collection `validation.json`,
not a renamed downloaded validation copy. `accepted_release` checks its filename,
sibling capsule/final_vacancy, evidence hashes, exact phase/root/plan and collector.
Normalization verifies BOTH fits completed/released, AUTH finite saved weights,
terminal/receipt/source/base/adapter joins; no component-pass condition. It loads
no model/tokenizer or fits, but reads/hashes saved weights and original receipts.
The subprocess timeout is300s; use it BEFORE importing another source's organism_v6
modules to avoid old/new source-cache collisions. `verify_custody` then requires
the new snapshot to preserve the original pinned birth dependencies and model/AUTH.
Persist normalized bytes/pins in the new plan; do not rerun normalization in status.

## 2. Prepare native request inputs; reuse only generic capture

```python
candidate = material.build_candidate()
material.check_candidate(candidate)
requests = material.call_map(candidate)  # OFF/AUTH identical16; preserve every setting
native = readout.native_inputs(tokenizer, requests['OFF'])
for request, encoded in zip(requests['OFF'], native, strict=True):
    diagnostic.require(len(encoded['prompt_token_ids']) + request['max_tokens']
                       <= diagnostic.MAX_MODEL_LEN, 'actual role cap exceeds context')
```

IMPORTANT: `readout.native_inputs` uses its historical MAX_TOKENS=64 internally;
the additional per-request400/100 check above is necessary. Do not patch that helper.
Save `tokenizer.eos_token_id` in prepare for later raw EOS/limit flag reporting.
Do NOT call readout.prepare/verify/worker/run/scorers: they bind another48-case task.
Do NOT call birth.capture_receipt unchanged: it hard-codes128calls and64tokens.

Each cell's capture plan needs exactly these consumed fields (extra metadata okay):
`model`, `adapter`, `model_files`, `adapter_files`, `identity`, `requests`, `native_inputs`.
OFF adapter=None/files={}; AUTH adapter=auth/files=normalized['adapter_all_files'];
identity=`diagnostic.expected_identity({'model': model}, adapter)`.
Check AUTH identity equals normalized['pin']['child_identity']; retain exact base pins.
Only request.prompt enters the chat template, not IDs/source/derivation/example labels.
`arm='protocol_practice'` is valid generic capture metadata, not a P/A formation route.

## 3. Two serial fresh owned workers; one bounded controller

Controller uses a Main-bound hard_end=min(start+cap, deadline, lease_cutoff):
```python
with birth.work_window(hard_end):
    for cell in ('OFF', 'AUTH'):
        stage = run / cell
        stage.mkdir()
        with birth.supervisor_window(hard_end):
            diagnostic.supervise(run, {'model': model, 'device': device, 'lease_end': hard_end},
                stage/'worker', worker_argv[cell], stage/'data/calls')
```
Use the SAME `run` accounting root for both workers. Existing limits: worker600s,
cleanup reserve140s, load180s, call120s; inherited reservation ceiling1800s across
supervision receipts, further narrowed by Main's hard_end. No retries after failure.
Do not create stage/worker beforehand: supervise creates it and its process receipt.
Use os.path.abspath(sys.executable), never resolve the interpreter's venv symlink.

Worker validates its sealed spec, source/model/adapter/request pins, then:
```python
with birth.owned_worker(stage/'worker', hard_end):
    data = birth.fresh(stage/'data', (model, auth, source_root))
    data.mkdir()
    readout.capture(cell_plan, data)
```
Here `auth` is the known non-null AUTH path even for OFF (protected input only).
owned_worker requires the real supervisor-created fresh session and watches parent
death/deadline. supervise supplies V6_MODEL/offline/device env and checks release.
capture checks loader identity, records raw request/response/tokens/finish reasons,
compares prepared rendering/tokens, closes backend, and writes usage + manifest.
Write a small isolation receipt before capture if using birth's existing pattern.
Never reuse a backend across cells or introduce teacher calls.

## 4. Thin probe-specific status/collect, not inherited high-level entrypoints

Birth/formation `status`, `collect`, `read_plan`, `launch_contract`, inventories and
terminal reducers are phase/schema-bound; they are NOT generic callable wrappers.
Adapt the existing short formation status algorithm for worker receipts at
run/{OFF,AUTH}/worker/process.json: verify pinned launch/controller joins, collect
owned launcher/controller/worker IDs, then use `common.process_snapshot()` and
its recursive parent plus pgid/session closure. Status reads terminal presence only;
ready means no live owned scope and exactly one success/failure terminal marker.
PID/session release alone is NOT GPU vacancy or permission to inspect partial scores.

Minimal collection sequence (Main, CUDA_VISIBLE_DEVICES unset):
1. `output=birth.fresh(out,(root,logs,launcher)); output.mkdir(mode=0o700)`;
   `with birth.collection_window():` gives300s. Exclusively write collection.claim.json.
2. Require probe status ready; bind actual reviewed launcher hash/command to launch.json
   and exit.json `{launch_sha256,returncode,ended_wall}`; birth release precedes launch.
3. `gpu,xml=birth.vacancy(plan,launch['gpu_uuid'])`; save initial_vacancy.xml.
   This checks selected-device process/queue occupancy and exact UUID via the pinned
   source checker; do not invoke it in this advice task or treat backend.closed as release.
4. For success, require both16-pair call inventories, manifests, identity, cleanup,
   supervision and raw request/response hashes/tokens/time joins. Replace birth's64/128
   constants with each request.max_tokens/16; preserve finish/stop/EOS/raw-limit flags.
   Freeze both manifest hashes in one capture-barrier receipt BEFORE calling
   `material.check_outputs(candidate, outputs)` once for all32. No cell-only reducer.
5. Explicit small allowlist for plan/material/native audit, both raw captures/worker
   logs, terminal/launcher and collection receipts. For each file use birth.raw,
   common.scan_text and hash; reject unknown files/links/credentials. No adapter bytes.
   `archive_sha=common.pack(output/'capsule.tgz', files, hashes)` with archive member
   names under metadata/; pack is exclusive and already validates every member.
6. Recheck status, inventory hashes and `birth.vacancy(plan,launch['gpu_uuid'])`;
   save final_vacancy and released validation. Bound launch→release by Main's cap+300
   and lease cutoff; durations are nested, not added. On any failure preserve files,
   write collection_failure, no accepted release/blind retry/phase chaining.

The existing checker uses only process/queue inspection for collection, not model
or tokenizer replay. Keep finite-weight checking in birth normalization; collector
can rehash normalized custody inputs without inventing new checkpoint semantics.
Formatting caveat remains: public_contract_correct is action-string-sensitive;
report it alongside parser_valid/exact_target, not as pure hidden-rule knowledge.
Stop filtering means absent returned OUTCOME is not proof none was attempted.

## Reviewed bytes / handoff

- Formation helper SHA256: 90919a280f78cce8f41c1ef7bf7b08e722f4ab0b3cf3d278d256bfd91653dda4
- Birth helper SHA256: 072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa
- Generic readout SHA256: d6eebc6e70f5a76fcde6c530aeacc273ae5f29a8d9a67ffe5948f04842684bb6
- No new CPU/native execution in this read-only interface review. Main owns runtime
  implementation/CLI tests and actual launcher hash binding. This note is not a launch.
