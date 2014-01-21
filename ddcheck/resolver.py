import logging
import socket
import dns.resolver
from urlparse import urlparse, urlunparse
from collections import namedtuple

from ddcheck.utils import get_zone



Checkpoint = namedtuple('checkpoint', ['url', 'host', 'record', 'ip', 'type'])
logger = logging.getLogger()


def dig(qname, rdtype, nameservers=None):
    logger.debug('Digging %s %s %s', qname, rdtype, nameservers)
    resolver = dns.resolver.Resolver()
    if nameservers:
        resolver.nameservers=[socket.gethostbyname(x) for x in nameservers]
    return resolver.query(qname, rdtype)


def resolve_ips(urls, ipv6=True):
    types = ('A', 'AAAA')
    if not ipv6:
        types = ('A',)
    ret = []
    for url in urls:
        logger.debug('Resolving %s', url)
        scheme, netloc, url, params, query, fragment = urlparse(url)
        ns = [a.to_text() for a in dig(get_zone(netloc), 'NS')]
        logger.debug("Using nameservers: %s", ", ".join(ns))
        for record_type in types:
            answer = dig(netloc, record_type, nameservers=ns)
            record = answer.rrset.name.to_text()
            for rdata in answer:
                if record_type == 'AAAA':
                    address_part = '[%s]' % rdata.address
                else:
                    address_part = rdata.address
                ret.append(
                    Checkpoint(
                        urlunparse((scheme, address_part, url, params, query, fragment)),
                        netloc,
                        record,
                        rdata.address,
                        record_type,
                    )
                )
                logger.debug('Found health check point:  %s', ret[-1])
    return ret



