# Manifest of raw data and environments (2026-09-10)

| artifact | contents | location(s) | SHA-256 |
|---|---|---|---|
| node1_v6_out_receipts_2026-09-10.tar.gz | node-1 `~/v6_out` receipts: ledgers, probe JSON + ledgers, gate.json, briefs, corpora, life logs (adapters excluded); 10,202 files, 1.03 GB | laptop `~/dream-state-artifacts/`; node 2 `~/node1_mirror/` | 557ee80a0dd6cd283d2e1f654d1d9efc80e954ca815c6deee53cea9f69504d5c |
| node1_adapters.tar.gz | node-1 committed adapters: final and mid-life for every life (20 adapters); manifest `list.txt` | node 1 `~/adapter_pack/` (4 parts); downloading to laptop | recorded in `~/adapter_pack/sha256.txt` (see `~/dream-state-artifacts/adapters_sha256_node1.txt`) |
| node environments | `pip freeze`, torch 2.13.0+cu130, vLLM 0.27.1, PEFT 0.20.0, transformers 5.5.3, driver 580.173.02; child Qwen2.5-7B-Instruct snapshot a09a35458c702b33eeacc393d103063234e8bc28 | `~/v6_out/ENV/` on both nodes | — |
| analysis JSON | per-life, noise, per-program, ritual ON/OFF; efficiency and markers | `research_notes/analysis/` | in git |

Node 1 lease ends 2026-09-14; node 2 ~2026-09-21. Raw probe/gate JSON for node 2 remains on node 2 (`~/v6_out`) until archived.
