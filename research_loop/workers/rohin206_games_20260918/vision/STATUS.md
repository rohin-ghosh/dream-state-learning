# Current R209 service — September18,2026 04:41 UTC

- Actual node4 physical1 combined VLM LOADED04:40:24.065UTC; listening04:40:29.746UTC; PID3987161. Physical0 verified empty and released to Main04:41:02UTC. No old learner signaled.
- Three real HTTP image→scene calls completed04:40:52.048UTC, generated73/84/149 tokens. Exact game/image/evidence paths and hashes are in `API.md`; receiving root is `/localhome/local-rohing/rohin206_games_20260918/vision_node4_r209`.
- Vision endpoint `http://[REDACTED_ADDRESS]:8178/v1/inspect`; exact client source SHA256 `aa49c3e2bf7c7495e8629b7a3fe16f830afc6e48d77042fe9f7eec110dde3f18`. Private comparator socket is listening on the same model, separately from game integration; no real caption comparison claimed yet.
- 41 focused local and receiving tests PASS. Actual startup partial-JSON failure preserved in previous `vision_node4` runtime. The repaired prompt requests plain factual prose; canonicalization preserves raw output and does not invent syntax or facts. No independent accuracy claim.
- Main scalar export hash verified read-only: `0bcd17e266defc772855501a1da02286ce83c80b975e081eb0acfa9e67239c3f`. No scalar/judge/game source, private panels, frozen bundles or COORDINATION edited.
- All ovx5 GPU allocation is paused under R209. Existing node4 cached Qwen weights used; finite lease cutoff18:00UTC unchanged. Persistent supervision, exact device confinement and receipt bindings retained.
- Source deployment is identified by byte hashes, not a claim of commit/push: this checkout still reported HEAD `de1fc4b779e939a1082c54c341bef8a6a6497512` and untracked vision source/tests. Main's separately reported preservation commit is not the deployed revision identifier.

## Historical preparation — superseded

Actual ovx5 SSH attempted2026-09-18 around04:19UTC: public-key authentication denied. No remote changes or GPU dispatches. Assigned newnode physical5 vision and physical4 comparator; other slots remain untouched.

Inspected only existing released-development R177 vision receipts: five `invalid_json_no_repair` and two `exact_visual_schema` errors, all EOS/nontruncated. Old receipts contain only raw output hashes, not raw strings; exact original formatting cannot be reconstructed. No claim that old failures have been repaired retrospectively.

Local non-material vision repair preserves raw output on success/failure, adds disclosed complete-fence/string-list canonicalization and verbatim plaintext fallback with an explicitly operator-authored uncertainty notice, and retains rejection of malformed structured JSON, extra fields, duplicates, unsafe content and truncation. Raw and canonical forms are hash-bound at the HTTP client. Model-facing facts are never invented; tests are not actual image receipts.

Added targeted tests in the assigned `tests/test_ny_caption_vision.py`. Initial system-Python test attempt could not run because pytest is not installed there; validation remains pending in the project environment. The new persistent lease-bounded service/comparator operator is NOT implemented or dispatched yet. Legacy backend budget check now accepts finite lease-bounded durations rather than a one-hour maximum; old owner metadata itself is unchanged and must not be used to claim new service persistence.

Need actual admitted ovx5 device/lease/model bindings and image→scene receipt before any serving-ready claim. Comparator will be local image+caption, origin-blind, Main-private, without private panel or raw-caption delivery to parents. R207 scalar ranker/constructed contrasts and all threshold decisions are Main-owned; no30-percent guess or three-class quantile gate is introduced here.
