# Mini-Sudoku behavior-material positive-control audit

**Verdict: NO-GO for either fit on the reviewed bytes.** The material contrast
is scientifically useful, but the present execution does not yet prove that
training and evaluation condition on the same first-chunk tokens, has no
prospective base/headroom or success decision, and does not make the reducer
verify the material -> fit -> adapter -> probe chain. Repair those seams before
spending the two 96-step fits. This is an engineering behavior positive control,
not parenting, child-authored compilation, clean lineage, or H1/H2 evidence.

Reviewed the tracked material/launcher bytes through `40c7d4c3` plus the
read-only pending reducer copy. Relevant SHA-256s:

- `mini_sudoku_behavior_material.py` `0ba6ac4f6f05dfa374f2e127c4e7c3c29d03a74f33ff918255b40692d8f922b0`
- pending `mini_sudoku_behavior_analysis.py` `03e92393da8606ebba7117ae60ed636e8f5a780937b0d248792b7c30b37d484b`
- tracked `astra_mini_sudoku_diagnostic.py` `2ad427002e74bfe2a8687032a3e8a6f066824649be8d2d2ae0481c009fd5ccd7`
- material test `918d7706...`, pending analysis test `cf465bc4...`, and
  tracked launcher test `92a0e85b...`

Attempt 2 is terminal infrastructure evidence, not a scientific result. Both
arms launched on GPUs 1/3 but the bound trainer argv selected
`/usr/bin/python3.12`, which lacks Torch, so both failed before optimizer step
1; owned-process/GPU cleanup was verified. No adapter, OFF/ON comparison, or
behavior result exists from that attempt.

## What is already valid

The 32 useful and 32 cyclic-wrong rows share the same prompts and exact target
text/token multiset. Every useful target is an independently row/column/box and
givens-valid canonical answer. Every cyclic target is accepted only when its
native score is below 1 and it violates at least one recipient given. Thus the
contrast is correctly described as **correct prompt-answer binding versus a
structured wrong-board permutation**, not a neutral or information-identical
control. Both arms still teach the same output vocabulary, ACT marker, valid
Sudoku-grid marginal, and formatting; that is a feature of this narrow test.

The current first-ACT reducer also does the important thing: it takes the first
authoritative ledger `act`, zero-fills a missing/unmeasured/invalid first ACT,
and does not substitute a later correct ACT or `native_best`. Existing fixtures
cover missing, empty, invalid-feedback, multi-ACT, episode-join, source/custody,
and changed-seed failures.

There is **no trailing-newline mismatch in these exact bytes**. The material
code renders `apply_chat_template(raw_prompt_with_trailing_newline)` itself,
stores that rendered string as the masked context, and invokes V3 with
`chat_template=False`. Therefore V3's separate chat-mode `.rstrip("\n")` path
is bypassed. The synthetic test explicitly distinguishes stripped and
unstripped renderings. This correction must not be regressed into
`chat_template=True` without changing the prompt contract.

## Fit-blocking corrections

1. **Bind and preflight the actual training interpreter/environment.** The
   preparation accepts an interpreter and freezes it into
   `trainer_commands.json`, but the launcher checks only cwd and adapter
   absence before executing that argv. Attempt 2 therefore used the wrong
   system Python even though its controller ran in the working node venv.
   Require the resolved trainer executable to equal the prospectively declared
   node venv executable, then run a CUDA-hidden subprocess preflight through
   that exact executable importing Torch, PEFT and Transformers and recording
   Python/package versions and the native-build prerequisite. The execution
   receipt must repeat the interpreter identity before optimizer start. A
   repair is a fresh attempt; attempt 2 remains a zero-step infrastructure
   failure.

2. **Make the CLOCK deterministic in both producer and evaluator.**
   `one_tick_prompt` currently constructs a real driver and preserves elapsed
   wall time; its own test demonstrates `alive 2s` is possible. The later
   neutral probe independently reconstructs the prompt and neither the runner
   nor reducer compares it with the stored source-map prompt. A usual immediate
   call will often say `alive 0s`, but that is scheduling luck, not identity.
   Use one shared pure first-chunk renderer with a frozen literal clock (for
   example `alive 0s`) in both material preparation and evaluation, or make the
   evaluator consume the stored frozen prompt after checking its board binding.
   Do not merely sample the real clock twice. Record and require all 48 raw
   prompt hashes.

3. **Bind actual inference prefix tokens before fitting.** The present CPU
   preflight proves HF-tokenizer IDs for the stored, pre-rendered trainer span;
   it does not prove the IDs vLLM actually submits during generation. On the
   pinned local tokenizer, for all 48 rows require:

   - shared renderer raw user bytes equal the stored `q` bytes;
   - HF and vLLM chat-template strings are byte-equal, with exactly the intended
     trailing-newline policy;
   - HF IDs, vLLM tokenizer IDs, and the actual vLLM request/returned
     `prompt_token_ids` are exactly equal;
   - those IDs equal the V3 masked context prefix; target IDs are all supervised
     exactly once plus EOS; no context/target token is dropped.

   Emit a hash and length for every ID vector. Prefer passing the verified token
   IDs into generation; otherwise retain vLLM's actual prompt-token IDs. Any
   difference is a pre-fit stop, not a limitation to disclose afterward.

4. **Run a base-only pre-fit gate on the fixed 16 boards.** Use the exact future
   prompt/token path, one tick, same output cap, decoding settings and seeds,
   before either optimizer runs. Require 16/16 terminal rows, an ACT marker in
   at least 12/16 (interface floor), at most 4/16 first-ACT exact solves and a
   zero-filled mean native first-ACT score at most 0.35 (headroom). Missing or
   malformed ACT remains zero. If the floor fails, repair prompt/parser; if the
   ceiling fails, select a prospectively harder board set/prompt before fitting.
   The already examined native P0 sample had 0/9 exact first-ACT solves, so this
   gate is expected to be cheap and informative rather than prohibitive.

5. **Predeclare the positive-control decision.** On the same 16 boards, call a
   seed-0 engineering positive-control pass only if all are true:

   - useful ON first-ACT exact solves are at least 12/16;
   - useful ON exceeds the common OFF solve count by at least 8/16;
   - useful ON exceeds corrupt ON solve count by at least 8/16;
   - useful-minus-OFF and useful-minus-corrupt zero-filled mean native
     first-ACT scores are each at least +0.40;
   - useful ON has a measured first ACT on at least 15/16, with no missing cell,
     truncation, nonfinite score, or custody failure.

   `native_best` and total ACT count remain secondary diagnostics. Do not rescue
   a failed first-ACT gate with later ACTs, continuous partial credit, or a
   threshold chosen after seeing the panel. One optimizer seed supports only
   this bounded engineering instance; a reliability/material-effect claim needs
   prospectively repeated optimizer seeds (the prepared seeds 1 and 2 are
   sufficient as the next panel).

6. **Bind the causal labels to actual adapters.** The analysis currently accepts
   two pair roots by the caller's names. It does not consume the material
   manifest or training manifests and cannot prove that `useful/on` loaded the
   useful-corpus adapter (or that `corrupt/on` loaded the corrupt one). For each
   arm, write and hash-bind one receipt containing material-manifest hash,
   corpus hash, base inventory, exact trainer config, train-manifest hash,
   adapter file hashes, device, and completed step/token counts. Put that receipt
   hash in the probe specification/PAIR_STARTED record and require it in the
   reducer. The reducer must reject swapped adapters or corpus/adapter mismatch.

7. **Remove the arm-by-device confound.** The launcher permits devices 1 and 3;
   one useful fit on one GPU and one corrupt fit on the other would perfectly
   confound material with hardware/runtime at the only optimizer seed. The
   smallest valid run is one reserved GPU, fresh base per fit, useful and corrupt
   fits sequentially, and fresh-process common OFF/useful ON/corrupt ON probes on
   that same GPU. Alternatively cross the arms over both devices. If two OFF
   replicas are retained, require their per-board first-ACT results to be exactly
   equal before using an adjusted contrast; otherwise use one prospectively
   shared OFF and mark stochastic instability.

8. **Prove unique solutions independently.** Reasoning-gym 0.1.25 attempts to
   generate unique puzzles, but this preparation only validates the reference
   grid. Its scorer awards 1 only to the stored reference and partial token-match
   credit otherwise; it does not accept arbitrary constraint-valid alternatives.
   Enumerate all completions for each of the 48 puzzles in CPU preflight and
   require exactly one, byte-equal to the reference. An ambiguous fixture must
   fail. Then `first_act_solved == (native score == 1)` is a defensible valid-board
   endpoint. Also report first-ACT marker presence, strict 4x4 parse, givens
   consistency, and Sudoku validity separately from partial native score.

## Desirable, not fit-blocking

- Four held-out puzzle boards have solution grids that also occur in training.
  This is disclosed and does not favor useful over corrupt because both arms
  have the exact same target-grid multiset. Removing that overlap would make the
  held-out-generalization story cleaner, but puzzle/givens identities are already
  disjoint and this remains a valid matched material diagnostic.
- Temperature 0 would make this tiny panel cheaper to interpret. Native 0.7 with
  prospectively identical per-board seeds is acceptable for the engineering
  control, provided actual temperature is included in the cross-pair equality
  check. The reducer should also compare source identity/temperature,
  `total_token_budget`, `max_episodes`, and any generation finish/truncation
  metadata, not only its current `MATCH_FIELDS`.
- The target begins directly with `ACT:` although the bootstrap asks the child
  to predict first. That narrows the claim to direct first-action supervised
  behavior. Adding a matched `PREDICT: 1.0` line would be more native but is not
  needed for the useful-versus-cyclic semantic contrast.

**Smallest release sequence:** exact-venv import/native-build gate -> CPU
uniqueness/corruption/real-token tests ->
16-request common-OFF prompt/headroom/token receipt -> two sequential 96-step
rank-8 fits on one GPU -> 32 ON requests in fresh processes -> custody-bound CPU
reduction against the frozen decision above. No parenting, full-life, or neutral
competency runner is needed to answer this narrow question.
