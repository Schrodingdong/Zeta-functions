# Docker Proxy

Python proxy that is running on your host machine, manages the containers and zeta functions.

# Zeta endpoint list
- `GET /zeta/meta`
  - Retrieve metadata for all Zeta functions.
- `GET /zeta/meta/{zeta_name}`
  - Retrieve metadata for the specified Zeta function.
- `POST /zeta/create/{zeta_name}`
  - Deploy the zeta function. This creates its metadata and build its runner image.
  - Payload should be a form data entry: `key: file` and a `value: handler file(s)` 
  - The handler file(s) should have their entrypoint as **a function nammed `main_handler`**
  - Supported handler input:
    - [x] single file
    - [ ] multiple file
    - [ ] zip file
    - [ ] tar file
- `POST /zeta/run/{zeta_name}`
  - Run the zeta function.
  - Payload should be `json`, the same argument passed to the `main_handler` function defined in your files

# Deploying the function
Deploying the Zeta will trigger :
- The build of the zeta runner image 
- (Re)create zeta metadata, for easy runner container management

# Run the function
## Cold start
If the zeta container runner is `exited` / `removed` , The cold start will instanciate a container, based on the runner image built in the deployment process. 

## Heartbeat system for Zeta
> Technical note: As of now, the heartbeat system is based around **unix sockets**, making this implementation Unix only.
> 
> Using sockets will also imply that if the docker-proxy was restarted, all the zeta runner containers created in the previous run won't be able to communicate with the restarted proxy instance.

Heartbeats are sent from the zeta runner container to the docker-proxy app in the host, on function activity - aka running the function. This will make us able to track lingering zeta runner containers, and remove them if there wasn't any activity for a duration longer than a defined TIMEOUT.

### Potential solution for a multiplatform app
- Use TCP for container-host communication, with `host.docker.internal`, but there is some issues using this method on linux.
- Containerize the host application, and have inter-container communication.

# Example execution
- User deploys the zeta
- User run the zeta right after deployment
  - This will trigger a cold start - instanciate a zeta container runner, and adds its metadata to a local cache, with the container id and the timestamp of its last execution, and its port configuration.
- User run the zeta after some time ( < then TIMEOUT )
  - The zeta container runner should  be up and running, and update the timestamp of the `container_last_activity`
- User run the zeta after some time ( > then TIMEOUT )
  - The zeta container runner had been removed, therefore, it will trigger a cold start.
