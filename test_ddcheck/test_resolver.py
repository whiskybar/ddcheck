from nose import tools
from mock import MagicMock, patch
import dns.resolver

from ddcheck.resolver import resolve_ips, Checkpoint, dig



class FakeDnsAnswer(list):
    def __init__(self, data, name, type):
        self.rrset = MagicMock()
        self.rrset.name.to_text.return_value = name
        super(FakeDnsAnswer, self).__init__([MagicMock(address=i) for i in data])
        for i in self:
            i.to_text.return_value = i.address


def patched_dig(qname, rdtype, nameservers=None):
    if nameservers:
        nameservers = tuple(nameservers)
    print "Resolving %s, %s, %s" % (qname, rdtype, nameservers)
    return {
        ('www.google.com', 'A', ('8.8.8.8',)): FakeDnsAnswer(['173.194.70.104', '173.194.70.147', '173.194.70.106', '173.194.70.99'], name='www.google.com.', type='A'),
        ('www.google.com', 'A', None): FakeDnsAnswer(['173.194.70.104', '173.194.70.147', '173.194.70.106', '173.194.70.99'], name='www.google.com.', type='A'),
        ('www.google.com', 'AAAA', ('8.8.8.8',)): FakeDnsAnswer([], name='www.google.com.', type='AAAA'),
        ('www.google.com', 'AAAA', None): FakeDnsAnswer([], name='www.google.com.', type='AAAA'),

        ('www.example.com', 'A', ('9.9.9.9',)): FakeDnsAnswer(['93.184.216.119'], name='www.example.com.', type='A'),
        ('www.example.com', 'A', None): FakeDnsAnswer(['93.184.216.119'], name='www.example.com.', type='A'),
        ('www.example.com', 'AAAA', ('9.9.9.9',)): FakeDnsAnswer(['fe80::224:d7ff:fecd:6048', 'fe80::224:d7ff:fecd:6047'], name='www.example.com.', type='AAAA'),
        ('www.example.com', 'AAAA', None): FakeDnsAnswer(['fe80::224:d7ff:fecd:6048', 'fe80::224:d7ff:fecd:6047'], name='www.example.com.', type='AAAA'),

        ('web.mit.edu', 'A', ('10.10.10.10',)): FakeDnsAnswer(['23.51.166.151'], name='e7086.b.akamaiedge.net.', type='A'),
        ('web.mit.edu', 'A', None): FakeDnsAnswer(['23.51.166.151'], name='e7086.b.akamaiedge.net.', type='A'),
        ('e7086.b.akamaiedge.net', 'A', ('11.11.11.11',)): FakeDnsAnswer(['23.51.166.152'], name='e7086.b.akamaiedge.net.', type='A'),
        ('e7086.b.akamaiedge.net', 'AAAA', ('11.11.11.11',)): FakeDnsAnswer([], name='e7086.b.akamaiedge.net.', type='A'),
        ('web.mit.edu', 'AAAA', ('10.10.10.10',)): FakeDnsAnswer([], name='e7086.b.akamaiedge.net.', type='AAAA'),
        ('web.mit.edu', 'AAAA', None): FakeDnsAnswer([], name='e7086.b.akamaiedge.net.', type='AAAA'),

        ('google.com', 'NS', None): FakeDnsAnswer(["8.8.8.8"], name='', type='NS'),
        ('example.com', 'NS', None): FakeDnsAnswer(["9.9.9.9"], name='', type='NS'),
        ('mit.edu', 'NS', None): FakeDnsAnswer(["10.10.10.10"], name='', type='NS'),
        ('akamaiedge.net', 'NS', None): FakeDnsAnswer(["11.11.11.11"], name='', type='NS'),
    }.get((qname, rdtype, nameservers))

@patch('ddcheck.resolver.dig', new=patched_dig)
def test_resolve_ips():
    from ddcheck.resolver import dig
    tools.assert_equal(
        set(
            [
                Checkpoint(url='http://173.194.70.104/', host='www.google.com', record='www.google.com.', ip='173.194.70.104', type='A'),
                Checkpoint(url='http://173.194.70.147/', host='www.google.com', record='www.google.com.', ip='173.194.70.147', type='A'),
                Checkpoint(url='http://173.194.70.106/', host='www.google.com', record='www.google.com.', ip='173.194.70.106', type='A'),
                Checkpoint(url='http://173.194.70.99/', host='www.google.com', record='www.google.com.', ip='173.194.70.99', type='A'),
                Checkpoint(url='http://93.184.216.119/test/', host='www.example.com', record='www.example.com.', ip='93.184.216.119', type='A'),
                Checkpoint(url='http://[fe80::224:d7ff:fecd:6048]/test/', host='www.example.com', record='www.example.com.', ip='fe80::224:d7ff:fecd:6048', type='AAAA'),
                Checkpoint(url='http://[fe80::224:d7ff:fecd:6047]/test/', host='www.example.com', record='www.example.com.', ip='fe80::224:d7ff:fecd:6047', type='AAAA'),
                Checkpoint(url='http://23.51.166.152/health/', host='web.mit.edu', record='e7086.b.akamaiedge.net.', ip='23.51.166.152', type='A')
            ]
        ),
        set(
            resolve_ips(
                [
                    'http://www.google.com/',
                    'http://www.example.com/test/',
                    'http://web.mit.edu/health/', # CNAME
                ],
            )
        )
    )


@patch('ddcheck.resolver.dig', new=patched_dig)
def test_resolve_ips_ipv6_disabled():
    tools.assert_equal(
        set(
            [
                Checkpoint(url='http://173.194.70.104/', host='www.google.com', record='www.google.com.', ip='173.194.70.104', type='A'),
                Checkpoint(url='http://173.194.70.147/', host='www.google.com', record='www.google.com.', ip='173.194.70.147', type='A'),
                Checkpoint(url='http://173.194.70.106/', host='www.google.com', record='www.google.com.', ip='173.194.70.106', type='A'),
                Checkpoint(url='http://173.194.70.99/', host='www.google.com', record='www.google.com.', ip='173.194.70.99', type='A'),
                Checkpoint(url='http://93.184.216.119/test/', host='www.example.com', record='www.example.com.', ip='93.184.216.119', type='A'),
                Checkpoint(url='http://23.51.166.152/health/', host='web.mit.edu', record='e7086.b.akamaiedge.net.', ip='23.51.166.152', type='A')
            ]
        ),
        set(
            resolve_ips(
                [
                    'http://www.google.com/',
                    'http://www.example.com/test/',
                    'http://web.mit.edu/health/', # CNAME
                ],
                ipv6=False,
            )
        )
    )


