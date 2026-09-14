# PERSIST-CODE L1 bounded screen, September 14, 2026

Scope/intake: W1 conditional admission and current direct worker instruction;
invariant-preserving L1 experiment. No material thesis/base/visibility change.

Two readonly native actors start from identical portable 37ec; RICH=A1004,
TERSE=A1005. Each has its own persistent Python ledger module and records.
Tasks are precisely `build_tasks(count=8)`, IDs ledger_000 through ledger_007,
in order. The full L1 pool is 64 distinct specifications. Repeated structural
patterns deliberately permit experience reuse across episodes. Task specs and
helper semantics are public; deterministic test fixtures/reference evaluator
are not in actor context. On failure only the actual first counterexample
is returned; success reports the finite test count, not universal correctness.

Partition: L1 mining = integer-ledger-pipelines-v1. No held L1 family is
instantiated in this feasibility screen; unused same-family IDs are not
claimed as a transfer set. L2proposal structured-text-ledger-v1 and
heldL3proposal dependency-build-graph-v1 are scope-only, never generated,
mined, or admitted without Rohin. Exact proposal meanings are in worker journal.

At most five repair turns followed by one own-record turn, six maximum.
Every call <=1536 prompt tokens + <=512 generated tokens, thus <=2048 total.
RICH requests 150–400 first-person narrative tokens plus final JSON action;
TERSE requests only the same action. Equal maximum generation/call budgets;
actual tokens and wall time are reported, not assumed equal. Greedy native
generation, same base/adapter/tokenizer, no sampling or optimization/fit.
Only the last two own records are offered; whole older records are removed
if needed for the context cap, never silently truncate source text. The
immediately preceding expression and oracle feedback are shown for revision.
No other worker's native outputs are used. No public solution corpus.

Persistent ledger functions are accepted only after the task's deterministic
oracle passes and all earlier functions' tests remain green. The expression
AST permits only six pure bounded helpers, integer literals and `values`;
no filesystem, imports, attributes, loops, comprehensions, or arbitrary Python.
The independent reference uses direct arithmetic/list/set logic. This toy
repository tests reusable pipeline semantics, not realistic repo maintenance.

Primary diagnostic: paired task successes RICH versus TERSE /8; report all
task outcomes, record yield, failed-test -> changed-successful-repair -> own
record chains, per-call token distributions, regressions, and actual cost.
Fixed nonlearned baseline before readout: `sum(values)` on each task's tests.
Exploratory survival requires strictly more RICH successes, >=2 RICH complete
content-qualified episodes, and >=1 grounded correction+lesson chain. Anything
else deallocates this bounded screen, unless a new discriminating hypothesis
is explicitly proposed. Not a significance test or disproof of persistence.
No fits, scale campaign or best-checkpoint selection is admitted here.

Semantic review reads whole original turns with their actual inputs, previous
attempt, counterexample/outcome and action. PASS requires grounded evidence,
task relevance, checkable justified expectation, and meaningful applicable
revision/lesson rather than generic padding. Unsupported success claims,
invented observed facts, wrong helper relations, and unjustified expectations
FAIL; ambiguity is UNRESOLVED and excluded. Token bounds are a separate gate,
never semantic proxies. A complete candidate episode needs every original
turn semantically PASS, correct repairs, and a grounded own record. All raw
failures and exclusions remain preserved. No synthetic rewriting of targets.

Stored `student_prefix` omits the scaffold/parent instruction; child responses
alone are possible future targets. There is no loss computation now, and no
claim that raw candidate rows are training-admitted. Future prompted
consolidation uses the same child and its own experienced events; projection
is deterministic only. Future causal cycles compare guided+sleep against BOTH
frozen twin and unparented+sleep, with parent-free fresh-process evaluation;
autonomous collection is not a prerequisite. This paired screen alone cannot
isolate record utility from extra inference or demonstrate parameter learning.

Operational ceiling 1800 seconds per assigned GPU including setup/teardown,
maximum 96 native calls across both. Guard uses actual lease end
September27 05:05UTC (Main reconfirmed; notebook1233), with six-hour margin.
Source/archive, CPU pass, portable inventories and dated
preGPU publication must precede launch. Physical UUID/PIDs and existing /proc
CVD scanner with identity-bound service exceptions must be clear immediately
before use. Unknown owners are neither used nor killed. No process-name kills.
Source packaged locally on /data; A100 has no /data mount, so its observed
large-volume equivalent is `/localhome/local-rohing/data/` and root
`orch_persist_code_20260914_attempt1`. No evidence deletion or lease change.
