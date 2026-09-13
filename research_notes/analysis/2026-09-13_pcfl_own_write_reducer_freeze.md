# PCFL scoped own-write: prospective readout reduction freeze

**Date:** 2026-09-13 PT  
**Status:** frozen recommendation after the formation launch was announced but
before any fit or AUTH/C0 readout result was available  
**Scope:** one disposable, one-life storage diagnostic only

## Decision

If the fixed twenty-call formation completes without replacement or repair,
reduce the already sealed 17-address x nine-wrapper roster as follows. Freeze
this rule in executable source before the fit or either model readout. A failed
formation is the result and does not enter this reduction.

The **primary endpoint** is the full ordered 17-bit vector of `strict_stop` on
the unseen outer wrapper `W8`, separately for `AUTH_WRITE` and `NO_WRITE_C0`.
No W0--W7 observation may select or replace W8. A missing, truncated, malformed,
semantically incomplete, or non-byte-exact response is zero.

Assign the bounded label `SCOPED_OWN_WRITE_ACQUISITION_PASS` only if all of the
following hold:

1. the deterministic exact-child service reproduces all `17/17` registered
   blocks byte-for-byte;
2. `AUTH_WRITE` achieves at least `15/17` W8 `strict_stop`;
3. `NO_WRITE_C0` achieves at most `2/17` W8 `strict_stop`; and
4. the paired W8 difference is at least `13/17` in favor of `AUTH_WRITE`.

The 15/17 threshold carries forward the existing v2.2 strict local-read
tolerance at this smaller combined roster; it was not chosen from this run's
adapter outputs. Report semantic exactness beside strict exactness, but do not
substitute it for the primary endpoint.

## Mandatory diagnostics

Preserve and report every raw response plus:

- W8 vectors split into `READ EVENT` (8), `READ EVENTS_AT` (6), and
  `READ LINKS_FROM` (3);
- W0--W7 strict and semantic vectors by address and wrapper, labeled repeated
  trained-surface diagnostics;
- refusal, usable false-row, finish reason, and truncation counts;
- the exact 12 child rows, 17 address blocks, 20 scheduled training blocks,
  160 unique wrapper/block encodings, 800 presentations, 200 updates, one
  fitted life, one root, and one initialization; and
- complete formation -> admitted row -> compiled block -> adapter -> cold
  readout hashes and process/GPU release receipts.

Do not compute a confidence interval or p-value treating 153 calls as
independent observations. They are repeated measurements of 17 mappings from
12 rows in one life.

## Claim boundary

A pass supports only this sentence:

> In one controlled curriculum life, a rank-8 LoRA write caused a cold-loaded
> model to reproduce most trained address-to-block mappings compiled from its
> own world-grounded EVENT/LINK records under one unseen query wrapper, while
> the unchanged base did not.

It does not establish autonomous exploration, address selectivity,
generalization to new facts, traversal, connected reasoning, preservation,
compression, recurrence, parenting, lifetime improvement, or a full
Dream--LoRA--Think loop. The absent/wrong-root read panel and generic no-harm
canary remain mandatory before any broader writer qualification.

## Priority

This storage slice may run opportunistically because it is cheap and its route
readout is independent of the failed C0 route interface. It must not delay the
higher-value DEV repair that (a) discloses the exact READ dialect and (b)
restores the promised THINK-before-ROUTE opportunity while preserving the
world and final route scorer.
