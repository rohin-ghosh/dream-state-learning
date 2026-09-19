"""Target-only sleep eligibility; never rewrites child history or the encoder."""

POLICY = 'R144_SPECIAL_TOKEN_TARGET_EXCLUSION_V1'
REJECTION = 'no_special_token_target_injection'


def encode_sleep_targets(new_rows, old_rows, tokenizer, context_limit, encoder):
    retained = {'NEW': [], 'REHEARSAL': []}
    encoded, excluded = {}, []
    for cohort, rows in (('NEW', new_rows), ('REHEARSAL', old_rows)):
        for row in rows:
            try:
                sample = encoder(row, tokenizer, context_limit)
            except ValueError as error:
                if error.args != (REJECTION,):
                    raise
                excluded.append(dict(source_sha256=row['source_sha256'],
                    cohort=cohort, reason=REJECTION, policy=POLICY))
                continue
            retained[cohort].append(row)
            encoded[row['source_sha256']] = sample
    return retained['NEW'], retained['REHEARSAL'], encoded, excluded
