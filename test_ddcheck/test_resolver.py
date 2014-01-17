from nose import tools
from mock import MagicMock, patch
import dns.resolver

from ddcheck.resolver import resolve_ips, Checkpoint, _dig



class FakeDnsAnswer(list):
    def __init__(self, data, name):
        self.rrset = MagicMock()
        self.rrset.name.to_text.return_value = name
        super(FakeDnsAnswer, self).__init__([MagicMock(address = i) for i in data])


@patch('ddcheck.resolver._dig')
def test_resolve_ips(dig):
    dig.side_effect = [
            FakeDnsAnswer(['173.194.70.104', '173.194.70.147', '173.194.70.106', '173.194.70.99'], name='www.google.com.'),
            FakeDnsAnswer(['93.184.216.119'], name='www.example.com.'),
            FakeDnsAnswer(['23.51.166.151'], name='e7086.b.akamaiedge.net.'),

    ]
    tools.assert_equal(
        set(
            [
                Checkpoint(url='http://173.194.70.104/', host='www.google.com', record='www.google.com.', ip='173.194.70.104'),
                Checkpoint(url='http://173.194.70.147/', host='www.google.com', record='www.google.com.', ip='173.194.70.147'),
                Checkpoint(url='http://173.194.70.106/', host='www.google.com', record='www.google.com.', ip='173.194.70.106'),
                Checkpoint(url='http://173.194.70.99/', host='www.google.com', record='www.google.com.', ip='173.194.70.99'),
                Checkpoint(url='http://93.184.216.119/test/', host='www.example.com', record='www.example.com.', ip='93.184.216.119'),
                Checkpoint(url='http://23.51.166.151/health/', host='web.mit.edu', record='e7086.b.akamaiedge.net.', ip='23.51.166.151')
            ]
        ),
        set(
            resolve_ips(
                [
                    'http://www.google.com/',
                    'http://www.example.com/test/',
                    'http://web.mit.edu/health/', # CNAME
                ],
                ['8.8.8.8'],
            )
        )
    )


