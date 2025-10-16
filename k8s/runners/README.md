# Zeta Runners
Zeta runners the units that execute the code deployed by the user. These runners need to be containerized, and independent from one another.
The runner is going to be a container image that has the following:
- The user's function.
- The main runner program.

## Zeta Runner specs
- The runner should be instanciated on demand
- The runner should shutdown after a period of inactivity
- The runners are managed by a `ZRM - zeta runner manager`

## Zeta Runner Manager specs
- The ZRM should be responsible to the instanciation of the runners
- The ZRM should send periodic heartbeats to the runner instances
- The ZRM should shutdown