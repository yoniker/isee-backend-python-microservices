import dns.resolver

def resolve_srv_addr(srv_addr):
    try:
        possible_hosts = dns.resolver.resolve(srv_addr, 'SRV')
        server_details = possible_hosts[0] #TODO support a weighted randomized selection between hosts via weights here if needed
        port = server_details.port
        host = str(server_details.target).rstrip('.')
        return f'{host}:{port}'

    except:
        return ''