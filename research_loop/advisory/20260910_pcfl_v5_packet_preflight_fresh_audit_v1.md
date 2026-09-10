# PCFL V5 deliberation-packet fresh preflight audit — v1

Date: 2026-09-10

Status: **BLOCK before approval of the configured V5 deliberation**. This is a
read-only governance audit of the already initialized, zero-attempt packet. It
is not a ratification and grants no source-authoring, preparation,
implementation, execution, model, scientific, GPU, resource, claim, release,
or submission authority.

## 1. Exact packet inspected

The audit completely read the governing `AGENTS.md`, the V4 consensus, all
three V5 repair advisories, the integrated V5 source-authoring candidate, the
V5 source-authoring plan, directive, scope proposal, workflow, and initialized
hidden runner state. It also checked the runner's role and write boundary and
the predecessor bytes needed to evaluate the packet's declared context.

The initialized V5 control hashes are:

| Artifact | SHA-256 |
|---|---|
| `research_loop/workflows/pcfl_m0_mtext_bound_v5.deliberation.json` | `1dfc7328418689be874f96538b1a9182ef9ffa4c4897437348ad1d8f1a403a9d` |
| `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v5.deliberation.state.json` | `05de3604cf4430ec2fdb6ecb83bdaee7d15b01e8f4d42a1415046962946104ee` |

The hidden state is structurally pre-run: `phase="advocate_pending"`, all five
attempt counts are zero, `artifacts={}`, `human_required=true`, and
`implementation_authorized=false`.

## 2. Exact blockers

### BLOCK-V5-PREFLIGHT-001 — the declared complete V4 chain is incomplete

Evidence:

- `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v5/human_directive.txt:30-33`
  directs the roles to adjudicate the "complete V4 chain".
- The architecture contract begins the durable chain with the verbatim
  directive (`AGENTS.md:4-12`).
- `research_loop/workflows/pcfl_m0_mtext_bound_v5.deliberation.json:11-20`
  lists the V4 workflow, scope, five role artifacts, intake state, runner state,
  and integrated candidate, but omits
  `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/human_directive.txt`.
- The initialized V5 state's bindings at
  `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v5.deliberation.state.json:33-70`
  reproduce the same omission. The predecessor hidden state binds only the
  omitted directive's digest; it does not supply its verbatim bytes to the V5
  roles.

Impact: the role contexts cannot literally read every byte in the chain they
are instructed to adjudicate. This is a context-completeness and exact-binding
failure, even though the new V5 directive repeats the standing directives.

Smallest repair: preserve the initialized zero-attempt V5 state, fork a new
change/workflow/state identifier, add the exact V4 `human_directive.txt` path to
`context_files`, and initialize new bindings. Do not refresh or delete the
existing initialized state in place.

### BLOCK-V5-PREFLIGHT-002 — the closed handoff graph cannot represent three retained baselines

Evidence:

- The authority repair defines the renderer's first-turn input as exactly
  `ModelTurnPublicV4` and provides no static-context, baseline-channel, corpus,
  graph, or retrieval field
  (`research_loop/advisory/20260910_pcfl_v5_authority_handoff_delayed_v7_source_repair_v1.md:354-377`).
- The same repair declares its consumer edges exhaustive and forbids every
  unlisted edge. It contains only `COMMON_READER`, with no RAW-context,
  BM25/RAG, or native-graph producer/reader edge
  (`research_loop/advisory/20260910_pcfl_v5_authority_handoff_delayed_v7_source_repair_v1.md:395-428`).
- The resource repair nevertheless requires `RAW_CONTEXT_RECURRENT` to place
  raw rows in static context, `RAG_RAW_RECURRENT` to use deterministic BM25,
  and `NATIVE_GRAPH_RECURRENT` to place a native graph in static context
  (`research_loop/advisory/20260910_pcfl_v5_provenance_resource_repair_v1.md:68-87`).
  It preserves these as deliberately unequal alternative channels at
  `:249-256`.
- The integrated V5 candidate retains all 18 conditions and adopts both the
  exact handoff graph and those baseline/resource contracts
  (`research_loop/plans/pcfl_m0_mtext_exact_v5_source_authoring_candidate.md:51-73`,
  `:113-137`, and `:274-292`).

Impact: exact source authors would have to make an outcome-changing choice:
smuggle baseline content into an existing field, add an edge forbidden by the
normative graph, or leave three registered arms without an input path. None is
authorized by the current bytes.

Smallest repair: in a newly bound successor, define closed baseline-specific
public projection type(s) for RAW context, deterministic RAG retrieval, and
native graph context; add their typed producer/consumer/renderer edges; specify
their reset, padding, identity, ordering, and leakage/noninterference rules;
and update the exact handoff schemas, consumer graph, mutation tests, candidate,
source plan if a new path is needed, workflow, and bindings. Removing the three
arms is also possible but changes the registered design and requires the same
fresh deliberation boundary.

## 3. Checks that otherwise pass

- Every one of the 21 initialized V5 source bindings rehashed to the digest
  recorded in hidden state, including the directive, workflow, V4 artifacts,
  three V5 repairs, V5 candidate, source plan, and scope proposal.
- The candidate's four normative-input hashes match the current V4 integrated
  candidate and the three current V5 advisory bytes.
- The V4 consensus is preserved as `recommendation="rework"` and
  `state="human_required"`; its eleven unresolved design dispositions map
  disjointly and completely across the repairs as 4 authority/handoff/delayed/
  V7 items, 5 endpoint/neutrality/claim items, and 2 provenance/resource items.
- `source_authoring_plan.json` conforms to the stated `SourceAuthoringPlanV1`
  shape. It has exactly 24 unique, NFC/ASCII, repository-relative, bytewise
  sorted literal paths: 23 rows with `manifest_member=true` plus the one
  `normative_source_manifest.json` output row with
  `role="NORMATIVE_SOURCE_MANIFEST"` and `manifest_member=false`. Roles, media
  types, and positive byte maxima are within the closed vocabulary. No plan row
  is a directory, glob, absolute path, unresolved variable, `..` path, or
  symlink.
- The source plan contains all four repairs' explicitly required minimum
  surfaces: exact public/private handoff schemas, projection allowlist,
  consumer graph, delayed entitlement, V7 boundary, and manifest output. It
  also allocates files for integrated semantics, transition/failure tables,
  object schemas, provenance, claims/endpoints, resources/runtime, CAS,
  preparation, materialization, two checkers, mutations, and tests.
- The 18-condition roster arithmetic is internally correct:
  `2*43 + 8*39 + 2*26 + 1*4 + 3*13 + 2*4 = 501` slots/root;
  generated allowance is `148,224` tokens/root; input allowance is
  `4,104,192` tokens/root; and the DEV, confirmation, sentinel, grand, and
  reserve totals recompute to the registered values.
- Requested and forbidden scope arrays are nonempty, sorted, unique, disjoint,
  and explicit that deliberation does not confer later authority.
- The workflow has exactly the five required roles. Systems and benchmark are
  separate fresh-context interpretations and cannot see each other's result;
  critique and consensus receive the required upstream artifacts.
- Every bound context file is below the configured
  `max_context_chars_per_file=300000`, so the runner's per-file truncation rule
  would not truncate this packet.

These passing checks do not compensate for either blocker.

## 4. Deliberation-only authority boundary

Apart from the two packet defects, the configured runner is authority-safe for
its stated five-role purpose:

- each Codex role is invoked with `allow_write=false`, which selects the
  read-only role sandbox;
- the runner itself writes only bound prompts, schemas/logs/results, the five
  canonical architecture artifacts, and its deliberation/intake state;
- it does not call planned PCFL source, a checker, materializer, benchmark,
  tokenizer, scientific model, or GPU workload;
- it has no ratification transition; and
- it must stop at `human_required` with `implementation_authorized=false`, even
  if consensus recommends proceeding.

Therefore running the configured roles would not itself cross into source
authoring or scientific execution. Approval is nevertheless blocked because
the roles would deliberate an incomplete predecessor context and mutually
incompatible handoff/baseline bytes.

## 5. Audit execution statement

No PCFL source file, fixture, root, data, checker, materializer, benchmark,
model, tokenizer, scientific workflow, GPU job, resource acquisition, claim,
release, or submission was executed or authorized during this audit. No file
other than this advisory was created or edited.
