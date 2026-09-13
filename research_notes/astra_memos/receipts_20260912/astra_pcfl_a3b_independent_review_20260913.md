# SEQ-183 A3B independent result review — 2026-09-13

## Verdict and authority

**ACCEPT the narrow descriptive result and retained capture/accounting evidence. The predeclared joint interface gate FAILED: 4/8, against a 7/8 threshold. No evidence-integrity blocker was found in the inspected capsule. This is not scientific-claim approval or launch authorization.**

All 25 native-labeled captures have consistent retained request, sampling, raw-output, response, identity, token-count and byte-hash joins. All eight first responses satisfy the exact THINK predicate; 17 THINK turns actually entered the conversation loop. Only four tasks subsequently emitted a syntactically strict ROUTE; all four were graph-illegal. The other four terminated INVALID_TURN. Thus 8/8 first-THINK, 4/8 joint THINK/strict-terminal, 0/8 legal routes, and 0/8 graph successes are different quantities, not competing scores.

Independent, fresh-context, **outcome-aware** static review: I read SEQ-183 and Main's post-outcome audit, then checked the retained evidence independently with standard-library Python and inspected archive-pinned source, without importing the live driver. This is not blinded scoring, a new seed, a replication, or a second native execution. No code edits, GPU access, network access, job launches, model/tokenizer execution, test-suite execution, or literature lookup were performed. The sole written artifact is this file. Main remains integration/launch owner; this review neither implements a successor nor pauses unrelated authorized builder work.

## Evidence locations and identity

All relative paths below are relative to `/data/home/rohing/dream-state` (the shell resolves this checkout to `/home/rohing/dream-state`). Define:

- `B = gpu_artifacts_local/pcfl_a3b_20260913_attempt1`
- `U = B/unpacked`
- `R = U/pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1`
- `S = R/A3B_NEWLINE_FRAMED_SMOKE`
- `O = U/pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1.outer`
- `T = U/astra_pcfl_a3b_source_20260913_attempt1.tar`

The archive's **194 regular files** are byte-identical to their unpacked siblings; no duplicate regular-file member names were found. Source was read with `tar -xOf T <member>`, never from the mutable checkout driver. All eight project source pins in the captured actor identity match members of T. T contains 316 regular files. The notebook identifies source commit `4ca790d546d1b93b1499de25440ccc1db5997def`; the direct content authentication here is the archive/member SHA256, not an independent Git-commit reconstruction.

| File or source member | SHA256 of file bytes |
| --- | --- |
| `B/evidence.tar` | `fb4b074911f8d8190bd71caef846d6b1440ca56f9b8ad19003ec1ddcfdb391ae` |
| `T` | `cf6ee7375ebedd1956d7c46b47c561aaae0cbd8189b3d12d59a287b8eb5e1e2c` |
| `T::gpu/astra_pcfl_interface_dev.py` | `b07004bfc1f27e025ee4f611ac3c7d51219ea8bda751b1f399b6e87ac9ced8de` |
| `T::gpu/astra_pcfl_native_actor.py` | `a69d2f1d0b5060af31f7ad900b5250bbbacce8b38b20ec1d28039c8e5d447fc4` |
| `T::gpu/astra_pcfl_interface_command.py` | `8f1a9c733cd0b6da66f821683695099811c87d17ba498d656b7f139afa251217` |
| `T::gpu/astra_pcfl_interface_outer.py` | `48a843258edefafdad2a0f70430350670e262970df9b10e95965bfd13a040a6c` |
| `T::gpu/astra_pcfl_vertical_dev.py` | `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1` |
| `T::gpu/astra_pcfl_zero_fit_dev.py` | `7bcc99f89b661f2f77202c3cc5aa61533bad2daff25f5b548ed8e1ecd1c1b5d5` |
| `T::gpu/astra_pcfl_zero_fit_outer.py` | `fdd29c64bc73b1602998e6509da9f6d3132b90f9a5d50dceb1ad20ce86128f19` |
| `T::organism_v6/pcfl_vertical_dev.py` | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |
| `R/manifest.json` | `9b39c966f41f4bf87544b1e032352cdf2b7c82218d0f171483a0893061e202e7` |
| `S/completed.json` | `e94a22d8901bbfbd67707f88e1452c8b7305006021405b7c1df847e918412b45` |
| `S/records/report.json` | `535cf07dbebd3d87a79253ae8ebd6e33cd8da07bd30c39fe6defc1ade9c2c393` |
| `S/records/roster.json` | `5cf0349d9a7c7b9ee3dd6c0679f647d03b9c6f7b7cdbbcabd3efb1116a5d65b4` |
| `S/custody.json` | `7f8d7f4c3e43609a5cd1e814a8859e35c59b28647d9484d9ba752c6e778dbbde` |
| `S/replay.json` | `bc224b754c50d4923ca4f5ebe2164120c7798372aae7dae45f1a32fed343ec8a` |
| `O/collection.json` | `fbe7fddde69ae8fa1c19091e6035ab4c3c98bbfb05f1f81509601f16eb4b159a` |
| `O/worker_release.json` | `f07752738deee6c6c7f17806973efbe74f83a39119d508be0f5df14c172f1c08` |
| `O/allocation.input.json` | `217fb3ba2b31f919e47c9bb4e911157970ba02cae98b1adab156e2c19895f1ec` |
| `R/roots.input.json` | `bcca78ae2abadb2a5f9680dc70ed55327185614198a4b873a5f3e487b2ed443e` |
| `U/astra_qwen_node2_binding_20260913_attempt1.json` | `a7481b25da06b3358abbaa0934c9e2d4983bc667d97cfbeac8bc3eef7ca3e3e2` |

Main's supplied audit is `research_notes/astra_memos/receipts_20260912/astra_pcfl_a3b_audit_20260913_attempt1.json`, file SHA256 `e61632ca08c6415dfcc56ca0b4c0647abe76df9d144a27066fb998127ac1b039`. Its companion `.py` is SHA256 `d9dbf46eb748638659086e695ce30ea0192bc147a237b283565df3a66ce01ea7`. I inspected but did not execute that script. It pins the driver and checks the stored decode/frame relation; its PASS label is not itself independent retokenization or scientific approval.

SEQ-183 starts at `research_loop/COORDINATION.md:14871` in the inspected notebook. Nearby entries record the prospective eight-case framing scope and later report the failed gate. Notebook line numbers can move as others append/edit; this review makes no notebook changes.

## All 25 captures: LF relation, identities, budgets

For each index 0000–0024, I joined `S/records/attempt_NNNN.json`, the corresponding embedded report attempt, and all six embedded capture files to the original `S/actor/` bytes: config, identity, request, render, raw and response. Each capture's own SHA256 matched its UTF-8 bytes. All kinds are NATIVE, all mounts C0, all LoRA requests null, and the identity PID is 205563. Request digests, limits, seeds, response raw hex/UTF-8 hashes and full prompt/output ID-array lengths agree. Captured raw prompt IDs equal rendered prompt IDs; no extra/error capture replaces a success capture.

All sampling dictionaries match the pinned policy: temperature 0, top_p 1, top_k -1, n 1, presence/frequency penalties 0, repetition penalty 1, ignore_eos false, the task seed, max_tokens 256, `stop=["\n"]`, and `include_stop_str_in_output=false`; no structured-output constraint. See pinned driver:153–175 and native actor:28–30.

**Nine LF cases:** `finish_reason="stop"`, `stop_reason="\n"`, and stored `decoded == raw.text + "\n"` exactly. The raw returned text has no LF/CR; there are no extra hidden words after the delimiter in these nine observed decodes. Every LF capture ends with output token ID 624. **Sixteen non-LF/EOS-class cases:** finish stop, stop_reason null, stored decoded/returned text exactly equal, and final output token ID 151645. There are zero LENGTH cases. All eight initial THINKs are LF-framed; the only later LF is call 0023. All eight terminal outputs use the non-LF/EOS-class relation, including the four malformed ROUTEs.

| Call | Returned type | Stop class | Prompt IDs charged | Output IDs charged |
| --- | --- | --- | ---: | ---: |
| 0000 | THINK | LF | 542 | 41 |
| 0001 | ROUTE | EOS-class | 609 | 43 |
| 0002 | THINK | LF | 542 | 164 |
| 0003 | ROUTE | EOS-class | 732 | 51 |
| 0004 | THINK | LF | 542 | 31 |
| 0005 | THINK | EOS-class | 599 | 28 |
| 0006 | THINK | EOS-class | 652 | 53 |
| 0007 | ROUTE, invalid grammar | EOS-class | 730 | 43 |
| 0008 | THINK | LF | 542 | 31 |
| 0009 | THINK | EOS-class | 599 | 36 |
| 0010 | ROUTE, invalid grammar | EOS-class | 660 | 34 |
| 0011 | THINK | LF | 542 | 98 |
| 0012 | THINK | EOS-class | 666 | 84 |
| 0013 | ROUTE, invalid grammar | EOS-class | 775 | 33 |
| 0014 | THINK | LF | 542 | 31 |
| 0015 | ROUTE | EOS-class | 599 | 51 |
| 0016 | THINK | LF | 542 | 32 |
| 0017 | THINK | EOS-class | 600 | 48 |
| 0018 | THINK | EOS-class | 673 | 130 |
| 0019 | ROUTE | EOS-class | 828 | 59 |
| 0020 | THINK | LF | 542 | 32 |
| 0021 | THINK | EOS-class | 600 | 63 |
| 0022 | THINK | EOS-class | 688 | 78 |
| 0023 | THINK | LF | 791 | 153 |
| 0024 | ROUTE, invalid grammar | EOS-class | 970 | 57 |
| **Total** | **17 THINK + 8 terminal attempts** | **9 LF + 16 EOS-class** | **16107** | **1504** |

No generated IDs were subtracted for the stripped LF or special terminal tokens. The output count is the full retained array length, not a re-encoding of the shorter returned string. Maximum observed output length is 164, below 256; maximum prompt length is 970. All per-task charged totals match, and every task remains below 2048 generated tokens. The roster permits 56 calls, six THINKs and one terminal slot per task; 25 are consumed and the remaining 31 slots are uncalled tails, not omitted failed experiments.

**Verification boundary:** I checked stored decode strings against stored raw strings and token-array accounting; I did not independently run a tokenizer to establish IDs-to-text or messages-to-rendered-prompt equality. The pinned native actor performs tokenizer.decode on the full output IDs before saving the response (native actor:417–431); pinned driver `_verify` rerenders/redecodes during the recorded original replay (driver:264–290). T does not include tokenizer.json, tokenizer_config.json, vocab.json, merges.txt, or the installed vLLM core_client.py. Their recorded hashes are evidence bindings, not locally available executable dependencies. “EOS-class” above describes the observed finish/stop/token tuple, not a fresh verification of the tokenizer's special-token map.

## Turn reconstruction and independent graph check

I reconstructed all eight conversations from roster messages plus each exact returned THINK and the fixed CONTINUE string. All 25 request message lists, slot IDs and seeds match that reconstruction; each of the 17 accepted THINKs has the subsequent continuation call. No READ or memory-service response is inserted. This is actual typed-loop execution, not merely outputs beginning with the word THINK.

The pinned driver uses `re.fullmatch(r"THINK [^\r\n]+", raw)` plus a nonwhitespace-content check (driver:386–391). Its framed gate counts tasks with at least one accepted THINK **and a strict terminal ROUTE**, requires 7/8, and does not require graph success (driver:307–341). Calling it a “joint route gate” must not obscure that it is an interface gate; even a hypothetical 7/8 pass would not establish route-solving ability.

Every selected task is one of indices `(0,1,16,17,32,33,48,49)`: four excluded roots, old/relevant/distractor all zero, two goals per root. I parsed only the public EDGE lines and searched simple paths independently of the project's scorer. Every task has exactly one public start-to-goal path, of length five. Applying the exact ROUTE grammar and traversing public directed edges reproduces all eight strict/legal/success flags.

| Root / goal (all switches 0) | Call indices, inclusive | Accepted THINKs | Terminal result | First concrete defect |
| --- | --- | ---: | --- | --- |
| 0 / 0 | 0000–0001 | 1 | strict, illegal | Step 2 requests registered `P_JFTRJJNMXM` at `N_IPQ2WLA2DK`; that edge is not outgoing there. |
| 0 / 1 | 0002–0003 | 1 | strict, illegal | Step 1 requests unregistered `P_DPH5JSJYDT` at `N_S6JZXHYXBT`. |
| 1 / 0 | 0004–0007 | 3 | INVALID_TURN | Port list `RPRTAHQJHF, P_QKUOHFCFN7, W2GYE4FYXE` has bare identifiers and spaces. |
| 1 / 1 | 0008–0010 | 2 | INVALID_TURN | Port list starts with bare `RPRTAHQJHF`. |
| 2 / 0 | 0011–0013 | 2 | INVALID_TURN | Port list `V7JDYLIKJ2 JKGQFEUMDQ` has no P_ prefixes or comma separator. |
| 2 / 1 | 0014–0015 | 1 | strict, illegal | Step 3 requests unregistered `P_JKGQFEUMDQ` at `N_IQZJID3SEE`. |
| 3 / 0 | 0016–0019 | 3 | strict, illegal | Step 2 requests unregistered `P_Y5DKX2EZGE` at `N_Y5DKX2EZGE`. |
| 3 / 1 | 0020–0024 | 4 | INVALID_TURN | Bare node-like identifiers and spaces replace the required prefixed comma-separated ports. |

For example, root 0 / goal 0's unique valid port sequence is `P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH,P_RK7VLTKHNM`. Call 0001 instead returns `P_7MGNA5ALJT,P_JFTRJJNMXM,P_RK7VLTKHNM`. The defect is not only formatting: all three returned ports are registered, but the second is inapplicable at the reached node and the route omits required transitions. In the other three strict failures, node suffixes have been presented as port identifiers. None of these judgments needs forgiving parsing or retrospective identifier repair. Reference scorer definitions: pinned core:68–75, 239–261, 324–350.

## Inventory, replay and owned cleanup

- Rehashed all **162** files bound by `S/completed.json`; the only stage file outside that inventory is completed.json itself. Rehashed the outer's **163** stage-inventory entries including completion, and all **18** outer-inventory entries, including their sizes. The only outer file outside its own inventory is collection.json itself. Both self-exclusions are closed by the supplied archive hash.
- Recomputed canonical body seals for report, roster, completion, manifest and collection. Report's **body seal** is `abd2c722dfea577d748be3a386e27409b4138bf6d12495eb03d7c6fe8298e9c4`; that is not its file-byte hash in the table. Similarly the manifest body seal is `6990680059d3a1656051885aaec5003729e80a116cbbe1a701cd3d5bc43e30ad`, completion body seal `543d571846e49938c57805ebd755a4c0e902d620302e7100e08c07784abddd7c`, and collection body seal `cd6abbd7188d4a097a19ac72e0ed7e9795952793c9f1924b56caf8f9f55f8681`.
- The five prepared-input hashes match; prepared and stage rosters agree; original and outer manifest copies are byte-identical; original and outer completion copies are byte-identical. Manifest/completion/report/roster/replay/collection references and summary fields agree.
- `S/replay.json` records local_replay_valid=true but native_custody_verified=false. That is **not** a native-custody failure: pinned replay intentionally returns false for that separate authority (driver:495–515). `S/custody.json` subsequently records native_actor_custody_verified=true, joins every captured identity to the live worker identity at production time, joins load/close hashes, and verifies 25 calls/16107 prompt/1504 output tokens (command:156–185). This review freshly rechecked the archived joins and turn/graph reconstruction, not the full tokenizer-dependent `replay_validate` function.
- C0/no-LoRA and zero fits/updates are consistent across report, identity, load and completion. Captured model binding names Qwen/Qwen2.5-7B-Instruct at revision `a09a35458c702b33eeacc393d103063234e8bc28`; its local binding-file hash matches. Model weight files and external runtime dependencies were not rehashed here; clean_lineage_certified remains false.
- Worker identity joins across start, exit, release, collection and actor PID: PID=PGID=SID **205563**, UID **2524**, start_ticks **54542714**, boot_id **8ff7b0dc-fbdf-4945-9044-3dffe94b5407**. Worker wait/exit return 0, signal null. The release record has one observation with `members=[]`, no signal event, and owned_group_released=true. This is stronger than trusting `actor_close.json` alone. Pinned cleanup only signals an identified owned group if members remain (zero_fit_outer:318–338); the observed path needed no signal.
- Native generic close reports shutdown_method_available=false, but `S/shutdown.json` separately records the command's explicit `llm.llm_engine.engine_core.shutdown` returned true, with installed source SHA256 `7f5e1ac1a999faf36eab7d0c184bea7c93ae5e92234c39a148a809fd6e89840c`. Completion's gpu_released=false/outer_release_required=true is likewise intentional: final release is the outer's responsibility. These fields are not contradictions (command:146–153, 234–240; interface_outer:111–132).
- Pre/post GPU receipts identify node2 GPU0 UUID **GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0**, empty compute-process lists, and successful recorded queries. Queue observations match empty pending/running allowlists. CVD receipts are clear with no owners/unexpected/unresolved entries, **but complete_cvd_visibility=false** and status PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS. Two allocation-bound, unreadable-environment service exceptions cover systemd PID36935 and sd-pam PID36938; their before/after metadata agree. Do not paraphrase this as exhaustive process-environment visibility or global reservation proof.
- Outer collection status COMPLETED, errors=[], generation_retries=0. The one-hour outer bound, 120-second cleanup reserve, 3480-second worker deadline, and six-hour declared lease margin are mutually consistent; recorded exit precedes those bounds. These are historical archived observations, not fresh remote vacancy or lease checks.
- Outer elapsed time is **97.50548254500609 s**, including cold startup and cleanup. Stage completion records **90.49440233898349 s**. Sum of returned per-call device_seconds is **81.82837472273968 s**; actor-close accumulated time is **81.864320521825 s**. The latter includes finally/close accounting after response timing (native actor:426–442, 464–480), so equality is not expected. None is measured GPU-active time. My initial scratch check wrongly required exact equality; source inspection resolved that reviewer assumption, with no evidence modification.

## Blockers and advisories

### B1 — Result promotion is blocked by the actual joint gate

The bound result fails 7/8 with only 4/8 strict terminal tasks. Eight first THINKs cannot substitute for that denominator or endpoint. Do not label A3B passed, silently weaken the gate, expand it automatically to the 64-case panel, or automatically launch A4 on this result. This is the same stop on automatic progression stated in SEQ-183, not a new blanket veto over Main's separately scoped experiments. Disposition: preserve the failed gate and keep any successor decision prospective and Main-owned.

### B2 — Causal/scientific promotion is unsupported

“Externally framed typed THINK turns executed on eight exposed DEV tasks” is supported. “The model learned reasoning,” “THINK improves route accuracy,” “recurrent deliberation works,” “memory/parenting/H1/H2 improved,” or “the base model cannot reason” is not supported. There is no fit, no adapter, no learned intervention, no READ, no withheld-graph information, and no successful route. This is the researcher-authored excluded-root full-graph ceiling, not a child-life or supplied-memory utility result.

The framed driver prospectively changes generation boundaries and therefore subsequent conversation history. It does not show that the old A3 outputs would have completed valid multi-turn routes after post-hoc splitting. Initial task content/seeds are designed to match selected A3 cases in the pinned builder, but the supplied A3B capsule is not a newly audited paired original-A3 execution. The earlier mixed-turn failure remains unchanged. Eight cells comprise only four root structures with shared-goal pairs, all at one switch setting; neither 25 calls nor 17 thoughts are independent seeds. No population rate, statistical gain, or isolated reasoning-mechanism effect follows.

“Failure now includes identifier/path composition beyond transport” is a defensible **behavioral description**, because the four strict terminals are complete, non-LF, graph-illegal outputs. It is not a causal localization of an internal reasoning deficit: representation/copying, prompting, external framing and the terminal action interface remain entangled. Disposition: retain descriptive wording; do not turn it into a mechanism claim without separately justified evidence.

### A1 — Portable replay is bounded, not hermetic

The archive preserves full token IDs/recorded decodes and pinned project source, but omits tokenizer bytes, model weights and installed shutdown implementation. Local standard-library verification can authenticate the evidence joins, not independently execute those absent dependencies. This does not invalidate the observed frame relation/counts; it limits any assertion of a wholly self-contained native replay. Do not report this review as a fresh native/tokenizer replay or a stronger lineage certificate.

### A2 — Controller disappearance is not independently established here

The launch and binding receipts identify controller **205552** (start_ticks **54542241**). The capsule proves the worker's observed exit/release and the post-run resource observations. Its terminal collection is written by the controller and is not a later independent observation that the controller itself disappeared. SEQ-183 says both controller and worker are gone; controller disappearance is notebook-reported, not freshly authenticated from a post-controller liveness receipt in this capsule. No remote/process probe was made or requested. This is a provenance qualification, not a claim that controller 205552 remained running.

### A3 — Keep layers and clocks separate

Stage COMPLETE is infrastructure completion, not gate PASS; replay-valid is not native-custody verification; stage gpu_released=false is not the final outer release; CVD clear-with-exceptions is not full visibility; wall-operation timing is not GPU-active timing. The artifacts already preserve these distinctions. Future summaries should too.

## Reproducibility commands (read-only)

Commands were run from the checkout with shell reads and `python3 -B` standard-library in-memory checks. `python` is not installed in this shell; an initial invocation failed before execution and was replaced with python3. No archive was extracted or project code imported. Source inspection examples:

```bash
sha256sum gpu_artifacts_local/pcfl_a3b_20260913_attempt1/evidence.tar
tar -tf gpu_artifacts_local/pcfl_a3b_20260913_attempt1/evidence.tar
tar -xOf gpu_artifacts_local/pcfl_a3b_20260913_attempt1/unpacked/astra_pcfl_a3b_source_20260913_attempt1.tar gpu/astra_pcfl_interface_dev.py | nl -ba | sed -n '153,202p'
tar -xOf gpu_artifacts_local/pcfl_a3b_20260913_attempt1/unpacked/astra_pcfl_a3b_source_20260913_attempt1.tar gpu/astra_pcfl_interface_dev.py | nl -ba | sed -n '307,341p'
tar -xOf gpu_artifacts_local/pcfl_a3b_20260913_attempt1/unpacked/astra_pcfl_a3b_source_20260913_attempt1.tar organism_v6/pcfl_vertical_dev.py | nl -ba | sed -n '324,350p'
sed -n '14871,14903p' research_loop/COORDINATION.md
```

The compact check below reproduces the central inventory, all-capture framing/token and public-graph counts without native execution. It deliberately treats stored decoded strings as evidence, not as an independently verified tokenizer decode. Additional checks described above included all source pins, request/identity/chronology joins, prepared-input copies, and outer wrapped `.value` observations.

```bash
python3 -B - <<'PY'
import collections
import hashlib
import json
from pathlib import Path
import re
import tarfile

base = Path('gpu_artifacts_local/pcfl_a3b_20260913_attempt1')
root = base / 'unpacked/pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1'
stage = root / 'A3B_NEWLINE_FRAMED_SMOKE'
outer = root.with_name(root.name + '.outer')
read = lambda path: json.loads(path.read_bytes())
sha = lambda data: hashlib.sha256(data).hexdigest()
with tarfile.open(base / 'evidence.tar') as archive:
    members = [member for member in archive.getmembers() if member.isfile()]
    assert len(members) == len({member.name for member in members}) == 194
    for member in members:
        assert archive.extractfile(member).read() == (base / 'unpacked' / member.name).read_bytes()
report = read(stage / 'records/report.json')
roster = read(stage / 'records/roster.json')
completed = read(stage / 'completed.json')
collection = read(outer / 'collection.json')
for folder, inventory in [(stage, completed['files']), (outer, collection['files']),
                          (stage, collection['stage_inventory'])]:
    for name, record in inventory.items():
        data = (folder / name).read_bytes()
        assert sha(data) == (record if isinstance(record, str) else record['sha256'])
        if isinstance(record, dict):
            assert len(data) == record['size']
stops = collections.Counter()
prompt_tokens = output_tokens = 0
for index, attempt in enumerate(report['attempts']):
    assert attempt == read(stage / f'records/attempt_{index:04d}.json')
    assert attempt['capture']['index'] == index and attempt['error'] is None
    prefix = f'call_{index:04d}.'
    expected_files = {'config.json', 'identity.json'} | {
        prefix + suffix + '.json' for suffix in ('request', 'render', 'raw', 'response')}
    assert set(attempt['capture']['files']) == expected_files
    for name, record in attempt['capture']['files'].items():
        assert record['utf8'].encode() == (stage / 'actor' / name).read_bytes()
        assert sha(record['utf8'].encode()) == record['sha256']
    raw = read(stage / 'actor' / (prefix + 'raw.json'))['raw']
    returned = read(stage / 'actor' / (prefix + 'response.json'))
    render = read(stage / 'actor' / (prefix + 'render.json'))
    response = attempt['response']
    assert returned['response'] == response and response['text'] == raw['text']
    assert render['prompt_token_ids'] == raw['prompt_token_ids']
    assert response['prompt_tokens'] == len(raw['prompt_token_ids'])
    assert response['output_tokens'] == len(raw['output_token_ids']) <= 256
    assert render['sampling']['stop'] == ['\n']
    assert render['sampling']['include_stop_str_in_output'] is False
    assert 'structured_outputs' not in render['sampling']
    assert raw['finish_reason'] == 'stop'
    if raw['stop_reason'] == '\n':
        assert returned['decoded'] == raw['text'] + '\n'
    else:
        assert raw['stop_reason'] is None and returned['decoded'] == raw['text']
    assert '\n' not in raw['text'] and '\r' not in raw['text']
    stops[str(raw['stop_reason'])] += 1
    prompt_tokens += response['prompt_tokens']
    output_tokens += response['output_tokens']
first_thinks = thoughts = strict_count = legal_count = success_count = 0
consumed = []
pattern = r'ROUTE (N_[A-Z2-7]{10}) (N_[A-Z2-7]{10}) : (P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)'
for task, result in zip(roster['tasks'], report['results']):
    messages = list(task['messages'])
    accepted = 0
    indices = [slot['attempt_index'] for slot in result['slots'] if slot['attempt_index'] is not None]
    for position, index in enumerate(indices):
        consumed.append(index)
        attempt = report['attempts'][index]
        assert attempt['request']['messages'] == messages
        text = attempt['response']['text']
        think = bool(re.fullmatch(r'THINK [^\r\n]+', text)) and bool(text[6:].strip())
        if position == 0:
            first_thinks += think
        if think:
            accepted += 1
            messages += [{'role': 'assistant', 'content': text},
                         {'role': 'user', 'content': roster['continue']}]
        else:
            assert position == len(indices) - 1
    assert accepted == result['thinks'] and text == result['raw']
    thoughts += accepted
    public = task['messages'][1]['content']
    edges = re.findall(r'^EDGE (\S+) (\S+) (\S+)$', public, re.M)
    start = re.search(r'^START (\S+)$', public, re.M).group(1)
    goal = re.search(r'^GOAL (\S+)$', public, re.M).group(1)
    pending, paths = [(start, [], {start})], []
    while pending:
        current, ports, visited = pending.pop()
        if current == goal:
            paths.append(ports)
            continue
        for source, port, destination in edges:
            if source == current and destination not in visited:
                pending.append((destination, ports + [port], visited | {destination}))
    assert len(paths) == 1 and len(paths[0]) == 5
    parsed = re.fullmatch(pattern, text)
    strict, legal, success = parsed is not None, False, False
    if strict:
        assert parsed.group(1) == start and parsed.group(2) == goal
        current, legal = start, True
        for port in parsed.group(3).split(','):
            matches = [destination for source, edge_port, destination in edges
                       if source == current and edge_port == port]
            if len(matches) != 1:
                legal = False
                break
            current = matches[0]
        success = legal and current == goal
    assert (strict, legal, success) == tuple(result['score'][key]
                                           for key in ('strict', 'legal', 'graph_success'))
    strict_count += strict
    legal_count += legal
    success_count += success
assert consumed == list(range(25))
assert (first_thinks, thoughts, strict_count, legal_count, success_count) == (8, 17, 4, 0, 0)
assert (prompt_tokens, output_tokens) == (16107, 1504)
assert stops == {'\n': 9, 'None': 16}
assert report['summary']['stage_gate_passed'] is False
print('PASS: retained framing/accounting; first THINK 8/8; joint 4/8 FAIL; legal/success 0/8')
PY
```

**Disposition:** retain SEQ-183's failed joint gate and its narrow positive transport/typed-loop observation. No repair to the preserved run is requested. Keep original artifacts immutable, retain all visibility/replay limitations, and leave any separately scoped successor integration or launch to Main.

EDITSTOP
