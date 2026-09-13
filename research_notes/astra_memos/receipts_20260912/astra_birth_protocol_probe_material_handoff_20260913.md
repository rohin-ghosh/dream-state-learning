# Fixed protocol practice probe — CPU-ready, EDITSTOP

Scope: data-only ready queue, not a curriculum switch, native launch authorization,
new runtime, or interpretation of any current birth/formation result. Only the
three named `/tmp` files were edited. Historical code and live dependencies remain frozen.
No model/tokenizer/native/GPU/Git/network execution or live-result reads occurred.

## Public API

Import `astra_birth_protocol_probe_material_20260913` with the repo and `/tmp` on
`sys.path`; source imports use existing pure specification/generator helpers.

- `build_candidate() -> dict`: deterministic JSON-compatible fixed16 inventory,
  source hashes, public contexts, separate example targets/provenance/derivations.
- `check_candidate(candidate) -> dict`: exact regeneration/source/partition check,
  all16 AUTH raw-parser controls, revision contrast checks, canonical candidate hash.
- `call_map(candidate) -> {'OFF': [16 requests], 'AUTH': [16 requests]}`:
  identical ordered requests and settings, independent deep copies, no execution.
- `validate_output(case, text) -> dict`: parser validity, public-contract correctness,
  exact-target equality, canonical instruction compliance, and failures.
- `check_outputs(candidate, outputs) -> {state: {case_id: result}}`: requires exactly
  both states and all16 unique external case IDs/state BEFORE output reduction.
  Values are raw response strings; malformed responses remain in the denominator.
- `digest(value) -> str`: SHA256 over UTF-8 `json.dumps(sort_keys=True,
  ensure_ascii=False, allow_nan=False)` with default JSON separators.

Only `request['prompt']` is child input. `candidate['cases'][*]['source']`,
`derivation`, `auth_example_target`, and candidate-wide metadata must NOT be passed
to the model. Request IDs/role/settings are routing metadata, not appended context.
No hidden parent, restatement, KEEP/DROP, optimizer, or adapter-loading API exists.
AUTH denotes the externally selected immutable birth-AUTH state, not training here.

## Frozen16 cases (same inventory in OFF and AUTH)

| IDs | Public contract and target basis | Generator partition |
| --- | --- | --- |
| practice-try-0..3 | Supplied triples `[2,5,8]`, `[3,6,9]`, `[-2,0,4]`, `[7,7,1]`; supplied forecasts T,F,T,F; emit PREDICT then ACT TRY | Authored specification scaffold; no rule lookup |
| practice-quiz-0..1 | Zero TRY budget, not revealed: emit `ACT: QUIZ ?` | Authored state scaffold |
| practice-quiz-2..3 | Already revealed triples, supplied ordered labels TFTFTF / FTFTFT; emit six-label ACT QUIZ | rule6/rule7 reveal generation; labels are NOT hidden-rule accuracy targets |
| practice-record-0 | `[2,1,3]`, prior T, observed T, matched | rule6 |
| practice-record-1 | `[0,9,0]`, prior T, observed F, mismatched | rule7 |
| practice-record-2 | `[5,1,2]`, prior null, observed T, unavailable | rule8 |
| practice-record-3 | `[1,2,3]`, prior null, observed F, unavailable | rule9 |
| practice-revision-0..1 | Same observed triple `[1,3,5]`, same prior T; public outcome F/T; repeat triple with forecast F/T | rule6/rule7; revision-pair-0 |
| practice-revision-2..3 | Same observed triple `[6,1,6]`, same prior F; public outcome T/F; repeat triple with forecast T/F | rule8/rule9; revision-pair-1 |

Generated source IDs are `ruleN/birth-protocol-practice-v1/{family}-{index}`;
quiz uses `quiz-2`/`quiz-3`. Full generated actions/outcomes/rewards and reveal
triples are retained outside requests. Neutral public IDs hide rule identity.
Revision pair members share a neutral public ID and generation seed; external
case IDs remain distinct. Within each pair ONLY public outcome differs.

All source-dependent cases use rules6–9. Formation0–1/evaluation2–5 are excluded;
no current formation/readout artifacts were consulted. Scaffold-only rows have
`rule_index=None`. No global tuple novelty, clean pretraining lineage, or new
train/eval split is claimed. These16 are developmental probes, not fit rows or
sealed confirmation; any later curriculum needs a separate disjoint inventory.
Counts/recipe are fixed, never selected by native outcomes or replaced on failure.

## Existing source and truth rules

`organism_v6/rulegame.py`: `RuleGame.evaluate`, `quiz_triples` generate public
practice observations/reveal data. Its existing `QUIZ ?` reveal returns an
`INVALID: quiz needs ...` message with triples; that exact behavior is preserved.
No rewrite of the environment or grader is made.

`organism_v6/rulegame_parenting_diagnostic.py`: `parse_action(...,'interaction_v3')`,
`record_prompt`, `judge_record`, `_seed_for`, `TOKENS`, `interaction_settings`.
`organism_v6/rulegame_process_material.py`: `validate_wake(...,protocol=PROTOCOL_V2)`
requires exactly one explicit preceding PREDICT T/F for TRY/revision targets.
No prescribed source-slot selector or wrong/null prediction is changed.

Validation derives records/revisions from the emitted prior TRY and its exact
PUBLIC observation, checks their triple join, and forbids revision to an unseen
triple. It never calls a hidden-rule function to score an output. Candidate
integrity checking DOES regenerate authored source observations; that is provenance
verification, not model induction scoring. CPU tests poison hidden evaluators
while validating every example target to verify the distinction.

TRY forecasts and quiz labels are explicitly supplied scaffolds, not induction.
Revision is a previously observed triple repeat, not informative action selection.
Wake prompts are authored practice contexts with existing grammar/state semantics,
not claimed byte-identical native formation prompts. Record contexts use the
existing renderer. No feedback after the target action appears in its context.

Parser-valid action syntax alone does not prove PREDICT chronology or truth.
`public_contract_correct` adds those checks and reveal/budget legality.
Native TRY aliases can be parser/public-correct but noncanonical. Record JSON
whitespace/key ordering can be semantically correct but nonexact. Canonical
`instruction_compliant` accepts only the example serialization (plus trailing
newlines); `exact_target` requires byte equality. All measures remain separate.

## Call settings and limits

12 wake calls ×400 +4 record calls ×100 =5200 maximum generated tokens/state;
32 calls total and10400 maximum generated tokens across OFF/AUTH. These are
output ceilings, not measured tokens, wall-clock forecasts, or fit dose.
Temperature0.7; interaction_v3; wake stop `['\n[OUTCOME]']`, record stop `[]`,
`include_stop_str_in_output=False`. Seeds follow existing born-role semantics:
`spec._seed_for(public_id,tick,spec.GEN_SEED ^ salt)` with salt0 wake /0x5A5A record.
Ticks: TRY/record1, revision2, reveal4, supplied quiz answer5.
No arbitrary new generation settings, thresholds, or automatic L1 verdict.
Data completeness checks cannot attest an actual runtime capture barrier or
fresh-process/adapter custody; those remain a future Main-owned consumer concern.

## CPU validation and exact commands

From `/data/home/rohing/dream-state` (or an equivalent source-root checkout):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_birth_protocol_probe_material_20260913.py -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp:. python3 -B -c 'import astra_birth_protocol_probe_material_20260913 as p; c=p.build_candidate(); print(p.check_candidate(c)); print(p.digest(p.call_map(c)))'
```

Result:21 tests PASS,0.048s unittest elapsed. Module166lines; tests205lines.
Coverage includes all16 raw positives, wrong/null record negatives, chronology,
imagined outcomes, aliases, quiz legality, scaffold fidelity, public-only revision,
source/partition/partial-pair mutation, request isolation/settings, all32 presence,
and invalid-output retention. No native probe was run or authorized.

## Frozen hashes

- Module SHA256: `2799efda619f7686db88d7990b203a3c7ad39eb8577228a26402037de16cc66b`
- Tests SHA256: `927c870c1df79fe7f2b93c64562d36375ad18eff5d350625c652105a0b700485`
- Candidate digest: `9c680f2010cd11b0116517383281764432f4351628f23059b1c9ee69a283e300`
- Call-map digest: `9f960c825d02a04fad40e86afd2e822ee52e7ea376a4fd198c0c1b74f5c064a6`
- `rulegame.py`: `88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`
- `rulegame_parenting_diagnostic.py`: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`
- `rulegame_process_material.py`: `a060f11165e68baa9baaf50433e157e2b3d348a3577e4fbc8ba540d269c24168`

Origin: `SOURCE_AUTHORED_PROTOCOL_PRACTICE_NOT_CLEAN`. No efficacy, persistence,
induction, selective-retention, full L1/H1/H2, or deployment-gym readiness claim.
Main decides whether this probe is useful after the current formation/potential write.
EDITSTOP: no further changes planned to these files or any live dependency.
