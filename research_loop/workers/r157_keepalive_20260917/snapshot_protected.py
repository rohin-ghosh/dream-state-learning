"""Collect parent-safe metadata for the two already-armed protected handoffs."""

import datetime
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''
import hashlib,json,re,time
from pathlib import Path

def read(path):
    return json.loads(path.read_bytes())

def receipt(path):
    return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

report={"observed_unix":time.time(),"lives":{}}
for label in ("run1","pilot"):
    control=Path("/localhome/local-rohing")/f"orch_r157_keepalive_{label}_20260917_attempt2"
    staged=read(control/"STAGED.json")
    for attempt in (1,2):
        readmission=control.with_name(f"orch_r157_keepalive_{label}_20260917_readmit{attempt}")
        if (readmission/"READMISSION.json").exists():control=readmission
    config_path=control/"GUARD.json"
    if not config_path.exists():config_path=Path(staged["old_config"])
    config=read(config_path)
    plan=read(Path(config["plan_path"]))
    root=Path(plan["root"])
    item={"control":str(control),"root":str(root),"configured_wall":plan["hard_end_unix"],"events":[],"receipts":{},"natives":[]}
    paths=sorted(path for path in (root/"stream/records").glob("*.json") if re.fullmatch(r"[0-9]{20}\.json",path.name))
    latest=read(paths[-1]); document=latest["document"]
    item["latest"]={"index":latest["index"],"kind":latest["kind"],"mtime":paths[-1].stat().st_mtime,"optimizer_step":document.get("optimizer_step")}
    for path in reversed(paths):
        record=read(path)
        if record["kind"] in ("WALL_EXTENDED","LOADED"):
            item["events"].append(dict(receipt(path),index=record["index"],kind=record["kind"],mtime=path.stat().st_mtime,after_current_stage=path.stat().st_mtime>=staged["staged_unix"]))
            if record["kind"]=="WALL_EXTENDED":break
    for name in ("BOUNDARY","LEASE_BUDGET","READMISSION","OLD_STOPPED","SUPERVISOR_STARTED","ADMISSION","LAUNCH","HANDOFF_FAILED","EXIT","SERVICE_EXIT"):
        path=control/(name+".json")
        if path.exists():item["receipts"][name]=receipt(path)
    for process in Path("/proc").iterdir():
        if not process.name.isdecimal():continue
        try:
            argv=process.joinpath("cmdline").read_bytes().rstrip(b"\0").decode().split("\0")
            if not argv or Path(argv[0]).name not in ("python","python3"):continue
            if "gpu.orch_r125_continual_guard" not in argv or "native" not in argv or "--config" not in argv:continue
            bound=argv[argv.index("--config")+1]
            if bound not in (str(config_path),staged["old_config"]):continue
            fields=process.joinpath("stat").read_text().rsplit(") ",1)[1].split()
            item["natives"].append({"pid":int(process.name),"start_ticks":fields[19],"state":fields[0],"config":bound})
        except (OSError,ValueError,IndexError):pass
    report["lives"][label]=item
print(json.dumps(report,sort_keys=True))
'''


def main():
    command = ['bash', 'gpu/ovx3_ssh.sh', "python3 - <<'R157_METADATA'\n" + REMOTE + '\nR157_METADATA']
    result = subprocess.run(command, text=True, capture_output=True, timeout=45, check=True)
    report = json.loads(result.stdout)
    stamp = datetime.datetime.fromtimestamp(report['observed_unix'], datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = Path(__file__).parent / ('STATUS_' + stamp + '.json')
    with output.open('x') as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'report': report}, sort_keys=True))


if __name__ == '__main__':
    main()
