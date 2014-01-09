from nose import tools

from ddcheck.dyndns import resolve_ips, checkpoint


# mock _dig
def test_resolve_ips():
    tools.assert_equal(
        set(
            [
                checkpoint(url='http://173.194.70.104/', host='www.google.com'),
                checkpoint(url='http://173.194.70.147/', host='www.google.com'),
                checkpoint(url='http://173.194.70.106/', host='www.google.com'),
                checkpoint(url='http://173.194.70.103/', host='www.google.com'),
                checkpoint(url='http://173.194.70.99/', host='www.google.com'),
                checkpoint(url='http://173.194.70.105/', host='www.google.com'),
                checkpoint(url='http://173.194.70.18/', host='gmail.com'),
                checkpoint(url='http://173.194.70.17/', host='gmail.com'),
                checkpoint(url='http://173.194.70.83/', host='gmail.com'),
                checkpoint(url='http://173.194.70.19/', host='gmail.com'),
                checkpoint(url='http://93.184.216.119/test/', host='www.example.com'),
            ]
        ),
        set(
            resolve_ips(
                [
                    'http://www.google.com/',
                    'http://gmail.com/',
                    'http://www.example.com/test/',
                ],
                ['8.8.8.8'],
            )
        )
    )


