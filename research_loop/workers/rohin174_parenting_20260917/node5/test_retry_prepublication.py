from console_baseline import sha, write
from retry_prepublication import MODEL, candidate, consumed_request


def failed(tmp_path):
    directory=tmp_path/'parent_7'
    directory.mkdir()
    state=dict(request_count=7,response_count=7)
    write(directory/'SOURCE.json',state)
    write(directory/'API_REQUEST.json',dict(model=MODEL))
    write(directory/'RESULT.json',dict(status='PROVIDER_FAILED',error_type='HTTPError',error='HTTP Error 404',source_sha256=sha(directory/'SOURCE.json')))
    return directory,state


def test_same_failed_source_permits_one_candidate(tmp_path):
    directory,state=failed(tmp_path)
    assert candidate(directory,state)
    assert not candidate(directory,dict(state,request_count=8))


def test_publish_intent_never_retried(tmp_path):
    directory,state=failed(tmp_path)
    write(directory/'PUBLISH_INTENT.json',dict(message='uncertain'))
    assert not candidate(directory,state)


def test_retry_never_recurses(tmp_path):
    directory,state=failed(tmp_path)
    renamed=directory.with_name(directory.name+'_prepub_retry1')
    directory.rename(renamed)
    assert not candidate(renamed,state)


def test_consumed_source_never_reuses_same_directory_after_retry(tmp_path):
    unused, state = failed(tmp_path)
    attempts = [dict(source=state, result=dict(status='VALIDATION_FAILED'))]
    assert consumed_request(dict(attempts=[]), attempts, state)
    assert consumed_request(dict(attempts=attempts), [], dict(state, response_count=8))
    assert not consumed_request(dict(attempts=attempts), [], dict(state, request_count=8))
