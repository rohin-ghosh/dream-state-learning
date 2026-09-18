# One bounded follow-up; first acquisition preserved

The first pass succeeded as transport but five manifests exceeded the
1,024-source-file count ceiling. Follow-up does not widen that ceiling:
for such manifests read only the declared guard/native/journal/R161 `.py`
entry files (at most four), reporting partial closure and retaining the
current native identity. Complete small manifests retain full declared-pin
verification. No assertion about extra unlisted files or in-memory code.

Both passes count cumulatively against 32 MiB per life. Recheck native
identity after frontier acquisition. Correct the first-pass display's
`birth_context_present`: PLAN stores `system_prompt` and `birth_prompt`
directly, not in a `context` object. First-pass false therefore does NOT mean
birth is missing. The exact PLAN hash evidence remains unchanged.

For repo_reader, stat/hash original process-root initial metadata separately;
never substitute it for the absent restored-storage-root initial baseline.
Still no record documents, response/loss payloads, tensor reads or queue writes.
