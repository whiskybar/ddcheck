import logging

import eventlet
from eventlet.timeout import Timeout

requests = eventlet.patcher.import_patched('requests.__init__')

from ddcheck.resolver import resolve_ips
from ddcheck.dyndns import DynDns



def check_url(checkpoint, failed, error_codes, timeout):
    response = None
    try:
        with Timeout(timeout, False):
            response = requests.get(checkpoint.url, headers={'Host': checkpoint.host})
    except requests.ConnectionError, e:
        logging.error('%s (%s) connection failed: %s', checkpoint.url, checkpoint.host, e)
        failed.put(checkpoint)
    except requests.HTTPError, e:
        logging.error('%s (%s) HTTP error: %s', checkpoint.url, checkpoint.host, e)
        failed.put(checkpoint)
    except requests.RequestException, e:
        logging.error('%s (%s) error: %s', checkpoint.url, checkpoint.host, e)
        failed.put(checkpoint)
    else:
        if response is None:
            logging.warning('%s timed out after %d seconds', checkpoint.url, timeout)
            failed.put(checkpoint)
        else:
            if response.status_code not in error_codes:
                logging.debug('%s hit -> %s (OK)', checkpoint.url, response.status_code)
            else:
                logging.error('%s hit -> %s (!!)', checkpoint.url, response.status_code)
                failed.put(checkpoint)


def healthcheck(urls, error_codes=[], timeout=5, dry_run=False, dyndns_credentials={}):
    checkpoints = resolve_ips(urls) #TODO: green this?
    pool = eventlet.GreenPool()
    failed = eventlet.Queue()
    dyndns = DynDns(dry_run=dry_run, **dyndns_credentials)
    for checkpoint in checkpoints:
        pool.spawn(check_url, checkpoint, failed, error_codes, timeout)
    pool.waitall()
    if not failed.empty():
        records = list(failed.queue)
        dyndns.remove_records(records) #TODO: or return the records and call this elsewhere


def healthcheck_daemon(urls, wait=60, error_codes=[], timeout=5, dry_run=False, dyndns_credentials={}):
    pass
    # TODO resolve_ips, for sleep ``wait`` check_url

