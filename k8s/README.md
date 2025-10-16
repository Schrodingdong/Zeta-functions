# Zeta Functions
Zeta functions is an open-source FaaS implementation.
> Note: Zeta Functions is not a production ready project. 

## Simple Description
Zeta is a framework for FaaS for local and development purposes. It allows the use of containerized code runners -- `Zeta Functions`, to run code the user provides. The code can be written in a multitude of programming languages, which then gets deployed to the `Zeta Backend`, and the execution can be triggered.

## Terminology
- `User` Human interacting with the system
- `Client` User or a software application interacting with the system
- `Zeta` is the framework unifying this FaaS implementation.
- `Zeta Function / Runner` is a unit able to execute code on demand, whenever it is triggered, that is scalable and not resource intensive

# Product spec
## Functional requirements
- The user is be able to deploy a function written in one of the supported languages.
- The user is be able to manually trigger the deployed function.
- A client should be able to trigger the deployed function.
- A Function can be invoked synchronously (eg: retrieve data)
- A Function can be invoked asynchronously (eg: optimistic data delete, returns a response immediately)
## Non-functional requirements
- The system must be easily setup
- The system must be interacted with using a CLI
- The system must have horizontal scaling in mind