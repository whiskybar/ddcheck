import sys
import time
import signal
import argparse
import os.path
import eventlet
from eventlet.timeout import Timeout
from eventlet.green import urllib2
from email.mime.text import MIMEText
from eventlet.green import subprocess
import logging
import logging.handlers


def scheduled_urls():
    return []


def check_url(url, timeout, mailto):
    result = None
    try:
        with Timeout(timeout, False):
            result = urllib2.urlopen(url).read()
        if result is None:
            logging.warning('%s timed out after %d seconds', url, timeout)
        else:
            logging.debug('%s hit', url)
    except urllib2.HTTPError, e:
        logging.error('%s returned %s', url, e.code)
    except urllib2.URLError, e:
        logging.error('%s failed: %s', url, e.reason)
    except Exception, e:
        logging.error('%s fatal: %s', url, e)
               
def parse_arguments():
    parser = argparse.ArgumentParser(description='Start a ddcheck daemon')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='debug mode on')
    return parser.parse_args()
    
def shutdown(signal, frame):
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    options = parse_arguments()
    if options.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(format='%(asctime)s %(message)s', level=level)
    rh = logging.handlers.TimedRotatingFileHandler(
        filename='/var/log/hosting/ddcheck.log',
        when='midnight',
    )
    rh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    rootLogger = logging.getLogger('')
    rootLogger.removeHandler(rootLogger.handlers[0])
    rootLogger.setLevel(logging.DEBUG)
    rootLogger.addHandler(rh)

    while True:
        now = time.time()
        next_minute = int(now) / 60 * 60 - now + 61
        for url, timeout, mailto in scheduled_urls():
            eventlet.spawn_after(next_minute, check_url, url, timeout, mailto)
        eventlet.sleep(next_minute + 1)

if __name__ == '__main__':
    main()

