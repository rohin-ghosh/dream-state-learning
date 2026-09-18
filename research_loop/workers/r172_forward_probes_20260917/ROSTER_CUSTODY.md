# R172 per-life design custody / missingness

Snapshot times are R171 observations, not new liveness checks. All 24 require fresh admission;
18 have prior R167 markers, six require new custody. No R172 frontier or baseline reuse is verified.

| Life | Node/physical | Snapshot UTC | Saved metadata only | Prior marker | Additional missing custody |
| --- | --- | --- | --- | --- | --- |
| C1 | ovx3/0 | 14:50:27 | 37 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| C2 | ovx3/1 | 14:50:27 | 36 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| C3 | ovx3/3 | 14:50:27 | 34 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| C4 | ovx3/4 | 14:50:27 | 34 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| C5 | ovx3/5 | 14:50:27 | 33 | False | EXACT_RECOVERY_RELEASE_AND_COMMIT_CHAIN, ORIGINAL_INITIAL_BIRTH_NOT_RECOVERY_PROMPT |
| KERNEL0_RESUMED_SPARSE2 | a40r/0 | 14:50:29 | 37 | False | NEW_EXACT_DECLARATION, ORIGINAL_BIRTH_INITIAL_AND_LINEAGE_CHAIN |
| brain_free | ovx2/2 | 14:50:26 | 40 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| brain_guided | ovx2/3 | 14:50:26 | 38 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| classroom_brain | a100/5 | 14:50:25 | 37 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| classroom_creative | a100/6 | 14:50:25 | 38 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| classroom_support | a100/7 | 14:50:25 | 42 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| continual_run1 | ovx3/2 | 14:50:27 | 45 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| creative_free | ovx2/4 | 14:50:26 | 39 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| creative_reread | ovx2/1 | 14:50:26 | 42 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| creative_select | ovx2/7 | 14:50:26 | 40 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| orch_r136_raw_unparented_a40r1_20260916_attempt1 | a40r/1 | 14:50:29 | 39 | False | NEW_EXACT_DECLARATION, ORIGINAL_BIRTH_INITIAL_AND_LINEAGE_CHAIN |
| pilot | ovx3/6 | 14:50:27 | 42 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| r137_kernel4_sparse2_free_coach | a40r/4 | 14:50:29 | 36 | False | NEW_EXACT_DECLARATION, ORIGINAL_BIRTH_INITIAL_AND_LINEAGE_CHAIN |
| r137_raw3_sparse3_free_socratic_seed1 | a40r/3 | 14:50:29 | 38 | False | NEW_EXACT_DECLARATION, ORIGINAL_BIRTH_INITIAL_AND_LINEAGE_CHAIN |
| repo_reader | ovx3/7 | 14:50:27 | UNKNOWN (old-root 30 is not current) | False | PROCESS_ROOT_TO_RECOVERY_STORAGE_ALIAS, FRESH_RECOVERY_STORAGE_FRONTIER |
| support_free | ovx2/0 | 14:50:26 | 42 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| teach_parenting | a100/4 | 14:50:25 | 40 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| teach_perception | a100/3 | 14:50:25 | 40 | True | fresh identity/frontier/birth/copy; baseline match unverified |
| teach_replay | a100/2 | 14:50:25 | 39 | True | fresh identity/frontier/birth/copy; baseline match unverified |

Zero R172 GPU/provider calls; zero new source/adapter reads. Missing is not negative.
Exact roots, PID/start/boot, plan/config references and roster hash are in PROPOSAL.json.
