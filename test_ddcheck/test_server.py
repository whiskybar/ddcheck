from nose import tools

import eventlet

from ddcheck.resolver import Checkpoint
from ddcheck.server import check_url

def test_non_existing_host_get_to_failed():
    checkpoint = Checkpoint(url='http://127.0.0.1/', host='this.really.does.not.exist', record='this.really.does.not.exist.', ip='127.0.0.1', type='A')

    failed = eventlet.Queue()
    check_url(checkpoint, failed, [], 100)

    tools.assert_equals([checkpoint], list(failed.queue))

