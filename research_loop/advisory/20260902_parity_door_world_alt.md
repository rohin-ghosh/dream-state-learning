# Parity-Door Transition World (alternative prospective-schema design)

Date: 2026-09-02

Status: independent design check; proposal only. This note authorizes no
implementation, model/provider/network/GPU run, or scientific claim.

## Minimal world

Use fresh, depth-4 binary transition trees as cohorts. Each internal state has
two action labels and a persistent public type vector `t`; each cohort has a
public descriptor vector `d`. State handles, action names, and natural-language
skins are freshly randomized, while the descriptor/type features retain their
meaning. A hidden world-level law determines which action reaches the left
child:

```text
left_action_bit = theta XOR dot(a, d) XOR dot(b, t)  (mod 2)
```

The coefficient vector `(theta, a, b)` is sampled once per world. It is not
given to the compiler. The exact finite hypothesis family and arithmetic are
declared before generation, but the coefficient values, labels, and target
allocations are hidden. This is a small reusable physical regularity (a
parity-controlled door orientation), rather than an arbitrary per-edge lookup
table.

## Experience and prospective commitment

Practice episodes expose only the public transition event:

```text
current_state, chosen_action -> next_state, cost
```

They never emit a rule, proof, target path, goal, or answer. A fixed,
balanced, target-independent policy visits both actions at enough typed nodes
in several earlier cohorts for a prompted 32B compiler to fit the affine law.
The compiler must append a typed schema hypothesis, with provenance and a
commit timestamp, before the later cohort's transition outcomes are exposed.
Delayed practice outcomes then mechanically support or contradict that
hypothesis. The target manifest, held-out edge, and target goals are presealed
but unavailable to compiler, trainer, index, retries, caches, and thinker.

## Held-out action test

Generate a fresh cohort whose descriptor combination was absent from the fitting
prefix. Present a fresh start state and a goal leaf four transitions away.
All but one target-path transition can be locally observed; the decisive edge
is withheld until after schema commitment. Its child handles are opaque, so
the local atom corpus gives no information about which action reaches that
child. Under the no-schema model, the exact target-local ceiling is 1/2 for
the missing binding. The schema predicts it, after which the thinker must issue
four irreversible `MOVE(label)` actions and a terminal `COMMIT`. Wrong branch
choices cannot be repaired within the declared cap.

Pair every target with a goal twin sharing the same start and byte-level target
format but requiring a different first action. Credit requires the actual
state trajectory and terminal success, not a plan string, citation, or answer
text. The held-out edge is revealed only in delayed public confirmation after
the prospective action test, so later confirmation cannot steer the original
decision.

## Counterfactual twins and controls

The world twin flips `theta` (or another preregistered coefficient involution),
thereby flipping action-to-child bindings while preserving target/goal bytes,
action inventories, caps, chronology, and balanced practice action/outcome
marginals. The source event sequence and correct trajectories differ only in
the hidden binding.

The minimum control panel is:

1. All local transition atoms with no cross-cohort schema.
2. Exact target-only Bayes and a schema-after-holdout (leaked) ceiling.
3. Descriptor/mapping twins, wrong-twin memory, and schema-binding shuffle.
4. Complete decisive-schema masking versus an equal-size sham mask.
5. Exact symbolic schema versus prompted compiled text and compiled LoRA.
6. Raw episodic RAG, no-memory/native-context, and explicit transition-program
   controls.

Every item is allocated before support or compilation; unsupported,
uncompiled, malformed, timeout, and runtime-failed items remain in the
denominator. Authentic-versus-twin adapters and whole-corpus text cuts are
needed for parametric claims; deleting a displayed citation is not a LoRA
intervention.

## Why this is not merely QA

The decisive local fact is absent. The agent must use a prospectively inferred
reusable rule to choose a sequence of irreversible environment actions, and
the goal twin tests goal-conditioned branching. Twin substitution must redirect
the trajectory and schema cuts must reduce return relative to sham cuts.
Correct final text without the required trajectory receives no credit.

## Context scaling and scope

Append fresh cohorts and practice traces under the same law until raw history
crosses exact `2L_native`, `4L_native`, and `8L_native` checkpoints, retaining a
constant-size schema and reporting raw tokens, unique local bindings, retained
state, query work, compiler/training work, and action value. This tests
prospective lossy abstraction and cross-cohort transfer; it does not establish
independent-entropy accumulation or on-policy evidence acquisition.

## Paper-1 risk judgment

This is too risky for a Paper-1 headline. It directly invokes the
PCFL-Schema/semantic-compression rung that the area-chair review recommends
cutting, and its validity depends on stringent prospective-commitment,
descriptor-twin, target-leakage, and binding-intervention audits. A one-world
sentinel is feasible within two weeks and could gate a follow-up, but Paper 1
should retain the safer fixed-source PCFL-Stream acquisition/retention claim.

