import os
from nose import tools, SkipTest
from dynect.DynectDNS import DynectRest

from ddcheck.dyndns import DynDns
from ddcheck.resolver import Checkpoint



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
        self.rest_iface.execute('/AAAARecord/%s/root.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'address': '::1'}, 'ttl': 10})
        self.rest_iface.execute('/AAAARecord/%s/root.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'address': '::2'}, 'ttl': 10})
        self.rest_iface.execute('/CNAMERecord/%s/cname1.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'cname': 'root.%s.' % self.zone}, 'ttl': 10})
        self.rest_iface.execute('/CNAMERecord/%s/cname2.%s/' % (self.zone, self.zone), 'POST', {'rdata': {'cname': 'cname1.%s.' % self.zone}, 'ttl': 10})
        self.rest_iface.execute('/Zone/%s/' % self.zone, 'PUT', {'publish': 'true'})

    def test_remove_records_with_disabled_readd_feature(self):
        dyndns = DynDns(
            dry_run=False,
            customer_name=self.customer_name,
            user_name=self.user_name,
            password=self.password,
        )
        dyndns.sync_records(
            failed=[
                Checkpoint(url='http://127.0.0.1/health/', host='cname2.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.1', type='A'), # remove this
                Checkpoint(url='http://127.0.0.4/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4', type='A'), # remove this
                Checkpoint(url='http://127.0.0.104/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4', type='A'), # non existent
                Checkpoint(url='http://[::2]/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='::2', type='AAAA'), # ipv6
            ],
            passed=[],
            enable_readd=False,
        )

        # IPv4 removed
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
        # IPv6 removed
        tools.assert_equal(
            set([
                '::1',
            ]),
            set([
                self.rest_iface.execute(url, 'GET')['data']['rdata']['address']
                for url in
                self.rest_iface.execute('/AAAARecord/%s/root.%s/' % (self.zone, self.zone), 'GET')['data']
            ])
        )
        # CNAMEs kept
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
        dyndns.sync_records(
            failed=[
                Checkpoint(url='http://127.0.0.2/health/', host='cname2.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.1', type='A'),
                Checkpoint(url='http://127.0.0.3/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4', type='A'),
            ],
            passed=[],
            enable_readd=False,
        )
        # IPv4 not removed - we are not deleting when all records fails
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

    def test_remove_records_with_enabled_readd_feature(self):
        dyndns = DynDns(
            dry_run=False,
            customer_name=self.customer_name,
            user_name=self.user_name,
            password=self.password,
        )
        dyndns.sync_records(
            failed=[
                Checkpoint(url='http://127.0.0.1/health/', host='cname2.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.1', type='A'), # remove this
                Checkpoint(url='http://127.0.0.4/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4', type='A'), # remove this
                Checkpoint(url='http://127.0.0.104/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.4', type='A'), # non existent
                Checkpoint(url='http://[::2]/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='::2', type='AAAA'), # ipv6
            ],
            passed=[
                Checkpoint(url='http://127.0.0.2/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.2', type='A'), # remove this
                Checkpoint(url='http://127.0.0.3/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='127.0.0.3', type='A'), # remove this
                Checkpoint(url='http://[::1]/health/', host='root.%s' % self.zone, record='root.%s.' % self.zone, ip='::1', type='AAAA'), # ipv6
            ],
            enable_readd=True,
        )


        # IPv4 removed
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
        # IPv6 removed
        tools.assert_equal(
            set([
                '::1',
            ]),
            set([
                self.rest_iface.execute(url, 'GET')['data']['rdata']['address']
                for url in
                self.rest_iface.execute('/AAAARecord/%s/root.%s/' % (self.zone, self.zone), 'GET')['data']
            ])
        )
