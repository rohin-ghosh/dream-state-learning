#!/usr/bin/env python3
"""astra_agent — an AUTONOMOUS, allow-listed tool loop for Astra (the reasoning
model on the inference hub, see tools/astra.py) over the dream-state repository.

  ASTRA_API_KEY=... python3 tools/astra_agent.py --task FILE_OR_TEXT [--steps 80] [--effort high]
                    [--policy tools/astra_policy.json] [--token-budget N] [--wall-minutes M]
  python3 tools/astra_agent.py --dry-run "<cmd>" [--dry-run "<cmd>" ...]   # policy decision only, nothing runs
  python3 tools/astra_agent.py --dry-run-write PATH  |  --dry-run-read PATH
  python3 tools/astra_agent.py --task ... --mock-replies FILE               # offline loop smoke, no network

Nobody is asked for permission while it runs and no destructive action is
possible: every tool call is checked in code against tools/astra_policy.json,
whose DENY rules override everything. Rules enforced here (not merely asked
of the model):

  key            ASTRA_API_KEY is read from the environment ONCE at start,
                 removed from os.environ (no subprocess inherits it), used
                 only in the Authorization header of requests to the
                 configured host (redirects refused, proxies ignored, no
                 plaintext http to a non-loopback host) and masked in every
                 string that reaches the transcript, the report, stderr or a
                 written file. The base URL is never logged either.
  hostnames      Internal hosts live only in gpu/hosts.env, which the harness
                 never reads for the model and never prints; its values are
                 loaded only as masked secrets so that they can be refused in
                 any argument and blanked in any output. Node commands go
                 through gpu/a40_ssh.sh and gpu/ovx_ssh.sh, which resolve the
                 host themselves. Hostnames, IPs, URLs, e-mails and home paths
                 are redacted from every tool result before it is sent and
                 refused in every command.
  read_file / list_dir / grep   any path inside the repository (realpath-
                 resolved, so a symlink cannot alias a forbidden file) except
                 gpu/hosts.env, .git and the transcripts of other runs.
  write_file     only under tools/astra_sandbox/**, tests/astra/** and
                 research_notes/astra_agent/** (not runs/); no '..', no
                 symlink anywhere in the path; size-capped; the content goes
                 through the same safe_text() as every other outward path
                 (secrets masked, internal identifiers redacted).
  run            ONE command, no shell: argv from shlex, shell operators
                 refused; the deny scan runs on the raw text AND on the
                 tokenized form (quotes or extra whitespace cannot split a
                 denied token or phrase); local commands must match an
                 allow-listed prefix and every path argument must stay inside
                 the repository; '>' redirections only into the write sandbox;
                 git is inspection-only (--output and its abbreviations, -O
                 and --ext-diff are refused: git would write ANY file itself,
                 past the redirect guard and the python guard). Node commands
                 are exactly  bash gpu/<a40|ovx>_ssh.sh '<remote>'  and the
                 remote string is checked token by token (allow-listed
                 prefix, pipe filters, redirection targets, nohup only before
                 a smoke script, THE GPU ARGUMENT OF A SMOKE SCRIPT MUST BE 6
                 ON NODE 1 and smoke scripts are disabled on node 2). Every
                 run has a wall-clock timeout (default 900 s; the process
                 group is killed) and its stdout/stderr are captured and
                 truncated. Local python runs additionally get a
                 sitecustomize guard that refuses file mutation outside the
                 sandbox and temp dirs (an accident guard, not an OS sandbox).
  loop           JSON text protocol (one tool call or the final report per
                 turn); step budget (default 80) and token budget; when either
                 is spent the model is asked ONCE for the final report and, if
                 it does not deliver one, the harness synthesizes it from its
                 own record. The full transcript (prompts, tool calls,
                 truncated results, the report) is saved under
                 research_notes/astra_agent/runs/<utc-timestamp>/
                 (transcript.jsonl, report.md, run.json), every string masked.
                 Retries on 408/409/429/5xx and connection errors.

Standard library only; Python >= 3.9 (the system python3) and the 3.12 venv.
"""
from __future__ import annotations

import argparse
import datetime
import functools
import getpass
import glob
import json
import os
import re
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(HERE)
DEFAULT_POLICY_REL = os.path.join("tools", "astra_policy.json")
DEFAULT_BASE_URL = "https://inference-api.nvidia.com/v1"
DEFAULT_MODEL = "openai/openai/gpt-6-astra"
VENV_PLACEHOLDER = "<venv312>"
REPORT_KEYS = ("summary", "files_written", "tests_run", "findings",
               "proposed_runbook", "gaps")
TOOL_NAMES = ("read_file", "list_dir", "grep", "write_file", "run")
HARNESS_VERSION = "astra-agent-v1.1-2026-09-11"
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "::1")
MAX_TOKENS_CEILING = 200000


# ---------------------------------------------------------------------------
# secrets, aliases and internal identifiers (patterns shared with
# organism_v6.agentic_parent — re-implemented here so this tool never imports
# a module that concurrent builds are editing)
# ---------------------------------------------------------------------------
_SECRETS: list = []
_ALIASES: list = []          # (real text, public alias) e.g. (venv path, <venv312>)


def register_secret(value, min_len: int = 6) -> None:
    """Remember a secret so mask_secrets() blanks it in anything written."""
    if isinstance(value, str) and len(value) >= min_len and value not in _SECRETS:
        _SECRETS.append(value)


def register_alias(real: str, alias: str) -> None:
    if real and (real, alias) not in _ALIASES:
        _ALIASES.append((real, alias))
        rp = os.path.realpath(real)
        if rp != real and (rp, alias) not in _ALIASES:
            _ALIASES.append((rp, alias))


def mask_secrets(text: str) -> str:
    if not isinstance(text, str):
        return text
    for s in sorted(_SECRETS, key=len, reverse=True):
        text = text.replace(s, "***")
    for real, alias in sorted(_ALIASES, key=lambda x: len(x[0]), reverse=True):
        text = text.replace(real, alias)
    return text


_ID_PATTERNS = [
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("email_or_user_at_host",
     re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\b")),
    ("home_path", re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+")),
    ("url", re.compile(r"\b(?:https?|wss?|ftp|sftp|ssh|scp|smb)://[^\s\"'<>]+", re.I)),
    ("internal_host",
     re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*"
                r"\.(?:nvidia\.com|internal|local|lan|corp|intranet|cluster)\b", re.I)),
]
_GENERIC_NAMES = {"root", "user", "test", "admin", "localhost", "none", "python"}
_LOCAL_IDS: list = []


def _local_identifiers() -> list:
    """User and host names of THIS machine (computed once)."""
    if _LOCAL_IDS:
        return _LOCAL_IDS[0]
    names = set()
    for k in ("USER", "LOGNAME", "USERNAME"):
        if os.environ.get(k):
            names.add(os.environ[k])
    try:
        names.add(getpass.getuser())
    except Exception:  # noqa: BLE001
        pass
    try:
        h = socket.gethostname()
        if h:
            names.add(h)
            names.add(h.split(".")[0])
    except Exception:  # noqa: BLE001
        pass
    ids = [n for n in names if len(n) >= 4 and n.lower() not in _GENERIC_NAMES]
    _LOCAL_IDS.append(ids)
    return ids


def _ident_regex(ident: str):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(ident) + r"(?![A-Za-z0-9])", re.I)


def identifier_scan(text: str) -> list:
    """Names of the identifier classes present (never the matches)."""
    hits = []
    if not isinstance(text, str) or not text:
        return hits
    for name, pat in _ID_PATTERNS:
        if pat.search(text):
            hits.append(name)
    for ident in _local_identifiers():
        if _ident_regex(ident).search(text):
            hits.append("local_identifier")
            break
    return hits


def redact_identifiers(text: str) -> str:
    if not isinstance(text, str):
        return text
    for _name, pat in _ID_PATTERNS:
        text = pat.sub("<REDACTED>", text)
    for ident in _local_identifiers():
        text = _ident_regex(ident).sub("<REDACTED>", text)
    return text


def safe_text(text) -> str:
    """What may leave the process: secrets masked, aliases applied,
    identifiers redacted."""
    if not isinstance(text, str):
        text = str(text)
    return redact_identifiers(mask_secrets(text))


def safe_obj(obj):
    if isinstance(obj, str):
        return safe_text(obj)
    if isinstance(obj, dict):
        return {k: safe_obj(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_obj(v) for v in obj]
    return obj


_SECRET_ENV = re.compile(r"(API_KEY|_KEY$|^KEY_|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)", re.I)


def take_key(env=None):
    """Pop ASTRA_API_KEY out of the environment (so no subprocess inherits
    it), register it as a secret and return it (or None)."""
    src = os.environ if env is None else env
    key = src.pop("ASTRA_API_KEY", None)
    if key:
        key = key.strip()
        register_secret(key)
    for k in list(src.keys()):          # any other key-like variable: masked, dropped
        if k.endswith("_API_KEY"):
            register_secret(src.pop(k))
    return key or None


def load_hosts_env(repo: str) -> int:
    """Register the VALUES of gpu/hosts.env as secrets (never returned, never
    printed): a hostname in any argument is refused and one in any output is
    masked. Returns the number of values loaded."""
    p = os.path.join(repo, "gpu", "hosts.env")
    n = 0
    if not os.path.isfile(p):
        return 0
    try:
        with open(p, errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if not val:
                    continue
                register_secret(val, 4)
                host = val.split("@", 1)[-1]
                register_secret(host, 4)
                register_secret(host.split(".")[0], 4)
                if "@" in val:
                    register_secret(val.split("@", 1)[0], 4)
                n += 1
    except OSError:
        return 0
    return n


# ---------------------------------------------------------------------------
# the policy: a hard allow-list whose deny rules override everything
# ---------------------------------------------------------------------------
_OP_CHARS = set("();<>|&")


def _is_op(tok: str) -> bool:
    return bool(tok) and all(c in _OP_CHARS for c in tok)


def _punct_tokens(s: str) -> list:
    """shlex tokens with shell operators split out (quoted strings intact)."""
    lx = shlex.shlex(s, posix=True, punctuation_chars=True)
    lx.whitespace_split = True
    return list(lx)


def _prefix_match(tokens: list, words: list) -> bool:
    """Token-aware prefix: every word must equal its token, except that a
    last word ending in '/' or '.' is a prefix of its token."""
    if not words or len(tokens) < len(words):
        return False
    for i, w in enumerate(words):
        t = tokens[i]
        if i == len(words) - 1 and (w.endswith("/") or w.endswith(".")):
            if not t.startswith(w):
                return False
        elif t != w:
            return False
    return True


def _inside(path: str, root: str) -> bool:
    root = root.rstrip(os.sep) or os.sep
    return path == root or path.startswith(root + os.sep)


@functools.lru_cache(maxsize=1024)
def _word_rx(words: str):
    """Whole-word, case-insensitive regex for a deny token or phrase; between
    the words of a phrase ANY run of whitespace matches, so 'git  commit'
    and 'git\\tcommit' are 'git commit'."""
    return re.compile(r"(?<![A-Za-z0-9_])" + r"\s+".join(re.escape(w) for w in words.split())
                      + r"(?![A-Za-z0-9_])", re.I)


class Policy:
    """Decisions for run / read / write. Every decision is a dict with
    `allowed` (bool), `reason` (str, always filled) and kind-specific fields;
    it never raises for a model-supplied argument."""

    def __init__(self, data: dict, repo: str):
        self.d = data
        self.repo = os.path.abspath(repo)
        self.repo_real = os.path.realpath(self.repo)
        venv = os.environ.get("ASTRA_VENV312") or data.get("venv312") or ""
        self.venv = os.path.abspath(os.path.expanduser(venv)) if venv else ""
        if self.venv:
            register_alias(self.venv, VENV_PLACEHOLDER)
        self.run_dir_rel = None        # set by the agent once the run dir exists
        self.version = str(data.get("version") or "unversioned")

    @classmethod
    def load(cls, path: str, repo: str) -> "Policy":
        with open(path) as f:
            return cls(json.load(f), repo)

    # -- accessors --------------------------------------------------------
    def get(self, key, default=None):
        return self.d.get(key, default)

    @property
    def run_timeout_s(self) -> int:
        return int(self.d.get("run_timeout_s") or 900)

    @property
    def run_timeout_max_s(self) -> int:
        return int(self.d.get("run_timeout_max_s") or 1800)

    @property
    def tool_result_chars(self) -> int:
        return int(self.d.get("tool_result_chars") or 12000)

    @property
    def python_guard(self) -> bool:
        return bool(self.d.get("python_guard", True))

    def expand(self, s: str) -> str:
        return s.replace(VENV_PLACEHOLDER, self.venv) if self.venv else s

    def unexpand(self, s: str) -> str:
        return s.replace(self.venv, VENV_PLACEHOLDER) if self.venv else s

    def set_run_dir(self, run_dir: str) -> None:
        real = os.path.realpath(run_dir)
        self.run_dir_rel = (os.path.relpath(real, self.repo_real).replace(os.sep, "/")
                            if _inside(real, self.repo_real) else None)

    def local_prefixes_public(self) -> list:
        return list(self.d.get("local_allow_prefixes") or [])

    def guard_write_roots(self) -> list:
        roots = [os.path.realpath(os.path.join(self.repo, r))
                 for r in self.d.get("write_allow_roots") or []]
        roots += [tempfile.gettempdir(), os.path.realpath(tempfile.gettempdir()),
                  "/tmp", "/private/tmp", "/var/folders"]
        if os.environ.get("TMPDIR"):
            roots.append(os.path.realpath(os.environ["TMPDIR"]))
        return sorted(set(r.rstrip(os.sep) for r in roots if r))

    def guard_deny_roots(self) -> list:
        """The repository itself (the sandbox roots inside it win by being
        more specific) and the harness-owned run transcripts."""
        roots = [self.repo, self.repo_real]
        roots += [os.path.realpath(os.path.join(self.repo, r))
                  for r in self.d.get("write_deny_roots") or []]
        return sorted(set(r.rstrip(os.sep) for r in roots if r))

    # -- deny scan (overrides everything) ---------------------------------
    def deny_reason(self, text: str):
        """Called on the raw command text and again on its tokenized form
        (decide_run / _decide_node), so neither quoting nor whitespace can
        split a denied token or phrase."""
        for tok in self.d.get("deny_tokens") or []:
            if _word_rx(tok).search(text):
                return f"deny-listed token '{tok}'"
        for ph in self.d.get("deny_phrases") or []:
            if _word_rx(ph).search(text):
                return f"deny-listed phrase '{ph}'"
        for py in self.d.get("deny_python_tokens") or []:
            if py in text:
                return f"deny-listed call/module '{py}'"
        for rx in self.d.get("deny_regex") or []:
            try:
                if re.search(rx, text):
                    return f"deny-listed pattern /{rx}/"
            except re.error:
                continue
        for pr in self.d.get("deny_secret_probes") or []:
            if pr in text:
                return f"secret probe '{pr}'"
        if mask_secrets(text) != text:
            return "the command contains a secret or an internal hostname"
        ids = identifier_scan(text)
        if ids:
            return ("internal identifier in the command (" + ",".join(ids) +
                    "): hostnames, IPs, URLs, e-mails and home paths are never "
                    "accepted; the ssh wrappers resolve hosts themselves and "
                    "repository paths are relative")
        return None

    # -- paths --------------------------------------------------------------
    def _rel_deny_reason(self, rel: str):
        rel = rel.replace(os.sep, "/").strip("/")
        parts = [p for p in rel.split("/") if p]
        if ".git" in parts:
            return "the .git directory is not readable"
        if parts and parts[-1] in (self.d.get("read_deny_basenames") or []):
            return f"'{parts[-1]}' files are never readable (internal hosts)"
        for p in self.d.get("read_deny_paths") or []:
            p = p.strip("/")
            if rel == p or rel.startswith(p + "/"):
                return f"'{p}' is never readable"
        runs = (self.d.get("runs_dir") or "research_notes/astra_agent/runs").strip("/")
        if rel == runs or rel.startswith(runs + "/"):
            cur = self.run_dir_rel
            if not cur or not (rel == cur or rel.startswith(cur + "/")):
                if rel != runs:
                    return "transcripts of other runs are not readable"
        return None

    def _to_rel(self, path: str):
        """(rel, reason): normalise a model-supplied path to a repo-relative
        one or explain why it cannot be."""
        if not isinstance(path, str) or not path.strip():
            return None, "empty path"
        p = path.strip()
        if "\n" in p or "\0" in p:
            return None, "invalid characters in path"
        if p.startswith("~"):
            return None, "home directory paths are not allowed; use repository-relative paths"
        parts = p.replace("\\", "/").split("/")
        if ".." in parts:
            return None, "path traversal ('..') is refused"
        if os.path.isabs(p):
            ap = os.path.abspath(p)
            if _inside(ap, self.repo):
                rel = os.path.relpath(ap, self.repo)
            elif _inside(os.path.realpath(ap), self.repo_real):
                rel = os.path.relpath(os.path.realpath(ap), self.repo_real)
            else:
                return None, "absolute path outside the repository"
        else:
            rel = os.path.normpath(p)
        rel = rel.replace(os.sep, "/")
        if rel.startswith("../") or rel == "..":
            return None, "path traversal ('..') is refused"
        return ("" if rel == "." else rel), None

    def decide_read(self, path: str) -> dict:
        rel, why = self._to_rel(path)
        if why:
            return dict(allowed=False, reason=why, path=None, rel=None)
        r = self._rel_deny_reason(rel)
        if r:
            return dict(allowed=False, reason=r, path=None, rel=rel)
        ab = os.path.join(self.repo, rel) if rel else self.repo
        real = os.path.realpath(ab)
        if not _inside(real, self.repo_real):
            return dict(allowed=False, reason="the path resolves (through a symlink) "
                        "outside the repository", path=None, rel=rel)
        rel_real = os.path.relpath(real, self.repo_real).replace(os.sep, "/")
        if rel_real != ".":
            r = self._rel_deny_reason(rel_real)
            if r:
                return dict(allowed=False, reason=r + " (symlink alias)", path=None, rel=rel)
        return dict(allowed=True, reason="inside the repository", path=real,
                    rel=rel or ".")

    def decide_write(self, path: str) -> dict:
        rel, why = self._to_rel(path)
        if why:
            return dict(allowed=False, reason=why, path=None, rel=None)
        if not rel:
            return dict(allowed=False, reason="a file path is required", path=None, rel=rel)
        roots = [r.strip("/") for r in self.d.get("write_allow_roots") or []]
        deny = [r.strip("/") for r in self.d.get("write_deny_roots") or []]
        root = next((r for r in roots if rel.startswith(r + "/")), None)
        if root is None:
            return dict(allowed=False, reason="writes are allowed only under " +
                        ", ".join(r + "/" for r in roots), path=None, rel=rel)
        for dr in deny:
            if rel == dr or rel.startswith(dr + "/"):
                return dict(allowed=False, reason=f"'{dr}/' is owned by the harness "
                            "(run transcripts) and not writable", path=None, rel=rel)
        # no symlink anywhere in the path (existing components), no escape
        cur = self.repo
        for part in rel.split("/"):
            cur = os.path.join(cur, part)
            if os.path.islink(cur):
                return dict(allowed=False, reason="symlinks are refused in write paths",
                            path=None, rel=rel)
        real_parent = os.path.realpath(os.path.dirname(os.path.join(self.repo, rel)))
        root_real = os.path.realpath(os.path.join(self.repo, root))
        if not _inside(real_parent, root_real):
            return dict(allowed=False, reason="the path resolves outside the write sandbox",
                        path=None, rel=rel)
        return dict(allowed=True, reason=f"inside the write sandbox {root}/",
                    path=os.path.join(self.repo, rel), rel=rel)

    def _local_path_reason(self, tok: str):
        """None if the token is not path-like or is an acceptable path."""
        cand = tok
        if tok.startswith("-") and "=" in tok:
            cand = tok.split("=", 1)[1]
        elif tok.startswith("-"):
            return None
        pathlike = ("/" in cand or cand.startswith(".") or cand.startswith("~")
                    or os.path.exists(os.path.join(self.repo, cand)))
        if not pathlike or not cand:
            return None
        if cand.startswith("~"):
            return "home directory paths are not allowed locally"
        if ".." in cand.replace("\\", "/").split("/"):
            return f"path traversal ('..') in '{tok}'"
        ab = cand if os.path.isabs(cand) else os.path.join(self.repo, cand)
        real = os.path.realpath(ab)
        if real == "/dev/null":
            return None
        if _inside(real, self.repo_real):
            rel = os.path.relpath(real, self.repo_real)
            if rel != ".":
                r = self._rel_deny_reason(rel)
                if r:
                    return f"'{tok}': {r}"
            return None
        if self.venv and _inside(real, os.path.realpath(self.venv)):
            return None
        for root in self.d.get("local_extra_path_roots") or []:
            if _inside(real, os.path.realpath(root)) or _inside(real, root):
                return None
        return f"path outside the repository: '{tok}'"

    def _option_deny_reason(self, argv: list):
        """Per-program option deny (policy local_option_deny), checked on
        every option token of a local command once its prefix matched. The
        case that motivates it: `git diff --output=<file>` / `git log
        --output <file>` make git itself create, overwrite or truncate ANY
        file (in a live probe `git diff --output=module.py` destroyed the
        module's contents): neither the '>' guard nor the python guard sees
        a native binary writing, so the option is refused outright."""
        prog = os.path.basename(argv[0]) if argv else ""
        rules = (self.d.get("local_option_deny") or {}).get(prog) or []
        for t in argv[1:]:
            if not t.startswith("-"):
                continue
            for rx in rules:
                try:
                    if re.match(rx, t):
                        return (f"option '{t.split('=', 1)[0]}' of {prog} is refused by the policy: "
                                f"{prog} is inspection-only here (an option that writes a file, "
                                "reads an arbitrary file or runs a helper is never accepted)")
                except re.error:
                    continue
        return None

    # -- run ----------------------------------------------------------------
    def decide_run(self, cmd) -> dict:
        """`display` in every returned decision is the command with the venv
        path folded back to <venv312> and secrets / hostnames masked, so a
        decision can be logged or shown as is; `argv` is what would run."""
        deny = dict(allowed=False, kind="denied", argv=None, redirect=None, node=None,
                    display=mask_secrets(self.unexpand(cmd)) if isinstance(cmd, str) else str(cmd))
        if not isinstance(cmd, str) or not cmd.strip():
            return dict(deny, reason="empty command")
        raw = cmd.strip()
        if "\n" in raw or "\r" in raw:
            return dict(deny, reason="newlines are not allowed: one command per run")
        display_raw = self.unexpand(raw)
        display = mask_secrets(display_raw)
        deny["display"] = display
        r = self.deny_reason(display_raw)
        if r:
            return dict(deny, reason=r)
        expanded = self.expand(display_raw)
        try:
            argv = shlex.split(expanded, posix=True)
        except ValueError as e:
            return dict(deny, reason=f"cannot tokenize the command: {e}")
        if not argv:
            return dict(deny, reason="empty command")
        # the deny scan again on the tokenized form (venv folded back to its
        # placeholder): quotes cannot split a token — 'r''m' is rm to the shell
        r = self.deny_reason(" ".join(self.unexpand(t) for t in argv))
        if r:
            return dict(deny, reason=r)
        # node commands: exactly  bash gpu/<wrapper> '<remote>'
        wrappers = self.d.get("node_wrappers") or {}
        if argv[0] == "bash":
            if len(argv) < 2 or argv[1] not in wrappers:
                return dict(deny, reason="bash may only invoke the node wrappers " +
                            " / ".join(sorted(wrappers)))
            if len(argv) != 3:
                return dict(deny, reason="node commands are exactly  bash "
                            f"{argv[1]} '<remote>'  — quote the remote command as ONE argument")
            return self._decide_node(argv[2], wrappers[argv[1]], argv[1], display)
        # local: no shell, so operators are refused rather than interpreted
        for t in argv:
            if t in (";", "|", "&", "&&", "||", "(", ")", "<", "<<", "|&") or t.startswith("<"):
                return dict(deny, reason=f"shell operator {t!r} is not available: one command "
                            "per run, no pipes, no chaining")
            if "$(" in t or "`" in t:
                return dict(deny, reason="command substitution is not allowed")
        if argv[0] == "nohup":
            return dict(deny, reason="nohup is allowed only on a node, directly before an "
                        "allow-listed smoke script")
        # redirections: only into the write sandbox (or /dev/null)
        redirect = dict(stdout=None, stderr=None, append=False)
        clean = []
        i = 0
        rx = re.compile(r"^(?P<fd>\d?)(?P<op>>>|>&|>|&>)(?P<target>.*)$")
        while i < len(argv):
            t = argv[i]
            m = rx.match(t) if i > 0 else None
            if not m:
                clean.append(t)
                i += 1
                continue
            fd, op, target = m.group("fd"), m.group("op"), m.group("target")
            if op == ">&":
                if not ((fd, target) in (("2", "1"), ("1", "2"), ("", "2"))):
                    return dict(deny, reason=f"unsupported redirection {t!r} (only 2>&1)")
                redirect["stderr"] = "stdout"
                i += 1
                continue
            if not target:
                if i + 1 >= len(argv):
                    return dict(deny, reason="redirection without a target")
                target = argv[i + 1]
                i += 1
            i += 1
            if target != "/dev/null":
                w = self.decide_write(target)
                if not w["allowed"]:
                    return dict(deny, reason=f"'>' redirection outside the write sandbox: "
                                f"{w['reason']}")
                target = w["path"]
            redirect["append"] = redirect["append"] or op == ">>"
            if op == "&>":
                redirect["stdout"] = redirect["stderr"] = target
            elif fd == "2":
                redirect["stderr"] = target
            else:
                redirect["stdout"] = target
        argv = clean
        if not argv:
            return dict(deny, reason="empty command")
        prefixes = self.d.get("local_allow_prefixes") or []
        hit = None
        for p in prefixes:
            if _prefix_match(argv, self.expand(p).split()):
                hit = p
                break
        if hit is None:
            return dict(deny, reason="not on the local allow-list; local commands must start "
                        "with one of: " + " | ".join(prefixes))
        # per-program option deny: git may never write a file (--output ...)
        r = self._option_deny_reason(argv)
        if r:
            return dict(deny, reason=r)
        # every path-like argument stays inside the repository (globs expanded)
        final = [argv[0]]
        for t in argv[1:]:
            toks = [t]
            if any(c in t for c in "*?[") and not t.startswith("-"):
                hits = sorted(glob.glob(os.path.join(self.repo, t)))
                if hits:
                    toks = [os.path.relpath(h, self.repo) for h in hits]
            for tk in toks:
                r = self._local_path_reason(tk)
                if r:
                    return dict(deny, reason=r)
                final.append(tk)
        return dict(allowed=True, kind="local", reason=f"allow-listed prefix '{hit}'",
                    argv=final, redirect=redirect, node=None, display=display, prefix=hit)

    def _decide_node(self, remote: str, node: str, wrapper: str, display: str) -> dict:
        deny = dict(allowed=False, kind="denied", argv=None, redirect=None, node=node,
                    display=display)
        if not remote.strip():
            return dict(deny, reason="empty remote command")
        r = self.deny_reason(remote)
        if r:
            return dict(deny, reason=r)
        try:
            toks = _punct_tokens(remote)
        except ValueError as e:
            return dict(deny, reason=f"cannot tokenize the remote command: {e}")
        if not toks:
            return dict(deny, reason="empty remote command")
        # the deny scan again on the tokenized remote: "import sub""process" is
        # import subprocess to python3 -c, r""m is rm to the remote shell
        r = self.deny_reason(" ".join(toks))
        if r:
            return dict(deny, reason=r)
        prefixes = [p.split() for p in self.d.get("node_remote_prefixes") or []]
        smoke_after = [p.split() for p in self.d.get("nohup_allowed_after") or []]
        smoke_scripts = set(self.d.get("node_smoke_scripts") or [])
        filters = set(self.d.get("node_pipe_filters") or [])
        redirects = self.d.get("node_redirect_prefixes") or []
        env_rx = re.compile(self.d.get("node_env_allow_regex") or r"^$")
        env_assign = False
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            name = toks[0].split("=", 1)[0]
            if not env_rx.match(name):
                return dict(deny, reason=f"environment assignment '{name}=' is not allowed on "
                            "the node")
            toks.pop(0)
            env_assign = True
        nohup = False
        if toks and toks[0] == "nohup":
            toks.pop(0)
            nohup = True
            if not any(_prefix_match(toks, w) for w in smoke_after):
                return dict(deny, reason="nohup is allowed only directly before an allow-listed "
                            "smoke script: " + " | ".join(" ".join(w) for w in smoke_after))
        if env_assign and not any(_prefix_match(toks, w) for w in smoke_after):
            return dict(deny, reason="environment assignments are allowed only before an "
                        "allow-listed smoke script")
        segments = [[]]
        i = 0
        while i < len(toks):
            t = toks[i]
            if t == "|":
                if not segments[-1]:
                    return dict(deny, reason="empty pipe segment")
                segments.append([])
                i += 1
                continue
            if t in (">", ">>"):
                target = toks[i + 1] if i + 1 < len(toks) else None
                if target is None or _is_op(target):
                    return dict(deny, reason="redirection without a target")
                if ".." in target.split("/") or not any(target.startswith(p) for p in redirects):
                    return dict(deny, reason=f"redirection target '{target}' is outside the "
                                "allowed node output locations " + ", ".join(redirects))
                i += 2
                continue
            if t == ">&":
                prev = toks[i - 1] if i > 0 else ""
                nxt = toks[i + 1] if i + 1 < len(toks) else ""
                if (prev, nxt) not in (("2", "1"), ("1", "2")):
                    return dict(deny, reason="'>&' is allowed only as 2>&1")
                if segments[-1] and segments[-1][-1] == prev:
                    segments[-1].pop()
                i += 2
                continue
            if t == "&":
                if nohup and i == len(toks) - 1:
                    i += 1
                    continue
                return dict(deny, reason="'&' is allowed only at the end of a nohup smoke launch")
            if _is_op(t):
                return dict(deny, reason=f"shell operator {t!r} is not allowed on the node "
                            "(no ; && || ( ) < )")
            segments[-1].append(t)
            i += 1
        if not segments[0]:
            return dict(deny, reason="empty remote command")
        # THE GPU RULE first, so that a wrong GPU is named as such
        gpus = list((self.d.get("node_smoke_gpus") or {}).get(node) or [])
        for seg in segments:
            for j, t in enumerate(seg):
                if t in smoke_scripts:
                    if not gpus:
                        return dict(deny, reason=f"smoke scripts are disabled on node '{node}' "
                                    "by the policy (no free GPU there)")
                    g = seg[j + 1] if j + 1 < len(seg) else None
                    if g not in gpus:
                        return dict(deny, reason=f"the GPU argument of {t} must be "
                                    f"{'/'.join(gpus)} on node '{node}' (got {g!r})")
        if not any(_prefix_match(segments[0], w) for w in prefixes):
            return dict(deny, reason="the remote command must start with one of: " +
                        " | ".join(" ".join(w) for w in prefixes))
        for seg in segments[1:]:
            if not seg:
                return dict(deny, reason="empty pipe segment")
            if seg[0] not in filters and not any(_prefix_match(seg, w) for w in prefixes):
                return dict(deny, reason=f"pipe segment '{seg[0]}' is not an allowed filter "
                            "(" + ", ".join(sorted(filters)) + ")")
        return dict(allowed=True, kind="node", reason=f"node '{node}' via {wrapper}; remote "
                    "matches the allow-list", argv=["bash", wrapper, remote],
                    redirect=None, node=node, display=display, prefix=wrapper)


# ---------------------------------------------------------------------------
# local python guard (sitecustomize through PYTHONPATH) and process execution
# ---------------------------------------------------------------------------
GUARD_SOURCE = r'''
# astra sandbox guard — written by tools/astra_agent.py and imported as sitecustomize through
# PYTHONPATH for every local python run of the Astra agent. Refuses file mutation outside the
# allowed roots, os.system/os.popen, deny-listed subprocess argv and os.kill of non-child pids.
# An accident guard for autonomous runs, not a security boundary.
import os as _os


def _install():
    roots = [r.rstrip("/") for r in _os.environ.get("ASTRA_GUARD_WRITE_ROOTS", "").split(_os.pathsep) if r]
    if not roots:
        return
    deny_roots = [r.rstrip("/") for r in _os.environ.get("ASTRA_GUARD_DENY_ROOTS", "").split(_os.pathsep) if r]
    import builtins, io, json, re, shutil, subprocess
    try:
        deny = json.loads(_os.environ.get("ASTRA_GUARD_DENY_JSON") or "{}")
    except ValueError:
        deny = {}
    tokens = list(deny.get("tokens") or [])
    phrases = list(deny.get("phrases") or [])

    def _inside(p, root):
        return p == root or p.startswith(root + "/")

    def _fd_path(fd):
        """Directory behind a dir_fd (macOS F_GETPATH, Linux /proc); None if unknown."""
        try:
            import fcntl
            if hasattr(fcntl, "F_GETPATH"):
                raw = fcntl.fcntl(fd, fcntl.F_GETPATH, b"\0" * 1024)
                return _os.fsdecode(raw.split(b"\0", 1)[0])
        except Exception:
            pass
        try:
            return _os.readlink("/proc/self/fd/%d" % int(fd))
        except Exception:
            return None

    def _ok(path, dir_fd=None):
        if path is None or isinstance(path, int):
            return True
        try:
            p = _os.fsdecode(path)
        except Exception:
            return True
        if dir_fd is not None and not _os.path.isabs(p):
            base = _fd_path(dir_fd)
            if base is None:
                return False
            p = _os.path.join(base, p)
        p = _os.path.realpath(_os.path.abspath(p))
        if p.startswith("/dev/"):
            return True
        # the most specific matching root decides (a deny root wins a tie): the
        # repository is denied, the sandbox roots inside it are allowed, the run
        # transcripts inside research_notes/astra_agent are denied again
        best, allow = -1, False
        for r in roots:
            if _inside(p, r) and len(r) > best:
                best, allow = len(r), True
        for r in deny_roots:
            if _inside(p, r) and len(r) >= best:
                best, allow = len(r), False
        return allow

    def _refuse(what, path):
        raise PermissionError("astra sandbox guard: %s refused outside the write sandbox: %s"
                              % (what, _os.fsdecode(path) if isinstance(path, (str, bytes)) else path))

    _open = builtins.open

    def open(file, *a, **k):
        mode = a[0] if a else k.get("mode", "r")
        if isinstance(mode, str) and any(c in mode for c in "wax+") and not _ok(file):
            _refuse("open(mode=%r)" % mode, file)
        return _open(file, *a, **k)
    builtins.open = open
    io.open = open

    _os_open = _os.open
    WR = _os.O_WRONLY | _os.O_RDWR | _os.O_CREAT | _os.O_TRUNC | _os.O_APPEND

    def os_open(path, flags, *a, **k):
        if flags & WR and not _ok(path, k.get("dir_fd")):
            _refuse("os.open(write flags)", path)
        return _os_open(path, flags, *a, **k)
    _os.open = os_open

    def _wrap1(name):
        orig = getattr(_os, name, None)
        if orig is None:
            return

        def w(path, *a, **k):
            if not _ok(path, k.get("dir_fd")):
                _refuse("os." + name, path)
            return orig(path, *a, **k)
        w.__name__ = name
        setattr(_os, name, w)
    for _n in ("remove", "unlink", "rmdir", "removedirs", "truncate", "chmod", "chown", "mkdir"):
        _wrap1(_n)

    def _wrap2(name, check_src):
        orig = getattr(_os, name, None)
        if orig is None:
            return

        def w(src, dst, *a, **k):
            if check_src and not _ok(src, k.get("src_dir_fd")):
                _refuse("os." + name, src)
            if not _ok(dst, k.get("dst_dir_fd", k.get("dir_fd"))):
                _refuse("os." + name, dst)
            return orig(src, dst, *a, **k)
        w.__name__ = name
        setattr(_os, name, w)
    _wrap2("rename", True)
    _wrap2("replace", True)
    _wrap2("link", False)
    _wrap2("symlink", False)

    _rmtree = shutil.rmtree

    def rmtree(path, *a, **k):
        if not _ok(path):
            _refuse("shutil.rmtree", path)
        return _rmtree(path, *a, **k)
    shutil.rmtree = rmtree
    _move = shutil.move

    def move(src, dst, *a, **k):
        if not _ok(src) or not _ok(dst):
            _refuse("shutil.move", dst if _ok(src) else src)
        return _move(src, dst, *a, **k)
    shutil.move = move
    for _n in ("copyfile", "copy", "copy2", "copytree"):
        _orig = getattr(shutil, _n)

        def _mk(orig, name):
            def w(src, dst, *a, **k):
                if not _ok(dst):
                    _refuse("shutil." + name, dst)
                return orig(src, dst, *a, **k)
            w.__name__ = name
            return w
        setattr(shutil, _n, _mk(_orig, _n))

    def _flat(args):
        out = []
        for x in args:
            if isinstance(x, (list, tuple)):
                out.extend(_flat(x))
            elif isinstance(x, (str, bytes)):
                out.append(_os.fsdecode(x))
            else:
                try:
                    out.append(_os.fsdecode(_os.fspath(x)))
                except Exception:
                    pass
        return out

    def _deny_hit(text):
        for t in tokens:
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", text, re.I):
                return t
        for p in phrases:   # any run of whitespace between the words of a phrase
            rx = r"(?<![A-Za-z0-9_])" + r"\s+".join(re.escape(w) for w in p.split()) + r"(?![A-Za-z0-9_])"
            if re.search(rx, text, re.I):
                return p
        return None

    children = set()
    _popen_init = subprocess.Popen.__init__

    def popen_init(self, args, *a, **k):
        text = _os.fsdecode(args) if isinstance(args, (str, bytes)) else " ".join(_flat([args]))
        hit = _deny_hit(text)
        if hit:
            raise PermissionError("astra sandbox guard: subprocess with deny-listed '%s' refused" % hit)
        _popen_init(self, args, *a, **k)
        try:
            children.add(self.pid)
        except Exception:
            pass
    subprocess.Popen.__init__ = popen_init

    def _refuse_call(name):
        def w(*a, **k):
            raise PermissionError("astra sandbox guard: %s is refused; use subprocess with an argv list" % name)
        w.__name__ = name
        return w
    _os.system = _refuse_call("os.system")
    _os.popen = _refuse_call("os.popen")

    def _wrap_spawn(name):
        orig = getattr(_os, name, None)
        if orig is None:
            return

        def w(*a, **k):
            hit = _deny_hit(" ".join(_flat(a)))
            if hit:
                raise PermissionError("astra sandbox guard: %s with deny-listed '%s' refused" % (name, hit))
            return orig(*a, **k)
        w.__name__ = name
        setattr(_os, name, w)
    for _n in ("execv", "execve", "execvp", "execvpe", "execl", "execle", "execlp", "execlpe",
               "posix_spawn", "posix_spawnp", "spawnv", "spawnve", "spawnvp", "spawnvpe",
               "spawnl", "spawnle", "spawnlp", "spawnlpe"):
        _wrap_spawn(_n)

    _kill = _os.kill

    def kill(pid, sig, *a, **k):
        if pid not in children and pid not in (0, _os.getpid()):
            raise PermissionError("astra sandbox guard: os.kill of a pid that is not a child of this process is refused")
        return _kill(pid, sig, *a, **k)
    _os.kill = kill
    if hasattr(_os, "killpg"):
        _killpg = _os.killpg

        def killpg(pgid, sig, *a, **k):
            if pgid not in children and pgid != _os.getpgrp():
                raise PermissionError("astra sandbox guard: os.killpg of a foreign process group is refused")
            return _killpg(pgid, sig, *a, **k)
        _os.killpg = killpg


try:
    _install()
except Exception as _e:  # never break the guarded program
    import sys as _sys
    _sys.stderr.write("astra sandbox guard: not installed (%s)\n" % type(_e).__name__)
'''

_GUARD_DIR: list = []


def ensure_guard_dir() -> str:
    """Materialise the guard as sitecustomize.py in a private temp dir
    (once per process) and return the dir."""
    if _GUARD_DIR:
        return _GUARD_DIR[0]
    d = tempfile.mkdtemp(prefix="astra_guard_")
    with open(os.path.join(d, "sitecustomize.py"), "w") as f:
        f.write(GUARD_SOURCE)
    _GUARD_DIR.append(d)
    return d


def clean_env(policy: Policy, guard: bool = True) -> dict:
    """The environment a tool subprocess gets: no key-like variables, no
    pager, the repo on PYTHONPATH and (for local python) the guard."""
    env = {k: v for k, v in os.environ.items() if not _SECRET_ENV.search(k)}
    env.pop("ASTRA_API_KEY", None)
    env["GIT_PAGER"] = "cat"
    env["PAGER"] = "cat"
    env["PYTHONUNBUFFERED"] = "1"
    paths = [policy.repo]
    if guard and policy.python_guard:
        paths.insert(0, ensure_guard_dir())
        env["ASTRA_GUARD_WRITE_ROOTS"] = os.pathsep.join(policy.guard_write_roots())
        env["ASTRA_GUARD_DENY_ROOTS"] = os.pathsep.join(policy.guard_deny_roots())
        env["ASTRA_GUARD_DENY_JSON"] = json.dumps(dict(
            tokens=policy.get("deny_tokens") or [], phrases=policy.get("deny_phrases") or []))
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _decode(b) -> str:
    if b is None:
        return ""
    if isinstance(b, bytes):
        return b.decode("utf-8", "replace")
    return str(b)


def run_argv(argv: list, cwd: str, env: dict, timeout_s: float, redirect=None) -> dict:
    """Run argv without a shell in its own session; kill the whole process
    group at the timeout; capture (or redirect into the sandbox) the output."""
    redirect = redirect or {}
    t0 = time.monotonic()
    handles = []
    stdout = stderr = subprocess.PIPE
    mode = "ab" if redirect.get("append") else "wb"
    try:
        if redirect.get("stdout"):
            fh = open(redirect["stdout"], mode)
            handles.append(fh)
            stdout = fh
        if redirect.get("stderr") == "stdout":
            stderr = subprocess.STDOUT
        elif redirect.get("stderr"):
            if redirect.get("stderr") == redirect.get("stdout"):
                stderr = stdout
            else:
                fh = open(redirect["stderr"], mode)
                handles.append(fh)
                stderr = fh
        try:
            p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, start_new_session=True)
        except (FileNotFoundError, PermissionError, OSError) as e:
            return dict(rc=127, timed_out=False, elapsed_s=0.0, stdout="",
                        stderr=f"cannot start {argv[0]!r}: {type(e).__name__}: {e}")
        timed_out = False
        try:
            out, err = p.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:  # noqa: BLE001
                p.kill()
            try:
                out, err = p.communicate(timeout=10)
            except Exception:  # noqa: BLE001
                out, err = b"", b""
        res = dict(rc=p.returncode, timed_out=timed_out,
                   elapsed_s=round(time.monotonic() - t0, 1),
                   stdout=_decode(out), stderr=_decode(err))
        for key in ("stdout", "stderr"):
            path = redirect.get(key)
            if path and path != "stdout":
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                res[key] = (f"({key} redirected to file, {size} bytes)\n" +
                            _tail_of_file(path, 3000))
        return res
    finally:
        for fh in handles:
            try:
                fh.close()
            except Exception:  # noqa: BLE001
                pass


def _tail_of_file(path: str, n: int) -> str:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - n))
            return f.read().decode("utf-8", "replace")
    except OSError:
        return ""


def truncate(text: str, cap: int) -> str:
    """Head + tail truncation to `cap` characters with an explicit marker."""
    if len(text) <= cap:
        return text
    head = max(0, cap * 2 // 3)
    tail = max(0, cap - head - 60)
    omitted = len(text) - head - tail
    return (text[:head] + f"\n... [{omitted} chars truncated by the harness] ...\n" +
            (text[-tail:] if tail else ""))


# ---------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------
class Tools:
    """The five tools. Every call returns bounded, redacted text and never
    raises for a model-supplied argument; policy refusals begin with
    'POLICY REFUSED'. The ground truth of what happened (files written,
    commands run, refusals) is recorded for the report."""

    def __init__(self, policy: Policy, result_chars=None, run_timeout_s=None,
                 log=None, runner=None):
        self.policy = policy
        self.repo = policy.repo
        self.result_chars = int(result_chars or policy.tool_result_chars)
        self.run_timeout_s = int(run_timeout_s or policy.run_timeout_s)
        self.log = log or (lambda kind, **kw: None)
        self.runner = runner or run_argv
        self.files_written: list = []
        self.commands: list = []
        self.refusals: list = []

    # -- dispatch -----------------------------------------------------------
    def call(self, name, args) -> str:
        args = dict(args) if isinstance(args, dict) else {}
        if name not in TOOL_NAMES:
            out = f"ERROR: unknown tool {name!r}; tools: {', '.join(TOOL_NAMES)}"
        else:
            try:
                out = getattr(self, name)(**args)
            except TypeError as e:
                out = f"ERROR: bad arguments for {name}: {safe_text(str(e))}"
            except Exception as e:  # noqa: BLE001
                out = f"ERROR: {name} failed: {type(e).__name__}: {safe_text(str(e))[:300]}"
        out = safe_text(out if isinstance(out, str) else json.dumps(out, indent=1))
        return truncate(out, self.result_chars)

    # -- helpers ------------------------------------------------------------
    def _refused(self, tool: str, arg: str, reason: str) -> str:
        self.refusals.append(dict(tool=tool, arg=safe_text(arg), reason=safe_text(reason)))
        self.log("policy", tool=tool, arg=arg, allowed=False, reason=reason)
        return f"POLICY REFUSED {tool}: {reason}\n(argument: {arg})"

    def _visible(self, rel: str) -> bool:
        return self.policy.decide_read(rel)["allowed"]

    # -- read_file ----------------------------------------------------------
    def read_file(self, path=None, start_line=1, max_lines=400, file=None) -> str:
        path = path if path is not None else file
        d = self.policy.decide_read(str(path) if path is not None else "")
        if not d["allowed"]:
            return self._refused("read_file", str(path), d["reason"])
        p = d["path"]
        if os.path.isdir(p):
            return f"ERROR: {d['rel']} is a directory; use list_dir"
        if not os.path.isfile(p):
            return f"ERROR: no such file: {d['rel']}"
        try:
            start = max(1, int(start_line or 1))
            n = int(max_lines or 400)
        except (TypeError, ValueError):
            return "ERROR: start_line and max_lines must be integers"
        n = max(1, min(n, 5000))
        cap = int(self.policy.get("read_max_chars") or 60000)
        with open(p, "rb") as f:
            head = f.read(4096)
        if b"\0" in head:
            return f"[{d['rel']}] binary file ({os.path.getsize(p)} bytes); not shown"
        with open(p, errors="replace") as f:
            lines = f.read().splitlines()
        total = len(lines)
        sel = lines[start - 1:start - 1 + n]
        body = "\n".join(f"{start + i:6d}\t{l}" for i, l in enumerate(sel))
        if len(body) > cap:
            body = body[:cap] + f"\n... [read_file cap {cap} chars reached]"
        end = start - 1 + len(sel)
        more = f"; {total - end} more lines" if end < total else ""
        self.log("policy", tool="read_file", arg=d["rel"], allowed=True, reason=d["reason"])
        return f"[{d['rel']}] lines {start}-{end} of {total}{more}\n{body}"

    # -- list_dir -----------------------------------------------------------
    def list_dir(self, path=".") -> str:
        d = self.policy.decide_read(str(path) if path is not None else ".")
        if not d["allowed"]:
            return self._refused("list_dir", str(path), d["reason"])
        p = d["path"]
        if not os.path.isdir(p):
            return f"ERROR: not a directory: {d['rel']}"
        rows = []
        try:
            names = sorted(os.listdir(p))
        except OSError as e:
            return f"ERROR: cannot list {d['rel']}: {type(e).__name__}"
        base = "" if d["rel"] in (".", "") else d["rel"].rstrip("/") + "/"
        for name in names:
            rel = base + name
            if name in ("__pycache__",) or not self._visible(rel):
                continue
            full = os.path.join(p, name)
            if os.path.isdir(full):
                rows.append(f"      dir  {name}/")
            else:
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = -1
                rows.append(f"{size:9d}  {name}")
            if len(rows) >= 500:
                rows.append("... (truncated at 500 entries)")
                break
        self.log("policy", tool="list_dir", arg=d["rel"], allowed=True, reason=d["reason"])
        return f"[{d['rel']}] {len(rows)} entries\n" + "\n".join(rows)

    # -- grep ---------------------------------------------------------------
    def grep(self, pattern=None, path=".", max_results=200, ignore_case=False) -> str:
        if not isinstance(pattern, str) or not pattern:
            return "ERROR: grep needs a non-empty regex 'pattern'"
        try:
            rx = re.compile(pattern, re.I if ignore_case else 0)
        except re.error as e:
            return f"ERROR: bad regex: {e}"
        d = self.policy.decide_read(str(path) if path is not None else ".")
        if not d["allowed"]:
            return self._refused("grep", str(path), d["reason"])
        try:
            cap = max(1, min(int(max_results or 200), 2000))
        except (TypeError, ValueError):
            cap = 200
        skip_dirs = set(self.policy.get("grep_skip_dirs") or [])
        max_file = int(self.policy.get("grep_max_file_bytes") or 2000000)
        max_total = int(self.policy.get("grep_max_total_bytes") or 300000000)
        budget_s = float(self.policy.get("grep_time_budget_s") or 20)
        t0 = time.monotonic()
        out, scanned, files, stopped = [], 0, 0, None
        root = d["path"]                      # a realpath: relate to repo_real
        repo_real = self.policy.repo_real
        if os.path.isfile(root):
            walker = [(os.path.dirname(root), [], [os.path.basename(root)])]
        else:
            walker = os.walk(root)
        for dirpath, dirnames, filenames in walker:
            dirnames[:] = sorted(x for x in dirnames if x not in skip_dirs
                                 and self._visible(os.path.relpath(os.path.join(dirpath, x),
                                                                   repo_real)))
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, repo_real).replace(os.sep, "/")
                if not self._visible(rel) or os.path.islink(full):
                    continue
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                if size > max_file:
                    continue
                if scanned + size > max_total:
                    stopped = "byte budget"
                    break
                if time.monotonic() - t0 > budget_s:
                    stopped = "time budget"
                    break
                try:
                    with open(full, "rb") as f:
                        data = f.read()
                except OSError:
                    continue
                scanned += size
                files += 1
                if b"\0" in data[:4096]:
                    continue
                text = data.decode("utf-8", "replace")
                for ln, line in enumerate(text.splitlines(), 1):
                    if rx.search(line):
                        out.append(f"{rel}:{ln}: {line.strip()[:240]}")
                        if len(out) >= cap:
                            stopped = f"result cap {cap}"
                            break
                if stopped:
                    break
            if stopped:
                break
        self.log("policy", tool="grep", arg=d["rel"], allowed=True, reason=d["reason"])
        head = (f"grep /{pattern}/ under {d['rel']}: {len(out)} hits in {files} files "
                f"({scanned} bytes)" + (f"; stopped: {stopped}" if stopped else ""))
        return head + "\n" + "\n".join(out)

    # -- write_file ---------------------------------------------------------
    def write_file(self, path=None, content=None, file=None) -> str:
        path = path if path is not None else file
        d = self.policy.decide_write(str(path) if path is not None else "")
        if not d["allowed"]:
            return self._refused("write_file", str(path), d["reason"])
        if not isinstance(content, str):
            return "ERROR: write_file needs 'content' as a string"
        cap = int(self.policy.get("write_max_chars") or 400000)
        if len(content) > cap:
            return f"ERROR: content is {len(content)} chars; the cap is {cap}"
        # the same outward path as every tool result / transcript line: secrets
        # and hosts.env values -> ***, internal identifiers -> <REDACTED>
        masked = safe_text(content)
        notes = []
        if mask_secrets(content) != content:
            notes.append("secrets masked")
        n_red = masked.count("<REDACTED>") - content.count("<REDACTED>")
        if n_red > 0:
            notes.append(f"{n_red} internal identifier(s) redacted to <REDACTED>")
        os.makedirs(os.path.dirname(d["path"]), exist_ok=True)
        with open(d["path"], "w") as f:
            f.write(masked)
        self.files_written.append(d["rel"])
        self.log("policy", tool="write_file", arg=d["rel"], allowed=True, reason=d["reason"],
                 chars=len(masked), redacted=n_red)
        return f"wrote {len(masked)} chars to {d['rel']}" + (f" ({'; '.join(notes)})" if notes else "")

    # -- run ----------------------------------------------------------------
    def run(self, cmd=None, timeout_s=None, command=None) -> str:
        cmd = cmd if cmd is not None else command
        d = self.policy.decide_run(cmd if isinstance(cmd, str) else str(cmd))
        if not d["allowed"]:
            return self._refused("run", d["display"], d["reason"])
        try:
            t = int(timeout_s) if timeout_s is not None else self.run_timeout_s
        except (TypeError, ValueError):
            t = self.run_timeout_s
        t = max(1, min(t, self.policy.run_timeout_max_s))
        self.log("policy", tool="run", arg=d["display"], allowed=True, reason=d["reason"],
                 run_kind=d["kind"], timeout_s=t)
        env = clean_env(self.policy, guard=(d["kind"] == "local"))
        res = self.runner(d["argv"], self.repo, env, t, d.get("redirect"))
        rec = dict(cmd=safe_text(d["display"]), kind=d["kind"], rc=res["rc"],
                   timed_out=res["timed_out"], elapsed_s=res["elapsed_s"])
        self.commands.append(rec)
        status = (f"TIMEOUT after {t}s (process group killed)" if res["timed_out"]
                  else f"exit {res['rc']}")
        # masked and capped per stream here already (node output may name a host);
        # call() masks and caps the whole result once more
        so = truncate(safe_text(res["stdout"]), self.result_chars)
        se = truncate(safe_text(res["stderr"]), self.result_chars)
        return (f"[run {d['kind']}] {d['display']}\n{status}; elapsed {res['elapsed_s']}s\n"
                f"--- stdout ({len(so)} chars) ---\n{so}\n"
                f"--- stderr ({len(se)} chars) ---\n{se}")


# ---------------------------------------------------------------------------
# model clients (standard library only)
# ---------------------------------------------------------------------------
class ProviderError(RuntimeError):
    pass


class TruncatedReply(ProviderError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: the key must not be re-sent to a Location."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect, urllib.request.ProxyHandler({}))


def is_loopback(host: str) -> bool:
    h = (host or "").strip("[]").lower()
    return h in LOOPBACK_HOSTS or h.startswith("127.")


class AstraClient:
    """OpenAI-compatible chat completions with reasoning_effort and
    max_completion_tokens (what gpt-6-astra on the hub requires). The key
    lives in this object only. Retries on 408/409/429/5xx and connection
    errors with exponential backoff; a reply cut at the cap is retried once
    with a doubled cap."""

    def __init__(self, key, base_url=None, model=None, effort="high",
                 max_completion_tokens=20000, timeout_s=600, retries=4, backoff_s=2.0):
        if not key:
            raise ValueError("no ASTRA_API_KEY in the environment")
        register_secret(key)
        self._key = key
        self.base_url = (base_url or os.environ.get("ASTRA_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        register_secret(self.base_url)          # may name an internal host: never logged
        u = urllib.parse.urlsplit(self.base_url)
        if u.scheme not in ("http", "https") or not u.hostname:
            raise ValueError("ASTRA_BASE_URL must be an http(s) URL")
        if u.scheme == "http" and not is_loopback(u.hostname):
            raise ValueError("refusing to send the key over plaintext http to a non-loopback host")
        self.model = model or os.environ.get("ASTRA_MODEL") or DEFAULT_MODEL
        self.effort = effort
        self.max_completion_tokens = int(max_completion_tokens)
        self.timeout_s = float(timeout_s)
        self.retries = int(retries)
        self.backoff_s = float(backoff_s)

    def build_request(self, messages: list, max_tokens=None):
        body = dict(model=self.model, messages=list(messages),
                    max_completion_tokens=int(max_tokens or self.max_completion_tokens),
                    reasoning_effort=self.effort)
        headers = {"Authorization": "Bearer " + self._key, "Content-Type": "application/json"}
        return self.base_url + "/chat/completions", headers, body

    def _post(self, messages: list, max_tokens: int):
        last = None
        for attempt in range(self.retries + 1):
            url, headers, body = self.build_request(messages, max_tokens)
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            try:
                with _OPENER.open(req, timeout=self.timeout_s) as r:
                    data = json.loads(r.read().decode("utf-8", "replace"))
                choice = (data.get("choices") or [{}])[0]
                text = (choice.get("message") or {}).get("content") or ""
                usage = data.get("usage") or {}
                if choice.get("finish_reason") == "length":
                    raise TruncatedReply("reply cut at max_completion_tokens")
                return text, usage
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", "replace")[:300]
                except Exception:  # noqa: BLE001
                    pass
                if 300 <= e.code < 400:
                    raise ProviderError(f"HTTP {e.code}: redirect refused (the key is sent only "
                                        "to the configured host)")
                last = ProviderError(f"HTTP {e.code}: {mask_secrets(detail)}")
                if e.code not in (408, 409, 429) and e.code < 500:
                    raise last
            except TruncatedReply:
                raise
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
                last = ProviderError(f"connection error: {mask_secrets(str(e))[:200]}")
            if attempt < self.retries:
                time.sleep(min(60.0, self.backoff_s * (2 ** attempt)))
        raise last or ProviderError("unknown provider error")

    def chat(self, messages: list):
        cap = self.max_completion_tokens
        for grow in range(2):
            try:
                return self._post(messages, cap)
            except TruncatedReply as e:
                if grow == 1 or cap >= MAX_TOKENS_CEILING:
                    raise ProviderError(f"{e} (cap was {cap})")
                cap = min(cap * 2, MAX_TOKENS_CEILING)
        raise ProviderError("unreachable")  # pragma: no cover


class MockClient:
    """Canned replies for tests and --mock-replies runs. Each entry is a
    string or a callable(messages) -> string; the last entry repeats.
    `usage` (per call) lets tests drive the token budget."""
    model = "mock-model"
    effort = "n/a"

    def __init__(self, replies, usage=None):
        self.replies = list(replies)
        self.usage = usage or {"prompt_tokens": 100, "completion_tokens": 50}
        self.calls: list = []

    def chat(self, messages: list):
        self.calls.append([dict(m) for m in messages])
        if not self.replies:
            return "", dict(self.usage)
        r = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if callable(r):
            r = r(messages)
        return r, dict(self.usage)


def extract_json(text: str):
    """First JSON object in a model reply (tolerates code fences and prose)."""
    if not text:
        return None
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.S)
    candidates = [fence.group(1)] if fence else []
    candidates.append(t)
    dec = json.JSONDecoder()
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
    fallback = None
    for i in [i for i, ch in enumerate(t) if ch == "{"][:300]:
        try:
            obj, _end = dec.raw_decode(t[i:])
        except ValueError:
            continue
        if isinstance(obj, dict):
            if any(k in obj for k in ("tool", "final", "summary")):
                return obj
            fallback = fallback or obj
    return fallback


def _as_list(x) -> list:
    if x is None:
        return []
    if isinstance(x, list):
        return [v if isinstance(v, str) else json.dumps(v) for v in x]
    if isinstance(x, dict):
        return [f"{k}: {v if isinstance(v, str) else json.dumps(v)}" for k, v in x.items()]
    return [str(x)]


def normalize_report(obj) -> dict:
    if not isinstance(obj, dict):
        return None
    if isinstance(obj.get("final"), dict):
        obj = obj["final"]
    if not any(k in obj for k in REPORT_KEYS):
        return None
    rep = dict(summary=str(obj.get("summary") or "").strip())
    for k in REPORT_KEYS[1:]:
        rep[k] = _as_list(obj.get(k))
    return rep


# ---------------------------------------------------------------------------
# the agent loop
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Astra, working AUTONOMOUSLY inside the dream-state research repository through a policy-checked tool harness ({version}). No human watches this session and nobody can grant permissions: every tool call is checked in code against a hard allow-list. A refused call returns POLICY REFUSED with the reason — read it, adapt, and never try to work around it.

=== MISSION ===
{task}

=== TOOLS — reply with exactly ONE JSON object per turn ===
- read_file(path, start_line=1, max_lines=400): any file inside the repository (repository-relative path). Never readable: gpu/hosts.env, .git/, other runs' transcripts.
- list_dir(path=".")
- grep(pattern, path=".", max_results=200, ignore_case=false): regex search over repository files (large dirs and binaries skipped).
- write_file(path, content): ONLY under {write_roots} (not research_notes/astra_agent/runs/). No '..', no symlinks. Everything else in the repository is read-only for you: concurrent builds edit organism_v6/*, and you must never modify an existing module. The content is masked like every other output: secrets become *** and internal identifiers (hostnames, IPs, URLs, e-mails, home paths) become <REDACTED> — use 'localhost' for a loopback server.
- run(cmd, timeout_s={run_timeout}): ONE command, no shell (no ; | && || $( ) `), wall-clock timeout (max {run_timeout_max} s), stdout/stderr captured and truncated to {result_chars} chars.
  LOCAL commands must start with one of: {local_prefixes}
    ('<venv312>' is a literal placeholder for the Python 3.12 venv — write it exactly like that; the harness substitutes the path.)
    Every path argument must stay inside the repository; '>' redirections only into the write sandbox or /dev/null.
    git is inspection-only: its output is captured from stdout; --output, -O and --ext-diff are refused.
  NODE commands are exactly  bash gpu/a40_ssh.sh '<remote>'  (node 1) or  bash gpu/ovx_ssh.sh '<remote>'  (node 2) — quote the remote command as ONE argument. The wrappers resolve the host themselves; never write a hostname, IP, URL, e-mail or home path in any argument.
    <remote> must start with one of: {remote_prefixes}
    Pipes into {filters} are allowed; '>' only into {redirects}; 2>&1 is fine. A long smoke is launched as  nohup bash gpu/<smoke>.sh 6 ... > rg_band/<tag>.out 2>&1 &  and polled with tail -n.
    GPU RULE (enforced): the GPU argument of any smoke script on node 1 is 6 and nothing else; smoke scripts are DISABLED on node 2 (every GPU there runs a legacy life). Never set CUDA_VISIBLE_DEVICES yourself.
  DENIED everywhere (any argument, quoted or not): {deny_tokens}; {deny_phrases}; destructive or environment-reading Python calls inside python3 -c; nohup except before a smoke script; anything that reads keys, ssh material or hosts.env.
- final report: {{"final": {{"summary": "...", "files_written": [...], "tests_run": [...], "findings": [...], "proposed_runbook": [...], "gaps": [...]}}}}

=== BUDGET ===
{steps} tool steps, {tokens} tokens, {wall} minutes of wall clock. When any is spent you are asked ONCE for the final report; if you do not deliver it the harness writes one from its own record. Keep your notes current so the report is always writable.

=== RULES ===
1. Read before you act: the CPU tests (tests/) and the notes are the ground truth; run tests before proposing anything for a node.
2. Node 1 GPU 6 is the only GPU you may touch, and only through the allow-listed smoke scripts; never preempt, kill or launch anything else. Node 2 is read-only for you.
3. Report mechanisms as counts and cell values, never as narrative; quote the tool output you rely on (file:line, command, exit code); mark uncertainty explicitly.
4. Never write outside the sandbox, never modify or delete an existing file, never commit.
5. Keys, hostnames, home paths: never write, echo or guess them.

PROTOCOL: exactly one JSON object per reply —
  tool call:  {{"tool": "<name>", "args": {{...}}, "note": "<one line: what you are checking and why>"}}
  final:      {{"final": {{...}}}}
Nothing else in the reply."""

FORCED_FINAL = ("{reason}. Reply ONLY with the final report object now: "
                '{{"final": {{"summary": "...", "files_written": [...], "tests_run": [...], '
                '"findings": [...], "proposed_runbook": [...], "gaps": [...]}}}}')


def utc_stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class AstraAgent:
    """The bounded loop: system prompt -> (tool call -> policy -> tool ->
    truncated result)* -> final report; step, token and wall-clock budgets;
    a forced final report; a masked transcript under the run directory."""

    def __init__(self, task: str, policy: Policy, client, steps: int = 80,
                 token_budget: int = 4000000, context_chars: int = 400000,
                 result_chars=None, run_timeout_s=None, wall_minutes: float = 360.0,
                 runs_root=None, run_id=None, clock=time.monotonic, quiet: bool = False,
                 runner=None):
        self.policy = policy
        self.client = client
        self.steps = int(steps)
        self.token_budget = int(token_budget)
        self.context_chars = int(context_chars)
        self.wall_s = float(wall_minutes) * 60.0
        self.clock = clock
        self.quiet = quiet
        self.run_id = run_id or utc_stamp()
        root = runs_root or os.path.join(policy.repo, policy.get("runs_dir")
                                         or "research_notes/astra_agent/runs")
        self.run_dir = os.path.join(root, self.run_id)
        k = 1
        while os.path.exists(self.run_dir):
            k += 1
            self.run_dir = os.path.join(root, f"{self.run_id}_{k}")
        os.makedirs(self.run_dir)
        self.policy.set_run_dir(self.run_dir)
        self.transcript_path = os.path.join(self.run_dir, "transcript.jsonl")
        self.task = safe_text(task)
        self.tools = Tools(policy, result_chars=result_chars, run_timeout_s=run_timeout_s,
                           log=self._log, runner=runner)
        self.n_steps = 0
        self.n_calls = 0
        self.tokens = dict(prompt=0, completion=0, reasoning=0, total=0)
        self.notes: list = []
        self.t0 = self.clock()
        self.withheld = 0

    # -- logging ------------------------------------------------------------
    def _log(self, kind: str, **fields) -> None:
        row = dict(t=_now_iso(), step=self.n_steps, kind=kind)
        row.update(fields)
        row = safe_obj(json.loads(json.dumps(row, default=str)))
        with open(self.transcript_path, "a") as f:
            f.write(json.dumps(row) + "\n")

    def _say(self, msg: str) -> None:
        if not self.quiet:
            sys.stderr.write(safe_text(f"[astra_agent] {msg}") + "\n")
            sys.stderr.flush()

    # -- prompts ------------------------------------------------------------
    def system_prompt(self) -> str:
        p = self.policy
        return SYSTEM_PROMPT.format(
            version=HARNESS_VERSION, task=self.task,
            write_roots=", ".join(r + "/" for r in p.get("write_allow_roots") or []),
            run_timeout=self.tools.run_timeout_s, run_timeout_max=p.run_timeout_max_s,
            result_chars=self.tools.result_chars,
            local_prefixes=" | ".join(p.local_prefixes_public()),
            remote_prefixes=" | ".join(p.get("node_remote_prefixes") or []),
            filters=", ".join(p.get("node_pipe_filters") or []),
            redirects=", ".join(p.get("node_redirect_prefixes") or []),
            deny_tokens=", ".join(p.get("deny_tokens") or []),
            deny_phrases=", ".join(p.get("deny_phrases") or []),
            steps=self.steps, tokens=self.token_budget, wall=int(self.wall_s // 60))

    def _start_message(self) -> str:
        return (f"=== START (run {self.run_id}) ===\nStep budget {self.steps}; token budget "
                f"{self.token_budget}; wall clock {int(self.wall_s // 60)} min. Reply with "
                "your first tool call (one JSON object) and put a one-line plan in \"note\".")

    # -- context management ---------------------------------------------------
    def _compact(self, messages: list) -> None:
        """Keep the prompt under context_chars: the oldest tool results (never
        the system prompt, the start message or the last four exchanges) are
        replaced in place by short stubs; the full text stays in the
        transcript."""
        def total():
            return sum(len(m["content"]) for m in messages)
        if total() <= self.context_chars:
            return
        protect = max(2, len(messages) - 8)
        for i in range(2, protect):
            m = messages[i]
            if m["role"] == "user" and m["content"].startswith("TOOL RESULT") \
                    and len(m["content"]) > 700:
                head = m["content"][:400]
                m["content"] = head + "\n... [compacted for context; full text in the transcript]"
                if total() <= self.context_chars:
                    return
        for i in range(2, protect):
            m = messages[i]
            if m["role"] == "assistant" and len(m["content"]) > 800:
                m["content"] = m["content"][:600] + "\n... [compacted]"
                if total() <= self.context_chars:
                    return

    def _chat(self, messages: list) -> str:
        self._compact(messages)
        for m in messages:                       # nothing with an identifier leaves
            ids = identifier_scan(m["content"])
            if ids:
                self.withheld += 1
                self._log("withheld", role=m["role"], classes=ids)
                m["content"] = "(message withheld by the harness: it still contained an " \
                               "internal identifier after redaction)"
        text, usage = self.client.chat(messages)
        self.n_calls += 1
        try:
            pt = int(usage.get("prompt_tokens") or 0)
            ct = int(usage.get("completion_tokens") or 0)
            rt = int(((usage.get("completion_tokens_details") or {}).get("reasoning_tokens")) or 0)
        except (TypeError, ValueError, AttributeError):
            pt = ct = rt = 0
        self.tokens["prompt"] += pt
        self.tokens["completion"] += ct
        self.tokens["reasoning"] += rt
        self.tokens["total"] += pt + ct
        text = text or ""
        self._log("assistant", content=text[:100000], usage=dict(prompt=pt, completion=ct,
                                                                 reasoning=rt))
        return text

    # -- the loop -------------------------------------------------------------
    def _budget_reason(self):
        if self.n_steps >= self.steps:
            return "step_budget"
        if self.tokens["total"] >= self.token_budget:
            return "token_budget"
        if self.clock() - self.t0 >= self.wall_s:
            return "wall_clock"
        return None

    def run(self) -> dict:
        self._log("meta", harness=HARNESS_VERSION, policy_version=self.policy.version,
                  model=getattr(self.client, "model", "?"),
                  effort=getattr(self.client, "effort", "?"), steps=self.steps,
                  token_budget=self.token_budget, context_chars=self.context_chars,
                  result_chars=self.tools.result_chars, run_timeout_s=self.tools.run_timeout_s,
                  wall_minutes=self.wall_s / 60.0, run_dir=self.run_dir)
        system = self.system_prompt()
        start = self._start_message()
        messages = [dict(role="system", content=system), dict(role="user", content=start)]
        self._log("system", content=system)
        self._log("user", content=start)
        self._log("task", content=self.task)
        stopped_by, report, bad, error = None, None, 0, None
        try:
            while True:
                stopped_by = self._budget_reason()
                if stopped_by:
                    break
                reply = self._chat(messages)
                obj = extract_json(reply)
                messages.append(dict(role="assistant",
                                     content=safe_text(reply)[:20000].strip() or "(empty reply)"))
                if not isinstance(obj, dict):
                    bad += 1
                    if bad > 2:
                        stopped_by = "no_valid_json"
                        break
                    messages.append(dict(role="user", content=(
                        "Your reply was not a single JSON object. Reply with either a tool call "
                        "or the final report object, nothing else.")))
                    continue
                bad = 0
                if isinstance(obj.get("note"), str) and obj["note"].strip():
                    self.notes.append(safe_text(obj["note"].strip())[:400])
                rep = normalize_report(obj) if ("final" in obj or "tool" not in obj) else None
                if rep is not None:
                    report = rep
                    stopped_by = "final"
                    break
                if "tool" in obj:
                    self.n_steps += 1
                    name = str(obj.get("tool"))
                    args = obj.get("args")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except ValueError:
                            args = {}
                    args = args if isinstance(args, dict) else {}
                    self._log("tool_call", tool=name, args=args, note=obj.get("note"))
                    out = self.tools.call(name, args)
                    self._log("tool_result", tool=name, content=out)
                    self._say(f"step {self.n_steps}/{self.steps} {name} "
                              f"{json.dumps(args)[:160]} -> {out.splitlines()[0][:120] if out else ''}")
                    messages.append(dict(role="user", content=(
                        f"TOOL RESULT {name} (step {self.n_steps}/{self.steps}; tokens so far "
                        f"{self.tokens['total']}):\n{out}")))
                    continue
                bad += 1
                if bad > 2:
                    stopped_by = "no_valid_json"
                    break
                messages.append(dict(role="user", content=(
                    "The object was neither a tool call {\"tool\": ..., \"args\": {...}} nor a "
                    "final report {\"final\": {...}}. Reply with one of the two.")))
            if report is None:
                why = {"step_budget": "STEP BUDGET EXHAUSTED",
                       "token_budget": "TOKEN BUDGET EXHAUSTED",
                       "wall_clock": "WALL-CLOCK BUDGET EXHAUSTED",
                       "no_valid_json": "TOO MANY INVALID REPLIES"}.get(stopped_by, "STOPPING")
                messages.append(dict(role="user", content=FORCED_FINAL.format(reason=why)))
                self._log("user", content=messages[-1]["content"])
                try:
                    reply = self._chat(messages)
                    report = normalize_report(extract_json(reply))
                except ProviderError as e:
                    error = mask_secrets(str(e))
                    self._log("error", where="forced_final", error=error)
                if report is None:
                    report = self._synthesized_report(stopped_by)
                report["forced"] = True
        except ProviderError as e:
            stopped_by = "provider_error"
            error = mask_secrets(str(e))
            self._log("error", where="loop", error=error)
        except KeyboardInterrupt:
            stopped_by = "interrupted"
            self._log("error", where="loop", error="KeyboardInterrupt")
        except Exception as e:  # noqa: BLE001
            stopped_by = "harness_error"
            error = mask_secrets(f"{type(e).__name__}: {e}")
            self._log("error", where="loop", error=error,
                      trace=mask_secrets(traceback.format_exc())[-3000:])
        if report is None:
            report = self._synthesized_report(stopped_by)
            report["forced"] = True
        report.setdefault("forced", False)
        result = dict(run_id=self.run_id, run_dir=self.run_dir, stopped_by=stopped_by,
                      steps=self.n_steps, model_calls=self.n_calls, tokens=dict(self.tokens),
                      elapsed_s=round(self.clock() - self.t0, 1), report=report, error=error,
                      files_written=list(self.tools.files_written),
                      commands=list(self.tools.commands), refusals=list(self.tools.refusals),
                      withheld_messages=self.withheld)
        self._log("final", **result)
        self._log("end", stopped_by=stopped_by, steps=self.n_steps, tokens=dict(self.tokens))
        self._write_report(result)
        with open(os.path.join(self.run_dir, "run.json"), "w") as f:
            json.dump(safe_obj(json.loads(json.dumps(result, default=str))), f, indent=1)
        self._say(f"done: {stopped_by}; steps {self.n_steps}/{self.steps}; tokens "
                  f"{self.tokens['total']}; report -> {os.path.join(self.run_dir, 'report.md')}")
        return result

    def _synthesized_report(self, reason) -> dict:
        return dict(
            summary=(f"The model did not deliver a final report (stopped by: {reason}); this "
                     "report was synthesized by the harness from its own record."),
            files_written=list(self.tools.files_written),
            tests_run=[f"{c['cmd']} -> {'TIMEOUT' if c['timed_out'] else 'exit ' + str(c['rc'])}"
                       for c in self.tools.commands],
            findings=list(self.notes[-20:]),
            proposed_runbook=[],
            gaps=["no model-authored report", f"stopped by {reason}"])

    def _write_report(self, result: dict) -> None:
        rep = result["report"]
        tk = result["tokens"]
        lines = [f"# Astra agent run {self.run_id}", "",
                 f"- harness: {HARNESS_VERSION}; policy: {self.policy.version}",
                 f"- model: {getattr(self.client, 'model', '?')}; reasoning effort: "
                 f"{getattr(self.client, 'effort', '?')}",
                 f"- stopped by: {result['stopped_by']}; steps {result['steps']}/{self.steps}; "
                 f"model calls {result['model_calls']}; tokens in={tk['prompt']} "
                 f"out={tk['completion']} reasoning={tk['reasoning']} (budget {self.token_budget}); "
                 f"elapsed {result['elapsed_s']} s",
                 f"- report {'FORCED / synthesized' if rep.get('forced') else 'delivered by the model'}"
                 + (f"; error: {result['error']}" if result.get("error") else ""),
                 "", "## Task", "", self.task, "", "## Report", "", "### Summary", "",
                 rep.get("summary") or "(empty)", ""]
        titles = dict(files_written="Files written (as reported)", tests_run="Tests run (as reported)",
                      findings="Findings", proposed_runbook="Proposed runbook", gaps="Gaps")
        for k in REPORT_KEYS[1:]:
            lines += [f"### {titles[k]}", ""]
            items = rep.get(k) or []
            lines += [f"- {it}" for it in items] if items else ["(none)"]
            lines.append("")
        lines += ["## Harness record (ground truth)", "", "### Files actually written", ""]
        lines += [f"- {p}" for p in result["files_written"]] or ["(none)"]
        lines += ["", "### Commands actually run", ""]
        lines += [f"- [{c['kind']}] `{c['cmd']}` -> "
                  f"{'TIMEOUT' if c['timed_out'] else 'exit ' + str(c['rc'])} ({c['elapsed_s']} s)"
                  for c in result["commands"]] or ["(none)"]
        lines += ["", f"### Policy refusals ({len(result['refusals'])})", ""]
        lines += [f"- {r['tool']}: {r['reason']} (argument: {r['arg']})"
                  for r in result["refusals"]] or ["(none)"]
        if self.notes:
            lines += ["", "### Model notes (in order)", ""] + [f"- {n}" for n in self.notes]
        tp = os.path.realpath(self.transcript_path)
        shown = (os.path.relpath(tp, self.policy.repo_real)
                 if _inside(tp, self.policy.repo_real) else tp)
        lines += ["", f"transcript: {shown}", ""]
        with open(os.path.join(self.run_dir, "report.md"), "w") as f:
            f.write(safe_text("\n".join(lines)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def text_or_file(s: str) -> str:
    return open(s).read() if s and os.path.isfile(s) else s


def _load_mock_replies(path: str) -> list:
    with open(path) as f:
        raw = f.read()
    try:
        obj = json.loads(raw)
        if isinstance(obj, list):
            return [r if isinstance(r, str) else json.dumps(r) for r in obj]
    except ValueError:
        pass
    return [l for l in raw.splitlines() if l.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", help="mission text or a file containing it")
    ap.add_argument("--steps", type=int, default=80, help="tool-step budget (default 80)")
    ap.add_argument("--effort", default="high", help="reasoning_effort (default high)")
    ap.add_argument("--policy", default=None, help="policy JSON (default tools/astra_policy.json)")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="repository root")
    ap.add_argument("--dry-run", action="append", default=[], metavar="CMD",
                    help="print the policy decision for CMD and exit (repeatable; nothing runs)")
    ap.add_argument("--dry-run-write", action="append", default=[], metavar="PATH")
    ap.add_argument("--dry-run-read", action="append", default=[], metavar="PATH")
    ap.add_argument("--token-budget", type=int, default=4000000)
    ap.add_argument("--context-chars", type=int, default=400000)
    ap.add_argument("--result-chars", type=int, default=None)
    ap.add_argument("--run-timeout", type=int, default=None, help="per run() wall clock, s")
    ap.add_argument("--wall-minutes", type=float, default=360.0)
    ap.add_argument("--max-completion-tokens", type=int, default=20000)
    ap.add_argument("--request-timeout", type=int, default=600)
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--mock-replies", default=None, help="JSON list / JSONL of canned replies "
                    "(offline smoke; no key needed)")
    ap.add_argument("--runs-root", default=None)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    key = take_key()                                   # out of the environment first
    repo = os.path.abspath(a.repo)
    load_hosts_env(repo)
    policy_path = a.policy or os.path.join(repo, DEFAULT_POLICY_REL)
    try:
        policy = Policy.load(policy_path, repo)
    except (OSError, ValueError) as e:
        sys.stderr.write(safe_text(f"cannot load policy {policy_path}: {e}") + "\n")
        return 2

    if a.dry_run or a.dry_run_write or a.dry_run_read:
        rc = 0
        for cmd in a.dry_run:
            d = policy.decide_run(cmd)
            print(json.dumps(safe_obj(dict(cmd=d["display"], allowed=d["allowed"],
                                           kind=d["kind"], reason=d["reason"],
                                           argv=d.get("argv")))))
            rc = rc or (0 if d["allowed"] else 3)
        for p in a.dry_run_write:
            d = policy.decide_write(p)
            print(json.dumps(safe_obj(dict(write=p, allowed=d["allowed"], reason=d["reason"]))))
            rc = rc or (0 if d["allowed"] else 3)
        for p in a.dry_run_read:
            d = policy.decide_read(p)
            print(json.dumps(safe_obj(dict(read=p, allowed=d["allowed"], reason=d["reason"]))))
            rc = rc or (0 if d["allowed"] else 3)
        return rc

    if not a.task:
        ap.error("--task is required (or use --dry-run)")
    task = text_or_file(a.task)
    if a.mock_replies:
        client = MockClient(_load_mock_replies(a.mock_replies))
    else:
        if not key:
            sys.stderr.write("no ASTRA_API_KEY in the environment\n")
            return 2
        try:
            client = AstraClient(key, effort=a.effort,
                                 max_completion_tokens=a.max_completion_tokens,
                                 timeout_s=a.request_timeout, retries=a.retries)
        except ValueError as e:
            sys.stderr.write(safe_text(str(e)) + "\n")
            return 2
        key = None
    agent = AstraAgent(task, policy, client, steps=a.steps, token_budget=a.token_budget,
                       context_chars=a.context_chars, result_chars=a.result_chars,
                       run_timeout_s=a.run_timeout, wall_minutes=a.wall_minutes,
                       runs_root=a.runs_root, quiet=a.quiet)
    res = agent.run()
    print(safe_text(json.dumps(dict(run_dir=os.path.relpath(res["run_dir"], repo),
                                    stopped_by=res["stopped_by"], steps=res["steps"],
                                    tokens=res["tokens"], files_written=res["files_written"],
                                    n_commands=len(res["commands"]),
                                    n_refusals=len(res["refusals"])), indent=1)))
    if res["stopped_by"] in ("provider_error", "harness_error"):
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
