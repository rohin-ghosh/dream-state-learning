"""Bind the unchanged R181 handoff to a journal-only successor revision."""

import hashlib
from pathlib import Path
import shutil
from types import SimpleNamespace

import r181_operator as operator


JOURNAL = 'gpu/orch_r125_stream_journal.py'
JOURNAL_SHA = 'd57c318baa509c009f12328b566f391f79a3948e497b6fdbc04bd2d1d274c9fd'
READY_NATIVE = {
    '09bc0214f96d57734d4c56fb59cfdb698dee917f51faebfcf46731df8ca3a50f',
    '53e27117a19d2bb2c824af03051ef1d887296ff24c263f2dcbe5161fbc42ef60',
    'c1bac2d2ef86fd5190e717d15aaa3aee61fc8fa98638aa43a8dcdc13f9081c32',
}
ORIGINAL_MODULE = operator.module


def patched_native(source, canonical):
    if hashlib.sha256(source.encode()).hexdigest() in READY_NATIVE:
        return source
    delta = ORIGINAL_MODULE(operator.HERE / 'r181_native_delta.py', 'original_r181_delta')
    return delta.patch(source, canonical)


def module(path, name):
    if Path(path) == operator.HERE / 'r181_native_delta.py':
        return SimpleNamespace(patch=patched_native)
    return ORIGINAL_MODULE(path, name)


def copy_source(original, destination, inventory, patched):
    operator.require(not destination.exists(), 'new_source_only')
    journal = operator.HERE / 'canonical_journal.py'
    operator.require(operator.sha(journal) == JOURNAL_SHA, 'Main_exact_journal_overlay')
    destination.mkdir()
    for directory in original.rglob('*'):
        if directory.is_dir():
            (destination / directory.relative_to(original)).mkdir(parents=True, exist_ok=True)
    for relative in inventory:
        old_path, new_path = original / relative, destination / relative
        new_path.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith('.py'):
            if relative == operator.NATIVE:
                new_path.write_text(patched)
            else:
                shutil.copyfile(journal if relative == JOURNAL else old_path, new_path)
            new_path.chmod(0o444)
        else:
            operator.os.link(old_path, new_path, follow_symlinks=False)
    for path in sorted(destination.rglob('*'), reverse=True):
        if path.is_dir():
            path.chmod(0o555)
    destination.chmod(0o555)


def verify_source_copy(original, copied, before, after):
    operator.require(set(after) == set(before), 'same_source_closure_native_and_journal_only')
    operator.require(after[JOURNAL]['sha256'] == JOURNAL_SHA, 'exact_successor_journal')
    operator.require(after[operator.NATIVE]['sha256'] in READY_NATIVE, 'exact_R181_successor_native')
    for relative, metadata in before.items():
        if relative.endswith('.py') and relative not in (operator.NATIVE, JOURNAL):
            operator.require(after[relative]['sha256'] == metadata['sha256'], 'unchanged_other_python')
        elif not relative.endswith('.py'):
            operator.require(after[relative] == metadata, 'opaque_noncode_same_inode_size_mode')
    operator.require(operator.source_inventory(original) == before, 'original_source_unchanged')


def main():
    operator.REMOTE = Path('/localhome/local-rohing/orch_r181_node1_20260917/journal_overlay')
    operator.module = module
    operator.copy_source = copy_source
    operator.verify_source_copy = verify_source_copy
    operator.main()


if __name__ == '__main__':
    main()
