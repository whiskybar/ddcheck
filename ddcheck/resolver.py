import logging
import socket
import dns.resolver
from urlparse import urlparse, urlunparse
from collections import namedtuple



DYNDNS_NAMESERVERS = ['ns4.p30.dynect.net', 'ns1.p30.dynect.net', 'ns2.p30.dynect.net', 'ns3.p30.dynect.net']
Checkpoint = namedtuple('checkpoint', ['url', 'host', 'record', 'ip', 'type'])
logger = logging.getLogger()


def dig(qname, rdtype, nameservers=None):
    resolver = dns.resolver.Resolver()
    if nameservers:
        resolver.nameservers=[socket.gethostbyname(x) for x in nameservers]
    return resolver.query(qname, rdtype)


def resolve_ips(urls, nameservers=DYNDNS_NAMESERVERS, ipv6=True):
    types = ('A', 'AAAA')
    if not ipv6:
        types = ('A,')
    ret = []
    for url in urls:
        logger.debug('Resolving %s', url)
        scheme, netloc, url, params, query, fragment = urlparse(url)
        for record_type in types:
            answer = dig(netloc, record_type, nameservers=nameservers)
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



