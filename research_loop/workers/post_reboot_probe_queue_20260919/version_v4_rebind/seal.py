"""Create a CPU-only, write-once release receipt; never activate this candidate."""

import argparse
from pathlib import Path

import admission as rules
import probe_runtime as runtime


WORKER = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    names = {path.name for path in WORKER.glob("*.py")}
    names.update({"policy.json", "scientific_inputs.json", "history.json", "capsules.json", "README.md",
        "activation.example.json", "rebind.example.json", "NEXT_ENTRY.json", "NEXT_SOURCE_RECEIPT.json",
        "CONSTRUCT_NEXT_CAPSULE.sh", "ACTIVATE_FOREGROUND.sh", "POLICY_ADJUDICATION.md", "CACHE_REPAIR.md", "RUNTIME_REBIND.md"})
    payload = dict(schema="INACTIVE_QUEUE_SOURCE_FREEZE_V1", files={name: runtime.sha(WORKER / name) for name in sorted(names)},
        canonical_policy_sha256=rules.digest(runtime.read(WORKER / "policy.json")), automatic_launch=False,
        execution_performed=False, boot_installation="BLOCKED_UNINSTALLED", credential_bootstrap="UNVERIFIED")
    runtime.write_once(args.output, payload)
    print(rules.canonical(dict(source_freeze_file_sha256=runtime.sha(args.output),
        canonical_policy_sha256=payload["canonical_policy_sha256"], files=len(names), activated=False)))


if __name__ == "__main__":
    main()
