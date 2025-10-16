from services.docker import docker_client, logger


def create_network(network_name: str):
    try:
        network = docker_client.networks.create(network_name, driver="bridge")
        return network
    except Exception as e:
        logger.error(e)
        raise e


def does_network_exist(network_name: str):
    try:
        return len(docker_client.networks.list(names=[network_name])) > 0
    except Exception as e:
        logger.error(e)
        raise e


def get_network(network_name: str):
    try:
        filtered_network_list = docker_client.networks.list(names=[network_name])
    except Exception as e:
        logger.error(e)
        raise e
    if len(filtered_network_list) == 1:
        return filtered_network_list[0]
    else:
        raise RuntimeError(f"Can't find network '{network_name}'")
