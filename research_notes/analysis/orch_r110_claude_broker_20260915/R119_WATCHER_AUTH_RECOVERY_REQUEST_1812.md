# Node5 authentication recovery request — September 15, 2026, 18:12 UTC

To the authorized watcher/service-account custodian: restore Claude authentication for the existing node5 service user through the normal approved login flow (`claude auth login`) and ensure required organization-managed settings load successfully. Keep the same authorized account, organization policy, model and LOW-effort subparent configuration. Do not disable managed settings, substitute credentials/accounts, or change prompts to bypass controls.

Observed September 15 at 18:09:12 UTC: `claude auth status --json` exited 1 with `loggedIn=false`, `authMethod=none`, `apiProvider=firstParty`. Credential-cache metadata showed `expiresAt=0` and no refresh token. No credential values were exported or modified. F3's managed-settings failure has not independently been proven to have the same root cause as F4's explicit OAuth failure.

Return only a timestamped no-secret recovery receipt: authentication status exit code, `loggedIn`, and whether required managed settings successfully load. Never paste tokens, authorization headers, login codes, private URLs, account identifiers, or raw credential files into coordination, repository evidence, prompts, or chat. No synthetic parent/model call is requested as an authentication probe.

Preserve F3 `C023_E0_PARENT` and F4 `P0041` as charged MISSING failures, including their original raw captures, labels and hashes. Do not retry, rephrase, resubmit, reset counters, or reclassify those attempts. After authorized recovery, only genuinely new requests may be served under preserved caps/deadlines and exact family lifecycle bindings. Children continue nonblocking; no GPU process, child, or head should wait on this recovery. Actual future publication and native consumption must be reported separately with measured timing.

The prospective source patch only improves error classification; it does not repair authentication and is not deployed into the immutable running LOW snapshot. Existing HIGH/LOW receipts remain historical evidence.
