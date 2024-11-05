from random import randint

dns = {}
def set_zeta_port(zeta_name: str, container_port: int):
    dns[container_port] = zeta_name

def prune_dns_port(zeta_name: str, container_port: int):
    if container_port not in dns:
        return
    del dns[container_port]

def retrieve_dynamic_port():
    port = randint(1025, 49151)
    while port in dns:
        print(f"[PORT DNS] - conflicting ports : {port} already in use")
        port = ((port + 1) % 49151) + 1025
    return port