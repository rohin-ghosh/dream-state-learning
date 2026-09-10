# PCFL V6 deliberation-packet fresh preflight audit — v1

Date: 2026-09-10

Status: **BLOCK before approval of the configured V6 deliberation**. V6 closes
the V5 predecessor-context omission, but its replacement baseline projection is
not yet an exact closed type/consumer/runtime contract. This audit is not a
ratification and grants no source-authoring, preparation, implementation,
execution, model, scientific, GPU, resource, claim, release, or submission
authority.

## 1. Exact packet and initialized state

The audit read the V6 directive, scope, workflow, hidden state, source plan,
integrated candidate, baseline-projection repair, and the inherited artifacts
needed to check both V5 preflight blockers and the V6 precedence claims.

Current V6 packet hashes are:

| Artifact | SHA-256 |
|---|---|
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/human_directive.txt` | `948eb76c5912c002a2b1b33d5b005cb7d35e5c61ee918e392c6337ba5a239ff4` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/scope_proposal.json` | `497b0a8cc5921c84079bfed0511c3e8eb55748f2cfd66747f75aec3ef216d8f1` |
| `research_loop/workflows/pcfl_m0_mtext_bound_v6.deliberation.json` | `11076a8a5cd137f1e005836d9ac37c86c8c6e1e3ed46ea96912bafb5c34be9d9` |
| `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v6.deliberation.state.json` | `0d02f33b10ac053292a81beb5280a7e5398617fa2b21ba836c8c1b96fe90b4fc` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/source_authoring_plan.json` | `2356cab6d9f0d521897497a3e8f85efdd06ebb436c6285264ffd9d47502ddbf8` |
| `research_loop/plans/pcfl_m0_mtext_exact_v6_source_authoring_candidate.md` | `74134a0545816d1cfd9edeb3229d77bc83261fa6582cd0f8dd459df1102d822f` |
| `research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md` | `12960868a1cafb820e33600482866a6387538280e8baeb698d59c8a4072d44ee` |

All 30 source bindings in the initialized state rehash exactly. The state is
pre-run: `phase="advocate_pending"`, every attempt count is zero,
`artifacts={}`, `human_required=true`, and `implementation_authorized=false`.

## 2. Disposition of the two V5 blockers

### V5 predecessor-context blocker: closed

The V6 directive requests the complete V4 chain at
`research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/human_directive.txt:30-34`.
The V6 workflow now directly includes the missing V4 directive at
`research_loop/workflows/pcfl_m0_mtext_bound_v6.deliberation.json:11`, and the
hidden state binds it at
`.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v6.deliberation.state.json:33-35`.
It also binds the frozen zero-attempt V5 packet and its preflight rejection.

### V5 missing baseline-path blocker: partially closed, still blocking

V6 adds typed RAW, RAG, and native-graph public surfaces, model projections,
and named consumer nodes. That closes the gross absence identified in V5, but
the following exactness and graph defects remain.

## 3. Exact blockers

### BLOCK-V6-PREFLIGHT-001 — new projection fields have no complete allowed dataflow

The replacement `ModelTurnPublicV4` requires `memory_mode` and makes memory
returns/surfaces mode-dependent
(`research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md:160-188`).
The same repair says its consumer graph remains closed and adds only the edges
at `:193-208`. Those edges route static context and the RAG corpus/result, but
they do not route:

- `VERIFIED_PUBLIC.memory_surface.mode` to `ModelTurnPublicV4.memory_mode` or a
  typed controller/projector;
- `VERIFIED_PUBLIC.memory_surface.read_protocol` to the public controller that
  must admit `RAG_READ` or other legal read forms; or
- an identity-null surface to any identity-null reader and back to the public
  controller.

The inherited V5 graph gives `PUBLIC_CONTROLLER` only phase mode, initial view,
action catalog, budgets, and response schema; it has no generic entitlement to
consume the new memory-surface fields. V6 explicitly says every other new edge
remains forbidden at `:215-224`. Consequently an author cannot populate the
required `memory_mode`, select the declared read protocol, or execute an
identity-null return without inventing a forbidden edge.

Smallest repair: add exact field-level edges from the verified public memory
surface to a typed mode/protocol projector and public controller, then to the
corresponding `ModelTurnPublicV4` fields; add the exact identity-null reader
input/output path; and include negative edge mutations. Preserve private
condition/route/scorer denial.

### BLOCK-V6-PREFLIGHT-002 — one identity-null tag cannot derive the three inherited control behaviors

The legal-mode table places `REACHOUT_OFF`, `NO_MEMORY`, and
`PASSIVE_SIGNATURE` under one `IDENTITY_NULL_READER` mode with the same null
payload and `IDENTITY_NULL` protocol
(`research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md:60-69`).
However, the inherited exact resource roster requires REACHOUT_OFF and
NO_MEMORY to return fixed-size `BLOCKED` behavior without lookup, while
PASSIVE_SIGNATURE returns a condition-independent null envelope
(`research_loop/advisory/20260910_pcfl_v5_provenance_resource_repair_v1.md:68-79`).

The public union contains no discriminator for those distinct outputs, and V6
forbids private condition influence on the baseline reader. The candidate's
phrase “fixed null/BLOCKED behavior” at
`research_loop/plans/pcfl_m0_mtext_exact_v6_source_authoring_candidate.md:61-64`
does not choose an exact status/envelope law. Source authors would have to pick
which behavior applies or consult a forbidden private label.

Smallest repair: split the public mode/protocol into exact `BLOCKED_READER` and
`PASSIVE_NULL_READER` cases, with closed fixed-size return schemas and edges,
or normatively replace all three inherited behaviors with one exact behavior
and re-disposition their resource/endpoint meanings.

### BLOCK-V6-PREFLIGHT-003 — deterministic RAG bytes and scoring remain underdefined

The RAG section leaves several outcome-changing choices open
(`research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md:119-154`,
`:173-188`):

- `public_document_handle` is only `string`; its exact grammar, width, and byte
  assignment are absent;
- the state/goal/last-event query has no canonical term sequence, multiplicity,
  separator, or byte preimage;
- `k1=1.2`, `b=0.75`, document frequency, and top four do not select a complete
  BM25 variant: IDF equation, query-term treatment, length definition, numeric
  arithmetic/rounding, and equality comparison remain unspecified;
- `RagReturnPublicV4` is referenced but has no closed field/type/status/slot
  schema; and
- the public query fingerprint has no domain tag or canonical preimage
  encoding.

These choices can change ranks, returned bytes, token/resource counts, padding,
and model-visible evidence, so chronological handle tie-breaking alone is not
sufficient.

Smallest repair: bind an exact handle grammar; canonical query term list and
byte serialization; complete BM25 equation and deterministic arithmetic;
closed four-slot return/status/padding schema; and a domain-separated canonical
fingerprint preimage, with positive goldens and one mutation per field/ranking
choice.

### BLOCK-V6-PREFLIGHT-004 — TARGET_ONLY read protocol conflicts with its retained opportunity contract

The V6 legal-mode table assigns TARGET_ONLY P/D phases
`NO_MEMORY_SURFACE` with `read_protocol="NONE"`
(`research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md:62-70`).
The inherited exact roster retains 24 READ opportunities/root for
`TARGET_ONLY_ANSWER_PRIOR_TAPE` and says its no-memory READ commands are
`BLOCKED`
(`research_loop/advisory/20260910_pcfl_v5_provenance_resource_repair_v1.md:55-59`,
`:86-87`). V6 simultaneously claims no roster/opportunity change.

`NONE` does not specify an advertised blocked READ command or a component that
can consume its 24 opportunities. Treating them as absent changes the fixed
interface/opportunity match; treating them as present requires an unregistered
protocol and edge.

Smallest repair: assign TARGET_ONLY an exact blocked-reader public
mode/protocol with the retained 24 executor-side READ opportunities and typed
fixed-size `BLOCKED` result, while preserving that no memory or future handles
are available. Changing the count would instead require explicit roster,
resource, and no-change revisions.

## 4. Checks that otherwise pass

- The V6 normative hashes in the integrated candidate match the current V4,
  V5, and V6 bytes.
- V6 preserves V5's initialized zero-attempt state rather than refreshing it.
- The V6 source plan has exactly 24 unique, ASCII/NFC, bytewise-sorted,
  repository-relative literal paths: 23 manifest members and one non-member
  manifest output. Its roles, media types, positive maxima, change ID, and
  manifest membership satisfy the inherited `SourceAuthoringPlanV1` contract.
  No row is a directory, glob, absolute path, `..` escape, unresolved variable,
  or symlink.
- The existing planned object-schema, handoff-schema, projection, consumer,
  runtime/resource, test, and mutation members are sufficient homes for a
  repaired baseline contract; no new path is intrinsically required.
- RAW_STATIC and NATIVE_GRAPH_STATIC are explicitly static unequal-resource
  channels with zero reader opportunities; RAG is explicitly an unequal
  deterministic-retrieval channel with up to eight pre-action reads. Their
  scientific endpoint applicability remains substrate-neutral PB/DB with
  common-reader PM/DM excluded, consistent with the inherited endpoint matrix.
- Delayed baseline surfaces are tied to the model-independent supplied D
  fixture and exclude U model output and session/cache survivors.
- Resource language charges static context, corpus/index construction,
  retrieval work, returned bytes/tokens, calls, and artifacts and preserves the
  prohibition on equal-resource or scalar-efficiency claims.
- The 18-condition, 501-slot, 148,224-generated-token/root, and
  4,104,192-input-token/root arithmetic remains unchanged and correct.
- Requested and forbidden scope arrays are sorted, unique, disjoint, and limit
  the present action to nonauthorizing five-role deliberation.

These passing checks do not compensate for the four blockers.

## 5. Deliberation-only execution boundary

The configured V6 runner remains within deliberation-only authority:

- it has exactly advocate, systems, benchmark, critique, and consensus roles;
- systems and benchmark receive independent fresh contexts;
- each Codex role runs with `allow_write=false` in the read-only role sandbox;
- runner writes are limited to bound prompts, response schema/log/result
  records, canonical architecture artifacts, and deliberation/intake state;
- it has no ratification transition and must stop at `human_required` with
  `implementation_authorized=false`; and
- it does not execute authored PCFL source, preparation, checkers,
  materialization, benchmark/model/tokenizer science, or GPU work.

Thus the configured run is authority-safe, but approval is blocked because its
roles would adjudicate baseline bytes whose public dataflow, control returns,
RAG scoring/wire format, and TARGET_ONLY read semantics are not yet exact.

## 6. Audit execution statement

No deliberation role, PCFL source, fixture, root, data, checker, materializer,
benchmark, model, tokenizer, scientific workflow, GPU job, resource
acquisition, claim, release, or submission was executed or authorized during
this audit. No file other than this advisory was created or edited.
