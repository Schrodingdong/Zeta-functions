from random import randint
from requests.exceptions import ConnectionError, ReadTimeout
import requests

dns = {}
def set_zeta_port(zeta_name: str, container_port: int):
    dns[container_port] = zeta_name

def prune_dns_port(zeta_name: str, container_port: int):
    if container_port not in dns:
        return
    del dns[container_port]

def retrieve_dynamic_port():
    port = randint(1024, 49151)
    while True:
        # Check if it is in DNS
        if port in dns:
            print(f"[PORT DNS] - conflicting ports : {port} already in use")
            port = ((port + 1) % 49151) + 1025
        # And if it is in used by some other app
        else:
            try:
                requests.get(f"http://localhost:{port}", timeout=0.1)
                print(f"[PORT DNS] - conflicting ports : {port} already in use")
                port = ((port + 1) % 49151) + 1025
            except ReadTimeout:
                print(f"[PORT DNS] - conflicting ports : {port} already in use")
                port = ((port + 1) % 49151) + 1025
                continue
            except ConnectionError:
                break
    print(f"[PORT DNS] - Port to be assigned: {port}")
    return port