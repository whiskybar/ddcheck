import sys
import time
import signal
import argparse
import os.path
import eventlet
from eventlet.timeout import Timeout
from eventlet.green import subprocess
import logging
import logging.handlers
requests = eventlet.patcher.import_patched('requests')

from dyndns import resolve_ips


def check_url(cp, timeout):
    response = None
    try:
        with Timeout(timeout, False):
            response = requests.get(cp.url, headers={'Host': cp.host})
    except requests.exceptions.ConnectionError, e:
        logging.error('%s (%s) connection failed: %s', cp.url, cp.host, e)
    except requests.exceptions.HTTPError, e:
        logging.error('%s (%s) HTTP error: %s', cp.url, cp.host, e)
    except requests.exceptions.RequestException, e:
        logging.error('%s (%s) error: %s', cp.url, cp.host, e)
    else:
        if response is None:
            logging.warning('%s timed out after %d seconds', cp.url, timeout)
        else:
            if response.status_code == requests.codes.ok:
                logging.debug('%s hit', cp.url)
            else:
                logging.error('%s returned %s', cp.url, e.code)
               
def parse_arguments():
    parser = argparse.ArgumentParser(description='Start a ddcheck daemon')
    parser.add_argument('urls', metavar='URL', nargs='+', help='URL to check')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='debug mode on')
    parser.add_argument('-i', '--check-interval', default=10, type=int, help='check interval')
    parser.add_argument('-t', '--timeout', default=5, type=int, help='URL timeout')
    return parser.parse_args()
    
def shutdown(signal, frame):
    sys.exit(0)

def configure_logging(level):
    logging.basicConfig(format='%(asctime)s %(message)s', level=level)
    rh = logging.handlers.TimedRotatingFileHandler(
        filename='/tmp/ddcheck.log',
        when='midnight',
    )
    rh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    rootLogger = logging.getLogger('')
    rootLogger.removeHandler(rootLogger.handlers[0])
    rootLogger.setLevel(logging.DEBUG)
    rootLogger.addHandler(rh)

def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    options = parse_arguments()
    if options.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    configure_logging(level)

    check_interval = options.check_interval
    checkpoints = resolve_ips(options.urls) #TODO: green this?
    while True:
        now = time.time()
        next_check = int(now) /  check_interval * check_interval - now + check_interval + 1
        for cp in checkpoints:
            eventlet.spawn_after(next_check, check_url, cp, options.timeout)
        eventlet.sleep(next_check + 1)

if __name__ == '__main__':
    main()

