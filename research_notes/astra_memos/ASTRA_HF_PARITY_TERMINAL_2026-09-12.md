# SEQ103 — original seed0 memory-prefix HF check

EXECUTED, native reduction/Main release complete September12,2026
19:08:53UTC. Independent raw-logit numerical review PASS. In-sample diagnostic of
the ORIGINAL SEQ098 teaching checkpoint only, not repetition checkpoints.

## Result

HF/PEFT next-token top1 is red for all16 original memory questions, matching
the existing SEQ100 vLLM first token16/16 and scoring4/16 gold colors. The
mean gold-color NLL is1.566293843; mean teacher-forced EOS NLL0.000219939.
For all16 cases, prefix-only versus teacher-forced color-position logits
match exactly in the stored float32 vectors. Maximum discrepancy between
HF's reported two-target loss and independently recomputed color/EOS mean
is5.4027543e-7. Gold-minus-red logits for incorrect colors range-1.625 to-.375;
this is not a greedy tie rescued by changing a threshold.

All saved LoRA keys/shapes/tensors match the HF-loaded state after explicitly
recorded dtype conversion; base and adapter are frozen/eval, and the full
loaded adapter state is unchanged after the32forwards. Exact original
training prefix IDs, color/EOS labels and causal positions were checked.

Therefore a vLLM-only failure is not required to explain this checkpoint's
constant red output. No prefix/teacher-forcing discrepancy appears in this
test. This does NOT certify full numerical HF/vLLM logit equivalence (vLLM
logits were not captured), explain the training failure, prove no latent
association, prove dropped labels, or rule out every capacity/optimization/
interference effect. Prior canonical-completion probability evidence is a
different interface and not directly contradictory free-generation evidence.

## Scope and evidence

Source3a12807f88747bafd0aada1d4a09ba88b915f903; node3 root
~/astra_diagnostics/astra_fundamental_hf_parity_20260912_attempt1.
PlanSHA05b6f8f906d1009977ba1439a5ca2db20036faed04ad2491e2a9a2f6ef7fd27f.
Sixteen existing exact-training-prefix cases, twoHFforwards each; no new
generation/vLLM/OFF/confirmation calls, no optimizer or weight writes.
Original SEQ100 raw responses and exact state/input bindings are reused.

Controller191049/GPU0 launched19:06:31.752UTC. Supervised worker64.699761s;
full reservation141.936394s includes Main audit delay. Full release verified,
no other process disturbed. Initial scout/parity budget90A40min retained;
098–101 plus this worker is54.874483supervisedA40min. Separate continuation
budget is not included. No active-compute or monetary-cost inference.

Capsule receipts_20260912/astra_fundamental_hf_parity_terminal_20260912.tgz,
SHA54ec0bf1613e67d6256062a24e1ed30fe2b49bfa73a5675d1b83c0b9d4653e32.
All48files, including raw full-vocabulary float32 vectors, retained. Loaded
tensor inventories, original request/response copies, cleanup, reduction and
Main summary are included. Model/adapter weights remain at their original
node3 paths, unchanged. Scripts/tests/handoff archived in receipts_20260912.
Model origin stays UNRESOLVED_LOCAL_HASHES_ONLY; no finalC11 or memorygate.
