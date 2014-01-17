import sys
import signal
import logging
import logging.handlers
import argparse

from ddcheck.server import healthcheck



def parse_arguments():
    parser = argparse.ArgumentParser(description='Run a ddcheck.')
    parser.add_argument('urls', metavar='URL', nargs='+', help='URL to check') # TODO read from stdin?
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='Debug logging on')
    parser.add_argument('-e', '--error-codes', default='', help='HTTP codes considered as non-OK')
    parser.add_argument('-t', '--timeout', default=5, type=int, help='URL timeout')
    parser.add_argument('-D', '--dry-run', default=False, action='store_true', help='Do not really update the dyndns. Just print records to delete.')
    return parser.parse_args()


def shutdown(signal, frame):
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    options = parse_arguments()
    level = logging.WARNING
    if options.debug:
        level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(message)s', level=level)

    error_codes = []
    if options.error_codes:
        error_codes = map(int, options.error_codes.split(','))

    healthcheck(options.urls, error_codes=error_codes, timeout=options.timeout, dry_run=options.dry_run, dyndns_credentials={}) # TODO credentials

if __name__ == '__main__':
    main()

