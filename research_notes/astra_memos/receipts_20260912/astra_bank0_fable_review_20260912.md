# Fable bank0 independent review — 2026-09-12

Started UTC: 2026-09-12T07:33:20.152267+00:00

Invocation: `claude -p --model claude-fable-5-1 --output-format text --restricted --tools "" --strict-mcp-config --no-session-persistence` with self-contained evidence supplied on stdin. No permission bypass. Tools and MCP unavailable to reviewer.

Prompt SHA256: `ed73ec971d2cdeb3983f8cece0913542fdc0a51ce29cd9bf33705cfde82cb815`; prompt bytes: 135302. Includes complete captured analysis/receipt/wrapper/analysis source, historical G9/metric/bootstrap definitions, four archived queue commands, and all raw frame/control cue projections.

CLI exit status: 0

## Reviewer stdout

# Independent review: bank0 G9_frame_binding diagnostic bundle (2026-09-12)

**Verdict.** The four recorded G9_frame_binding failures stand as computed under the frozen definition. The arithmetic I could check by hand matches analysis.json. However, three of the four failures are driven almost entirely by the spill term, and the spill term as defined measures a marginal colour-distribution shift rather than leakage of the owner's colour. The fourth failure (F seed 3) reflects a degenerate fit, not a binding outcome. These flags should be recorded as "gate fails" with the two caveats below, not as evidence that binding is absent or that spill is present. No pooling, no between-family comparison, no H1/H2 claim is supported, and none is made.

## Direct arithmetic I checked (by hand, from the raw projections)

- **F seed 2 dose16 frame mass_on.** Sum of the 16 ON masses gives a mean of 0.99815843, matching the reported 0.99815843125.
- **F seed 2 dose16 frame mass_off.** Sum of the 16 OFF masses is 0.1398025, mean 0.00873765625, exact match.
- **OFF invariance across seeds.** Both F fits report identical conditional_p_off and mass_off for all three kinds, as do both CF fits. Correct, since OFF does not depend on the adapter.
- **Mass equals candidate sum.** For U2T5 ON the four p_raw values sum to 0.9982105, equal to the recorded mass at seven decimals. So the conditional P in the dose16 table and p_norm in cue_metrics coincide up to serialization rounding, as the candidate interpretation states.
- **Spot log-odds gains.** F seed 2 owner V7F9: owner d_logodds about +0.38, look-alike about -1.94, gain about +2.31. CF seed 0 owner P8G7: owner about +4.95, look-alike about -2.17, gain about +7.1. Both are consistent with the reported means (1.92 and 2.45) but I did not compute all 16 gains per fit or the 2000-draw bootstrap.

Not executed: full 16-owner means for conditional P, full spill strata means, the bootstrap intervals, the SHA checks. I accept the builder's statement that an independent stdlib implementation matched those, but I did not reproduce them.

## Findings, severity ranked, with smallest corrective action

**1. The spill metric is dominated by removal of the base model's red bias, not by owner-colour leakage (high, interpretive).** Under OFF the base model puts roughly 50 to 65 percent of normalized candidate mass on "red" for every frame, exposed or not (for example U2T5 OFF normalized red is about 0.62). Every trained adapter moves that mass elsewhere on every frame. Spill uses |d_p_norm| on the owner's colour, so for a red-target owner the look-alike control registers a spill of about 0.5 purely because ON no longer favours red. For non-red owners the reverse happens when ON adopts a new default (F seed 2 ON favours "white" broadly). A spill of 0.03 therefore cannot be met by any adapter that changes the marginal colour prior at all, independent of whether owner-specific binding exists. This is a property of the frozen definition, not a computation error. Smallest corrective: leave the gate and threshold untouched, and add to the memo a descriptive breakdown of signed d_p_norm on control frames split by owner colour, plus the control frame's shift toward the owner's colour relative to its shift toward the other three colours. That is a report-only addition and does not require a new gate or a re-fit.

**2. F seed 3 is a collapsed adapter and its CI result is not binding evidence (high).** Every ON distribution in the seed 3 eval, across all 160 frame rows and all doses, is approximately [0.045, 0.095, 0.24, 0.60] on [red, blue, green, white], regardless of owner or target. Conditional P ON for owners (0.2575) equals the OFF value (0.2596) to within noise, and the paired gain mean is 0.0037. This is an adapter that learned a fixed output. The failure of "CI lower > 0" for this fit is a fit-quality failure. Smallest corrective: mark F seed 3 as degenerate in the memo and check its train_meta loss curve and any validation loss before treating it as an evaluation. Also note that seeds 2 and 3 of the same source cell diverge completely, so two fits per cell cannot characterize optimizer-seed variance, and the missing F seed 0/1 reference fits matter.

**3. The bicycle control tracks the owner frame almost exactly (medium, interpretive).** In F seed 2 and both CF fits, the bicycle frame's ON distribution is nearly identical to the owner frame's (V7F9: owner red 0.806, bicycle red 0.742; P8G7: 0.938 versus 0.905). This means the adapter associates the colour with the owner's identity token, not with the owner-plus-object frame. Under the definition this is spill, but it is a different phenomenon from look-alike leakage and should be described as name-level association. No corrective beyond stating this distinction; spill_parts already separates the strata.

**4. High conditional P ON is not selectivity (medium, already acknowledged).** F seed 2 conditional P ON for owners is 0.685, but for bicycles 0.669 and for unseen look-alikes 0.401 (well above the OFF 0.25). The look-alike difference is real in log-odds terms but the absolute level shows broad colour induction. The candidate interpretation states this correctly.

**5. Unexplained "attempt2" suffix on both CF runs (medium, lineage).** The job files show only attempt2 for CF seeds 0 and 1. Attempt 1 records, and the reason for re-queueing, are absent from the bundle. Smallest corrective: attach the attempt 1 queue log or failure reason so the lineage is complete.

**6. Only bank0 of F_BANKS "0 1 2" is present (low, expected).** The job commands request three banks; the bundle holds bank0 only, consistent with a 07:18 snapshot of in-progress runs. Not a defect, but banks 1 and 2 must be analyzed separately and never pooled with bank0.

**7. Bootstrap convention (low).** With 2000 draws the code uses sorted-means indices 50 and 1950. That is the historical percentile convention and is deterministic under random.Random(0). For n=16 the percentile interval is slightly liberal, but for F seed 2 and both CF fits the lower bound exceeds 1.2, far from zero, so the convention does not change any flag. No change recommended.

## Source-command lineage

The four job files reference the frozen source at f2e5b65e, matching the stated experiment source. F fits ran memory_dose_frames.sh with both F_CELLS and CF_CELLS set to F_r16k16 and a 25 minute cap; CF fits ran memory_dose_childframes.sh with CF_CELLS only and a 35 minute cap. The analysis receipt argv matches run_analysis.sh, exit code 0, empty stderr. The receipt-versus-eval hash checks are implemented in the analysis code but I did not verify the hashes themselves.

## Evidence limits

- Four fits, two per source cell, on two distinct hashed bank0 instances (S1 seed 1 and D32 seed 0). Not replicates, not a controlled F versus CF comparison.
- Synthetic researcher-planted HFScorer data. No clean-lineage eligibility.
- The G9 spill gate as frozen cannot be passed by any adapter that shifts the marginal colour prior. Every future "spill fail" under this definition should carry that caveat until a descriptive signed breakdown is reported alongside it.
- No statement here about G9_mass, G10, G11, stage completion, retention, or any hypothesis verdict.
