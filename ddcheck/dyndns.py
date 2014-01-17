import sys
import logging
from collections import defaultdict
from dynect.DynectDNS import DynectRest



logger = logging.getLogger()


class DynectRestDry(DynectRest):
    def output_curl(self, uri, method, args):
        if not uri.startswith('/'):
            uri = '/' + uri

        if not uri.startswith('/REST'):
            uri = '/REST' + uri

        print """curl -X%(method)s %(protocol)s://%(host)s:%(port)s%(uri)s \\
    --header "Content-Type: %(content_type)s" \\
    --header "API-Version: %(api_version)s" \\
    --header "Auth-Token: %(token)s" %(data)s
    """ % {
            'method': method,
            'protocol': self.ssl and 'https' or 'http',
            'host': self.host,
            'port': self.port,
            'uri': uri,
            'content_type': self.content_type,
            'api_version': self.api_version,
            'token': self._token,
            'data': args and "--data '%s'" % self.format_arguments(args) or ''
        }

    def execute(self, uri, method, args=None):
        if method in ['DELETE', 'PUT']:
            self.output_curl(uri, method, args)
        else:
            return super(DynectRestDry, self).execute(uri, method, args)


class DynDns(object):
    def __init__(self, customer_name, user_name, password, dry_run=False):
        self.customer_name = customer_name
        self.user_name = user_name
        self.password = password
        self.dry_run = dry_run
        self.connect()

    def connect(self):
        if self.dry_run:
            rest_iface = DynectRestDry()
        else:
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
            if record['rdata']['address'] in addresses:
                self.rest_iface.execute(url, 'DELETE')
        self.rest_iface.execute('/Zone/%s/' % zone, 'PUT', {'publish': 'true'})

    def __del__(self):
        self.disconnect()


# TODO This should be method on DynDns. So it would connect only once.
def remove_records(failed_checkpoints, dyndns_credentials, dry_run):
    def get_zone(record):
        return '.'.join(record.rsplit('.', 3)[1:])

    dyndns = DynDns(**dyndns_credentials, dry_run=dry_run)
    zones = defaultdict(lambda: defaultdict(list))

    # group the failed checkpoints by zone and hostname (record)
    for checkpoint in failed_checkpoints:
        zones[get_zone(checkpoint.record)][checkpoint.record].append(checkpoint)
    for zone, records in zones.items():
        for record, checkpoints in records.items():
            dyndns.remove_addresses(zone=zone, name=record, addresses=[ch.ip for ch in checkpoints])

