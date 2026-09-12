# Conditional contrast amendment — advisory math review

2026-09-12. **PASS the amended construction, with the sign-language correction below.** This is advisory, not human ratification or a launch gate. Only actual local attempt2 candidate/native-interface bytes were read; no partial Bernoulli implementation or outcome scores were consulted. No GPU/model/network/Git/repository actions. Only this report written.

## Actual string check

Material: `/tmp/astra_conditional_native_preps_20260912/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material`.

- `candidate.json` SHA256: `5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c`.
- `teacher_forcing_interface.json` SHA256: `eaf287d50ffb623e6efb0fd4744c5749375061317dc0dcf1a63f64ece6407211`.
- All six material-file hashes match the local manifest. Each primary family has16 twins partitioning32 distinct dev endpoints. All64 interface contexts equal their candidate contexts; all assistant stubs are empty.

**PROSPECT belief twins: four distinct complete strings in16/16 pairs; zero cross-map swaps.** For the first twin, GOAL remains `fep`; belief changes from `dax -> fep; wug -> nup` to `dax -> nup; wug -> fep`:

| Fixed map pair | Endpoint0 target | Endpoint1 target |
|---|---|---|
| AUTH |`PREDICT: dax -> fep\nACT: dax`|`PREDICT: wug -> fep\nACT: wug`|
| DERANGED |`PREDICT: wug -> nup\nACT: wug`|`PREDICT: dax -> nup\nACT: dax`|

Here `\n` denotes the actual newline byte. Independently deriving chosen/opposite actions and their predicted consequences from each candidate's belief/goal reproduces every PROSPECT target. Action spellings swap within each pair, but the **complete AUTH and DERANGED pairs are different**; negating the AUTH contrast cannot recover the DERANGED contrast.

**REVISE outcome twins: two distinct strings in16/16 pairs, with AUTH0=DERANGED1 and AUTH1=DERANGED0.** First example: `COMPARE: MATCH\nPOLICY: KEEP\nNEXT: dax` versus `COMPARE: MISMATCH\nPOLICY: SWITCH\nNEXT: wug`. Thus two candidates still suffice; with fixed endpoint ordering, the two map-oriented REVISE contrasts are exact negatives within each state—not independent replications.

## Contrast, denominator and causal scoring

For state s and map m, freeze A=target_m(x0), B=target_m(x1), then compute:

`I[s,m] = (L_s(A|x0) − L_s(B|x0)) − (L_s(A|x1) − L_s(B|x1))`.

Evaluate the same strings at both endpoints. Report both map contrasts in **OFF, AUTH and DERANGED**, retaining all16 twin values and separate16-twin means per operation/map/state. PROSPECT's two contrasts do not make32 independent twins; REVISE's reversed sign does not double its denominator. Do not pool maps, replace the primary family with goal/prior-action twins, relabel targets at endpoint1, take absolute values or orient signs after outcomes. Any inherited mean threshold applies to its explicitly named16-twin cell.

**Required wording correction:** positive is the *desired orientation for each map's endpoint association*, not a numerical result guaranteed “by definition.” I may be positive, zero or negative in any state. Even I>0 need not mean both endpoints prefer their own target: endpoint log-odds2 and1 give I=1 while A wins at both. Retain endpoint log-odds alongside I.

L must sum causal token log-probabilities for the **entire continuation plus EOS**, excluding context loss, without length normalization. The common prefix is the unchanged rendered input plus empty assistant stub—not an answer-bearing PREDICT/COMPARE prefix. Token j is scored from its preceding causal position. Actual native concatenation IDs/boundaries must be checked; this review did not tokenize or execute forwards. Bind the expanded four-string PROSPECT registry in the amended scoring plan: the existing interface still lists only each endpoint's two own-map strings.

## Cost and interpretation

Counts are correct: PROSPECT16 twins×2 endpoints×4 strings×3 states=384 forwards; REVISE16×2×2×3=192; **576 total**, up192 (**50%**) from384. **672 generation calls remain unchanged.** Update HF cost accounting; an old384-forward forecast is not the amended workload.

Positive PROSPECT interactions for both maps can coexist, including in OFF; they demonstrate relative input-dependent likelihood shifts, not uniquely correct goal choice, high absolute sequence probability or learning caused by training. Preserve all-state comparisons and unchanged pure-generation own/opposite-map controls, validity, component/joint scores and locality/copy results. These contrasts do not replace generation controls or establish whole-loop composition. Candidate composition remains `UNTRAINED_FUTURE_ASSAY`, with zero trained chain rows and no L1 verdict. **No full L1 claim without the required composition evidence. EDIT-STOP.**
