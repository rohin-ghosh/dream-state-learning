# SEQ-100 — seed-zero memory failure also appears on original training prompts

**IN_SAMPLE_TRAINING_PROMPT_DIAGNOSTIC_NOT_HELDOUT.** This supplements, and does
not replace, the SEQ098 fixed development endpoint. Sixteen original memory
training contexts were queried in each of OFF/teach/control, with the same
seed0 checkpoints and no new fit. Main verified rendered query bytes against
the actual exported training corpus, not only the candidate's description.

| State | Exact color | Invalid answer | Observed answer pattern |
|---|---:|---:|---|
| OFF |0/16|16/16|prose; every response hits64-token cap|
| Teaching seed0 |4/16|0/16|red for all16 devices|
| Task-only control seed0 |4/16|0/16|red for all16 devices|

The two fitted states reproduce their development-paraphrase collapse even
on the exact training question form. This is evidence against explaining
seed0's failure solely by a recall paraphrase mismatch. It does not prove
absence of any latent binding, locate a neural cause, or establish acquisition
failure for every dose/seed. No semantic answer rescue, new training examples,
confirmation prompts or endpoint substitution occurs. OFF's length-capped
invalidity is scoped to the fixed decoder budget, not an uncapped claim.

The original corpus contributes880 arithmetic and32 memory supervised tokens
per epoch, including EOS. A sparse memory target budget is a diagnostic lead;
this experiment does not isolate it causally from capacity, optimization,
interference or context sensitivity. The upcoming repetition comparison will
remain explicitly separate from this in-sample diagnosis.

## Execution and cost

Source `255ae18863538ec2b0d0ce5699807f67f3975e36`; node3 root
`~/astra_diagnostics/astra_fundamental_memory_trainprompt_20260912_attempt1`.
OFF GPU4/PID170792, teach GPU5/PID170795, control GPU6/PID170798 started at
18:13:31.074069/18:13:31.351912/18:13:31.631151UTC on September12,2026.
Native reducers and Main verify source/model/adapter identities, all48 actual
requests and returned token/text records, unchanged16 source-derived keys,
supervised cleanup, absent controllers and full vacancy. Full releases occur
18:20:23.969200/18:20:48.406036/18:21:19.567197UTC. No reservations remain.

Actual input/output token totals are2016/1088;3072 is the cap, not usage.
Generation-call time sums32.979904s. Supervised windows sum339.980983s,
including owned cleanup but excluding outer CPU preparation/reduction and
Main audit delay. Together with SEQ098/099 fits and readouts, completed
supervised work totals1510.135936s =25.168932A40-minutes, leaving64.831068
minutes of the initial90-minute budget on that accounting. This is not full
reserved time, monetary cost, or total historical campaign compute.

Capsule `receipts_20260912/astra_fundamental_memory_terminal_20260912.tgz`,
SHA256 `a3c2bc8ba3a97a4f4b7e73f0a818f7b162872675d1fd577bc0ea4be4df5da378`,
contains native plans, calls, reductions and cleanup/release evidence. No
weights were changed; the original seed0 adapters remain on node3. Independent
numerical review is pending. Main/native61 fundamental tests passed, including
the28 new diagnostic tests; these overlapping counts are not89 tests.

No memory-readiness, parenting, H1/H2, clean-lineage, model-origin or mechanism
freeze claim follows. Keep formal C11 work deferred under Rohin's steer.
