# Lower-LR local analysis handoff — September 12, 2026

**Preparation only; main retrieves terminal results and owns interpretation/resources.** User-estimated completion is **September 12, 2026, 10:40 UTC**, not an observed completion. No SSH, GPU, Git, fits, or campaign-analyzer changes are needed for this handoff. Analyze only the two launched rates against the existing seed2/bank0 baseline; no extra experiments.

## Actual runs and retrieval checklist

Local launch receipts supersede the earlier proposal's node2/new-root suggestions. Both jobs execute on **node3**, while the historical baseline ran on **node2**:

- 3e-5: `/localhome/local-rohing/astra_diagnostics/astra_A1_lowerlr_bank0_ts2_3e5_20260912_attempt1`; recorded start10:13:57 UTC.
- 1e-5: `/localhome/local-rohing/astra_diagnostics/astra_A1_lowerlr_bank0_ts2_1e5_20260912_attempt1`; recorded start10:14:01 UTC.
- Local baseline root: `/tmp/astra_seed_bank0_evidence_20260912/runs/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912`.

Receipts `/tmp/astra_lowerlr_{3e5,1e5}_launch_20260912.json` say `LAUNCHED_NOT_COMPLETED`, `model_authentication=UNRESOLVED_LOCAL_HASHES_ONLY`. The jobs' source commit is `52e0e4db0d67d54defa4151cb091ccc925cd9e8c`, not the baseline's `f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`. I read the local source tar without extracting it: **memory_dose.py still hashes to `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`**, identical to baseline. The preparation helper is also byte-identical. Same code is not proof of identical cross-node model/dependency/initialization bytes.

Main should capture, preserving relative paths and remote-path strings:

- `seed_run_receipt.json`, `manifest.json`, `distractor.json`, `banks/bank{0,1,2}.json`, `corpora/bank0/F_r16k16/across/sleep4/corpus.json`.
- `adapters/bank0/F_r16k16/across/sleep4/r8/{DONE,train_meta.json,throughput.json}`; adapter configuration/hash evidence if available. Weights are not needed for CPU analysis; preserve them at source.
- `eval/bank0__F_r16k16__across__sleep4__r8__lam1.json`, `report/report.json`, `report/F_r16k16__across__r8__lam1.md`.
- `provenance/comparison.json`, `logs/{launch_receipt.json,controller_result.json,worker.log,controller.log}`, execution-source hashes and any existing model/runtime receipts. Bind retrieved bytes with a capture manifest/hash list; do not rewrite paths or fabricate missing authentication.

`DONE` alone is not evaluation/report completion. Read controller status and artifacts; missing/failed/partial outputs are **unavailable**, never an inferred scientific failure or a reason to recreate a fit. Worker completion and matching fit exposure must be recorded separately from scientific G9. Keep native reports unchanged; **do not run `memory_dose report` inside captured roots**, because it writes there. Never run `evaluate` locally: that loads a model. The pure functions below need no model or GPU.

## Exact match checks before a matched interpretation

1. **Source/fit binding.** Check captured files against their receipts and against the baseline bytes, especially corpus SHA256 `f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d`, bank0 `87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31`, manifest and distractor. Keep source-bank seed1 distinct from training seed2. Actual fit must be rank8/alpha16/dropout.05, original target modules, batch4/max512, three epochs/**9,693 actual steps**, 12,924 items, 749,985 input/711,213 supervised tokens, zero training straddles/truncations, no gradient checkpointing, and the expected actual LR. Compare recipe/model/order/masks metadata to baseline. Preserve source manifest `lora.lr=1e-4`: it describes historical source, not treatment LR. Check eval `adapter` against the **remote** `receipt.destination_run` plus adapter-relative path, not against the relocated capture path; join eval `adapter_meta` to actual train metadata.
2. **Cue identity, not positional score pairing.** Require 1,313 rows and 1,313 unique `cue_id`s. Join by `cue_id`; separately report ordered cue-ID equality because batching/order may affect numerics. Compare **every saved non-score field**, i.e. each row minus `OFF`/`ON`: this includes `kind`, `owner`, `lesson_id`, `dose`, `a`, `b` when present, `form`, `context`, `cue_id_used`, `tool`, `cand_tokens`, and `abstain`. Do not drop extra fields or coerce missing/null values. Preserve candidate-key order too (OFF tie-breaking can depend on it). Exact metadata equality also preserves the legacy question-cue controls.
3. **Completeness.** Frame inventory must be64 owner frames (16 each at dose0/1/4/16), 48 `frame_similar`, 48 `frame_bicycle`; each exposed owner must have both controls and each dose16 owner its matching look-alike. Check owner/dose/colour/control-ID joins against the frozen bank. OFF/ON candidate keys must match `cand_tokens`; numbers must be finite, probabilities nonnegative, mass and candidate probability sum positive. Preserve all176 frame-family abstention values. No missing-control/zero imputation. Native summaries alone are not a completeness validator.
4. **OFF equality, all three pairs.** Compare baseline↔3e-5, baseline↔1e-5, and3e-5↔1e-5 across all1,313 cue IDs. Exact parsed-JSON equality of the entire OFF object is the primary observation; separately count changed cues and report maximum absolute differences for each of `p_raw`, `mass`, `logp`, `p_abstain`. Preserve missing-key distinctions. Values are serialized at **7 decimals for probability/mass/abstention, 5 for logp**; equality only establishes equality at that precision, not bit-identical tensors. No new numeric tolerance or pass threshold: report drift as drift, retain each arm's own OFF, and qualify the node2/node3 comparison rather than silently substituting/rebaselining scores. Same-node OFF agreement is informative but cannot authenticate historical weights.
5. **Eval configuration.** Match `bank=0`, `meta={cell:F_r16k16,arm:across,sleep:4,rank:8}`, `model=hf`, `lam=1`, `synthetic=true`, `template_check=true`, full `abstain_check`, `tokenization`, and **eval** `boundary_straddles=512` (different from training's0). Seed0/adjacent-subset4/batch-size16 are documented in the launch job, not top-level eval fields. Compare the recorded job/source as well. Eval JSON intentionally omits prompt/candidate strings; saved metadata plus identical bank/distractor/code and tokenization receipts bind the intended cues, not a recovered execution-time prompt-byte seal.

The native G9 remains **dose16 paired-owner interval lower bound >0 AND spill <=.03**, bootstrap2,000/seed0, n16. Spill equally weights the three means over48 similar,16 unexposed,48 bicycle owners—not112 pooled rows. Keep scientific G9 separate from source/comparability/authentication status. Do not use or modify `astra_seed_campaign.py`: its eligibility check still hardcodes1e-4.

## Read-only executable OFF/cue comparison

After retrieval, main sets `LOW3` and `LOW1` to their **actual local capture roots**. This command prints diagnostics only; it does not write captures, score models, or approve comparability. Failure means inspect preserved evidence, not regenerate it.

```bash
: "${LOW3:?Set retrieved local 3e-5 root}"
: "${LOW1:?Set retrieved local 1e-5 root}"
BASE=/tmp/astra_seed_bank0_evidence_20260912/runs/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912
python3 -B - "$BASE" "$LOW3" "$LOW1" <<'PY'
import collections, itertools, json, math, pathlib, sys
relative = 'eval/bank0__F_r16k16__across__sleep4__r8__lam1.json'
documents = [json.loads((pathlib.Path(root)/relative).read_text()) for root in sys.argv[1:]]
indexed = []
for document in documents:
    rows = document['cues']
    assert document['n_cues'] == len(rows) == 1313
    mapping = {row['cue_id']: row for row in rows}
    assert len(mapping) == 1313, 'duplicate cue_id'
    counts = collections.Counter(row['kind'] for row in rows)
    assert [counts[kind] for kind in ('frame','frame_similar','frame_bicycle')] == [64,48,48]
    assert collections.Counter(row['dose'] for row in rows if row['kind']=='frame') == {0:16,1:16,4:16,16:16}
    for row in rows:
        for side in ('OFF','ON'):
            scores = row[side]
            assert set(scores['p_raw']) == set(scores['logp']) == set(row['cand_tokens'])
            values = [*scores['p_raw'].values(), *scores['logp'].values(), scores['mass']]
            if 'abstain' in row:
                values.append(scores['p_abstain'])
                assert scores['p_abstain'] >= 0
            assert all(type(value) in (float,int) and math.isfinite(value) for value in values)
            assert min(scores['p_raw'].values()) >= 0 and sum(scores['p_raw'].values()) > 0 and scores['mass'] > 0
    indexed.append(mapping)
for left, right in itertools.combinations(range(3), 2):
    first, second = indexed[left], indexed[right]
    assert first.keys() == second.keys(), 'cue-ID set differs'
    metadata_changes, off_changes = [], []
    maximum = {field:0.0 for field in ('p_raw','mass','logp','p_abstain')}
    for identity in first:
        earlier, later = first[identity], second[identity]
        strip = lambda row: {key:value for key,value in row.items() if key not in ('OFF','ON')}
        if strip(earlier) != strip(later): metadata_changes.append(identity)
        assert list(earlier['cand_tokens']) == list(later['cand_tokens']), 'candidate order differs'
        for side in ('OFF','ON'):
            assert list(earlier[side]['p_raw']) == list(later[side]['p_raw']), 'candidate order differs'
        before, after = earlier['OFF'], later['OFF']
        if before != after: off_changes.append(identity)
        assert before.keys() == after.keys(), 'OFF field set differs'
        for field in maximum:
            if field not in before: continue
            old, new = before[field], after[field]
            changes = [abs(old[key]-new[key]) for key in old] if isinstance(old,dict) else [abs(old-new)]
            maximum[field] = max(maximum[field], *changes)
    print(json.dumps(dict(pair=[sys.argv[left+1],sys.argv[right+1]],
        cue_order_equal=list(first)==list(second), metadata_changed_count=len(metadata_changes),
        metadata_changed_ids=metadata_changes, off_changed_count=len(off_changes),
        off_changed_ids=off_changes, off_max_abs=maximum), allow_nan=False))
PY
```

## Acquisition/spill rows: exact schema and CPU extraction

Native report entry: `.results["F_r16k16__across__r8__lam1"]`. Verify `.banks==[0]`, `.sleeps==[4]`, report `.n_evals==1` and the selected eval tag; don't mix rates in one native report. Native `.per_bank["0"]` contains **gates/interpretation**, not a full per-dose summary. The baseline capsule has raw eval and frozen analysis, not necessarily a native report; use the same pure native functions for all three rows rather than creating a baseline GPU/report run.

| Table field | Native source |
|---|---|
| `lr, seed, steps, tokens, supervised_tokens, fit_s` | actual `train_meta.json` (`wall_seconds` for fit_s) |
| `eval_s, cues` | eval `seconds, n_cues` |
| `P16_OFF, P16_ON, deltaP16` | report `.headline.frame_p_off, frame_p_on, frame_d_p` |
| `frame_mass16_OFF, frame_mass16_ON` | pure summary `per_dose[16].frame_mass_off/on`; **not** report `.headline.mass_*` (those are question-cue masses) |
| `I_d_frame, CI_lo, CI_hi, n16, G9` | report `.frame.G9_frame_binding.{value,lo,hi,n,passed}`; same as bank0's gate |
| `spill_similar, spill_unexposed, spill_bicycle, spill` | report `.frame.spill_parts.*`, `.headline.frame_spill` |
| `deltaP_d0,d1,d4,d16` | report `.frame.dose_curve` (not outer `.dose_curve`, which is question-cue) |
| `abstain_ON_unexposed,similar,bicycle,exposed16; G11` | report `.frame.abstain`, `.frame.G11_abstention` |
| `source_match,cue_match,OFF_drift,model_authentication` | separate evidence/check results, never inferred from G9 |

Following source/completeness checks, this CPU-only command emits one JSON table row per rate to stdout. It imports **only the frozen native definitions** and uses their existing summary and seed0 gate functions. It does not call `train`, `evaluate`, `report_command`, or the campaign analyzer. Keep stdout in a new analysis artifact if main wants a durable result; never redirect over any captured file.

```bash
python3 -B - "$BASE" "$LOW3" "$LOW1" <<'PY'
import hashlib, importlib.util, json, pathlib, sys
source = pathlib.Path('/tmp/astra_seed_bank0_evidence_20260912/experiment_code/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d/organism_v6/memory_dose.py')
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3'
spec = importlib.util.spec_from_file_location('frozen_memory_dose', source)
native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
key = 'F_r16k16__across__r8__lam1'
for root, rate in zip(map(pathlib.Path,sys.argv[1:]), (1e-4,3e-5,1e-5)):
    load = lambda relative: json.loads((root/relative).read_text())
    fit = load('adapters/bank0/F_r16k16/across/sleep4/r8/train_meta.json')
    assert fit['lr'] == rate and fit['seed'] == 2 and fit['steps'] == 9693
    evaluation = load('eval/bank0__F_r16k16__across__sleep4__r8__lam1.json')
    summary = native.summarize_eval(evaluation, load('banks/bank0.json'))
    gates = native.evaluate_gates(summary, seed=0)
    if (root/'report/report.json').exists():
        report = load('report/report.json')
        assert report['n_evals'] == 1 and report['results'][key]['banks'] == [0]
        assert report['results'][key]['sleeps'] == [4]
        assert report['results'][key]['frame']['G9_frame_binding'] == gates['G9_frame_binding']
        assert report['results'][key]['per_bank']['0']['gates']['G9_frame_binding'] == gates['G9_frame_binding']
    dose = summary['per_dose'][16]
    print(json.dumps(dict(root=str(root), lr=rate,
        fit={field:fit[field] for field in ('seed','rank','epochs','steps','tokens','supervised_tokens','wall_seconds')},
        eval_s=evaluation['seconds'], cues=evaluation['n_cues'],
        acquisition={field:dose[field] for field in ('n','frame_p_off','frame_p_on','frame_d_p','frame_mass_off','frame_mass_on','I_d_frame')},
        G9=gates['G9_frame_binding'],
        controls={field:value for field,value in summary['controls'].items() if field.startswith(('frame_spill','abstain_'))},
        frame_dose_curve={dose:summary['per_dose'][dose]['frame_d_p'] for dose in (0,1,4,16)},
        G11=gates['G11_abstention']), allow_nan=False))
PY
```

**Readout boundary:** lower spill with lost acquisition is weaker writing, not selective success; retained acquisition with lower spill but failed G9 is a descriptive tradeoff. Even G9 pass is only this oracle-material bank/initialization, with cross-node authentication caveats. No cross-rate pooling, new CI/threshold, baseline-OFF replacement, clean-lineage claim, or claim that the current selective writer works. The native owner bootstrap is within one fit, not uncertainty over optimizer seeds/nodes. Main can juxtapose rows without promoting a confirmatory LR-only causal claim.

Prepared from local baseline/native source and local node3 launch/preparation records only. Embedded commands are suggestions for later retrieved data; syntax validation only, no scientific summaries or new-run analysis executed during this handoff.
