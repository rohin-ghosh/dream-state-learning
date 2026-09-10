# Native-writer counter: ordering and runtime-drift correction

The source-row counter now uses wake-summary segmentation plus two passes over
the closed ledger prefix. Each manifest occurrence supplies its exact `ticks`;
the extractor consumes that many ordered thought rows and verifies ticks
`1..T`. Acts then join the unique nearest same-program/same-tick thought;
distance ties are accepted only when another unambiguous act establishes a
consistent before/after adjacency orientation, otherwise they fail closed.
This handles consecutive one-tick occurrences, which cannot be segmented by
tick-reset inference. It then recomputes
`best_before` by physical ledger byte order and joins thought rows against the
complete act index, so a remote/local merge may write an act first without
silently losing the row.

Each `(program, local_occurrence)` is mapped immutably to its wake-manifest
ordinal before filtering; repeated programs therefore cannot be remapped to
their final occurrence. The report includes this counter's extractor digest
(`--expected-extractor-source-sha256`), explicitly labeled as extractor
provenance rather than a digest of the runtime `batch_loop` module. Conflicting
or mismatching source receipts are flagged as `source_code_drift`; the combined
`runtime_or_source_drift` field also raises on the missing-prompt runtime
schema defect.

Missing persisted `prompt` fields are separately reported as
`prompt_present`/`prompt_absent` and flagged as runtime/schema drift. Such rows
remain non-authorizing `legacy_note_candidate` diagnostics for continuation-only
C1/C2 feasibility; they cannot enter `eligible` C3 rows, and the counter never
reconstructs prompts. Both an all-act action histogram and a candidate-only
histogram (after the non-prompt gates) are emitted as minimum birth-prompt
diagnostics, restricted to the closed prefix.
Histogram keys are SHA-256 payload identities, not emitted action text.

A CPU-only fixture covers two consecutive `ticks=1` summaries for one
program, with both thought-before-act (`T0 A0 T1 A1`) and act-before-thought
(`A0 T0 A1 T1`) physical layouts. Both map to distinct manifest ordinals;
unresolvable nearest-neighbor ties are rejected.

The copied audit prefix was also rerun with its real row shape (`thought`
rows have `episode_id`, `tick`, and `note`, but no `prompt`). The extractor
now skips unassigned post-prefix rows before touching `_occurrence`, reports
`eligible=0`, and leaves those rows only in `legacy_note_candidate`.

The legacy feasibility diagnostic follows the exact floor contract: required
column-zero colon markers, byte-counted UTF-8 target under 2,000 bytes,
byte-preserving ACT payload extraction, unique act join, independently valid
`instructions I0 -> I1` outcome, finite score agreement within `1e-12`, and
improvement over only earlier valid acts. It reports raw/unique continuation
counts, UTF-8 bytes, payload diversity/share, and exclusion reasons. It emits
no continuation text or tokenizer claims.

CPU regressions cover colonless markers, a trailing ACT payload space,
multibyte UTF-8 cap enforcement, inconsistent outcome/score, and an invalid
earlier act that must not debit the later act's best-before value.

On the copied wake-256 prefixes, the strict artifact-only feasibility pass
found:

| life | qualifying/unique continuations | UTF-8 bytes | distinct ACT payloads | maximum payload share |
|---|---:|---:|---:|---:|
| B0 | 168 / 168 | 96,202 | 8 | 0.7381 |
| B1 | 179 / 179 | 97,494 | 4 | 0.7486 |
| B2 | 127 / 127 | 88,036 | 11 | 0.3465 |

Every one of the 9,771 prefix thoughts lacked a persisted prompt, so authentic
task-conditioned eligibility remains 0/3,578, 0/3,544, and 0/2,649. The exact
birth-demonstrated four-pass payload accounts for 124/168 B0, 134/179 B1, and
34/127 B2 strict candidates. Removing it leaves only 44, 45, and 93 rows;
therefore B0/B1 cannot support a 64-row birth-excluded cell. This is positive
feasibility for a narrow continuation/action-reinforcement floor, not for
novel action discovery or experience grounding.

This remains a read-only feasibility check. No remote ledger, model, GPU, or
training artifact is modified or authorized.
