import sys
import signal
import logging
import logging.handlers
import argparse

from ddcheck.dyndns import resolve_ips
from ddcheck.server import check

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run a ddcheck.')
    parser.add_argument('urls', metavar='URL', nargs='+', help='URL to check')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='debug mode on')
    parser.add_argument('-t', '--timeout', default=5, type=int, help='URL timeout')
    return parser.parse_args()
    
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
    configure_logging(level)

    checkpoints = resolve_ips(options.urls, options.timeout) #TODO: green this?
    check(checkpoints)

if __name__ == '__main__':
    main()

