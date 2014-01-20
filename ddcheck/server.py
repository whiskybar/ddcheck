import logging

import eventlet
from eventlet.timeout import Timeout

requests = eventlet.patcher.import_patched('requests.__init__')

from ddcheck.resolver import resolve_ips, dig
from ddcheck.dyndns import DynDns



REFERENCE_IPV6_HOSTNAME = 'google.com'


def detect_ipv6_support():
    answer = dig(REFERENCE_IPV6_HOSTNAME, 'AAAA')
    address = answer[0].address
    try:
        response = requests.get('http://[%s]/' % address)
        return response.status_code == 200
    except:
        return False


def check_url(checkpoint, failed, error_codes, timeout):
    response = None
    try:
        with Timeout(timeout, False):
            response = requests.get(checkpoint.url, headers={'Host': checkpoint.host}, allow_redirects=False)
    except requests.ConnectionError, e:
        logging.info('%s %s hit -> (timeout)', checkpoint.host, checkpoint.url)
        logging.debug('%s', e)
        failed.put(checkpoint)
    except requests.HTTPError, e:
        logging.info('%s %s hit -> (error)', checkpoint.host, checkpoint.url)
        logging.debug('%s', e)
        failed.put(checkpoint)
    except requests.RequestException, e:
        logging.info('%s %s hit -> (error)', checkpoint.host, checkpoint.url)
        logging.debug('%s', e)
        failed.put(checkpoint)
    else:
        if response is None:
            logging.warning('%s timed out after %d seconds', checkpoint.url, timeout)
            failed.put(checkpoint)
        else:
            if response.status_code not in error_codes:
                logging.info('%s %s hit -> %s (OK)', checkpoint.host, checkpoint.url, response.status_code)
            else:
                logging.info('%s %s hit -> %s (!!)', checkpoint.host, checkpoint.url, response.status_code)
                failed.put(checkpoint)


def healthcheck(urls, error_codes=[], timeout=5, dry_run=False, backend_kwargs={}, backend=DynDns):
    enable_ipv6 = detect_ipv6_support()
    logging.info('IPv6 support... %s', enable_ipv6 and 'on' or 'off')

    pool = eventlet.GreenPool()
    failed = eventlet.Queue()
    backend_instance = backend(dry_run=dry_run, **backend_kwargs)

    checkpoints = resolve_ips(urls, ipv6=enable_ipv6) #TODO: green this?

    for checkpoint in checkpoints:
        pool.spawn(check_url, checkpoint, failed, error_codes, timeout)
    pool.waitall()

    if not failed.empty():
        records = list(failed.queue)
        backend_instance.remove_records(records) #TODO: or return the records and call this elsewhere


def healthcheck_daemon(urls, wait=60, error_codes=[], timeout=5, dry_run=False, dyndns_credentials={}):
    pass
    # TODO resolve_ips, for sleep ``wait`` check_url

