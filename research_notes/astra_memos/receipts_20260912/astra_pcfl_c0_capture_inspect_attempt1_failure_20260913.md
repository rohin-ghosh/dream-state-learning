# First offline capture inspection failure — 2026-09-13 13:52 UTC

Committed pre-outcome inspector adf39c4a exited1 before raw task replay at
capture_lineage, `actual CVD finalization failure`. No score table/output
directory was produced and no native call or collection was repeated.

Root cause: inspector expected exception type string `ValueError`, but the
actual outer imports native.require, which throws its subclass `ActorError`.
The archived original failure is `ActorError` with the expected CVD message.
Main changes only that exact exception-class binding, updates the synthetic
fixture and adds a regression using the actual native.require exception.
No scorer, denominator, task, threshold, original evidence, failure policy or
full finalized-analyzer requirement changes. Both inspector versions remain
in Git history. This non-material receipt compatibility repair precedes
scientific outcome inspection; the next offline invocation uses a fresh name.
