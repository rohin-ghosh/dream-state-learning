# Independent manuscript review — C76–C78 / SEQ134–136

Date: 2026-09-13 UTC. Bounded, read-only manuscript review.

## Verdict: ACCEPT

Accept the six-file new diff against observed current HEAD
`7be0799785adb223922ff397969fe41d1b12fe03`, for local manuscript integration only.
No required corrections found. No broad rewrite requested. This is not a GPU
gate, scientific promotion, mission-completion finding, publication approval,
or authorization to send the collaborator draft. Other runs remain unaffected.

The handoff names preparation HEAD `4b4e90ab`; current HEAD is newer. I reviewed
the actual six-path `git diff HEAD`, not an assumed handoff base. All six working
file hashes match EDITSTOP and remained unchanged at the final check; current
HEAD also remained unchanged. Unrelated dirty files were neither reviewed nor
modified. Only this `/tmp` review is written.

## Evidence checks

Paths below are relative to `research_notes/astra_memos/` unless specified.

### C76: supplement does not repair the primary

- `receipts_20260912/astra_q0_R1_supplement_replay_20260913_attempt2.json`:
  `report.joined_diagnostic.cells` gives AUTH exact 67/128, held 31/64;
  DERANGED exact 69/128, held 32/64; copy 8/8 each. Complements are 37/128
  exact and 0/64 held, with `endpoint_passed=false`.
- The same report records 288 prefix readouts, 296 generations, 584 records,
  zero updates/training forwards, `original_primary_changed=false`,
  `primary_three_root_complete=false`, `scientific_claim=false`, and original
  label `NONREPORTABLE_RUNTIME_ABORT`.
- Original `receipts_20260912/astra_q0_fulldose_R1_terminal_20260913.json`
  independently preserves that label, nine partial stages, failure of
  `09_eval_P_DERANGED_128`, and `scientific_claim=false`. Its durable seal
  `d3a7fa5b18b74821955d06c5e4b28c88fd92586479fbd6d284e6c2ba8885ab87`
  matches the supplement's `original_seal_sha256`.
- The new manuscript consistently treats the joined counts as a post-abort
  diagnostic, not a third complete primary, new fit/seed, repaired abort,
  or three-root scientific failure rate. Historical primary missingness remains.

### C77: native connectivity, unchanged generation endpoint

- `receipts_20260912/astra_l2_collection_20260913_attempt1.json` has 11
  completed stages and no incomplete stages. Independently summing its
  stage-level `exposure` yields 128 calls, three physical fits, 100 updates:
  shared fit1 20, fit2_PROMOTE 40, fit2_SHADOW 40. Shared fit1 is not doubled.
- `formation` records admissions 8, 16, 16 and identical frozen-base
  initialization hashes for all three fits. The linked prospective
  `ASTRA_L2_PUBLIC_RECORD_PROTOCOL_2026-09-13.md` explicitly specifies
  fresh-base cumulative refits, PROMOTE mounting versus SHADOW retaining
  candidate bytes while staying base, and externally checked admission.
- All five `reports` panels are total 16, old 4/8, new 4/8, legal 16/16,
  malformed 0, length-capped 0. Thus each panel has eight correct, not 16
  correct. Final paired counts: both 8, neither 8, PROMOTE-only 0,
  SHADOW-only 0. No measured accuracy or retention advantage is claimed.
- `endpoint.native_verified=false` and `scientific_pass=null` are preserved;
  `scientific_replay=true` is not promoted into independent certification.
  Completion is execution connectivity of this exploratory loop, not general
  G1/G3, parenting, clean ancestry, H1/H2, or mechanism freeze.

### C78: forced scores are not greedy generation

- `receipts_20260912/astra_l2_access_report_20260913_attempt2.json` contains
  96 paired rows / 192 candidate continuations, 192 forwards, zero updates.
  I re-counted stored row correctness and exact first ties for every state/view:

  | State/view | First strict | First ties | Full sum | First gold NLL |
  | --- | ---: | ---: | ---: | ---: |
  | OFF/train | 8/16 | 0 | 8/16 | 2.784746 |
  | OFF/readout | 8/16 | 0 | 8/16 | 2.077657 |
  | fit1/train | 8/16 | 1 | 9/16 | 0.689233 |
  | fit1/readout | 8/16 | 0 | 8/16 | 0.670401 |
  | fit2_PROMOTE/train | 8/16 | 5 | 12/16 | 0.638386 |
  | fit2_PROMOTE/readout | 8/16 | 0 | 8/16 | 0.675427 |

- NLL cells agree with the report's mean gold `first_decision` NLL, rounded
  to six decimals; they are not full-target losses. Fit2/train first old/new
  counts are 3/8 and 5/8; full counts are 5/8 and 7/8.
- All five fit2/train exact-first ties choose action1 under full likelihood;
  four are correct and one incorrect. Their absolute full margins are
  0.00016377845, 0.00003957630, 0.00070999083, 0.00033563383,
  and 0.00025745654 nats. Recomputing length-normalized candidate preference
  reverses all five to action0. Every stored row has action0/action1 target
  lengths 14/12 including EOS. The manuscript keeps full sum, mean, first
  preference, and teacher-forcing versus greedy generation distinct.
- Report `original_vllm_reports` equals the original collection's five
  `reports` exactly. HF train 12/16 never replaces native greedy 8/16.
  The prose recognizes distribution change and fragile training-form
  discrimination without claiming robust acquisition or an isolated
  access-only explanation. Fit1 train wording is not misrepresented as
  exposure to all 16 keys.
- Read the linked independent stored-evidence analysis and inspected preserved
  v1 source at its `disable_adapters` test and v2 `verify_adapter_routes` /
  `native_model` (lines 236 onward). V1's broad truthiness test versus v2's
  actual tuner-layer Boolean checks supports the stated repair boundary.
  V2 explicitly compares saved/loaded tensor records after dtype conversion
  and freezes/evaluates the model. Neither this review nor that source check
  independently loads tensors or demonstrates HF/vLLM numerical parity.
- The independent analysis's 392-record-per-adapter consistency check remains
  attributed to that stored-evidence analysis. The linked CPU log records
  20 tests in 2.832 seconds; the native CPU route fixture records zero forwards
  and updates. These are archived checks, not tests rerun by this reviewer.

## Link integrity and claim scope

All nine new claim-map source links resolve locally. Recomputed SHA256 values
match all seven explicitly hashed linked files: R1 supplement, L2 protocol,
L2 collection, HF report, independent analysis, CPU acceptance log, and native
CPU route log. Also hashed both preserved diagnostic sources. The supplement's
embedded report identity and L2 plan/seal values match the manuscript.

The six-file additions preserve unresolved H1/H2, deferred C11, no clean-lineage
or mechanism-freeze promotion, no general G3 claim, and an ongoing unresolved
mission. Later LR-comparison outcomes and pending runs are not incorporated as
results. The collaborator text remains UNSENT. Historical text is not treated
as fresh evidence or expanded into a new scientific claim.

Scoped `git diff HEAD --check` passes. No network, model imports, GPU commands,
training, test execution, Git mutations, repository writes, or operational
changes. No PDF/layout validation, retokenization, independent tensor loading,
raw-archive replay, or full producer/custody audit is claimed.

## Accepted working-file identities

| Repository-relative file | SHA256 |
| --- | --- |
| paper_prototype/astra_sprint_draft_20260912.tex | `1cb89a54dda0c961535d6da88a01a7c865ee053a5d6dd8cd39d86c1354cf834e` |
| paper_prototype/astra_sprint_abstract_20260912.md | `57e21d10c76ce67f0721c042055500fd82b0995eea770c9366cf05181ea67267` |
| paper_prototype/main.tex | `67ccd2c13344e8ea1e2fe30d7536145bc24c0cdad9ae8c58c60ce89b754f320e` |
| paper_prototype/README.md | `10e7b1ae9e24bde349de7e24fa201e2e545cb4d21b26a015abe6c01239cabada` |
| research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md | `4f8bd4c13f3f9d6cb78c838bdbaf38b677dc9604cd0c2d5bbf343a0ecd77eb81` |
| research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md | `25aa499c5b0e3e50ead5cd7a5b89ce04a263d6c46ff772f305ee8814250766a1` |
