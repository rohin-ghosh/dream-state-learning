# SEQ-120 birth readout: what the result establishes and what it does not

Date: 2026-09-13 UTC  
Status: watcher interpretation pending a separate raw-output recount  
Evidence capsule: `07816cb0649255ddaec5377e0b2ab4442919ea806d2eb60243b0155f1dc96a2a`

## Short verdict

The predeclared full birth conjunction **fails**, and its thresholds must not be
weakened after seeing the result.  Nevertheless, this is positive mechanism
evidence: a rank-8 LoRA learned two opposed, input-dependent action policies on
held instances and held surface forms while retaining almost all registered
off-task behavior.  This is much stronger than learning a fixed marker or
constant action, but it is still authored supervised training, not learning
from the child's own experience, parenting efficacy, or self-learning.

## Complete registered counts

| Readout | OFF | AUTH on its map | DERANGED on its map | Required |
|---|---:|---:|---:|---:|
| PROSPECT strict joint | 0/32 | 32/32 | 32/32 | 29/32 |
| REVISE strict joint | 0/64 | 58/64 | 56/64 | 58/64 |
| Belief twins | 0/16 | 16/16 | 16/16 | 15/16 |
| Goal twins | 0/16 | 16/16 | 16/16 | 15/16 |
| Expected twins | 0/32 | 26/32 | 24/32 | 29/32 |
| Observed twins | 0/32 | 26/32 | 24/32 | 29/32 |
| Prior-action twins | 0/32 | 26/32 | 24/32 | 29/32 |
| Addition instruction compliance | 8/16 | 15/16 | 15/16 | 16/16 |
| Copy instruction compliance | 8/16 | 16/16 | 16/16 | 16/16 |
| Forbidden anchor-tag spill | 0 | 0 | 0 | 0 |

DERANGED scores `0/32` and `0/64` against AUTH's conditional targets while
scoring `32/32` and `56/64` against its own complementary targets.  Thus the
two trained adapters do not merely induce the same generic formatting habit:
the supplied target map causally redirects their outputs.

OFF hits the 64-token cap on 96/128 requests.  Its zero strict score therefore
does not show that the base model lacks task reasoning; it shows that, under
this readout budget and prompt, it does not emit the required native action
interface.  The trained cells do.

## Failure localization from the raw scored rows

AUTH's six REVISE misses all occur on held `template/2`; it is `26/32` there
and `32/32` on held `template/3`.  In all six misses, `COMPARE` and `POLICY`
are correct and only `NEXT` is wrong.  DERANGED is likewise `24/32` on
`template/2` and `32/32` on `template/3`; seven misses have a wrong `NEXT`,
and one emits `NEXT: dax, wug`.  This is a reproducible surface-robustness and
action-selection defect, not a wholesale failure to compute whether expected
and observed outcomes match.

Both trained adapters also fail the same held addition item, though with
different wrong numerals.  The locality conjunction therefore properly fails
even though the overall intervention is far safer than the earlier SEQ-108
writer.

## Scientific interpretation

What is supported, subject to the independent raw recount:

> On one source-authored root, full-response supervised training of a rank-8
> adapter installs complementary finite policies that condition prospective
> action on `(belief, goal)` and revision on `(expected, observed,
> prior-action)`, and those policies transfer to held instances and held
> renderings while preserving 31/32 registered anchors.

What is not supported:

- the child selected or compiled its own experience;
- a teacher improved later learning;
- a qualified or clean-lineage birth checkpoint exists;
- the behavior transfers into RuleGame or CompilerGym;
- the policy is robust beyond one root and two held renderings;
- Dream--LoRA--Think's lifetime flywheel works.

In Rohin's terminology, this is **trained birth behavior**, not learned or
self-learned behavior.  Its relevance is that birth can plausibly amortize the
basic act of turning an internal comparison into a native action, leaving
parenting and lived experience to supply what should be compared and revised.

## Next actions

1. Finish an independent raw recount of all 384 responses and preserve the
   failure pattern; do not infer from the stored reducer alone.
2. Keep the already launched born-RuleGame formation exploratory and firewall
   its weights, prompts, and outcomes from every claim-bearing lineage.
3. Do not lower the twin or anchor thresholds.  A successor birth may add
   *new* training-surface diversity and reserve *new* held renderings, but may
   not train on the failed held strings.
4. Before calling birth qualified, repeat the frozen successor on fresh roots
   and require the complete complementarity/interface/locality conjunction.
5. Treat exact-training-form readout as a calibration diagnostic, not a rescue:
   held acquisition already succeeded strongly, while exact-versus-held gaps
   can still quantify extraction robustness.

