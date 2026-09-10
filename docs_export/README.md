# docs_export — documentation that lived outside the repo until 2026-09-10

- `memory/` — the assistant's persistent project memory files (rulings, preferences, infra laws, lessons) kept in its own memory directory across sessions; copied here verbatim except for redaction of internal addresses.
- `workflow_reports/` — the full structured outputs of every agent in the multi-agent workflows (paper draft v1: 186 agents; harsh review of the notes: 118; paper revision and review: 73; next-experiment design: 12 so far; earlier PCFL/reviewer workflows), exported from the workflow journals. These are the raw findings, judgments, designs and verdicts behind REVIEW_HARSH_2026-09-10.md, REVIEW_PAPER_PROTOTYPE_2026-09-10.md and paper_prototype/.
- `../gpu/node_scripts/` — helper scripts that ran on the GPU nodes (status, readers, lineage chains, bootstrap training, parent-server chains).
- `../gpu/local_watchers/` — the laptop-side watcher and provisioning scripts (internal addresses redacted to <INTERNAL_IP>/<INTERNAL_HOST>).
