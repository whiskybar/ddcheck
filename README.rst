=======
ddcheck
=======

Check URLs and manage the respective records in DynDNS.


Description
===========

``ddcheck`` accepts a list of healthckeck URLs, resolve them to IPs and makes
HTTP requests directly to the IPs. When given IP is recognized as down, it will
remove the record from DynDNS

Features
--------

* IPv4 and IPv6 support (A and AAAA records in DNS)
* Traversing over CNAMEs to target A/AAAA records
* IP is marked as failed when it either timeouts (configurable in seconds) or
  returns defined HTTP code (for example 500, by default turned off)
* Dry run mode: Will not change the DynDNS recods. Outputs only ``curl`` commands
  instead.
* Will not delete IPs from DynDNS, when all the IPs in the dns record fail.

Installation
============

``pip install 'git+https://github.com/whiskybar/ddcheck.git#egg=ddcheck'``


Usage
=====


CLI
---

DynDNS credetials can be defined either by env variables, or as parameters.

::

    # ddcheck --help

    usage: ddcheck [-h] [-d] [-e ERROR_CODES] [-t TIMEOUT] [-D]
                   [--dynect-customer DYNECT_CUSTOMER] [--dynect-user DYNECT_USER]
                   [--dynect-password DYNECT_PASSWORD]
                   URL [URL ...]

    Run a ddcheck.

    positional arguments:
      URL                   URL to check

    optional arguments:
      -h, --help            show this help message and exit
      -d, --debug           Debug logging on
      -e ERROR_CODES, --error-codes ERROR_CODES
                            HTTP codes considered as non-OK
      -t TIMEOUT, --timeout TIMEOUT
                            URL timeout
      -D, --dry-run         Do not really update the dyndns. Just print records to
                            delete.
      --dynect-customer DYNECT_CUSTOMER
                            Customer name in DynEct (defaults to
                            DYNECT_CUSTOMER_NAME env variable)
      --dynect-user DYNECT_USER
                            Username in DynEct (defaults to DYNECT_USER_NAME env
                            variable)
      --dynect-password DYNECT_PASSWORD
                            Password in DynEct (defaults to DYNECT_PASSWORD env
                            variable)



Example
~~~~~~~

::

    export DYNECT_PASSWORD=aaa
    export DYNECT_USER_NAME=bbb
    export DYNECT_CUSTOMER_NAME=ccc
    ddcheck -e 500 --debug --dry-run http://root.example1.com/health/ http://cname.example2.com/check/

Python
------

Example
~~~~~~~
