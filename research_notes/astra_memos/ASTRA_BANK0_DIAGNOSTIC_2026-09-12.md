# Bank0 diagnostic evidence and independent review — 2026-09-12

## Status and scope

**Additive evidence only. Four completed, source-compatible bank0 fits; four failures of the frozen `G9_frame_binding` gate. No pooling, campaign success rate, clean-lineage promotion, or H1/H2 claim.** A gate failure is not proof that all binding is absent; positive owner-versus-look-alike contrasts alone are not a selective-binding pass.

This bounded preservation/review sidecar changes no scientific definition, threshold, architecture, source, test, notebook, remote job, or GPU state. No experiment was rerun. Only captured-data CPU arithmetic was reproduced. No SEQ number is assigned. The main integration owner retains notebook and commit ownership. Existing outputs are never overwritten; the two repository additions and the new temporary reviewer output are listed below.

Read root `AGENTS.md`, `CLAUDE.md`, and the notebook's 2026-09-12T07:27Z authorization for `claude -p`. No additional AGENTS/CLAUDE files were found in the relevant evidence or destination subtrees. `git pull --ff-only` initially encountered read-only `.git/FETCH_HEAD`; the explicit approval/escalation succeeded, reporting already up to date, before any evidence write. No approval denial was bypassed. Initial integration HEAD was `533c9920f3052c64be972b5307575201178221a5`; another worker advanced HEAD to `6ff8aaa028cd7f1b36218ceb817f641a4ac27e46` during this review. Neither is substituted for the frozen experiment source below. Other workers' changes were left alone.

## Custody and artifact map

Define `E=/tmp/astra_seed_bank0_evidence_20260912`. The permanent archive contains this top-level directory, including its analysis outputs; no extraction or overwrite was needed here.

| Artifact | SHA256 / role |
| --- | --- |
| Original `/tmp/astra_seed_bank0_evidence_20260912.tgz` | `21c28aeb20c0d256b22602445439ad75b76dea9828577cf3813d37a72d251d4e` |
| NEW `research_notes/astra_memos/receipts_20260912/astra_seed_bank0_evidence_20260912.tgz` | Same exact SHA256; 13,835,670 bytes; verified before and after no-clobber copy |
| `E/analysis.json` | `e7bd30eef0e37d9d164e43d2badfb8e9ceebc25a55d89384659ba42a4ac5ed65` |
| `E/ANALYSIS_RECEIPT.json` | Exact original argv, shell command, Python version, analysis-code hashes, output hash, exit status and eligibility |
| `E/CAPTURE_MANIFEST.json` | Original source paths, byte counts, SHA256 and source mtimes for 98 files |
| `E/SHA256SUMS` | All 112 listed files verified; excludes itself |
| `E/node2_bank0_source_capture.tar.gz` | `e5725880b35b80f0f54d93faa921d1e811506d399caac8d2b3b328beb2480db1`; original source-only transport, not the complete later analysis bundle |
| `E/analysis_code/research_notes/analysis/astra_seed_campaign.py` | `e1327b3d2fdc060e33aad3d088beada167226437a9b1e6f28b819c6b5959eea9` |
| `E/analysis_code/organism_v6/memory_dose.py` | `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`; byte-identical hash to captured experiment definition |
| NEW `/tmp/astra_bank0_fable_review_20260912.md` | `8e6d6403c5fd37fec04454d669e82d781ba235767f80b6f7eda8d2f12c8501dc`; immutable raw reviewer response plus invocation metadata; remains temporary, not inside the already frozen archive |

Original source capture: **2026-09-12 07:17:04.353825–07:17:07.632182 UTC**, node2, as recorded in the manifest. Analysis receipt creation: **07:17:47.291240 UTC**, exit 0, empty stderr. Separate progress observation: **07:18:19.386875 UTC**. These timestamps are historical observations, not a current remote-status check.

Local verification established: 98 capture-manifest files totaling **121,276,287 bytes** match their hashes/lengths; all 113 regular files inside the complete archive match the existing extracted files byte-for-byte; all six analysis-code receipt hashes match. This verifies custody/internal consistency, not independent authentication of model origin or unrecorded execution. Weights/models and reuse indexes were not captured.

### Exact run paths

Each run root is `E/runs/<run_name>`. For its cell `C`, the analyzed triple is exactly:

```text
eval/bank0__C__across__sleep4__r8__lam1.json
adapters/bank0/C/across/sleep4/r8/train_meta.json
seed_run_receipt.json
```

The corresponding `adapters/bank0/C/across/sleep4/r8/DONE`, `banks/bank0.json`, corpus/generations, manifest/distractor, train/eval logs, throughput-profile metadata and original queue records are preserved in the bundle. The receipt retains original remote paths intentionally; the manifest maps them to captured files.

| Short label | Exact run_name | Cell | Optimizer seed | Source-bank seed |
| --- | --- | --- | ---: | ---: |
| F2 | `astra_A1_memory_dose_S1_F_r16k16_ts2_20260912` | `F_r16k16` | 2 | 1 |
| F3 | `astra_A1_memory_dose_S1_F_r16k16_ts3_20260912` | `F_r16k16` | 3 | 1 |
| CF0 | `astra_A2_memory_dose_D32_CF_r16_b_ts0_20260912_attempt2` | `CF_r16_b` | 0 | 0 |
| CF1 | `astra_A2_memory_dose_D32_CF_r16_b_ts1_20260912_attempt2` | `CF_r16_b` | 1 | 0 |

F2/F3 share bank0 SHA256 `87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31` and corpus SHA256 `f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d`. CF0/CF1 share bank0 SHA256 `b8069c4e62f4e655453ca47c556ebd145be77071dab8db807e6ffbff51a06ed6` and corpus SHA256 `70b50213c85fdacc7895163e0766e2a90717ba9ee3b90d250e7a276f4d4c3cd4`.

Both instances are called bank0 but are **different hashed source banks**. Optimizer seeds are repeated fits within each source cell, not independent bank replicates; the F-versus-CF difference is not an isolated treatment comparison. F optimizer seeds 0/1 are explicitly unavailable reference fits in this bundle, not observed failures. The CF attempt2 seed2 progress record is pending without fit/eval evidence, not a fifth negative.

## Numerical results under unchanged definitions

Every row has 1,313 eval cues, a completed non-profile scientific fit, a receipt, compatible source hashes with no reported mismatches, and available binding controls. The dose16 endpoint uses **16 paired owners per fit**, not 1,313 independent observations. Values below are rounded to six decimal places; `analysis.json` retains full precision.

`I_d_frame` is the owner's ON-minus-OFF target-versus-alternative log-odds gain minus the corresponding gain for that owner's unseen look-alike frame. The alternative is selected under OFF and held fixed for that pair. The historical implementation clips raw probabilities at `1e-12` before logs. Its paired-owner percentile bootstrap uses 2,000 draws, seed 0, sorted indices 50 and 1950. These are within-bank/fit descriptive intervals, not optimizer-seed, family-level or population confidence intervals.

G9 passes only if **CI lower bound > 0 AND frame spill <= 0.03**. Here, “G9” means `G9_frame_binding`, not the distinct `G9_mass` endpoint.

| Fit | I_d_frame mean | Historical 95% interval | Frame spill | Positive-lower-bound criterion | G9_frame_binding |
| --- | ---: | --- | ---: | --- | --- |
| F2 | 1.921470 | [1.202608, 2.682503] | 0.415537 | Pass | **FAIL: spill** |
| F3 | 0.003650 | [-0.184280, 0.190964] | 0.308698 | Fail | **FAIL: interval and spill** |
| CF0 | 2.446476 | [1.448077, 3.472732] | 0.292354 | Pass | **FAIL: spill** |
| CF1 | 1.743430 | [1.253261, 2.287387] | 0.287368 | Pass | **FAIL: spill** |

Spill is the **equal-weight mean of three stratum means** of absolute target-colour normalized probability change: 16 unexposed owner frames (dose0), 48 exposed unseen-look-alike frames (doses1/4/16), and 48 exposed bicycle frames (doses1/4/16). It is neither a 112-cue weighted mean nor a dose16-only control statistic. Normalization here is `p_raw[target]/sum(p_raw.values())`, exactly as in historical `cue_metrics`.

| Fit | Unexposed mean abs delta | Similar-exposed mean abs delta | Bicycle-exposed mean abs delta | Equal-stratum spill |
| --- | ---: | ---: | ---: | ---: |
| F2 | 0.321309 | 0.416577 | 0.508725 | 0.415537 |
| F3 | 0.294983 | 0.294027 | 0.337085 | 0.308698 |
| CF0 | 0.181459 | 0.305031 | 0.390571 | 0.292354 |
| CF1 | 0.185291 | 0.313009 | 0.363803 | 0.287368 |

The next table instead follows the recorded dose16 presentation: mean per-cue **conditional** `p_raw[target]/recorded_mass`, plus mean recorded candidate mass. The two normalizers can differ slightly because of serialization rounding. These are not raw target probabilities or accuracy rates. All 16 OFF and ON values in each row are valid; no missing value is zero-imputed.

| Fit | Dose16 cue kind | Conditional P OFF | Conditional P ON | Candidate mass OFF | Candidate mass ON |
| --- | --- | ---: | ---: | ---: | ---: |
| F2 | Owner frame | 0.259650 | 0.685323 | 0.008738 | 0.998158 |
| F2 | Unseen look-alike | 0.249868 | 0.401309 | 0.009308 | 0.997686 |
| F2 | Bicycle | 0.258205 | 0.668630 | 0.004478 | 0.997259 |
| F3 | Owner frame | 0.259650 | 0.257545 | 0.008738 | 0.973117 |
| F3 | Unseen look-alike | 0.249868 | 0.252802 | 0.009308 | 0.975301 |
| F3 | Bicycle | 0.258205 | 0.258202 | 0.004478 | 0.980435 |
| CF0 | Owner frame | 0.230088 | 0.789892 | 0.008601 | 0.782299 |
| CF0 | Unseen look-alike | 0.238222 | 0.472662 | 0.009759 | 0.735654 |
| CF0 | Bicycle | 0.238555 | 0.719736 | 0.004774 | 0.813130 |
| CF1 | Owner frame | 0.230088 | 0.735849 | 0.008601 | 0.850205 |
| CF1 | Unseen look-alike | 0.238222 | 0.503494 | 0.009759 | 0.837128 |
| CF1 | Bicycle | 0.238555 | 0.626800 | 0.004774 | 0.860747 |

High ON candidate mass and target conditional P coexist with substantial changes on control frames. They do not rescue selectivity. Conversely, small aggregate target change in F3 does not imply unchanged individual cue distributions: its dose16 owner-frame mean absolute conditional change is 0.287169.

## Source-command and fit provenance

The original source snapshot is `E/experiment_code/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d/`. Captured job files, which are evidence and must not be executed during this review:

```text
E/queue/running/0045_astra_A1_memory_dose_S1_F_r16k16_ts2_20260912.job
E/queue/running/0046_astra_A1_memory_dose_S1_F_r16k16_ts3_20260912.job
E/queue/running/0050_astra_A2_memory_dose_D32_CF_r16_b_ts0_20260912_attempt2.job
E/queue/running/0051_astra_A2_memory_dose_D32_CF_r16_b_ts1_20260912_attempt2.job
```

Their full `CMD` values bind `REPO=/localhome/local-rohing/astra_sources/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`, the respective original `RUN`, `PYTHONDONTWRITEBYTECODE=1`, `MODEL=hf`, `F_RANK=8`, `F_BANKS='0 1 2'`, and `F_TOKEN_BUDGET=250000`. F jobs use `SEED=2/3`, `F_CELLS=F_r16k16`, `CF_CELLS=F_r16k16`, `MAX_FIT_MIN=25`, and `gpu/memory_dose_frames.sh {gpu} fits`. CF jobs use `SEED=0/1`, `CF_CELLS=CF_r16_b`, `MAX_FIT_MIN=35`, and `gpu/memory_dose_childframes.sh {gpu} fits`. These are recorded commands, not newly launched commands.

Inspected both captured launch scripts: their full fit call passes `--seed "$SEED" --rank "$r" --epochs 3 --lr 1e-4`; their separate 100-step `--measure-only` throughput probe does not pass that seed. A default seed0 profile is therefore not a seed0 scientific fit. The analyzer checks the scientific `train_meta.json`, `measure_only=false`, seed, sibling DONE, source receipt and source hashes; it excludes throughput paths. Receipt `status=prepared` alone is not completion.

| Fit | Steps / total steps | Final recorded training loss | Scientific seed |
| --- | --- | ---: | ---: |
| F2 | 9693 / 9693 | 1.093895 | 2 |
| F3 | 9693 / 9693 | 1.162619 | 3 |
| CF0 | 10614 / 10614 | 1.311253 | 0 |
| CF1 | 10614 / 10614 | 1.341968 | 1 |

All name `Qwen/Qwen2.5-7B-Instruct`; receipts name `HFScorer`. `synthetic=true` means researcher-planted diagnostic memories here, not a mock evaluator. The preserved label is **`SYNTHETIC_DIAGNOSTIC_NOT_CLEAN_LINEAGE`**, with `clean_lineage_eligible=false`. At the captured progress time all four had only bank0 DONE/eval and no complete-stage markers. A requested three-bank job is not evidence of three completed banks.

### CF attempt1 provenance gap resolved locally

Fable correctly noticed that attempt1 reasons were absent from its supplied bank0 packet. The already-existing, unchanged repository archive `research_notes/astra_memos/receipts_20260912/astra_attempt2_and_profile_failures_20260912.tgz` supplies them; SHA256 verified as `8e97bc2c082205e5deab0d435b68c4afdf7fb79ce53eeeb15cb5558822022e75`. This is a separate provenance supplement, not a modification of the bank0 archive.

Read its `astra_A2_memory_dose_D32_CF_r16_b_ts{0,1,2}_20260912/logs/runbook_childframes.log` members directly, without extraction: at 06:32:16, 06:32:17 and 06:33:16 UTC they report projected fits of **25.2, 27.8, 26.8 minutes**, respectively, and aborts at `MAX_FIT_MIN=25` after 100-step profiling. They are resource-guard aborts, not scientific endpoint failures. The 06:35:17.926284 UTC notebook entry records the resource-only cap increase to 35 for fresh attempt2 runs. Both analyzed CF attempt2 seed receipts are byte-identical between the existing supplement and the bank0 bundle. No attempt1 outcome was silently discarded from this note, no FORCE is inferred, and no new run was requested.

## Independent Fable review and author-side disposition

Used the exact available Claude CLI on the VM, started **2026-09-12T07:33:20.152267 UTC**, with the notebook-named model, not a substitute service:

```bash
claude -p --model claude-fable-5-1 --output-format text --restricted --tools "" --strict-mcp-config --no-session-persistence
```

The self-contained stdin packet contained actual complete `analysis.json`, receipt, wrapper and analyzer source; frozen metric/G9/bootstrap definitions; all four archived job commands; and all 160 raw frame/control projections per fit, preserving candidate order, target, optional alternative, OFF/ON raw vectors and masses. Prompt bytes: 135,302; SHA256 `ed73ec971d2cdeb3983f8cece0913542fdc0a51ce29cd9bf33705cfde82cb815`. The new review file was created with exclusive `open('x')`, never overwritten. CLI returned 0 with 7,288 stdout bytes and empty stderr. The reviewer had no tools or MCP access, was explicitly forbidden WebFetch/network/SSH/source writes/launches, and used only the authorized model inference call. No permission-bypass flags were used.

This is an independent model critique of supplied evidence, **not a second independently executed numerical pipeline**. Fable spot-checked masses and log-odds examples, acknowledged not recomputing all gains, spill means, hashes or bootstrap draws, and agreed the four recorded flags stand. Author-side follow-ups below were performed afterward; Fable has not re-reviewed these dispositions. Its raw response is preserved unchanged, including overstatements.

| Finding | Disposition / smallest corrective action |
| --- | --- |
| High: spill can reflect marginal colour-prior shifts rather than owner-colour leakage | Accepted interpretive caution. Added signed, colour-stratified control changes below. Rejected the categorical claim that *any* prior shift makes passing impossible: sufficiently small shifts can remain <=0.03. Absolute changes can be increases or decreases; call the computed quantity “spill metric,” not demonstrated causal leakage. No metric or threshold changed. |
| High: F3 is a “collapsed adapter” with a fixed distribution | Qualified to a white-dominant, limited-discrimination **pattern within these 160 frame/control cues**. ON distributions vary measurably; exact ranges below contradict a literal fixed-output claim. Completed training and final loss are preserved. No loss trajectory or validation-loss series is present in the inspected metadata/log; failure mechanism remains unresolved. F3 is retained as a completed evaluated fit, not excluded as invalid. |
| Medium: bicycle responses establish name-level association | Similar owner/bicycle responses are consistent with object-insensitive association, but do not identify its mechanism or establish name-level storage. Report separate controls; do not replace G9 with a mechanism claim. |
| Medium: high conditional P is not selectivity | Accepted; report OFF/ON mass and all three dose16 cue kinds, not just owner improvement. |
| Medium: unexplained CF attempt2 suffix | Resolved from the pre-existing hash-verified resource-failure archive above; attempt2 receipt bytes match. This supplement was not supplied to Fable in its original packet. |
| Low: only bank0 despite three-bank job command | Accepted snapshot limit. Do not infer bank1/2 completion, whole-stage success, or current queue status. |
| Low: bootstrap indices 50/1950; purported “slightly liberal” interval | Historical indices and seed reproduced exactly. Coverage/liberality is not established by this packet, so that statistical characterization is not adopted. No new interval method or significance claim. |

### Report-only signed controls requested by reviewer

Each entry is mean **signed** ON-minus-OFF target probability normalized by the sum of the four raw candidate probabilities, within the named control stratum and owner-target colour. Unexposed has 4 owners per colour; each exposed stratum has 12. These are exploratory decompositions of existing data, not new acceptance criteria, independent replicates, or replacements for absolute G9 spill. Do not average these signed values to reconstruct the absolute endpoint.

| Fit | Control stratum | Red target | Blue target | Green target | White target |
| --- | --- | ---: | ---: | ---: | ---: |
| F2 | Unexposed | -0.450170 | +0.152572 | +0.097070 | +0.489764 |
| F2 | Similar exposed | -0.498917 | +0.167476 | +0.318258 | +0.649659 |
| F2 | Bicycle exposed | -0.340287 | +0.252916 | +0.574619 | +0.862017 |
| F3 | Unexposed | -0.530495 | -0.031579 | +0.172312 | +0.445544 |
| F3 | Similar exposed | -0.556758 | -0.029413 | +0.151863 | +0.424753 |
| F3 | Bicycle exposed | -0.636734 | -0.054056 | +0.108153 | +0.549398 |
| CF0 | Unexposed | -0.307596 | +0.067860 | +0.160083 | -0.134806 |
| CF0 | Similar exposed | -0.160022 | +0.512344 | +0.268381 | +0.039193 |
| CF0 | Bicycle exposed | -0.103541 | +0.652802 | +0.474642 | +0.210452 |
| CF1 | Unexposed | -0.401935 | +0.078747 | +0.198148 | +0.037989 |
| CF1 | Similar exposed | -0.217441 | +0.456656 | +0.316795 | +0.144561 |
| CF1 | Bicycle exposed | -0.244072 | +0.558453 | +0.325497 | +0.288779 |

For a given normalized four-colour cue, the mean shift in the other three colours is algebraically `-target_shift/3`; target shift relative to that mean is `4*target_shift/3`. Thus the reviewer's suggested target-versus-other-three summary is recoverable from this table but adds no independent evidence. Direction-specific changes and heterogeneous controls do not justify reducing all spill to one prior-shift mechanism. OFF red probability across these cues ranges 0.454827–0.752563 for F and 0.485599–0.748694 for CF; the reviewer's “50–65 percent for every frame” is too narrow.

F3 ON candidate-normalized probabilities across all 160 frame/control cues:

| Colour | Mean | Minimum | Maximum |
| --- | ---: | ---: | ---: |
| Red | 0.045837 | 0.028245 | 0.056097 |
| Blue | 0.094627 | 0.051324 | 0.124653 |
| Green | 0.236285 | 0.175366 | 0.304399 |
| White | 0.623252 | 0.538633 | 0.728070 |

White is the largest candidate for every one of these cues, but neither invariance nor collapse across all 1,313 eval cues or all model behavior has been established. The captured F3 train log ends `TRAIN_DONE items=12924 steps=9693 tokens=749985 loss=1.1626 wall_s=1361.7`; this is completion/final-loss evidence, not a validation curve or an explanation of the output pattern.

## Verification commands and reproducibility

Preservation performed only after verifying the expected source digest and destination absence: `mkdir -p research_notes/astra_memos/receipts_20260912`, then `cp -n /tmp/astra_seed_bank0_evidence_20260912.tgz research_notes/astra_memos/receipts_20260912/astra_seed_bank0_evidence_20260912.tgz`, then verified the copied digest. The destination is now occupied: **do not replace or recopy over it**.

Original analysis command, recorded in the receipt (historical, not an instruction to overwrite): `bash /tmp/astra_seed_bank0_evidence_20260912/run_analysis.sh > /tmp/astra_seed_bank0_evidence_20260912/analysis.json 2> /tmp/astra_seed_bank0_evidence_20260912/analysis.stderr`. The wrapper resolves its own directory, expands the four explicit triples above, then invokes `python3 -B .../analysis_code/research_notes/analysis/astra_seed_campaign.py ... --bootstrap-seed 0`. The full original absolute argv is in the receipt. Do not execute archived GPU job commands.

Safe read-only checks (CPU only; stdout, no captured outputs overwritten):

```bash
E=/tmp/astra_seed_bank0_evidence_20260912
sha256sum /tmp/astra_seed_bank0_evidence_20260912.tgz research_notes/astra_memos/receipts_20260912/astra_seed_bank0_evidence_20260912.tgz
(cd "$E" && sha256sum -c SHA256SUMS)
set -o pipefail
bash "$E/run_analysis.sh" | sha256sum
sha256sum "$E/analysis.json" /tmp/astra_bank0_fable_review_20260912.md
```

In this sidecar the frozen analysis was actually run via `subprocess.run(['bash', str(root/'run_analysis.sh')], capture_output=True, check=True)`; asserted stdout equals the original `analysis.json` **byte-for-byte**, stderr empty, without writing either. A separate standard-library implementation, not importing the scientific helpers, reconstructed every owner's raw-vector log-odds/normalized deltas, the historical seeded bootstrap, equal-stratum spill, and all dose16 conditional/mass table values; all matched exactly, including four false flags. Hash and archive-content checks were also actually executed. No GPU/model load occurred.

To reproduce the reviewer-requested supplemental diagnostics from the captured raw cues without editing source or outputs:

```python
import json
import statistics
from pathlib import Path

root = Path('/tmp/astra_seed_bank0_evidence_20260912')
analysis = json.loads((root / 'analysis.json').read_text())
colours = ['red', 'blue', 'green', 'white']

def normalized(cue, side, colour):
    raw = cue[side]['p_raw']
    return raw[colour] / sum(raw.values())

for row in analysis['rows']:
    evaluation = json.loads(Path(row['eval_path']).read_text())
    cues = [cue for cue in evaluation['cues']
            if cue['kind'] in ('frame', 'frame_similar', 'frame_bicycle')]
    print(row['cell'], row['optimizer_seed'])
    for kind in ('frame', 'frame_similar', 'frame_bicycle'):
        selected = [cue for cue in cues if cue['kind'] == kind
                    and (cue['dose'] == 0 if kind == 'frame' else cue['dose'] > 0)]
        for colour in colours:
            group = [cue for cue in selected if cue['a'] == colour]
            signed = statistics.mean(normalized(cue, 'ON', colour)
                                     - normalized(cue, 'OFF', colour) for cue in group)
            print(kind, colour, len(group), f'{signed:+.6f}')
    if row['cell'] == 'F_r16k16' and row['optimizer_seed'] == 3:
        for colour in colours:
            values = [normalized(cue, 'ON', colour) for cue in cues]
            print(colour, statistics.mean(values), min(values), max(values))
```

## Final limits and changed files

Available controls support the stated existing diagnostic failures; they do not establish an exposed-partner swapped-ID test, causal name-level storage, or a reason for F3's white dominance. The look-alike is an unseen similar identity. No threshold was fit to these outcomes. No generic G9_mass/G10/G11, three-bank completion, retention, parenting, autonomous consolidation, clean-lineage, H1 or H2 conclusion follows. Reviewer disagreements were disposed by narrower wording and descriptive checks, not by overriding a gate or authorizing promotion. Any future definition/claim change belongs to the project's material-deliberation process, outside this sidecar.

Created only:

- `research_notes/astra_memos/ASTRA_BANK0_DIAGNOSTIC_2026-09-12.md` — this additive memo.
- `research_notes/astra_memos/receipts_20260912/astra_seed_bank0_evidence_20260912.tgz` — exact no-overwrite preservation copy.
- `/tmp/astra_bank0_fable_review_20260912.md` — new raw independent response and invocation metadata.

No commit, notebook edit, remote access/job change, or GPU rerun. Existing evidence and the raw Fable response remain unchanged. The main integration owner may log/integrate these paths; this memo assigns no SEQ number.
