"""No residual-utilization relaxation can admit resident or scoped processes."""

from gpu.orch_combined_l1_dev_repair import settling_only
from gpu.orch_rich_hot_a100_minor_scan import minor_from_documents


def report():
    return dict(gpu=dict(uuid='GPU-idle', memory_used_mib=0), blocking_reasons=['device_not_idle'],
        compute_processes=[dict(gpu_uuid='GPU-peer', pid=463012)])


def test_waits_for_new_clear_scan_only_with_zero_memory_and_no_target_process():
    assert settling_only(report())
    for key, value in [('memory_used_mib', 1), ('uuid', 'GPU-peer')]:
        document = report()
        document['gpu'][key] = value
        assert not settling_only(document)
    document = report()
    document['blocking_reasons'].append('open_device_pid:463012')
    assert not settling_only(document)
    document['blocking_reasons'][-1] = 'partial_or_exact_uuid_reservation:463012'
    assert not settling_only(document)


def test_observed_a100_index_minor_permutation_not_pid_whitelist():
    documents = [f'GPU UUID: GPU-physical{index}\nDevice Minor: {minor}\n'
        for index, minor in enumerate((3, 2, 1, 0))]
    assert minor_from_documents(documents, 'GPU-physical0') == 3
    assert minor_from_documents(documents, 'GPU-physical1') == 2
    assert minor_from_documents(documents, 'GPU-physical3') == 0
