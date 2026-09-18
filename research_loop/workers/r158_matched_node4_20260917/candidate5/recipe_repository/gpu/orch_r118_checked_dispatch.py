"""Launch a dispatcher only after every bounded CPU preflight succeeds."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def launch(request, *, run=subprocess.run, spawn=subprocess.Popen):
    output = Path(request["output"])
    if not request["preflight_commands"]:
        raise ValueError("explicit_preflight_required")
    if not 0 < request["preflight_timeout_seconds"] <= 120:
        raise ValueError("bounded_preflight_timeout")
    output.mkdir(exist_ok=False)
    environment = dict(os.environ, **request["env"])
    write_new(output / "START.json", dict(request=request, started_unix=time.time()))
    try:
        for index, command in enumerate(request["preflight_commands"]):
            result = run(command, cwd=request["cwd"], env=environment,
                         stdin=subprocess.DEVNULL, capture_output=True, text=True,
                         timeout=request["preflight_timeout_seconds"], check=True)
            write_new(output / f"PREFLIGHT_{index:02d}.json",
                      dict(command=command, returncode=result.returncode,
                           stdout=result.stdout, stderr=result.stderr))
    except Exception as error:
        write_new(output / "PREFLIGHT_FAILED.json",
                  dict(error=type(error).__name__ + ": " + str(error),
                       dispatcher_started=False))
        raise
    with (output / "DISPATCH.log").open("xb") as log:
        process = spawn(request["command"], cwd=request["cwd"], env=environment,
                        stdin=subprocess.DEVNULL, stdout=log,
                        stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(pid=process.pid, command=request["command"],
                   started_unix=time.time(), status="STARTED_NOT_BOOTSTRAP_PROOF")
    write_new(output / "DISPATCH_LAUNCH.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(launch(json.loads(args.request.read_text())), sort_keys=True))


if __name__ == "__main__":
    main()
