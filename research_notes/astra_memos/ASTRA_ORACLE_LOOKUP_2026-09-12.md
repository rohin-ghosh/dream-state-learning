# Single-row oracle diagnostic — September 12, 2026

**Completed; external frozen replay exit0; no writer qualification.**
Source35ba8f2c983d9baa99ece979183dceffd3e4e344, node3GPU1,
`~/astra_diagnostics/astra_oracle_lookup_20260912_attempt1`.

The64 new requests retained the calibrated chat/explicit-format instruction,
question, strict parser and32token cap. Each received exactly the existing table
row selected by its tool/mode key. Selection used no generated outcome.

| Condition | Correct / 64 | Valid / 64 | Truncated | Multiple ACT |
| --- | ---: | ---: | ---: | ---: |
| Historical full-table chat/explicit baseline | 45 | 61 | 0 | 0 |
| Single relevant row | 32 | 58 | 0 | 0 |

Every new root/map cell has8/16 correct. Raw outputs are exactly58 instances of
`ACT: a1` and six of `ACT: a`. The latter end without a valid action; they are
not token-cap truncations. This does not support the hoped-for explanation that
removing irrelevant table rows alone repairs the positive control. It is not
evidence about parameter writing, since no adapter was loaded or trained.
The comparison reuses the historical baseline, not a concurrent rerun; all data
are already-inspected development items, not independent learner replicates.

Reserved elapsed time67.62631254799999seconds =0.018785086818888887A40-hours.
Archive `receipts_20260912/astra_oracle_lookup_terminal_20260912.tgz`, SHA256
`2d03417687053731d542f03987c76e8d5bb1b988edbb37091da73bc219dd2b0c`,99395bytes.
All86archived payload hashes verified;72sealed run files, four source bindings
and the external worker log match. Raw requests/token IDs/output bytes, seals,
resource receipt, external logs, frozen source, exact replay and analysis script
are bundled. Report SHA256
`aa805fe7a15cecc3ec2b99c0cb9faf4477ad414446d3013c20109f091971a241`.
Dependencies: retained local-only model/runtime and the original calibration
capsule46815dde46a3b50c037905c7cda8eb12893bdd1032b75f2d59b608aea8eb7412;
model weights are not bundled or newly authenticated.

One final predeclared follow-up adds an explicit instruction to use the table
as the source of truth and copy the action for the exact tool/mode. Everything
else in the single-row condition remains unchanged. This tests a task-instruction
ambiguity, not a new writer recipe. Compare against the actual single-row result
above; the full-table comparison changes two factors and is not that contrast.
After this bounded64request check, park further prompt search and prioritize
the active lesson/sham material-to-write path. Old runs are never resealed or
reclassified, and the existing W0 oracle threshold remains unchanged.
