from nose import tools
from os import path

from ddcheck.checkpoints import load_json
from ddcheck.types import Checkpoint



JSON_FILE = path.join(path.dirname(__file__), 'test.json')


def test_load_json_with_ipv6():
    tools.assert_equal(
        set([
            Checkpoint(url=u'http://127.0.0.1/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'127.0.0.1', type='A'),
            Checkpoint(url=u'http://127.0.0.2/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'127.0.0.2', type='A'),
            Checkpoint(url=u'http://127.0.0.3/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'127.0.0.3', type='A'),
            Checkpoint(url=u'http://[::1]/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'::1', type='AAAA'),
            Checkpoint(url=u'http://[::2]/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'::2', type='AAAA'),
            Checkpoint(url=u'http://[::3]/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'::3', type='AAAA'),
            Checkpoint(url=u'http://127.0.0.10/test/', host=u'dev.example.com', record=u'dev.example.com.', ip=u'127.0.0.10', type='A'),
            Checkpoint(url=u'http://127.0.0.20/test/', host=u'dev.example.com', record=u'dev.example.com.', ip=u'127.0.0.20', type='A'),
            Checkpoint(url=u'http://127.0.0.30/test/', host=u'dev.example.com', record=u'dev.example.com.', ip=u'127.0.0.30', type='A'),
        ]),

        set(load_json(JSON_FILE, ipv6=True)),
    )

def test_load_json_without_ipv6():
    tools.assert_equal(
        set([
            Checkpoint(url=u'http://127.0.0.1/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'127.0.0.1', type='A'),
            Checkpoint(url=u'http://127.0.0.2/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'127.0.0.2', type='A'),
            Checkpoint(url=u'http://127.0.0.3/health_check/', host=u'test.example.com', record=u'test.example.com.', ip=u'127.0.0.3', type='A'),
            Checkpoint(url=u'http://127.0.0.10/test/', host=u'dev.example.com', record=u'dev.example.com.', ip=u'127.0.0.10', type='A'),
            Checkpoint(url=u'http://127.0.0.20/test/', host=u'dev.example.com', record=u'dev.example.com.', ip=u'127.0.0.20', type='A'),
            Checkpoint(url=u'http://127.0.0.30/test/', host=u'dev.example.com', record=u'dev.example.com.', ip=u'127.0.0.30', type='A'),
        ]),

        set(load_json(JSON_FILE, ipv6=False)),
    )

