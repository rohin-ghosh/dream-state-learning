# Second bounded C5 read; first receipt preserved

First attempt was an inspector overconstraint, not a recovery runtime failure:
GO binds readiness/PLAN.json, while the native config binds control/PLAN.json.
Both are legitimately distinct paths carrying the same pinned SHA256.
Read and hash both, require byte-hash/document equality and exact references
at their own roles; also verify readiness CPU proof equals control saved proof.
No runtime guard/queue rule changed. Account the first701128 metadata bytes
against this same32MiB metadata ceiling; no TRAIN bytes were read in attempt1.
All original C5 read caps and no-write/no-GPU restrictions remain unchanged.
