import os
import sys
import signal
import logging
import logging.handlers
import argparse

from ddcheck.server import healthcheck
from ddcheck.exceptions import DdCheckError
from ddcheck.dyndns import DynDns, LogOnly



def parse_arguments():
    parser = argparse.ArgumentParser(description='Run a ddcheck.')
    parser.add_argument('urls', metavar='URL', default=None, nargs='*', help='URL to check') # TODO read from stdin?
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='Debug logging on')
    parser.add_argument('-e', '--error-codes', default='', help='HTTP codes considered as non-OK')
    parser.add_argument('-t', '--timeout', default=5, type=int, help='URL timeout in seconds')
    parser.add_argument('-b', '--beat-interval', default=None, type=int, help='check every beat seconds (daemon mode)')
    parser.add_argument('-D', '--dry-run', default=False, action='store_true', help='Do not really update the dyndns. Just print records to delete.')
    parser.add_argument('-H', '--healthcheck-only', default=False, action='store_true', help='Do not really talk to any API. Just do a healthcheck and print rhe results.')
    parser.add_argument('-f', '--json-file', default=None, help='Read endpoints from a JSON file')
    parser.add_argument('--dynect-customer', default=None, help='Customer name in DynEct (defaults to DYNECT_CUSTOMER_NAME env variable)')
    parser.add_argument('--dynect-user', default=None, help='Username in DynEct (defaults to DYNECT_USER_NAME env variable)')
    parser.add_argument('--dynect-password', default=None, help='Password in DynEct (defaults to DYNECT_PASSWORD env variable)')

    return parser.parse_args()


def shutdown(signal, frame):
    sys.exit(0)


def configure_logging(options):
    level = logging.DEBUG if options.debug else logging.INFO
    logging.basicConfig(format='%(asctime)s ddcheck: [%(levelname)s] %(message)s', level=level)

    handler = logging.handlers.SysLogHandler(
        address='/dev/log',
        facility=logging.handlers.SysLogHandler.LOG_SYSLOG,
    )
    handler.setFormatter(logging.Formatter('ddcheck: %(message)s'))

    rootLogger = logging.getLogger('')
    rootLogger.setLevel(level)
    rootLogger.addHandler(handler)

def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    options = parse_arguments()
    configure_logging(options)

    error_codes = []
    if options.error_codes:
        error_codes = map(int, options.error_codes.split(','))

    if options.healthcheck_only:
        backend = LogOnly
        dyndns_credentials = {}
    else:
        backend = DynDns
        dyndns_credentials = {
            'customer_name': options.dynect_customer or os.environ.get('DYNECT_CUSTOMER_NAME'),
            'user_name': options.dynect_user or os.environ.get('DYNECT_USER_NAME'),
            'password': options.dynect_password or os.environ.get('DYNECT_PASSWORD'),
        }
        if not dyndns_credentials['customer_name']:
            print 'Dynect customer name not set. Use --dynect-customer or DYNECT_CUSTOMER_NAME'
            sys.exit(1)
        if not dyndns_credentials['user_name']:
            print 'Dynect username not set. Use --dynect-user or DYNECT_USER_NAME'
            sys.exit(1)
        if not dyndns_credentials['password']:
            print 'Dynect password not set. Use --dynect-password or DYNECT_PASSWORD'
            sys.exit(1)

    try:
        healthcheck(
            options.urls,
            error_codes=error_codes,
            timeout=options.timeout,
            dry_run=options.dry_run,
            backend_kwargs=dyndns_credentials,
            backend=backend,
            beat=options.beat_interval,
            json_file=options.json_file,
        )
    except DdCheckError, e:
        sys.exit(1)


if __name__ == '__main__':
    main()

