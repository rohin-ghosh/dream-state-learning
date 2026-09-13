# PCFL Astra D binding: implementation acceptance audit

**Date:** 2026-09-13  
**Authority audited:** `research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md`  
**Authority SHA-256:** `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91`  
**Scope:** static/independent CPU audit only; no runtime edit, tokenizer, model, training, native backend, or GPU work

## Verdict

**ACCEPT the selected Astra D contract as scientifically valid for the narrow PCFL v2.2 experiment, conditional on the implementation gates below.** I found no contradiction that invalidates the design.

The selected construction does the needed causal job:

- relevant unknown: `H --q_R--> S_R`;
- distractor unknown: `X --q_D--> Z`;
- R and D independently select from the same `q0/q1` alphabet;
- the relevant bit changes the unique delayed route;
- the distractor bit has equal entropy but no effect on either delayed route;
- a distractor commitment ends the branch and never becomes experiential training data.

I independently enumerated the 8 `(O,R,D)` cells and both delayed goals after adding the private X-to-Z transition. All 16 cases had one unique delayed route, the route was invariant to D, and deleting either e0 or e8 destroyed it. This was a pure local graph calculation.

The contract supports only the narrow claim that a child chose a task-relevant unknown over an equally uncertain irrelevant unknown. Both registered delayed goals require the same frontier, so this main assay does **not** show that changing the goal reverses experiment choice or establish general value-of-information planning. The separate Y-goal sidecar may study that later, but must not be folded into main-PCFL D-neutrality.

The earlier laptop candidate is superseded for exact bytes. Its four-line/no-final-LF surface and no-r9/r10 custody are now negative mutations, not alternative legal implementations.

## Exact state-machine acceptance matrix

| state/input | exact public effect | private effect | next state | acceptance condition |
|---|---|---|---|---|
| PRECOMMIT + valid relevant probe | exactly `PROBE RESULT {probe} TESTED {H} TO {S_R} AVAILABLE PORT {q_R}\n` | issue private r9 probe-observation custody | RELEVANT_RESULT | one result only; no receipt ID or role label is public |
| RELEVANT_RESULT + exact `EXPLORE H q_R` | ordinary public executed-event receipt | issue executed-action r8, then permit e8/l4/l5 authoring opportunities | RELEVANT_EXPLORED | r8, not r9, is the only NEW executed-event evidence |
| RELEVANT_RESULT + any other action | no successful receipt/repair | record failed attempt only | terminal failure for that opportunity | never canonicalize or reveal the right action |
| PRECOMMIT + valid distractor probe | exactly `PROBE RESULT {probe} TESTED {X} TO {Z} AVAILABLE PORT {q_D}\n` | issue private r10 probe-observation custody | TERMINAL_DISTRACTOR | no next model call, EXPLORE, r8, EVENT, LINK, corpus row, or retry |
| PRECOMMIT + malformed/unlisted probe | zero result bytes | no r9/r10 result receipt; the one commitment is consumed | TERMINAL_INVALID | no correction, legal-probe list, or retry |
| any postcommit state + second PROBE | zero result bytes | rejected attempt only | terminal/unchanged terminal | exactly one commitment per lineage |

Here `\n` is exactly one LF byte. No CRLF, missing LF, double LF, trailing spaces, extra terminal message, Markdown, or second line is legal.

The private r9/r10 record must use one closed successor schema bound before execution. Under the selected memo's reference to the existing receipt machinery, the current shape is the exact starting point: probe ID, receipt ID, source, destination, port, `kind=PROBE`, root, `stage=NEW`, chronological turn, predecessor hash, production/fixture status, and self-hash over the canonical record without the self-hash. The implemented schema must be written literally into the production registry rather than inferred at runtime. Required distinctions:

- r9 is relevant-probe observation custody;
- r10 is distractor-probe observation custody;
- neither is model-visible;
- neither is an executed-event receipt;
- neither may support EVENT/LINK admission, a memory target, a service return, or a fit;
- after relevant commitment, r8 is downstream of r9 in private chronological custody even though numeric suffixes are not chronology;
- after distractor commitment, r10 has no child-action descendant.

## Scientific invariance and nonleakage matrix

| invariant | exact required check | failure meaning |
|---|---|---|
| quartet pre-outcome collision | at fixed `(root,O,goal)`, all four `(R,D)` cells have byte-identical messages, IDs, option order, task state, and prompt hashes until a result is returned | R/D or future route leaked before choice |
| balanced independent bits | every quartet is exactly `00,01,10,11`; no redraw; R and D are independent | distractor is not a matched one-bit unknown |
| shared outcome alphabet | both frontiers use the same opaque q0/q1 inventory; relevant returns qR and distractor returns qD | surface/type or entropy mismatch |
| neutral result surface | all four relevant-R0/relevant-R1/distractor-D0/distractor-D1 results instantiate the same one-line template | role can be decoded from grammar or length |
| token equality | complete chat/result and required result-join substitution classes are equal-token under the pinned tokenizer | token length leaks role/bit or changes budget |
| exact information table | compute, do not hardcode, `H(Y_R)=1`, `H(Y_D)=1`, `I(Y_R;Z_G)=1`, `I(Y_D;Z_G)=0` in every fixed `(root,O,goal)` quartet | the matched-uncertainty/irrelevance construction failed |
| D-neutral delayed labels | at fixed `(root,O,R,goal)`, toggling D changes no correct route, OLD/NEW memory, prompt, score, or fitted target | D is not an irrelevant control |
| R necessity | at fixed `(root,O,D,goal)`, toggling R changes qR in the unique delayed route | relevant outcome is not informative |
| route uniqueness | full private graph, including latent `X --q_D--> Z` and old `Z --u--> Y`, has exactly one path to each delayed goal | alternate route/shortcut invalidates dependence |
| causal cuts | deleting e0 or e8 destroys every delayed route; control mate remains unchanged | OLD/NEW causal claim fails |
| projection collision | OLD-only is byte-identical across R while labels differ; NEW-only is byte-identical across O while labels differ | a nominal memory ablation still contains the missing bit |
| prompt-only ceiling | at fixed `(root,goal)`, all eight O/R/D native prompts collide and the four route labels occur twice each, giving exact deterministic ceiling `.25` | identifiers or prompt bytes leak a route label |
| no witnessed D | latent X-to-Z is absent from EXACT_WITNESSED_GRAPH, raw episodic experience, EVENT/LINK rosters, memory service, authentic corpus, and LoRA targets | compiler injects an unexperienced fact |
| endpoint privacy | mnemonic X/Z/H/S_R, structural role, root label, R/D, and G_ goal handles never reach the model; only root-local opaque IDs do | direct semantic/role leakage |
| order balance | RA/RB preserve the exact registered surfaces and opposite order; structural relevant position is balanced prospectively | position can substitute for learned relevance |
| failure denominator | a D choice is recorded as a stopped/failed lineage, never dropped or replaced | selective survival inflates reachout success |

The public endpoints intentionally differ: H/S_R is connected to the remembered delayed route while X/Z lies on the dead-end branch. That is the information the child is supposed to use. The nonleakage condition is not endpoint identity; it is absence of a role label, hidden outcome, future answer, or surface/token shortcut beyond the child's own stored graph knowledge.

## Compatibility with the landed implementation

| selected requirement | current landed support | required change before native use |
|---|---|---|
| one-line result with one LF | `PROBE_WIRE` already matches byte-for-byte | snapshot all four result instances and joins under the adopted source pin |
| q0/q1 shared inventory | q0/q1 and r0..r10 are already reserved | bind D to X/Z and certify token/substitution equality |
| r9/r10 private observation receipts | fixture probe already selects r9/r10 | publish exact production schema/custody and forbid these IDs from EVENT/LINK admission |
| X-to-Z private distractor | absent; fixture uses Z/Y endpoints | add a distinct private frontier relation; do not misrepresent it as a witnessed `Edge` with EVENT/receipt |
| terminal distractor | absent; current fixture stores every valid probe result as an exploration affordance | add explicit RELEVANT_RESULT, TERMINAL_DISTRACTOR, and TERMINAL_INVALID states |
| relevant-only EXPLORE | fixture permits exploration after either probe | only relevant result may expose singleton `H,q_R`; exact explore produces r8 |
| production source authority | core/preparer still pin the unresolved earlier memo | add Astra memo path/hash, explicit supersession, and schema/seed-domain successor |
| production validation | all release flags intentionally false | regenerate registry, construct certificate, tokenizer evidence, work joins, and profiles before enabling true flags |
| native runtime | constructor accepts scripted backend only | implement sealed native controller after preparation closes |

The private X-to-Z frontier should not simply be appended to `WorldCell.edges`: that structure currently implies an EVENT/receipt-bearing edge and feeds witnessed/full-memory renders. Give latent probe frontiers a separate private type and let the independent route oracle opt into them only for full-private shortcut/cut certification.

## Root-seal inputs

The production root/contract seal must commit, before any model output, to all of the following:

1. successor schema and canonicalization rule;
2. selected Astra memo path/hash and explicit supersession of prior unresolved/alternative D byte rules;
3. complete structural topology, including latent X-to-Z and old Z-to-Y, plus the distinction between latent frontiers and witnessed EVENT edges;
4. canonical node/port/event/link/probe/receipt/goal slot names and cardinalities, including r9/r10;
5. each root's opaque inventory and its real tokenizer qualification receipt;
6. all root/O/R/D/goal cube assignments, seeds, RA/RB assignments, and DEV primary choice;
7. exact reachout prompts, one-line PROBE result bytes, single-LF policy, relevant result-to-EXPLORE join, r8 receipt-to-EVENT join, terminal D behavior, and parsers;
8. private r9/r10 schema, mapping, predecessor rules, and the prohibition on semantic admission;
9. all ten projections, retention render, W0-W8, substitution classes, and negative/refusal grammar;
10. slot/replay/batch registries, counterpart maps, diagnostic addresses, cuts, and work/profile identities.

Scores, child outputs, admitted derivative bytes, losses, or observed behavior remain forbidden root-seal inputs.

The current `root_skeleton_digest` is insufficient because it omits the render registry and the chosen D source. A one-byte change to the result template, LF, endpoint placement, result join, terminal policy, or receipt schema must change the sealed production contract/root identity. Replay selection may then depend on that frozen identity but never on later child bytes.

## Exact 800-work joins

The zero-fit task denominator is unchanged by the Astra choice:

| panel | expansion | logical tasks |
|---|---:|---:|
| delayed | `4 excluded roots x 2 O x 2 R x 2 D x 2 goals x 10 projections` | 640 |
| reachout | `4 excluded roots x 2 O x 2 goals x 2 surfaces (RA/RB) x 5 projections` | 160 |
| total | | **800** |

Within that total, the expected top-level split is 704 one-shot actor tasks and 96 service-loop tasks: delayed 576+64 and reachout 128+32. A service loop may expand into multiple bound generations/lookups, but may not change the 800 logical-task denominator.

Every one of the 800 task records must have a one-to-one join to its presealed work identity and exact:

- stage/panel/projection/root/O/R/D/goal/render or surface;
- public system/user byte hashes and parser/scorer version;
- seed, C0 mount, input/output/returned-token caps, endpoint, ancestry, and denominator;
- service address roster and each possible generation/lookup continuation where applicable;
- chosen private postcommit result/state record for reachout, without adding another model attempt;
- profile/GPU UUID/accounting row and terminal collection identity.

The native runtime must consume these rows rather than independently reconstructing `runtime-test/...` tasks. The landed scripted planner's count of 800 is a useful fixture, but its `fixture_only=True`, ideal rows, hardcoded R=D=0 reachout cell, dynamically appended service instruction, and lack of work-registry joins do not satisfy this matrix.

## Adversarial cases that must fail before native release

1. Selected memo path/hash absent, changed, or accompanied by two simultaneous exact-byte authorities.
2. D frontier source/destination differs from X/Z, uses `u` rather than qD, becomes a witnessed EVENT, or is absent from the full-private shortcut oracle.
3. R and D use different port alphabets, are correlated, imbalanced, redrawn, or selected after an output.
4. Any result has the superseded four-line form, no final LF, CRLF, two LFs, trailing whitespace, extra terminal prose, a role/usefulness word, score, route, receipt ID, or hidden bit.
5. Relevant result contains qD, distractor result contains qR, endpoints/probe IDs mismatch the committed option, or result bytes are assembled from unsealed free strings.
6. r9/r10 are swapped, public, admitted as executed evidence, used in EVENT/LINK, exposed through READ, or included in a fit target.
7. A distractor or malformed commitment permits EXPLORE, a second generation, correction, retry, r8, EVENT/LINK, or authentic lineage.
8. A relevant commitment creates e8 directly from r9 without the exact `EXPLORE H q_R` and ordinary r8 receipt.
9. Toggling D changes a delayed route, prompt, authentic row, service response, fit roster, score, or route label.
10. Toggling R fails to change the required q port, or adding X-to-Z creates an alternate delayed path.
11. Any fixed-quartet pre-outcome byte/hash differs across R/D, any quartet is not exact 00/01/10/11, or computed information values differ from `(1,1,1,0)`.
12. OLD e0 or NEW e8 cut leaves a delayed route, or a registered cut changes its paired control mate.
13. Mnemonic node names, root labels, R/D, G_ handles, structural role, or hidden outcome appears in a model-visible render.
14. RA/RB order counts are unbalanced or their content differs beyond registered neutral surface/order.
15. Any complete result/result-join substitution class has unequal real-tokenizer counts, a forbidden ID collision, or incomplete receipt coverage.
16. A byte/state/receipt/render mutation leaves the production root/contract seal unchanged.
17. Any of the 800 logical tasks lacks exactly one work join, two tasks share an identity, a work row is orphaned, or runtime bytes/seeds/caps differ from the sealed row.
18. Production execution reaches a fixture-only path, ideal/oracle rows enter the backend or corpus, hidden cell/scorer state is passed to the actor, or a scripted result is promoted to native evidence.

## Release conclusion

Main's choice removes the prior exact-byte ambiguity and is compatible with the v2.2 scientific design. It is also deliberately close to the reserved current core: the one-line LF result, q0/q1 namespace, and r9/r10 slots already exist. The implementation still requires a schema-successor production world, render-sensitive seal, real tokenizer inventory, semantic 800-work joins, and native controller.

No scientific contradiction blocks that implementation. The only mandatory claim restriction is that the main experiment tests **relevant versus matched-uncertain irrelevant probing for a fixed shared frontier**, not goal-switched experiment selection, continual learning, parenting, or the whole organism.
