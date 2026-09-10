"""Agentic parent harness (Rohin's rulings of 2026-09-10): the parent is an
AGENT — a frozen, stronger model with read-only tools over ONE child's life
directory and over the parental society's shared ledger — not a single chat
call with a bounded playbook. Two such parents share a room, cross-verify each
other's brief, and merge into the ONE brief the child reads at its next wake.

Runs ON the GPU nodes (Python 3.12 venv), standard library only; the model is
reached over HTTP (OpenAI-compatible, Anthropic /v1/messages, or the local
vLLM server), selected by environment variables. Invoked ONLY at sleep
boundaries from run_life_v2 (--parent-mode agentic) through
`parent_brief_agentic`, which has the same signature and return shape as
`parent_brief.parent_brief`.

HARD RULES (each is enforced in code, not only asked of the model)
  thinker/compiler line  The brief is written to <sleep_dir>/parent_brief.txt
                         and shown in the WAKING brief only. It is never
                         written into the sleep corpus (corpus.json) and
                         nothing here touches the compiler or the trainer.
                         The child learns from its own thoughts; the parent's
                         words reach the weights only if the child restates
                         them itself (rehearsal).
  repetition             The parent sees its previous briefs and is told to
                         keep the SAME core lesson (sharpen, do not switch);
                         every delivered brief ends with REHEARSAL_TAIL, which
                         asks the child to restate the lesson as its first NOTE
                         of every episode until it is how it thinks.
  persistence            The parent is instructed to reward continued,
                         changing attempts after a non-improving outcome and
                         never early stopping; the cross-verification round
                         checks the other parent's brief for this.
  never answers          Every brief, frontier estimate, curriculum reason and
                         society note passes `parent_backend.leak_scan` (with
                         `parent_brief`'s quote-back exemption: a phrase the
                         child itself keeps writing may be quoted back to name
                         its ritual) plus the GYM's leak terms — held-out ids
                         or families and the window's reference answers,
                         passed by run_life_v2 as exact substrings, never
                         excused by quote-back. Any hit -> the fixed
                         process-only FALLBACK is delivered instead.
  private reflections    Rows of kind 'reflection' may be read (tool
                         `reflections`, shown only when they exist) but never
                         quoted, paraphrased or mentioned: reflection.
                         reflection_violations (unicode-normalised 6-gram
                         quote, >= 4 unshared content words of one row, any
                         mention) -> FALLBACK for the brief; critiques,
                         evidence and society notes are redacted before they
                         are logged; the parent ledger records only the
                         COUNT of visible reflection rows.
  blind to the exam      The parent may read the child's ledger, ritual /
                         rehearsal / efficiency metrics, GATE-panel decisions,
                         prior briefs, the parental ledger and the other
                         children's SUMMARIES. It may NEVER read report-panel
                         or test scores. File access is ALLOW-LIST based
                         (`guarded_path`): a path is resolved with realpath
                         (symlinks cannot alias a forbidden file), must stay
                         inside the life directory, and its resolved relative
                         name must be one of ledger.jsonl, parent_ledger.jsonl,
                         probe_gate*.json, sleep_*/gate.json,
                         sleep_*/parent_brief.{txt,json} or
                         sleep_*/waking_brief.txt. Everything else raises
                         ForbiddenRead — explicitly every probe_* that is not
                         probe_gate*.json (probe_ep*.json,
                         probe_ep*_adapterOFF.json, *.ledger.jsonl of probes),
                         life.log (it logs report-panel probe means),
                         wake_*.json and corpus.json. Score scalars from
                         gate.json are exposed only when the gate panel is
                         verifiably disjoint from the report panel.
  no identifiers         No hostnames, IP addresses, user names, home paths,
                         URLs or e-mail addresses in any prompt or output.
                         Tool output is redacted before it is sent; a prompt
                         that still matches is never sent; an output that
                         matches is replaced with FALLBACK.
  no keys on disk        PARENT_*_API_KEY values are copied out of the
                         environment when this module is imported (process
                         start), removed from os.environ so no subprocess
                         (the sleep trainer) inherits them, registered as
                         secrets, and masked in every string that is written
                         to a ledger, a log or a debug dump. Base URLs are
                         never logged either (they may be internal hosts).
  key stays home         The key is sent only to the configured host: HTTP
                         redirects are refused (never followed, so the key is
                         never re-sent to a Location), *_proxy environment
                         variables are ignored, and a key is refused outright
                         when the base URL is plaintext http:// to a
                         non-loopback host.
  bounded               <= PARENT_MAX_TOOL_CALLS (default 8) tool calls per
                         parent per invocation; room dialogue <= 3 exchanges
                         (proposals, critiques, merge); every tool result is
                         truncated to PARENT_TOOL_RESULT_CHARS; the whole
                         room has a wall-clock deadline (PARENT_ROOM_TIMEOUT_S,
                         default 900 s): past it no request is sent, late
                         phases are skipped and the best validated proposal
                         (or FALLBACK, reason "deadline") is delivered.
  never blocks the life  parent_brief_agentic never raises into run_life_v2:
                         any exception in the room (provider, corrupt shared
                         ledger line, bad JSON on disk) delivers FALLBACK +
                         REHEARSAL_TAIL and logs a `room_error` row. Shared
                         society files are appended/rewritten under an
                         fcntl lock and read tolerantly (bad lines skipped).

Environment (documented here and in gpu/run_parent_agent.sh):
  PARENT_PROVIDER      openai_compat | anthropic | local | mock
  PARENT_BASE_URL      e.g. https://<hub>/v1 ; anthropic default
                       https://api.anthropic.com/v1 ; local default
                       http://127.0.0.1:8011/v1 (http:// + key is accepted
                       for loopback hosts only)
  PARENT_MODEL         model name (anthropic default claude-opus-5; local
                       default $V6_PARENT_MODEL)
  PARENT_API_KEY       read at process start; never written anywhere
  PARENT_MAX_TOKENS    max output tokens per model call. Default 16000 for
                       anthropic (the cap covers thinking PLUS text; current
                       Claude models think adaptively even when `thinking`
                       is omitted) and for openai_compat with
                       PARENT_REASONING set; 4000 for openai_compat without
                       reasoning; 2000 for local (8k-context vLLM). A reply
                       cut at the cap (stop_reason max_tokens /
                       finish_reason length) is retried ONCE with a doubled
                       cap, then is a provider error (-> FALLBACK).
  PARENT_MAX_TOKENS_FIELD  request field carrying the cap. Default
                       max_completion_tokens for openai_compat (what
                       reasoning endpoints such as the inference hub's
                       gpt-6-astra require) and max_tokens for local vLLM.
                       On an HTTP 400 whose body names the field, the other
                       field is tried once and then kept.
  PARENT_REASONING     effort: low|medium|high|xhigh|max (anthropic ->
                       output_config.effort + adaptive thinking;
                       openai_compat -> reasoning_effort; local -> ignored)
  PARENT_TIMEOUT_S     per-request timeout (default 240 s)
  PARENT_ROOM_TIMEOUT_S  wall-clock deadline for one room invocation
                       (default 900 s); PARENT_ROOM_MIN_PHASE_S (default
                       60 s) = time a critique/merge phase needs to start
  PARENT_CRITIQUE_CONTEXT_CHARS  budget for replaying a parent's own tool
                       results into its critique and merge turns (40000)
  PARENT_MAX_TOOL_CALLS, PARENT_TOOL_RESULT_CHARS
  PARENT_A_* / PARENT_B_*  the same variables per parent of a two-parent room
                       (if only one of them is configured, or only PARENT_*,
                       the room runs in single-parent mode)
  PARENT_MERGER        A | B — which parent writes the merged brief (default A)
  PARENT_AGENTIC_ONLY_RITUAL=1  call the room only at ritual-flagged sleeps
                       (default: every sleep — frontier estimates and
                       curriculum moves are wanted at every sleep)
  PARENTAL_SOCIETY_DIR shared ledger dir (default ~/v6_out/parental_society)
  PARENT_FORBIDDEN_TERMS  extra comma-separated identifiers to redact
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import getpass
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import fcntl                # Unix only (the nodes); locking is best-effort
except ImportError:  # pragma: no cover
    fcntl = None

from .parent_backend import PARENT_BOOT, ParentLedger, leak_scan, FALLBACK
from .parent_brief import (ritual_metrics, rehearsal_rate, episode_instances,
                           REHEARSAL_TAIL, _already_childs,
                           PROMPT_VERSION as BRIEF_PROMPT_VERSION)
from . import efficiency_markers
from .reflection import (REFLECTION_RULE, reflection_texts as _reflection_texts,
                         reflection_violations, scrub_reflections)

PROMPT_VERSION = "agentic-v1.1-2026-09-10"   # v1.1: critics see the evidence
MOVES = ("repeat", "sharpen", "advance", "reset")
PROVIDERS = ("openai_compat", "anthropic", "local", "mock")
ANTHROPIC_VERSION = "2023-06-01"
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
MAX_BRIEF_LINES = 10
MAX_BRIEF_CHARS = 1500          # + REHEARSAL_TAIL stays under the 1900 cap
MAX_EXCHANGES = 3               # proposals, critiques, merge
DEFAULT_TIMEOUT_S = 240         # per request
DEFAULT_ROOM_TIMEOUT_S = 900    # per room invocation (wall clock)
DEFAULT_MIN_PHASE_S = 60        # a critique/merge phase needs this much left
DEFAULT_CRITIQUE_CONTEXT_CHARS = 40000
MAX_TOKENS_CEILING = 128000     # never grow the cap past the largest output
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "::1")

try:                            # the 8 report-panel programs (never exposed)
    from .run_life import PROBES as REPORT_PANEL
except Exception:  # noqa: BLE001 — CPU box without the gym
    REPORT_PANEL = ["cbench-v1/susan", "cbench-v1/sha", "cbench-v1/dijkstra",
                    "cbench-v1/patricia", "cbench-v1/jpeg-c",
                    "cbench-v1/tiff2bw", "cbench-v1/gsm",
                    "cbench-v1/stringsearch"]


# ---------------------------------------------------------------------------
# secrets: snapshot at process start, mask everywhere
# ---------------------------------------------------------------------------
_SECRETS: list = []
_CONFIG_PREFIXES = ("PARENT_", "PARENTAL_", "V6_PARENT")


def register_secret(value) -> None:
    """Remember a secret so mask_secrets() can blank it in anything written."""
    if isinstance(value, str) and len(value) >= 6 and value not in _SECRETS:
        _SECRETS.append(value)


def mask_secrets(text: str) -> str:
    for s in _SECRETS:
        text = text.replace(s, "***")
    return text


def scrub(obj):
    """Recursively mask secrets in any JSON-like structure."""
    if isinstance(obj, str):
        return mask_secrets(obj)
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [scrub(v) for v in obj]
    return obj


def _is_key_var(name: str) -> bool:
    return name == "PARENT_API_KEY" or (name.startswith("PARENT_")
                                        and name.endswith("_API_KEY"))


def snapshot_env(env=None) -> dict:
    """Copy the PARENT_* configuration out of `env` (default os.environ) and
    REMOVE the API-key variables from it, so that no subprocess started later
    (the sleep trainer, the gym evaluator) inherits a key. The returned
    snapshot lives in memory only; its key values are registered as secrets."""
    src = os.environ if env is None else env
    snap = {k: v for k, v in src.items() if k.startswith(_CONFIG_PREFIXES)}
    for k in [k for k in list(src.keys()) if _is_key_var(k)]:
        register_secret(src[k])
        src.pop(k, None)
    return snap


_BOOT_ENV = snapshot_env()      # process start


# ---------------------------------------------------------------------------
# internal-identifier scanner (hostnames, IPs, users, paths, URLs, e-mail)
# ---------------------------------------------------------------------------
_ID_PATTERNS = [
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("email_or_user_at_host",
     re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b")),
    ("home_path", re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+")),
    # network schemes only: gym URIs ("benchmark://cbench-v1/x") must survive
    ("url", re.compile(r"\b(?:https?|wss?|ftp|sftp|ssh|scp|smb)://[^\s\"'<>]+",
                       re.I)),
    ("internal_host",
     re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*"
                r"\.(?:nvidia\.com|internal|local|lan|corp|intranet|cluster)\b",
                re.I)),
]
_GENERIC_NAMES = {"root", "user", "test", "admin", "localhost", "none"}


_LOCAL_IDS: list = []


def _local_identifiers() -> list:
    """User and host names of THIS process, plus PARENT_FORBIDDEN_TERMS
    (computed once)."""
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
    for h in (socket.gethostname(), os.uname().nodename
              if hasattr(os, "uname") else ""):
        if h:
            names.add(h)
            names.add(h.split(".")[0])
    extra = (_BOOT_ENV.get("PARENT_FORBIDDEN_TERMS")
             or os.environ.get("PARENT_FORBIDDEN_TERMS") or "")
    names.update(t.strip() for t in extra.split(",") if t.strip())
    ids = [n for n in names if len(n) >= 4 and n.lower() not in _GENERIC_NAMES]
    _LOCAL_IDS.append(ids)
    return ids


def identifier_scan(text: str) -> list:
    """Return the NAMES of matched identifier classes (never the matches
    themselves — the hits are logged, and a hit must not re-leak). Empty =
    clean."""
    hits = []
    for name, pat in _ID_PATTERNS:
        if pat.search(text):
            hits.append(name)
    for ident in _local_identifiers():
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(ident) + r"(?![A-Za-z0-9])",
                     text, re.I):
            hits.append("local_identifier")
            break
    return hits


def redact_identifiers(text: str) -> str:
    for _name, pat in _ID_PATTERNS:
        text = pat.sub("<REDACTED>", text)
    for ident in _local_identifiers():
        text = re.sub(r"(?<![A-Za-z0-9])" + re.escape(ident) + r"(?![A-Za-z0-9])",
                      "<REDACTED>", text, flags=re.I)
    return text


def safe_text(text: str) -> str:
    """What may be written to a ledger: secrets masked, identifiers redacted."""
    return redact_identifiers(mask_secrets(text))


def safe_obj(obj):
    """safe_text applied to every string VALUE of a JSON-like structure (never
    to the serialized JSON: a redaction spanning an escaped quote would break
    it)."""
    if isinstance(obj, str):
        return safe_text(obj)
    if isinstance(obj, dict):
        return {k: safe_obj(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_obj(v) for v in obj]
    return obj


class IdentifierLeak(RuntimeError):
    """A prompt still contained an internal identifier after redaction; it
    was NOT sent."""


# ---------------------------------------------------------------------------
# provider configuration and HTTP clients (standard library only)
# ---------------------------------------------------------------------------
class ProviderError(RuntimeError):
    pass


class TruncatedReply(ProviderError):
    """The reply was cut at the output cap (anthropic stop_reason max_tokens,
    openai finish_reason length): its text is not a complete answer."""


class RoomDeadline(ProviderError):
    """The room's wall-clock deadline passed; no request was sent."""


def is_loopback(host: str) -> bool:
    h = (host or "").strip("[]").lower()
    return h in LOOPBACK_HOSTS or h.startswith("127.")


def default_max_tokens(provider: str, reasoning) -> int:
    """See the module docstring: the cap covers thinking + text."""
    if provider == "anthropic":
        return 16000
    if provider == "openai_compat":
        return 16000 if reasoning else 4000
    return 2000                             # local 8k-context vLLM, mock


class ProviderConfig:
    """One parent's model endpoint. The key is held in memory only; repr(),
    public() and every log path exclude it (and the base URL). A key is
    refused when it would travel in plaintext (http:// to a non-loopback
    host)."""

    def __init__(self, provider: str, model=None, base_url=None, api_key=None,
                 max_tokens=None, reasoning=None, temperature=None, role="A",
                 timeout_s=None, max_tokens_field=None):
        if provider not in PROVIDERS:
            raise ValueError(f"PARENT_PROVIDER must be one of {PROVIDERS}, "
                             f"got {provider!r}")
        self.provider = provider
        self.role = role
        if provider == "anthropic":
            base_url = base_url or "https://api.anthropic.com/v1"
            model = model or "claude-opus-5"
        elif provider == "local":
            base_url = base_url or "http://127.0.0.1:8011/v1"
            model = model or os.environ.get("V6_PARENT_MODEL",
                                            "Qwen/Qwen2.5-32B-Instruct")
        elif provider == "openai_compat":
            if not base_url:
                raise ValueError("PARENT_BASE_URL is required for openai_compat")
            if not model:
                raise ValueError("PARENT_MODEL is required for openai_compat")
        else:                                   # mock
            model = model or "mock-model"
        self.model = model
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or None
        register_secret(self.api_key)
        if provider != "mock":
            u = urllib.parse.urlsplit(self.base_url)
            if u.scheme not in ("http", "https") or not u.hostname:
                raise ValueError(f"PARENT_BASE_URL must be an http(s) URL "
                                 f"for role {role}")
            if self.api_key and u.scheme == "http" and \
                    not is_loopback(u.hostname):
                raise ValueError(
                    f"refusing to send the role-{role} API key over plaintext "
                    f"http to a non-loopback host; use https")
        self.reasoning = (reasoning or "").strip().lower() or None
        self.max_tokens = int(max_tokens or default_max_tokens(provider,
                                                               self.reasoning))
        self.temperature = None if temperature is None else float(temperature)
        self.timeout_s = int(timeout_s or DEFAULT_TIMEOUT_S)
        self.max_tokens_field = max_tokens_field or (
            "max_completion_tokens" if provider == "openai_compat"
            else "max_tokens")

    def __repr__(self) -> str:
        return (f"ProviderConfig(role={self.role}, provider={self.provider}, "
                f"model={self.model}, api_key={'***' if self.api_key else None})")

    def public(self) -> dict:
        """What the ledgers record: provider and model names only."""
        return dict(role=self.role, provider=self.provider, model=self.model)

    @classmethod
    def from_env(cls, prefix: str, env: dict, role: str) -> "ProviderConfig":
        def g(name, default=None):
            return env.get(prefix + name, env.get("PARENT_" + name, default))
        return cls(provider=env[prefix + "PROVIDER"],
                   model=env.get(prefix + "MODEL"),
                   base_url=env.get(prefix + "BASE_URL"),
                   api_key=env.get(prefix + "API_KEY"),
                   max_tokens=g("MAX_TOKENS"), reasoning=g("REASONING"),
                   temperature=g("TEMPERATURE"), role=role,
                   timeout_s=g("TIMEOUT_S"),
                   max_tokens_field=g("MAX_TOKENS_FIELD"))


def configs_from_env(env=None) -> list:
    """PARENT_A_* and PARENT_B_* -> two parents; else PARENT_* -> one; else []."""
    env = _BOOT_ENV if env is None else env
    out = []
    for role in ("A", "B"):
        if env.get(f"PARENT_{role}_PROVIDER"):
            out.append(ProviderConfig.from_env(f"PARENT_{role}_", env, role))
    if not out and env.get("PARENT_PROVIDER"):
        out.append(ProviderConfig.from_env("PARENT_", env, "A"))
    return out


class ChatClient:
    """Interface: chat(messages, max_tokens=None, *, retries=None,
    deadline=None) -> text. messages are OpenAI-style dicts with roles
    system/user/assistant. `deadline` is an absolute time.monotonic() value:
    no request may start after it and every request's timeout is clipped
    to it."""
    provider = "abstract"
    model = "abstract"

    def chat(self, messages: list, max_tokens=None, *, retries=None,
             deadline=None) -> str:
        raise NotImplementedError


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: urllib would otherwise re-send the
    Authorization / x-api-key header to whatever Location a (compromised or
    misconfigured) hub or DNS answer names, and a POST would become a GET
    somewhere else. Returning None makes urllib raise HTTPError(3xx), which
    chat() maps to ProviderError."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# One opener for the process: no redirects, and NO proxies (a *_proxy
# variable in the node's environment must not reroute the key either).
_OPENER = urllib.request.build_opener(_NoRedirect,
                                      urllib.request.ProxyHandler({}))


class HTTPChatClient(ChatClient):
    """openai_compat and local: POST {base}/chat/completions.
    anthropic: POST {base}/messages with x-api-key + anthropic-version.
    Tool calling is NOT delegated to the provider: the agent protocol is JSON
    in the text, identical for every provider. Requests go through _OPENER
    (no redirects, no proxies); a reply cut at the output cap is retried once
    with a doubled cap; a 400 naming the max-tokens field swaps the field
    once (max_tokens <-> max_completion_tokens) and keeps the one that
    worked."""

    def __init__(self, cfg: ProviderConfig, retries: int = 2):
        self.cfg = cfg
        self.provider = cfg.provider
        self.model = cfg.model
        self.retries = retries

    def build_request(self, messages: list, max_tokens=None):
        """(url, headers, body) — pure; unit-tested without a network."""
        cfg = self.cfg
        max_tokens = int(max_tokens or cfg.max_tokens)
        # never ship an empty turn: the Anthropic API rejects it with a 400
        messages = [dict(m, content=m["content"] if str(m.get("content") or "")
                         .strip() else "(empty)") for m in messages]
        if cfg.provider == "anthropic":
            system = "\n\n".join(m["content"] for m in messages
                                 if m["role"] == "system")
            turns = []
            for m in messages:
                if m["role"] == "system":
                    continue
                if turns and turns[-1]["role"] == m["role"]:
                    turns[-1]["content"] += "\n\n" + m["content"]
                else:
                    turns.append(dict(role=m["role"], content=m["content"]))
            body = dict(model=cfg.model, max_tokens=max_tokens, messages=turns)
            if system:
                body["system"] = system
            if cfg.reasoning:
                effort = cfg.reasoning if cfg.reasoning in EFFORT_LEVELS \
                    else "high"
                body["thinking"] = {"type": "adaptive"}
                body["output_config"] = {"effort": effort}
            headers = {"Content-Type": "application/json",
                       "anthropic-version": ANTHROPIC_VERSION}
            if cfg.api_key:
                headers["x-api-key"] = cfg.api_key
            return cfg.base_url + "/messages", headers, body
        body = dict(model=cfg.model, messages=list(messages))
        body[cfg.max_tokens_field] = max_tokens
        if cfg.provider == "openai_compat" and cfg.reasoning:
            body["reasoning_effort"] = cfg.reasoning
        elif cfg.temperature is not None:
            body["temperature"] = cfg.temperature
        elif cfg.provider == "local":
            body["temperature"] = 0.4
        headers = {"Content-Type": "application/json"}
        if cfg.api_key:
            headers["Authorization"] = "Bearer " + cfg.api_key
        return cfg.base_url + "/chat/completions", headers, body

    @staticmethod
    def parse_response(provider: str, data: dict) -> str:
        """Text of the reply. Raises TruncatedReply when the provider stopped
        at the output cap (the text, often empty after adaptive thinking, is
        not an answer and must not be parsed as one)."""
        if provider == "anthropic":
            stop = data.get("stop_reason")
            if stop == "refusal":
                raise ProviderError("provider refused the request")
            text = "\n".join(b.get("text", "") for b in data.get("content", [])
                             if b.get("type") == "text")
            if stop == "max_tokens":
                raise TruncatedReply("truncated at max_tokens; raise "
                                     "PARENT_MAX_TOKENS")
            return text
        choice = (data.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content") or ""
        if choice.get("finish_reason") == "length":
            raise TruncatedReply("truncated at the output cap (finish_reason "
                                 "length); raise PARENT_MAX_TOKENS")
        return text

    def _post(self, messages: list, max_tokens: int, retries: int,
              deadline) -> str:
        """One logical request with bounded HTTP retries (408/409/429/5xx and
        connection errors) and one field swap on a 400 that names the
        max-tokens field. Timeouts are clipped to the deadline."""
        last, swapped = None, False
        attempt = 0
        while True:
            url, headers, body = self.build_request(messages, max_tokens)
            data = json.dumps(body).encode()
            timeout = float(self.cfg.timeout_s)
            if deadline is not None:
                left = deadline - time.monotonic()
                if left <= 1.0:
                    raise RoomDeadline("room deadline reached before the "
                                       "request could start")
                timeout = min(timeout, left)
            req = urllib.request.Request(url, data=data, headers=headers)
            try:
                with _OPENER.open(req, timeout=timeout) as r:
                    return self.parse_response(self.provider, json.load(r))
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", "replace")[:300]
                except Exception:  # noqa: BLE001
                    pass
                if 300 <= e.code < 400:
                    raise ProviderError(f"HTTP {e.code}: redirect refused (the "
                                        f"key is sent only to the configured "
                                        f"host)")
                last = ProviderError(f"HTTP {e.code}: {mask_secrets(detail)}")
                if e.code == 400 and not swapped and \
                        self.cfg.max_tokens_field in detail:
                    other = ("max_tokens"
                             if self.cfg.max_tokens_field != "max_tokens"
                             else "max_completion_tokens")
                    self.cfg.max_tokens_field = other      # keep what works
                    swapped = True
                    continue
                if e.code not in (408, 409, 429) and e.code < 500:
                    raise last
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = ProviderError(f"connection error: "
                                     f"{mask_secrets(str(e))[:200]}")
            if attempt >= retries:
                break
            attempt += 1
            pause = 2.0 * attempt
            if deadline is not None and time.monotonic() + pause >= deadline:
                break
            time.sleep(pause)
        raise last or ProviderError("unknown provider error")

    def chat(self, messages: list, max_tokens=None, *, retries=None,
             deadline=None) -> str:
        retries = self.retries if retries is None else int(retries)
        cap = int(max_tokens or self.cfg.max_tokens)
        for grow in range(2):
            try:
                return self._post(messages, cap, retries, deadline)
            except TruncatedReply as e:
                if grow == 1 or cap >= MAX_TOKENS_CEILING:
                    raise ProviderError(f"{e} (cap was {cap})")
                cap = min(cap * 2, MAX_TOKENS_CEILING)
        raise ProviderError("unreachable")  # pragma: no cover


class MockChatClient(ChatClient):
    """Canned client for tests and --mock smoke runs. Replies are chosen by
    phase: the CROSS-VERIFICATION and MERGE prompts get their own canned
    answers; everything else pops the `script` FIFO (the last entry repeats).
    A user message containing 'TOOL BUDGET EXHAUSTED' gets `final`.
    `raise_with` makes chat() raise, echoing that string (secret masking
    test)."""
    provider = "mock"

    def __init__(self, script=None, critique=None, merge=None, final=None,
                 model="mock-model", raise_with=None):
        self.script = list(script or [])
        self.critique = critique
        self.merge = merge
        self.final = final
        self.model = model
        self.raise_with = raise_with
        self.calls: list = []            # every messages list received

    def chat(self, messages: list, max_tokens=None, *, retries=None,
             deadline=None) -> str:
        self.calls.append([dict(m) for m in messages])
        if self.raise_with:
            raise ProviderError(f"HTTP 401: invalid key {self.raise_with}")
        last = messages[-1]["content"] if messages else ""
        if "=== CROSS-VERIFICATION ===" in last and self.critique is not None:
            return self.critique
        if "=== MERGE ===" in last and self.merge is not None:
            return self.merge
        if "TOOL BUDGET EXHAUSTED" in last and self.final is not None:
            return self.final
        if not self.script:
            return self.final or ""
        return self.script.pop(0) if len(self.script) > 1 else self.script[0]


def make_client(cfg: ProviderConfig) -> ChatClient:
    if cfg.provider == "mock":
        return MockChatClient(script=_MOCK_SMOKE_SCRIPT, critique=_MOCK_CRITIQUE,
                              merge=_MOCK_MERGE, final=_MOCK_SMOKE_SCRIPT[-1],
                              model=cfg.model)
    return HTTPChatClient(cfg)


# ---------------------------------------------------------------------------
# JSON protocol helpers
# ---------------------------------------------------------------------------
def extract_json(text: str):
    """First JSON object in a model reply (tolerates code fences and prose).
    Returns a dict or None."""
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
    starts = [i for i, ch in enumerate(t) if ch == "{"][:200]
    fallback = None
    for i in starts:
        try:
            obj, _end = dec.raw_decode(t[i:])
        except ValueError:
            continue
        if isinstance(obj, dict):
            if any(k in obj for k in ("tool", "final", "brief", "verdict")):
                return obj
            fallback = fallback or obj
    return fallback


# ---------------------------------------------------------------------------
# the child's life directory, read-only, with the exam blinded
# ---------------------------------------------------------------------------
class ForbiddenRead(PermissionError):
    """Raised for any path that is not on the parent's read allow-list —
    including every piece of report-panel / test material."""


# explicit denials (named in the error so the model learns the rule): every
# probe_* that is not the gate panel's summary, and the life log, which
# records report-panel probe means and gate candidates
_FORBIDDEN_NAME = re.compile(r"^(probe_(?!gate[^/]*\.json$)|life\.log$)")
# the ALLOW-list: what the parent may open, as paths relative to the life dir
# (after realpath resolution). Anything else is a ForbiddenRead.
_ALLOWED_PATHS = [
    re.compile(r"^ledger\.jsonl$"),
    re.compile(r"^parent_ledger\.jsonl$"),
    re.compile(r"^probe_gate[^/]*\.json$"),
    re.compile(r"^sleep_[^/]+/gate\.json$"),
    re.compile(r"^sleep_[^/]+/parent_brief\.(txt|json)$"),
    re.compile(r"^sleep_[^/]+/waking_brief\.txt$"),
]


def is_allowed_relpath(rel: str) -> bool:
    rel = rel.replace(os.sep, "/")
    if _FORBIDDEN_NAME.match(os.path.basename(rel)):
        return False
    return any(p.match(rel) for p in _ALLOWED_PATHS)


def guarded_path(life_real: str, rel: str) -> str:
    """The ONLY way a life-directory file is opened here. `life_real` is the
    realpath of the life directory; `rel` a path relative to it. The joined
    path is resolved with realpath (so a symlink cannot alias a forbidden
    file or a file outside), re-checked for containment, and its resolved
    relative name must match the allow-list."""
    p = os.path.realpath(os.path.join(life_real, rel))
    if p == life_real or not p.startswith(life_real + os.sep):
        raise ForbiddenRead(f"outside the life directory: {rel}")
    relp = os.path.relpath(p, life_real)
    base = os.path.basename(p)
    if _FORBIDDEN_NAME.match(base):
        raise ForbiddenRead(f"report-panel material is invisible to the "
                            f"parent: {base}")
    if not is_allowed_relpath(relp):
        raise ForbiddenRead(f"not on the parent's read allow-list: {relp}")
    return p


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _read_jsonl(path: str) -> list:
    """Tolerant JSONL reader for SHARED or long-lived files: a torn or corrupt
    line (several lives append to the society ledger) is skipped, never
    raised into the child's life."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                out.append(row)
    return out


def _tick(r) -> int:
    try:
        return int(r.get("tick", 0))
    except (TypeError, ValueError):
        return 0


def _instances_with_acts(rows: list):
    """Episode instances (same rule as parent_brief.episode_instances, keyed
    on thought rows) with each act row attached to the chunk of the SAME
    episode and tick — whichever order the writer used (batch_loop appends
    act rows before the tick's thought row; the older loop.py appended them
    after). An act whose chunk has not arrived yet waits in `pending` for the
    next thought row of that episode; pending acts are flushed to the last
    chunk of the previous instance when a new instance of the program starts,
    so an outcome never leaks into another instance."""
    inst = collections.OrderedDict()
    last_tick, count = {}, collections.Counter()
    pending = collections.defaultdict(list)
    for r in rows:
        k = r.get("kind")
        e = r.get("episode_id")
        if k == "act":
            key = (e, count[e])
            chunks = inst.get(key)
            if chunks and chunks[-1]["tick"] == _tick(r):
                chunks[-1]["acts"].append(r)      # thought row came first
            else:
                pending[e].append(r)              # thought row still to come
            continue
        if k != "thought" or not r.get("note"):
            continue
        t = _tick(r)
        if e not in last_tick or t <= last_tick[e]:
            if e in last_tick and pending.get(e):
                # new instance: pending outcomes from other ticks belong to
                # the old instance; same-tick ones are this chunk's (act-first
                # writer) and stay pending
                stray = [a for a in pending[e] if _tick(a) != t]
                pending[e] = [a for a in pending[e] if _tick(a) == t]
                prev = inst.get((e, count[e]))
                if prev and stray:
                    prev[-1]["acts"].extend(stray)
            count[e] += 1
        last_tick[e] = t
        inst.setdefault((e, count[e]), []).append(
            dict(tick=t, note=r["note"], acts=pending.pop(e, [])))
    return inst


class ChildView:
    """Read-only tools over one child's life directory. Every file the view
    opens goes through _resolve() -> guarded_path(): realpath-resolved, inside
    the life directory, and on the read allow-list (report-panel material,
    life.log, wake batches and the sleep corpus are never readable). Tool
    outputs are redacted of internal identifiers before they are returned."""

    TOOLS = {
        "ledger_tail": ("the child's last N episode instances as raw text: "
                        "its own thinking, actions and outcomes",
                        {"n_episodes": "int (default 6, max 24)"}),
        "metrics": ("ritual metrics, rehearsal rate against the previous "
                    "brief, efficiency markers for the last windows",
                    {"window": "int episodes (default 32)"}),
        "gate_decisions": ("per sleep: write-gate verdict (DONE / REJECTED_*)"
                           " and decision flags; GATE panel only",
                           {"last_k": "int (default 6)"}),
        "prior_briefs": ("earlier briefs to this child with their measured "
                         "effect, and this room's earlier frontier estimates "
                         "and curriculum moves", {"last_k": "int (default 3)"}),
        "society": ("the parental society's playbook and recent ledger "
                    "(all children)", {"last_k": "int (default 12)"}),
        "other_children": ("summaries of the sibling children: their briefs "
                           "and metrics, never their scores",
                           {"limit": "int (default 6)"}),
        "waking_brief": ("the child's own dreamed brief from its last sleep",
                         {}),
        "list_files": ("the files of the life directory that you may read "
                       "(everything else is hidden by design)", {}),
        # listed in the prompt ONLY when reflection rows exist (system_prompt)
        "reflections": ("PRIVATE: the child's last N reflection rows, written "
                        "between sessions with no task and no score. Read to "
                        "understand the child; NEVER quote, grade, mention or "
                        "respond to them", {"n": "int (default 4, max 12)"}),
    }

    def __init__(self, life_dir: str, rows=None, sleep_dir=None,
                 society_dir=None, tool_result_chars: int = 9000):
        self.life_dir = os.path.abspath(os.path.expanduser(life_dir))
        self.life_real = os.path.realpath(self.life_dir)
        self.child_id = os.path.basename(self.life_dir)
        self._rows = rows
        self.sleep_dir = os.path.abspath(sleep_dir) if sleep_dir else None
        self.stage = os.path.basename(self.sleep_dir) if self.sleep_dir else ""
        self.society_dir = society_dir or default_society_dir()
        self.tool_result_chars = int(tool_result_chars)
        self.samples_seen: list = []      # child's own text shown to parents
        self.calls: list = []             # (tool, args) log = evidence

    # -- guard -------------------------------------------------------------
    def _resolve(self, rel: str) -> str:
        return guarded_path(self.life_real, rel)

    def _exists(self, rel: str) -> bool:
        """Existence of an ALLOWED file (a forbidden name is 'absent')."""
        try:
            return os.path.exists(self._resolve(rel))
        except ForbiddenRead:
            return False

    def read_text(self, rel: str, max_chars: int = 20000) -> str:
        with open(self._resolve(rel), errors="replace") as f:
            return f.read()[:max_chars]

    def read_json(self, rel: str):
        return _read_json(self._resolve(rel))

    @property
    def rows(self) -> list:
        if self._rows is None:
            self._rows = _read_jsonl(self._resolve("ledger.jsonl"))
        return self._rows

    def _sleep_dirs(self) -> list:
        return sorted(d for d in os.listdir(self.life_dir)
                      if d.startswith("sleep_")
                      and os.path.isdir(os.path.join(self.life_dir, d)))

    def previous_brief(self) -> str:
        """Most recent parent brief from any EARLIER sleep (repetition)."""
        for d in reversed(self._sleep_dirs()):
            if d == self.stage:
                continue
            rel = f"{d}/parent_brief.txt"
            if self._exists(rel):
                t = self.read_text(rel).strip()
                if t:
                    return t
        return ""

    # -- tools -------------------------------------------------------------
    def list_files(self) -> str:
        """Only what the allow-list permits: probe_*, life.log, wake_*.json,
        corpus.json, adapters and markers are not listed (nor readable)."""
        out = []
        for root, dirs, files in os.walk(self.life_dir):
            dirs[:] = [d for d in sorted(dirs) if d != "adapter"]
            rel = os.path.relpath(root, self.life_dir)
            for f in sorted(files):
                relf = f if rel == "." else os.path.join(rel, f)
                if not is_allowed_relpath(relf):
                    continue
                try:                        # symlink aliases are hidden too
                    self._resolve(relf)
                except ForbiddenRead:
                    continue
                out.append(relf)
            if len(out) > 400:
                out.append("... (truncated)")
                break
        return "\n".join(out)

    def ledger_tail(self, n_episodes: int = 6) -> str:
        """The child's last N episode instances: each chunk's own text, then
        the outcome(s) of the action(s) it took in that chunk."""
        n = max(1, min(int(n_episodes or 6), 24))
        inst = list(_instances_with_acts(self.rows).items())[-n:]
        parts = []
        for (eid, k), chunks in inst:
            acts = [a for c in chunks for a in c["acts"]]
            best = max([a.get("score") or 0.0 for a in acts] or [0.0])
            lines = [f"### {eid} (instance {k}) chunks={len(chunks)} "
                     f"acts={len(acts)} best={best:.4f}"]
            for c in chunks:
                lines.append(f"[chunk {c['tick']}] " + c["note"][:600])
                for a in c["acts"]:
                    pred = a.get("prediction")
                    sur = a.get("surprise")
                    lines.append(
                        f"   [chunk {c['tick']}] ACT -> score "
                        f"{(a.get('score') or 0.0):.4f}"
                        + (f" (predicted {pred:.3f}, surprise {sur:+.3f})"
                           if isinstance(pred, (int, float))
                           and isinstance(sur, (int, float)) else ""))
            parts.append("\n".join(lines)[:4000])
        text = "\n\n".join(parts) or "(no episodes yet)"
        self.samples_seen.append(text)
        return text

    def metrics(self, window: int = 32) -> dict:
        window = max(4, int(window or 32))
        prev = self.previous_brief()
        m = ritual_metrics(self.rows, window, brief_text=prev)
        m["rehearsal_rate_vs_previous_brief"] = round(
            rehearsal_rate(self.rows, prev, window), 3)
        th = [r for r in self.rows if r.get("kind") == "thought"
              and r.get("note")]
        m["episode_instances_lived"] = len(episode_instances(th))
        try:
            wins = efficiency_markers.analyse(self.life_dir, rows=self.rows)
            m["efficiency_last_windows"] = wins[-2:] if wins else \
                "too few episodes for a 32-episode window"
        except Exception as e:  # noqa: BLE001
            m["efficiency_last_windows"] = f"unavailable ({type(e).__name__})"
        return m

    def gate_decisions(self, last_k: int = 6) -> list:
        """Decisions only. Score scalars appear only when the gate panel is
        verifiably disjoint from the report panel."""
        out = []
        for d in self._sleep_dirs()[-max(1, int(last_k or 6)):]:
            sd = os.path.join(self.life_dir, d)
            ad = os.path.join(sd, "adapter")
            verdict = "not trained"
            if os.path.isdir(ad):
                marks = [m for m in os.listdir(ad)
                         if m in ("DONE", "CANDIDATE") or m.startswith("REJECTED")]
                verdict = ",".join(sorted(marks)) or "training"
            row = dict(sleep=d, write_verdict=verdict)
            if self._exists(f"{d}/gate.json"):
                try:
                    g = self.read_json(f"{d}/gate.json")
                except ValueError:              # torn / corrupt gate.json
                    g = None
                if not isinstance(g, dict):
                    row["gate_json"] = "unreadable"
                    out.append(row)
                    continue
                row.update(score_ok=g.get("score_ok"),
                           brevity_ok=g.get("brevity_ok"),
                           cand_chunks_per_ep=g.get("cand_chunks_per_ep"),
                           base_chunks_per_ep=g.get("base_chunks_per_ep"))
                try:
                    pg = f"probe_gate{int(d[6:]):04d}.json"
                except ValueError:
                    pg = None
                if pg and self._exists(pg):
                    try:
                        res = self.read_json(pg).get("results") or {}
                    except (ValueError, AttributeError):
                        res = {}
                    canon = {p.replace("benchmark://", "") for p in res}
                    report = {p.replace("benchmark://", "") for p in REPORT_PANEL}
                    if canon and not (canon & report):
                        row.update(gate_panel="disjoint", n_programs=len(canon),
                                   candidate=_r4(g.get("candidate")),
                                   floor=_r4(g.get("floor")),
                                   base=_r4(g.get("base")))
                    else:
                        row.update(gate_panel="report (scores withheld)")
            out.append(row)
        return out

    def prior_briefs(self, last_k: int = 3) -> dict:
        k = max(1, int(last_k or 3))
        briefs = []
        for d in reversed(self._sleep_dirs()):
            if d == self.stage or len(briefs) >= k:
                continue
            tp, jp = f"{d}/parent_brief.txt", f"{d}/parent_brief.json"
            if not (self._exists(tp) or self._exists(jp)):
                continue
            b = dict(sleep=d)
            if self._exists(tp):
                b["brief"] = self.read_text(tp).strip()[:1900]
            if self._exists(jp):
                try:
                    meta = self.read_json(jp)
                except ValueError:
                    meta = {}
                mm = meta.get("metrics") or {}
                b["measured_at_that_sleep"] = {
                    x: mm.get(x) for x in ("ritual", "flags", "rehearsal_rate",
                                           "n_episodes")}
                b["intervened"] = meta.get("intervened")
                b["prompt_version"] = meta.get("prompt_version")
            briefs.append(b)
        rooms = [r for r in _read_jsonl(self._resolve("parent_ledger.jsonl"))
                 if r.get("kind") == "agentic_room"][-k:]
        return dict(briefs=briefs, previous_rooms=[
            dict(stage=r.get("child_stage"),
                 frontier_estimate=(r.get("merged") or {}).get("frontier_estimate"),
                 curriculum_move=(r.get("merged") or {}).get("curriculum_move"),
                 fallback=(r.get("merged") or {}).get("fallback"))
            for r in rooms])

    def society(self, last_k: int = 12) -> dict:
        k = max(1, int(last_k or 12))
        sd = self.society_dir
        pb = os.path.join(sd, "playbook.md")
        rows = _read_jsonl(os.path.join(sd, "ledger.jsonl"))[-k:]
        playbook = "(no playbook yet)"
        if os.path.exists(pb):
            with open(pb, errors="replace") as f:
                playbook = f.read()[:4000]
        return dict(
            playbook=playbook,
            ledger_tail=[dict(child=r.get("child"), stage=r.get("stage"),
                              move=(r.get("curriculum_move") or {}).get("move"),
                              frontier=((r.get("frontier_estimate") or {})
                                        .get("text") or "")[:300],
                              brief=(r.get("brief") or "")[:300])
                         for r in rows])

    def other_children(self, limit: int = 6) -> list:
        """SUMMARIES only: small files (briefs, meta, markers). Sibling
        ledgers and probe files are never opened."""
        root = os.path.dirname(self.life_dir)
        out = []
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if d == self.child_id or not os.path.isdir(p) or \
                    not os.path.exists(os.path.join(p, "ledger.jsonl")):
                continue
            out.append(_life_summary(p))
            if len(out) >= max(1, int(limit or 6)):
                break
        return out

    def waking_brief(self) -> str:
        for d in reversed(self._sleep_dirs()):
            rel = f"{d}/waking_brief.txt"
            if self._exists(rel):
                t = self.read_text(rel).strip()
                if t:
                    self.samples_seen.append(t)
                    return f"[{d}]\n" + t[:6000]
        return "(no waking brief yet)"

    # -- private reflection rows (2026-09-10) -----------------------------------
    def reflection_texts(self) -> list:
        return _reflection_texts(self.rows)

    def n_reflections(self) -> int:
        return len(self.reflection_texts())

    def reflections(self, n: int = 4) -> str:
        """The child's private reflections. Deliberately NOT appended to
        samples_seen: the quote-back exemption of the leak scan must never
        excuse a quoted reflection (validate_output rejects it)."""
        n = max(1, min(int(n or 4), 12))
        texts = self.reflection_texts()[-n:]
        if not texts:
            return "(no reflection rows)"
        head = ("PRIVATE REFLECTION ROWS — read only. Never quote, grade, "
                "mention or respond to them.\n")
        return head + "\n---\n".join(t[:1500] for t in texts)

    # -- dispatch ----------------------------------------------------------
    def call(self, name: str, args=None) -> str:
        """Run a tool; returns redacted, bounded text. Unknown tool or a
        forbidden read returns an explanatory error string (the model is
        told; the harness never crashes on the model's request)."""
        args = dict(args or {})
        self.calls.append((name, args))
        if name not in self.TOOLS:
            return f"ERROR: unknown tool {name!r}; tools: {sorted(self.TOOLS)}"
        try:
            res = getattr(self, name)(**args)
        except ForbiddenRead as e:
            return f"FORBIDDEN: {e}"
        except TypeError as e:
            return f"ERROR: bad arguments for {name}: {e}"
        except Exception as e:  # noqa: BLE001
            return f"ERROR: {name} failed: {type(e).__name__}"
        text = res if isinstance(res, str) else json.dumps(res, indent=1)
        text = redact_identifiers(mask_secrets(text))
        if len(text) > self.tool_result_chars:
            text = text[:self.tool_result_chars] + "\n... (truncated)"
        return text


def _r4(x):
    return round(x, 4) if isinstance(x, (int, float)) else None


def _life_summary(p: str) -> dict:
    """A sibling's summary from small files only (no ledger, no probes);
    every file is opened through guarded_path on the sibling's directory."""
    name = os.path.basename(p)
    real = os.path.realpath(p)

    def gp(rel):
        return guarded_path(real, rel)

    sleeps = sorted(d for d in os.listdir(p) if d.startswith("sleep_"))
    verdicts = collections.Counter()
    for d in sleeps:
        ad = os.path.join(p, d, "adapter")
        if os.path.isdir(ad):
            for m in os.listdir(ad):
                if m == "DONE" or m.startswith("REJECTED"):
                    verdicts[m] += 1
    wakes = [f for f in os.listdir(p) if f.startswith("wake_")
             and f.endswith(".json")]
    exposure = 0
    for w in wakes:
        try:
            exposure = max(exposure, int(w[10:14]))
        except ValueError:
            pass
    s = dict(child=name, n_sleeps=len(sleeps), episodes_lived=exposure,
             write_verdicts=dict(verdicts),
             done=os.path.exists(os.path.join(p, "LIFE_DONE")))
    for d in reversed(sleeps):
        tp = gp(f"{d}/parent_brief.txt")
        jp = gp(f"{d}/parent_brief.json")
        if os.path.exists(tp) or os.path.exists(jp):
            s["latest_brief_sleep"] = d
            if os.path.exists(tp):
                with open(tp, errors="replace") as f:
                    s["latest_brief"] = f.read().strip()[:500]
            if os.path.exists(jp):
                try:
                    mm = _read_json(jp).get("metrics") or {}
                except ValueError:
                    mm = {}
                s["latest_metrics"] = {x: mm.get(x) for x in
                                       ("ritual", "flags", "rehearsal_rate")}
            break
    rooms = [r for r in _read_jsonl(gp("parent_ledger.jsonl"))
             if r.get("kind") == "agentic_room"]
    if rooms:
        mg = rooms[-1].get("merged") or {}
        s["latest_room"] = dict(stage=rooms[-1].get("child_stage"),
                                frontier_estimate=mg.get("frontier_estimate"),
                                curriculum_move=mg.get("curriculum_move"))
    return s


def default_society_dir() -> str:
    return os.path.expanduser(os.environ.get("PARENTAL_SOCIETY_DIR")
                              or _BOOT_ENV.get("PARENTAL_SOCIETY_DIR")
                              or "~/v6_out/parental_society")


# ---------------------------------------------------------------------------
# output validation: schema, length, leak scan, identifier scan
# ---------------------------------------------------------------------------
def fallback_output(reason: str, hits=None) -> dict:
    return dict(brief=FALLBACK, delivered_text=FALLBACK + REHEARSAL_TAIL,
                frontier_estimate=dict(text=f"unknown (fallback: {reason})",
                                       confidence=0.0),
                curriculum_move=dict(move="repeat",
                                     reason=f"fallback: {reason}"),
                evidence=[], society_note=None, fallback=True,
                fallback_reason=reason, hits=list(hits or []))


def _strip_tail(brief: str) -> str:
    core = REHEARSAL_TAIL.strip()
    i = brief.find(core[:40])
    return brief[:i] if i >= 0 else brief


def validate_output(obj, samples: str, evidence_default=None,
                    reflections=None, exact_terms=None) -> dict:
    """Normalize a model's final object or return fallback_output(). The
    brief is strict (present, <= 10 lines, no leak, no identifier, no quote /
    paraphrase / mention of any private reflection row — reflection.
    reflection_violations); the frontier estimate and the move are lenient
    (defaulted, but scanned when present); the society note is optional and
    dropped if it fails; evidence entries that fail any scan are dropped
    (they are logged to the parent ledger). exact_terms: the gym's leak
    terms (held-out ids / families, window answers), exact substrings."""
    if not isinstance(obj, dict):
        return fallback_output("final object missing or not JSON")
    if isinstance(obj.get("final"), dict):
        obj = obj["final"]
    brief = obj.get("brief")
    if not isinstance(brief, str) or not brief.strip():
        return fallback_output("brief missing")
    lines = [l.rstrip() for l in _strip_tail(brief).splitlines() if l.strip()]
    truncated = len(lines) > MAX_BRIEF_LINES
    body = "\n".join(lines[:MAX_BRIEF_LINES]).strip()[:MAX_BRIEF_CHARS]
    fe = obj.get("frontier_estimate")
    if not isinstance(fe, dict):
        fe = dict(text=str(fe) if fe else "not stated", confidence=0.0)
    fe_text = " ".join(str(fe.get("text") or "not stated").split("\n")[:3])[:400]
    try:
        conf = min(1.0, max(0.0, float(fe.get("confidence", 0.0))))
    except (TypeError, ValueError):
        conf = 0.0
    fe = dict(text=fe_text, confidence=round(conf, 2))
    cm = obj.get("curriculum_move")
    if isinstance(cm, str):
        cm = dict(move=cm, reason="")
    if not isinstance(cm, dict):
        cm = {}
    move = str(cm.get("move") or "").strip().lower()
    if move not in MOVES:
        cm = dict(move="repeat", reason=f"not stated (defaulted); given: "
                                        f"{str(cm.get('move'))[:40]}")
    else:
        cm = dict(move=move, reason=str(cm.get("reason") or "")[:400])
    ev = obj.get("evidence")
    if not isinstance(ev, list):
        ev = list(evidence_default or [])
    ev = [str(e)[:120] for e in ev][:16]
    note = obj.get("society_note")
    note = str(note).strip()[:240] if isinstance(note, str) and note.strip() \
        else None
    refl = list(reflections or [])
    # --- scans: any hit anywhere in the delivered or logged text -> fallback
    scanned = "\n".join([body, fe["text"], cm["reason"]])
    hits = [h for h in leak_scan(scanned, exact_terms=exact_terms)
            if not _already_childs(h, scanned, samples)]
    if hits:
        return fallback_output("leak_scan", hits)
    ids = identifier_scan(scanned)
    if ids:
        return fallback_output("identifier_scan", ids)
    # a quoted, paraphrased or mentioned private reflection falls back
    # exactly like a leak hit (hit labels carry counts, never content)
    rq = reflection_violations(scanned, refl, samples)
    if rq:
        return fallback_output("reflection_quote", rq)
    if note and (leak_scan(note, exact_terms=exact_terms) or identifier_scan(note)
                 or reflection_violations(note, refl, samples)):
        note = None
    # evidence is logged to the parent ledger: an entry that quotes a
    # reflection, leaks or names an identifier is dropped, never written
    ev = [e for e in ev if not (leak_scan(e, exact_terms=exact_terms)
                                or identifier_scan(e)
                                or reflection_violations(e, refl, samples))]
    return dict(brief=body, delivered_text=body + REHEARSAL_TAIL,
                frontier_estimate=fe, curriculum_move=cm, evidence=ev,
                society_note=note, fallback=False, fallback_reason=None,
                hits=[], truncated=truncated)


# ---------------------------------------------------------------------------
# prompts
# ---------------------------------------------------------------------------
def _tool_lines(include_reflections: bool = False) -> str:
    out = []
    for name, (desc, args) in ChildView.TOOLS.items():
        if name == "reflections" and not include_reflections:
            continue
        a = ", ".join(f"{k}: {v}" for k, v in args.items()) or "no arguments"
        out.append(f"- {name}({a}): {desc}")
    return "\n".join(out)


def system_prompt(role: str, n_parents: int, window: int,
                  max_tool_calls: int, n_reflections: int = 0) -> str:
    room = ("one of TWO parents in this room; the other parent will critique "
            "your brief and you will critique theirs before ONE merged brief "
            "is delivered" if n_parents > 1 else "the only parent in this room")
    # rule 9 and the reflections tool appear ONLY when the child has private
    # reflection rows; every other life's prompt is byte-identical
    reflection_block = (f"\n9. {REFLECTION_RULE} ({n_reflections} reflection "
                        f"rows are visible through the reflections tool.)"
                        if n_reflections else "")
    return (PARENT_BOOT + f"""

=== THE ROOM (agentic parent harness {PROMPT_VERSION}) ===
You are parent {role}, {room}. Your child is a small model living in an
optimization workshop; it learns from its own experience and every {window}
episodes it sleeps (its recent thoughts are compiled into a small weight
update). You are a frozen, stronger model with READ-ONLY tools over this
child's life directory and over your parental society's shared ledger. You
have judgment: read before you speak, and change your method when the record
says the last one did not take.

HARD RULES (enforced in code; a violation replaces your brief with a fixed
process-only fallback, which teaches nothing):
1. Never give answers. Never name specific actions, passes, options, recipes
   or scores for specific programs, and never paraphrase them. You may quote
   a short phrase the child itself keeps repeating, to name its ritual.
2. Process only, no metric-teaching: never tell the child what is measured or
   how to move a measurement (do not mention rehearsal rates, ritual flags,
   similarity scores, gates, probes, adapters, sleeps or training). The child
   must get better at thinking, not at looking better.
3. The exam is invisible to you by design; do not ask for it or infer it. The
   only evaluation you see is the write gate on the gate panel.
4. Repetition is the mechanism: keep the SAME core lesson as the previous
   brief(s) unless the evidence justifies a change. Sharpen it; acknowledge
   what the child has begun to do; insist on the rest. A new lesson every
   sleep teaches nothing.
5. Persistence: reward continued, changing attempts after a non-improving
   outcome; never reward stopping early; never ask the child to do less.
6. Your brief goes ONLY into the child's waking context. It is never written
   into its sleep corpus. The child learns from ITS OWN thoughts, so ask it to
   think and to restate, not to obey.
7. No hostnames, addresses, paths, user names or keys anywhere in your output.
8. Speak to the child directly, concretely, in its own terms; at most
   {MAX_BRIEF_LINES} lines. The harness appends the standard rehearsal request
   to every brief — do not write it yourself.{reflection_block}

FRONTIER ESTIMATE (your core organ): what the child can ALMOST do after
working through this lesson — post-adaptation, not immediately — in 1-3 lines,
with a confidence in [0, 1]. It is logged and later audited against outcomes.
CURRICULUM MOVE: repeat (same lesson, same difficulty) | sharpen (same lesson,
more specific ask) | advance (the lesson has taken; move to the next trait) |
reset (lesson difficulty drifted for several sleeps without gains; restate the
simplest version). Stability rule: if the previous rooms advanced repeatedly
without evidence of gains, choose reset.

TOOLS (at most {max_tool_calls} calls; results are truncated; the dashboard
you receive already has the basics — ledger_tail is usually essential):
{_tool_lines(bool(n_reflections))}

PROTOCOL: reply with exactly ONE JSON object and nothing else.
  tool call: {{"tool": "<name>", "args": {{...}}}}
  final:     {{"final": {{"brief": "<= {MAX_BRIEF_LINES} lines to the child",
              "frontier_estimate": {{"text": "1-3 lines", "confidence": 0.0}},
              "curriculum_move": {{"move": "repeat|sharpen|advance|reset",
                                  "reason": "..."}},
              "evidence": ["tool(args) you relied on", ...],
              "society_note": "optional: one transferable teaching observation for the shared playbook"}}}}
""")


def dashboard(view: ChildView, context: dict) -> str:
    m = context.get("metrics") or {}
    prev = context.get("prev_brief") or ""
    rooms = view.prior_briefs(3).get("previous_rooms") or []
    gates = view.gate_decisions(4)
    soc = view.society(6)
    text = (f"=== CHILD ===\nchild: {view.child_id}   stage: {view.stage}   "
            f"sleep window: {context.get('window')} episodes\n"
            f"ritual metrics over the last window (with flags): "
            f"{json.dumps(m, default=str)}\n"
            f"write-gate decisions (last sleeps): {json.dumps(gates)}\n\n"
            "=== YOUR PREVIOUS BRIEF TO THIS CHILD ===\n"
            + (prev or "(none — this is the first brief)") +
            "\n\n=== PREVIOUS ROOM DECISIONS (frontier estimate, move) ===\n"
            + (json.dumps(rooms, indent=1) if rooms else "(none)") +
            "\n\n=== SOCIETY PLAYBOOK (head) ===\n"
            + (soc.get("playbook") or "")[:1500] +
            "\n=== END ===\nUse tools as needed (read the child's own words "
            "before you speak), then produce the final object.")
    return redact_identifiers(mask_secrets(text))


CRITIQUE_PROMPT = """=== CROSS-VERIFICATION ===
You are parent {role}. Below is the OTHER parent's proposal for the same child
you just studied. Check it strictly for:
(a) answers or leaks — named or paraphrased actions, passes, recipes, scores;
(b) overreach — claims the evidence does not support; a new lesson replacing
    the established one without cause; more than {max_lines} lines;
(c) teaching the metric — any mention of what is measured or how to move it;
(d) persistence — does it reward continued, changing attempts and never
    early stopping?
(e) the frontier estimate — plausible? post-adaptation? confidence honest?
Reply with exactly ONE JSON object:
{{"verdict": "accept|revise|reject", "answers_or_leaks": [...],
 "overreach": [...], "teaches_the_metric": [...],
 "persistence": "ok|weak|violates", "frontier": "plausible|too high|too low",
 "suggestion": "<= 3 lines of concrete repair, or empty"}}

=== OTHER PARENT'S PROPOSAL ===
{proposal}
"""

MERGE_PROMPT = """=== MERGE ===
You are the merging parent. Below are both proposals and both critiques.
Produce the ONE final object (same schema as your final object; no tool
calls). Rules: keep the same core lesson as the previous brief(s) unless both
critiques support a change; remove anything flagged as an answer, a leak,
overreach or metric-teaching; at most {max_lines} lines; speak to the child
directly; the frontier estimate and the move must follow from the cited
evidence, and the confidence must reflect the disagreement between parents.

=== PROPOSAL A ===
{a}
=== PROPOSAL B ===
{b}
=== CRITIQUE OF A (by B) ===
{crit_a}
=== CRITIQUE OF B (by A) ===
{crit_b}
"""


def _proposal_for_prompt(p: dict) -> str:
    return json.dumps(dict(brief=p.get("brief"),
                           frontier_estimate=p.get("frontier_estimate"),
                           curriculum_move=p.get("curriculum_move"),
                           evidence=p.get("evidence"),
                           fallback=p.get("fallback")), indent=1)


# ---------------------------------------------------------------------------
# one parent: the bounded agent loop
# ---------------------------------------------------------------------------
def check_prompt(messages: list) -> None:
    for m in messages:
        ids = identifier_scan(m.get("content") or "")
        if ids:
            raise IdentifierLeak("prompt contains internal identifiers: "
                                 + ",".join(ids))


def _env_int(name: str, default):
    v = _BOOT_ENV.get(name) or os.environ.get(name)
    try:
        return float(v) if v else default
    except ValueError:
        return default


class ParentAgent:
    """One parent's agent loop over the JSON text protocol. Bounded by
    max_tool_calls and by the room's wall-clock deadline (no request starts
    after it); every outgoing prompt is identifier-checked; every final
    object is validated (see validate_output). The proposal transcript
    (system prompt, dashboard, tool calls and results, final) is kept so the
    critique and merge turns argue from the same evidence — replayed under a
    character budget, never re-fetched."""

    def __init__(self, cfg: ProviderConfig, client: ChatClient,
                 max_tool_calls: int = 8, context_chars=None):
        self.cfg = cfg
        self.client = client
        self.max_tool_calls = int(max_tool_calls)
        self.context_chars = int(context_chars or _env_int(
            "PARENT_CRITIQUE_CONTEXT_CHARS", DEFAULT_CRITIQUE_CONTEXT_CHARS))
        self.deadline = None            # absolute clock() value, set by the room
        self.clock = time.monotonic     # injectable for tests (mock clients)
        self.transcript: list = []      # messages of the last propose()

    def _chat(self, messages: list, retries=None) -> str:
        if self.deadline is not None and self.clock() >= self.deadline:
            raise RoomDeadline("room deadline passed; request not sent")
        check_prompt(messages)
        return self.client.chat(messages, max_tokens=self.cfg.max_tokens,
                                retries=retries, deadline=self.deadline)

    def _opening(self, view: ChildView, context: dict, n_parents: int) -> list:
        return [dict(role="system", content=system_prompt(
            self.cfg.role, n_parents, context.get("window") or 32,
            self.max_tool_calls, n_reflections=view.n_reflections())),
            dict(role="user", content=dashboard(view, context))]

    def propose(self, view: ChildView, context: dict, n_parents: int) -> dict:
        tool_log, n_calls, bad_replies = [], 0, 0
        result, error = None, None
        messages: list = []
        try:
            # the dashboard reads shared, possibly torn files: inside the try
            messages = self._opening(view, context, n_parents)
            while True:
                reply = self._chat(messages)
                obj = extract_json(reply)
                # the model's own words re-enter the transcript redacted, so
                # a chatty reply cannot make check_prompt block the next turn;
                # never an EMPTY assistant turn (the Anthropic API rejects it)
                messages.append(dict(role="assistant", content=(
                    redact_identifiers(reply)[:12000].strip()
                    or "(empty reply)")))
                if obj is None or not isinstance(obj, dict):
                    bad_replies += 1
                    if bad_replies > 2:
                        result = fallback_output("no valid JSON after 3 replies")
                        break
                    messages.append(dict(role="user", content=(
                        "Your reply was not a single JSON object. Reply with "
                        "either a tool call or the final object, nothing else.")))
                    continue
                if "tool" in obj and "final" not in obj and "brief" not in obj:
                    if n_calls >= self.max_tool_calls:
                        messages.append(dict(role="user", content=(
                            "TOOL BUDGET EXHAUSTED. Reply ONLY with the final "
                            "object now.")))
                        reply = self._chat(messages)
                        messages.append(dict(role="assistant", content=(
                            redact_identifiers(reply)[:12000].strip()
                            or "(empty reply)")))
                        result = validate_output(
                            extract_json(reply), "\n".join(view.samples_seen),
                            tool_log, reflections=view.reflection_texts(),
                            exact_terms=context.get("leak_terms"))
                        break
                    name = str(obj.get("tool"))
                    args = obj.get("args") if isinstance(obj.get("args"), dict) \
                        else {}
                    n_calls += 1
                    out = view.call(name, args)
                    tool_log.append(f"{name}({json.dumps(args)})")
                    messages.append(dict(role="user", content=(
                        f"TOOL RESULT {name}:\n{out}")))
                    continue
                result = validate_output(obj, "\n".join(view.samples_seen),
                                         tool_log,
                                         reflections=view.reflection_texts(),
                                         exact_terms=context.get("leak_terms"))
                break
        except RoomDeadline as e:
            error = str(e)
            result = fallback_output("deadline")
        except IdentifierLeak as e:
            error = str(e)
            result = fallback_output("prompt blocked: " + error)
        except ProviderError as e:
            error = mask_secrets(str(e))
            result = fallback_output("provider error")
        except Exception as e:  # noqa: BLE001
            error = mask_secrets(f"{type(e).__name__}: {e}")[:300]
            result = fallback_output("agent error")
        self.transcript = messages
        result.update(role=self.cfg.role, provider=self.cfg.provider,
                      model=self.cfg.model, tool_calls=tool_log,
                      n_tool_calls=n_calls, error=error)
        return result

    def _context_messages(self, view: ChildView, context: dict,
                          n_parents: int) -> list:
        """The proposal transcript for a follow-up turn: system prompt,
        dashboard and the final reply are kept whole; the tool exchanges in
        between are truncated to fit self.context_chars. Without a transcript
        (the proposal never started) the opening alone is used."""
        msgs = [dict(m) for m in self.transcript]
        if len(msgs) < 2:
            msgs = self._opening(view, context, n_parents)
        head, middle, tail = msgs[:2], msgs[2:-1], msgs[2:][-1:]
        fixed = sum(len(m["content"]) for m in head + tail)
        budget = max(0, self.context_chars - fixed)
        if middle:
            per = budget // len(middle)
            if per < 400:
                middle = [dict(role="user", content=(
                    "(tool exchanges omitted for length; the final object "
                    "below was produced from them)"))]
            else:
                middle = [dict(m, content=(m["content"] if len(m["content"])
                                           <= per else m["content"][:per]
                                           + "\n... (truncated for length)"))
                          for m in middle]
        return head + middle + tail

    def critique(self, other: dict, view=None, context=None,
                 n_parents: int = 2) -> dict:
        """Cross-verification of the OTHER parent's proposal, argued from this
        parent's own evidence (its transcript); no tools, no retries."""
        prompt = CRITIQUE_PROMPT.format(role=self.cfg.role,
                                        max_lines=MAX_BRIEF_LINES,
                                        proposal=_proposal_for_prompt(other))
        try:
            if view is not None:
                msgs = self._context_messages(view, context or {}, n_parents)
            else:                                   # no child state at hand
                msgs = [dict(role="system", content=PARENT_BOOT)]
            msgs.append(dict(role="user", content=redact_identifiers(prompt)))
            reply = self._chat(msgs, retries=0)
        except Exception as e:  # noqa: BLE001
            return dict(verdict="unavailable", error=mask_secrets(str(e))[:300],
                        by=self.cfg.role)
        obj = extract_json(reply)
        if not isinstance(obj, dict):
            obj = dict(verdict="unparsed", raw=reply[:1500])
        obj["by"] = self.cfg.role
        obj["verdict"] = str(obj.get("verdict") or "unparsed").lower()
        obj = safe_obj(obj)
        # the critique is logged to the parent ledger: a field that quotes,
        # paraphrases or mentions a private reflection is redacted here
        if view is not None:
            obj = scrub_reflections(obj, view.reflection_texts(),
                                    "\n".join(view.samples_seen))
        return obj

    def merge(self, view: ChildView, context: dict, a: dict, b: dict,
              crit_a: dict, crit_b: dict, n_parents: int) -> dict:
        prompt = MERGE_PROMPT.format(
            max_lines=MAX_BRIEF_LINES, a=_proposal_for_prompt(a),
            b=_proposal_for_prompt(b), crit_a=json.dumps(crit_a, indent=1),
            crit_b=json.dumps(crit_b, indent=1))
        try:
            msgs = self._context_messages(view, context, n_parents)
            msgs.append(dict(role="user", content=redact_identifiers(prompt)))
            reply = self._chat(msgs, retries=0)
        except Exception as e:  # noqa: BLE001
            out = fallback_output("merge provider error")
            out["error"] = mask_secrets(str(e))[:300]
            return out
        ev = list(dict.fromkeys((a.get("evidence") or []) +
                                (b.get("evidence") or [])))
        return validate_output(extract_json(reply), "\n".join(view.samples_seen),
                               ev, reflections=view.reflection_texts(),
                               exact_terms=context.get("leak_terms"))


# ---------------------------------------------------------------------------
# the room: two parents, cross-verification, one delivered brief
# ---------------------------------------------------------------------------
class ParentRoom:
    """Runs on ONE child's state, at a sleep boundary only:
      exchange 1  each parent proposes (bounded agent loop, own tool calls)
      exchange 2  each parent critiques the other's proposal (no tools)
      exchange 3  the merger (PARENT_MERGER, default A) writes the delivered
                  brief from both proposals and both critiques
    Single-parent mode (one config): exchange 1 only; delivered = proposal.
    WALL CLOCK: run() sets a deadline (room_timeout_s from now); no request
    starts past it; a critique or merge phase is skipped when less than
    min_phase_s remains, and the best validated proposal is delivered instead
    (FALLBACK with reason "deadline" if none validated). Everything is logged
    with prompt_version, provider and model names — no keys, no base URLs,
    no identifiers."""

    def __init__(self, configs: list, clients=None, max_tool_calls=None,
                 merger=None, room_timeout_s=None, min_phase_s=None,
                 clock=None):
        if not configs:
            raise ValueError("ParentRoom needs at least one ProviderConfig")
        self.configs = list(configs)[:2]
        clients = clients or {}
        self.agents = []
        mtc = int(max_tool_calls or _BOOT_ENV.get("PARENT_MAX_TOOL_CALLS")
                  or os.environ.get("PARENT_MAX_TOOL_CALLS") or 8)
        for cfg in self.configs:
            client = clients.get(cfg.role) or make_client(cfg)
            self.agents.append(ParentAgent(cfg, client, mtc))
        self.merger = (merger or _BOOT_ENV.get("PARENT_MERGER") or "A").upper()
        self.room_timeout_s = float(room_timeout_s or _env_int(
            "PARENT_ROOM_TIMEOUT_S", DEFAULT_ROOM_TIMEOUT_S))
        self.min_phase_s = float(min_phase_s if min_phase_s is not None
                                 else _env_int("PARENT_ROOM_MIN_PHASE_S",
                                               DEFAULT_MIN_PHASE_S))
        self.clock = clock or time.monotonic

    @classmethod
    def from_env(cls, env=None, fallback_local=None, clients=None,
                 max_tool_calls=None) -> "ParentRoom":
        """Configs from PARENT_* env; with none, fall back to the local
        vLLM server given as (base_url, model) — the same server the
        baseline parent_brief uses — so `--parent-mode agentic` works with
        no extra environment."""
        cfgs = configs_from_env(env)
        if not cfgs and fallback_local and fallback_local[0]:
            cfgs = [ProviderConfig("local", model=fallback_local[1],
                                   base_url=fallback_local[0], role="A")]
        if not cfgs:
            raise RuntimeError("no parent configured: set PARENT_PROVIDER (or "
                               "PARENT_A_PROVIDER/PARENT_B_PROVIDER) or pass "
                               "--parent-url")
        return cls(cfgs, clients=clients, max_tool_calls=max_tool_calls)

    def public_parents(self) -> list:
        return [c.public() for c in self.configs]

    @staticmethod
    def _best_proposal(pa: dict, pb: dict, critiques: dict, reason: str,
                       prefer: str) -> dict:
        """Deliver a proposal that passed validation and was not rejected by
        its critic (the merger's own first), else FALLBACK with `reason`."""
        ra, rb = pa.get("role", "A"), pb.get("role", "B")
        order = [(pa, critiques.get(f"{rb}_on_{ra}") or {}),
                 (pb, critiques.get(f"{ra}_on_{rb}") or {})]
        if prefer == rb:
            order.reverse()
        for p, crit in order:
            if not p.get("fallback") and crit.get("verdict") != "reject":
                m = dict(p)
                m["merged_from"] = f"proposal {p.get('role')} ({reason})"
                return m
        m = fallback_output(reason)
        m["merged_from"] = f"fallback ({reason})"
        return m

    def run(self, view: ChildView, context: dict) -> dict:
        n = len(self.agents)
        deadline = self.clock() + self.room_timeout_s
        for ag in self.agents:
            ag.deadline, ag.clock = deadline, self.clock

        def left():
            return deadline - self.clock()

        skipped = []
        proposals = collections.OrderedDict()
        for ag in self.agents:                             # exchange 1
            if left() <= 0:
                p = fallback_output("deadline")
                p.update(role=ag.cfg.role, provider=ag.cfg.provider,
                         model=ag.cfg.model, tool_calls=[], n_tool_calls=0,
                         error="room deadline passed before the proposal")
                skipped.append(f"proposal {ag.cfg.role}")
            else:
                p = ag.propose(view, context, n)
            proposals[ag.cfg.role] = p
        critiques, exchanges = {}, 1
        if n == 1:
            merged = dict(proposals[self.agents[0].cfg.role])
            merged["merged_from"] = "single-parent"
        else:
            a, b = self.agents[0], self.agents[1]
            pa, pb = proposals[a.cfg.role], proposals[b.cfg.role]
            merger = a if self.merger == a.cfg.role else b
            if proposals[merger.cfg.role].get("error"):
                merger = b if merger is a else a            # merger is dead
            if left() < self.min_phase_s:
                skipped += ["critiques", "merge"]
                merged = self._best_proposal(pa, pb, {}, "deadline",
                                             merger.cfg.role)
            else:                                            # exchange 2
                critiques[f"{a.cfg.role}_on_{b.cfg.role}"] = \
                    a.critique(pb, view, context, n)
                critiques[f"{b.cfg.role}_on_{a.cfg.role}"] = \
                    b.critique(pa, view, context, n)
                exchanges = 2
                if left() < self.min_phase_s:
                    skipped.append("merge")
                    merged = self._best_proposal(pa, pb, critiques, "deadline",
                                                 merger.cfg.role)
                else:                                        # exchange 3
                    merged = merger.merge(
                        view, context, pa, pb,
                        critiques[f"{b.cfg.role}_on_{a.cfg.role}"],
                        critiques[f"{a.cfg.role}_on_{b.cfg.role}"], n)
                    exchanges = 3
                    merged["merged_from"] = f"merge by {merger.cfg.role}"
                    if merged.get("fallback"):
                        # degrade gracefully: a validated proposal not
                        # rejected by its critic beats the fallback
                        merged = self._best_proposal(
                            pa, pb, critiques, "merge failed", merger.cfg.role)
            merged.setdefault("role", merger.cfg.role)
            merged.setdefault("provider", merger.cfg.provider)
            merged.setdefault("model", merger.cfg.model)
        assert exchanges <= MAX_EXCHANGES, "room dialogue bound violated"
        return dict(prompt_version=PROMPT_VERSION,
                    brief_prompt_version=BRIEF_PROMPT_VERSION,
                    parents=self.public_parents(), proposals=dict(proposals),
                    critiques=critiques, merged=merged,
                    delivered=merged["delivered_text"],
                    hits=merged.get("hits") or [],
                    fallback=bool(merged.get("fallback")),
                    exchanges=exchanges, tool_calls=list(view.calls),
                    skipped=skipped, deadline_hit=bool(skipped),
                    room_timeout_s=self.room_timeout_s,
                    elapsed_s=round(self.room_timeout_s - left(), 1))


# ---------------------------------------------------------------------------
# logging: child's parent ledger, society ledger, bounded playbook
# ---------------------------------------------------------------------------
def _compact_proposal(p: dict) -> dict:
    keys = ("role", "provider", "model", "brief", "frontier_estimate",
            "curriculum_move", "evidence", "society_note", "fallback",
            "fallback_reason", "hits", "tool_calls", "n_tool_calls", "error",
            "merged_from", "truncated")
    return {k: p.get(k) for k in keys if k in p}


@contextlib.contextmanager
def _locked(lock_path: str):
    """Exclusive fcntl lock (several lives on one node share the society
    files). Best-effort: without fcntl (non-Unix) it is a no-op."""
    if fcntl is None:  # pragma: no cover
        yield
        return
    os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
    with open(lock_path, "a") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def log_room(view: ChildView, result: dict, metrics: dict,
             ledger_dir=None, society_dir=None) -> None:
    """Append the room's record to the child's parent_ledger.jsonl and to
    the parental society ledger; append the society note to the bounded
    playbook. All text is secret-masked and identifier-redacted; the shared
    society files are written under a lock. A room that died (result has
    `error`) additionally gets a `room_error` row in the child's ledger."""
    # defence in depth for the private-reflection invariant: nothing written
    # to a ledger may carry reflection text (critiques, evidence, notes,
    # error strings) — the count is the only thing recorded
    refl = view.reflection_texts()
    shown = "\n".join(view.samples_seen)
    merged = scrub_reflections(_compact_proposal(result["merged"]), refl, shown)
    row = dict(kind="agentic_room", source="parent_room",
               child_stage=view.stage, prompt_version=PROMPT_VERSION,
               brief_prompt_version=BRIEF_PROMPT_VERSION,
               parents=result["parents"],
               proposals={r: scrub_reflections(_compact_proposal(p), refl, shown)
                          for r, p in result["proposals"].items()},
               critiques=scrub_reflections(result["critiques"], refl, shown),
               merged=merged,
               text=result["delivered"][:1900], hits=result["hits"],
               fallback=result["fallback"], exchanges=result["exchanges"],
               skipped=result.get("skipped") or [],
               elapsed_s=result.get("elapsed_s"),
               metrics=_compact_metrics(metrics),
               # how many private reflection rows the room could see — the
               # count only, never their content
               n_reflection_rows_visible=view.n_reflections())
    if result.get("error"):
        row["error"] = result["error"]
    row = safe_obj(json.loads(json.dumps(row, default=str)))
    child_ledger = ParentLedger(ledger_dir or view.life_dir)
    child_ledger.append(**row)
    if result.get("error"):
        child_ledger.append(kind="room_error", source="harness",
                            child_stage=view.stage, prompt_version=PROMPT_VERSION,
                            error=safe_text(str(result["error"]))[:300])
    sd = os.path.expanduser(society_dir or view.society_dir)
    os.makedirs(sd, exist_ok=True)
    srow = dict(ts=time.time(), kind="room", child=view.child_id,
                stage=view.stage, prompt_version=PROMPT_VERSION,
                parents=result["parents"], metrics=_compact_metrics(metrics),
                frontier_estimate=merged.get("frontier_estimate"),
                curriculum_move=merged.get("curriculum_move"),
                brief=result["delivered"][:1900], fallback=result["fallback"],
                skipped=result.get("skipped") or [],
                critique_verdicts={k: v.get("verdict")
                                   for k, v in result["critiques"].items()},
                proposal_frontiers={r: p.get("frontier_estimate")
                                    for r, p in result["proposals"].items()})
    line = json.dumps(safe_obj(json.loads(json.dumps(srow, default=str))))
    note = merged.get("society_note")
    with _locked(os.path.join(sd, ".society.lock")):
        _append_line(os.path.join(sd, "ledger.jsonl"), line)
        if note:
            append_playbook_note(sd, f"[{view.child_id} {view.stage}] {note}",
                                 lock=False)


def _append_line(path: str, line: str) -> None:
    """Append one JSONL record. If a previous writer died mid-line (no
    trailing newline), terminate that fragment first so the new record is
    not glued to it (which would lose both to _read_jsonl)."""
    need_nl = False
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            need_nl = f.read(1) != b"\n"
    with open(path, "a") as f:
        f.write(("\n" if need_nl else "") + line + "\n")


def _compact_metrics(m: dict) -> dict:
    keys = ("n_episodes", "ritual", "flags", "rehearsal_rate",
            "modal_first_act_share", "predict_sd", "note_consecutive_jaccard",
            "recall_modal_share")
    return {k: m.get(k) for k in keys if k in (m or {})}


def append_playbook_note(society_dir: str, line: str, max_lines: int = 80,
                         *, lock: bool = True) -> None:
    """BOUNDED playbook: keeps the header and the last `max_lines` notes.
    Read-modify-write under the society lock (lock=False when the caller
    already holds it — flock is not re-entrant across file objects)."""
    p = os.path.join(society_dir, "playbook.md")
    header = "# Parental society playbook (bounded; newest last)\n"
    ctx = _locked(os.path.join(society_dir, ".society.lock")) if lock \
        else contextlib.nullcontext()
    with ctx:
        notes = []
        if os.path.exists(p):
            with open(p, errors="replace") as f:
                for l in f.read().splitlines():
                    if l.startswith("- "):
                        notes.append(safe_text(l))  # re-redact on every rewrite
        notes.append("- " + safe_text(" ".join(line.split()))[:300])
        notes = notes[-max_lines:]
        tmp = p + f".tmp{os.getpid()}"
        with open(tmp, "w") as f:
            f.write(header + "\n".join(notes) + "\n")
        os.replace(tmp, p)


# ---------------------------------------------------------------------------
# run_life_v2 adapter: same signature and return shape as parent_brief
# ---------------------------------------------------------------------------
def parent_brief_agentic(life_dir: str, rows: list, sleep_dir: str,
                         parent_url, model_name, last_episodes: int = 32,
                         *, room=None, society_dir=None, ledger_dir=None,
                         out_dir=None, extra_leak_terms=None) -> dict:
    """Drop-in for parent_brief.parent_brief (run_life_v2 --parent-mode
    agentic). Measures ritual/rehearsal exactly as the baseline does, runs the
    ParentRoom, writes <sleep_dir>/parent_brief.txt (the child reads it at the
    next wake) and parent_brief.json (idempotency + the same meta shape:
    metrics, intervened, text, hits, prompt_version, parent_model). Returns
    the meta dict. Keyword-only extras exist for tests and smoke runs.

    NEVER RAISES INTO THE LIFE: any exception while building or running the
    room (provider down, corrupt shared-ledger line, bad JSON on disk)
    delivers FALLBACK + REHEARSAL_TAIL, records `room_error` in the child's
    parent ledger and returns a complete meta; a failure while logging is
    recorded in meta["log_error"]."""
    out_dir = out_dir or sleep_dir
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "parent_brief.txt")
    meta_p = os.path.join(out_dir, "parent_brief.json")
    if os.path.exists(meta_p):
        try:
            return _read_json(meta_p)
        except ValueError:
            pass                        # torn meta: redo this sleep's brief
    view = ChildView(life_dir, rows=rows, sleep_dir=sleep_dir,
                     society_dir=society_dir)
    try:
        prev_text = view.previous_brief()
    except Exception:  # noqa: BLE001 — unreadable earlier brief
        prev_text = ""
    m = ritual_metrics(rows, last_episodes, brief_text=prev_text)
    m["rehearsal_rate"] = round(rehearsal_rate(rows, prev_text, last_episodes), 3)
    meta = dict(metrics=m, intervened=False, text=None, hits=None,
                prompt_version=PROMPT_VERSION, mode="agentic")
    only_ritual = (os.environ.get("PARENT_AGENTIC_ONLY_RITUAL")
                   or _BOOT_ENV.get("PARENT_AGENTIC_ONLY_RITUAL")) == "1"
    if only_ritual and not m.get("ritual"):
        ParentLedger(ledger_dir or life_dir).append(
            kind="ritual_check", source="harness",
            child_stage=os.path.basename(sleep_dir), metrics=m)
        with open(meta_p, "w") as f:
            json.dump(meta, f, indent=1)
        return meta
    parents = []
    try:
        room = room or ParentRoom.from_env(fallback_local=(parent_url,
                                                           model_name))
        parents = room.public_parents()
        context = dict(child_id=view.child_id, stage=view.stage, metrics=m,
                       prev_brief=prev_text, window=last_episodes,
                       # the gym's leak terms (held-out ids / families and
                       # the window's reference answers): exact-substring
                       # hits in any delivered text -> FALLBACK
                       leak_terms=list(extra_leak_terms or []))
        result = room.run(view, context)
    except Exception as e:  # noqa: BLE001 — the room must never kill the life
        result = room_error_result(mask_secrets(
            f"{type(e).__name__}: {e}")[:300], parents)
    text = result["delivered"]
    with open(out, "w") as f:
        f.write(text.strip()[:1900])
    merged = result["merged"]
    meta.update(intervened=True, text=text, hits=result["hits"],
                parent_model=", ".join(p["model"] for p in result["parents"]),
                parents=result["parents"],
                frontier_estimate=merged.get("frontier_estimate"),
                curriculum_move=merged.get("curriculum_move"),
                fallback=result["fallback"], exchanges=result["exchanges"],
                merged_from=merged.get("merged_from"),
                skipped=result.get("skipped") or [],
                room_error=result.get("error"))
    try:
        log_room(view, result, m, ledger_dir=ledger_dir, society_dir=society_dir)
    except Exception as e:  # noqa: BLE001
        meta["log_error"] = mask_secrets(f"{type(e).__name__}: {e}")[:300]
        try:
            ParentLedger(ledger_dir or life_dir).append(
                kind="room_error", source="harness", child_stage=view.stage,
                error=safe_text(meta["log_error"]))
        except Exception:  # noqa: BLE001
            pass
    meta = safe_obj(json.loads(json.dumps(meta, default=str)))
    with open(meta_p, "w") as f:
        json.dump(meta, f, indent=1)
    return meta


def room_error_result(error: str, parents=None) -> dict:
    """The room's result shape when the room itself raised: FALLBACK is
    delivered, nothing else is claimed."""
    merged = fallback_output("room_error")
    merged["error"] = error
    merged["merged_from"] = "fallback (room error)"
    return dict(prompt_version=PROMPT_VERSION,
                brief_prompt_version=BRIEF_PROMPT_VERSION,
                parents=list(parents or []), proposals={}, critiques={},
                merged=merged, delivered=merged["delivered_text"], hits=[],
                fallback=True, exchanges=0, tool_calls=[], skipped=["room"],
                deadline_hit=False, error=error)


# ---------------------------------------------------------------------------
# mock script for --mock smoke runs (no network, no key)
# ---------------------------------------------------------------------------
_MOCK_SMOKE_SCRIPT = [
    json.dumps(dict(tool="ledger_tail", args=dict(n_episodes=4))),
    json.dumps(dict(tool="metrics", args={})),
    json.dumps(dict(final=dict(
        brief=("You open every episode the same way and expect the same "
               "result, whatever the program in front of you.\nBefore you act, "
               "name one feature of THIS program and say what it makes you "
               "expect, with a range.\nWhen the outcome disagrees, write which "
               "belief was wrong — not just that you were surprised.\nRun one "
               "deliberate deviation per episode and predict its effect first; "
               "keep going after a flat result, changing something each time."),
        frontier_estimate=dict(text="Can vary its opening move by a named "
                                    "program feature after a few episodes of "
                                    "practice.", confidence=0.4),
        curriculum_move=dict(move="sharpen", reason="same lesson as before; "
                                                    "the child has begun to "
                                                    "restate it"),
        evidence=["ledger_tail(4)", "metrics()"],
        society_note="Children lock into one opening move; naming a program "
                     "feature before acting is the lever."))),
]
_MOCK_CRITIQUE = json.dumps(dict(verdict="accept", answers_or_leaks=[],
                                 overreach=[], teaches_the_metric=[],
                                 persistence="ok", frontier="plausible",
                                 suggestion=""))
_MOCK_MERGE = _MOCK_SMOKE_SCRIPT[-1]


# ---------------------------------------------------------------------------
# CLI: smoke invocation against a life directory (see gpu/run_parent_agent.sh)
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=(
        "Smoke-run the agentic parent room on one life directory. Writes to "
        "<life>/parent_smoke_<ts>/ (not a sleep_* dir, so the child never "
        "reads it) unless --commit."))
    ap.add_argument("--life-dir", required=True)
    ap.add_argument("--sleep-dir", default=None,
                    help="default: the latest sleep_* dir of the life")
    ap.add_argument("--window", type=int, default=32)
    ap.add_argument("--mock", action="store_true",
                    help="use the canned MockChatClient (no network, no key)")
    ap.add_argument("--commit", action="store_true",
                    help="write into the real sleep dir, child ledger and "
                         "society ledger (default: sandboxed smoke dir)")
    ap.add_argument("--parent-url", default=None,
                    help="local vLLM fallback if no PARENT_* env is set")
    ap.add_argument("--parent-model", default=None)
    args = ap.parse_args()

    life = os.path.abspath(os.path.expanduser(args.life_dir))
    sleeps = sorted(d for d in os.listdir(life) if d.startswith("sleep_"))
    sleep_dir = os.path.abspath(os.path.expanduser(args.sleep_dir)) \
        if args.sleep_dir else (os.path.join(life, sleeps[-1]) if sleeps
                                else os.path.join(life, "sleep_0000"))
    rows = _read_jsonl(os.path.join(life, "ledger.jsonl"))
    if args.mock:
        cfgs = [ProviderConfig("mock", role="A", model="mock-A"),
                ProviderConfig("mock", role="B", model="mock-B")]
        room = ParentRoom(cfgs)
    else:
        room = ParentRoom.from_env(fallback_local=(args.parent_url,
                                                   args.parent_model))
    print("parents:", json.dumps(room.public_parents()), flush=True)
    if args.commit:
        out_dir = ledger_dir = society_dir = None
    else:
        out_dir = os.path.join(life, f"parent_smoke_{int(time.time())}")
        ledger_dir = out_dir
        society_dir = os.path.join(out_dir, "society")
    meta = parent_brief_agentic(life, rows, sleep_dir, args.parent_url,
                                args.parent_model, args.window, room=room,
                                society_dir=society_dir, ledger_dir=ledger_dir,
                                out_dir=out_dir)
    show = {k: meta.get(k) for k in ("intervened", "hits", "fallback",
                                     "exchanges", "merged_from",
                                     "frontier_estimate", "curriculum_move",
                                     "parents")}
    show["metrics"] = _compact_metrics(meta.get("metrics") or {})
    print(json.dumps(show, indent=1))
    print("=== DELIVERED BRIEF ===")
    print(meta.get("text") or "(none)")
    print("SMOKE_DONE out_dir=" + (out_dir or sleep_dir))


if __name__ == "__main__":
    main()
