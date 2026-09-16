# F1 attempt3: ready, not launched

Non-material repair of the saved-C55 process handoff. No new retirement/release is needed. `attempt3/RELEASED.json` reuses the original immutable `attempt2/RELEASED.json` by symlink; stage2 and its failed R139 ready/launch/log/plan/history remain untouched.

## Actual charge proof

Cycle56 has exactly `START.json` and `EPISODE_0.json`, zero `CALL_*` and **zero charged native/parent/readout calls after C55**. The ledger is still3175 rows, SHA `cc6e032e5b7ee569e6d841c77fb9a0e1fa4c6f32097de5b791f900a72d689ae1`; all200 original preserved hashes match. The episode's `actor_calls=1` means one metadata capture, not a charged model call: turn0 has no response/command/reads/routes, only the original `TimeoutError/owned_lifetime_signal`. A no-dispatch CPU callback reconstructs the entire episode metadata identically from the frozen cohort and episode code. No extra parent application exists outside the saved boundary.

Original actor3356570 and failed successor2608951/timeout2608950 are absent. The repair adopts only those two exact-hash metadata files. New actual episode output is `cycle_0056/EPISODE_0_R139B.json`; its obstacle provenance points to that same new file. Original `EPISODE_0.json` is never overwritten or treated as a completed interaction. Any actual charge, response, action, extra file, parent-context change, or hash mismatch blocks repair.

## Frozen source and evidence

- `gpu/orch_r139_route_resume_repair.py`: `77894fad3b736a05536e26119dee946674bd3c688d1b4db82b448a43a80b9057`.
- `gpu/orch_r139_route_resume_broker.py`: `3a43f81ca0a48026604f60c6b836dd5b2d9273d164e83fc1a84a7698d01d3154`.
- Local22 PASS; original native venv22 PASS; actual native CPU preparation/check PASS; staged broker observer imports successfully without dispatch.
- Node stage `/localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt3`, source `handoff.py`.
- READY SHA `f85c48d1d637acae9ebd425a27102990561156d6cefef82c5eea7fb4ae594c80`.
- Attempt3 boundary SHA `47b26eb5b0a2eed44a940e4bf8ae7b26da8eff1eaaa380d9c9b99ded1d41355c`; exact original C55 state/context, with additional failure-metadata preservation bindings.
- Controller source `/data/home/rohing/courier/runtime/r139_f1_repair_source_20260916_attempt3`; manifest `bc3fe8880f587e1e30f42c001c4778c9a48ff8784c2732df08b87dd660c95c07`.

No source-policy, provider, optimizer, RNG, carry, history, parent-context or budget change. The original frozen attempt2 resume/guard is reused with narrow source substitutions: R139B ready/inventory names, exact two-file START adoption, and a separate path for the new episode record. The original old-source pins, privileged GPU admission and no-reset restoration remain mandatory.

```bash
python3 -B -m unittest discover -s tests -p 'test_orch_r139_route_resume_*.py' -q
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt3/handoff.py check'
```

## Main-only publication and native command

Main publishes the exact files, then creates **new stage3** `GO.json` from its `GO_TEMPLATE.json`: `authorized=true`, actual `published_commit`, retain the exact READY digest and `logical_life_reset=false`; choose a current bounded expiry no later than the original hard wall. Do not edit stage2 GO, source, release, or boundary. Do not rerun stage3 preparation or overwrite any stage3 artifact.

Main-only supervisor command (reuses release; sends no retirement signal; privileged admission precedes the new actor):

```bash
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 nohup /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt3/handoff.py supervise --stage /localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt3 --python /localhome/local-rohing/v2/venv/bin/python > /localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt3/SUPERVISOR.log 2>&1 < /dev/null &'
```

The actual actor runs **attempt3/handoff.py resume**. Require root `R139B_INDEPENDENT_ACTOR_READY.json`, not the failed R139 receipt. The separate `R139B_INDEPENDENT_ANCHOR_INVENTORY.json` also avoids collision. `ADOPTED_UNCHARGED_START.json` records adoption without changing the original START. First newly charged native call should be cycle56 and retain saved C55 adapter/AdamW/CPU+CUDA RNG/history/parent context.

## Main-only broker observer/dispatch command

The old dispatcher2147783 is not reused. The new wrapper keeps the existing F1 prospective broker's provider/effort/budget/timeout/parser and historical-request gates unchanged, but both wait and validation target **attempt3 + R139B**. It verifies the actual resumed actor command/start identity and saved checkpoint, not file existence alone. Its source pins include the original frozen broker wrapper as well as the new wrapper. It may be armed before native readiness; it does not prepare or call the provider until actual R139B readiness appears.

Use Main's existing authorized provider environment. The repository argument deliberately retains the original authorized wrapper/hosts context; staged source has no credential files. Substitute Main's actual published commit. The `--directory` below must not already exist; do not pre-create it.

```bash
CUDA_VISIBLE_DEVICES= PYTHONPATH=/data/home/rohing/courier/runtime/r139_f1_repair_source_20260916_attempt3 nohup python3 -B /data/home/rohing/courier/runtime/r139_f1_repair_source_20260916_attempt3/gpu/orch_r139_route_resume_broker.py dispatch --directory /data/home/rohing/courier/runtime/r139_f1_repair_broker_20260916_attempt3 --repository /data/home/rohing/dream-state-orch --published-commit MAIN_PUBLISHED_COMMIT --wait-until "$(python3 -c 'import time; print(time.time()+1800)')" > /data/home/rohing/courier/runtime/r139_f1_repair_source_20260916_attempt3/DISPATCH.log 2>&1 < /dev/null &
```

Verify the dispatcher’s new PID, actual R139B actor/checkpoint binding, and first naturally generated post-C55 request. Historical refusals/MISSING requests remain excluded. Do not manually resend the old request or reuse any previous claim. No launches, signals, GPU/model/provider calls, Git/shared-ledger changes or changes to F2/F4 were performed in preparing this repair.
