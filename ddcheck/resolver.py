import socket
import dns.resolver
from urlparse import urlparse, urlunparse
from collections import namedtuple

Checkpoint = namedtuple('checkpoint', ['url', 'host', 'record', 'ip'])


def _dig(qname, rdtype, nameservers):
    resolver = dns.resolver.Resolver()
    resolver.nameservers=[socket.gethostbyname(x) for x in nameservers]
    return resolver.query(qname, rdtype)


def resolve_ips(urls, nameservers=DYNDNS_NAMESERVERS):
    ret = []
    for url in urls:
        logger.debug('Resolving %s', url)
        scheme, netloc, url, params, query, fragment = urlparse(url)
        answer = _dig(netloc, 'A', nameservers=nameservers)
        record = answer.rrset.name.to_text()
        for rdata in answer:
            ret.append(
                Checkpoint(
                    urlunparse((scheme, rdata.address, url, params, query, fragment)),
                    netloc,
                    record,
                    rdata.address,
                )
            )
            logger.debug('Found health check point:  %s', ret[-1])
    return ret



