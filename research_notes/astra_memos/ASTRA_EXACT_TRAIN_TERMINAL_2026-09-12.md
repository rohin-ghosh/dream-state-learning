# SEQ-087 — exact training prompts do not reveal usable key binding

Both roots finish their inference-only supplementary assay from immutable
source4465e537. Root1 attempt1 and root0 attempt2 each run384 generations and
384 scores over all128 actual training prompts, using OFF and the two original
adapters. No new fitting, material or threshold change.

| Root/map | Exact-training correct | OFF on same map | Original held-form correct |
|---|---:|---:|---:|
|0/W+|68/128|64/128|37/64|
|0/W-|68/128|64/128|33/64|
|1/W+|64/128|65/128|32/64|
|1/W-|63/128|63/128|34/64|

All384 generations per root are format-valid, without truncation or multiple
ACT. Plus/minus actions differ102/128 and113/128 respectively; this is not
binding. Root1W+ emits gvn128/128 times. Root0W+ emits mem2reg104 times,
root0W- emits gvn124 times, root1W- emits mem2reg113 times. OFF emits mem2reg
128/128 and127/128. Large changed-output counts mostly reflect global action
preference, not useful keyed associations. These are exact seen contexts,
not retention or generalization. Root and optimizer seed are confounded.

Native reductions replay against source/request/adapter pins. Main separately
recounts all768 generated outputs, with per-template and per-key denominators.
Both controllers are absent, all six terminal worker cleanups pass, and full
GPU0/GPU7 XML/CUDA/queue release checks pass. Runner elapsed is396.154617s
(root0) and399.416826s(root1), excluding outside verification and the failed
root0 attempt. Recorded emitted token IDs total5596 including terminal EOS;
scoring forwards and cold-start overhead are separate costs.

## Failure and next test

Root0 attempt1 failed before the first adapter load because the nvidia-smi
identity query exceeded15s. OFF256 records are preserved, not spliced into
attempt2; no adapter LOAD or output record exists in the failed stage. Owned
cleanup and later identity/free-device checks pass. One full unchanged-source
retry completes. No manual kill or unbounded retry was used.

Hilbert's implementation audit finds no concrete label-mask, optimizer-step
or row-routing bug. Epoch2 mean full-response losses0.097–0.103 are close to
an illustrative key-blind optimum0.09253: only the first divergent token
requires the association; formatting and teacher-forced suffixes do not.
This is mechanistic consistency, not final-loss decomposition or proof of
absent adapter capacity. Original masks and recipes stay unchanged.

Next selected diagnostic: separately versioned full-response versus
first-choice label-mask fits on exact root1W+ data, same initial seed,
recipe/order and256 updates. Instrument decision loss and greedy conditional
behavior; no held results select the fit. Implementation and CPU/native
preparation precede launch. No mechanism freeze, G3, parenting, H1/H2 or
campaign-completion result follows here.

## Immutable receipts

All under `receipts_20260912/`:
- root0 terminal capsule SHA256
  `7bfc98cc39fc4e98072540476c961111494815bcd517e89b2eac2bdb91cf141a`.
- root1 terminal capsule SHA256
  `2c87796110b611b07f57f2724c8de050bddd9cf316f7df0bc1c54bbc9bba72a7`.
- root0 failure capsule SHA256
  `28d518e03198bbb9b6c06cb77c0407d500b0088f1540290f4264c942d118a240`.
- combined raw-generation analysis SHA256
  `60df19e4388bd335c89c1976412cb76c09c2b7ba5ca15fe3adb8189cf795c842`.
- root0 report `4b1be70a8e2b20a23a2d76b32fb7e02564a958545b7eb8afe870e32b7e832e69`;
  root1 report `5b349b1b4742f061f0c884ef37b7c4f3478845d46b5f27424c97237d6d492fc2`.

Capture/raw-count scripts and training audit accompany the capsules.
Original weights remain untouched on node3.
