"""Bind brain's completed R181 dispatch without altering five armed bindings."""

from pathlib import Path

import r181_journal_operator as overlay


if __name__ == '__main__':
    overlay.operator.REMOTE = Path('/localhome/local-rohing/orch_r181_node1_20260917/journal_overlay/brain')
    overlay.operator.module = overlay.module
    overlay.operator.copy_source = overlay.copy_source
    overlay.operator.verify_source_copy = overlay.verify_source_copy
    overlay.operator.main()
