# Zeta Runners
Zeta Runners for the supported languages

For each supported language, we have 2 types of container images:
- `base-runner` image
  - Contains the needed code infrastructure to wrap the user's code in the `runner` image
  - To build it
    ```sh
    cd zeta-runners/python/base-runner
    docker image build . -t zeta-base-runner-<language>:<version>
    ```
- `runner` image
  - The image used in deployments