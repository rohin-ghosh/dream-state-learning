# Main archive handoff — hash/location export only

Allowlist `MAIN_PRESERVATION_MANIFEST.json` and this note. Conservatively exclude
the rest of `research_loop/workers/rohin174_parenting_20260917/node5/` from an
unreviewed bulk push. Keep its actual files in the private insurance archive.

Especially private: MSG201/C2_SNAPSHOT_20260918T021847Z (checkpoint plus exact
console/context); all parent run directories (SOURCE, PROMPT, SYSTEM, RESULT,
provider records); pause/recovery/current-incarnation receipts; INSURANCE;
console observations, raw journals/inboxes, captured source trees and archives;
operator logs/configs and provider transport files. Their filenames alone do
not establish that their contents are safe for publication.

The current parent inherits its API credential from the process environment;
these launch actions did not persist it. A credential-filename scan found none
in this node5 tree, which is NOT a credential-content clearance. Never export
environment dumps, authentication headers, provider wire logs, credential files,
raw transport configuration or endpoint/host inventories. No secret value or
credential hash is included in the manifest.

Do not push COORDINATION.md verbatim without Main's sanitization: it includes
private conversation quotations and machine identifiers from multiple operators.
Its hash/location is listed instead. No historical coordination text was removed.

The manifest identifies essential private receipts by repository-relative path,
file SHA256 and size. Source51/optimizer4908 and separate console5846 remain
distinct; preserved52 and latest inspected complete64 are not clone source51.
The complete64 pointer contains only checkpoint paths/hashes, not its embedded
experiment/history. Main owns off-node copies; this task did not duplicate them.

No child signals/reloads/holds, journal retraction, human-message creation, or
credential/environment output was used to prepare this handoff. Review other
operators' directories separately; this inventory covers node5's operator scope.
