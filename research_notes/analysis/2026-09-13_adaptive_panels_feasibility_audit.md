# Adaptive Panels: bounded CPU-only feasibility audit

**Date:** 2026-09-13. **Audience:** Main. **Status:** advisory mathematical evidence; EDITSTOP.

## Scope and conclusion

Read target: §1 of
`research_notes/analysis/2026-09-13_adaptive_parenting_dev_gate01_binding_successor_v1.md`.
This audit owns only this new note and the new certificate
`research_notes/astra_memos/receipts_20260912/adaptive_panels_feasibility_cpu_20260913_rohin_audit.py`.
No existing specification, design, gate, source generator, model, tokenizer,
GPU workload, remote system, or other contributor's files were changed or run.
No commit was made. The abstract counterexample below is not a released task
or bank, and is not a proposal to change the contract.

**The suspected contradiction is real under the literal reading of §1(2).**
Balanced columns, no singleton fiber for any pair, and failure of every fixed
triple imply at most four complete response signatures. Consequently no
adaptive policy can identify eight candidates, even with unlimited probes.
Thus §1(1), (2), (3), and (4) cannot simultaneously hold. Seven columns, block
balancing, IDs, and later acceptance conditions cannot cure that contradiction.

**There is also a separate obstruction to §1(5).** Even if (2) were read only
as “no two probes identify all eight,” balanced columns plus adaptive depth
three plus failure of every fixed triple imply a successful policy with the
same second probe in both first-outcome branches. Different second probes
cannot be *required*. This conclusion uses the natural necessity reading of
“required,” not merely a policy choosing to use different probes.

Neither finding weakens a gate or grants run authority. This is evidence for
Main, not an independent-review verdict or an operational stop instruction.

## 1. Exact quantifiers and duplicate/complement handling

Let the eight candidates be a set Ω. Each probe is a deterministic function
`A: Ω -> {0,1}`. For a probe set `S`, the fiber of candidate `h` is
`F_S(h) = {g in Ω : g and h agree on every probe in S}`.

The literal condition “no candidate is identified by zero, one, or two
probes” is:

```text
for every candidate h and every probe set S with |S| <= 2:
    |F_S(h)| >= 2.
```

Zero probes leave eight possibilities. One balanced probe leaves four.
Repeating a probe supplies no new information. An adaptive path of length
two supplies precisely the same candidate fiber as its two realized probes:
any candidate matching the first outcome takes the same second-probe branch.
Thus forbidding *any* policy from identifying *any* candidate within two
probes has the same strong interpretation.

Column duplicates and complements induce the same unordered candidate
partition. Complementing a column just swaps its outcome labels, including
in an adaptive tree. Normalize every column so that candidate 0 has outcome
0, and quotient duplicates. There are `C(8,4) = 70` oriented balanced columns
and exactly `70/2 = C(7,4) = 35` canonical partitions. This quotient preserves
singleton fibers and all fixed/adaptive distinguishability properties.
It does not assume that the seven opaque probe IDs have distinct columns.

## 2. Exact proof of the suspected contradiction

### Pair lemma

For balanced probes A and B, put `t = |{A=0, B=0}|`. Balance forces their
four cell counts, in order `00, 01, 10, 11`, to be

```text
(t, 4-t, 4-t, t),  where t is an integer from 0 through 4.
```

For `t=0` or `4`, the probes are complements or duplicates. For `t=1` or
`3`, there are singleton fibers, contrary to literal (2). For distinct,
noncomplement partitions the only remaining possibility is `t=2`:
all four pair fibers have size two. Equivalently, every pair of different
canonical columns is statistically independent under the uniform candidate.

### Triple lemma, including its integer constraint

Let A, B, C have all three pairwise margins equal to two in each cell.
Writing `t = n000`, the twelve pair-margin equations force

```text
(n000,n001,n010,n011,n100,n101,n110,n111)
    = (t,2-t,2-t,t,2-t,t,t,2-t).
```

Every count is a nonnegative integer, so `t` is exactly 0, 1, or 2.
There are only three possible tables:

- `t=1`: all eight cells have count one; this fixed triple identifies all eight.
- `t=0`: the four odd-parity cells have count two; the other cells are empty.
- `t=2`: the four even-parity cells have count two; the other cells are empty.

In either noninjective case `C = A XOR B XOR constant` on every candidate.
This is an exact finite count argument, not an approximation from pairwise
independence. The certificate also solves the integer margins independently,
without constructing columns or assuming this formula.

### Global closure and adaptive impossibility

If the canonical family has at most one partition, it has at most two total
signatures, and cannot identify eight. Otherwise choose different canonical
columns A and B. Their four fibers all have size two by the pair lemma.

Any other canonical column C is pairwise uniform with A and B. Condition (4)
excludes the all-one triple table. Hence C is A XOR B up to complementation.
Since canonical A, B, C all equal zero on candidate 0, the complement bit is
zero: `C = A XOR B`. Every canonical column therefore belongs to

```text
{ A, B, A XOR B }.
```

The normalized columns lie in a vector space of dimension at most two over
GF(2). Before normalization, the possible balanced columns are
`A`, `NOT A`, `B`, `NOT B`, `A XOR B`, and `NOT(A XOR B)`; the constant
functions in the affine span are not balanced. There are at most three
distinct unordered partitions, however many probe IDs are provided.

The two candidates in each `(A,B)` fiber agree on every available column.
An adaptive policy must choose the same next probe for these two candidates
at every matching history, and receives the same outcome. Induction gives
identical complete transcripts. It cannot distinguish the pair at any depth.
Randomization cannot produce certainty for both either: condition on the
policy's random choices and the same indistinguishability argument applies.

**Therefore (1) + literal (2) + (4) contradict (3).** This proof handles
duplicate/complement columns and is stronger than failure at depth three.

## 3. Independent decision-tree obstruction to required different seconds

This proof does **not** use condition (2), the global affine-span argument,
or pairwise independence of arbitrary columns.

Suppose a balanced family admits a binary decision tree identifying eight
candidates in at most three probes. A depth-three binary tree has at most
eight leaves. To identify eight it must be full: all eight leaves are at
depth three, and posterior sizes along a path are `8 -> 4 -> 2 -> 1`.

Fix any successful root R. Let A be the successful second probe in branch
`R=0`, and B the successful second probe in branch `R=1`. If A and B are the
same probe, a common second probe already exists. Otherwise:

1. A splits the four candidates in `R=0` into two pairs. Because A is globally
   balanced, it also splits `R=1` into two pairs. The same holds for B.
2. On four candidates, two balanced binary partitions either induce the same
   two pairs, up to outcome labels, or intersect in four singletons. Indeed,
   their counts are `(u,2-u,2-u,u)` with `u=0,1,2`.
3. If A and B intersect in four singletons on **both** R branches, fixed
   `(R,A,B)` identifies all eight, contrary to (4).
4. Therefore A and B induce the same unordered pair partition on at least
   one R branch. If that branch is `R=0`, replace A there with B and reuse
   A's original third probes, swapping outcome branches if necessary. B is
   now a successful common second probe. If the matching branch is `R=1`,
   use A as the common second probe instead.

The replacement uses only probes and pair-splitting third probes already
available in the original family. It does not assume access to extra columns.
It works for every successful root, including when A and B are complements.

Thus **(1) + (3) + (4) exclude (5) if “required” means that no common second
probe can succeed**. If (5) means only that a selected oracle happens to use
different second probes, this separate obstruction does not apply; such a
choice need not be necessary. The literal-(2) contradiction still applies.

## 4. Ambiguity counterexample, not a replacement contract

The following weaker readings of (2) are not equivalent to its literal text:

- No fixed pair identifies *all* eight candidates.
- No adaptive depth-two policy identifies *all* eight candidates.
- No candidate is identified before probe three along one designated
  successful depth-three tree, or by one designated initial probe pair.

The first two statements follow just from binary information capacity:
two probes give at most four signatures/leaves. The third follows from the
full-tree argument above. They do not prohibit a different pair from
identifying an individual candidate.

Here is an exact seven-distinct-partition witness for (1), these weaker
readings of (2), (3), and (4). Candidate numbers are zero-based; probe numbers
are one-based. These are abstract mathematical labels, not production IDs.

| Candidate | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| 3 | 1 | 1 | 0 | 1 | 1 | 1 | 0 |
| 4 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| 5 | 0 | 1 | 0 | 1 | 0 | 0 | 1 |
| 6 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| 7 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |

Each column has four ones. With bit `h` representing candidate h, the column
masks are `(30,46,86,170,78,142,166)`. No two are duplicates or complements.

Successful adaptive tree: ask P1, then P4 on both branches. Choose the third
probe by the first two outcomes:

| P1,P4 outcomes | Remaining pair | Third probe | Third=0 answer | Third=1 answer |
|---|---|---|---|---|
| 00 | {0,6} | P3 | 0 | 6 |
| 01 | {5,7} | P2 | 7 | 5 |
| 10 | {2,4} | P2 | 4 | 2 |
| 11 | {1,3} | P3 | 3 | 1 |

Every candidate requires exactly three along this tree. Nevertheless P1,P2
outcomes `(1,0)` uniquely identify candidate 4; `(0,1)` uniquely identify
candidate 5. Hence the literal no-singleton condition fails.

All `7^3 = 343` fixed ordered three-probe sequences, including repeats, fail
to identify all eight. Their numbers of nonempty signatures are:

| Signatures | Number of fixed sequences |
|---|---|
| 2 | 7 |
| 4 | 126 |
| 5 | 54 |
| 6 | 156 |
| 8 | 0 |

This witness does **not** satisfy required branch-dependent second probes:
P4 works on both root-P1 branches. The certificate additionally checks all
seven possible roots and finds common successful second choices for every
one. This is **not** a counterexample to the literal contract, to the
necessity interpretation of (5), or a claim to satisfy the other bank,
shortcut, namespace, or tokenizer conditions in §1.

## 5. Executed CPU certificate and reproducible receipt

The preserved certificate uses Python's standard library only. It performs
no network calls, subprocess launches, model imports, GPU access, writes,
task-bank generation, or acceptance-gate modifications. It reads its own
bytes and the binding document solely to report SHA-256 provenance.
Its explicit `check` calls remain active under Python `-O`.

Executed on Python **3.12.3**. Receipt timestamp for normal/optimized
re-execution: **2026-09-13T19:33:13Z** (12:33:13 America/Los_Angeles).
The initial direct execution returned JSON with `"status": "PASS"` and exit
code zero. Normal and optimized re-executions returned identical output
hashes. Commands, from the repository root:

```bash
python3 -B research_notes/astra_memos/receipts_20260912/adaptive_panels_feasibility_cpu_20260913_rohin_audit.py
python3 -B research_notes/astra_memos/receipts_20260912/adaptive_panels_feasibility_cpu_20260913_rohin_audit.py | sha256sum
python3 -B -O research_notes/astra_memos/receipts_20260912/adaptive_panels_feasibility_cpu_20260913_rohin_audit.py | sha256sum
```

Provenance for the executed bytes:

```text
certificate SHA-256:
fe8c43229ffe07b962be728977b1fc9c6c6bd325ce14880b412d8d00fe42c69f

binding document SHA-256:
a7a39ed2a71ff397d4eb6219d29b409436bc3d8c062b127a55b617d9409caa8d

binding §1 SHA-256:
935e2452660da2f8993b5f872c1d59e4aaad0bee942f6dc7172c62a03c8746be

complete JSON stdout SHA-256, normal and optimized:
88cdd95725e94343699ce312c05643d764cc2d0a3f02e47674ee926e929554ff
```

The section hash covers bytes starting at `## 1.` and ending immediately
before `## 2.`, including intervening newlines. Whole-document changes by
other contributors can change future receipt hashes without changing the
mathematical result; compare the section hash separately.

Exact executed enumeration results:

| Check | Executed result |
|---|---|
| All oriented balanced columns / canonical partitions | 70 / 35 |
| All raw unordered pairs with repetition | 2,485 |
| Duplicate/complement raw pairs | 105 |
| Pairwise-uniform raw pairs | 1,260 |
| Raw pairs with singleton fibers | 1,120 |
| Distinct canonical pairs | 595: 315 uniform, 280 with singletons |
| All distinct canonical triples | 6,545 |
| Triples with all pair margins uniform | 945 |
| Uniform-pair triples with eight singleton cells | 840 |
| Uniform-pair triples with four parity double cells | 105 |
| Other canonical triples | 5,600 |
| Independent integer-cell search | All `3^8 = 6,561` vectors tested; exactly 3 solutions |
| All strong-admissible canonical subfamilies | 456 including empty: 1 empty, 35 singletons, 315 pairs, 105 triples |
| Strong-admissible families of size >=4 | 0 |
| Maximum complete signatures in any strong-admissible family | 4 |
| Successful adaptive depth-three strong-admissible families | 0 |
| Root / ordered balanced-second choices for transfer lemma | 11,340 |
| Cases already fixed-triple injective | 5,040 |
| Remaining cases admitting a matching-branch transfer | 6,300; no exception |
| Weaker-reading witness | All 343 fixed sequences fail; all 8 adaptive paths replay correctly |

“Strong-admissible” here means balance, no singleton pair fibers, and no
injective fixed triple; it does not assume an adaptive solution. The family
search backtracks through **every** subset of the 35 canonical partitions
that obeys these hereditary conditions, rejecting a proposed extension only
when it introduces an invalid pair or injective triple. It is not a random
sample and does not need to enumerate arbitrary seven-column multisets:
every such multiset quotients to one of these canonical subsets, while
duplicates/complements add no information. Successful identification is also
checked by a separate memoized candidate-mask decision-tree solver.

The independent integer-margin enumeration uses direct cell sums, not the
XOR classification. The branch-transfer check directly compares the induced
partitions on each four-candidate root branch. The weak witness's reconstructed
tree is independently replayed row-by-row using transcript matching. These
are distinct computational checks within this certificate, **not** two
fresh-context model reviews or a claimed satisfaction of the binding
document's two-independent-implementation gate.

## Disposition

The literal combinatorial task family is empty. Weaker quantifiers in (2)
change that mathematical conclusion for (1)–(4), as the explicit witness
shows, but do not resolve the independent necessity obstruction in (5).
This note records those facts without selecting revised wording, authoring
production sources, altering gates, or authorizing any run. Other §1 bank
and shortcut conditions were not certified.

**EDITSTOP — bounded audit complete; no further edits or operational actions.**
