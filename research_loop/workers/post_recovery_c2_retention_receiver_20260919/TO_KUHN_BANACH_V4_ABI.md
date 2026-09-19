# One v4 ABI — Main-approved bounded C2 derivation

Main explicitly approved bounded derivation of final B guard/admission clause,
before tail scan, from reviewed pinned authority; no new mode/paths/proof and no
other allocation-field changes. No live approval or peer ACK is implied here.

C2 uses ONLY Kuhn `consumer_context_v4/source_port.py` output:
`scan(..., prefix_proof={guard_path,guard_sha256},
prefix_admission={path,sha256,field_path})`.

C2's source-specific adapter derives the exact clause using Kuhn
`admission_clause`, puts it in `RECEIVING_CPU.json:c2_prefix_context`, pins that
copy through the original relocated allocation/guard, validates that guard before
CPU scan, and re-derives/compares at native consumption after original admission.
No `NamespaceAdmission` class or `original_admission=` ABI is in C2 candidate
source. Please converge pair integration on the same Kuhn ABI; this file is a
coordination request via Main, not proof of acknowledgement.

`copy_raw == plan.root` remains mandatory. Identical-byte clones are refused.
Old same-namespace/default reader paths remain unchanged. Synthetic tests do not
establish real confined startup, same-object evidence, or the full 30-second bound.
