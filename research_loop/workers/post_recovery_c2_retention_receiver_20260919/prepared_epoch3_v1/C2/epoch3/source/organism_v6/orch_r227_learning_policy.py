"""Prospective R227 policy; preserves historical rows and provenance checks."""

POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
SEMANTIC_FILTER_FIELDS = (
    'code_target_filter', 'learn_review_filter', 'prose_target_filter',
    'content_target_filter', 'question_target_filter', 'fabricated_speaker_filter',
)


def all_child_rows(config):
    if 'learn_row_policy' not in config:
        return False
    if config['learn_row_policy'] != POLICY:
        raise ValueError('known_learn_row_policy')
    return True


def effective_config(config):
    if not all_child_rows(config):
        return config
    return {key: value for key, value in config.items() if key not in SEMANTIC_FILTER_FIELDS}


def recipe_fields(config):
    if not all_child_rows(config):
        return {}
    return dict(learn_row_policy=POLICY, active_semantic_filters=[],
        semantic_row_exclusion=False, historical_row_annotations='PRESERVED_NOT_APPLIED',
        technical_provenance_and_encoding_checks=True)
