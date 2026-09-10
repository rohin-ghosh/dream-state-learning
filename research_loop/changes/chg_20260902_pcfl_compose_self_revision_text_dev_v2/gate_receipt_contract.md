# v2 Stage-1 gate receipt reducer contract

`gate_receipt.schema.json` is the only accepted root grammar for Stage-1
evidence and evaluation.  Each G01--G11 slot embeds its typed receipt; the gate
does not follow caller-selected string pointers.  The exact receipt ID, gate
ID, and receipt kind are schema constants.  JCS duplicate-key rejection occurs
before validation, so a key cannot be supplied twice.

The reducer resolves every embedded assignment/call/read/terminal ID against
the already sealed assignment manifest and outcome/call ledgers.  Resolution
must be one-to-one and kind-correct.  An unresolved, duplicate, extra,
wrong-stage, wrong-root, wrong-h, wrong-z-side, wrong-twin, wrong-condition, or
wrong receipt-kind reference invalidates the gate artifact.  Invalid evidence
does not become `gate_value=false` because that would hide a contract failure;
it terminates Stage 1 as `NOT_RUN; HUMAN_REQUIRED` and leaves Stage 2
`NOT_TRIGGERED`.

For each valid receipt, `gate_value` is recomputed from component fields:

- G01 resolves its schema-suite, runtime-freeze, and report-lint receipt hashes,
  then conjoins its five Boolean validity fields and the exact 128 root count.
- G02 is the conjunction of its three Boolean manifest checks and its constant
  count summary.
- G03 requires both exact z-side rows and, on each, an exact committed
  candidate with A1 and A2 exact.
- G04 requires both z-side pairs and all four h branches. The reducer resolves
  each branch against its complete fresh Dream-2 trace and committed Dream-1
  pool. There must be exactly one charged `RAW_A_EVENT` read and exactly one
  charged candidate-parent read. Their distinct receipt refs must each occur
  exactly once in the decisive PREDICT
  `decision_provenance_receipt_ids`; the exact raw-A handle must occur exactly
  once in that PREDICT's `public_handles`. The candidate-read handle and hash
  identify exactly one member of `pre_a_dream1_pool`, and the capability minted
  by that read equals the PREDICT `parent_candidate_capability`. Both read
  ordinals are distinct and precede the decisive PREDICT. That PREDICT has
  `decision=REPLACE`; terminal COMMIT is later, also has `decision=REPLACE`,
  selects exactly the capability issued by that PREDICT, and repeats its
  ordered decision-provenance array byte-for-byte. The selected candidate hash
  differs from every pre-A pool member. Within each h pair, the ordered pre-A
  pool, Dream-1 clone hash, and treatment-invariant seed-key hash match
  byte-for-byte while the selected candidate hashes differ.
- G05 requires the exact four `(z_side,h)` assignments and B1/B2 exact with
  endpoint one in every branch.
- G06 requires its literal exact-program counts and both fixed oracle endpoints.
- G07 requires the exact Cartesian product of two z sides and two goal twins,
  with returned/accepted rows, four unique actor USE receipts, a valid minimal
  actor-input projection, Think-local LOCK, registered exact sequence, and
  endpoint one. LOCK never appears in actor input.
- G08 requires exactly one twin pair per z side; both sequences are valid and
  registered-exact, their first legal actions differ, and the registered
  relation is complementary.
- G09 and G10 recompute each endpoint from the named pair rows, set numerator
  to `sum(SELF)-sum(control)`, denominator four, and require numerator > 0.
- G11 resolves the two presealed sham-constructor receipts and four sham
  endpoints; pre-target sealing, target-independence, declared nuisance
  matching, and absence of an opaque semantic label must pass; SELF-minus-sham
  numerator must be > 0 and complementary sham redirection count must be zero.

The evaluation reducer compares each recomputed value with both the embedded
receipt `gate_value` and the evaluation `values.Gxx`.  Any mismatch invalidates
the artifact.  It then evaluates the fixed conjunction over G01 through G11.
Only all true emits `stage1_pass=true` and
`OPEN_EXACT_2504_CALL_STAGE2`.  Every other complete valid vector emits
`stage1_pass=false`, `NOT_TRIGGERED`, and `HUMAN_REQUIRED`.

Stored resolver ordinals are zero-based. Human-readable operation numbers are
derived only at report rendering as `ordinal+1`. The two-read/PREDICT/COMMIT inequalities
always compare stored ordinals; no report number may re-enter the reducer.

The causal revision receipt is nonsemantic. Its private integrity process may
read canonical candidate bytes only to compute equality and hashes. The gate
and report receive the signed receipt, never opaque content. G04 proves a
raw-A-conditioned branch-responsive selected-object update in the registered
fork. It does not prove that note content is true, useful, or semantically
appropriate, and it does not connect h-specific updates to the selected-h
target action contrast.
