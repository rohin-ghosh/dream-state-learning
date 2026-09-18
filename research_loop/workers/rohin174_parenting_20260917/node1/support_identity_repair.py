"""NODE1 scanner-only repair: process titles are not kernel identities."""

from pathlib import Path


SCANNER = 'gpu/orch_rich_hot_a100_scan.py'
MINOR = 'gpu/orch_rich_hot_a100_minor_scan.py'
ORIGINAL_HASHES = {
    SCANNER: '9902c38ecadeaa06bc02abf184f6a04025a289868f809b63aace5148cd95575e',
    MINOR: 'f7136608f4b3fca051b3852a006abf86b704dbf1cfe882f6b8c3b43704ec387e',
}
IDENTITY_HELPER = '''def same_process_identity(before, after):
    keys = ('pid', 'uid', 'start_ticks', 'boot_id')
    return all(key in before and key in after and before[key] == after[key] for key in keys)


'''


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError('exact_scanner_repair_seam')
    return source.replace(before, after, 1)


def patch(relative, source):
    if relative == SCANNER:
        source = replace_once(source, 'def service(path):', IDENTITY_HELPER + 'def service(path):')
        source = replace_once(source, 'before[process_id] != after',
                              'not same_process_identity(before[process_id], after)')
        return replace_once(source, "('start_ticks', 'uid', 'command_sha256'))):",
                             "('start_ticks', 'uid'))):")
    if relative == MINOR:
        source = replace_once(source, 'if before != after:',
                              'if not pinned.same_process_identity(before, after):')
        return replace_once(source, "if process.get('pinned_identity') != after:",
                             "if not pinned.same_process_identity(process.get('pinned_identity', {}), after):")
    raise ValueError('only_two_scanner_files')


def candidate(root):
    return {relative: patch(relative, (Path(root) / relative).read_text())
            for relative in ORIGINAL_HASHES}
