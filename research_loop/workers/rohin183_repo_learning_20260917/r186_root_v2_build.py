"""New path-only candidate; freeze all consumed runtime bytes, never reuse raw."""

import json
from pathlib import Path
import tarfile

from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import ARMS, OWN
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write, digest, require


ROOT = Path(__file__).resolve().parent
REMOTE = '/localhome/local-rohing/orch_r153_r186_c2_plasticity_20260917'


def replace_once(raw, before, after):
    require(raw.count(before.encode()) == 1, 'exact_repair_token:' + before)
    return raw.replace(before.encode(), after.encode(), 1)


def build():
    source_summary = {}
    original_receive = (ROOT / 'r186_receive.py').read_bytes()
    receive = original_receive.replace("(label + '1')".encode(), "(label + '2')".encode())
    require(original_receive.count(b"(label + '1')") == 2, 'two_exact_root_checks')
    receive = replace_once(receive, "label + '_1.sock'", "label + '_2.sock'")
    receive = replace_once(receive, "    raw = ROOT / 'raw'\n",
        "    raw = ROOT / 'raw'\n    from gpu.orch_r153_community_transport import remote_root\n"
        "    require(remote_root(str(raw)) == raw, 'actual_bridge_root_accepted_before_copy')\n")
    write(ROOT / 'r186_root_v2_receive.py', receive)
    for label in ARMS:
        original_pinfile = ROOT / ('R186_' + label.upper() + '_SOURCE.json')
        original = json.loads(original_pinfile.read_bytes())
        files = {}
        for name, expected in original['source_pins'].items():
            raw = (ROOT / ('r186_' + label + '_source') / name).read_bytes()
            require(digest(raw) == expected, 'consumed_source_immutable:' + name)
            files[name] = raw
        helper_name = OWN + '/r186_copy.py'
        helper = replace_once(files[helper_name],
            '/localhome/local-rohing/orch_r186_c2_plasticity_20260917', REMOTE)
        helper = replace_once(helper, "OWN.replace('/', '.') + '.test_r186_copy')",
            "OWN.replace('/', '.') + '.test_r186_copy', OWN.replace('/', '.') + '.test_r186_root_v2')")
        files[helper_name] = helper
        files[OWN + '/test_r186_root_v2.py'] = (ROOT / 'test_r186_root_v2.py').read_bytes()
        unchanged = {name: expected for name, expected in original['source_pins'].items() if name != helper_name}
        require(all(digest(files[name]) == expected for name, expected in unchanged.items()),
            'all_consumed_runtime_bytes_preserved')
        source = ROOT / ('r186_root_v2_' + label + '_source')
        require(not source.exists(), 'fresh_repair_source')
        for name, raw in files.items():
            write(source / name, raw)
        manifest = dict(original, schema='R186_ROOT_REPAIR_SOURCE_V2',
            source_pins={name: digest(raw) for name, raw in files.items()},
            consumed_source_manifest_sha256=digest(original_pinfile.read_bytes()),
            unchanged_consumed_pins=unchanged, remote_root=REMOTE,
            source_delta='owned_root_and_test_list_only_plus_root_regression')
        pinfile = ROOT / ('R186_ROOT_V2_' + label.upper() + '_SOURCE.json')
        write(pinfile, manifest)
        archive_path = ROOT / ('R186_ROOT_V2_' + label.upper() + '.tar.gz')
        with tarfile.open(archive_path, 'x:gz') as archive:
            archive.add(source, arcname='source')
            archive.add(pinfile, arcname='SOURCE.json')
            archive.add(ROOT / 'r186_root_v2_receive.py', arcname='receive.py')
            archive.add(ROOT / 'R186_SCOPE.md', arcname='SCOPE.md')
            archive.add(ROOT / 'R186_ROOT_FAILURE.md', arcname='SCOPE_REPAIR_ADDENDUM.md')
        source_summary[label] = dict(source_root=str(source), manifest_sha256=digest(pinfile.read_bytes()),
            archive=str(archive_path), archive_sha256=digest(archive_path.read_bytes()),
            source_file_count=len(files), runtime_files_unchanged=True)
    print(json.dumps(write(ROOT / 'R186_ROOT_V2_BUILD.json', source_summary), sort_keys=True))


if __name__ == '__main__':
    build()
