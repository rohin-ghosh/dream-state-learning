# Relay causal-cost attack: fresh independent review v1

Date: 2026-09-09

Provenance: fresh independent read-only scientific/statistical attack requested
under `/root/relay_causal_cost_attack`; analysis only, with no execution or
scientific-claim authority. Any adoption remains subject to `AGENTS.md`.

## Verdict

The fixed `N=96`, `47/96` exact-binomial test is valid for one narrow estimand:

\[
p_R=\Pr(\text{the fixed child completes every registered TEXT and LoRA predicate on a root}).
\]

It is not an efficient discovery design and does not separately identify population effects for connection, traversal, experiment selection, writing, or delayed use. The binomial test is efficient for its Bernoulli datum; the inefficiency is paying for a very expensive, highly compound Bernoulli datum.

V4 defines `R_r` as the product of two complete chains and demotes all component values to diagnostics (`research_notes/60_one_child_pcfl_relay_v4_information_efficient_candidate.md:59-100`). V3 makes every positive, intervention, control, and mismatch an all-or-nothing factor (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:884-936`). Thus:

- `R=0` conflates absent mechanism, exact-trace brittleness, one control leak, writer/read failure, model noise, and ordinary technical failure.
- `R=1` establishes a strong same-root operational conjunction, but `X_R` neither localizes the limiting link nor estimates component effect sizes.
- `P(R)>.40` implies over 40% of roots passed every per-root predicate, but does not release standalone population claims for those predicates. The proper language remains “observed/intervention-tested relay,” not causal mediation (`research_loop/advisory/20260907_one_child_pcfl_relay_v4_final_attack_v1.md:143-174`).
- Existing bounded continuous values are deliberately descriptive (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:941-946`). Ignoring them in DEV discards the best failure-localization information.

The current eight-root DEV gate is also a poor launch selector. At the illustrative planning marginals, `Pr(DEV_GO)=.59049` and unconditional program-release probability is `.53241` (`research_loop/advisory/20260907_one_child_pcfl_relay_v4_revised_candidate_reaudit_v1.md:71-95`). This is not a Type-I-error flaw, but it kills roughly 41% of planning-compatible programs while learning little about why.

## Valid staged repair

A single averaged continuous “relay score” is invalid: strong writing could compensate for absent traversal. Connection, traversal, and expansion must remain separately falsifiable (`research_loop/advisory/20260907_objective_coverage_audit_v1.md:120-135`).

Use a vector of root-level paired endpoints in disjoint, no-claim DEV, followed by a later binary confirmation:

\[
\begin{aligned}
d^{conn}_{rk}
 &= \tfrac12\sum_g[Y_B(AUTH,g)-Y_B(DERANGED,g)],\\
d^{trav}_{rk}
 &= \tfrac12\sum_g[Y_B(AUTH,g)-Y_B(BRIDGE\_CUT,g)],\\
d^{select}_{rk}
 &=Qselect_{AUTH}-Qselect_{SHAM},\\
d^{EIG}_{rk}
 &=Qrelevant_{AUTH}-Qrelevant_{SHAM}.
\end{aligned}
\]

Also retain absolute authentic path/action success, exact returned-before-action receipts, and the two-goal path-switch indicator. These reuse the existing Phase-B and Phase-C bounded quantities (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:582-648,650-726`).

A smaller core can preserve all five requested objects:

1. Connection: `AUTH` versus matched `DERANGED`.
2. Goal traversal: two same-start goals with different paths, plus `BRIDGE_CUT`.
3. Experience-directed selection: `AUTH_SIGNAL` versus truthful matched `SHAM_SIGNAL`.
4. Write necessity: truthful new-row write versus masked no-write.
5. Delayed old-plus-new use: a D-phase \(2\times2\) factorial,

\[
OLD\in\{available,cut\},\qquad NEW\in\{written,no\text{-}write\}.
\]

For outcomes \(Y_{11},Y_{10},Y_{01},Y_{00}\), retain:

\[
d^{write}=Y_{11}-Y_{10},\quad
d^{old}=Y_{11}-Y_{01},\quad
d^{joint}=Y_{11}-Y_{10}-Y_{01}+Y_{00},
\]

plus absolute exact-path \(Y_{11}\). This empirically intervenes on both necessary rows; current v3 proves old/new necessity statically but experimentally focuses mainly on the new write and binding (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:748-818`).

The minimal LoRA core then needs only three builds per attempted root:

- authentic old deck plus pad;
- deranged old deck plus pad;
- authentic old deck plus new row.

Bridge cut, sham signal, old-row cut, adapter-off, and binding swaps are read-time interventions. `NULL` and `SHAM_WRITE` become conditional extra builds. This is a material architecture change requiring the full `AGENTS.md:3-18` path.

## Controls

Essential before or during DEV:

- Root/twin theorem, exact compilers, provenance chronology, hidden-truth separation, reset/capability isolation, and passive-field equality.
- Leaked-oracle fixture and exhaustive target-blind/visible-feature-subset closure.
- Explicit-TEXT minimal relay before LoRA.
- Derangement, bridge cut, two-goal switch, sham signal, `OLD×NEW`, full delayed positive, and one omnibus no-semantic/base-model control.

Systematic theorem or closure counterexamples remain global benchmark `NO_GO`, as v4 requires (`research_notes/60_one_child_pcfl_relay_v4_information_efficient_candidate.md:104-111`).

Epistemically essential for the eventual strong LoRA claim, but executable only on core-positive roots:

- `ADAPTER_OFF` for parametric attribution.
- `WRONG_LIFE` for personal/root-specific attribution.
- `NEW_BIND_SWAP` for correct binding rather than generic update effects.
- Exact no-carrier/unaided control.
- Exact TEXT/LoRA deck-equivalence receipts if both carriers remain in the claim.

Conditional execution is valid because an earlier core failure fixes the final product at zero (`research_loop/advisory/20260907_one_child_pcfl_relay_v4_revised_candidate_reaudit_v1.md:104-131`).

Conditional terminal diagnostics:

- `LINK_NULL` after a positive authentic-versus-deranged result.
- `BRIDGE_TWIN` after a positive cut effect.
- `SHAM_WRITE` after a positive write-versus-no-write effect.
- `REACHOUT_OFF` only for the distinct total acquisition-path claim; v3 correctly separates it from controlled writing (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:728-746`).
- Individual goal/state/identifier/candidate/passive/source-string controls to localize a failed omnibus leakage test.
- Outcome-level `TEXT_SAME_SEMANTICS` as comparability, not superiority.

If v4’s exact claim continues to name all these controls, they remain claim-gating. Demotion requires a narrower claim and new ratification.

## Concrete no-claim DEV ladder

Preseal eight DEV roots in fixed order plus four disjoint reserve-DEV roots. None enters confirmation.

1. **DEV-0, static/CPU:** Run all theorem, oracle, closure, compiler, capability, and reset fixtures. Any hidden-access violation, oracle failure, nonunique old/new support, controller counterexample, or integrity failure stops the protocol version. Repair requires fresh DEV identities.

2. **DEV-1, TEXT roots 1–4:** Run the minimal B/C/D factorial. Stop if fewer than `2/4` roots complete the minimal TEXT core or any required stage has no favorable paired root. These are engineering triage rules, not inference.

3. **DEV-2, TEXT roots 5–8:** Require at least `6/8` minimal TEXT cores, mean authentic B and D values at least `.75`, and every required paired contrast mean at least `.20`. No stage may compensate for another.

4. **DEV-3, LoRA core:** Run the three-build core only on TEXT-core roots, in presealed order. TEXT failures remain adverse zeros. Stop once four possible dual-core successes become impossible. Require at least `4/8` and no required LoRA contrast mean at or below zero.

5. **DEV-4, terminal attribution:** Only on dual-core candidates, run adapter-off, wrong-life, new-binding swap, and omnibus no-semantic. Stop when four surviving candidates become impossible; require at least `4/8`.

6. **Single amber extension:** If exactly `3/8` survive, all block means are positive, and no integrity fault occurred, run the four presealed reserve roots unchanged. Proceed only with at least `6/12` survivors and all contrast means positive. No further extension.

7. **Freeze or restart:** Any prompt, carrier, threshold, control, or interface change requires fresh DEV identities. DEV is never pooled with confirmation and supports no scientific claim.

Only then should a disjoint binary confirmation open. `N=96`, `X_R≥47` may remain if the final binary endpoint and `p_R>.40` claim are unchanged. The current fixed-denominator success/futility law is sound (`research_notes/60_one_child_pcfl_relay_v4_information_efficient_candidate.md:137-155`).

## E6 lifetime/saturation

Current PCFL roots support no E6 inference, even conditional on the fixed child.

- They are isolated environment trials of byte-identical clones of one selected child, not independent child lives or successive ages (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:28-40`; `research_notes/58_one_child_pcfl_relay_v2_executable_contract.md:14-18`).
- Phase B is destroyed and C restarts from `C0` (`research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md:575-580`). D uses clean-base rebuilds and fresh processes (`:465-470,748-762`).
- More roots tighten task-distribution inference conditional on one child; they add no time axis, cumulative lifetime, between-child replication, or baseline plateau.
- V4 expressly excludes lifetime improvement (`research_notes/60_one_child_pcfl_relay_v4_information_efficient_candidate.md:71-76`).
- E6 requires at least three prospective checkpoints after the strong active-text comparator meets its own local-plateau rule, with slopes and matched resources (`research_notes/DREAM_LORA_THINK_FULL_EVIDENCE_STACK_20260907.md:198-211`).

The same environment family may be reused, but E6 must remain a separate longitudinal experiment. Its unit must be a sealed cumulative trajectory of the fixed child across successive experience blocks—or independently selected child lives for population generalization. Reset PCFL task roots cannot be relabeled as either.
