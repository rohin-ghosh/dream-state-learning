"""R227: diagnostics never remove child targets; technical provenance stays native."""

from pathlib import Path
import time

from gpu import r205_runtime as runtime
from gpu.r226_caption_runtime import ASSIGNMENTS, bounded_runtime


FILTER_KEYS = ('code_target_filter', 'learn_review_filter', 'content_target_filter',
    'prose_target_filter', 'question_target_filter', 'fabricated_speaker_filter')
POLICY = 'R227_CHILD_TARGET_DIAGNOSTICS_ONLY_V1'


def caption_binding(plan):
    name = Path(plan['source_root']).parent.name
    if name not in ASSIGNMENTS or plan['physical'] != ASSIGNMENTS[name][0]:
        raise ValueError('exact_five_caption_identities_and_devices')
    if any(key in scope for scope in (plan, plan['think_act_learn']) for key in FILTER_KEYS):
        raise ValueError('R227_no_semantic_or_child_review_exclusions')
    if plan['new_presentations'] != 16 or 'plasticity' in plan:
        raise ValueError('unchanged_checkpoint51_baseline_learning_recipe')
    return name, '/tmp/r226-caption-' + str(plan['physical']) + '.sock'


def diagnostics(rows):
    from organism_v6.orch_r194_code_target_filter import scan_target as code_scan
    from organism_v6.orch_r203_prose_target_filter import scan_target as prose_scan
    from organism_v6.orch_r225_content_target_filter import scan_target as content_scan
    from organism_v6.orch_r220_speaker_target_filter import speaker_labels
    checks = []
    for row in rows:
        check = dict(segment=row['segment'], source_sha256=row['source_sha256'])
        try:
            text = row['target']
            check.update(content=content_scan(text), prose=prose_scan(text),
                fullwidth_code=code_scan(text), speaker_labels=speaker_labels(text),
                cjk_characters=sum(0x3400 <= ord(character) <= 0x9fff for character in text))
        except Exception as error:
            check['diagnostic_error'] = type(error).__name__
        checks.append(check)
    return dict(policy=POLICY, checks=checks, candidate_count=len(rows),
        semantic_excluded_rows=0, raw_modified=False, diagnostics_only=True,
        receipt_quality_gate=False, child_review_exclusion=False,
        semantic_correctness_claimed=False, technical_provenance_checks_retained=True)


def make_sleep_hook(original, inspect=diagnostics):
    def sleep(child, new_rows, old_rows, anchors, record):
        try:
            evidence = inspect(new_rows)
        except Exception as error:
            evidence = dict(policy=POLICY, diagnostics_only=True, semantic_excluded_rows=0,
                candidate_count=len(new_rows), diagnostic_error=type(error).__name__)
        record('R227_TARGET_METRICS', evidence)
        return original(child, new_rows, old_rows, anchors, record)
    return sleep


def main():
    original_install, original_command = runtime.install_runtime, runtime.contained_command

    def install(plan):
        from gpu.ny_caption_life import activate
        name, socket_path = caption_binding(plan)
        runtime.receive_peer = lambda driver: None
        original_install(plan)
        runtime.native.NativeChild.sleep = make_sleep_hook(runtime.native.NativeChild.sleep)
        activate(socket_path, max_act_attempts=3)

    def command(config_path, mode):
        from gpu.orch_r125_continual_guard import validate
        _, plan = validate(config_path)
        caption_binding(plan)
        return bounded_runtime(original_command(config_path, mode), plan['hard_end_unix'], time.time())

    runtime.MODULE = 'gpu.r227_caption_runtime'
    runtime.install_runtime, runtime.contained_command = install, command
    runtime.main()


if __name__ == '__main__':
    main()
