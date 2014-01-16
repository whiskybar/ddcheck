import logging

import eventlet
from eventlet.timeout import Timeout
requests = eventlet.patcher.import_patched('requests')

from ddcheck.dyndns import remove_records

def check_url(cp, failed, timeout):
    response = None
    try:
        with Timeout(timeout, False):
            response = requests.get(cp.url, headers={'Host': cp.host})
    except requests.exceptions.ConnectionError, e:
        logging.error('%s (%s) connection failed: %s', cp.url, cp.host, e)
        failed.put(cp)
    except requests.exceptions.HTTPError, e:
        logging.error('%s (%s) HTTP error: %s', cp.url, cp.host, e)
    except requests.exceptions.RequestException, e:
        logging.error('%s (%s) error: %s', cp.url, cp.host, e)
        failed.put(cp)
    else:
        if response is None:
            logging.warning('%s timed out after %d seconds', cp.url, timeout)
            failed.put(cp)
        else:
            if response.status_code == requests.codes.ok:
                logging.debug('%s hit', cp.url)
            else:
                logging.error('%s returned %s', cp.url, e.code)

def check(checkpoints, timeout):
    pool = eventlet.GreenPool()
    failed = eventlet.Queue()
    for cp in checkpoints:
        pool.spawn(check_url, cp, failed, timeout)
    pool.waitall()
    if not failed.empty():
        records = [failed.get() for _ in xrange(failed.qsize())]
        remove_records(records) #TODO: or return the records and call this elsewhere

