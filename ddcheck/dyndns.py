import sys
import logging
from collections import defaultdict
from dynect.DynectDNS import DynectRest

logger = logging.getLogger()

DYNDNS_NAMESERVERS = ['ns4.p30.dynect.net', 'ns1.p30.dynect.net', 'ns2.p30.dynect.net', 'ns3.p30.dynect.net']



class DynDns(object):
    def __init__(self, customer_name, user_name, password):
        self.customer_name = customer_name
        self.user_name = user_name
        self.password = password
        self.connect()

    def connect(self):
        rest_iface = DynectRest()
        arguments = {
            'customer_name': self.customer_name,
            'user_name': self.user_name,
            'password': self.password,
        }
        response = rest_iface.execute('/Session/', 'POST', arguments)
        if response['status'] != 'success':
            sys.exit("Incorrect DynDns credentials")
        self.rest_iface = rest_iface

    def disconnect(self):
        if self.rest_iface:
            self.rest_iface.execute('/Session/', 'DELETE')
        self.rest_iface = None

    def a_addresses(self, zone, name):
        ret = {}
        for url in self.rest_iface.execute('/ARecord/%s/%s/' % (zone, name), 'GET')['data']:
            ret[url] = self.rest_iface.execute(url, 'GET')['data']
        return ret

    def remove_addresses(self, zone, name, addresses):
        for url, record in self.a_addresses(zone, name).items():
            print record
            if record['rdata']['address'] in addresses:
                self.rest_iface.execute(url, 'DELETE')
        self.rest_iface.execute('/Zone/%s/' % zone, 'PUT', {'publish': 'true'})

    def __del__(self):
        self.disconnect()


# TODO This should be method on DynDns. So it would connect only once.
def remove_records(failed_checkpoints, dyndns_credentials, dry_run):
    def get_zone(record):
        return '.'.join(record.rsplit('.', 3)[1:])

    dyndns = DynDns(**dyndns_credentials)
    zones = defaultdict(lambda: defaultdict(list))

    # group the failed checkpoints by zone and hostname (record)
    for checkpoint in failed_checkpoints:
        zones[get_zone(checkpoint.record)][checkpoint.record].append(checkpoint)
    for zone, records in zones.items():
        for record, checkpoints in records.items():
            dyndns.remove_addresses(zone=zone, name=record, addresses=[ch.ip for ch in checkpoints])

