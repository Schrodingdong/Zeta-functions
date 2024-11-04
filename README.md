# Zeta - The local open-source serverless project
This project will try to mimic serverless computing localy on your device.

## Why would you need it ?
idk its cool tho.

## Supported Languages
- Python

## Future Languages
- Java

## Quickstart
> Right now, the project is tested on linux / WSL. Make sure that the project is set up in the same host as the one docker is running in. 
> For WSL make sure to check the `Use the WSL 2 based engine` and `Enable integration with my default WSL distro`.
- Pull the project
- Create a venv. Activate it and install the requirements
- Run the fastapi host application, which is a docker-proxy
```bash
fastapi dev ./src/docker_proxy/main.py 
```
- Build the runner images
```bash
# Python Base runner
docker build -t python-base-runner:latest ./src/runner_images/python_base_runner
```
- Create a Zeta function `POST localhost:8000/zeta/create/<zeta_name>`
    - payload is a python file, with a `main_handler` as its entrypoint:
    ```python
    def do_some_computation():
        # ...

    def main_handler(params):
        # Logic ...
        return { ... }
    ```
- Run the function `localhost:8000/zeta/run/<zeta_name>` 
    - payload should be the same as used for the handler


## Requirements
- The User should define functions in a supported language, which will be defined as a "Zeta Function"
- Creating a Zeta function will build an image following this name convention:
    - `<zeta_function_name>-runner-image-<uuid>`
- A Zeta function should instanciate a container to execute the function
- The container lingers for 5 minute before stopping if no activity is detected
- Concurrency: Each user will have their containers separated from the other ones
- Auto-scalability: If there is to much load on a container, make sure to scale it horizontally