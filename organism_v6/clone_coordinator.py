"""Clone coordinator (NEXT_EXPERIMENT_DESIGN_v1 3.12; IDEAS 2026-09-10 night:
one child, X clones in X gyms, merged at every sleep).

X clones = X `run_life_v2` processes (each on its own GPU, each possibly in a
different gym) sharing ONE adapter lineage through a group directory:

  DIR/manifest.json            clone ids, gyms, stage schedule, runtime hashes
                               (no hosts, URLs or home paths: flags are
                               redacted before they are written)
  DIR/clones/clone_k.json      each clone's registration (gym, gate set, ...)
  DIR/clones/LIFE_DONE_k       clone k finished its life (the barrier stops
                               expecting it)
  DIR/cursors/clone_k.json     how many of clone k's ledger rows are pooled —
                               written by the COORDINATOR when it pools (the
                               truth), mirrored by the clone
  DIR/pooled_ledger.jsonl      the cumulative pooled ledger (all clones)
  DIR/round_NNNN/slice_k.jsonl clone k's ledger slice since its last pooled
                               sleep, every row stamped with provenance
                               (clone_id, gym, round) — hygiene only, no
                               per-source attribution analysis (Rohin:
                               "thoughts carry the gain")
  DIR/round_NNNN/slice_k.DONE  barrier marker ({n, start, end})
  DIR/round_NNNN/POOLING_k / POOLED_k   pooling intent / done (crash-safe)
  DIR/round_NNNN/round.json    present/skipped/finished clones, verdict, gate
                               stats (written BEFORE the verdict marker)
  DIR/round_NNNN/corpus.json   ONE compile_sleep over the pooled ledger
  DIR/round_NNNN/adapter.train the trainer's staging directory
  DIR/round_NNNN/adapter/      ONE adapter trained from the frozen base by the
                               existing trainer; appears (atomic rename from
                               adapter.train) holding CANDIDATE only, then
                               DONE or REJECTED_<reason> after the gate — a
                               DONE marker is NEVER visible before the gate

Protocol at a sleep boundary (round r = the clone's r-th sleep):
  every clone   attach_missed_rounds(): a round whose verdict arrived late
                (after this clone's round timeout) is attached now, so the
                clone converges to the group's best committed adapter;
                write_slice(r) -> barrier
  coordinator   (clone 0 by default) wait_for_slices(r, timeout): expected =
                every clone not marked LIFE_DONE; a clone that misses the
                barrier by more than the timeout is SKIPPED for this round and
                logged; the round still completes with the slices present.
                pool (rows already pooled for a clone — a stale cursor after
                a round timeout — are dropped by ledger index, so nothing is
                ever pooled twice) -> compile once -> train once into
                adapter.train -> promote (DONE -> CANDIDATE, atomic rename
                to adapter/) -> gate: the write commits (adapter/DONE) only
                if EVERY registered clone's gate passes — canary parseable-
                ACT rate, score >= floor - tol on THAT clone's gym GATE set
                (never its exam set; registration refuses a clone without a
                gate set), floor = max(base on that gate set, best committed
                round's probe on it), brevity ok on THAT clone's chunks — else
                adapter/REJECTED_<reason> naming the failing clone(s).
                round.json records it all, gate stats before the marker.
  every clone   wait_for_verdict(r) -> attach_round_to_life(): the round's
                adapter and corpus are symlinked and the waking brief COPIED
                (the parent's allow-listed reader refuses symlinks that leave
                the life dir) into the clone's own sleep_XXXX/ so the EXISTING
                reload path (run_life.latest_adapter -> sleep_*/adapter/DONE)
                picks it up unchanged. No verdict within the timeout ->
                CLONE_PENDING is left in the sleep dir and the clone continues
                on its current adapter; the next sleep attaches it.
Registration refuses: a clone without a gate set; a deployment-gym
(compiler) clone in a group with a trait-gym clone unless
allow_deployment_gym=True (then the manifest is labelled not_target_blind);
clones whose --episodes reach different round counts under the schedule;
a clone_count/coordinator that disagrees with the manifest.
Restart-safe: every step is a marker; re-running a round redoes nothing that
finished; a torn pooled append is truncated back on restart. Timing uses
time.monotonic (tests freeze time.time).
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import time

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

from .ledger import Ledger

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME_FILES = [
    "run_life_v2.py", "batch_loop.py", "state.py", "ledger.py",
    "sleep_compile.py", "train_adapter.py", "model_backend.py",
    "gym_backend.py", "reasoning_gym_gym.py", "clone_coordinator.py",
    "curriculum.py", "reflection.py", "bootstrap.txt",
    "bootstrap_reasoning_gym.txt", "reasoning_gym_families.json",
    "curriculum_schedule_v1.json",
    # the parent harness (design 3.5: mechanism_version covers it)
    "agentic_parent.py", "parent_brief.py", "parent_backend.py",
    "parent_prompt.txt",
]
DEPLOYMENT_DOMAIN_PREFIX = "compiler_gym"

_URL = re.compile(r"\b(?:https?|wss?|ftp|sftp|ssh|scp|smb)://[^\s\"'<>]+", re.I)
_HOME = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+")
_HOST = re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*"
                   r"\.(?:nvidia\.com|internal|local|lan|corp|intranet|cluster)\b",
                   re.I)
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _sha(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def runtime_hashes() -> dict:
    return {f: _sha(os.path.join(HERE, f)) for f in RUNTIME_FILES}


def redact(text: str) -> str:
    """URLs, home paths, internal hostnames and IPv4 addresses replaced (the
    manifest is hashed and mirrored; internal hosts live only in
    gpu/hosts.env)."""
    t = _URL.sub("<URL>", str(text))
    t = _HOME.sub("<HOME>", t)
    t = _HOST.sub("<HOST>", t)
    return _IPV4.sub("<IP>", t)


def redact_obj(obj):
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact_obj(v) for v in obj]
    return obj


def _marker(p: str) -> bool:
    return os.path.exists(p)


def _touch(p: str, text: str = "ok") -> None:
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        f.write(text + "\n")
    os.replace(tmp, p)


def _write_json(p: str, obj) -> None:
    tmp = p + f".tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, p)


def _read_json(p: str, default=None):
    if not os.path.exists(p):
        return default
    try:
        with open(p) as f:
            return json.load(f)
    except ValueError:
        return default


def _read_jsonl(p: str) -> list:
    out = []
    if not os.path.exists(p):
        return out
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


class ProvenanceLedger(Ledger):
    """The life ledger of a clone: every appended row carries clone_id, gym
    and exposure_domain (hygiene for the pooled compile; nothing reads them
    for attribution)."""

    def __init__(self, path: str, clone_id: int | None = None,
                 gym: str | None = None, exposure_domain: str | None = None):
        super().__init__(path)
        self.prov = {k: v for k, v in (("clone_id", clone_id), ("gym", gym),
                                       ("exposure_domain", exposure_domain))
                     if v is not None}

    def append(self, rec: dict) -> None:
        rec = dict(rec)
        for k, v in self.prov.items():
            rec.setdefault(k, v)
        super().append(rec)


class CloneGroup:
    def __init__(self, group_dir: str, clone_id: int, clone_count: int,
                 coordinator_id: int = 0, poll_s: float = 2.0, log=print,
                 clock=time.monotonic, sleep=time.sleep):
        if not (0 <= int(clone_id) < int(clone_count)):
            raise ValueError(f"clone id {clone_id} not in [0, {clone_count})")
        self.dir = os.path.abspath(os.path.expanduser(group_dir))
        self.clone_id = int(clone_id)
        self.clone_count = int(clone_count)
        self.coordinator_id = int(coordinator_id)
        self.poll_s = float(poll_s)
        self.log = log
        self.clock = clock
        self.sleep = sleep
        for d in ("clones", "cursors"):
            os.makedirs(os.path.join(self.dir, d), exist_ok=True)

    # -- paths -----------------------------------------------------------------
    @property
    def is_coordinator(self) -> bool:
        return self.clone_id == self.coordinator_id

    def round_dir(self, r: int) -> str:
        return os.path.join(self.dir, f"round_{int(r):04d}")

    def slice_path(self, r: int, k: int) -> str:
        return os.path.join(self.round_dir(r), f"slice_{k}.jsonl")

    def slice_done(self, r: int, k: int) -> str:
        return self.slice_path(r, k) + ".DONE"

    def record_path(self, r: int) -> str:
        return os.path.join(self.round_dir(r), "round.json")

    def adapter_dir(self, r: int) -> str:
        return os.path.join(self.round_dir(r), "adapter")

    def staging_dir(self, r: int) -> str:
        """Where the trainer writes; promoted to adapter_dir by an atomic
        rename once DONE has been renamed to CANDIDATE."""
        return self.adapter_dir(r) + ".train"

    def _life_done_path(self, k: int | None = None) -> str:
        k = self.clone_id if k is None else k
        return os.path.join(self.dir, "clones", f"LIFE_DONE_{k}")

    # -- locking / manifest --------------------------------------------------------
    def _lock(self):
        class _L:
            def __init__(s, path):
                s.path = path
                s.f = None

            def __enter__(s):
                s.f = open(s.path, "a")
                if fcntl is not None:
                    fcntl.flock(s.f.fileno(), fcntl.LOCK_EX)
                return s

            def __exit__(s, *a):
                if fcntl is not None:
                    fcntl.flock(s.f.fileno(), fcntl.LOCK_UN)
                s.f.close()
        return _L(os.path.join(self.dir, ".group.lock"))

    def register(self, **spec) -> dict:
        """Write this clone's spec (gym, gate/exam/canary sets, budget,
        compile vocabulary, n_rounds, ...) and merge it into
        DIR/manifest.json (clone ids, gyms, stage schedule, runtime hashes).
        Refuses (RuntimeError): no gate set; a deployment-gym clone in a group
        with a trait-gym clone without allow_deployment_gym; a round count
        that differs from an already registered clone's; a clone_count or
        coordinator that disagrees with the manifest. Paths, URLs and hosts
        never reach the manifest (redacted; life_dir -> its basename)."""
        spec = dict(spec)
        if spec.get("gate_set") is None or not list(spec.get("gate_set") or []):
            raise RuntimeError(
                "clone group requires a gate set disjoint from the exam set "
                "(design 3.3: the coordinator must never select an adapter on "
                "the report/exam panel); pass --gate-panel to this clone")
        if spec.get("life_dir"):
            spec["life_name"] = os.path.basename(os.path.normpath(spec["life_dir"]))
            del spec["life_dir"]
        if spec.get("flags") is not None:
            spec["flags"] = redact_obj(spec["flags"])
        spec = redact_obj(spec)
        spec.update(clone_id=self.clone_id, registered_at=time.time())
        with self._lock():
            mp = os.path.join(self.dir, "manifest.json")
            man = _read_json(mp, {}) or {}
            if man:
                for key, mine in (("clone_count", self.clone_count),
                                  ("coordinator", self.coordinator_id)):
                    if key in man and int(man[key]) != int(mine):
                        raise RuntimeError(
                            f"clone group manifest says {key}={man[key]} but "
                            f"this clone was launched with {key}={mine}")
            clones = dict(man.get("clones") or {})
            others = {int(k): v for k, v in clones.items()
                      if int(k) != self.clone_id}
            # deployment gym in a childhood group (Decision 1: the compiler
            # gym is the unseen final test): refused unless explicitly allowed
            mine_dep = str(spec.get("exposure_domain") or "").startswith(
                DEPLOYMENT_DOMAIN_PREFIX)
            dep = [k for k, c in others.items() if str(c.get("exposure_domain")
                                                       or "").startswith(DEPLOYMENT_DOMAIN_PREFIX)]
            trait = [k for k in others if k not in dep]
            mixed = (mine_dep and trait) or (not mine_dep and dep)
            if mixed and not spec.get("allow_deployment_gym"):
                raise RuntimeError(
                    "clone group mixes the deployment gym (compiler) with a "
                    f"trait gym (deployment clones {sorted(dep + ([self.clone_id] if mine_dep else []))}, "
                    f"trait clones {sorted(trait + ([] if mine_dep else [self.clone_id]))}): "
                    "the childhood must stay target-blind. Pass "
                    "--allow-deployment-gym to every clone of a DEVELOPMENT "
                    "group (the manifest is then labelled not_target_blind)")
            # equal round counts (curriculum shares differ per gym)
            if spec.get("n_rounds") is not None:
                for k, c in sorted(others.items()):
                    if c.get("n_rounds") is not None and \
                            int(c["n_rounds"]) != int(spec["n_rounds"]):
                        raise RuntimeError(
                            f"clone {self.clone_id} reaches {spec['n_rounds']} "
                            f"rounds but clone {k} ({c.get('gym')}) reaches "
                            f"{c['n_rounds']}: set --episodes per clone so every "
                            "clone sleeps the same number of times "
                            "(curriculum.episodes_for_rounds)")
            _write_json(os.path.join(self.dir, "clones",
                                     f"clone_{self.clone_id}.json"), spec)
            man.setdefault("group_name", os.path.basename(self.dir))
            man.setdefault("created_at", time.time())
            man.update(clone_count=self.clone_count,
                       coordinator=self.coordinator_id,
                       runtime_hashes=runtime_hashes())
            clones[str(self.clone_id)] = {
                k: v for k, v in spec.items()
                if k in ("clone_id", "gym", "life_name", "gate_set", "exam_set",
                         "canary_set", "budget_ticks", "seed", "arm",
                         "exposure_domain", "rank", "registered_at", "flags",
                         "n_rounds", "allow_deployment_gym")}
            man["clones"] = clones
            if spec.get("schedule") is not None:
                man["stage_schedule"] = spec["schedule"]
            if spec.get("reasoning_gym_version"):
                man["reasoning_gym_version"] = spec["reasoning_gym_version"]
            man["gyms"] = sorted({c.get("gym") for c in clones.values()
                                  if c.get("gym")})
            doms = {str(c.get("exposure_domain") or "") for c in clones.values()}
            has_dep = any(d.startswith(DEPLOYMENT_DOMAIN_PREFIX) for d in doms)
            has_trait = any(not d.startswith(DEPLOYMENT_DOMAIN_PREFIX) for d in doms)
            if has_dep and has_trait:
                man["not_target_blind"] = (
                    "development group: the deployment gym (compiler) is "
                    "pooled with a trait gym; no target-blindness claim")
            _write_json(mp, man)
        return spec

    def manifest(self) -> dict:
        return _read_json(os.path.join(self.dir, "manifest.json"), {}) or {}

    def clone_specs(self) -> dict:
        out = {}
        cd = os.path.join(self.dir, "clones")
        for f in sorted(os.listdir(cd)):
            if f.startswith("clone_") and f.endswith(".json"):
                s = _read_json(os.path.join(cd, f))
                if isinstance(s, dict):
                    out[int(s["clone_id"])] = s
        return out

    def mark_life_done(self) -> None:
        """This clone's life is over: the barrier stops expecting it."""
        _touch(self._life_done_path(), json.dumps(dict(at=time.time())))

    def finished_clones(self) -> list:
        return [k for k in range(self.clone_count)
                if _marker(self._life_done_path(k))]

    # -- cursors and slices -----------------------------------------------------------
    def _cursor_path(self, k: int | None = None) -> str:
        k = self.clone_id if k is None else k
        return os.path.join(self.dir, "cursors", f"clone_{k}.json")

    def cursor(self, k: int | None = None) -> int:
        """Rows of clone k's ledger already pooled (the coordinator writes
        this when it pools; the clone mirrors it)."""
        c = _read_json(self._cursor_path(k), {}) or {}
        return int(c.get("pooled_rows", 0))

    def _write_cursor(self, k: int, n: int, r: int) -> None:
        if int(n) > self.cursor(k):
            _write_json(self._cursor_path(k), dict(pooled_rows=int(n),
                                                    round=int(r)))

    def write_slice(self, r: int, rows: list, gym_name: str,
                    exposure_domain: str | None = None) -> int:
        """rows = the clone's WHOLE ledger; the slice is rows[cursor:], each
        stamped with provenance. Idempotent per round (marker). A stale
        cursor (round timeout) only makes the slice overlap the previous one;
        pool() drops the overlap by ledger index."""
        rd = self.round_dir(r)
        os.makedirs(rd, exist_ok=True)
        done = self.slice_done(r, self.clone_id)
        if _marker(done):
            return int((_read_json(done, {}) or {}).get("n", 0))
        start = self.cursor()
        sl = rows[start:]
        tmp = self.slice_path(r, self.clone_id) + ".tmp"
        with open(tmp, "w") as f:
            for row in sl:
                row = dict(row)
                row.setdefault("clone_id", self.clone_id)
                row.setdefault("gym", gym_name)
                if exposure_domain:
                    row.setdefault("exposure_domain", exposure_domain)
                row["round"] = int(r)
                f.write(json.dumps(row) + "\n")
        os.replace(tmp, self.slice_path(r, self.clone_id))
        _write_json(done, dict(n=len(sl), start=start, end=len(rows),
                               clone_id=self.clone_id, gym=gym_name,
                               written_at=time.time()))
        return len(sl)

    def slices_present(self, r: int) -> list:
        return [k for k in range(self.clone_count)
                if _marker(self.slice_done(r, k))]

    def wait_for_slices(self, r: int, timeout_s: float) -> tuple[list, list]:
        """Barrier. Returns (present, skipped). Expected = every clone not
        marked LIFE_DONE; finished clones are not waited for (recorded in
        barrier.json['finished']). A closed round (round.json or barrier.json
        exists) returns its recorded decision without waiting."""
        rec = _read_json(self.record_path(r)) or \
            _read_json(os.path.join(self.round_dir(r), "barrier.json"))
        if isinstance(rec, dict) and "present" in rec:
            return list(rec["present"]), list(rec["skipped"])
        t0 = self.clock()
        deadline = t0 + float(timeout_s)
        while True:
            finished = self.finished_clones()
            expected = [k for k in range(self.clone_count) if k not in finished]
            present = self.slices_present(r)
            if set(expected) <= set(present):
                break
            if self.clock() >= deadline:
                break
            self.sleep(self.poll_s)
        skipped = [k for k in expected if k not in present]
        not_waited = [k for k in finished if k not in present]
        waited = round(self.clock() - t0, 2)
        if skipped:
            self.log(f"[clone-group round {r}] BARRIER TIMEOUT after "
                     f"{waited}s: skipping clones {skipped} this round")
        if not_waited:
            self.log(f"[clone-group round {r}] clones {not_waited} have "
                     f"finished their lives: not waited for")
        os.makedirs(self.round_dir(r), exist_ok=True)
        _write_json(os.path.join(self.round_dir(r), "barrier.json"),
                    dict(present=present, skipped=skipped, finished=not_waited,
                         waited_s=waited, timeout_s=timeout_s))
        return present, skipped

    def pool(self, r: int, present: list) -> list:
        """Append the present slices to the cumulative pooled ledger and
        return ALL pooled rows. Idempotent per clone per round (POOLED_k);
        rows below the clone's pooled cursor (a slice written from a stale
        cursor after a round timeout) are dropped by ledger index, so no row
        is pooled twice; a crash between the append and the marker is undone
        on restart by truncating the ledger to the recorded size."""
        pl = os.path.join(self.dir, "pooled_ledger.jsonl")
        rd = self.round_dir(r)
        os.makedirs(rd, exist_ok=True)
        for k in range(self.clone_count):          # recover a torn append
            pooling = os.path.join(rd, f"POOLING_{k}")
            if _marker(pooling) and not _marker(os.path.join(rd, f"POOLED_{k}")):
                info = _read_json(pooling, {}) or {}
                size = int(info.get("bytes_before", 0))
                if os.path.exists(pl) and os.path.getsize(pl) > size:
                    with open(pl, "r+b") as f:
                        f.truncate(size)
                    self.log(f"[clone-group round {r}] recovered a torn pool "
                             f"append of clone {k} (truncated to {size} bytes)")
                os.remove(pooling)
        for k in present:
            mk = os.path.join(rd, f"POOLED_{k}")
            if _marker(mk):
                continue
            d = _read_json(self.slice_done(r, k), {}) or {}
            rows = _read_jsonl(self.slice_path(r, k))
            start = int(d.get("start", 0))
            end = int(d.get("end", start + len(rows)))
            cur = self.cursor(k)
            skip = max(0, min(len(rows), cur - start))
            if skip:
                self.log(f"[clone-group round {r}] clone {k}: {skip} rows of "
                         f"its slice were already pooled (stale cursor); dropped")
            rows = rows[skip:]
            pooling = os.path.join(rd, f"POOLING_{k}")
            before = os.path.getsize(pl) if os.path.exists(pl) else 0
            _write_json(pooling, dict(clone_id=k, round=int(r), bytes_before=before,
                                      start=start + skip, end=end, n=len(rows)))
            with open(pl, "a") as f:
                for row in rows:
                    f.write(json.dumps(row) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self._write_cursor(k, max(cur, end), r)
            os.replace(pooling, mk)
        return _read_jsonl(pl)

    def prior_corpus(self, r: int) -> list:
        for rr in range(int(r) - 1, 0, -1):
            cp = os.path.join(self.round_dir(rr), "corpus.json")
            c = _read_json(cp)
            if isinstance(c, dict):
                return list(c.get("corpus") or [])
        return []

    # -- records and verdicts ---------------------------------------------------------
    def write_record(self, r: int, record: dict) -> None:
        _write_json(self.record_path(r), record)

    def read_record(self, r: int) -> dict | None:
        rec = _read_json(self.record_path(r))
        return rec if isinstance(rec, dict) else None

    def verdict(self, r: int) -> str | None:
        """The round's final verdict marker, or None while the round is open.
        adapter/ never holds a DONE marker before the gate (the trainer
        writes into adapter.train; promotion renames DONE to CANDIDATE
        before the atomic rename), so a DONE seen here is final."""
        ad = self.adapter_dir(r)
        if not os.path.isdir(ad):
            rec = self.read_record(r)
            return rec.get("verdict") if rec and str(rec.get("verdict", "")).startswith("REJECTED") else None
        for m in sorted(os.listdir(ad)):
            if m == "DONE" or m.startswith("REJECTED"):
                return m
        return None

    def wait_for_verdict(self, r: int, timeout_s: float) -> str | None:
        deadline = self.clock() + float(timeout_s)
        while True:
            v = self.verdict(r)
            if v is not None:
                return v
            if self.clock() >= deadline:
                self.log(f"[clone {self.clone_id} round {r}] ROUND TIMEOUT: no "
                         f"verdict after {timeout_s}s; continuing with the "
                         f"current adapter")
                return None
            self.sleep(self.poll_s)

    def advance_cursor_if_pooled(self, r: int) -> bool:
        """Mirror of the coordinator's cursor write (same value); True when
        this clone's slice was pooled in round r."""
        rec = self.read_record(r)
        if not rec or self.clone_id not in rec.get("present", []):
            return False
        d = _read_json(self.slice_done(r, self.clone_id), {}) or {}
        cur = self.cursor()
        if int(d.get("end", cur)) > cur:
            self._write_cursor(self.clone_id, int(d["end"]), r)
        return True

    def committed_rounds(self, upto: int | None = None) -> list:
        out = []
        for d in sorted(os.listdir(self.dir)):
            if d.startswith("round_"):
                r = int(d[6:])
                if upto is not None and r > upto:
                    continue
                if self.verdict(r) == "DONE":
                    out.append(r)
        return out

    def attach_round_to_life(self, r: int, life_dir: str, sleep_dir: str) -> str | None:
        """Symlink the round's adapter and corpus and COPY its waking brief
        into the clone's own sleep dir; write CLONE_ROUND and, for the
        parent's allow-listed reader, gate.json with THIS clone's gate stats.
        Without a verdict yet, leave CLONE_PENDING (attach_missed_rounds
        finishes the job at a later sleep) and return None."""
        v = self.verdict(r)
        os.makedirs(sleep_dir, exist_ok=True)
        pend = os.path.join(sleep_dir, "CLONE_PENDING")
        if v is None:
            _write_json(pend, dict(round=int(r), group=self.dir,
                                   clone_id=self.clone_id))
            return None
        for name in ("adapter", "corpus.json"):
            src = os.path.join(self.round_dir(r), name)
            dst = os.path.join(sleep_dir, name)
            if os.path.exists(src) and not os.path.lexists(dst):
                os.symlink(src, dst)
        bp = os.path.join(self.round_dir(r), "waking_brief.txt")
        dst = os.path.join(sleep_dir, "waking_brief.txt")
        if os.path.exists(bp) and not os.path.lexists(dst):
            tmp = dst + ".tmp"
            shutil.copyfile(bp, tmp)
            os.replace(tmp, dst)
        rec = self.read_record(r) or {}
        g = (rec.get("gate") or {}).get("per_clone", {}).get(str(self.clone_id))
        gj = os.path.join(sleep_dir, "gate.json")
        if isinstance(g, dict) and not os.path.exists(gj):
            _write_json(gj, dict(g, verdict=v, round=r))
        _touch(os.path.join(sleep_dir, "CLONE_ROUND"),
               json.dumps(dict(round=r, verdict=v, group=self.dir)))
        if _marker(pend):
            os.remove(pend)
        return v

    def attach_missed_rounds(self, life_dir: str) -> list:
        """Attach every earlier round whose verdict arrived after this
        clone's round timeout (sleep dirs holding CLONE_PENDING without
        CLONE_ROUND). Returns [(round, verdict, sleep dir name)] so the
        caller can reload when latest_adapter changed."""
        out = []
        for d in sorted(os.listdir(life_dir)):
            sd = os.path.join(life_dir, d)
            pend = os.path.join(sd, "CLONE_PENDING")
            if not (d.startswith("sleep_") and os.path.isdir(sd)
                    and _marker(pend) and not _marker(os.path.join(sd, "CLONE_ROUND"))):
                continue
            rr = int((_read_json(pend, {}) or {}).get("round", -1))
            if rr < 0 or self.verdict(rr) is None:
                continue
            v = self.attach_round_to_life(rr, life_dir, sd)
            self.advance_cursor_if_pooled(rr)
            self.log(f"[clone {self.clone_id} round {rr}] late verdict={v} "
                     f"attached to {d}")
            out.append((rr, v, d))
        return out


def coordinate_round(group: CloneGroup, r: int, compile_fn, train_fn, gate_fn,
                     barrier_timeout_s: float, log=print) -> str:
    """The coordinator's work for round r (restart-safe):
      compile_fn(rows, out_dir, prior_corpus) -> dict   (compile_sleep)
      train_fn(corpus_path, staging_dir) -> returncode  (the trainer; writes
                                                         staging_dir/DONE)
      gate_fn(adapter_dir, clone_specs) -> dict(ok, reason, per_clone)
    Returns the verdict marker name ("DONE" or "REJECTED_<reason>"). The
    trainer never writes into adapter/: its DONE is renamed to CANDIDATE in
    the staging dir, which is then renamed atomically to adapter/, so no
    clone can observe a DONE marker before the gate has run. Gate stats are
    written to round.json BEFORE the verdict marker."""
    rd = group.round_dir(r)
    os.makedirs(rd, exist_ok=True)
    present, skipped = group.wait_for_slices(r, barrier_timeout_s)
    barrier = _read_json(os.path.join(rd, "barrier.json"), {}) or {}
    rows = group.pool(r, present)
    rec = group.read_record(r) or dict(round=r)
    rec.update(present=present, skipped=skipped,
               finished=list(barrier.get("finished") or []),
               n_pooled_rows=len(rows), coordinator=group.clone_id)
    group.write_record(r, rec)
    if not _marker(os.path.join(rd, "COMPILED")):
        res = compile_fn(rows, rd, group.prior_corpus(r))
        rec["compile"] = {k: v for k, v in (res or {}).items()
                          if k in ("n_new", "n_principles", "n_stream",
                                   "n_recall")}
        group.write_record(r, rec)
        _touch(os.path.join(rd, "COMPILED"))
        log(f"[clone-group round {r}] compiled pooled rows={len(rows)} "
            f"from clones {present} (skipped {skipped}) -> {rec.get('compile')}")
    verdict = group.verdict(r)
    ad = group.adapter_dir(r)
    stage = group.staging_dir(r)
    if verdict is None:
        if not os.path.exists(os.path.join(ad, "CANDIDATE")):
            if _marker(os.path.join(stage, "DONE")):
                rc = 0            # trained before a crash; promotion pending
            else:
                rc = train_fn(os.path.join(rd, "corpus.json"), stage)
            rec["train_rc"] = rc
            if rc != 0 or not _marker(os.path.join(stage, "DONE")):
                os.makedirs(ad, exist_ok=True)
                if _marker(os.path.join(stage, "DONE")):   # rc != 0 but DONE written
                    os.replace(os.path.join(stage, "DONE"),
                               os.path.join(stage, f"TRAIN_DONE_BUT_RC_{rc}"))
                verdict = "REJECTED_TRAIN"
                _touch(os.path.join(ad, verdict), f"rc={rc}")
            else:
                # promote: never a DONE marker inside adapter/ before the gate
                os.replace(os.path.join(stage, "DONE"),
                           os.path.join(stage, "CANDIDATE"))
                os.rename(stage, ad)
        if verdict is None:
            if rec.get("pending_verdict") and rec.get("gate"):
                # gated before a crash that preceded the marker: apply it
                verdict = str(rec["pending_verdict"])
            else:
                gate = gate_fn(ad, group.clone_specs())
                rec["gate"] = gate
                verdict = "DONE" if gate.get("ok") else \
                    f"REJECTED_{gate.get('reason') or 'GATE'}"
                rec["pending_verdict"] = verdict
                group.write_record(r, rec)      # stats persist before the marker
            os.replace(os.path.join(ad, "CANDIDATE"), os.path.join(ad, verdict))
    rec.pop("pending_verdict", None)
    rec["verdict"] = verdict
    rec["closed_at"] = time.time()
    group.write_record(r, rec)
    log(f"[clone-group round {r}] verdict={verdict}")
    return verdict


def probe_summary(dir_: str, tag: str) -> tuple[float | None, float | None]:
    """(mean, chunks per episode) of a finished probe written by
    run_life_v2.run_probes_batch into dir_."""
    pj = _read_json(os.path.join(dir_, f"probe_{tag}.json"))
    if not isinstance(pj, dict):
        return None, None
    n_eps = len(pj.get("results") or []) or 1
    lp = os.path.join(dir_, f"probe_{tag}.ledger.jsonl")
    n_th = sum(1 for r in _read_jsonl(lp) if r.get("kind") == "thought")
    return pj.get("mean"), n_th / max(1, n_eps)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="clone group status")
    ap.add_argument("--group", required=True)
    a = ap.parse_args()
    g = os.path.expanduser(a.group)
    man = _read_json(os.path.join(g, "manifest.json"), {})
    print(json.dumps(dict(clones=len(man.get("clones", {})),
                          gyms=man.get("gyms"),
                          not_target_blind=man.get("not_target_blind"),
                          schedule=(man.get("stage_schedule") or {}).get("name")),
                     indent=1))
    for d in sorted(os.listdir(g)):
        if d.startswith("round_"):
            rec = _read_json(os.path.join(g, d, "round.json"), {}) or {}
            print(d, rec.get("verdict"), "present", rec.get("present"),
                  "skipped", rec.get("skipped"), "finished", rec.get("finished"))


if __name__ == "__main__":
    main()
