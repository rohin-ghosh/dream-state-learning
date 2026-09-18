# Before-exposure budget addendum — September17,2026

Supersedes only the five-full-pool selection schedule in WIDEGAP100K_SCOPE.md.
That original proposal is preserved; no new candidate scoring has occurred.
Main's bounded-compute warning is incorporated before source/config freeze.

Use a fixed natural256-row-per-contest model-selection sample (seed218) at
steps8/1563/3125/4688/6250. Selection composite is equal-weight macro mean-rating
Spearman and centered precision of sample-predicted top ceil(200*Nsample/Noriginal)
in the original true top half. This is explicitly a sample proxy, not literal
full-contest top200. Select the highest composite checkpoint; fixed schedule
and metric cannot change after observing scores.

Exactly one full clean eligible model-selection pass reports selected-checkpoint
Spearman and literal predicted-top200-in-original-top-half precision afterward.
It does not reselect the checkpoint, is not a new independent dataset, and does
not score quarantined original rows. Original100k target, mean-order BT objective,
warm-start, optimizer reset, split roles, calibration and6h maximum are unchanged.

After receiving CPU determines exact eligible counts, the strict admitted GPU
process runs a bounded8-update pilot plus256 longest-token selection-input
inference rows. It records real optimizer progress separately. Before sustained
fitting it requires1.25*(remaining100k fitting time + all remaining selection,
full-pool reporting and calibration inference time)+900 seconds to fit the actual
remaining admitted wall. Fit throughput uses updates2–8; inference throughput
uses those256 longest-token inputs. Failure preserves a consumed pilot and does
not retry or expand the lease. Measured ETA is an estimate, not a finish receipt.
