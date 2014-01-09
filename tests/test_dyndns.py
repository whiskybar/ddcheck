from nose import tools

from ddcheck import dyndns


def test_resolve_ips():
    tools.assert_equal(
        [],
        dyndns.resolve_ips(
            []
        )
    )


