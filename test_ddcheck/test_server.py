from nose import tools
import responses
import eventlet

from ddcheck.resolver import Checkpoint
from ddcheck.server import check_url

def test_non_existing_host_get_to_failed():
    checkpoint = Checkpoint(url='http://127.0.0.1/', host='this.really.does.not.exist', record='this.really.does.not.exist.', ip='127.0.0.1', type='A')

    failed = eventlet.Queue()
    error_codes = []
    check_url(checkpoint, failed, error_codes, 100)

    tools.assert_equals([checkpoint], list(failed.queue))

@responses.activate
def test_error_not_in_error_codes_should_pass():
    checkpoint = Checkpoint(url='http://199.16.156.6/api/1/foobar', host='twitter.com', record='twitter.com.', ip='199.16.156.6', type='A')

    responses.add(responses.GET, 'http://199.16.156.6/api/1/foobar',
                  body='{"error": "not found"}', status=404,
                  content_type='application/json')

    failed = eventlet.Queue()
    error_codes = []

    check_url(checkpoint, failed, error_codes, 100)
    tools.assert_equals([], list(failed.queue))

@responses.activate
def test_when_an_error_is_specified_put_checkpoint_to_failures():
    checkpoint = Checkpoint(url='http://199.16.156.6/api/1/foobar', host='twitter.com', record='twitter.com.', ip='199.16.156.6', type='A')

    responses.add(responses.GET, 'http://199.16.156.6/api/1/foobar',
                  body='{"error": "not found"}', status=404,
                  content_type='application/json')

    failed = eventlet.Queue()
    error_codes = [404]

    check_url(checkpoint, failed, error_codes, 100)
    tools.assert_equals([checkpoint], list(failed.queue))

