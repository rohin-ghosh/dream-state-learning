# Sparse-factor graph audit for PCFL-Compose

**Date:** 2026-09-02  
**Status:** read-only mathematical and construct-validity advisory. This is not an architecture consensus, implementation authorization, model run, GPU authorization, or scientific result.

## Verdict

Replacing the designated anchor row/column by a presealed connected sparse bipartite action graph is mathematically sound and is a modestly better presentation of the intended factor-completion problem. It makes source experience less like a supplied formula table, permits genuinely prospective chord tests, and makes connectivity explicit.

It does **not** by itself make PCFL-Compose a stronger test of DREAM-style connected memory. In the noiseless `S_6` world, a connected tree already determines every unobserved compound transformation conditional on orientation, by exact group propagation; one informative chord selects orientation. The latent reasoning remains a tiny known-family finite-group matrix-factorization problem. An exact public program has an `O(|I|+|J|)` sufficient statistic and an easy target-time solution.

The essential correction: a single global two-world twin bounds D4 target-only full-trajectory value by `1/2`, not `1/16`. A `1/16` ceiling requires a sealed `2^4` orbit with independently swappable action labels at the four stages.

## 1. Formal world, gauge, and tree propagation

Let `G=(I union J,E)` be a public simple connected bipartite source graph. A source edge `(i,j)` reveals its exact permutation `t_ij in S_6`. With the convention that the rightmost function acts first, the life-wide orientation is either

```text
BA: t_ij = b_j a_i
AB: t_ij = a_i b_j.
```

The assertion is convention-independent if generation, extraction, inference, and scoring agree.

For a fixed orientation, a connected source graph determines all factors only up to one global gauge. For `BA`, `b_j -> b_j g, a_i -> g^-1 a_i`; for `AB`, `a_i -> a_i g, b_j -> g^-1 b_j`. A disconnected graph has one independent gauge per component, so any target joining components is unidentifiable.

Use a deterministic root `(i0,j0)` and store a gauge-fixed schema, not generator factors:

```text
BA: set a_i0=e; b_j=t_i0,j; a_i=t_i0,j0^-1 t_i,j0.
AB: set b_j0=e; a_i=t_i,j0; b_j=t_i0,j0^-1 t_i0,j.
```

Thus, with `R_i=t_i,j0`, `C_j=t_i0,j`, and `M=t_i0,j0`, the anchored completions are

```text
P_BA(i,j)=C_j M^-1 R_i
P_AB(i,j)=R_i M^-1 C_j.
```

For a general spanning tree, replace this by the alternating product along its unique path. A tree always admits both orientations: cycle constraints are vacuous. Conditional on orientation, it predicts every missing pair whose endpoints are in the connected graph.

The canonical sufficient statistic is `|I|+|J|-1` group elements plus one orientation bit. This is linear in independent factors; it does not justify an independent-information compression claim.

## 2. Exact identifiability and minimum chord evidence

Choose a pre-chord spanning tree `F`; let `P_h^F(e)` be the prediction under orientation `h` for later source edge or holdout `e`.

Orientation is uniquely identified exactly when:

1. every target endpoint has source support in the same connected component;
2. the true orientation is consistent with all observed chords; and
3. at least one chord rejects the other orientation:

```text
exists e in chords: P_BA^F(e) != P_AB^F(e).
```

One noncommuting fundamental chord is sufficient in the noiseless two-law world. For a smallest square with `M=t_11, R=t_21, C=t_12`, the two fourth-edge predictions are `C M^-1 R` and `R M^-1 C`; inequality is the required witness. An abstract minimum is therefore one noncommuting 4-cycle chord.

There is a real degeneracy. Under `BA`, define `p_i=a_i a_i0^-1` and `q_j=b_j0^-1 b_j`. Both orientations give the same complete action table iff

```text
q_j p_i = p_i q_j for every i,j.
```

This includes nonidentity factors with mutually commuting relative subgroups (such as disjoint-support permutations). No number of chords identifies orientation there because it has no observable consequence. A sparse graph can also leave both orientations consistent on observed edges while differing on holdouts; freezing a target memory then is information-starvation. Reject either situation for an orientation headline.

Finally, chord identification alone is insufficient: every decisive target action must differ under the wrong orientation, and the registered target path must fail under that substitution. Otherwise orientation was measured but not causally used.

## 3. Minimum useful sizes

| Purpose | Minimum transparent construction |
|---|---|
| One unseen pair plus orientation witness | `r=2,c=3`: four tree edges then one noncommuting chord, five actions total. A `2x2` square alone has no remaining pair after observing its chord. |
| Exact two-action D1 stem-twin | `r=3,c=3`: a symmetric five-edge pre-chord tree plus a two-edge chord orbit, seven actions total. The third stem supports the target suffix while both paired-stem target edges stay unexecuted. |
| Clean D4, independent-stage `2^4` twins | `r=9,c=5`: a 13-edge symmetric pre-chord tree and a two-edge chord orbit, 15 actions total. This is a minimal clean *tree-first construction*, not a universal optimum under every symmetry relaxation. |

For D4, use paired stems `(u_l,v_l)`, decisive suffixes `j_l`, `l=1..4`, and support factors `u0,j0`. Before validation execute

```text
(u_l,j0), (v_l,j0) for every l;
(u0,j0), (u0,j_l) for every l.
```

These `8+1+4=13` edges are a tree on `9+5=14` vertices. Leave all `(u_l,j_l)` and `(v_l,j_l)` unexecuted. Commit predictions, then execute the label-symmetric non-target chord orbit `(u_1,j_2),(v_1,j_2)`, certified to reject the wrong law. The target factors all have support; neither decisive compound has been executed.

Mathematically one chord is enough. The two-edge orbit is needed here so the nontrivial label-swap source schedule remains equivariant. A less symmetric schedule may be valid algebraically but weakens the twin/firewall story.

## 4. Targets, twins, and Bayes headroom

For target sequence `s=((i_1,j_1),...,(i_D,j_D))`, choose a fresh start tray `x`, set `y=t_iD,jD ... t_i1,j1 x`, and show at stage `l` the fixed-order labels `(u_l,j_l),(v_l,j_l)`. Exhaustively certify all `2^D` menu sequences: exactly one reaches `y`, no shorter sequence reaches it, no wrong prefix recovers, and no observed tool substitutes. Check this in every twin.

A single global involution swapping paired stems and setting `a'_i=a_sigma(i)` leaves start, goal, menus, budgets, rendering, and visible checkpoint bytes identical when the correct labels are mapped by `sigma`. It establishes a strong first-action target-byte test, but only creates two indistinguishable world states. Full D4 sequence success is then at most `1/2`.

For a real `1/16` target-only ceiling, make a hypercube `H_z`, `z in {0,1}^4`, where bit `z_l` independently swaps `u_l,v_l` and maps that stage's correct label. The factor pairs must be disjoint, all 16 worlds equally likely, schedules/corpora equivariant under every swap, and the 16 correct sequences distinct. Then:

```text
Bayes(D1 action) = 1/2
Bayes(D4 full trajectory) = 1/16
Bayes(D4 first action) = 1/2.
```

Without the uniform free orbit, `1/16` is only a random-menu heuristic. The independent-edge negative-law sentinel must preserve this entire target/twin distribution while sampling every unexecuted transformation independently of eligible source experience.

## 5. Reader and hop complexity

With atomic gauge-fixed factor records and no target-specific shortcut, an unseen action requires two factor records and the orientation relation. In the D4 hypercube construction, selecting between both actions at all stages generally needs

```text
8 candidate stem records + 4 suffix records + 1 orientation record = 13 local semantic items.
```

The redundant `R,C,M,h` representation needs 14. A cap below this exact declared requirement is reader starvation; returning a completed compound transformation, full factor table, or target-assembled path is a solution packet.

The certifier should issue a minimum-read certificate under a fixed atomic record grammar. For every supposedly necessary record, substitute a legal alternative factor while holding all other accessible records and target bytes fixed, and verify the correct first action changes. This establishes an information lower bound for that reader interface.

One action has constant algebraic dependency depth after compilation (two factors plus order), though deriving it directly from episodic tree edges can take an alternating path of length `O(r+c)`. D4 is four environment actions, not demonstrated four-hop memory traversal. Iterative-thinking claims still require itemwise reads, cited workspace updates/replans, and a one-shot full-schema control at equal information and work.

## 6. Formal certifier and oracle firewall

A scorer-only manifest should prove:

1. graph connectedness, factor coverage, chosen tree, gauge-fixed factors under both laws, and every observed-cycle constraint;
2. prediction bytes/provenance/deadline committed before chord execution, true-law equality afterward, and wrong-law disagreement on a chord;
3. target pairs absent from source, corpus, candidates, indexes, and derived closure; supported endpoints; and target failure under wrong-law and decisive-factor cuts;
4. exhaustive unique-path/no-shortcut certificates in every twin;
5. hashes of target-visible byte equality across each twin orbit, equal priors, distinct correct sequences, source-schedule equivariance, and no world-ID/handle/RNG/cache/error/timing side channel;
6. declared reader record grammar/bytes, exact minimum legitimate reads, and per-record decision forks;
7. an independent-law sentinel matched on graph roles, renderer, menus, permutation marginals, twin orbit, and target distribution, with holdouts conditionally unidentified; and
8. a firewall that prevents hidden factors, exact closures, solver paths, target identities, and certificates from reaching prompts, retrieval keys, compiler inputs, candidates, trainer state, logs, or errors.

The comparator may only check a previously committed prediction against a later public outcome. Selecting hypotheses, repairing factors, or unbounded propose-and-filter retries is cognition, not mechanical verification.

## 7. Construct and shortcut assessment

The graph variant improves source presentation and prospective validation, not the underlying cognitive difficulty.

- Revealing exact `S_6` elements means one action supplies a complete local operator. The public morphology and connected graph advertise the factor grammar.
- If a prompt gives the two equations, or a compiler performs tree propagation and chooses the chord-consistent law, the claimed dream connection has already been solved by scaffolding/code.
- The omitted-edge set is a public candidate universe. Enumerating its closure is an exact algebraic compiler, even if target-blind.
- `S_6` has only 720 elements and D4 has only 16 menu sequences; an exact public program and one-shot full-schema planner are mandatory ceilings/controls.
- Unequal paired-label timing, serialization, source order, factor-sampling bias, candidate order, or metadata can leak a twin bit. Target-byte equality alone is insufficient.
- The independent-law sentinel fails if terminal goals/menus differ in a way that identifies an unexecuted transformation.

## Final disposition

Adopt the sparse graph as a disciplined repair only if the certificates, hypercube twins, chronology, and ownership firewall are enforced. The honest resulting claim is prospective completion of a known two-orientation noncommutative factor family from sparse public action experience, followed by memory-assisted use of never-executed actions.

Without those additions it is just a slightly less transparent algebra puzzle: a tree is a deterministic propagator, a chord is a one-bit selector, and D4 is a sixteen-sequence search. It does not itself improve evidence for DREAM, connected-memory traversal, or a self-improving developmental architecture.

No code, models, network resources, or experiments were run for this audit.

