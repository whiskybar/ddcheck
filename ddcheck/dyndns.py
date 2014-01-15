import sys
import socket
import dns.resolver
from urlparse import urlparse, urlunparse
from collections import namedtuple
from dynect.DynectDNS import DynectRest


DYNDNS_NAMESERVERS = ['ns4.p30.dynect.net', 'ns1.p30.dynect.net', 'ns2.p30.dynect.net', 'ns3.p30.dynect.net']
checkpoint = namedtuple('checkpoint', ['url', 'host', 'record', 'ip'])



class DynDns(object):
    def __init__(self, customer_name, user_name, password):
        self.customer_name = customer_name
        self.user_name = user_name
        self.password = password
        self.connect()

    def connect(self):
        rest_iface = DynectRest()
        arguments = {
            'customer_name': self.customer_name,
            'user_name': self.user_name,
            'password': self.password,
        }
        response = rest_iface.execute('/Session/', 'POST', arguments)
        if response['status'] != 'success':
            sys.exit("Incorrect DynDns credentials")
        self.rest_iface = rest_iface

    def disconnect(self):
        if self.rest_iface:
            self.rest_iface.execute('/Session/', 'DELETE')
        self.rest_iface = None

    def zones(self):
        response = self.rest_iface.execute('/Zone/', 'GET')
        return response['data']

    def __del__(self):
        self.disconnect()



def _dig(qname, rdtype, nameservers):
    resolver = dns.resolver.Resolver()
    resolver.nameservers=[socket.gethostbyname(x) for x in nameservers]
    return resolver.query(qname, rdtype)

def resolve_ips(urls, nameservers=DYNDNS_NAMESERVERS):
    ret = []
    for url in urls:
        scheme, netloc, url, params, query, fragment = urlparse(url)
        answer = _dig(netloc, 'A', nameservers=nameservers)
        record = answer.rrset.name.to_text()
        for rdata in answer:
            ret.append(
                checkpoint(
                    urlunparse((scheme, rdata.address, url, params, query, fragment)),
                    netloc,
                    record,
                    rdata.address,
                )
            )
    return ret


def remove_records(failed_checkpoints, dyndns_credentials):
    dyndns = DynDns(**dyndns_credentials)
    pass

