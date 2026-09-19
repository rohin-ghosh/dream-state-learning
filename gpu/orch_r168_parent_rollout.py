"""Parent-only custody transaction; no native or provider signals."""


def handoff(operations):
    operations.preflight()
    handle = None
    successor = None
    try:
        with operations.quiesce() as handle:
            manifest = operations.settled()
            operations.preserve(manifest)
            handle.terminate()
        with operations.old_lock():
            operations.confirm_exit(manifest)
            successor = operations.start_successor()
            operations.verify_successor(successor)
            operations.record_started(successor)
        return successor
    except BaseException:
        if handle is not None and handle.terminated:
            operations.reconcile_failed_handoff(successor)
        raise
