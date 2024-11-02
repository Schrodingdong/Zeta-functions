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
- A Zeta function should instanciate a container to execute the function
- The container lingers for 1 minute before stopping if no activity is detected
- Concurrency: Each user will have their containers separated from the other ones
- Auto-scalability: If there is to much load on a container, make sure to scale it horizontally
- Function Design:
    - The default function name should be: `main_handler`
    - The function should always return a dict object
    - the function params should be static
- Image Design:
    - The container should already have the functino upon its instanciation.
    - The container sits in an IDLE state until an external activity (http request) triggers the execution of the file