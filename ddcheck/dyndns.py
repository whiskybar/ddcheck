import logging
from collections import defaultdict
from dynect.DynectDNS import DynectRest

from ddcheck.utils import get_zone
from ddcheck.exceptions import InvalidCredentialsError, ZoneDoesNotExistError



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
        if method in ['DELETE', 'PUT'] and not uri.startswith('/Session/'):
            return self.output_curl(uri, method, args)
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
            raise InvalidCredentialsError('Incorrect DynDns credentials')
        self.rest_iface = rest_iface

    def disconnect(self):
        if self.rest_iface:
            self.rest_iface.execute('/Session/', 'DELETE')
        self.rest_iface = None

    def zone_addresses(self, zone, name, type):
        ret = {}
        for url in self.rest_iface.execute('/%sRecord/%s/%s/' % (type, zone, name), 'GET')['data']:
            ret[url] = self.rest_iface.execute(url, 'GET')['data']
        import pprint
        pprint.pprint(ret)
        return ret

    def sync_addresses(self, zone, name, failed_addresses, passed_addresses, enable_readd, type):
        current_addresess = dict((r['rdata']['address'], url) for url, r in self.zone_addresses(zone, name, type).items())

        if enable_readd:
            to_delete = set(a for a in current_addresess if a not in passed_addresses)
            to_add = set(a for a in passed_addresses if a not in current_addresess)
        else:
            to_add = set()
            to_delete = set(a for a in current_addresess if a in failed_addresses)
        all_down = not(len(current_addresess) + len(to_add) - len(to_delete) > 0)

        # sanity check
        if all_down:
            logging.warning('All IPs (%s) for the record (%s) seems down. Doing nothing.', ", ".join(to_delete), name)
            return
        # add new ones
        for a in to_add:
            logging.info('%s (%s) seems up. Adding.', a, name)
            self.rest_iface.execute('/ARecord/%s/%s/' % (zone, name), 'POST', {'rdata': {'address': a}})
            self._changed_zones.add(zone)
        # remove old ones
        for a in to_delete:
            logging.info('%s (%s) seems down. Removing.', a, name)
            self.rest_iface.execute(current_addresess[a], 'DELETE')
            self._changed_zones.add(zone)

    def publish(self, zone):
        if zone in self._changed_zones:
            logger.debug('Commiting changes to zone %s', zone)
            self.rest_iface.execute('/Zone/%s/' % zone, 'PUT', {'publish': 'true'})
            self._changed_zones.remove(zone)

    def list_zones(self):
        ret = []
        for url in self.rest_iface.execute('/Zone/', 'GET')['data']:
            ret.append(self.rest_iface.execute(url, 'GET')['data']['zone'])
        return ret

    def sync_records(self, failed, passed, enable_readd):
        # sort records by zone, record, type
        zones = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        for checkpoint in failed:
            zone = get_zone(checkpoint.record)
            zones[zone][checkpoint.record][checkpoint.type]['failed'].append(checkpoint)
        for checkpoint in passed:
            zone = get_zone(checkpoint.record)
            zones[zone][checkpoint.record][checkpoint.type]['passed'].append(checkpoint)

        # sanity check (not removing unknow zones)
        dyndns_zones = self.list_zones()
        for zone in zones.keys():
            if zone not in dyndns_zones:
                logger.error('Zone %s is not managed by this DynDns account', zone)
                raise ZoneDoesNotExistError('Zone %s is not managed by this DynDns account', zone)

        # sync IPs
        for zone, records in zones.iteritems():
            for record, types in records.iteritems():
                for type, checkpoints in types.iteritems():
                    self.sync_addresses(
                        zone=zone,
                        name=record,
                        failed_addresses=[cp.ip for cp in checkpoints['failed']],
                        passed_addresses=[cp.ip for cp in checkpoints['passed']],
                        enable_readd=enable_readd,
                        type=type)
            self.publish(zone)


    def __del__(self):
        self.disconnect()


class LogOnly(object):

    def __init__(self, **kwargs):
        pass

    def sync_records(self, failed, passed, enable_readd):
        logger.info('Readd feature is %s', enable_readd and 'enabled' or 'disabled')
        for checkpoint in failed:
            logger.info('Detected DOWN: %s %s', checkpoint.host, checkpoint.ip)
        for checkpoint in passed:
            logger.info('Detected UP: %s %s', checkpoint.host, checkpoint.ip)



