# Post-memory formation: local raw audit — 2026-09-13

Pinned archive, all six captures and all three admitted banks replayed locally with frozen cores. Request/response bytes, source-execution joins, routes and token/call accounting agree. No native calls, model/tokenizer loads or recollection.

|Seed|Arm|Eligible /16 (of 8 records)|Content|Canonical strict|Action training/example matches|Exact old-target bytes|Record training-triple matches|
|---|---|---|---|---|---|---|---|
|0|WRITE|8/16|8|4|8/0|7|8|
|0|LR0|7/16|7|4|7/0|4|7|
|1|WRITE|8/16|8|0|8/0|3|8|
|1|LR0|6/16|6|0|7/0|3|7|
|2|WRITE|8/16|8|0|4/4|0|4|
|2|LR0|4/16|4|0|4/3|0|4|

## Raw failures, copying and coverage

### Seed 0 — 14 admitted rows; 4 distinct targets, 2 distinct triples
- WRITE: executed triples {"[3,7,11]":4,"[4,6,8]":4}; target match × source eligibility {"match/eligible":7,"nonmatch/eligible":1}. Non-training/non-example executions 0, eligible 0; untested.
- WRITE typed full-target match × source eligibility (format ignored, no value repair): {"match/eligible":7,"nonmatch/eligible":1}; correct fields {"observed":8,"predicted":8,"relation":8,"try":8}.
- WRITE invalid-wake reasons: {"ACT needs exactly three integers or six literal T/F labels":8}; space-separated TRY raw patterns 8; finish reasons {"stop":16}. Record errors: {}; formats {"exact":4,"json_noncanonical":4}.
- WRITE distinct invalid raw wakes (JSON-escaped, no repair): ["PREDICT: T\nACT: TRY 3 7 11","PREDICT: T\nACT: TRY 7 11 13"]
- LR0: executed triples {"[3,7,11]":4,"[4,6,8]":3,"[4,8,12]":1}; target match × source eligibility {"match/eligible":4,"nonmatch/eligible":3,"nonmatch/rejected":1}. Non-training/non-example executions 1, eligible 1; descriptive within reached subset.
- LR0 typed full-target match × source eligibility (format ignored, no value repair): {"match/eligible":6,"nonmatch/eligible":1,"nonmatch/rejected":1}; correct fields {"observed":8,"predicted":7,"relation":7,"try":8}.
- LR0 invalid-wake reasons: {"ACT needs exactly three integers or six literal T/F labels":8}; space-separated TRY raw patterns 8; finish reasons {"stop":16}. Record errors: {"prediction mismatch":1}; formats {"exact":5,"json_noncanonical":3}.
- LR0 distinct invalid raw wakes (JSON-escaped, no repair): ["PREDICT: T\nACT: TRY 1 2 3","PREDICT: T\nACT: TRY 2 5 8","PREDICT: T\nACT: TRY 3 7 11","PREDICT: T\nACT: TRY 3 7 9","PREDICT: T\nACT: TRY 4 5 6","PREDICT: T\nACT: TRY 4 6 8","PREDICT: T\nACT: TRY 5 9 13"]
- Paired production WRITE-only/LR0-only/both/neither: 1/0/7/8. WRITE-only slots: ["next-record-dev-108d90929358b84c6264#t2"]; LR0-only: [].
- example_present/turn1: WRITE 4/4, LR0 4/4.
- example_present/turn2: WRITE 4/4, LR0 3/4.
- example_absent/turn1: WRITE 0/4, LR0 0/4.
- example_absent/turn2: WRITE 0/4, LR0 0/4.
- WRITE costs: 24 calls, 6112 prompt + 498 output tokens; 21.376s generation, zero fits/updates.
- LR0 costs: 24 calls, 6097 prompt + 478 output tokens; 20.859s generation, zero fits/updates.
- Pair controller elapsed 180.324s. Prior WRITE held regressions: 3/48; not erased by this endpoint.
- LR0 rejected record raw evidence: [{"action":[4,6,8],"errors":["prediction mismatch"],"prior":false,"raw_record":"{\"observed\":false,\"predicted\":null,\"relation\":\"unavailable\",\"try\":[4,6,8]}","slot":"next-record-dev-108d90929358b84c6264#t2"}]
- Among jointly executed slots, identical action/outcome/prior: 7/8; identical first-/second-turn wake prompts: 8/8 and 3/8.

### Seed 1 — 8 admitted rows; 5 distinct targets, 4 distinct triples
- WRITE: executed triples {"[3,7,11]":4,"[4,8,12]":4}; target match × source eligibility {"match/eligible":3,"nonmatch/eligible":5}. Non-training/non-example executions 0, eligible 0; untested.
- WRITE typed full-target match × source eligibility (format ignored, no value repair): {"match/eligible":3,"nonmatch/eligible":5}; correct fields {"observed":8,"predicted":8,"relation":8,"try":8}.
- WRITE invalid-wake reasons: {"ACT needs exactly three integers or six literal T/F labels":8}; space-separated TRY raw patterns 8; finish reasons {"stop":16}. Record errors: {}; formats {"json_noncanonical":8}.
- WRITE distinct invalid raw wakes (JSON-escaped, no repair): ["PREDICT: F\nACT: TRY 5 11 17","PREDICT: F\nACT: TRY 5 9 17","PREDICT: F\nACT: TRY 7 11 13"]
- LR0: executed triples {"[3,7,11]":4,"[4,2,7]":1,"[4,6,8]":1,"[4,8,12]":2}; target match × source eligibility {"match/eligible":3,"nonmatch/eligible":3,"nonmatch/rejected":2}. Non-training/non-example executions 1, eligible 1; descriptive within reached subset.
- LR0 typed full-target match × source eligibility (format ignored, no value repair): {"match/eligible":3,"nonmatch/eligible":3,"nonmatch/rejected":2}; correct fields {"observed":8,"predicted":6,"relation":6,"try":8}.
- LR0 invalid-wake reasons: {"ACT needs exactly three integers or six literal T/F labels":8}; space-separated TRY raw patterns 8; finish reasons {"stop":16}. Record errors: {"prediction mismatch":2}; formats {"json_noncanonical":8}.
- LR0 distinct invalid raw wakes (JSON-escaped, no repair): ["PREDICT: F\nACT: TRY 101 202 303","PREDICT: F\nACT: TRY 12 34 56","PREDICT: F\nACT: TRY 123 456 789","PREDICT: F\nACT: TRY 42 17 23"]
- Paired production WRITE-only/LR0-only/both/neither: 2/0/6/8. WRITE-only slots: ["next-record-dev-427e7a31a18b9c3c101a#t1","next-record-dev-108d90929358b84c6264#t1"]; LR0-only: [].
- example_present/turn1: WRITE 4/4, LR0 2/4.
- example_present/turn2: WRITE 4/4, LR0 4/4.
- example_absent/turn1: WRITE 0/4, LR0 0/4.
- example_absent/turn2: WRITE 0/4, LR0 0/4.
- WRITE costs: 24 calls, 6116 prompt + 479 output tokens; 20.963s generation, zero fits/updates.
- LR0 costs: 24 calls, 6125 prompt + 494 output tokens; 21.268s generation, zero fits/updates.
- Pair controller elapsed 167.119s. Prior WRITE held regressions: 11/48; not erased by this endpoint.
- LR0 rejected record raw evidence: [{"action":[3,7,11],"errors":["prediction mismatch"],"prior":false,"raw_record":"{\"try\":[3,7,11],\"observed\":false,\"predicted\":null,\"relation\":\"unavailable\"}","slot":"next-record-dev-427e7a31a18b9c3c101a#t1"},{"action":[3,7,11],"errors":["prediction mismatch"],"prior":false,"raw_record":"{\"try\":[3,7,11],\"observed\":false,\"predicted\":null,\"relation\":\"unavailable\"}","slot":"next-record-dev-108d90929358b84c6264#t1"}]
- Among jointly executed slots, identical action/outcome/prior: 6/8; identical first-/second-turn wake prompts: 8/8 and 2/8.

### Seed 2 — 8 admitted rows; 5 distinct targets, 3 distinct triples
- WRITE: executed triples {"[2,5,9]":4,"[3,7,11]":4}; target match × source eligibility {"nonmatch/eligible":8}. Non-training/non-example executions 4, eligible 4; descriptive within reached subset.
- WRITE typed full-target match × source eligibility (format ignored, no value repair): {"nonmatch/eligible":8}; correct fields {"observed":8,"predicted":8,"relation":8,"try":8}.
- WRITE invalid-wake reasons: {"ACT needs exactly three integers or six literal T/F labels":8}; space-separated TRY raw patterns 8; finish reasons {"stop":16}. Record errors: {}; formats {"json_noncanonical":8}.
- WRITE distinct invalid raw wakes (JSON-escaped, no repair): ["PREDICT: T\nACT: TRY 1 2 3","PREDICT: T\nACT: TRY 3 7 11","PREDICT: T\nACT: TRY 4 5 6","PREDICT: T\nACT: TRY 5 9 13"]
- LR0: executed triples {"[1,2,3]":3,"[2,3,7]":1,"[2,5,9]":3,"[3,4,7]":1}; target match × source eligibility {"nonmatch/eligible":4,"nonmatch/rejected":4}. Non-training/non-example executions 4, eligible 0; descriptive within reached subset.
- LR0 typed full-target match × source eligibility (format ignored, no value repair): {"nonmatch/eligible":4,"nonmatch/rejected":4}; correct fields {"observed":8,"predicted":4,"relation":4,"try":8}.
- LR0 invalid-wake reasons: {"ACT needs exactly three integers or six literal T/F labels":8}; space-separated TRY raw patterns 8; finish reasons {"stop":16}. Record errors: {"prediction mismatch":4}; formats {"json_noncanonical":8}.
- LR0 distinct invalid raw wakes (JSON-escaped, no repair): ["PREDICT: F\nACT: TRY 1 2 3","PREDICT: F\nACT: TRY 2 3 4","PREDICT: F\nACT: TRY 4 5 6","PREDICT: T\nACT: TRY 2 2 2","PREDICT: T\nACT: TRY 2 3 4","PREDICT: T\nACT: TRY 5 6 7"]
- Paired production WRITE-only/LR0-only/both/neither: 4/0/4/8. WRITE-only slots: ["next-record-dev-627e2b39856014cb44d1#t1","next-record-dev-427e7a31a18b9c3c101a#t1","next-record-dev-108d90929358b84c6264#t1","next-record-dev-6cf84cecdaa9fe5f7e2d#t1"]; LR0-only: [].
- example_present/turn1: WRITE 4/4, LR0 0/4.
- example_present/turn2: WRITE 4/4, LR0 4/4.
- example_absent/turn1: WRITE 0/4, LR0 0/4.
- example_absent/turn2: WRITE 0/4, LR0 0/4.
- WRITE costs: 24 calls, 6131 prompt + 518 output tokens; 22.340s generation, zero fits/updates.
- LR0 costs: 24 calls, 6100 prompt + 502 output tokens; 21.515s generation, zero fits/updates.
- Pair controller elapsed 182.749s. Prior WRITE held regressions: 31/48; not erased by this endpoint.
- LR0 rejected record raw evidence: [{"action":[1,2,3],"errors":["prediction mismatch"],"prior":true,"raw_record":"{\"observed\": false, \"predicted\": null, \"relation\": \"unavailable\", \"try\": [1, 2, 3]}","slot":"next-record-dev-627e2b39856014cb44d1#t1"},{"action":[1,2,3],"errors":["prediction mismatch"],"prior":true,"raw_record":"{\"observed\": true, \"predicted\": null, \"relation\": \"unavailable\", \"try\": [1, 2, 3]}","slot":"next-record-dev-427e7a31a18b9c3c101a#t1"},{"action":[1,2,3],"errors":["prediction mismatch"],"prior":true,"raw_record":"{\"observed\": false, \"predicted\": null, \"relation\": \"unavailable\", \"try\": [1, 2, 3]}","slot":"next-record-dev-108d90929358b84c6264#t1"},{"action":[3,4,7],"errors":["prediction mismatch"],"prior":true,"raw_record":"{\"observed\": false, \"predicted\": null, \"relation\": \"unavailable\", \"try\": [3, 4, 7]}","slot":"next-record-dev-6cf84cecdaa9fe5f7e2d#t1"}]
- Among jointly executed slots, identical action/outcome/prior: 3/8; identical first-/second-turn wake prompts: 8/8 and 0/8.

## Interpretation and limits
- Each arm has 8 example-present and 8 example-absent opportunities, with 4 per cue × turn. Uncalled records remain missing; conditional record rates are N/A when no records were called.
- Execution triples and output target/triple overlap are separate diagnostics. Repetition is not causal proof of retrieval. A byte-identical old target can still agree with a new source when facts coincide; that does not distinguish recall from reconstruction.
- Fresh task IDs do not ensure fresh triples. Record prompts expose current executed facts. Non-training/non-example execution coverage, rather than task-ID novelty, bounds the fidelity evidence.
- Cue assignment is fixed by episode ID, not randomized. Any cue-associated failure is observational; exact syntax errors are independently reproducible, but their causal origin is not identified.
- WRITE/LR0 share initial tasks and schedule, not necessarily action, outcome, prior or second-turn history. Full paired rows, field scores, raw outputs and source requests are in JSON. Repeated triples/turns are not independent learners; only three learner pairs.
- Prior memory acquisition coexists with held regressions 3/11/31 and intact canaries. No stable-substrate, strong H1, H2, recursive-learning or automatic-pass claim.
- Local byte joins reuse archived native token/route attestations, not new tokenization, model execution or independent hardware-identity checks. No future launch decision is made here.
