def get_zone(host):
    if host.endswith('.'):
        host = host[:-1]
    chunks = host.split(".")
    host = ".".join(chunks[-2:])
    return host
