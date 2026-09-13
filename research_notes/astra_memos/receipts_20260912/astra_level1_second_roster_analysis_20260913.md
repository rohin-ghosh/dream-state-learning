# SEQ146 — second/fallback roster: complete 12-cell evidence analysis

Main collected every included cell once. This sidecar copied and verified existing outputs, then replayed the exact original frozen scorers locally. No native collection, model execution, generation, training rerun, protocol change, or outcome-based seed selection. Previous3/6/9-cell analysis snapshots remain preserved.

| Skill/seed | Held content OFF→post /48 | Strict OFF→post /48 | Canary content OFF→post /12 | Canary regressions |
|---|---|---|---|---|
| perception/0 | 21→47 | 0→47 | 12→12 | 0 |
| perception/1 | 21→48 | 0→48 | 12→12 | 0 |
| perception/2 | 21→48 | 0→48 | 12→12 | 0 |
| repetition/0 | 0→48 | 0→48 | 12→11 | 1 |
| repetition/1 | 0→48 | 0→48 | 12→11 | 1 |
| repetition/2 | 0→48 | 0→48 | 12→12 | 0 |
| self_reflection/0 | 0→48 | 0→48 | 12→12 | 0 |
| self_reflection/1 | 0→48 | 0→48 | 12→12 | 0 |
| self_reflection/2 | 0→48 | 0→48 | 12→12 | 0 |
| meta_reflection/0 | 9→48 | 9→48 | 12→12 | 0 |
| meta_reflection/1 | 9→48 | 9→48 | 12→12 | 0 |
| meta_reflection/2 | 9→48 | 9→48 | 12→11 | 1 |

## Perception: records versus abstentions

Records OFF16/24→23,24,24/24; abstentions OFF5/24→24/24 each. OFF44 fenced+4 unparseable per seed; post48 exact-format JSON per seed. Seed0 has one try:integer_triple_required failure: a scalar instead of three integers. Exact JSON format is not typed correctness or compiler admission.
Post seed0 each record field23 correct+1 unavailable /24; each abstention field24/24. Post seeds1/2 all applicable fields24/24. OFF record-field correct/incorrect/unavailable: observed19/1/4, predicted16/4/4, relation16/4/4, try19/1/4; abstain6/0/18, reason5/1/18. Unavailable is frozen scorer gating, not a finding that each field is independently wrong.
OFF per-seed error occurrences: output_variant16; unparseable extra-data4; source predicted4/relation4/reason1/try1/observed1; typed-schema observed1/try1. Categories overlap. JSON retains raw failures and source-diagnosis strata.

## Repetition and reflection fields

Repetition: all held outputs exact-format before/after. OFF supplementary typed field correctness decision1/48, reason2/48, independent_support_after48/48; post all fields48/48. This is supplied-policy classification, not proof that rehearsal causes downstream learning.
Self-reflection: OFF47 fenced+1 unparseable; post48 exact each. All five post native target fields diagnosis/next_action/evidence.try/evidence.observed/evidence.predicted48/48. Structured diagnosis/evidence/action screening is not full self-reflection or actual execution.
Meta-reflection: all held outputs exact-format before/after; content9/48→48/48 each. Both post diagnosis and next_action fields48/48. Supplementary typed field diagnostics and source-reason strata are in JSON.

## Explicit preservation failures

**Three canary regressions, so no blanket no-harm claim:** repetition seeds0/1 and meta-reflection seed2. All other cells retain12/12; all canary baseline panels were12/12. No held content regressions were observed.

- `repetition_seed0` `copy:canary:repetition-meta-4:skin2`: target `{"answer":"rehearse? wait"}`; raw `{"answer":"rehearse"}`; format `exact`; errors `['wrong_values']`.
- `repetition_seed1` `copy:canary:repetition-meta-4:skin2`: target `{"answer":"rehearse? wait"}`; raw `{"answer":"rehearse"}`; format `exact`; errors `['wrong_values']`.
- `meta_reflection_seed2` `arithmetic:canary:repetition-meta-5:skin1`: target `{"answer":241}`; raw `{"answer":241"}`; format `unparseable`; errors `['invalid_json']`.

Native content/strict values remain authoritative. Perception/self-reflection field diagnostics are native saved scores; repetition/meta-reflection field diagnostics are supplementary typed comparisons of saved parsed values with supplied targets, not rescoring or repaired answers.

## Complete archives and provenance

- node1_repetition: `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node1_second_repetition.tar` (254648320 bytes); SHA256 `b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6`.
- Manifest SHA256 `7d4656318dd2a4d825834d6eed6db612a5b542fb428bc60518ba2bdf61b165e4`; roster SHA256 `781b9a3e21786c3b5ff5a78f97933fcf738b6e5d18720cb447c5e06140fb6179`; native/VM verified 874 files/901 members.
- node2_perception: `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar` (253890560 bytes); SHA256 `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a`.
- Manifest SHA256 `4cc0a9e544523e55c1aa81a519597d903740de4fd8e61d546b9023614fe537e6`; roster SHA256 `2bca9e4a66cc576993119fc1d5fddcac77de7cc3f93686327b962c45c2d17c69`; native/VM verified 874 files/901 members.
- node2_self_reflection: `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/self_reflection/node2_second_self_reflection.tar` (255641600 bytes); SHA256 `e472f483529ae37e6105557ef4ca2b779f3691e183f3ad7008352852a2382ac5`.
- Manifest SHA256 `5475be7658afcf03a512e8ba9e2adb09707de77ce7067c95fb387a9d86c64243`; roster SHA256 `2bca9e4a66cc576993119fc1d5fddcac77de7cc3f93686327b962c45c2d17c69`; native/VM verified 874 files/901 members.
- node1_meta_reflection: `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar` (258232320 bytes); SHA256 `1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9`.
- Manifest SHA256 `58ec5a49440b1fedd925d2b2535edf6409c9002596b42f4a4787259ab46fe03e`; roster SHA256 `781b9a3e21786c3b5ff5a78f97933fcf738b6e5d18720cb447c5e06140fb6179`; native/VM verified 874 files/901 members.

Four separate fresh archives preserve earlier verified tar bytes. Total3496 file instances/3604 members;104 priority-copy file instances match archives, including intentionally repeated roster/start metadata. Full roots, actual adapters, collections, driver logs/results, once-only claims, launch directories, batch start, pinned specs/runtime/helpers/source are included.
Native archive guards verify boot/UID, exact roster/node/cell/device/plan identities, completed120calls, original controller absence, no failure receipt, successful one-shot collection and cross-receipt hashes. Source metadata/membership remains stable through archive creation and native tar verification. VM checks complete tar hashes, every file payload and size, exact member set/types, priority-copy equality, saved adapter identities and plan input hashes. No extraction.
All self-reflection and meta-reflection score hashes match Main’s supplied pins. JSON contains every score/collection/claim/driver/plan/completion pin and recorded fit/token costs.

## Pending / failed original attempts

**No included cells pending.** All12 completed/collected cells are archived. Original six A100 attempt1 repetition/meta-reflection missing-ninja failures remain separately recorded, untouched, and unscored here. Their paths/outcomes are not merged with node1 fallback attempt2. No A100 archive or native failure re-audit was performed.

## Limitations

- Authored Level1 screen, not live child SLEEP, compiler admission, recursive learning, or general H1/H2 evidence.
- Content primary tolerates specified whitespace/key ordering and sole JSON fences; strict secondary requires correct canonical content.
- Format exact describes canonical JSON serialization, not correct schema or target. Seed0 demonstrates this distinction.
- Field unavailable is scorer null after variant/parse/schema gating, not an independent finding that every field was wrong.
- Same material_seed0 held sources across three learner seeds; 144 pooled observations are not 144 independent source cases.
- Twelve simple canaries constrain only measured no-harm; they do not establish broad preservation.
- Fresh320 recipe-inspired fit is not faithful SEQ113 warm80+320/replay replication.
- Archive includes actual adapters and pinned source/receipts, not frozen base weight payloads or a new audit of installed dependencies.
- Repetition is an authored local rehearsal-policy classification screen, not evidence that rehearsal improves downstream learning; seed0/1 show measured copy-canary harm.
- Self-reflection here means authored verifiable diagnosis/evidence/warranted-action classification; no claim to exact thought truth, full reflection, actual action execution or recursive learning.
- Meta-reflection is an authored diagnosis/next-action screen; seed2 loses one canary through unparseable output. No outcome-based seed choice or claim of broad no-harm.

Verification/reduction sources are in `/tmp/astra_level1_second_scores_20260913/`: `analyze_verify.py`, `extend_repetition.py`, `extend_self_reflection.py`, `extend_meta_reflection.py`. Existing outputs use exclusive snapshot creation; do not rerun into completed destinations. Main owns native experimentation; no native preparation or launch required.

## Original frozen scorer replay — PASS

All1440 archived responses (12cells×2states×60rows) replayed through the original hash-pinned `material.score_row` functions using exact archived material rows, response text and finish reason. Every complete score object—including field errors, parsing/format labels and content/strict flags—matches the saved object exactly. All48 panel summaries match. Runtime13.478567seconds, bounded by180seconds externally/165seconds internally. No import dependency blocker; no torch/transformers/vLLM import.

Perception/self-reflection use scorer `4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941`; repetition/meta use `498e841af8c65654b3f090a1c9f951b6d0aa0e040fd3d757d320f69cba007700`. Native archived parser/corpus/reference source bytes remain unchanged, with the supported source-root environment directed to local archive copies. No monkeypatch or alternate scoring protocol. Original saved scores and four tar archives remain unchanged.

Receipt: `/tmp/astra_level1_second_scores_20260913/scorer_replay/receipt.json`; SHA256 `7daa501567354293697e17f1fe8681d37faceb96c1af7d89b796e1c709b616af`. This is deterministic original-protocol replay, not an independent scoring standard, fresh model evidence, or a compiler-admission test. Pre-replay3/6/9/12-cell snapshots remain preserved.
