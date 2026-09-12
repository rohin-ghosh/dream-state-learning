# V10R2 semantic carrier pre-implementation audit

Date: 2026-09-12 UTC  
Status: watcher-side, CPU/read-only engineering audit. No builder source, run,
model, adapter, process, GPU, node, or remote ref was changed.

## Bound inputs and verdict

This audit binds the semantic ruling at commit `0637262f`, file SHA-256
`d0ca1fdacf63cb932684d02bbd92da0f96376cfb572773b3303a0d00ad04792e`,
and these current V10R1 producer bytes:

- `organism_v6/multikey_writer_gateway_simple.py`:
  `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8`
- `tests/test_multikey_writer_gateway_simple.py`:
  `44e66d283a2c9b27d449dfb099f54f93bec52f518edf4e11e9f235054c24e84c`
- `gpu/multikey_writer_gateway_simple.sh`:
  `3994bf389e63ac790b3eb500c74a974ed57b88fd8fd02d494ae6fecc0ab33665`

**Implementation is scientifically straightforward but is not a string
replacement.** The current executor fits before it evaluates its positive
control, uses raw prompts, assumes equal candidate token counts/masks, contains
the signed locality-rate loophole, has no wrong-root family, and treats a
16-row a0/a1 table as `oracle_ok`. All of those must change before the fresh
carrier. Retaining any one can produce an invalid or falsely permissive W0.

## Version/custody gate

Prefer a versioned V10R2 producer/test/launcher and leave the V10R1 three-file
producer immutable. `writer_interface_calibration.py` and
`oracle_lookup_diagnostic.py` import V10R1 constants, `oracle_prompt`, request
construction, validation, and replay directly. Updating the existing module
in place therefore breaks historical diagnostic replay or silently interprets
old manifests under new constants. The safe implementation surface is:

- new `organism_v6/multikey_writer_gateway_v10r2.py`;
- new `tests/test_multikey_writer_gateway_v10r2.py`;
- new `gpu/multikey_writer_gateway_v10r2.sh`.

An in-place implementation is acceptable only if it first supplies explicit
version-dispatched backward replay and keeps the old diagnostic tests green.
Do not make old a0/a1 artifacts pass the semantic reducer. The later
`writer_replay_plan.py` consumer will also need version-dispatched replay if a
semantic W0 pass is ever handed to W1; that is not needed to run the carrier.

## Exact implementation map

The V10R2 module needs these contract-level changes.

1. **Identity and provenance.** Change `VERSION`, `REAL_VERSION`, receipt
   names, `approved_intake`, `requested_scope`, `PENDING`, profile counts, and
   maximum claim text to V10R2. Preserve V9/V10/V10R1 as inherited history,
   but additionally bind the semantic audit commit/path/hash; do not continue
   to claim that the unamended V10R1 exact scope is the whole active contract.
2. **Separate action values from continuations.** Define action values
   `("-mem2reg", "-gvn")` and derive exact candidates
   `("ACT: -mem2reg\n", "ACT: -gvn\n")`. Backend validation consumes only
   the action values; generation, scoring, parser, fits, and reports consume
   the full continuations. Replace every constructed `ACT: a{target}` and
   a0/a1 parser entry, including fixture records.
3. **One renderer.** Freeze the ruling's response-contract bytes and render
   exactly one user message with the pinned tokenizer's
   `apply_chat_template(tokenize=False, add_generation_prompt=True)`; tokenize
   that rendered string with `add_special_tokens=False`. Store/bind both the
   user-message bytes and rendered-prefix bytes/IDs. Use the identical
   response contract and renderer once in fit, primary, and binary-locality
   contexts. Only carrier requests add `Binding:` plus the answer row. Copy
   prompts use their separately frozen exact-copy body. Raw, double-templated,
   target-bearing primary, or evaluation-only contracts must fail closed.
4. **Fresh material.** Replace the outcome-exposed default identifier seed and
   freeze new opaque identifiers and held renderings before output. Retain two
   roots, 16 keys/root, eight train plus four held forms/key, the orientation
   arrays, complementary maps, 128 rows/fit, 64 primary rows/cell, two epochs,
   and all recipe fields. Bind a deny receipt reconstructed from the V10R1
   calibration material and require no new tool, neighbour, complete prompt,
   or token-ID sequence to collide with it. The ruling prints an exact task
   literal previously used as a V10R1 template; therefore claim freshness for
   the new rendered tool/task instances, not for that literal itself, unless
   the contract is prospectively amended before output.
5. **Material panels.** Replace `spill` with typed `missing` (8/root),
   `unsupported_m2` (8/root), `neighbour` (16/root), `wrong_root` (the other
   root's 64 no-row held prompts per fitted adapter), and semantic-copy (the
   eight frozen actions named in the ruling). A wrong-root observation must
   carry separate adapter-root and prompt-root fields and must never enter an
   owner-primary reducer.
6. **Carrier requests.** Replace `oracle_generate` and the 16-row
   `oracle_prompt` gate with OFF-only `carrier_generate` and `carrier_score`.
   Build exactly 64 items/128 requests: four 16-item balanced root-map cells
   and 32 paired map swaps. A pair has the same root/key/task/seed and changes
   only the target in its supplied binding row. Give these kinds a disjoint
   request/cache namespace and prove that their complete prompt and token IDs
   occur nowhere in fit, primary, or locality artifacts.
7. **Stage order and terminal shape.** Current `execute_real()` launches four
   fits first. V10R2 must instead run two fresh OFF loads (generation and
   scoring), reduce and seal all 128 carrier records, and also seal the 16 OFF
   semantic-copy generations before any `fit_*_STARTED` or adapter path can
   exist. Thus the complete pre-fit model block is 144 requests although the
   carrier itself is exactly 128. A carrier/copy failure is a replayable
   zero-fit terminal result labeled
   `ASSAY_INVALID_SEMANTIC_ACTION_SURFACE`, not an infrastructure
   `NONREPORTABLE_ABORT`. Only `SEMANTIC_EXACT_ROW_CARRIER_OK` dispatches the
   four clean-base fits. Carrier requests allow exactly one attempt; a
   pre-output infrastructure failure aborts the run rather than retrying a
   selected item.
8. **Reducer/report.** Replace `oracle_ok` with a separately reduced carrier
   receipt. Per modality and per cell require BA at least `.90` (15/16), total
   generation validity at least 61/64, zero truncations, zero multiple-ACT,
   and at least 29/32 strict row-swap redirects. A score tie has choice `None`
   and is wrong. Report per-cell target-by-prediction confusion (including
   invalid/tie), per-item full score margins, both candidate token counts,
   generation/score agreement on a fixed 64 denominator, invalid UTF-8-byte
   hex, and both redirection lists even on failure.
9. **Preserve downstream W0 gates.** Keep all-key median NLL gain `.50`, map
   mean-gain asymmetry `.25`, BA `.80`, stratum accuracy `.75`, 12/16 and 6/8
   margin counts, OFF gain `.20`, own-minus-opposite BA `.50`, validity `.95`
   and `.875`, and zero multiple-ACT conjunctive in each fitted cell. Retain
   full-candidate sums without length normalization. Add confusion/margin
   reporting but do not pool roots, maps, strata, or families.
10. **Close locality.** For each binary locality item compute the stable
    two-candidate softmax from full sums and record per-item TV, mean TV, and
    maximum TV. Gate the mean at `.05`. Replace the current signed
    `mean(I_ON-I_OFF)` with
    `abs(mean(I_ON)-mean(I_OFF)) <= .05`; the existing test deliberately shows
    that `-1` passes and must be inverted. Apply the four binary-family gates
    separately, including wrong-root. The eight-action copy panel uses exact
    generation, not the binary parser or binary candidate scoring, and OFF
    plus each applicable fitted adapter must be 8/8.
11. **Backend receipt.** Before model requests, capture the actual
    CompilerGym `llvm-v0` action registry, registry hash, interpreter/package
    identity, `cgym_eval.py` hash, and one predeclared public smoke benchmark.
    Require both action values as distinct single registry entries and require
    each alone to return `ok=true`. Require all eight copy actions in the same
    registry. Preserve smoke scores only as interface receipts; never expose
    them to the model or use them to choose/order the pair.

The full post-fit request total is not yet uniquely determined by the prose.
With owner-root copy panels and reuse of the identical primary-OFF record as
the wrong-root OFF baseline, it is 1,840: carrier 128, primary 768, owner
binary locality 384, fitted wrong-root 512, and semantic copy 48. Issuing
typed duplicate wrong-root OFF baselines makes it 2,096; crossing every
adapter over both roots' copy panels adds another 32. Freeze one interpretation
and exact denominators in `profile_plan` and tests before any output. This
ambiguity does not change the carrier denominator or its 144-request pre-fit
block.

## Tokenizer and candidate-score hazards

- The semantic candidates have unequal byte length and are likely to have
  unequal Qwen response-token counts. Delete `masks[0] == masks[1]`,
  `counts[0] == counts[1]`, and tests requiring equal target length. Instead,
  require each candidate independently to have the exact shared prefix IDs,
  an all-response mask through its final LF and one EOS, no boundary-straddling
  token, and its own bound count. Unequal counts are valid and must be reported.
- Keep joint prefix-plus-candidate tokenization. Separately tokenizing and
  concatenating the response can change a BPE boundary. Reject any token that
  straddles the rendered-prefix/response boundary, and require generation IDs
  to equal the masked scoring prefix for both candidates.
- Keep sums of every LF-plus-EOS response-token log probability. The shorter
  `-gvn` continuation may have a strong length prior; balance and row swaps are
  the control. Length normalization would change the declared action and is
  forbidden.
- Require `candidate_response_tokens_including_EOS <= 24` for both candidates,
  giving eight-token headroom under `max_new_tokens=32`, in addition to the
  2,048-token context cap. Pin EOS ID, chat-template text/hash, special-token
  map, rendered bytes, offsets, IDs, masks, and counts in the pre-model receipt.
- The literal-boundary fixture must actually merge characters across
  `len(prefix)`; the present `Straddled` fake mutates token zero and does not
  exercise that predicate. Add raw/chat/double-template negative fixtures.
- `validate_record` may accept finite equal totals as data, but the carrier
  chooser must count exact ties as wrong. Nonfinite/missing values remain
  nonreportable, never merely incorrect.

## Balance and invariance gates

Before inference, prove rather than infer:

- 64/64 semantic targets in every 128-row fit, 32/32 in every 64-row primary
  cell, and 8/8 in every 16-row carrier cell;
- W+ and W- fit rows have byte-identical prompts, order, masks, seeds, recipe,
  and nuisances and complementary targets; unequal candidate byte/token length
  must not be mistaken for a prompt/dose imbalance;
- each carrier cell covers the same 16-key geometry, W+/W- order is identical
  within a root, and each map-swap pair differs only in its binding target
  bytes; cross-root byte order need not match;
- constant, tool, mode, stratum, stratum-by-mode, template, and
  template-by-mode shortcut maxima remain exactly chance, while
  orientation-by-mode remains 1.0;
- complete cross-root disjointness of tools and one-character neighbours;
- response-contract bytes occur exactly once on every binary surface, no
  answer row enters a fit/primary/locality prompt, and target permutation
  cannot change any no-row prompt or schedule;
- per-family locality denominators and OFF records are fixed, with no pooling
  or signed-rate cancellation.

## Minimum CPU/pre-model gate before the fresh carrier

1. All canonical material, parser, balance, complement, freshness,
   anti-flow, typed-request, cardinality, and mutation tests pass on the exact
   source bytes.
2. Fake-tokenizer tests pass for ordinary, genuinely boundary-straddling,
   multi-token, unequal-length, missing/duplicate EOS, truncated, raw,
   double-chat, and changed-chat-template cases.
3. The pinned real Qwen tokenizer performs full round-trip/mask/prefix/headroom
   preflight over all four fit inputs and every frozen carrier/primary/locality
   request without loading the model.
4. The pinned CompilerGym registry and single-action smoke receipt passes for
   `-mem2reg`, `-gvn`, and presence of all eight copy actions.
5. Golden reducers cover every inclusive boundary and adjacent failure,
   score-pass/generation-fail, tie, nonfinite abort, fixed invalid denominators,
   28/29 redirection, 60/61 validity, per-root AND, and negative legal-emission
   changes failing through the absolute-value rule.
6. A mock staged controller proves: carrier/copy pass launches exactly four
   later fits; every carrier/copy failure launches zero fits, creates no
   adapter/optimizer artifact, seals the exact failure label, and replays
   byte-identically; full success also replays after the real CLI closes with
   stdout/stderr outside the root.
7. Preparation rechecks source, snapshot/environment, backend, tokenizer,
   protected roots, fresh output root, lease deadline, and zero model/GPU use,
   and binds the exact 144 pre-fit requests before any inference.

The current 68-test V10R1 suite was run locally during this audit. It produced
39 passes and 29 failures/errors because macOS exposes `/var` as a symlink to
`/private/var`, which `checked_path()` rejects; one header-receipt assertion
also compares those two aliases. This is not semantic evidence, but it is not
a green baseline. The pre-carrier receipt must come from the exact Linux
execution environment, or a separately reviewed path-canonicalization repair
must make the portable suite green first. No GPU/model action is justified by
the present laptop result.
