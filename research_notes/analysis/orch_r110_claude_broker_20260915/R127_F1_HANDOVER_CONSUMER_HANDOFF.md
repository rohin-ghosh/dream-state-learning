# R127: F1 broker live; compatible consumer prepared, not activated

## Authorized scope and CPU provenance

[Builder] 2026-09-15: user explicitly authorized the F1-only prospective `claude-opus-5` broker opt-in and subsequently `gpu/orch_r121_route_independent.py` consumer compatibility with dedicated tests. Requested Fable/LOW, strict default/head/A1/other branches, parent visibility, scientific prompts, child training recipe, LoRA/AdamW/RNG and counters remain unchanged. No historical MISSING replay, parent credential operation, Git mutation or forced child restart is authorized by this implementation. Main owns Git.

Broker source SHA256 `704df1d4184be7444daec4c5ccb29c65bc4969ab773d8e7cccb80f1a8011064b`; broker test SHA256 `dc3bcf3a5d7d416b42f0a2803b555ba3726ee9a7560e87edc0c94269eed07d8b`. **111 local and node5 tests PASS.** These broker bytes are unchanged from the earlier CPU-ready handoff.

Consumer source SHA256 `ecc52086ab67559aa74943f85947bb62a039af0682656745448ef4e2cdd095c2`; dedicated test SHA256 `a7d4736b75177be15a396b7a06de8a803285fc6445b6267db12821410d22bc2f`. **18 new consumer + 10 existing route + 111 broker tests PASS locally and natively**, plus validation of the actual live broker CONFIG against the candidate's source pins. Native CPU log SHA256 `66a7087db3d77f65bfc56b436905307b5283c1a346d1b52e670954bf655ecf05`.

Commands: `python3 -m unittest discover -s tests -p test_orch_r127_route_substitution.py -q`, then the same command with `test_orch_r121_route_independent.py` and `test_orch_r110_claude_broker.py`. Tests use synthetic TRAIN payloads and a mocked provider runner; no historical failed reply is revalidated or promoted.

## Actual exclusive broker handover

Idle predecessor **3825740** was checked against its full pinned identity, fenced, and retired while holding the F1 provider lock. All **85 prior claims / 170 claim files** were hash-verified unchanged after exit; no unpublished or pending request was interrupted. Old responses and archived provider failures are unchanged. Claim-tree digest `a8553c08b9ef82a9d1350a35c2aed7f07ba6f103f1a31cd3efe9e88a74681231`.

Successor **407245**, PPID **1**, start ticks `3932533`, has the explicit CLI opt-in and matching config, and owns the same single-runner queue lock. READY at **20:23:28 UTC** SHA256 `88f72329e6493e9ace959d420c0631a3e7278f21e3db7fb1192d3d8263b60254`:

- Runtime: `/localhome/local-rohing/orch_r127_f1_substitution_20260915_v1`.
- Config: runtime `/F1/CONFIG.json`, SHA256 `aa2abe0e496c5334f68ccc8c21d8108c378fd1a3814341de7dd1e66a6a0295d4`.
- Queue root: `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1`.
- Terminal remains that root's `R121_INDEPENDENT_TERMINAL.json`, with the actual original owner/writer hashes unchanged.
- Provider lock: `/tmp/orch_l2_evaluator_F1.lock`; LOW, one broker/process per branch, original caps and deadline retained.

This is **an actual deployed broker**, superseding the earlier candidate-only status. `R127_F1_POST_HANDOVER_OBSERVATION.json` supplies the latest single observation and exact genuinely new request/publication counts. No artificial probe or replay was used to obtain a first response. The pre-handover C21 Fable COMPLETE is not substitution-repair evidence.

## Consumer contract

New source is frozen separately at `/localhome/local-rohing/orch_r127_route_substitution_consumer_20260915_v2/source`. V1 candidate and all old native source bytes remain preserved. **No consumer process was launched.**

A future immutable F1 plan can opt in with this exact additional field (not written into the live plan):

```json
{
  "parent_model_substitution": {
    "allowed_models": ["claude-opus-5"],
    "broker_config": {
      "path": "/localhome/local-rohing/orch_r127_f1_substitution_20260915_v1/F1/CONFIG.json",
      "sha256": "aa2abe0e496c5334f68ccc8c21d8108c378fd1a3814341de7dd1e66a6a0295d4"
    }
  }
}
```

`parent_result` defaults remain unchanged. The opt-in requires F1/route, requested Fable, exact config/source binding, TRAIN-only request validation, native request/response equality, a single-attempt reservation charged to the new config, publication hash join, every archived file hash, exact archived REQUEST/RESULT, and reparsing actual stdout via the broker's model/plan/usage verifier. These checks apply to both Fable and Opus responses in the new epoch, so relabelling Opus as Fable cannot bypass them. Unknown and ambiguous model identities remain rejected.

COMPLETE/SILENT results retain requested/actual model, full model usage, raw/config/reservation/publication hashes, `SUBSTITUTED` and `fable_parent_claim_eligible=false` when appropriate. `poll_parents` carries these through observed/applied receipts exactly once; the existing TRIPLE path retains the full arrival. Child guidance itself is not changed or labelled. SILENT stays SILENT; historical MISSING is returned before raw reparse. The response-file-before-PUBLISHED race remains pending without blocking the child until publication appears or the original deadline expires; no retries or budget extension.

## Why the child has not been stopped

Actual actor **3356570** remains alive. At the bound 20:29 observation, C21 was complete and C22 had started without a checkpoint/COMPLETE yet. `R127_CONSUMER_V2_BOUNDARY_STATUS.json` records metadata hashes only; no sealed readout/task/output content was read.

The current independent loop **does not expose a safe continuation handshake**: it rejects an existing actor-ready marker, its initializer restores the original fork rather than the latest checkpoint, evolving replay history/parent conversation/head settings are not exported as a complete continuation state, and COMPLETE immediately advances to the next cycle. The older shared-boundary adapter requires shared-state artifacts and cannot be reused for this independent loop. The candidate's `run()` body is byte-identical to the original, not a hidden restart or birth implementation.

Therefore this is a **tested consumer candidate, not an armed or runnable same-state restart**. No child signal, stale-checkpoint restore, marker deletion, new birth, readout replay, unsafe admission or GPU launch occurred. A proper future transition must first provide an exact settled COMPLETE/readout boundary, full continuation export (LoRA, AdamW/RNG, replay history, own carry, parent history/head settings and all counters), and verified process release. Only then can the candidate become a separately pinned successor. This is a concrete missing lifecycle capability, not a request for another scientific review gate.

Until that transition exists, an Opus response may be truthfully published by the new broker but the unchanged native consumer will still reject it. **No substituted native consumption or learning success is claimed.** Recipe addendum remains parked. Head, A1 and other broker processes are untouched.

## Publication

`R127_F1_HANDOVER_CONSUMER_STAGE_READY.json` lists only owned source/tests and compact evidence. Historical candidate-only receipts remain unchanged and are superseded only by these dated handover facts. No raw prompts, provider bodies, credentials or task/answer-key content is included.
