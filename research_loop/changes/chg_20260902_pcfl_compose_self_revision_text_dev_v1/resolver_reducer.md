# Shared resolver reducer v1

**Status:** hash-bound proposal specification; no implementation authority.

## State

Every recurrent Dream and Think invocation uses the same parser and pure state
reducer over the tuple:

```text
(mode, representation, objective_hash, public_state_hash,
 eligible_store_hash, workspace_nodes, candidate_state,
 staged_prediction, last_read_receipt, action_state,
 counters, terminal_status)
```

`mode` is `DREAM1`, `DREAM2`, or `THINK`; `representation` is
`OPAQUE_NOTE` or `OPERATOR_AST`. Inputs differ by mode, but the tuple shape,
canonical encoding, parser, counter order, workspace operations, and failure
semantics are identical. The reducer receives one parsed `RESOLVER_STEP`, the
current tuple, and a mode-specific capability allowlist; it returns one new
tuple plus at most one external-effect request. It never calls a model, reader,
actor, scorer, or private store itself.

## Universal accounting order

Before parsing a response, charge one model call and its exact input/output
bytes and tokens. A parse/schema/UTF-8/cap failure increments `malformed` and
the operation counter, preserves every scientific byte, leaves all other state
unchanged, and may consume only the registered PASS/malformed allowance. There
is no semantic repair. A byte-identical infrastructure replay, where allowed,
is a separate receipt and never replaces the first scientific row.

For a valid step, charge the operation and the relevant read/cognitive/predict/
action counter before applying it. Exceeding a cap is terminal failure with no
mutation. Every array preserves authored order; every object is canonically
serialized as UTF-8, sorted keys, separators `(',',':')`, Unicode NFC only at
the opaque reader boundary, and no hidden whitespace rewrite.

## Shared operations

- `READ(locator)`: validate the locator type against the mode's sealed eligible
  store. Emit exactly one external read request. On receipt, set
  `last_read_receipt` to the immutable object/hash or `NOT_FOUND`; do not
  alter workspace/candidates/actions. Dream locators are one E/A/C handle.
  Think locators are one LEXICAL or AST query. Reader internals never enter the
  reducer.
- `NOTICE(node)`: append one new node with at least one eligible premise from
  `last_read_receipt` or an existing node. No other field changes.
- `CONNECT(node)`: append one new node with at least two distinct eligible
  premises. No other field changes.
- `REVISE(node)`: replace exactly one existing node named among premises and
  require at least one additional eligible event/read/node premise. The old
  node remains in the append-only trace; only the live workspace pointer
  changes.
- `PASS`: change no scientific state; only counters/trace advance.
- `ABSTAIN`: terminal in every mode, with no action and no active Dream memory.

Node IDs are unique within a call sequence. A node can cite only an eligible
public event/read object or an earlier node, so the reducer can reject cycles
without interpreting content. Opaque text and AST payloads use the same
premise graph and mutation logic.

## Dream-only operations

- DREAM1 `PREDICT` adds or replaces exactly one `C01`/`C02` candidate and the
  exact `A1,A2` prediction set. It changes no workspace node.
- DREAM1 `COMMIT` is terminal and must repeat the current ordered candidate
  state byte-for-byte. The exact model response is the DREAM1 commitment.
- DREAM2 `PREDICT` stages exactly one `RETAIN` or `REVISE` choice and exact
  `B1,B2`. RETAIN's representation/content must equal a candidate package
  previously obtained by READ. REVISE must cite a read candidate plus public
  evidence and emit one replacement in the same representation. Mixed opaque/
  AST content is invalid.
- DREAM2 `COMMIT` is terminal, contains no new prediction, and repeats the
  staged representation, decision, parents, content, and citations exactly.
  The standalone DREAM2 artifact is a deterministic envelope of these exact
  COMMIT bytes plus the previously staged predictions; its construction adds
  no authored field.

Dream cannot `USE` or `LOCK`. DREAM1 cannot read C/A handles. DREAM2's eight
reads are partitioned exactly as specified in `experiment_spec.md`.

## Think-only operations

- `USE(action)` emits exactly one external request naming a currently legal
  visible action. The public actor's ordinary tray response becomes
  `public_state_hash`/`last_read_receipt`; no success label is returned.
- `LOCK` terminally submits the current tray.

Think cannot `PREDICT` or `COMMIT`, cannot mutate frozen memory, and cannot
use Dream candidate/event handles. The one-shot planner is a nonrecurrent
control outside this reducer and is labeled accordingly.

## Proof fixtures required before model work

The implementation must run byte-exact cross-mode traces showing that identical
READ/NOTICE/CONNECT/REVISE/PASS steps over isomorphic eligible stores produce
identical counter and workspace deltas. Negative fixtures cover every illegal
mode/op pair, field cardinality, duplicate ID, wrong A/B request set, RETAIN
mismatch, REVISE missing ancestry, cycle, ineligible locator, multibyte byte
limit, mixed representation, cap overflow, malformed output, and post-terminal
step. The reducer source hash, parser hash, schema hash, and fixture receipt are
mandatory inputs to the fresh pre-GPU review.
