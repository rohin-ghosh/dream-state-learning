# PCFL Transition-Path visibility, taint, and reset contract

Status: proposed material design only. Any implementation must fail closed on
this contract before P1. The prior Bubblewrap receipt is not inherited: it did
not cover this model-facing transition interface.

## 1. Information and taint classes

| Class | Contents | Model-visible? |
|---|---|---|
| `T_PUBLIC_SOURCE` | Exact public source-event prefix and event provenance | Compiler only; not placed in the P1 target prompt |
| `T_PUBLIC_TARGET` | Current state, two action IDs, goal state, uniform caps | Resolver, reader query validator, parser, executor |
| `T_SEMANTIC` | Frozen compiled atoms and the arm's permitted reader returns | Assigned reader/resolver only |
| `T_HIDDEN_WORLD` | Topology coordinates, bits, twin side, correct paths, alternative-world execution | Constructor/certifier and post-freeze scorer only |
| `T_TARGET_MANIFEST` | Target IDs, cell/depth/age labels, goal pairing, cut and sham sets, split roots | Allocator/certifier and post-freeze scorer only |
| `T_TREATMENT` | Arm name, corpus/index root, lag/cross/cut key, memory capacity | Assigner/installer and post-freeze analysis only; resolver sees only uniform interface behavior |
| `T_OUTCOME` | Earlier target/model outcomes, aggregate statistics, pass/fail state, timing, retries, resource aborts | Terminal analysis/gate only |

Taint propagates to every value, filename, ordering decision, count, length,
rank, omission, error, retry, timing branch, cache entry, RNG state, prompt,
conversation, index, adapter/optimizer placeholder, workspace object, log, and
receipt derived from a class. Renaming or hashing a value does not remove taint.
Only explicit public projections defined in `world_contract.md` declassify
constructor output.

## 2. Descendant contract

| Descendant | Allowed input | Forbidden input | Output and only post-exit consumer | Shape and reset obligation |
|---|---|---|---|---|
| Hidden sampler | Pinned generator version; split/index domain; ID/order/age/binding RNG streams | Prior outcomes; compiler/model state | Hidden world closure to certifier and scorer | New domain-separated streams per pair; no rejection/resampling |
| Opaque-ID allocator | Topology and ID RNG only | Binding bits; target result; treatment | Fixed-width public IDs to renderer; private map to certifier | Same inventory/length across H/tau; allocator state destroyed after closure |
| Target allocator/certifier | Topology, age template, split root | Binding outcomes, source/compiler success, model outcomes | Sealed private manifest/root to scorer; public target projection later to resolver | Total allocation before source events; no duplicate replacement |
| Twin constructor | Hidden world closure | Outcomes or treatment | `tau(H)` closure to source renderer/scorer | Exact involution; no shared mutable bit table between sides |
| Source scheduler | Presealed start/action order and propensity-one ledger | Targets/goals, binding outcomes, treatment, prior results | One assigned action slot at a time to renderer | Exactly 240 slots/life; no outcome branch/retry; state reset each one-step episode |
| Source renderer/event writer | Current public state/action/outcome projection | Tree/depth/age/target/twin labels; proofs; scores | Canonical public event bytes to immutable source store | Fixed JSON union; fixed-width error sentinel; one LF; no optional keys |
| Source store | Public events only | Hidden manifests and outcomes | Read-only prefix to compiler; full bytes to audit | Separate immutable store per side; never reused across pair/split |
| Event parser | Public prefix | Targets, treatment, hidden truth | Typed public events to canonicalizer | Total strict parser; malformed slot retained as failure; no recovery query |
| `WCANON-T1` canonicalizer | Typed public events and hashes | Goals/targets, topology, age, truth, arm/capacity, prior results | Frozen atoms/corpus root to indexers and installer | Fresh process/state per side/snapshot; deterministic order; no model/provider call |
| Linked indexer | Frozen atoms | Targets/goals, truth, outcomes | Forward/reverse indices and byte/work ledger to linked reader/analysis | Target-independent construction; fresh empty index; no persistent cache |
| Flat-bag builder | Same frozen atoms; independent order stream | Targets/goals, truth, outcomes, linked indices | Atom bag and order/work ledger to scan reader/analysis | Fresh bag; stores no endpoint/adjacency index |
| Exact-graph builder | Eligible frozen public atoms only | Hidden transition table/proof path | Public graph to typed controller and audit | Rebuild from empty state per side; graph root differs from hidden closure root |
| Split/arm assigner | Sealed split/arm schedule and frozen object roots | Target/model outcomes; compiler usefulness | One opaque installation instruction to installer | Presealed order; no cell deletion/replacement; treatment labels withheld downstream |
| Memory installer | Assigned immutable object | Hidden truth/proofs; prior results | Uniform reader handle to prompt/reader | New process and empty caches per target episode; validates exact root |
| Prompt builder | Frozen common system bytes, one public target, uniform reader schema | Arm name, depth/age/cell, truth/path, prior outcomes, scan progress/timing | Exact prompt bytes to pinned provider transport | Constant template/order; no filenames; fresh conversation each arm/target |
| Provider transport | Exact prompt/conversation bytes and pinned model manifest | Any other file, URL, network payload, secret, target history, prior result | Response bytes to parser; resource counters to terminal sink | One attempt, no retry/fallback; no cross-target conversation/cache |
| Model conversation | Target prompt and permitted reader returns | Source stream, hidden manifests/truth, arm label, other target/arm outcomes | Query or final operation bytes to reader/parser | New conversation per episode; deleted after immutable audit copy |
| Query validator | Current public target plus immediately prior permitted return | Hidden parent/path; full corpus; future result | Valid typed query to reader or fixed rejection to parser/audit | Maximum four; dependent-chain rule; constant error schema |
| Linked reader | Valid query and assigned linked object | Goal object as a whole, truth, score, other arms | One exact atom or `NOT_FOUND` to model conversation | Fixed fields/width; no rank/count/cache/timing; fresh empty cache |
| Flat scan reader | Valid query and assigned bag | Linked indices, truth, score, other arms | Same return bytes as linked reader; work count to terminal sink | Full counted scan; scan progress/order/timing hidden; fresh state |
| Response parser | Model response and strict operation schema | Hidden truth; corrective feedback; scorer messages | Parsed action list or one failure record to executor/scorer | No repair, reprompt, prose tolerance, or alternate parser |
| Action executor | Actual hidden world, parsed operations, public start/goal | Memory object, compiler state, other-arm outcomes | Immutable state trajectory and terminal return to scorer | Fresh target specimen; four moves plus one commit max; no model feedback |
| Offline scorer/counterpart replay | Frozen target manifest, hidden H/tau closures, immutable executed path | Unfrozen cognition or writable upstream channel | Item outcomes and directional twin/cut fields to terminal analysis | Starts only after session closes; output path cannot be imported upstream |
| Statistics/gate | Complete assigned ledger including zeros/NOT_RUN and resource counts | Editable target/model/compiler state | One terminal `STOP`, `NOT_RUN`, or `REQUEST` receipt to human | Pure aggregate; no threshold change; no automatic dispatch |
| Resource monitor | Process/provider counters and frozen caps | Hidden answers or decision authority | Append-only cap/abort receipt to scorer/gate | Out-of-cap terminates; it never supplies feedback to model/compiler |
| Audit sink | Copies of declared public/model/action/resource artifacts | Authority to mutate or promote | Immutable P0/P1 evidence bundle for fresh review/human inspection | Write-only during stage; never a cache or input to another target |
| Reset/cleanup | Explicit object registry and stage end signal | Hidden choice of what to preserve | Zero-live-object receipt to next assigned episode | Clears process, conversation, reader, index/bag handle, prompt workspace, RNG cursor, temp files, caches, environment instance, and provider session |

## 3. Constant-shape and metadata rules

H/tau source slots have identical event schemas, action choices, counts, order,
and fixed-width IDs; only legitimate public `next_state_id` observations may
differ. Goal-pair public inputs differ only in `goal_state_id`. Before memory
installation, target-visible bytes are identical across treatment arms.

Reader `FOUND`, `NOT_FOUND`, and validation-error responses have the same keys
and fixed-width payload fields. The model never sees candidate count/rank,
index size, scan progress, filenames, host/process IDs, cache hits, wall-clock
times, retries, error stack traces, treatment label, or resource balance.
Arm order is sealed and arm names are absent from prompts. There is no provider
fallback and no retry, so retry count cannot encode success.

Provider/model identity and interface differences are part of the declared P1
treatment, not hidden evidence about a memory substrate. P1 makes no LoRA or
reader-efficiency claim.

## 4. Reset boundaries

The following reset is mandatory before every `(pair, side, target-member,
arm)` episode:

- new target-world specimen at its declared start;
- new model conversation and provider request chain;
- new prompt/workspace/query-chain state;
- read-only reopen of the exact assigned corpus/bag/index root;
- empty reader/candidate/result cache;
- no adapter, optimizer, trainer, gradient, or weight state;
- new parser/executor and resource counters;
- domain-separated action-order seed where applicable;
- no data from the other world side, target goal, arm, split, or prior result.

After each world-life and at stage exit, the runner enumerates all registered
live objects and requires zero unapproved handles. Failure is retained; it is
not repaired by rerun.

## 5. Visibility mutation certification

P0 must inject one tagged sentinel into every forbidden class and into every
listed derived channel: value, hash, filename, ordering, rank, count, omission,
length, retry, error, timing, cache, RNG, conversation, index, workspace, and
resource branch. Exact prompt, compiler input, reader response, and model-bound
byte scans must find zero forbidden tags. Removing any one guard must make its
corresponding mutant fail. P0 also runs sequential H/tau, target, arm, and split
orders in both directions and requires byte-identical allowed outputs and zero
undeclared carryover.

## 6. Violation semantics

A visibility/reset/call-boundary violation found before the first P1 provider
response makes the whole P1 environment `NOT_RUN`. Once any P1 response exists,
an affected episode and every unexecuted assigned episode score zero; the run
stops without retry, repair, replacement, or threshold change. A violation can
never become evidence against a scientific hypothesis, and neither outcome
authorizes a successor.
