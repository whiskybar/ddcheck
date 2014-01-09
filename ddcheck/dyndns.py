import sys
from collections import namedtuple

from dynect.DynectDNS import DynectRest

checkpoint = namedtuple('checkpoint', ['url', 'host'])
rest_iface = DynectRest()


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


def resolve_ips(urls):
    return [
        checkpoint('http://127.0.0.1/health/', 'www.host-a.com'),
        checkpoint('http://127.0.0.2/health/', 'www.host-a.com'),
        checkpoint('http://127.0.0.3/health/', 'www.host-b.com'),
    ]


def mark_down(failed_checkpoints):
    pass

