# Prospective scoped C0 inventory — September 13, 2026 12:56 UTC

Main selects `SCOPED_C0_FIXED_L8_NOT_FULL_ALLOCATOR` only for the separately
named PCFL_C0_ZERO_FIT_DIAGNOSTIC_V1. No native PCFL output has been collected.
This is an explicit Builder implementation choice, not inherited permission
to relabel a different allocator as the full v2.2 algorithm. The original
qualifier, smallest-L/4096-pool search, full training classes and C11 guard
remain unchanged and unqualified. Simple hygiene applies now.

## Basis and scope

The actual offline tokenizer profile (SEQ163) encoded4096fixed candidates:
L6:51,L7:603,L8:1470,L9:1294,L10:557,L11:119,L12:2. All strings/token vectors
were unique. Raw provisional IDs have mixed lengths6..12 and are not native
inputs. L8 is the modal observed candidate length, selected for preparation
cost, not learner outcomes. The measured candidate loop took0.271424484s and
tokenizer load3.673167628s. These do not forecast joint full-search cost.

## Fixed algorithm before any actor output

- Four roots excluded/0,excluded/1,excluded/2,excluded/3 only, in that order.
  Within each, use committed core SLOTS namespace and slot order unchanged.
- For each slot enumerate the existing opaque_candidate(root,namespace,index,
  salt) for salt0..999999. Select the first candidate whose actual tokenizer
  encoding (no specials/truncation) has exactly8tokens, whose text and token
  vector are unique across all already selected slots, and which has no
  reserved-literal substring collision. All examined candidates, token IDs,
  accept/reject reasons and exact chosen salts are preserved.
- Reserved literals are exactly EVENT,AT,DID,GOT,EVIDENCE,LINK,FROM,THEN,VIA,
  RECEIPT,READ,EVENTS_AT,LINKS_FROM,ROUTE,EXPLORE,PROBE,RESULT,TESTED,TO,
  AVAILABLE,PORT,MEMORY,MISS,EDGE,TASK,START,GOAL,PROBES,TESTS,SOURCE,
  DESTINATION,OPTIONS,TEST,USING,PORTS,COMMIT,ADDRESS. This scoped task has
  no canary IDs; namespace prefixes are structural, not excluded substrings.
- No alternate length, backtracking, redraw, root replacement or adaptive
  selection. An exhausted slot or failed final used-surface measurement is
  retained as preparation failure, not silently repaired or resampled.
- Expand exactly800unchanged tasks and1952conditional call slots, then run
  actual measure_tokenizer on every used opaque ID, initial prompt, READ and
  returned block. All required group equalities, private-byte exclusions,
  uniqueness, exact template and context-budget checks still apply. Common
  standalone ID length alone does not pass those checks. RA/RB are separate
  deliberately different render templates, with within-render substitutions.
- Pin this policy, source bytes, public-revision tokenizer-file hashes and
  actual chat template. Preparation is offline, CPU-only, no weights loaded;
  fresh directories and a180second outer cap preserve incomplete failures.

This produces at most a used-inventory certificate for a zero-write interface
diagnostic. It does not certify the full registered allocator/assay, unused
training schedules, clean ancestry, C11, memory, parenting or H1/H2. No future
child may inherit these researcher-authored ceiling rows as authentic evidence.
