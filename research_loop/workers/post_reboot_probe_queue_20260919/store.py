"""Durable queue projection with append-only audit events and no attempt retry."""

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

import admission as rules


ACTIVE = {"INTENT", "DISPATCHED", "RUNNING", "RECONCILING"}
TERMINAL = {"SUCCEEDED", "COMPLETED_WITH_SCORING_SHORTFALL", "FAILED_NO_RETRY",
    "INTERRUPTED_NO_RETRY", "UNKNOWN_NO_RETRY", "PRIOR_ATTEMPT_NO_RETRY"}


class Store:
    def __init__(self, path, policy=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS entries (ordinal INTEGER PRIMARY KEY, source_key TEXT UNIQUE NOT NULL,
                journal TEXT NOT NULL, record_index INTEGER NOT NULL, payload TEXT NOT NULL,
                fingerprint TEXT NOT NULL, UNIQUE(journal, record_index));
            CREATE TABLE IF NOT EXISTS attempts (job_id TEXT PRIMARY KEY, source_key TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL, intent TEXT NOT NULL, receipt TEXT);
            CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL,
                payload TEXT NOT NULL, previous_sha256 TEXT, sha256 TEXT NOT NULL);
        """)
        if policy is not None:
            rules.validate_policy(policy)
            with self.transaction():
                existing = self.get_meta("policy")
                if existing is None:
                    self.set_meta("policy", policy)
                    self.event("POLICY_BOUND", dict(policy_sha256=rules.digest(policy)))
                else:
                    rules.require(existing == policy, "explicit_review_rebind_required")

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()

    def get_meta(self, key):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def set_meta(self, key, value):
        self.db.execute("INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, rules.canonical(value)))

    def event(self, kind, payload):
        previous = self.db.execute("SELECT sha256 FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = previous[0] if previous else None
        fingerprint = rules.digest(dict(kind=kind, payload=payload, previous_sha256=previous))
        self.db.execute("INSERT INTO events(kind,payload,previous_sha256,sha256) VALUES (?,?,?,?)",
            (kind, rules.canonical(payload), previous, fingerprint))

    def verify_events(self):
        previous = None
        for row in self.db.execute("SELECT * FROM events ORDER BY seq"):
            rules.require(row["previous_sha256"] == previous and row["sha256"] == rules.digest(dict(
                kind=row["kind"], payload=json.loads(row["payload"]), previous_sha256=previous)), "audit_chain_changed")
            previous = row["sha256"]

    def ingest(self, rows, snapshot_refs):
        incoming = {}
        for entry in rows:
            rules.validate_entry(entry)
            key = rules.source_key(entry)
            rules.require(key not in incoming or incoming[key] == entry, "conflicting_duplicate_enrollment")
            incoming[key] = entry
        with self.transaction():
            existing = {row["source_key"]: row for row in self.db.execute("SELECT * FROM entries")}
            rules.require(set(existing) <= set(incoming), "enrollment_snapshot_regression_no_age_deletion")
            added = 0
            for key, entry in incoming.items():
                if key in existing:
                    rules.require(existing[key]["fingerprint"] == rules.digest(entry), "immutable_enrollment_or_epoch_changed")
                    continue
                self.db.execute("INSERT INTO entries(source_key,journal,record_index,payload,fingerprint) VALUES (?,?,?,?,?)",
                    (key, entry["journal_id"], entry["record_index"], rules.canonical(entry), rules.digest(entry)))
                added += 1
            if added:
                self.event("ENROLLMENT_IMPORTED", dict(added=added, retained=len(incoming), inputs=snapshot_refs))
        return added

    def entries(self):
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM entries ORDER BY ordinal")]

    def attempts(self):
        return [dict(job_id=row["job_id"], source_key=row["source_key"], status=row["status"],
            intent=json.loads(row["intent"]), receipt=json.loads(row["receipt"]) if row["receipt"] else None)
            for row in self.db.execute("SELECT * FROM attempts ORDER BY rowid")]

    def active(self):
        return [row for row in self.attempts() if row["status"] in ACTIVE]

    def pause(self, reason):
        with self.transaction():
            if self.get_meta("pause") != reason:
                self.set_meta("pause", reason)
                self.event("PAUSED_REVIEW_REQUIRED", dict(reason=reason))

    def prior_attempt(self, key, evidence):
        with self.transaction():
            if self.db.execute("SELECT 1 FROM attempts WHERE source_key=?", (key,)).fetchone():
                return
            row = self.db.execute("SELECT payload FROM entries WHERE source_key=?", (key,)).fetchone()
            if not row:
                return
            entry = json.loads(row[0])
            identifier = rules.job_id(entry)
            self.db.execute("INSERT INTO attempts VALUES (?,?,?,?,?)", (identifier, key,
                "PRIOR_ATTEMPT_NO_RETRY", rules.canonical(dict(imported=True)), rules.canonical(evidence)))
            self.event("PRIOR_ATTEMPT_IMPORTED", dict(job_id=identifier, source_key=key, evidence=evidence))

    def record_intent(self, plan):
        with self.transaction():
            rules.require(self.get_meta("pause") is None, "queue_paused")
            rules.require(not self.active(), "serialized_lane_already_has_intent")
            row = self.db.execute("SELECT payload FROM entries WHERE source_key=?", (plan["source_key"],)).fetchone()
            rules.require(row is not None and rules.job_id(json.loads(row[0])) == plan["job_id"], "intent_source_join")
            self.db.execute("INSERT INTO attempts VALUES (?,?,?,?,NULL)",
                (plan["job_id"], plan["source_key"], "INTENT", rules.canonical(plan)))
            self.event("DURABLE_INTENT_BEFORE_REMOTE_CALL", plan)

    def update_attempt(self, identifier, status, receipt):
        rules.require(status in ACTIVE | TERMINAL, "known_lifecycle_state")
        with self.transaction():
            row = self.db.execute("SELECT status,receipt FROM attempts WHERE job_id=?", (identifier,)).fetchone()
            rules.require(row is not None, "existing_attempt_only")
            if row["status"] in TERMINAL:
                rules.require(row["status"] == status, "terminal_state_never_retried_or_rewritten")
                return
            if row["status"] == status:
                return
            self.db.execute("UPDATE attempts SET status=?,receipt=? WHERE job_id=?",
                (status, rules.canonical(receipt), identifier))
            self.event("JOB_LIFECYCLE", dict(job_id=identifier, status=status, receipt=receipt))

    def rebind(self, policy, review):
        rules.validate_policy(policy)
        old = self.get_meta("policy")
        rules.require(review["old_policy_sha256"] == rules.digest(old)
            and review["new_policy_sha256"] == rules.digest(policy)
            and review["reviewed"] is True and rules.is_sha(review["source_freeze_sha256"]), "exact_review_rebind_receipt")
        allowed = {"receiving_boot_id", "protected_processes", "supported_journals", "frontiers", "source_roots", "initial_loaded", "current_loaded"}
        rules.require(all(old.get(key) == policy.get(key) for key in set(old) | set(policy) if key not in allowed), "rebind_cannot_extend_lease_lane_or_battery")
        with self.transaction():
            rules.require(not self.active(), "reconcile_existing_job_before_rebind")
            self.set_meta("policy", policy)
            self.set_meta("pause", None)
            self.event("EXPLICIT_REVIEW_REBIND", dict(review=review, old=old, new=policy))


def select(store, capsules, policy):
    attempts = store.attempts()
    attempted = {row["source_key"] for row in attempts}
    entries = store.entries()
    dispositions = [dict(source_key=rules.source_key(entry), life=entry["life"], sleep=entry["sleep"],
        journal_id=entry["journal_id"], runtime_load=entry.get("runtime_load"), record_index=entry["record_index"],
        status=rules.classify(entry, attempted, capsules, policy)) for entry in entries]
    ready_keys = {row["source_key"] for row in dispositions if row["status"] == "CPU_ELIGIBLE_PENDING_CURRENT_ADMISSION"}
    by_key = {rules.source_key(entry): entry for entry in entries}
    last_attempt = {}
    for ordinal, attempted_row in enumerate(attempts, 1):
        entry = by_key.get(attempted_row["source_key"])
        if entry:
            last_attempt[entry["life"]] = ordinal
    candidates = sorted((by_key[key] for key in ready_keys), key=lambda entry:
        (last_attempt.get(entry["life"], 0), entry["record_index"], entry["life"], entry["key"]))
    return dict(dispositions=dispositions, selected=candidates[0] if candidates else None,
        retained=len(entries), pending=sum(row["source_key"] not in attempted for row in dispositions),
        active=store.active(), pause=store.get_meta("pause"), automatic_launch=False)
