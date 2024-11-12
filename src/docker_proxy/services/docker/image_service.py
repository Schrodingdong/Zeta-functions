from . import docker_client, logger


# Retrieval ========================================================
def list_images():
    """
    List all docker images images
    """
    return docker_client.images.list()


def get_images_from_prefix(prefix: str):
    """
    Return a list of images given a string prefix. The matching is done to the `image.tags` elements.

    Attributes
    ---
    - prefix: str
    """
    image_list = docker_client.images.list()
    found_images = []
    for image in image_list:
        for tag in image.tags:
            if tag.startswith(prefix) and "base-runner" not in tag:
                found_images.append(image)
                break
    return found_images

# Build image ======================================================
def build_image(image_name: str, dockerfile_path: str):
    """
    Build an image of `image_name`, using the dockerfile specified at `dockerfile_path`

    Attributes
    ---
    - image_name: str
        The image name to be used
    - dockerfile_path: str
        Dockerfile to use for the build
    """
    try:
        docker_client.images.build(
            tag=image_name,
            path=dockerfile_path,
            forcerm=True  # Alwyas remove intermediate containers
        )
    except Exception:
        raise Exception("Unable to build the image '" + image_name + "': "+ dockerfile_path)


# Delete image =====================================================
def delete_images_from_prefix(prefix: str):
    """
    Delete the images prefixed with `prefix`

    Attributes
    ---
    - prefix: str
        Prefix to check the image tag on.

    Return Value
    ---
    - removed_containers: List
    """
    image_list = docker_client.images.list()
    removed_images = []
    for image in image_list:
        print(f"for {image} we have these tags : {image.tags}")
        for tag in image.tags:
            if tag.startswith(prefix) and "base-runner" not in tag:
                try:
                    logger.info(f"Removing image: {tag}...")
                    docker_client.images.remove(image=image.id)
                except Exception:
                    logger.info(f"Forcefully removing image: {tag}...")
                    docker_client.images.remove(image=image.id, force=True)
                finally:
                    removed_images.append(image.id)
                break
    return removed_images
