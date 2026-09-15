# Existing F1/F3 refusal metadata — 2026-09-15 20:36 UTC

Read-only bounded capture audit; no provider probe, retry, model-fallback dispatch, credentials, process/config/source change or guidance adaptation. Raw stdout/stderr remains node-local. This report supplements, never rewrites, old MISSING claims.

## Exact confirmed F3 category

Among the **latest 100 of 200 eligible finalized F3 response files** in the preceding two hours, **28** have this same captured envelope shape:

```json
{"type":"result","subtype":"success","is_error":true,"num_turns":1,"stop_reason":"refusal"}
```

The literal **`reasoning_extraction`** and safeguard wording occur in the `result` **string**, not a structured `error.code` field. All 28 remain broker `MISSING` with `error={"type":"ValueError","code":"provider_exit_failure"}`. CLI exit is **1**, with no cleanup termination; actual raw model usage lists Fable plus Haiku. They are **explicit safeguard refusals**, not ordinary model-identity mismatch, OAuth unavailability, or timeout. The provider `subtype="success"` is not guidance acceptance when `is_error=true` and `stop_reason="refusal"`.

Observed refusal finishes span **20:21:46.977–20:36:24.280 UTC**, `C069_E0_OPEN_PARENT` through `C074_META_PARENT`; CLI durations **2.95–6.10 seconds**. Example latest response SHA256 `0663a6d17f6c48b310ca5eb3b71e0901cbe17309ef292eaeb16a2fbcd47329e9`. All response/stdout/stderr/CLI references are in the compact JSON. No refusal body is reproduced or converted to a plan.

The selected 100 F3 captures contain 71 COMPLETE, 28 explicit-refusal MISSING, and one separate actual-model-rejection MISSING. This bounded selection is **not** the full two-hour delivery rate. F3 broker **4101015** remains alive with an **empty substitution allowlist**.

## F1 is distinct in inspected captures

All **13 eligible F1 captures** in the preceding two-hour selection contain six COMPLETE, five old actual-Opus identity rejections, and two guidance-cap failures. **No explicit reasoning_extraction marker was found in these F1 captures.** The five Opus envelopes have CLI exit0, `is_error=false`, `stop_reason="end_turn"`; they are not established safeguard refusals. Their old MISSING verdicts remain unchanged and are not revalidated as guidance. This does not refute a notice about different/uninspected F1 captures.

F1 broker **407245** remains alive, with requested Fable/LOW and the already-authorized F1-only actual-Opus opt-in. It performs no second-model request or automatic retry. The first genuinely new post-handover request **`000086_F1_C0023`** finished COMPLETE at **20:33:45.906 UTC**, **actual Fable**, `REQUESTED_MODEL` attribution. Native observation was COMPLETE at **20:33:55.310 UTC**; response SHA256 `1272f2304e3fb1db3a6b15033ede60f8af5aaa03b7a8d1886b15d86e17c85d7a`, observation SHA256 `26a063424879bc1b1ea2c30a8f3233c57f749e2c4905f01da05c60b1fcaf36ea`. This proves a post-handover Fable publication/native observation, **not** substituted delivery or completed-child guidance application.

Consumer **3356570** remains on original frozen source `d1b0de12edc1ad45bbc1b3d20def7f0084198310ef0a7c9ee2db3f6bc6095673`. The tested compatible candidate `ecc52086ab67559aa74943f85947bb62a039af0682656745448ef4e2cdd095c2` is still **unarmed**, with no safe independent full-state resume handshake. No child stop/reset occurred. The old consumer's native observation omits the new model-attribution field; it must not be treated as full substituted-consumer adoption.

## Boundaries retained

No automatic retry/fallback on safeguard refusal, no F3 allowlist extension, no head change, no prompt alteration or refusal relabel. Genuine already-served model substitutions and refusal envelopes remain separate categories. R124 transport caps/no-cropping rules and historical claims remain intact. Main alone owns publication/Git. Exact compact publication files: this Markdown and `R127_REFUSAL_METADATA_2036.json`.
