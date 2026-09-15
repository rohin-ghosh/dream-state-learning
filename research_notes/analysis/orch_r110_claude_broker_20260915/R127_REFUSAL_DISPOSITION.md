# Refusals and substitutions are different outcomes

## Superseding disposition — September 15, 2026, 20:55 UTC

The prospective safeguard-motivated model switch described below is withdrawn before activation. Do not automatically retry refused inputs, or route subsequent instances of the same blocked workflow to another model to avoid the safeguard. No prompt obfuscation, credential changes, or diagnostic provider probes are authorized. The head-parent configuration is unchanged.

Preserve refusal envelopes, original request identity, charges and MISSING outcomes. A successful provider-served envelope is a distinct accounting observation, not proof that a refused request was usable or that the learner consumed it. Any existing successful substitution receipts keep their original model attribution; this update does not relabel historical evidence.

The scoped non-material repair is explicit rejection of `stop_reason="refusal"`, even if other envelope fields misleadingly indicate success. Regression tests must establish that identity aliases or a substitute-model allowlist cannot turn refusal text into child-facing guidance. No new model configuration or GPU launch is part of that repair. The earlier prospective-model-choice section is retained below as superseded history, not operating authorization.

September 15, 2026. This disposition uses existing captures only; no diagnostic provider calls were made.

## Verified distinction

- F3: 28 of the latest 100 inspected captures have `is_error=true`, `stop_reason="refusal"`, `num_turns=1`, CLI exit 1, despite the envelope also saying `subtype="success"`. The string `reasoning_extraction` occurs in the result text, not a structured error-code field. They remain MISSING, not guidance, timeouts or usable substitutions.
- F1: none of 13 inspected captures has that explicit marker. Five old Opus identity failures instead have `is_error=false`, normal end-of-turn and exit 0. Successful provider-served substitutions and explicit refusals must not be merged into one measured failure category. A common upstream cause is not established by these envelope checks.
- F1's first new post-handover C23 reply was actual Fable: delivered 20:33:45 UTC, native-observed COMPLETE 20:33:55. This is neither a retry nor consumed Opus guidance.
- The two recovered older CODE brokers have six sampled exit-1 failures naming the same refusal category, not a demonstrated packaging defect. One distinct later a40r_5 request succeeded on Fable at 20:31:39 and was consumed in `C070_E1_segment1`; ovx2_5 still had no COMPLETE at its 20:37 snapshot.

Exact metadata: `R127_REFUSAL_METADATA_2036.json` and the R128 exit-diagnosis receipts in `research_notes/analysis/orch_r118_code_parallel_20260915_attempt1/`. Raw stdout remains node-local.

## Prospective model-choice scope

The recorded provider message explicitly offers selecting another model. Under the user's requested model-choice change, the next candidate is a **separately declared Opus sub-parent configuration for fresh scheduled requests**, with consumer compatibility verified before claiming usable delivery. It is not an automatic replay of safeguard-refused inputs. No prompt rephrasing, safeguard disabling, credential changes, refusal relabeling or extra diagnostic model calls are authorized by this disposition.

Record nominal experiment model, effective requested model, actual served model and SUBSTITUTED/non-Fable eligibility explicitly. The head parent remains Fable-strict. Refused calls retain their original charges and MISSING outcomes. A valid already-served Opus envelope must pass raw/config/request/consumer binding; error envelopes never become guidance merely because their modelUsage names an allowed model.

At this disposition, F1 broker replacement is live, but its compatible consumer candidate is **not armed**: the existing actor lacks a safe continuation handshake and must not be reset to its original fork. The F3 prospective configuration is under compatibility work; no live switch or successful Opus consumption is claimed. Current child work continues without waiting for that preparation.
