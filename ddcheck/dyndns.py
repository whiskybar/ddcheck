from collections import namedtuple

checkpoint = namedtuple('checkpoint', ['url', 'host'])


def resolve_ips(urls):
    return [
        checkpoint('http://127.0.0.1/health/', 'www.host-a.com'),
        checkpoint('http://127.0.0.2/health/', 'www.host-a.com'),
        checkpoint('http://127.0.0.3/health/', 'www.host-b.com'),
    ]

def mark_down(failed_checkpoints):
    pass

