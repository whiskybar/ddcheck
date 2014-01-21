from nose import tools

from ddcheck.utils import get_zone



def test_get_zone():
    tools.assert_equals("example.com", get_zone("example.com."))
    tools.assert_equals("example.com", get_zone("example.com"))
    tools.assert_equals("example.com", get_zone("log.sub-domain.there.example.com."))
    tools.assert_equals("example.com", get_zone("www.example.com"))

