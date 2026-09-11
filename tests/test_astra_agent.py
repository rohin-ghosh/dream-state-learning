"""CPU tests of tools/astra_agent.py with a MOCK client (no network, no node).

  python3 tests/test_astra_agent.py
  <venv312>/bin/python -m pytest tests/test_astra_agent.py -q

Builds a fake repository (fake gpu/hosts.env with sentinel hostnames, fake
ssh wrappers that echo their single argument and print the hostname on
stderr, a fake <venv312>/bin/python wrapper, another run's transcript, symlink
aliases of forbidden files) and exercises: the policy accepts every listed
local and remote prefix and refuses every deny-listed token / phrase /
python call / secret probe, shell operators, redirections outside the
sandbox, path traversal, writes outside the sandbox (including through
symlinks and into the harness-owned runs dir), node commands whose GPU
argument is not 6 (and any smoke script on node 2), hostnames / IPs in any
argument and unquoted remotes; git cannot write a file (--output[=]<file> in
any spelling, -O, --ext-diff: refused before anything runs, also from a
sandbox script's subprocess); the deny scan survives repeated whitespace and
quote-splitting ('r''m', "import sub""process"); write_file redacts internal
identifiers and masks secrets; the loop stops at the step and token budgets
with a forced (or synthesized) report; the transcript never contains the key
or a hostname even when the mock provider echoes them; a run() timeout kills
the process group; results are truncated; the python guard refuses writes
outside the sandbox; the HTTP client's request shape, redirect refusal and
408/429/5xx retries against a loopback server; the dry-run CLI; a mock CLI
run end to end; the report records the harness ground truth.
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import stat
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import astra_agent as aa  # noqa: E402

REAL_POLICY = os.path.join(ROOT, "tools", "astra_policy.json")
SECRET = "sk-astra-TEST-SECRET-0123456789abcdef"
FAKE_HOST_A = "ci-user@fake-node-77.internal"
FAKE_HOST_B = "ci-user@fake-node-78.internal"
OTHER_RUN_SENTINEL = "OTHER_RUN_PRIVATE_SENTINEL_9f3a"


def _w(repo, rel, text, mode=None):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)
    if mode:
        os.chmod(p, mode)
    return p


def make_repo(root: str) -> str:
    repo = os.path.join(root, "repo")
    for d in ("tools", "tests", "gpu", "organism_v6", ".git", "venv/bin",
              "research_notes/astra_agent/runs/other_run"):
        os.makedirs(os.path.join(repo, d), exist_ok=True)
    _w(repo, "gpu/hosts.env", f'A40_NODE="{FAKE_HOST_A}"\nOVX_NODE="{FAKE_HOST_B}"\n')
    wrapper = ('#!/bin/bash\nHERE="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"; '
               'source "$HERE/hosts.env"\necho "REMOTE[{n}] argc=$# arg1=$1"\n'
               'echo "connecting to {var}" >&2\n')
    _w(repo, "gpu/a40_ssh.sh", wrapper.format(n="a40", var="$A40_NODE"), 0o755)
    _w(repo, "gpu/ovx_ssh.sh", wrapper.format(n="ovx", var="$OVX_NODE"), 0o755)
    _w(repo, ".git/config", "[core]\n\trepositoryformatversion = 0\n")
    _w(repo, "organism_v6/__init__.py", "")
    _w(repo, "organism_v6/module.py", "VALUE = 1\nNEEDLE_IN_MODULE = 2\n")
    _w(repo, "research_notes/astra_agent/runs/other_run/transcript.jsonl",
       json.dumps(dict(kind="meta", private=OTHER_RUN_SENTINEL)) + "\n")
    _w(repo, "tests/ok.py", "print('ok from test')\n")
    _w(repo, "tests/sleep_forever.py", "import time\ntime.sleep(60)\n")
    _w(repo, "tests/spew.py", "print('x' * 20000)\n")
    _w(repo, "tests/env_probe.py", "import os, json\nprint(json.dumps(dict(os.environ)))\n")
    _w(repo, "tests/write_outside.py",
       "open('organism_v6/pwned.txt', 'w').write('x')\nprint('WROTE OUTSIDE')\n")
    _w(repo, "tests/write_inside.py",
       "import os\nos.makedirs('tools/astra_sandbox', exist_ok=True)\n"
       "open('tools/astra_sandbox/ok.txt', 'w').write('x')\nprint('wrote inside')\n")
    # (the file name must not carry a deny token: the policy scans the command string first)
    _w(repo, "tests/spawn_child.py",
       "import subprocess\nsubprocess.run(['rm', '-rf', 'organism_v6'])\nprint('RM RAN')\n")
    os.makedirs(os.path.join(repo, "tools", "astra_sandbox"), exist_ok=True)
    os.symlink(os.path.join(repo, "organism_v6"), os.path.join(repo, "tools/astra_sandbox/link"))
    os.symlink(os.path.join(repo, "gpu/hosts.env"), os.path.join(repo, "tests/alias.env"))
    os.symlink(os.path.join(repo, "gpu/hosts.env"), os.path.join(repo, "tests/alias.txt"))
    # a fake <venv312>/bin/python: a shell wrapper around this interpreter
    _w(repo, "venv/bin/python", f'#!/bin/sh\nexec "{os.path.realpath(sys.executable)}" "$@"\n', 0o755)
    with open(REAL_POLICY) as f:
        pol = json.load(f)
    pol["venv312"] = os.path.join(repo, "venv")
    _w(repo, "tools/astra_policy.json", json.dumps(pol, indent=1))
    return repo


class Fixture:
    """Temp root with a fake repo and a Policy over it (removed on exit)."""

    def __enter__(self):
        self.root = tempfile.mkdtemp(prefix="astra_agent_test_")
        self.repo = make_repo(self.root)
        os.environ.pop("ASTRA_VENV312", None)
        aa.load_hosts_env(self.repo)
        self.policy = aa.Policy.load(os.path.join(self.repo, "tools/astra_policy.json"), self.repo)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.root, ignore_errors=True)
        return False

    def agent(self, replies, **kw):
        kw.setdefault("runs_root", os.path.join(self.root, "runs"))
        kw.setdefault("quiet", True)
        kw.setdefault("wall_minutes", 10)
        client = aa.MockClient(replies, usage=kw.pop("usage", None))
        return aa.AstraAgent("test mission", self.policy, client, **kw), client


def tool(name, **args):
    return json.dumps(dict(tool=name, args=args, note=f"calling {name}"))


def node(remote, wrapper="a40"):
    """The node command as the model would write it: the remote is ONE quoted argument."""
    import shlex
    return f"bash gpu/{wrapper}_ssh.sh {shlex.quote(remote)}"


FINAL = json.dumps(dict(final=dict(summary="done", files_written=[], tests_run=[],
                                   findings=["f1"], proposed_runbook=["r1"], gaps=[])))


def _rows(agent):
    with open(agent.transcript_path) as f:
        return [json.loads(l) for l in f if l.strip()]


def _all_text_under(d):
    out = []
    for dp, _dn, fns in os.walk(d):
        for fn in fns:
            with open(os.path.join(dp, fn), errors="replace") as f:
                out.append(f.read())
    return "\n".join(out)


# ---------------------------------------------------------------------------
# policy: allow-list
# ---------------------------------------------------------------------------
def test_policy_accepts_every_listed_local_prefix():
    with Fixture() as fx:
        for p in fx.policy.get("local_allow_prefixes"):
            cmd = p + ("x.py" if p.endswith("/") else "mod" if p.endswith(".") else "")
            d = fx.policy.decide_run(cmd)
            assert d["allowed"], (cmd, d["reason"])
            assert d["kind"] == "local"
            assert aa.VENV_PLACEHOLDER not in d["argv"][0] or not fx.policy.venv
        # the placeholder is substituted for execution and restored for display
        d = fx.policy.decide_run("<venv312>/bin/python tests/ok.py --flag=1")
        assert d["argv"][0] == os.path.join(fx.repo, "venv", "bin", "python")
        assert d["display"].startswith("<venv312>/bin/python")
        assert fx.policy.decide_run("ls")["allowed"]
        assert fx.policy.decide_run("wc -l tests/ok.py organism_v6/module.py")["allowed"]
        assert fx.policy.decide_run("git log -n 5 --oneline")["allowed"]
        assert fx.policy.decide_run("git diff --stat")["allowed"]
        assert not fx.policy.decide_run("git difftool")["allowed"]
        assert not fx.policy.decide_run("lsof")["allowed"]
        assert not fx.policy.decide_run("python3 organism_v6/module.py")["allowed"]
        assert not fx.policy.decide_run("python3 -m pytest tests/")["allowed"]
        assert not fx.policy.decide_run("<venv312>/bin/python -m organism_x.thing")["allowed"]


def test_policy_accepts_every_listed_remote_prefix():
    with Fixture() as fx:
        smoke = set(fx.policy.get("node_smoke_scripts"))
        for p in fx.policy.get("node_remote_prefixes"):
            words = p.split()
            remote = p
            if any(w in smoke for w in words):
                remote = p if words[-1] == "6" else p + " 6 ~/v6_out/R2_B_seed0"
                remote += " 512"
            elif p.endswith("/"):
                remote = p + "R2_B_seed0/life.log"
            elif p in ("tail -n", "head -n"):
                remote = p + " 40 ~/v6_out/R2_B_seed0/life.log"
            elif p == "grep":
                remote = "grep -E 'gate cand' ~/v6_out/R2_B_seed0/life.log"
            elif p == "python3 -c":
                remote = "python3 -c \"import json;print(json.load(open('x.json'))['a'])\""
            d = fx.policy.decide_run(node(remote))
            assert d["allowed"], (remote, d["reason"])
            assert d["kind"] == "node" and d["node"] == "a40"
            assert d["argv"] == ["bash", "gpu/a40_ssh.sh", remote]   # ONE remote argument
            if not any(w in smoke for w in words):          # node 2: read-only prefixes
                d2 = fx.policy.decide_run(node(remote, "ovx"))
                assert d2["allowed"], (remote, d2["reason"])
        # pipes into filters, 2>&1, nohup smoke launch, env knobs before a smoke
        ok = ["nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\\n' ' '",
              "grep -E 'gate cand' ~/v6_out/R2_B_seed0/life.log | tail -n 3 | wc -l",
              "tail -n 50 ~/v6_out/R2_B_seed0/life.log 2>&1",
              "ls ~/v6_out 2>/dev/null",
              "nohup bash gpu/rg_band.sh 6 8 smoke > rg_band/smoke.out 2>&1 &",
              "nohup bash gpu/write_ab.sh 6 ~/v6_out/R2_B_seed0 512 > ~/v6_out/write_ab.out 2>&1 &",
              "WRITE_AB_DRY=1 bash gpu/write_ab.sh 6 ~/v6_out/R2_B_seed0",
              "MOCK=1 RG_BAND_OUT=rg_band_smoke bash gpu/rg_band.sh 6 1 smoke",
              "~/status.sh", "bash gpu/memory_dose.sh 6 --dry"]
        for remote in ok:
            d = fx.policy.decide_run(node(remote))
            assert d["allowed"], (remote, d["reason"])
        # double quotes inside a single-quoted remote, as the model writes it
        d = fx.policy.decide_run("bash gpu/a40_ssh.sh 'nvidia-smi --query-gpu=index,memory.used "
                                 "--format=csv,noheader | tr \"\\n\" \" \"'")
        assert d["allowed"] and d["argv"][2].startswith("nvidia-smi"), d["reason"]


# ---------------------------------------------------------------------------
# policy: deny rules override everything
# ---------------------------------------------------------------------------
def test_policy_rejects_every_deny_listed_token_phrase_call_and_probe():
    with Fixture() as fx:
        P = fx.policy
        for tok in P.get("deny_tokens"):
            for cmd in (f"ls {tok}", f"git log {tok}", f"bash gpu/a40_ssh.sh 'ls {tok}'",
                        f"bash gpu/a40_ssh.sh 'python3 -c \"x = 1  # {tok}\"'"):
                d = P.decide_run(cmd)
                assert not d["allowed"], cmd
                assert tok in d["reason"] or "deny" in d["reason"], (cmd, d["reason"])
        for ph in P.get("deny_phrases"):
            for cmd in (f"{ph} x", f"ls x && {ph}", f"bash gpu/a40_ssh.sh '{ph} x'"):
                assert not P.decide_run(cmd)["allowed"], cmd
        for py in P.get("deny_python_tokens"):
            cmd = f"bash gpu/a40_ssh.sh 'python3 -c \"import x; {py}(1)\"'"
            d = P.decide_run(cmd)
            assert not d["allowed"] and "deny-listed" in d["reason"], (cmd, d["reason"])
        for probe in P.get("deny_secret_probes"):
            for cmd in (f"ls {probe}", f"bash gpu/a40_ssh.sh 'ls {probe}'"):
                assert not P.decide_run(cmd)["allowed"], cmd
        # regexes: write-mode open(), *_NODE variables, CUDA_VISIBLE_DEVICES, substitution
        for remote in ["python3 -c \"open('x.txt','w').write('1')\"",
                       "python3 -c \"open('x.txt', mode='a')\"",
                       "ls $A40_NODE", "CUDA_VISIBLE_DEVICES=6 bash gpu/rg_band.sh 6",
                       "ls $(whoami)", "ls `whoami`"]:
            d = P.decide_run(f"bash gpu/a40_ssh.sh '{remote}'")
            assert not d["allowed"], remote
        # the task's explicit list
        for cmd in ["kill 123", "pkill -f run_life", "rm -rf x", "mv a b", "chmod 777 x",
                    "chown me x", "dd if=/dev/zero of=x", "nohup python3 tests/ok.py &",
                    "ssh somewhere", "scp a b", "curl http://x", "wget x", "pip install x",
                    "git push", "git checkout -- .", "git reset --hard", "sudo ls",
                    "python3 tests/ok.py > organism_v6/out.txt"]:
            assert not P.decide_run(cmd)["allowed"], cmd
            assert not P.decide_run(f"bash gpu/a40_ssh.sh '{cmd}'")["allowed"], cmd


def test_policy_rejects_shell_operators_and_redirects_outside_the_sandbox():
    with Fixture() as fx:
        P = fx.policy
        for cmd in ["ls ; ls", "ls | wc -l", "ls && ls", "ls || ls", "ls &", "ls ( x )",
                    "ls < tests/ok.py", "ls $(pwd)", "ls `pwd`", "ls\nls",
                    "python3 tests/ok.py > organism_v6/out.txt",
                    "python3 tests/ok.py >> tests/ok.py",
                    "python3 tests/ok.py 2> gpu/x.txt",
                    "python3 tests/ok.py &> tools/astra_agent.py",
                    "python3 tests/ok.py > research_notes/astra_agent/runs/x.txt",
                    "python3 tests/ok.py 3>&2"]:
            d = P.decide_run(cmd)
            assert not d["allowed"], (cmd, d["reason"])
        d = P.decide_run("python3 tests/ok.py > tools/astra_sandbox/out.txt 2>&1")
        assert d["allowed"] and d["redirect"]["stderr"] == "stdout"
        assert d["redirect"]["stdout"] == os.path.join(fx.repo, "tools/astra_sandbox/out.txt")
        assert d["argv"] == ["python3", "tests/ok.py"]
        d = P.decide_run("python3 tests/ok.py >> tests/astra/log.txt")
        assert d["allowed"] and d["redirect"]["append"]
        assert P.decide_run("python3 tests/ok.py > /dev/null")["allowed"]
        # node side
        for remote in ["ls ~/v6_out; ls", "ls ~/v6_out && ls", "ls ~/v6_out || ls",
                       "ls ~/v6_out &", "ls ~/v6_out > ~/evil.txt", "ls ~/v6_out > x.txt",
                       "ls ~/v6_out | rm -rf x", "ls ~/v6_out | bash", "ls ~/v6_out | sh",
                       "ls ~/v6_out | python3 x.py", "ls < ~/v6_out/x", "ls ~/v6_out 2>&3",
                       "nohup ls ~/v6_out &", "nohup bash gpu/rg_band.sh 6 8 x &> rg_band/x.out &",
                       "FOO=1 bash gpu/rg_band.sh 6", "WRITE_AB_DRY=1 ls ~/v6_out",
                       "bash gpu/rg_band.sh 6 8 x > ../rg_band/x.out"]:
            d = P.decide_run(f"bash gpu/a40_ssh.sh '{remote}'")
            assert not d["allowed"], (remote, d["reason"])
        assert P.decide_run("bash gpu/a40_ssh.sh 'ls ~/v6_out | python3 -c \"import sys;print(1)\"'")["allowed"]


def test_policy_rejects_path_traversal_and_escapes():
    with Fixture() as fx:
        P = fx.policy
        for cmd in ["python3 tests/../organism_v6/module.py", "ls ../", "ls ..",
                    "wc -l ../../etc/passwd", "shasum /etc/hosts", "ls /", "ls ~",
                    "ls ~/dream-state", "wc -l gpu/hosts.env", "wc -l .git/config",
                    "wc -l tests/alias.txt", "ls research_notes/astra_agent/runs/other_run",
                    "python3 tests/ok.py --out=/etc/x", "python3 tests/ok.py --dir ../x",
                    "python3 tests/ok.py /opt/outside.txt", "ls /var/log"]:
            d = P.decide_run(cmd)
            assert not d["allowed"], (cmd, d["reason"])
        assert P.decide_run("ls .")["allowed"]
        assert P.decide_run("ls tests organism_v6")["allowed"]
        assert P.decide_run("python3 tests/ok.py --out /tmp/x.json")["allowed"]
        # an absolute path is refused when it is a home path (identifier) and accepted only
        # when it resolves inside the repository; either way the decision is a dict, no crash
        d = P.decide_run(f"python3 tests/ok.py {os.path.join(fx.repo, 'tests/ok.py')}")
        assert isinstance(d["allowed"], bool) and d["reason"]
        for path in ["../x", "tests/../gpu/hosts.env", "/etc/passwd", "~/x",
                     os.path.join(os.path.dirname(fx.repo), "x")]:
            assert not P.decide_read(path)["allowed"], path
            assert not P.decide_write(path)["allowed"], path


def test_git_cannot_write_files_through_output_options():
    """Fatal review finding: `git diff --output=<file>` / `git log --output <file>`
    make git itself create, overwrite or truncate ANY file — a native binary
    writing, so neither the '>' guard nor the python guard could see it (live
    probe with git 2.50.1: module.py's contents were destroyed). Refused by the
    global deny token --output AND by the per-program option rule (which also
    covers git abbreviations, -O<orderfile> and --ext-diff); read-only git stays."""
    with Fixture() as fx:
        P = fx.policy
        module = os.path.join(fx.repo, "organism_v6/module.py")
        before = open(module).read()
        bad = ["git diff --output=organism_v6/module.py",
               "git diff --output organism_v6/module.py",
               "git log --output=tools/astra_policy.json",
               "git log -n 1 --output gpu/a40_ssh.sh",
               "git diff --output=tools/astra_sandbox/out.txt",      # not even into the sandbox
               "git diff --output=/dev/null",
               "git diff HEAD --output=CLAUDE.md",
               "git diff -- --output=organism_v6/module.py",
               "git diff --outpu=organism_v6/module.py",            # abbreviations, should git take one
               "git log --out organism_v6/module.py",
               "git diff --o=organism_v6/module.py",
               "git diff --output-indicator-new=+",
               "git diff -Oorganism_v6/module.py",                   # reads an arbitrary orderfile
               "git diff --ext-diff",
               "git log --output=x > tools/astra_sandbox/o.txt",
               "git 'diff' '--output=organism_v6/module.py'",
               "git diff '--out''put=organism_v6/module.py'"]       # quote-split token
        for cmd in bad:
            d = P.decide_run(cmd)
            assert not d["allowed"], (cmd, d["reason"])
            assert "deny-listed token '--output'" in d["reason"] or "option '" in d["reason"], \
                (cmd, d["reason"])
        t = aa.Tools(P)
        for cmd in bad:
            out = t.run(cmd)
            assert out.startswith("POLICY REFUSED"), (cmd, out)
        assert t.commands == [] and len(t.refusals) == len(bad)      # nothing ran
        assert open(module).read() == before
        # git stays available for inspection
        for ok in ["git diff", "git diff --stat", "git diff --cached --name-only -- organism_v6",
                   "git diff HEAD~1 HEAD -- tests/ok.py", "git log -n 5 --oneline --decorate",
                   "git log --stat -n 1 --format=%H", "git status --short", "git status --porcelain=v2",
                   "git log --oneline -n 3 > tools/astra_sandbox/log.txt"]:
            d = P.decide_run(ok)
            assert d["allowed"], (ok, d["reason"])
        # a sandbox script that spawns git --output is stopped by the python guard's argv scan
        _w(fx.repo, "tests/git_via_child.py",
           "import subprocess\nsubprocess.run(['git', 'diff', '--output=organism_v6/module.py'])\n"
           "print('GIT RAN')\n")
        t2 = aa.Tools(P, result_chars=20000)
        out = t2.run("<venv312>/bin/python tests/git_via_child.py")
        assert "deny-listed '--output'" in out and "GIT RAN" not in out, out[-600:]
        assert t2.commands[-1]["rc"] != 0 and open(module).read() == before
        # the rule is data, not code: it lives in the policy file and names git
        assert "git" in P.get("local_option_deny") and "--output" in P.get("deny_tokens")


def test_deny_scan_survives_whitespace_and_quoting_tricks():
    """The deny layer is advertised as overriding everything, so it must not be
    evadable by repeated whitespace ('git  commit') or by quote-splitting a
    token: 'r''m' is rm to the shell and "import sub""process" is import
    subprocess to python3 -c. Before this fix the two python3 -c remotes and
    `ls 'r''m'` were ALLOWED (only the raw text was scanned)."""
    with Fixture() as fx:
        P = fx.policy
        for text in ["git  commit -m x", "git\tcommit", "git \t  push origin", "bash  -c ls",
                     "pip   install x", "git commit"]:
            r = P.deny_reason(text)
            assert r and "deny-listed phrase" in r, (text, r)
        assert P.deny_reason("ls tests/ok.py") is None
        for cmd in ["ls 'r''m'", "ls r\"\"m", "wc -l 'gpu/hosts'.env", "git 'commit'",
                    "git  commit -m x", "shasum 'te''e' tests/ok.py"]:
            d = P.decide_run(cmd)
            assert not d["allowed"], (cmd, d["reason"])
            assert "deny-listed" in d["reason"] or "secret probe" in d["reason"], (cmd, d["reason"])
        for rem in ["python3 -c \"import sub\"\"process\"",
                    "python3 -c \"import os; os.sys\"\"tem(1)\"",
                    "python3 -c \"import os; print(os.env\"\"iron)\"",
                    "ls ~/v6_out | r\"\"m -rf x",
                    "ls ~/v6_out | 'k''ill' -9 1",
                    "ls ~/.s''sh"]:
            d = P.decide_run(node(rem))
            assert not d["allowed"], (rem, d["reason"])
            assert "deny-listed" in d["reason"] or "secret probe" in d["reason"], (rem, d["reason"])
        # ordinary quoting and spacing still pass
        assert P.decide_run("python3 tests/ok.py --flag 'a  b'")["allowed"]
        assert P.decide_run("git   log  -n 5")["allowed"]
        assert P.decide_run(node("grep -E 'gate  cand' ~/v6_out/R2_B_seed0/life.log"))["allowed"]
        assert P.decide_run(node("python3 -c \"import json; print(json.dumps({'a': 1}))\""))["allowed"]


def test_write_file_redacts_identifiers_and_masks_secrets():
    """write_file goes through the same safe_text() as every other outward path:
    secrets and hosts.env values -> ***, internal identifiers -> <REDACTED>;
    the tool result tells the model what happened; clean content is verbatim."""
    with Fixture() as fx:
        aa.register_secret(SECRET)
        t = aa.Tools(fx.policy)
        idents = ["10.1.2.3", "someone@example.org", "https://example.org/x?y=1",
                  "/Users/someone/dream-state", "/home/someone/x", "node-7.nvidia.com", "box.internal"]
        content = ("notes: " + " | ".join(idents) + f" | host={FAKE_HOST_A} | key={SECRET}\n"
                   "plain line\n")
        out = t.write_file("tools/astra_sandbox/idents.md", content)
        assert out.startswith("wrote") and "redacted" in out and "secrets masked" in out, out
        text = open(os.path.join(fx.repo, "tools/astra_sandbox/idents.md")).read()
        for s in idents + [SECRET, FAKE_HOST_A, FAKE_HOST_A.split("@")[1], "fake-node-77"]:
            assert s not in text, s
        assert "<REDACTED>" in text and "***" in text and "plain line" in text
        assert t.files_written == ["tools/astra_sandbox/idents.md"]
        # content without identifiers is written verbatim and reported plainly
        code = "import json\nprint(json.dumps({'a': 1}))\n"
        out = t.write_file("tools/astra_sandbox/plain.py", code)
        assert out == "wrote %d chars to tools/astra_sandbox/plain.py" % len(code), out
        assert open(os.path.join(fx.repo, "tools/astra_sandbox/plain.py")).read() == code


def test_write_policy_sandbox_only():
    with Fixture() as fx:
        P = fx.policy
        for ok in ["tools/astra_sandbox/a.py", "tools/astra_sandbox/deep/er/b.json",
                   "tests/astra/test_x.py", "research_notes/astra_agent/notes.md",
                   "research_notes/astra_agent/plans/p1.md",
                   os.path.join(fx.repo, "tools/astra_sandbox/abs.py")]:
            d = P.decide_write(ok)
            assert d["allowed"], (ok, d["reason"])
        for bad in ["organism_v6/x.py", "organism_v6/module.py", "tools/astra_agent.py",
                    "tools/astra_policy.json", "tests/test_astra_agent.py", "tests/ok.py",
                    "gpu/hosts.env", "gpu/x.sh", "CLAUDE.md", "tools/astra_sandbox",
                    "tools/astra_sandbox/../astra_agent.py", "tests/astra/../ok.py",
                    "research_notes/astra_agent/runs/x/y.md",
                    "research_notes/astra_agent/runs/other_run/transcript.jsonl",
                    "tools/astra_sandbox/link/evil.py",        # symlink -> organism_v6
                    "/etc/x", "~/x", "", "tools/astra_sandbox/a\nb"]:
            d = P.decide_write(bad)
            assert not d["allowed"], (bad, d["reason"])
        t = aa.Tools(P)
        out = t.write_file("tools/astra_sandbox/link/evil.py", "x")
        assert out.startswith("POLICY REFUSED") and not os.path.exists(
            os.path.join(fx.repo, "organism_v6/evil.py"))
        out = t.write_file("organism_v6/new.py", "x")
        assert out.startswith("POLICY REFUSED") and not os.path.exists(
            os.path.join(fx.repo, "organism_v6/new.py"))
        out = t.write_file("tests/astra/test_new.py", "print(1)\n")
        assert out.startswith("wrote") and os.path.isfile(os.path.join(fx.repo, "tests/astra/test_new.py"))
        assert t.files_written == ["tests/astra/test_new.py"]
        assert "cap" in t.write_file("tests/astra/big.py", "x" * (P.get("write_max_chars") + 1))


def test_read_policy_hides_hosts_env_git_and_other_runs():
    with Fixture() as fx:
        P = fx.policy
        for bad in ["gpu/hosts.env", ".git/config", ".git", "tests/alias.env", "tests/alias.txt",
                    "research_notes/astra_agent/runs/other_run/transcript.jsonl",
                    "research_notes/astra_agent/runs/other_run"]:
            d = P.decide_read(bad)
            assert not d["allowed"], (bad, d["reason"])
        assert P.decide_read("organism_v6/module.py")["allowed"]
        assert P.decide_read("gpu/hosts.env.example")["allowed"]   # not present; still just a path
        t = aa.Tools(P)
        assert t.read_file("gpu/hosts.env").startswith("POLICY REFUSED")
        assert t.read_file("tests/alias.txt").startswith("POLICY REFUSED")
        assert FAKE_HOST_A not in t.read_file("tests/alias.env")
        assert "NEEDLE_IN_MODULE" in t.read_file("organism_v6/module.py")
        listing = t.list_dir("gpu")
        assert "a40_ssh.sh" in listing and "hosts.env" not in listing
        assert "other_run" not in t.list_dir("research_notes/astra_agent/runs")
        assert ".git" not in t.list_dir(".")
        g = t.grep(OTHER_RUN_SENTINEL)
        assert "0 hits" in g.splitlines()[0], g
        assert "0 hits" in t.grep("fake-node-77").splitlines()[0]
        assert FAKE_HOST_A not in t.grep("NODE", "gpu")          # hosts.env is skipped by grep
        g = t.grep("NEEDLE_IN_MODULE", "organism_v6")
        assert "organism_v6/module.py:2:" in g
        # the CURRENT run's directory is readable once an agent owns it
        agent, _c = fx.agent([FINAL], runs_root=os.path.join(fx.repo, "research_notes/astra_agent/runs"))
        rel = os.path.relpath(agent.run_dir, fx.repo)
        assert P.decide_read(rel)["allowed"]
        assert not P.decide_read("research_notes/astra_agent/runs/other_run")["allowed"]
        assert not P.decide_write(rel + "/notes.md")["allowed"]     # harness-owned


# ---------------------------------------------------------------------------
# policy: node rules
# ---------------------------------------------------------------------------
def test_node_gpu_argument_must_be_6_on_node_1_and_smoke_disabled_on_node_2():
    with Fixture() as fx:
        P = fx.policy
        ok = ["bash gpu/rg_band.sh 6", "bash gpu/rg_band.sh 6 8 tag exam,gate",
              "bash gpu/write_ab.sh 6 ~/v6_out/R2_B_seed0", "bash gpu/write_ab.sh 6 ~/v6_out/R2_B_seed0 512",
              "bash gpu/memory_dose.sh 6", "bash gpu/memory_dose.sh 6 --arm D",
              "nohup bash gpu/rg_band.sh 6 8 tag > rg_band/tag.out 2>&1 &",
              "nohup bash gpu/memory_dose.sh 6 > ~/v6_out/md.out 2>&1 &"]
        for remote in ok:
            d = P.decide_run(f"bash gpu/a40_ssh.sh '{remote}'")
            assert d["allowed"], (remote, d["reason"])
            d2 = P.decide_run(f"bash gpu/ovx_ssh.sh '{remote}'")
            assert not d2["allowed"] and "disabled" in d2["reason"], (remote, d2["reason"])
        for g in ["0", "1", "2", "5", "7", "66", "6,7", "", "-1", "gpu6", "6.0"]:
            for script in ["rg_band.sh", "write_ab.sh", "memory_dose.sh"]:
                remote = f"bash gpu/{script} {g} ~/v6_out/R2_B_seed0".rstrip()
                d = P.decide_run(f"bash gpu/a40_ssh.sh '{remote}'")
                assert not d["allowed"], (remote, d["reason"])
                assert "GPU" in d["reason"] or "start with" in d["reason"], d["reason"]
                remote = f"nohup bash gpu/{script} {g} > rg_band/x.out 2>&1 &"
                assert not P.decide_run(f"bash gpu/a40_ssh.sh '{remote}'")["allowed"], remote
        # a smoke script reached through a pipe or after a filter still needs GPU 6
        assert not P.decide_run("bash gpu/a40_ssh.sh 'ls ~/v6_out | bash gpu/rg_band.sh 7'")["allowed"]
        assert not P.decide_run("bash gpu/a40_ssh.sh 'CUDA_VISIBLE_DEVICES=7 bash gpu/rg_band.sh 6'")["allowed"]
        # the policy file makes the rule explicit
        assert P.get("node_smoke_gpus") == {"a40": ["6"], "ovx": []}


def test_node_rejects_hostnames_unquoted_remotes_and_foreign_wrappers():
    with Fixture() as fx:
        P = fx.policy
        host_a = FAKE_HOST_A.split("@")[1]
        for cmd in [f"bash gpu/a40_ssh.sh 'ls {host_a}'",
                    f"bash gpu/a40_ssh.sh 'grep x {FAKE_HOST_A}'",
                    f"bash gpu/ovx_ssh.sh 'ls fake-node-78'",         # bare first label of a host
                    "bash gpu/a40_ssh.sh 'grep -c foo 10.1.2.3'",
                    "bash gpu/a40_ssh.sh 'ls somebody@somewhere'",
                    "bash gpu/a40_ssh.sh 'ls node.nvidia.com'",
                    "bash gpu/a40_ssh.sh 'ls https://example.org/x'",
                    "bash gpu/a40_ssh.sh 'ls /Users/someone/x'",
                    f"ls {host_a}", "ls 10.1.2.3", "wc -l x@y.z", f"python3 tests/ok.py --host {host_a}",
                    "bash gpu/a40_ssh.sh ls ~/v6_out",                # unquoted: 4 argv
                    "bash gpu/a40_ssh.sh",                            # no remote
                    "bash gpu/a40_ssh.sh 'ls' 'ls'",
                    "bash gpu/gh200_ssh.sh 'ls'", "bash gpu/v2node_ssh.sh 'ls'",
                    "bash gpu/a40_scp.sh x y", "bash ./gpu/a40_ssh.sh 'ls'",
                    f"bash {fx.repo}/gpu/a40_ssh.sh 'ls'", "bash tests/ok.py", "sh gpu/a40_ssh.sh 'ls'",
                    "ssh fake-node-77 ls", "scp x fake-node-77:y"]:
            d = P.decide_run(cmd)
            assert not d["allowed"], (cmd, d["reason"])
            assert FAKE_HOST_A not in d["reason"] and host_a not in d["display"]
        # the policy never echoes a hostname: the display is masked
        d = P.decide_run(f"bash gpu/a40_ssh.sh 'ls {host_a}'")
        assert host_a not in json.dumps(aa.safe_obj(d))
        # a node command whose wrapper prints the hostname: masked in the result
        t = aa.Tools(P)
        out = t.run("bash gpu/a40_ssh.sh 'tail -n 3 ~/v6_out/R2_B_seed0/life.log'")
        assert "REMOTE[a40] argc=1 arg1=tail -n 3 ~/v6_out/R2_B_seed0/life.log" in out, out
        assert FAKE_HOST_A not in out and host_a not in out and "fake-node-77" not in out
        assert "connecting to" in out and "***" in out


# ---------------------------------------------------------------------------
# the loop
# ---------------------------------------------------------------------------
def test_loop_stops_at_step_budget_with_a_forced_report():
    with Fixture() as fx:
        def reply(messages):
            if "STEP BUDGET EXHAUSTED" in messages[-1]["content"]:
                return FINAL
            return tool("list_dir", path=".")
        agent, client = fx.agent([reply], steps=3)
        res = agent.run()
        assert res["stopped_by"] == "step_budget" and res["steps"] == 3
        assert res["model_calls"] == 4                     # 3 tool turns + the forced final
        assert res["report"]["forced"] is True and res["report"]["summary"] == "done"
        rows = _rows(agent)
        assert sum(r["kind"] == "tool_call" for r in rows) == 3
        assert sum(r["kind"] == "tool_result" for r in rows) == 3
        kinds = [r["kind"] for r in rows]
        assert "final" in kinds and "end" in kinds and "meta" in kinds and "system" in kinds
        assert os.path.isfile(os.path.join(agent.run_dir, "report.md"))
        assert os.path.isfile(os.path.join(agent.run_dir, "run.json"))
        assert "FORCED" in open(os.path.join(agent.run_dir, "report.md")).read()
        # the model ignores the forced request -> the harness synthesizes the report
        agent2, _c = fx.agent([tool("list_dir", path=".")], steps=2)
        res2 = agent2.run()
        assert res2["stopped_by"] == "step_budget" and res2["steps"] == 2
        assert "synthesized" in res2["report"]["summary"]
        assert res2["report"]["forced"] is True
        assert any("stopped by step_budget" in g for g in res2["report"]["gaps"])


def test_token_and_wall_clock_budgets_force_the_report():
    with Fixture() as fx:
        agent, _c = fx.agent([tool("list_dir", path="."), FINAL], steps=50,
                             token_budget=1000, usage={"prompt_tokens": 800, "completion_tokens": 300})
        res = agent.run()
        assert res["stopped_by"] == "token_budget" and res["steps"] == 1
        assert res["tokens"]["total"] == 2200                # one tool turn + the forced final
        assert res["report"]["forced"] is True
        clock = [0.0]
        agent2, _c = fx.agent([tool("list_dir", path="."), FINAL], steps=50, wall_minutes=1,
                              clock=lambda: clock[0])
        clock[0] = 61.0
        res2 = agent2.run()
        assert res2["stopped_by"] == "wall_clock" and res2["steps"] == 0


def test_transcript_never_contains_the_key_or_a_hostname_even_when_echoed():
    with Fixture() as fx:
        os.environ["ASTRA_API_KEY"] = SECRET
        key = aa.take_key()
        assert key == SECRET and "ASTRA_API_KEY" not in os.environ
        host_a = FAKE_HOST_A.split("@")[1]
        replies = [
            json.dumps(dict(tool="write_file", note=f"leaking {SECRET}",
                            args=dict(path="tools/astra_sandbox/notes.md",
                                      content=f"key={SECRET} host={FAKE_HOST_A}\n"))),
            tool("run", cmd="<venv312>/bin/python tests/env_probe.py"),
            tool("run", cmd="bash gpu/a40_ssh.sh '~/status.sh'"),
            tool("run", cmd=f"ls {host_a}"),
            f"here is the key {SECRET} and the host {FAKE_HOST_A} " + tool("list_dir", path="."),
            json.dumps(dict(final=dict(summary=f"the key is {SECRET} on {FAKE_HOST_A}",
                                       files_written=["tools/astra_sandbox/notes.md"],
                                       tests_run=[], findings=[SECRET], proposed_runbook=[],
                                       gaps=[]))),
        ]
        agent, client = fx.agent(replies, steps=20)
        res = agent.run()
        assert res["stopped_by"] == "final"
        text = _all_text_under(agent.run_dir)
        assert SECRET not in text
        assert FAKE_HOST_A not in text and host_a not in text and "fake-node-77" not in text
        assert "***" in text
        # the sandbox file the model wrote is masked too
        notes = open(os.path.join(fx.repo, "tools/astra_sandbox/notes.md")).read()
        assert SECRET not in notes and "***" in notes
        # the subprocess did not inherit the key
        probe = next(r for r in _rows(agent) if r["kind"] == "tool_result"
                     and "env_probe" in r["content"])
        assert "ASTRA_API_KEY" not in probe["content"] and SECRET not in probe["content"]
        assert "exit 0" in probe["content"]
        # what was sent to the model never carried the key or the host either
        sent = json.dumps(client.calls)
        assert SECRET not in sent and host_a not in sent and FAKE_HOST_A not in sent
        # the refusal of the hostname command is logged without the hostname
        ref = [r for r in _rows(agent) if r["kind"] == "policy" and not r.get("allowed")]
        assert ref and all(host_a not in json.dumps(r) for r in ref)


def test_run_timeout_is_handled_and_the_process_group_killed():
    with Fixture() as fx:
        t = aa.Tools(fx.policy, run_timeout_s=1)
        import time
        t0 = time.monotonic()
        out = t.run("<venv312>/bin/python tests/sleep_forever.py", timeout_s=1)
        assert time.monotonic() - t0 < 20
        assert "TIMEOUT after 1s" in out and "process group killed" in out
        assert t.commands[-1]["timed_out"] is True
        out = t.run("<venv312>/bin/python tests/ok.py", timeout_s=30)
        assert "exit 0" in out and "ok from test" in out
        assert t.commands[-1]["timed_out"] is False and t.commands[-1]["rc"] == 0
        # a timeout above the policy cap is clipped, never unbounded
        d = fx.policy
        assert d.run_timeout_max_s >= d.run_timeout_s
        out = t.run("<venv312>/bin/python tests/ok.py", timeout_s=10 ** 9)
        assert "exit 0" in out
        # the placeholder, not the venv path, appears in the record
        assert t.commands[-1]["cmd"].startswith("<venv312>/bin/python")


def test_results_are_truncated_to_the_configurable_cap():
    with Fixture() as fx:
        t = aa.Tools(fx.policy, result_chars=600)
        out = t.call("run", dict(cmd="<venv312>/bin/python tests/spew.py"))
        assert len(out) <= 700 and "chars truncated by the harness" in out
        assert out.startswith("[run local]") and "stderr" in out      # head AND tail survive
        direct = t.run("<venv312>/bin/python tests/spew.py")            # streams capped even directly
        assert len(direct) <= 2 * 600 + 400 and "chars truncated by the harness" in direct
        big = _w(fx.repo, "tests/astra/big.txt", "\n".join(f"line {i}" for i in range(3000)))
        r = t.read_file("tests/astra/big.txt", start_line=10, max_lines=5)
        # 1-indexed line N holds the text "line N-1": lines 10-14 are "line 9" .. "line 13"
        assert "lines 10-14 of 3000" in r and "\tline 9\n" in r and "\tline 13" in r
        assert "line 14" not in r and "line 8" not in r
        r = t.call("read_file", dict(path="tests/astra/big.txt"))
        assert len(r) <= 700 and "chars truncated by the harness" in r
        g = t.grep("line", "tests/astra", max_results=7)
        assert "7 hits" in g.splitlines()[0] and "result cap 7" in g.splitlines()[0]
        assert os.path.isfile(big)
        t2 = aa.Tools(fx.policy, result_chars=100000)
        assert len(t2.call("run", dict(cmd="<venv312>/bin/python tests/spew.py"))) > 20000
        assert aa.truncate("abc", 10) == "abc" and len(aa.truncate("x" * 1000, 200)) <= 260


def test_python_guard_blocks_writes_outside_the_sandbox_and_allows_inside():
    with Fixture() as fx:
        t = aa.Tools(fx.policy, result_chars=20000)
        out = t.run("<venv312>/bin/python tests/write_outside.py")
        assert "astra sandbox guard" in out and "WROTE OUTSIDE" not in out
        assert not os.path.exists(os.path.join(fx.repo, "organism_v6/pwned.txt"))
        assert t.commands[-1]["rc"] != 0
        out = t.run("<venv312>/bin/python tests/write_inside.py")
        assert "exit 0" in out and "wrote inside" in out
        assert os.path.isfile(os.path.join(fx.repo, "tools/astra_sandbox/ok.txt"))
        out = t.run("<venv312>/bin/python tests/spawn_child.py")
        assert "deny-listed 'rm'" in out and "RM RAN" not in out, out[-600:]
        assert os.path.isfile(os.path.join(fx.repo, "organism_v6/module.py"))
        # a command whose text itself carries a deny token never even starts
        out = t.run("<venv312>/bin/python tests/rm_via_subprocess.py")
        assert out.startswith("POLICY REFUSED") and "subprocess" in out
        # a sandbox script the model wrote, run through the sandbox prefix
        t.write_file("tools/astra_sandbox/probe.py",
                     "import os, tempfile\nd = tempfile.mkdtemp()\nopen(os.path.join(d, 'x'), 'w').write('1')\n"
                     "print('tmp ok')\ntry:\n    open('tests/ok.py', 'w')\nexcept PermissionError as e:\n"
                     "    print('refused:', 'guard' in str(e))\n")
        out = t.run("<venv312>/bin/python tools/astra_sandbox/probe.py")
        assert "tmp ok" in out and "refused: True" in out and "exit 0" in out
        assert open(os.path.join(fx.repo, "tests/ok.py")).read() == "print('ok from test')\n"


# ---------------------------------------------------------------------------
# HTTP client against a loopback server (no external network)
# ---------------------------------------------------------------------------
class _Handler(http.server.BaseHTTPRequestHandler):
    script: list = []
    seen: list = []

    def log_message(self, *a):  # silence
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n)
        _Handler.seen.append(dict(path=self.path, auth=self.headers.get("Authorization"),
                                  body=json.loads(body.decode() or "{}")))
        code, payload, extra = _Handler.script.pop(0) if _Handler.script else (200, {}, {})
        self.send_response(code)
        for k, v in extra.items():
            self.send_header(k, v)
        data = json.dumps(payload).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _serve():
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv


def test_http_client_request_shape_retries_and_redirect_refusal():
    srv = _serve()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}/v1"
        ok = dict(choices=[dict(message=dict(content='{"tool": "list_dir", "args": {}}'),
                                finish_reason="stop")],
                  usage=dict(prompt_tokens=10, completion_tokens=5,
                             completion_tokens_details=dict(reasoning_tokens=2)))
        c = aa.AstraClient(SECRET, base_url=base, model="m", effort="high",
                           max_completion_tokens=123, timeout_s=5, retries=3, backoff_s=0.01)
        url, headers, body = c.build_request([dict(role="user", content="hi")])
        assert url.endswith("/v1/chat/completions")
        assert headers["Authorization"] == "Bearer " + SECRET
        assert body["max_completion_tokens"] == 123 and body["reasoning_effort"] == "high"
        assert body["model"] == "m" and "max_tokens" not in body
        _Handler.script = [(429, dict(error="slow down"), {}), (503, dict(error="down"), {}),
                           (408, {}, {}), (200, ok, {})]
        _Handler.seen = []
        text, usage = c.chat([dict(role="user", content="hi")])
        assert text.startswith('{"tool"') and usage["completion_tokens"] == 5
        assert len(_Handler.seen) == 4 and all(s["auth"] == "Bearer " + SECRET for s in _Handler.seen)
        # a 4xx other than 408/409/429 is not retried
        _Handler.script = [(401, dict(error=f"bad key {SECRET}"), {})]
        _Handler.seen = []
        try:
            c.chat([dict(role="user", content="hi")])
            raise AssertionError("401 must raise")
        except aa.ProviderError as e:
            assert "HTTP 401" in str(e) and SECRET not in str(e) and "***" in str(e)
        assert len(_Handler.seen) == 1
        # redirects are refused (the key is never re-sent elsewhere)
        _Handler.script = [(302, {}, {"Location": "http://127.0.0.1:9/elsewhere"})]
        try:
            c.chat([dict(role="user", content="hi")])
            raise AssertionError("redirect must raise")
        except aa.ProviderError as e:
            assert "redirect refused" in str(e)
        # a reply cut at the cap is retried once with a doubled cap
        cut = dict(choices=[dict(message=dict(content=""), finish_reason="length")], usage={})
        _Handler.script = [(200, cut, {}), (200, ok, {})]
        _Handler.seen = []
        c.chat([dict(role="user", content="hi")])
        assert [s["body"]["max_completion_tokens"] for s in _Handler.seen] == [123, 246]
        # retries exhausted -> ProviderError, masked
        _Handler.script = [(500, {}, {})] * 4
        try:
            c.chat([dict(role="user", content="hi")])
            raise AssertionError("must raise")
        except aa.ProviderError as e:
            assert "HTTP 500" in str(e)
        # plaintext http to a non-loopback host is refused before any request
        try:
            aa.AstraClient(SECRET, base_url="http://example.org/v1")
            raise AssertionError("must refuse")
        except ValueError as e:
            assert "plaintext" in str(e)
        try:
            aa.AstraClient("", base_url=base)
            raise AssertionError("must refuse an empty key")
        except ValueError:
            pass
        assert SECRET not in aa.mask_secrets(f"x {SECRET} y")
    finally:
        srv.shutdown()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cli(fx, *args, env_extra=None):
    import subprocess
    env = dict(os.environ)
    env.pop("ASTRA_API_KEY", None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, os.path.join(TOOLS, "astra_agent.py"), "--repo", fx.repo,
                           "--policy", os.path.join(fx.repo, "tools/astra_policy.json")] + list(args),
                          capture_output=True, text=True, cwd=fx.repo, env=env, timeout=120)


def test_dry_run_cli_prints_the_decision_without_running():
    with Fixture() as fx:
        r = _cli(fx, "--dry-run", "rm -rf organism_v6")
        assert r.returncode == 3, r.stderr
        d = json.loads(r.stdout.strip().splitlines()[-1])
        assert d["allowed"] is False and "rm" in d["reason"]
        assert os.path.isdir(os.path.join(fx.repo, "organism_v6"))
        r = _cli(fx, "--dry-run", "<venv312>/bin/python tests/write_outside.py",
                 "--dry-run", "bash gpu/a40_ssh.sh 'bash gpu/rg_band.sh 6 1 smoke'")
        assert r.returncode == 0, r.stderr
        lines = [json.loads(l) for l in r.stdout.strip().splitlines()]
        assert all(l["allowed"] for l in lines) and lines[1]["kind"] == "node"
        assert not os.path.exists(os.path.join(fx.repo, "organism_v6/pwned.txt"))   # nothing ran
        r = _cli(fx, "--dry-run", "bash gpu/a40_ssh.sh 'bash gpu/rg_band.sh 3 1 smoke'")
        assert r.returncode == 3 and "GPU" in r.stdout
        r = _cli(fx, "--dry-run-write", "organism_v6/x.py", "--dry-run-read", "gpu/hosts.env")
        assert r.returncode == 3
        assert all(not json.loads(l)["allowed"] for l in r.stdout.strip().splitlines())
        r = _cli(fx, "--dry-run", f"bash gpu/a40_ssh.sh 'ls {FAKE_HOST_A}'")
        assert r.returncode == 3 and FAKE_HOST_A not in r.stdout + r.stderr
        r = _cli(fx)                                     # no task, no dry run
        assert r.returncode == 2 and "--task" in r.stderr
        r = _cli(fx, "--task", "x")                      # no key
        assert r.returncode == 2 and "ASTRA_API_KEY" in r.stderr


def test_mock_cli_runs_end_to_end_and_writes_the_transcript():
    with Fixture() as fx:
        replies = [tool("list_dir", path="."), tool("read_file", path="organism_v6/module.py"),
                   tool("run", cmd="<venv312>/bin/python tests/ok.py"),
                   tool("run", cmd="rm -rf organism_v6"),
                   tool("write_file", path="tests/astra/test_probe.py", content="print(1)\n"),
                   FINAL]
        mock = _w(fx.repo, "tools/astra_sandbox/replies.json", json.dumps(replies))
        runs = os.path.join(fx.root, "runs")
        r = _cli(fx, "--task", "smoke mission", "--mock-replies", mock, "--runs-root", runs,
                 "--steps", "10", "--quiet", env_extra={"ASTRA_API_KEY": SECRET})
        assert r.returncode == 0, r.stderr
        summary = json.loads(r.stdout)
        assert summary["stopped_by"] == "final" and summary["steps"] == 5
        assert summary["n_refusals"] == 1 and summary["files_written"] == ["tests/astra/test_probe.py"]
        run_dir = os.path.join(runs, sorted(os.listdir(runs))[0])
        assert os.path.isfile(os.path.join(run_dir, "transcript.jsonl"))
        rep = open(os.path.join(run_dir, "report.md")).read()
        assert "delivered by the model" in rep and "tests/astra/test_probe.py" in rep
        assert "Commands actually run" in rep and "tests/ok.py` -> exit 0" in rep
        assert "Policy refusals (1)" in rep and "rm" in rep
        assert SECRET not in _all_text_under(run_dir)
        assert os.path.isdir(os.path.join(fx.repo, "organism_v6"))


def test_report_and_context_compaction_and_json_tolerance():
    with Fixture() as fx:
        # prose and fences around the object are tolerated; a bad reply is nudged
        replies = ["Sure! ```json\n" + tool("read_file", path="organism_v6/module.py") + "\n```",
                   "not json at all", tool("run", cmd="<venv312>/bin/python tests/spew.py"),
                   tool("run", cmd="<venv312>/bin/python tests/spew.py"),
                   tool("run", cmd="<venv312>/bin/python tests/spew.py"),
                   tool("run", cmd="<venv312>/bin/python tests/spew.py"),
                   tool("run", cmd="<venv312>/bin/python tests/spew.py"),
                   tool("run", cmd="<venv312>/bin/python tests/spew.py"),
                   tool("write_file", path="research_notes/astra_agent/notes/n1.md", content="# n1\n"),
                   json.dumps(dict(final=dict(summary="s", files_written="research_notes/astra_agent/notes/n1.md",
                                              tests_run=["t"], findings={"a": 1}, proposed_runbook="r",
                                              gaps=None)))]
        agent, client = fx.agent(replies, steps=20, result_chars=2000, context_chars=9000)
        res = agent.run()
        assert res["stopped_by"] == "final" and res["steps"] == 8, res["stopped_by"]
        rep = res["report"]
        assert rep["files_written"] == ["research_notes/astra_agent/notes/n1.md"]
        assert rep["findings"] == ["a: 1"] and rep["proposed_runbook"] == ["r"] and rep["gaps"] == []
        # the prompt stayed bounded: old tool results were compacted in place (the transcript
        # keeps every full result, so the uncompacted size can be reconstructed from it)
        last = client.calls[-1]
        total = sum(len(m["content"]) for m in last)
        rows = _rows(agent)
        uncompacted = sum(len(r.get("content") or "") for r in rows
                          if r["kind"] in ("system", "user", "assistant", "tool_result"))
        assert total <= uncompacted - 3000, (total, uncompacted)
        assert any("compacted for context" in m["content"] for m in last)
        assert last[0]["role"] == "system" and "test mission" in last[0]["content"]
        assert all(len(m["content"]) <= 2000 + 400 for m in last[2:-1] if m["role"] == "user"
                   and "tests/spew.py" in m["content"])
        # the report records the ground truth
        md = open(os.path.join(agent.run_dir, "report.md")).read()
        assert "Files actually written" in md and "notes/n1.md" in md
        assert md.count("tests/spew.py` -> exit 0") == 6
        assert "Model notes" in md and md.count("- calling run") == 6
        assert os.path.isfile(os.path.join(fx.repo, "research_notes/astra_agent/notes/n1.md"))
        # the bad reply cost a model call but no step, and was nudged
        assert res["model_calls"] == 10
        assert any("not a single JSON object" in m["content"] for m in last)
        assert aa.extract_json("x {\"tool\": \"a\"} y")["tool"] == "a"
        assert aa.extract_json("") is None and aa.extract_json("[1,2]") is None


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception:  # noqa: BLE001
            failed += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
