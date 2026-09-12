# SEQ-079 — post-hoc teacher-absent descriptive anchor

September12,2026,12:26UTC. The original process/sham primary result remains
1/16versus1/16. Adding a later no-teacher condition does not retrofit a matched
three-arm experiment or establish parenting/internalization.

| Fixed first-action endpoint | Process | Sham | No teacher |
|---|---:|---:|---:|
| Solved/16 | 1 | 1 | 0 |
| Strict grid format/16 | 7 | 4 | 3 |
| Invalid-format-zero score mean | 0.192578125 | 0.11875 | 0.084375 |
| Raw native first-score mean | 0.216548295 | 0.159659091 | 0.09140625 |
| Retokenized output tokens | 1079 | 1068 | 968 |
| Teacher presentations | 16 | 16 | 0 |

All48episodes contain exactly one ACT; no retokenized output reaches400tokens.
This is not independently recorded generation finish-reason evidence. Same
16existing training questions1850000–1850015 and native per-episode generation
seed7101, temperature0.7, batch8, one wake, frozen base/no adapter. No teacher
block or added separator remains in the anchor. Native renderer's ordinary
bootstrap trailing-whitespace stripping is explicitly accounted for; all32
process/sham-to-anchor prompt joins match exactly, with input97tokens shorter
for every anchor question. Input exposure is intentionally not token matched.

Both teacher-present arms descriptively exceed the later anchor on this small
panel, while tying each other on the primary solve count. This does not isolate
process supervision, exclude sampling/sequence-length effects, establish a
statistically reliable teaching benefit, or show learning after teacher
removal. No output-dependent curriculum revision or new weight fit is selected
by this memo. The next parenting comparison must address useful child material
and persistence, not treat this formatting difference as P1.

## Audit and custody

Run `astra_P1_no_teacher_20260912_attempt1`, node3GPU3, controller90625,
source18006b39dd936ff750999f3b85e0c490711ab437. Started12:17:40.187846UTC,
root completion12:20:36.664152UTC:176.476306reserved seconds, including load
and cleanup, not pure inference time. Controller absence observed12:21:08UTC;
worker90626cleanup verifies owned group/GPU processes absent and reservation
released with no error. GPU3released; normal owned backend shutdown escalation
is retained in logs. No manualkill, displaced work or overwritten run.

Terminal capsule SHA256:
`9574db1e566685923fbeee0d0900e0975a8a2569325fc50079f8143742fdbc95`.
Offline reduction SHA256:
`cfe62c19fd75edb68a6c5eeefc053310daaf4e3b4ca4924a3622238749f038d8`.
Main reran the reducer and obtained byte-identical output. Popper's18CPU tests
cover tampered capsules, source joins, ACT order, renderer whitespace,
invalid-first-action handling and exclusive outputs. Audits validate all
sealed source/prompt/request/output joins, unchanged static per-episode rows,
native ledger scores, and independent Sudoku constraint/solution enumeration.
Native partial scoring is preserved from captured ledgers, not freshly rerun
through reasoning_gym. Model/source metadata are provenance receipts, not a
fresh weight rehash or official model-origin authentication.

Receipts, standalone reducer, CPU selftests and analysis are stored under
`research_notes/astra_memos/receipts_20260912/` with the `astra_no_teacher_`
prefix. Original static evidence stays unchanged. Full C11 custody remains
deferred; H1/H2, mechanism readiness and the integrated campaign remain open.
