# Zeta - The local open-source serverless project
This project will try to mimic serverless computing localy on your device.

## Why would you need it ?
idk its cool tho.

## Supported Languages
- Python

## Future Languages
- Java

## Requirements
- The User should define functions in a supported language, which will be defined as a "Zeta Function"
- Creating a Zeta function will build an image following this name convention:
    - `<zeta_function_name>-runner-image-<uuid>`
- A Zeta function should instanciate a container to execute the function
- The container lingers for 5 minute before stopping if no activity is detected
- Concurrency: Each user will have their containers separated from the other ones
- Auto-scalability: If there is to much load on a container, make sure to scale it horizontally