# Private typed-action provenance canary v2

Date: 2026-09-06

Status: architecture-deliberation candidate only. No implementation,
execution, model, tokenizer, task, tool, environment, trainer, adapter, GPU,
or scientific claim is authorized. The complete normative protocol is the
hash-bound advisory
`research_loop/advisory/20260906_private_typed_action_provenance_canary_v2_design.md`.
This plan converts that completed design into an exact deliberation surface;
it does not broaden or silently repair it.

## Decision question

Should the project authorize, after exact human ratification only, a strictly
CPU-local plumbing canary that asks one question:

> Can one deterministic source-bound child-stub response be bound
> byte-for-byte to one offered typed-tool schema, one parser decision, and one
> recomputable pure private mock transition in one prospectively written,
> atomically committed trace?

This is deliberately smaller than the rejected prospective action-trace
spine. It proves no learning, model intent, real tool behavior, secrecy,
public projection, recurrence, improvement, memory, dreaming, sleep,
consolidation, or Experience Models claim.

## Frozen topology

There is one private filesystem root, one single-writer lock, and one private
six-record JSONL ledger. The only roles are:

1. `HARNESS`, which opens the canary, freezes one invocation, writes the
   terminal close, and performs atomic publication;
2. `CHILD_STUB`, a deterministic source-bound process that consumes only the
   exact canonical child-request bytes and returns one closed response
   envelope;
3. `PARSER`, which consumes only the exact structured tool-channel bytes and
   either rejects them or derives one authorized typed call;
4. `PRIVATE_MOCK_ENV`, a total pure in-memory function over the frozen fixture,
   mock manifest, and dispatch bytes;
5. two source-distinct CPU validators and a comparator, which independently
   validate the committed artifact against a declarative oracle and produce a
   separately bound evidence receipt.

There is no public root or projection, no real environment, and no future-life
consumer. The broader spine's context selection, recurrence, retry,
supersession, declassification, parent, dream, sleep, trainer, adapter,
evaluation, and reporting nodes are absent.

## Exact artifact and lifecycle

The normative advisory freezes six records, in order:

1. `CANARY_OPEN / HARNESS`
2. `INVOCATION_PREPARED / HARNESS`
3. `CHILD_RESPONSE_RECEIVED / CHILD_STUB`
4. `TYPED_CALL_PARSED / PARSER`
5. `PRIVATE_DISPATCH_RECEIPT / PRIVATE_MOCK_ENV`
6. `CANARY_CLOSE / HARNESS`

The wrapper, closed payloads, ByteString form, canonical JSON rules, hash
chain, parent chain, manifest contents, parser authorization hash, transition,
rational score, terminal counts, resource envelope, validation order, and
stable failures are exactly those in the advisory. In particular:

- one successful path accepts one call and executes one valid pure transition;
- one rejection path records a rejected parse and a deterministic
  `NOT_EXECUTED/PARSE_REJECTED` receipt;
- `EXECUTED_INVALID` exists only for synthetic mutation fixtures and can never
  close or publish;
- action-looking assistant prose is inert;
- a second generation, accepted call, or dispatch is a hard error;
- every operation-authorizing record is fsynced before the authorized step;
- a partial is never resumed or promoted;
- publication is no-replace atomic rename followed by directory fsync;
- no committed canary is evidence without a complete canonical evidence
  receipt binding sources, schemas, manifests, oracle, fixtures, both
  validators, comparator, registry, and committed bytes.

The successful mock fixture remains exactly the advisory's three-action
vocabulary and transition law: initial measurement 20, action order
`simplify_cfg` then `fold_constants`, terminal measurement 12, reduced score
`2/5`. Exact canonical fixture and message bytes must be ratified artifacts;
post-ratification implementation may execute them but may not invent them.

## Two legal paths only

```text
INIT -> OPEN -> INVOCATION_FSYNCED -> RESPONSE_FSYNCED
     -> PARSE_ACCEPTED_FSYNCED -> DISPATCH_VALID_FSYNCED
     -> CLOSE_SUCCESS_FSYNCED -> COMMITTED

INIT -> OPEN -> INVOCATION_FSYNCED -> RESPONSE_FSYNCED
     -> PARSE_REJECTED_FSYNCED -> NOT_DISPATCHED_FSYNCED
     -> CLOSE_REJECTED_FSYNCED -> COMMITTED
```

Any crash before committed publication yields an ineligible quarantined
partial. The pure mock has no external effect, so the local ledger commit does
not claim real-tool atomicity.

## Validation and resources

Both validators must be source-distinct and must not import canary
implementation helpers. Their shared surface is limited to the ratified
schemas, standard JSON/base64/SHA-256 primitives, and the declarative oracle.
They apply the advisory's exact first-error order from `E_RESOURCE` through
`E_EVIDENCE_BINDING`.

All work is deterministic CPU-only. Limits are exact: six records and six LF
bytes; 262,144 encoded ledger bytes; 131,072 aggregate decoded ByteString
bytes; 65,536 decoded bytes per ByteString; 131,072 encoded bytes per line;
JSON depth 8; 32 ByteStrings; 1..4096 input IDs; 0..512 generated IDs; and
1..16 accepted actions. The canary makes no wall-clock or memory-usage claim.

## Required pre-claim tests

The exact PC1--PC9 registry from the advisory is mandatory:

- PC1 golden success and rejection;
- PC2 structured-channel provenance mutations;
- PC3 prose is inert;
- PC4 transition and action-order recomputation;
- PC5 total linear lifecycle;
- PC6 crash/publication matrix;
- PC7 coordinated relational mutations;
- PC8 exact and one-over resource boundaries;
- PC9 evidence-receipt binding.

Every fixture is immutable and content-addressed. The mutation matrix includes
coordinated downstream rehashing, so one-sided checksum failures cannot stand
in for relational validation.

## Maximum claim

Only after deliberation, exact human ratification, scoped CPU implementation,
PC1--PC9, and fresh independent audit may the project state:

> In the registered deterministic-stub/private-mock fixture, the committed
> six-event trace prospectively bound one exact child request and response to
> one offered typed-tool schema, one parser decision, and one recomputable pure
> private transition, under the registered byte, lifecycle, durability, and
> resource checks.

This sentence is not headline-eligible and may not be generalized to a model,
tokenizer, real tool, private/public information-flow guarantee, benchmark,
learning system, or GPU result.

## Authority boundary

This candidate itself authorizes nothing. Deliberation may recommend rework,
reject, defer, or an exact human decision. Model agreement cannot ratify. If
and only if a releasable consensus exists, Rohin must approve the exact change,
context, consensus, and sorted scope bytes. A later implementation supervisor
must revalidate that chain before any file outside the deliberation artifacts
is authored or any test is executed.

Replacing the child stub with a model, the pure mock with CompilerGym or any
real tool, adding public projection, recurrence, parenting, dreaming, sleep,
LoRA, evaluation, or GPUs is a new material change with a new deliberation and
ratification.
