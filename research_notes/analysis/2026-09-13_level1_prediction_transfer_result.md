# SEQ192 — prediction worksheet prompt-package robustness

Builder, September 13, 2026, 18:18 UTC. Executed and independently audited,
DEV-only. The predeclared continuation rule is **FALSE**; this branch stops.

## Fixed comparison and outcomes

Three existing SEQ142 prediction adapters, no new fits or updates, versus
disabled-adapter OFF. Shared 24 fresh authored cases, FULL/MINIMAL views,
six cases per supported-true/supported-false/missing/conflicting group.
Primary typed-content counts retain malformed and truncated outputs.

| Learner seed | OFF FULL /24 | Post FULL /24 | OFF MINIMAL /24 | Post MINIMAL /24 | MINIMAL contrast |
|---|---:|---:|---:|---:|---:|
| 0 | 16 | 24 | 14 | 24 | +10 |
| 1 | 16 | 23 | 14 | 1 | -13 |
| 2 | 16 | 19 | 14 | 18 | +4 |

The rule required positive MINIMAL contrast and at least20/24 post in every
learner. Seeds1 and2 fail. Do not promote or rescue with new prompts, dose,
scoring, or token caps. FULL improves in all learners but does not establish
uniform robustness. Seed1 MINIMAL has23unparseable outputs and one fenced
answer; one generation reaches length, the other23 stop. Seed2 loses five
conflicting cases in FULL and all six in MINIMAL. Seed0 MINIMAL content is
24/24 but every response is fenced: strict format0/24. Strict MINIMAL post
counts are0,0,18; OFF0 for every seed. Content and format are distinct.

This tests worksheet prompt-package robustness, not isolated conditional
evidence use: FULL/MINIMAL also differ in packaging. Original SEQ142 action
residues encode labels; its48/48 cannot establish reading the evidence.
The new material uses24distinct selected residues and fresh disjoint triples,
but lacks same-identity counterfactual quartets and cannot rule out all
shortcuts. These limits were recorded before primary outcome inspection.
No matched-trained parenting control, independent fact-bank replication,
retention, new-family transfer, P1/H1/H2, or mechanism freeze follows.

## Eligibility, custody, and cost

Original parallel attempt1 captured288calls; all six workers exited0 and
released. Seeds0/1 controllers failed their post-CVD check against finished,
unreaped seed2 controller2960286. Those attempts remain ineligible. Before
reading outcomes, Main fixed primary selection to serial retries for0/1,
retaining successful seed2attempt1; no third attempt. Primary attempts2/2/1
all completed and collected. Total480calls:288eligible plus192failed-attempt
calls. Zero fits, updates, or parent calls. No historical receipt is repaired.

Eligible per-seed OFF/post generation seconds:34.747/50.663,
34.755/157.042,34.735/36.542. Controller seconds:193.323,299.035,259.847;
these are not additive wall-time or measured aggregate GPU-hours. Each state
uses14936prompt tokens; OFF output1149 each, post1152/3747/807. Full load
times and finish/format/group counts are in the audit JSON. The failed
attempts' raw token/runtime receipts remain in their archive; their costs
must not disappear from later campaign totals.

Main audited288eligible request/response/route/token/score/custody joins.
Frozen native source `f84cc3beaf7030b411a93a739dd99eb2d6462de5`; material
seal `150bc6b4431a2ad80205ee17e04f3f2d99c4f8e19e917ce7d6bbb8210e537d29`.

- Primary archive: `gpu_artifacts_local/prediction_transfer_primary_20260913/evidence.tar`, SHA256 `365cfdbe817c41f5bedf4099a35d0e836d788eeec75edc687addc92dfb295b69`.
- Original archive: `gpu_artifacts_local/prediction_transfer_20260913_attempt1/evidence.tar`, SHA256 `0928686137e8a61db60cc91952c407920117e136285b847ee71a8afa68e508bf`.
- Durable audit: `research_notes/astra_memos/receipts_20260912/astra_prediction_transfer_audit_20260913.py`, SHA256 `65f86d8b365922110d5a1402b3d3df571748168cc3ae8d77ea1e7d3c3555cedc`.
- Durable result: `research_notes/astra_memos/receipts_20260912/astra_prediction_transfer_audit_20260913_result.json`, SHA256 `9ca1433d5cce275cbc9ae8af1a36a43e7f93351d28eb823e9d6e5cde8c821344`.

Both evidence archives are verified on the VM outside the expiring node.
Continuation is a separately specified retention-v2 runtime integration,
not a renewed prediction sweep. Overall research mission remains incomplete.
