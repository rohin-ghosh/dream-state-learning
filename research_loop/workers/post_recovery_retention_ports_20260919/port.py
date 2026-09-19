"""Emit apply_patch input using only the exact phase2 edits and variant context."""

import difflib

from prepare import FILES, HERE, PHASE2, VARIANTS


def reference_edits():
    edits = {name: [] for name in FILES}
    name, hunk = None, []

    def consume():
        position = 0
        while position < len(hunk):
            if hunk[position].startswith(' '):
                position += 1
                continue
            start = position
            while position < len(hunk) and hunk[position][:1] in ('-', '+'):
                position += 1
            old = ''.join(line[1:] for line in hunk[start:position] if line.startswith('-'))
            new = ''.join(line[1:] for line in hunk[start:position] if line.startswith('+'))
            prefix = []
            for line in reversed(hunk[:start]):
                if not line.startswith(' '):
                    break
                prefix.insert(0, line[1:])
            suffix = []
            for line in hunk[position:]:
                if not line.startswith(' '):
                    break
                suffix.append(line[1:])
            edits[name].append((prefix, old, new, suffix))

    for line in (PHASE2 / 'REPAIR.patch').read_text().splitlines(keepends=True):
        if line.startswith('--- a/'):
            if hunk:
                consume()
            name, hunk = line[len('--- a/'):].strip(), []
        elif line.startswith('+++ b/'):
            continue
        elif line.startswith('@@'):
            if hunk:
                consume()
            hunk = []
        else:
            hunk.append(line)
    if hunk:
        consume()
    return edits


def port_text(before, edits):
    after = before
    for prefix, old, new, suffix in edits:
        if old == '             compaction_threshold=None, action_policy=None):\n' and old not in after:
            old = old.replace('action_policy=None)', 'action_policy=None, interrupt=None)')
            new = new.replace('action_policy=None, retained_parent_event_id=None)',
                'action_policy=None, interrupt=None, retained_parent_event_id=None)')
        matched = False
        for prefix_count in range(len(prefix), -1, -1):
            for suffix_count in range(len(suffix), -1, -1):
                leading = ''.join(prefix[-prefix_count:]) if prefix_count else ''
                trailing = ''.join(suffix[:suffix_count])
                target = leading + old + trailing
                if target and after.count(target) == 1:
                    after = after.replace(target, leading + new + trailing, 1)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            raise ValueError('phase2_edit_requires_unambiguous_existing_variant_context: ' + repr(old))
    return after


def main():
    edits = reference_edits()
    application = ['*** Begin Patch\n']
    for life in VARIANTS:
        delta = []
        for relative in FILES:
            before = (HERE / life / 'preimage' / relative).read_text()
            after = port_text(before, edits[relative])
            difference = list(difflib.unified_diff(before.splitlines(keepends=True),
                after.splitlines(keepends=True), fromfile='a/' + relative, tofile='b/' + relative))
            delta.extend(difference)
            application.append('*** Update File: ' + str(HERE / life / 'fork' / relative) + '\n')
            application.extend('@@\n' if line.startswith('@@') else line for line in difference[2:])
        (HERE / life / 'RETENTION.patch').write_text(''.join(delta))
    application.append('*** End Patch\n')
    (HERE / 'APPLY_PORTS.patch').write_text(''.join(application))
    print('Exact phase2 delta emitted for five variants; existing interrupt arguments retained.')


if __name__ == '__main__':
    main()
