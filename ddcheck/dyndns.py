import sys
import logging
from collections import defaultdict
from dynect.DynectDNS import DynectRest

from ddcheck.utils import get_zone



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
        self.rest_iface = None
        self.connect()
        self._changed_zones = set([])

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
            logging.error('Incorrect DynDns credentials')
            sys.exit(1)
        self.rest_iface = rest_iface

    def disconnect(self):
        if self.rest_iface:
            self.rest_iface.execute('/Session/', 'DELETE')
        self.rest_iface = None

    def zone_addresses(self, zone, name, type):
        ret = {}
        for url in self.rest_iface.execute('/%sRecord/%s/%s/' % (type, zone, name), 'GET')['data']:
            ret[url] = self.rest_iface.execute(url, 'GET')['data']
        return ret

    def remove_addresses(self, zone, name, addresses, type):
        current_addresess = self.zone_addresses(zone, name, type).items()
        to_delete = []
        for url, record in current_addresess:
            if record['rdata']['address'] in addresses:
                to_delete.append((url, record['rdata']['address']))
        if len(current_addresess) > len(to_delete):
            for url, address in to_delete:
                logging.info('%s (%s) seems down. Removing', addresses, name)
                self.rest_iface.execute(url, 'DELETE')
                self._changed_zones.add(zone)
        else:
            logging.warning('All IPs (%s) for the record (%s) seems down. Doing nothing.', ", ".join(addresses), name)

    def publish(self, zone):
        if zone in self._changed_zones:
            self.rest_iface.execute('/Zone/%s/' % zone, 'PUT', {'publish': 'true'})
            self._changed_zones.remove(zone)

    def remove_records(self, checkpoints):
        zones = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for checkpoint in checkpoints:
            zone = get_zone(checkpoint.record)
            zones[zone][checkpoint.record][checkpoint.type].append(checkpoint)
        for zone, records in zones.iteritems():
            for record, types in records.iteritems():
                for type, checkpoints in types.iteritems():
                    self.remove_addresses(zone=zone, name=record, addresses=[cp.ip for cp in checkpoints], type=type)
            self.publish(zone)

    def __del__(self):
        self.disconnect()


class LogOnly(object):

    def __init__(self, **kwargs):
        pass

    def remove_records(self, checkpoints):
        for checkpoint in checkpoints:
            logger.info('Detected down: %s %s', checkpoint.host, checkpoint.ip)


