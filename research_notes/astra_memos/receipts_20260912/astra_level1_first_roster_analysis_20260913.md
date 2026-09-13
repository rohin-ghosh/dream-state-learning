# First Level1 roster: verified archive and compact scientific analysis

September 13, 2026. **All 12 first-roster roots complete, already collected
once, archived and transferred; no missing cells or integrity failures found.**
No native recollection occurred. No second-roster, A100 retry, perception/
reflection, repetition or meta-reflection output was inspected or included.

## Immediate scientific decision

All three learner seeds in each of four skills reach **48/48 held typed-content
and 48/48 strict**, with **12/12 canaries**. The improvements include genuine
typed/source-field corrections, not merely stripping fences. These are useful
authored-skill candidates for a **fresh, prospectively fixed transfer test**,
not a reason to run more unchanged dose on these now-ceiling fixtures.

The strongest directly visible distinctions are goal-state decisions and
contradiction/source judgments; prediction also corrects over-abstention, while
update judgement learns the declared candidate-support test. Neither three
matching seeds nor perfect fixture scores demonstrate general reasoning,
autonomous goals, actual child learning, clean ancestry or mechanism freeze.
The receipt flags remain `automatic_pass=false`, `scientific_pass=null`.

## All 12 counts and cost

Arrows are **OFF→post**. Held denominators are 48; canaries are 12.
Strict is content-correct **and** canonical output, not format alone.
Canary content and strict counts coincide in every cell. W/L means item-paired
content wins/losses, not independent-trial significance.

**Uniform cost per cell:** 120 generation calls, one fit, 320 updates,
1,280 row presentations over 96 rows (14 epochs entered, final one partial).
Tokens below are actual training tokens; elapsed seconds are controller totals.

| Cell | Node | Held content | Held strict | Canary C/S | Held W/L | Canary W/L | Train tokens | Elapsed s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| contradiction_seed0 | node2 | 17→48 | 0→48 | 12→12 | 31/0 | 0/0 | 384529 | 597.274 |
| contradiction_seed1 | node2 | 17→48 | 0→48 | 12→12 | 31/0 | 0/0 | 384548 | 582.837 |
| contradiction_seed2 | node2 | 17→48 | 0→48 | 12→12 | 31/0 | 0/0 | 384517 | 584.323 |
| goal_completion_seed0 | node1 | 32→48 | 32→48 | 11→12 | 16/0 | 1/0 | 377717 | 647.308 |
| goal_completion_seed1 | node1 | 32→48 | 32→48 | 11→12 | 16/0 | 1/0 | 378058 | 620.943 |
| goal_completion_seed2 | node1 | 32→48 | 32→48 | 11→12 | 16/0 | 1/0 | 377763 | 614.543 |
| prediction_seed0 | node1 | 22→48 | 22→48 | 11→12 | 26/0 | 1/0 | 355360 | 686.769 |
| prediction_seed1 | node1 | 22→48 | 22→48 | 11→12 | 26/0 | 1/0 | 355359 | 653.053 |
| prediction_seed2 | node1 | 22→48 | 22→48 | 11→12 | 26/0 | 1/0 | 355317 | 638.767 |
| update_judgement_seed0 | node2 | 8→48 | 0→48 | 12→12 | 40/0 | 0/0 | 490962 | 728.780 |
| update_judgement_seed1 | node2 | 8→48 | 0→48 | 12→12 | 40/0 | 0/0 | 490934 | 724.586 |
| update_judgement_seed2 | node2 | 8→48 | 0→48 | 12→12 | 40/0 | 0/0 | 490996 | 732.728 |

All post-fit responses classify as `exact`. Strict paired held wins are
48/0 for contradiction and update judgement, 16/0 for goal completion, and
26/0 for prediction; content wins are the separately reported smaller counts
where OFF had content-correct fenced responses.

### Three-learner means/ranges

All three complete learners use **the same material seed 0**, as preregistered.
Each numerical count in the following table is its three-seed mean; **every
count range is [x,x]**. Identical count ranges are not population certainty.
The structured JSON retains explicit mean/minimum/maximum for each count,
paired statistic, token cost and timing.

| Skill | Mean held content OFF→post | Mean held strict OFF→post | Mean content gain | Mean canary OFF→post | Controller seconds mean [min,max] |
| --- | ---: | ---: | ---: | ---: | --- |
| Contradiction | 17→48 | 0→48 | +31 | 12→12 | 588.145 [582.837,597.274] |
| Goal completion | 32→48 | 32→48 | +16 | 11→12 | 627.598 [614.543,647.308] |
| Prediction | 22→48 | 22→48 | +26 | 11→12 | 659.530 [638.767,686.769] |
| Update judgement | 8→48 | 0→48 | +40 | 12→12 | 728.698 [724.586,732.728] |

Total recorded work: **1,440 calls, 12 fits, 3,840 updates, 15,360 presentations**;
4,826,060 training tokens, 251,819 supervised tokens, 5,053,224 padded tokens.
Summed fit-training time is 4,646.8 s; summed controller time is 7,811.911 s.
Concurrent sums are accounting totals, **not** elapsed fleet time or measured
GPU utilization. The raw per-state/panel generation costs remain in JSON.

## Error families: what improved

These diagnostic counts are per seed, identical across seeds. Raw errors and
the frozen scorers are unchanged; no malformed answer receives repaired credit.

- **Prediction:** OFF's 26 failures comprise four invalid JSON responses and
  22 `wrong_types` responses. The latter are semantically consequential typed
  decisions: 21 valid JSON outputs abstain with `prediction:null` despite a
  uniquely supported Boolean card, and one predicts `true` despite conflicting
  evidence requiring abstention. Those 22 outputs were already canonical;
  they are not whitespace/fence fixes. Source families: uniquely supported
  cards 7/32→32/32; conflicting evidence 7/8→8/8; missing evidence 8/8→8/8.
  The four unparseable responses include Python-style capitalized Booleans;
  they remain unscorable in OFF. OFF canonical-format count was 44/48, not 22.
- **Goal completion:** all OFF outputs were already canonical JSON. All 16
  failures were `wrong_values`: `continue/false` when the supplied verified
  state justified `complete/true`. Thus all +16 are content-value corrections.
  By case family, all-requirements 10/16→16/16, claim-requires-verification
  11/16→16/16, single-requirement 11/16→16/16. This is applying supplied goals,
  not generating goals or proving real-world mission completion.
- **Contradiction:** OFF's 48 answers were valid enclosing JSON fences, which
  the **predeclared content scorer already permits**. Seventeen were content
  correct but noncanonical; 31 were wrong: 23 wrong verdict+reason, four wrong
  verdict only, four wrong reason only. The +31 therefore cannot be attributed
  to fence removal. OFF got 8/16 agreement and 9/16 disagreement cases, and
  0/4 each for ambiguous prediction, missing prediction, missing outcome and
  outcome-action mismatch; all become correct. Event IDs were already right.
- **Update judgement:** OFF had eight content-correct fenced answers, 32
  field-wrong answers with valid schema, two invalid reason-domain answers,
  and six unparseable answers. The 32 field failures split into 15 wrong
  decision+reason, six decision-only and 11 reason-only. One of the six
  unparseable responses was length-capped; it is a **failed response in a
  completed root**, not a missing experiment or a repaired answer. The +40
  contains substantial source-field improvement but is not purely semantic:
  it also includes schema/interface/completion repairs. OFF source-mismatch
  cases were 0/16, supported cases 8/16, and all four insufficient-source
  subtypes 0/4; post is correct throughout.

There are **no itemwise OFF-correct canary regressions**. Prediction and goal
completion each fix the same `copy:canary:1:skin1` item in each learner; these
are repeated observations, not six independent retention discoveries. The
canaries are narrow and shared, and their answer contracts differ between
the two material modules. Perfect canaries do not certify broad retention.

## Interpretation and next scientific choice

The evidence supports typed authored-fixture acquisition under this cold-base
LoRA recipe across three learner seeds. It is stronger than the prior merely
fenced-output contrast because already content-scored controls improve on
decisions/source fields. However, reasons are fixture labels, not evaluated
reasoning traces; supplied instructions and public evidence remain in OFF and
post prompts. The no-update control is not a matched trained parenting control.

The held panels are now **post-fit ceiling-limited**. Preserve this result;
do not select more favorable cases, weaken scorers, or treat additional doses
on the same panel as transfer. The protocol-consistent next decision is a
separately versioned, prospectively fixed transfer distribution that stresses
the demonstrated skill without reusing these inspected answers. Once relevant
transfer is established, test the smallest matching experience→child record→
sleep→reload loop, with its own controls. This is advice only; no next-roster
launch, retry, material or allocation was changed by this sidecar.

Uncertainty: three learner seeds per fixed dataset, not three independently
sampled tasks; construction families, siblings and skins remain dependent.
Do not pool the 576 post-fit held renderings into an independent-n=576 claim,
infer general competence from zero observed errors, or identify which recipe
component caused acquisition without an additional comparator. No confidence
interval or significance claim based on independent episodes is asserted.
All four are only the first part of the curriculum, not the whole program.
No general G1/P1/H1/H2, clean-lineage, freeze, parenting or mission claim follows.

## Archive and score custody

VM directory (already gitignored by existing `.gitignore`, not modified):
`/data/home/rohing/dream-state/gpu_artifacts_local/level1_first_roster_20260913/`.

| Archive beneath VM directory | Bytes | SHA256 |
| --- | ---: | --- |
| `node1/node1_first_roster.tar` | 504350720 | `0d822a18838314346f1fa332ad4ac71234e1d20e59e7f841d81109a1f23226d1` |
| `node2/node2_first_roster.tar` | 508026880 | `cf5891687771560df7867de197b3f95480c70a842cfe71b853949bb158fa05c1` |

Each tar contains **1,784 members / 1,730 regular files**, including all six
exact completed roots on that node, every `_collected`, `_collection_driver`
and `.collection_claim.json`, the actual batch receipts, relevant roster/specs,
and pinned source/helper/protocol bytes. No model cache was included. Original
paths are preserved as relative tar member names. No symlinks or special files
were admitted. Total archive size is 1,012,377,600 bytes.

Native sources stayed unchanged in device/inode/mode/size/mtime/ctime and tree
membership. Every native archive payload was hashed against its source; VM
archive, manifest and listing hashes then matched native values, and **all
3,460 transferred file payloads and exact listings were independently checked**.
The remote fresh tar directories remain intact for recovery:

- node1: `/tmp/astra_level1_first_roster_archive_20260913T075723Z_node1_c70cd61e/`
- node2: `/tmp/astra_level1_first_roster_archive_20260913T075723Z_node2_2d794f83/`

Each VM node directory contains the per-file SHA256 manifest, native listing,
and `vm_verification.json`; the parent contains native receipt records. Exact
paths, hashes and all 12 per-cell plan/completion/score/collection/claim/driver
receipt hashes are in the structured analysis JSON. No existing artifact was
overwritten, and all original node roots and one-shot claims remain untouched.

Copied scores: `/tmp/astra_level1_first_scores_20260913/<cell>/scores.json` and
`collection.json`, one distinct pair per exact cell name in the table.

Structured report: `/tmp/astra_level1_first_roster_analysis_20260913.json`,
SHA256 `156662015a531a5644e1e1e754f54e0b302fe4221b9b739b5d409876762339d8`.
It records all count/cost means and ranges, paired win/loss IDs, error families,
format transitions, archive hashes, and explicit empty incompleteness lists.

## Verification scope

Roster SHA256: `ad1c8d522d295e3c1b33c7e6ed93fbf89c467d3206d61e449d6844905fa19423`.
Protocol SHA256: `c5420d9b6464eca62695be450884c2a3226615a065a3e7d6b9021fb2c7303297`.
Runtime SHA256: `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`.
Actual batches: node1 `batch_node1_parentfix`, node2 `batch_node2`.

Before archiving, all 12 original controller PIDs were absent, controller
failure files absent, and existing completion/collection/driver/claim bindings
agreed. No collector was invoked. On the VM, all four material datasets rebuilt
exactly from archived pinned sources. All **1,440 archived request/response rows**
were traced to completion inventories and reproduced the original scorer's
entire row objects, panel counts and format/error fields exactly. Generation
costs and paired differences also reduced exactly. No score rule was repaired.

Offline stored-evidence verification is not native inference replay, tokenizer
execution, numerical parity certification or an independent training rerun.
The source/model execution claims retain their original collection scope.
No Git operation, tracked-repository edit, live second-roster read, GPU work,
kill, lease action or native recollection occurred. Only fresh archives,
copies and this analysis's untracked/`/tmp` artifacts were written.
