# Zeta - The local open-source serverless project
This project will try to mimic serverless computing localy on your device.

## Why would you need it ?
idk its cool tho.

## Quickstart
> Right now, the project is tested on linux / WSL. Make sure that the project is set up in the same host as the one docker is running in. 
> For WSL make sure to check the `Use the WSL 2 based engine` and `Enable integration with my default WSL distro`.

- Pull the project
- Create a venv. Activate it and install the requirements
- Run this command
```bash
# Export the DOCKER_SOCKET variable in this shell instance
# For global use (not recommended because of sudo), add it to your .bashrc file or similar
export DOCKER_SOCKET=$(sudo find / -name docker.sock | grep docker.sock)
```
- Build the runner images
```bash
# Python Base runner
docker build -t python-base-runner:latest ./src/runner_images/python_base_runner
```
- Run the fastapi host application, which is a docker-proxy
```bash
fastapi dev ./src/docker_proxy/main.py 
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
> Technical Note: Using the same python file for multiple function deployment will result in multiple runner images generated, with the same imageID. 
> That is because they are using the same layers. This shouldn't impact the app execution, but the more you know ;)
- Run the function `localhost:8000/zeta/run/<zeta_name>` 
    - payload should be the same as used for the handler

## To use the CLI
Here are the commands supported:
```
VERSION ===========================
zeta version

CREATE ============================
zeta create <zeta_name> </path/to/file>
	- (Re)Create / (Re)Deploy the zeta, and returns its url for the user

DELETE ============================
zeta delete <zeta_name>
	- Deletes the zeta

NAME LIST =========================
zeta list
zeta ls
	- List zeta names (ONLY)

INFO ==============================
zeta ps 
	- List all zeta metadata
zeta ps <zeta_name>
	- Returns zeta metadata for the specified zeta
```


## Supported Languages
- [x] Python
- [ ] Java


## Requirements
- The User should define functions in a supported language, which will be defined as a "Zeta Function"
- Creating a Zeta function will build an image following this name convention:
    - `<zeta_function_name>-runner-image-<uuid>`
- A Zeta function should instanciate a container to execute the function
- The container lingers for 5 minute before stopping if no activity is detected
- Concurrency: Each user will have their containers separated from the other ones
- Auto-scalability: If there is to much load on a container, make sure to scale it horizontally
