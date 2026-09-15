# Evidence storage after Rohin101

Raw captures, corpus capsules, model tensors and tar archives live on leased
nodes' local disks, not in the VM checkout. Keep every original capture and
failed attempt; changing storage is not permission to discard evidence.

Commit source code, tests, compact manifests, source and archive hashes,
reductions, outcome/richness tables and operational receipts. A manifest must
name the node alias/wrapper, native archive path, SHA256, creation timestamp,
lineage/source version, and any retention or lease-copy deadline. Never put
credentials or internal host addresses in it. Archive inventories can remain
native with their hash in the compact manifest.

Stream copies directly between storage locations. Verify transfer SHA256 and
file inventory before declaring a mirror valid. Prune a completed VM copy only
after its manifest and hashes are pushed and the copy is committed or verified
on a node, as authorized by Rohin101. Do not prune an active broker's state or
pending input. Use immutable runtime directories outside Git for VM controllers;
keep review buffers bounded and delete them only after verified native upload.

The September15 large-file migration is recorded in
`orch_vm_evidence_preservation_20260915/BIG_FILES_MANIFEST.json`,
`BIG_FILES_VERIFIED.json` and `BIG_FILES_PRUNED.json` in that directory.
Git history is preserved, not rewritten. Older raw paths in receipts can be
retrieved from the named native archive or their historical Git commit; they
are not promised to remain in the current VM working tree.
