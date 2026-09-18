"""Transport only this pinned operator package using the existing A100 wrapper."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
REMOTE = "/localhome/local-rohing/orch_r179_node1_20260917_attempt1"
PYTHON = "/localhome/local-rohing/v2/venv/bin/python"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_once(path, document):
    with path.open("x") as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write("\n")


def bootstrap():
    tested = subprocess.run([sys.executable, "-B", str(HERE / "test_node1_operator.py"), "-v"],
                            text=True, capture_output=True)
    log = tested.stdout + tested.stderr
    if tested.returncode != 0:
        print(log, file=sys.stderr)
        raise RuntimeError("local_operator_tests_failed_no_upload")
    matched = re.search(r"Ran (\d+) tests", log)
    if not matched:
        raise RuntimeError("actual_test_count_missing")
    receipt = dict(returncode=tested.returncode, passed=int(matched.group(1)), observed_unix=time.time(),
        operator_sha256=sha((HERE / "node1_operator.py").read_bytes()),
        test_sha256=sha((HERE / "test_node1_operator.py").read_bytes()),
        test_log_sha256=sha(log.encode()))
    stamp = str(time.time_ns())
    (HERE / ("OPERATOR_CPU_" + stamp + ".log")).write_text(log)
    write_once(HERE / ("OPERATOR_CPU_" + stamp + ".json"), receipt)
    files = {
        "node1_operator.py": (HERE / "node1_operator.py").read_bytes(),
        "test_node1_operator.py": (HERE / "test_node1_operator.py").read_bytes(),
        "receiving_cpu.py": (HERE / "receiving_cpu.py").read_bytes(),
        "r144_base.py": (REPOSITORY / "gpu/orch_r144_a100_a40r_target_rollout.py").read_bytes(),
        "policy.py": (REPOSITORY / "gpu/orch_r179_context_survival.py").read_bytes(),
        "BUILDER_SCOPE.json": (HERE.parent / "BUILDER_SCOPE.json").read_bytes(),
        "CPU_MAIN_1.log": (HERE.parent / "CPU_MAIN_1.log").read_bytes(),
        "PREPARED_NODE1.json": (HERE / "PREPARED_NODE1.json").read_bytes(),
        "LOCAL_CPU.json": json.dumps(receipt, sort_keys=True).encode(),
    }
    package = dict(files={name: sha(data) for name, data in files.items()}, created_unix=time.time())
    files["PACKAGE.json"] = json.dumps(package, sort_keys=True).encode()
    code = '''import base64,hashlib,json,os,socket,sys
from pathlib import Path
root=Path(sys.argv[1]); payload=json.load(sys.stdin)
assert socket.gethostname()=="[REDACTED_HOST]" and os.getuid()==1395
assert root==Path("/localhome/local-rohing/orch_r179_node1_20260917_attempt1/operator")
assert not root.exists()
decoded={name:base64.b64decode(value,validate=True) for name,value in payload["files"].items()}
assert sum(map(len,decoded.values()))<2*1024*1024
for name,data in decoded.items():
 assert Path(name).name==name and hashlib.sha256(data).hexdigest()==payload["hashes"][name]
root.mkdir(parents=True)
for name,data in decoded.items():
 with (root/name).open("xb") as stream: stream.write(data)
 (root/name).chmod(0o444)
print(json.dumps({"status":"OPERATOR_PACKAGE_RECEIVED","path":str(root),"files":payload["hashes"],"signals_sent":0}))
'''
    command = shlex.join(["env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1", PYTHON,
                          "-B", "-c", code, REMOTE + "/operator"])
    result = subprocess.run(["bash", "gpu/a100_ssh.sh", command], cwd=REPOSITORY, text=True,
        input=json.dumps(dict(files={name: base64.b64encode(data).decode() for name, data in files.items()},
                              hashes={name: sha(data) for name, data in files.items()})),
        capture_output=True, timeout=60)
    write_once(HERE / ("PACKAGE_TRANSFER_" + stamp + ".json"), dict(returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr, package=package))
    if result.returncode:
        raise RuntimeError("operator_package_transfer_failed:" + result.stderr[-2000:])
    print(result.stdout)


def operate(action, physical, seconds, background):
    command = shlex.join(["env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1", PYTHON, "-B",
        REMOTE + "/operator/node1_operator.py", action, "--physical", str(physical), "--seconds", str(seconds)])
    if background:
        if action != "handoff":
            raise ValueError("background_handoff_only")
        log = REMOTE + "/lanes/lane" + str(physical) + "/OPERATOR.log"
        command = "nohup " + command + " >" + shlex.quote(log) + " 2>&1 </dev/null & echo $!"
    result = subprocess.run(["bash", "gpu/a100_ssh.sh", command], cwd=REPOSITORY, text=True,
                            capture_output=True, timeout=240 if action == "stage" else 660)
    path = HERE / (action.upper() + "_LANE" + str(physical) + "_" + str(time.time_ns()) + ".json")
    write_once(path, dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                         background_dispatch=background, observed_unix=time.time()))
    print(json.dumps(dict(receipt=str(path), returncode=result.returncode,
                         stdout=result.stdout, stderr=result.stderr)))
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("bootstrap", "stage", "handoff", "observe"))
    parser.add_argument("--physical", type=int, choices=range(2, 8))
    parser.add_argument("--seconds", type=int, default=1800)
    parser.add_argument("--background", action="store_true")
    arguments = parser.parse_args()
    if arguments.action == "bootstrap":
        bootstrap()
    else:
        if arguments.physical is None:
            parser.error("--physical is required")
        operate(arguments.action, arguments.physical, arguments.seconds, arguments.background)


if __name__ == "__main__":
    main()
