# FeltCraft standalone exact symbolic information kernel v7

Status: governance proposal only. It authorizes no implementation, test or
kernel execution, audit execution, review, receipt, compute, benchmark,
promotion, or scientific claim. Approval is not inferred.

V7 is a final bounded cleanup of V6 consensus SHA-256
`6be5b2c2da9f0f372dea38ab15177f3a357cfdbb08ca682e702bc8ed6c7cc68a`.
It makes exactly three repairs and no architecture, mathematics, scope, or
claim expansion.

1. Comparator protocol repair. Governance oracle records are split into call
   stimuli and expected results or exact expected error type/code/args. SKN06
   has explicit typed directed call/control edges to SKN02, SKN03, and SKN04,
   and distinct reverse observation-only edges. A candidate receives exactly
   one addressed stimulus during an invocation and never any expectation,
   other candidate stimulus, mismatch, or comparator state. Expectations and
   mismatches stay comparator-local; only aggregates and SK01--SK08 receipts
   flow from SKN06 to terminal SKN05. Comparator constants are independently
   bound governance input, not bytes forwarded by SKN01. SKN01 sees only real
   context path/hash/scope and ratification metadata.
2. Audit request repair. `scope_audit.request.json` has its own strict schema,
   `scope_audit_request.schema.json`, and contains no field for its own path or
   SHA-256. The later receipt separately records the request repository path,
   SHA-256 of the exact request-file bytes, and a byte-equivalent parsed copy of
   the request content validated against that request schema.
3. Audit-claim repair. Deterministic SK10 covers only fixed binding equality;
   recursive path/manifest/byte/hash/root-digest checks; diff path equality;
   JCS-plus-one-LF and request-schema validation; timestamp ordering;
   `ast.parse` success; and literal `Import`/`ImportFrom` inventory against the
   exact allowlist and fully specified local-path resolution. Every forbidden
   AST, CLI/options/stdin/environment/configuration, write-equivalence,
   dynamic/capability/reachability, and semantic Python judgment is performed
   by a fresh independent human source reviewer and explicitly adjudicated by
   human governance. None is called deterministic or a complete proof.

The exact requested scope remains the same three sorted atoms and the exact
forbidden scope remains the same eight sorted atoms. The standalone empty base,
six-node final registry, thirteen explicitly directed edges, two loops, six
claims, pi-inverse algebra, exact finite cardinalities, 72 copied vectors,
ordered 25 negative calls, exact DomainError behavior, fixed twins, 5/8/16/17
costs, 36,864 bridge cases, 73,728 deletions, LOCAL-not-atoms limit,
direct-graph MOTIF limit, and SK06/SK07 results are unchanged.

The golden protocol and version-bearing receipt identifiers advance to V7;
their values do not change. Runtime reports, comparator internals, audit
artifacts, reviewer evidence, and governance artifacts remain terminal and
cannot enter renderer, life, agent, model/provider/tokenizer, DREAM/SLEEP/
memory, LoRA/weights, GPU/remote, benchmark, promotion, paper, or scientific
stages. `passed` is governance evidence only and requires both the exact
deterministic subset and fresh/independent human attestations accepted by
explicit human governance adjudication.
