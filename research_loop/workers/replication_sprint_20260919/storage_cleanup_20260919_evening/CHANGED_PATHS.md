# Exact changed paths

All 16 local files below are newly added for this task, under the sole allowed
output directory. Code and receipts were written using `apply_patch`. No
pre-existing local source, evidence, instruction file, or Git index was edited.
No commit or push was performed.

- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/audit.py`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/test_audit.py`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/CPU_TESTS.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/AUDIT_RECEIPT.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/archive_cleanup.py`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/test_archive_cleanup.py`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/CPU_ARCHIVE_TESTS.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/PREPARE_REJECTION_1.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/CPU_ARCHIVE_TESTS_2.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/ARCHIVE_INTEGRITY.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/DELETION_MANIFEST.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/PREDELETE_RECEIPT.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/DELETION_RECEIPT.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/FINAL_VERIFICATION.json`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/REPORT.md`
- `research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/CHANGED_PATHS.md`

The only remote evidence/data changes were deletion of these three exact
redundant archive copies, plus their parent directory's unavoidable unlink
metadata updates:

- `/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/final_transport/physical1.tar.gz`
- `/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/final_transport/physical4.tar.gz`
- `/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/final_transport/physical7.tar.gz`

The independently verified surviving archive files were read only and remain
unchanged. Disposable synthetic CPU-test fixtures were automatically removed;
their bytes are not included in reclaimed-storage totals.
