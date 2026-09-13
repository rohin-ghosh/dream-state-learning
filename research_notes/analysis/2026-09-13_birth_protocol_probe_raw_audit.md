# Independent raw audit: teacher-free AUTH-birth protocol probe

Date: 2026-09-13 UTC. Scope: the completed, released node-3 root
`astra_birth_protocol_probe_seed0_20260913_attempt1` (SEQ-122). This is a
read-only recount of the 32 native request/response pairs, followed by a bounded
independent recount of the 32-call clarified-prompt control when it became
terminal. I did not import or trust either stored scorer, change a
prompt/parser/adapter, or run a model/GPU job.

## Verdict

The stored family counts are correct. The result supports a narrow causal
statement: mounting the source-authored AUTH birth adapter changes behavior
under exactly paired prompts, but does **not** make the child compatible with
the RuleGame protocol. It increases generic action emission on public-revision
requests (`0/4` parser-valid OFF -> `4/4` AUTH), while damaging a quiz interface
the base model already followed (`4/4` exact OFF -> `1/4` AUTH) and slightly
damaging faithful record serialization (`4/4` -> `3/4`). Both states preserve
the public revision truth in their text (`4/4` tolerant forecast content), so
the main revision error is action selection/serialization rather than failure
to read the observation.

In Rohin's vocabulary this is a **trained** output policy, not learned or
self-learned behavior: someone else authored the birth targets. Together with
SEQ-120's complementary conditional-map result, the probe is evidence for a
narrow installed policy plus cross-schema interference. It is not evidence for
RuleGame induction, parenting, own-experience learning, retention, useful
thought, or Level 1/2 qualification.

The separately versioned grammar-clarification control materially narrows that
diagnosis. Explicit grammar makes **all 32/32** responses parser-valid, restores
quiz to `4/4` in both states, and makes AUTH complete all four revisions versus
OFF's two. Therefore a second model-call projection is **not the first repair
for direct protocol prompts**: exact grammar/action priority is sufficient.
Projection remains useful only for genuinely free-thinking turns that still
bundle actions after this prompt repair. A narrower coexistence problem remains
in the unchanged record role: OFF is `4/4`, AUTH `3/4` in both runs, with the
same null-prediction relation error. That needs an isolated relation diagnostic
and, if replicated, a birth-interface anchor—not an action projection.

## Independent 32-cell recount

I derived targets from the fixed public case fields and independently parsed
each raw string. For action calls, `parser` means exactly one legal RuleGame
`ACT:` payload for the supplied revealed/budget state. `public` additionally
requires the requested action, triple/labels, and a preceding literal
`PREDICT: T/F` where required. For records, `parser` means valid JSON and
`public` means the four decoded values equal the executed public event; JSON
whitespace and key order are ignored. `exact` is byte equality to the frozen
reference target.

| Family (n=4/state) | OFF parser / public / exact | AUTH parser / public / exact |
| --- | ---: | ---: |
| TRY serialization | `0 / 0 / 0` | `0 / 0 / 0` |
| Quiz format | `4 / 4 / 4` | `1 / 1 / 1` |
| Record | `4 / 4 / 0` | `4 / 3 / 0` |
| Public-evidence revision | `0 / 0 / 0` | `4 / 1 / 1` |
| **All families** | **`8 / 8 / 4` of 16** | **`9 / 5 / 2` of 16** |

These reproduce the stored reducer exactly. Two interpretation details matter:

1. Record exactness is intentionally too strict for semantic fidelity. OFF's
   `0/4` exact records are all correct JSON with ordinary whitespace. AUTH has
   three faithful records; its only semantic error maps absent prediction to
   `matched` instead of `unavailable`.
2. Public-contract correctness is formatting-sensitive for action families.
   I therefore separately read forecast content tolerantly (`T`/`True`,
   `F`/`False`). Both OFF and AUTH state the correct observed result in all four
   revision cases. OFF then emits no action. AUTH emits one generic legal action
   in all four, but twice chooses quiz reveal instead of repeating the triple,
   once spells `TRUE` rather than literal `T`, and only once gives the complete
   requested response.

The raw behavior by family is:

- **TRY:** OFF produces two malformed attempts containing the requested triple
  and two quiz actions, all with noncanonical `PREDICT ACT:` syntax. AUTH emits
  bare `PREDICT` three times and malformed `PREDICT ACT: QUIZ ?` once. Neither
  state supplies even one complete forecast-plus-TRY response.
- **Quiz:** OFF exactly supplies both reveal actions and both six-label
  submissions. AUTH drops `?` from both reveal actions, supplies one six-label
  answer exactly, and drops all labels from the other. This is the cleanest
  within-probe evidence of negative cross-schema transfer because the requests
  are unambiguous and OFF is perfect.
- **Record:** OFF is semantically `4/4`; AUTH is `3/4`. The single AUTH miss is
  `{"predicted": null, "relation": "matched"}` where `unavailable` is required.
- **Revision twins:** OFF forecasts `F/T/True/F`, all correct, but never emits
  an action. AUTH forecasts `F/T/TRUE/F`, also all semantically correct; within
  the first outcome twin it emits the same wrong quiz action on both sides, and
  within the second it repeats the correct triple on both sides. Thus the
  observation controls forecast content, while prompt/schema competition
  controls whether the requested action is completed.

## Bounded comparison: explicit grammar clarification

After the original audit was complete, I separately inspected the terminal
root `astra_birth_protocol_clarified_seed0_20260913_attempt1`. This control
appends one uniform grammar/action-priority block to the same 12 wake cases;
the four record prompts, all targets, public facts, seeds, caps, graders, base,
and AUTH adapter are unchanged. It was adaptively selected after the exposed
original result, so it diagnoses the failure but cannot confirm an effect.

I again scored all 32 raw strings without the stored reducer:

| Clarified family (n=4/state) | OFF parser / public / exact | AUTH parser / public / exact |
| --- | ---: | ---: |
| TRY serialization | `4 / 2 / 2` | `4 / 2 / 2` |
| Quiz format | `4 / 4 / 4` | `4 / 4 / 4` |
| Record (byte-identical prompt control) | `4 / 4 / 0` | `4 / 3 / 0` |
| Public-evidence revision | `4 / 2 / 2` | `4 / 4 / 4` |
| **All families** | **`16 / 12 / 8` of 16** | **`16 / 13 / 10` of 16** |

The recount matches the stored result. All requests still pair exactly across
OFF/AUTH, both inner 36-file manifests hash cleanly, the root has 91 files, the
old controller/launcher PIDs are absent, and the plan/capture/release evidence
is terminal. Key hashes are plan `cceacca7...aff46b`, controller
`ee8f1dc8...d847`, capture barrier `7da3b65f...447`, audit
`12b238de...7a16`, and release `d83c0f5a...a3b`.

What changed:

- **Syntax and action routing were mostly prompt problems.** Every originally
  malformed or missing action becomes parser-valid. The original `4/4` OFF to
  `1/4` AUTH quiz regression disappears completely. It is no longer defensible
  to call that a durable erasure of the quiz interface.
- **The narrow trained policy is now visible.** With the requested grammar
  explicit, AUTH repeats the correct observed triple and forecast in all four
  revision cases; OFF still follows the printed quiz reminder in the first two
  and succeeds only on the other pair (`4/4` versus `2/4`). This is the most
  useful transfer signal in the probe, but it is source-authored training, one
  root, and an exposed practice panel.
- **Neither state obeys supplied false forecasts in the TRY family.** Both emit
  `T` on all four cases, so both score exactly `2/4`. That is a remaining
  instruction-following limitation, not an AUTH-specific effect.
- **The record defect is stable and role-local.** Record prompts were unchanged;
  AUTH repeats the same `null -> matched` error while OFF remains semantically
  `4/4`. This is the surviving evidence of negative cross-schema interference,
  but it is one case and should be isolated before changing training.

## Custody, routing, and release

- Frozen plan SHA-256:
  `50d47f1fc8b9c8c2557e963f296f593c4c92deb220aee75b85200eb8f5153352`.
  The remote plan, controller, and capture-barrier hashes match the collected
  archive.
- Capsule SHA-256:
  `11bd6633d462adfff2b3b2a2ca07de78e4f103344c69c7418ab1be37cc258973`;
  validation SHA-256:
  `e7e64988e46c67c442493a19e299c7e0fe9378b90d19c7cfdf59b31642420452`.
  I independently hashed all `91/91` archive members against the validation
  map and both inner data manifests against their raw request/response files.
- Material/runtime hashes independently match their native files:
  `2799efda...cc66b` and `4be56ece...702c`. The three relevant frozen RuleGame,
  parser, and record-source files also match their plan pins.
- All `16/16` request objects are exactly paired OFF versus AUTH, including
  prompt, role, seed, temperature, cap, stop settings, case ID, and tick.
  Each state has 12 wake calls and four record calls. Only loader identity
  differs.
- OFF has no adapter. AUTH loads the original birth adapter with configuration
  hash `75559e94...ffc7` and weight hash `82f8e22a...52b57`; I re-hashed those
  actual native files. Both use the same locally hash-pinned Qwen2.5-7B-Instruct
  snapshot. The historical plan's `UNRESOLVED_LOCAL_HASHES_ONLY` label remains
  part of this result even though future experiments now have a prospective
  public-revision binding rule.
- All `32/32` responses end in EOS, finish normally, have no token-limit or
  explicit stop-string match, and remain denominators. Usage is 5,432 input and
  472 output tokens, with output EOS included.
- Both worker supervision receipts are return code zero, owned-group empty,
  GPU-process absent, and reservation-release verified. Backend cleanup is
  closed for both states. The old controller PID 283963 and launcher PID
  283888 are absent on a fresh read-only node check. A later process, if any,
  is not evidence about this released root.

## What the probe identifies

The paired intervention is strong enough to say the AUTH adapter changes the
output distribution. It is not strong enough to call that change a useful
RuleGame policy. The pattern is coherent with the birth corpus:

- birth repeatedly trains `PREDICT ... / ACT ...` and
  `COMPARE / POLICY / NEXT` output families;
- RuleGame requires a different nested payload grammar:
  `PREDICT: T/F` followed by `ACT: TRY a,b,c`, plus separate quiz and JSON
  record schemas;
- in the ambiguous original prompt, AUTH becomes more likely than OFF to finish
  an action-shaped revision but its trained tag/action prior competes with the
  requested native payload;
- explicit grammar removes that apparent quiz competition and exposes a useful
  AUTH revision advantage; only the unchanged record-relation miss survives as
  evidence of possible negative cross-schema interference.

The original TRY/revision prompt has a real ambiguity: it asks for a TRY while
also printing `ACT: QUIZ ?` as a harness-state reminder, and it never states the
literal forecast-line grammar. The clarified control confirms that this—not a
general inability—caused the action-validity failure. The original quiz prompts
were more direct, but their AUTH regression also disappears once the same
uniform action-priority block is appended; it was prompt sensitivity, not
durable interface erasure.

The result is one exposed developmental panel, one optimizer root, and a
source-authored non-clean birth. Sampling at temperature 0.7 is exactly paired
by requested seeds but not proven bitwise common-random across separate
backends. Do not turn the observed count differences into population efficacy
or a general interference rate.

## Prompt grammar, projection, and coexistence: the decisive ordering

1. Preserve both roots and every failure. Do not relax the parser or execute
   the first action-shaped substring from an invalid response.
2. Use the clarified one-call grammar for the next development-only formation
   before adding a second inference call. It has already restored parser
   validity and quiz behavior at lower cost.
3. Keep a separately versioned second-turn projection only for free-thinking
   formation turns that remain multi-action or actionless. It may consume one
   existing slot, use the exact tentative text/public state, get one chance,
   and expose no outcome before a strict parse. Report original-valid and
   projection-recovered cases separately.
4. Before modifying birth data, run the already-motivated no-world relation
   canary over `false/true -> mismatched`, `true/true -> matched`, and
   `null/true -> unavailable`, with only the relation token requested. If AUTH
   alone still misses the null case, add a small role-conditioned record/native
   interface anchor to a **development successor**, balanced within training
   groups and evaluated on fresh held schemas.
5. Neither explicit grammar nor projection qualifies birth. A fresh birth must
   still pass the original complementary conditional and locality gates across
   independent roots, then participate in a clean parent-deleted Level-2 path.

The ordering is therefore: **explicit grammar first; projection only for
residual free-thought bundling; corpus repair only for a replicated role-local
coexistence defect.** This is less invasive than my original diagnosis and is
what the clarified control supports. None should replace or tune Q0.

## Quarantine and claim boundary

This probe was observed after SEQ-120 and is `EXPLORATORY_PRE_Q0`. None of its
prompts, responses, errors, source cases, adapter behavior, action-projection
idea, or follow-up outcome may select or modify Q0's material, objective,
hyperparameters, thresholds, root/seed choices, or reducer. Q0 must run from
fresh base under its already-closed pair-balanced contract. This probe may
guide a separately declared **development-only, post-Q0** birth/interface
successor, which then needs fresh held forms and independent roots.

Defensible statement: **the source-authored AUTH birth adapter installs a
narrow output policy that improves public-revision completion when exact action
grammar is supplied. Most original action/quiz failures were prompt-schema
ambiguity, not a need for a second projection call. One stable record-relation
error remains possible cross-schema interference. This does not qualify birth,
learning, parenting, or Level 2.**
