import os
from nose import tools, SkipTest
from mock import MagicMock, patch
import dns.resolver
from dynect.DynectDNS import DynectRest

from ddcheck.dyndns import resolve_ips, checkpoint, remove_records, _dig


class FakeDnsAnswer(list):
    def __init__(self, data, name):
        self.rrset = MagicMock()
        self.rrset.name.to_text.return_value = name
        super(FakeDnsAnswer, self).__init__([MagicMock(address = i) for i in data])

@patch('ddcheck.dyndns._dig')
def test_resolve_ips(dig):
    dig.side_effect = [
            FakeDnsAnswer(['173.194.70.104', '173.194.70.147', '173.194.70.106', '173.194.70.99'], name='www.google.com.'),
            FakeDnsAnswer(['93.184.216.119'], name='www.example.com.'),
            FakeDnsAnswer(['23.51.166.151'], name='e7086.b.akamaiedge.net.'),

    ]
    tools.assert_equal(
        set(
            [
                checkpoint(url='http://173.194.70.104/', host='www.google.com', record='www.google.com.', ip='173.194.70.104'),
                checkpoint(url='http://173.194.70.147/', host='www.google.com', record='www.google.com.', ip='173.194.70.147'),
                checkpoint(url='http://173.194.70.106/', host='www.google.com', record='www.google.com.', ip='173.194.70.106'),
                checkpoint(url='http://173.194.70.99/', host='www.google.com', record='www.google.com.', ip='173.194.70.99'),
                checkpoint(url='http://93.184.216.119/test/', host='www.example.com', record='www.example.com.', ip='93.184.216.119'),
                checkpoint(url='http://23.51.166.151/health/', host='web.mit.edu', record='e7086.b.akamaiedge.net.', ip='23.51.166.151')
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


class TestDynDns():

    def setUp(self):
        self.customer_name = os.environ.get('TEST_DYNDNS_CUSTOMER_NAME')
        self.user_name = os.environ.get('TEST_DYNDNS_USER_NAME')
        self.password = os.environ.get('TEST_DYNDNS_PASSWORD')
        self.zone = os.environ.get('TEST_DYNDNS_ZONE')
        if not all((self.customer_name, self.user_name, self.password, self.zone)):
            raise SkipTest('Please set env variables TEST_DYNDNS_CUSTOMER_NAME, TEST_DYNDNS_USER_NAME, TEST_DYNDNS_PASSWORD and TEST_DYNDNS_ZONE.')
        arguments = {
            'customer_name': self.customer_name,
            'user_name': self.user_name,
            'password': self.password,
        }
        self.rest_iface = DynectRest()
        self.rest_iface.execute('/Session/', 'POST', arguments)
        self.rest_iface.execute('/Node/%s/root.%s/' % (self.zone, self.zone), 'DELETE')
        self.rest_iface.execute('/Node/%s/cname1.%s/' % (self.zone, self.zone), 'DELETE')
        self.rest_iface.execute('/Node/%s/cname2.%s/' % (self.zone, self.zone), 'DELETE')
        self.rest_iface.execute('/ARecord/%s/root.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'address': '127.0.0.1'}, 'ttl': 10})
        self.rest_iface.execute('/ARecord/%s/root.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'address': '127.0.0.2'}, 'ttl': 10})
        self.rest_iface.execute('/ARecord/%s/root.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'address': '127.0.0.3'}, 'ttl': 10})
        self.rest_iface.execute('/ARecord/%s/root.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'address': '127.0.0.4'}, 'ttl': 10})
        self.rest_iface.execute('/CNAMERecord/%s/cname1.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'cname': 'root.%s.' % self.zone}, 'ttl': 10})
        self.rest_iface.execute('/CNAMERecord/%s/cname2.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'cname': 'cname1.%s.' % self.zone}, 'ttl': 10})
        self.rest_iface.execute('/Zone/%s/' % self.zone, 'PUT', {'publish': 'true'})

    def test_remove_records(self):
        remove_records(
            [
                checkpoint(url='http://127.0.0.1/health/', host='cname2.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.1'),
                checkpoint(url='http://127.0.0.4/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4'),
                checkpoint(url='http://127.0.0.104/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4'), # non existent
            ],
            {
                'customer_name': self.customer_name,
                'user_name': self.user_name,
                'password': self.password,
            }
        )
        tools.assert_equal(
            set([
                '127.0.0.2',
                '127.0.0.3',
            ]),
            set([
                self.rest_iface.execute(url, 'GET')['data']['rdata']['address']
                for url in
                self.rest_iface.execute('/ARecord/%s/root.%s/' % (self.zone, self.zone), 'GET')['data']
            ])

        )
        tools.assert_equal(
            [{u'cname': u'root.pantheondnstestdomain.com.'}],
            [
                self.rest_iface.execute(url, 'GET')['data']['rdata']
                for url in
                self.rest_iface.execute('/CNAMERecord/%s/cname1.%s/' % (self.zone, self.zone), 'GET')['data']
            ]
        )
        tools.assert_equal(
            [{u'cname': u'cname1.pantheondnstestdomain.com.'}],
            [
                self.rest_iface.execute(url, 'GET')['data']['rdata']
                for url in
                self.rest_iface.execute('/CNAMERecord/%s/cname2.%s/' % (self.zone, self.zone), 'GET')['data']
            ]
        )



