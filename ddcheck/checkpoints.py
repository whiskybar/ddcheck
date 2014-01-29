import json
import logging

from ddcheck.resolver import resolve_ips
from ddcheck.exceptions import DdCheckError
from ddcheck.types import Checkpoint



logger = logging.getLogger()


def load_checkpoints(urls, json_file, ipv6):
    if urls and json_file:
        logger.error('Cannot have both JSON file and URLs as the input at the same time.')
        raise DdCheckError('Cannot have both JSON file and URLs as the input at the same time.')
    if urls:
        return resolve_ips(urls, ipv6=ipv6) #TODO: green this
    if json_file:
        return load_json(json_file, ipv6)
    return []


def load_json(json_file, ipv6):
    logging.info('Loading endpoints from %s', json_file)
    data = json.load(open(json_file))
    ret = []
    for endpoint_name, endpoint in data['endpoints'].items():
        logging.debug('Loading endpoint: %s', endpoint_name)
        check_path = endpoint['check_path']
        if not check_path.startswith('/'):
            check_path = "/%s" % check_path
        for ip in endpoint.get('ipv4', []):
            ret.append(
                Checkpoint(
                    'http://%s%s' % (ip, check_path),
                    endpoint['hostname'],
                    "%s." % endpoint['hostname'],
                    ip,
                    'A',
                )
            )
        if ipv6:
            for ip in endpoint.get('ipv6', []):
                ret.append(
                    Checkpoint(
                        'http://[%s]%s' % (ip, check_path),
                        endpoint['hostname'],
                        "%s." % endpoint['hostname'],
                        ip,
                        'AAAA',
                    )
                )
    logging.info('Found %s endpoints', len(ret))
    logging.debug('Found following endpoints: %s', ret)
    return ret

