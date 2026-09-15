# R118 A2 delivery repair and math shared-client publication

## Actual migration

Old A2 Astra broker833114 was released at a verified completed-call boundary. All13 charged claims had immutable published responses and reverified native archives:9COMPLETE,3MISSING,1SILENT. No native/Fable process was signalled, no charged call was retried, no config/GO/counter reset. New broker974244 runs the prospective R118 source. Its initial launch sampled empty argv during exec; STARTUP_VERIFIED preserves the later exact module/PID/start/UID/command hash instead of hiding that sampling gap.

Four common direct-HTTP slots replace only this prospective broker's old CLI lock. The existing1GiB floor is checked after slot admission, with one HTTP attempt, no retry, same cutoffs/caps/prompts/model verification. The shared helper is Main-owned and unchanged. HTTP slot/wait/attempt records are archived on-node with every result. The old frozen broker/native sources remain unchanged.

First actual slot-backed attempt C003_E0_open_turn used slot1 with0.000114s queue wait and one HTTP attempt, cli_lock_used=false. It timed out at the existing cutoff and is MISSING, not retried. FIRST_HTTP_ATTEMPT.json is the dated receipt; it is NOT a successful-delivery claim.

Authoritative first original A2 COMPLETE:11:05:56.999UTC, actual openai/openai/gpt-6-astra; native delivery11:06:32.889UTC; following child363tokens/EOS11:06:43.960UTC. Actual parent guidance was verified in the child's causal messages, but semantic uptake remains unaudited. Exact source paths/hashes are in MIGRATION.json. All raw transcripts remain node-local, with bounded temporary VM buffering until verified archival.

## Math shared-client specs

Post-migration success now verified separately in DELIVERY_STATUS_1132.json: C003_E1_experience actual Astra COMPLETE11:32:08.090533UTC, native-delivered COMPLETE11:32:47.229776UTC, slot0/one HTTP attempt/no CLI lock; all archive hashes reverified. This is a NEW source request, not a retry of the first timeout. At11:32:47.252UTC published totals were10COMPLETE/4MISSING/1SILENT; native-consumed totals9COMPLETE/5MISSING/1SILENT. The discrepancy is the pre-migration C002_E1_presleep_metacognition response: provider COMPLETE but native lane_wait_expired. Both records are preserved; do not collapse provider completion into successful child delivery.

SHARED_CLIENT_READY.json provides exact registered F2 lane1 / A2 lane5 roots and86 authorized TRAIN IDs for the existing43-cycle bound. It separately preserves all192 source-pool IDs for exclusion/provenance; those are not permission for additional cycles. Native TRAIN manifest SHA8fdff9a6ba6f697a91bf5357783c46a353406aa0cff7fc8b03f2ebc4b13b5b4b unchanged. No questions, answers or sealed readouts are exported.

The R117 CPU client captures shared_generation:int and shared_checkpoint_sha256:str before dispatch, exports every six-call two-episode TRAIN cycle with canonical replay_row, and reloads only a genuinely published shared LoRA. F1 alone initializes/owns the optimizer. No shared initialization is done here; the resident/readout successor boundary remains pending. HTTP delivery repair is independent and already deployed. Current math natives remain frozen BASE elicitation-only, not weight-learning lanes.

## Publication

Own broker/migration/tests pass16 CPU tests including the Main five-slot tests in the actual frozen runtime. STAGE_PATHS.txt is the explicit own-source/tests/journal/compact-only allowlist. Do not stage Main's slot helper or coordinator as this worker's edits. Runtime roots/configs/identities and source hashes are recorded in MIGRATION.json; no raw archives, credentials, checkpoint files or Git mutations.
